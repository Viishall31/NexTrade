# Step 7 — findings (for the report)

Numbers: `07_test_results.md` · Selection record: `07_selection.json` (frozen 2026-09-17 00:15, before test)

## 1. Model selection (validation only)
Rule (spec 9.3): macro-F1 within 2 pp of the best, then highest Sharpe.

| Tuned model | Val macro-F1 | Val Sharpe | Eligible | Flag (FR-E4) |
|---|---|---|---|---|
| LSTM | 0.685 | 0.70 | no | – |
| CNN-BiLSTM-Attention | 0.762 | 0.67 | yes | best classifier but not best Sharpe |
| **Transformer** | 0.758 | **0.77** | yes | **selected** |

Deployed form (decided before the test run): average of the 5 tuned seeds' softmax outputs.

## 2. Classification generalises
Test = May 2024 – Apr 2025, 232 days, labelled by the frozen HMM (bull 61 / bear 20 / sideways 151 / high_vol 0).

- Deployed Transformer ensemble: **accuracy 0.879, macro-F1 0.836** (3 present regimes).
- Single tuned Transformer seeds: macro-F1 0.708 ± 0.124 (validation 0.758 → gap −0.05).
- Ensembling the seeds adds ~13 points of macro-F1 and removes most seed variance.
- Logistic-regression baseline: macro-F1 0.730 — the ensemble beats it; single seeds do not reliably.
- Recall by regime: bull 0.87, bear 0.85, sideways 0.89. Only 0.4% of predictions are low-confidence (< 0.5).

## 3. Trading does not generalise
| | Sharpe | Max DD | Return |
|---|---|---|---|
| Deployed ensemble | −1.31 | −10.1% | −7.7% |
| Buy & hold | −0.46 | −15.7% | −1.8% |
| Trading on the true HMM label (oracle) | −0.59 | −7.7% | +0.9% |

Every regime strategy has a negative Sharpe, including the oracle: the market was roughly flat
(below the 6% risk-free rate). The strategies still cut drawdown by about a third vs buy & hold.
The tuned Transformer — chosen for the best validation Sharpe — has the worst test Sharpe of
all models. The validation Sharpe ranking did not carry over.

## 4. Why: the labels lag, and the model learned the lag
Verified day by day around the 4 June 2024 election result:
- 3 June close: model predicts bull → 100% invested.
- 4 June: Nifty −5.65%. The strategy takes the full loss.
- The crash itself flips the HMM label to bear (the 20-day return and volatility jump), so the
  model follows the label into 0% exposure for four weeks.
- Nifty recovers about +9% over those weeks; the strategy earns cash.

This is the lag documented in `03_hmm.md`: HMM regimes are identified after the move. A model that
reproduces those labels accurately inherits the lag. In a crash-and-rebound market (June 2024,
the August 2024 yen-carry unwind, the April 2025 tariff shock) that is costly. Higher agreement
with the labels does not mean better trading, and here it meant worse.

## 5. Second label limitation seen on test
The Oct 2024 – Mar 2025 correction (about −16% peak to trough) is labelled mostly **sideways**.
The HMM, trained on 2016–2021, learned "bear" as "elevated volatility". This decline was slow
and calm, so it did not trigger bear. No high_vol days occur in the test period.

## 6. What this means for the conclusions
- Objective 1 (HMM labels): fits known historical periods in-sample; on test they lag sharp moves and miss slow declines.
- Objective 2/3 (models + tuning): supported. Tuning improves validation F1 for all models; the
  seed ensemble generalises well on classification.
- Model selection by validation Sharpe: not supported by the test result (a single validation
  period of about 2.3 years is too short to rank Sharpe reliably; differences were within seed noise).
- The test set has now been used. Any change to labels, strategy or selection must be justified
  on validation data and reported as post-hoc, not re-scored on this test set as if it were clean.
