import pandas as pd

from ashare_pilot.strategy import golden_cross


def test_golden_cross_detects_buy_and_sell():
    # 构造一段：先跌后涨再跌，制造一次金叉(买)和一次死叉(卖)
    prices = pd.Series([10, 8, 6, 4, 6, 8, 10, 8, 6, 4], dtype="float64")
    signals = golden_cross.generate_signals(prices, fast=2, slow=3)

    # 金叉买点在 i5，死叉卖点在 i8（手算验证过）
    assert signals.iloc[5] == 1
    assert signals.iloc[8] == -1
    # 其余位置都应为 0（持有/无动作）
    others = signals.drop(index=[5, 8])
    assert (others == 0).all()


def test_signals_only_contain_valid_values():
    prices = pd.Series(range(1, 30), dtype="float64")
    signals = golden_cross.generate_signals(prices, fast=5, slow=10)
    assert set(signals.unique()).issubset({-1, 0, 1})


def test_signals_index_aligned():
    idx = pd.date_range("2024-01-01", periods=10)
    prices = pd.Series([10, 8, 6, 4, 6, 8, 10, 8, 6, 4], index=idx, dtype="float64")
    signals = golden_cross.generate_signals(prices, fast=2, slow=3)
    assert list(signals.index) == list(idx)


def test_fast_must_be_less_than_slow():
    prices = pd.Series([1, 2, 3], dtype="float64")
    try:
        golden_cross.generate_signals(prices, fast=10, slow=5)
        assert False, "应当因 fast>=slow 抛错"
    except ValueError:
        pass
