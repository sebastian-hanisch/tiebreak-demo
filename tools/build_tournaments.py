"""Erzeugt data/tournaments.json.gz: die festen Turniere der Experimente, mit der echten FIDE-Dutch-Engine (ss_engine).

    python tools/build_tournaments.py [--workers 4] [--only main,n31]

Je Menge aus tbk_constants.SETS: `Anzahl` Turniere mit den Seeds Seed-Anfang + 0 … Anzahl − 1. Rund 12 Minuten einkernig; die Datei ist deterministisch."""

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import tbk_constants as C  # noqa: E402
import tbk_data as D  # noqa: E402
from tbk_tournament import play_tournament  # noqa: E402


def _one(args):
    n, rounds, draw, noise, withdraw, seed = args
    return play_tournament(n, rounds, draw, noise, withdraw, seed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", default="", help="kommagetrennte Schlüssel (sonst alle)")
    args = ap.parse_args()
    keys = [k for k in C.SETS if not args.only or k in args.only.split(",")]
    sets = {}
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for key in keys:
            n, rounds, draw, noise, withdraw, count, seed0 = C.SETS[key]
            t0 = time.time()
            jobs = [(n, rounds, draw, noise, withdraw, seed0 + i) for i in range(count)]
            sets[key] = list(ex.map(_one, jobs, chunksize=4))
            print(f"{key}: {count} Turniere in {time.time() - t0:.0f} s", flush=True)
    if args.only:                                   # nur einzelne Mengen ersetzen: die übrigen aus der vorhandenen Datei übernehmen
        for key in C.SETS:
            if key not in sets:
                sets[key] = list(D.tournaments(key))
    D.write(ROOT / "data" / "tournaments.json.gz", {k: sets[k] for k in C.SETS})
    print("geschrieben:", ROOT / "data" / "tournaments.json.gz")


if __name__ == "__main__":
    main()
