"""ashare-pilot：A股策略研究与信号系统。

分层：datasource(取数) → indicators(指标) → strategy(信号)
      → backtest(回测) / screener(选股) → notify(提醒) → execution(下单, 预留)
"""


def main() -> None:
    from ashare_pilot.cli import main as cli_main

    cli_main()
