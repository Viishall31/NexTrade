"""Integrity dashboard (spec FR-U1..U4, EI-5): read-only view of regimes, models, replay and trading.

Run:  streamlit run dashboard/app.py
"""
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

import charts
import data as D

st.set_page_config(page_title="Nifty 50 Regime Detection", page_icon="📈", layout="wide")


def theme() -> str:
    try:
        return st.context.theme.type or "light"
    except Exception:
        return "light"


def inr(x: float, signed: bool = False) -> str:
    """Indian digit grouping: 1021018 -> Rs 10,21,018."""
    neg, n = x < 0, int(round(abs(x)))
    s = str(n)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        head = ",".join([head[max(0, i - 2):i] for i in range(len(head), 0, -2)][::-1])
        s = f"{head},{tail}"
    sign = "−" if neg else ("+" if signed and n else "")
    return f"{sign}Rs {s}"


def lakh(x: float, signed: bool = False) -> str:
    """Compact tile value: 1082677 -> Rs 10.83 lakh."""
    # ASCII hyphen: st.metric only treats a delta as negative (red, down arrow) when it starts with "-"
    sign = "-" if x < 0 else ("+" if signed and x > 0 else "")
    return f"{sign}Rs {abs(x) / 1e5:.2f} lakh"


def ensemble_scores(arch: str, period: str) -> dict:
    s = D.signals(arch, period)
    labels = sorted(set(s["true_regime"]))
    return {"accuracy": accuracy_score(s["true_regime"], s["predicted"]),
            "macro_f1": f1_score(s["true_regime"], s["predicted"], labels=labels, average="macro", zero_division=0)}


# --------------------------------------------------------------------------------------------- pages
def overview():
    st.title("AI-based market regime detection · Nifty 50")
    st.caption("HMM regime labels → LSTM / CNN-BiLSTM-Attention / Transformer classifiers → tuning → selection → "
               "walk-forward replay → rule-based trading. Everything shown is read from saved results.")

    fresh = D.report("12_fresh_results.json")
    test_deployed = D.report("07_test_results.json")["deployed_seed_ensemble"]
    t_fresh = fresh["architectures"]["transformer"]["classification_fresh"]
    realistic = [(a, k, s) for a, e in fresh["architectures"].items() for k, s in e["systems"].items() if "short" not in k]
    chained = {}
    for a, e in fresh["architectures"].items():
        for k, s in e["systems"].items():
            chained[(a, k)] = s["test_year_final"] * s["final_capital"] / 1e6
    bh_chain = D.report("11_rulebook_test.json")["buy_and_hold"]["final_capital"] * fresh["buy_and_hold"]["final_capital"] / 1e6
    cash_chain = D.report("11_rulebook_test.json")["cash_only_final"] * fresh["cash_only_final"] / 1e6
    best_key = max((k for k in chained if "short" not in k[1]), key=chained.get)

    st.subheader("Verdict")
    st.info("**Regime classification works; trading on the regimes does not beat a liquid fund.** "
            "The classifiers reproduce the HMM regimes on unseen data, but the HMM regimes change only after the market "
            "has moved, so trading signals arrive late. The consistent benefit is lower drawdown.", icon="🧭")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Accuracy · test year", f"{test_deployed['accuracy']:.1%}",
              help="Selected Transformer, 5-seed ensemble, vs frozen-HMM labels, May 2024 – Apr 2025 (Nifty50_test.csv).")
    c2.metric("Accuracy · fresh data", f"{t_fresh['accuracy']:.1%}",
              help="Same frozen Transformer on 8 Apr 2025 – 15 Sep 2026 (yfinance): data no decision ever saw.")
    c3.metric("Profitable ETF systems · fresh", f"{sum(s['final_capital'] > 1e6 for _, _, s in realistic)} of {len(realistic)}",
              help="ETF systems (Exp 1 rules, Exp 2 rulebook default and tuned) × 3 models, starting from Rs 10 lakh.")
    c4.metric("Best ETF system · 2.4 years", lakh(chained[best_key]),
              help=f"{D.NAMES[best_key[0]]}, {D.SYSTEMS[best_key[1]]}. Test year and fresh period chained from Rs 10 lakh. "
                   f"Buy & hold: {inr(bh_chain)}, cash at 6%: {inr(cash_chain)}.")

    st.subheader("Pipeline and where to look")
    steps = pd.DataFrame([
        ("1–2", "Clean 15-min data, 13 technical features", "Data cleaned: duplicates, special sessions, gaps", "01_data_cleaning.json · 02_features.json"),
        ("3", "Gaussian HMM, 4 regimes, frozen", "Regimes page", "03_hmm.md"),
        ("4–6", "Train 3 architectures, Optuna tuning (50 trials each)", "Models page", "04_default_daily.md · 06_tuning_daily.md"),
        ("7", "Select on validation, one-time test", "Models page", "07_findings.md · 07_test_results.md"),
        ("8–9", "15-min Transformer + bar-by-bar replay", "Replay page", "08_15min_validation.md · 09_replay_test.md"),
        ("10–11", "Trading rules: Exp 1 regime rules, Exp 2 probability rulebook", "Trading page", "10_findings.md · 11_findings.md · 11_rulebook.md"),
        ("12", "Forward test on fresh data, all frozen", "Trading page (fresh)", "12_findings.md · 12_fresh_results.md"),
    ], columns=["Step", "What", "Dashboard", "Report (reports/)"])
    st.dataframe(steps, hide_index=True, width="stretch")


def regimes_page():
    st.title("Market regimes")
    st.caption("Ground truth = frozen Gaussian HMM (20-day return + 20-day volatility), filtered forward in time so a "
               "day's label never uses later data. Model forecasts exist from Jan 2022 (validation) onward.")
    df = D.daily_regimes()
    lo, hi = df.index.min().date(), df.index.max().date()

    f1, f2, f3 = st.columns([2, 1, 2])
    date_range = f1.slider("Date range", min_value=lo, max_value=hi, value=(pd.Timestamp("2022-01-01").date(), hi), format="MMM YYYY")
    model = f2.selectbox("Model forecast", ["None"] + [D.NAMES[a] for a in D.ARCHS], index=3)
    regimes = f3.multiselect("Regimes", D.REGIMES, default=D.REGIMES, format_func=D.REGIME_LABEL.get)

    view = df.loc[str(date_range[0]):str(date_range[1])]
    arch = next((a for a in D.ARCHS if D.NAMES[a] == model), None)
    pred = D.predictions(arch).loc[str(date_range[0]):str(date_range[1])] if arch else None
    if pred is not None and pred.empty:
        st.warning("No model forecasts in this range (forecasts start in January 2022).")
        pred = None
    st.plotly_chart(charts.regime_timeline(view, pred, model, regimes or D.REGIMES, D.REGIME_LABEL, theme()), width="stretch")

    shares = df.groupby("split")["regime"].value_counts(normalize=True).unstack().reindex(["train", "val", "test", "fresh"])
    shares = shares.reindex(columns=D.REGIMES).fillna(0).rename(columns=D.REGIME_LABEL)
    shares.index = ["Train (2016–2021)", "Validation (2022 – Apr 2024)", "Test year", "Fresh data"]
    st.subheader("Regime mix by period")
    st.dataframe(shares.style.format("{:.0%}"), width="stretch")

    with st.expander("Table view"):
        table = view[view["regime"].isin(regimes)][["close", "regime", "p_bull", "p_sideways", "p_bear", "p_high_vol"]].copy()
        if arch:
            p = D.predictions(arch)
            table = table.join(p[["predicted", "confidence"]], how="left")
        table["regime"] = table["regime"].map(D.REGIME_LABEL)
        st.dataframe(table.sort_index(ascending=False), width="stretch",
                     column_config={"p_bull": st.column_config.NumberColumn("HMM P(bull)", format="%.2f", help="Filtered HMM state probability"),
                                    "confidence": st.column_config.NumberColumn("Model confidence", format="%.2f",
                                                                                help="Highest class probability of the 5-seed ensemble")})


def models_page():
    st.title("Models")
    tab_val, tab_period, tab_cm = st.tabs(["Tuning (validation)", "Accuracy by period", "Confusion matrices"])

    with tab_val:
        st.caption("Validation Jan 2022 – Apr 2024. Default = spec hyperparameters; tuned = Optuna TPE (50 trials) with the "
                   "top 3 re-run on 5 seeds. Objective = 0.6 × macro-F1 + 0.4 × normalised Sharpe.")
        default_bt = D.report("05_backtest_daily.json")["models"]
        rows = []
        for a in D.ARCHS:
            chosen = D.report(f"06_tuning_daily_{a}.json")["chosen"]
            rows += [{"Model": D.NAMES[a], "Config": "Default", "Macro-F1": default_bt[a]["macro_f1_mean"], "Sharpe": default_bt[a]["sharpe_mean"]},
                     {"Model": D.NAMES[a], "Config": "Tuned", "Macro-F1": chosen["mean"]["macro_f1"], "Sharpe": chosen["mean"]["sharpe"]}]
        tbl = pd.DataFrame(rows)
        st.plotly_chart(charts.grouped_bars(tbl, "Model", "Macro-F1", "Config", ["Default", "Tuned"], theme(),
                                            "Validation macro-F1, 5-seed mean", ".3f"), width="stretch")
        st.dataframe(tbl, hide_index=True, width="stretch",
                     column_config={"Macro-F1": st.column_config.NumberColumn(format="%.3f", help="Unweighted mean F1 over the four regimes"),
                                    "Sharpe": st.column_config.NumberColumn(format="%.2f", help="Spec strategy (100/50/25/0% exposure), excess over 6%")})
        sel = D.report("07_selection.json")
        st.success(f"Selected on validation (frozen {sel['decided_at']}): **{D.NAMES[sel['selected']]}**. Rule: {sel['rule']}.", icon="✅")

    with tab_period:
        st.caption("5-seed ensembles vs frozen-HMM labels. Macro-F1 averages only the regimes that occur in each period.")
        rows = [{"Period": name, "Model": D.NAMES[a], **ensemble_scores(a, p)}
                for p, name in [("val", "Validation"), ("test", "Test year"), ("fresh", "Fresh data")] for a in D.ARCHS]
        tbl = pd.DataFrame(rows)
        metric = st.radio("Metric", ["macro_f1", "accuracy"], horizontal=True, format_func={"macro_f1": "Macro-F1", "accuracy": "Accuracy"}.get)
        st.plotly_chart(charts.grouped_bars(tbl, "Period", metric, "Model", [D.NAMES[a] for a in D.ARCHS], theme(),
                                            "Ensemble " + ("macro-F1" if metric == "macro_f1" else "accuracy") + " by period", ".2f"),
                        width="stretch")
        st.dataframe(tbl.pivot(index="Model", columns="Period", values=metric)[["Validation", "Test year", "Fresh data"]].style.format("{:.3f}"),
                     width="stretch")

    with tab_cm:
        c1, c2 = st.columns(2)
        arch = c1.selectbox("Model", D.ARCHS, format_func=D.NAMES.get, index=2)
        period = c2.selectbox("Period", ["val", "test", "fresh"], format_func={"val": "Validation", **{k: v for k, v in D.PERIODS.items()}}.get, index=1)
        s = D.signals(arch, period)
        classes = D.config()["sequence"]["classes"]
        cm = confusion_matrix(s["true_regime"], s["predicted"], labels=classes)
        st.plotly_chart(charts.confusion_heatmap(cm, classes, D.REGIME_LABEL, theme(), f"{D.NAMES[arch]} · rows sum to 100%"), width="stretch")


def replay_page():
    st.title("Walk-forward replay · 15-minute Transformer")
    st.caption("Replaces Kite Connect live validation: the test file's 5,800 bars were fed one at a time to the frozen 5-seed "
               "15-min Transformer; the frozen HMM advanced one step at each day close. No orders are placed anywhere.")
    r = D.report("09_replay_test.json")
    preds, days = D.replay_tables()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bars processed", f"{r['uptime']['bars_received']:,} / {r['uptime']['bars_expected']:,}", help="Spec NFR-4 requires ≥ 95%.")
    c2.metric("Latency per bar (p95)", f"{r['latency_ms']['p95']:.0f} ms", help="Features + 5-model inference on CPU. Spec NFR-3: < 2,000 ms.")
    c3.metric("Accuracy · replay", f"{r['classification']['accuracy']:.1%}",
              delta=f"{100 * r['replay_vs_validation']['accuracy']['gap']:.1f} pts vs validation",
              help="Prediction for bar t+1 vs the frozen HMM label of that bar's day.")
    c4.metric("Matches batch pipeline", f"{r['consistency_with_batch_pipeline']['prediction_agreement']:.0%}",
              help="Bar-by-bar predictions identical to the batch pipeline: no look-ahead in the live path.")

    preds["day"] = preds["timestamp"].dt.normalize()
    truth = days.set_index("date")["regime"]
    preds["next_day"] = preds["timestamp"].shift(-1).dt.normalize()
    preds["true"] = truth.reindex(preds["next_day"]).to_numpy()
    valid = preds.dropna(subset=["true"])
    daily = valid.groupby("day").agg(confidence=("confidence", "mean"),
                                     accuracy=("predicted_regime", lambda s: float((s == valid.loc[s.index, "true"]).mean())))
    st.plotly_chart(charts.replay_chart(daily, theme()), width="stretch")

    st.subheader("Replay vs validation backtest")
    gap = pd.DataFrame(r["replay_vs_validation"]).T.rename(index={"macro_f1": "Macro-F1", "accuracy": "Accuracy", "sharpe": "Sharpe",
                                                                   "max_drawdown": "Max drawdown", "cumulative_return": "Cumulative return"})
    st.dataframe(gap.style.format("{:+.3f}", subset=["gap"]).format("{:.3f}", subset=["validation", "replay"]), width="stretch")

    st.subheader("Prediction log")
    f1, f2, f3 = st.columns([2, 2, 1])
    dr = f1.date_input("Days", value=(preds["day"].min().date(), preds["day"].max().date()),
                       min_value=preds["day"].min().date(), max_value=preds["day"].max().date())
    regs = f2.multiselect("Predicted regime", D.REGIMES, default=D.REGIMES, format_func=D.REGIME_LABEL.get)
    low_only = f3.toggle("Low confidence only", help="Confidence below 0.5 is flagged, per spec section 10.")
    log = preds[preds["predicted_regime"].isin(regs)]
    if isinstance(dr, tuple) and len(dr) == 2:
        log = log[(log["day"] >= pd.Timestamp(dr[0])) & (log["day"] <= pd.Timestamp(dr[1]))]
    if low_only:
        log = log[log["low_confidence"] == 1]
    st.dataframe(log[["timestamp", "close", "predicted_regime", "confidence", "low_confidence", "p_bull", "p_sideways", "p_bear",
                      "p_high_vol", "latency_ms"]].sort_values("timestamp", ascending=False),
                 hide_index=True, width="stretch",
                 column_config={"confidence": st.column_config.ProgressColumn("Confidence", min_value=0.0, max_value=1.0, format="%.2f"),
                                "latency_ms": st.column_config.NumberColumn("Latency (ms)", format="%.0f")})


def trading_page():
    st.title("Trading from Rs 10 lakh")
    st.caption("Frozen rules only. Exp 1 = regime-map rules searched on validation; Exp 2 = probability rulebook "
               "(designed after the test year was seen, so post-hoc). Costs included; idle cash earns 6%. "
               "Futures versions are idealized (spot prices, fractional contracts).")
    f1, f2, f3 = st.columns([1.3, 1, 2.2])
    period = f1.radio("Period", list(D.PERIODS), format_func=D.PERIODS.get)
    arch = f2.selectbox("Model", D.ARCHS, format_func=D.NAMES.get)
    systems = f3.multiselect("Systems", list(D.SYSTEMS), default=["exp1_long_only", "exp2_default", "exp2_tuned_cash"],
                             format_func=D.SYSTEMS.get, max_selections=4)
    start = D.config()["trading"]["initial_capital"]
    bench = D.benchmarks(period)
    bh = bench["buy_and_hold"]

    rows, lines = [], {}
    for k in systems:
        res = D.trade(arch, k, period)
        lines[D.SYSTEMS[k]] = (res["equity"], "system")
        rows.append({"System": D.SYSTEMS[k], "Rule": res["rule_name"], "Amount left": res["final_capital"],
                     "Profit": res["net_profit"], "Cash interest": res["interest_earned"],
                     "Trading P&L": res["net_profit"] - res["interest_earned"], "Max drawdown": res["max_drawdown"],
                     "Trades": res["n_trades"], "Costs": res["total_costs"]})
    lines["Buy & hold ETF"] = (bh["equity"], "buy_and_hold")
    lines["Cash at 6%"] = (bench["cash"], "cash")
    rows += [{"System": "Buy & hold ETF", "Rule": "–", "Amount left": bh["final_capital"], "Profit": bh["net_profit"],
              "Cash interest": bh["interest_earned"], "Trading P&L": bh["net_profit"] - bh["interest_earned"],
              "Max drawdown": bh["max_drawdown"], "Trades": bh["n_trades"], "Costs": bh["total_costs"]},
             {"System": "Cash at 6%", "Rule": "–", "Amount left": bench["cash"].iloc[-1], "Profit": bench["cash"].iloc[-1] - start,
              "Cash interest": bench["cash"].iloc[-1] - start, "Trading P&L": 0.0, "Max drawdown": 0.0, "Trades": 0, "Costs": 0.0}]

    if systems:
        best = max(rows[:len(systems)], key=lambda r: r["Amount left"])
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Best selected system", lakh(best["Amount left"]), delta=lakh(best["Profit"], signed=True),
                  help=f"{best['System']}: final portfolio value from Rs 10,00,000.")
        k2.metric("Its trading P&L", lakh(best["Trading P&L"], signed=True),
                  help="Profit minus interest earned on idle cash: what the buy/sell decisions themselves made.")
        k3.metric("Buy & hold ETF", lakh(bh["final_capital"]), delta=lakh(bh["net_profit"], signed=True))
        k4.metric("Cash at 6%", lakh(bench["cash"].iloc[-1]), delta=lakh(bench["cash"].iloc[-1] - start, signed=True))

    st.plotly_chart(charts.equity_chart(lines, start, theme(), f"{D.NAMES[arch]} · {D.PERIODS[period]}"), width="stretch")
    tbl = pd.DataFrame(rows)
    money = {c: st.column_config.NumberColumn(c, format="%,.0f") for c in ["Amount left", "Profit", "Cash interest", "Trading P&L", "Costs"]}
    money["Trading P&L"] = st.column_config.NumberColumn("Trading P&L", format="%,.0f", help="Profit excluding interest on idle cash")
    money["Max drawdown"] = st.column_config.NumberColumn("Max drawdown", format="percent", help="Largest peak-to-trough fall of the portfolio")
    st.dataframe(tbl, hide_index=True, width="stretch", column_config=money)

    if systems:
        st.subheader("Trade log")
        which = st.selectbox("System", systems, format_func=D.SYSTEMS.get)
        t = D.trade(arch, which, period)["trades"]
        if t.empty:
            st.write("No trades.")
        else:
            cols = [c for c in ["time", "action", "reason", "price", "value", "cost", "position_after", "target_exposure",
                                "p_bull", "p_bear", "p_high_vol", "equity_before"] if c in t.columns]
            st.dataframe(t[cols], hide_index=True, width="stretch",
                         column_config={"price": st.column_config.NumberColumn("Nifty", format="%,.0f"),
                                        "value": st.column_config.NumberColumn("Traded value", format="%,.0f"),
                                        "cost": st.column_config.NumberColumn("Cost", format="%,.0f"),
                                        "equity_before": st.column_config.NumberColumn("Portfolio before", format="%,.0f")})

    with st.expander(f"Scorecard · all models and systems · {D.PERIODS[period]}"):
        score = []
        for a in D.ARCHS:
            for k in D.SYSTEMS:
                res = D.trade(a, k, period)
                score.append({"Model": D.NAMES[a], "System": D.SYSTEMS[k], "Amount left": res["final_capital"],
                              "Trading P&L": res["net_profit"] - res["interest_earned"],
                              "Profit?": "✓" if res["final_capital"] > start else "✗",
                              "Beat buy & hold?": "✓" if res["final_capital"] > bh["final_capital"] else "✗",
                              "Beat cash?": "✓" if res["final_capital"] > bench["cash"].iloc[-1] else "✗"})
        st.dataframe(pd.DataFrame(score).sort_values("Amount left", ascending=False), hide_index=True, width="stretch",
                     column_config={"Amount left": st.column_config.NumberColumn(format="%,.0f"),
                                    "Trading P&L": st.column_config.NumberColumn(format="%,.0f")})


def method_page():
    st.title("Method, deviations and limitations")
    st.subheader("Where the implementation differs from the specification")
    dev = pd.DataFrame([
        ("Data", "Daily 2015–present + live 15-min via Kite", "Vendor 15-min file 2015–Apr 2025 (daily resampled); yfinance daily after", "No Kite account; replay + fresh forward test instead"),
        ("Features", "15 incl. OBV slope, VWAP, India VIX", "13 indicators", "No volume in the index data; VIX not used"),
        ("HMM emissions", "1-day log return + 20-day vol", "20-day log return + 20-day vol", "1-day returns gave volatility-only states (2023 rally labelled sideways)"),
        ("HMM labels", "argmax posterior", "Filtered (forward-only) posterior", "Smoothed posteriors use future days and cannot be reproduced live"),
        ("Split", "Train 2015–21 / val 2022 / test 2023+", "Train 2016–21 / val 2022–Apr 2024 / test = test file", "EMA-200 warm-up; test file kept untouched until Step 7"),
        ("Tuning", "50 trials, best trial", "50 trials + top-3 re-run on 5 seeds", "Single-seed winners were lucky seeds (0.71 → 0.63)"),
        ("CNN-BiLSTM-Attn heads", "Tunable", "Not tuned", "Spec 6.2 defines additive attention, which has no heads"),
        ("15-min model", "All three tuned", "Selected Transformer only, daily hyperparameters", "CPU budget; trained on Colab GPU"),
        ("Live validation", "≥ 2 weeks on Kite websocket", "Bar-by-bar replay of the test file", "No broker API; replay proven identical to batch pipeline"),
        ("Trading rules", "Spec exposure map", "Plus Exp 1 rule search and Exp 2 rulebook", "Requested by the project guide"),
    ], columns=["Area", "Specification", "Implemented", "Why"])
    st.dataframe(dev, hide_index=True, width="stretch")

    st.subheader("Limitations")
    st.markdown(
        "- **Lagging labels.** HMM regimes are identified after the move, so accurate classifiers inherit the delay; the best classifier (Transformer) is the worst trader.\n"
        "- **Slow declines look sideways.** The HMM learned 'bear' as elevated volatility; the Oct 2024 – Mar 2025 grind is mostly 'sideways'.\n"
        "- **Few regime switches.** About 9 per year, so validation and test periods contain only a handful of regime episodes; high-volatility days are rare (≈ 2–4%).\n"
        "- **Post-hoc Experiment 2.** The rulebook was designed after seeing the test year; the fresh-data forward test shows its test-year profit did not persist.\n"
        "- **Idealized futures.** Spot prices, fractional contracts, no margin calls; one real Nifty lot exceeds Rs 10 lakh.\n"
        "- **Cost model is approximate.** All-in percentages; verify with a broker's calculator.")
    with st.expander("Trading rulebook (Experiment 2)"):
        st.markdown(D.report_text("11_rulebook.md"))


pg = st.navigation([st.Page(overview, title="Overview", icon="🧭", default=True),
                    st.Page(regimes_page, title="Regimes", icon="📊", url_path="regimes"),
                    st.Page(models_page, title="Models", icon="🧠", url_path="models"),
                    st.Page(replay_page, title="Replay", icon="⏱️", url_path="replay"),
                    st.Page(trading_page, title="Trading", icon="💰", url_path="trading"),
                    st.Page(method_page, title="Method & limitations", icon="📝", url_path="method")])
pg.run()
