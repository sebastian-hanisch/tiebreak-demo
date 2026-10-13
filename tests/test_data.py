"""Die vorberechneten Turniere: Aufbau der Datei, Kodierung, Fingerabdruck der Engine und Seed-für-Seed-Vergleich einer frischen Stichprobe."""

import pytest

import tbk_constants as C
import tbk_data as D
from tbk_tournament import play_tournament


def test_the_file_has_every_set_with_the_declared_count_and_parameters():
    raw = D.load_raw()
    assert raw["format"] == D.FORMAT and set(raw["sets"]) == set(C.SETS)
    for key, (n, rounds, draw, noise, withdraw, count, seed0) in C.SETS.items():
        s = raw["sets"][key]
        assert (s["n"], s["rounds"], s["draw"], s["noise"], s["withdraw"]) == (n, rounds, draw, noise, withdraw)
        assert len(s["tournaments"]) == count
        assert [x["seed"] for x in s["tournaments"]] == list(range(seed0, seed0 + count))


def test_the_file_was_made_with_the_engine_that_is_in_the_repo():
    assert D.load_raw()["engine"] == D.engine_fingerprint()


def test_encode_and_decode_are_inverse_on_the_stored_tournaments():
    for key in ("n16r5", "n31"):
        for t in D.tournaments(key)[:3]:
            n, rounds = t.n, t.rounds
            assert D.decode(D.encode(t), n, rounds) == t


def test_a_fresh_sample_equals_the_stored_tournaments_seed_for_seed():
    cases = (("n16r5", 0), ("n16r5", 5), ("n31", 0), ("w30", 0), ("draw40", 0), ("main", 0))
    for key, idx in cases:
        n, rounds, draw, noise, withdraw, _count, seed0 = C.SETS[key]
        assert play_tournament(n, rounds, draw, noise, withdraw, seed0 + idx) == D.tournaments(key)[idx], (key, idx)


def test_all_stored_tournaments_are_consistent():
    for key in C.SETS:
        for t in D.tournaments(key):
            board = sum(1 for gl in t.games for g in gl if not g.bye) // 2
            byes = sum(1 for gl in t.games for g in gl if g.bye)
            assert sum(t.score) == pytest.approx(board + byes)


def test_the_withdrawal_sets_contain_leavers_and_the_others_none():
    assert any(any(t.leave) for t in D.tournaments("w30"))
    assert not any(any(t.leave) for t in D.tournaments("main"))


def test_the_file_is_small():
    assert D.DATA_PATH.stat().st_size < 2_000_000


def test_all_stored_tournaments_were_played_to_the_end():
    for key, (n, rounds, *_rest) in C.SETS.items():
        assert all(t.n == n and t.rounds == rounds for t in D.tournaments(key)), key
