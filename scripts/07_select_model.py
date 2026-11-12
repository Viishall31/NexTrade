"""Step 7a: apply the model-selection rule (spec 9.3) on VALIDATION results only.

Rule: keep architectures whose tuned 5-seed macro-F1 is within `f1_tolerance` of the best;
among those, the highest 5-seed Sharpe wins. Written to reports/07_selection.json before
any test data is evaluated, so the choice cannot be influenced by the test set.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from regime.config import ROOT, load_config
from regime.models import ARCHITECTURES


def main() -> None:
    cfg = load_config()
    freq = "daily"
    tol = cfg["selection"]["f1_tolerance"]
    rep = ROOT / "reports"
    out = rep / "07_selection.json"
    if out.exists():
        raise SystemExit(f"{out.name} already exists — the selection is frozen. Delete it deliberately to redo.")

    cands = {}
    for arch in ARCHITECTURES:
        c = json.loads((rep / f"06_tuning_{freq}_{arch}.json").read_text())["chosen"]
        cands[arch] = {"macro_f1": c["mean"]["macro_f1"], "sharpe": c["mean"]["sharpe"],
                       "objective": c["mean"]["objective"], "trial": c["trial"], "params": c["params"]}

    best_f1 = max(c["macro_f1"] for c in cands.values())
    best_sharpe = max(c["sharpe"] for c in cands.values())
    for arch, c in cands.items():
        c["within_f1_tolerance"] = best_f1 - c["macro_f1"] <= tol
        # FR-E4: flag disagreement between the two criteria instead of averaging it away.
        flags = []
        if c["macro_f1"] == best_f1 and c["sharpe"] < best_sharpe - 0.05:
            flags.append("best classifier but not best Sharpe")
        if c["sharpe"] == best_sharpe and not c["within_f1_tolerance"]:
            flags.append("best Sharpe but macro-F1 outside tolerance")
        c["flags"] = flags

    eligible = [a for a, c in cands.items() if c["within_f1_tolerance"]]
    winner = max(eligible, key=lambda a: cands[a]["sharpe"])
    decision = {
        "decided_at": datetime.now().isoformat(timespec="seconds"),
        "based_on": "validation split (Jan 2022 – Apr 2024), tuned configs, 5-seed means",
        "rule": f"macro-F1 within {tol * 100:.0f} pp of best ({best_f1:.3f}); then highest Sharpe",
        "candidates": cands, "eligible": eligible, "selected": winner,
    }
    out.write_text(json.dumps(decision, indent=2))
    for arch, c in cands.items():
        print(f"{arch:16s} F1 {c['macro_f1']:.3f}  Sharpe {c['sharpe']:.2f}  eligible={c['within_f1_tolerance']}  {c['flags']}")
    print(f"SELECTED: {winner}")


if __name__ == "__main__":
    main()
