import pandas as pd

from ashare_pilot.indicators import sma


def test_sma_basic():
    s = pd.Series([1, 2, 3, 4, 5], dtype="float64")
    result = sma(s, window=3)
    # 前两个不足窗口为 NaN，第三个起为算术平均
    assert pd.isna(result.iloc[0])
    assert pd.isna(result.iloc[1])
    assert result.iloc[2] == 2.0  # (1+2+3)/3
    assert result.iloc[3] == 3.0  # (2+3+4)/3
    assert result.iloc[4] == 4.0  # (3+4+5)/3


def test_sma_preserves_index():
    idx = pd.date_range("2024-01-01", periods=4)
    s = pd.Series([10, 20, 30, 40], index=idx, dtype="float64")
    result = sma(s, window=2)
    assert list(result.index) == list(idx)
    assert result.iloc[1] == 15.0


def test_sma_window_one_is_identity():
    s = pd.Series([5, 6, 7], dtype="float64")
    result = sma(s, window=1)
    assert list(result) == [5.0, 6.0, 7.0]
