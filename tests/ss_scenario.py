"""NUR FÜR TESTS: Teilmenge von `ss_scenario.py` der Schwesterdemo (`schweizer-system-demo`) - nur der Regeltext-Modus.

Die übernommenen Tests `test_bracket.py` und `test_chain.py` brauchen einen kleinen Turnier-Generator (Elo-Wertungen, Partien nach dem Elo-
Erwartungswert). Das Original importiert außerdem die bbpPairings-treue Engine (networkx), die diese Demo bewusst nicht mitbringt; hier fehlt sie,
sonst ist `generate_tournament` mit dem Original identisch (gleiche Zufallszahlen, gleiche Ergebnisse)."""

from __future__ import annotations

import random
from dataclasses import dataclass

import ss_engine
from ss_engine import apply_round
from ss_model import Player

RULESET = "ruleset"

BASE_RATING = 2000.0
RATING_SPREAD = 150.0


def expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


@dataclass(frozen=True)
class TournamentState:
    players: dict
    ratings: dict
    rounds: tuple
    accelerated: bool = False


def generate_tournament(n_players: int, n_rounds: int, seed: int, engine_mode: str = RULESET, accelerated: bool = False) -> TournamentState:
    if engine_mode != RULESET or accelerated:
        raise NotImplementedError("nur der Regeltext-Modus ohne Beschleunigung (Teilmenge für die Tests)")
    rng = random.Random(seed)
    raw_ratings = sorted((BASE_RATING + rng.gauss(0.0, RATING_SPREAD) for _ in range(n_players)), reverse=True)
    ratings = {rank: raw_ratings[rank - 1] for rank in range(1, n_players + 1)}

    players = {r: Player(rank=r) for r in range(1, n_players + 1)}
    rounds = []
    for rnd in range(1, n_rounds + 1):
        try:
            result = ss_engine.pair_round(players, rnd, total_rounds=n_rounds)
        except ss_engine.NoValidPairingError:
            break
        white_wins = {}
        for p in result.pairings:
            white_wins[p.white] = rng.random() < expected_score(ratings[p.white], ratings[p.black])
        players = apply_round(players, result, white_wins)
        rounds.append(result)
    return TournamentState(players=players, ratings=ratings, rounds=tuple(rounds), accelerated=accelerated)
