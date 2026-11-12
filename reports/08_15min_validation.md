# Step 8 — transformer on 15-minute bars, validation (14,325 bars)

Window 48 bars, tuned daily hyperparameters, rebalance every 48 bars, device cuda.

| Model | Accuracy | Macro-F1 | Sharpe | Max DD | Cum. return | Avg exposure |
|---|---|---|---|---|---|---|
| transformer (5 seeds) | 0.689 ± 0.013 | 0.603 ± 0.023 | 0.72 ± 0.17 | -10.9% | 26.4% | 62.5% |
| transformer seed ensemble | 0.702 | 0.613 | 0.56 | -11.0% | 23.4% | 63.6% |
| *buy & hold* | – | – | 0.56 | -16.9% | 30.1% | 100.0% |

Ensemble confusion matrix (rows true, cols predicted, ['bull', 'bear', 'sideways', 'high_vol']): [[5855, 75, 995, 0], [38, 2005, 486, 46], [1323, 1094, 2104, 29], [0, 179, 0, 96]]