import os
import sys

import numpy as np
import streamlit as st
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from theme import make_nav_css

st.set_page_config(page_title="V2V Training Curves", layout="wide")

st.markdown(make_nav_css(), unsafe_allow_html=True)
st.markdown("""
<style>
 .page-subtitle { color: #4B5563 !important; font-size: 22px; margin: 0.1rem 0 0; }
 .ds-label {
   font-size: 13px; font-weight: 700; letter-spacing: 0.08em;
   text-transform: uppercase; color: #2563EB !important;
   margin: 0 0 2px;
 }
 .ds-title {
   font-size: 32px; font-weight: 800; color: #0F172A !important;
   line-height: 1.15; margin: 0 0 4px;
 }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="v2v-site-title">Semantic V2V Communication</div>
<nav class="v2v-nav">
  <a href="/" class="v2v-tab" target="_self">Dashboard</a>
  <a href="/analysis" class="v2v-tab" target="_self">Analysis</a>
  <a href="/tensorboard" class="v2v-tab active" target="_self">TensorBoard</a>
</nav>
""", unsafe_allow_html=True)

st.title("Training Curves — Model Comparison")
st.markdown(
    '<p class="page-subtitle">'
    "mAP@0.5 vs epoch — top 5 runs per fusion model, per dataset. "
    "Best run shown as solid line; others are dashed."
    "</p>",
    unsafe_allow_html=True,
)
st.info("Dummy data — replace with real TensorBoard event logs once wired up.", icon="ℹ️")
st.divider()

# ── Design constants (matching analysis.py) ───────────────────────────────────
_LIGHT = dict(
    template="plotly_white",
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    font=dict(family="Inter, sans-serif", color="#374151", size=12),
)
_AXIS = dict(gridcolor="#F3F4F6", linecolor="#D1D5DB", tickfont=dict(size=11, color="#374151"))
_TITLE_FONT = dict(size=15, color="#111827")
_AXIS_TITLE = dict(size=12, color="#374151")

FUSION_COLORS = {
    "early":        "#4C72B0",
    "intermediate": "#55A868",
    "late":         "#DD8452",
}
_OTHER_PALETTE = ["#AAAAAA", "#B0B8C8", "#BBBBBB", "#C5CDD8"]


# ── Dummy-data generator ──────────────────────────────────────────────────────

def _curve(total_ep: int, peak: float, noise: float = 0.018, seed: int = 0) -> dict:
    """Smooth smoothstep training curve with light noise, sampled every 10 epochs."""
    rng = np.random.default_rng(seed)
    xs = list(range(10, total_ep + 1, 10))
    t = np.array([x / total_ep for x in xs])
    plateau = 0.62
    t_s = np.clip(t / plateau, 0, 1)
    base = peak * (3 * t_s ** 2 - 2 * t_s ** 3)
    y = np.clip(base + rng.normal(0, noise, len(xs)), 0.04, 0.80)
    return {x: round(float(v), 4) for x, v in zip(xs, y)}


# ── Run specs ─────────────────────────────────────────────────────────────────
# RUNS[dataset][fusion] → list of run dicts
# Each run: label, lr, bs (batch_size), ep (epochs), peak (target mAP), is_best, seed

RUNS: dict = {
    "lidar_64": {
        "early": [
            {"label": "lr=2e-3 bs=4 ep=150", "lr": 0.002, "bs": 4, "ep": 150, "peak": 0.344, "is_best": True,  "seed": 1},
            {"label": "lr=1e-3 bs=4 ep=150", "lr": 0.001, "bs": 4, "ep": 150, "peak": 0.310, "is_best": False, "seed": 4},
            {"label": "lr=2e-3 bs=2 ep=100", "lr": 0.002, "bs": 2, "ep": 100, "peak": 0.265, "is_best": False, "seed": 2},
            {"label": "lr=3e-3 bs=2 ep=100", "lr": 0.003, "bs": 2, "ep": 100, "peak": 0.285, "is_best": False, "seed": 5},
            {"label": "lr=2e-3 bs=2 ep=30",  "lr": 0.002, "bs": 2, "ep": 30,  "peak": 0.218, "is_best": False, "seed": 3},
        ],
        "intermediate": [
            {"label": "lr=1e-3 bs=2 ep=150", "lr": 0.001, "bs": 2, "ep": 150, "peak": 0.416, "is_best": True,  "seed": 7},
            {"label": "lr=1e-3 bs=2 ep=100", "lr": 0.001, "bs": 2, "ep": 100, "peak": 0.391, "is_best": False, "seed": 6},
            {"label": "lr=2e-3 bs=2 ep=100", "lr": 0.002, "bs": 2, "ep": 100, "peak": 0.369, "is_best": False, "seed": 8},
            {"label": "lr=1e-3 bs=4 ep=100", "lr": 0.001, "bs": 4, "ep": 100, "peak": 0.355, "is_best": False, "seed": 9},
            {"label": "lr=2e-3 bs=4 ep=150", "lr": 0.002, "bs": 4, "ep": 150, "peak": 0.340, "is_best": False, "seed": 10},
        ],
        "late": [
            {"label": "lr=2e-3 bs=4 ep=150 (b)",  "lr": 0.002, "bs": 4, "ep": 150, "peak": 0.303, "is_best": True,  "seed": 12},
            {"label": "lr=2e-3 bs=4 ep=150 (a)",  "lr": 0.002, "bs": 4, "ep": 150, "peak": 0.270, "is_best": False, "seed": 11},
            {"label": "lr=3e-3 bs=4 ep=150",      "lr": 0.003, "bs": 4, "ep": 150, "peak": 0.260, "is_best": False, "seed": 15},
            {"label": "lr=1e-3 bs=2 ep=100",      "lr": 0.001, "bs": 2, "ep": 100, "peak": 0.255, "is_best": False, "seed": 13},
            {"label": "lr=2e-3 bs=2 ep=100",      "lr": 0.002, "bs": 2, "ep": 100, "peak": 0.242, "is_best": False, "seed": 14},
        ],
    },
    "lidar_128": {
        "early": [
            {"label": "lr=2e-3 bs=4 ep=150", "lr": 0.002, "bs": 4, "ep": 150, "peak": 0.448, "is_best": True,  "seed": 21},
            {"label": "lr=1e-3 bs=4 ep=150", "lr": 0.001, "bs": 4, "ep": 150, "peak": 0.415, "is_best": False, "seed": 23},
            {"label": "lr=2e-3 bs=2 ep=100", "lr": 0.002, "bs": 2, "ep": 100, "peak": 0.382, "is_best": False, "seed": 22},
            {"label": "lr=3e-3 bs=2 ep=100", "lr": 0.003, "bs": 2, "ep": 100, "peak": 0.360, "is_best": False, "seed": 24},
            {"label": "lr=2e-3 bs=2 ep=50",  "lr": 0.002, "bs": 2, "ep": 50,  "peak": 0.325, "is_best": False, "seed": 25},
        ],
        "intermediate": [
            {"label": "lr=1e-3 bs=2 ep=150", "lr": 0.001, "bs": 2, "ep": 150, "peak": 0.516, "is_best": True,  "seed": 26},
            {"label": "lr=1e-3 bs=2 ep=100", "lr": 0.001, "bs": 2, "ep": 100, "peak": 0.490, "is_best": False, "seed": 27},
            {"label": "lr=2e-3 bs=2 ep=100", "lr": 0.002, "bs": 2, "ep": 100, "peak": 0.462, "is_best": False, "seed": 28},
            {"label": "lr=1e-3 bs=4 ep=150", "lr": 0.001, "bs": 4, "ep": 150, "peak": 0.445, "is_best": False, "seed": 29},
            {"label": "lr=2e-3 bs=4 ep=100", "lr": 0.002, "bs": 4, "ep": 100, "peak": 0.430, "is_best": False, "seed": 30},
        ],
        "late": [
            {"label": "lr=2e-3 bs=4 ep=150", "lr": 0.002, "bs": 4, "ep": 150, "peak": 0.388, "is_best": True,  "seed": 31},
            {"label": "lr=1e-3 bs=4 ep=150", "lr": 0.001, "bs": 4, "ep": 150, "peak": 0.365, "is_best": False, "seed": 32},
            {"label": "lr=2e-3 bs=2 ep=150", "lr": 0.002, "bs": 2, "ep": 150, "peak": 0.348, "is_best": False, "seed": 33},
            {"label": "lr=3e-3 bs=4 ep=100", "lr": 0.003, "bs": 4, "ep": 100, "peak": 0.330, "is_best": False, "seed": 34},
            {"label": "lr=2e-3 bs=4 ep=100", "lr": 0.002, "bs": 4, "ep": 100, "peak": 0.315, "is_best": False, "seed": 35},
        ],
    },
    "lidar_cam": {
        "early": [
            {"label": "lr=2e-3 bs=2 ep=100", "lr": 0.002, "bs": 2, "ep": 100, "peak": 0.305, "is_best": True,  "seed": 41},
            {"label": "lr=1e-3 bs=2 ep=150", "lr": 0.001, "bs": 2, "ep": 150, "peak": 0.278, "is_best": False, "seed": 42},
            {"label": "lr=1e-3 bs=4 ep=100", "lr": 0.001, "bs": 4, "ep": 100, "peak": 0.255, "is_best": False, "seed": 45},
            {"label": "lr=2e-3 bs=4 ep=100", "lr": 0.002, "bs": 4, "ep": 100, "peak": 0.261, "is_best": False, "seed": 43},
            {"label": "lr=3e-3 bs=2 ep=100", "lr": 0.003, "bs": 2, "ep": 100, "peak": 0.245, "is_best": False, "seed": 44},
        ],
        "intermediate": [
            {"label": "lr=1e-3 bs=2 ep=150", "lr": 0.001, "bs": 2, "ep": 150, "peak": 0.358, "is_best": True,  "seed": 46},
            {"label": "lr=1e-3 bs=2 ep=100", "lr": 0.001, "bs": 2, "ep": 100, "peak": 0.332, "is_best": False, "seed": 47},
            {"label": "lr=2e-3 bs=2 ep=100", "lr": 0.002, "bs": 2, "ep": 100, "peak": 0.318, "is_best": False, "seed": 48},
            {"label": "lr=1e-3 bs=4 ep=150", "lr": 0.001, "bs": 4, "ep": 150, "peak": 0.308, "is_best": False, "seed": 49},
            {"label": "lr=2e-3 bs=4 ep=100", "lr": 0.002, "bs": 4, "ep": 100, "peak": 0.295, "is_best": False, "seed": 50},
        ],
        "late": [
            {"label": "lr=2e-3 bs=4 ep=150", "lr": 0.002, "bs": 4, "ep": 150, "peak": 0.262, "is_best": True,  "seed": 51},
            {"label": "lr=1e-3 bs=4 ep=150", "lr": 0.001, "bs": 4, "ep": 150, "peak": 0.240, "is_best": False, "seed": 52},
            {"label": "lr=1e-3 bs=2 ep=100", "lr": 0.001, "bs": 2, "ep": 100, "peak": 0.228, "is_best": False, "seed": 55},
            {"label": "lr=2e-3 bs=2 ep=100", "lr": 0.002, "bs": 2, "ep": 100, "peak": 0.225, "is_best": False, "seed": 53},
            {"label": "lr=3e-3 bs=2 ep=100", "lr": 0.003, "bs": 2, "ep": 100, "peak": 0.215, "is_best": False, "seed": 54},
        ],
    },
}


# ── Chart builder ─────────────────────────────────────────────────────────────

def make_fusion_chart(run_specs: list, fusion: str) -> go.Figure:
    color = FUSION_COLORS[fusion]
    fig = go.Figure()
    other_i = 0

    for r in run_specs:
        curve = _curve(r["ep"], r["peak"], seed=r["seed"])
        xs = sorted(curve)
        ys = [curve[x] for x in xs]
        best = r["is_best"]

        if best:
            line_kw   = dict(color=color, width=2.5, dash="solid")
            marker_kw = dict(size=6, color=color, line=dict(color="white", width=1))
            opacity   = 1.0
        else:
            muted     = _OTHER_PALETTE[other_i % len(_OTHER_PALETTE)]
            other_i  += 1
            line_kw   = dict(color=muted, width=1.5, dash="dash")
            marker_kw = dict(size=4, color=muted)
            opacity   = 0.70

        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode="lines+markers",
            name=r["label"],
            line=line_kw,
            marker=marker_kw,
            opacity=opacity,
            hovertemplate=(
                "Epoch %{x}<br>"
                "mAP@0.5: %{y:.4f}<br>"
                f"lr={r['lr']}  bs={r['bs']}  ep={r['ep']}"
                f"<extra>{r['label']}</extra>"
            ),
        ))

    fig.update_layout(
        **_LIGHT,
        title=dict(
            text=f"{fusion.capitalize()} Fusion",
            font=_TITLE_FONT,
            x=0, xanchor="left",
        ),
        height=310,
        showlegend=False,
        margin=dict(l=52, r=14, t=44, b=48),
        xaxis=dict(**_AXIS, title=dict(text="Epoch", font=_AXIS_TITLE)),
        yaxis=dict(**_AXIS, title=dict(text="mAP@0.5", font=_AXIS_TITLE), range=[0, 0.65]),
        hovermode="x unified",
    )
    return fig


# ── Legend helper (shown once per row) ───────────────────────────────────────

def _row_legend(fusion: str):
    color = FUSION_COLORS[fusion]
    st.markdown(
        f'<span style="display:inline-block;width:18px;height:3px;'
        f'background:{color};vertical-align:middle;margin-right:6px;"></span>'
        f'<span style="font-size:12px;color:#374151;">Best run — solid</span>'
        f'&nbsp;&nbsp;'
        f'<span style="display:inline-block;width:18px;height:2px;'
        f'background:#AAAAAA;vertical-align:middle;margin-right:6px;border-top:2px dashed #AAAAAA;"></span>'
        f'<span style="font-size:12px;color:#374151;">Other runs — dashed</span>',
        unsafe_allow_html=True,
    )


# ── Page layout: 3 dataset rows × 3 fusion columns ───────────────────────────

DATASETS = [
    ("lidar_64",  "LiDAR-64",  "64-beam LiDAR"),
    ("lidar_128", "LiDAR-128", "128-beam LiDAR"),
    ("lidar_cam", "LiDAR-Cam", "Camera + LiDAR"),
]
FUSIONS = ["early", "intermediate", "late"]

_cfg = {"displayModeBar": False}

for ds_key, ds_short, ds_desc in DATASETS:
    st.markdown(
        f'<p class="ds-label">{ds_desc}</p>'
        f'<p class="ds-title">{ds_short}</p>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    for col, fusion in zip([col1, col2, col3], FUSIONS):
        with col:
            fig = make_fusion_chart(RUNS[ds_key][fusion], fusion)
            st.plotly_chart(fig, use_container_width=True, config=_cfg)

            # Best-run summary line
            best = next(r for r in RUNS[ds_key][fusion] if r["is_best"])
            st.caption(
                f"★ Best: {best['label']} — peak mAP ≈ **{best['peak']:.3f}**"
            )

    st.divider()

st.caption("FYP — Semantic V2V Communication for Autonomous Cooperative Perception")
