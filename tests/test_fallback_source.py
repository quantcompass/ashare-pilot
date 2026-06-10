"""FallbackSource 测试：依次尝试多个源，前者失败自动切下一个。用假源，不联网。"""

from __future__ import annotations

import pandas as pd
import pytest

from ashare_pilot.datasource.fallback_source import FallbackSource


def _df(close):
    idx = pd.DatetimeIndex(pd.to_datetime(["2024-01-02"]), name="date")
    return pd.DataFrame(
        {"open": close, "high": close, "low": close, "close": close}, index=idx
    )


class _GoodSource:
    def __init__(self, tag):
        self.tag = tag
        self.calls = 0

    def fetch_daily(self, symbol, start, end, adjust="qfq"):
        self.calls += 1
        return _df([float(self.tag)])


class _BadSource:
    def __init__(self):
        self.calls = 0

    def fetch_daily(self, symbol, start, end, adjust="qfq"):
        self.calls += 1
        raise ConnectionError("boom")


def test_uses_first_source_when_it_succeeds():
    first, second = _GoodSource(1), _GoodSource(2)
    src = FallbackSource([first, second])
    df = src.fetch_daily("600519", "20240101", "20240201")
    assert df["close"].iloc[0] == 1.0      # 用了第一个
    assert second.calls == 0               # 没碰第二个


def test_falls_back_to_second_on_error():
    first, second = _BadSource(), _GoodSource(2)
    src = FallbackSource([first, second])
    df = src.fetch_daily("600519", "20240101", "20240201")
    assert df["close"].iloc[0] == 2.0      # 切到了第二个
    assert first.calls == 1
    assert second.calls == 1


def test_raises_when_all_sources_fail():
    first, second = _BadSource(), _BadSource()
    src = FallbackSource([first, second])
    with pytest.raises(RuntimeError, match="所有数据源"):
        src.fetch_daily("600519", "20240101", "20240201")


def test_empty_source_list_raises():
    with pytest.raises(ValueError):
        FallbackSource([])
