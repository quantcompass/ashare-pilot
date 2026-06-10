"""选股层：对一组股票跑策略，挑出当日出现买入信号的标的。

关键：区分「真的没有信号」与「取数失败」——后者必须显式暴露，
绝不能把取数失败静默当成「无买入信号」（量化场景下会误导决策）。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ashare_pilot.datasource.base import DataSource
from ashare_pilot.strategy import breakout, golden_cross


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
    refresh: bool = False,
) -> ScanResult:
    """扫描 symbols，返回 ScanResult。

    单只取数失败时记录到 failed 并继续，不中断整体扫描，也不伪装成「无信号」。
    refresh=True 时强制重拉（透传给支持的数据源，如 CachedSource）。
    """
    # 仅在需要刷新时才传 refresh，避免给不支持该参数的源报错
    extra = {"refresh": True} if refresh else {}
    result = ScanResult(total=len(symbols))
    for symbol in symbols:
        try:
            df = source.fetch_daily(symbol, start, end, adjust=adjust, **extra)
            signals = golden_cross.generate_signals(df["close"], fast=fast, slow=slow)
            if int(signals.iloc[-1]) == 1:
                result.hits.append((symbol, float(df["close"].iloc[-1])))
        except Exception as exc:  # noqa: BLE001
            result.failed.append((symbol, str(exc)))
    return result


@dataclass
class BreakoutHit:
    """一只巨量启动波段股的扫描结果。"""

    symbol: str
    launch_date: str       # 启动日
    launch_gain: float     # 启动当日涨幅
    vol_ratio: float       # 启动当日量比
    since_launch: float    # 启动至今涨跌
    from_peak: float       # 距启动后高点回撤
    stage: str             # 阶段标注


def scan_breakouts(
    source: DataSource,
    symbols: list[str],
    start: str,
    end: str,
    recent_days: int = 15,
    vol_ratio: float = 3.0,
    pct_change: float = 0.09,
    adjust: str = "qfq",
) -> list[BreakoutHit]:
    """扫描 symbols，找出近 recent_days 内出现「巨量启动」的波段股并标注阶段。

    取数失败、或数据源不含成交量(如腾讯源)的标的会被跳过，不中断扫描。
    """
    hits: list[BreakoutHit] = []
    for symbol in symbols:
        try:
            df = source.fetch_daily(symbol, start, end, adjust=adjust)
        except Exception:  # noqa: BLE001
            continue
        if "volume" not in df.columns or len(df) < 6:
            continue  # 无成交量无法判断启动

        close, volume = df["close"], df["volume"]
        sig = breakout.detect_breakout(close, volume, vol_ratio, pct_change)
        recent = sig.tail(recent_days)
        launches = recent[recent == 1]
        if not len(launches):
            continue

        ld = launches.index[-1]
        after = close.loc[ld:]
        peak, cur, lpx = after.max(), close.iloc[-1], close.loc[ld]
        vr = (volume / volume.rolling(5).mean().shift(1)).loc[ld]
        hits.append(BreakoutHit(
            symbol=symbol,
            launch_date=ld.strftime("%Y-%m-%d"),
            launch_gain=float(close.pct_change().loc[ld]),
            vol_ratio=float(vr),
            since_launch=float(cur / lpx - 1),
            from_peak=float(cur / peak - 1),
            stage=breakout.stage(float(cur / peak - 1)),
        ))
    return hits


__all__ = ["scan_buy_signals", "ScanResult", "scan_breakouts", "BreakoutHit"]
