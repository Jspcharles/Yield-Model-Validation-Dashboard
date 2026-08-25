# Yield Model Validation Dashboard

Interactive dashboard comparing **Actual**, **Model**, and **ABARES** yield estimates
across farms. 

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

## Updating data
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
