"""市场成本估算(VWAP + 筹码分布粗估)。

对应《行情判断方法论》§6：在缺乏真实筹码/资金数据时，用成交量加权均价
和成交密集区，对"市场平均成本"做**粗略代理**估算 —— 不是真实主力成本。

纯函数(行情 DataFrame → 数值/分布)，无状态、不联网，便于单元测试。
要求 df 含 high/low/close/volume。
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def typical_price(df: pd.DataFrame) -> pd.Series:
    """典型价 = (最高 + 最低 + 收盘) / 3，作为当日成交均价的代理。"""
    return (df["high"] + df["low"] + df["close"]) / 3


def vwap(df: pd.DataFrame) -> float:
    """成交量加权均价(VWAP)，市场平均成本的代理。"""
    tp = typical_price(df)
    return float((tp * df["volume"]).sum() / df["volume"].sum())


def chip_distribution(df: pd.DataFrame, bin_width: float = 2.0) -> pd.Series:
    """筹码分布粗估：按价格分桶累加成交量，返回各价格档的成交量占比。

    Returns:
        index 为价格区间(pd.Interval)、值为占总成交量比例的 Series，按占比降序。
    """
    tp = typical_price(df)
    lo = np.floor(tp.min() / bin_width) * bin_width
    hi = tp.max() + bin_width
    edges = np.arange(lo, hi, bin_width)
    # include_lowest：让恰好落在最低边界的成交量也计入(否则边界值被丢成 NaN)
    bins = pd.cut(tp, bins=edges, include_lowest=True)
    dist = df["volume"].groupby(bins, observed=True).sum()
    total = dist.sum()
    return (dist / total).sort_values(ascending=False)


def position_ratio(df: pd.DataFrame, price: float) -> tuple[float, float]:
    """现价上下方的成交量占比。

    Returns:
        (下方占比, 上方占比) —— 下方≈浮盈筹码、上方≈套牢筹码。
        恰好等于 price 的不计入两者。
    """
    tp = typical_price(df)
    v = df["volume"]
    total = v.sum()
    below = float(v[tp < price].sum() / total)
    above = float(v[tp > price].sum() / total)
    return below, above


__all__ = ["typical_price", "vwap", "chip_distribution", "position_ratio"]
