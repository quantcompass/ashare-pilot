"""基于 akshare 腾讯接口（stock_zh_a_hist_tx）的 A股日线数据源。

免费、无 token，实测稳定性优于东财。作为 stockapi 的备源。
注意：腾讯接口返回 amount（成交额）但无 volume（成交量）——契约已放宽允许。
symbol 需带 sz/sh 前缀。
"""

from __future__ import annotations

import pandas as pd

from .base import validate

_OUT_COLUMNS = ["open", "high", "low", "close", "amount"]


def _to_prefixed(code: str) -> str:
    """6 位代码 -> 带交易所前缀：6/9 开头沪(sh)，其余(0/2/3)深(sz)。"""
    return ("sh" if code[0] in ("6", "9") else "sz") + code


class TencentSource:
    """用 akshare 腾讯接口拉取 A股日线（前复权）。"""

    def fetch_daily(
        self, symbol: str, start: str, end: str, adjust: str = "qfq"
    ) -> pd.DataFrame:
        import akshare as ak  # 延迟导入，避免无网络环境下导入即失败

        raw = ak.stock_zh_a_hist_tx(
            symbol=_to_prefixed(symbol),
            start_date=start,
            end_date=end,
            adjust=adjust,
        )
        df = raw.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").sort_index()
        df = df[[c for c in _OUT_COLUMNS if c in df.columns]]
        for col in df.columns:
            df[col] = df[col].astype("float64")
        return validate(df)
