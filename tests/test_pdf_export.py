"""PDF-Export: erzeugt für jede Konfiguration gültige PDF-Bytes; der Latin-1-Filter ersetzt alle Zeichen außerhalb der Kernschrift."""

import tbk_evaluation as ev
import tbk_pdf_export as X
from tbk_scenario import Settings


def test_pdf_is_built_for_several_configurations():
    for s in (Settings(), Settings(n=16, rounds=5, seed=3), Settings(n=31, withdraw=0.3, mode="ignore", cascade=("BH",), seed=4),
              Settings(n=8, rounds=3, cascade=("DE", "PS", "SB", "WIN"), seed=9)):
        data = X.build_pdf(ev.analyse(s))
        assert data[:5] == b"%PDF-" and len(data) > 1500


def test_latin_filter_replaces_greek_and_math_symbols():
    out = X._latin("τ ≈ 0,5; σ → fett **x** € −")
    assert out == "Tau ca. 0,5; sigma -> fett x EUR -"
    assert out.encode("latin-1")
