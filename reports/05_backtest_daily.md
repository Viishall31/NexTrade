# Step 5 — regime-conditioned backtest, daily, validation 2022-01-03 → 2024-04-30

Exposure bull 100% / sideways 50% / high_vol 25% / bear 0%; 5 bps per unit exposure change; uninvested cash earns 6% p.a.; Sharpe/Sortino on excess return over 6%.

| Strategy | Sharpe | Sortino | Max DD | Cum. return | Ann. return | Avg exposure | Macro-F1 |
|---|---|---|---|---|---|---|---|
| lstm (5 seeds) | 0.80 ± 0.14 | 1.14 | -7.0% | 30.9% | 12.6% | 62.0% | 0.631 |
| cnn_bilstm_attn (5 seeds) | 0.75 ± 0.10 | 1.07 | -6.8% | 29.6% | 12.1% | 61.4% | 0.689 |
| transformer (5 seeds) | 0.71 ± 0.10 | 0.99 | -6.7% | 28.0% | 11.5% | 59.5% | 0.709 |
| *buy_and_hold* | 0.49 | 0.68 | -16.5% | 30.1% | 12.3% | 100.0% | – |
| *hmm_label_oracle* | 0.53 | 0.73 | -8.3% | 25.0% | 10.3% | 64.7% | – |
| *hmm_label_lagged* | 0.46 | 0.63 | -8.7% | 23.8% | 9.8% | 64.5% | – |

*hmm_label_oracle* trades on the true next-day HMM label (unattainable upper reference); *hmm_label_lagged* trades on the HMM label known at the close of t.