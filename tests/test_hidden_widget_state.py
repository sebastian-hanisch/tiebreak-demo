"""Invariante der ausblendbaren Regler (DEMO-PLAYBOOK §3, KEPT-Muster): der Anteil der Rücktritte wird nur gezeichnet, wenn Rücktritte zugelassen sind; sein zuletzt
gewählter Wert wird gemerkt und kommt beim nächsten Zeichnen zurück, ohne je in ein nicht gezeichnetes Widget geschrieben zu werden."""

import os

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = 600


def fresh():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def widget_keys(at):
    return {s.key for s in at.slider}


def test_the_withdrawal_slider_is_only_drawn_where_it_acts():
    at = fresh()
    assert "withdraw_slider" not in widget_keys(at)
    at.checkbox(key="withdraw_toggle").check().run(timeout=TIMEOUT)
    assert "withdraw_slider" in widget_keys(at) and not at.exception


def test_the_hidden_value_survives_and_is_not_written_into_the_hidden_widget():
    at = fresh()
    at.checkbox(key="withdraw_toggle").check().run(timeout=TIMEOUT)
    at.slider(key="withdraw_slider").set_value(0.35).run(timeout=TIMEOUT)
    at.checkbox(key="withdraw_toggle").uncheck().run(timeout=TIMEOUT)
    assert "withdraw_slider" not in at.session_state
    at.checkbox(key="withdraw_toggle").check().run(timeout=TIMEOUT)
    assert abs(at.slider(key="withdraw_slider").value - 0.35) < 1e-9
    assert not at.exception


def test_a_preset_sets_values_and_the_hidden_widget_for_the_next_drawing():
    at = fresh()
    labels = {b.label: i for i, b in enumerate(at.button)}
    at.button[labels["Viele Rücktritte"]].click().run(timeout=TIMEOUT)
    assert at.checkbox(key="withdraw_toggle").value is True and abs(at.slider(key="withdraw_slider").value - 0.3) < 1e-9
    assert at.selectbox(key="mode_select").value == "ignore" and at.selectbox(key="c2_select").value == "–"
    labels = {b.label: i for i, b in enumerate(at.button)}
    at.button[labels["Ungerade Zahl mit Freilosen"]].click().run(timeout=TIMEOUT)
    assert at.slider(key="n_slider").value == 31 and at.checkbox(key="withdraw_toggle").value is False
    assert "withdraw_slider" not in at.session_state
    assert not at.exception


def test_the_flip_selection_is_reset_by_a_preset():
    at = fresh()
    labels = {b.label: i for i, b in enumerate(at.button)}
    at.button[labels["Kippbares Turnier"]].click().run(timeout=TIMEOUT)
    assert at.session_state["flip_choice"] == 0 and not at.exception
