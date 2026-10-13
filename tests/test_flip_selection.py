"""Die Auswahl einer Partie zum Umkehren: wechselt der Sieger, steht eine Warnung da, sonst eine Bestätigung; die Auswahl wird beim Wechsel des Turniers zurückgesetzt."""

import os

from streamlit.testing.v1 import AppTest

import tbk_constants as C
import tbk_evaluation as ev
from tbk_scenario import Settings

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = 600


def _app(seed):
    at = AppTest.from_file(APP_PATH)
    at.query_params["seed"] = str(seed)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_a_flipping_game_shows_the_new_winner_and_a_quiet_game_a_confirmation():
    seed = C.PRESETS["Kippbares Turnier"]["seed"]
    a = ev.analyse(Settings(seed=seed))
    flipping = [i for i, (_x, _y, w) in enumerate(a.flips, start=1) if w != a.winner]
    quiet = [i for i, (_x, _y, w) in enumerate(a.flips, start=1) if w == a.winner]
    assert flipping and quiet
    at = _app(seed)
    at.selectbox(key="flip_choice").set_value(flipping[0]).run(timeout=TIMEOUT)
    assert not at.exception
    new_winner = a.flips[flipping[0] - 1][2]
    assert any(f"Der Sieger wechselt von Nr. {a.winner} zu Nr. {new_winner}" in w.value for w in at.warning)
    at.selectbox(key="flip_choice").set_value(quiet[0]).run(timeout=TIMEOUT)
    assert not at.exception
    assert any(f"Der Sieger bleibt Nr. {a.winner}" in s.value for s in at.success)


def test_a_new_random_tournament_resets_the_selection():
    at = _app(C.DEFAULT_SEED)
    at.selectbox(key="flip_choice").set_value(1).run(timeout=TIMEOUT)
    assert at.session_state["flip_choice"] == 1
    labels = {b.label: i for i, b in enumerate(at.button)}
    at.button[labels["🎲 Neues Turnier würfeln"]].click().run(timeout=TIMEOUT)
    assert at.session_state["flip_choice"] == 0 and not at.exception
