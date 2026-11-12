# Step 10 — trading rule search (daily, cnn_bilstm_attn), validation 2021-12-31 → 2024-04-30

Start Rs 1,000,000. Buy & hold ends at Rs 1,300,325 (max DD -16.5%); cash at 6% ends at Rs 1,141,670.

## long_only — Nifty 50 ETF + cash

42 rules searched, 42 with drawdown no worse than buy & hold. **Selected: `risk_off|confirm1|conf0|stop5`**

| Rank | Rule | Final capital | Return | Max DD | Sharpe | Trades | Costs | Time in market |
|---|---|---|---|---|---|---|---|---|
| 1 | `risk_off|confirm1|conf0|stop5` ✅ | Rs 1,349,134 | 34.9% | -8.5% | 0.86 | 11 | Rs 11,206 | 65% |
| 2 | `risk_off|confirm3|conf0|nostop` | Rs 1,348,851 | 34.9% | -11.1% | 0.80 | 5 | Rs 5,191 | 76% |
| 3 | `spec|confirm3|conf0|nostop` | Rs 1,335,012 | 33.5% | -6.6% | 0.91 | 16 | Rs 8,375 | 77% |
| 4 | `risk_off|confirm2|conf0|stop5` | Rs 1,330,306 | 33.0% | -7.2% | 0.80 | 11 | Rs 11,449 | 64% |
| 5 | `spec|confirm2|conf0|stop5` | Rs 1,327,437 | 32.7% | -5.7% | 0.91 | 22 | Rs 12,114 | 67% |
| 6 | `risk_off|confirm1|conf0.6|stop5` | Rs 1,326,253 | 32.6% | -6.6% | 0.80 | 9 | Rs 9,420 | 63% |
| 7 | `spec|confirm3|conf0|stop5` | Rs 1,322,574 | 32.3% | -7.5% | 0.87 | 18 | Rs 10,561 | 77% |
| 8 | `spec|confirm3|conf0.6|nostop` | Rs 1,320,784 | 32.1% | -6.6% | 0.85 | 16 | Rs 8,323 | 77% |
| 9 | `risk_off|confirm2|conf0.6|nostop` | Rs 1,320,730 | 32.1% | -11.5% | 0.71 | 5 | Rs 5,155 | 76% |
| 10 | `spec|confirm2|conf0|nostop` | Rs 1,319,787 | 32.0% | -7.0% | 0.84 | 20 | Rs 9,860 | 78% |
| – | *buy & hold* | Rs 1,300,325 | 30.0% | -16.5% | 0.48 | 1 | Rs 1,000 | 100% |

## long_short — Nifty futures, idealized (no lot size, spot price)

30 rules searched, 29 with drawdown no worse than buy & hold. **Selected: `ls_spec|confirm3|conf0|nostop`**

| Rank | Rule | Final capital | Return | Max DD | Sharpe | Trades | Costs | Time in market |
|---|---|---|---|---|---|---|---|---|
| 1 | `ls_spec|confirm3|conf0|nostop` ✅ | Rs 1,542,490 | 54.2% | -9.4% | 1.20 | 17 | Rs 21,873 | 98% |
| 2 | `ls_risk_off|confirm3|conf0|nostop` | Rs 1,534,707 | 53.5% | -14.2% | 1.07 | 8 | Rs 23,059 | 100% |
| 3 | `ls_spec|confirm3|conf0.6|nostop` | Rs 1,495,135 | 49.5% | -10.9% | 1.10 | 16 | Rs 20,430 | 97% |
| 4 | `ls_spec|confirm2|conf0|nostop` | Rs 1,478,237 | 47.8% | -12.5% | 1.04 | 21 | Rs 22,837 | 98% |
| 5 | `ls_spec|confirm3|conf0.6|stop5` | Rs 1,475,937 | 47.6% | -9.2% | 1.05 | 19 | Rs 20,008 | 93% |
| 6 | `ls_spec|confirm2|conf0.6|nostop` | Rs 1,457,137 | 45.7% | -10.3% | 0.99 | 17 | Rs 20,880 | 98% |
| 7 | `ls_risk_off|confirm2|conf0|nostop` | Rs 1,449,369 | 44.9% | -17.6% | 0.87 | 12 | Rs 23,762 | 100% |
| 8 | `ls_risk_off|confirm2|conf0.6|nostop` | Rs 1,448,732 | 44.9% | -14.9% | 0.88 | 8 | Rs 22,077 | 100% |
| 9 | `ls_risk_off|confirm3|conf0.6|nostop` | Rs 1,441,300 | 44.1% | -16.4% | 0.87 | 7 | Rs 21,474 | 99% |
| 10 | `ls_risk_off|confirm2|conf0|stop5` | Rs 1,437,097 | 43.7% | -11.9% | 0.88 | 20 | Rs 21,916 | 87% |
| – | *buy & hold* | Rs 1,300,325 | 30.0% | -16.5% | 0.48 | 1 | Rs 1,000 | 100% |