"""Das Turnier: Determinismus, Struktur (Partien spiegeln einander, Punktesumme), Freilose und Rücktritte, Eigenschaften der echten Engine."""

import pytest

import tbk_tournament as TT
from tbk_tournament import play_tournament


@pytest.fixture(scope="module")
def open32():
    return play_tournament(32, 7, 0.2, 0.4, 0.0, 11)


@pytest.fixture(scope="module")
def odd_withdraw():
    return play_tournament(31, 7, 0.2, 0.4, 0.3, 12)


def test_the_same_inputs_give_the_same_tournament():
    assert play_tournament(16, 5, 0.2, 0.4, 0.0, 3) == play_tournament(16, 5, 0.2, 0.4, 0.0, 3)
    assert play_tournament(16, 5, 0.2, 0.4, 0.0, 3) != play_tournament(16, 5, 0.2, 0.4, 0.0, 4)


def test_every_player_plays_every_round_in_a_complete_even_tournament(open32):
    for gl in open32.games:
        assert [g.round_no for g in gl] == list(range(1, 8))
        assert not any(g.bye for g in gl)


def test_games_mirror_each_other(open32):
    for r in range(1, 33):
        for g in open32.games[r - 1]:
            mirror = [h for h in open32.games[g.opponent - 1] if h.round_no == g.round_no]
            assert len(mirror) == 1 and mirror[0].opponent == r
            assert mirror[0].score == pytest.approx(1.0 - g.score)
            assert {mirror[0].colour, g.colour} == {"w", "b"}


def test_point_sum_equals_games_plus_byes(odd_withdraw):
    t = odd_withdraw
    board_games = sum(1 for gl in t.games for g in gl if not g.bye) // 2
    byes = sum(1 for gl in t.games for g in gl if g.bye)
    assert sum(t.score) == pytest.approx(board_games + byes)


def test_nobody_meets_twice(open32, odd_withdraw):
    for t in (open32, odd_withdraw):
        for gl in t.games:
            opp = [g.opponent for g in gl if not g.bye]
            assert len(opp) == len(set(opp))


def test_an_odd_field_gives_one_bye_per_round_and_nobody_gets_two():
    t = play_tournament(31, 7, 0.2, 0.4, 0.0, 5)
    holders = [r for r in range(1, 32) if any(g.bye for g in t.games[r - 1])]
    assert len(holders) == 7
    assert all(sum(1 for g in t.games[r - 1] if g.bye) == 1 for r in holders)


def test_withdrawn_players_have_no_games_from_their_round_on(odd_withdraw):
    t = odd_withdraw
    leavers = [r for r in range(1, 32) if t.leave[r - 1]]
    assert leavers
    for r in leavers:
        assert all(g.round_no < t.leave[r - 1] for g in t.games[r - 1])
        assert TT.missing_rounds(t, r) == t.rounds - (t.leave[r - 1] - 1)
        assert 3 <= t.leave[r - 1] <= t.rounds - 1
    for r in range(1, 32):
        if not t.leave[r - 1]:
            assert TT.played_rounds(t, r) == t.rounds


def test_without_withdrawals_nobody_leaves(open32):
    assert set(open32.leave) == {0}


def test_start_ratings_are_ordered_and_strengths_are_rounded(open32):
    assert list(open32.start) == sorted(open32.start, reverse=True)
    assert all(round(x, 6) == x for x in open32.strength + open32.start)


def test_the_strengths_are_the_generators_equidistant_values_in_some_order(open32):
    import numpy as np
    import turnier_generator as T
    assert sorted(open32.strength) == pytest.approx(sorted(T.make_strengths(32, 0.12)), abs=1e-6)
    assert np.std(open32.strength) > 0


def test_invalid_input_is_rejected():
    with pytest.raises(ValueError):
        play_tournament(2, 3, 0.2, 0.4, 0.0, 1)
    with pytest.raises(ValueError):
        play_tournament(8, 0, 0.2, 0.4, 0.0, 1)


def test_a_draw_free_tournament_has_only_decisive_games():
    t = play_tournament(16, 5, 0.0, 0.4, 0.0, 7)
    assert all(g.score in (0.0, 1.0) for gl in t.games for g in gl)
    t = play_tournament(16, 5, 0.5, 0.4, 0.0, 7)
    assert any(g.score == 0.5 for gl in t.games for g in gl)


def test_the_smallest_field_is_four_players_and_the_last_start_number_can_withdraw():
    with pytest.raises(ValueError):
        play_tournament(3, 2, 0.2, 0.4, 0.0, 1)
    assert play_tournament(4, 1, 0.2, 0.4, 0.0, 1).n == 4
    ts = [play_tournament(8, 7, 0.2, 0.4, 0.9, s) for s in range(12)]
    assert any(t.leave[-1] for t in ts) and any(t.leave[0] for t in ts)          # beide Enden der Startrangliste können zurücktreten
    for t in ts:
        for r in (1, t.n):                                                         # und fehlen danach in den Berichten
            if t.leave[r - 1]:
                assert all(g.round_no < t.leave[r - 1] for g in t.games[r - 1])


def test_a_tournament_that_cannot_be_paired_to_the_end_stops_early_and_stays_consistent():
    short = [play_tournament(8, 9, 0.2, 0.4, 0.0, s) for s in range(6)]
    assert all(1 <= t.rounds <= 7 for t in short)                   # acht Spieler: höchstens sieben Runden ohne Wiederholung
    for t in short:
        assert all(g.round_no <= t.rounds for gl in t.games for g in gl)
        board = sum(1 for gl in t.games for g in gl if not g.bye) // 2
        assert sum(t.score) == pytest.approx(board + sum(1 for gl in t.games for g in gl if g.bye))
