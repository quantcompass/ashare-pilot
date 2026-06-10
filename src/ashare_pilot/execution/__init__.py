"""交易执行层：统一的下单接口。

第一阶段只提供 PaperBroker（模拟盘），用于把信号"假装"成交、跟踪资金与持仓。
未来接入券商真实下单时，新增 QMTBroker 实现同一个 Broker 协议即可，
上层策略/调度代码无需改动。

⚠️ 真实下单涉及资金风险与券商权限（A股通常需 QMT/Ptrade 权限），
   务必在策略经过充分回测和模拟盘验证后再接入。
"""

from .broker import Broker, Order, PaperBroker

__all__ = ["Broker", "Order", "PaperBroker"]
