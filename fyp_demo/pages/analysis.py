from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(page_title="V2V Analysis", layout="wide")


# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
 /* ── Page background ── */
 .stApp, [data-testid="stAppViewContainer"] {
   background-color: #FFFFFF !important;
   color: #111827 !important;
 }

 [data-testid="stHeader"] { background-color: #FFFFFF !important; }

 h1, h2, h3, h4, h5, h6,
 .stMarkdown p, p, label { color: #111827 !important; }

 hr { border-color: #B0B8C8 !important; }
 .stCaption, medium { color: #4B5563 !important; }

 /* ── Site title ── */
 .v2v-site-title {
   font-size: 45px;
   font-weight: 700;
   color: #111827 !important;
   margin: 0;
   padding: 8px 0 14px;
   letter-spacing: -0.01em;
   line-height: 1.1;
 }

 /* ── Nav underline tabs ── */
 .v2v-nav {
   display: flex;
   border-bottom: 1.5px solid #E5E7EB;
   margin-bottom: 16px;
   padding: 0;
   gap: 0;
 }
 .v2v-tab {
   display: inline-block;
   padding: 10px 20px 10px 0;
   font-size: 1.5rem;
   font-weight: 500;
   color: #6B7280 !important;
   text-decoration: none !important;
   border-bottom: 2px solid transparent;
   margin-bottom: -1.5px;
   margin-right: 8px;
   transition: color 0.18s ease, border-color 0.18s ease;
 }
 .v2v-tab:hover {
   color: #111827 !important;
   text-decoration: none !important;
 }
 .v2v-tab.active {
   color: #10B981 !important;
   border-bottom-color: #10B981;
   font-weight: 600;
 }

 /* ── Widgets ── */
 .stSelectbox > div > div,
 .stMultiSelect > div > div {
   background: #F9FAFB !important;
   border: 1px solid #9CA3AF !important;
   color: #111827 !important;
 }

 .stSelectbox {
   min-width: 160px;
 }

 /* Selected value text */
 .stSelectbox [data-baseweb="select"] > div {
   padding-right: 2.2rem !important;
   position: relative;
   font-size: 23px !important;
 }

 /* Dropdown list items */
 [data-baseweb="menu"] li,
 [role="option"],
 [data-baseweb="popover"] li {
   font-size: 23px !important;
 }

[data-baseweb="tag"] {
   background: #EEF2FF !important;
   color: #1D4ED8 !important;
   border: 1px solid #BFDBFE !important;
   border-radius: 20px !important;
 }

 [data-baseweb="tag"] span { color: #1D4ED8 !important; }

 [data-testid="stRadio"] label {
   color: #111827 !important;
   font-size: 21px !important;
   background: transparent !important;
   border: none !important;
   padding: 0 !important;
 }

 [data-testid="stRadio"] {
   min-width: 180px;
 }

 [data-testid="stRadio"] > div {
   column-gap: 0.8rem !important;
   flex-direction: row !important;
   flex-wrap: nowrap !important;
  }

 /* ── Locally scoped slide/card styling ── */
 [data-testid="stVerticalBlockBorderWrapper"]:has(.noise-card-anchor):not(:has([data-testid="stVerticalBlockBorderWrapper"] .noise-card-anchor)) {
   background: #FFFFFF !important;
   border: 1px solid rgba(17,24,39,0.13) !important;
   border-radius: 14px !important;
   box-shadow: 0 18px 44px rgba(15,23,42,0.13) !important;
   padding: 26px 28px 20px !important;
 }

 [data-testid="stVerticalBlockBorderWrapper"]:has(.noise-card-anchor):not(:has([data-testid="stVerticalBlockBorderWrapper"] .noise-card-anchor)) [data-testid="stVerticalBlock"] {
   gap: 0.65rem !important;
 }

 .noise-card-anchor {
   display: none;
 }

 .section-eyebrow {
   color: #2563EB !important;
   font-size: 21px;
   font-weight: 800;
   letter-spacing: 0.09em;
   margin: 0 0 0.15rem;
   text-transform: uppercase;
 }

 .noise-title {
   color: #0F172A !important;
   font-size: 50px;
   font-weight: 800;
   letter-spacing: 0;
   line-height: 1.15;
   margin: 0;
 }

 .noise-caption {
   color: #475569 !important;
   font-size: 25px;
   line-height: 1.5;
   margin: 0.25rem 0 1.35rem;
   max-width: 100%;
 }

 .filter-label {
   color: #64748B !important;
   font-size: 21px;
   font-weight: 700;
   letter-spacing: 0.06em;
   margin-bottom: 0.2rem;
   text-transform: uppercase;
 }

 .page-subtitle {
   color: #4B5563 !important;
   font-size: 22px;
   margin: 0.1rem 0 0;
 }

 .filter-row-spacer {
   height: 1.8rem;
 }
</style>
""", unsafe_allow_html=True)


# ── Navigation ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="v2v-site-title">Semantic V2V Communication</div>
<nav class="v2v-nav">
  <a href="/" class="v2v-tab">Dashboard</a>
  <a href="/analysis" class="v2v-tab active">Analysis</a>
</nav>
""", unsafe_allow_html=True)


st.title("Fusion Model Analysis")
st.markdown('<p class="page-subtitle">Quantitative evaluation of fusion strategies and datasets</p>', unsafe_allow_html=True)

st.divider()

# ── Data ──────────────────────────────────────────────────────────────────────
CSV_PATH = Path(__file__).parent.parent.parent / "noise" / "ap_vs_snr_intermediate_rayleigh_awgn.csv"


@st.cache_data
def load_snr_data():
    df = pd.read_csv(CSV_PATH)
    order = ["∞ (clean)", "+30.0 dB", "+10.0 dB", "+0.0 dB", "-30.0 dB"]
    df["snr_label"] = pd.Categorical(df["snr_label"], categories=order, ordered=True)
    return df.sort_values("snr_label").reset_index(drop=True)


df = load_snr_data()


# ═══════════════════════════════════════════════════════════════════════════════
# Section: Noise Robustness
# ═══════════════════════════════════════════════════════════════════════════════
with st.container(border=True):
    st.markdown('<span class="noise-card-anchor"></span>', unsafe_allow_html=True)

    st.markdown(
        """
        <h2 class="noise-title">Noise Robustness</h2>
        <p class="noise-caption">
          Average Precision response across SNR levels for the Intermediate
          fusion model under Rayleigh + AWGN channel noise.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="filter-row-spacer"></div>', unsafe_allow_html=True)

    fc1, fc2, _ = st.columns([2.4, 2.8, 2.8])

    with fc1:
        st.markdown('<div class="filter-label">IoU threshold</div>', unsafe_allow_html=True)
        iou_choice = st.selectbox(
            "IoU Threshold",
            ["0.3", "0.5", "0.7"],
            index=1,
            label_visibility="collapsed",
        )

    with fc2:
        st.markdown('<div class="filter-label">Detection class</div>', unsafe_allow_html=True)
        class_options = ["Vehicle", "Pedestrian", "Truck", "mAP"]
        selected_class = st.selectbox(
            "Class",
            class_options,
            index=0,
            label_visibility="collapsed",
        )

    class_cols = {
        "Vehicle": f"vehicle_AP@{iou_choice}",
        "Pedestrian": f"pedestrian_AP@{iou_choice}",
        "Truck": f"truck_AP@{iou_choice}",
        "mAP": f"mAP_AP@{iou_choice}",
    }

    class_colors = {
        "Vehicle": "#2563EB",
        "Pedestrian": "#D97706",
        "Truck": "#059669",
        "mAP": "#7C3AED",
    }

    x_labels = df["snr_label"].tolist()
    col = class_cols[selected_class]
    color = class_colors[selected_class]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x_labels,
        y=df[col].tolist(),
        mode="lines+markers",
        name=selected_class,
        line=dict(color=color, width=3),
        marker=dict(size=9, color=color, line=dict(color="white", width=1.5)),
        hovertemplate=(
            f"<b>%{{fullData.name}}</b><br>"
            f"SNR: %{{x}}<br>"
            f"AP @ IoU {iou_choice}: %{{y:.4f}}<extra></extra>"
        ),
    ))

    fig.add_vrect(
        x0="+0.0 dB",
        x1="-30.0 dB",
        fillcolor="rgba(239,68,68,0.07)",
        layer="below",
        line_width=0,
        annotation_text="Degraded zone",
        annotation_position="top left",
        annotation=dict(
            font=dict(color="#B91C1C", size=20),
            bgcolor="rgba(254,226,226,0.92)",
            bordercolor="#FCA5A5",
            borderwidth=1,
            borderpad=4,
        ),
    )

    st.divider()

    fig.update_layout(
        template="plotly_white",
        height=520,
        margin=dict(l=100, r=28, t=72, b=110),
        title=dict(
            text=f"Average Precision vs SNR — IoU {iou_choice}",
            font=dict(size=27, color="#111827"),
            x=0,
            xanchor="left",
        ),
        xaxis=dict(
            title=dict(text="SNR Level", font=dict(size=23, color="#374151")),
            tickfont=dict(size=21, color="#374151"),
            gridcolor="#F3F4F6",
            linecolor="#D1D5DB",
            showgrid=True,
        ),
        yaxis=dict(
            title=dict(text=f"AP @ IoU {iou_choice}", font=dict(size=23, color="#374151")),
            tickfont=dict(size=21, color="#374151"),
            gridcolor="#F3F4F6",
            linecolor="#D1D5DB",
            showgrid=True,
            range=[0, max(df[col]) * 1.18],
            tickformat=".2f",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.28,
            xanchor="center",
            x=0.5,
            font=dict(size=21, color="#374151"),
            bgcolor="rgba(255,255,255,0)",
            borderwidth=0,
        ),
        hovermode="x unified",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
    )

    st.markdown('<div style="height: 2rem;"></div>', unsafe_allow_html=True)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "modeBarButtonsToRemove": ["select2d", "lasso2d"],
            "displaylogo": False,
        },
    )

st.caption("FYP — Semantic V2V Communication for Autonomous Cooperative Perception")
