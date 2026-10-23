# Production v1 hardening

Ops notes for [BEE Check](https://beecalculator.streamlit.app/) on Streamlit Community Cloud.

## CI gates on `main`

Workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

Runs on:

- `push` to `main`
- every `pull_request`
- manual `workflow_dispatch` (Actions → CI → Run workflow)

Jobs that must stay green:

| Check name (GitHub Actions) | Job | What it does |
| --- | --- | --- |
| **test** | `test` | ruff lint/format, pytest, sector CSV totals, pinned `pip-audit` |
| **gitleaks** | `gitleaks` | secret scan (do not disable) |

### Branch protection — what Dumisani must click

CTO cannot set this via API without admin rights. In GitHub:

1. Open **Settings → Branches → Branch protection rules** (or **Rules → Rulesets**).
2. Rule for branch name pattern: `main`.
3. Enable **Require a pull request before merging** (recommended for v1).
4. Enable **Require status checks to pass before merging**.
5. Under required checks, add exactly:
   - `test`
   - `gitleaks`
6. Prefer **Do not allow bypassing the above settings** for admins once the team is used to the flow.
7. Optional: require branches to be up to date before merging.

Until those clicks are done, CI still runs but merges can land without green checks.

## Live smoke (host-up)

Script: [`tools/live_smoke.py`](../tools/live_smoke.py)

```bash
# from repo root (Python 3.11+; stdlib only)
python tools/live_smoke.py
# or:
python tools/live_smoke.py --url https://beecalculator.streamlit.app/
```

Exit `0` = HTTP 200 after Cloud’s auth cookie redirect **and** body matches a known marker
(`BEE Check`, `Privacy`, or Streamlit Cloud shell markers such as `streamlitAppPage`).

**Limitation:** Community Cloud serves a JS shell; page title / “Privacy notice” text are not in
the first HTML response. Curl smoke proves the host is up, not full UI. Keep QA browser smoke
(`/workspace/bee-team/qa/live-smoke.md`) for consent / PDF / sizing.

Cron / Grok Bot routine: see `/workspace/bee-team/cto/live-smoke-automation.md` (parent creates the routine).

## Error reporting

- `.streamlit/config.toml` keeps `showErrorDetails = false` (no stack traces in the UI).
- Unexpected **score calculation**, **PDF build**, and **TF planner** failures show the existing
  generic `st.error`, plus an `st.caption` support hint with **time of attempt only** (no email,
  company name, or input values).
- Exception **type** only is written via `logging` to stderr (`bee_check` logger) so it appears in
  Streamlit Cloud logs. Never log inputs, emails, or secrets.

## Pinned deploy from `main`

Streamlit Community Cloud for **bee_calculator**:

| Setting | v1 value |
| --- | --- |
| Repository | `Vambane/BEE_calculator` |
| Branch | **`main`** |
| Main file | **`app.py`** |
| Deploy model | Tip of `main` (no separate release channel / tag pin in v1) |

After merges to `main`:

1. Confirm Cloud shows the new commit (or use **Reboot** / **Reboot app** on the app settings).
2. Run `python tools/live_smoke.py`.
3. For PDF/system packages (`packages.txt`), prefer a full reboot so OS deps reinstall.

v1 does **not** use a separate staging app or release tag. Phase-2 may add one.
