"""巨量启动策略测试。对齐方法论 §5：量比>阈值 且 涨幅>阈值 = 启动。"""

from __future__ import annotations

import pandas as pd

from ashare_pilot.strategy import breakout


def _series(vals):
    idx = pd.date_range("2026-01-01", periods=len(vals), freq="B", name="date")
    return pd.Series(vals, index=idx, dtype="float64")


def test_detects_volume_breakout():
    close = _series([10.0] * 20 + [11.0])
    vol = _series([100.0] * 20 + [400.0])
    sig = breakout.detect_breakout(close, vol, vol_ratio=3.0, pct_change=0.09)
    assert sig.iloc[-1] == 1
    assert sig.iloc[:-1].sum() == 0


def test_not_breakout_when_volume_insufficient():
    close = _series([10.0] * 20 + [11.0])
    vol = _series([100.0] * 20 + [150.0])
    assert breakout.detect_breakout(close, vol).iloc[-1] == 0


def test_not_breakout_when_gain_insufficient():
    close = _series([10.0] * 20 + [10.3])
    vol = _series([100.0] * 20 + [400.0])
    assert breakout.detect_breakout(close, vol).iloc[-1] == 0


def test_thresholds_configurable():
    close = _series([10.0] * 20 + [10.3])
    vol = _series([100.0] * 20 + [150.0])
    sig = breakout.detect_breakout(close, vol, vol_ratio=1.4, pct_change=0.02)
    assert sig.iloc[-1] == 1


def test_early_rows_no_false_signal():
    close = _series([10.0, 11.0, 12.0])
    vol = _series([100.0, 400.0, 500.0])
    assert (breakout.detect_breakout(close, vol) == 0).all()


def test_returns_aligned_int_series():
    close = _series([10.0] * 21)
    vol = _series([100.0] * 21)
    sig = breakout.detect_breakout(close, vol)
    assert list(sig.index) == list(close.index)
    assert sig.dtype == "int64"


def test_stage_from_drawdown():
    assert breakout.stage(-0.01) == "🟢拉升/高位"
    assert breakout.stage(-0.06) == "🟡见顶回落"
    assert breakout.stage(-0.20) == "🔴已深跌"
