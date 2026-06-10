"""数据源接口定义。"""

from __future__ import annotations

from typing import Protocol

import pandas as pd

# 核心必需列：所有数据源都必须提供（策略/回测只依赖这些）
CORE_COLUMNS = ["open", "high", "low", "close"]
# 可选列：有则带上。不同源支持程度不同（腾讯无 volume、stockapi 有 amount）
OPTIONAL_COLUMNS = ["volume", "amount"]
# 向后兼容：旧代码（akshare_source）引用的全集
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
    missing = [c for c in CORE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"数据缺少必需列：{missing}")
    if df.index.name != "date":
        raise ValueError(f"索引名必须为 'date'，实际为 {df.index.name!r}")
    return df


class DataIntegrityError(ValueError):
    """行情数据自相矛盾(OHLC 错乱/负价等)，多见于数据源间歇性返回坏数据。

    继承 ValueError，便于上层(如 FallbackSource)用 except 兜住并回落到备源。
    """


def check_ohlc_sane(df: pd.DataFrame) -> pd.DataFrame:
    """校验 OHLC 是否自洽，干净则原样返回，错乱则抛 DataIntegrityError。

    检查每根 K 线满足：
    - 四价均为正且非 NaN
    - high >= open / close / low（最高价名副其实）
    - low  <= open / close / high（最低价名副其实）

    用于拦截 stockapi 个别票偶发的坏数据(如复权算错导致 high<open)。
    空 DataFrame 视为合法(由别处处理)。
    """
    if df.empty:
        return df

    o, h, l, c = df["open"], df["high"], df["low"], df["close"]

    positive = (o > 0) & (h > 0) & (l > 0) & (c > 0)
    high_ok = (h >= o) & (h >= c) & (h >= l)
    low_ok = (l <= o) & (l <= c) & (l <= h)
    # NaN 参与比较得 False，会被下面判为坏行
    sane = positive & high_ok & low_ok

    bad = int((~sane).sum())
    if bad:
        first = df.index[~sane][0]
        raise DataIntegrityError(
            f"检测到 {bad} 行 OHLC 错乱/异常数据(首个异常日 {first.date()})，"
            f"疑似数据源返回了坏数据"
        )
    return df
