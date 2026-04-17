"""Section 5 — Download a ready-to-deploy placement plan."""

from __future__ import annotations

import io
import json
from datetime import date

import pandas as pd
import streamlit as st

from data_io import (
    METHOD_META,
    available_ks,
    load_sensor_coords,
    method_metrics,
)

try:
    from utils.kml_exporter import dataframe_to_kml
    HAS_KML = True
except Exception:
    HAS_KML = False


def _to_geojson(df: pd.DataFrame) -> str:
    features = []
    for i, row in df.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(row["longitude"]), float(row["latitude"])],
            },
            "properties": {
                "id": f"sensor_{i+1:04d}",
                "state": str(row.get("state", "")),
            },
        })
    return json.dumps({"type": "FeatureCollection", "features": features}, indent=2)


def _brief_markdown(method: str, k: int, metrics: dict, cost_per_lakh: int) -> str:
    meta = METHOD_META[method]
    total_cr = cost_per_lakh * k / 100
    return f"""# Fair Sensor Deployment Plan — {meta['label']} @ k = {k}

**Generated:** {date.today().isoformat()}
**Strategy:** {meta['full']}
**Number of sensors:** {k}
**Estimated capex:** ₹{total_cr:.2f} crore (₹{cost_per_lakh} lakh × {k})

## Performance on held-out CPCB stations

| Metric | Value |
| --- | --- |
| Baseline RMSE (existing network) | {metrics.get('rmse_before', 0):.3f} μg/m³ |
| Post-deployment RMSE | {metrics.get('rmse_after', 0):.3f} μg/m³ |
| Error reduction | {metrics.get('improvement_percent', 0):.2f}% |
| Predictive RMSE (forecast horizon) | {metrics.get('pred_rmse', 0):.3f} μg/m³ |
| Independent runs aggregated | {metrics.get('n_files_found', '—')} |

## Methodology (one paragraph)

{meta['full']} optimises sensor coordinates against a PM₂.₅ field inferred by a
Transformer Neural Process trained on CPCB + satellite reanalysis (2019–2023).
{'The Gumbel-softmax relaxation (GD-MI) allows joint gradient-based optimisation of all k sensor positions simultaneously.' if method == 'gdmi' else 'The greedy MaxVar baseline selects the single highest-variance grid cell at each step, conditional on sensors already placed.'}
Evaluation uses a held-out CPCB subset that was never shown to the optimiser.

## Deliverables in this bundle

- `sensors.csv` — lat/lon/state, ready for GIS tools
- `sensors.kml` — loads directly into Google Earth
- `sensors.geojson` — standard web-map format
- `README.md` — this file

## Contact

IIT Gandhinagar Sustainability Lab · nipun.batra@iitgn.ac.in
"""


def _zip_bundle(df: pd.DataFrame, brief_md: str) -> bytes:
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("sensors.csv", df.to_csv(index=False))
        z.writestr("sensors.geojson", _to_geojson(df))
        if HAS_KML:
            z.writestr("sensors.kml", dataframe_to_kml(df))
        z.writestr("README.md", brief_md)
    return buf.getvalue()


def render():
    st.markdown(
        '<p class="section-lede">'
        "Choose a strategy and budget — walk away with a zip containing the coordinate "
        "list (CSV / KML / GeoJSON) and a one-page methodology brief. This is the file "
        "a state pollution control board actually needs."
        "</p>",
        unsafe_allow_html=True,
    )

    methods = [m for m in ("gdmi", "maxvar") if available_ks(m)]
    if not methods:
        st.error("No coordinate CSVs found in `cache/loc_csv/`.")
        return

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        method = st.selectbox(
            "Strategy",
            methods,
            format_func=lambda m: f"{METHOD_META[m]['label']} — {METHOD_META[m]['full']}",
        )
    with c2:
        ks = available_ks(method)
        k = st.select_slider("Budget (k)", options=ks, value=ks[-1])
    with c3:
        cost_per = st.number_input("₹ lakh / sensor", 1, 100, 20, 1)

    df = load_sensor_coords(method, k)
    m = method_metrics(method, k) or {}

    st.markdown("**Coordinate preview** (first 20 rows)")
    st.dataframe(df.head(20), use_container_width=True, hide_index=True,
                 column_config={
                     "latitude": st.column_config.NumberColumn(format="%.4f"),
                     "longitude": st.column_config.NumberColumn(format="%.4f"),
                 })

    brief = _brief_markdown(method, k, m, cost_per)

    cols = st.columns([1, 1, 1, 1, 2])
    with cols[0]:
        st.download_button(
            "⬇ CSV",
            data=df.to_csv(index=False).encode(),
            file_name=f"sensors_{method}_{k}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with cols[1]:
        if HAS_KML:
            st.download_button(
                "⬇ KML",
                data=dataframe_to_kml(df).encode(),
                file_name=f"sensors_{method}_{k}.kml",
                mime="application/vnd.google-earth.kml+xml",
                use_container_width=True,
            )
        else:
            st.caption("KML unavailable (install simplekml)")
    with cols[2]:
        st.download_button(
            "⬇ GeoJSON",
            data=_to_geojson(df).encode(),
            file_name=f"sensors_{method}_{k}.geojson",
            mime="application/geo+json",
            use_container_width=True,
        )
    with cols[3]:
        st.download_button(
            "⬇ Brief",
            data=brief.encode(),
            file_name=f"deployment_brief_{method}_{k}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with cols[4]:
        st.download_button(
            "⬇ Everything (.zip)",
            data=_zip_bundle(df, brief),
            file_name=f"deployment_plan_{method}_{k}.zip",
            mime="application/zip",
            use_container_width=True,
            type="primary",
        )

    with st.expander("Preview methodology brief"):
        st.markdown(brief)
