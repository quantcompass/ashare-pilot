"""数据健全性校验测试：检测 OHLC 错乱(如 high<open、负价)等坏数据。

针对 stockapi 个别票间歇性返回错乱数据(复权算错 + OHLC 不合逻辑)的防护。
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ashare_pilot.datasource.base import DataIntegrityError, check_ohlc_sane


def _df(rows):
    """rows: list of (open, high, low, close)。"""
    idx = pd.DatetimeIndex(
        pd.to_datetime([f"2024-01-{i+1:02d}" for i in range(len(rows))]), name="date"
    )
    return pd.DataFrame(
        {
            "open": [r[0] for r in rows],
            "high": [r[1] for r in rows],
            "low": [r[2] for r in rows],
            "close": [r[3] for r in rows],
        },
        index=idx,
        dtype="float64",
    )


# ---------- 正常数据应通过 ----------

def test_clean_ohlc_passes():
    df = _df([(10, 11, 9, 10.5), (10.5, 12, 10, 11)])
    assert check_ohlc_sane(df) is df  # 原样返回


def test_high_equals_open_close_ok():
    # high 等于 open/close(一字板)也算合法
    df = _df([(10, 10, 10, 10)])
    assert check_ohlc_sane(df) is df


def test_passes_with_optional_volume_amount():
    df = _df([(10, 11, 9, 10.5)])
    df["volume"] = [100.0]
    df["amount"] = [1000.0]
    assert check_ohlc_sane(df) is df


# ---------- 各种 OHLC 错乱应报错 ----------

def test_high_below_open_raises():
    df = _df([(10, 11, 9, 10), (10.5, 9.0, 10, 10.5)])  # 第2行 high<open
    with pytest.raises(DataIntegrityError):
        check_ohlc_sane(df)


def test_high_below_close_raises():
    df = _df([(10, 10.4, 9, 10.5)])  # high < close
    with pytest.raises(DataIntegrityError):
        check_ohlc_sane(df)


def test_low_above_open_raises():
    df = _df([(10, 11, 10.5, 10.8)])  # low > open
    with pytest.raises(DataIntegrityError):
        check_ohlc_sane(df)


def test_low_above_close_raises():
    df = _df([(10, 11, 10.6, 10.2)])  # low > close
    with pytest.raises(DataIntegrityError):
        check_ohlc_sane(df)


def test_high_below_low_raises():
    df = _df([(10, 9, 11, 10)])  # high < low
    with pytest.raises(DataIntegrityError):
        check_ohlc_sane(df)


def test_zero_price_raises():
    df = _df([(10, 11, 9, 10), (0, 0, 0, 0)])  # 第2行价格为0
    with pytest.raises(DataIntegrityError):
        check_ohlc_sane(df)


def test_negative_price_raises():
    df = _df([(-1, 11, 9, 10)])
    with pytest.raises(DataIntegrityError):
        check_ohlc_sane(df)


def test_nan_price_raises():
    df = _df([(10, 11, 9, 10)])
    df.loc[df.index[0], "high"] = np.nan
    with pytest.raises(DataIntegrityError):
        check_ohlc_sane(df)


# ---------- 错误信息友好 ----------

def test_error_message_reports_count():
    # 两行坏数据，信息里应能体现数量/异常
    df = _df([(10, 9, 11, 10), (10, 8, 9, 12)])
    with pytest.raises(DataIntegrityError, match="2"):
        check_ohlc_sane(df)


def test_is_valueerror_subclass():
    # 便于上层用 except Exception 兜住并 fallback
    assert issubclass(DataIntegrityError, ValueError)


def test_empty_df_passes():
    # 空数据不算坏数据(由别处处理)
    df = pd.DataFrame(
        {"open": [], "high": [], "low": [], "close": []},
        index=pd.DatetimeIndex([], name="date"), dtype="float64",
    )
    assert check_ohlc_sane(df) is df
