"""下单接口与模拟盘实现。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Order:
    """一笔成交记录。"""

    symbol: str
    side: str      # "buy" 或 "sell"
    shares: int
    price: float


class Broker(Protocol):
    """券商下单协议。真实券商（如 QMT）实现同一接口即可平滑替换。"""

    def buy(self, symbol: str, shares: int, price: float) -> Order: ...
    def sell(self, symbol: str, shares: int, price: float) -> Order: ...
    def position(self, symbol: str) -> int: ...


class PaperBroker:
    """模拟盘：在内存里记账，不连真实券商。"""

    def __init__(self, cash: float = 100_000.0) -> None:
        self.cash = cash
        self._positions: dict[str, int] = {}
        self.orders: list[Order] = []

    def position(self, symbol: str) -> int:
        return self._positions.get(symbol, 0)

    def buy(self, symbol: str, shares: int, price: float) -> Order:
        cost = shares * price
        if cost > self.cash:
            raise ValueError(f"资金不足：需 {cost}，仅有 {self.cash}")
        self.cash -= cost
        self._positions[symbol] = self.position(symbol) + shares
        order = Order(symbol=symbol, side="buy", shares=shares, price=price)
        self.orders.append(order)
        return order

    def sell(self, symbol: str, shares: int, price: float) -> Order:
        held = self.position(symbol)
        if shares > held:
            raise ValueError(f"持仓不足：欲卖 {shares}，仅持 {held}")
        self.cash += shares * price
        self._positions[symbol] = held - shares
        order = Order(symbol=symbol, side="sell", shares=shares, price=price)
        self.orders.append(order)
        return order
