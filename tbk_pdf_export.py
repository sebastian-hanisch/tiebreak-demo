"""PDF-Export des gezeigten Turniers und der Kaskade (fpdf2, Kernschrift: nur Zeichen aus Latin-1, daher „Tau“ statt τ und „->“ statt →)."""

from fpdf import FPDF

import tbk_constants as C
import tbk_criteria as K
import tbk_evaluation as ev
import tbk_verdicts as vd


def _latin(text: str) -> str:
    for old, new in (("–", "-"), ("—", "-"), ("τ", "Tau"), ("σ", "sigma"), ("≈", "ca."), ("≥", ">="), ("≤", "<="), ("→", "->"), ("**", ""), ("€", "EUR"), ("−", "-")):
        text = text.replace(old, new)
    return text.encode("latin-1", "replace").decode("latin-1")


def build_pdf(a: ev.Analysis) -> bytes:
    s, t = a.settings, a.tournament
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", "B", 15)
    pdf.multi_cell(0, 8, _latin("Tie-Breaker im Schweizer System"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(2)
    wd = f", Rücktritte: {ev.pct(s.withdraw)} %" if s.withdraw > 0 else ""
    pdf.multi_cell(0, 5.5, _latin(f"Spieler: {s.n}, Runden: {s.rounds}, Remis: {ev.pct(s.draw)} %, Rauschen der Startwertung: {ev.de(s.noise)}{wd}, Seed: {s.seed}."), new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 5.5, _latin(f"Kaskade: {' -> '.join(s.cascade)} (dann Los). Nicht gespielte Runden: {C.MODES[s.mode]}."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    _level, text = vd.verdict_analysis(a)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Kernaussage", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5.5, _latin(text), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    cols = list(dict.fromkeys(s.cascade))
    headers = ("Platz", "Nr.", "Punkte", "getrennt durch") + tuple(cols) + ("wahrer Rang",)
    widths = [14, 12, 16, 30] + [20] * len(cols) + [24]
    pdf.set_font("Helvetica", "B", 9)
    for h, w in zip(headers, widths):
        pdf.cell(w, 6, _latin(h), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    true_rank = {r: i + 1 for i, r in enumerate(sorted(range(1, t.n + 1), key=lambda q: -t.strength[q - 1]))}
    for place, (nr, why) in enumerate(a.standing, start=1):
        cells = [str(place), str(nr), ev.de(a.score[nr - 1]), {"": "", "LOS": "Los"}.get(why, why)]
        for c in cols:
            cells.append("" if c == "DE" else ev.de(a.values[c][nr - 1], 2))
        cells.append(str(true_rank[nr]))
        for value, w in zip(cells, widths):
            pdf.cell(w, 6, _latin(value), border=1)
        pdf.ln()
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4.5, _latin(
        "Alles ist simuliert (Stärken aus dem Generator der Ranking-Linie, Paarung mit dem FIDE-Dutch-System); die wahre Stärke ist nur in der Simulation bekannt. "
        "Quelle: Demo von Sebastian Hanisch, sebastianhanisch.net."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
