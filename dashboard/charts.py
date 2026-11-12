"""Plotly figures. Palette = the validated reference instance (dataviz skill, references/palette.md).

Categorical slots are used in fixed order. Regimes are drawn as one row per regime (position is the
primary encoding, colour secondary), so four regime colours never compete in one field.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PALETTE = {
    "light": {"series": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"], "ink": "#0b0b0b", "ink2": "#52514e",
              "muted": "#898781", "grid": "#e1e0d9", "axis": "#c3c2b7",
              "seq": ["#fcfcfb", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]},
    "dark": {"series": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181"], "ink": "#ffffff", "ink2": "#c3c2b7",
             "muted": "#898781", "grid": "#2c2c2a", "axis": "#383835",
             "seq": ["#1a1a19", "#0d366b", "#104281", "#184f95", "#256abf", "#3987e5", "#6da7ec", "#b7d3f6"]},
}
# regime -> slot (fixed): sideways blue, bear orange, bull aqua, high-vol yellow
REGIME_SLOT = {"sideways": 0, "bear": 1, "bull": 2, "high_vol": 3}


def pal(theme: str) -> dict:
    return PALETTE["dark" if theme == "dark" else "light"]


def regime_color(regime: str, theme: str) -> str:
    return pal(theme)["series"][REGIME_SLOT[regime]]


def _layout(fig: go.Figure, theme: str, height: int, **kw) -> go.Figure:
    p = pal(theme)
    fig.update_layout(height=height, margin=dict(l=8, r=8, t=36, b=8), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif",
                                                               color=p["ink2"], size=13),
                      hoverlabel=dict(font_family="system-ui, sans-serif"), legend=dict(orientation="h", y=1.08, x=0), **kw)
    fig.update_xaxes(showgrid=False, linecolor=p["axis"], tickcolor=p["axis"], ticks="outside", tickfont_color=p["muted"])
    fig.update_yaxes(gridcolor=p["grid"], gridwidth=1, zeroline=False, linecolor=p["axis"], tickfont_color=p["muted"])
    return fig


def regime_timeline(df: pd.DataFrame, pred: pd.DataFrame | None, model_name: str, regimes: list, labels: dict, theme: str) -> go.Figure:
    """Price line + one row per regime for the HMM label (and the model's forecast, if given)."""
    p = pal(theme)
    rows = 3 if pred is not None else 2
    heights = [0.5, 0.25, 0.25] if rows == 3 else [0.62, 0.38]
    titles = ["Nifty 50 close", "Frozen HMM regime (ground truth)"] + ([f"{model_name} forecast for that day"] if rows == 3 else [])
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, row_heights=heights, vertical_spacing=0.07, subplot_titles=titles)
    fig.add_trace(go.Scatter(x=df.index, y=df["close"], mode="lines", line=dict(color=p["ink"], width=1.5), name="Nifty 50",
                             customdata=np.array([labels[r] for r in df["regime"]]),
                             hovertemplate="%{x|%d %b %Y}<br>Close %{y:,.0f}<br>HMM regime: %{customdata}<extra></extra>",
                             showlegend=False), row=1, col=1)
    order = [r for r in ["bull", "sideways", "bear", "high_vol"] if r in regimes]
    strips = [(df["regime"], 2, True)] + ([(pred["predicted"], 3, False)] if rows == 3 else [])
    for series, row, legend in strips:
        for r in order:
            idx = series.index[series == r]
            fig.add_trace(go.Scatter(x=idx, y=[labels[r]] * len(idx), mode="markers", name=labels[r], legendgroup=r,
                                     showlegend=legend, marker=dict(symbol="line-ns", size=11, line=dict(width=2, color=regime_color(r, theme))),
                                     hovertemplate="%{x|%d %b %Y}: " + labels[r] + "<extra></extra>"), row=row, col=1)
        fig.update_yaxes(categoryorder="array", categoryarray=[labels[r] for r in order[::-1]], showgrid=False, row=row, col=1)
    fig.update_yaxes(tickformat=",.0f", row=1, col=1)
    for a in fig.layout.annotations:
        a.update(font=dict(size=13, color=p["ink2"]), x=0, xanchor="left")
    return _layout(fig, theme, 560 if rows == 3 else 440, hovermode="closest")


def equity_chart(lines: dict, start: float, theme: str, title: str) -> go.Figure:
    """lines: {label: (series, role)} with role in {'system', 'buy_and_hold', 'cash'}."""
    p = pal(theme)
    fig = go.Figure()
    slot = 0
    for label, (s, role) in lines.items():
        if role == "buy_and_hold":
            line = dict(color=p["ink"], width=2)
        elif role == "cash":
            line = dict(color=p["muted"], width=2, dash="dot")
        else:
            line = dict(color=p["series"][slot % len(p["series"])], width=2)
            slot += 1
        fig.add_trace(go.Scatter(x=s.index, y=s / 1e5, mode="lines", name=label, line=line,
                                 hovertemplate="%{y:.2f} lakh"))
    fig.add_hline(y=start / 1e5, line=dict(color=p["axis"], width=1))
    fig.update_yaxes(title_text="Portfolio value (Rs lakh)", ticksuffix="")
    fig = _layout(fig, theme, 500, hovermode="x unified", title=dict(text=title, font=dict(size=15, color=p["ink"]), x=0))
    # legend below the plot so long system names never cover the lines on narrow screens
    fig.update_layout(legend=dict(orientation="h", y=-0.14, yanchor="top", x=0), margin=dict(b=90))
    return fig


def confusion_heatmap(cm, classes: list, labels: dict, theme: str, title: str) -> go.Figure:
    p = pal(theme)
    cm = np.asarray(cm, dtype=float)
    row_share = cm / np.maximum(cm.sum(axis=1, keepdims=True), 1)
    names = [labels[c] for c in classes]
    text = [[f"{int(cm[i, j])}<br>{100 * row_share[i, j]:.0f}%" if cm[i].sum() else "–" for j in range(len(classes))]
            for i in range(len(classes))]
    scale = [[i / (len(p["seq"]) - 1), c] for i, c in enumerate(p["seq"])]
    fig = go.Figure(go.Heatmap(z=row_share, x=names, y=names, colorscale=scale, zmin=0, zmax=1, text=text, texttemplate="%{text}",
                               xgap=2, ygap=2, colorbar=dict(title="Share of<br>true regime", tickformat=".0%"),
                               hovertemplate="True %{y} → predicted %{x}<br>%{text}<extra></extra>"))
    fig.update_yaxes(autorange="reversed", title_text="True (HMM)")
    fig.update_xaxes(title_text="Predicted", side="bottom")
    return _layout(fig, theme, 400, title=dict(text=title, font=dict(size=15, color=p["ink"]), x=0))


def grouped_bars(df: pd.DataFrame, x: str, y: str, group: str, groups: list, theme: str, title: str, fmt: str) -> go.Figure:
    p = pal(theme)
    fig = go.Figure()
    for i, g in enumerate(groups):
        d = df[df[group] == g]
        fig.add_trace(go.Bar(x=d[x], y=d[y], name=g, marker=dict(color=p["series"][i], cornerradius=4),
                             texttemplate="%{y:" + fmt + "}", textposition="outside", textfont_color=p["ink2"],
                             hovertemplate=g + " · %{x}: %{y:" + fmt + "}<extra></extra>"))
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.08)
    fig = _layout(fig, theme, 400, title=dict(text=title, font=dict(size=15, color=p["ink"]), x=0))
    fig.update_layout(legend=dict(orientation="h", y=-0.12, yanchor="top", x=0), margin=dict(b=70))
    return fig


def replay_chart(daily: pd.DataFrame, theme: str) -> go.Figure:
    """Daily mean confidence and daily accuracy of the 15-min replay (two panels, one axis each)."""
    p = pal(theme)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                        subplot_titles=["Mean prediction confidence per day", "Share of bars predicted correctly per day"])
    fig.add_trace(go.Scatter(x=daily.index, y=daily["confidence"], mode="lines", line=dict(color=p["series"][0], width=2),
                             name="Confidence", hovertemplate="%{x|%d %b %Y}: %{y:.2f}<extra></extra>", showlegend=False), row=1, col=1)
    fig.add_hline(y=0.5, line=dict(color=p["axis"], width=1), row=1, col=1)
    fig.add_trace(go.Scatter(x=daily.index, y=daily["accuracy"], mode="lines", line=dict(color=p["series"][1], width=2),
                             name="Accuracy", hovertemplate="%{x|%d %b %Y}: %{y:.0%}<extra></extra>", showlegend=False), row=2, col=1)
    fig.update_yaxes(range=[0, 1.02], row=1, col=1)
    fig.update_yaxes(range=[0, 1.02], tickformat=".0%", row=2, col=1)
    for a in fig.layout.annotations:
        a.update(font=dict(size=13, color=p["ink2"]), x=0, xanchor="left")
    return _layout(fig, theme, 460, hovermode="x unified")
