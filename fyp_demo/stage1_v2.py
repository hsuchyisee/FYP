import streamlit as st
from utils import render_tunnel
from theme import make_global_css, make_stage2_css, make_stage3_css, make_stage4_css
from stage2 import render_stage2
from stage3 import render_stage3
from stage4 import render_stage4
from scenario_loader import (
    validate_and_extract_zip,
    cleanup_extracted,
    ScenarioValidationError,
)

# Default dataset root for the dropdown SCENARIOS (uploaded scenarios override this).
DEFAULT_DATASET_ROOT  = "/Users/hsuchyi/Downloads/Camera_LiDAR"
DEFAULT_SCENARIO_KEY  = "📁  Camera_LiDAR / 2023-03-17-16-12-12_3_0"
# DEFAULT_DATASET_ROOT = "C:/Users/Jess/Downloads/Camera_LiDAR"
# Lab PC: "/home/student/Downloads/V2XReal_Data/Camera_LiDAR_test/test"

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="SemanticV2V — Research Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CSS (all design tokens live in theme.py) ───────────────────
st.markdown(
    make_global_css() + make_stage2_css() + make_stage3_css() + make_stage4_css(),
    unsafe_allow_html=True,
)
1
# ── Top navigation ─────────────────────────────────────────────
# This file is the multipage entrypoint, so it is served at "/".
# pages/analysis.py -> /analysis, pages/tensorboard.py -> /tensorboard.
st.markdown("""
<style>
  /* hide Streamlit's auto page-list; we navigate via the custom tabs */
  [data-testid="stSidebarNav"] { display: none; }
  .v2v-nav { display:flex; border-bottom:1.5px solid #E5E7EB;
             margin:0 0 24px; padding:0; }
  .v2v-tab { display:inline-block; padding:10px 20px 10px 0;
             font-family:'Inter',sans-serif; font-size:0.95rem; font-weight:500;
             color:#6B7280 !important; text-decoration:none !important;
             border-bottom:2px solid transparent; margin-bottom:-1.5px;
             margin-right:8px; transition:color .18s, border-color .18s; }
  .v2v-tab:hover { color:#111827 !important; }
  .v2v-tab.active { color:#10B981 !important; border-bottom-color:#10B981;
                    font-weight:600; }
</style>
<nav class="v2v-nav">
  <a href="/" class="v2v-tab active" target="_self">Dashboard</a>
  <a href="/analysis" class="v2v-tab" target="_self">Analysis</a>
  <a href="/tensorboard" class="v2v-tab" target="_self">Summary</a>
</nav>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# SCENARIO DATA — all 9 mixed V2V+Infra scenarios
# ══════════════════════════════════════════════════════════════
SCENARIOS = {
    "📁  Camera_LiDAR / 2023-03-17-16-12-12_3_0":  {
        "id": "2023-03-17-16-12-12_3_0",
        "label": "Urban Intersection — Mar 17",
        "frames": 119, "agents": 4,
        "type": "V2V + Infrastructure",
        "description": "4-agent urban intersection scene. 2 connected vehicles (CAV-1, CAV-2) and 2 roadside infrastructure units (RSU-1, RSU-2)."
    },
    "📁  Camera_LiDAR / 2023-04-03-18-19-32_13_0": {
        "id": "2023-04-03-18-19-32_13_0", 
        "label": "Urban Crossroad — Apr 3 (A)",
        "frames": 240, "agents": 4,
        "type": "V2V + Infrastructure",
        "description": "Longest 4-agent scenario. High-density urban crossroad with diverse object types."
    },

}

# ══════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════
if "stage" not in st.session_state:
    st.session_state.stage    = 3
    st.session_state.scenario = SCENARIOS[DEFAULT_SCENARIO_KEY]

# Counter used to force-reset the selectbox + file_uploader widgets by
# rotating their keys. Streamlit doesn't reliably clear widget state via
# session_state deletion alone — changing the widget's key is the canonical fix.
if "widget_reset_counter" not in st.session_state:
    st.session_state.widget_reset_counter = 0


# ══════════════════════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
  <div class="hero-eyebrow">FYP · Semantic V2V Communication for Autonomous Cooperative Perception</div>
  <div class="hero-title">System-Level Design &amp; Evaluation of<br><span>Semantic V2V Communication</span></div>
  <div class="hero-sub">
    Select a real-world V2X-Real scenario to begin the cooperative perception pipeline.
    Each scenario contains synchronised multi-agent LiDAR and camera sensor data from
    connected autonomous vehicles and roadside infrastructure units.
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# ACT 1 — PIPELINE OVERVIEW
# ══════════════════════════════════════════════════════════════

st.markdown("""
<div class="section-header">
  <span class="section-num">00</span>
  <span class="section-title">Research Pipeline</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="pipeline">
  <div class="pipe-step">
    <div class="pipe-icon active">📡</div>
    <div class="pipe-label active">V2X-Real<br>Dataset</div>
  </div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step">
    <div class="pipe-icon active">⚙️</div>
    <div class="pipe-label active">Preprocessing<br>& Encoding</div>
  </div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step">
    <div class="pipe-icon active">🧠</div>
    <div class="pipe-label active">Model<br>Training</div>
  </div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step">
    <div class="pipe-icon active">🔧</div>
    <div class="pipe-label active">Hyperparameter<br>Tuning</div>
  </div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step">
    <div class="pipe-icon active">📊</div>
    <div class="pipe-label active">Inference<br>& Evaluation</div>
  </div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step">
    <div class="pipe-icon active">📶</div>
    <div class="pipe-label active">Channel<br>Noise Test</div>
  </div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step">
    <div class="pipe-icon active">✅</div>
    <div class="pipe-label active">Result<br>Analysis</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.caption("All stages have been completed. This dashboard presents the outputs of each phase interactively.")

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# STAGE 1 — SCENARIO INPUT
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="stage-box active">
  <div class="stage-label">Stage 01 · Scenario Input</div>
  <div class="stage-title">Select V2X-Real Scenario</div>
  <div class="stage-sub">
    Choose a scenario folder from the Camera–LiDAR test dataset.
    The pipeline will load synchronised sensor streams from all cooperating agents.
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Scenario selectbox ─────────────────────────────────────────
_rc = st.session_state.widget_reset_counter
chosen_key = st.selectbox(
    "Browse scenario folder:",
    options=["— Select a scenario folder —"] + list(SCENARIOS.keys()),
    label_visibility="collapsed",
    key=f"scenario_dropdown_{_rc}",
)

# ── Custom scenario upload ─────────────────────────────────────
st.markdown(
    '<div style="margin:18px 0 8px;font-family:JetBrains Mono,monospace;'
    'font-size: 19px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.15em;">'
    '— or upload your own scenario —</div>',
    unsafe_allow_html=True,
)

uploaded_zip = st.file_uploader(
    "Upload a scenario .zip — layout: scenario_id/<agent>/  with "
    "000000.yaml (required, one per agent) and 000000_camN.jpeg (optional). "
    "LiDAR .bin files are not needed.",
    accept_multiple_files=False,
    key=f"scenario_zip_upload_{_rc}",
)

# ── Single Load button ─────────────────────────────────────────
col_btn, _ = st.columns([2, 5])
with col_btn:
    load_clicked = st.button("▶  Load Scenario", use_container_width=True)

# ── Resolve input — exactly one source allowed (dropdown XOR upload) ──
sc_to_load = None
if load_clicked:
    has_dropdown = chosen_key != "— Select a scenario folder —"
    has_upload   = uploaded_zip is not None

    if has_dropdown and has_upload:
        st.error("Use either the dropdown selection OR an uploaded zip — not both. "
                 "Clear one and try again.")
    elif has_dropdown:
        sc_to_load = SCENARIOS[chosen_key]
    elif has_upload:
        try:
            sc_to_load = validate_and_extract_zip(uploaded_zip)
        except ScenarioValidationError as e:
            st.error(f"❌ Invalid scenario zip: {e}")
    else:
        st.warning("Select a scenario from the dropdown or upload a .zip first.")

# ── On load (shared by both inputs) ────────────────────────────
if sc_to_load is not None:
    # Clean up any previous uploaded-scenario temp dir
    prev = st.session_state.get("scenario")
    if prev and prev.get("_uploaded") and prev is not sc_to_load:
        cleanup_extracted(prev)

    # Reset all downstream stage-3/4 progress so re-loading any scenario
    # (same or different) starts fresh — no carried-over inference/lidar/noise results.
    for key in ["s3_inference_started", "s3_inference_done",
                "s3_cards_animated",
                "s3_video_started", "s3_video_tunnel_done",
                "s4_started", "s4_tunnel_done", "s4_snr_slider"]:
        if key in st.session_state:
            del st.session_state[key]

    sc = sc_to_load
    st.session_state.scenario = sc
    st.session_state.stage    = 2

    # Show detected card immediately
    st.markdown(f"""
    <div class="scenario-detected">
      <div class="s-label">Scenario identified</div>
      <div class="s-value">{sc["label"]}</div>
      <div class="s-meta">
        <span>Path ·</span> Camera_LiDAR/{sc["id"]}<br>
        <span>Frames ·</span> {sc["frames"]} timesteps &nbsp;·&nbsp;
        <span>Agents ·</span> {sc["agents"]} &nbsp;·&nbsp;
        <span>Type ·</span> {sc["type"]}<br>
        <span>Description ·</span> {sc["description"]}
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Neon tunnel animation (shared helper) ──────────────────
    render_tunnel(
        label             = "Indexing scenario frames...",
        done_label        = "✓ Pipeline ready",
        steps             = 25,
        step_delay        = 0.030,
        header_label      = "▶ Processing",
        status_msgs       = [
            (0,  "Indexing scenario frames..."),
            (30, "Loading agent sensor streams..."),
            (60, "Parsing YAML metadata..."),
            (85, "Initialising cooperative pipeline..."),
        ],
    )

    st.session_state.stage = 3
    st.rerun()

# ── Already loaded — show static completed state ───────────────
elif st.session_state.stage == 3 and st.session_state.scenario:
    sc = st.session_state.scenario

    st.markdown(f"""
    <div class="scenario-detected">
      <div class="s-label">✓ Scenario loaded</div>
      <div class="s-value">{sc["label"]}</div>
      <div class="s-meta">
        <span>Path ·</span> Camera_LiDAR/{sc["id"]}<br>
        <span>Frames ·</span> {sc["frames"]} timesteps &nbsp;·&nbsp;
        <span>Agents ·</span> {sc["agents"]} &nbsp;·&nbsp;
        <span>Type ·</span> {sc["type"]}
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Static 100% tunnel — same helper, no animation
    render_tunnel(
        done_label        = "✓ Pipeline ready",
        animate           = False,
    )


# ══════════════════════════════════════════════════════════════
# STAGE 2 PLACEHOLDER
# ══════════════════════════════════════════════════════════════
st.markdown("<br>", unsafe_allow_html=True)

if st.session_state.stage < 3:
    # Locked state — scenario not yet selected
    st.markdown("""
    <div class="stage2-locked">
      <div style="font-size: 61px;margin-bottom:14px;opacity:0.15;">📡</div>
      STAGE 02 · SCENE INTELLIGENCE<br>
      <span style="font-size: 19px;opacity:0.4;margin-top:6px;display:block;">
        Awaiting scenario input to unlock
      </span>
    </div>
    """, unsafe_allow_html=True)
 
else:
    # ── Stage 2: Scene Intelligence ───────────────────────────
    # Uploaded scenarios carry their own extracted dataset_root;
    # dropdown scenarios fall back to the project-wide default.
    active_dataset_root = (
        st.session_state.scenario.get("dataset_root") or DEFAULT_DATASET_ROOT
    )
    render_stage2(
        scenario_id  = st.session_state.scenario["id"],
        dataset_root = active_dataset_root,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Stage 3: Model Analysis ───────────────────────────────
    # render_tunnel inside render_stage3 handles the stage 2→3 tunnel.
    # Reads model_results.csv + config diffs from the scenario folder.
    render_stage3(
        dataset_root = active_dataset_root,
        scenario_id  = st.session_state.scenario["id"],
    )

    # ── Stage 4: Channel Noise Robustness ─────────────────────
    # Unlocks only after Stage 3's LiDAR detection has run, so the
    # stage 3→4 tunnel reads as a continuation of the pipeline.
    if st.session_state.get("s3_video_tunnel_done"):
        st.markdown("<br>", unsafe_allow_html=True)
        render_stage4(
            dataset_root = active_dataset_root,
            scenario_id  = st.session_state.scenario["id"],
        )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("↩  Load a different scenario"):
        # Clean up any temp dir from a previously uploaded scenario
        cleanup_extracted(st.session_state.get("scenario"))

        # Clear all non-widget session state.
        for key in ["stage", "scenario",
                    "s3_inference_started", "s3_inference_done",
                    "s3_cards_animated",
                    "s3_video_started", "s3_video_tunnel_done",
                    "s4_started", "s4_tunnel_done", "s4_snr_slider"]:
            if key in st.session_state:
                del st.session_state[key]

        # Rotate widget keys so the selectbox + file_uploader are
        # re-instantiated on the next rerun (returns them to initial state).
        st.session_state.widget_reset_counter += 1
        st.rerun()