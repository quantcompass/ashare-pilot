"""双均线金叉/死叉策略。

- 金叉：快线从下方上穿慢线 → 买入信号 (1)
- 死叉：快线从上方下穿慢线 → 卖出信号 (-1)
- 其余：无动作 (0)
"""

from __future__ import annotations

import pandas as pd

from ashare_pilot.indicators import sma


def generate_signals(close: pd.Series, fast: int = 5, slow: int = 20) -> pd.Series:
    """根据收盘价生成双均线信号。

    Args:
        close: 收盘价序列。
        fast: 快线窗口（默认 5）。
        slow: 慢线窗口（默认 20）。

    Returns:
        与 close 等长、索引对齐的信号序列，取值 {1, -1, 0}。

    Raises:
        ValueError: 当 fast >= slow 时。
    """
    if fast >= slow:
        raise ValueError(f"fast({fast}) 必须小于 slow({slow})")

    fast_ma = sma(close, fast)
    slow_ma = sma(close, slow)

    # 快线是否在慢线上方（NaN 比较为 False，得到干净的布尔序列）
    above = (fast_ma > slow_ma).fillna(False)
    prev_above = above.shift(1, fill_value=False)

    # 只在前后两根均线都有效时才允许出信号，避免均线"刚生效"那根被误判为穿越
    valid = fast_ma.notna() & slow_ma.notna()
    can_signal = valid & valid.shift(1, fill_value=False)

    golden = above & (~prev_above) & can_signal  # 金叉：由下方上穿
    death = (~above) & prev_above & can_signal    # 死叉：由上方下穿

    signals = pd.Series(0, index=close.index, dtype="int64")
    signals[golden] = 1
    signals[death] = -1
    return signals


__all__ = ["generate_signals"]
