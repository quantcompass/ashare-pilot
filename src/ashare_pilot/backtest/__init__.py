"""回测层：用历史价格 + 策略信号模拟交易，输出绩效指标。

简化假设（v1，便于理解与验证；后续可逐步逼近真实）：
- 全仓进出：买入信号时用全部现金买入，卖出信号时全部卖出。
- 信号当根收盘价成交（轻微前视，主流简易回测的通行做法，后续可改为次日开盘）。
- 按整数股买入（A股实际最小 100 股一手，可后续加 lot 约束）。
- fee_rate 为单边费率，买卖各收一次。
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class BacktestResult:
    """回测结果与核心绩效指标。"""

    final_value: float          # 期末总资产
    total_return: float         # 总收益率 = (期末-期初)/期初
    max_drawdown: float         # 最大回撤（正数，0.4 表示 40%）
    num_trades: int             # 完成的完整交易（买后卖）次数
    win_rate: float             # 盈利交易占比（无交易时为 0）
    equity_curve: pd.Series     # 每日总资产曲线


def run(
    close: pd.Series,
    signals: pd.Series,
    initial_cash: float = 100_000.0,
    fee_rate: float = 0.0,
) -> BacktestResult:
    """执行回测。

    Args:
        close: 收盘价序列。
        signals: 同索引的信号序列（1 买 / -1 卖 / 0 无）。
        initial_cash: 初始资金。
        fee_rate: 单边交易费率（如 0.001 = 0.1%）。

    Returns:
        BacktestResult。
    """
    cash = initial_cash
    shares = 0
    equity = []
    buy_price = None          # 当前持仓的买入价（用于判断盈亏）
    completed = []            # 每次完整交易的盈亏（卖价-买价）

    for price, signal in zip(close, signals):
        if signal == 1 and shares == 0:
            shares = int(cash // price)
            cost = shares * price
            cash -= cost + cost * fee_rate
            buy_price = price
        elif signal == -1 and shares > 0:
            proceeds = shares * price
            cash += proceeds - proceeds * fee_rate
            completed.append(price - buy_price)
            shares = 0
            buy_price = None
        equity.append(cash + shares * price)

    equity_curve = pd.Series(equity, index=close.index, dtype="float64")
    final_value = float(equity_curve.iloc[-1])
    total_return = final_value / initial_cash - 1.0

    running_max = equity_curve.cummax()
    drawdown = (running_max - equity_curve) / running_max
    max_drawdown = float(drawdown.max())

    num_trades = len(completed)
    wins = sum(1 for pnl in completed if pnl > 0)
    win_rate = wins / num_trades if num_trades else 0.0

    return BacktestResult(
        final_value=final_value,
        total_return=total_return,
        max_drawdown=max_drawdown,
        num_trades=num_trades,
        win_rate=win_rate,
        equity_curve=equity_curve,
    )


__all__ = ["run", "BacktestResult"]
