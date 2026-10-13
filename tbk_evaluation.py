"""Maße und Experimente: wie gut trennen die Kriterien die Punktgleichen, und wie leicht lassen sie sich kippen.

Alle Aussagen über „richtig“ messen gegen die wahre Stärke, die nur in der Simulation bekannt ist. Maße je Kriterium oder Kaskade (über feste Turniere):
Auflösung (Anteil punktgleicher Paare, die es trennt), Treffer (Anteil richtig geordneter getrennter Paare), Erwartung (mittlere σ der Stärkedifferenz des Vorderen),
Sieger richtig, Podium richtig, τ des Endstandes gegen die Stärke, Kippen (Turniere mit Gleichstand um Platz 1, in denen die Umkehr einer irrelevanten Partie der
letzten Runde den Sieger ändert) und Freilos-Verzerrung (bei Paaren mit genau einem Freilos-Inhaber: Anteil „Inhaber vorn“ minus Anteil „Inhaber stärker“)."""

import math
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np

import tbk_constants as C
import tbk_criteria as K
import tbk_data as D
import turnier_generator as T
from tbk_scenario import Settings, make_tournament

STICH, LOS = "STICH", "LOS"
STICH_SALT = 0x57C


def de(x: float, digits: int = 1) -> str:
    """Zahl mit Dezimalkomma."""
    return f"{x:.{digits}f}".replace(".", ",")


def signed(x: float) -> str:
    """Ganzzahl mit Vorzeichen (echtes Minus, kein „−0“): +8, −13, ±0."""
    v = int(round(x))
    if v == 0:
        return "±0"
    return f"+{v}" if v > 0 else f"−{-v}"


def pct(x: float, digits: int = 0) -> str:
    """Anteil (0 bis 1) als Prozentzahl mit Dezimalkomma, ohne Prozentzeichen."""
    return de(100 * x, digits)
CASCADES = {
    "DE → BH-C1 → BH → WIN": ("DE", "BH-C1", "BH", "WIN"),
    "BH-C1 → BH → SB → DE": ("BH-C1", "BH", "SB", "DE"),
    "PS → BH-C1 → SB": ("PS", "BH-C1", "SB"),
    "WIN → DE → BH": ("WIN", "DE", "BH"),
    "DE → PS → BH-C1": ("DE", "PS", "BH-C1"),
    "AOB → BH → SB": ("AOB", "BH", "SB"),
    "BH-C1 → RTNG": ("BH-C1", "RTNG"),
}


def sig(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


@dataclass
class Counts:
    pairs: int = 0
    resolved: int = 0
    hits: int = 0
    expect: float = 0.0
    tournaments: int = 0
    winner_ok: int = 0
    podium_ok: int = 0
    tau: float = 0.0
    top_tie: int = 0            # Turniere mit Gleichstand um Platz 1
    flip_t: int = 0             # davon: mit mindestens einer Umkehr, die den Sieger ändert
    flip_games: int = 0
    flip_changed: int = 0
    bye_pairs: int = 0
    bye_front: int = 0
    bye_stronger: int = 0


@dataclass(frozen=True)
class Metrics:
    key: str
    pairs: int
    resolved: int
    resolution: float
    hit_rate: float
    expectation: float
    winner_rate: float
    podium_rate: float
    tau: float
    tournaments: int
    top_tie: int
    flip_rate_t: float          # Anteil der Turniere mit Gleichstand um Platz 1
    flip_rate_g: float          # Anteil der Umkehrungen
    flip_games: int
    bye_pairs: int
    bye_bias: float             # Anteil „Inhaber vorn“ minus Anteil „Inhaber stärker“


def _ratio(a, b):
    return a / b if b else float("nan")


def _metrics(key: str, c: Counts) -> Metrics:
    return Metrics(key, c.pairs, c.resolved, _ratio(c.resolved, c.pairs), _ratio(c.hits, c.resolved), _ratio(c.expect, c.resolved),
                   _ratio(c.winner_ok, c.tournaments), _ratio(c.podium_ok, c.tournaments), _ratio(c.tau, c.tournaments), c.tournaments, c.top_tie,
                   _ratio(c.flip_t, c.top_tie), _ratio(c.flip_changed, c.flip_games), c.flip_games, c.bye_pairs,
                   _ratio(c.bye_front - c.bye_stronger, c.bye_pairs))


def kendall_tau(order, strength) -> float:
    """τ des Endstandes (Startnummern, beste zuerst) gegen die wahre Stärke: (konkordant − diskordant) / Paare."""
    n = len(order)
    s = np.array([strength[r - 1] for r in order])
    diff = np.sign(s[:, None] - s[None, :])                 # >0: Zeile steht vor Spalte und ist stärker
    iu = np.triu_indices(n, 1)
    return float(diff[iu].sum() / len(iu[0]))


def _runs(order_with_reason, score):
    """Je Startnummer die Lauf-Nummer: Punktgruppe und Folge ungelöster Gleichstände ('LOS') bilden einen Lauf."""
    run, out = -1, {}
    for r, why in order_with_reason:
        if why != "LOS":
            run += 1
        out[r] = run
    return out


def _stichkampf_order(t, score):
    """Stichkampf unter den Punktgleichen: der Ausgang einer Partie ist σ(Δ) zugunsten des Stärkeren (logistisches Rauschen auf der Stärke)."""
    u = T.SplitMix64(t.seed ^ STICH_SALT).uniform(t.n)
    noisy = [t.strength[r] + math.log(u[r] / (1.0 - u[r])) for r in range(t.n)]
    return sorted(range(1, t.n + 1), key=lambda r: (-score[r - 1], -noisy[r - 1]))


def measure(tournaments, specs: dict, mode: str = "ignore", flips: bool = True) -> dict:
    """`specs`: Name -> Kaskade (Tupel von Kriterien) oder "STICH"/"LOS". Rückgabe: Name -> Metrics."""
    counts = {name: Counts() for name in specs}
    for t in tournaments:
        score, strength = t.score, t.strength
        vals, lot = K.values(t, mode), K.lots(t)
        best = max(range(1, t.n + 1), key=lambda r: strength[r - 1])
        top3 = set(sorted(range(1, t.n + 1), key=lambda r: -strength[r - 1])[:3])
        has_bye = [any(g.bye for g in gl) for gl in t.games]
        groups = defaultdict(list)
        for r in range(1, t.n + 1):
            groups[score[r - 1]].append(r)
        top = max(score)
        tied_top = len(groups[top]) >= 2
        flip_cases = []
        if flips and tied_top:
            for a, b in K.irrelevant_games(t):
                t2 = K.flip_game(t, a, b, t.rounds)
                flip_cases.append((t2, K.values(t2, mode)))
        for name, spec in specs.items():
            c = counts[name]
            c.tournaments += 1
            if spec == STICH:
                order = _stichkampf_order(t, score)
                for g in groups.values():
                    for i in range(len(g)):
                        for j in range(i + 1, len(g)):
                            c.pairs += 1
                            c.resolved += 1
                            p = sig(abs(strength[g[i] - 1] - strength[g[j] - 1]))
                            c.hits += p                                    # erwartete Treffer: der Stärkere gewinnt die Partie mit σ(|Δ|)
                            c.expect += p
            else:
                cascade = () if spec == LOS else tuple(spec)
                st = K.standing(t, cascade, mode, vals, lot)
                order = [r for r, _w in st]
                run = _runs(st, score)
                for g in groups.values():
                    for i in range(len(g)):
                        for j in range(i + 1, len(g)):
                            a, b = g[i], g[j]
                            c.pairs += 1
                            if run[a] == run[b]:
                                continue
                            c.resolved += 1
                            front, back = (a, b) if run[a] < run[b] else (b, a)
                            c.hits += int(strength[front - 1] > strength[back - 1])
                            c.expect += sig(strength[front - 1] - strength[back - 1])
                            if has_bye[a - 1] != has_bye[b - 1]:
                                holder, other = (a, b) if has_bye[a - 1] else (b, a)
                                c.bye_pairs += 1
                                c.bye_front += int(front == holder)
                                c.bye_stronger += int(strength[holder - 1] > strength[other - 1])
            c.winner_ok += int(order[0] == best)
            c.podium_ok += int(set(order[:3]) == top3)
            c.tau += kendall_tau(order, strength)
            if tied_top and spec not in (STICH, LOS):
                c.top_tie += 1
                base = K.winner_of(t, spec, vals, lot)
                changed = False
                for t2, vals2 in flip_cases:
                    c.flip_games += 1
                    ch = int(K.winner_of(t2, spec, vals2, lot) != base)
                    c.flip_changed += ch
                    changed = changed or bool(ch)
                c.flip_t += int(changed)
    return {name: _metrics(name, counts[name]) for name in specs}


def single_specs(keys=K.KEYS, references=True) -> dict:
    specs = {k: (k,) for k in keys}
    if references:
        specs[STICH] = STICH
        specs[LOS] = LOS
    return specs


# --- Das Turnier der Reglerwerte -----------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Analysis:
    settings: Settings
    tournament: object
    values: dict
    standing: tuple                  # ((Startnummer, Grund), …) in Platzfolge
    score: tuple
    metrics: Metrics                 # Maße der gewählten Kaskade auf diesem einen Turnier
    top_group: tuple                 # Spieler mit Höchstpunktzahl
    winner: int
    best: int                        # wahrer Stärkster
    flips: tuple                     # ((a, b, Sieger nach der Umkehr), …) für die irrelevanten Partien der letzten Runde


def analyse(s: Settings) -> Analysis:
    t = make_tournament(s)
    vals, lot = K.values(t, s.mode), K.lots(t)
    st = K.standing(t, s.cascade, s.mode, vals, lot)
    score = t.score
    top = max(score)
    group = tuple(r for r in range(1, t.n + 1) if score[r - 1] == top)
    m = measure([t], {"cascade": tuple(s.cascade)}, s.mode, flips=True)["cascade"]
    flips = []
    for a, b in K.irrelevant_games(t):
        t2 = K.flip_game(t, a, b, t.rounds)
        flips.append((a, b, K.winner_of(t2, s.cascade, K.values(t2, s.mode), lot)))
    best = max(range(1, t.n + 1), key=lambda r: t.strength[r - 1])
    return Analysis(s, t, vals, tuple(st), score, m, group, st[0][0], best, tuple(flips))


# --- Experimente ---------------------------------------------------------------------------------------------------------------------------------

def exp_criteria(mode: str = "fide2026") -> dict:
    """E1 und E2: alle Kriterien auf den 150 Turnieren der Hauptkonfiguration (32 Spieler, 7 Runden, 20 % Remis, Rauschen 0,4)."""
    return measure(D.tournaments("main"), single_specs(), mode, flips=True)


def exp_cascades(mode: str = "fide2026") -> dict:
    return measure(D.tournaments("main"), dict(CASCADES), mode, flips=True)


WITHDRAW_SETS = (("main", 0.0), ("w15", 0.15), ("w30", 0.30))
WITHDRAW_KEYS = ("BH", "BH-C1", "AOB", "SB", "PS", "WIN", "TPR")


def exp_withdraw() -> list:
    """E4: Rücktritte 0/15/30 % gegen die Behandlung nicht gespielter Runden. Zeilen: (Rücktritte, Modus, Schlüssel) -> Metrics."""
    rows = []
    for set_key, w in WITHDRAW_SETS:
        for mode in C.MODES:
            res = measure(D.tournaments(set_key), single_specs(WITHDRAW_KEYS, references=False), mode, flips=False)
            for k, m in res.items():
                rows.append({"withdraw": w, "mode": mode, "key": k, "hit_rate": m.hit_rate, "resolution": m.resolution})
    return rows


BYE_KEYS = ("BH", "BH-C1", "BH-M1", "AOB", "SB", "WIN", "WON", "PS", "TPR", "DE", "RTNG")


def exp_bye() -> list:
    """E5: n = 31, jede Runde ein Freilos: Verzerrung zugunsten der Freilos-Inhaber, je Behandlung."""
    rows = []
    for mode in C.MODES:
        res = measure(D.tournaments("n31"), single_specs(BYE_KEYS, references=False), mode, flips=False)
        for k, m in res.items():
            rows.append({"mode": mode, "key": k, "bias": m.bye_bias, "pairs": m.bye_pairs, "hit_rate": m.hit_rate})
    return rows


NOISE_SETS = (("noise0", 0.0), ("main", 0.4), ("noise10", 1.0), ("noise20", 2.0))
DRAW_SETS = (("draw0", 0.0), ("main", 0.2), ("draw40", 0.4))
SIZE_SETS = (("n16r5", "16 Spieler, 5 Runden"), ("n32r5", "32 Spieler, 5 Runden"), ("main", "32 Spieler, 7 Runden"), ("n32r9", "32 Spieler, 9 Runden"))
SETTING_KEYS = ("BH", "BH-C1", "AOB", "SB", "DE", "PS", "WIN", "RTNG")


def exp_setting(sets, mode: str = "fide2026", keys=SETTING_KEYS, references=True) -> list:
    """E6 und E7: Treffer je Kriterium über eine Folge fester Mengen. `sets`: ((Schlüssel, Wert), …)."""
    rows = []
    for set_key, value in sets:
        res = measure(D.tournaments(set_key), single_specs(keys, references=references), mode, flips=False)
        for k, m in res.items():
            rows.append({"value": value, "key": k, "hit_rate": m.hit_rate, "resolution": m.resolution, "winner_rate": m.winner_rate})
    return rows
