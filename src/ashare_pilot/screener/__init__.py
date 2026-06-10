"""选股层：对一组股票跑策略，挑出当日出现买入信号的标的。

关键：区分「真的没有信号」与「取数失败」——后者必须显式暴露，
绝不能把取数失败静默当成「无买入信号」（量化场景下会误导决策）。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ashare_pilot.datasource.base import DataSource
from ashare_pilot.strategy import golden_cross


@dataclass
class ScanResult:
    """选股扫描结果。"""

    hits: list[tuple[str, float]] = field(default_factory=list)   # (代码, 现价)
    failed: list[tuple[str, str]] = field(default_factory=list)   # (代码, 失败原因)
    total: int = 0

    @property
    def all_failed(self) -> bool:
        """是否所有标的都取数失败（结果不可信的信号）。"""
        return self.total > 0 and len(self.failed) == self.total


def scan_buy_signals(
    source: DataSource,
    symbols: list[str],
    start: str,
    end: str,
    fast: int = 5,
    slow: int = 20,
    adjust: str = "qfq",
) -> ScanResult:
    """扫描 symbols，返回 ScanResult。

    单只取数失败时记录到 failed 并继续，不中断整体扫描，也不伪装成「无信号」。
    """
    result = ScanResult(total=len(symbols))
    for symbol in symbols:
        try:
            df = source.fetch_daily(symbol, start, end, adjust=adjust)
            signals = golden_cross.generate_signals(df["close"], fast=fast, slow=slow)
            if int(signals.iloc[-1]) == 1:
                result.hits.append((symbol, float(df["close"].iloc[-1])))
        except Exception as exc:  # noqa: BLE001
            result.failed.append((symbol, str(exc)))
    return result


__all__ = ["scan_buy_signals", "ScanResult"]
