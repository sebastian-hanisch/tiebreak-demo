"""Grenzfälle der Verdikte und der Empfehlungstabelle mit künstlichen Messwerten: Schwellen (Auflösung ab 0,3, mindestens 200 Paare) sind eingeschlossen, und die
Zeilen für Rücktritte und Freilose lesen genau die Behandlung nach FIDE ab 03/2026."""

from types import SimpleNamespace as NS

import tbk_criteria as K
import tbk_evaluation as ev
import tbk_verdicts as vd


def metric(hit, flip=0.5, res=0.9, resolved=100, top=10, winner=0.2):
    return NS(hit_rate=hit, flip_rate_t=flip, resolution=res, resolved=resolved, top_tie=top, winner_rate=winner, expectation=0.5)


def base_metrics():
    m = {k: metric(0.55) for k in K.KEYS}
    m["STICH"], m["LOS"] = metric(0.70, res=1.0), metric(float("nan"), res=0.0, resolved=0)
    return m


def test_a_criterion_at_the_resolution_threshold_counts_in_the_criteria_verdict():
    m = base_metrics()
    m["BH"] = metric(0.90, res=0.3)
    assert "**BH** am häufigsten (90 %" in vd.verdict_criteria(m)[1]
    m["BH"] = metric(0.90, res=0.29)
    assert "**BH** am häufigsten" not in vd.verdict_criteria(m)[1]


def test_a_criterion_at_the_resolution_threshold_counts_in_the_flip_verdict():
    m = base_metrics()
    m["SB"] = metric(0.55, flip=0.99, res=0.3)
    assert "bei SB in 99 %" in vd.verdict_flips(m)[1]
    m["SB"] = metric(0.55, flip=0.99, res=0.29)
    assert "bei SB in 99 %" not in vd.verdict_flips(m)[1]


def _rows_for_recommendations():
    withdraw = []
    for w in (0.0, 0.15, 0.30):
        for mode in ("ignore", "fide2024", "fide2026"):
            for key, rates in {"BH": (0.40, 0.50, 0.60), "PS": (0.70, 0.52, 0.55)}.items():
                withdraw.append({"withdraw": w, "mode": mode, "key": key, "hit_rate": rates[("ignore", "fide2024", "fide2026").index(mode)], "resolution": 0.9})
    withdraw += [{"withdraw": 0.15, "mode": "fide2026", "key": "BH", "hit_rate": 0.10, "resolution": 0.9},       # zuletzt: falscher Rücktrittsanteil
                 {"withdraw": 0.30, "mode": "ignore", "key": "PS", "hit_rate": 0.99, "resolution": 0.9}]         # zuletzt: falsche Behandlung
    bye = []
    for key, pairs, bias in (("BH", 300, 0.08), ("SB", 250, 0.05), ("AOB", 200, 0.01), ("TPR", 199, 0.00), ("WIN", 500, 0.30)):
        bye.append({"mode": "fide2026", "key": key, "bias": bias, "pairs": pairs, "hit_rate": 0.5})
    bye.append({"mode": "ignore", "key": "TPR", "bias": 0.0, "pairs": 500, "hit_rate": 0.5})                    # falsche Behandlung, darf nicht gewinnen
    return withdraw, bye


def _other_rows():
    size = [{"value": ev.SIZE_SETS[0][1], "key": "BH", "hit_rate": 0.5, "resolution": 0.9}]
    noise = [{"value": 2.0, "key": "BH", "hit_rate": 0.5, "resolution": 0.9}, {"value": 2.0, "key": "RTNG", "hit_rate": 0.6, "resolution": 1.0}]
    return noise, size


def test_the_withdrawal_row_reads_the_last_withdrawal_share_and_the_2026_treatment():
    withdraw, bye = _rows_for_recommendations()
    noise, size = _other_rows()
    rows = vd.recommendations(base_metrics(), withdraw, bye, noise, size)
    assert rows[2][1] == "BH; Buchholz meiden" and rows[2][2].startswith("60 % Treffer")      # 2026 und 30 %: BH 0,60 gegen PS 0,55


def test_the_bye_row_includes_exactly_200_pairs_and_only_the_2026_treatment():
    withdraw, bye = _rows_for_recommendations()
    noise, size = _other_rows()
    rows = vd.recommendations(base_metrics(), withdraw, bye, noise, size)
    assert rows[3][1] == "AOB"        # kleinste Verzerrung unter den Zeilen der Behandlung 2026 mit mindestens 200 Paaren (TPR hat 199, die zweite TPR-Zeile die falsche Behandlung)


def test_resolution_thresholds_hold_in_noise_size_and_main_rows():
    withdraw, bye = _rows_for_recommendations()
    noise = [{"value": 2.0, "key": "SB", "hit_rate": 0.80, "resolution": 0.3}, {"value": 2.0, "key": "RTNG", "hit_rate": 0.6, "resolution": 1.0}]
    size = [{"value": ev.SIZE_SETS[0][1], "key": "AOB", "hit_rate": 0.80, "resolution": 0.3}]
    rows = vd.recommendations(base_metrics(), withdraw, bye, noise, size)
    assert rows[4][1].startswith("SB;") and rows[6][2].startswith("bestes Kriterium AOB")
    noise[0]["resolution"] = size[0]["resolution"] = 0.29
    noise.append({"value": 2.0, "key": "BH", "hit_rate": 0.5, "resolution": 0.9})
    size.append({"value": ev.SIZE_SETS[0][1], "key": "BH", "hit_rate": 0.5, "resolution": 0.9})
    rows = vd.recommendations(base_metrics(), withdraw, bye, noise, size)
    assert rows[4][1].startswith("BH;") and rows[6][2].startswith("bestes Kriterium BH")
    m = base_metrics()
    m["BH"] = metric(0.99, flip=0.0, res=0.3)
    assert vd.recommendations(m, withdraw, bye, noise, size)[0][1] == "BH"


def test_the_winner_wording_of_the_tournament_verdict():
    from tbk_scenario import Settings
    best_wins = next(a for a in (ev.analyse(Settings(seed=s)) for s in range(80)) if a.winner == a.best and len(a.top_group) >= 2)
    assert "und ist der wahre Stärkste." in vd.verdict_analysis(best_wins)[1] and "nicht der wahre" not in vd.verdict_analysis(best_wins)[1]
    other = next(a for a in (ev.analyse(Settings(seed=s)) for s in range(80)) if a.winner != a.best and len(a.top_group) >= 2)
    assert "nicht der wahre Stärkste (das ist Nr." in vd.verdict_analysis(other)[1]
