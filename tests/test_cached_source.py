"""CachedSource 测试：本地 parquet 缓存。历史命中复用，今天总是联网。

用 tmp 目录 + 假源 + 注入固定的「今天」，不联网。
"""

from __future__ import annotations

import datetime as dt

import pandas as pd

from ashare_pilot.datasource.cached_source import CachedSource


def _df(dates, base=10.0):
    idx = pd.DatetimeIndex(pd.to_datetime(dates), name="date")
    vals = [base + i for i in range(len(dates))]
    return pd.DataFrame(
        {"open": vals, "high": vals, "low": vals, "close": vals}, index=idx
    )


class _CountingSource:
    """记录被调次数；返回请求区间内的工作日数据。"""

    def __init__(self):
        self.calls = 0

    def fetch_daily(self, symbol, start, end, adjust="qfq"):
        self.calls += 1
        days = pd.bdate_range(pd.to_datetime(start), pd.to_datetime(end))
        df = _df([d.strftime("%Y-%m-%d") for d in days])
        df.index.name = "date"
        return df


def _fixed_today(d):
    return lambda: d


def test_first_call_misses_and_writes_cache(tmp_path):
    inner = _CountingSource()
    src = CachedSource(inner, cache_dir=tmp_path, today_fn=_fixed_today(dt.date(2024, 6, 1)))
    df = src.fetch_daily("600519", "20240102", "20240110")
    assert inner.calls == 1
    assert len(df) > 0
    # 缓存文件已落盘
    assert (tmp_path / "600519_qfq.parquet").exists()


def test_second_call_hits_cache(tmp_path):
    inner = _CountingSource()
    src = CachedSource(inner, cache_dir=tmp_path, today_fn=_fixed_today(dt.date(2024, 6, 1)))
    src.fetch_daily("600519", "20240102", "20240110")
    src.fetch_daily("600519", "20240102", "20240110")  # 同区间，end < today
    assert inner.calls == 1  # 第二次没再调底层


def test_today_in_range_always_refetches(tmp_path):
    inner = _CountingSource()
    today = dt.date(2024, 1, 10)
    src = CachedSource(inner, cache_dir=tmp_path, today_fn=_fixed_today(today))
    # end == 今天 -> 绕过缓存
    src.fetch_daily("600519", "20240102", "20240110")
    src.fetch_daily("600519", "20240102", "20240110")
    assert inner.calls == 2  # 每次都联网


def test_today_rows_not_persisted(tmp_path):
    inner = _CountingSource()
    today = dt.date(2024, 1, 10)
    src = CachedSource(inner, cache_dir=tmp_path, today_fn=_fixed_today(today))
    src.fetch_daily("600519", "20240102", "20240110")
    cached = pd.read_parquet(tmp_path / "600519_qfq.parquet")
    # 缓存里不含「今天及以后」的行
    assert (cached.index < pd.Timestamp(today)).all()


def test_returns_correct_slice(tmp_path):
    inner = _CountingSource()
    src = CachedSource(inner, cache_dir=tmp_path, today_fn=_fixed_today(dt.date(2024, 6, 1)))
    df = src.fetch_daily("600519", "20240103", "20240105")
    assert df.index.min() >= pd.Timestamp("2024-01-03")
    assert df.index.max() <= pd.Timestamp("2024-01-05")
