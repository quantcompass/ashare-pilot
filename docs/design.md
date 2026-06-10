# ashare-pilot 设计文档

## 定位与范围

ashare-pilot 第一阶段是一个 **A股策略研究 & 信号系统**：拉数据、算指标、出信号、做回测、扫选股、发提醒。**自动下单仅做接口预留**（A股真实下单需券商 QMT/Ptrade 量化权限，通常有资金门槛），等策略经回测与模拟盘验证有效后再接入。

**不做（YAGNI）**：实盘自动下单、Web 界面、多市场（先专注 A股）、高频。

## 为什么这样选型

- **语言 Python**：A股数据库（akshare/tushare/baostock）和券商量化接口（QMT/Ptrade）都是 Python，分析与未来下单能无缝衔接。
- **数据源 akshare**：免费、免 token，开箱即用；通过 `DataSource` 协议隔离，日后可插拔 tushare/baostock。
- **回测自研轻量引擎**：透明、可控、易测；暂不引入 backtrader 等重框架。
- **包管理 uv**：快。

## 分层架构

```
datasource → indicators → strategy → backtest / screener → notify → execution(预留)
```

| 层 | 职责 | 关键约定 |
|----|------|----------|
| `datasource` | 取行情，屏蔽数据提供方差异 | 统一返回 DatetimeIndex(name=date) + open/high/low/close/volume |
| `indicators` | 技术指标，纯函数 | 输入 Series 出 Series，索引对齐，窗口不足为 NaN |
| `strategy` | 价格 → 信号 | **纯函数、无状态**；信号 1 买 / -1 卖 / 0 无 |
| `backtest` | 历史模拟，算绩效 | 输出收益/回撤/胜率/资金曲线 |
| `screener` | 池内扫描买入信号 | 单只失败跳过，不中断 |
| `notify` | 信号外发 | 当前 console，预留钉钉/邮件 |
| `execution` | 下单 | 当前 PaperBroker 模拟盘，预留 QMTBroker |

### 核心设计原则

**策略是纯函数（价格 → 信号），不持有状态、不下单。** 回测、选股、未来实盘共用同一份策略代码，从根上避免"回测与实盘逻辑漂移"。

## 数据流

`datasource` 取数 → `indicators` 算指标 → `strategy` 出信号 → (`backtest` 验证 / `screener` 选股) → `notify` 提醒 →（未来）`execution` 下单。

## 当前实现

- 指标：`sma`（简单移动平均）
- 策略：`golden_cross`（双均线金叉/死叉，默认 5/20）
- 回测假设：全仓进出、信号当根收盘成交、整数股、单边费率
- CLI：`backtest` / `signal` / `screen` 三个子命令

## 回测引擎的已知简化（后续逐步逼近真实）

1. 全仓进出（无仓位管理）
2. 信号当根收盘价成交（轻微前视；可改为次日开盘）
3. 整数股买入（未约束 A股 100 股/手）
4. 单边固定费率（未细分印花税/佣金/过户费、未含滑点）
5. 未处理停牌、涨跌停无法成交等情形

## 路线图

1. 更多指标与策略（MACD/RSI/布林带）
2. 信号推送（钉钉/企业微信/邮件）
3. 配置文件化（TOML）+ 行情本地缓存
4. 回测引擎增强（次日成交、仓位管理、滑点、涨跌停约束）
5. 第二阶段：接入券商 QMT/Ptrade 实盘下单
