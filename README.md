# Trading Strategy
**量化交易策略**

Automated systematic trading.

自动化系统交易。

## 收益曲线 / Equity Curve

![Equity Curve](charts/tsla_equity.png)

> 数据：[`data/daily_total_value.csv`](data/daily_total_value.csv)　·　重画：`python3 scripts/plot_equity_curve.py`

---

## Stack / 技术栈
- Alpaca Markets (paper + live) · WebSocket + REST
- Python · Daily-bar backtest sharing live signal logic

## Status / 状态
- ✅ Backtest / 回测
- ✅ Live via WebSocket (paper-tested) / 实盘 (纸面验证)
- ✅ Monitoring dashboard / 监控面板

## Caveats / 风险提示
- ⚠️ backtest ≠ future · educational use only
- ⚠️ 回测非未来 · 仅供学习

## Disclaimer / 免责声明
For research and education only. Not investment advice. No warranty.
Use at your own risk.

仅供研究学习，不构成投资建议。使用者自行承担一切风险。

All Rights Reserved


## 数据格式

`data/daily_total_value.csv` 列：

| 字段 | 含义 |
|---|---|
| `date` | 交易日 |
| `total_value` | 当日盘后总市值 |
| `daily_return` | 相对前一交易日的简单收益率 |
| `initial_value` | 起始本金 |
| `P/L` | 累计盈亏（金额） |
| `P/L_percent` | 累计盈亏（小数，例如 `-0.0832` 即 −8.32%） |
| `MaxDrawDown` | 截至当日的历史最大回撤 |
| `SharpeRatio` | 截至当日的年化夏普比率，样本不足 20 个交易日时留空 |

## 默认参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| 起始本金 | `2000.00` | `INITIAL_VALUE` |
| 年化无风险利率 | `0.0368` | `RF_ANNUAL`（US 3M T-bill, 2026-05-01；季度同步一次） |
| 年化交易日数 | `252` | `TRADING_DAYS` |
| 夏普最小样本 | `20` | `MIN_DAYS_FOR_SHARPE` |
