"""
Generic parser for the farm yield workbook.

Designed to be robust to future edits:
- Any number of sheets (farms) — loops over whatever sheets exist.
- Finds the "Name" / "Latitude" / "Longtitude" labels and the "Year" header
  row by searching for the label text rather than a fixed row number, so a
  sheet with an extra blank row (or a slightly different layout) still parses.
- Skips any sheet that doesn't match the expected shape instead of crashing,
  and reports which sheets were skipped so a bad sheet doesn't take down the
  whole dashboard.
"""

import pandas as pd
import numpy as np
from scipy import stats


def _find_label_row(col, label_fragment):
    """Return the first row index in `col` whose string contains label_fragment (case-insensitive)."""
    for i, v in col.items():
        if isinstance(v, str) and label_fragment.lower() in v.lower():
            return i
    return None


def parse_sheet(raw: pd.DataFrame, sheet_name: str):
    """Parse one raw (header=None) sheet into metadata + a tidy yearly dataframe."""
    # Search the first ~20 rows / first 3 columns for the label cells.
    search_area = raw.iloc[:20, :3]

    name_row = None
    lat_row = None
    lon_row = None
    year_row = None

    for col_idx in range(search_area.shape[1]):
        col = search_area.iloc[:, col_idx]
        if name_row is None:
            name_row = _find_label_row(col, "name")
        if lat_row is None:
            lat_row = _find_label_row(col, "latitud")
        if lon_row is None:
            lon_row = _find_label_row(col, "longt") or _find_label_row(col, "longi")
        if year_row is None:
            year_row = _find_label_row(col, "year")

    if year_row is None:
        raise ValueError(f"Could not find a 'Year' header row in sheet '{sheet_name}'")

    # The label and the value sit in the same row; value is the first non-null
    # cell to the right of the label cell in that row.
    def value_right_of_label(row_idx, label_fragment):
        if row_idx is None:
            return None
        row = raw.iloc[row_idx]
        label_col = None
        for c, v in row.items():
            if isinstance(v, str) and label_fragment.lower() in v.lower():
                label_col = c
                break
        if label_col is None:
            return None
        for c in range(label_col + 1, raw.shape[1]):
            v = row[c]
            if pd.notna(v):
                return v
        return None

    farm_name = value_right_of_label(name_row, "name") or sheet_name
    lat = value_right_of_label(lat_row, "latitud")
    lon = value_right_of_label(lon_row, "longt") or value_right_of_label(lon_row, "longi")

    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        lat, lon = np.nan, np.nan

    # Data columns: find which column has "Year" in the header row, then
    # assume Actual/Model/ABARES are the next three columns to the right
    # (matches the template — Year, Actual, Model, ABARES).
    header_row = raw.iloc[year_row]
    year_col = None
    for c, v in header_row.items():
        if isinstance(v, str) and "year" in v.lower():
            year_col = c
            break
    if year_col is None:
        raise ValueError(f"Could not locate the Year column in sheet '{sheet_name}'")

    col_names = ["Year", "Actual", "Model", "ABARES"]
    data = raw.iloc[year_row + 1:, year_col:year_col + 4].copy()
    data.columns = col_names[:data.shape[1]]
    data = data.apply(pd.to_numeric, errors="coerce")
    data = data.dropna(subset=["Year"])
    data["Year"] = data["Year"].astype(int)
    data = data.reset_index(drop=True)

    return {
        "sheet_name": sheet_name,
        "farm_name": str(farm_name),
        "lat": lat,
        "lon": lon,
        "data": data,
    }


def load_workbook(file):
    """Load every sheet in the workbook. Returns (farms: dict, skipped: list of (sheet, error))."""
    xl = pd.ExcelFile(file)
    farms = {}
    skipped = []
    for sheet in xl.sheet_names:
        try:
            raw = pd.read_excel(xl, sheet_name=sheet, header=None)
            parsed = parse_sheet(raw, sheet)
            if parsed["data"].empty:
                skipped.append((sheet, "no yearly data rows found"))
                continue
            farms[parsed["farm_name"]] = parsed
        except Exception as e:
            skipped.append((sheet, str(e)))
    return farms, skipped


def pair_correlation(df: pd.DataFrame, col_x: str, col_y: str):
    """Pearson r, p-value and n for two columns, dropping rows where either is missing."""
    sub = df[[col_x, col_y]].dropna()
    n = len(sub)
    if n < 3:
        return {"r": np.nan, "p": np.nan, "n": n}
    r, p = stats.pearsonr(sub[col_x], sub[col_y])
    return {"r": r, "p": p, "n": n}


def farm_correlations(df: pd.DataFrame):
    pairs = [("Actual", "ABARES"), ("Model", "ABARES"), ("Actual", "Model")]
    return {f"{a} vs {b}": pair_correlation(df, a, b) for a, b in pairs}
