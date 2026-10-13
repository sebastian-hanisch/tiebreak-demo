"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 8, 32, 32
ROUNDS_MIN, ROUNDS_MAX, DEFAULT_ROUNDS = 3, 9, 7
DRAW_MIN, DRAW_MAX, DRAW_STEP, DEFAULT_DRAW = 0.0, 0.5, 0.05, 0.2         # Anteil der Remis unter allen Partien
NOISE_MIN, NOISE_MAX, NOISE_STEP, DEFAULT_NOISE = 0.0, 2.0, 0.1, 0.4      # Rauschen der Startwertung (logistische Einheiten)
WITHDRAW_MIN, WITHDRAW_MAX, WITHDRAW_STEP, DEFAULT_WITHDRAW = 0.05, 0.4, 0.05, 0.15   # Anteil der Spieler, die vorzeitig ausscheiden
SEED_MAX, DEFAULT_SEED = 999999, 29           # typisch: drei Spieler an der Spitze, Buchholz Cut-1 entscheidet, Treffer 61 % (Mittel 59 %), nicht kippbar
DELTA = 0.12                                  # Stärkeabstand zweier Nachbarn (logistische Einheiten), wie in der Vorab-Messreihe
CASCADE_LEN = 4                               # Kriterien der Kaskade (das erste ist Pflicht)
EMPTY = "–"                                   # Auswahlwert: Kaskadenstufe nicht belegt

# Behandlung nicht gespielter Runden: Schlüssel -> Anzeige
MODES = {
    "ignore": "Ignorieren (Freilos und Runden nach Rücktritt zählen nicht)",
    "fide2024": "FIDE Artikel 16, Fassung 08/2024",
    "fide2026": "FIDE Artikel 16, Fassung ab 03/2026",
}
DEFAULT_MODE = "fide2026"

# Feste Turniermengen für alle Experimente (data/tournaments.json.gz): Schlüssel -> (n, Runden, Remis, Rauschen, Rücktritte, Anzahl, Seed-Anfang)
SETS = {
    "main": (32, 7, 0.2, 0.4, 0.0, 400, 400000),
    "noise0": (32, 7, 0.2, 0.0, 0.0, 60, 410000),
    "noise10": (32, 7, 0.2, 1.0, 0.0, 60, 420000),
    "noise20": (32, 7, 0.2, 2.0, 0.0, 60, 430000),
    "draw0": (32, 7, 0.0, 0.4, 0.0, 60, 440000),
    "draw40": (32, 7, 0.4, 0.4, 0.0, 60, 450000),
    "w15": (32, 7, 0.2, 0.4, 0.15, 60, 460000),
    "w30": (32, 7, 0.2, 0.4, 0.30, 60, 470000),
    "n16r5": (16, 5, 0.2, 0.4, 0.0, 100, 480000),
    "n32r5": (32, 5, 0.2, 0.4, 0.0, 60, 490000),
    "n32r9": (32, 9, 0.2, 0.4, 0.0, 60, 500000),
    "n31": (31, 7, 0.2, 0.4, 0.0, 100, 510000),
}
SEED_SALT = 0x7B1E
FLIP_MARGIN = 1.5                             # „irrelevante“ Partie: beide Beteiligten liegen mindestens so viele Punkte unter der Spitze

COLOR_MAIN = "#2F6B65"
COLOR_FIDE = "#8e6bb0"
COLOR_BAD = "#c0392b"
COLOR_REF = "#e67e22"
COLOR_GREY = "rgba(150,150,150,0.65)"

_BASE = {"n": DEFAULT_N, "rounds": DEFAULT_ROUNDS, "draw": DEFAULT_DRAW, "noise": DEFAULT_NOISE, "withdraw_on": False, "withdraw": DEFAULT_WITHDRAW,
         "mode": DEFAULT_MODE, "c1": "DE", "c2": "BH-C1", "c3": "BH", "c4": "WIN", "seed": DEFAULT_SEED}
PRESETS = {
    "Open mit 32 Spielern": dict(_BASE),
    "Vereinsturnier": {**_BASE, "n": 16, "rounds": 5},
    "Viele Rücktritte": {**_BASE, "withdraw_on": True, "withdraw": 0.3, "c1": "BH", "c2": EMPTY, "c3": EMPTY, "c4": EMPTY, "mode": "ignore"},
    "Ungerade Zahl mit Freilosen": {**_BASE, "n": 31, "c1": "BH", "c2": EMPTY, "c3": EMPTY, "c4": EMPTY, "mode": "ignore"},
    "Kippbares Turnier": {**_BASE, "seed": 23},
}
PRESET_HELP = {
    "Open mit 32 Spielern": "32 Spieler, 7 Runden, 20 % Remis: Direktvergleich, dann Buchholz ohne den schlechtesten Gegner, dann Buchholz, dann Siege.",
    "Vereinsturnier": "16 Spieler, 5 Runden: wenig Information, die Kriterien trennen kaum besser als der Zufall.",
    "Viele Rücktritte": "30 % der Spieler scheiden vorzeitig aus, Buchholz ohne FIDE-Regel für nicht gespielte Runden: die Gegner zählen mit weniger Partien.",
    "Ungerade Zahl mit Freilosen": "31 Spieler: jede Runde bekommt einer ein Freilos; Buchholz ignoriert es und benachteiligt die Inhaber.",
    "Kippbares Turnier": "Ein Turnier, in dem die Umkehr einer Partie ohne Bedeutung für die Spitze den Sieger ändert (unten im Abschnitt zur Umkehr ausprobieren).",
}
