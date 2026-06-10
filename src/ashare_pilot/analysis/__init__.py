"""分析层：在行情数据之上做衍生分析(成本估算、波段判断等)。

与 strategy(产生买卖信号)平级但定位不同：analysis 不产生交易信号，
只做"看清楚现状"的衍生计算。
"""

from . import cost

__all__ = ["cost"]
