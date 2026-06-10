"""选股层：对一组股票跑策略，挑出当日出现买入信号的标的。"""

from __future__ import annotations

import pandas as pd

from ashare_pilot.datasource.base import DataSource
from ashare_pilot.strategy import golden_cross


def scan_buy_signals(
    source: DataSource,
    symbols: list[str],
    start: str,
    end: str,
    fast: int = 5,
    slow: int = 20,
    adjust: str = "qfq",
) -> list[tuple[str, float]]:
    """扫描 symbols，返回当日出现金叉买入信号的 (代码, 最新收盘价) 列表。

    单只股票取数失败时跳过该只，不中断整体扫描。
    """
    hits: list[tuple[str, float]] = []
    for symbol in symbols:
        try:
            df = source.fetch_daily(symbol, start, end, adjust=adjust)
            signals = golden_cross.generate_signals(df["close"], fast=fast, slow=slow)
            if int(signals.iloc[-1]) == 1:
                hits.append((symbol, float(df["close"].iloc[-1])))
        except Exception as exc:  # noqa: BLE001
            print(f"  跳过 {symbol}：{exc}")
    return hits


__all__ = ["scan_buy_signals"]
