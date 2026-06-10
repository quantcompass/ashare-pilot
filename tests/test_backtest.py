import pandas as pd

from ashare_pilot.backtest import run


def test_single_winning_trade():
    prices = pd.Series([10, 11, 12, 11, 10], dtype="float64")
    signals = pd.Series([1, 0, -1, 0, 0], dtype="int64")  # 10 买，12 卖
    result = run(prices, signals, initial_cash=1000.0, fee_rate=0.0)

    assert result.final_value == 1200.0
    assert abs(result.total_return - 0.2) < 1e-9
    assert result.num_trades == 1
    assert result.win_rate == 1.0
    assert result.max_drawdown == 0.0


def test_losing_trade_has_drawdown():
    prices = pd.Series([10, 8, 6], dtype="float64")
    signals = pd.Series([1, 0, -1], dtype="int64")  # 10 买，6 卖
    result = run(prices, signals, initial_cash=1000.0, fee_rate=0.0)

    assert result.final_value == 600.0
    assert abs(result.total_return - (-0.4)) < 1e-9
    assert result.num_trades == 1
    assert result.win_rate == 0.0
    # 从 1000 跌到 600，最大回撤 40%
    assert abs(result.max_drawdown - 0.4) < 1e-9


def test_fee_reduces_return():
    prices = pd.Series([10, 12], dtype="float64")
    signals = pd.Series([1, -1], dtype="int64")
    no_fee = run(prices, signals, initial_cash=1000.0, fee_rate=0.0)
    with_fee = run(prices, signals, initial_cash=1000.0, fee_rate=0.001)
    assert with_fee.final_value < no_fee.final_value


def test_no_signal_keeps_cash():
    prices = pd.Series([10, 20, 30], dtype="float64")
    signals = pd.Series([0, 0, 0], dtype="int64")
    result = run(prices, signals, initial_cash=1000.0)
    assert result.final_value == 1000.0
    assert result.num_trades == 0
