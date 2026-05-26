import os
import sys

import streamlit as st
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from theme import make_nav_css
from components.chart_data import TENSORBOARD_RUNS

st.set_page_config(page_title="V2V Training Curves", layout="wide", initial_sidebar_state="collapsed")

st.markdown(make_nav_css(), unsafe_allow_html=True)
st.markdown("""
<style>
 .tb-hero {
   background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 60%, #ffffff 100%);
   border: 1px solid #bfdbfe;
   border-radius: 20px;
   padding: 52px 48px 44px;
   margin-bottom: 40px;
   position: relative;
   overflow: hidden;
   box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
 }
 .tb-hero::after {
   content: '';
   position: absolute;
   top: -80px; right: -80px;
   width: 300px; height: 300px;
   background: radial-gradient(circle, #2563eb22 0%, transparent 65%);
   border-radius: 50%;
   pointer-events: none;
 }
 .tb-hero-eyebrow {
   font-family: 'JetBrains Mono', monospace;
   font-size: 21px;
   color: #2563eb;
   letter-spacing: 0.2em;
   text-transform: uppercase;
   margin-bottom: 14px;
 }
 .tb-hero-title {
   font-size: 46px;
   font-weight: 600;
   color: #0f172a;
   line-height: 1.2;
   margin-bottom: 12px;
 }
 .tb-hero-title span { color: #2563eb; }
 .tb-hero-sub {
   font-size: 32px;
   color: #475569;
   max-width: 600px;
   line-height: 1.8;
   margin: 0;
 }
 .ds-label {
   font-family: 'JetBrains Mono', monospace;
   font-size: 19px; font-weight: 600; letter-spacing: 0.18em;
   text-transform: uppercase; color: #2563EB !important;
   margin: 0 0 8px;
 }
 .ds-title {
   font-size: 38px; font-weight: 600; color: #0F172A !important;
   line-height: 1.15; margin: 0 0 6px;
 }
 .stMarkdown p { font-size: 20px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<nav class="v2v-nav">
  <a href="/" class="v2v-tab" target="_self">Dashboard</a>
  <a href="/analysis" class="v2v-tab" target="_self">Analysis</a>
  <a href="/tensorboard" class="v2v-tab active" target="_self">Summary</a>
</nav>
<div class="tb-hero">
  <div class="tb-hero-eyebrow">FYP · Semantic V2V Communication</div>
  <div class="tb-hero-title">Training Curves — <span>Model Comparison</span></div>
  <div class="tb-hero-sub">
    mAP vs epoch for all runs per fusion model, per dataset.
    Best run shown as solid line; others as dashed.
  </div>
</div>
""", unsafe_allow_html=True)

# ── Design constants ──────────────────────────────────────────────────────────
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

IOU_CHOICE = 0.5


def make_fusion_chart(run_specs: list, fusion: str) -> go.Figure:
    color = FUSION_COLORS[fusion]
    fig = go.Figure()
    other_i = 0

    for r in run_specs:
        xs = sorted(r["curves"])
        ys = [r["curves"][x] for x in xs]

        if r["is_best"]:
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
                f"mAP@{IOU_CHOICE}: %{{y:.4f}}"
                f"<extra>{r['label']}</extra>"
            ),
        ))

    max_ep = max((max(r["curves"]) for r in run_specs), default=150)

    fig.update_layout(
        **_LIGHT,
        title=dict(text=f"{fusion.capitalize()} Fusion", font=_TITLE_FONT, x=0, xanchor="left"),
        height=310,
        showlegend=False,
        margin=dict(l=52, r=14, t=44, b=48),
        xaxis=dict(**_AXIS, title=dict(text="Epoch", font=_AXIS_TITLE), range=[0, max_ep * 1.08]),
        yaxis=dict(**_AXIS, title=dict(text=f"mAP@{IOU_CHOICE}", font=_AXIS_TITLE), range=[0, 0.65]),
        hovermode="x unified",
    )
    return fig


# ── Page layout: dataset rows × fusion columns ────────────────────────────────
DATASETS = [
    ("lidar_64",  "LiDAR-64",  "64-beam LiDAR"),
    ("lidar_128", "LiDAR-128", "128-beam LiDAR"),
    ("lidar_cam", "LiDAR-Cam", "Camera + LiDAR"),
]
FUSIONS = ["early", "intermediate", "late"]
_cfg = {"displayModeBar": False}

for ds_key, ds_short, ds_desc in DATASETS:
    if ds_key not in TENSORBOARD_RUNS:
        continue

    st.markdown(
        f'<p class="ds-label">{ds_desc}</p>'
        f'<p class="ds-title">{ds_short}</p>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    for col, fusion in zip([col1, col2, col3], FUSIONS):
        with col:
            run_list = TENSORBOARD_RUNS[ds_key].get(fusion, [])
            if not run_list:
                st.markdown(f"*No {fusion} fusion runs for {ds_short}.*")
                continue

            fig = make_fusion_chart(run_list, fusion)
            st.plotly_chart(fig, use_container_width=True, config=_cfg)

            best = next(r for r in run_list if r["is_best"])
            best_peak = max(best["curves"].values())
            st.caption(f"★ Best: **{best['label']}** — peak mAP@{IOU_CHOICE} = **{best_peak:.3f}**")

    st.divider()

st.caption("FYP — Semantic V2V Communication for Autonomous Cooperative Perception")
