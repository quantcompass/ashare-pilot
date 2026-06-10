"""相对强弱测试：个股 vs 基准(大盘/同行)在某窗口的超额收益。纯函数。

对应方法论 §4：判断个股是跑赢还是跑输基准(独走/弱势)。
"""

from __future__ import annotations

import pandas as pd
import pytest

from ashare_pilot.analysis import strength


def _s(vals, start="2026-01-01"):
    idx = pd.date_range(start, periods=len(vals), freq="B", name="date")
    return pd.Series(vals, index=idx, dtype="float64")


def test_outperform_when_stock_rises_more():
    stock = _s([10, 11, 12])     # +20%
    bench = _s([100, 101, 102])  # +2%
    r = strength.relative_strength(stock, bench)
    assert r.stock_return == pytest.approx(0.20)
    assert r.bench_return == pytest.approx(0.02)
    assert r.excess == pytest.approx(0.18)
    assert r.outperforming is True


def test_underperform_when_stock_falls_more():
    stock = _s([10, 9, 8])        # -20%
    bench = _s([100, 100, 99])    # -1%
    r = strength.relative_strength(stock, bench)
    assert r.excess < 0
    assert r.outperforming is False


def test_window_limits_lookback():
    stock = _s([10, 20, 11, 12])  # 全程+20%，但近2根(11->12)
    bench = _s([100, 100, 100, 100])
    r = strength.relative_strength(stock, bench, window=2)
    # 只看最近 window+1=3 根的首尾? 约定 window=N 表示近 N 个交易日变化
    assert r.stock_return == pytest.approx(12 / 20 - 1)  # 从 window 根前(20)到现在(12)


def test_aligns_on_common_dates():
    stock = _s([10, 11, 12], start="2026-01-01")
    bench = pd.Series(
        [100, 102], index=pd.date_range("2026-01-02", periods=2, freq="B", name="date"),
        dtype="float64",
    )
    # 只有 01-02、01-03 重叠
    r = strength.relative_strength(stock, bench)
    assert r.stock_return == pytest.approx(12 / 11 - 1)  # 用重叠区间首尾
    assert r.bench_return == pytest.approx(102 / 100 - 1)


def test_flat_is_not_outperforming():
    stock = _s([10, 10, 10])
    bench = _s([100, 100, 100])
    r = strength.relative_strength(stock, bench)
    assert r.excess == pytest.approx(0.0)
    assert r.outperforming is False  # 持平不算跑赢
