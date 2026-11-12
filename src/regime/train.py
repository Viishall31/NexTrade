"""Step 4: common training harness (FR-M4, FR-M5, spec section 7).

Identical for all architectures: class-weighted cross-entropy, Adam, early stopping on
validation macro-F1 with best weights restored.
"""
import random
import time

import numpy as np
import torch
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def class_weights(y_train: np.ndarray, n_classes: int) -> torch.Tensor:
    """Inverse class frequency on the train split: N / (K * n_c)."""
    counts = np.bincount(y_train, minlength=n_classes).astype(float)
    if (counts == 0).any():
        raise ValueError(f"class missing from train split: {counts}")
    return torch.tensor(len(y_train) / (n_classes * counts), dtype=torch.float32)


@torch.no_grad()
def predict_proba(model: nn.Module, X: np.ndarray, batch_size: int = 1024) -> np.ndarray:
    """Runs on whatever device the model is on; returns a CPU numpy array."""
    model.eval()
    device = next(model.parameters()).device
    out = [torch.softmax(model(torch.from_numpy(X[i:i + batch_size]).to(device)), dim=1).cpu()
           for i in range(0, len(X), batch_size)]
    return torch.cat(out).numpy()


def classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, classes: list) -> dict:
    labels = list(range(len(classes)))
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
        # Over classes that occur in y_true only (differs from macro_f1 when a regime is absent, e.g. test has no high_vol).
        "macro_f1_present": float(f1_score(y_true, y_pred, labels=sorted(set(y_true.tolist())), average="macro", zero_division=0)),
        "per_class": {c: {"precision": float(p[i]), "recall": float(r[i]), "f1": float(f[i]), "support": int(s[i])}
                      for i, c in enumerate(classes)},
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
    }


def train_model(model: nn.Module, X_tr, y_tr, X_val, y_val, tcfg: dict, n_classes: int, seed: int,
                on_epoch=None) -> dict:
    """on_epoch(epoch, val_pred) is called after each epoch; it may raise (e.g. optuna.TrialPruned)."""
    set_seed(seed)
    loader = DataLoader(TensorDataset(torch.from_numpy(X_tr), torch.from_numpy(y_tr)),
                        batch_size=tcfg["batch_size"], shuffle=True,
                        generator=torch.Generator().manual_seed(seed))
    device = next(model.parameters()).device
    loss_fn = nn.CrossEntropyLoss(weight=class_weights(y_tr, n_classes).to(device))
    opt = torch.optim.Adam(model.parameters(), lr=tcfg["lr"])

    best_f1, best_state, best_epoch, wait, history = -1.0, None, 0, 0, []
    start = time.time()
    for epoch in range(1, tcfg["max_epochs"] + 1):
        model.train()
        total = 0.0
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()
            total += loss.item() * len(xb)
        val_pred = predict_proba(model, X_val).argmax(axis=1)
        val_f1 = f1_score(y_val, val_pred, labels=list(range(n_classes)), average="macro", zero_division=0)
        if on_epoch is not None:
            on_epoch(epoch, val_pred)
        history.append({"epoch": epoch, "train_loss": total / len(X_tr), "val_macro_f1": float(val_f1)})
        if val_f1 > best_f1:
            best_f1, best_epoch, wait = val_f1, epoch, 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            wait += 1
            if wait >= tcfg["patience"]:
                break
    model.load_state_dict(best_state)
    return {"best_epoch": best_epoch, "epochs_run": epoch, "best_val_macro_f1": float(best_f1),
            "train_seconds": round(time.time() - start, 1), "history": history}
