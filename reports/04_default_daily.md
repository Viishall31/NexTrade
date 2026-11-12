# Step 4 — default hyperparameters, daily (validation split, 573 samples)

| Model | Params | Accuracy | Macro-F1 | F1 bull | F1 bear | F1 sideways | F1 high_vol |
|---|---|---|---|---|---|---|---|
| lstm | 55,716 | 0.764 ± 0.020 | 0.631 ± 0.020 | 0.85 | 0.75 | 0.70 | 0.23 |
| cnn_bilstm_attn | 139,172 | 0.777 ± 0.026 | 0.689 ± 0.048 | 0.84 | 0.77 | 0.73 | 0.42 |
| transformer | 70,052 | 0.762 ± 0.027 | 0.709 ± 0.063 | 0.83 | 0.78 | 0.67 | 0.55 |
| *majority_class* | – | 0.483 | 0.163 | 0.65 | 0.00 | 0.00 | 0.00 |
| *logistic_regression_last_bar* | – | 0.787 | 0.592 | 0.85 | 0.81 | 0.71 | 0.00 |
| *persistence_reference* | – | 0.941 | 0.932 | 0.96 | 0.95 | 0.91 | 0.91 |

Mean ± std over 5 seeds. Confusion matrices (rows = true, cols = predicted, order ['bull', 'bear', 'sideways', 'high_vol']) for the best seed are in `04_default_daily.json`.
*persistence_reference* uses the HMM label at t, which the models never see — it is an upper reference for how sticky the labels are, not a competitor.