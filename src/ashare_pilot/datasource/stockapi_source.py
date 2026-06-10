"""基于 stockapi.com.cn 的 A股日线数据源（day 接口，前复权）。

token 从环境变量 STOCKAPI_TOKEN 读取（或构造时传入），绝不硬编码、绝不入库。
实测返回：data 为列式、中文字段、date 为毫秒时间戳数组，code==20000 表示成功。
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import requests

from .base import check_ohlc_sane, validate

_BASE_URL = "https://www.stockapi.com.cn/v1/base/day"

# 输出列（契约核心 + 可选 volume/amount）；源已是英文 key，字符串值
_OUT_COLUMNS = ["open", "high", "low", "close", "volume", "amount"]

# calculationCycle: 100-日, 101-周, 102-月
_CYCLE_DAILY = "100"
_OK_CODE = 20000


def _to_dashed(date: str) -> str:
    """YYYYMMDD -> YYYY-MM-DD；已带横线则原样返回。"""
    if "-" in date:
        return date
    return f"{date[:4]}-{date[4:6]}-{date[6:8]}"


class StockApiSource:
    """用 stockapi.com.cn 拉取 A股日线（前复权）。"""

    def __init__(self, token: str | None = None, timeout: float = 15.0) -> None:
        self._token = token
        self._timeout = timeout

    def _resolve_token(self) -> str:
        token = self._token or os.environ.get("STOCKAPI_TOKEN")
        if not token:
            raise ValueError(
                "未提供 stockapi token：请传入 token= 或设置环境变量 STOCKAPI_TOKEN"
            )
        return token

    def list_by_concept(
        self, concept: str, cache_dir: str | Path = "data/cache"
    ) -> list[str]:
        """从 A股列表(/v1/base/all)按概念名筛出股票代码列表。

        概念字段 gl 形如 "广告营销,AIGC概念,..."，包含 concept 即命中。

        A股列表接口每日限 2 次、且当天数据不变，故**本地缓存一份**
        (data/cache/_ashare_list.json)，之后从本地读，不再联网。
        删除该文件即可强制更新。
        """
        path = Path(cache_dir) / "_ashare_list.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            resp = requests.get(
                "https://www.stockapi.com.cn/v1/base/all",
                params={"token": self._resolve_token()},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            payload = resp.json()
            if payload.get("code") != _OK_CODE:
                raise RuntimeError(
                    f"stockapi 返回错误 code={payload.get('code')} msg={payload.get('msg')}"
                )
            data = payload.get("data", [])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        return [
            str(row["api_code"])
            for row in data
            if concept in str(row.get("gl", ""))
        ]

    def fetch_daily(
        self, symbol: str, start: str, end: str, adjust: str = "qfq"
    ) -> pd.DataFrame:
        # adjust 仅为签名兼容：stockapi day 接口固定前复权
        params = {
            "token": self._resolve_token(),
            "code": symbol,
            "startDate": _to_dashed(start),
            "endDate": _to_dashed(end),
            "calculationCycle": _CYCLE_DAILY,
        }
        resp = requests.get(_BASE_URL, params=params, timeout=self._timeout)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("code") != _OK_CODE:
            raise RuntimeError(
                f"stockapi 返回错误 code={payload.get('code')} msg={payload.get('msg')}"
            )

        data = payload.get("data") or []
        if not data:
            empty = pd.DataFrame(columns=_OUT_COLUMNS)
            empty.index = pd.DatetimeIndex([], name="date")
            return validate(empty)

        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["time"])
        df = df.set_index("date")[_OUT_COLUMNS].sort_index()
        for col in _OUT_COLUMNS:
            df[col] = df[col].astype("float64")
        # 拦截 stockapi 个别票偶发的坏数据(OHLC 错乱)，让 FallbackSource 回落备源
        return check_ohlc_sane(validate(df))
