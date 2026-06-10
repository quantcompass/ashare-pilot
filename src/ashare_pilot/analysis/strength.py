"""相对强弱：个股相对基准(大盘/同行)在某窗口内的超额收益。

对应《行情判断方法论》§4：判断个股是跑赢还是跑输基准。
跑输大盘的票，往往是独自走弱(不要指望大盘反弹来救它)。

纯函数(两条价格序列 → 强弱结果)，按共同日期对齐，便于单元测试。
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class Strength:
    stock_return: float    # 个股区间收益
    bench_return: float    # 基准区间收益
    excess: float          # 超额收益 = 个股 - 基准
    outperforming: bool    # 是否跑赢基准(超额 > 0)


def relative_strength(
    stock: pd.Series, bench: pd.Series, window: int | None = None
) -> Strength:
    """计算个股相对基准的强弱。

    Args:
        stock: 个股收盘价序列(DatetimeIndex)。
        bench: 基准收盘价序列(同类索引)。
        window: 回看交易日数；None 表示用全部共同区间。

    Returns:
        Strength。区间取两序列的共同日期；window 给定时取最近 window+1 个点的首尾。
    """
    joined = pd.concat([stock.rename("s"), bench.rename("b")], axis=1).dropna()
    if window is not None:
        joined = joined.tail(window + 1)

    s, b = joined["s"], joined["b"]
    stock_return = float(s.iloc[-1] / s.iloc[0] - 1)
    bench_return = float(b.iloc[-1] / b.iloc[0] - 1)
    excess = stock_return - bench_return
    return Strength(
        stock_return=stock_return,
        bench_return=bench_return,
        excess=excess,
        outperforming=excess > 0,
    )


__all__ = ["relative_strength", "Strength"]
