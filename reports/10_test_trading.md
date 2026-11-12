# Step 10 — trading the held-out test year (2024-04-30 → 2025-04-07)

Start: **Rs 1,000,000**. Rules and the recommended system were frozen on validation (Jan 2022 – Apr 2024) before this run. Costs: long-only 0.10% per side + Rs 15.93 per sell; futures 0.03% per side + monthly roll. Idle cash earns 6% p.a.

## Recommended system: daily long only — `risk_off|confirm2|conf0|stop5`

- **Amount at the end: Rs 929,569** (net Rs -70,431, -7.0%)
- Buy & hold the ETF instead: Rs 981,776 (-1.8%); cash at 6%: Rs 1,055,109
- Max drawdown -13.0% (Rs -137,446) vs buy & hold -15.7% (Rs -182,261)
- 8 trades, costs Rs 7,831, interest on idle cash Rs 21,056, invested 58% of the time

## All frozen systems vs benchmarks

| System | Rule | Validation final | **Test final** | Test return | Max DD | Sharpe | Trades | Costs |
|---|---|---|---|---|---|---|---|---|
| **daily_long_only** | `risk_off|confirm2|conf0|stop5` | Rs 1,404,106 | **Rs 929,569** | -7.0% | -13.0% | -1.15 | 8 | Rs 7,831 |
| daily_long_short (idealized) | `ls_risk_off|confirm3|conf0|nostop` | Rs 1,515,768 | **Rs 884,083** | -11.6% | -17.5% | -1.27 | 5 | Rs 9,132 |
| 15min_long_only | `risk_off|confirm1|conf0.6|stop5` | Rs 1,306,920 | **Rs 871,623** | -12.8% | -20.7% | -2.03 | 26 | Rs 25,684 |
| 15min_long_short (idealized) | `ls_risk_off|confirm1|conf0.6|nostop` | Rs 1,374,980 | **Rs 899,013** | -10.1% | -19.9% | -1.44 | 25 | Rs 20,518 |
| *buy & hold ETF* | – | Rs 1,300,325 | Rs 981,776 | -1.8% | -15.7% | -0.47 | 1 | Rs 1,000 |
| *spec exposure rule (Step 7), daily* | `spec|confirm1|conf0|nostop` | – | Rs 921,122 | -7.9% | -10.0% | -1.34 | 13 | Rs 7,325 |
| *cash at 6%* | – | Rs 1,141,670 | Rs 1,055,109 | +5.5% | 0.0% | – | 0 | – |

## Month by month — daily_long_only

| Month end | Equity | Month P&L | Buy & hold equity |
|---|---|---|---|
| May 2024 | Rs 994,541 | Rs -5,459 | Rs 996,837 |
| Jun 2024 | Rs 972,169 | Rs -22,372 | Rs 1,061,343 |
| Jul 2024 | Rs 1,004,717 | Rs 32,547 | Rs 1,103,982 |
| Aug 2024 | Rs 1,016,198 | Rs 11,482 | Rs 1,116,598 |
| Sep 2024 | Rs 1,039,042 | Rs 22,843 | Rs 1,141,697 |
| Oct 2024 | Rs 967,188 | Rs -71,854 | Rs 1,071,083 |
| Nov 2024 | Rs 954,229 | Rs -12,958 | Rs 1,066,973 |
| Dec 2024 | Rs 922,278 | Rs -31,952 | Rs 1,046,122 |
| Jan 2025 | Rs 920,159 | Rs -2,119 | Rs 1,040,238 |
| Feb 2025 | Rs 924,425 | Rs 4,265 | Rs 978,172 |
| Mar 2025 | Rs 928,495 | Rs 4,070 | Rs 1,039,588 |
| Apr 2025 | Rs 929,569 | Rs 1,074 | Rs 981,776 |

Trade-by-trade logs: `reports/10_trades_<system>.csv`.
Long/short systems are idealized: spot index prices instead of futures prices, fractional contracts (one real Nifty lot is worth more than Rs 10 lakh), no margin calls.