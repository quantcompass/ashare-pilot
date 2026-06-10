"""全局配置。

后续可改为从 TOML/环境变量读取；现在用一个 dataclass 集中管理默认参数。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Config:
    # 自选股池（用于 screen 全市场/池内扫描）
    watchlist: list[str] = field(
        default_factory=lambda: ["000001", "600519", "000858", "601318", "600036"]
    )
    # 双均线参数
    fast: int = 5
    slow: int = 20
    # 回测/模拟盘资金与费率
    initial_cash: float = 100_000.0
    fee_rate: float = 0.0003  # 万三，粗略示意，实际含印花税/佣金/过户费
    # 复权方式
    adjust: str = "qfq"


DEFAULT = Config()
