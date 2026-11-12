# Step 10 — trading rule search (daily), validation 2021-12-31 → 2024-04-30

Start Rs 1,000,000. Buy & hold ends at Rs 1,300,325 (max DD -16.5%); cash at 6% ends at Rs 1,141,670.

## long_only — Nifty 50 ETF + cash

42 rules searched, 42 with drawdown no worse than buy & hold. **Selected: `risk_off|confirm2|conf0|stop5`**

| Rank | Rule | Final capital | Return | Max DD | Sharpe | Trades | Costs | Time in market |
|---|---|---|---|---|---|---|---|---|
| 1 | `risk_off|confirm2|conf0|stop5` ✅ | Rs 1,404,106 | 40.4% | -5.9% | 1.07 | 9 | Rs 9,550 | 65% |
| 2 | `risk_off|confirm1|conf0|stop5` | Rs 1,400,231 | 40.0% | -6.5% | 1.06 | 9 | Rs 9,452 | 64% |
| 3 | `spec|confirm2|conf0|stop5` | Rs 1,355,680 | 35.6% | -5.4% | 1.05 | 21 | Rs 11,767 | 67% |
| 4 | `risk_off|confirm1|conf0.6|stop5` | Rs 1,354,019 | 35.4% | -5.9% | 0.91 | 9 | Rs 9,501 | 62% |
| 5 | `risk_off|confirm3|conf0|nostop` | Rs 1,340,677 | 34.1% | -9.8% | 0.78 | 7 | Rs 7,097 | 74% |
| 6 | `risk_off|confirm3|conf0|stop5` | Rs 1,336,303 | 33.6% | -9.3% | 0.80 | 11 | Rs 11,474 | 70% |
| 7 | `risk_off|confirm1|conf0.6|nostop` | Rs 1,327,900 | 32.8% | -10.3% | 0.74 | 5 | Rs 5,047 | 75% |
| 8 | `risk_off|confirm3|conf0.6|nostop` | Rs 1,320,529 | 32.1% | -9.9% | 0.72 | 5 | Rs 5,070 | 74% |
| 9 | `risk_off|confirm2|conf0|nostop` | Rs 1,312,520 | 31.3% | -11.4% | 0.69 | 7 | Rs 7,048 | 74% |
| 10 | `risk_off|confirm2|conf0.6|nostop` | Rs 1,311,803 | 31.2% | -10.9% | 0.68 | 5 | Rs 5,036 | 75% |
| – | *buy & hold* | Rs 1,300,325 | 30.0% | -16.5% | 0.48 | 1 | Rs 1,000 | 100% |

## long_short — Nifty futures, idealized (no lot size, spot price)

30 rules searched, 30 with drawdown no worse than buy & hold. **Selected: `ls_risk_off|confirm3|conf0|nostop`**

| Rank | Rule | Final capital | Return | Max DD | Sharpe | Trades | Costs | Time in market |
|---|---|---|---|---|---|---|---|---|
| 1 | `ls_risk_off|confirm3|conf0|nostop` ✅ | Rs 1,515,768 | 51.6% | -11.3% | 1.02 | 10 | Rs 23,667 | 100% |
| 2 | `ls_spec|confirm3|conf0|nostop` | Rs 1,479,870 | 48.0% | -7.8% | 1.03 | 21 | Rs 22,209 | 98% |
| 3 | `ls_risk_off|confirm3|conf0.6|nostop` | Rs 1,462,528 | 46.3% | -11.3% | 0.90 | 8 | Rs 21,899 | 100% |
| 4 | `ls_spec|confirm2|conf0|stop5` | Rs 1,462,070 | 46.2% | -9.5% | 0.99 | 23 | Rs 21,828 | 96% |
| 5 | `ls_spec|confirm2|conf0|nostop` | Rs 1,460,202 | 46.0% | -10.5% | 0.98 | 21 | Rs 21,704 | 98% |
| 6 | `ls_spec|confirm2|conf0.6|nostop` | Rs 1,457,402 | 45.7% | -9.2% | 0.97 | 19 | Rs 21,051 | 98% |
| 7 | `ls_spec|confirm3|conf0.6|nostop` | Rs 1,450,970 | 45.1% | -7.4% | 0.95 | 19 | Rs 21,377 | 98% |
| 8 | `ls_risk_off|confirm1|conf0.6|nostop` | Rs 1,449,008 | 44.9% | -12.4% | 0.87 | 8 | Rs 22,107 | 100% |
| 9 | `ls_risk_off|confirm2|conf0|nostop` | Rs 1,445,991 | 44.6% | -14.4% | 0.86 | 10 | Rs 23,017 | 100% |
| 10 | `ls_risk_off|confirm2|conf0.6|nostop` | Rs 1,436,427 | 43.6% | -13.6% | 0.84 | 8 | Rs 21,543 | 100% |
| – | *buy & hold* | Rs 1,300,325 | 30.0% | -16.5% | 0.48 | 1 | Rs 1,000 | 100% |