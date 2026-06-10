"""默认数据源组装测试：CachedSource(FallbackSource([StockApi, Tencent]))。"""

from __future__ import annotations

from ashare_pilot.datasource import build_default_source
from ashare_pilot.datasource.cached_source import CachedSource
from ashare_pilot.datasource.fallback_source import FallbackSource
from ashare_pilot.datasource.stockapi_source import StockApiSource
from ashare_pilot.datasource.tencent_source import TencentSource


def test_build_default_source_structure(tmp_path):
    src = build_default_source(cache_dir=tmp_path)
    # 最外层是缓存
    assert isinstance(src, CachedSource)
    # 内层是 fallback，顺序：stockapi 主、tencent 备
    inner = src._inner
    assert isinstance(inner, FallbackSource)
    sources = inner._sources
    assert isinstance(sources[0], StockApiSource)
    assert isinstance(sources[1], TencentSource)


def test_build_default_source_exposes_fetch_daily(tmp_path):
    src = build_default_source(cache_dir=tmp_path)
    assert hasattr(src, "fetch_daily")
