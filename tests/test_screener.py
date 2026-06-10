"""选股层测试：必须区分「真无信号」与「取数失败」，不能把失败误报为无信号。"""

from __future__ import annotations

import pandas as pd

from ashare_pilot.screener import scan_buy_signals


def _golden_cross_df(fast=5, slow=20):
    """构造一段收盘序列，并截断到「最后一根恰为金叉」处。"""
    from ashare_pilot.strategy import golden_cross

    closes = [10] * 20 + [9, 8, 7, 6, 5] + [6, 7, 8, 9, 10, 12, 14, 16, 18, 20]
    idx = pd.date_range("2024-01-01", periods=len(closes), freq="B", name="date")
    s = pd.Series(closes, index=idx, dtype="float64")
    sig = golden_cross.generate_signals(s, fast=fast, slow=slow)
    cross_idx = [i for i, v in enumerate(sig) if int(v) == 1]
    assert cross_idx, "测试夹具未产生金叉，请调整序列"
    cut = cross_idx[0] + 1  # 截断到金叉那根（含）
    closes2 = closes[:cut]
    idx2 = idx[:cut]
    return pd.DataFrame(
        {"open": closes2, "high": closes2, "low": closes2, "close": closes2}, index=idx2
    )


def _flat_df():
    closes = [10.0] * 40
    idx = pd.date_range("2024-01-01", periods=len(closes), freq="B", name="date")
    return pd.DataFrame(
        {"open": closes, "high": closes, "low": closes, "close": closes}, index=idx
    )


class _FakeSource:
    def __init__(self, mapping):
        self._mapping = mapping  # symbol -> df 或 Exception

    def fetch_daily(self, symbol, start, end, adjust="qfq"):
        v = self._mapping[symbol]
        if isinstance(v, Exception):
            raise v
        return v


def test_all_fetch_failures_flagged_not_silent():
    src = _FakeSource({"A": ConnectionError("x"), "B": ConnectionError("y")})
    result = scan_buy_signals(src, ["A", "B"], "20240101", "20240301")
    assert result.hits == []
    assert len(result.failed) == 2          # 失败被记录
    assert result.all_failed is True        # 明确标记「全失败」


def test_no_signal_is_not_failure():
    src = _FakeSource({"A": _flat_df()})
    result = scan_buy_signals(src, ["A"], "20240101", "20240301")
    assert result.hits == []
    assert result.failed == []
    assert result.all_failed is False       # 真的没信号，不是失败


def test_hit_detected():
    src = _FakeSource({"A": _golden_cross_df()})
    result = scan_buy_signals(src, ["A"], "20240101", "20240301", fast=5, slow=20)
    assert len(result.hits) == 1
    assert result.hits[0][0] == "A"


def test_mixed_success_and_failure():
    src = _FakeSource({"A": _golden_cross_df(), "B": ConnectionError("boom")})
    result = scan_buy_signals(src, ["A", "B"], "20240101", "20240301")
    assert len(result.hits) == 1
    assert len(result.failed) == 1
    assert result.all_failed is False
