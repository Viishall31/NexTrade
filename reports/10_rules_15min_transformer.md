# Step 10 — trading rule search (15min), validation 2021-12-31 → 2024-04-30

Start Rs 1,000,000. Buy & hold ends at Rs 1,300,325 (max DD -16.9%); cash at 6% ends at Rs 1,141,670.

## long_only — Nifty 50 ETF + cash

42 rules searched, 40 with drawdown no worse than buy & hold. **Selected: `risk_off|confirm1|conf0.6|stop5`**

| Rank | Rule | Final capital | Return | Max DD | Sharpe | Trades | Costs | Time in market |
|---|---|---|---|---|---|---|---|---|
| 1 | `risk_off|confirm1|conf0.6|stop5` ✅ | Rs 1,306,920 | 30.7% | -11.6% | 0.82 | 35 | Rs 37,874 | 70% |
| 2 | `risk_off|confirm1|conf0.6|nostop` | Rs 1,289,162 | 28.9% | -12.4% | 0.74 | 33 | Rs 35,501 | 71% |
| 3 | `risk_off|confirm4|conf0.6|stop5` | Rs 1,278,778 | 27.9% | -12.1% | 0.72 | 29 | Rs 31,536 | 68% |
| 4 | `risk_off|confirm12|conf0.6|stop5` | Rs 1,274,075 | 27.4% | -13.8% | 0.70 | 19 | Rs 20,342 | 68% |
| 5 | `spec|confirm1|conf0.6|stop5` | Rs 1,272,173 | 27.2% | -10.2% | 0.75 | 72 | Rs 43,427 | 71% |
| 6 | `spec|confirm4|conf0.6|stop5` | Rs 1,270,090 | 27.0% | -10.8% | 0.76 | 62 | Rs 37,942 | 69% |
| 7 | `risk_off|confirm4|conf0.6|nostop` | Rs 1,262,747 | 26.3% | -12.7% | 0.64 | 27 | Rs 29,211 | 69% |
| 8 | `risk_off|confirm12|conf0.6|nostop` | Rs 1,250,279 | 25.0% | -14.4% | 0.57 | 15 | Rs 15,878 | 70% |
| 9 | `spec|confirm12|conf0.6|stop5` | Rs 1,249,417 | 24.9% | -12.3% | 0.64 | 40 | Rs 27,575 | 69% |
| 10 | `spec|confirm1|conf0.6|nostop` | Rs 1,243,863 | 24.4% | -11.7% | 0.59 | 71 | Rs 41,999 | 72% |
| – | *buy & hold* | Rs 1,300,325 | 30.0% | -16.9% | 0.56 | 1 | Rs 1,000 | 100% |

## long_short — Nifty futures, idealized (no lot size, spot price)

30 rules searched, 19 with drawdown no worse than buy & hold. **Selected: `ls_risk_off|confirm1|conf0.6|nostop`**

| Rank | Rule | Final capital | Return | Max DD | Sharpe | Trades | Costs | Time in market |
|---|---|---|---|---|---|---|---|---|
| 1 | `ls_risk_off|confirm1|conf0.6|nostop` ✅ | Rs 1,374,980 | 37.5% | -13.7% | 0.79 | 47 | Rs 42,258 | 100% |
| 2 | `ls_risk_off|confirm4|conf0.6|nostop` | Rs 1,336,604 | 33.7% | -15.7% | 0.67 | 39 | Rs 37,878 | 100% |
| 3 | `ls_spec|confirm1|conf0.6|nostop` | Rs 1,336,240 | 33.6% | -13.2% | 0.71 | 71 | Rs 42,901 | 99% |
| 4 | `ls_spec|confirm4|conf0.6|nostop` | Rs 1,329,937 | 33.0% | -16.6% | 0.68 | 61 | Rs 39,598 | 99% |
| 5 | `ls_risk_off|confirm1|conf0.6|stop5` | Rs 1,325,513 | 32.6% | -17.8% | 0.66 | 53 | Rs 42,317 | 97% |
| 6 | `ls_risk_off|confirm12|conf0.6|nostop` | Rs 1,306,163 | 30.6% | -22.2% | 0.59 | 19 | Rs 28,023 | 100% |
| 7 | `ls_spec|confirm12|conf0.6|nostop` | Rs 1,279,980 | 28.0% | -23.2% | 0.52 | 38 | Rs 29,748 | 99% |
| 8 | `ls_spec|confirm1|conf0.6|stop5` | Rs 1,255,470 | 25.5% | -15.8% | 0.46 | 75 | Rs 41,322 | 96% |
| 9 | `ls_prob_weighted|confirm1|conf0|stop5` | Rs 1,237,844 | 23.8% | -8.9% | 0.59 | 292 | Rs 38,403 | 100% |
| 10 | `ls_prob_weighted|confirm1|conf0|nostop` | Rs 1,237,844 | 23.8% | -8.9% | 0.59 | 292 | Rs 38,403 | 100% |
| – | *buy & hold* | Rs 1,300,325 | 30.0% | -16.9% | 0.56 | 1 | Rs 1,000 | 100% |