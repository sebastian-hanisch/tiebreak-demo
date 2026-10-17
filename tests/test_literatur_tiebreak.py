"""Literatur-Referenzwerte für die Kriterien nach FIDE C.07 (ORACLE-PLAYBOOK §5.1).

Quelle aller Zahlen (am 2026-10-17 abgerufen und gelesen):

  Mario Held (IA), "Exercises in Tie-Breaking", FIDE Arbiters' Commission, Rev. 2403220900, C.07-2023,
  https://arbiters.fide.com/wp-content/uploads/2024/04/C.07-2023-Tiebreak-exercises.pdf
  (PDF abgerufen, Text extrahiert und gelesen; das Heft rechnet Aufgaben mit Lösungen zu den Kriterien der FIDE-Regeln C.07 an einem Swiss-Turnier mit
  16 Spielern und 5 Runden und an einem Rundenturnier mit 6 Spielern).

Verwendete Stellen des Hefts:
  - Abschnitt 2.1 "Swiss individual tournament crosstable": die Kreuztabelle (unten SWISS) mit Wertungszahlen (Elo) und Ergebnissen.
  - Abschnitt 2.2: die Kreuztabelle des Rundenturniers (unten ROUND_ROBIN, in der Schreibweise der "Swiss format"-Tabelle).
  - Abschnitt 3.1, Aufgabe 9 (AOB, mit der Tabelle aller Buchholz-Werte): BH und AOB aller 16 Spieler.
  - Abschnitt 3.2, Aufgaben 5 bis 8: Buchholz Cut-1 einzelner Spieler.
  - Abschnitt 4.1, Aufgabe 12: Sonneborn-Berger aller 16 Spieler; Abschnitt 4.2, Aufgabe 14: Sonneborn-Berger des Rundenturniers.
  - Abschnitt 5.1, Aufgabe 17: ARO aller 16 Spieler (auf ganze Zahlen gerundet).
  - Abschnitt 6, Aufgaben 23 bis 26: Direktvergleich (Swiss, 3,5-Punkte-Gruppe nach fünf Runden; neun Runden: Gruppen mit 6,0, 4,5, 4,0 und 3,0
    Punkten, gegeben als getrennte Kreuztabellen; Rundenturnier).
  - Abschnitt 7, Aufgaben 27 bis 32 und die Vergleichstabelle am Ende des Kapitels: WIN, WON, BPG, BWG und Fortschrittswertung PS aller 16 Spieler.
Die Heft-Fassung ist C.07 von 2023; die Behandlung nicht gespielter Runden stimmt für die hier verglichenen Werte mit Artikel 16 der Fassung 08/2024
(Webportal https://handbook.fide.com/chapter/TieBreakRegulations082024, über WebFetch eingesehen 2026-10-17: 7.1 WIN, 7.2 WON, 7.3 BPG, 7.4 BWG, 7.5 PS, 8.1
BH, 8.2 AOB, 9.1 SB, 14 Modifikatoren, 16.1 bis 16.5) überein; verglichen wird deshalb mit der Behandlung "fide2024" der Demo (die Fassung ab 03/2026
deckelt den Dummy-Gegner, das Heft kennt den Deckel nicht).

Abbildung der Heft-Kreuztabelle auf das Modell der Demo (keine Wertung, nur Übersetzung der Zeichen):
  "+B10" = Sieg mit Schwarz gegen 10; "=W2" = Remis mit Weiß; "-B3" = Niederlage.
  "+BYE" (Freilos der Paarung, PAB) und "=BYE" (Halbpunkt-Bye auf Antrag, HPB): Freilos mit 1 bzw. 0,5 Punkten.
  "+F14" (Sieg durch Forfait) und "-F12" (Niederlage durch Forfait): Freilos-ähnlicher Eintrag mit 1 bzw. 0 Punkten ohne Brett.
  "ZPB" (Null-Punkte-Bye, Paul in Runde 4): Eintrag mit 0 Punkten ohne Brett. "--" (Rücktritt von Nick, Runden 4 und 5): kein Spielbericht.
Die Demo kennt Bye auf Antrag, Forfaits und ZPB nicht als eigene Arten ("keine requested byes, keine Forfaits" in der README); alle drei werden hier als
Freilos-Eintrag abgebildet. Das ist für Kriterien richtig, die die nicht gespielten Runden mit dem eigenen Endstand als Dummy-Gegner bewerten (BH, SB, PS, WIN,
WON, BPG, BWG, AOB, ARO), nicht aber für die Modifikatoren Cut-1 bei freiwillig nicht gespielten Runden (Artikel 16.5) und für GE/REP (Spiele, die man
spielen wollte): dafür werden nur Spieler ohne Bye auf Antrag, Forfait-Niederlage und ZPB verglichen (Begründung in den Tests).
"""

import pytest

import tbk_criteria as K
from tbk_tournament import Game, Tournament

# --- Kreuztabelle des Swiss-Turniers (Heft, Abschnitt 2.1): Nummer -> (Name, Elo, Runde 1 bis 5) -----------------------------------------------------

SWISS = {
    1: ("Alyx", 2200, ["+W9", "=B13", "=W2", "+B15", "=W4"]),
    2: ("Bruno", 2150, ["+B10", "+W7", "=B1", "+W16", "=B3"]),
    3: ("Charline", 2100, ["=W11", "+B6", "+W8", "=B4", "=W2"]),
    4: ("David", 2050, ["+B12", "=BYE", "+W13", "=W3", "=B1"]),
    5: ("Helene", 2000, ["-W13", "-B15", "+W11", "=B7", "+W10"]),
    6: ("Franck", 1950, ["-B14", "-W3", "+BYE", "+W10", "+B8"]),
    7: ("Genevieve", 1900, ["+W15", "-B2", "-B16", "=W5", "-B11"]),
    8: ("Irina", 1850, ["=B16", "+W14", "-B3", "+W13", "-W6"]),
    9: ("Jessica", 1800, ["-B1", "-W10", "=BYE", "-F11", "+BYE"]),
    10: ("Lais", 1750, ["-W2", "+B9", "-W15", "-B6", "-B5"]),
    11: ("Maria", 1700, ["=B3", "-W16", "-B5", "+F9", "+W7"]),
    12: ("Nick", 1650, ["-W4", "+BYE", "+F14", "--", "--"]),
    13: ("Opal", 1600, ["+B5", "=W1", "-B4", "-B8", "-W14"]),
    14: ("Paul", 1550, ["+W6", "-B8", "-F12", "ZPB", "+B13"]),
    15: ("Reine", 1500, ["-B7", "+W5", "+B10", "-W1", "-B16"]),
    16: ("Stephan", 1450, ["=W8", "+B11", "+W7", "-B2", "+W15"]),
}
SWISS_SCORE = {1: 3.5, 2: 4.0, 3: 3.5, 4: 3.5, 5: 2.5, 6: 3.0, 7: 1.5, 8: 2.5, 9: 1.5, 10: 1.0, 11: 2.5, 12: 2.0, 13: 1.5, 14: 2.0, 15: 2.0, 16: 3.5}

# Rundenturnier (Heft, Abschnitt 2.2, Schreibweise der Tabelle "Swiss format"); die Forfait-Partie 5-6 zählt wie eine gespielte
ROUND_ROBIN = {
    1: ("Alyx", 2200, ["=W5", "+W2", "+B3", "-W4", "+B6"]),
    2: ("Bruno", 2150, ["+W6", "-B1", "+W5", "=W3", "+B4"]),
    3: ("Charline", 2100, ["+W4", "+B6", "-W1", "=B2", "+W5"]),
    4: ("David", 2050, ["-B3", "-B5", "=W6", "+B1", "-W2"]),
    5: ("Franck", 1950, ["=B1", "+W4", "-B2", "-W6", "-B3"]),
    6: ("Helene", 2000, ["-B2", "-W3", "=B4", "+B5", "-W1"]),
}
ROUND_ROBIN_SCORE = {1: 3.5, 2: 3.5, 3: 3.5, 4: 1.5, 5: 1.5, 6: 1.5}

SIGN = {"+": 1.0, "=": 0.5, "-": 0.0}


def parse(token, rnd):
    """Zeichen der Heft-Kreuztabelle -> Game der Demo oder None (kein Spielbericht)."""
    if token == "--":
        return None
    if token == "ZPB":
        return Game(0, 0.0, "", True, rnd)
    score = SIGN[token[0]]
    rest = token[1:]
    if rest == "BYE" or rest.startswith("F"):
        return Game(0, score, "", True, rnd)
    return Game(int(rest[1:]), score, rest[0].lower(), False, rnd)


def build(table, rounds):
    n = len(table)
    games = []
    for r in range(1, n + 1):
        gl = [parse(tok, rnd) for rnd, tok in enumerate(table[r][2], start=1)]
        games.append(tuple(g for g in gl if g is not None))
    start = tuple(float(table[r][1]) for r in range(1, n + 1))
    return Tournament(n, rounds, start, start, tuple(games), tuple([0] * n), 0)


@pytest.fixture(scope="module")
def swiss():
    return build(SWISS, 5)


@pytest.fixture(scope="module")
def rr():
    return build(ROUND_ROBIN, 5)


def test_the_transcribed_crosstables_are_consistent_with_the_printed_scores(swiss, rr):
    # Prüfung der Abschrift: Endstände wie im Heft, und jede Brettpartie steht bei beiden Spielern mit entgegengesetztem Ergebnis und Farbe
    for t, scores in ((swiss, SWISS_SCORE), (rr, ROUND_ROBIN_SCORE)):
        assert dict(enumerate(t.score, start=1)) == scores
        for r in range(1, t.n + 1):
            for g in t.games[r - 1]:
                if g.bye:
                    continue
                back = [h for h in t.games[g.opponent - 1] if h.round_no == g.round_no]
                assert len(back) == 1 and back[0].opponent == r
                assert back[0].score == 1.0 - g.score and {g.colour, back[0].colour} == {"w", "b"}
    # die Forfaits stehen ebenfalls paarweise (Runde 3: 12 gewinnt gegen 14; Runde 4: 11 gewinnt gegen 9)
    assert (swiss.games[11][2].score, swiss.games[13][2].score) == (1.0, 0.0)
    assert (swiss.games[10][3].score, swiss.games[8][3].score) == (1.0, 0.0)


# --- Buchholz, AOB, Sonneborn-Berger (Aufgaben 9, 12) -------------------------------------------------------------------------------------------------

BH = {2: 13.0, 3: 15.5, 4: 15.0, 1: 12.5, 16: 12.5, 6: 12.0, 8: 13.5, 11: 13.5, 5: 8.5, 15: 12.0, 12: 11.5, 14: 11.0, 7: 14.5, 13: 14.0, 9: 9.0, 10: 13.0}
AOB = {2: 13.60, 3: 13.40, 4: 13.38, 16: 13.30, 1: 12.60, 6: 13.25, 5: 13.40, 8: 13.00, 11: 12.75, 12: 15.00, 14: 13.17, 15: 12.20, 9: 12.75, 13: 12.10,
       7: 11.90, 10: 10.90}
SB = {2: 9.50, 3: 10.50, 4: 9.75, 1: 8.00, 16: 7.25, 6: 6.50, 11: 5.75, 8: 5.25, 5: 4.25, 14: 4.50, 12: 4.00, 15: 3.50, 13: 4.25, 7: 3.25, 9: 2.25, 10: 1.50}


def test_buchholz_of_all_16_players_matches_the_table_of_exercise_9(swiss):
    v = K.values(swiss, "fide2024")["BH"]
    for r, expected in BH.items():
        assert v[r - 1] == pytest.approx(expected), r


def test_average_buchholz_of_opponents_matches_exercise_9(swiss):
    v = K.values(swiss, "fide2024")["AOB"]
    for r, expected in AOB.items():
        assert v[r - 1] == pytest.approx(expected, abs=0.006), r            # das Heft rundet auf zwei Stellen


def test_sonneborn_berger_of_all_16_players_matches_exercise_12(swiss):
    v = K.values(swiss, "fide2024")["SB"]
    for r, expected in SB.items():
        assert v[r - 1] == pytest.approx(expected), r


def test_sonneborn_berger_of_the_round_robin_matches_exercise_14(rr):
    v = K.values(rr, "ignore")["SB"]
    assert v == pytest.approx([9.25, 6.25, 6.25, 4.25, 3.25, 2.25])


def test_buchholz_of_the_round_robin_is_the_total_minus_own_score(rr):
    # Heft, Abschnitt 3 (Einleitung): im Rundenturnier ist BH = Gesamtpunkte (6 * 5 / 2 = 15) minus eigener Stand
    v = K.values(rr, "ignore")["BH"]
    assert v == pytest.approx([15 - s for s in rr.score])


# --- Buchholz Cut-1 (Aufgaben 5 bis 8) -----------------------------------------------------------------------------------------------------------------

# nur Spieler ohne Bye auf Antrag, Forfait-Niederlage und ZPB (dort schneidet Artikel 16.5 zuerst die freiwillig nicht gespielte Runde, was die Demo
# für diese Arten nicht unterscheidet). Nick (12) hat zwei Runden nach dem Rücktritt, die die Demo als freiwillig nicht gespielt erkennt.
BH_C1 = {5: 7.5, 8: 12.0, 11: 12.0, 7: 12.5, 13: 12.0, 1: 11.0, 3: 13.0, 16: 11.0, 15: 11.0, 12: 9.5}


def test_buchholz_cut_1_of_exercises_5_to_8(swiss):
    v = K.values(swiss, "fide2024")["BH-C1"]
    for r, expected in BH_C1.items():
        assert v[r - 1] == pytest.approx(expected), r


# --- ARO, WIN, WON, BPG, BWG, PS (Aufgaben 17, 27 bis 32 und Vergleichstabelle) ---------------------------------------------------------------------

ARO = {2: 1880, 3: 1940, 4: 1888, 1: 1820, 16: 1820, 6: 1813, 11: 1863, 8: 1730, 5: 1690, 12: 2050, 15: 1860, 14: 1800, 9: 1975, 13: 1930, 7: 1760, 10: 1880}
# Nummer -> (WIN, WON, BPG, BWG, PS)
TABLE = {2: (3, 3, 3, 1, 13.0), 4: (2, 2, 2, 1, 11.5), 1: (2, 2, 2, 1, 11.0), 3: (2, 2, 2, 1, 11.0), 16: (3, 3, 2, 1, 10.5), 6: (3, 2, 2, 1, 6.0),
         8: (2, 2, 2, 0, 8.5), 11: (2, 1, 2, 0, 5.5), 5: (2, 2, 2, 0, 5.0), 12: (2, 0, 0, 0, 7.0), 15: (2, 2, 3, 1, 7.0), 14: (2, 2, 2, 1, 6.0),
         13: (1, 1, 3, 1, 7.0), 7: (1, 1, 3, 0, 6.0), 9: (1, 0, 1, 0, 2.5), 10: (1, 1, 3, 1, 4.0)}


def test_aro_matches_exercise_17(swiss):
    v = K.values(swiss, "fide2024")["ARO"]
    for r, expected in ARO.items():
        assert v[r - 1] == pytest.approx(expected, abs=0.5 + 1e-9), r       # das Heft rundet auf ganze Zahlen (z. B. 1887,5 zu 1888)


def test_wins_games_won_black_games_black_wins_and_progressive_score_match_the_final_table(swiss):
    v = K.values(swiss, "fide2024")
    for r, (win, won, bpg, bwg, ps) in TABLE.items():
        assert (v["WIN"][r - 1], v["WON"][r - 1], v["BPG"][r - 1], v["BWG"][r - 1]) == (win, won, bpg, bwg), r
        assert v["PS"][r - 1] == pytest.approx(ps), r


# --- Direktvergleich (Aufgaben 23 bis 26) -------------------------------------------------------------------------------------------------------------

def games_from_matrix(n, results):
    """Partien aus {(a, b): Punkte von a gegen b} (je Paar einmal); die Runde spielt für den Direktvergleich keine Rolle."""
    gl = [[] for _ in range(n)]
    for k, ((a, b), s) in enumerate(results.items(), start=1):
        gl[a - 1].append(Game(b, s, "w", False, k))
        gl[b - 1].append(Game(a, 1.0 - s, "b", False, k))
    return tuple(tuple(x) for x in gl)


def test_direct_encounter_of_the_round_robin_exercise_26(rr):
    # 3,5-Punkte-Gruppe: Alyx vorn, Bruno und Charline (Remis) bleiben gleich; 1,5-Punkte-Gruppe: Helene (1,5), Franck (1), David (0,5)
    assert K.direct_encounter([1, 2, 3], rr.games) == [[1], [2, 3]]
    assert K.direct_encounter([4, 5, 6], rr.games) == [[6], [5], [4]]


def test_direct_encounter_of_the_3_5_point_group_after_five_rounds_breaks_nothing(swiss):
    # Aufgaben 23 und 24: die Gruppe 1, 3, 4, 16 hat Lücken; Stephan (16) hat gegen keinen von ihnen gespielt
    assert K.direct_encounter([1, 3, 4, 16], swiss.games) == [[1, 3, 4, 16]]


def test_direct_encounter_of_the_four_score_groups_after_nine_rounds_exercise_25():
    n = 16
    # 6,0 Punkte: Alyx (1), Bruno (2), David (4), Franck (6); alle haben gegeneinander gespielt
    g6 = games_from_matrix(n, {(1, 2): .5, (1, 4): .5, (1, 6): .5, (2, 4): .5, (2, 6): 0.0, (4, 6): .5})
    assert K.direct_encounter([1, 2, 4, 6], g6) == [[6], [1, 4], [2]]
    # 4,5 Punkte: Genevieve (7), Irina (8), Stephan (16); Genevieve gegen Irina fehlt
    g45 = games_from_matrix(n, {(7, 16): 0.0, (8, 16): .5})
    assert K.direct_encounter([7, 8, 16], g45) == [[7, 8, 16]]
    # 4,0 Punkte: Helene (5), Lais (10), Paul (14), Reine (15); Lücken Lais-Paul, Lais-... (laut Kreuztabelle) und Paul-Reine
    g4 = games_from_matrix(n, {(5, 10): 1.0, (5, 14): 1.0, (5, 15): 0.0, (10, 15): 0.0})
    assert K.direct_encounter([5, 10, 14, 15], g4) == [[5, 10, 14, 15]]
    # 3,0 Punkte: Jessica (9) und Nick (12) haben remis gespielt
    g3 = games_from_matrix(n, {(9, 12): .5})
    assert K.direct_encounter([9, 12], g3) == [[9, 12]]
