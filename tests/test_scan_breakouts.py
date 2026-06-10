"""巨量启动扫描测试：在股票池里找近期启动的波段股并标注阶段。用假源，不联网。"""

from __future__ import annotations

import pandas as pd

from ashare_pilot.screener import scan_breakouts


def _df(closes, vols):
    idx = pd.date_range("2026-01-01", periods=len(closes), freq="B", name="date")
    return pd.DataFrame(
        {"open": closes, "high": closes, "low": closes,
         "close": closes, "volume": vols},
        index=idx,
    )


def _breakout_then_fall():
    # 20天平稳 -> 启动(+10%,量比4) -> 冲高 -> 回落到深跌(-15%+)
    closes = [10.0] * 20 + [11.0, 11.5, 12.0, 11.0, 10.0]
    vols = [100.0] * 20 + [400.0, 200, 150, 180, 160]
    return _df(closes, vols)


def _flat():
    return _df([10.0] * 25, [100.0] * 25)


def _no_volume():
    d = _df([10.0] * 25, [100.0] * 25)
    return d.drop(columns=["volume"])


class _FakeSource:
    def __init__(self, mapping):
        self._m = mapping

    def fetch_daily(self, symbol, start, end, adjust="qfq"):
        return self._m[symbol]


def test_finds_breakout_and_stage():
    src = _FakeSource({"A": _breakout_then_fall()})
    hits = scan_breakouts(src, ["A"], "20260101", "20260301", recent_days=10)
    assert len(hits) == 1
    h = hits[0]
    assert h.symbol == "A"
    assert h.stage == "🔴已深跌"          # 启动后冲到12再跌回10
    assert h.from_peak < -0.12


def test_no_breakout_no_hit():
    src = _FakeSource({"A": _flat()})
    hits = scan_breakouts(src, ["A"], "20260101", "20260301")
    assert hits == []


def test_missing_volume_skipped():
    src = _FakeSource({"A": _no_volume()})
    hits = scan_breakouts(src, ["A"], "20260101", "20260301")
    assert hits == []  # 无成交量无法判断，跳过而非报错


def test_fetch_error_skipped():
    class _Bad:
        def fetch_daily(self, *a, **k):
            raise ConnectionError("x")
    hits = scan_breakouts(_Bad(), ["A"], "20260101", "20260301")
    assert hits == []
