# """
# Tab 1: AQ Sensor Placement Visualization
# Implements interactive sensor placement with animation and comparison maps.
# """

# import streamlit as st
# import pandas as pd
# import plotly.graph_objects as go
# import json
# import time

# # Import utilities
# import sys
# from pathlib import Path
# sys.path.append(str(Path(__file__).parent.parent))

# # All data loading now handled by map_creator functions
# from utils.tab1_utils import (
#     create_plotly_india_map
# )

# def render_tab1():
#     """Render the AQ Sensor Placement Visualization tab."""
    
#     st.title("🌍 AQ Sensor Placement Visualization")
    
#     st.info("Using optimization results from TNPD model with measurements from CPCB sensors")
    
#     # Simple configuration without data dependencies
#     col1, col2 = st.columns(2)
    
#     with col1:
#         k_sensors = st.selectbox(
#             "Sensor Configuration",
#             options=["20","40", "100", "500"],
#             index=0,
#         )
    
#     with col2:
#         method = st.selectbox(
#             "Optimization Method",
#             options=[ "GDMI ", "MaxVar"],
#             index=0,
#         )
    
#     # Detect selection change and show loading delay
#     _tab1_key = f"{k_sensors}_{method}"
#     if st.session_state.get("_tab1_prev_key") != _tab1_key:
#         st.session_state["_tab1_prev_key"] = _tab1_key
#         with st.spinner("⏳ Deploying new configuration..."):
#             time.sleep(5)

#     # Main visualization section
#     st.header("📍 Sensor Deployment Map")
    
    
#     col = st.columns(1)
#     with col[0]:
#         show_pm25_overlay = st.checkbox("Show Overlay", value=True)

#     # Resolve method key
#     method_key = "MaxVar" if "MaxVar" in method else "GDMI"

#     try:
#         with st.spinner("Rendering interactive map..."):
#             # time.sleep(5)  # simulate loading delay
#             fig = create_plotly_india_map(k=int(str(k_sensors).strip()), method=method_key, show_overlay=show_pm25_overlay)
#             st.plotly_chart(fig, use_container_width=True)
#         st.success("✅ Map loaded successfully!", icon="🌍")
#     except Exception as e:
#         st.warning(f"⚠️ Could not render Plotly map: {e}")

#     # --- Optimization Statistics Section ---
#     st.divider()
#     st.subheader("📊 Metrics")

#     summary_path = Path(__file__).resolve().parent / "../cache/vis_data/summary.json"
#     try:
#         with open(summary_path, "r") as f:
#             summary_data = json.load(f)

#         # Pick the right section
#         section_key = "maxvar" if method_key == "MaxVar" else "gdmi"
#         k_str = str(int(str(k_sensors).strip()))
#         stats = summary_data.get(section_key, {}).get(k_str)

#         if stats is None:
#             st.info(f"No statistics available for {method_key} with k={k_str}.")
#         else:
#             rmse_before = stats.get("rmse_before")
#             rmse_after = stats.get("rmse_after")
#             improvement_pct = stats.get("improvement_percent")
#             pred_rmse = stats.get("pred_rmse")
#             final_loss = stats.get("best_loss") or stats.get("final_loss")

#             # Metric cards row
#             m1, m2 = st.columns(2)
#             m1.metric(
#                 label="RMSE (Existing Sensors)",
#                 value=f"{rmse_before:.3f} " if rmse_before is not None else "—",
#             )
#             m2.metric(
#                 label="RMSE (Post Deployment)",
#                 value=f"{rmse_after:.3f} " if rmse_after is not None else "—",
#                 delta=f"-{improvement_pct:.2f}%" if improvement_pct else None,
#                 delta_color="inverse",
#             )
            

#             m4, m5 = st.columns(2)
#             m4.metric(
#                 label="Final Predictive RMSE",
#                 value=f"{pred_rmse:.3f} μg/m³" if pred_rmse is not None else "—",
#             )
#             m5.metric(
#                 label="Final Optimization Loss",
#                 value=f"{final_loss:.6f}" if final_loss is not None else "—",
#             )

#     except FileNotFoundError:
#         st.warning("Summary statistics file not found.")
#     except Exception as e:
#         st.warning(f"Could not load statistics: {e}")

    
#     # Animation section
#     st.divider()
#     st.subheader("Optimization Animation")
#     # Button to reveal animation controls
#     if 'show_animation_panel' not in st.session_state:
#         st.session_state.show_animation_panel = False


#     if st.button("▶️ Play Animation", key="open_anim_btn"):
#         st.session_state.show_animation_panel = True

#     if st.session_state.get("show_animation_panel", False):
#         # Resolve k and method keys for file matching
#         try:
#             k_val = int(str(k_sensors).strip())
#         except Exception:
#             st.warning("Invalid sensor count; defaulting to k=50.")
#             k_val = 50

#         # Animation directory
#         anim_dir = (Path(__file__).resolve().parent / "../cache/animations").resolve()
#         if not anim_dir.exists():
#             st.warning(f"Animations directory not found: {anim_dir}")
#         else:
#             # Find best matching animation file 
#             if method_key == "MaxVar":
#                 pattern = f"prediction_error_maxvar_n{k_val}.gif"
#             else:
#                 pattern = f"prediction_error_n{k_val}.gif"
#             candidates = list(anim_dir.glob(pattern))

#             # Fallback: show most recent animation if none match k
#             if not candidates:
#                 candidates = sorted(anim_dir.glob("*.*"), key=lambda p: p.stat().st_mtime, reverse=True)

#             if not candidates:
#                 st.info(f"No animation found in {anim_dir}.")
#             else:
#                 anim_path = candidates[0]
#                 st.caption(f"🎬 Showing animation: {anim_path.name}")

#                 # Render based on file extension
#                 ext = anim_path.suffix.lower()
#                 with open(anim_path, "rb") as f:
#                     data = f.read()
#                     if ext in (".mp4", ".webm", ".m4v", ".mov"):
#                         st.video(data)
#                     elif ext == ".gif":
#                         st.image(data, use_container_width=False, width=1000)
#                     else:
#                         st.info(f"Unsupported animation format: {ext}")

#     # Best sensors CSV preview and download
#     st.divider()
#     st.subheader("Download optimum sensor locations")
        

#     n_val = int(str(k_sensors).strip())

#     # --- Setup paths ---
#     BASE_DIR = Path(__file__).resolve().parent
#     cache_dir = BASE_DIR / "../cache/loc_csv"

#     # Ensure directory exists
#     if not cache_dir.exists():
#         st.warning(f"Cache directory not found: {cache_dir}")
#     else:
#         # --- Find matching CSV(s) based on method ---
#         if method_key == "MaxVar":
#             candidates = list(cache_dir.glob(f"best_sensors_var_{n_val}*.csv"))
#         else:
#             candidates = list(cache_dir.glob(f"best_sensors_{n_val}*.csv"))

#         if not candidates:
#             csv_prefix = f"best_sensors_var_{n_val}" if method_key == "MaxVar" else f"best_sensors_{n_val}"
#             st.info(f"No CSV found in {cache_dir} for n={n_val}, method={method_key} (expected: {csv_prefix}.csv)")
#         else:
#             # Pick most recently modified file
#             csv_path = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]

#             # Load and show preview
#             df_preview = pd.read_csv(csv_path)
#             st.caption(f"📄 Showing: {csv_path.name}")
#             st.dataframe(df_preview.head(50), use_container_width=True, height=300)

#             from utils.kml_exporter import dataframe_to_kml

#             # Generate KML string
#             kml_string = dataframe_to_kml(df_preview, lon_col="longitude", lat_col="latitude")

#             # KML download button
#             kml_filename = f"best_sensors_var_{n_val}.kml" if method_key == "MaxVar" else f"best_sensors_{n_val}.kml"
#             st.download_button(
#                 label="🌐 Download KML (Google Earth)",
#                 data=kml_string.encode("utf-8"),
#                 file_name=kml_filename,
#                 mime="application/vnd.google-earth.kml+xml",
#                 key=f"download_best_sensors_kml_{n_val}_{method_key}"
#             )


    
#     # # Summary section
#     # st.header("📈 Optimization Summary")
    
#     # # Get final summary data
#     # summary_data = get_sensor_optimization_data() if get_sensor_optimization_data else None
#     # if summary_data:
#     #     col1, col2 = st.columns(2)
        
#     #     with col1:
#     #         st.subheader("📊 Key Metrics")
#     #         st.write(f"**Total Sensors Optimized**: {summary_data['num_optimized']}")
#     #         st.write(f"**Existing CPCB Sensors**: {summary_data['num_deployed']}")
#     #         st.write(f"**Optimization Iteration**: {summary_data['iteration']}")
#     #         st.write(f"**Variance Loss**: {summary_data['variance_loss']:.6f}")
#     #         if summary_data['rmse'] is not None:
#     #             st.write(f"**Prediction RMSE**: {summary_data['rmse']:.4f} μg/m³")
        
#     #     with col2:
#     #         st.subheader("🎯 Research Impact")
#     #         st.write("✅ **Population-aware sensor placement**")
#     #         st.write("✅ **Neural network-based optimization (TNPD)**")
#     #         st.write("✅ **Real PM2.5 data integration**")
#     #         st.write("✅ **Fairness-driven deployment strategy**")
#     #         st.write("✅ **Interactive visualization for policy decisions**")
#     # else:
#     #     st.error("Could not load optimization summary data")

# if __name__ == "__main__":
#     render_tab1()

"""
Tab 1: Live AQ Sensor Placement (Distilled Model + Animation)
"""

import streamlit as st
import numpy as np
import torch
import torch.nn.functional as F
import xarray as xr
import json
import time
import yaml
import os
import imageio.v2 as imageio
import tempfile
from pathlib import Path
import plotly.graph_objects as go
from einops import repeat
from importlib.machinery import SourceFileLoader

# -----------------------------
# CONFIG
# -----------------------------

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
os.environ["CUDA_VISIBLE_DEVICES"] = "1"

def snap_to_grid(x_norm, x_all_norm, coords):
    """
    x_norm: (k, 2) normalized coords (model output)
    x_all_norm: (M, 2) all normalized grid points
    coords: (M, 2) lat/lon
    """
    dists = np.linalg.norm(x_norm[:, None] - x_all_norm[None, :], axis=-1)
    idx = dists.argmin(axis=1)
    return coords[idx]


import imageio.v2 as imageio
import tempfile

def create_animation(history, x, coords, base_pts, n_frames=50, seconds_per_frame=0.5):
    indices = np.linspace(0, len(history)-1, n_frames, dtype=int)

    frames = []

    for idx in indices:
        pts = history[idx]
        snapped_pts = snap_to_grid(pts, x, coords)

        fig = plot_map(base_pts, snapped_pts)

        img_bytes = fig.to_image(format="png", scale=1)
        img = imageio.imread(img_bytes)

        # 🔥 remove alpha if present
        if img.shape[-1] == 4:
            img = img[:, :, :3]

        # 🔥 downscale
        # img = img[::2, ::2]

        # 🔥 FIX: ensure EVEN dimensions (CRITICAL)
        h, w = img.shape[:2]
        img = img[:h - (h % 2), :w - (w % 2)]

        frames.append(img.astype(np.uint8))

    # 🔥 FIX: use integer FPS
    fps = 2  # stable

    # 🔥 repeat frames to simulate 1.5 sec per frame
    repeat_factor = int(seconds_per_frame * fps)  # = 3

    frames_extended = []
    for f in frames:
        frames_extended.extend([f] * repeat_factor)

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")

    imageio.mimsave(
        tmp_file.name,
        frames_extended,
        fps=fps,
        codec="libx264",
        quality=5
    )

    return tmp_file.name
# -----------------------------
# DATA LOADING
# -----------------------------
@st.cache_resource
def load_data_and_models():
    # Load masks
    india_mask = np.load("data/india_mask.npz")['arr_0']
    sensors_mask = np.load("data/station_mask.npz")['arr_0']
    mask = sensors_mask[india_mask]

    # Load dataset
    ds = xr.open_dataset('data/val_data.nc')
    from utils.run import scale_ds
    x, y = scale_ds(ds, apply_india_mask=True)

    # Load distilled model
    module = SourceFileLoader("tnpd", "models/tnpd.py").load_module()
    model_cls = getattr(module, "TNPD")

    student_ckpt = torch.load("models/distilled/student_student.pt")

    config = student_ckpt.get("config")
    model = model_cls(**config)
    model.load_state_dict(student_ckpt["model_state_dict"])
    model = model.to(DEVICE).eval()

    # Load teacher
    with open("configs/tnpd.yaml") as f:
        teacher_config = yaml.safe_load(f)

    teacher = model_cls(**teacher_config)
    teacher.load_state_dict(
        torch.load("models/best.pt", map_location="cpu")
    )
    teacher = teacher.to(DEVICE).eval()
    
    lats = ds['lat'].values
    lons = ds['lon'].values

    # Create full grid
    lat_grid, lon_grid = np.meshgrid(lats, lons, indexing='ij')

    # Flatten ONLY India region (same as x)
    coords = np.stack([
        lat_grid[india_mask],
        lon_grid[india_mask]
    ], axis=1)   # (M, 2)

    return x, y, mask, model, teacher, coords


# -----------------------------
# OPTIMIZATION CORE
# -----------------------------
def run_optimization(x, y, mask, model, n_new, n_iters=200, method="Gumbel"):
    x_cuda = torch.tensor(x, dtype=torch.float32).to(DEVICE)
    y_cuda = torch.tensor(y, dtype=torch.float32).to(DEVICE)[..., None]

    x_deployed = torch.tensor(x[mask], dtype=torch.float32).to(DEVICE)
    y_deployed = torch.tensor(y[:, mask], dtype=torch.float32).to(DEVICE)[..., None]

    pool_pts = torch.tensor(x, dtype=torch.float32, device=DEVICE)

    # ============================
    # 🔵 GUMBEL METHOD (UNCHANGED)
    # ============================
    if method == "Gumbel":
        logits = torch.nn.Parameter(torch.randn(n_new, x.shape[0], device=DEVICE))
        optimizer = torch.optim.Adam([logits], lr=0.5)

        history = []

        for it in range(n_iters):
            tau = max(5 - (5 - 0.01) * it / n_iters, 0.01)

            probs = F.gumbel_softmax(logits, tau=tau, hard=True, dim=1)
            x_best = probs @ pool_pts

            history.append(x_best.detach().cpu().numpy())

            x_all = torch.cat([x_deployed, x_best], dim=0)
            x_all = repeat(x_all, 'b d -> t b d', t=y_deployed.shape[0])

            y_pred, _ = model.predict(
                x_all[:, :-n_new, :],
                y_deployed,
                x_all[:, -n_new:, :]
            )

            y_all = torch.cat([y_deployed, y_pred], dim=1)

            # variance loss
            std_list = []
            for i in range(0, x_cuda.shape[0], 1024):
                xt = x_cuda[i:i+1024]
                xt = repeat(xt, 'b d -> t b d', t=y.shape[0])
                _, std = model.predict(x_all, y_all, xt)
                std_list.append(std)

            loss = torch.cat(std_list, dim=1).mean()

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        return history, x_best.detach().cpu().numpy()

    # ============================
    # 🔴 MAXVAR METHOD (NEW)
    # ============================
    elif method == "MaxVar":

        x_cuda_rep = repeat(x_cuda, 'b d -> t b d', t=y_deployed.shape[0])

        x_best_list = []
        history = []

        x_all = repeat(x_deployed, 'b d -> t b d', t=y_deployed.shape[0])
        y_all = y_deployed

        with torch.no_grad():
            for i in range(n_new):

                # ---- compute variance over full grid ----
                _, std = model.predict(x_all, y_all, x_cuda_rep)

                # ---- pick highest variance point ----
                best_idx = torch.mean(std, dim=0).argmax(dim=0)

                # (T,1,2)
                best = x_cuda_rep[:, best_idx:best_idx+1, :]

                x_best_list.append(best)

                # concat all selected points
                x_best = torch.cat(x_best_list, dim=1)  # (T, i+1, 2)

                # store history (take one timestep)
                history.append(x_best[0].detach().cpu().numpy())

                # update x_all
                x_all = torch.cat([
                    repeat(x_deployed, 'b d -> t b d', t=y_deployed.shape[0]),
                    x_best
                ], dim=1)

                # ---- autoregressive prediction ----
                y_pred, _ = model.predict(
                    x_all[:, :-1, :],
                    y_all,
                    x_all[:, -1:, :]
                )

                y_all = torch.cat([y_all, y_pred], dim=1)

                torch.cuda.empty_cache()

        final_pts = x_best[0].detach().cpu().numpy()

        return history, final_pts

    else:
        raise ValueError(f"Unknown method: {method}")


# -----------------------------
# RMSE (TEACHER)
# -----------------------------
def calculate_rmse(x, y, mask, teacher, x_new, scales):
    x_cuda = torch.tensor(x, dtype=torch.float32).to(DEVICE)
    y_cuda = torch.tensor(y, dtype=torch.float32).to(DEVICE)[..., None]

    final_mask = mask.copy()

    if len(x_new) > 0:
        dists = np.linalg.norm(x_new[:, None] - x[None, :], axis=-1)
        idx = dists.argmin(axis=1)
        final_mask[idx] = True

    x_context = torch.tensor(x[final_mask], dtype=torch.float32).to(DEVICE)
    y_context = torch.tensor(y[:, final_mask], dtype=torch.float32).to(DEVICE)[..., None]

    x_context = repeat(x_context, 'b d -> t b d', t=y.shape[0])

    preds = []
    with torch.no_grad():
        for i in range(0, x.shape[0], 1024):
            xt = x_cuda[i:i+1024]
            xt = repeat(xt, 'b d -> t b d', t=y.shape[0])
            pred, _ = teacher.predict(x_context, y_context, xt)
            preds.append(pred)

    preds = torch.cat(preds, dim=1)

    # 🔥 UN-SCALE (CRITICAL)
    def unscale(t):
        mean = scales['PM25']['mean']
        std = scales['PM25']['std']
        return torch.exp(t * std + mean)

    preds_unscaled = unscale(preds)
    y_unscaled = unscale(y_cuda)

    rmse = torch.sqrt(((preds_unscaled - y_unscaled) ** 2).mean()).item()

    return rmse

# -----------------------------
# PLOT
# -----------------------------
def plot_map(base_pts, new_pts):
    fig = go.Figure()

    # Existing sensors (blue)
    fig.add_trace(go.Scattergeo(
        lon=base_pts[:, 1],
        lat=base_pts[:, 0],
        mode='markers',
        marker=dict(color='blue', size=5, opacity=0.7),
        name='Existing Sensors'
    ))

    # New sensors (red)
    fig.add_trace(go.Scattergeo(
        lon=new_pts[:, 1],
        lat=new_pts[:, 0],
        mode='markers',
        marker=dict(color='red', size=7),
        name='Optimized Sensors'
    ))

    # 🔥 India-focused layout
    fig.update_layout(
        geo=dict(
            projection_type='mercator',

            # 🔥 HARD bounds for India (very important)
            lonaxis=dict(range=[67, 97]),
            lataxis=dict(range=[4, 39]),

            showland=True,
            landcolor="rgb(240, 240, 240)",

            showcoastlines=True,
            coastlinecolor="black",

            showcountries=True,
            countrycolor="black",

            resolution=50,   # higher = sharper borders
        ),
        height=650,
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(x=0.01, y=0.99)
    )

    return fig

# -----------------------------
# MAIN TAB
# -----------------------------
def render_tab1():
    st.title("🌍 Live Sensor Placement (Distilled Model)")

    x, y, mask, model, teacher, coords = load_data_and_models()

    col1, col2 = st.columns(2)

    with col1:
        n_new = st.number_input("Number of sensors", 1, 10000, 50)

    with col2:
        method = st.selectbox("Method", ["Gumbel", "MaxVar"])

    if st.button("🚀 Run Optimization"):
        with st.spinner("Running model..."):
            history, final_pts = run_optimization(x, y, mask, model, n_new, method=method)

        st.success("Optimization complete!")

        # Animation
        st.subheader("🎬 Sensor Evolution")

        base_pts = coords[mask]

        with st.spinner("Rendering video..."):
            video_path = create_animation(
                history,
                x,
                coords,
                base_pts,
                n_frames=20,
                seconds_per_frame=1.5
            )

        st.video(video_path)
        
        # Final RMSE
        st.subheader("📊 Evaluation")
        with open("data/scale_dict.json") as f:
            scales = json.load(f)
        rmse = calculate_rmse(x, y, mask, teacher, final_pts, scales)
        st.metric("Final RMSE", f"{rmse:.4f}")


if __name__ == "__main__":
    render_tab1()