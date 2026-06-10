"""数据源接口定义。"""

from __future__ import annotations

from typing import Protocol

import pandas as pd

REQUIRED_COLUMNS = ["open", "high", "low", "close", "volume"]


class DataSource(Protocol):
    """行情数据源协议。实现者需返回符合数据契约的 DataFrame。"""

    def fetch_daily(
        self, symbol: str, start: str, end: str, adjust: str = "qfq"
    ) -> pd.DataFrame:
        """获取单只股票的日线行情。

        Args:
            symbol: 股票代码，6 位，如 "000001"。
            start: 起始日期 "YYYYMMDD"。
            end: 结束日期 "YYYYMMDD"。
            adjust: 复权方式，"qfq" 前复权 / "hfq" 后复权 / "" 不复权。

        Returns:
            DatetimeIndex(name="date") 升序、含 open/high/low/close/volume 的 DataFrame。
        """
        ...


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """校验 DataFrame 是否符合数据契约，符合则原样返回，否则抛错。"""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"数据缺少必需列：{missing}")
    if df.index.name != "date":
        raise ValueError(f"索引名必须为 'date'，实际为 {df.index.name!r}")
    return df
