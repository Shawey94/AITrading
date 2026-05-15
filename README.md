# Trading Strategy
**量化交易策略**

Automated systematic trading.

自动化系统交易。

## 收益曲线 / Equity Curve

![Equity Curve](charts/tsla_equity.png)

> 数据：
> - Live：[`data/daily_total_value_live.csv`](data/daily_total_value_live.csv)（当前活跃 — 2026-05 起实盘）
> - Paper：[`data/daily_total_value_paper.csv`](data/daily_total_value_paper.csv)（历史归档，2026-04 至 2026-05-14）
>
> 重画：`python3 scripts/plot_equity_curve.py --source data/daily_total_value_<paper|live>.csv`

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

`data/daily_total_value_{paper,live}.csv` 列：

| 字段 | 含义 |
|---|---|
| `date` | 交易日 |
| `total_value` | 当日盘后总市值 |
| `daily_return` | 时间加权日度收益率（已扣除当日 Injection） |
| `initial_value` | **STARTING_CAPITAL + 累计 Injection**（不含 profit 盈利）|
| `Injection` | 当日补仓注入金额（$）；无注入则 0 |
| `P/L` | 累计盈亏金额 = `total_value − initial_value` |
| `P/L_percent` | `P/L / initial_value` |
| `MaxDrawDown` | 截至当日的历史最大回撤 |
| `SharpeRatio` | 截至当日的年化夏普比率，样本不足 20 个交易日时留空 |

**Time-weighted daily_return**（即 `daily_return = (V_t − I_t − V_{t-1}) / V_{t-1}`）：

$$r_t = \frac{V_t - I_t - V_{t-1}}{V_{t-1}}$$

其中 $V_t$ 为第 $t$ 日的 `total_value`，$I_t$ 为当日 `Injection`（来自源 CSV 的 `ddi_total_injected` 增量）。补仓日 $I_t > 0$，不会被算作收益。

## 默认参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| 起始本金 | `2000.00` | `STARTING_CAPITAL`（live 与 paper 相同；脚本里硬编码） |
| 年化无风险利率 | `0.0368` | `RF_ANNUAL`（US 3M T-bill, 2026-05-01；季度同步一次） |
| 年化交易日数 | `252` | `TRADING_DAYS` |
| 夏普最小样本 | `20` | `MIN_DAYS_FOR_SHARPE` |
