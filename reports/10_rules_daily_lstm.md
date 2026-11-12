# Step 10 — trading rule search (daily, lstm), validation 2021-12-31 → 2024-04-30

Start Rs 1,000,000. Buy & hold ends at Rs 1,300,325 (max DD -16.5%); cash at 6% ends at Rs 1,141,670.

## long_only — Nifty 50 ETF + cash

42 rules searched, 42 with drawdown no worse than buy & hold. **Selected: `risk_off|confirm1|conf0.6|stop5`**

| Rank | Rule | Final capital | Return | Max DD | Sharpe | Trades | Costs | Time in market |
|---|---|---|---|---|---|---|---|---|
| 1 | `risk_off|confirm1|conf0.6|stop5` ✅ | Rs 1,420,871 | 42.1% | -8.7% | 1.10 | 11 | Rs 11,603 | 67% |
| 2 | `risk_off|confirm2|conf0|stop5` | Rs 1,409,873 | 41.0% | -8.7% | 1.06 | 11 | Rs 11,549 | 67% |
| 3 | `risk_off|confirm1|conf0|stop5` | Rs 1,393,983 | 39.4% | -9.5% | 1.01 | 11 | Rs 11,386 | 66% |
| 4 | `spec|confirm1|conf0.6|stop5` | Rs 1,351,750 | 35.2% | -5.4% | 1.02 | 25 | Rs 12,682 | 71% |
| 5 | `spec|confirm1|conf0|stop5` | Rs 1,335,111 | 33.5% | -5.4% | 0.93 | 27 | Rs 13,111 | 77% |
| 6 | `spec|confirm2|conf0|stop5` | Rs 1,335,050 | 33.5% | -5.4% | 0.93 | 25 | Rs 12,506 | 71% |
| 7 | `risk_off|confirm2|conf0.6|stop5` | Rs 1,329,084 | 32.9% | -9.1% | 0.75 | 13 | Rs 13,360 | 72% |
| 8 | `risk_off|confirm3|conf0.6|nostop` | Rs 1,325,119 | 32.5% | -9.8% | 0.71 | 9 | Rs 9,001 | 76% |
| 9 | `spec|confirm3|conf0.6|nostop` | Rs 1,317,328 | 31.7% | -6.6% | 0.83 | 24 | Rs 11,279 | 79% |
| 10 | `risk_off|confirm1|conf0.6|nostop` | Rs 1,315,480 | 31.5% | -11.0% | 0.68 | 9 | Rs 9,016 | 76% |
| – | *buy & hold* | Rs 1,300,325 | 30.0% | -16.5% | 0.48 | 1 | Rs 1,000 | 100% |

## long_short — Nifty futures, idealized (no lot size, spot price)

30 rules searched, 30 with drawdown no worse than buy & hold. **Selected: `ls_risk_off|confirm1|conf0.6|stop5`**

| Rank | Rule | Final capital | Return | Max DD | Sharpe | Trades | Costs | Time in market |
|---|---|---|---|---|---|---|---|---|
| 1 | `ls_risk_off|confirm1|conf0.6|stop5` ✅ | Rs 1,549,352 | 54.9% | -9.8% | 1.13 | 22 | Rs 25,653 | 91% |
| 2 | `ls_risk_off|confirm2|conf0|stop5` | Rs 1,532,084 | 53.2% | -10.3% | 1.10 | 22 | Rs 24,920 | 90% |
| 3 | `ls_risk_off|confirm2|conf0.6|stop5` | Rs 1,494,873 | 49.5% | -10.4% | 1.01 | 22 | Rs 24,411 | 90% |
| 4 | `ls_spec|confirm1|conf0|nostop` | Rs 1,494,112 | 49.4% | -8.5% | 1.08 | 27 | Rs 26,266 | 97% |
| 5 | `ls_risk_off|confirm3|conf0.6|nostop` | Rs 1,493,744 | 49.4% | -11.3% | 0.97 | 16 | Rs 25,433 | 100% |
| 6 | `ls_risk_off|confirm1|conf0|stop5` | Rs 1,491,922 | 49.2% | -9.3% | 1.00 | 24 | Rs 25,566 | 90% |
| 7 | `ls_spec|confirm3|conf0.6|nostop` | Rs 1,487,947 | 48.8% | -8.4% | 1.07 | 25 | Rs 24,582 | 97% |
| 8 | `ls_spec|confirm1|conf0.6|nostop` | Rs 1,478,475 | 47.8% | -9.9% | 1.05 | 25 | Rs 25,428 | 97% |
| 9 | `ls_spec|confirm1|conf0|stop5` | Rs 1,469,253 | 46.9% | -8.5% | 1.03 | 29 | Rs 26,190 | 94% |
| 10 | `ls_spec|confirm1|conf0.6|stop5` | Rs 1,467,381 | 46.7% | -8.8% | 1.04 | 28 | Rs 25,361 | 94% |
| – | *buy & hold* | Rs 1,300,325 | 30.0% | -16.5% | 0.48 | 1 | Rs 1,000 | 100% |