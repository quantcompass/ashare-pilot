"""CachedSource 测试：本地 parquet 缓存。

规格：所有数据(含今天)都落盘复用；默认命中缓存，只有 refresh=True 才强制重拉。
用 tmp 目录 + 假源，不联网。
"""

from __future__ import annotations

import pandas as pd

from ashare_pilot.datasource.cached_source import CachedSource


def _df(dates):
    idx = pd.DatetimeIndex(pd.to_datetime(dates), name="date")
    vals = [10.0 + i for i in range(len(dates))]
    return pd.DataFrame(
        {"open": vals, "high": vals, "low": vals, "close": vals}, index=idx
    )


class _CountingSource:
    def __init__(self):
        self.calls = 0

    def fetch_daily(self, symbol, start, end, adjust="qfq"):
        self.calls += 1
        days = pd.bdate_range(pd.to_datetime(start), pd.to_datetime(end))
        df = _df([d.strftime("%Y-%m-%d") for d in days])
        df.index.name = "date"
        return df


def test_first_call_misses_and_writes_cache(tmp_path):
    inner = _CountingSource()
    src = CachedSource(inner, cache_dir=tmp_path)
    df = src.fetch_daily("600519", "20240102", "20240110")
    assert inner.calls == 1
    assert len(df) > 0
    assert (tmp_path / "600519_qfq.parquet").exists()


def test_second_call_hits_cache(tmp_path):
    inner = _CountingSource()
    src = CachedSource(inner, cache_dir=tmp_path)
    src.fetch_daily("600519", "20240102", "20240110")
    src.fetch_daily("600519", "20240102", "20240110")
    assert inner.calls == 1  # 第二次命中缓存，没再调底层


def test_all_rows_persisted_including_recent(tmp_path):
    """新规格：缓存持久化全部行(不再排除今天)。"""
    inner = _CountingSource()
    src = CachedSource(inner, cache_dir=tmp_path)
    src.fetch_daily("600519", "20240102", "20240110")
    cached = pd.read_parquet(tmp_path / "600519_qfq.parquet")
    fresh = inner.fetch_daily("600519", "20240102", "20240110")
    assert len(cached) == len(fresh)


def test_refresh_forces_refetch(tmp_path):
    inner = _CountingSource()
    src = CachedSource(inner, cache_dir=tmp_path)
    src.fetch_daily("600519", "20240102", "20240110")
    src.fetch_daily("600519", "20240102", "20240110", refresh=True)
    assert inner.calls == 2  # refresh 触发重拉


def test_refresh_updates_cache(tmp_path):
    inner = _CountingSource()
    src = CachedSource(inner, cache_dir=tmp_path)
    src.fetch_daily("600519", "20240102", "20240110", refresh=True)
    assert (tmp_path / "600519_qfq.parquet").exists()


def test_returns_correct_slice(tmp_path):
    inner = _CountingSource()
    src = CachedSource(inner, cache_dir=tmp_path)
    df = src.fetch_daily("600519", "20240103", "20240105")
    assert df.index.min() >= pd.Timestamp("2024-01-03")
    assert df.index.max() <= pd.Timestamp("2024-01-05")
