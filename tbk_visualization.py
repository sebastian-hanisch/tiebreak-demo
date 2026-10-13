"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import tbk_constants as C
import tbk_criteria as K
from tbk_evaluation import de

FAMILY_COLOR = {
    "BH": "#2F6B65", "BH-C1": "#2F6B65", "BH-C2": "#2F6B65", "BH-M1": "#2F6B65", "BH-M2": "#2F6B65", "AOB": "#5f9d95",
    "SB": "#8e6bb0", "DE": "#d98c1f", "PS": "#3d7ab5", "PS-G": "#3d7ab5",
    "WIN": "#7a8f3c", "WON": "#7a8f3c", "BWG": "#7a8f3c", "BPG": "#7a8f3c", "REP": "#7a8f3c",
    "ARO": "#b0577e", "TPR": "#b0577e", "RTNG": "#5a5a5a", "STICH": "#c0392b", "LOS": "#9a9a9a",
}


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _name(key):
    return key if key in K.NAMES else {"STICH": "Stichkampf", "LOS": "Los"}.get(key, key)


def build_hit_bars(metrics: dict, lot_line: bool = True):
    """Treffer je Kriterium (Anteil der getrennten Punktgleichen, die richtig geordnet sind), absteigend; die Referenzlinie bei 50 % ist das Los."""
    items = sorted((m for k, m in metrics.items() if k != "LOS" and m.resolved), key=lambda m: m.hit_rate)
    fig = go.Figure(go.Bar(
        x=[100 * m.hit_rate for m in items], y=[_name(m.key) for m in items], orientation="h", marker_color=[FAMILY_COLOR.get(m.key, "#5a5a5a") for m in items],
        text=[f"{de(100 * m.hit_rate)} %" for m in items], textposition="outside", cliponaxis=False,
        customdata=[[100 * m.resolution, m.pairs] for m in items],
        hovertemplate="%{y}: %{x:.1f} % richtig<br>trennt %{customdata[0]:.0f} % der %{customdata[1]} punktgleichen Paare<extra></extra>"))
    if lot_line:
        fig.add_vline(x=50, line_dash="dash", line_color="rgba(150,150,150,0.9)", annotation_text="Los", annotation_position="top")
    fig.update_xaxes(title_text="Treffer: Anteil richtig geordneter getrennter Paare in %", range=[40, 100])
    return _base(fig, height=max(360, 26 * len(items) + 90))


def build_flip_scatter(metrics: dict):
    """Treffer gegen Kippbarkeit: oben links ist gut (trifft und lässt sich nicht kippen)."""
    items = [m for k, m in metrics.items() if k not in ("LOS", "STICH") and m.top_tie and m.resolved]
    fig = go.Figure(go.Scatter(
        x=[100 * m.flip_rate_t for m in items], y=[100 * m.hit_rate for m in items], mode="markers+text", text=[m.key for m in items], textposition="top center",
        marker=dict(size=12, color=[FAMILY_COLOR.get(m.key, "#5a5a5a") for m in items]), cliponaxis=False,
        hovertemplate="%{text}: %{y:.1f} % richtig, in %{x:.0f} % der Turniere mit Gleichstand um Platz 1 kippbar<extra></extra>"))
    fig.update_xaxes(title_text="kippbar durch eine irrelevante Partie der letzten Runde (% der Turniere mit Gleichstand um Platz 1)", range=[-3, 45])
    fig.update_yaxes(title_text="Treffer in %")
    return _base(fig, height=420)


def build_lines(rows, x_title: str, keys, modes=None, x_fmt=None):
    """Treffer je Kriterium über eine Folge von Werten; je Behandlung ein Linienstil (durchgezogen, gestrichelt)."""
    fig = go.Figure()
    dashes = {"ignore": "dot", "fide2024": "dash", "fide2026": "solid"}
    mode_list = modes or [None]
    for k in keys:
        for mode in mode_list:
            sel = [r for r in rows if r["key"] == k and (mode is None or r.get("mode") == mode)]
            if not sel:
                continue
            tag = _name(k) if mode is None else f"{_name(k)} ({'FIDE 03/2026' if mode == 'fide2026' else 'FIDE 08/2024' if mode == 'fide2024' else 'ignoriert'})"
            fig.add_trace(go.Scatter(
                x=[x_fmt(r["value"]) if x_fmt else r.get("value", r.get("withdraw")) for r in sel], y=[100 * r["hit_rate"] for r in sel], mode="lines+markers", name=tag,
                line=dict(color=FAMILY_COLOR.get(k, "#5a5a5a"), width=3, dash=dashes.get(mode, "solid")), marker=dict(size=8),
                hovertemplate=tag + ", %{x}: %{y:.1f} %<extra></extra>"))
    fig.update_xaxes(title_text=x_title, type="category")
    fig.update_yaxes(title_text="Treffer in %")
    return _base(fig, height=420)


def build_bye_bars(rows):
    """Freilos-Verzerrung in Prozentpunkten je Kriterium und Behandlung (positiv: der Freilos-Inhaber steht öfter vorn, als seine Stärke rechtfertigt)."""
    fig = go.Figure()
    colors = {"ignore": C.COLOR_GREY, "fide2024": "#8e6bb0", "fide2026": C.COLOR_MAIN}
    names = {"ignore": "ignoriert", "fide2024": "FIDE 08/2024", "fide2026": "FIDE ab 03/2026"}
    for mode in C.MODES:
        sel = [r for r in rows if r["mode"] == mode]
        fig.add_trace(go.Bar(x=[r["key"] for r in sel], y=[100 * r["bias"] for r in sel], name=names[mode], marker_color=colors[mode],
                             hovertemplate="%{x}, " + names[mode] + ": %{y:+.0f} Prozentpunkte<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Verzerrung (Prozentpunkte)")
    return _base(fig, height=400)
