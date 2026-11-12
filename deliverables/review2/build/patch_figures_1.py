"""One-off layout fixes for make_figures.py (architecture fit, model arrows, flowchart, gantt, labels)."""
from pathlib import Path

p = Path(__file__).with_name("make_figures.py")
s = p.read_text(encoding="utf-8")
rep = [
    ('    w, h, gx = 2.6, 1.55, 0.5\n    xs = [0.15 + i * (w + gx) for i in range(4)]\n    rows = [4.85, 2.65, 0.45]',
     '    w, h, gx = 2.55, 1.4, 0.45\n    xs = [0.1 + i * (w + gx) for i in range(4)]\n    rows = [4.75, 2.6, 0.45]'),
    ('("12  Forward test + dashboard", "fresh data Apr 2025 – Sep 2026\\nall models and rules frozen\\nStreamlit dashboard")',
     '("12  Forward test", "fresh data Apr 2025 – Sep 2026\\nall models and rules frozen\\n+ Streamlit dashboard")'),
    ('    fig, ax = plt.subplots(figsize=(12, 6.6))\n    ax.set_xlim(0, 12)\n    ax.set_ylim(0, 6.6)',
     '    fig, ax = plt.subplots(figsize=(12, 6.4))\n    ax.set_xlim(0, 12)\n    ax.set_ylim(0.3, 6.45)'),
    ('                ax.annotate("", xy=(0.5, y - 0.02), xytext=(0.5, y + 0.1), arrowprops=dict(arrowstyle="-|>", color="#5b6674", lw=1))',
     '                ax.annotate("", xy=(0.5, y - 0.22), xytext=(0.5, y - 0.01), arrowprops=dict(arrowstyle="-|>", color="#5b6674", lw=1, shrinkA=0, shrinkB=0))'),
    ('        a1.text(pd.Timestamp(d), df["close"].max() * 0.98, " " + label, fontsize=8.5, color=MUTED, va="top")',
     '        a1.text(pd.Timestamp(d), df["close"].min() * 1.02, " " + label, fontsize=8.5, color=MUTED, va="bottom")'),
    ('    ax.barh(len(tasks) - 1 - 11 + 0.18, 8, left=7.5, height=0.3, color="#ffffff", edgecolor="#1a9c6d", hatch="////", lw=0.8, zorder=4)',
     '    ax.barh(len(tasks) - 1 - 11 - 0.18, 8, left=7.5, height=0.3, color="#ffffff", edgecolor="#1a9c6d", hatch="////", lw=0.8, zorder=4)'),
]
for a, b in rep:
    assert a in s, a[:70]
    s = s.replace(a, b)

start = s.index("def fig_rulebook_flow():")
end = s.index('if __name__ == "__main__":')
new = '''def fig_rulebook_flow():
    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4.8)
    ax.axis("off")

    def node(x, y, w, h, text, face, edge):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.1", fc=face, ec=edge, lw=1.3))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9, color=INK, linespacing=1.3)

    w, h, gap, top, low = 2.05, 1.1, 0.38, 3.4, 1.3
    xs = [0.1 + i * (w + gap) for i in range(5)]
    node(xs[0], top, w, h, "Day close:\\nmodel gives P(bull),\\nP(sideways), P(bear),\\nP(high-vol)", "#eef3fb", SERIES[0])
    node(xs[1], top, w, h, "Stop-loss hit?\\nportfolio 8% below\\nits peak since entry", "#fdf3ea", SERIES[1])
    node(xs[2], top, w, h, "SELL signal?\\nP(bear)+P(high-vol)\\n≥ 0.5 for 2 days", "#fdf3ea", SERIES[1])
    node(xs[3], top, w, h, "BUY signal?\\nP(bull) ≥ 0.6\\nfor 2 days", "#eefaf4", SERIES[2])
    node(xs[4], top, w, h, "HOLD\\nkeep the position\\n(sideways never trades)", "#f4f6f8", MUTED)
    node(xs[1], low, w, h, "EXIT to cash\\n5-day cooldown,\\nthen a fresh BUY signal", "#ffffff", SERIES[1])
    node(xs[2], low, w, h, "SELL everything\\n→ cash\\n(futures: go short)", "#ffffff", SERIES[1])
    node(xs[3], low, w, h, "BUY / ADD\\n100% if P(bull) ≥ 0.75\\notherwise 50%", "#ffffff", SERIES[2])
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


'''
s = s[:start] + new + s[end:]
p.write_text(s, encoding="utf-8")
print("patched")
