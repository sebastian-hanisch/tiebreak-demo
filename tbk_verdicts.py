"""Verdikte und Empfehlung nach Zweck: Texte, die live aus den Messwerten gebaut werden (keine feste Zahl im Text)."""

import tbk_constants as C
import tbk_criteria as K
from tbk_evaluation import LOS, SIZE_SETS, STICH, WITHDRAW_SETS, Analysis, de, pct, signed


def verdict_analysis(a: Analysis):
    """Aussage über das gezeigte Turnier: wie wurde Platz 1 entschieden, und wie leicht wäre er zu kippen."""
    st = a.standing
    top = max(a.score)
    k = len(a.top_group)
    best_text = "der wahre Stärkste" if a.winner == a.best else f"nicht der wahre Stärkste (das ist Nr. {a.best})"
    if k < 2:
        return "info", (f"Platz 1 ist ohne Tie-Breaker entschieden: Nr. {a.winner} hat mit {de(top)} Punkten allein die meisten und ist {best_text}. Die Kaskade wird "
                        "hier nicht gebraucht; sie entscheidet nur die Gleichstände weiter unten.")
    why = st[1][1]
    reason = {"LOS": "das Los (kein Kriterium der Kaskade trennt die beiden)", "Punkte": "die Punkte"}.get(why, f"das Kriterium {why}")
    head = f"{k} Spieler liegen mit {de(top)} Punkten gleichauf; Nr. {a.winner} gewinnt, getrennt von Platz 2 durch {reason}, und ist {best_text}."
    m = len(a.flips)
    if not m:
        return "info", head + " In der letzten Runde gibt es keine irrelevante Partie, deren Umkehr man prüfen könnte."
    changed = sum(1 for _a, _b, w in a.flips if w != a.winner)
    if changed:
        return "warning", head + (f" **Kippbar:** die Umkehr von {changed} der {m} irrelevanten Partien der letzten Runde (beide Beteiligte mindestens "
                                  f"{de(C.FLIP_MARGIN)} Punkte hinter der Spitze) ändert den Sieger.")
    return "success", head + f" Die Umkehr jeder der {m} irrelevanten Partien der letzten Runde lässt den Sieger unverändert."


def verdict_criteria(metrics: dict):
    solid = {k: m for k, m in metrics.items() if k in K.SOLID_KEYS and m.resolved and m.resolution >= 0.3}
    best = max(solid, key=lambda k: solid[k].hit_rate)
    worst = min(solid, key=lambda k: solid[k].hit_rate)
    sp, rt = metrics[STICH], metrics["RTNG"]
    lo = min(m.winner_rate for m in metrics.values())
    hi = max(m.winner_rate for m in metrics.values())
    return "info", (f"Unter den Rechenkriterien trifft **{best}** am häufigsten ({pct(solid[best].hit_rate)} % der getrennten Paare), **{worst}** am seltensten "
                    f"({pct(solid[worst].hit_rate)} %); das Los trifft per Definition 50 %. Der **Direktvergleich** nach Artikel 6 trennt nur "
                    f"{pct(metrics['DE'].resolution, 1)} % der Paare. **Ein einziger Stichkampf** (eine Partie) trifft {pct(sp.hit_rate)} %, die "
                    f"**Startwertung** {pct(rt.hit_rate)} %, aber nur, weil diese Setzliste gut ist (Rauschen {de(C.DEFAULT_NOISE)}; Experiment 6). Der Sieger ist in "
                    f"{pct(lo)} bis {pct(hi)} % der Turniere der wahre Stärkste, egal welches Kriterium: Tie-Breaker ordnen innerhalb der Punktgruppen, sie retten die "
                    "Stärkeordnung eines kurzen Turniers nicht.")


def verdict_flips(metrics: dict):
    solid = {k: m for k, m in metrics.items() if k in K.KEYS and m.top_tie and m.resolved and m.resolution >= 0.3}
    zero = sorted(k for k, m in solid.items() if m.flip_rate_t == 0)
    worst = max(solid, key=lambda k: solid[k].flip_rate_t)
    bh = [k for k in ("BH", "BH-C1", "BH-C2", "BH-M1", "BH-M2") if k in solid]
    lo, hi = min(solid[k].flip_rate_t for k in bh), max(solid[k].flip_rate_t for k in bh)
    n = next(iter(solid.values())).top_tie
    return "warning", (f"In {n} Turnieren mit Gleichstand um Platz 1 ändert die Umkehr **einer** Partie, an der niemand aus der Spitze beteiligt ist, bei der "
                       f"Buchholz-Familie in {pct(lo)} bis {pct(hi)} % der Turniere den Sieger, bei {worst} in {pct(solid[worst].flip_rate_t)} %. "
                       f"**Nicht kippbar** sind Kriterien, die nur von den eigenen Partien des Spielers und der Startliste abhängen: {', '.join(zero)}. Das misst eine Möglichkeit, "
                       "keine Absicht.")


def verdict_cascades(c: dict):
    best_hit = max(c, key=lambda k: c[k].hit_rate)
    safe = min(c, key=lambda k: (c[k].flip_rate_t, -c[k].hit_rate))
    worst_flip = max(c, key=lambda k: c[k].flip_rate_t)
    if best_hit == safe:
        head = (f"Die Kaskade mit dem höchsten Treffer ist zugleich die am wenigsten kippbare: **{best_hit}** ({pct(c[best_hit].hit_rate)} % Treffer, "
                f"{pct(c[best_hit].flip_rate_t)} % der Turniere kippbar); ")
    else:
        head = (f"Die Kaskade mit dem höchsten Treffer ist **{best_hit}** ({pct(c[best_hit].hit_rate)} %), die am wenigsten kippbare **{safe}** "
                f"({pct(c[safe].flip_rate_t)} % der Turniere); ")
    return "info", (head + f"die am stärksten kippbare ist **{worst_flip}** ({pct(c[worst_flip].flip_rate_t)} %). "
                    "Alle trennen praktisch jedes Paar (zuletzt entscheidet das Los); sie unterscheiden sich in Treffer und Kippbarkeit, nicht in der Auflösung.")


def _hit(rows, key, w, mode):
    return next(r["hit_rate"] for r in rows if r["key"] == key and r["withdraw"] == w and r["mode"] == mode)


def verdict_withdraw(rows):
    w0, w1 = WITHDRAW_SETS[0][1], WITHDRAW_SETS[-1][1]
    bh0, bh_i, bh_f = _hit(rows, "BH", w0, "fide2026"), _hit(rows, "BH", w1, "ignore"), _hit(rows, "BH", w1, "fide2026")
    sb0, sb1 = _hit(rows, "SB", w0, "fide2026"), _hit(rows, "SB", w1, "fide2026")
    ps0, ps1 = _hit(rows, "PS", w0, "fide2026"), _hit(rows, "PS", w1, "fide2026")
    return "warning", (f"Bei {pct(w1)} % Rücktritten fällt **Buchholz von {pct(bh0)} auf {pct(bh_i)} %** (Runden nach dem Rücktritt ignoriert) bzw. "
                       f"**{pct(bh_f)} %** mit der FIDE-Regel: sie hilft, beseitigt den Einbruch aber nicht. **Sonneborn-Berger ({pct(sb0)} → {pct(sb1)} %) und "
                       f"Fortschritt ({pct(ps0)} → {pct(ps1)} %) steigen**. Die Fassungen 08/2024 und ab 03/2026 unterscheiden sich hier kaum.")


def verdict_bye(rows):
    def bias(key, mode):
        return signed(next(100 * r["bias"] for r in rows if r["key"] == key and r["mode"] == mode))
    return "warning", (f"Bei ungerader Zahl bekommt jede Runde ein Freilos. **Buchholz ignoriert es und benachteiligt die Inhaber** ({bias('BH', 'ignore')} "
                       f"Prozentpunkte), die FIDE-Regel dreht das um (**{bias('BH', 'fide2026')}**): Der Inhaber wird gerechnet, als hätte er gegen einen "
                       f"Gegner mit der eigenen Punktzahl gespielt. **Sonneborn-Berger geht von {bias('SB', 'ignore')} auf {bias('SB', 'fide2026')}.** "
                       f"Die Fortschrittswertung bleibt unverzerrt ({bias('PS', 'fide2026')}); **WIN zählt das Freilos als Sieg** und bevorzugt die Inhaber "
                       f"({bias('WIN', 'fide2026')}), WON benachteiligt sie ({bias('WON', 'fide2026')}).")


def _series(rows, key):
    return [r for r in rows if r["key"] == key]


def verdict_noise(rows):
    rt = {r["value"]: r["hit_rate"] for r in _series(rows, "RTNG")}
    ps = {r["value"]: r["hit_rate"] for r in _series(rows, "PS")}
    bh = {r["value"]: r["hit_rate"] for r in _series(rows, "BH-C1")}
    vals = sorted(rt)
    lo, hi = vals[0], vals[-1]
    return "info", (f"Die Startwertung trifft **{pct(rt[lo])} %** bei perfekter Setzliste (Rauschen {de(lo)}) und **{pct(rt[hi])} %** bei schlechter (Rauschen "
                    f"{de(hi)}). Der Fortschritt fällt von {pct(ps[lo])} auf {pct(ps[hi])} %, Buchholz Cut-1 bleibt zwischen {pct(min(bh.values()))} und "
                    f"{pct(max(bh.values()))} %. Die Startwertung ist ein Maß für die Setzliste: bei schlechter Setzliste liegt sie nicht mehr sicher vor den "
                    "Rechenkriterien.")


def verdict_draw(rows):
    bh = {r["value"]: r["hit_rate"] for r in _series(rows, "BH")}
    wins = {r["value"]: r for r in _series(rows, "WIN")}
    lo, hi = sorted(bh)[0], sorted(bh)[-1]
    return "info", (f"Mit mehr Remis sinkt die Trefferquote: Buchholz {pct(bh[lo])} % bei {pct(lo)} % Remis, {pct(bh[hi])} % bei {pct(hi)} %. **Siege** trennen ohne "
                    f"Remis fast nichts (Auflösung {pct(wins[lo]['resolution'])} %), bei {pct(hi)} % Remis {pct(wins[hi]['resolution'])} % der Paare.")


def verdict_size(rows):
    def at(label, key):
        return next(r["hit_rate"] for r in rows if r["value"] == label and r["key"] == key)
    small, big = SIZE_SETS[0][1], SIZE_SETS[-1][1]
    return "info", (f"Kleine Felder tragen kaum Information: im kleinsten Fall ({small}) trifft Buchholz {pct(at(small, 'BH'))} % und der Fortschritt "
                    f"{pct(at(small, 'PS'))} %, im größten ({big}) {pct(at(big, 'BH'))} % und {pct(at(big, 'PS'))} %. Mehr Runden helfen, weil jeder Spieler mehr "
                    "Gegner und mehr Ergebnisse hat.")


def recommendations(main: dict, withdraw_rows, bye_rows, noise_rows, size_rows) -> list:
    """Empfehlung nach Zweck, live aus den Messwerten: Liste von Zeilen (Zweck, Empfehlung, Messwert, Vorbehalt)."""
    rows = []
    solid = {k: m for k, m in main.items() if k in K.SOLID_KEYS and m.resolved and m.resolution >= 0.3}
    safe = [k for k, m in solid.items() if m.top_tie and m.flip_rate_t <= 0.05]
    pick = max(safe, key=lambda k: solid[k].hit_rate) if safe else min(solid, key=lambda k: solid[k].flip_rate_t)
    rows.append(("Preis oder Titel hängt an der Platzierung (Manipulationsschutz)", pick,
                 f"{pct(solid[pick].hit_rate)} % Treffer; in {pct(solid[pick].flip_rate_t)} % der Turniere mit Gleichstand um Platz 1 kippbar",
                 "Ein Kriterium aus den eigenen Partien des Spielers kann ein Dritter nicht verändern; es liest dafür weniger von der Spielstärke der Gegner."))
    order = sorted(solid, key=lambda k: -solid[k].hit_rate)
    rows.append(("Möglichst treffsicher, vollständiges Feld", f"{order[0]}, dann {order[1]}",
                 f"{pct(solid[order[0]].hit_rate)} und {pct(solid[order[1]].hit_rate)} % Treffer; Los 50 %",
                 f"Treffer und Kippbarkeit zusammen lesen: {order[1]} ist in {pct(solid[order[1]].flip_rate_t)} % der Turniere mit Gleichstand um Platz 1 kippbar; "
                 f"der Stichkampf trifft {pct(main[STICH].hit_rate)} %."))
    w1 = WITHDRAW_SETS[-1][1]
    cand = {r["key"]: r["hit_rate"] for r in withdraw_rows if r["withdraw"] == w1 and r["mode"] == "fide2026"}
    b = max(cand, key=cand.get)
    rows.append((f"Viele Rücktritte ({pct(w1)} %)", f"{b}; Buchholz meiden",
                 f"{pct(cand[b])} % Treffer; Buchholz {pct(cand['BH'])} % mit FIDE-Regel, {pct(_hit(withdraw_rows, 'BH', w1, 'ignore'))} % ohne",
                 "Rücktritte gleichverteilt zwischen Runde 3 und der vorletzten; keine Forfaits."))
    cand = {r["key"]: r["bias"] for r in bye_rows if r["mode"] == "fide2026" and r["pairs"] >= 200}
    b = min(cand, key=lambda k: abs(cand[k]))
    rows.append(("Ungerade Spielerzahl mit Freilosen", b,
                 f"Verzerrung {signed(100 * cand[b])} Prozentpunkte; Buchholz {signed(100 * cand['BH'])}, Sonneborn-Berger {signed(100 * cand['SB'])}",
                 "Das Freilos geht im Paarungsverfahren an Spieler der unteren Punktgruppen; jede Behandlung ist ein Konstrukt."))
    worst = sorted({r["value"] for r in noise_rows})[-1]
    cand = {r["key"]: r["hit_rate"] for r in noise_rows if r["value"] == worst and r["key"] not in ("RTNG", STICH, LOS) and r["resolution"] >= 0.3}
    b = max(cand, key=cand.get)
    rt = next(r["hit_rate"] for r in noise_rows if r["value"] == worst and r["key"] == "RTNG")
    rows.append((f"Schwache Setzliste (Rauschen {de(worst)})", f"{b}; die Startwertung nicht als Tie-Breaker",
                 f"{pct(cand[b])} % Treffer; Startwertung {pct(rt)} %",
                 "Die Startwertung misst die Güte der Setzliste, nicht die Leistung im Turnier."))
    rows.append(("Eine zusätzliche Partie ist möglich", "Stichkampf unter den Punktgleichen",
                 f"{pct(main[STICH].hit_rate)} % Treffer, besser als jedes Rechenkriterium",
                 "Kostet eine Partie je Gleichstand und ist selbst ein Zufallsergebnis (Remis nicht eingerechnet)."))
    small = SIZE_SETS[0][1]
    cand = {r["key"]: r["hit_rate"] for r in size_rows if r["value"] == small and r["key"] not in ("RTNG", STICH, LOS) and r["resolution"] >= 0.3}
    b = max(cand, key=cand.get)
    rows.append((f"Kleines Feld, kurzes Turnier ({small})", "keine verlässliche Rangfolge; das Los ist ehrlich",
                 f"bestes Kriterium {b} mit {pct(cand[b])} % Treffer",
                 "Hier entscheidet das Verfahren über Platz 1, nicht die Stärke; die Regel vorab bekannt machen."))
    return rows
