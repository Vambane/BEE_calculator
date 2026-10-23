# Streamlit B-BBEE Calculator

Streamlit app to estimate a South African B-BBEE score and recognition level on the
Generic (Amended Codes 2019), QSE (Code Series 600), and loaded sector scorecards.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## What it does
- **Profile:** company name, sector code, revenue (for EME/QSE/Generic sizing), Black ownership %, financial bases (NPAT, leviable payroll, TMPS, headcount), optional YES Initiative, and an opt-in to score on the full scorecard when a deemed (affidavit) level would otherwise apply.
- **Element steps (Indicators by default on Ownership and Management Control):** enter each scorecard indicator — including Black women / Black female lines — or switch to pre-calculated points from a verification agency. Net Value stays agency-entered (Annexe 100(E) is not calculated here).
- **Results:** recognition level, total points, distance to next level, and a **Black women / Black female contribution: X of Y pts** line (not a separate element). PDF gap report available after an email unlock for the session.
- Planning tool only; confirm with your verification agency and sector code.

## Notes
- Race- and gender-linked aggregates are processed only for the scorecard (see [docs/PRIVACY.md](docs/PRIVACY.md)).
- Sector codes that are not loaded fall back to the Generic / QSE cards with a warning.

## Secrets
Never commit API keys, tokens, or `.streamlit/secrets.toml`. Use Streamlit Cloud’s Secrets UI (or a local gitignored `secrets.toml` / `.env`). See [docs/SECRETS.md](docs/SECRETS.md). Rotate any credential that may have leaked.
