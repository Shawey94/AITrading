# Adaptive Leveraged ETF Hedging Strategy
**自适应杠杆 ETF 对冲策略**

Dynamically rebalances between paired bull/bear leveraged ETFs, using moving-average signals to tilt exposure toward short-term
momentum. Includes adaptive thresholds, drawdown-triggered response mechanism, and profit reset.

在标的的牛/熊杠杆 ETF 之间动态调仓，基于均线信号倾向短期趋势方向。
内置自适应阈值引擎、回撤应对机制和止盈重置。

---

## Stack / 技术栈
- Alpaca Markets (paper + live) · WebSocket + REST
- Python · Daily-bar backtest sharing live signal logic
- Multi-strategy orchestration on a single API client

## Status / 状态
- ✅ Backtest / 回测
- ✅ Live via WebSocket (paper-tested) / 实盘 (纸面验证)
- 🚧 Monitoring dashboard / 监控面板

## Caveats / 风险提示
⚠️ Leveraged ETFs · hedged ≠ risk-free · backtest ≠ future · educational use only
⚠️ 杠杆 ETF · 对冲非无风险 · 回测非未来 · 仅供学习

## Disclaimer / 免责声明
For research and education only. Not investment advice. No warranty.
Use at your own risk.

仅供研究学习，不构成投资建议。使用者自行承担一切风险。

All Rights Reserved
For educational reference only


## 数据格式

`data/daily_total_value.csv` 字段如下：

| 字段 | 含义 | 说明 |
|---|---|---|
| `date` | 交易日 | 格式 `YYYY-MM-DD`，仅记录实际交易日，不补节假日 |
| `total_value` | 当日盘后总市值 | 从本地 Excel 的 `total_value` 列读取最后一个非空值 |
| `daily_return` | 当日收益率 | 相对前一交易日的简单收益率，首日为 0 |
| `initial_value` | 起始本金 | 全表恒定，第一次运行脚本时写入后不再变 |
| `P/L` | 累计盈亏（金额） | `total_value − initial_value` |
| `MaxDrawDown` | 截至当日的历史最大回撤 | 负数，例如 `-0.0832` 代表 −8.32% |
| `SharpeRatio` | 截至当日的年化夏普比率 | 样本不足 20 个交易日时留空 |

## 指标计算口径

**daily_return**

$$r_t = \frac{V_t - V_{t-1}}{V_{t-1}}$$

其中 $V_t$ 为第 $t$ 个交易日的 `total_value`。首日 $r_0 = 0$。

**P/L**

$$\text{P/L}_t = V_t - V_{\text{initial}}$$

简单的金额差。注意：此口径假设期间**没有入金/出金**。如果中途追加或赎回本金，需改用时间加权收益率（TWR），届时再调整脚本。

**MaxDrawDown**

$$\text{MDD}_t = \min_{s \le t} \frac{V_s - \max_{u \le s} V_u}{\max_{u \le s} V_u}$$

即截至 $t$ 日，历史净值相对其历史峰值的最大跌幅。用负数表示，越接近 0 越好。每天会基于完整历史重算。

**SharpeRatio**

$$\text{Sharpe}_t = \frac{\overline{r - r_f}}{\sigma_{r - r_f}} \cdot \sqrt{252}$$

其中 $r_f$ 为日度无风险利率（默认 0），样本为开仓至 $t$ 日的全部 `daily_return`。年化系数 252（按 A 股/美股交易日数；加密货币改 365）。**样本少于 20 个交易日时留空**，因为统计意义不足。

### 默认参数

| 参数 | 默认值 | 在脚本中的位置 |
|---|---|---|
| 起始本金 | `1_000_000.00` | `INITIAL_VALUE` |
| 年化无风险利率 | `0.0` | `RF_ANNUAL` |
| 年化交易日数 | `252` | `TRADING_DAYS` |
| 夏普最小样本 | `20` | `MIN_DAYS_FOR_SHARPE` |



