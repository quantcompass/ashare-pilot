"""本地 parquet 缓存装饰器：所有日线(含今天)落盘复用。

缓存键 = (symbol, adjust)，文件 data/cache/{symbol}_{adjust}.parquet 存累积历史。
默认命中条件：缓存覆盖请求区间即直接读本地，不联网(含今天的快照也复用)。
refresh=True 时绕过缓存强制重拉并更新缓存(盘中想要最新值时用)。

注意：因为今天的数据也会缓存，盘中拿到的是「某一时刻的快照」，
不 refresh 就不会更新到最新——这是刻意的取舍(省流量/额度，按需刷新)。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .base import DataSource


def _parse(date: str) -> pd.Timestamp:
    """YYYYMMDD 或 YYYY-MM-DD -> Timestamp。"""
    return pd.to_datetime(date)


class CachedSource:
    """给任意 DataSource 加一层本地 parquet 缓存。"""

    def __init__(self, inner: DataSource, cache_dir: str | Path) -> None:
        self._inner = inner
        self._cache_dir = Path(cache_dir)

    def _cache_path(self, symbol: str, adjust: str) -> Path:
        return self._cache_dir / f"{symbol}_{adjust}.parquet"

    def fetch_daily(
        self,
        symbol: str,
        start: str,
        end: str,
        adjust: str = "qfq",
        refresh: bool = False,
    ) -> pd.DataFrame:
        start_ts, end_ts = _parse(start), _parse(end)
        path = self._cache_path(symbol, adjust)

        cache = None
        if path.exists():
            cache = pd.read_parquet(path)

        # 命中：未要求刷新、且缓存覆盖请求区间 -> 直接读本地(含今天的快照也复用)
        if (
            not refresh
            and cache is not None
            and not cache.empty
            and cache.index.min() <= start_ts
            and cache.index.max() >= end_ts
        ):
            return cache.loc[start_ts:end_ts]

        # 未命中或强制刷新：联网取
        fresh = self._inner.fetch_daily(symbol, start, end, adjust=adjust)

        # 合并缓存与新数据(按日期去重，保留最新)
        if cache is not None and not cache.empty:
            combined = pd.concat([cache, fresh])
            combined = combined[~combined.index.duplicated(keep="last")].sort_index()
        else:
            combined = fresh

        # 落盘：持久化全部行(含今天)
        if not combined.empty:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            combined.to_parquet(path)

        return fresh
