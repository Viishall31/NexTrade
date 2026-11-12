# Step 12 — forward test on fresh data: findings (for the report)

Numbers: `12_fresh_results.md` · Data check: `12_fresh_data.json` · Charts: `12_fresh_equity.png`, `12_fresh_regimes.png`

## Why this test matters
Experiment 2 (the probability rulebook) was designed after the test-year results had been seen, so its test-year
profit could be hindsight. The project files end on 7 Apr 2025, so 8 Apr 2025 – 15 Sep 2026 (354 trading days)
is data that no model, rule or design decision has ever touched. Everything was run **frozen**: scaler, HMM, tuned
models, Experiment 1 rules, Experiment 2 rulebook.

## Data
- Source: yfinance ^NSEI daily bars, cached in `data/raw/yfinance_nsei_daily.csv`.
- Check on 2,413 overlapping days: close differs from the vendor data by a median 0.024% (official close vs last
  traded price), daily return correlation 0.998.
- Dropped the 21 Oct 2025 Muhurat session (as Step 1 does) and the incomplete 16 Sep 2026 bar. Kept 3 Nov 2025
  (normal prices, glitchy volume).
- Integrity: every feature and label up to 7 Apr 2025 is identical to the earlier files.
- Market: Nifty 22,203 → 23,119 (+4.0%). Buy & hold drawdown −15.2%. Frozen-HMM labels: bull 190, sideways 88,
  bear 72, high-vol 4. This period is bull-dominated, unlike the sideways-labelled test year.

## Classification holds up for the Transformer only
| Model | Test year macro-F1 | Fresh macro-F1 |
|---|---|---|
| LSTM | 0.621 | 0.495 |
| CNN-BiLSTM-Attention | 0.580 | 0.419 |
| Transformer | 0.836 | **0.652** (accuracy 0.811) |

## Trading: the test-year ranking reverses
| System | Test year | Fresh period |
|---|---|---|
| Exp 2 rulebook (all 9 versions) | 6 of 9 profitable | **0 of 9 profitable** |
| Exp 1 rules (all 6 versions) | 1 of 6 profitable | 5 of 6 profitable |
| Best realistic system | Rs 10,21,018 (LSTM, rulebook tuned) | **Rs 11,24,388 (CNN, Exp 1 rules)** |
| Buy & hold / cash at 6% | Rs 9,81,776 / Rs 10,55,109 | Rs 10,40,165 / Rs 10,85,297 |

- The rulebook lost money for every model. It sat in cash through the April – June 2025 rebound (it needs P(bull) ≥
  the threshold for 2 days after a bear phase) and was about 50–60% invested in a rising market.
- The CNN-BiLSTM-Attention with its Experiment 1 rule was the only realistic system to beat buy & hold and cash.
  It had positive trading P&L (+Rs 1,06,102 excluding interest), and its timing beat holding the same average exposure
  without signals. Its key move: it exited before the March 2026 fall and re-entered for the July 2026 rise.
- All 15 systems had smaller drawdowns than buy & hold.

## Both unseen periods together (May 2024 – Sep 2026, chained from Rs 10 lakh)
| System | Test year × fresh | vs buy & hold (Rs 10,21,208) | vs cash (Rs 11,45,107) |
|---|---|---|---|
| CNN, Exp 1, futures (idealized) | Rs 12,12,346 | ✓ | ✓ |
| CNN, Exp 1, ETF | Rs 10,82,677 | ✓ | ✗ |
| LSTM, Exp 1, futures (idealized) | Rs 10,44,646 | ✓ | ✗ |
| LSTM, Exp 1, ETF | Rs 10,01,101 | ✗ | ✗ |
| Best Exp 2 rulebook (Transformer, tuned ETF) | Rs 9,99,592 | ✗ | ✗ |
| Transformer, Exp 1, ETF (the pre-registered choice) | Rs 9,36,382 | ✗ | ✗ |

## Conclusions
1. **The Experiment 2 test-year profit did not survive fresh data.** It was the result of fitting rules to one
   period, which is exactly the hindsight risk flagged when the rulebook was built.
2. **No realistic (ETF) system is profitable in both unseen periods.** Results depend on the market type (sideways/declining vs bull
   with sharp corrections). The only system profitable in both is idealized: CNN-BiLSTM-Attention, Exp 1 futures (Rs 10,66,782 and
   Rs 11,36,452), which depends on spot prices, fractional contracts and interest on the full collateral.
3. **The CNN-BiLSTM-Attention is the most promising trader across both periods**, while being the weakest classifier
   of the three. It is the only model whose realistic (ETF) system beat buy & hold over the full 2.4 years, though
   not cash at 6%.
4. **Classification quality and trading value are not aligned.** The Transformer classifies best in both periods and
   trades worst. The HMM labels lag the market, so copying them faithfully means acting late.
5. **The one consistent benefit is risk reduction:** every realistic (ETF) system had a smaller drawdown than buy & hold
   in both unseen periods (all 15 systems on fresh data; in the test year one idealized futures system, the Transformer's
   Exp 1 rule, fell further: −17.5% vs −15.7%).
