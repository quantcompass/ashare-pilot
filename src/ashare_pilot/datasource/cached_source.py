"""本地 parquet 缓存装饰器：历史日线落盘复用，今天的数据总是联网拉。

缓存键 = (symbol, adjust)，文件 data/cache/{symbol}_{adjust}.parquet 存累积历史。
命中条件：缓存覆盖请求区间 且 end < 今天（今天盘中会变，不信缓存）。
落盘时只持久化「今天之前」的行。
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Callable

import pandas as pd

from .base import DataSource


def _parse(date: str) -> pd.Timestamp:
    """YYYYMMDD 或 YYYY-MM-DD -> Timestamp。"""
    return pd.to_datetime(date)


class CachedSource:
    """给任意 DataSource 加一层本地 parquet 缓存。"""

    def __init__(
        self,
        inner: DataSource,
        cache_dir: str | Path,
        today_fn: Callable[[], dt.date] = dt.date.today,
    ) -> None:
        self._inner = inner
        self._cache_dir = Path(cache_dir)
        self._today_fn = today_fn

    def _cache_path(self, symbol: str, adjust: str) -> Path:
        return self._cache_dir / f"{symbol}_{adjust}.parquet"

    def fetch_daily(
        self, symbol: str, start: str, end: str, adjust: str = "qfq"
    ) -> pd.DataFrame:
        today = pd.Timestamp(self._today_fn())
        start_ts, end_ts = _parse(start), _parse(end)
        path = self._cache_path(symbol, adjust)

        cache = None
        if path.exists():
            cache = pd.read_parquet(path)

        # 命中：缓存覆盖请求区间，且不涉及「今天」
        if cache is not None and not cache.empty and end_ts < today:
            if cache.index.min() <= start_ts and cache.index.max() >= end_ts:
                return cache.loc[start_ts:end_ts]

        # 未命中：联网取
        fresh = self._inner.fetch_daily(symbol, start, end, adjust=adjust)

        # 合并缓存与新数据（按日期去重，保留最新）
        if cache is not None and not cache.empty:
            combined = pd.concat([cache, fresh])
            combined = combined[~combined.index.duplicated(keep="last")].sort_index()
        else:
            combined = fresh

        # 落盘：只持久化「今天之前」的行
        to_persist = combined[combined.index < today]
        if not to_persist.empty:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            to_persist.to_parquet(path)

        return fresh
