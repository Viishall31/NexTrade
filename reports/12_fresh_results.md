# Step 12 — forward test on fresh data (2025-04-07 → 2026-09-15, 354 trading days)

Data that did not exist in the project files (yfinance ^NSEI, after Nifty50_test.csv ends). **Nothing was changed**: frozen scaler, frozen HMM, tuned daily models, frozen Experiment 1 rules and frozen Experiment 2 rulebook. Frozen-HMM labels in this period: {'bull': 190, 'sideways': 88, 'bear': 72, 'high_vol': 4}. Nifty 22,203 → 23,119.

## Classification

| Model | Test year accuracy | Test year macro-F1 | **Fresh accuracy** | **Fresh macro-F1** | Predicted (fresh) |
|---|---|---|---|---|---|
| LSTM | 0.793 | 0.621 | **0.703** | **0.495** | {'bull': 181, 'sideways': 118, 'bear': 46, 'high_vol': 9} |
| CNN-BiLSTM-Attention | 0.841 | 0.580 | **0.630** | **0.419** | {'bull': 181, 'sideways': 108, 'bear': 58, 'high_vol': 7} |
| Transformer | 0.879 | 0.836 | **0.811** | **0.652** | {'bull': 203, 'sideways': 79, 'bear': 54, 'high_vol': 18} |

## Trading from Rs 1,000,000

Benchmarks on fresh data: **buy & hold Rs 1,040,165 (+4.0%, max DD -15.2%)**, **cash at 6% Rs 1,085,297 (+8.5%)**. *futures = idealized.

| Model | System | Test year final | **Fresh: amount left** | Profit | of which interest | **Trading P&L** | Max DD | Trades | Avg exposure | Same exposure, no signals |
|---|---|---|---|---|---|---|---|---|---|---|
| LSTM | Exp 1 rules, ETF | Rs 970,051 | **Rs 1,032,009** | Rs 32,009 (+3.2%) | Rs 14,570 | **Rs 17,439** | -11.1% | 9 | 84% | Rs 1,050,038 |
| LSTM | Exp 1 rules, futures* | Rs 983,903 | **Rs 1,061,737** | Rs 61,737 (+6.2%) | Rs 91,066 | **Rs -29,329** | -12.4% | 11 | 94% | Rs 1,044,652 |
| LSTM | Exp 2 rulebook default, ETF | Rs 992,193 | **Rs 930,077** | Rs -69,923 (-7.0%) | Rs 33,765 | **Rs -103,688** | -12.2% | 12 | 58% | Rs 1,062,489 |
| LSTM | Exp 2 rulebook tuned, ETF | Rs 1,021,018 | **Rs 961,420** | Rs -38,580 (-3.9%) | Rs 32,236 | **Rs -70,816** | -7.8% | 4 | 60% | Rs 1,061,442 |
| LSTM | Exp 2 rulebook tuned, futures* | Rs 949,524 | **Rs 928,228** | Rs -71,772 (-7.2%) | Rs 79,564 | **Rs -151,337** | -9.6% | 18 | 70% | Rs 1,056,929 |
| CNN-BiLSTM-Attention | Exp 1 rules, ETF | Rs 962,903 | **Rs 1,124,388** | Rs 124,388 (+12.4%) | Rs 18,286 | **Rs 106,102** | -6.7% | 7 | 80% | Rs 1,051,926 |
| CNN-BiLSTM-Attention | Exp 1 rules, futures* | Rs 1,066,782 | **Rs 1,136,452** | Rs 136,452 (+13.6%) | Rs 91,245 | **Rs 45,207** | -5.8% | 14 | 83% | Rs 1,050,403 |
| CNN-BiLSTM-Attention | Exp 2 rulebook default, ETF | Rs 1,004,727 | **Rs 961,066** | Rs -38,934 (-3.9%) | Rs 40,436 | **Rs -79,369** | -8.8% | 17 | 51% | Rs 1,065,873 |
| CNN-BiLSTM-Attention | Exp 2 rulebook tuned, ETF | Rs 1,006,074 | **Rs 953,172** | Rs -46,828 (-4.7%) | Rs 37,732 | **Rs -84,560** | -9.2% | 19 | 54% | Rs 1,064,484 |
| CNN-BiLSTM-Attention | Exp 2 rulebook tuned, futures* | Rs 1,025,999 | **Rs 971,386** | Rs -28,614 (-2.9%) | Rs 83,503 | **Rs -112,117** | -9.7% | 23 | 60% | Rs 1,061,639 |
| Transformer | Exp 1 rules, ETF | Rs 929,569 | **Rs 1,007,329** | Rs 7,329 (+0.7%) | Rs 18,774 | **Rs -11,445** | -6.2% | 4 | 77% | Rs 1,053,358 |
| Transformer | Exp 1 rules, futures* | Rs 884,083 | **Rs 982,703** | Rs -17,297 (-1.7%) | Rs 78,926 | **Rs -96,223** | -11.0% | 6 | 97% | Rs 1,042,962 |
| Transformer | Exp 2 rulebook default, ETF | Rs 990,485 | **Rs 951,128** | Rs -48,872 (-4.9%) | Rs 34,048 | **Rs -82,920** | -8.8% | 13 | 58% | Rs 1,062,489 |
| Transformer | Exp 2 rulebook tuned, ETF | Rs 1,019,525 | **Rs 980,449** | Rs -19,551 (-2.0%) | Rs 29,254 | **Rs -48,805** | -7.4% | 4 | 64% | Rs 1,059,581 |
| Transformer | Exp 2 rulebook tuned, futures* | Rs 1,019,884 | **Rs 881,300** | Rs -118,700 (-11.9%) | Rs 76,982 | **Rs -195,683** | -12.0% | 19 | 74% | Rs 1,054,913 |

## Scorecard

| Question | All 15 systems | Realistic (ETF) 9 systems |
|---|---|---|
| Ended with a profit | 5 | 3 |
| Beat buy & hold (Rs 1,040,165) | 3 | 1 |
| Beat cash at 6% (Rs 1,085,297) | 2 | 1 |
| Positive trading P&L (excl. interest) | 3 | 2 |
| Timing beat same exposure without signals | 3 | 1 |
| Smaller drawdown than buy & hold (-15.2%) | 15 | 9 |

'Same exposure, no signals' holds the system's average exposure every day with no timing (costs ignored) — it separates the value of buy/sell timing from simply being less invested.
Trade logs: `reports/12_trades_fresh_<arch>_<system>.csv`.