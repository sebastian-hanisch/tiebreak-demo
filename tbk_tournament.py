"""Ein Schweizer Turnier mit der echten FIDE-Dutch-Engine (ss_engine, wortgleich aus schweizer-system-demo).

Stärken aus turnier_generator.make_strengths (Abstand DELTA), zufällig auf die Spieler verteilt; die Startrangliste entsteht aus Stärke + Rauschen (Rang 1 = höchste
Startwertung). Ausgang einer Partie: Remis mit Wahrscheinlichkeit `draw`, sonst Sieg des Weißen mit Wahrscheinlichkeit σ(Stärkedifferenz). Rücktritte: ein Spieler tritt
vor einer Runde zurück (`absent` der Engine), bleibt aber mit seinem Stand in der Tabelle. Zufall nur über SplitMix64. Spieler heißen nach ihrer Startnummer 1..n."""

import math
from dataclasses import dataclass
from typing import NamedTuple

import numpy as np

import ss_engine
import tbk_constants as C
import turnier_generator as T
from ss_model import Player


class Game(NamedTuple):
    opponent: int      # Startnummer des Gegners, 0 bei Freilos
    score: float       # Punkte dieser Runde
    colour: str        # "w", "b" oder "" (Freilos)
    bye: bool          # Freilos (kein Gegner am Brett)
    round_no: int


@dataclass(frozen=True)
class Tournament:
    n: int
    rounds: int
    strength: tuple    # wahre Stärke je Startnummer (Index = Nummer − 1)
    start: tuple       # Startwertung je Startnummer
    games: tuple       # je Startnummer ein Tupel von Game, in Rundenfolge
    leave: tuple       # Runde, ab der der Spieler fehlt (0 = bleibt bis zum Ende)
    seed: int

    @property
    def score(self) -> tuple:
        return tuple(sum(g.score for g in gl) for gl in self.games)


def normals(rng: T.SplitMix64, size: int) -> np.ndarray:
    """Standardnormalverteilte Zahlen per Box-Muller aus der Gleichverteilten des Generators."""
    u1 = 1.0 - rng.uniform(size)
    u2 = rng.uniform(size)
    return np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2)


def play_tournament(n: int, rounds: int, draw: float, noise: float, withdraw: float, seed: int) -> Tournament:
    """Deterministisch aus den Eingaben: gleiche Eingabe, gleiches Turnier (die Engine ist deterministisch).

    `Tournament.rounds` ist die Zahl der tatsächlich gespielten Runden: Findet die Engine in einer Runde keine Paarung ohne Wiederholung (kleines Feld, viele Runden,
    Rücktritte), endet das Turnier vorher, wie ein echtes Turnier auch."""
    if n < 4 or rounds < 1:
        raise ValueError("n >= 4 und rounds >= 1 verlangt")
    rng = T.SplitMix64(seed ^ C.SEED_SALT)
    s = T.make_strengths(n, C.DELTA)
    s = s[rng.permutation(n)]
    r0 = s + noise * normals(rng, n)
    order = np.argsort(-r0, kind="stable")
    strength = [round(float(s[order[r]]), 6) for r in range(n)]
    start = [round(float(r0[order[r]]), 6) for r in range(n)]
    u_leave, u_round = rng.uniform(n), rng.uniform(n)
    leave = [0] * n
    hi = max(rounds - 1, 4)                                          # Rücktritt vor einer Runde in [3, hi − 1]
    for r in range(n):
        if u_leave[r] < withdraw:                                     # u in [0, 1): bei withdraw = 0 nie erfüllt
            leave[r] = 3 + int(u_round[r] * (hi - 3))
    players = {r: Player(rank=r) for r in range(1, n + 1)}
    played = rounds                                                   # kürzer, wenn das Schweizer System keine zulässige Paarung mehr findet
    for rnd in range(1, rounds + 1):
        absent = frozenset(r + 1 for r in range(n) if leave[r] and leave[r] <= rnd)
        try:
            res = ss_engine.pair_round(players, rnd, absent=absent, total_rounds=rounds)
        except ss_engine.NoValidPairingError:                         # kleines Feld, viele Runden, Rücktritte: ohne Wiederholung geht es nicht weiter
            played = rnd - 1
            break
        u = rng.uniform(len(res.pairings))
        white_wins = {}
        for k, p in enumerate(res.pairings):
            e = 1.0 / (1.0 + math.exp(-(strength[p.white - 1] - strength[p.black - 1])))
            pw = (1.0 - draw) * e
            white_wins[p.white] = True if u[k] < pw else (None if u[k] < pw + draw else False)
        players = ss_engine.apply_round(players, res, white_wins)
    games = tuple(tuple(Game(g.opponent, float(g.score), g.colour or "", bool(g.counted_as_bye), g.round_no) for g in players[r].games)
                  for r in range(1, n + 1))
    return Tournament(n, played, tuple(strength), tuple(start), games, tuple(leave), seed)


def played_rounds(t: Tournament, r: int) -> int:
    """Runden, in denen Spieler r einen Spielbericht hat (Partie oder Freilos)."""
    return len({g.round_no for g in t.games[r - 1]})


def missing_rounds(t: Tournament, r: int) -> int:
    """Runden ohne Spielbericht (nach dem Rücktritt)."""
    return t.rounds - played_rounds(t, r)
