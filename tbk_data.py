"""Vorberechnete Turniere (data/tournaments.json.gz): Laden, Kodieren und der Fingerabdruck der Engine.

Die Experimente rechnen auf festen Turnieren, die einmal mit der echten FIDE-Dutch-Engine erzeugt wurden (rund 0,8 s je Turnier mit 32 Spielern und 7 Runden; über
900 Turniere wären live nicht tragbar). `tools/build_tournaments.py` erzeugt die Datei; ein Test erzeugt eine Stichprobe frisch und vergleicht Seed für Seed."""

import gzip
import hashlib
import json
from functools import lru_cache
from pathlib import Path

import tbk_constants as C
from tbk_tournament import Game, Tournament

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "tournaments.json.gz"
ENGINE_MODULES = ("ss_model", "ss_compat", "ss_colour", "ss_quality", "ss_blossom", "ss_bracket", "ss_engine")
FORMAT = 1
_COLOUR = {"": 0, "w": 1, "b": 2}
_COLOUR_BACK = {0: "", 1: "w", 2: "b"}


def engine_fingerprint() -> str:
    """SHA-1 über die sieben Engine-Module (Zeilenenden normalisiert): hält fest, mit welcher Engine die Datei erzeugt wurde."""
    h = hashlib.sha1()
    for name in ENGINE_MODULES:
        h.update((ROOT / f"{name}.py").read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def encode(t: Tournament) -> dict:
    return {
        "seed": t.seed,
        "strength": list(t.strength),
        "start": list(t.start),
        "leave": list(t.leave),
        "games": [[[g.opponent, int(round(g.score * 2)), _COLOUR[g.colour], int(g.bye), g.round_no] for g in gl] for gl in t.games],
    }


def decode(d: dict, n: int, rounds: int) -> Tournament:
    games = tuple(tuple(Game(o, s / 2.0, _COLOUR_BACK[c], bool(b), rn) for o, s, c, b, rn in gl) for gl in d["games"])
    return Tournament(n, rounds, tuple(d["strength"]), tuple(d["start"]), games, tuple(d["leave"]), d["seed"])


def write(path: Path, sets: dict) -> None:
    """`sets`: Schlüssel -> Liste von Turnieren (Parameter aus C.SETS)."""
    payload = {"format": FORMAT, "engine": engine_fingerprint(), "sets": {}}
    for key, ts in sets.items():
        n, rounds, draw, noise, withdraw, _count, _seed0 = C.SETS[key]
        payload["sets"][key] = {"n": n, "rounds": rounds, "draw": draw, "noise": noise, "withdraw": withdraw, "tournaments": [encode(t) for t in ts]}
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    with gzip.GzipFile(str(path), "wb", mtime=0) as f:           # mtime=0: dieselbe Datei bei gleichem Inhalt
        f.write(raw)


@lru_cache(maxsize=1)
def load_raw() -> dict:
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=None)
def tournaments(key: str) -> tuple:
    """Die Turniere einer festen Menge (C.SETS) als Tuple von Tournament."""
    d = load_raw()["sets"][key]
    return tuple(decode(x, d["n"], d["rounds"]) for x in d["tournaments"])
