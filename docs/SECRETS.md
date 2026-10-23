# Secrets hygiene

**Rule:** never commit secrets to this repository.

## What counts as a secret
API keys, tokens, passwords, private keys, Streamlit Cloud secrets, SMTP credentials, database URLs with credentials, and any `.env` values.

## Local development
- Put secrets in a gitignored `.env` (never committed) or in `.streamlit/secrets.toml` (also gitignored).
- `.gitignore` already covers `.env`, `.env.*`, `.venv/`, `__pycache__/`, and `.streamlit/secrets.toml`.
- `.streamlit/config.toml` is theme/server config only — do not put credentials there.

## Streamlit Community Cloud
- Add secrets in the app’s **Settings → Secrets** UI (TOML), not in the repo.
- Prefer the Cloud UI over committing any secrets file.

## If something leaks
1. Rotate the credential immediately (revoke + issue a new one).
2. Remove it from git history if it was committed (filter-repo / support).
3. Tell Dumisani before changing production credentials.

## Scanning
CI runs gitleaks on PRs. Do not disable it. GitHub push protection should stay on for the repo.
