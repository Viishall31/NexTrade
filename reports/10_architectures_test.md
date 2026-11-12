# Step 10 — all three architectures trade the test year (2024-04-30 → 2025-04-07)

Daily models, tuned, 5-seed ensembles. Start **Rs 1,000,000**. Same costs, same cash yield, same rule search on validation for every architecture; the test year is traded once.

## A. Each architecture with its own validation-selected rules

| Model | Test accuracy | Test macro-F1 | Instrument | Frozen rule | Validation final | **Test final** | Test return | Max DD | Trades | Costs |
|---|---|---|---|---|---|---|---|---|---|---|
| LSTM | 0.793 | 0.621 | ETF + cash | `risk_off|confirm1|conf0.6|stop5` | Rs 1,420,871 | **Rs 970,051** | -3.0% | -13.0% | 9 | Rs 9,156 |
| LSTM | 0.793 | 0.621 | futures (idealized) | `ls_risk_off|confirm1|conf0.6|stop5` | Rs 1,549,352 | **Rs 983,903** | -1.6% | -13.2% | 9 | Rs 8,361 |
| CNN-BiLSTM-Attention | 0.841 | 0.580 | ETF + cash | `risk_off|confirm1|conf0|stop5` | Rs 1,349,134 | **Rs 962,903** | -3.7% | -11.8% | 7 | Rs 7,052 |
| CNN-BiLSTM-Attention | 0.841 | 0.580 | futures (idealized) | `ls_spec|confirm3|conf0|nostop` | Rs 1,542,490 | **Rs 1,066,782** | +6.7% | -8.0% | 6 | Rs 5,557 |
| Transformer | 0.879 | 0.836 | ETF + cash | `risk_off|confirm2|conf0|stop5` | Rs 1,404,106 | **Rs 929,569** | -7.0% | -13.0% | 8 | Rs 7,831 |
| Transformer | 0.879 | 0.836 | futures (idealized) | `ls_risk_off|confirm3|conf0|nostop` | Rs 1,515,768 | **Rs 884,083** | -11.6% | -17.5% | 5 | Rs 9,132 |
| *Buy & hold ETF* | – | – | ETF | – | Rs 1,300,325 | Rs 981,776 | -1.8% | -15.7% | 1 | Rs 1,000 |
| *Cash at 6%* | – | – | liquid fund | – | Rs 1,141,670 | Rs 1,055,109 | +5.5% | 0.0% | 0 | – |

## B. Same rules for every architecture (differences come from the models only)

| Rule | LSTM | CNN-BiLSTM-Attention | Transformer |
|---|---|---|---|
| spec rule (`spec|confirm1|conf0|nostop`) | Rs 937,969 (-6.2%, DD -11.7%) | Rs 1,008,033 (+0.8%, DD -9.3%) | Rs 921,122 (-7.9%, DD -10.0%) |
| transformer's frozen long-only rule (`risk_off|confirm2|conf0|stop5`) | Rs 955,673 (-4.4%, DD -12.9%) | Rs 1,006,310 (+0.6%, DD -9.8%) | Rs 929,569 (-7.0%, DD -13.0%) |

## Summary

- Most money left (own rules, ETF): **LSTM — Rs 970,051** (-3.0%).
- Buy & hold: Rs 981,776; cash at 6%: Rs 1,055,109.
- Profitable (ended above Rs 10,00,000): CNN-BiLSTM-Attention long short.
- Beat buy & hold: LSTM long short, CNN-BiLSTM-Attention long short.

Trade logs: `reports/10_trades_daily_<arch>_long_only.csv`. Long/short is idealized (spot prices, fractional contracts).