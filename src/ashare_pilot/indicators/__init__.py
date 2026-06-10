"""技术指标层：纯函数，输入价格序列，输出指标序列。

约定：所有指标都不修改入参，返回与入参等长、索引对齐的 pandas Series，
窗口不足的位置为 NaN。这样上层（策略/回测）可以放心组合。
"""

from __future__ import annotations

import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    """简单移动平均（Simple Moving Average）。

    Args:
        series: 价格序列（通常是收盘价）。
        window: 窗口长度，必须 >= 1。

    Returns:
        与入参等长、索引对齐的移动平均序列；前 window-1 个位置为 NaN。
    """
    if window < 1:
        raise ValueError(f"window 必须 >= 1，收到 {window}")
    return series.rolling(window=window).mean()


__all__ = ["sma"]
