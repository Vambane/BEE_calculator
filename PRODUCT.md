# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack
Rebuild of the front end confirmed by the owner (2026-11-06): a static site with the existing Python scoring engine (`bee/`, `bee_ui/` logic) running in the visitor's browser through Pyodide, hosted free on Cloudflare Pages. Front-end framework delegated: Svelte 5 + Vite, chosen because a multi-step calculator with editable tables, derived totals and saved/opened client files is mostly reactive state and forms, Svelte compiles that to a small bundle with little boilerplate, and the output is plain static files. The Streamlit app (`app.py`) stays in the repo and on Streamlit Community Cloud until the owner switches over.

## Users
Primary: accountants and B-BBEE consultants who estimate scorecards for many client companies. They enter each client's figures, compare scenarios, save one file per client and measurement year, and reopen it later to roll forward. Secondary: SME owners and finance managers checking their own company (the existing copy speaks to them).

## Product Purpose
Estimate a South African B-BBEE recognition level and points per element before formal verification, show the gap to the next level and what moves it, and produce a gap report to share with the client. It is a planning tool, not a verification certificate: every result tells the user to confirm with their verification agency and sector code.

## Positioning
Covers the Amended Codes 2019 Generic card, the QSE card (Code Series 600) and twelve loaded sector cards with their own targets, plus the calculations practitioners otherwise do in spreadsheets: Net Value from share values and acquisition debt (Annexe 100(E)), contributions at Annexe 400(B)/500(A) benefit factors, supplier lists to recognised procurement spend, and the Statement 400 cl. 3.2.1 turnover basis for loss or low profit. In the rebuild, client figures never leave the user's device.

## Operating Context
Used at a desk during client engagements, typically on a laptop or desktop, often with the client's financials, verification certificates and supplier lists open alongside. Inputs come from management accounts, payroll, shareholder registers and supplier spreadsheets (CSV). Outputs are a results screen, a downloadable PDF gap report, a supplier-list CSV, and a JSON client file kept on the user's own device. Sessions are long and iterative; the same client is revisited across measurement years.

## Capabilities and Constraints
- Sectors: Generic (Amended Codes), AgriBEE, Chartered Accountancy, Construction, Defence, Financial Services (Amended FSC 2017), Forestry, ICT, Integrated Transport, Legal, Marketing Advertising & Communication, Property, Tourism. Unloaded codes fall back to Generic/QSE with a warning.
- Sizing from revenue (EME / QSE / Generic); deemed (affidavit) levels with an opt-in to score the full card; YES Initiative tiers; draft-rule planning toggle.
- Per element: indicator entry (rand or percentage, including Black women / Black female lines) or pre-calculated points from a verification agency.
- Results: recognition level, total points, distance to next level, Black women / Black female contribution as a line (not a separate element), sub-minimum and discount effects.
- POPIA: consent to the privacy notice is required before scoring; race- and gender-linked aggregates are processed only for the scorecard. Consent is never stored in a client file.
- Client file format `bee-check-client` v1 must stay compatible between the Streamlit app and the rebuild.
- The scoring engine is the single source of truth; the front end must not reimplement scoring rules.
- Open decision: the PDF "email unlock" gate. In the Streamlit app the email is only shape-checked and never sent or stored; a static site has nowhere to send it either. The rebuild drops the gate pending the owner's decision.

## Brand Commitments
Name: BEE Check. Voice: plain, calm and precise ("B-BBEE scorecard, calmly estimated"); always frames results as estimates to confirm with a verification agency. No visual identity is binding; the current honey palette is not a commitment. Visual commitment (owner's choice, 2026-11-06): the category standard played straight, at the craft level of Xero (clear, friendly, task-led accounting UI). No themed or decorative world.

## Evidence on Hand
- Scoring tables and sector targets in `bee/sectors/data/sector-element-targets.csv`; regression tests in `tests/`.
- Privacy policy (`docs/PRIVACY.md`) and how-to guide (`docs/HOW_TO.md`); the privacy policy describes Streamlit hosting and must be updated for in-browser processing before the rebuild goes live.
- No testimonials, customer names, usage numbers or verification-agency endorsements exist. None may be invented.

## Product Principles
1. Every number traces to a rule: show where a point came from (element, indicator, target) rather than only the total.
2. Estimate, never certify: results are framed as planning figures with the next step named.
3. The practitioner's rhythm: fast re-entry for many clients, scenario changes without losing work, files they own.
4. Privacy by construction: client data stays on the device unless the user exports it.
