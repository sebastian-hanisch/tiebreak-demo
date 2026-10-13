"""Maße und Experimente: Grenzen, Zählungen gegen unabhängige Schleifen, Referenzen (Los, Stichkampf), Verdikte und Empfehlungen."""

import math
from collections import defaultdict

import pytest

import tbk_constants as C
import tbk_criteria as K
import tbk_data as D
import tbk_evaluation as ev
import tbk_verdicts as vd
from tbk_scenario import Settings


@pytest.fixture(scope="module")
def sample():
    return D.tournaments("main")[:40]


@pytest.fixture(scope="module")
def metrics(sample):
    return ev.measure(sample, ev.single_specs(), "fide2026", flips=True)


def _top_tied(t):
    return sum(1 for s in t.score if s == max(t.score)) >= 2


def test_kendall_tau_of_identical_and_reversed_orders():
    strength = [0.5, 0.1, -0.2, -0.9]
    assert ev.kendall_tau([1, 2, 3, 4], strength) == 1.0
    assert ev.kendall_tau([4, 3, 2, 1], strength) == -1.0
    assert ev.kendall_tau([1, 3, 2, 4], strength) == pytest.approx((5 - 1) / 6)


def test_the_number_of_tied_pairs_is_the_same_for_every_specification(sample, metrics):
    expected = 0
    for t in sample:
        groups = defaultdict(int)
        for s in t.score:
            groups[s] += 1
        expected += sum(g * (g - 1) // 2 for g in groups.values())
    assert {m.pairs for m in metrics.values()} == {expected}
    assert {m.tournaments for m in metrics.values()} == {len(sample)}


def test_the_lot_separates_nothing_and_the_playoff_everything(metrics):
    assert metrics["LOS"].resolved == 0 and math.isnan(metrics["LOS"].hit_rate)
    assert metrics["STICH"].resolution == 1.0
    assert 0.5 < metrics["STICH"].hit_rate < 0.9
    assert metrics["STICH"].expectation == pytest.approx(metrics["STICH"].hit_rate)


def test_rates_stay_in_range(metrics):
    for k, m in metrics.items():
        assert 0.0 <= m.resolution <= 1.0, k
        if m.resolved:
            assert 0.0 <= m.hit_rate <= 1.0 and 0.0 <= m.expectation <= 1.0, k
        assert 0.0 <= m.winner_rate <= 1.0 and 0.0 <= m.podium_rate <= 1.0 and -1.0 <= m.tau <= 1.0, k


def test_criteria_that_read_only_the_own_games_cannot_be_flipped(metrics):
    for k in ("PS", "WIN", "WON", "BWG", "BPG", "ARO", "TPR", "RTNG", "DE", "REP"):
        assert metrics[k].flip_games > 0 and metrics[k].flip_rate_g == 0.0 and metrics[k].flip_rate_t == 0.0, k


def test_opponent_dependent_criteria_can_be_flipped(metrics):
    assert any(metrics[k].flip_rate_t > 0 for k in ("BH", "BH-C1", "SB", "AOB", "PS-G"))


def test_the_number_of_flip_cases_equals_the_irrelevant_games_of_the_tied_tournaments(sample, metrics):
    expected = sum(len(K.irrelevant_games(t)) for t in sample if _top_tied(t))
    assert metrics["BH"].flip_games == expected
    assert metrics["BH"].top_tie == sum(1 for t in sample if _top_tied(t))


def test_a_cascade_resolves_at_least_as_many_pairs_as_its_first_criterion(sample):
    res = ev.measure(sample, {"a": ("WIN",), "b": ("WIN", "BH")}, "fide2026", flips=False)
    assert res["b"].resolution >= res["a"].resolution
    assert res["b"].resolution > 0.9


def test_the_default_tournament_is_typical_and_not_flippable():
    a = ev.analyse(Settings())
    assert len(a.top_group) >= 2 and a.winner == a.standing[0][0]
    assert all(w == a.winner for _x, _y, w in a.flips)


def test_the_flippable_preset_flips():
    a = ev.analyse(Settings(seed=C.PRESETS["Kippbares Turnier"]["seed"]))
    assert any(w != a.winner for _x, _y, w in a.flips)


def test_analyse_is_deterministic():
    assert repr(ev.analyse(Settings(seed=5))) == repr(ev.analyse(Settings(seed=5)))      # repr: NaN-Felder vergleichen sich sonst nie gleich


def test_the_verdict_levels_and_texts():
    a = ev.analyse(Settings())
    level, text = vd.verdict_analysis(a)
    assert level in ("info", "success", "warning") and str(a.winner) in text
    lone = next((b for b in (ev.analyse(Settings(seed=sd)) for sd in range(60)) if len(b.top_group) == 1), None)
    assert lone is not None
    assert "ohne Tie-Breaker entschieden" in vd.verdict_analysis(lone)[1]


def test_the_recommendation_table_covers_every_purpose(metrics):
    withdraw, bye = ev.exp_withdraw(), ev.exp_bye()
    noise, size = ev.exp_setting(ev.NOISE_SETS), ev.exp_setting(ev.SIZE_SETS)
    rows = vd.recommendations(metrics, withdraw, bye, noise, size)
    assert len(rows) == 7 and all(len(r) == 4 and all(isinstance(x, str) and x for x in r) for r in rows)
    assert rows[5][1].startswith("Stichkampf")


def test_experiments_are_deterministic_and_complete():
    assert ev.exp_bye() == ev.exp_bye()
    rows = ev.exp_withdraw()
    assert len(rows) == len(ev.WITHDRAW_SETS) * len(C.MODES) * len(ev.WITHDRAW_KEYS)
    assert len(ev.exp_setting(ev.SIZE_SETS)) == len(ev.SIZE_SETS) * (len(ev.SETTING_KEYS) + 2)


def test_number_formatting_uses_decimal_comma_and_a_real_minus():
    assert ev.de(3.14159, 2) == "3,14" and ev.pct(0.594) == "59" and ev.pct(0.5946, 1) == "59,5"
    assert ev.signed(-12.6) == "−13" and ev.signed(8.4) == "+8" and ev.signed(-0.2) == "±0" and ev.signed(0.4) == "±0"
    assert ev.signed(1.2) == "+1" and ev.signed(-1.2) == "−1" and ev.signed(0.6) == "+1"


def test_the_cascade_verdict_names_best_and_safest_separately_or_together():
    from types import SimpleNamespace as NS
    apart = {"a": NS(hit_rate=0.6, flip_rate_t=0.3), "b": NS(hit_rate=0.5, flip_rate_t=0.1)}
    text = vd.verdict_cascades(apart)[1]
    assert "höchsten Treffer ist **a** (60 %)" in text and "wenigsten kippbare **b** (10 % der Turniere)" in text and "am stärksten kippbare ist **a** (30 %)" in text
    together = {"a": NS(hit_rate=0.6, flip_rate_t=0.0), "b": NS(hit_rate=0.5, flip_rate_t=0.2)}
    text = vd.verdict_cascades(together)[1]
    assert "zugleich die am wenigsten kippbare: **a**" in text and "am stärksten kippbare ist **b** (20 %)" in text


def test_the_best_player_is_found_whatever_the_start_number():
    from conftest import build
    a = build(4, 2, [[(1, 2, 0.0), (3, 4, 0.0)], [(4, 2, 1.0), (3, 1, 0.5)]], strength=[0.1, 0.2, 0.0, 0.9])      # Spieler 4 ist der Stärkste und gewinnt
    b = build(4, 2, [[(1, 2, 1.0), (3, 4, 0.5)], [(1, 3, 1.0), (2, 4, 0.5)]], strength=[0.9, 0.2, 0.0, 0.1])      # Spieler 1 ist der Stärkste und gewinnt
    assert a.score == (0.5, 1.0, 0.5, 2.0) and b.score == (2.0, 0.5, 0.5, 1.0)
    for t in (a, b):
        m = ev.measure([t], {"c": ("RTNG",)}, "ignore", flips=False)["c"]
        assert m.winner_rate == 1.0 and m.podium_rate == 1.0                      # Sieger und Podium enthalten die höchste und die niedrigste Startnummer


def test_analyse_finds_the_top_group_and_the_best_player_independently():
    for seed in range(60):
        a = ev.analyse(Settings(n=8, rounds=3, seed=seed, cascade=("BH",)))
        score = a.tournament.score
        assert a.top_group == tuple(r for r in range(1, 9) if score[r - 1] == max(score)) and 0 not in a.top_group
        assert a.best == 1 + max(range(8), key=lambda i: a.tournament.strength[i])


def test_the_smallest_valid_tournament_can_be_played():
    from tbk_tournament import play_tournament
    t = play_tournament(4, 1, 0.2, 0.4, 0.0, 3)
    assert sum(t.score) == 2.0 and t.rounds == 1


def test_verdict_analysis_branches():
    two = next(b for b in (ev.analyse(Settings(seed=s)) for s in range(60)) if len(b.top_group) == 2)
    assert vd.verdict_analysis(two)[1].startswith("2 Spieler liegen")
    flip = ev.analyse(Settings(seed=C.PRESETS["Kippbares Turnier"]["seed"]))
    changed = sum(1 for _x, _y, w in flip.flips if w != flip.winner)
    level, text = vd.verdict_analysis(flip)
    assert level == "warning" and f"die Umkehr von {changed} der {len(flip.flips)} irrelevanten Partien" in text and "mit 6,0 Punkten gleichauf" in text
    level, text = vd.verdict_analysis(ev.analyse(Settings()))
    assert level == "success" and "lässt den Sieger unverändert" in text and "Kippbar" not in text


def test_the_manipulation_row_falls_back_to_the_least_flippable_criterion(metrics):
    from types import SimpleNamespace as NS
    withdraw, bye = ev.exp_withdraw(), ev.exp_bye()
    noise, size = ev.exp_setting(ev.NOISE_SETS), ev.exp_setting(ev.SIZE_SETS)

    def make(h, f):
        return NS(hit_rate=h, flip_rate_t=f, resolved=100, resolution=0.9, top_tie=10, winner_rate=0.2)

    main = {k: make(0.55, 0.30) for k in metrics}
    main["BH"], main["SB"], main["STICH"] = make(0.60, 0.10), make(0.58, 0.12), make(0.7, 0.0)
    assert vd.recommendations(main, withdraw, bye, noise, size)[0][1] == "BH"                  # niemand unter 5 %: der am wenigsten kippbare
    main["SB"] = make(0.58, 0.05)
    assert vd.recommendations(main, withdraw, bye, noise, size)[0][1] == "SB"                  # genau 5 % zählt noch als sicher
    main["AOB"] = make(0.30, 0.0)
    main["TPR"] = NS(hit_rate=0.99, flip_rate_t=0.0, resolved=3, resolution=0.2, top_tie=10, winner_rate=0.2)    # zu wenige getrennte Paare: nie die Empfehlung
    assert vd.recommendations(main, withdraw, bye, noise, size)[0][1] == "SB"


def test_a_short_tournament_can_be_analysed_and_exported():
    import tbk_pdf_export as X
    for seed in range(6):
        s = Settings(n=8, rounds=9, withdraw=0.4, seed=seed, cascade=("DE", "BH-C1", "SB"))
        a = ev.analyse(s)
        assert a.tournament.rounds < 9 and a.winner == a.standing[0][0]
        assert X.build_pdf(a)[:5] == b"%PDF-"


def test_without_flips_no_flip_cases_are_counted(sample):
    res = ev.measure(sample, {"a": ("BH",)}, "fide2026", flips=False)["a"]
    assert res.flip_games == 0 and res.top_tie > 0 and math.isnan(res.flip_rate_g)
