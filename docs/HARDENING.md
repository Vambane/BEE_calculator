# Production v1 hardening

Ops notes for [Klim](https://beecalculator.streamlit.app/) on Streamlit Community Cloud.

## CI gates on `main`

Workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

Runs on:

- `push` to `main`
- every `pull_request`
- manual `workflow_dispatch` (Actions → CI → Run workflow)

Jobs that must stay green:

| Check name (GitHub Actions) | Job | What it does |
| --- | --- | --- |
| **test** | `test` | installs `requirements-dev.lock` with `--require-hashes`, ruff lint/format, pytest, sector CSV totals, `pip-audit` |
| **gitleaks** | `gitleaks` | secret scan (do not disable) |

### Branch protection checklist

**State on 2026-11-06:** `main` is **not protected**. A ruleset named `protect_main` exists, but its
enforcement is **Disabled**, it targets **no branches**, and it only blocks deletion and force pushes.
So merges and direct pushes can land on `main` (and deploy to Streamlit Cloud) without green checks.

Edit the existing ruleset rather than creating a second one: **Settings → Rules → Rulesets →
`protect_main`**.

- [ ] **Enforcement status:** set to **Active** (not Disabled or Evaluate).
- [ ] **Target branches:** **Add target → Include default branch** (that is `main`).
- [ ] **Restrict deletions:** keep ticked.
- [ ] **Block force pushes:** keep ticked.
- [ ] **Require a pull request before merging:** tick it. Set **Required approvals = 0**, because
      GitHub does not let you approve your own PR. The rule still stops direct pushes to `main`.
- [ ] **Require status checks to pass:** tick it, then **Add checks** and pick both, with source
      **GitHub Actions**:
  - [ ] `test`
  - [ ] `gitleaks`
- [ ] **Require branches to be up to date before merging:** tick it (optional, but it means checks
      ran against the code that actually merges).
- [ ] **Bypass list:** leave empty. If you ever need an emergency push, add yourself with
      **For pull requests only**, so the bypass is visible in the PR.
- [ ] **Save changes.**

Verify afterwards (needs the GitHub CLI, signed in as the repo owner):

```bash
gh api repos/Vambane/BEE_calculator/rulesets --jq '.[] | {name, enforcement}'
# expect: {"name":"protect_main","enforcement":"active"}
gh api repos/Vambane/BEE_calculator/rules/branches/main --jq '.[].type'
# expect: deletion, non_fast_forward, pull_request, required_status_checks
```

Then open a throwaway PR and confirm the **Merge** button stays disabled until `test` and `gitleaks`
pass.

## Live smoke (host-up)

Script: [`tools/live_smoke.py`](../tools/live_smoke.py)

```bash
# from repo root (Python 3.11+; stdlib only)
python tools/live_smoke.py
# or:
python tools/live_smoke.py --url https://beecalculator.streamlit.app/
```

Exit `0` = HTTP 200 after Cloud’s auth cookie redirect **and** body matches a known marker
(`Klim`, `Privacy`, or Streamlit Cloud shell markers such as `streamlitAppPage`).

**Limitation:** Community Cloud serves a JS shell; page title / “Privacy notice” text are not in
the first HTML response. Curl smoke proves the host is up, not full UI. Keep QA browser smoke
(team QA live-smoke notes (internal)) for consent / PDF / sizing.

Cron / Grok Bot routine: see team live-smoke automation notes (internal) (parent creates the routine).

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
