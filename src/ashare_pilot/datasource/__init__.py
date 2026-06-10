"""数据源层：统一的行情获取接口，屏蔽底层数据提供方差异。

数据契约（所有数据源都必须返回这个格式）：
    一个 pandas DataFrame，
    - 索引：DatetimeIndex，名为 "date"，升序
    - 列：open, high, low, close（float64）必备；volume / amount 可选

上层（指标/策略/回测）完全不关心数据来自哪个提供方。

默认数据源 = CachedSource(FallbackSource([StockApiSource, TencentSource]))：
    stockapi 主源 + 腾讯备源，外层本地缓存。详见 build_default_source。
"""

from __future__ import annotations

from pathlib import Path

from .akshare_source import AkshareSource
from .base import DataSource
from .cached_source import CachedSource
from .fallback_source import FallbackSource
from .stockapi_source import StockApiSource
from .tencent_source import TencentSource

__all__ = [
    "DataSource",
    "AkshareSource",
    "StockApiSource",
    "TencentSource",
    "FallbackSource",
    "CachedSource",
    "build_default_source",
]


def build_default_source(cache_dir: str | Path = "data/cache") -> CachedSource:
    """组装默认数据源：stockapi 主 + 腾讯备，外层本地缓存。

    stockapi 需环境变量 STOCKAPI_TOKEN；缺失或超时会自动回落到腾讯源
    （腾讯免费无 token），因此即使没配 token 也能正常取数。
    """
    fallback = FallbackSource([StockApiSource(), TencentSource()])
    return CachedSource(fallback, cache_dir=cache_dir)
