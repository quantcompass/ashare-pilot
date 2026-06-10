"""多源 fallback：按顺序尝试多个数据源，前一个失败就用下一个。

用于「stockapi 主源 + 腾讯备源」：主源超时/报错时自动切到备源，提升可用性。
"""

from __future__ import annotations

import logging

import pandas as pd

from .base import DataSource

logger = logging.getLogger(__name__)


class FallbackSource:
    """按优先级顺序持有多个数据源，依次尝试直到成功。"""

    def __init__(self, sources: list[DataSource]) -> None:
        if not sources:
            raise ValueError("FallbackSource 至少需要一个数据源")
        self._sources = sources

    def fetch_daily(
        self, symbol: str, start: str, end: str, adjust: str = "qfq"
    ) -> pd.DataFrame:
        errors = []
        for source in self._sources:
            name = type(source).__name__
            try:
                return source.fetch_daily(symbol, start, end, adjust=adjust)
            except Exception as exc:  # noqa: BLE001 — 故意兜住所有异常以切换备源
                logger.warning("数据源 %s 失败，尝试下一个：%s", name, exc)
                errors.append(f"{name}: {exc}")
        raise RuntimeError(f"所有数据源都失败：{'; '.join(errors)}")
