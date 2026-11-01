# BEE Calculator — Privacy policy (v1)

**Privacy policy path (in-app):** `/privacy` (query: `?page=privacy`) until a public URL exists.

**Source of truth:** Compliance privacy notice v1 (internal team record; Security checklist fit, not legal approval). Dumisani approved this wording for production v1 (legal entity and Information Officer remain placeholders until launch).

---

## Responsible party

**Responsible party:** [Legal entity name — Dumisani to confirm]
**Contact:** [Information Officer email — Dumisani to confirm]

## What we collect

Company-level figures you type in to score a B-BBEE scorecard (for example turnover, ownership and management percentages, spend figures). If you use the procurement calculator, the supplier list you upload or type in: supplier names, spend, B-BBEE level, size and ownership percentages. If you use the contributions calculator, the contribution lines you type in: beneficiary names, contribution types and amounts. Optional work email if you use the PDF unlock. We do not collect ID numbers or names of individuals; if a supplier is a sole proprietor, use a reference instead of the person's name.

## Why

To calculate an indicative B-BBEE score and let you download a PDF report of that session. Race- and gender-linked aggregates are processed only for that scorecard purpose (POPIA s26).

## Consent

You must tick that you have read this notice and agree to this processing for this session’s scorecard before scoring or PDF unlock proceeds.

## Where / how long

Inputs and any unlock email are kept only for this interactive session on the app host and are discarded when the session ends. They are not written to a database or other long-term store. The PDF is generated on the app host for your download and is not retained after the response.

| Data | Where it lives | How long | Notes |
|---|---|---|---|
| Scorecard inputs (turnover, ownership %, etc.) | App-host session state for this interactive session | Until the session ends | Not written to a database or other long-term store |
| Supplier list (procurement calculator) | App-host session state for this interactive session | Until the session ends or Start over | Not written to a database; download it as CSV to keep it |
| Contribution lines (benefit-factor calculator) | App-host session state for this interactive session | Until the session ends or Start over | Not written to a database |
| Work email (PDF unlock) | App-host session state (`pdf_gate`) | Until the session ends | Not emailed; not persisted beyond the session |
| Marketing preference tick | App-host session state | Until the session ends | Does **not** create a list or subscribe anyone |
| Generated PDF | Rendered on the app host (WeasyPrint) for your download | Not retained after the response | You keep the file you download; we do not keep a copy |

When we add real email send or accounts, we will update this table (purpose, retention period, and how to export or delete) before collecting those details.

## Analytics and errors

We do not put your inputs into analytics or error reports. Usage statistics are off.

## Email and marketing

The email field unlocks a download. We do not send the PDF by email in v1. An optional marketing tick does not subscribe you to anything until we run a real marketing provider and obtain a fresh POPIA s69 opt-in.

## Your rights

You can stop using the tool and end the session to clear the data we hold for that session. Export and deletion of stored accounts will apply when accounts exist.

## Hosting and cross-border processing

v1 is hosted on Streamlit Community Cloud in the United States. Personal information is therefore processed outside South Africa. A POPIA s72 basis for that transfer is recorded (legal to confirm the exact ground).

## Changes

We will update this page when retention or email behaviour changes.
