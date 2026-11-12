# Step 10 — trading findings (for the report)

Numbers: `10_test_trading.md` · Frozen rules: `10_rules_daily_transformer.json`, `10_rules_15min_transformer.json` · Trades: `10_trades_*.csv`

## Method
1. Seed-ensemble probabilities for validation (Jan 2022 – Apr 2024) and test (May 2024 – Apr 2025): `signals_{daily,15min}_transformer.parquet`.
2. 72 rule combinations per model (42 long-only ETF + 30 long/short futures). Each combines an exposure map,
   a confirmation delay, a confidence filter and a 5% trailing stop.
3. Each rule is simulated in rupees from Rs 10,00,000 on validation, with costs and 6% interest on idle cash.
   Winner = highest final capital with drawdown no worse than buy & hold. Frozen, timestamped.
4. Recommended system = the frozen long-only system with the highest validation final capital → **daily model**.
5. The test year is traded once.

## Result
| From Rs 10,00,000 | Validation (2.3 yrs) | Test year |
|---|---|---|
| **Recommended: daily long-only, `risk_off / confirm 2 / 5% stop`** | Rs 14,04,106 | **Rs 9,29,569 (−7.0%)** |
| Buy & hold Nifty ETF | Rs 13,00,325 | Rs 9,81,776 (−1.8%) |
| Cash at 6% | Rs 11,41,670 | Rs 10,55,109 (+5.5%) |

No frozen system made money in the test year, and none beat buy & hold or cash. The recommended system
did have a smaller drawdown than buy & hold (−13.0% vs −15.7%).

## Why it lost: trade log of the recommended system
| # | Date | Action | Nifty | What happened |
|---|---|---|---|---|
| 1 | 2 May 2024 | BUY | 22,648 | bull regime |
| 2 | 4 Jun 2024 | SELL | 21,971 | 5% stop hit on the election-result crash |
| 3 | 1 Jul 2024 | BUY | 24,136 | label turned sideways → stop released, re-bought **9.9% higher** |
| 4 | 7 Oct 2024 | SELL | 24,802 | stop hit after the September peak |
| 5 | 11 Oct 2024 | BUY | 24,969 | sideways again 4 days later → re-bought higher |
| 6 | 12 Nov 2024 | SELL | 23,859 | stop hit |
| 7 | 4 Dec 2024 | BUY | 24,467 | re-bought 2.5% higher |
| 8 | 9 Jan 2025 | SELL | 23,539 | stop hit; cash until the end |

The pattern is sell-low / buy-high whipsaw, repeated four times:
- The stop-loss exits after a fall.
- The regime label changes soon after, which releases the stop.
- Under `risk_off`, "sideways" means 100% invested, so the system buys back at a higher price.

In the test year the frozen HMM labels 65% of days as sideways (see `07_findings.md`), including the
Oct 2024 – Mar 2025 decline, so the "sideways = invested" rule kept re-entering a falling market.

## What worked on validation and why it did not transfer
- Validation (2022–Apr 2024) had one clear bear phase followed by a long, steady rally. Exiting in bear and
  holding through sideways/bull was profitable there.
- The test year had two sharp V-shaped shocks (June 2024, and a smaller one in October) and then a slow,
  low-volatility decline. The HMM does not call that decline bear, so the model cannot either.
- The 15-min model trades 3× more often, pays 3× the costs, and does worse (Rs 8,71,623).
- Idealized shorting does not help (Rs 8,84,083 daily, Rs 8,99,013 15-min), because shorts only open in "bear",
  which is labelled after the fall.
- Rule selection on validation is optimistic: the models' validation predictions were also used for early
  stopping and hyperparameter tuning, and 72 rules were compared on one 2.3-year period.

## Honest conclusion for the report
The regime classifier reproduces the HMM labels well out of sample (Step 7: accuracy 0.88, macro-F1 0.84),
but trading on those regimes did not make money in May 2024 – Apr 2025. The limiting factor is the label
definition, not the classifier: the regimes are identified after the move and miss slow declines.

## Legitimate next steps (not tuned on the test year)
1. **Retrain on all pre-test data (2016 – Apr 2024)** with the frozen hyperparameters and rules. This is standard
   before deployment; the current models stop learning at Dec 2021.
2. **Stop re-entry rule:** require a *bull* confirmation (not any regime change) before re-entering after a stop.
   Justified by the validation trade logs, and it must be chosen on validation.
3. **Leading label definition:** e.g. label regimes by *forward* 20-day return/volatility (what the market does next)
   instead of the causal HMM state (what it has already done).
4. **Walk-forward evaluation:** refit yearly and trade each following year, giving several out-of-sample years instead of one.
Any of these must be reported as post-hoc changes made after the first test result.

---

## Addendum — all three architectures on the same test (`10_architectures_test.md`)
Every architecture (daily, tuned, 5-seed ensemble) went through the same procedure: its own rule search on
validation, frozen, then one pass over the test year from Rs 10,00,000.

| Model | Test accuracy | Test macro-F1 | ETF + cash (own rule) | Futures, idealized (own rule) |
|---|---|---|---|---|
| LSTM | 0.793 | 0.621 | Rs 9,70,051 (−3.0%) | Rs 9,83,903 (−1.6%) |
| CNN-BiLSTM-Attention | 0.841 | 0.580 | Rs 9,62,903 (−3.7%) | **Rs 10,66,782 (+6.7%)** |
| Transformer | **0.879** | **0.836** | Rs 9,29,569 (−7.0%) | Rs 8,84,083 (−11.6%) |
| Buy & hold ETF | | | Rs 9,81,776 (−1.8%) | |
| Cash at 6% | | | Rs 10,55,109 (+5.5%) | |

With identical rules for all three (spec rule / the Transformer's rule): LSTM Rs 9,37,969 / 9,55,673;
CNN-BiLSTM-Attention Rs 10,08,033 / 10,06,310; Transformer Rs 9,21,122 / 9,29,569.

### Reading this correctly
1. **Better classifier, worse trader.** The ranking by test accuracy (Transformer > CNN > LSTM) is the
   reverse of the ranking by money. The Transformer reproduces the lagging HMM labels most faithfully and
   inherits their lag. The weaker models deviate from the labels, and here that happened to help.
2. **The only profitable system never shorted.** The CNN futures rule (`ls_spec / confirm 3`) only moved between
   100% long (bull) and 50% long (sideways), because the CNN never predicted bear in the test year. Its edge over
   the ETF version comes from being 50% invested through the Oct 2024 – Mar 2025 decline, and from the idealized
   futures assumptions: the full Rs 10 lakh collateral earns 6%, and costs are lower. It beat cash by only about 1.2 points.
3. **One profit out of six systems is weak evidence.** Choosing it now, after seeing the test results, would be
   hindsight. The pre-registered choice (the Transformer, daily long-only) lost 7.0%.
4. With rules held constant, CNN-BiLSTM-Attention is the only model that ends slightly above Rs 10 lakh
   (+0.6% to +0.8%). It still earns less than cash.

## Step 9 replay — 15-min Transformer (`09_replay_test.md`)
- Pipeline: 5,800/5,800 bars, p95 latency 163 ms, replay identical to the batch pipeline (100% agreement). No orders.
- Classification collapses out of sample: accuracy 0.518 and macro-F1 0.412, vs 0.702 / 0.613 on validation.
- Trading (rebalance every 48 bars): −7.6% vs buy & hold −1.8%.
- The 15-min model is clearly weaker than the daily models, consistent with its early overfitting (best epoch 1–4)
  and the lack of 15-min-specific tuning.
