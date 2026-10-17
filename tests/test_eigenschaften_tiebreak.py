"""Eigenschaftstests (metamorph) und eine Handrechnung für die Kriterien nach FIDE C.07 (ORACLE-PLAYBOOK §5.2).

Zufallsturniere (feste Seeds): Runden mit zufälliger Paarung, Freilos (Punkt 1) bei ungerader Zahl, Rücktritte ab Runde 3, Remis, zufällige Ergebnisse. Die
Kriterien hängen nur an den Berichten, nicht an der Paarungsregel; deshalb genügt der Zufallsgenerator (keine Engine, schnell).

Eigenschaften:
1. Umnummerieren der Spieler (Gegner, Startwertung, Rücktrittsrunde mit) ändert jedes Kriterium nur um die Namen (alle Behandlungen), ebenso den Direktvergleich und
   den Endstand mit mitgeführtem Los.
2. Die Reihenfolge der Partien in der Liste eines Spielers ändert nichts (die Runde steht in der Partie).
3. Zählsätze, die aus den Definitionen folgen: Summe aller Buchholz-Werte = Summe von (Punkte x Brettpartien); Summe aller Sonneborn-Berger-Werte = Summe von
   (Punkte x von den Gegnern gegen ihn geholte Punkte) (Behandlung "ignore"); PS liegt zwischen Endstand und Runden x Endstand; Cut-Varianten nie größer als
   BH; WON <= WIN, BWG <= BPG, BWG <= WON; ARO verschiebt sich mit den Startwertungen, alle anderen Kriterien nicht.
4. Punktgleiche bleiben Punktgleiche: Im Endstand stehen die Spieler nach Punkten absteigend, jede Punktgruppe liegt zusammenhängend, "Punkte" steht genau an
   den Gruppengrenzen; innerhalb der Gruppe trennt das erste Kriterium nach seinem Wert.
5. Der Direktvergleich der Gruppe hängt nur an den Partien innerhalb der Gruppe (Artikel 6): Umkehr von Partien zweier Nicht-Mitglieder ändert nichts.
6. Handrechnung (Docstring von `test_hand_calculation_...`) von BH, SB, PS, AOB, WIN, WON und der Behandlung von Freilos und Rücktritt in den drei Behandlungen aus
   den Definitionen der FIDE-Regeln C.07 (Webportal, Fassung 08/2024, über WebFetch eingesehen 2026-10-17: 7.1 WIN, 7.2 WON, 7.5 PS, 8.1 BH, 8.2 AOB, 9.1 SB,
   14 Modifikatoren, 16.3 bis 16.5 nicht gespielte Runden; ab 03/2026 der Deckel des Dummy-Gegners bei 0,5 x Rundenzahl laut README der Demo).

Je Eigenschaft 25 bis 40 Zufallsturniere; Laufzeit unter 10 s.
"""

import math
import random

import pytest

import tbk_constants as C
import tbk_criteria as K
from conftest import build
from tbk_tournament import Game, Tournament

CRITERIA = ("BH", "BH-C1", "BH-C2", "BH-M1", "BH-M2", "AOB", "SB", "PS", "PS-G", "WIN", "WON", "BWG", "BPG", "REP", "ARO", "TPR", "RTNG")
MODES = tuple(C.MODES)


def random_tournament(rng, n, rounds, p_withdraw=0.3, p_draw=0.25, seed=0):
    leave = [0] * n
    for i in range(n):
        if rng.random() < p_withdraw and rounds >= 4:
            leave[i] = rng.randint(3, rounds)               # Rücktritt vor dieser Runde (Runde >= 3), wie die Demo
    games = [[] for _ in range(n)]
    for rnd in range(1, rounds + 1):
        active = [i for i in range(n) if not leave[i] or leave[i] > rnd]
        rng.shuffle(active)
        if len(active) % 2:
            b = active.pop()
            games[b].append(Game(0, 1.0, "", True, rnd))
        for k in range(0, len(active), 2):
            w, bl = active[k], active[k + 1]
            u = rng.random()
            sw = 0.5 if u < p_draw else (1.0 if u < p_draw + (1 - p_draw) / 2 else 0.0)
            games[w].append(Game(bl + 1, sw, "w", False, rnd))
            games[bl].append(Game(w + 1, 1.0 - sw, "b", False, rnd))
    start = tuple(round(2000 + 300 * rng.random(), 3) for _ in range(n))
    return Tournament(n, rounds, start, start, tuple(tuple(g) for g in games), tuple(leave), seed)


def tournaments(seed, count=30, ns=(6, 7, 8, 9, 10, 12), rounds=(4, 5, 6)):
    rng = random.Random(seed)
    for k in range(count):
        yield random_tournament(rng, rng.choice(ns), rng.choice(rounds), seed=seed * 1000 + k)


def relabel(t, perm):
    """Spieler i (1-basiert) heißt danach perm[i-1] (1-basiert)."""
    games = [None] * t.n
    for i in range(1, t.n + 1):
        games[perm[i - 1] - 1] = tuple(g._replace(opponent=perm[g.opponent - 1] if g.opponent else 0) for g in t.games[i - 1])
    start, strength, leave = [None] * t.n, [None] * t.n, [None] * t.n
    for i in range(1, t.n + 1):
        start[perm[i - 1] - 1], strength[perm[i - 1] - 1], leave[perm[i - 1] - 1] = t.start[i - 1], t.strength[i - 1], t.leave[i - 1]
    return Tournament(t.n, t.rounds, tuple(strength), tuple(start), tuple(games), tuple(leave), t.seed)


# --- 1 Umnummerieren ----------------------------------------------------------------------------------------------------------------------------

def test_relabelling_the_players_only_renames_every_criterion_in_every_mode():
    rng = random.Random(11)
    for t in tournaments(1, 30):
        perm = list(range(1, t.n + 1))
        rng.shuffle(perm)
        t2 = relabel(t, perm)
        for mode in MODES:
            v1, v2 = K.values(t, mode), K.values(t2, mode)
            for key in CRITERIA:
                for i in range(t.n):
                    assert v2[key][perm[i] - 1] == pytest.approx(v1[key][i], abs=1e-9), (key, mode, i)


def test_relabelling_renames_the_direct_encounter_and_the_final_standing():
    rng = random.Random(12)
    cascades = (("DE", "BH", "PS"), ("BH-C1", "SB", "DE", "RTNG"), ("PS", "WIN", "DE", "RTNG"))
    for t in tournaments(2, 30):
        perm = list(range(1, t.n + 1))
        rng.shuffle(perm)
        t2 = relabel(t, perm)
        # das Los wandert mit den Spielern (sonst entscheidet es anders)
        lot = [rng.random() for _ in range(t.n)]
        lot2 = [None] * t.n
        for i in range(t.n):
            lot2[perm[i] - 1] = lot[i]
        groups = {}
        for i, s in enumerate(t.score, start=1):
            groups.setdefault(s, []).append(i)
        for group in groups.values():
            b1 = K.direct_encounter(group, t.games)
            b2 = K.direct_encounter([perm[i - 1] for i in group], t2.games)
            assert [sorted(perm[i - 1] for i in b) for b in b1] == [sorted(b) for b in b2]
        for cascade in cascades:
            s1 = K.standing(t, cascade, "fide2024", lot=lot)
            s2 = K.standing(t2, cascade, "fide2024", lot=lot2)
            assert [(perm[r - 1], why) for r, why in s1] == s2, cascade


# --- 2 Reihenfolge der Partien -----------------------------------------------------------------------------------------------------------------

def test_the_order_of_the_games_in_a_players_list_does_not_matter():
    rng = random.Random(21)
    for t in tournaments(3, 25):
        games = []
        for gl in t.games:
            gl = list(gl)
            rng.shuffle(gl)
            games.append(tuple(gl))
        t2 = Tournament(t.n, t.rounds, t.strength, t.start, tuple(games), t.leave, t.seed)
        for mode in MODES:
            v1, v2 = K.values(t, mode), K.values(t2, mode)
            for key in CRITERIA:
                assert v2[key] == pytest.approx(v1[key], abs=1e-9), (key, mode)


# --- 3 Zählsätze aus den Definitionen -----------------------------------------------------------------------------------------------------------

def test_sums_of_buchholz_and_sonneborn_berger_follow_from_their_definitions():
    for t in tournaments(4, 40):
        v = K.values(t, "ignore")
        score = t.score
        board = [[g for g in gl if not g.bye] for gl in t.games]
        # jede Brettpartie von i liefert ein Summand score(Gegner) zu BH(i): Summe = Summe über j von score(j) x Zahl der Brettpartien von j
        assert sum(v["BH"]) == pytest.approx(sum(score[j] * len(board[j]) for j in range(t.n)))
        # SB(i) = Summe score(Gegner) x Punkte von i gegen ihn; die Punkte der Gegner gegen j sind (Partien von j) - (Punkte von j am Brett)
        assert sum(v["SB"]) == pytest.approx(sum(score[j] * (len(board[j]) - sum(g.score for g in board[j])) for j in range(t.n)))


def test_ranges_and_orderings_of_the_criteria():
    for t in tournaments(5, 40):
        for mode in MODES:
            v = K.values(t, mode)
            for i in range(t.n):
                s = t.score[i]
                assert s - 1e-9 <= v["PS"][i] <= t.rounds * s + 1e-9
                assert v["BH-C1"][i] <= v["BH"][i] + 1e-9 and v["BH-C2"][i] <= v["BH-C1"][i] + 1e-9
                assert v["BH-M1"][i] <= v["BH-C1"][i] + 1e-9 and v["BH-M2"][i] <= v["BH-M1"][i] + 1e-9
                assert v["WON"][i] <= v["WIN"][i] and v["BWG"][i] <= v["BPG"][i] and v["BWG"][i] <= v["WON"][i]
                assert v["WIN"][i] <= t.rounds and v["REP"][i] <= t.rounds


def test_a_common_shift_of_the_start_ratings_moves_only_aro_and_tpr_by_the_shift():
    for t in tournaments(6, 25):
        shifted = Tournament(t.n, t.rounds, t.strength, tuple(r + 123.5 for r in t.start), t.games, t.leave, t.seed)
        v1, v2 = K.values(t, "fide2024"), K.values(shifted, "fide2024")
        for key in CRITERIA:
            if key in ("ARO", "TPR", "RTNG"):
                continue
            assert v2[key] == pytest.approx(v1[key]), key
        for i in range(t.n):
            if any(not g.bye for g in t.games[i]):
                assert v2["ARO"][i] == pytest.approx(v1["ARO"][i] + 123.5)
                assert v2["TPR"][i] == pytest.approx(v1["TPR"][i] + 123.5)


# --- 4 Punktgleiche bleiben Punktgleiche --------------------------------------------------------------------------------------------------------

def test_a_criterion_only_orders_within_the_score_groups_of_the_standing():
    rng = random.Random(41)
    keys = [k for k in K.KEYS if k != "DE"]
    for t in tournaments(7, 40):
        cascade = tuple(rng.sample(keys, 2))
        for mode in MODES:
            vals = K.values(t, mode)
            st = K.standing(t, cascade, mode, vals=vals)
            assert sorted(r for r, _w in st) == list(range(1, t.n + 1))
            scores = [t.score[r - 1] for r, _w in st]
            assert scores == sorted(scores, reverse=True)                              # Punkte vor allen Kriterien
            for k in range(1, len(st)):
                same = scores[k] == scores[k - 1]
                assert (st[k][1] == "Punkte") == (not same)                            # "Punkte" genau an den Gruppengrenzen
                if same:                                                               # innerhalb der Gruppe: erstes Kriterium absteigend (bis auf Rundung)
                    assert vals[cascade[0]][st[k - 1][0] - 1] >= vals[cascade[0]][st[k][0] - 1] - 1e-8
    # Randfall: Spieler 2 und 3 haben beide 1 Punkt und beide den Buchholz 2,0 (Gegner 1 und 4): das Los entscheidet, die beiden anderen stehen fest
    t = build(4, 2, [[(1, 2, 1.0), (3, 4, 1.0)], [(1, 3, 1.0), (2, 4, 1.0)]])
    st = K.standing(t, ("BH",), "ignore")
    assert [r for r, _w in st][0] == 1 and [r for r, _w in st][3] == 4 and {st[1][0], st[2][0]} == {2, 3}
    assert [w for _r, w in st] == ["", "Punkte", "LOS", "Punkte"]


# --- 5 Direktvergleich hängt nur an der Gruppe --------------------------------------------------------------------------------------------------

def test_the_direct_encounter_depends_only_on_the_games_inside_the_group():
    rng = random.Random(51)
    checked = 0
    for t in tournaments(8, 80, ns=(8, 10, 12), rounds=(5, 6)):
        groups = {}
        for i, s in enumerate(t.score, start=1):
            groups.setdefault(s, []).append(i)
        for group in groups.values():
            if len(group) < 2:
                continue
            members = set(group)
            outside = [(r, g.opponent, g.round_no) for r in range(1, t.n + 1) if r not in members for g in t.games[r - 1]
                       if not g.bye and g.opponent not in members and r < g.opponent]
            if not outside:
                continue
            t2 = t
            for a, b, rnd in rng.sample(outside, min(3, len(outside))):
                t2 = K.flip_game(t2, a, b, rnd)
            assert K.direct_encounter(group, t2.games) == K.direct_encounter(group, t.games)
            checked += 1
    assert checked >= 25


# --- 5b dieselben Eigenschaften an Turnieren der echten Engine (feste vorberechnete Mengen: Rücktritte, Freilose) ----------------------------------

def test_the_properties_also_hold_for_tournaments_of_the_fide_dutch_engine():
    import tbk_data as D
    rng = random.Random(55)
    sample = list(D.tournaments("main")[:8]) + list(D.tournaments("w30")[:8]) + list(D.tournaments("n31")[:8]) + list(D.tournaments("n16r5")[:6])
    for t in sample:
        perm = list(range(1, t.n + 1))
        rng.shuffle(perm)
        t2 = relabel(t, perm)
        for mode in MODES:
            v1, v2 = K.values(t, mode), K.values(t2, mode)
            for key in CRITERIA:
                for i in range(t.n):
                    assert v2[key][perm[i] - 1] == pytest.approx(v1[key][i], abs=1e-9), (key, mode, i)
        board = [[g for g in gl if not g.bye] for gl in t.games]
        assert sum(K.values(t, "ignore")["BH"]) == pytest.approx(sum(t.score[j] * len(board[j]) for j in range(t.n)))


# --- 6 Handrechnung -----------------------------------------------------------------------------------------------------------------------------

def hand_tournament():
    """Sechs Spieler, vier Runden; Spieler 4 erhält in Runde 4 das Freilos, Spieler 6 tritt vor Runde 4 zurück (leave = 4). Weiß steht zuerst.
    R1: 1-2 (1 gewinnt), 3-4 (Remis), 5-6 (5 gewinnt); R2: 1-3 (Remis), 2-5 (2 gewinnt), 4-6 (4 gewinnt);
    R3: 1-4 (1 gewinnt), 2-6 (Remis), 3-5 (3 gewinnt); R4: 1-5 (5 gewinnt), 2-3 (Remis), Freilos 4."""
    return build(6, 4, [[(1, 2, 1.0), (3, 4, 0.5), (5, 6, 1.0)], [(1, 3, 0.5), (2, 5, 1.0), (4, 6, 1.0)], [(1, 4, 1.0), (2, 6, 0.5), (3, 5, 1.0)],
                        [(1, 5, 0.0), (2, 3, 0.5), ("bye", 4, 1.0)]], leave=[0, 0, 0, 0, 0, 4], start=[2300.0, 2200.0, 2100.0, 2000.0, 1900.0, 1800.0])


def test_hand_calculation_of_buchholz_sonneborn_berger_progressive_and_the_treatment_of_bye_and_withdrawal():
    """Von Hand gerechnet aus den Definitionen (FIDE C.07, 08/2024: WIN 7.1, WON 7.2, PS 7.5, BH 8.1, AOB 8.2, SB 9.1, Cut 14.1, Artikel 16).

    Endstand (Summe der Berichte): S1 = 1 + 0,5 + 1 + 0 = 2,5; S2 = 0 + 1 + 0,5 + 0,5 = 2,0; S3 = 0,5 + 0,5 + 1 + 0,5 = 2,5; S4 = 0,5 + 1 + 0 + 1 (Freilos) = 2,5;
    S5 = 1 + 0 + 0 + 1 = 2,0; S6 = 0 + 0 + 0,5 (Runde 4 ohne Bericht) = 0,5. Kontrolle: 12 Punkte in 12 Partien-Punkten (3 + 3 + 3 + 2 Partien + 1 Freilos).
    Gegner am Brett: 1: 2, 3, 4, 5; 2: 1, 5, 6, 3; 3: 4, 1, 5, 2; 4: 3, 6, 1 (+ Freilos); 5: 6, 2, 3, 1; 6: 5, 4, 2 (+ Runde 4 ohne Bericht).

    Behandlung "ignore" (Freilos und Runden nach Rücktritt zählen nicht):
      BH(i) = Summe der Endstände der Brettgegner:
        BH1 = 2,0 + 2,5 + 2,5 + 2,0 = 9,0;  BH2 = 2,5 + 2,0 + 0,5 + 2,5 = 7,5;  BH3 = 2,5 + 2,5 + 2,0 + 2,0 = 9,0;
        BH4 = 2,5 + 0,5 + 2,5 = 5,5;  BH5 = 0,5 + 2,0 + 2,5 + 2,5 = 7,5;  BH6 = 2,0 + 2,5 + 2,0 = 6,5.
      SB(i) = Summe über die Brettpartien (Endstand des Gegners x eigene Punkte gegen ihn):
        SB1 = 1 x 2,0 + 0,5 x 2,5 + 1 x 2,5 + 0 x 2,0 = 5,75;  SB2 = 0 + 1 x 2,0 + 0,5 x 0,5 + 0,5 x 2,5 = 3,5;  SB3 = 0,5 x 2,5 + 0,5 x 2,5 + 1 x 2,0 + 0,5 x 2,0 = 5,5;
        SB4 = 0,5 x 2,5 + 1 x 0,5 + 0 x 2,5 = 1,75;  SB5 = 1 x 0,5 + 0 + 0 + 1 x 2,5 = 3,0;  SB6 = 0 + 0 + 0,5 x 2,0 = 1,0.
    Behandlung "fide2024" (Artikel 16):
      16.3: Runden nach dem Rücktritt zählen für die Gegner als Remis: Spieler 6 hat eine Runde ohne Bericht, sein Wert für die Gegner ist 0,5 + 0,5 = 1,0.
      16.4: Eigene nicht gespielte Runden (Freilos Spieler 4 Runde 4; Runde 4 von Spieler 6) zählen als Partie gegen einen Dummy mit dem eigenen Endstand
      (Spieler 4: 2,5; Spieler 6: 0,5); der Ausgang ist der vergebene Punkt (Freilos 1, Runde nach Rücktritt 0).
        BH1 = 2,0 + 2,5 + 2,5 + 2,0 = 9,0 (kein Gegner betroffen);  BH2 = 2,5 + 2,0 + 1,0 + 2,5 = 8,0;  BH3 = 9,0;  BH4 = 2,5 + 1,0 + 2,5 + 2,5 (Dummy) = 8,5;
        BH5 = 1,0 + 2,0 + 2,5 + 2,5 = 8,0;  BH6 = 2,0 + 2,5 + 2,0 + 0,5 (Dummy) = 7,0.
        SB2 = 0 + 2,0 + 0,5 x 1,0 + 1,25 = 3,75;  SB4 = 1,25 + 1 x 1,0 + 0 + 1 x 2,5 (Dummy x Freilos-Punkt) = 4,75;  SB5 = 1 x 1,0 + 0 + 0 + 2,5 = 3,5;
        SB1 = 5,75, SB3 = 5,5, SB6 = 1,0 unverändert.
        BH-C1 (14.1, bei freiwillig nicht gespielter Runde zuerst diese, 16.5): BH1-C1 = 9,0 - 2,0 = 7,0; BH2-C1 = 8,0 - 1,0 = 7,0; BH3-C1 = 9,0 - 2,0 = 7,0;
        BH4-C1 = 8,5 - 1,0 = 7,5; BH5-C1 = 8,0 - 1,0 = 7,0; BH6-C1 = 7,0 - 0,5 (die Runde nach dem Rücktritt, zugleich der kleinste Beitrag) = 6,5.
        AOB1 = (BH2 + BH3 + BH4 + BH5)/4 = (8,0 + 9,0 + 8,5 + 8,0)/4 = 8,375;  AOB3 = (BH4 + BH1 + BH5 + BH2)/4 = (8,5 + 9,0 + 8,0 + 8,0)/4 = 8,375;
        AOB4 = (BH3 + BH6 + BH1)/3 = (9,0 + 7,0 + 9,0)/3 = 8,3333.
    Behandlung "fide2026": der Dummy hat höchstens 0,5 x 4 = 2,0 Punkte (Spieler 4: 2,0 statt 2,5): BH4 = 2,5 + 1,0 + 2,5 + 2,0 = 8,0; SB4 = 1,25 + 1,0 + 0 + 2,0 = 4,25;
      Spieler 6 (0,5) bleibt unter dem Deckel.
    Fortschritt PS (Summe der Zwischenstände nach jeder Runde, Runde ohne Bericht: Stand bleibt):
        PS1 = 1 + 1,5 + 2,5 + 2,5 = 7,5;  PS2 = 0 + 1 + 1,5 + 2,0 = 4,5;  PS3 = 0,5 + 1 + 2 + 2,5 = 6,0;  PS4 = 0,5 + 1,5 + 1,5 + 2,5 = 6,0;
        PS5 = 1 + 1 + 1 + 2 = 5,0;  PS6 = 0 + 0 + 0,5 + 0,5 = 1,0.
    WIN (7.1, mit Freilos): 2, 1, 1, 2, 2, 0;  WON (7.2, nur am Brett): 2, 1, 1, 1, 2, 0.
    """
    t = hand_tournament()
    assert t.score == (2.5, 2.0, 2.5, 2.5, 2.0, 0.5)
    ign, f24, f26 = K.values(t, "ignore"), K.values(t, "fide2024"), K.values(t, "fide2026")
    assert ign["BH"] == pytest.approx([9.0, 7.5, 9.0, 5.5, 7.5, 6.5])
    assert ign["SB"] == pytest.approx([5.75, 3.5, 5.5, 1.75, 3.0, 1.0])
    assert f24["BH"] == pytest.approx([9.0, 8.0, 9.0, 8.5, 8.0, 7.0])
    assert f24["SB"] == pytest.approx([5.75, 3.75, 5.5, 4.75, 3.5, 1.0])
    assert f24["BH-C1"] == pytest.approx([7.0, 7.0, 7.0, 7.5, 7.0, 6.5])
    assert f24["AOB"][0] == pytest.approx(8.375) and f24["AOB"][2] == pytest.approx(8.375) and f24["AOB"][3] == pytest.approx(25 / 3)
    assert f26["BH"][3] == pytest.approx(8.0) and f26["SB"][3] == pytest.approx(4.25) and f26["BH"][5] == pytest.approx(7.0)
    for v in (ign, f24, f26):
        assert v["PS"] == pytest.approx([7.5, 4.5, 6.0, 6.0, 5.0, 1.0])
        assert v["WIN"] == [2, 1, 1, 2, 2, 0] and v["WON"] == [2, 1, 1, 1, 2, 0]
