# AI-Based Market Regime Detection for Nifty 50 — Project Summary

MPSTME Capstone · Group 17 · Summary of the implementation, results, deviations and limitations.
Detailed reports for every step are in `reports/`; the interactive dashboard is `streamlit run dashboard/app.py`.

---

## 1. What was built
A research pipeline that
1. labels Nifty 50 market regimes (**bull, bear, sideways, high volatility**) with a Gaussian Hidden Markov Model,
2. trains three deep-learning classifiers — **LSTM, CNN-BiLSTM-Attention, Transformer** — to predict the next day's regime
   from the last 30 days of technical indicators,
3. tunes all three with Optuna, selects one on validation data, and tests it once on held-out data,
4. validates the selected model bar-by-bar on 15-minute data (simulated live run),
5. trades on the predictions from Rs 10,00,000 with frozen rules, and
6. forward-tests everything, unchanged, on 17 months of data that did not exist in the project files.

## 2. Data
| Item | Detail |
|---|---|
| Training file | `Nifty50_train.csv`: 57,478 15-min bars, Apr 2015 – Apr 2024 |
| Test file | `Nifty50_test.csv`: 6,014 bars, May 2024 – Apr 2025 |
| Fresh data | yfinance ^NSEI daily bars, 8 Apr 2025 – 15 Sep 2026 (354 days) |
| Cleaning | 1,850 duplicate rows from chunked export removed (kept the first copy; the second had a corrupted 09:15 open); Muhurat/special sessions dropped; vendor EMA/Supertrend columns discarded (they restart at chunk boundaries). Train: 55,575 bars, 2,223 days |
| Features (13) | RSI(14); MACD line, signal, histogram (÷ price); close/EMA 20, 50, 200; ATR(14)/close; ADX(14); Bollinger %B and bandwidth; Stochastic RSI %K, %D |
| Split | Train Feb 2016 – Dec 2021 · Validation Jan 2022 – Apr 2024 · Test = test file · Fresh = yfinance after the test file |
| Leakage controls | All indicators causal (tested); scaler fitted on train only (tested); HMM labels use the forward-filtered posterior (tested); test file untouched until selection was frozen |

## 3. Regime labels (HMM)
- 4-state Gaussian HMM, full covariance, 10 restarts, fitted on train only and frozen.
- Emissions: **20-day log return + 20-day realised volatility** (spec said 1-day return; see §8).
- Checks: Feb–Apr 2020 crash → 69% high-vol + 21% bear; H1 2022 correction → 65% bear; 2023 rally → 72% bull.
- ~9 regime switches per year. BIC prefers 5 states (2012 vs 2542 for 4); 4 kept to match the project definition.

## 4. Models and tuning (validation, 5-seed means)
| Model | Params (tuned) | Default macro-F1 | Tuned macro-F1 | Tuned Sharpe | Tuning objective default → tuned |
|---|---|---|---|---|---|
| LSTM | 342K | 0.631 | 0.685 | 0.70 | 0.619 → 0.637 |
| CNN-BiLSTM-Attention | 366K | 0.689 | 0.762 | 0.67 | 0.647 → 0.680 |
| Transformer | 271K | 0.709 | 0.758 | 0.77 | 0.654 → 0.691 |

- Optuna TPE, 50 trials per model, median pruner, objective 0.6 × macro-F1 + 0.4 × normalised Sharpe.
- The top 3 trials per model were re-run on 5 seeds: single-seed winners (~0.71) fell to 0.63–0.68, so tuning gains would have
  been overstated without this step.
- Most important hyperparameters: learning rate and dropout; model size barely mattered (~1,400 training days).
- **Selection rule (spec 9.3), frozen before testing:** macro-F1 within 2 points of the best, then highest Sharpe → **Transformer**.

## 5. Classification results (5-seed ensembles, accuracy / macro-F1)
| Model | Validation* | Test year | Fresh data |
|---|---|---|---|
| LSTM | 0.803 / 0.687 | 0.793 / 0.621 | 0.703 / 0.495 |
| CNN-BiLSTM-Attention | 0.822 / 0.818 | 0.841 / 0.580 | 0.630 / 0.419 |
| **Transformer** | 0.787 / 0.809 | **0.879 / 0.836** | **0.811 / 0.652** |

\*Validation was also used for early stopping and tuning, so it is optimistic. Baselines on the test year: logistic regression on the
last day's features 0.815 / 0.730; always predicting the majority class gives macro-F1 0.16 on validation.

**15-minute Transformer** (trained on a Colab T4 GPU, tuned daily hyperparameters): validation 0.702 / 0.613. The bar-by-bar replay
of the test file gives 0.518 / 0.412. The replay itself matched the batch pipeline exactly (100% prediction agreement), processed
5,800/5,800 bars, and had a p95 latency of 163 ms (requirement < 2 s).

## 6. Trading results (from Rs 10,00,000; costs included; idle cash earns 6%)
**Experiment 1** — regime-map rules (which regimes to hold, confirmation, confidence filter, 5% stop), searched on validation per model.
**Experiment 2** — probability rulebook: BUY when P(bull) ≥ threshold for N days (50%/100% size), SELL when P(bear)+P(high-vol) ≥ threshold,
never trade on sideways, trailing stop, cooldown. Designed after the Experiment 1 test results were seen, so it is post-hoc.
Parameters were chosen on validation.

### Realistic systems (Nifty ETF + cash)
| Model | System | Test year | Fresh data | Both periods chained |
|---|---|---|---|---|
| LSTM | Exp 1 rules | Rs 9,70,051 | Rs 10,32,009 | Rs 10,01,101 |
| LSTM | Exp 2 rulebook (tuned) | Rs 10,21,018 | Rs 9,61,420 | Rs 9,81,627 |
| CNN-BiLSTM-Attention | Exp 1 rules | Rs 9,62,903 | **Rs 11,24,388** | **Rs 10,82,677** |
| CNN-BiLSTM-Attention | Exp 2 rulebook (tuned) | Rs 10,06,074 | Rs 9,53,172 | Rs 9,58,962 |
| Transformer (selected) | Exp 1 rules | Rs 9,29,569 | Rs 10,07,329 | Rs 9,36,382 |
| Transformer (selected) | Exp 2 rulebook (tuned) | Rs 10,19,525 | Rs 9,80,449 | Rs 9,99,592 |
| *Buy & hold ETF* | | Rs 9,81,776 | Rs 10,40,165 | Rs 10,21,208 |
| *Cash at 6%* | | Rs 10,55,109 | Rs 10,85,297 | Rs 11,45,107 |

Key facts:
- **Test year:** Experiment 1 lost money for every model. Experiment 2 ended slightly positive for most versions, but trading P&L
  excluding interest was negative for all nine versions; the positive balance was interest on idle cash.
- **Fresh data:** the ranking reversed. Experiment 2 lost money for every model; Experiment 1 was profitable for 5 of 6 versions.
  CNN-BiLSTM-Attention with Experiment 1 rules was the only realistic system to beat buy & hold and cash, with genuinely positive
  trading P&L (+Rs 1,06,102).
- **No realistic (ETF) system was profitable in both unseen periods, and none beat cash in either.** The one exception overall is idealized:
  CNN-BiLSTM-Attention, Exp 1 futures (Rs 10,66,782 → Rs 11,36,452; chained Rs 12,12,346), which relies on spot prices, fractional contracts
  and 6% interest on the full collateral.
- Every realistic (ETF) system had a smaller drawdown than buy & hold in both periods
  (test year −6.6% to −13.0% vs −15.7%; fresh −6.2% to −12.2% vs −15.2%). One idealized futures system did not (Transformer, Exp 1: −17.5% in the test year).

## 7. Conclusions
1. **Regime classification works.** The selected Transformer reproduces the HMM regimes on data it never saw (test 88%, fresh 81% accuracy).
2. **Trading on these regimes is not reliably profitable.** Results depend on the market type, and no realistic (ETF) system was
   profitable in both unseen periods. The best realistic system over 2.4 years (CNN, Exp 1) beat buy & hold but not a 6% liquid fund;
   only an idealized futures version of it beat cash in both periods.
3. **Better classification did not mean better trading.** The HMM labels change after the market moves; the model that copies them
   most faithfully (Transformer) inherits the delay and trades worst, while the weakest classifier (CNN) trades best.
4. **The consistent value is risk reduction:** every realistic system cut the maximum drawdown versus buy & hold, by roughly 15–60%.
5. **Methodology matters:** multi-seed re-runs, validation-only selection, a one-time test and an untouched forward test exposed the
   seed luck in tuning and the post-hoc optimism of Experiment 2.

## 8. Deviations from the specification
| Area | Specification | Implemented | Reason |
|---|---|---|---|
| Features | 15 incl. OBV, VWAP, India VIX | 13 | No volume in index data; VIX not used |
| HMM emissions | 1-day return + 20-day vol | 20-day return + 20-day vol | 1-day returns produced volatility-only states (2023 rally labelled sideways) |
| HMM labels | argmax posterior | Forward-filtered posterior | Smoothed posteriors use future data and cannot be reproduced live |
| Splits | Train 2015–21 / val 2022 / test 2023+ | Train 2016–21 / val 2022 – Apr 2024 / test file | EMA-200 warm-up; separate test file provided |
| Tuning | 50 trials | 50 trials + top-3 re-run on 5 seeds | Seed noise ±0.05 F1 |
| CNN-BiLSTM-Attention heads | Tunable | Not tuned | Spec 6.2 defines additive attention (no heads) |
| 15-min models | All three | Selected Transformer only, daily hyperparameters | CPU budget; trained on Colab |
| Live validation | ≥ 2 weeks on Kite Connect | Bar-by-bar replay of the test file + forward test on fresh daily data | No broker API account |
| Trading | Spec exposure map | Plus Exp 1 rule search and Exp 2 rulebook | Requested by the project guide |

## 9. Limitations
- HMM labels lag turning points and treat slow, calm declines as sideways (Oct 2024 – Mar 2025).
- Few regime episodes per period (~9 switches/year) and rare high-volatility days (2–4%) make per-class metrics noisy.
- The 15-min model overfits within 1–4 epochs and was not tuned for 15-min data.
- Experiment 2 is post-hoc. Futures results are idealized (spot prices, fractional contracts). Costs are approximate.
- Fresh data comes from a different source (yfinance official close vs vendor last traded price; median difference 0.02%).

## 10. Future work
- Label regimes by what the market does next (forward 20-day return/volatility) instead of the lagging causal HMM state.
- Walk-forward retraining (e.g. yearly) to get many out-of-sample years instead of two.
- Tune the 15-min model separately; add genuine volume (Nifty futures) and India VIX features.
- Combine regime signals with a trend or momentum overlay, evaluated on validation only.

## 11. How to reproduce (in order)
```
python scripts/01_clean_data.py
python scripts/02_build_features.py
python scripts/03_label_regimes.py
python scripts/04_train_default_models.py --freq daily
python scripts/05_backtest_default_models.py --freq daily
python scripts/06_tune.py --arch lstm            # also cnn_bilstm_attn, transformer (can run in parallel)
python scripts/06_summarize_tuning.py
python scripts/07_select_model.py
python scripts/07_prepare_test_data.py
python scripts/07_evaluate_test.py
python scripts/08_make_colab_bundle.py           # then run colab/08_train_15min_colab.ipynb on a GPU
python scripts/09_replay.py
python scripts/10_make_signals.py --freq daily --arch <arch>     # each architecture; --freq 15min for the Transformer
python scripts/10_design_rules.py --freq daily --arch <arch>
python scripts/10_trade_test.py
python scripts/10_compare_architectures.py
python scripts/11_design_rulebook.py
python scripts/11_trade_test.py
python scripts/12_prepare_fresh.py
python scripts/12_evaluate_fresh.py
python -m pytest tests                           # 52 tests
streamlit run dashboard/app.py
```
All parameters live in `config/config.yaml`. Every run is logged in `reports/experiments.jsonl`. Seeds are fixed.
Selections and rules are frozen in timestamped JSON files and the scripts refuse to overwrite them.
