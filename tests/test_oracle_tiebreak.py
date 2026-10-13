"""Orakel-Tests: die Kriterien, die Kaskade, der Direktvergleich und die Umkehr gegen unabhängige Rechenwege.

- Kriterien: rundenweise Schleife über die Spielberichte statt der Partienlisten der Implementierung, mit eigener Behandlung nicht gespielter Runden (FIDE Art. 16).
- Kaskade: lexikografischer Schlüssel mit `sorted` statt der rekursiven Auflösung.
- Direktvergleich: Aufzählung aller möglichen Ausgänge der fehlenden Partien („unabhängig vom Ausgang der fehlenden Partien“ wörtlich).
- Umkehr: nur Spieler, die einen der beiden Beteiligten gespielt haben, ändern ihre gegnerabhängigen Werte.
Die Turniere sind ein fester Ausschnitt der vorberechneten Mengen; alles unter 10 Sekunden."""

import itertools
import math
import random

import pytest

import tbk_criteria as K
import tbk_data as D
from conftest import build


def _round_record(t, r, rnd):
    for g in t.games[r - 1]:
        if g.round_no == rnd:
            return g
    return None


def oracle_values(t, mode):
    """Unabhängig: je Runde nachsehen, ob und wie der Spieler gespielt hat."""
    n, R = t.n, t.rounds
    fide = mode != "ignore"
    cap = 0.5 * R if mode == "fide2026" else math.inf
    score = [sum(g.score for g in t.games[r]) for r in range(n)]
    played = [sum(1 for rnd in range(1, R + 1) if _round_record(t, r + 1, rnd) is not None) for r in range(n)]
    adjusted = [score[r] + (0.5 * (R - played[r]) if fide else 0.0) for r in range(n)]
    bh_parts, out = [], {}
    for r in range(n):
        parts = []                                                # (Wert, freiwillig nicht gespielt)
        for rnd in range(1, R + 1):
            g = _round_record(t, r + 1, rnd)
            if g is None:
                if fide:
                    parts.append((min(score[r], cap), True))
            elif g.bye:
                if fide:
                    parts.append((min(score[r], cap), False))
            else:
                parts.append((adjusted[g.opponent - 1], False))
        bh_parts.append(parts)

    def cut(parts, low, high):
        rest = sorted(parts)                                      # (Wert, Flag): bei gleichem Wert zuerst die nicht freiwilligen
        for _ in range(low):
            if not rest:
                break
            vur = [p for p in rest if p[1]]
            victim = min(vur) if (fide and vur) else rest[0]
            rest.remove(victim)
        for _ in range(high):
            if rest:
                rest.pop()
        return sum(v for v, _f in rest)

    out["BH"] = [sum(v for v, _f in p) for p in bh_parts]
    out["BH-C1"] = [cut(p, 1, 0) for p in bh_parts]
    out["BH-C2"] = [cut(p, 2, 0) for p in bh_parts]
    out["BH-M1"] = [cut(p, 1, 1) for p in bh_parts]
    out["BH-M2"] = [cut(p, 2, 2) for p in bh_parts]
    sb, ps, win, won, bwg, bpg, aob, psg = [], [], [], [], [], [], [], []
    for r in range(n):
        s_sb = s_win = s_won = s_bwg = s_bpg = 0.0
        run = tot = 0.0
        opp = []
        for rnd in range(1, R + 1):
            g = _round_record(t, r + 1, rnd)
            if g is not None:
                run += g.score
                s_win += int(g.score == 1.0)
                if g.bye:
                    if fide:
                        s_sb += min(score[r], cap) * g.score
                else:
                    opp.append(g.opponent)
                    s_sb += adjusted[g.opponent - 1] * g.score
                    s_won += int(g.score == 1.0)
                    s_bpg += int(g.colour == "b")
                    s_bwg += int(g.colour == "b" and g.score == 1.0)
            tot += run
        sb.append(s_sb)
        ps.append(tot)
        win.append(s_win)
        won.append(s_won)
        bwg.append(s_bwg)
        bpg.append(s_bpg)
    for r in range(n):
        opp = [g.opponent for g in t.games[r] if not g.bye]
        aob.append(sum(out["BH"][o - 1] for o in opp) / len(opp) if opp else 0.0)
        psg.append(sum(ps[o - 1] for o in opp))
    out.update({"SB": sb, "PS": ps, "WIN": win, "WON": won, "BWG": bwg, "BPG": bpg, "AOB": aob, "PS-G": psg})
    out["REP"] = played
    out["ARO"] = [sum(t.start[g.opponent - 1] for g in t.games[r] if not g.bye) / max(1, sum(1 for g in t.games[r] if not g.bye)) for r in range(n)]
    return out


SAMPLE = [(key, i) for key, count in (("main", 6), ("n31", 4), ("w30", 4), ("w15", 2), ("n16r5", 3)) for i in range(count)]


@pytest.mark.parametrize("mode", ["ignore", "fide2024", "fide2026"])
def test_values_equal_the_round_by_round_oracle(mode):
    for key, i in SAMPLE:
        t = D.tournaments(key)[i]
        mine, theirs = K.values(t, mode), oracle_values(t, mode)
        for k, v in theirs.items():
            assert mine[k] == pytest.approx(v, abs=1e-9), (key, i, mode, k)


def test_the_cascade_equals_a_lexicographic_sort_for_criteria_without_the_direct_encounter():
    rng = random.Random(7)
    pool = [k for k in K.KEYS if k != "DE"]
    for key, i in SAMPLE[:10]:
        t = D.tournaments(key)[i]
        vals, lot, score = K.values(t, "fide2026"), K.lots(t), t.score
        for _ in range(4):
            cascade = tuple(rng.sample(pool, rng.randint(1, 4)))
            expected = sorted(range(1, t.n + 1), key=lambda r: (-score[r - 1], *(-round(vals[c][r - 1], 9) for c in cascade), lot[r - 1]))
            assert [r for r, _w in K.standing(t, cascade, "fide2026", vals, lot)] == expected, (key, i, cascade)


def test_the_standing_never_reorders_players_with_different_points():
    for key, i in SAMPLE[:6]:
        t = D.tournaments(key)[i]
        order = [r for r, _w in K.standing(t, ("DE", "BH-C1", "BH", "WIN"), "fide2026")]
        pts = [t.score[r - 1] for r in order]
        assert pts == sorted(pts, reverse=True) and sorted(order) == list(range(1, t.n + 1))


# --- Direktvergleich gegen die Aufzählung aller Ausgänge der fehlenden Partien ------------------------------------------------------------

def oracle_de(group, results, missing_pairs):
    """`results`: {(a, b): Punkte von a} für gespielte Paare (a < b); `missing_pairs`: Liste der fehlenden Paare. Geordnete Blöcke wie Artikel 6."""
    group = sorted(group)
    if len(group) < 2:
        return [group]
    pairs = [(a, b) for a, b in itertools.combinations(group, 2)]
    res = {p: results[p] for p in pairs if p in results}
    miss = [p for p in pairs if p not in res]
    if not miss:
        total = {r: 0.0 for r in group}
        for (a, b), p in res.items():
            total[a] += p
            total[b] += 1.0 - p
        levels = sorted({total[r] for r in group}, reverse=True)
        blocks = [[r for r in group if total[r] == lv] for lv in levels]
        if len(blocks) == 1:
            return blocks
        out = []
        for b in blocks:
            out += oracle_de(b, results, []) if len(b) > 1 else [b]
        return out
    alone = None
    for cand in group:
        ok = True
        for outcome in itertools.product((0.0, 0.5, 1.0), repeat=len(miss)):
            full = dict(res)
            full.update(dict(zip(miss, outcome)))
            total = {r: 0.0 for r in group}
            for (a, b), p in full.items():
                total[a] += p
                total[b] += 1.0 - p
            if not all(total[cand] > total[o] for o in group if o != cand):
                ok = False
                break
        if ok:
            alone = cand
            break
    if alone is None:
        return [group]
    return [[alone]] + oracle_de([r for r in group if r != alone], results, [])


def test_the_direct_encounter_equals_the_enumeration_of_all_outcomes_of_the_missing_games():
    rng = random.Random(3)
    checked = 0
    for _ in range(250):
        size = rng.randint(2, 4)
        group = list(range(1, size + 1))
        pairs = list(itertools.combinations(group, 2))
        results = {}
        for p in pairs:
            if rng.random() < 0.6:
                results[p] = rng.choice((0.0, 0.5, 1.0))
        rounds = [[] for _ in range(max(1, len(results)))]
        # jede gespielte Partie in eine eigene Runde (weiß = der Kleinere)
        for k, ((a, b), pts) in enumerate(results.items()):
            rounds[k].append((a, b, pts))
        t = build(size, len(rounds), rounds)
        got = K.direct_encounter(group, t.games)
        want = oracle_de(group, results, [p for p in pairs if p not in results])
        assert [sorted(b) for b in got] == [sorted(b) for b in want], (results, got, want)
        checked += 1
    assert checked == 250


# --- Umkehr einer Partie ---------------------------------------------------------------------------------------------------------------

def test_a_flip_changes_the_opponent_dependent_values_only_of_the_neighbours():
    for key, i in (("main", 0), ("main", 1), ("n31", 0)):
        t = D.tournaments(key)[i]
        for a, b in K.irrelevant_games(t)[:3]:
            t2 = K.flip_game(t, a, b, t.rounds)
            v1, v2 = K.values(t, "fide2026"), K.values(t2, "fide2026")
            touched = {a, b} | {r for r in range(1, t.n + 1) if any(g.opponent in (a, b) and not g.bye for g in t.games[r - 1])}
            touched2 = touched | {r for r in range(1, t.n + 1) if any(g.opponent in touched and not g.bye for g in t.games[r - 1])}
            for r in range(1, t.n + 1):
                if r not in touched:
                    for k in ("BH", "BH-C1", "BH-C2", "BH-M1", "BH-M2", "SB", "PS", "PS-G", "WIN", "WON", "BWG", "BPG"):
                        assert v1[k][r - 1] == pytest.approx(v2[k][r - 1]), (key, i, a, b, r, k)
                if r not in touched2:                                          # der mittlere Buchholz liest die Buchholz-Werte der Gegner: zwei Schritte
                    assert v1["AOB"][r - 1] == pytest.approx(v2["AOB"][r - 1]), (key, i, a, b, r)
            for k in ("PS", "WIN", "WON", "ARO", "RTNG", "TPR"):             # eigene Partien und Startliste: nur a und b ändern sich
                for r in range(1, t.n + 1):
                    if r not in (a, b):
                        assert v1[k][r - 1] == pytest.approx(v2[k][r - 1])


def test_the_points_follow_the_games_for_every_stored_tournament_in_the_sample():
    for key, i in SAMPLE:
        t = D.tournaments(key)[i]
        board = sum(1 for gl in t.games for g in gl if not g.bye) // 2
        byes = sum(1 for gl in t.games for g in gl if g.bye)
        assert sum(t.score) == pytest.approx(board + byes)


def test_the_mini_instance_by_hand(mini):
    """Dieselben Zahlen wie in test_criteria, hier gegen das Orakel: ein Orakel, das an der Handrechnung scheitert, wäre falsch."""
    theirs = oracle_values(mini, "ignore")
    assert theirs["BH"] == [4.5, 4.5, 5.0, 5.5, 4.0, 3.5]
    assert theirs["SB"] == [3.5, 1.0, 3.0, 2.0, 1.0, 1.0]
    assert theirs["PS"] == [5.0, 2.0, 3.5, 3.5, 3.0, 1.0]
