import uuid

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from data_loader import load_workbook, farm_correlations, pair_correlation

st.set_page_config(page_title="Yield Model Validation Dashboard", layout="wide", page_icon="🌾")

DATA_PATH = "data_files/yield_comparison_dataset_v2.xlsx"

# ---------- Styling ----------
st.markdown("""
<style>
    .metric-card {background-color:#f7f7f2; border-radius:10px; padding:14px; border:1px solid #e0e0d8;}
    .low-n {color:#b45309; font-weight:600;}
    .stat-badge {display:inline-block; padding:2px 8px; border-radius:6px; font-size:0.8em; margin-left:6px;}
    .good {background:#dcfce7; color:#166534;}
    .warn {background:#fef3c7; color:#92400e;}
    .bad {background:#fee2e2; color:#991b1b;}
</style>
""", unsafe_allow_html=True)

st.title("🌾 Yield Model Validation Dashboard")
st.caption("Actual vs Model vs ABARES yield estimates, by farm.")

# ---------- Data source: bundled file, with self-serve refresh ----------
with st.sidebar:
    st.header("Data")
    uploaded_files = st.file_uploader(
        "Upload updated workbook(s) to refresh the dashboard",
        type=["xlsx"],
        accept_multiple_files=True,
        help="Same template: one sheet per farm, with Name/Latitude/Longtitude "
             "and a Year/Actual/Model/ABARES table. Add a new farm by adding a "
             "new sheet in this format — no other changes needed. You can "
             "upload several files at once (e.g. one per region) — they're "
             "merged into a single dashboard.",
    )

if uploaded_files:
    farms, skipped = {}, []
    for uf in uploaded_files:
        f_farms, f_skipped = load_workbook(uf)
        for name in f_farms:
            if name in farms:
                skipped.append((f"{uf.name}: {name}",
                                 "duplicate farm name — this file's version overwrote an earlier upload"))
        farms.update(f_farms)
        skipped.extend([(f"{uf.name}: {s}", e) for s, e in f_skipped])
    st.sidebar.success(f"Using {len(uploaded_files)} uploaded file(s): "
                        + ", ".join(u.name for u in uploaded_files))
else:
    farms, skipped = load_workbook(DATA_PATH)
    st.sidebar.info(f"Using bundled file: {DATA_PATH}")

if skipped:
    with st.sidebar.expander(f"⚠️ {len(skipped)} sheet(s) skipped", expanded=False):
        for sheet, err in skipped:
            st.write(f"**{sheet}**: {err}")

if not farms:
    st.error("No farm sheets could be parsed from this workbook.")
    st.stop()

farm_names = sorted(farms.keys())

def badge(n, min_n=10):
    if n == 0:
        return '<span class="stat-badge bad">no data</span>'
    if n < min_n:
        return f'<span class="stat-badge warn">n={n}, small sample</span>'
    return f'<span class="stat-badge good">n={n}</span>'

def r_or_dash(r):
    return "—" if (r is None or np.isnan(r)) else f"{r:.2f}"

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"

def render_chart(fig, height=400):
    """Render a Plotly figure with an added 'Copy image' modebar button.
    Plotly has no built-in clipboard button, so this wires one up via the
    browser Clipboard API, alongside the existing zoom/pan/download tools.
    Falls back to triggering a normal PNG download if the browser blocks
    clipboard access (some browsers restrict this inside embedded frames)."""
    div_id = "chart_" + uuid.uuid4().hex
    fig_json = fig.to_json()
    html = f"""
    <div id="{div_id}" style="width:100%;"></div>
    <script src="{PLOTLY_CDN}"></script>
    <script>
    (function() {{
        var figure = {fig_json};
        var config = {{
            responsive: true,
            displaylogo: false,
            modeBarButtonsToAdd: [{{
                name: 'copyImage',
                title: 'Copy image to clipboard',
                icon: Plotly.Icons.camera,
                click: function(gd) {{
                    Plotly.toImage(gd, {{format: 'png', scale: 2,
                                          width: gd._fullLayout.width,
                                          height: gd._fullLayout.height}})
                        .then(function(dataUrl) {{
                            fetch(dataUrl).then(function(r) {{ return r.blob(); }}).then(function(blob) {{
                                if (navigator.clipboard && window.ClipboardItem) {{
                                    navigator.clipboard.write([new ClipboardItem({{'image/png': blob}})])
                                        .then(function() {{ toast(gd, 'Copied to clipboard'); }})
                                        .catch(function() {{
                                            Plotly.downloadImage(gd, {{format: 'png', filename: '{div_id}'}});
                                            toast(gd, "Couldn't access clipboard — downloaded instead");
                                        }});
                                }} else {{
                                    Plotly.downloadImage(gd, {{format: 'png', filename: '{div_id}'}});
                                    toast(gd, "Clipboard not supported — downloaded instead");
                                }}
                            }});
                        }});
                }}
            }}]
        }};
        Plotly.newPlot('{div_id}', figure.data, figure.layout, config);

        function toast(gd, msg) {{
            var t = document.createElement('div');
            t.innerText = msg;
            t.style.cssText = 'position:absolute; top:6px; right:8px; background:#333; color:#fff;'
                + 'padding:4px 10px; border-radius:5px; font-size:12px; z-index:1000; opacity:0.95;';
            gd.parentElement.style.position = 'relative';
            gd.parentElement.appendChild(t);
            setTimeout(function() {{ t.remove(); }}, 1800);
        }}
    }})();
    </script>
    """
    st.iframe(html, height=height + 40)

tab_overview, tab_farm, tab_compare, tab_data = st.tabs(
    ["📍 Overview", "🔎 Farm detail", "📊 Cross-farm comparison", "📄 Data"]
)

# ============================================================
# TAB 1 — Overview map
# ============================================================
with tab_overview:
    st.subheader("Farm locations")
    st.caption("Colour = how closely the Model tracks ABARES at that farm (Pearson r). "
               "Hover a point for details.")

    map_rows = []
    for name, f in farms.items():
        c = farm_correlations(f["data"])
        map_rows.append({
            "Farm": name,
            "lat": f["lat"],
            "lon": f["lon"],
            "Model vs ABARES (r)": c["Model vs ABARES"]["r"],
            "Actual vs ABARES (r)": c["Actual vs ABARES"]["r"],
            "n (Actual)": c["Actual vs ABARES"]["n"],
            "Years": len(f["data"]),
        })
    map_df = pd.DataFrame(map_rows)

    if map_df[["lat", "lon"]].notna().all(axis=None):
        fig = px.scatter_map(
            map_df, lat="lat", lon="lon", color="Model vs ABARES (r)",
            size=[14] * len(map_df),
            hover_name="Farm",
            hover_data={"lat": False, "lon": False,
                        "Model vs ABARES (r)": ":.2f",
                        "Actual vs ABARES (r)": ":.2f",
                        "n (Actual)": True},
            color_continuous_scale="RdYlGn", range_color=[-1, 1],
            zoom=3.2, height=480,
        )
        fig.update_layout(map_style="carto-positron", margin=dict(l=0, r=0, t=0, b=0))
        render_chart(fig, height=480)
    else:
        st.warning("Some farms are missing coordinates, so the map view is skipped.")

    st.subheader("At a glance")
    cols = st.columns(len(farm_names))
    for col, name in zip(cols, farm_names):
        f = farms[name]
        c = farm_correlations(f["data"])
        with col:
            st.markdown(f"**{name}**")
            st.markdown(
                f"Model↔ABARES: **{r_or_dash(c['Model vs ABARES']['r'])}**<br>"
                f"Actual↔ABARES: **{r_or_dash(c['Actual vs ABARES']['r'])}** "
                f"{badge(c['Actual vs ABARES']['n'])}",
                unsafe_allow_html=True,
            )

# ============================================================
# TAB 2 — Farm detail
# ============================================================
with tab_farm:
    selected = st.radio("Select a farm", farm_names, horizontal=True, key="farm_detail_pick")
    f = farms[selected]
    df = f["data"]
    yr_min, yr_max = int(df["Year"].min()), int(df["Year"].max())
    yr_range = st.slider("Year range", yr_min, yr_max, (yr_min, yr_max))
    dff = df[(df["Year"] >= yr_range[0]) & (df["Year"] <= yr_range[1])]

    st.markdown(f"### {selected}  \n*Lat {f['lat']}, Lon {f['lon']}*")

    # --- Time series ---
    fig_ts = go.Figure()
    for col, color in [("Actual", "#1f77b4"), ("Model", "#ff7f0e"), ("ABARES", "#2ca02c")]:
        fig_ts.add_trace(go.Scatter(
            x=dff["Year"], y=dff[col], name=col, mode="lines+markers",
            connectgaps=False, line=dict(color=color),
        ))
    fig_ts.update_layout(height=400, title="Yield over time", yaxis_title="Yield",
                          hovermode="x unified", legend=dict(orientation="h", y=1.1))
    render_chart(fig_ts, height=400)

    # --- Scatter pairs ---
    st.markdown("#### Correlation scatter plots")
    corrs = farm_correlations(dff)
    pairs = [("Actual", "ABARES"), ("Model", "ABARES"), ("Actual", "Model")]
    scols = st.columns(3)
    for scol, (x, y) in zip(scols, pairs):
        key = f"{x} vs {y}"
        stat = corrs[key]
        sub = dff[[x, y]].dropna()
        with scol:
            if len(sub) < 3:
                st.markdown(f"**{x} vs {y}**")
                st.info("Not enough overlapping data points to correlate.")
                continue
            fig_sc = go.Figure()
            fig_sc.add_trace(go.Scatter(
                x=sub[x], y=sub[y], mode="markers",
                marker=dict(size=9, color="#1f77b4"), name="years",
            ))
            if len(sub) >= 2:
                slope, intercept = np.polyfit(sub[x], sub[y], 1)
                x_line = np.linspace(sub[x].min(), sub[x].max(), 20)
                fig_sc.add_trace(go.Scatter(
                    x=x_line, y=slope * x_line + intercept, mode="lines",
                    line=dict(color="#444", dash="dash"), name="trend",
                ))
            fig_sc.update_layout(height=300, margin=dict(t=30, b=10), showlegend=False,
                                  xaxis_title=x, yaxis_title=y,
                                  title=f"{x} vs {y}  (r={stat['r']:.2f}, n={stat['n']})")
            render_chart(fig_sc, height=300)
            if stat["n"] < 10:
                st.markdown('<span class="low-n">⚠ small sample — treat this r with caution</span>',
                            unsafe_allow_html=True)

# ============================================================
# TAB 3 — Cross-farm comparison
# ============================================================
with tab_compare:
    st.subheader("Correlation heatmap across all farms")
    pair_options = ["Actual vs ABARES", "Model vs ABARES", "Actual vs Model"]
    which = st.radio("Pair", pair_options, horizontal=True)

    heat_rows = []
    for name in farm_names:
        c = farm_correlations(farms[name]["data"])
        heat_rows.append({"Farm": name, "r": c[which]["r"], "n": c[which]["n"]})
    heat_df = pd.DataFrame(heat_rows)

    fig_heat = go.Figure(data=go.Heatmap(
        z=[heat_df["r"].values],
        x=heat_df["Farm"],
        y=[which],
        colorscale="RdYlGn", zmin=-1, zmax=1,
        text=[[f"r={r:.2f}\nn={n}" if not np.isnan(r) else "no data"
               for r, n in zip(heat_df["r"], heat_df["n"])]],
        texttemplate="%{text}",
        hoverinfo="text",
    ))
    fig_heat.update_layout(height=220, margin=dict(t=20, b=10))
    render_chart(fig_heat, height=220)

    st.caption("Cells with fewer than 10 overlapping years are still shown but should be read with caution — "
               "a strong-looking r from 5 points is not the same statistical evidence as one from 30.")

    st.markdown("#### Full comparison table")
    table_rows = []
    for name in farm_names:
        c = farm_correlations(farms[name]["data"])
        table_rows.append({
            "Farm": name,
            "Actual↔ABARES r": r_or_dash(c["Actual vs ABARES"]["r"]),
            "Actual↔ABARES n": c["Actual vs ABARES"]["n"],
            "Model↔ABARES r": r_or_dash(c["Model vs ABARES"]["r"]),
            "Model↔ABARES n": c["Model vs ABARES"]["n"],
            "Actual↔Model r": r_or_dash(c["Actual vs Model"]["r"]),
            "Actual↔Model n": c["Actual vs Model"]["n"],
        })
    st.dataframe(pd.DataFrame(table_rows), width='stretch', hide_index=True)

# ============================================================
# TAB 4 — Raw data / export
# ============================================================
with tab_data:
    selected2 = st.selectbox("Farm", farm_names, key="data_tab_farm")
    st.dataframe(farms[selected2]["data"], width='stretch', hide_index=True)
    csv = farms[selected2]["data"].to_csv(index=False).encode("utf-8")
    st.download_button("Download this farm's data as CSV", csv,
                        file_name=f"{selected2}_yield_data.csv", mime="text/csv")