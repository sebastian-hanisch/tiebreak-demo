"""Tie-Breaker nach FIDE C.07 (Fassungen 08/2024 und ab 03/2026), die Behandlung nicht gespielter Runden (Artikel 16) und die Kaskade.

Spieler sind Startnummern 1..n. Alle Werte sind „größer ist besser“. Nur der Direktvergleich (Artikel 6) hängt von der Gruppe der Punktgleichen ab und wird deshalb
nicht vorab, sondern je Gruppe berechnet (`direct_encounter`). Die Kaskade löst jede Gruppe Stufe für Stufe auf (Artikel 4.2: für jede verbleibende Untergruppe
weiter in der Liste) und lost am Ende."""

import math
from collections import defaultdict
from dataclasses import replace

import turnier_generator as T
import tbk_constants as C
from tbk_tournament import Game, Tournament, missing_rounds

KEYS = ("BH", "BH-C1", "BH-C2", "BH-M1", "BH-M2", "AOB", "SB", "DE", "PS", "PS-G", "WIN", "WON", "BWG", "BPG", "REP", "ARO", "TPR", "RTNG")
NAMES = {
    "BH": "Buchholz",
    "BH-C1": "Buchholz ohne den schwächsten Gegner (Cut-1)",
    "BH-C2": "Buchholz ohne die zwei schwächsten Gegner (Cut-2)",
    "BH-M1": "Buchholz ohne besten und schwächsten Gegner (Median-1)",
    "BH-M2": "Buchholz ohne die zwei besten und zwei schwächsten (Median-2)",
    "AOB": "Mittlerer Buchholz der Gegner",
    "SB": "Sonneborn-Berger",
    "DE": "Direktvergleich",
    "PS": "Fortschrittswertung (Summe der Zwischenstände)",
    "PS-G": "Fortschrittswertungen der Gegner",
    "WIN": "Siege (auch ohne Spiel, z. B. Freilos)",
    "WON": "Siege am Brett",
    "BWG": "Siege mit Schwarz",
    "BPG": "Partien mit Schwarz",
    "REP": "Runden, in denen man spielen wollte",
    "ARO": "Mittlere Gegnerwertung",
    "TPR": "Leistungswertung",
    "RTNG": "Startwertung",
}
VALUE_KEYS = tuple(k for k in KEYS if k != "DE")
REFERENCES = ("STICH", "LOS")                         # Stichkampf (eine Partie) und Los: Referenzen, keine Rechenkriterien
REFERENCE_NAMES = {"STICH": "Stichkampf (eine Partie, Referenz)", "LOS": "Los (Referenz)"}
SOLID_KEYS = tuple(k for k in KEYS if k != "RTNG")    # ohne die Setzliste, die kein Leistungsmaß ist
LOT_SALT = 0x10C


def label(key: str) -> str:
    return f"{key} – {NAMES.get(key) or REFERENCE_NAMES[key]}"


# ---------------------------------------------------------------------------------------------------------------------------------------------

def over_the_board(gl):
    return [g for g in gl if not g.bye]


def _cut(contrib, low: int, high: int, fide: bool) -> float:
    """Summe der Beiträge ohne die `low` kleinsten und `high` größten. FIDE 16.5: bei freiwillig nicht gespielten Runden (VUR) wird zuerst der kleinste VUR-Beitrag
    gestrichen, sofern er nicht unter dem kleinsten Wert liegt (das ist stets der Fall, wenn es einen VUR-Beitrag gibt)."""
    vals = sorted(contrib, key=lambda x: x[0])
    for _ in range(low):
        if not vals:
            break
        vur = [i for i, (_v, f) in enumerate(vals) if f]
        vals.pop(vur[0] if fide and vur else 0)
    for _ in range(high):
        if vals:
            vals.pop()
    return sum(v for v, _f in vals)


def progressive(t: Tournament) -> list:
    """Summe der Zwischenstände nach jeder der `rounds` Runden (Runden ohne Bericht bringen nichts, der Stand bleibt)."""
    out = []
    for gl in t.games:
        per_round = defaultdict(float)
        for g in gl:
            per_round[g.round_no] += g.score
        run = total = 0.0
        for rnd in range(1, t.rounds + 1):
            run += per_round.get(rnd, 0.0)
            total += run
        out.append(total)
    return out


def values(t: Tournament, mode: str = "ignore") -> dict:
    """Alle Kriterien außer DE: Schlüssel -> Liste je Startnummer (Index = Nummer − 1).

    `mode`: "ignore" (Freilos und Runden nach Rücktritt zählen für Buchholz und Sonneborn-Berger nicht) oder FIDE Artikel 16 in der Fassung "fide2024" bzw.
    "fide2026" (Unterschied: der Dummy-Gegner für eigene nicht gespielte Runden hat höchstens 0,5 · Rundenzahl Punkte, Artikel 16.4.2)."""
    if mode not in C.MODES:
        raise ValueError(f"unbekannte Behandlung: {mode}")
    n, R = t.n, t.rounds
    fide = mode != "ignore"
    score = t.score
    miss = [missing_rounds(t, r) for r in range(1, n + 1)]
    eff = [score[i] + (0.5 * miss[i] if fide else 0.0) for i in range(n)]        # 16.3: Runden nach Rücktritt zählen für die Gegner als Remis
    cap = 0.5 * R if mode == "fide2026" else math.inf
    dummy = [min(score[i], cap) for i in range(n)]                                 # 16.4: Dummy mit der eigenen Punktzahl (ab 03/2026 gedeckelt)
    board = [over_the_board(gl) for gl in t.games]
    contrib = []
    for i in range(n):
        c = [(eff[g.opponent - 1], False) for g in board[i]]
        if fide:
            c += [(dummy[i], False) for g in t.games[i] if g.bye]                  # Freilos des Paarungsprogramms: keine freiwillig nicht gespielte Runde
            c += [(dummy[i], True)] * miss[i]                                      # Runden nach Rücktritt: freiwillig nicht gespielt
        contrib.append(c)
    bh = [sum(v for v, _f in c) for c in contrib]
    ps = progressive(t)
    out = {k: [0.0] * n for k in VALUE_KEYS}
    for i in range(n):
        opp = [g.opponent - 1 for g in board[i]]
        out["BH"][i] = bh[i]
        out["BH-C1"][i] = _cut(contrib[i], 1, 0, fide)
        out["BH-C2"][i] = _cut(contrib[i], 2, 0, fide)
        out["BH-M1"][i] = _cut(contrib[i], 1, 1, fide)
        out["BH-M2"][i] = _cut(contrib[i], 2, 2, fide)
        out["AOB"][i] = sum(bh[o] for o in opp) / len(opp) if opp else 0.0
        sb = sum(eff[g.opponent - 1] * g.score for g in board[i])
        if fide:
            sb += sum(dummy[i] * g.score for g in t.games[i] if g.bye)
        out["SB"][i] = sb
        out["PS"][i] = ps[i]
        out["PS-G"][i] = sum(ps[o] for o in opp)
        out["WIN"][i] = sum(1 for g in t.games[i] if g.score == 1.0)
        out["WON"][i] = sum(1 for g in board[i] if g.score == 1.0)
        out["BWG"][i] = sum(1 for g in board[i] if g.colour == "b" and g.score == 1.0)
        out["BPG"][i] = sum(1 for g in board[i] if g.colour == "b")
        out["REP"][i] = R - miss[i]
        aro = sum(t.start[o] for o in opp) / len(opp) if opp else 0.0
        out["ARO"][i] = aro
        frac = sum(g.score for g in board[i]) / len(opp) if opp else 0.5
        frac = min(max(frac, 0.02), 0.98)
        out["TPR"][i] = aro + math.log(frac / (1.0 - frac))                          # logistische Einheiten; die Skala ändert die Ordnung nicht
        out["RTNG"][i] = t.start[i]
    return out


def direct_encounter(group, games) -> list:
    """FIDE Artikel 6 für eine Gruppe punktgleicher Spieler: geordnete Blöcke (Liste von Listen), beste zuerst.

    Die Summe der Ergebnisse gegeneinander (mehrfache Treffen als Mittel) trennt die Gruppe. Haben alle einander gespielt, entscheidet die Tabelle; sonst wird im
    Schweizer System nur ein Spieler vorn eingeordnet, der es unabhängig vom Ausgang der fehlenden Partien ist (6.3); danach gilt Artikel 6 erneut für den Rest."""
    group = list(group)
    if len(group) < 2:
        return [group]
    members = set(group)
    meetings = {r: defaultdict(list) for r in group}
    for r in group:
        for g in games[r - 1]:
            if not g.bye and g.opponent in members:
                meetings[r][g.opponent].append(g.score)
    s = {r: sum(sum(v) / len(v) for v in meetings[r].values()) for r in group}
    missing = {r: len(group) - 1 - len(meetings[r]) for r in group}
    if all(m == 0 for m in missing.values()):
        blocks = defaultdict(list)
        for r in group:
            blocks[round(s[r], 9)].append(r)
        ordered = [blocks[k] for k in sorted(blocks, reverse=True)]
        if len(ordered) == 1:
            return ordered
        out = []
        for b in ordered:
            out += direct_encounter(b, games)
        return out
    top = [i for i in group if all(s[i] > s[j] + missing[j] for j in group if j != i)]
    if not top:
        return [group]
    rest = [r for r in group if r != top[0]]
    return [[top[0]]] + direct_encounter(rest, games)


def _split(group, key: str, vals: dict, games) -> list:
    """Teilt eine Gruppe nach einem Kriterium in geordnete Blöcke (beste zuerst)."""
    if key == "DE":
        return direct_encounter(group, games)
    blocks = defaultdict(list)
    for r in group:
        blocks[round(vals[key][r - 1], 9)].append(r)
    return [blocks[k] for k in sorted(blocks, reverse=True)]


def lots(t: Tournament) -> list:
    """Ein fester Losentscheid je Turnier (Gleichverteilte je Startnummer)."""
    return [float(u) for u in T.SplitMix64(t.seed ^ LOT_SALT).uniform(t.n)]


def _resolve(group, crits, vals, games, lot, reason):
    if len(group) == 1:
        return [(group[0], reason)]
    if not crits:
        order = sorted(group, key=lambda r: lot[r - 1])
        return [(order[0], reason)] + [(r, "LOS") for r in order[1:]]
    c, rest = crits[0], crits[1:]
    blocks = _split(group, c, vals, games)
    if len(blocks) == 1:
        return _resolve(group, rest, vals, games, lot, reason)
    out = []
    for i, b in enumerate(blocks):
        out += _resolve(b, rest, vals, games, lot, reason if i == 0 else c)
    return out


def standing(t: Tournament, cascade, mode: str = "ignore", vals: dict | None = None, lot: list | None = None) -> list:
    """Endstand nach Punkten, dann der Kaskade, dann Los: Liste (Startnummer, Grund der Trennung vom Vorgänger) in Platzfolge.

    Der Grund ist "" für Platz 1, "Punkte" bei anderem Punktestand, sonst das Kriterium, das den Spieler vom Vorgänger trennt, oder "LOS"."""
    vals = values(t, mode) if vals is None else vals
    lot = lots(t) if lot is None else lot
    score = t.score
    groups = defaultdict(list)
    for r in range(1, t.n + 1):
        groups[score[r - 1]].append(r)
    out = []
    for s in sorted(groups, reverse=True):
        part = _resolve(groups[s], list(cascade), vals, t.games, lot, "Punkte" if out else "")
        out += part
    return out


# ---------------------------------------------------------------------------------------------------------------------------------------------

def flip_game(t: Tournament, a: int, b: int, round_no: int) -> Tournament:
    """Kopie des Turniers, in der der Ausgang der Partie a gegen b in Runde `round_no` umgekehrt ist (Sieg ↔ Niederlage; Remis → Sieg von a)."""
    games = [list(gl) for gl in t.games]
    new_a = None
    for idx, g in enumerate(games[a - 1]):
        if g.opponent == b and g.round_no == round_no and not g.bye:
            new_a = 1.0 - g.score if g.score != 0.5 else 1.0
            games[a - 1][idx] = g._replace(score=new_a)
    if new_a is None:
        raise ValueError("diese Partie gibt es nicht")
    for idx, g in enumerate(games[b - 1]):
        if g.opponent == a and g.round_no == round_no and not g.bye:
            games[b - 1][idx] = g._replace(score=1.0 - new_a)
    return replace(t, games=tuple(tuple(gl) for gl in games))


def irrelevant_games(t: Tournament, margin: float = C.FLIP_MARGIN) -> list:
    """Partien der letzten Runde, an denen niemand beteiligt ist, der durch die Umkehr in die Spitzengruppe rücken könnte: beide mindestens `margin` Punkte
    unter dem Besten. Rückgabe: Liste (a, b) mit a < b."""
    score = t.score
    top = max(score)
    seen, out = set(), []
    for r in range(1, t.n + 1):
        for g in t.games[r - 1]:
            if g.round_no == t.rounds and not g.bye:
                pair = (min(r, g.opponent), max(r, g.opponent))
                if pair not in seen and score[pair[0] - 1] <= top - margin and score[pair[1] - 1] <= top - margin:
                    seen.add(pair)
                    out.append(pair)
    return out


def winner_of(t: Tournament, cascade, vals: dict, lot: list) -> int:
    """Sieger des Turniers: der Erste der Spitzengruppe nach der Kaskade (und Los). Rechnet nur die Spitzengruppe, nicht den ganzen Endstand."""
    score = t.score
    top = max(score)
    group = [r for r in range(1, t.n + 1) if score[r - 1] == top]
    return _resolve(group, list(cascade), vals, t.games, lot, "")[0][0]
