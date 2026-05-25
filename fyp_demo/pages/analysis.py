from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


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

 /* ── Locally scoped card styling (noise section) ── */
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

 .noise-card-anchor { display: none; }

 /* ── Locally scoped card styling (cross-val section) ── */
 [data-testid="stVerticalBlockBorderWrapper"]:has(.cv-card-anchor):not(:has([data-testid="stVerticalBlockBorderWrapper"] .cv-card-anchor)) {
   background: #FFFFFF !important;
   border: 1px solid rgba(17,24,39,0.13) !important;
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

 /* ── Cross-val KPI boxes ── */
 .cv-kpi {
   background: #F9FAFB;
   border: 1px solid #E5E7EB;
   border-radius: 12px;
   padding: 18px 20px;
   text-align: center;
 }
 .cv-kpi-val {
   font-size: 40px;
   font-weight: 800;
   color: #111827 !important;
   line-height: 1;
   margin-bottom: 6px;
 }
 .cv-kpi-label {
   font-size: 15px;
   color: #6B7280 !important;
   line-height: 1.4;
 }
</style>
""", unsafe_allow_html=True)


# ── Navigation ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="v2v-site-title">Semantic V2V Communication</div>
<nav class="v2v-nav">
  <a href="/" class="v2v-tab" target="_self">Dashboard</a>
  <a href="/analysis" class="v2v-tab active" target="_self">Analysis</a>
  <a href="/tensorboard" class="v2v-tab" target="_self">TensorBoard</a>
</nav>
""", unsafe_allow_html=True)


st.title("Fusion Model Analysis")
st.markdown('<p class="page-subtitle">Quantitative evaluation of fusion strategies and datasets</p>', unsafe_allow_html=True)

st.divider()

# ── Noise data ────────────────────────────────────────────────────────────────
SNR_CSV_PATH = Path(__file__).parent.parent.parent / "noise" / "ap_vs_snr_intermediate_rayleigh_awgn.csv"


@st.cache_data
def load_snr_data():
    df = pd.read_csv(SNR_CSV_PATH)
    order = ["∞ (clean)", "+30.0 dB", "+10.0 dB", "+0.0 dB", "-30.0 dB"]
    df["snr_label"] = pd.Categorical(df["snr_label"], categories=order, ordered=True)
    return df.sort_values("snr_label").reset_index(drop=True)


snr_data_available = SNR_CSV_PATH.exists()
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
MODEL_COLORS = {"Early": "#2563EB", "Intermediate": "#7C3AED", "Late": "#D97706"}
MODE_COLORS  = {"i2i": "#059669", "ic": "#7C3AED", "vc": "#2563EB", "v2v": "#DC2626"}
CLASS_COLORS = {"vehicle": "#2563EB", "pedestrian": "#D97706", "truck": "#059669"}


# ═══════════════════════════════════════════════════════════════════════════════
# Section: Cross-Validation Inference
# ═══════════════════════════════════════════════════════════════════════════════
with st.container(border=True):
    st.markdown('<span class="cv-card-anchor"></span>', unsafe_allow_html=True)

    st.markdown("""
    <h2 class="cv-title">Cross-Validation Inference</h2>
    <p class="cv-caption">
      mAP@0.5 evaluated across 3 Fusion Models, 3 Training Groups,
      2 LiDAR Densities, and 4 cooperation modes on V2X-Real.
    </p>
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
            title=dict(text="mAP@0.5 by Training Group, Model & LiDAR Density", font=_TITLE_FONT, x=0, xanchor="left"),
        )
        fig1.update_layout(legend=dict(font=dict(size=12, color="#374151"), bgcolor="rgba(255,255,255,0)", borderwidth=0))
        fig1.update_yaxes(range=[0, 0.60], **_AXIS, title_text="mAP@0.5", col=1)
        fig1.update_yaxes(range=[0, 0.60], **_AXIS, col=2)
        fig1.update_yaxes(range=[0, 0.60], **_AXIS, col=3)
        fig1.update_xaxes(**_AXIS)
        st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})
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
            colors = [gc if d >= 0 else "#DC2626" for d in sub.delta]
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
            title=dict(text="mAP@0.5 Gain: LiDAR-64 to LiDAR-128", font=_TITLE_FONT, x=0, xanchor="left"),
            xaxis=dict(**_AXIS, title=dict(text="Fusion Model", font=_AXIS_TITLE_FONT)),
            yaxis=dict(**_AXIS, title=dict(text="Δ mAP@0.5", font=_AXIS_TITLE_FONT)),
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
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
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
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
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            "Pedestrian AP@0.5 peaks at only **{:.3f}** across all models. "
            "Headline mAP is primarily dragged down by the pedestrian class.".format(ped_ceil)
        )



st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# Section: Noise Robustness
# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════
# Section: Noise Robustness
# ═══════════════════════════════════════════════════════════════════════════════
if not snr_data_available:
    with st.container(border=True):
        st.markdown('<span class="noise-card-anchor"></span>', unsafe_allow_html=True)
        st.markdown('<h2 class="noise-title">Noise Robustness</h2>', unsafe_allow_html=True)
        st.info("Data not yet available — pending teammate upload.")

if snr_data_available:
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

    x_labels = df["snr_label"].tolist()
    col      = class_cols[selected_class]
    color    = class_colors[selected_class]

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
        x0="+0.0 dB", x1="-30.0 dB",
        fillcolor="rgba(239,68,68,0.07)", layer="below", line_width=0,
        annotation_text="Degraded zone", annotation_position="top left",
        annotation=dict(
            font=dict(color="#B91C1C", size=20),
            bgcolor="rgba(254,226,226,0.92)",
            bordercolor="#FCA5A5", borderwidth=1, borderpad=4,
        ),
    )

    st.divider()

    fig.update_layout(
        **_LIGHT,
        height=520,
        margin=dict(l=100, r=28, t=72, b=110),
        title=dict(text=f"Average Precision vs SNR — IoU {iou_choice}", font=_TITLE_FONT, x=0, xanchor="left"),
        xaxis=dict(**_AXIS, title=dict(text="SNR Level", font=_AXIS_TITLE_FONT)),
        yaxis=dict(**_AXIS, title=dict(text=f"AP @ IoU {iou_choice}", font=_AXIS_TITLE_FONT),
                   range=[0, max(df[col]) * 1.18], tickformat=".2f"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5,
                    font=dict(size=21, color="#374151"), bgcolor="rgba(255,255,255,0)", borderwidth=0),
        hovermode="x unified",
    )

    st.markdown('<div style="height: 2rem;"></div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True,
                    config={"modeBarButtonsToRemove": ["select2d", "lasso2d"], "displaylogo": False})


st.divider()
st.caption("FYP — Semantic V2V Communication for Autonomous Cooperative Perception")
