"""Szenario: Reglerwerte (Settings) und das daraus erzeugte Turnier."""

from dataclasses import dataclass

import tbk_constants as C
from tbk_tournament import Tournament, play_tournament


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    rounds: int = C.DEFAULT_ROUNDS
    draw: float = C.DEFAULT_DRAW
    noise: float = C.DEFAULT_NOISE
    withdraw: float = 0.0                       # 0 = niemand tritt zurück
    mode: str = C.DEFAULT_MODE
    cascade: tuple = ("DE", "BH-C1", "BH", "WIN")
    seed: int = C.DEFAULT_SEED


def make_tournament(s: Settings) -> Tournament:
    """Deterministisch aus den Reglerwerten: gleiche Eingabe, gleiches Turnier."""
    return play_tournament(s.n, s.rounds, s.draw, s.noise, s.withdraw, s.seed)
