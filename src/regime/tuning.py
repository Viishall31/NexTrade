"""Step 6: Optuna search space and tuning objective (FR-H1..H4, spec section 8)."""
import numpy as np

from regime.backtest import evaluate_strategy
from regime.train import classification_metrics


def suggest_hparams(trial, arch: str, base_models: dict, base_training: dict, space: dict) -> tuple[dict, dict]:
    """Model and training hyperparameters for one trial. Works with optuna.trial.FixedTrial too."""
    train_hp = dict(base_training,
                    lr=trial.suggest_float("lr", *space["lr"], log=True),
                    batch_size=trial.suggest_categorical("batch_size", space["batch_size"]))
    dropout = trial.suggest_float("dropout", *space["dropout"])
    hidden = trial.suggest_categorical("hidden", space["hidden"])
    hp = dict(base_models[arch])

    if arch == "lstm":
        hp.update(hidden=hidden, layers=trial.suggest_int("layers", *space["layers"]),
                  dropout=dropout, head_dropout=dropout)
    elif arch == "cnn_bilstm_attn":
        n_conv = trial.suggest_int("layers", *space["layers"])
        hp.update(hidden=hidden, conv_filters=space["conv_filters"][:n_conv],
                  dropout=dropout, head_dropout=dropout)
    elif arch == "transformer":
        hp.update(d_model=hidden, heads=trial.suggest_categorical("heads", space["heads"]),
                  ff_dim=trial.suggest_categorical("ff_dim", space["ff_dim"]), dropout=dropout)
    else:
        raise ValueError(arch)
    return hp, train_hp


def normalized_sharpe(sharpe: float, low: float, high: float) -> float:
    return float(np.clip((sharpe - low) / (high - low), 0.0, 1.0))


def tuning_objective(y_true, y_pred, asset_returns, classes, bt_cfg: dict, obj_cfg: dict, freq: str) -> dict:
    """0.6 x macro-F1 + 0.4 x normalised Sharpe, plus the components for logging."""
    macro_f1 = classification_metrics(y_true, y_pred, list(classes))["macro_f1"]
    perf, _ = evaluate_strategy(np.asarray(classes)[y_pred], asset_returns, bt_cfg, freq)
    score = (obj_cfg["f1_weight"] * macro_f1
             + obj_cfg["sharpe_weight"] * normalized_sharpe(perf["sharpe"], *obj_cfg["sharpe_range"]))
    return {"objective": float(score), "macro_f1": macro_f1, **perf}
