"""数据源层：统一的行情获取接口，屏蔽底层数据提供方差异。

数据契约（所有数据源都必须返回这个格式）：
    一个 pandas DataFrame，
    - 索引：DatetimeIndex，名为 "date"，升序
    - 列：open, high, low, close, volume（float64）

这样上层（指标/策略/回测）完全不关心数据来自 akshare 还是 tushare。
默认实现见 datasource.akshare_source。
"""

from .base import DataSource
from .akshare_source import AkshareSource

__all__ = ["DataSource", "AkshareSource"]
