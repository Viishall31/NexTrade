# Step 7 — held-out test, daily, 2024-05-02 → 2025-04-07 (232 days)

Selection frozen on validation before this run (`07_selection.json`): **transformer**. Test labels (frozen HMM): {'bull': 61, 'bear': 20, 'sideways': 151, 'high_vol': 0}. Macro-F1 (3) = over the regimes present in the test labels; Macro-F1 (4) counts absent high_vol as 0.

| Model | Accuracy | Macro-F1 (3) | Macro-F1 (4) | Sharpe | Max DD | Cum. return | Avg exposure |
|---|---|---|---|---|---|---|---|
| lstm/default | 0.763 ± 0.025 | 0.574 ± 0.051 | 0.431 | -0.64 ± 0.11 | -10.5% | -2.2% | 63.8% |
| cnn_bilstm_attn/default | 0.805 ± 0.035 | 0.555 ± 0.023 | 0.417 | -0.62 ± 0.15 | -10.9% | -1.9% | 66.2% |
| transformer/default | 0.799 ± 0.049 | 0.613 ± 0.067 | 0.460 | -0.88 ± 0.15 | -10.0% | -3.4% | 59.9% |
| lstm/tuned | 0.781 ± 0.016 | 0.603 ± 0.042 | 0.452 | -0.84 ± 0.15 | -10.8% | -3.9% | 64.1% |
| cnn_bilstm_attn/tuned | 0.749 ± 0.089 | 0.583 ± 0.096 | 0.437 | -0.53 ± 0.13 | -11.0% | -1.0% | 63.9% |
| **transformer/tuned** | 0.802 ± 0.054 | 0.708 ± 0.124 | 0.531 | -1.34 ± 0.14 | -11.4% | -7.7% | 60.0% |
| **deployed: transformer 5-seed ensemble** | 0.879 | 0.836 | 0.627 | -1.31 | -10.1% | -7.7% | 57.8% |
| *logistic regression (last bar)* | 0.815 | 0.730 | 0.548 | -0.84 | -10.4% | -2.2% | 58.2% |
| *buy_and_hold* | – | – | – | -0.46 | -15.7% | -1.8% | 100.0% |
| *hmm_label_oracle* | – | – | – | -0.59 | -7.7% | 0.9% | 58.8% |
| *hmm_label_lagged* | – | – | – | -0.93 | -8.7% | -3.0% | 59.1% |

## Validation → test gap (transformer, tuned, 5-seed mean)

| Metric | Validation | Test | Gap |
|---|---|---|---|
| macro_f1 | 0.758 | 0.708 | -0.050 |
| sharpe | 0.770 | -1.342 | -2.112 |
| max_drawdown | -0.066 | -0.114 | -0.048 |
| cumulative_return | 0.296 | -0.077 | -0.373 |

## Deployed model by true regime (FR-E2)

| True regime | Days | Recall | Predicted as | Strategy bps/day | Buy & hold bps/day |
|---|---|---|---|---|---|
| bull | 61 | 0.87 | {'bull': 53, 'bear': 0, 'sideways': 8, 'high_vol': 0} | 3.1 | 4.8 |
| bear | 20 | 0.85 | {'bull': 1, 'bear': 17, 'sideways': 2, 'high_vol': 0} | -25.3 | 18.8 |
| sideways | 151 | 0.89 | {'bull': 8, 'bear': 9, 'sideways': 134, 'high_vol': 0} | -2.9 | -4.9 |

Confidence: mean 0.80; 0.4% of predictions below 0.5 (flagged). Accuracy high-confidence 0.8831168831168831, low-confidence 0.0.

Confusion matrix, deployed model (rows true, cols predicted, ['bull', 'bear', 'sideways', 'high_vol']): [[53, 0, 8, 0], [1, 17, 2, 0], [8, 9, 134, 0], [0, 0, 0, 0]]