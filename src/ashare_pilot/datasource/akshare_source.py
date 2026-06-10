"""基于 akshare 的 A股日线数据源（免费、免 token）。"""

from __future__ import annotations

import pandas as pd

from .base import REQUIRED_COLUMNS, validate

# akshare 中文列名 -> 统一英文列名
_COLUMN_MAP = {
    "日期": "date",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
}


class AkshareSource:
    """用 akshare 拉取 A股日线行情。"""

    def fetch_daily(
        self, symbol: str, start: str, end: str, adjust: str = "qfq"
    ) -> pd.DataFrame:
        import akshare as ak  # 延迟导入，避免无网络环境下导入即失败

        raw = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start,
            end_date=end,
            adjust=adjust,
        )
        df = raw.rename(columns=_COLUMN_MAP)
        df = df[["date", *REQUIRED_COLUMNS]].copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").sort_index()
        for col in REQUIRED_COLUMNS:
            df[col] = df[col].astype("float64")
        return validate(df)
