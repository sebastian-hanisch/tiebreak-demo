"""Tie-Breaker im Schweizer System – wer entscheidet bei Punktgleichheit? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Zusatzstück der Linie Turnierplanung, hinter dem Schweizer System: Es paart die Runden, aber wer bei Punktgleichheit vorn steht, entscheiden die Tie-Breaker. Die Demo
spielt Turniere mit der echten FIDE-Dutch-Engine, rechnet die Kriterien nach FIDE C.07 und misst, wie gut sie trennen, wie leicht sie sich kippen lassen und was
nicht gespielte Runden mit ihnen machen. Aufbau und Regeln: DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import tbk_constants as C
import tbk_criteria as K
import tbk_evaluation as ev
import tbk_verdicts as vd
from tbk_pdf_export import build_pdf
from tbk_presets import (
    apply_preset,
    bounds,
    current_value,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    remember,
    seed_widget,
    sync_query_params,
)
from tbk_scenario import Settings
from tbk_visualization import build_bye_bars, build_flip_scatter, build_hit_bars, build_lines

st.set_page_config(page_title="Tie-Breaker im Schweizer System – Sebastian Hanisch", layout="wide")

SHOW = {"success": st.success, "info": st.info, "warning": st.warning}


def verdict(level, text):
    SHOW[level](text)


@st.cache_data(show_spinner="Das Turnier wird mit der FIDE-Dutch-Engine gespielt …")
def _analysis(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner="Experiment rechnet über 400 feste Turniere …")
def _criteria(mode):
    return ev.exp_criteria(mode)


@st.cache_data(show_spinner="Experiment rechnet über 400 feste Turniere …")
def _cascades(mode):
    return ev.exp_cascades(mode)


@st.cache_data(show_spinner="Experiment rechnet über feste Turniere …")
def _withdraw():
    return ev.exp_withdraw()


@st.cache_data(show_spinner="Experiment rechnet über 100 feste Turniere …")
def _bye():
    return ev.exp_bye()


@st.cache_data(show_spinner="Experiment rechnet über feste Turniere …")
def _noise(mode):
    return ev.exp_setting(ev.NOISE_SETS, mode)


@st.cache_data(show_spinner="Experiment rechnet über feste Turniere …")
def _draw(mode):
    return ev.exp_setting(ev.DRAW_SETS, mode, references=False)


@st.cache_data(show_spinner="Experiment rechnet über feste Turniere …")
def _size(mode):
    return ev.exp_setting(ev.SIZE_SETS, mode)


def label_of(key):
    return K.label(key) if key in K.NAMES else {"STICH": "Stichkampf", "LOS": "Los", C.EMPTY: C.EMPTY}.get(key, key)


st.title("⚖️ Tie-Breaker im Schweizer System – wer entscheidet bei Punktgleichheit?")
st.markdown(
    """
Das Schweizer System paart die Runden, aber nach sieben Runden mit 32 Spielern liegen mehrere Spieler bei gleichen Punkten gleichauf, und **wer vorn steht, entscheiden
die Tie-Breaker**: Buchholz, Sonneborn-Berger, Direktvergleich, Fortschrittswertung und ein Dutzend mehr. Diese Demo spielt Turniere mit der **echten FIDE-Dutch-Engine**
des Schwesterstücks, rechnet die Kriterien nach **FIDE C.07** und misst gegen die wahre Stärke, die in der Simulation bekannt ist: **wie gut trennen sie, wie leicht
lassen sie sich kippen, und was machen Freilose und Rücktritte mit ihnen?** Am Ende steht eine **Empfehlung nach Zweck**.

Weiter unten: sieben **🔬 Experimente** mit Verdikt, die **Empfehlungstabelle**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So entscheidet man bei Punktgleichheit", expanded=True):
    st.markdown(
        """
1. **Die Kaskade:** Gleiche Punkte? Dann zählt das erste Kriterium der Liste. Trennt es die Gruppe nur teilweise, gilt das nächste für jede verbleibende
   **Untergruppe** (FIDE C.07, Art. 4 Abs. 2); was am Ende übrig bleibt, entscheidet das Los.
2. **Was die Kriterien lesen:** Die **Buchholz**-Familie addiert die Punkte der Gegner (mit Streichungen: Cut-1, Median-1), **Sonneborn-Berger** gewichtet sie mit dem
   eigenen Ergebnis, die **Fortschrittswertung** summiert die Zwischenstände nach jeder Runde, der **Direktvergleich** zählt nur die Partien unter den Punktgleichen.
3. **Nicht gespielte Runden:** Freilose und Runden nach einem Rücktritt kennt Buchholz nicht von selbst; **Artikel 16** rechnet einen Dummy-Gegner mit der eigenen
   Punktzahl. Die Fassung ab März 2026 deckelt diese auf 0,5 mal Rundenzahl.
4. **Der Maßstab:** In der Simulation ist die wahre Stärke bekannt. Ein Kriterium **trifft**, wenn es von zwei punktgleichen Spielern den stärkeren vorn einordnet.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
cols = st.columns(len(C.PRESETS))
for col, name in zip(cols, C.PRESETS):
    with col:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Turnier**")
    n = st.slider("Spieler n", *bounds("n_slider"), key="n_slider", help="Bei ungerader Zahl bekommt jede Runde ein Freilos (Paarung nach FIDE Dutch).")
    rounds = st.slider("Runden", *bounds("rounds_slider"), key="rounds_slider", help="Schweizer System: feste, kleine Rundenzahl.")
    draw = st.slider("Anteil Remis", *bounds("draw_slider"), step=C.DRAW_STEP, key="draw_slider", help="Wahrscheinlichkeit eines Remis je Partie, unabhängig von der Stärke.")
    noise = st.slider("Rauschen der Startwertung", *bounds("noise_slider"), step=C.NOISE_STEP, key="noise_slider",
                      help="Wie schlecht die Setzliste die wahre Stärke kennt (logistische Einheiten). 0 = perfekt.")
    withdraw_on = st.checkbox("Rücktritte zulassen", key="withdraw_toggle", help="Ein Teil der Spieler scheidet vor einer Runde zwischen 3 und der vorletzten aus.")
    if withdraw_on:
        seed_widget("withdraw_slider")
        withdraw = st.slider("Anteil der Spieler, die zurücktreten", *bounds("withdraw_slider"), step=C.WITHDRAW_STEP, key="withdraw_slider")
        remember("withdraw_slider", withdraw)
    st.markdown("**Nicht gespielte Runden**")
    mode = st.selectbox("Behandlung in Buchholz und Sonneborn-Berger", list(C.MODES), format_func=lambda m: C.MODES[m], key="mode_select",
                        help="Freilose und Runden nach Rücktritt: ignorieren oder nach FIDE Artikel 16 (zwei Fassungen).")
    st.markdown("**Kaskade**")
    c1 = st.selectbox("1. Kriterium", K.KEYS, format_func=label_of, key="c1_select")
    c2 = st.selectbox("2. Kriterium", (C.EMPTY,) + K.KEYS, format_func=label_of, key="c2_select")
    c3 = st.selectbox("3. Kriterium", (C.EMPTY,) + K.KEYS, format_func=label_of, key="c3_select")
    c4 = st.selectbox("4. Kriterium", (C.EMPTY,) + K.KEYS, format_func=label_of, key="c4_select")
    seed = st.number_input("Zufalls-Seed des Turniers", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neues Turnier würfeln", width="stretch", on_click=randomize_seed)

withdraw_value = round(float(current_value("withdraw_slider")), 2)
cascade = tuple(dict.fromkeys(c for c in (c1, c2, c3, c4) if c != C.EMPTY))     # doppelte Kriterien zählen nur einmal
sync_query_params({"n_slider": int(n), "rounds_slider": int(rounds), "draw_slider": round(float(draw), 2), "noise_slider": round(float(noise), 1),
                   "withdraw_toggle": bool(withdraw_on), "withdraw_slider": withdraw_value, "mode_select": mode, "c1_select": c1, "c2_select": c2, "c3_select": c3,
                   "c4_select": c4, "seed_input": int(seed)})

settings = Settings(int(n), int(rounds), round(float(draw), 2), round(float(noise), 1), withdraw_value if withdraw_on else 0.0, mode, cascade, int(seed))
a = _analysis(settings)
t = a.tournament

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Der Endstand")
if t.rounds < settings.rounds:
    st.info(f"Das Turnier endet nach Runde {t.rounds} von {settings.rounds}: Das Schweizer System findet für die nächste Runde keine Paarung ohne Wiederholung "
            "(kleines Feld, viele Runden oder Rücktritte). Ein echtes Turnier bräche an derselben Stelle ab.")
m = a.metrics
tied_pairs = m.pairs
m1, m2, m3, m4 = st.columns(4)
m1.metric("Spieler auf Platz 1 nach Punkten", len(a.top_group), delta=f"{ev.de(max(a.score))} Punkte", delta_color="off",
          help="Gleichstand um Platz 1: so viele Spieler hat die Kaskade zu trennen.")
m2.metric("Sieger nach der Kaskade", f"Nr. {a.winner}", delta="wahrer Stärkster" if a.winner == a.best else f"wahrer Stärkster: Nr. {a.best}", delta_color="off")
m3.metric("Punktgleiche Paare", tied_pairs, delta=f"{ev.pct(m.resolution)} % getrennt vor dem Los" if tied_pairs else "–", delta_color="off",
          help="Paare mit gleichen Punkten; getrennt heißt, ein Kriterium der Kaskade unterscheidet sie (sonst entscheidet das Los).")
m4.metric("Treffer der Kaskade", "–" if not m.resolved else f"{ev.pct(m.hit_rate)} %", delta=f"τ gegen die Stärke: {ev.de(m.tau, 2)}", delta_color="off",
          help="Anteil der getrennten Paare, bei denen der Stärkere vorn steht (nur in der Simulation messbar; ein einzelnes Turnier ist eine kleine Stichprobe).")

true_rank = {r: i + 1 for i, r in enumerate(sorted(range(1, t.n + 1), key=lambda q: -t.strength[q - 1]))}
shown = list(dict.fromkeys(["BH", "BH-C1", "SB", "PS", "WIN"] + list(cascade)))
shown = [k for k in shown if k != "DE"]
rows = []
for place, (nr, why) in enumerate(a.standing, start=1):
    row = {"Platz": place, "Nr.": nr, "Punkte": a.score[nr - 1], "getrennt vom Vorgänger durch": {"": "–", "Punkte": "Punkte", "LOS": "Los"}.get(why, why)}
    for k in shown:
        row[k] = round(a.values[k][nr - 1], 2)
    row["wahrer Rang"] = true_rank[nr]
    row["Freilos"] = "ja" if any(g.bye for g in t.games[nr - 1]) else ""
    row["Rücktritt vor Runde"] = t.leave[nr - 1] or ""
    rows.append(row)
df = pd.DataFrame(rows)
st.dataframe(df, hide_index=True, width="stretch")
st.caption("Die Spalten Buchholz (BH) bis WIN sind nach der gewählten Behandlung nicht gespielter Runden berechnet. Der Direktvergleich hängt von der Gruppe der "
           "Punktgleichen ab und hat deshalb keine Spalte. „wahrer Rang“ ist die Stärkeordnung der Simulation (1 = stärkster).")
st.download_button("📄 PDF des Endstands", data=build_pdf(a), file_name="tie-breaker.pdf", mime="application/pdf", key="pdf_download")

st.markdown("**Eine irrelevante Partie der letzten Runde umkehren**")
st.session_state.setdefault("flip_choice", 0)
games = [(x, y) for x, y, _w in a.flips]


def _flip_label(i):
    if i == 0:
        return "– keine Partie –"
    x, y = games[i - 1]
    res = next(g.score for g in t.games[x - 1] if g.opponent == y and g.round_no == t.rounds)
    return f"Nr. {x} gegen Nr. {y} (Ergebnis für Nr. {x}: {ev.de(res)})"


if not games:
    st.caption("In der letzten Runde gibt es keine Partie, an der niemand beteiligt ist, der die Spitze erreichen könnte (beide mindestens "
               f"{ev.de(C.FLIP_MARGIN)} Punkte dahinter).")
else:
    st.session_state["flip_choice"] = min(st.session_state["flip_choice"], len(games))
    choice = st.selectbox("Partie, deren Ausgang umgekehrt wird (Sieg ↔ Niederlage, Remis → Sieg des Erstgenannten)", range(len(games) + 1), format_func=_flip_label,
                          key="flip_choice")
    if choice:
        x, y, new_winner = a.flips[choice - 1]
        t2 = K.flip_game(t, x, y, t.rounds)
        v2 = K.values(t2, settings.mode)
        st.dataframe(pd.DataFrame([{"Nr.": r, "Punkte": a.score[r - 1], **{k: round(a.values[k][r - 1], 2) for k in shown},
                                    **{f"{k} nach Umkehr": round(v2[k][r - 1], 2) for k in shown}} for r in a.top_group]), hide_index=True, width="stretch")
        if new_winner == a.winner:
            st.success(f"Der Sieger bleibt Nr. {a.winner}: diese Partie ändert nichts an der Spitze.")
        else:
            st.warning(f"**Der Sieger wechselt von Nr. {a.winner} zu Nr. {new_winner}**, obwohl keiner der beiden Beteiligten die Spitze erreichen konnte: Die Kaskade liest "
                       "die Gegner der Spitzenspieler, und deren Ergebnis hat sich geändert.")
    st.caption(f"{sum(1 for _x, _y, w in a.flips if w != a.winner)} von {len(games)} irrelevanten Partien der letzten Runde ändern in diesem Turnier den Sieger.")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wer steht vorn, und wäre es auch ohne die irrelevante Partie so?")
verdict(*vd.verdict_analysis(a))

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

mode_name = C.MODES[settings.mode]
st.subheader("🔬 Experiment 1: Wie gut trifft jedes Kriterium?")
st.caption(f"400 feste Turniere (32 Spieler, 7 Runden, 20 % Remis, Rauschen 0,4, unabhängig vom Regler; Behandlung nicht gespielter Runden: {mode_name}). "
           "Punktgleiche Paare, die das Kriterium trennt: Anteil, bei dem der stärkere Spieler vorn steht.")
crit = _criteria(settings.mode)
st.plotly_chart(build_hit_bars(crit), width="stretch", key="exp1_chart")
verdict(*vd.verdict_criteria(crit))
st.dataframe(pd.DataFrame([{"Kriterium": label_of(k), "trennt (% der Paare)": round(100 * mt.resolution), "Treffer (%)": None if not mt.resolved else round(100 * mt.hit_rate, 1),
                            "Erwartung (σ der Differenz)": None if not mt.resolved else round(mt.expectation, 3), "Sieger richtig (%)": round(100 * mt.winner_rate),
                            "Podium richtig (%)": round(100 * mt.podium_rate), "τ": round(mt.tau, 3)} for k, mt in crit.items()]), hide_index=True, width="stretch")

st.subheader("🔬 Experiment 2: Wie leicht lässt sich ein Kriterium kippen?")
st.caption("Dieselben 400 Turniere. In den Turnieren mit Gleichstand um Platz 1 wird der Ausgang **einer** Partie der letzten Runde umgekehrt, an der kein Spieler beteiligt "
           f"ist, der die Spitze erreichen könnte (beide mindestens {ev.de(C.FLIP_MARGIN)} Punkte dahinter). Ändert sich der Sieger?")
st.plotly_chart(build_flip_scatter(crit), width="stretch", key="exp2_chart")
verdict(*vd.verdict_flips(crit))

st.subheader("🔬 Experiment 3: Kaskaden")
st.caption("Dieselben 400 Turniere; sieben Listen, wie sie in der Praxis vorkommen, zuletzt jeweils das Los. Auflösung heißt: getrennt, bevor das Los entscheidet.")
casc = _cascades(settings.mode)
st.dataframe(pd.DataFrame([{"Kaskade": name, "trennt (% der Paare)": round(100 * mt.resolution), "Treffer (%)": round(100 * mt.hit_rate, 1),
                            "Sieger richtig (%)": round(100 * mt.winner_rate), "kippbar (% der Turniere)": round(100 * mt.flip_rate_t),
                            "kippbar (% der Umkehrungen)": round(100 * mt.flip_rate_g, 1), "τ": round(mt.tau, 3)} for name, mt in casc.items()]),
             hide_index=True, width="stretch")
verdict(*vd.verdict_cascades(casc))

st.subheader("🔬 Experiment 4: Rücktritte und nicht gespielte Runden")
st.caption("Je 60 feste Turniere mit 0 / 15 / 30 % Rücktritten (die Hauptmenge für 0 %); Treffer je Kriterium, mit den Runden nach dem Rücktritt ignoriert (gepunktet) und "
           "nach FIDE Artikel 16 ab 03/2026 (durchgezogen).")
wrows = _withdraw()
fig_rows = [{**r, "value": f"{round(100 * r['withdraw'])} %"} for r in wrows if r["mode"] in ("ignore", "fide2026")]
st.plotly_chart(build_lines(fig_rows, "Anteil der Rücktritte", ("BH", "BH-C1", "SB", "PS", "WIN"), modes=("ignore", "fide2026")), width="stretch", key="exp4_chart")
verdict(*vd.verdict_withdraw(wrows))
st.dataframe(pd.DataFrame([{"Kriterium": k, "Rücktritte": f"{round(100 * w)} %", **{C.MODES[md]: round(100 * next(r['hit_rate'] for r in wrows if r['key'] == k and
                            r['withdraw'] == w and r['mode'] == md), 1) for md in C.MODES}} for k in ev.WITHDRAW_KEYS for _s, w in ev.WITHDRAW_SETS]),
             hide_index=True, width="stretch")

st.subheader("🔬 Experiment 5: Freilose")
st.caption("100 feste Turniere mit 31 Spielern, 7 Runden: jede Runde bekommt ein Spieler das Freilos. Bei Paaren, von denen genau einer ein Freilos hatte: "
           "Anteil „Inhaber vorn“ minus Anteil „Inhaber ist der Stärkere“, in Prozentpunkten.")
brows = _bye()
st.plotly_chart(build_bye_bars(brows), width="stretch", key="exp5_chart")
verdict(*vd.verdict_bye(brows))

st.subheader("🔬 Experiment 6: Setzliste und Remis")
st.caption("Je 60 feste Turniere (Hauptmenge für Rauschen 0,4 und 20 % Remis), 32 Spieler, 7 Runden; Behandlung wie in der Seitenleiste.")
nrows = _noise(settings.mode)
n_rows = [{**r, "value": ev.de(r["value"], 1)} for r in nrows]
st.plotly_chart(build_lines(n_rows, "Rauschen der Startwertung", ("RTNG", "PS", "BH-C1", "SB", "AOB")), width="stretch", key="exp6a_chart")
verdict(*vd.verdict_noise(nrows))
drows = _draw(settings.mode)
d_rows = [{**r, "value": f"{round(100 * r['value'])} %"} for r in drows]
st.plotly_chart(build_lines(d_rows, "Anteil Remis", ("PS", "BH", "SB", "AOB", "WIN")), width="stretch", key="exp6b_chart")
verdict(*vd.verdict_draw(drows))

st.subheader("🔬 Experiment 7: Feldgröße und Runden")
st.caption("Je 60 bis 100 feste Turniere (Hauptmenge für 32 Spieler und 7 Runden), 20 % Remis.")
srows = _size(settings.mode)
st.plotly_chart(build_lines(srows, "Feld und Rundenzahl", ("PS", "BH", "BH-C1", "SB", "RTNG")), width="stretch", key="exp7_chart")
verdict(*vd.verdict_size(srows))

st.markdown("---")

# --- Empfehlung ----------------------------------------------------------------------------------------------------------------------------

st.subheader("🧭 Empfehlung nach Zweck")
st.caption("Aus den Messwerten oben abgeleitet (Behandlung nicht gespielter Runden: FIDE ab 03/2026); es gibt kein bestes Kriterium, nur eines je Zweck.")
rec_rows = vd.recommendations(_criteria("fide2026"), wrows, brows, _noise("fide2026"), _size("fide2026"))
st.dataframe(pd.DataFrame(rec_rows, columns=["Zweck", "Empfehlung", "Messwert", "Vorbehalt"]), hide_index=True, width="stretch")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Stärke ist eine Zahl, die Partie ein Münzwurf mit Gewicht** | Reale Remisquoten hängen an der Stärke und am Niveau; hier ist das Remis unabhängig von der Stärke (Experiment 6). | Tore, Remis, Heimvorteil |
| **Ein Stärkenmodell für alle** | Spieler mit Stil und Form fehlen; Buchholz liest die Gegnerstärke, die hier nur eine Zahl ist. | Elo, Glicko und TrueSkill |
| **Rücktritte und Freilose nach Artikel 16** | Nachgebaut sind Freilos und Runden nach dem Rücktritt; „requested byes“ und Forfaits kommen nicht vor. | – |
| **Das Ziel ist die Stärke** | Das Reglement verlangt nicht, dass der Stärkere vorn steht; es verlangt ein klares Verfahren. Die Stärke ist nur der Maßstab, den eine Simulation kennt. | – |
| **Kippen ist eine Möglichkeit, keine Absicht** | Die Umkehr einer Partie misst, wie sehr der Sieger an den Dritten hängt, nicht, ob jemand sie manipuliert. | – |
| **Feste, vorberechnete Turniere** | Die Experimente 1 bis 7 rechnen auf Turnieren, die einmal mit der Engine erzeugt wurden; ein Regler ändert nur Kaskade, Behandlung und das gezeigte Turnier. | – |
| **Alles ist simuliert** | Stärken, Setzliste, Remis und Rücktritte sind Konstruktionen des Generators; es gibt keinen echten Datensatz. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Punkte und Gruppe.** Spieler $i$ hat nach $R$ Runden die Punktzahl $s_i$; punktgleiche Spieler bilden eine Gruppe $G$.

**Buchholz.** $BH_i = \sum_{j \in O_i} s_j$ mit $O_i$ den Gegnern am Brett. **Cut-1** streicht den kleinsten Summanden, **Median-1** den kleinsten und den größten, **Cut-2**
und **Median-2** je zwei. **AOB** ist der Mittelwert der $BH_j$ über die Gegner.

**Sonneborn-Berger.** $SB_i = \sum_{j \in O_i} s_j \, p_{ij}$ mit $p_{ij}$ den Punkten von $i$ gegen $j$.

**Fortschritt.** $PS_i = \sum_{r=1}^{R} s_i^{(r)}$ mit $s_i^{(r)}$ dem Punktestand nach Runde $r$.

**Direktvergleich (Art. 6).** Innerhalb der Gruppe $G$ zählt $d_i = \sum_{j \in G} p_{ij}$ (mehrfache Treffen als Mittel). Haben alle einander gespielt, ordnet $d$ die
Gruppe; sonst steht nur ein Spieler $i$ vorn, für den $d_i > d_j + m_j$ für alle $j \neq i$ gilt ($m_j$ die Zahl der fehlenden Partien von $j$ in der Gruppe), danach gilt
Artikel 6 für den Rest erneut.

**Nicht gespielte Runden (Art. 16).** Für die Gegner zählt eine Runde nach dem Rücktritt als Remis ($s_j^{\ast} = s_j + \tfrac12 u_j$ mit $u_j$ der Zahl dieser Runden). Für
die eigenen Kriterien gilt ein Dummy-Gegner mit der Punktzahl $\min(s_i, c)$ und $c = \tfrac12 R$ (Fassung ab 03/2026; 08/2024: $c = \infty$) für Freilose und Runden nach
dem Rücktritt; beim Streichen wird zuerst der kleinste Beitrag einer freiwillig nicht gespielten Runde gestrichen.

**Leistungswertung.** $\mathrm{TPR}_i = \overline{r}_{O_i} + \ln\!\frac{f_i}{1 - f_i}$ mit $f_i$ der Punktquote an den Brettern (auf $[0{,}02;\,0{,}98]$ begrenzt), logistisch statt
der FIDE-Tabelle.

**Treffer.** Anteil der von einem Kriterium getrennten punktgleichen Paare $(i, j)$, bei denen der vordere Spieler die größere wahre Stärke hat; **Erwartung**: Mittel von
$\sigma(\theta_{\text{vorn}} - \theta_{\text{hinten}})$. **Kippen:** der Sieger wechselt, wenn der Ausgang einer Partie der letzten Runde umgekehrt wird, deren beide Beteiligte
mindestens 1,5 Punkte hinter der Spitze liegen.

**Zufall.** Stärken aus dem Generator der Linie (Version 1, SplitMix64), Paarung mit dem FIDE-Dutch-System (wortgleiche Engine aus `schweizer-system-demo`), Ausgang:
Remis mit Wahrscheinlichkeit $d$, sonst Sieg des Weißen mit $(1-d)\,\sigma(\theta_W - \theta_S)$.

**Literatur.**
- FIDE Handbook, C.07 *Play-Off and Tie-Break Regulations* (Fassungen „effective from 1 August 2024 till 28 February 2026“ und „from 1 March 2026“, handbook.fide.com;
  die Artikel 4, 6, 7, 8, 9, 14 und 16 nach dem veröffentlichten Text gelesen).
- Das Buchholz-System ist nach Bruno Buchholz benannt (Jahr und Fundstelle nicht geprüft).
- Steele, G. L., Lea, D., Flood, C. H. (2014): Fast splittable pseudorandom number generators. *OOPSLA 2014*, 453–472 (Zufallsstrom des Generators).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Turnierplanung: 7 Wege zum Turnierplan](https://sebastianhanisch.net/konzepte-turnierplanung.html)."
)
