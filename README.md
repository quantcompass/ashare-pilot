# ashare-pilot

A股策略研究与信号系统 —— quantcompass 旗下项目。

> ⚠️ **风险提示**：本项目用于策略研究与学习，不构成投资建议。第一阶段**只做分析、信号与回测，不做真实下单**。任何实盘交易请自行承担风险，并先经过充分的回测与模拟盘验证。

## 它能做什么（第一阶段）

- 📈 拉取 A股日线行情（基于 [akshare](https://akshare.akfamily.xyz/)，免费、免 token）
- 📐 计算技术指标（当前：SMA 移动平均）
- 🎯 双均线金叉/死叉策略生成买卖信号
- 🔁 回测：用历史数据验证策略收益、回撤、胜率
- 🔍 选股：扫描自选股池，输出当日买入候选
- 🔔 信号提醒（当前控制台输出，预留钉钉/邮件）
- 🔌 下单接口预留（PaperBroker 模拟盘；真实券商 QMT 日后接入）

## 快速开始

依赖管理用 [uv](https://docs.astral.sh/uv/)。

```bash
# 安装依赖
uv sync

# 回测单只股票（贵州茅台，近两年，双均线 5/20）
uv run ashare-pilot backtest --symbol 600519 --start 20220101 --end 20240101

# 查看单只股票最新信号
uv run ashare-pilot signal --symbol 000001

# 扫描自选股池的当日买入信号
uv run ashare-pilot screen

# 运行测试
uv run pytest
```

## 架构

```
datasource → indicators → strategy → backtest / screener → notify → execution(预留)
   取数         指标         信号        回测 / 选股          提醒        下单
```

**核心设计：策略是纯函数（价格 → 信号），无状态、不下单。** 回测、选股、未来的实盘共用同一套策略代码，避免"回测赚钱、实盘逻辑漂移"的经典坑。

各层职责见 [docs/design.md](docs/design.md)。

## 路线图

- [x] 第一阶段：分析 + 信号 + 回测（当前）
- [ ] 更多指标与策略（MACD、RSI、布林带…）
- [ ] 信号推送（钉钉 / 企业微信 / 邮件）
- [ ] 配置文件化（TOML）+ 数据本地缓存
- [ ] 第二阶段：接入券商 QMT/Ptrade 实盘下单（需券商量化权限）
