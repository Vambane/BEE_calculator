"""PDF gap report (WeasyPrint)."""

from bee import CompanyProfile, ScoreInput, calculate
from bee.registry import get_sector
from bee.report import render_pdf


def test_render_pdf_generic_contains_out_of_and_notes(tmp_path):
    cfg = get_sector("generic")
    from bee import EnterpriseSize as E

    card = cfg.card(E.GENERIC, None)
    r = calculate(
        ScoreInput(
            CompanyProfile(100_000_000, 40),
            points={
                "ownership": {"total": 15, "net_value": 5},
                "management": {"main": 10},
                "skills": {"main": 12},
                "esd": {"pp": 20, "sd": 5, "ed": 3},
                "sed": {"main": 3},
            },
        )
    )
    pdf = render_pdf(r, card, {}, "Generic Large", cfg, company_name="Test Co", example=True)
    assert pdf[:4] == b"%PDF"
    path = tmp_path / "out.pdf"
    path.write_bytes(pdf)
    # text extraction via pypdf if available, else size smoke
    try:
        from pypdf import PdfReader

        text = "\n".join(p.extract_text() or "" for p in PdfReader(str(path)).pages)
        assert "out of" in text
        assert "Test Co" in text
        assert "Interpretation notes" in text or "Assumptions" in text
    except ImportError:
        assert len(pdf) > 5_000


def test_render_pdf_construction_qse_out_of_110():
    cfg = get_sector("construction")
    from bee import EnterpriseSize as E

    card = cfg.card(E.QSE, "contractor")
    r = calculate(
        ScoreInput(
            CompanyProfile(20_000_000, 30, sector="construction", variant="contractor"),
            points={"ownership": {"main": 20, "net_value": 4}, "skills": {"main": 12}},
        )
    )
    pdf = render_pdf(r, card, {}, "Construction QSE", cfg, company_name="Builder")
    assert pdf[:4] == b"%PDF"
    assert card.display_max() == 110
