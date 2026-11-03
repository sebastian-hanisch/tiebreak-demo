"""JEDE Zahl und Aussage aus App-Texten und README wird hier nachgerechnet (über die festen, vorberechneten Turniere; nie ein einzelnes Turnier).
Die Turniere liegen als Datei vor, die Auswertung ist reine Python-Arithmetik: die Zahlen sind plattformunabhängig; Schwellen trotzdem mit Abstand zur Messung."""

import pytest

import tbk_constants as C
import tbk_data as D
import tbk_evaluation as ev
import tbk_verdicts as vd


@pytest.fixture(scope="module")
def crit():
    return ev.exp_criteria("fide2026")


@pytest.fixture(scope="module")
def casc():
    return ev.exp_cascades("fide2026")


@pytest.fixture(scope="module")
def withdraw():
    return ev.exp_withdraw()


@pytest.fixture(scope="module")
def bye():
    return {(r["mode"], r["key"]): r for r in ev.exp_bye()}


@pytest.fixture(scope="module")
def noise():
    return ev.exp_setting(ev.NOISE_SETS, "fide2026")


@pytest.fixture(scope="module")
def draw():
    return ev.exp_setting(ev.DRAW_SETS, "fide2026", references=False)


@pytest.fixture(scope="module")
def size():
    return ev.exp_setting(ev.SIZE_SETS, "fide2026")


def hit(rows, key, value):
    return 100 * next(r["hit_rate"] for r in rows if r["key"] == key and r["value"] == value)


def w_hit(rows, key, w, mode):
    return 100 * next(r["hit_rate"] for r in rows if r["key"] == key and r["withdraw"] == w and r["mode"] == mode)


# --- Aufbau der Mengen --------------------------------------------------------------------------------------------------------------------

def test_the_sets_and_the_tie_for_first_place():
    assert len(D.tournaments("main")) == 400
    assert sum(len(D.tournaments(k)) for k in C.SETS) == sum(v[5] for v in C.SETS.values()) == 1140
    tied = sum(1 for t in D.tournaments("main") if sum(1 for s in t.score if s == max(t.score)) >= 2)
    assert tied == 124                                            # „124 von 400 Turnieren (31 %)“


# --- Experiment 1 und 2: Treffer, Auflösung, Kippen -----------------------------------------------------------------------------------------

HITS = {"BH": 59.6, "BH-C1": 59.4, "BH-C2": 59.3, "BH-M1": 59.0, "BH-M2": 58.8, "AOB": 58.2, "SB": 58.2, "DE": 48.9, "PS": 63.1, "PS-G": 61.2, "WIN": 50.1,
        "WON": 50.1, "BWG": 49.0, "BPG": 49.5, "ARO": 52.5, "TPR": 52.5, "RTNG": 85.8, "STICH": 69.2}


def test_the_hit_rates_of_experiment_1(crit):
    for k, v in HITS.items():
        assert 100 * crit[k].hit_rate == pytest.approx(v, abs=0.06), k


EXPECTATIONS = {"BH": 0.553, "BH-C1": 0.552, "BH-C2": 0.551, "BH-M1": 0.551, "BH-M2": 0.549, "AOB": 0.544, "SB": 0.545, "DE": 0.496, "PS": 0.572, "PS-G": 0.560,
                "WIN": 0.501, "BWG": 0.496, "BPG": 0.498, "ARO": 0.512, "TPR": 0.512, "RTNG": 0.667, "STICH": 0.692}


def test_the_expectations_of_experiment_1(crit):
    for k, v in EXPECTATIONS.items():
        assert crit[k].expectation == pytest.approx(v, abs=0.0006), k


def test_the_resolution_of_experiment_1(crit):
    res = {k: round(100 * m.resolution) for k, m in crit.items()}
    assert res["BH"] == 95 and res["BH-C1"] == 95 and res["BH-C2"] == 94 and res["BH-M1"] == 94 and res["BH-M2"] == 90
    assert res["AOB"] == 98 and res["SB"] == 95 and res["PS"] == 94 and res["PS-G"] == 99
    assert res["DE"] == 2                                          # der Direktvergleich nach Artikel 6 trennt im Schweizer System kaum
    assert (crit["DE"].resolved, crit["DE"].pairs) == (350, 22080) and round(100 * crit["DE"].resolution, 1) == 1.6
    assert res["WIN"] == 47 and res["BWG"] == 63 and res["BPG"] == 52 and res["REP"] == 0
    assert res["ARO"] == 100 and res["RTNG"] == 100 and res["STICH"] == 100 and res["LOS"] == 0


def test_the_playoff_and_the_start_rating_beat_every_computed_criterion_except_the_start_rating_is_the_setting(crit):
    computed = [k for k in ("BH", "BH-C1", "BH-C2", "BH-M1", "BH-M2", "AOB", "SB", "PS", "PS-G", "ARO", "TPR")]
    assert crit["STICH"].hit_rate > max(crit[k].hit_rate for k in computed) + 0.05
    assert crit["PS"].hit_rate == max(crit[k].hit_rate for k in computed)
    assert min(crit[k].hit_rate for k in ("WIN", "WON", "BPG")) < 0.5          # Siege und Schwarzpartien: kein Informationsgewinn


def test_the_winner_is_rarely_the_strongest_whatever_the_criterion(crit):
    rates = [100 * m.winner_rate for m in crit.values()]
    assert 18 <= min(rates) and max(rates) <= 25.5                # „in 18 bis 24 % der Turniere der wahre Stärkste“
    assert max(100 * m.podium_rate for m in crit.values()) < 6.5


def test_the_flip_rates_of_experiment_2(crit):
    t = {k: round(100 * m.flip_rate_t) for k, m in crit.items() if k not in ("STICH", "LOS")}
    g = {k: round(100 * m.flip_rate_g, 1) for k, m in crit.items() if k not in ("STICH", "LOS")}
    assert t["BH"] == 34 and t["BH-C1"] == 30 and t["BH-C2"] == 23 and t["BH-M1"] == 30 and t["BH-M2"] == 32 and t["AOB"] == 27 and t["SB"] == 35 and t["PS-G"] == 9
    assert g["BH"] == pytest.approx(7.5, abs=0.06) and g["BH-C2"] == pytest.approx(2.6, abs=0.06) and g["AOB"] == pytest.approx(6.7, abs=0.06)
    assert g["SB"] == pytest.approx(6.9, abs=0.06) and g["PS-G"] == pytest.approx(1.7, abs=0.06)
    for k in ("PS", "DE", "WIN", "WON", "BWG", "BPG", "REP", "ARO", "TPR", "RTNG"):
        assert t[k] == 0 and g[k] == 0, k
    assert crit["BH"].top_tie == 124 and crit["BH"].flip_games == 1351


def test_the_family_range_in_the_flip_verdict(crit):
    text = vd.verdict_flips(crit)[1]
    assert "23 bis 34 %" in text and "124 Turnieren" in text and "bei SB in 35 %" in text


def test_the_direct_encounter_works_only_in_small_groups():
    from collections import defaultdict
    import tbk_criteria as K
    sizes, resolved, pairs = defaultdict(int), defaultdict(int), defaultdict(int)
    for t in D.tournaments("main"):
        groups = defaultdict(list)
        for r in range(1, t.n + 1):
            groups[t.score[r - 1]].append(r)
        for grp in groups.values():
            n = len(grp)
            if n < 2:
                continue
            blocks = K.direct_encounter(grp, t.games)
            block_of = {r: i for i, b in enumerate(blocks) for r in b}
            sizes[n] += 1
            pairs[n] += n * (n - 1) // 2
            resolved[n] += sum(1 for i in range(n) for j in range(i + 1, n) if block_of[grp[i]] != block_of[grp[j]])
    assert [sizes[n] for n in (2, 3, 4)] == [725, 617, 538] and sum(v for n, v in sizes.items() if n >= 5) == 1040
    assert [round(100 * resolved[n] / pairs[n], 1) for n in (2, 3, 4)] == [34.1, 5.4, 0.1]
    assert sum(resolved[n] for n in resolved if n >= 5) == 0


# --- Experiment 3: Kaskaden ---------------------------------------------------------------------------------------------------------------

def test_the_cascades(casc):
    exp = {"DE → BH-C1 → BH → WIN": (59.0, 14), "BH-C1 → BH → SB → DE": (59.0, 29), "PS → BH-C1 → SB": (62.3, 3), "WIN → DE → BH": (55.3, 12),
           "DE → PS → BH-C1": (62.3, 4), "AOB → BH → SB": (58.2, 28), "BH-C1 → RTNG": (60.8, 31)}
    for name, (h, f) in exp.items():
        assert 100 * casc[name].hit_rate == pytest.approx(h, abs=0.06), name
        assert round(100 * casc[name].flip_rate_t) == f, name
        assert casc[name].resolution >= 0.97, name
    assert casc["PS → BH-C1 → SB"].flip_rate_g < 0.01


# --- Experiment 4: Rücktritte ------------------------------------------------------------------------------------------------------------

def test_withdrawals_hurt_buchholz_and_help_sonneborn_berger_and_progressive(withdraw):
    assert [round(w_hit(withdraw, "BH", w, "ignore"), 1) for _s, w in ev.WITHDRAW_SETS] == [59.6, 53.9, 44.8]
    assert [round(w_hit(withdraw, "BH", w, "fide2026"), 1) for _s, w in ev.WITHDRAW_SETS] == [59.6, 58.9, 51.6]
    assert [round(w_hit(withdraw, "BH-C1", w, "ignore"), 1) for _s, w in ev.WITHDRAW_SETS] == [59.4, 54.1, 44.0]
    assert w_hit(withdraw, "BH-C1", 0.30, "fide2026") == pytest.approx(49.5, abs=0.06)
    assert [round(w_hit(withdraw, "SB", w, "fide2026"), 1) for _s, w in ev.WITHDRAW_SETS] == [58.2, 61.0, 63.0]
    assert [round(w_hit(withdraw, "PS", w, "fide2026"), 1) for _s, w in ev.WITHDRAW_SETS] == [63.1, 67.9, 70.8]
    assert w_hit(withdraw, "AOB", 0.30, "fide2026") == pytest.approx(55.8, abs=0.06)
    assert w_hit(withdraw, "WIN", 0.30, "fide2026") == pytest.approx(57.3, abs=0.06)


def test_the_two_fide_versions_hardly_differ_for_withdrawals(withdraw):
    for k in ev.WITHDRAW_KEYS:
        for w in (0.15, 0.30):
            assert abs(w_hit(withdraw, k, w, "fide2024") - w_hit(withdraw, k, w, "fide2026")) <= 0.1, (k, w)


# --- Experiment 5: Freilose --------------------------------------------------------------------------------------------------------------

def test_bye_bias(bye):
    def b(mode, key):
        return round(100 * bye[(mode, key)]["bias"])
    assert (b("ignore", "BH"), b("fide2026", "BH"), b("fide2024", "BH")) == (-13, 8, 9)
    assert (b("ignore", "BH-C1"), b("fide2026", "BH-C1"), b("fide2024", "BH-C1")) == (-16, 7, 7)
    assert (b("ignore", "SB"), b("fide2026", "SB"), b("fide2024", "SB")) == (-20, 13, 13)
    assert (b("ignore", "AOB"), b("fide2026", "AOB")) == (26, 21)
    assert b("fide2026", "WIN") == 51 and b("fide2026", "WON") == -18
    assert b("fide2026", "PS") == 0 and b("fide2026", "TPR") == -4 and b("fide2026", "RTNG") == -1


def test_the_two_fide_versions_differ_by_at_most_one_point_in_the_bye_bias(bye):
    for k in ev.BYE_KEYS:
        assert abs(100 * bye[("fide2024", k)]["bias"] - 100 * bye[("fide2026", k)]["bias"]) <= 1.0, k


# --- Experiment 6 und 7: Setzliste, Remis, Feldgröße ------------------------------------------------------------------------------------

def test_noise(noise):
    assert [round(hit(noise, "RTNG", v)) for v in (0.0, 0.4, 1.0, 2.0)] == [100, 86, 69, 61]
    assert [round(hit(noise, "PS", v)) for v in (0.0, 0.4, 1.0, 2.0)] == [65, 63, 61, 57]
    assert [round(hit(noise, "BH-C1", v)) for v in (0.0, 0.4, 1.0, 2.0)] == [60, 59, 62, 59]


def test_draws(draw):
    assert [round(hit(draw, "BH", v), 1) for v in (0.0, 0.2, 0.4)] == [67.0, 59.6, 58.7]
    assert [round(hit(draw, "PS", v)) for v in (0.0, 0.2, 0.4)] == [70, 63, 63]
    res = {r["value"]: r["resolution"] for r in draw if r["key"] == "WIN"}
    assert res[0.0] == 0.0 and round(100 * res[0.2]) == 47 and round(100 * res[0.4]) == 55


def test_sizes(size):
    labels = [s[1] for s in ev.SIZE_SETS]
    assert [round(hit(size, "BH", v), 1) for v in labels] == [53.3, 58.9, 59.6, 63.6]
    assert [round(hit(size, "PS", v)) for v in labels] == [55, 63, 63, 67]
    assert [round(hit(size, "STICH", v)) for v in labels] == [65, 70, 69, 69]
    assert [round(hit(size, "RTNG", v)) for v in labels] == [83, 87, 86, 85]
    de_values = [hit(size, "DE", v) for v in labels]
    assert round(min(de_values)) == 39 and round(max(de_values)) == 61      # Direktvergleich: wenige Paare, nicht zu deuten


# --- Texte der App stützen sich auf dieselben Werte ----------------------------------------------------------------------------------------

def test_verdict_texts_quote_the_measured_numbers(crit, withdraw, noise):
    text = vd.verdict_criteria(crit)[1]
    assert "**PS**" in text and "63 %" in text and "69 %" in text and "86 %" in text and "nur 1,6 % der Paare" in text
    assert "**BWG** am seltensten (49 %)" in text and "**PS** am häufigsten (63 % der getrennten Paare)" in text
    text = vd.verdict_withdraw(withdraw)[1]
    assert "60 auf 45 %" in text and "52 %" in text and "58 → 63 %" in text and "63 → 71 %" in text


def test_every_recommendation_names_a_criterion_that_exists(crit, withdraw, bye, noise, size):
    rows = vd.recommendations(crit, withdraw, list(bye.values()), noise, size)
    assert rows[0][1] == "PS"
    assert rows[1][1].startswith("PS, dann ")
    assert rows[2][1].startswith("PS;")
    assert rows[3][1] == "PS"


def test_the_playoff_reference_measures(crit):
    m = crit["STICH"]
    assert round(100 * m.winner_rate, 2) == 22.0 and round(100 * m.podium_rate, 2) == 4.0 and round(m.tau, 4) == 0.6169


def test_the_remaining_verdict_texts(crit, withdraw, bye, noise, draw, size):
    text = vd.verdict_flips(crit)[1]
    assert "ARO, BPG, BWG, PS, RTNG, TPR, WIN, WON" in text and "23 bis 34 %" in text
    assert "18 bis 24 %" in vd.verdict_criteria(crit)[1]
    text = vd.verdict_noise(noise)[1]
    assert "100 %" in text and "61 %" in text and "von 65 auf 57 %" in text and "zwischen 59 und 62 %" in text
    text = vd.verdict_draw(draw)[1]
    assert "67 % bei 0 % Remis" in text and "59 % bei 40 %" in text and "Auflösung 0 %" in text and "bei 40 % Remis 55 %" in text
    text = vd.verdict_size(size)[1]
    assert "(16 Spieler, 5 Runden) trifft Buchholz 53 % und der Fortschritt 55 %" in text and "32 Spieler, 9 Runden) 64 % und 67 %" in text
    text = vd.verdict_bye(list(bye.values()))[1]
    assert "(−13 Prozentpunkte)" in text and "(**+8**)" in text and "von −20 auf +13" in text and "(±0)" in text and "(+51)" in text and "(−18)" in text


def test_the_recommendation_table_rows(crit, withdraw, bye, noise, size):
    rows = vd.recommendations(crit, withdraw, list(bye.values()), noise, size)
    assert rows[0][2] == "63 % Treffer; in 0 % der Turniere mit Gleichstand um Platz 1 kippbar"
    assert rows[1][1] == "PS, dann PS-G" and "PS-G ist in 9 % der Turniere" in rows[1][3]
    assert rows[2][0] == "Viele Rücktritte (30 %)" and rows[2][2] == "71 % Treffer; Buchholz 52 % mit FIDE-Regel, 45 % ohne"
    assert rows[3][2].startswith("Verzerrung ±0 Prozentpunkte; Buchholz +8, Sonneborn-Berger +13")
    assert rows[4][1].startswith("BH;") and rows[4][2] == "59 % Treffer; Startwertung 61 %"
    assert rows[5][2] == "69 % Treffer im Modell, besser als jedes Rechenkriterium"
    assert rows[6][0].endswith("(16 Spieler, 5 Runden)") and rows[6][2] == "bestes Kriterium AOB mit 56 % Treffer"
