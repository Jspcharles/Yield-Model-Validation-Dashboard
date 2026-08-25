# Yield Model Validation Dashboard

An interactive dashboard comparing **Actual**, **Model**, and **ABARES** yield estimates across farms.

## 🌐 Live Dashboard

The dashboard has been published using **Streamlit Community Cloud** and is available online:

👉 **[Open the Live Yield Model Validation Dashboard](https://yield-model-validation-dashboard.streamlit.app/)**

No installation is required to view or interact with the published dashboard.

## 📁 What's Inside

- `app.py` — Main dashboard built with **Streamlit + Plotly**
- `data_loader.py` — Generic parser that reads **every sheet** in the workbook, so adding a new farm only requires adding a new sheet using the same template
- `Final_Dataset.xlsx` — Bundled/default dataset
- `requirements.txt` — Required Python dependencies

## 🚀 Run Locally

Install the required dependencies:

```bash
pip install -r requirements.txt