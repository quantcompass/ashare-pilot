"""通知层：信号怎么发出去。

第一阶段只做控制台输出；预留接口，未来可加 钉钉/企业微信/邮件 等，
新增实现满足 Notifier 协议即可。
"""

from __future__ import annotations

from typing import Protocol


class Notifier(Protocol):
    def send(self, title: str, message: str) -> None: ...


class ConsoleNotifier:
    """打印到控制台。"""

    def send(self, title: str, message: str) -> None:
        print(f"\n=== {title} ===\n{message}\n")


__all__ = ["Notifier", "ConsoleNotifier"]
