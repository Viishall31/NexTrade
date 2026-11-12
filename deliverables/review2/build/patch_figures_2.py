"""Second layout pass: chained-results labels, readable date ticks on equity charts."""
from pathlib import Path

p = Path(__file__).with_name("make_figures.py")
s = p.read_text(encoding="utf-8")

# helpers: Indian digit grouping + month ticks
s = s.replace('''def lakh_axis(ax):''', '''def inr(v):
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


def lakh_axis(ax):''', 1)
s = s.replace("import matplotlib.pyplot as plt\n", "import matplotlib.dates\nimport matplotlib.pyplot as plt\n", 1)

# equity charts: month ticks instead of rotated ISO dates
old_test = '''        lakh_axis(ax)
        ax.set_title(title, fontsize=10)
        ax.tick_params(axis="x", rotation=30)'''
new_test = '''        lakh_axis(ax)
        ax.set_title(title, fontsize=10)
        month_ticks(ax, 2)'''
assert old_test in s
s = s.replace(old_test, new_test)
old_fresh = '''        lakh_axis(ax)
        ax.set_title(NAMES[a], fontsize=10)
        ax.tick_params(axis="x", rotation=30)'''
new_fresh = '''        lakh_axis(ax)
        ax.set_title(NAMES[a], fontsize=10)
        month_ticks(ax, 4)'''
assert old_fresh in s
s = s.replace(old_fresh, new_fresh)
s = s.replace('axes[0].legend(loc="upper center", bbox_to_anchor=(1.7, -0.25), ncol=4)',
              'axes[0].legend(loc="upper center", bbox_to_anchor=(1.7, -0.12), ncol=4)')
s = s.replace('a1.legend(loc="upper center", bbox_to_anchor=(1.05, -0.2), ncol=5)',
              'a1.legend(loc="upper center", bbox_to_anchor=(1.05, -0.12), ncol=5)')

# chained chart: rupee labels with halo, reference labels in a clear band below the bars
start = s.index("def fig_chained():")
end = s.index("def fig_gantt():")
new = '''def fig_chained():
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
        ax.text(v / 1e5 + (0.03 if up else -0.03), yi, inr(v), va="center", ha="left" if up else "right",
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


'''
s = s[:start] + new + s[end:]
p.write_text(s, encoding="utf-8")
print("patched")
