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
- **Element steps (Indicators by default on Ownership and Management Control):** enter each scorecard indicator — including Black women / Black female lines — or switch to pre-calculated points from a verification agency. Net Value can be calculated on the Ownership step from share values, acquisition debt and the graduation factor (Annexe 100(E)), or entered from a verification agency.
- **Client files:** save the whole calculation (profile, every step, supplier list, contributions, Net Value inputs) as a JSON file from the sidebar and open it later to carry on or roll forward to a new year. Files are validated on open; consent is never stored. Logic in `bee_ui/client_file.py`.
- **Net Value calculator:** enter the company's value, the value of black-held shares, the acquisition debt still owed, economic interest and the current equity interest date. The app applies the Annexe 100(E) graduation factor and takes the lower of Formula A and Formula B, capped at the card's Net Value weighting. Logic in `bee/net_value.py`.
- **Procurement calculator:** upload or type a supplier list (CSV template provided) and the app works out TMPS, recognition-weighted B-BBEE spend for every procurement indicator on the selected scorecard, and fills the Preferential Procurement inputs. Logic in `bee/procurement.py`.
- **Contributions at benefit factors:** ED, SD and SED lines valued at the Annexe 400(B) / 500(A) factors (e.g. interest-free loan 70%, guarantee 50%, staff time 60%). Logic in `bee/contributions.py`.
- **Loss or low profit:** Statement 400 cl. 3.2.1 Turnover basis (deemed NPAT = Indicative Profit Margin x Turnover) when NPAT or the 5-year average is not positive, or the margin is below a quarter of the industry norm. Logic in `bee/npat.py`.
- **Results:** recognition level, total points, distance to next level, and a **Black women / Black female contribution: X of Y pts** line (not a separate element). PDF gap report available after an email unlock for the session.
- Planning tool only; confirm with your verification agency and sector code.

## Notes
- Race- and gender-linked aggregates are processed only for the scorecard (see [docs/PRIVACY.md](docs/PRIVACY.md)).
- Sector codes that are not loaded fall back to the Generic / QSE cards with a warning.

## Secrets
Never commit API keys, tokens, or `.streamlit/secrets.toml`. Use Streamlit Cloud’s Secrets UI (or a local gitignored `secrets.toml` / `.env`). See [docs/SECRETS.md](docs/SECRETS.md). Rotate any credential that may have leaked.
