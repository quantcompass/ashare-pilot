"""巨量启动策略（识别题材独走股的波段起点）。

对齐《行情判断方法论》§5 的「巨量启动」定义：
- 量比 = 当日成交量 / 前 5 日均量
- 启动 = 量比 > vol_ratio 且 当日涨幅 > pct_change

纯函数(价格 + 成交量 → 启动信号)，无状态、不联网，与 golden_cross 同范式。
"""

from __future__ import annotations

import pandas as pd

# 默认阈值（方法论 §5：量比>3 且 涨幅>9%）
_VOL_RATIO = 3.0
_PCT_CHANGE = 0.09
_VOL_WINDOW = 5


def detect_breakout(
    close: pd.Series,
    volume: pd.Series,
    vol_ratio: float = _VOL_RATIO,
    pct_change: float = _PCT_CHANGE,
) -> pd.Series:
    """检测巨量启动日。

    Args:
        close: 收盘价序列。
        volume: 成交量序列（同索引）。
        vol_ratio: 量比阈值（当日量 / 前 N 日均量）。
        pct_change: 当日涨幅阈值（0.09 = 9%）。

    Returns:
        与 close 等长、索引对齐的信号序列，1=启动日，0=否。
    """
    chg = close.pct_change()
    vol_ma = volume.rolling(_VOL_WINDOW).mean().shift(1)
    vr = volume / vol_ma  # 量比；前期 vol_ma 为 NaN -> vr 为 NaN -> 比较为 False

    launch = (vr > vol_ratio) & (chg > pct_change)
    return launch.fillna(False).astype("int64")


def stage(drawdown_from_peak: float) -> str:
    """根据"距启动后高点的回撤"标注波段阶段(方法论 §5)。

    Args:
        drawdown_from_peak: 现价相对启动后最高点的回撤(负数，如 -0.12)。

    Returns:
        阶段标签。
    """
    if drawdown_from_peak < -0.12:
        return "🔴已深跌"
    if drawdown_from_peak < -0.03:
        return "🟡见顶回落"
    return "🟢拉升/高位"


__all__ = ["detect_breakout", "stage"]
