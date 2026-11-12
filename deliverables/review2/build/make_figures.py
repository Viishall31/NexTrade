"""Review 2 figures for the NexTrade interim report and deck. Every number is read from the saved project
results (reports/, data/processed/, models/); nothing is retrained. Output: deliverables/review2/figures/*.png"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Patch
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "dashboard"))
import data as D  # noqa: E402  (dashboard data layer: frozen rules re-simulated from saved signals)

OUT = Path(__file__).resolve().parents[1] / "figures"
REP, PROC = ROOT / "reports", ROOT / "data" / "processed"
INK, INK2, MUTED, GRID = "#1b2430", "#4a5563", "#8a93a0", "#e3e7ec"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#4a3aa7"]
MODEL_COLOR = {"lstm": SERIES[0], "cnn_bilstm_attn": SERIES[1], "transformer": SERIES[2]}
REGIME_COLOR = {"bull": "#1baf7a", "sideways": "#2a78d6", "bear": "#eb6834", "high_vol": "#eda100"}
REGIME_ORDER = ["bull", "sideways", "bear", "high_vol"]
NAMES = D.NAMES
CLASSES = ["bull", "bear", "sideways", "high_vol"]

plt.rcParams.update({
    "font.family": "Arial", "font.size": 10, "axes.edgecolor": "#c3c9d1", "axes.labelcolor": INK2,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlecolor": INK, "axes.titlelocation": "left",
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False, "savefig.dpi": 220,
    "savefig.bbox": "tight", "figure.facecolor": "white",
})


def rj(name):
    return json.loads((REP / name).read_text(encoding="utf-8"))


def save(fig, name):
    fig.savefig(OUT / f"{name}.png")
    plt.close(fig)
    print("saved", name)


def inr(v):
    """1082677 -> 'Rs 10,82,677'"""
    n = str(int(round(v)))
    head, tail = n[:-3], n[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return "Rs " + ",".join(groups + [tail]) if groups else "Rs " + tail


def month_ticks(ax, every=3):
    ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator(interval=every))
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y"))
    ax.tick_params(axis="x", rotation=0)


def lakh_axis(ax):
    ax.set_ylabel("Portfolio value (Rs lakh)")
    ax.axhline(10, color="#9aa3ad", lw=0.8, zorder=1)


# ------------------------------------------------------------------ diagrams
def box(ax, x, y, w, h, title, body, face="#ffffff", edge="#1b2430", title_color=INK, dashed=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=face, ec=edge, lw=1.3,
                                ls="--" if dashed else "-"))
    ax.text(x + 0.12, y + h - 0.2, title, ha="left", va="top", fontsize=10.5, fontweight="bold", color=title_color)
    ax.text(x + 0.12, y + h - 0.55, body, ha="left", va="top", fontsize=8.6, color=INK2, linespacing=1.35)


def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color="#5b6674", lw=1.2))


def fig_architecture():
    fig, ax = plt.subplots(figsize=(12, 6.4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0.3, 6.45)
    ax.axis("off")
    w, h, gx = 2.55, 1.4, 0.45
    xs = [0.1 + i * (w + gx) for i in range(4)]
    rows = [4.75, 2.6, 0.45]
    data = [
        [("1  Market data", "Nifty 50 15-min OHLC (vendor)\nApr 2015 – Apr 2025\n+ yfinance daily to Sep 2026"),
         ("2  Cleaning", "1,850 duplicate rows removed\nspecial sessions dropped\n25-bar session grid"),
         ("3  Feature engineering", "13 causal indicators\nRSI · MACD · EMA ratios · ATR\nADX · Bollinger · Stoch RSI"),
         ("4  HMM regime labels", "Gaussian HMM, 4 states\n20-day return + 20-day vol\nforward-filtered, frozen")],
        [("8  Model selection", "validation only, frozen\nF1 within 2 pts → best Sharpe\n→ Transformer"),
         ("7  Optuna tuning", "TPE, 50 trials per model\ntop-3 re-run on 5 seeds\n0.6·F1 + 0.4·Sharpe"),
         ("6  Three classifiers", "LSTM · CNN-BiLSTM-Attention\nTransformer (PyTorch)\nclass-weighted CE, 5 seeds"),
         ("5  Sequence windows", "30 trading days × 13 features\ntarget = regime of day t+1\ntrain-only z-score scaler")],
        [("9  One-time test", "Nifty50_test.csv\nMay 2024 – Apr 2025\nclassification + backtest"),
         ("10  Walk-forward replay", "15-min Transformer (Colab GPU)\n5,800 bars one at a time\nSQLite prediction log"),
         ("11  Rule-based trading", "Rs 10 lakh, costs, cash @ 6%\nExp 1 rules · Exp 2 rulebook\nfrozen on validation"),
         ("12  Forward test", "fresh data Apr 2025 – Sep 2026\nall models and rules frozen\n+ Streamlit dashboard")],
    ]
    faces = ["#eef3fb", "#eefaf4", "#fdf3ea"]
    edges = ["#2a78d6", "#1a9c6d", "#d8672e"]
    for r, (y, row) in enumerate(zip(rows, data)):
        order = xs if r != 1 else xs[::-1]
        items = row if r != 1 else row[::-1]
        for x, (t, b) in zip(xs, row):
            box(ax, x, y, w, h, t, b, face=faces[r], edge=edges[r])
    for r, y in enumerate(rows):
        for i in range(3):
            if r == 1:
                arrow(ax, xs[i + 1], y + h / 2, xs[i] + w, y + h / 2)
            else:
                arrow(ax, xs[i] + w, y + h / 2, xs[i + 1], y + h / 2)
    arrow(ax, xs[3] + w / 2, rows[0], xs[3] + w / 2, rows[1] + h)
    arrow(ax, xs[0] + w / 2, rows[1], xs[0] + w / 2, rows[2] + h)
    legend = [Patch(fc=faces[0], ec=edges[0], label="Data and labels"), Patch(fc=faces[1], ec=edges[1], label="Modelling"),
              Patch(fc=faces[2], ec=edges[2], label="Validation, trading and delivery")]
    ax.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, 1.04), ncol=3, fontsize=9)
    save(fig, "fig_architecture")


def fig_models():
    tuned = {a: rj(f"06_tuning_daily_{a}.json")["chosen"] for a in D.ARCHS}
    stacks = {
        "lstm": [("Input", "30 days × 13 features"),
                 ("LSTM × {layers}", "{hidden} units, dropout {dropout:.2f}"),
                 ("Last time step", "final hidden state"),
                 ("Dense 32 + ReLU", "dropout {head_dropout:.2f}"),
                 ("Dense 4 → softmax", "bull · bear · sideways · high-vol")],
        "cnn_bilstm_attn": [("Input", "30 days × 13 features"),
                            ("Causal Conv1D × {nconv}", "filters {filters}, kernel 3, ReLU"),
                            ("MaxPool1D", "pool 2 → 15 steps"),
                            ("BiLSTM", "{hidden} units per direction"),
                            ("Additive attention", "Bahdanau, size {attn_dim}"),
                            ("Dense 32 + ReLU", "dropout {head_dropout:.2f}"),
                            ("Dense 4 → softmax", "bull · bear · sideways · high-vol")],
        "transformer": [("Input", "30 days × 13 features"),
                        ("Linear projection", "13 → d_model {d_model}"),
                        ("Sinusoidal positions", "fixed encoding"),
                        ("Encoder × {layers}", "{heads} heads, FF {ff_dim}, dropout {dropout:.2f}"),
                        ("Mean pooling", "over 30 steps"),
                        ("Dense 32 + ReLU", ""),
                        ("Dense 4 → softmax", "bull · bear · sideways · high-vol")],
    }
    fig, axes = plt.subplots(1, 3, figsize=(12, 6.2))
    for ax, a in zip(axes, D.ARCHS):
        hp = dict(tuned[a]["model_hp"])
        if a == "cnn_bilstm_attn":
            hp["nconv"] = len(hp["conv_filters"])
            hp["filters"] = "–".join(map(str, hp["conv_filters"]))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 8)
        ax.axis("off")
        layers = stacks[a]
        n = len(layers)
        step = 6.6 / n
        for i, (title, body) in enumerate(layers):
            y = 7.0 - (i + 1) * step + 0.12
            ax.add_patch(FancyBboxPatch((0.06, y), 0.88, step - 0.24, boxstyle="round,pad=0.01,rounding_size=0.04",
                                        fc="#ffffff" if 0 < i < n - 1 else "#eef3fb", ec=MODEL_COLOR[a], lw=1.3))
            ax.text(0.5, y + (step - 0.24) * 0.62, title.format(**hp), ha="center", va="center", fontsize=10, fontweight="bold", color=INK)
            if body:
                ax.text(0.5, y + (step - 0.24) * 0.27, body.format(**hp), ha="center", va="center", fontsize=8.4, color=INK2)
            if i < n - 1:
                ax.annotate("", xy=(0.5, y - 0.22), xytext=(0.5, y - 0.01), arrowprops=dict(arrowstyle="-|>", color="#5b6674", lw=1, shrinkA=0, shrinkB=0))
        ax.text(0.5, 7.55, NAMES[a], ha="center", fontsize=12.5, fontweight="bold", color=MODEL_COLOR[a])
        ax.text(0.5, 7.2, f"{tuned[a]['n_params']:,} parameters · lr {tuned[a]['params']['lr']:.1e} · batch {tuned[a]['params']['batch_size']}",
                ha="center", fontsize=8.6, color=INK2)
    save(fig, "fig_models")


def fig_split_timeline():
    df = D.daily_regimes()
    fig, ax = plt.subplots(figsize=(12, 3.6))
    spans = [("train", "Train (Feb 2016 – Dec 2021)", "#eef3fb", "top"), ("val", "Validation (Jan 2022 – Apr 2024)", "#eefaf4", "top"),
             ("test", "Test (May 24 – Apr 25)", "#fdf3ea", "bottom"), ("fresh", "Fresh (Apr 25 – Sep 26)", "#f4f0fb", "top")]
    lo, hi = df["close"].min(), df["close"].max()
    for split, label, color, where in spans:
        idx = df.index[df["split"] == split]
        ax.axvspan(idx.min(), idx.max(), color=color, lw=0)
        mid = idx.min() + (idx.max() - idx.min()) / 2
        if where == "top":
            ax.text(mid, hi * 1.05, label, ha="center", va="bottom", fontsize=8.5, color=INK2)
        else:
            ax.text(mid, lo * 1.05, label, ha="center", va="bottom", fontsize=8.5, color=INK2)
    ax.plot(df.index, df["close"], color=INK, lw=1)
    ax.set_ylim(lo * 0.9, hi * 1.16)
    ax.set_ylabel("Nifty 50 close")
    ax.grid(axis="x", visible=False)
    save(fig, "fig_split_timeline")


def ribbon(ax, series, title):
    for k, r in enumerate(REGIME_ORDER[::-1]):
        idx = series.index[series == r]
        ax.scatter(idx, np.full(len(idx), k), marker="|", s=90, lw=1.6, color=REGIME_COLOR[r])
    ax.set_yticks(range(4))
    ax.set_yticklabels([D.REGIME_LABEL[r] for r in REGIME_ORDER[::-1]], fontsize=8.5)
    ax.set_ylim(-0.7, 3.7)
    ax.grid(False)
    ax.set_title(title, fontsize=10)


def fig_regimes_full():
    df = D.daily_regimes()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 5.6), sharex=True, gridspec_kw={"height_ratios": [2.2, 1.3]})
    a1.plot(df.index, df["close"], color=INK, lw=1)
    a1.set_ylabel("Nifty 50 close")
    a1.set_title("Nifty 50 daily close, Feb 2016 – Sep 2026")
    for d, label in [("2022-01-01", "validation →"), ("2024-05-01", "test →"), ("2025-04-08", "fresh →")]:
        for ax in (a1, a2):
            ax.axvline(pd.Timestamp(d), color="#9aa3ad", lw=0.8, ls=(0, (3, 3)))
        a1.text(pd.Timestamp(d), df["close"].min() * 1.02, " " + label, fontsize=8.5, color=MUTED, va="bottom")
    ribbon(a2, df["regime"], "Frozen HMM regime (one row per regime)")
    save(fig, "fig_regimes_full")


def fig_test_timeline():
    df = D.daily_regimes()
    pred = D.predictions("transformer")
    t = df[df["split"] == "test"]
    p = pred.loc[t.index.min():t.index.max(), "predicted"]
    fig, axes = plt.subplots(3, 1, figsize=(12, 5.8), sharex=True, gridspec_kw={"height_ratios": [1.7, 1, 1]})
    axes[0].plot(t.index, t["close"], color=INK, lw=1.1)
    axes[0].set_ylabel("Nifty 50 close")
    axes[0].set_title("Test year: Nifty 50 close")
    ribbon(axes[1], t["regime"], "Frozen HMM regime (ground truth)")
    ribbon(axes[2], p, "Transformer 5-seed ensemble forecast (made at the previous close)")
    save(fig, "fig_test_timeline")


# ------------------------------------------------------------------ models
def ensemble_scores(arch, period):
    s = D.signals(arch, period)
    labels = sorted(set(s["true_regime"]))
    return accuracy_score(s["true_regime"], s["predicted"]), f1_score(s["true_regime"], s["predicted"], labels=labels, average="macro", zero_division=0)


def grouped(ax, groups, series, values, colors, fmt="{:.2f}", ylim=(0, 1)):
    x = np.arange(len(groups))
    width = 0.8 / len(series)
    for i, (name, vals, c) in enumerate(zip(series, values, colors)):
        bars = ax.bar(x + (i - (len(series) - 1) / 2) * width, vals, width * 0.92, color=c, label=name, zorder=3)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.012, fmt.format(v), ha="center", va="bottom", fontsize=8, color=INK2)
    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    ax.set_ylim(*ylim)
    ax.grid(axis="x", visible=False)


def fig_classification_periods():
    periods = [("val", "Validation*"), ("test", "Test year"), ("fresh", "Fresh data")]
    acc = {a: [ensemble_scores(a, p)[0] for p, _ in periods] for a in D.ARCHS}
    f1 = {a: [ensemble_scores(a, p)[1] for p, _ in periods] for a in D.ARCHS}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.2))
    for ax, vals, title in [(a1, acc, "Accuracy"), (a2, f1, "Macro-F1 (regimes present in the period)")]:
        grouped(ax, [l for _, l in periods], [NAMES[a] for a in D.ARCHS], [vals[a] for a in D.ARCHS],
                [MODEL_COLOR[a] for a in D.ARCHS])
        ax.set_title(title)
    a1.legend(loc="upper center", bbox_to_anchor=(1.1, -0.1), ncol=3)
    save(fig, "fig_classification_periods")


def fig_tuning():
    default_bt = rj("05_backtest_daily.json")["models"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw={"width_ratios": [1, 1.25]})
    groups = [NAMES[a] for a in D.ARCHS]
    dflt = [default_bt[a]["macro_f1_mean"] for a in D.ARCHS]
    tuned = [rj(f"06_tuning_daily_{a}.json")["chosen"]["mean"]["macro_f1"] for a in D.ARCHS]
    grouped(a1, groups, ["Default (spec)", "Tuned (Optuna)"], [dflt, tuned], ["#b7c2cf", "#1d4f91"], fmt="{:.3f}", ylim=(0, 0.9))
    a1.set_title("Validation macro-F1, 5-seed mean")
    a1.legend(loc="upper left", ncol=2)
    for a in D.ARCHS:
        tr = rj(f"06_tuning_daily_{a}.json")["trials"]
        vals = [t["value"] if t["state"] == "COMPLETE" else np.nan for t in tr]
        best = np.fmax.accumulate(np.nan_to_num(vals, nan=-np.inf))
        a2.scatter(range(len(vals)), vals, s=12, color=MODEL_COLOR[a], alpha=0.45, lw=0)
        a2.plot(range(len(vals)), best, color=MODEL_COLOR[a], lw=2, label=f"{NAMES[a]} (best so far)")
    a2.set_ylim(0.53, 0.73)
    a2.set_xlabel("Trial")
    a2.set_ylabel("Objective (single seed)")
    a2.set_title("Optuna TPE search: 50 trials per model")
    a2.legend(loc="lower right")
    save(fig, "fig_tuning")


def fig_confusion():
    s = D.signals("transformer", "test")
    cm = confusion_matrix(s["true_regime"], s["predicted"], labels=CLASSES)
    present = [i for i, c in enumerate(CLASSES) if cm[i].sum() > 0 or cm[:, i].sum() > 0]
    cm = cm[np.ix_(present, present)]
    names = [D.REGIME_LABEL[CLASSES[i]] for i in present]
    share = cm / cm.sum(axis=1, keepdims=True)
    fig, ax = plt.subplots(figsize=(5.8, 4.6))
    ax.imshow(share, cmap="Blues", vmin=0, vmax=1)
    for i in range(len(names)):
        for j in range(len(names)):
            ax.text(j, i, f"{cm[i, j]}\n{100 * share[i, j]:.0f}%", ha="center", va="center", fontsize=10,
                    color="white" if share[i, j] > 0.55 else INK)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True (frozen HMM)")
    ax.grid(False)
    ax.set_title("Transformer ensemble, test year (rows sum to 100%)")
    save(fig, "fig_confusion_test")


def fig_replay():
    preds, days = D.replay_tables()
    preds["day"] = preds["timestamp"].dt.normalize()
    truth = days.set_index("date")["regime"]
    preds["true"] = truth.reindex(preds["timestamp"].shift(-1).dt.normalize()).to_numpy()
    v = preds.dropna(subset=["true"])
    daily = v.groupby("day").apply(lambda g: pd.Series({"confidence": g["confidence"].mean(),
                                                        "accuracy": (g["predicted_regime"] == g["true"]).mean()}))
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 4.8), sharex=True)
    a1.plot(daily.index, daily["confidence"], color=SERIES[0], lw=1.4)
    a1.axhline(0.5, color="#9aa3ad", lw=0.8)
    a1.set_ylim(0, 1.02)
    a1.set_title("Mean prediction confidence per day (0.5 = low-confidence flag)")
    a2.plot(daily.index, daily["accuracy"].rolling(10, min_periods=3).mean(), color=SERIES[1], lw=1.6)
    a2.set_ylim(0, 1.02)
    a2.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    a2.set_title("Accuracy of next-bar regime forecasts (10-day rolling mean)")
    month_ticks(a2, 2)
    save(fig, "fig_replay")


# ------------------------------------------------------------------ trading
def eq(series):
    return series.resample("D").last().dropna() / 1e5


def fig_trading_test():
    bench = D.benchmarks("test")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
    for ax, system, title in [(a1, "exp1_long_only", "Experiment 1: regime rules (ETF), test year"),
                              (a2, "exp2_tuned_cash", "Experiment 2: probability rulebook, tuned (ETF), test year")]:
        ax.plot(eq(bench["buy_and_hold"]["equity"]).index, eq(bench["buy_and_hold"]["equity"]), color=INK, lw=1.6, label="Buy & hold ETF")
        ax.plot(bench["cash"].index, bench["cash"] / 1e5, color=MUTED, lw=1.6, ls=(0, (1, 2)), label="Cash at 6%")
        for a in D.ARCHS:
            e = eq(D.trade(a, system, "test")["equity"])
            ax.plot(e.index, e, color=MODEL_COLOR[a], lw=1.6, label=NAMES[a])
        lakh_axis(ax)
        ax.set_title(title, fontsize=10)
        month_ticks(ax, 2)
    a2.set_ylabel("")
    a1.legend(loc="upper center", bbox_to_anchor=(1.05, -0.12), ncol=5)
    save(fig, "fig_trading_test")


def fig_trading_fresh():
    bench = D.benchmarks("fresh")
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2), sharey=True)
    for ax, a in zip(axes, D.ARCHS):
        ax.plot(eq(bench["buy_and_hold"]["equity"]).index, eq(bench["buy_and_hold"]["equity"]), color=INK, lw=1.4, label="Buy & hold ETF")
        ax.plot(bench["cash"].index, bench["cash"] / 1e5, color=MUTED, lw=1.4, ls=(0, (1, 2)), label="Cash at 6%")
        for system, color, label in [("exp1_long_only", SERIES[0], "Exp 1 rules (ETF)"), ("exp2_tuned_cash", SERIES[1], "Exp 2 rulebook tuned (ETF)")]:
            e = eq(D.trade(a, system, "fresh")["equity"])
            ax.plot(e.index, e, color=color, lw=1.6, label=label)
        lakh_axis(ax)
        ax.set_title(NAMES[a], fontsize=10)
        month_ticks(ax, 4)
        if ax is not axes[0]:
            ax.set_ylabel("")
    axes[0].legend(loc="upper center", bbox_to_anchor=(1.7, -0.12), ncol=4)
    save(fig, "fig_trading_fresh")


def fig_profit_split():
    r = rj("11_rulebook_test.json")["results"]
    rows = [(f"{NAMES[a]}\n{lab}", r[a][v]["interest_earned"] / 1e3, (r[a][v]["net_profit"] - r[a][v]["interest_earned"]) / 1e3, r[a][v]["net_profit"] / 1e3)
            for a in D.ARCHS for v, lab in [("default", "default"), ("tuned_cash", "tuned")]]
    fig, ax = plt.subplots(figsize=(12, 4.2))
    x = np.arange(len(rows))
    ax.bar(x - 0.2, [q[1] for q in rows], 0.38, color="#9ec5f4", label="Interest on idle cash", zorder=3)
    ax.bar(x + 0.2, [q[2] for q in rows], 0.38, color=SERIES[1], label="Trading P&L (buy/sell decisions)", zorder=3)
    ax.scatter(x, [q[3] for q in rows], marker="D", s=36, color=INK, zorder=4, label="Total profit")
    ax.axhline(0, color="#7b8591", lw=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels([q[0] for q in rows], fontsize=8.8)
    ax.set_ylabel("Rs thousand")
    ax.grid(axis="x", visible=False)
    ax.set_title("Experiment 2 rulebook, test year (ETF): where the profit came from")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=3)
    save(fig, "fig_profit_split")


def fig_chained():
    f = rj("12_fresh_results.json")
    t2 = rj("11_rulebook_test.json")
    label = {"exp1_long_only": "Exp 1 rules", "exp2_tuned_cash": "Exp 2 rulebook (tuned)"}
    rows = [(f"{NAMES[a]} · {label[k]}", e["systems"][k]["test_year_final"] * e["systems"][k]["final_capital"] / 1e6)
            for a, e in f["architectures"].items() for k in label]
    rows.sort(key=lambda q: q[1])
    bh = t2["buy_and_hold"]["final_capital"] * f["buy_and_hold"]["final_capital"] / 1e6
    cash = t2["cash_only_final"] * f["cash_only_final"] / 1e6
    fig, ax = plt.subplots(figsize=(12, 4.8))
    y = np.arange(len(rows)) + 1
    halo = dict(boxstyle="round,pad=0.15", fc="white", ec="none")
    for yi, (name, v) in zip(y, rows):
        up = v >= 1e6
        ax.barh(yi, v / 1e5 - 10, left=10, color=SERIES[0] if up else SERIES[1], height=0.62, zorder=3)
        x_label = v / 1e5 + (0.03 if up else -0.03)
        if up and x_label < bh / 1e5 + 0.03 and v / 1e5 + 0.45 > bh / 1e5:   # keep clear of the buy & hold line
            x_label = bh / 1e5 + 0.04
        ax.text(x_label, yi, inr(v), va="center", ha="left" if up else "right",
                fontsize=9, color=INK, bbox=halo, zorder=5)
    ax.axvline(bh / 1e5, color=INK, lw=1.6, zorder=4)
    ax.axvline(cash / 1e5, color=MUTED, lw=1.6, ls=(0, (1, 2)), zorder=4)
    ax.text(bh / 1e5, 0.25, f" Buy & hold {inr(bh)}", fontsize=9, color=INK, va="center", ha="left", bbox=halo, zorder=5)
    ax.text(cash / 1e5, 0.25, f"Cash at 6% {inr(cash)} ", fontsize=9, color=INK2, va="center", ha="right", bbox=halo, zorder=5)
    ax.axvline(10, color="#9aa3ad", lw=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels([q[0] for q in rows])
    ax.set_ylim(-0.3, len(rows) + 0.6)
    ax.set_xlim(9.0, 11.7)
    ax.set_xlabel("Value of Rs 10 lakh after the test year and the fresh period (Rs lakh)")
    ax.grid(axis="y", visible=False)
    ax.set_title("Both unseen periods chained (May 2024 – Sep 2026), realistic ETF systems", pad=10)
    save(fig, "fig_chained")


def fig_gantt():
    tasks = [("Literature survey", (1, 2), [(1, 2)]),
             ("Data pipeline", (2, 3), [(1, 1), (7, 7)]),
             ("Feature engineering", (3, 3), [(1, 1), (7, 7)]),
             ("HMM regime labelling", (4, 5), [(2, 2), (7, 7)]),
             ("LSTM training", (5, 7), [(2, 2), (7, 7)]),
             ("CNN-BiLSTM-Attention training", (8, 9), [(2, 2), (7, 7)]),
             ("Transformer training", (9, 10), [(2, 2), (7, 7)]),
             ("Testing & comparison", (10, 11), [(5, 5), (7, 7)]),
             ("Hyperparameter tuning", (11, 12), [(5, 5), (7, 7)]),
             ("Trading test", (12, 13), [(7, 7)]),
             ("Live validation → replay + forward test", (13, 14), [(7, 7)]),
             ("Dashboard + report", (13, 15), [(7, 7)])]
    fig, ax = plt.subplots(figsize=(12, 5.4))
    for i, (name, (ps, pe), done) in enumerate(tasks):
        y = len(tasks) - 1 - i
        ax.barh(y + 0.18, pe - ps + 1, left=ps - 0.5, height=0.3, color="#aab6c4", zorder=3)
        for s, e in done:
            ax.barh(y - 0.18, e - s + 1, left=s - 0.5, height=0.3, color="#1a9c6d", zorder=3)
    ax.barh(len(tasks) - 1 - 11 - 0.18, 8, left=7.5, height=0.3, color="#ffffff", edgecolor="#1a9c6d", hatch="////", lw=0.8, zorder=4)
    ax.axvspan(6.5, 7.5, color="#f3e9d2", zorder=1)
    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels([t[0] for t in tasks][::-1])
    ax.set_xticks(range(1, 16))
    ax.set_xticklabels([f"W{w}" for w in range(1, 16)])
    ax.set_xlim(0.5, 15.5)
    ax.grid(axis="y", visible=False)
    ax.legend(handles=[Patch(color="#aab6c4", label="Planned (Review 1 plan)"), Patch(color="#1a9c6d", label="Completed"),
                       Patch(fc="#ffffff", ec="#1a9c6d", hatch="////", label="Black-book report, in progress"),
                       Patch(color="#f3e9d2", label="Review 2 = Week 7")], loc="upper center", bbox_to_anchor=(0.45, -0.07), ncol=4)
    ax.set_title("Plan vs actual, 15-week schedule (Week 1 = 3 Aug 2026)")
    save(fig, "fig_gantt")


def fig_rulebook_flow():
    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4.8)
    ax.axis("off")

    def node(x, y, w, h, text, face, edge):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.1", fc=face, ec=edge, lw=1.3))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9, color=INK, linespacing=1.3)

    w, h, gap, top, low = 2.05, 1.1, 0.38, 3.4, 1.3
    xs = [0.1 + i * (w + gap) for i in range(5)]
    node(xs[0], top, w, h, "Day close:\nmodel gives P(bull),\nP(sideways), P(bear),\nP(high-vol)", "#eef3fb", SERIES[0])
    node(xs[1], top, w, h, "Stop-loss hit?\nportfolio 8% below\nits peak since entry", "#fdf3ea", SERIES[1])
    node(xs[2], top, w, h, "SELL signal?\nP(bear)+P(high-vol)\n≥ 0.5 for 2 days", "#fdf3ea", SERIES[1])
    node(xs[3], top, w, h, "BUY signal?\nP(bull) ≥ 0.6\nfor 2 days", "#eefaf4", SERIES[2])
    node(xs[4], top, w, h, "HOLD\nkeep the position\n(sideways never trades)", "#f4f6f8", MUTED)
    node(xs[1], low, w, h, "EXIT to cash\n5-day cooldown,\nthen a fresh BUY signal", "#ffffff", SERIES[1])
    node(xs[2], low, w, h, "SELL everything\n→ cash\n(futures: go short)", "#ffffff", SERIES[1])
    node(xs[3], low, w, h, "BUY / ADD\n100% if P(bull) ≥ 0.75\notherwise 50%", "#ffffff", SERIES[2])
    for i in range(4):
        arrow(ax, xs[i] + w, top + h / 2, xs[i + 1], top + h / 2)
        if i > 0:
            ax.text(xs[i] + w + gap / 2, top + h / 2 + 0.08, "no", ha="center", va="bottom", fontsize=8.5, color=INK2)
    for i in (1, 2, 3):
        arrow(ax, xs[i] + w / 2, top, xs[i] + w / 2, low + h)
        ax.text(xs[i] + w / 2 + 0.08, (top + low + h) / 2, "yes", ha="left", va="center", fontsize=8.5, color=INK2)
    ax.text(xs[0], 0.35, "Checked in this order once per trading day; trades execute at that day's close. "
            "ETF costs 0.10% per side + Rs 15.93 per sell; idle cash earns 6% a year.", fontsize=8.8, color=INK2, va="bottom")
    save(fig, "fig_rulebook_flow")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for fn in [fig_architecture, fig_models, fig_split_timeline, fig_regimes_full, fig_test_timeline, fig_classification_periods,
               fig_tuning, fig_confusion, fig_replay, fig_trading_test, fig_trading_fresh, fig_profit_split, fig_chained,
               fig_gantt, fig_rulebook_flow]:
        fn()
