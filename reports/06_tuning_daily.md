# Step 6 — hyperparameter tuning, daily

Optuna TPE, 50 trials per architecture, median pruner. Objective = 0.6 × macro-F1 + 0.4 × clip((Sharpe + 1) / 3, 0, 1) on the validation split. Top 3 trials re-run with 5 seeds; best mean wins. Default and tuned numbers below are both 5-seed means on the same validation split.

| Model | Config | Objective | Macro-F1 | Sharpe | Max DD | Params |
|---|---|---|---|---|---|---|
| lstm | default | 0.6187 ± 0.0250 | 0.631 | 0.80 | -7.0% | 55,716 |
| lstm | **tuned** (trial 38) | **0.6371 ± 0.0320** | 0.685 | 0.70 | -6.8% | 341,668 |
| cnn_bilstm_attn | default | 0.6473 ± 0.0301 | 0.689 | 0.75 | -6.8% | 139,172 |
| cnn_bilstm_attn | **tuned** (trial 41) | **0.6799 ± 0.0358** | 0.762 | 0.67 | -7.5% | 365,604 |
| transformer | default | 0.6537 ± 0.0468 | 0.709 | 0.71 | -6.7% | 70,052 |
| transformer | **tuned** (trial 48) | **0.6908 ± 0.0199** | 0.758 | 0.77 | -6.6% | 271,012 |

## Chosen hyperparameters

- **lstm**: lr=3.38e-03, batch_size=64, dropout=0.379, hidden=128, layers=3
- **cnn_bilstm_attn**: lr=5.02e-03, batch_size=16, dropout=0.429, hidden=128, layers=3
- **transformer**: lr=1.51e-03, batch_size=64, dropout=0.308, hidden=128, heads=4, ff_dim=256

## Top-3 re-runs (single-seed trial score vs 5-seed mean)

| Model | Trial | Single seed | 5-seed mean ± std |
|---|---|---|---|
| lstm | 20 | 0.7104 | 0.6315 ± 0.0442 |
| lstm | 24 | 0.7056 | 0.6299 ± 0.0442 |
| lstm | 38 | 0.6957 | 0.6371 ± 0.0320 |
| cnn_bilstm_attn | 12 | 0.7065 | 0.6659 ± 0.0499 |
| cnn_bilstm_attn | 41 | 0.7012 | 0.6799 ± 0.0358 |
| cnn_bilstm_attn | 19 | 0.7002 | 0.6769 ± 0.0252 |
| transformer | 25 | 0.7143 | 0.6308 ± 0.0535 |
| transformer | 12 | 0.7041 | 0.6767 ± 0.0442 |
| transformer | 48 | 0.6960 | 0.6908 ± 0.0199 |

## Parameter importance (fANOVA over completed trials)

- **lstm**: lr 0.52, batch_size 0.21, dropout 0.14, hidden 0.12, layers 0.02
- **cnn_bilstm_attn**: dropout 0.66, lr 0.18, hidden 0.12, batch_size 0.03, layers 0.01
- **transformer**: dropout 0.55, lr 0.27, batch_size 0.07, heads 0.06, hidden 0.03, ff_dim 0.02

Deviation from spec: CNN-BiLSTM-Attention's attention heads are not tuned — spec 6.2 defines additive (Bahdanau) attention, which has no heads. Its `layers` parameter controls the number of conv layers.