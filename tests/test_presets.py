"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; Adressparameter."""

import tbk_constants as C
import tbk_criteria as K
import tbk_presets as P
from tbk_scenario import Settings


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds_and_choices():
    for name, p in C.PRESETS.items():
        assert C.N_MIN <= p["n"] <= C.N_MAX and C.ROUNDS_MIN <= p["rounds"] <= C.ROUNDS_MAX, name
        assert C.DRAW_MIN <= p["draw"] <= C.DRAW_MAX and C.NOISE_MIN <= p["noise"] <= C.NOISE_MAX, name
        assert C.WITHDRAW_MIN <= p["withdraw"] <= C.WITHDRAW_MAX and 0 <= p["seed"] <= C.SEED_MAX, name
        assert p["mode"] in C.MODES and p["c1"] in K.KEYS, name
        assert all(p[c] in (C.EMPTY,) + K.KEYS for c in ("c2", "c3", "c4")), name


def test_default_preset_equals_the_default_settings():
    p = C.PRESETS["Open mit 32 Spielern"]
    cascade = tuple(dict.fromkeys(c for c in (p["c1"], p["c2"], p["c3"], p["c4"]) if c != C.EMPTY))
    s = Settings(p["n"], p["rounds"], p["draw"], p["noise"], p["withdraw"] if p["withdraw_on"] else 0.0, p["mode"], cascade, p["seed"])
    assert s == Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_every_tournament_set_of_the_experiments_has_its_own_seed_range():
    starts = sorted(v[6] for v in C.SETS.values())
    assert len(starts) == len(set(starts))
    assert all(b - a >= max(v[5] for v in C.SETS.values()) for a, b in zip(starts, starts[1:]))


def test_permalink_parameters_are_unique():
    params = [spec.url_param for spec in P.SETTING_SPECS.values()]
    assert len(params) == len(set(params))
