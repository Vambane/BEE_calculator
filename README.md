# Streamlit B-BBEE Calculator

Minimal Streamlit app to estimate a South African SME/QSE B-BBEE score and recognition level.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## What it does
- Capture profile inputs: turnover, payroll, ownership %, women ownership %, management %, province.
- Capture contribution inputs: skills development (% payroll), black-owned supplier spend, EME/QSE spend, enterprise & supplier development (% NPAT), socio-economic development (% NPAT).
- Applies simplified SME/QSE weighting (100-point scale) with EME auto-levels and ownership discount for Generic <10%.
- Shows total points, recognition level, and a readable bar chart with per-element points vs max.

## Notes
- Planning tool only; confirm with your verification agency and sector code.
- Adjust targets/weighting in `app.py` if your sector uses different thresholds.

## Updating the chart
- The breakdown chart uses Altair layered bars: a light background for the max points and a green foreground for achieved points with labels (`points / max`). Tooltips include % of max.
- If you want a different palette or scale, tweak the colors and `max_domain` in the "Score breakdown" section of `app.py`.

## Git tips (manual)
If you want this in GitHub:
```bash
git add app.py requirements.txt README.md
git commit -m "Add Streamlit B-BBEE calculator with improved chart"
git push origin main   # adjust branch/remote if needed
```
