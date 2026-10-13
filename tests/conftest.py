"""Gemeinsame Fixtures: von Hand gebaute Mini-Turniere, an denen jede Einheit nachgerechnet wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tbk_tournament import Game, Tournament  # noqa: E402


def build(n, rounds, results, leave=None, start=None, strength=None, seed=0):
    """Baut ein Turnier aus Rundenergebnissen. `results`: je Runde eine Liste von (weiß, schwarz, Punkte des Weißen) oder ("bye", Spieler, Punkte)."""
    games = {r: [] for r in range(1, n + 1)}
    for rnd, round_results in enumerate(results, start=1):
        for item in round_results:
            if item[0] == "bye":
                _tag, p, pts = item
                games[p].append(Game(0, pts, "", True, rnd))
            else:
                w, b, pts = item
                games[w].append(Game(b, pts, "w", False, rnd))
                games[b].append(Game(w, 1.0 - pts, "b", False, rnd))
    start = start or [float(n - r) for r in range(n)]
    strength = strength or [float(n - r) for r in range(n)]
    return Tournament(n, rounds, tuple(strength), tuple(start), tuple(tuple(games[r]) for r in range(1, n + 1)), tuple(leave or [0] * n), seed)


@pytest.fixture
def mini():
    """Sechs Spieler, drei Runden, ohne Freilos. Endstand 1: 2,5; 2: 1,0; 3: 2,0; 4: 1,5; 5: 1,0; 6: 1,0.
    Runde 1: 1-2 (1 gewinnt), 3-4 (Remis), 5-6 (5 gewinnt); Runde 2: 1-3 (Remis), 2-5 (2 gewinnt), 4-6 (4 gewinnt);
    Runde 3: 1-4 (1 gewinnt), 2-6 (6 gewinnt), 3-5 (3 gewinnt). Die Spieler 2, 5, 6 bilden einen Dreierzyklus im Direktvergleich."""
    return build(6, 3, [[(1, 2, 1.0), (3, 4, 0.5), (5, 6, 1.0)], [(1, 3, 0.5), (2, 5, 1.0), (4, 6, 1.0)], [(1, 4, 1.0), (2, 6, 0.0), (3, 5, 1.0)]])


@pytest.fixture
def byes():
    """Fünf Spieler, drei Runden, in jeder Runde ein Freilos (5, 4, 3). Endstand 1: 2,0; 2: 0,0; 3: 1,5; 4: 2,5; 5: 3,0.
    Runde 1: 1-2 (1), 3-4 (Remis), Freilos 5; Runde 2: 1-3 (1), 2-5 (5), Freilos 4; Runde 3: 1-5 (5), 2-4 (4), Freilos 3."""
    return build(5, 3, [[(1, 2, 1.0), (3, 4, 0.5), ("bye", 5, 1.0)], [(1, 3, 1.0), (2, 5, 0.0), ("bye", 4, 1.0)], [(1, 5, 0.0), (2, 4, 0.0), ("bye", 3, 1.0)]])


@pytest.fixture
def withdrawn():
    """Vier Spieler, drei Runden, Spieler 4 tritt vor Runde 3 zurück (keine Berichte für Runde 3).
    Endstand 1: 1,5; 2: 1,5; 3: 2,5 (Freilos in Runde 3); 4: 0,5. Runde 1: 1-2 (1), 3-4 (Remis); Runde 2: 3-1 (3), 2-4 (2); Runde 3: 1-2 (Remis), Freilos 3."""
    return build(4, 3, [[(1, 2, 1.0), (3, 4, 0.5)], [(3, 1, 1.0), (2, 4, 1.0)], [(1, 2, 0.5), ("bye", 3, 1.0)]], leave=[0, 0, 0, 3])
