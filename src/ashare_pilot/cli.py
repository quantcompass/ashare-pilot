"""命令行入口：把数据源 → 策略 → 回测/选股/信号 串起来。

用法示例：
    uv run ashare-pilot backtest --symbol 000001 --start 20230101 --end 20240101
    uv run ashare-pilot signal   --symbol 600519
    uv run ashare-pilot screen   --start 20240101 --end 20240601
"""

from __future__ import annotations

import argparse
import datetime as _dt

from ashare_pilot import backtest
from ashare_pilot.config import DEFAULT
from ashare_pilot.datasource import AkshareSource
from ashare_pilot.notify import ConsoleNotifier
from ashare_pilot.screener import scan_buy_signals
from ashare_pilot.strategy import golden_cross


def _today() -> str:
    return _dt.date.today().strftime("%Y%m%d")


def _default_start() -> str:
    # 默认回看一年
    return (_dt.date.today() - _dt.timedelta(days=365)).strftime("%Y%m%d")


def cmd_backtest(args: argparse.Namespace) -> None:
    src = AkshareSource()
    df = src.fetch_daily(args.symbol, args.start, args.end, adjust=DEFAULT.adjust)
    signals = golden_cross.generate_signals(df["close"], fast=args.fast, slow=args.slow)
    result = backtest.run(
        df["close"], signals, initial_cash=DEFAULT.initial_cash, fee_rate=DEFAULT.fee_rate
    )
    print(f"\n标的 {args.symbol}  区间 {args.start}~{args.end}  "
          f"双均线({args.fast},{args.slow})")
    print(f"  期末资产：{result.final_value:,.2f}")
    print(f"  总收益率：{result.total_return:.2%}")
    print(f"  最大回撤：{result.max_drawdown:.2%}")
    print(f"  交易次数：{result.num_trades}")
    print(f"  胜    率：{result.win_rate:.2%}")


def cmd_signal(args: argparse.Namespace) -> None:
    src = AkshareSource()
    df = src.fetch_daily(args.symbol, args.start, args.end, adjust=DEFAULT.adjust)
    signals = golden_cross.generate_signals(df["close"], fast=args.fast, slow=args.slow)
    latest = signals.iloc[-1]
    action = {1: "🟢 金叉 买入", -1: "🔴 死叉 卖出", 0: "⚪ 无信号 持有/观望"}[int(latest)]
    last_date = df.index[-1].strftime("%Y-%m-%d")
    ConsoleNotifier().send(
        f"{args.symbol} 最新信号（{last_date}）",
        f"收盘价 {df['close'].iloc[-1]:.2f}\n动作：{action}",
    )


def cmd_screen(args: argparse.Namespace) -> None:
    buys = scan_buy_signals(
        AkshareSource(), DEFAULT.watchlist, args.start, args.end,
        fast=args.fast, slow=args.slow, adjust=DEFAULT.adjust,
    )
    msg = "\n".join(f"  {s}  现价 {p:.2f}" for s, p in buys) or "  今日无金叉买入信号"
    ConsoleNotifier().send("选股扫描 · 金叉买入候选", msg)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ashare-pilot", description="A股策略研究与信号系统")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser, need_symbol: bool) -> None:
        if need_symbol:
            p.add_argument("--symbol", required=True, help="股票代码，如 000001")
        p.add_argument("--start", default=_default_start(), help="起始日 YYYYMMDD")
        p.add_argument("--end", default=_today(), help="结束日 YYYYMMDD")
        p.add_argument("--fast", type=int, default=DEFAULT.fast, help="快线窗口")
        p.add_argument("--slow", type=int, default=DEFAULT.slow, help="慢线窗口")

    p_bt = sub.add_parser("backtest", help="回测单只股票")
    add_common(p_bt, need_symbol=True)
    p_bt.set_defaults(func=cmd_backtest)

    p_sig = sub.add_parser("signal", help="查看单只股票最新信号")
    add_common(p_sig, need_symbol=True)
    p_sig.set_defaults(func=cmd_signal)

    p_scr = sub.add_parser("screen", help="扫描自选股池的当日买入信号")
    add_common(p_scr, need_symbol=False)
    p_scr.set_defaults(func=cmd_screen)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
