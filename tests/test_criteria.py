"""Einheitentests der Kriterien an den von Hand gebauten Mini-Turnieren (tests/conftest.py); jede Zahl ist von Hand nachgerechnet."""

import pytest

import tbk_criteria as K
from conftest import build

# --- Sechs Spieler, ohne Freilos: Buchholz-Familie, Sonneborn-Berger, Fortschritt, Siege -----------------------------------------------------

def test_scores_of_the_mini_tournament(mini):
    assert mini.score == (2.5, 1.0, 2.0, 1.5, 1.0, 1.0)
    assert sum(mini.score) == 9.0                                  # neun Partien, jede vergibt einen Punkt


def test_buchholz_and_its_cuts_by_hand(mini):
    v = K.values(mini)
    assert v["BH"] == [4.5, 4.5, 5.0, 5.5, 4.0, 3.5]
    assert v["BH-C1"] == [3.5, 3.5, 4.0, 4.5, 3.0, 2.5]
    assert v["BH-C2"] == [2.0, 2.5, 2.5, 2.5, 2.0, 1.5]
    assert v["BH-M1"] == [1.5, 1.0, 1.5, 2.0, 1.0, 1.0]
    assert v["BH-M2"] == [0.0] * 6                                 # drei Gegner: nach zwei Streichungen unten und zwei oben bleibt nichts


def test_sonneborn_berger_progressive_and_counts_by_hand(mini):
    v = K.values(mini)
    assert v["SB"] == [3.5, 1.0, 3.0, 2.0, 1.0, 1.0]
    assert v["PS"] == [5.0, 2.0, 3.5, 3.5, 3.0, 1.0]
    assert v["WIN"] == [2, 1, 1, 1, 1, 1] and v["WON"] == v["WIN"]
    assert v["BWG"] == [0, 0, 0, 0, 0, 1]                           # nur Spieler 6 gewann mit Schwarz (Runde 3 gegen 2)
    assert v["BPG"] == [0, 1, 1, 2, 2, 3]
    assert v["REP"] == [3] * 6


def test_average_of_opponents_buchholz_and_progressive_of_opponents(mini):
    v = K.values(mini)
    assert v["AOB"][0] == pytest.approx((4.5 + 5.0 + 5.5) / 3)     # Gegner von 1: 2, 3, 4
    assert v["PS-G"][0] == 2.0 + 3.5 + 3.5


def test_rating_criteria(mini):
    v = K.values(mini)
    assert v["RTNG"] == [6.0, 5.0, 4.0, 3.0, 2.0, 1.0]
    assert v["ARO"][0] == pytest.approx((5.0 + 4.0 + 3.0) / 3)
    assert v["TPR"][0] > v["ARO"][0]                                # 2,5 aus 3: über 50 %
    assert v["TPR"][5] < v["ARO"][5]                                # 1 aus 3: unter 50 %


def test_the_three_cycle_is_not_resolved_by_the_direct_encounter(mini):
    assert K.direct_encounter([2, 5, 6], mini.games) == [[2, 5, 6]]
    assert K.direct_encounter([1, 3], mini.games) == [[1, 3]]       # Remis in Runde 2: kein Unterschied


# --- Standings, reasons and the cascade ---------------------------------------------------------------------------------------------------

def test_standing_with_a_cascade_and_its_reasons(mini):
    st = K.standing(mini, ("DE", "BH", "PS"))
    assert st == [(1, ""), (3, "Punkte"), (4, "Punkte"), (2, "Punkte"), (5, "BH"), (6, "BH")]
    st = K.standing(mini, ("PS",))
    assert st == [(1, ""), (3, "Punkte"), (4, "Punkte"), (5, "Punkte"), (2, "PS"), (6, "PS")]


def test_an_unresolved_tie_goes_to_the_lot_and_is_stable(mini):
    st = K.standing(mini, ("SB",))
    assert [r for r, _w in st[:3]] == [1, 3, 4]
    assert [w for _r, w in st[4:]] == ["LOS", "LOS"]
    assert st == K.standing(mini, ("SB",))                         # dieselbe Los-Reihenfolge
    assert sorted(r for r, _w in st[3:]) == [2, 5, 6]


def test_lots_depend_on_the_seed_only():
    a, b = build(6, 3, [[(1, 2, 1.0)]], seed=1), build(6, 3, [[(1, 2, 1.0)]], seed=1)
    c = build(6, 3, [[(1, 2, 1.0)]], seed=2)
    assert K.lots(a) == K.lots(b) and K.lots(a) != K.lots(c)


def test_a_repeated_criterion_does_not_change_the_result(mini):
    assert K.standing(mini, ("BH", "BH", "PS")) == K.standing(mini, ("BH", "PS"))


# --- Freilos: Behandlung nicht gespielter Runden (Artikel 16) -------------------------------------------------------------------------------

def test_byes_are_ignored_in_the_ignore_mode(byes):
    assert byes.score == (2.0, 0.0, 1.5, 2.5, 3.0)
    v = K.values(byes, "ignore")
    assert v["BH"] == [4.5, 7.5, 4.5, 1.5, 2.0]
    assert v["SB"][4] == 2.0                                        # Spieler 5: 0,0 · 1 + 2,0 · 1


def test_article_16_adds_a_dummy_with_the_own_score(byes):
    v24 = K.values(byes, "fide2024")
    assert v24["BH"] == [4.5, 7.5, 6.0, 4.0, 5.0]                   # Freilos: Dummy mit der eigenen Endpunktzahl (3: 1,5; 4: 2,5; 5: 3,0)
    assert v24["SB"][4] == 5.0                                      # 2,0 + 3,0 · 1,0


def test_the_2026_text_caps_the_dummy_at_half_the_number_of_rounds(byes):
    v26 = K.values(byes, "fide2026")                                # Deckel 0,5 · 3 Runden = 1,5
    assert v26["BH"] == [4.5, 7.5, 6.0, 3.0, 3.5]
    assert v26["SB"][4] == 3.5
    assert K.values(byes, "fide2026")["BH"][2] == K.values(byes, "fide2024")["BH"][2]      # 1,5 liegt nicht über dem Deckel


def test_win_counts_a_bye_but_won_does_not(byes):
    v = K.values(byes)
    assert v["WIN"] == [2, 0, 1, 2, 3]
    assert v["WON"] == [2, 0, 0, 1, 2]
    assert v["REP"] == [3] * 5                                      # ein Freilos des Paarungsprogramms zählt als gewollte Runde


def test_progressive_scores_count_a_bye_as_a_point(byes):
    assert K.values(byes)["PS"] == [1.0 + 2.0 + 2.0, 0.0, 0.5 + 0.5 + 1.5, 0.5 + 1.5 + 2.5, 1.0 + 2.0 + 3.0]


# --- Rücktritt -------------------------------------------------------------------------------------------------------------------------------

def test_a_withdrawn_players_missing_round_counts_as_a_draw_for_the_opponents(withdrawn):
    assert withdrawn.score == (1.5, 1.5, 2.5, 0.5)
    v_ignore, v24, v26 = K.values(withdrawn, "ignore"), K.values(withdrawn, "fide2024"), K.values(withdrawn, "fide2026")
    assert v_ignore["BH"][2] == 0.5 + 1.5                           # Spieler 3: Gegner 4 (0,5) und 1 (1,5)
    assert v24["BH"][2] == 1.0 + 1.5 + 2.5                          # Gegner 4 zählt 0,5 + 0,5; das Freilos: Dummy mit 2,5
    assert v26["BH"][2] == 1.0 + 1.5 + 1.5                          # Dummy gedeckelt bei 1,5
    assert v24["BH"][3] == 2.5 + 1.5 + 0.5                          # Spieler 4: die Runde nach dem Rücktritt bringt den Dummy mit 0,5
    assert v_ignore["BH"][3] == 2.5 + 1.5
    assert v24["REP"][3] == 2 and v_ignore["REP"][3] == 2


def test_the_cut_takes_the_voluntary_unplayed_round_first():
    contrib = [(0.5, False), (2.5, True), (1.5, False)]
    assert K._cut(contrib, 1, 0, fide=True) == 2.0                  # die freiwillig nicht gespielte Runde (2,5) wird gestrichen, nicht die 0,5
    assert K._cut(contrib, 1, 0, fide=False) == 4.0
    assert K._cut(contrib, 2, 0, fide=True) == 1.5                  # zweite Streichung: der Kleinste der übrigen (0,5)
    assert K._cut(contrib, 1, 1, fide=True) == 0.5                  # unten die VUR, oben der größte der übrigen (1,5)


def test_cut_one_of_a_withdrawn_player_cuts_the_missing_round(withdrawn):
    v = K.values(withdrawn, "fide2024")
    assert v["BH-C1"][3] == 4.0                                     # Beiträge 2,5, 1,5, 0,5 (VUR): die VUR wird gestrichen


# --- Direktvergleich (Artikel 6) -------------------------------------------------------------------------------------------------------------

def test_direct_encounter_orders_a_group_that_has_met_completely():
    t = build(3, 3, [[(1, 2, 1.0)], [(2, 3, 1.0)], [(1, 3, 1.0)]])
    assert K.direct_encounter([1, 2, 3], t.games) == [[1], [2], [3]]


def test_direct_encounter_does_not_use_games_against_players_outside_the_group():
    t = build(4, 1, [[(1, 4, 1.0), (2, 3, 0.5)]])
    assert K.direct_encounter([1, 2, 3], t.games) == [[1, 2, 3]]    # 1 hat kein Gruppenmitglied gespielt


def test_a_partial_encounter_ranks_only_a_player_who_is_alone_at_the_top_whatever_the_missing_games():
    # 1 hat 2 geschlagen; 3 hat niemanden gespielt: 3 könnte beide noch schlagen -> keine Entscheidung
    t = build(3, 1, [[(1, 2, 1.0)]])
    assert K.direct_encounter([1, 2, 3], t.games) == [[1, 2, 3]]
    # Zwei Gruppenmitglieder: 1 schlägt 2, das ist die ganze Gruppe -> getrennt
    assert K.direct_encounter([1, 2], t.games) == [[1], [2]]
    # Vier Spieler: 1 schlägt 2 und 3, hat aber 4 nicht gespielt; 2 könnte 3 und 4 noch schlagen und mit 2 Punkten gleichziehen: keine Entscheidung
    t = build(4, 2, [[(1, 2, 1.0)], [(1, 3, 1.0)]])
    assert K.direct_encounter([1, 2, 3, 4], t.games) == [[1, 2, 3, 4]]
    # hat 1 alle drei geschlagen, steht 1 vorn; der Rest hat einander nicht gespielt und bleibt beisammen
    t = build(4, 3, [[(1, 2, 1.0)], [(1, 3, 1.0)], [(1, 4, 1.0)]])
    assert K.direct_encounter([1, 2, 3, 4], t.games) == [[1], [2, 3, 4]]


def test_a_repeated_meeting_counts_as_the_mean_of_the_games():
    t = build(2, 2, [[(1, 2, 1.0)], [(2, 1, 0.5)]])
    assert K.direct_encounter([1, 2], t.games) == [[1], [2]]         # 1: Mittel 0,75, 2: Mittel 0,25


# --- Umkehr einer Partie ---------------------------------------------------------------------------------------------------------------------

def test_flipping_a_game_changes_only_the_two_players_and_keeps_the_point_sum(mini):
    t2 = K.flip_game(mini, 2, 6, 3)                                 # in Runde 3 gewann 6; Umkehr: 2 gewinnt
    assert t2.score == (2.5, 2.0, 2.0, 1.5, 1.0, 0.0)
    assert sum(t2.score) == sum(mini.score)
    for r in (1, 3, 4, 5):
        assert t2.games[r - 1] == mini.games[r - 1]


def test_flipping_a_draw_gives_the_first_player_the_win(mini):
    t2 = K.flip_game(mini, 3, 1, 2)                                 # Runde 2: 1 gegen 3 war Remis; Spieler 3 gewinnt, 1 verliert
    assert t2.score[2] == mini.score[2] + 0.5 and t2.score[0] == mini.score[0] - 0.5


def test_flipping_a_game_that_does_not_exist_is_an_error(mini):
    with pytest.raises(ValueError):
        K.flip_game(mini, 1, 5, 1)


def test_irrelevant_games_need_both_players_well_behind_the_leader():
    # Spitze 3,0: erlaubt sind Beteiligte mit höchstens 1,5
    results = [[(1, 2, 1.0), (3, 4, 1.0), (5, 6, 1.0)], [(1, 3, 1.0), (2, 4, 0.5), (5, 6, 0.5)], [(1, 5, 1.0), (2, 3, 0.5), (4, 6, 0.0)]]
    t = build(6, 3, results)
    assert max(t.score) == 3.0
    assert t.score == (3.0, 1.0, 1.5, 0.5, 1.5, 1.5)
    assert K.irrelevant_games(t) == [(2, 3), (4, 6)]                # 1 gegen 5 nicht: 1 liegt an der Spitze
    assert K.irrelevant_games(t, margin=1.51) == []                 # 3 und 6 liegen nur 1,5 hinter der Spitze


def test_winner_of_matches_the_first_place_of_the_standing(mini):
    vals, lot = K.values(mini), K.lots(mini)
    for cascade in (("BH",), ("PS", "BH"), ("DE", "SB", "BH-C1")):
        assert K.winner_of(mini, cascade, vals, lot) == K.standing(mini, cascade)[0][0]


def test_unknown_mode_is_rejected(mini):
    with pytest.raises(ValueError):
        K.values(mini, "fide1999")
