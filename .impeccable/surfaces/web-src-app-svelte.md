---
version: 1
slug: "web-src-app-svelte"
primary_target: "web/src/App.svelte"
related_targets: ["web/src/report/Report.svelte"]
---

# Surface brief: Klim web app (wizard, calculators, results) and print report

Scope: the whole rebuilt front end in `web/`: profile and consent, element steps with the procurement, contributions and Net Value calculators, results, client file open/save, how-to and privacy pages, and the print-ready gap report. Mode: Operate (the app); the gap report is a Read document inside the same world.

Audience and job: accountants and B-BBEE consultants estimating many clients' scorecards at a desk; enter figures, compare scenarios, save one file per client, hand the client a report.

Constraints: engine stays the single source of truth (Pyodide); client file format bee-check-client v1 unchanged; POPIA consent before scoring; no invented claims; results always framed as estimates.

## Direction contract

THESIS: Category standard played straight at Xero's craft level: a calm, task-led accounting tool. Refuses the themed or decorative scorecard; the clarity of the numbers is the identity.
OWN-WORLD: (Revised at the owner's request to a shadcn-style sign-in theme.) White cards on a zinc-50 canvas, a near-black primary for actions, violet for links, focus, selection and progress fills, state colours only where they mean something (green met, amber at risk, red blocking). Geist with tabular figures, glass-tinted 48px inputs, 16px controls and 24px cards, a staggered fade, slide and unblur entrance per step.
STORY: The practitioner opens or starts a client, sees which steps are done and what is missing, enters figures with help beside each field, and reaches a result that says the level, the points and exactly where the next points are, then saves the file and prints the report.
FIRST VIEWPORT: Top bar with Klim, the client name and scorecard chip, Open and Save client file on the right. Left rail: numbered steps with done/current/locked states. Main column: the step title, a one-line purpose, then the form card; primary Continue bottom-right of the card, Back beside it.
FORM: Category standard (standing exit chosen by the owner), benchmark Xero; seed: seed:fc1e51026eda99cb
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
