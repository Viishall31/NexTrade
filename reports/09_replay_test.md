# Step 9 — walk-forward replay (test): transformer 15-min, 2024-05-02 → 2025-04-07

5,800 bars fed one at a time over 232 trading days to a frozen 5-seed ensemble; ground truth = frozen HMM advanced one step at each day close. No orders placed (C-4).

## Classification

- Accuracy **0.518**, macro-F1 (regimes present) **0.412**, macro-F1 (all 4) 0.309
- True labels: {'sideways': 3775, 'bull': 1524, 'bear': 500}; predicted: {'sideways': 2642, 'bull': 2233, 'bear': 826, 'high_vol': 98}
- Confidence: mean 0.62; 16.6% flagged low (< 0.5); accuracy high-confidence 0.5263702171664943, low-confidence 0.47614107883817425
- Confusion matrix (rows true, cols predicted, ['bull', 'bear', 'sideways', 'high_vol']): [[944, 60, 520, 0], [186, 77, 139, 98], [1103, 689, 1983, 0], [0, 0, 0, 0]]

## Trading (rebalance every 48 bars)

| | Sharpe | Sortino | Max DD | Cum. return | Avg exposure |
|---|---|---|---|---|---|
| Regime strategy | -1.59 | -2.05 | -17.9% | -7.6% | 61.9% |
| Buy & hold | -0.60 | -0.80 | -16.8% | -1.8% | 100.0% |

## Replay vs validation backtest (FR-L4)

| Metric | Validation (Step 8) | Replay | Gap |
|---|---|---|---|
| macro_f1 | 0.613 | 0.412 | -0.201 |
| accuracy | 0.702 | 0.518 | -0.184 |
| sharpe | 0.557 | -1.591 | -2.148 |
| max_drawdown | -0.110 | -0.179 | -0.069 |
| cumulative_return | 0.234 | -0.076 | -0.310 |

## Operational checks

- Uptime: 5800/5800 bars (100.0%); incomplete days none
- Latency per bar (features + 5-model inference, CPU): p50 95 ms, p95 163 ms, max 400 ms (requirement < 2000 ms)
- Replay vs batch pipeline: prediction agreement 100.0%, max probability difference 3.0e-07, daily label agreement 100.0%, bar target agreement 100.0%
- SQLite log: `data/replay/replay.db` tables `predictions_test`, `daily_labels_test`