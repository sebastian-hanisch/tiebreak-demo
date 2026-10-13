# Tie-Breaker im Schweizer System – wer entscheidet bei Punktgleichheit? – Streamlit-Demo

Zusatzstück der Linie **Turnierplanung** (Konzepte-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“), hinter dem **Schweizer System**
(`schweizer-system-demo`): Das Stück dort paart die Runden, dieses hier fragt, **wer bei Punktgleichheit vorn steht**. Die Demo spielt Turniere mit der **echten
FIDE-Dutch-Engine** des Schwesterstücks (sieben Module, wortgleich übernommen), rechnet 18 Kriterien nach **FIDE C.07** und misst sie gegen die wahre Stärke, die in der
Simulation bekannt ist. Alles ist simuliert; es gibt keinen echten Datensatz.

## Warum dieses Problem

Nach sieben Runden mit 32 Spielern liegen mehrere Spieler bei gleichen Punkten, und das Reglement muss trotzdem eine Reihenfolge liefern. Die üblichen Antworten (Buchholz,
Sonneborn-Berger, Direktvergleich, Fortschrittswertung) werden in der Praxis als „stärkeres Gegnerfeld“ oder „bessere Ergebnisse“ erklärt. Die Frage hier ist nüchterner:
**Wie oft steht der wirklich Stärkere vorn, wie leicht kippt der Sieger durch eine Partie, die ihn nichts angeht, und was machen Freilose und Rücktritte mit der Rechnung?**

## Kernfrage

**Alle Rechenkriterien trennen die Punktgleichen nur wenig besser als der Zufall (49 bis 63 % richtig bei 50 % für das Los); ein einziger Stichkampf trifft 69 %.** Im
FIDE-Dutch-Turnier mit 32 Spielern, 7 Runden und 20 % Remis trifft die **Fortschrittswertung 63 %** und ist durch Partien Dritter **nicht kippbar**; Buchholz und seine Varianten
treffen 58 bis 60 %, sind aber in 19 bis 32 % der Turniere mit Gleichstand um Platz 1 durch **eine** irrelevante Partie der letzten Runde kippbar (Sonneborn-Berger 39 %).
Der **Direktvergleich** nach FIDE Artikel 6 trennt im Schweizer System nur 1,5 % der Punktgleichen (329 von 22 125 Paaren). **Freilose** und **Rücktritte** verzerren die Buchholz-Familie, je nachdem, wie
man die nicht gespielten Runden rechnet; die **Fortschrittswertung bleibt unverzerrt**. **Welches Kriterium „das beste“ ist, hängt am Zweck**; das Stück endet in einer
Empfehlung nach Zweck.

## Modell

- **Turnier:** FIDE Dutch System (`ss_engine.pair_round`, wortgleich aus `schweizer-system-demo`). Stärken aus `turnier_generator.make_strengths` (Abstand 0,12), zufällig verteilt;
  die Startrangliste ist Stärke + Rauschen (Rang 1 = höchste Startwertung). Ausgang: Remis mit Wahrscheinlichkeit d, sonst Sieg des Weißen mit Wahrscheinlichkeit
  (1 − d)·σ(Stärkedifferenz). Rücktritte: ein Spieler tritt vor einer Runde zwischen 3 und der vorletzten zurück (`absent` der Engine) und bleibt mit seinem Stand in der Tabelle. Findet die Engine in einer Runde keine Paarung ohne Wiederholung (kleines Feld, viele Runden oder Rücktritte), **endet das
  Turnier früher** (`Tournament.rounds` ist die Zahl der gespielten Runden), wie ein echtes Turnier; die App weist darauf hin.
- **Kriterien (FIDE C.07):** Buchholz BH (Art. 8 Abs. 1) mit Cut-1, Cut-2, Median-1, Median-2 (Art. 14), Mittlerer Buchholz der Gegner AOB (8.2), Sonneborn-Berger SB (9.1),
  Direktvergleich DE (Art. 6), Fortschrittswertung PS (7.5), dazu die Fortschrittswertungen der Gegner (älterer Brauch, ohne FIDE-Kürzel), Siege WIN (7.1, zählt Freilose) und WON
  (7.2, nur am Brett), Siege mit Schwarz BWG (7.4), Partien mit Schwarz BPG (7.3), gespielte Runden REP (7.6), mittlere Gegnerwertung ARO (10.1), Leistungswertung TPR (10.2, hier
  logistisch statt nach der FIDE-Tabelle) und die Startwertung RTNG (10.6). Referenzen: der **Stichkampf** (eine Partie unter den Punktgleichen) und das **Los**.
- **Kaskade (Art. 4 Abs. 2):** Für jede Untergruppe, die ein Kriterium nicht trennt, gilt das nächste; am Ende entscheidet das Los.
- **Direktvergleich (Art. 6):** Die Summe der Ergebnisse gegeneinander (mehrfache Treffen als Mittel). Haben alle einander gespielt, ordnet sie die Gruppe; sonst steht im
  Schweizer System nur ein Spieler vorn, der es **unabhängig vom Ausgang der fehlenden Partien** ist; danach gilt Artikel 6 für den Rest erneut.
- **Nicht gespielte Runden (Art. 16):** Wählbar zwischen *ignorieren*, der Fassung *08/2024* und der Fassung *ab 03/2026*. Für die Gegner zählt eine Runde nach dem Rücktritt als
  Remis; für die eigenen Kriterien gilt ein Dummy-Gegner mit der eigenen Punktzahl, **ab 03/2026 höchstens 0,5 · Rundenzahl** (16.4.2); beim Streichen wird zuerst der kleinste
  Beitrag einer freiwillig nicht gespielten Runde gestrichen (16.5).
- **Maße:** *Auflösung* (Anteil der punktgleichen Paare, die ein Kriterium trennt), *Treffer* (Anteil der getrennten Paare, bei denen der Stärkere vorn steht), *Erwartung*
  (mittlere σ der Stärkedifferenz des Vorderen), *Sieger* und *Podium* richtig, *τ* des Endstandes gegen die Stärke, *Kippen* (Turniere mit Gleichstand um Platz 1, in denen die
  Umkehr **einer** Partie der letzten Runde, an der niemand beteiligt ist, der die Spitze erreichen könnte, den Sieger ändert; beide Beteiligte mindestens 1,5 Punkte dahinter) und
  *Freilos-Verzerrung* (bei Paaren mit genau einem Freilos-Inhaber: Anteil „Inhaber vorn“ minus Anteil „Inhaber ist der Stärkere“).
- Alle Formeln stehen im 📐-Expander der App.

## Methodik

- **Experimente** über **feste, vorberechnete Turniere** (`data/tournaments.json.gz`, 1140 Turniere in 12 Mengen, rund 0,7 MB): die Engine braucht 0,8 s je Turnier mit 32 Spielern
  und 7 Runden, über 1000 Turniere wären live nicht tragbar. Die Datei trägt den Fingerabdruck der Engine; `tests/test_data.py` erzeugt eine Stichprobe frisch und vergleicht
  Seed für Seed. Neu erzeugen: `python tools/build_tournaments.py`.
- **Hauptmenge:** 400 Turniere mit 32 Spielern, 7 Runden, 20 % Remis, Rauschen 0,4; Gleichstand um Platz 1 in **125** davon (31 %). Weitere Mengen: Rauschen 0 / 1 / 2, Remis 0 / 40 %,
  Rücktritte 15 / 30 %, 16 Spieler mit 5 Runden, 32 mit 5 und 9 Runden, 31 Spieler (Freilose).
- **Zufall:** `turnier_generator.py` mit SplitMix64-Strom (wortgleich mit den Repos der Linie); Paarung durch die Engine (deterministisch).
- Das gezeigte Turnier der App wird **live** mit der Engine gespielt; ein Regler ändert dort Kaskade, Behandlung und Turnier, nicht die Experimente.

## Befunde (gemessen, keine Behauptungen)

Hauptmenge, Behandlung nicht gespielter Runden nach FIDE ab 03/2026 (ohne Freilose und Rücktritte ändert sie nichts).

| Kriterium | trennt | Treffer | Erwartung | kippbar (Turniere / Umkehrungen) | Sieger richtig | τ |
|---|---|---|---|---|---|---|
| Buchholz (BH) | 95 % | **59,5 %** | 0,552 | **32 % / 5,7 %** | 22 % | 0,592 |
| BH Cut-1 | 95 % | 59,0 % | 0,550 | 29 % / 4,2 % | 23 % | 0,591 |
| BH Cut-2 | 94 % | 58,9 % | 0,550 | 19 % / 2,6 % | 23 % | 0,590 |
| BH Median-1 | 94 % | 58,8 % | 0,550 | 28 % / 4,0 % | 23 % | 0,590 |
| BH Median-2 | 90 % | 58,5 % | 0,548 | 23 % / 3,3 % | 23 % | 0,589 |
| Mittlerer Buchholz der Gegner (AOB) | 98 % | 58,5 % | 0,547 | **32 % / 7,2 %** | 22 % | 0,591 |
| Sonneborn-Berger (SB) | 95 % | 58,2 % | 0,544 | **39 % / 7,2 %** | 22 % | 0,590 |
| Direktvergleich (DE) | **1,5 %** | 53,2 % (auf 329 Paaren) | 0,519 | 0 % | 22 % | 0,574 |
| **Fortschritt (PS)** | 94 % | **63,2 %** | 0,573 | **0 % / 0 %** | 21 % | 0,599 |
| Fortschrittswertungen der Gegner | 99 % | 60,9 % | 0,559 | 9 % / 1,6 % | 22 % | 0,596 |
| Siege (WIN) / am Brett (WON) | 46 % | 49,2 % | 0,497 | 0 % | 20 % | 0,572 |
| Siege mit Schwarz (BWG) | 63 % | 50,3 % | 0,501 | 0 % | 19 % | 0,573 |
| Partien mit Schwarz (BPG) | 51 % | 49,9 % | 0,499 | 0 % | 20 % | 0,572 |
| Mittlere Gegnerwertung (ARO) / Leistungswertung (TPR) | 100 % | 52,3 % | 0,511 | 0 % | 22 % | 0,577 |
| Startwertung (RTNG, Rauschen 0,4) | 100 % | **85,9 %** | 0,669 | 0 % | 25 % | 0,652 |
| Stichkampf (eine Partie, Referenz) | 100 % | **69,3 %** | 0,693 | – | 22 % | 0,603 |
| Los (Referenz) | 0 % | – | – | – | 20 % | 0,573 |

Tests: `test_the_hit_rates_of_experiment_1`, `test_the_resolution_of_experiment_1`, `test_the_flip_rates_of_experiment_2`, `test_the_winner_is_rarely_the_strongest_whatever_the_criterion`.

| Frage | Befund | Test |
|---|---|---|
| Wer ist am Ende der wahre Stärkste? | **Der Sieger ist in 19 bis 25 % der Turniere der wahre Stärkste, egal welches Kriterium;** das Podium (Plätze 1 bis 3 als Menge) in höchstens 6 %. Tie-Breaker ordnen innerhalb der Punktgruppen, sie retten die Stärkeordnung eines kurzen Turniers nicht. | `test_the_winner_is_rarely_the_strongest_whatever_the_criterion` |
| Direktvergleich nach Artikel 6 | Trennt **1,5 %** der punktgleichen Paare (329 von 22 125): Je größer die Gruppe, desto seltener haben alle einander gespielt, und ein Spieler steht nur vorn, wenn er es unabhängig vom Ausgang der fehlenden Partien ist: **Zweiergruppen 32 %, Dreiergruppen 5 %, Vierergruppen 0,2 %, ab fünf Spielern nie** (Gruppen der Hauptmenge: 715 mit zwei, 615 mit drei, 542 mit vier, 1054 mit fünf und mehr Spielern). | `test_the_resolution_of_experiment_1` |
| Kaskaden (trennt ≥ 97 %) | DE → BH-C1 → BH → WIN: Treffer 58,6 %, 16 % kippbar; BH-C1 → BH → SB → DE: 58,7 % / 31 %; **PS → BH-C1 → SB: 62,3 % / 4 %**; WIN → DE → BH: 54,7 % / 14 %; **DE → PS → BH-C1: 62,3 % / 4 %**; AOB → BH → SB: 58,5 % / 32 %; BH-C1 → RTNG: 60,4 % / 29 %. | `test_the_cascades` |
| Rücktritte 0 / 15 / 30 %, Runden ignoriert | Buchholz 59,5 / 54,5 / **45,2 %**; Cut-1 59,0 / 54,4 / 45,6 %. | `test_withdrawals_hurt_buchholz_and_help_sonneborn_berger_and_progressive` |
| dasselbe nach FIDE Artikel 16 | Buchholz 59,5 / 58,4 / **54,2 %**; Cut-1 (ab 03/2026) 52,2 % bei 30 %; AOB 54,9 %. **Sonneborn-Berger steigt (58,2 / 62,4 / 64,1 %), der Fortschritt auch (63,2 / 70,2 / 71,1 %).** Die Regel hebt Buchholz, beseitigt den Einbruch aber nicht. | dto. |
| Fassung 08/2024 gegen ab 03/2026 | Der Deckel des Dummy-Gegners (0,5 · Rundenzahl) ändert die Trefferquoten bei Rücktritten um höchstens 0,1 Punkte und die Freilos-Verzerrung um höchstens 1 Prozentpunkt. | `test_the_two_fide_versions_hardly_differ_for_withdrawals`, `test_the_two_fide_versions_differ_by_at_most_one_point_in_the_bye_bias` |
| Freilose (31 Spieler), ignoriert | Verzerrung zugunsten des Inhabers: Buchholz **−13**, Cut-1 −15, Sonneborn-Berger −19 Prozentpunkte; AOB +28. | `test_bye_bias` |
| Freilose nach FIDE ab 03/2026 | Buchholz **+8**, Cut-1 +6, Sonneborn-Berger **+16**, AOB +21: Die Regel dreht die Benachteiligung in eine Bevorzugung. **Fortschritt 0**, Leistungswertung −3, Startwertung −1. **WIN (zählt das Freilos als Sieg): +45; WON: −17.** | dto. |
| Rauschen der Startwertung 0 / 0,4 / 1 / 2 | Startwertung 100 / 86 / 70 / 61 %; Fortschritt 66 / 63 / 61 / 58 %; Buchholz Cut-1 61 / 59 / 61 / 60 %. | `test_noise` |
| Remis 0 / 20 / 40 % | Buchholz 65,4 / 59,5 / 57,2 %; Fortschritt 70 / 63 / 62 %. Siege trennen ohne Remis nichts, bei 20 % 46 %, bei 40 % 54 % der Paare. | `test_draws` |
| Feld und Runden (16/5, 32/5, 32/7, 32/9) | Buchholz 54,2 / 59,2 / 59,5 / 64,7 %; Fortschritt 55 / 64 / 63 / 65 %; Stichkampf 64 / 70 / 69 / 68 %. Kleine Felder tragen kaum Information. | `test_sizes` |

## Befunde und Korrekturen gegenüber dem Plan

- **Vereinfachte Paarung kehrte das Ergebnis um (Phase 0):** Mit einer Monrad-Paarung lag der Fortschritt unter dem Zufall (45 %); mit der FIDE-Dutch-Engine ist er das beste
  Rechenkriterium (63 %). Die Tie-Breaker hängen an der **Paarungsregel**, nicht nur an den Punktgruppen. Deshalb übernimmt dieses Stück die echte Engine.
- **Der Direktvergleich war in der Vorab-Messreihe zu großzügig:** Als „Minitabelle“ (Summe der Ergebnisse gegen alle Punktgleichen, auch bei fehlenden Partien) trennte er 69 %
  der Paare mit 57 % Treffern. Nach Artikel 6 (Gruppe vollständig gespielt oder unabhängig vom Ausgang der fehlenden Partien vorn) trennt er **1,5 %**. Die Messung folgt dem
  Wortlaut.
- **AOB ist ein Mittelwert:** Die Vorab-Messreihe summierte die Buchholz-Werte der Gegner (Freilos-Verzerrung −20 Prozentpunkte); FIDE Art. 8 Abs. 2 verlangt den **Durchschnitt** der
  Gegner am Brett (jetzt +28 ignoriert, +21 nach Artikel 16).
- **WIN zählt Freilose als Siege** (7.1); WON nur Partien am Brett (7.2). Die Vorab-Messreihe zählte nur Partien am Brett; beide stehen jetzt getrennt, mit entgegengesetzter
  Freilos-Verzerrung (+45 und −17).
- **Die Fassung ab 03/2026 deckelt den Dummy** auf 0,5 · Rundenzahl (16.4.2); die Fassung 08/2024 kennt den Deckel nicht. Gelesen wurde das Handbuch-Webportal; der
  Unterschied ist in den Messungen klein (siehe oben).
- **Kippen:** In der Vorab-Messreihe 19 % der Turniere für Buchholz bei 42 Turnieren mit Gleichstand um Platz 1; mit 400 Turnieren (125 mit Gleichstand) 32 %. Die Unsicherheit
  einer Quote aus 125 Turnieren liegt bei rund ±4 Prozentpunkten; die Quote je Umkehrung (1361 Fälle) ist stabiler.
- **Fortschrittswerte der Gegner sind kippbar** (9 % der Turniere): Eine Umkehr ändert die Fortschrittswertung der Beteiligten und damit die Summe ihrer Gegner. Die eigene
  Fortschrittswertung bleibt unberührt.
- **Abbruch bei kleinem Feld (beim Bau gefunden):** Mit 8 Spielern gibt es höchstens 7 Runden ohne Wiederholung; auch größere Felder mit vielen Runden und Rücktritten kommen an
  den Punkt, an dem die Engine keine zulässige Paarung mehr findet. Zuerst stürzte die App an dieser Stelle ab; jetzt endet das Turnier früh, und die App sagt es
  (`test_a_tournament_that_cannot_be_paired_to_the_end_stops_early_and_stays_consistent`). Die festen Turniere der Experimente sind alle vollständig.
- **Standard-Seed:** 29 (drei Spieler an der Spitze, Buchholz Cut-1 entscheidet, Treffer 61 % gegen den Mittelwert 59 %, nicht kippbar). Seed 23 ist ein kippbares Turnier
  (Preset „Kippbares Turnier“).

## Abgrenzung

- **`schweizer-system-demo`** (Turnierplanung): der **Paarungsalgorithmus** (FIDE Dutch, C1 bis C21, geprüft gegen bbpPairings); dieses Stück setzt hinter der Paarung an und
  übernimmt die Engine, ohne den bbpPairings-treuen Modus (networkx).
- **`siegtabelle-demo`** (Wurzel der Ranking-Linie): Gleichstand in der Tabelle nach Siegen (Siegquote → Direktvergleich → Los), ohne Paarung.
- **`elo-demo`**, **`bradley-terry-demo`**: Die Alternative zu einem Tie-Breaker ist eine **Wertung**, die die Gegnerstärke einrechnet; hier bleibt es bei Kriterien am Endstand.

## Ehrliche Grenzen

- **Ein Stärkenmodell, ein Remismodell:** logistisch, gleichabständig, Remisquote unabhängig von der Stärke; reale Turniere mit Wertungsunterschieden von 400 Punkten verhalten
  sich anders.
- **Treffer ist eine Aussage über die Stärke, nicht über Verdienst:** Das Reglement verlangt nicht, dass der Stärkere vorn steht; die Stärke ist nur der Maßstab, den eine
  Simulation kennt.
- **Artikel 16 nur teilweise nachgebaut:** Freilos des Paarungsprogramms und Runden nach dem Rücktritt; keine „requested byes“, keine Forfaits. Rücktritte sind gleichverteilt.
- **Kippen ist eine Möglichkeit, keine Absicht;** die Quote je Turnier beruht auf 125 Turnieren mit Gleichstand um Platz 1.
- **Der Direktvergleich hat nach Artikel 6 in dieser Konfiguration kaum Wirkung;** in Turnieren mit weniger Teilnehmern je Punktgruppe oder mehr Runden greift er öfter.
- **Die Startwertung ist kein Leistungsmaß:** ihr Treffer hängt allein an der Güte der Setzliste.
- **Feste Turniere:** Die Experimente rechnen auf vorberechneten Turnieren; einzelne Zellen (Direktvergleich bei kleinen Feldern: 39 bis 82 %) beruhen auf wenigen Paaren und
  sind nicht zu deuten.
- **Alles simuliert**, ein Generator, Felder bis 32.

## Quellen

- FIDE Handbook, C.07 *Play-Off and Tie-Break Regulations*, Fassungen „effective from 1 August 2024 till 28 February 2026“ (Council 29.07.2024) und „from 1 March 2026“
  (Council 02.02.2026), handbook.fide.com: Artikel 4 (Anwendung der Liste), 6 (Direktvergleich), 7 (Siege, Schwarzpartien, Fortschritt, REP), 8 (Buchholz, AOB), 9 (Sonneborn-Berger),
  10 (ARO, TPR), 14 (Modifikatoren) und 16 (nicht gespielte Runden) über das Webportal gelesen, in Auszügen.
- Das Buchholz-System ist nach Bruno Buchholz benannt (Jahr und Fundstelle nicht geprüft); Sonneborn-Berger nach den Genannten (Fundstelle nicht geprüft).
- Steele, G. L., Lea, D., Flood, C. H. (2014): Fast splittable pseudorandom number generators. *OOPSLA 2014*, 453–472 (Zufallsstrom des Generators).

## Tests

339 Tests, rund zwei Minuten (der erste Seitenaufruf rechnet die Experimente): Einheiten gegen die von Hand gerechneten Mini-Turniere (`test_criteria.py`: sechs Spieler,
fünf mit Freilosen, vier mit Rücktritt), Turnier und Datei (`test_tournament.py`, `test_data.py`), die sieben **Engine-Module mit ihren Tests** aus `schweizer-system-demo`
(`test_engine.py`, `test_blossom.py`, `test_bracket.py`, `test_colour.py`, `test_compat.py`), Generator (`test_generator.py`, wortgleich), **Orakel**
(`test_oracle_tiebreak.py`: Kriterien rundenweise neu gerechnet in allen drei Behandlungen, Kaskade gegen einen lexikografischen Schlüssel, **Direktvergleich gegen die
Aufzählung aller Ausgänge der fehlenden Partien** auf 250 Zufallsgruppen, Umkehr einer Partie gegen die betroffenen Nachbarn), Maße und Verdikte (`test_evaluation.py`,
`test_verdict_boundaries.py`: Schwellen mit künstlichen Messwerten), alle Zahlen dieses README (`test_claims.py`), Presets, ausblendbare Regler
(`test_hidden_widget_state.py`), Umkehr-Auswahl (`test_flip_selection.py`), PDF, Laufzeit-Importe und AppTest-Rauchtests.

**Mutationstest** (`tools/oracle_mutation.py` der Website, auf die vier `tbk_`-Module eingeschränkt, weil die Engine eigene Tests hat): 60 gezogene Mutanten nur gegen die
Orakel-Tests: 15 getötet, 45 überlebt (Rate 25 %). Daraufhin wurden **alle 305 Mutationsstellen** der vier Module einzeln gegen die Einheitentests (ohne App-Tests) geprüft:
277 getötet, 28 überlebt. Von den 28 waren **13 echte Lücken** in den Verdikten und der Empfehlungstabelle (Schwellen bei Auflösung 0,3 und 200 Paaren, Behandlung der
Rücktritts- und Freilos-Zeilen, Wortlaut „der wahre Stärkste“) und **15 äquivalent** (Fallunterscheidungen für Einzelgruppen, die die Rekursion ohnehin liefert; `u < p` gegen
`u <= p` bei stetigen Zufallszahlen; die Spiegelsymmetrie der Partienliste; `v > 0` nach der Prüfung `v == 0`). Die Lücken sind mit Grenzfall-Tests geschlossen und einzeln
erneut getötet (alle 70 Mutanten von `tbk_verdicts.py`). Schon vorher gefunden und geschlossen: die Erwartung und die Stichkampf-Reihenfolge ohne Prüfwert, der Rücktritt
der letzten Startnummer, der Beste an den Enden der Startrangliste (Sieger und Podium), die Zählung der Umkehrungen ohne Umkehr-Lauf und das Vorzeichen bei ±1. Entfernt:
zwei ungenutzte Funktionen, redundante Bedingungen und ein überflüssiges Epsilon im Direktvergleich.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche |
| `turnier_generator.py` | gemeinsamer Generator (wortgleich in allen Repos der Linie; liefert die Anfangsstärken) |
| `ss_model.py`, `ss_compat.py`, `ss_colour.py`, `ss_quality.py`, `ss_blossom.py`, `ss_bracket.py`, `ss_engine.py` | FIDE-Dutch-Engine (wortgleich mit `schweizer-system-demo`) |
| `tbk_tournament.py` | Turnier mit der Engine: Stärken, Setzliste, Ausgänge, Rücktritte |
| `tbk_criteria.py` | Kriterien, Direktvergleich (Art. 6), Art. 16, Kaskade, Umkehr einer Partie |
| `tbk_evaluation.py` | Maße, Analyse des gezeigten Turniers, sieben Experimente |
| `tbk_verdicts.py` | Verdikte und Empfehlung nach Zweck (live aus den Messwerten) |
| `tbk_data.py` | vorberechnete Turniere: Laden, Kodieren, Fingerabdruck der Engine |
| `tbk_scenario.py` | Reglerwerte (`Settings`) und das Turnier |
| `tbk_presets.py`, `tbk_constants.py` | Permalink, Presets, ausblendbarer Regler, Grenzen |
| `tbk_visualization.py`, `tbk_pdf_export.py` | Plotly-Abbildungen, PDF-Export |
| `data/tournaments.json.gz` | 1140 vorberechnete Turniere |
| `tools/build_tournaments.py` | erzeugt die Datei neu |
| `tests/` | Einheiten-, Orakel-, Claims-, Engine- und App-Tests |

## Bewusst nicht umgesetzt

- **Koya** (nur Rundenturnier), **Fore Buchholz** (nur vor der letzten Runde), **PTP, APRO, APPO** (brauchen echte Wertungen), **Armageddon** (Entscheidung als Format).
- **Mannschaftsturniere** (Art. 12, 13) und **Rundenturniere** (Buchholz und AOB sind dort nicht vorgesehen).
- **Requested byes und Forfaits** nach Artikel 16 Abs. 2.
- **Eine Wertung statt eines Kriteriums** (Elo, Bradley-Terry): eigene Stücke der Ranking-Linie.

## Lokal ausführen

```bash
pip install -r requirements.txt
streamlit run app.py
```

Tests: `pip install -r requirements-dev.txt` und `python -m pytest tests -q`.

Gebaut mit Streamlit, Plotly, numpy, pandas und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Turnierplanung: 7 Wege zum Turnierplan](https://sebastianhanisch.net/konzepte-turnierplanung.html).
