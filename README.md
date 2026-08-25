# Yield Model Validation Dashboard

Interactive dashboard comparing **Actual**, **Model**, and **ABARES** yield estimates
across farms. Built so it keeps working as you add farms or update numbers —
no code changes required for either.

## What's inside
- `app.py` — the dashboard (Streamlit + Plotly)
- `data_loader.py` — generic parser: reads *every* sheet in the workbook, so a
  new farm = a new sheet in the same template, nothing else to touch
- `Final_Dataset.xlsx` — the bundled/default dataset
- `requirements.txt` — dependencies

## Run it locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Opens at `http://localhost:8501`.

## Deploy it so the company can access it anytime (free)
1. Push this folder to a GitHub repo (public or private).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub.
3. Click **New app**, point it at the repo and `app.py`.
4. You get a permanent URL (e.g. `yourapp.streamlit.app`) — bookmark and share it.

Redeploying after a data change is automatic: push the updated `Final_Dataset.xlsx`
to the same repo and the live app picks it up within a minute or two.

## Updating data without touching GitHub at all
The app has an **upload box in the sidebar**. Anyone with the latest spreadsheet
(same template) can drag it in and the whole dashboard refreshes instantly —
no deployment, no code, no waiting on you. This is the easiest path for the
company's day-to-day use once new seasons' data comes in.

## Adding a new farm
Copy the sheet-tab format used by the existing farms exactly:
- A cell containing `Name` with the farm name in the cell to its right
- `Latitude` / `Longtitude` the same way
- A `Year | Actual | Model | ABARES` table below

The parser searches for these labels by text rather than a fixed cell
address, so minor layout drift (an extra blank row, etc.) won't break it —
but keeping the same structure is the safest bet.

## Notes on the correlation numbers
`Actual` yield is missing for most years at most farms (two farms currently
have none at all). Every correlation shown is labeled with its sample size
(`n`), and anything under 10 overlapping years is flagged — a strong-looking
r from 5 points isn't the same evidence as one from 30. Worth mentioning
explicitly when presenting this, since it's the kind of thing that undermines
credibility if a stakeholder notices it themselves first.
