import base64
import os
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from theme import make_nav_css

st.set_page_config(page_title="V2V Analysis", layout="wide", initial_sidebar_state="collapsed")


# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(make_nav_css(), unsafe_allow_html=True)
st.markdown("""
<style>
 /* ── Widgets ── */
 .stSelectbox > div > div,
 .stMultiSelect > div > div {
   background: #F9FAFB !important;
   border: 1px solid #9CA3AF !important;
   color: #111827 !important;
 }

 .stSelectbox {
   min-width: 260px;
 }

 /* Disable typing in selectbox — dropdown only */
 [data-baseweb="select"] input {
   pointer-events: none !important;
   caret-color: transparent !important;
 }

 /* Selected value text */
 .stSelectbox [data-baseweb="select"] > div {
   padding-right: 2.2rem !important;
   padding-top: 10px !important;
   padding-bottom: 10px !important;
   position: relative;
   font-size: 23px !important;
   min-height: 52px !important;
   align-items: center !important;
 }

 /* Dropdown popover container */
 [data-baseweb="popover"] {
   background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 60%, #ffffff 100%) !important;
   border: 1.5px solid #D1D5DB !important;
   border-radius: 8px !important;
   box-shadow: none !important;
   overflow: hidden !important;
 }

 /* Remove separator lines between items */
 [data-baseweb="menu"] ul {
   padding: 4px 0 !important;
 }
 [role="option"] {
   font-size: 20px !important;
   color: #374151 !important;
   padding: 10px 18px !important;
   border: none !important;
   border-bottom: none !important;
   background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 60%, #ffffff 100%) !important;
   transition: background 0.1s ease !important;
 }

 /* Hover state */
 [role="option"]:hover {
   background: rgba(37, 99, 235, 0.10) !important;
   color: #111827 !important;
 }

 /* Selected item */
 [aria-selected="true"][role="option"] {
   background: rgba(37, 99, 235, 0.10) !important;
   color: #111827 !important;
   font-weight: 600 !important;
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

 /* ── Locally scoped card styling (noise section) ── */
 [data-testid="stVerticalBlockBorderWrapper"]:has(.noise-card-anchor):not(:has([data-testid="stVerticalBlockBorderWrapper"] .noise-card-anchor)) {
   background: #ffffff !important;
   border: 1px solid #9abbe6 !important;
   border-radius: 14px !important;
   box-shadow: 0 18px 44px rgba(15,23,42,0.13) !important;
   padding: 26px 28px 20px !important;
 }

 [data-testid="stVerticalBlockBorderWrapper"]:has(.noise-card-anchor):not(:has([data-testid="stVerticalBlockBorderWrapper"] .noise-card-anchor)) [data-testid="stVerticalBlock"] {
   gap: 0.65rem !important;
 }

 .noise-card-anchor { display: none; }

 /* ── Locally scoped card styling (cross-val section) ── */
 [data-testid="stVerticalBlockBorderWrapper"]:has(.cv-card-anchor):not(:has([data-testid="stVerticalBlockBorderWrapper"] .cv-card-anchor)) {
   background: #ffffff !important;
   border: 1px solid #9abbe6 !important;
   border-radius: 14px !important;
   box-shadow: 0 18px 44px rgba(15,23,42,0.13) !important;
   padding: 26px 28px 20px !important;
 }

 [data-testid="stVerticalBlockBorderWrapper"]:has(.cv-card-anchor):not(:has([data-testid="stVerticalBlockBorderWrapper"] .cv-card-anchor)) [data-testid="stVerticalBlock"] {
   gap: 0.65rem !important;
 }

 .cv-card-anchor { display: none; }

 /* ── Shared section typography ── */
 .section-eyebrow {
   color: #2563EB !important;
   font-size: 21px;
   font-weight: 800;
   letter-spacing: 0.09em;
   margin: 0 0 0.15rem;
   text-transform: uppercase;
 }

 .noise-title, .cv-title {
   color: #0F172A !important;
   font-size: 50px;
   font-weight: 800;
   letter-spacing: 0;
   line-height: 1.15;
   margin: 0;
 }

 .noise-caption, .cv-caption {
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

 .filter-row-spacer { height: 1.8rem; }

 /* ── Cross-val tab underline ── */
 [data-baseweb="tab-highlight"] {
   background-color: #10B981 !important;
 }
 [data-baseweb="tab"][aria-selected="true"] {
   color: #10B981 !important;
 }

 /* ── Cross-val KPI boxes ── */
 .cv-kpi {
   background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 60%, #ffffff 100%) !important;
   border: 1px solid #9abbe6 !important;
   border-radius: 14px !important;
   padding: 22px 20px !important;
   text-align: center !important;
   box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
 }
 .cv-kpi-val {
   font-size: 40px;
   font-weight: 800;
   color: #000000 !important;
   line-height: 1;
   margin-bottom: 6px;
 }
 .cv-kpi-label {
   font-size: 15px;
   color: #000000 !important;
   font-weight: 500;
   line-height: 1.4;
 }

 /* ── Card download icon ── */
 .card-dl-header { position: relative; }
 .card-download {
   position: absolute; top: 4px; right: 0;
   width: 32px; height: 32px; border-radius: 8px;
   display: flex; align-items: center; justify-content: center;
   background: #ffffff; border: 1px solid #9abbe6;
   color: #2563eb; text-decoration: none !important; font-size: 16px;
   cursor: pointer; transition: background 0.15s, box-shadow 0.15s;
 }
 .card-download:hover {
   background: #eff6ff;
   box-shadow: 0 0 12px #2563eb33;
 }
 .card-download::after {
   content: attr(data-tip);
   position: absolute; top: 50%; right: 120%;
   transform: translateY(-50%);
   white-space: nowrap;
   background: #0f172a; color: #ffffff;
   font-family: 'JetBrains Mono', monospace; font-size: 11px;
   padding: 5px 9px; border-radius: 6px;
   opacity: 0; pointer-events: none; transition: opacity 0.15s;
   z-index: 999;
 }
 .card-download:hover::after { opacity: 1; }

 /* ── Print / PDF export ── */
 @media print {
   /* Hide interactive chrome */
   [data-testid="stHeader"], [data-testid="stToolbar"],
   [data-testid="stSidebar"], .v2v-nav, .stButton > button,
   .stSelectbox, .stMultiSelect, [data-testid="stRadio"],
   .card-download, .filter-row-spacer,
   [data-baseweb="tab-list"],
   [class*="modebar"] { display: none !important; }

   /* Reveal ALL tab panels, not just the active one */
   [data-baseweb="tab-panel"] {
     display: block !important;
     visibility: visible !important;
     opacity: 1 !important;
     height: auto !important;
     overflow: visible !important;
   }

   /* Avoid splitting cards and charts across pages */
   [data-testid="stVerticalBlockBorderWrapper"],
   [data-testid="stPlotlyChart"] { page-break-inside: avoid; break-inside: avoid; }

   /* Tighter margins for paper */
   .block-container { padding: 0.4in 0.6in !important; max-width: 100% !important; }

   /* Keep text black */
   * { color: #000000 !important; }
 }

 /* ── PDF button ── */
 .pdf-btn {
   display: inline-flex; align-items: center; gap: 6px;
   padding: 6px 14px;
   font-family: 'Inter', sans-serif; font-size: 0.85rem; font-weight: 500;
   color: #2563eb !important; text-decoration: none !important;
   border: 1px solid #9abbe6; border-radius: 8px;
   background: white; cursor: pointer;
   transition: background 0.15s, box-shadow 0.15s;
   margin-left: auto;
 }
 .pdf-btn:hover { background: #eff6ff; box-shadow: 0 0 10px #2563eb22; }
 .nav-row { display: flex; align-items: center; }

 /* ── Hero card ── */
 .analysis-hero {
   background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 60%, #ffffff 100%);
   border: 1px solid #9abbe6;
   border-radius: 20px;
   padding: 52px 48px 44px;
   margin-bottom: 16px;
   position: relative;
   overflow: hidden;
   box-shadow: 0 1px 3px rgba(15,23,42,0.04);
 }
 .analysis-hero::after {
   content: '';
   position: absolute;
   top: -80px; right: -80px;
   width: 300px; height: 300px;
   background: radial-gradient(circle, #2563eb22 0%, transparent 65%);
   border-radius: 50%;
   pointer-events: none;
 }
 .analysis-hero-eyebrow {
   font-family: 'JetBrains Mono', monospace;
   font-size: 21px;
   color: #2563eb;
   letter-spacing: 0.2em;
   text-transform: uppercase;
   margin-bottom: 14px;
 }
 .analysis-hero-title {
   font-size: 46px;
   font-weight: 600;
   color: #0f172a;
   line-height: 1.2;
   margin-bottom: 12px;
 }
 .analysis-hero-sub {
   font-size: 32px;
   color: #475569;
   max-width: 600px;
   line-height: 1.8;
   margin: 0;
 }
 .stMarkdown p { font-size: 20px !important; }
</style>
""", unsafe_allow_html=True)


# ── Navigation ────────────────────────────────────────────────────────────────
st.markdown("""
<nav class="v2v-nav">
  <a href="/" class="v2v-tab" target="_self">Dashboard</a>
  <a href="/analysis" class="v2v-tab active" target="_self">Analysis</a>
  <a href="/tensorboard" class="v2v-tab" target="_self">Summary</a>
</nav>
""", unsafe_allow_html=True)

# ── Hero card ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="analysis-hero">
  <div class="analysis-hero-eyebrow">FYP · Semantic V2V Communication</div>
  <div class="analysis-hero-title">Fusion Model Analysis</div>
  <div class="analysis-hero-sub">
    Quantitative evaluation of early, intermediate, and late fusion strategies
    across the V2X-Real dataset. Explore detection performance, cross-validation
    results, and robustness under realistic channel noise conditions.
  </div>
</div>
""", unsafe_allow_html=True)

# ── PDF builder ──────────────────────────────────────────────────────────────
def _build_pdf() -> bytes:
    import os, tempfile
    from fpdf import FPDF

    sections = [
        ("Cross-Validation: mAP by Training Group",        "_pdf_fig1"),
        ("Cross-Validation: LiDAR-64 -> LiDAR-128 Gain",  "_pdf_fig2"),
        ("Cross-Validation: Cooperation Modes",            "_pdf_fig3"),
        ("Cross-Validation: Per-class AP",                 "_pdf_fig4"),
        ("Noise Robustness: Detection Under Channel Noise", "_pdf_fig_bar"),
        ("Noise Robustness: Average Precision vs SNR",     "_pdf_fig_snr"),
    ]

    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(auto=True, margin=10)

    for title, key in sections:
        fig = st.session_state.get(key)
        if fig is None:
            continue
        try:
            img_bytes = fig.to_image(format="png", width=1400, height=650, scale=1.5)
        except Exception:
            continue
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(img_bytes)
                tmp_path = tmp.name
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
            pdf.image(tmp_path, x=10, y=22, w=277)
        except Exception:
            continue
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    return bytes(pdf.output())


# ── Noise data ────────────────────────────────────────────────────────────────
SNR_CSV_PATH      = Path(__file__).parent.parent.parent / "noise" / "ap_vs_snr_late_rayleigh_awgn.csv"
AVG_SNR_CSV_PATH  = Path(__file__).parent.parent.parent / "noise" / "ap_vs_snr_early_rayleigh_awgn.csv"
INTER_CSV_PATH    = Path(__file__).parent.parent.parent / "noise" / "ap_vs_snr_intermediate_rayleigh_awgn.csv"
COMBINED_CSV_PATH = Path(__file__).parent.parent.parent / "noise" / "ap_vs_snr_combined_rayleigh_awgn.csv"


@st.cache_data
def load_avg_snr_data():
    return pd.read_csv(AVG_SNR_CSV_PATH)


@st.cache_data
def load_inter_snr_data():
    return pd.read_csv(INTER_CSV_PATH)


@st.cache_data
def load_late_snr_bar():
    df = pd.read_csv(SNR_CSV_PATH)
    return df[df["fusion_method"] == "late"].copy() if "fusion_method" in df.columns else df


@st.cache_data
def load_combined_snr_data():
    return pd.read_csv(COMBINED_CSV_PATH)


@st.cache_data
def load_snr_data():
    df = pd.read_csv(COMBINED_CSV_PATH)
    order = ["+0.0 dB", "+10.0 dB", "+20.0 dB", "+30.0 dB", "∞ (clean)"]
    df["snr_label"] = pd.Categorical(df["snr_label"], categories=order, ordered=True)
    df = df[df["snr_label"].notna()].copy()
    return df.sort_values(["fusion_method", "dataset", "snr_label"]).reset_index(drop=True)


snr_data_available = COMBINED_CSV_PATH.exists()
df = load_snr_data() if snr_data_available else None


# ── Cross-val data ────────────────────────────────────────────────────────────
CV_CSV_PATH = Path(__file__).parent.parent / "data" / "all_results.csv"


@st.cache_data
def load_cv_data():
    df = pd.read_csv(CV_CSV_PATH)
    df = df[df["dataset"] != "lidar_cameras"].copy()
    df["group_label"] = df["group"].map({
        "lidar64":         "LiDAR64-Trained",
        "real":            "Cameras-Trained",
        "lidar128_models": "LiDAR128-Trained",
    })
    df["model_label"] = df["model"].str.replace("_fusion_tuned", "").str.capitalize()
    df["dataset_label"] = df["dataset"].map({"lidar64": "LiDAR-64", "lidar128": "LiDAR-128"})
    return df


# Shared Plotly light theme matching teammate's style
_LIGHT = dict(
    template="plotly_white",
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    font=dict(family="Inter, sans-serif", color="#374151", size=14),
    legend=dict(font=dict(size=16, color="#374151"), bgcolor="rgba(255,255,255,0)", borderwidth=0),
)
_AXIS = dict(gridcolor="#F3F4F6", linecolor="#D1D5DB", tickfont=dict(size=16, color="#374151"))
_TITLE_FONT = dict(size=27, color="#111827")
_AXIS_TITLE_FONT = dict(size=20, color="#374151")

GROUP_COLORS = {
    "LiDAR64-Trained":  "#2563EB",
    "Cameras-Trained":  "#7C3AED",
    "LiDAR128-Trained": "#059669",
}
MODEL_COLORS = {"Early": "#2563EB", "Intermediate": "#059669", "Late": "#D97706"}
MODE_COLORS  = {"i2i": "#059669", "ic": "#7C3AED", "vc": "#2563EB", "v2v": "#DC2626"}
CLASS_COLORS = {"vehicle": "#2563EB", "pedestrian": "#D97706", "truck": "#059669"}


# ═══════════════════════════════════════════════════════════════════════════════
# Section: Cross-Validation Inference
# ═══════════════════════════════════════════════════════════════════════════════
with st.container(border=True):
    st.markdown('<span class="cv-card-anchor"></span>', unsafe_allow_html=True)

    _cv_b64 = base64.b64encode(CV_CSV_PATH.read_bytes()).decode("ascii") if CV_CSV_PATH.exists() else ""
    _cv_dl = (f'<a class="card-download" download="cross_validation_results.csv" '
              f'href="data:text/csv;base64,{_cv_b64}" data-tip="Download CSV">⬇</a>'
              if _cv_b64 else "")
    st.markdown(f"""
    <div class="card-dl-header">
      <div class="cv-title">Cross-Validation Inference</div>
      <p class="cv-caption">
        mAP@0.5 evaluated across 3 Fusion Models, 3 Training Groups,
        2 LiDAR Densities, and 4 cooperation modes on V2X-Real.
      </p>
      {_cv_dl}
    </div>
    """, unsafe_allow_html=True)

    # ── Load & aggregate ──────────────────────────────────────────
    cv_raw = load_cv_data()
    map_mask = (cv_raw["class"] == "mAP") & (cv_raw["iou"] == 0.5)
    pivot = (
        cv_raw[map_mask]
        .groupby(["group_label", "model_label", "dataset_label"])["AP"]
        .mean()
        .reset_index()
        .rename(columns={"AP": "mAP_05"})
    )
    mode_avg = (
        cv_raw[map_mask]
        .groupby("mode")["AP"]
        .mean()
        .reset_index()
        .rename(columns={"AP": "mAP_05"})
        .sort_values("mAP_05", ascending=False)
    )
    per_class = (
        cv_raw[(cv_raw["class"] != "mAP") & (cv_raw["iou"] == 0.5)]
        .groupby(["model_label", "class"])["AP"]
        .mean()
        .reset_index()
        .rename(columns={"AP": "AP_05"})
    )

    best      = pivot.loc[pivot.mAP_05.idxmax()]
    mode_best = mode_avg.iloc[0]
    mode_worst = mode_avg.iloc[-1]

    # ── KPI row ───────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    for col_widget, val, label in [
        (k1, "3", "Fusion Models"),
        (k2, "4", "Cooperation Modes"),
        (k3, "2", "Test Datasets"),
        (k4, "3", "Training Groups"),
    ]:
        with col_widget:
            st.markdown(f"""
            <div class="cv-kpi">
              <div class="cv-kpi-val">{val}</div>
              <div class="cv-kpi-label">{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="filter-row-spacer"></div>', unsafe_allow_html=True)
    st.divider()

    # ── Chart tabs ────────────────────────────────────────────────
    t1, t2, t3, t4 = st.tabs([
        "  Model Performance  ",
        "  Density Gain  ",
        "  Cooperation Mode  ",
        "  Per-class AP  ",
    ])

    # ── Tab 1: mAP overview ───────────────────────────────────────
    with t1:
        groups = list(GROUP_COLORS.keys())
        fig1 = make_subplots(
            rows=1, cols=3,
            subplot_titles=groups,
            shared_yaxes=True,
            horizontal_spacing=0.06,
        )
        for col_idx, group in enumerate(groups, 1):
            sub = pivot[pivot.group_label == group]
            for model, mc in MODEL_COLORS.items():
                row = sub[sub.model_label == model]
                vals = row.set_index("dataset_label")["mAP_05"]
                y_vals = [vals.get("LiDAR-64", 0), vals.get("LiDAR-128", 0)]
                fig1.add_trace(go.Bar(
                    name=model,
                    x=["LiDAR-64", "LiDAR-128"],
                    y=y_vals,
                    marker_color=mc,
                    marker_line_color="white", marker_line_width=1,
                    text=[f"{v:.3f}" for v in y_vals],
                    textposition="outside",
                    textfont=dict(size=11, color="#374151"),
                    showlegend=(col_idx == 1),
                ), row=1, col=col_idx)

        fig1.update_layout(
            **_LIGHT, barmode="group", height=460,
            margin=dict(l=60, r=28, t=80, b=60),
            title=dict(text="Cross-Validation Performance Across Datasets", font=_TITLE_FONT, x=0, xanchor="left"),
        )
        fig1.update_layout(legend=dict(font=dict(size=12, color="#374151"), bgcolor="rgba(255,255,255,0)", borderwidth=0))
        fig1.update_yaxes(range=[0, 0.60], **_AXIS, title_text="mAP@0.5", col=1)
        fig1.update_yaxes(range=[0, 0.60], **_AXIS, col=2)
        fig1.update_yaxes(range=[0, 0.60], **_AXIS, col=3)
        fig1.update_xaxes(**_AXIS)
        st.plotly_chart(fig1, use_container_width=True, config={"modeBarButtons": [["toImage"]], "displaylogo": False, "toImageButtonOptions": {"format": "png", "filename": "fusion_model_performance", "scale": 2}})
        st.session_state["_pdf_fig1"] = fig1
        st.markdown(
            f"**Best result:** {best.group_label} · {best.model_label} on {best.dataset_label} — "
            f"**mAP@0.5 = {best.mAP_05:.3f}**",
            unsafe_allow_html=False,
        )

    # ── Tab 2: Density gain ───────────────────────────────────────
    with t2:
        delta_rows = []
        for group in GROUP_COLORS:
            for model in MODEL_COLORS:
                v64  = pivot[(pivot.group_label == group) & (pivot.model_label == model) & (pivot.dataset_label == "LiDAR-64")]["mAP_05"]
                v128 = pivot[(pivot.group_label == group) & (pivot.model_label == model) & (pivot.dataset_label == "LiDAR-128")]["mAP_05"]
                if len(v64) and len(v128):
                    delta_rows.append({"group": group, "model": model, "delta": round(v128.values[0] - v64.values[0], 3)})
        delta_df = pd.DataFrame(delta_rows)

        fig2 = go.Figure()
        for group, gc in GROUP_COLORS.items():
            sub = delta_df[delta_df.group == group]
            colors = [MODEL_COLORS.get(m, gc) if d >= 0 else "#DC2626" for m, d in zip(sub.model.tolist(), sub.delta)]
            fig2.add_trace(go.Bar(
                name=group,
                x=sub.model.tolist(),
                y=sub.delta.tolist(),
                marker_color=colors, marker_line_color="white", marker_line_width=1,
                text=[f"{'+' if d >= 0 else ''}{d:.3f}" for d in sub.delta],
                textposition="outside", textfont=dict(size=13, color="#374151"),
            ))
        fig2.add_hline(y=0, line_color="#9CA3AF", line_width=1.5)
        fig2.update_layout(
            **_LIGHT, barmode="group", height=440,
            margin=dict(l=60, r=28, t=72, b=60),
            title=dict(text="How Much Density Increase Helps Accuracy", font=_TITLE_FONT, x=0, xanchor="left"),
            xaxis=dict(**_AXIS, title=dict(text="Fusion Model", font=_AXIS_TITLE_FONT)),
            yaxis=dict(**_AXIS, title=dict(text="Δ mAP@0.5", font=_AXIS_TITLE_FONT)),
        )
        st.plotly_chart(fig2, use_container_width=True, config={"modeBarButtons": [["toImage"]], "displaylogo": False, "toImageButtonOptions": {"format": "png", "filename": "lidar_density_gain", "scale": 2}})
        st.session_state["_pdf_fig2"] = fig2
        best_d  = delta_df.loc[delta_df.delta.idxmax()]
        worst_d = delta_df.loc[delta_df.delta.idxmin()]
        st.markdown(
            f"**Biggest gain:** {best_d.group} · {best_d.model} +{best_d.delta:.3f} &nbsp;|&nbsp; "
            f"**Only drop:** {worst_d.group} · {worst_d.model} {worst_d.delta:+.3f}",
            unsafe_allow_html=True,
        )

    # ── Tab 3: Cooperation mode ───────────────────────────────────
    with t3:
        mode_sorted = mode_avg.sort_values("mAP_05")
        fig3 = go.Figure(go.Bar(
            x=mode_sorted.mAP_05,
            y=mode_sorted["mode"].str.upper(),
            orientation="h",
            marker_color=[MODE_COLORS[m] for m in mode_sorted["mode"]],
            marker_line_color="white", marker_line_width=1,
            text=[f"{v:.3f}" for v in mode_sorted.mAP_05],
            textposition="outside", textfont=dict(size=16, color="#374151"),
        ))
        fig3.update_layout(
            **_LIGHT, showlegend=False, height=340,
            margin=dict(l=60, r=60, t=72, b=60),
            title=dict(text="Cooperation Mode vs mAP@0.5", font=_TITLE_FONT, x=0, xanchor="left"),
            xaxis=dict(**_AXIS, range=[0, 0.60], title=dict(text="avg mAP@0.5", font=_AXIS_TITLE_FONT)),
            yaxis=dict(**_AXIS, title=dict(text="", font=_AXIS_TITLE_FONT)),
        )
        st.plotly_chart(fig3, use_container_width=True, config={"modeBarButtons": [["toImage"]], "displaylogo": False, "toImageButtonOptions": {"format": "png", "filename": "cooperation_modes", "scale": 2}})
        st.session_state["_pdf_fig3"] = fig3
        spread = round(float(mode_best["mAP_05"]) - float(mode_worst["mAP_05"]), 3)
        st.markdown(
            f"**{str(mode_best['mode']).upper()}** is the strongest cooperation mode "
            f"({float(mode_best['mAP_05']):.3f}) vs **{str(mode_worst['mode']).upper()}** "
            f"({float(mode_worst['mAP_05']):.3f}). "
            f"Mode spread (~{spread:.3f}) exceeds the spread across fusion models (~0.06) — "
            f"**sensor placement matters more than algorithm choice.**"
        )

    # ── Tab 4: Per-class AP ───────────────────────────────────────
    with t4:
        fig4 = go.Figure()
        for cls, cc in CLASS_COLORS.items():
            sub = per_class[per_class["class"] == cls]
            fig4.add_trace(go.Bar(
                name=cls.capitalize(),
                x=sub.model_label,
                y=sub.AP_05,
                marker_color=cc, marker_line_color="white", marker_line_width=1,
                text=[f"{v:.3f}" for v in sub.AP_05],
                textposition="outside", textfont=dict(size=13, color="#374151"),
            ))
        ped_ceil = float(per_class[per_class["class"] == "pedestrian"]["AP_05"].max())
        fig4.add_hline(
            y=ped_ceil, line_dash="dot", line_color="#9CA3AF", line_width=1.5,
            annotation_text=f"Pedestrian ceiling {ped_ceil:.3f}",
            annotation_font_size=14, annotation_font_color="#6B7280",
        )
        fig4.update_layout(
            **_LIGHT, barmode="group", height=440,
            margin=dict(l=60, r=28, t=72, b=60),
            title=dict(text="Per-class AP@0.5 — Averaged over all groups & modes", font=_TITLE_FONT, x=0, xanchor="left"),
            xaxis=dict(**_AXIS, title=dict(text="Fusion Model", font=_AXIS_TITLE_FONT)),
            yaxis=dict(**_AXIS, range=[0, 0.80], title=dict(text="AP@0.5", font=_AXIS_TITLE_FONT)),
        )
        st.plotly_chart(fig4, use_container_width=True, config={"modeBarButtons": [["toImage"]], "displaylogo": False, "toImageButtonOptions": {"format": "png", "filename": "per_class_ap", "scale": 2}})
        st.session_state["_pdf_fig4"] = fig4
        st.markdown(
            "Pedestrian AP@0.5 peaks at only **{:.3f}** across all models. "
            "Headline mAP is primarily dragged down by the pedestrian class.".format(ped_ceil)
        )



st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# Section: Noise Robustness
# ═══════════════════════════════════════════════════════════════════════════════
with st.container(border=True):
    st.markdown('<span class="noise-card-anchor"></span>', unsafe_allow_html=True)

    _snr_b64 = base64.b64encode(COMBINED_CSV_PATH.read_bytes()).decode("ascii") if COMBINED_CSV_PATH.exists() else ""
    _snr_dl = (f'<a class="card-download" download="noise_snr_results.csv" '
               f'href="data:text/csv;base64,{_snr_b64}" data-tip="Download CSV">⬇</a>'
               if _snr_b64 else "")

    if not snr_data_available:
        st.markdown('<div class="noise-title">Noise Robustness</div>', unsafe_allow_html=True)
        st.info("Data not yet available — pending teammate upload.")
    else:
        st.markdown(
            f"""
            <div class="card-dl-header">
              <div class="noise-title">Noise Robustness</div>
              <p class="noise-caption">
                Average Precision response across SNR levels for the Late
                fusion model under Rayleigh + AWGN channel noise.
              </p>
              {_snr_dl}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="filter-row-spacer"></div>', unsafe_allow_html=True)

        # ── Bar chart: Detection Performance Under Channel Noise ──────────────
        if COMBINED_CSV_PATH.exists():
            _combined = load_combined_snr_data()
            _bar_col  = "mAP_AP@0.5"
            _BAR_W    = 0.35

            # Average each fusion method's AP across all datasets
            _avg = (
                _combined[_combined["snr_label"].isin(["∞ (clean)", "+10.0 dB"])]
                .groupby(["fusion_method", "snr_label"])[_bar_col]
                .mean()
                .reset_index()
            )

            _group_defs = [
                ("Early<br>Fusion",        "early",        "#2563EB", "#93C5FD"),
                ("Intermediate<br>Fusion", "intermediate", "#059669", "#6EE7B7"),
                ("Late<br>Fusion",         "late",         "#F57C00", "#FDBA74"),
            ]

            _labels, _clean_cols, _ret_cols = [], [], []
            _clean_vals, _retained_vals, _lost_vals, _ret_pcts = [], [], [], []
            for lbl, method, cc, rc in _group_defs:
                _cv = float(_avg[(_avg["fusion_method"] == method) & (_avg["snr_label"] == "∞ (clean)")][_bar_col].values[0]) * 100
                _nv = float(_avg[(_avg["fusion_method"] == method) & (_avg["snr_label"] == "+10.0 dB")][_bar_col].values[0]) * 100
                _labels.append(lbl)
                _clean_cols.append(cc)
                _ret_cols.append(rc)
                _clean_vals.append(_cv)
                _retained_vals.append(_nv)
                _lost_vals.append(_cv - _nv)
                _ret_pcts.append(round(_nv / _cv * 100) if _cv > 0 else 0)

            fig_bar = go.Figure()

            fig_bar.add_trace(go.Bar(
                name="Clean (no noise)",
                x=_labels, y=_clean_vals,
                offsetgroup="clean",
                marker_color=_clean_cols,
                text=[f"{v:.1f}%" for v in _clean_vals],
                textposition="outside",
                textfont=dict(size=13, color="#6B7280"),
                width=_BAR_W,
            ))
            fig_bar.add_trace(go.Bar(
                name="At +10 dB SNR (retained)",
                x=_labels, y=_retained_vals,
                offsetgroup="noisy",
                base=[0] * 3,
                marker_color=_ret_cols,
                width=_BAR_W,
            ))
            # Red label on this trace — textposition="outside" places it exactly
            # above the top of the stacked bar (retained + lost = clean height)
            fig_bar.add_trace(go.Bar(
                name="AP lost to noise",
                x=_labels, y=_lost_vals,
                offsetgroup="noisy",
                base=_retained_vals,
                marker=dict(
                    color="rgba(180,40,40,0.65)",
                    pattern=dict(shape="/", fgcolor="white", size=12, solidity=0.3),
                ),
                text=[f"{p}% retained" for p in _ret_pcts],
                textposition="outside",
                textfont=dict(size=13, color="#DC2626"),
                width=_BAR_W,
            ))



            fig_bar.update_layout(
                **_LIGHT,
                barmode="group",
                height=560,
                margin=dict(l=80, r=60, t=100, b=100),
                title=dict(
                    text=(
                        "Detection Performance Under Channel Noise"
                        "<br><sup>Clean vs +10 dB SNR (Rayleigh + AWGN)</sup>"
                    ),
                    font=_TITLE_FONT, x=0.5, xanchor="center",
                ),
                hoverlabel=dict(bgcolor="white", bordercolor="#D1D5DB", font=dict(color="#111827")),
                xaxis=dict(**_AXIS),
                yaxis=dict(
                    **_AXIS,
                    title=dict(text="mAP@0.5 (%)", font=_AXIS_TITLE_FONT),
                    range=[0, max(_clean_vals) * 1.40],
                    tickformat=".0f",
                    ticksuffix="%",
                    dtick=10,
                ),
            )
            fig_bar.update_layout(legend=dict(
                orientation="v",
                yanchor="top", y=0.98,
                xanchor="right", x=0.99,
                font=dict(size=13, color="#374151"),
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#D1D5DB",
                borderwidth=1,
            ))

            st.plotly_chart(fig_bar, use_container_width=True, config={"modeBarButtons": [["toImage"]], "displaylogo": False, "toImageButtonOptions": {"format": "png", "filename": "channel_noise_performance", "scale": 2}})
            st.session_state["_pdf_fig_bar"] = fig_bar

        st.divider()

        # ── Filters ───────────────────────────────────────────────────────────
        fc1, fc2, fc3 = st.columns([3, 4, 4])

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

        with fc3:
            st.markdown('<div class="filter-label">Dataset</div>', unsafe_allow_html=True)
            available_datasets = sorted(df["dataset"].unique()) if "dataset" in df.columns else ["LiDAR-128"]
            dataset_options = available_datasets + ["Average (all datasets)"]
            selected_dataset = st.selectbox(
                "Dataset",
                dataset_options,
                index=0,
                label_visibility="collapsed",
            )

        class_cols = {
            "Vehicle":    f"vehicle_AP@{iou_choice}",
            "Pedestrian": f"pedestrian_AP@{iou_choice}",
            "Truck":      f"truck_AP@{iou_choice}",
            "mAP":        f"mAP_AP@{iou_choice}",
        }

        class_colors = {
            "Vehicle":    "#2563EB",
            "Pedestrian": "#D97706",
            "Truck":      "#059669",
            "mAP":        "#7C3AED",
        }

        col = class_cols[selected_class]

        if selected_dataset == "Average (all datasets)":
            plot_df = df.groupby(["fusion_method", "snr_label"], observed=True)[col].mean().reset_index()
        elif "dataset" in df.columns:
            plot_df = df[df["dataset"] == selected_dataset].copy()
        else:
            plot_df = df.copy()

        fusion_colors = {"early": "#2563EB", "intermediate": "#059669", "late": "#F57C00"}
        _snr_x_cats = ["+0.0 dB", "+10.0 dB", "+20.0 dB", "+30.0 dB", "∞ (clean)"]

        _fusion_labels = {"early": "Early", "intermediate": "Intermediate", "late": "Late"}

        fig = go.Figure()
        for fusion_method, fc in fusion_colors.items():
            sub = plot_df[plot_df["fusion_method"] == fusion_method]
            if sub.empty or col not in sub.columns:
                continue
            fig.add_trace(go.Scatter(
                x=sub["snr_label"].tolist(),
                y=sub[col].tolist(),
                mode="lines+markers",
                name=_fusion_labels[fusion_method],
                legendgroup=fusion_method,
                legendgrouptitle=dict(text=""),
                line=dict(color=fc, width=3),
                marker=dict(size=9, color=fc, line=dict(color="white", width=1.5)),
                hovertemplate=(
                    f"<b>%{{fullData.name}}</b><br>"
                    f"SNR: %{{x}}<br>"
                    f"AP @ IoU {iou_choice}: %{{y:.4f}}<extra></extra>"
                ),
            ))

        # Ego-only dotted threshold lines
        _raw = load_combined_snr_data()
        _ego = _raw[_raw["snr_label"] == "ego only"]
        for fusion_method, fc in fusion_colors.items():
            _ego_sub = _ego[_ego["fusion_method"] == fusion_method]
            if _ego_sub.empty or col not in _ego_sub.columns:
                continue
            if selected_dataset == "Average (all datasets)":
                ego_val = _ego_sub[col].mean()
            elif "dataset" in _ego_sub.columns:
                ego_val = _ego_sub[_ego_sub["dataset"] == selected_dataset][col].mean()
            else:
                ego_val = _ego_sub[col].mean()
            fig.add_trace(go.Scatter(
                x=_snr_x_cats,
                y=[ego_val] * len(_snr_x_cats),
                mode="lines",
                name=f"{_fusion_labels[fusion_method]} (ego only)",
                legendgroup=fusion_method,
                hoverinfo="skip",
                line=dict(color=fc, width=2, dash="dot"),
            ))

        fig.update_layout(
            **_LIGHT,
            height=600,
            margin=dict(l=100, r=28, t=72, b=240),
            title=dict(text=f"Average Precision vs SNR — IoU {iou_choice}", font=_TITLE_FONT, x=0, xanchor="left"),
            xaxis=dict(**_AXIS, title=dict(text="SNR Level", font=_AXIS_TITLE_FONT)),
            yaxis=dict(**_AXIS, title=dict(text=f"AP @ IoU {iou_choice}", font=_AXIS_TITLE_FONT),
                       range=[0, plot_df[col].max() * 1.18], tickformat=".2f"),
            hovermode="x unified",
            hoverlabel=dict(bgcolor="white", bordercolor="#D1D5DB", font=dict(color="#111827")),
        )
        fig.update_layout(legend=dict(
            orientation="h",
            traceorder="grouped",
            yanchor="top", y=-0.32,
            xanchor="center", x=0.5,
            font=dict(size=12, color="#374151"),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            tracegroupgap=40,
            itemsizing="constant",
            itemwidth=35,
        ))

        st.markdown('<div style="height: 2rem;"></div>', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True,
                        config={"modeBarButtons": [["toImage"]], "displaylogo": False, "toImageButtonOptions": {"format": "png", "filename": "average_precision_snr", "scale": 2}})
        st.session_state["_pdf_fig_snr"] = fig


st.divider()

# ── PDF download ──────────────────────────────────────────────────────────────
_has_figs = any(st.session_state.get(k) is not None
                for k in ["_pdf_fig1", "_pdf_fig_bar", "_pdf_fig_snr"])

_dl_col, _cap_col = st.columns([2, 5])
with _dl_col:
    if _has_figs:
        with st.spinner("Building PDF…"):
            _pdf_bytes = _build_pdf()
        st.download_button(
            label="⬇  Download PDF Report",
            data=_pdf_bytes,
            file_name="fusion_analysis_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        st.info("Scroll through the page once to load all charts, then the PDF button will appear.")
with _cap_col:
    st.caption("FYP — Semantic V2V Communication for Autonomous Cooperative Perception")
