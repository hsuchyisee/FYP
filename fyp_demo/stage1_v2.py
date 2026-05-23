import streamlit as st
import time
from utils import render_tunnel
from stage2 import render_stage2, STAGE2_CSS
from stage3 import render_stage3, STAGE3_CSS

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="SemanticV2V — Research Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;600&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #060a14;
    color: #e2e8f0;
  }
  .block-container { padding-top: 32px; max-width: 1100px; }
  #MainMenu, footer, header { visibility: hidden; }

  /* Hero */
  .hero {
    background: linear-gradient(135deg, #0d1424 0%, #111827 60%, #0d1424 100%);
    border: 1px solid #1e3a5f55;
    border-radius: 20px;
    padding: 52px 48px 44px;
    margin-bottom: 40px;
    position: relative;
    overflow: hidden;
  }
  .hero::after {
    content: '';
    position: absolute;
    top: -80px; right: -80px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, #3b82f615 0%, transparent 65%);
    border-radius: 50%;
    pointer-events: none;
  }
  .hero-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #3b82f6;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 14px;
  }
  .hero-title {
    font-size: 38px;
    font-weight: 600;
    color: #f1f5f9;
    line-height: 1.2;
    margin-bottom: 12px;
  }
  .hero-title span { color: #60a5fa; }
  .hero-sub {
    font-size: 14px;
    color: #64748b;
    max-width: 560px;
    line-height: 1.8;
  }

  /* Stage box */
  .stage-box {
    background: #0d1424;
    border: 1px solid #1e293b;
    border-radius: 16px;
    padding: 32px 36px;
    margin-bottom: 0;
  }
  .stage-box.active { border-color: #1e40af66; }
  .stage-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #3b82f6;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 8px;
  }
  .stage-title {
    font-size: 20px;
    font-weight: 600;
    color: #e2e8f0;
    margin-bottom: 6px;
  }
  .stage-sub {
    font-size: 13px;
    color: #475569;
    margin-bottom: 24px;
    line-height: 1.6;
  }

  /* Fake file picker */
  .filepath-bar {
    display: flex;
    align-items: center;
    gap: 0;
    background: #060a14;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 0;
    margin-bottom: 16px;
    overflow: hidden;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
  }
  .filepath-icon {
    background: #0d1f3c;
    border-right: 1px solid #1e3a5f;
    padding: 10px 14px;
    color: #3b82f6;
    font-size: 14px;
  }
  .filepath-text {
    flex: 1;
    padding: 10px 14px;
    color: #334155;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .filepath-text.filled { color: #93c5fd; }

  /* Scenario detected card */
  .scenario-detected {
    background: #061020;
    border: 1px solid #1e40af44;
    border-left: 3px solid #3b82f6;
    border-radius: 10px;
    padding: 16px 20px;
    margin-top: 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
  }
  .scenario-detected .s-label {
    color: #475569;
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 4px;
  }
  .scenario-detected .s-value { color: #93c5fd; font-size: 15px; font-weight: 600; margin-bottom: 8px; }
  .scenario-detected .s-meta  { color: #334155; font-size: 11px; line-height: 2.0; }
  .scenario-detected .s-meta span { color: #475569; }

  /* Tunnel */
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  /* Stage 2 locked */
  .stage2-locked {
    background: #07090f;
    border: 1px dashed #111827;
    border-radius: 16px;
    padding: 52px 36px;
    text-align: center;
    color: #1e293b;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.1em;
  }

  /* Streamlit selectbox override */
  [data-testid="stSelectbox"] > div > div {
    background: #060a14 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
    color: #93c5fd !important;
  }

  /* Button */
  .stButton > button {
    background: #0d1f3c !important;
    border: 1px solid #1e3a5f !important;
    color: #60a5fa !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
    border-radius: 8px !important;
    padding: 8px 20px !important;
    letter-spacing: 0.05em !important;
  }
  .stButton > button:hover {
    background: #1e3a5f !important;
    border-color: #3b82f6 !important;
    color: #93c5fd !important;
  }
            
  {STAGE2_CSS}
  {STAGE3_CSS}    

  /* Pipeline overview */
  .section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 32px 0 16px;
  }
  .section-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #3b82f6;
    background: #1e3a5f;
    padding: 3px 8px;
    border-radius: 4px;
    letter-spacing: 0.05em;
  }
  .section-title {
    font-size: 18px;
    font-weight: 600;
    color: #e2e8f0;
  }
  .pipeline {
    display: flex;
    align-items: center;
    gap: 0;
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 8px;
    overflow-x: auto;
  }
  .pipe-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 110px;
  }
  .pipe-icon {
    width: 44px; height: 44px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
    margin-bottom: 8px;
  }
  .pipe-icon.active   { background: #1e40af; box-shadow: 0 0 16px #3b82f640; }
  .pipe-icon.inactive { background: #1e293b; }
  .pipe-label {
    font-size: 11px;
    color: #64748b;
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
  }
  .pipe-label.active { color: #93c5fd; }
  .pipe-arrow {
    font-size: 18px;
    color: #1e293b;
    margin: 0 6px;
    padding-bottom: 20px;
  }
  .custom-divider {
    border: none;
    border-top: 1px solid #1e293b;
    margin: 24px 0;
  }
                
</style>
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
    "📁  Camera_LiDAR/ 2023-04-03-18-28-32_22_0": {
        "id": "2023-04-03-18-28-32_22_0",
        "label": "Urban Crossroad — Apr 3 (B)",
        "frames": 150, "agents": 4,
        "type": "V2V + Infrastructure",
        "description": "Follow-up capture from the same route. Different traffic conditions."
    },
    "📁  Camera_LiDAR / 2023-04-04-14-27-53_44_0": {
        "id": "2023-04-04-14-27-53_44_0",
        "label": "Intersection — Apr 4 (A)",
        "frames": 127, "agents": 4,
        "type": "V2V + Infrastructure",
        "description": "Afternoon 4-agent intersection. Mixed pedestrian and vehicle traffic."
    },
    "📁  Camera_LiDAR/ 2023-04-05-16-25-26_22_0": {
        "id": "2023-04-05-16-25-26_22_0",
        "label": "Urban Scene — Apr 5 (A)",
        "frames": 106, "agents": 4,
        "type": "V2V + Infrastructure",
        "description": "Late afternoon urban scene. Lower traffic density."
    },
    "📁  Camera_LiDAR / 2023-04-05-16-31-26_28_1": {
        "id": "2023-04-05-16-31-26_28_1",
        "label": "Urban Scene — Apr 5 (B)",
        "frames": 103, "agents": 4,
        "type": "V2V + Infrastructure",
        "description": "Continuation of Apr 5 route. Fewest frames — compact scenario."
    },
}

# ══════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════
if "stage" not in st.session_state:
    st.session_state.stage    = 1   # 1=idle, 2=selected, 3=ready
    st.session_state.scenario = None


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

# ── Fake filepath bar ──────────────────────────────────────────
if st.session_state.scenario:
    sc = st.session_state.scenario
    filepath_content = f"Camera_LiDAR / {sc['id']}"
    bar_class = "filled"
else:
    filepath_content = "No folder selected"
    bar_class = ""

st.markdown(f"""
<div class="filepath-bar">
  <div class="filepath-icon">📁</div>
  <div class="filepath-text {bar_class}">{filepath_content}</div>
</div>
""", unsafe_allow_html=True)

# ── Scenario selectbox ─────────────────────────────────────────
chosen_key = st.selectbox(
    "Browse scenario folder:",
    options=["— Select a scenario folder —"] + list(SCENARIOS.keys()),
    label_visibility="collapsed"
)

# ── Load button ────────────────────────────────────────────────
col_btn, col_gap = st.columns([2, 5])
with col_btn:
    load_clicked = st.button("▶  Load Scenario", use_container_width=True)

# ── On load ────────────────────────────────────────────────────
if load_clicked and chosen_key != "— Select a scenario folder —":
    sc = SCENARIOS[chosen_key]
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

    # ── Neon tunnel animation ──────────────────────────────────
    tunnel_ph = st.empty()
    label_ph  = st.empty()
    steps     = 35

    status_msgs = [
        (0,  "Indexing scenario frames..."),
        (30, "Loading agent sensor streams..."),
        (60, "Parsing YAML metadata..."),
        (85, "Initialising cooperative pipeline..."),
        (99, ""),
    ]

    for i in range(steps + 1):
        pct = int((i / steps) * 100)
        h   = int((pct / 100) * 120)   # fill height out of 120px

        # colour ramp: blue → cyan → green
        if pct < 40:
            c = "#3b82f6"
        elif pct < 80:
            c = "#22d3ee"
        else:
            c = "#34d399"

        # Pick status message
        msg = status_msgs[0][1]
        for threshold, text in status_msgs:
            if pct >= threshold:
                msg = text

        tunnel_ph.markdown(f"""
        <div style="display:flex;flex-direction:column;align-items:center;padding:4px 0;">
          <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
               color:{c};letter-spacing:0.15em;text-transform:uppercase;margin-bottom:12px;">
            {'▶ Processing' if pct < 100 else '✓ Ready'}
          </div>
          <div style="position:relative;width:4px;height:120px;
               background:#0f1929;border-radius:4px;overflow:visible;">
            <div style="width:12px;height:12px;border-radius:50%;
                 background:{c};box-shadow:0 0 12px {c},0 0 24px {c}88;
                 position:absolute;top:-6px;left:50%;transform:translateX(-50%);"></div>
            <div style="position:absolute;left:0;top:0;width:100%;
                 height:{h}px;max-height:120px;overflow:hidden;border-radius:4px;
                 background:linear-gradient(to bottom,#34d399,#22d3ee,{c});
                 box-shadow:0 0 14px {c}bb,0 0 28px {c}44;"></div>
            <div style="width:12px;height:12px;border-radius:50%;
                 background:{c};box-shadow:0 0 12px {c},0 0 24px {c}88;
                 position:absolute;bottom:-6px;left:50%;transform:translateX(-50%);"></div>
          </div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:11px;
          color:{c};margin-top:12px;text-align:center;">
          {pct}%
          {'<br>✓ Pipeline ready' if pct == 100 else ''}
          </div>
        """, unsafe_allow_html=True)

        label_ph.markdown(f"""
        <div style="text-align:center;font-family:'JetBrains Mono',monospace;
             font-size:11px;color:#334155;margin-top:2px;">{msg}</div>
        """, unsafe_allow_html=True)

        time.sleep(0.04)

    st.session_state.stage = 3
    tunnel_ph.empty()
    label_ph.empty()
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

    # Static 100% tunnel
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;padding:16px 0 8px;">
      <div style="position:relative;width:4px;height:120px;
           background:#0f1929;border-radius:4px;overflow:visible;">
        <div style="width:12px;height:12px;border-radius:50%;
             background:#34d399;box-shadow:0 0 12px #34d399,0 0 24px #34d39988;
             position:absolute;top:-6px;left:50%;transform:translateX(-50%);"></div>
        <div style="position:absolute;left:0;top:0;width:100%;height:120px;
             border-radius:4px;
             background:linear-gradient(to bottom,#3b82f6,#22d3ee,#34d399);
             box-shadow:0 0 14px #34d399bb,0 0 28px #34d39944;"></div>
        <div style="width:12px;height:12px;border-radius:50%;
             background:#34d399;box-shadow:0 0 12px #34d399,0 0 24px #34d39988;
             position:absolute;bottom:-6px;left:50%;transform:translateX(-50%);"></div>
      </div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:11px;
           color:#34d399;margin-top:12px;text-align:center;">
        100%<br>✓ Pipeline ready
      </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# STAGE 2 PLACEHOLDER
# ══════════════════════════════════════════════════════════════
st.markdown("<br>", unsafe_allow_html=True)

if st.session_state.stage < 3:
    # Locked state — scenario not yet selected
    st.markdown("""
    <div class="stage2-locked">
      <div style="font-size:32px;margin-bottom:14px;opacity:0.15;">📡</div>
      STAGE 02 · SCENE INTELLIGENCE<br>
      <span style="font-size:10px;opacity:0.4;margin-top:6px;display:block;">
        Awaiting scenario input to unlock
      </span>
    </div>
    """, unsafe_allow_html=True)
 
else:
    # ── Stage 2: Scene Intelligence ───────────────────────────
    render_stage2(
        scenario_id  = st.session_state.scenario["id"],
        dataset_root = "C:/Users/Jess/Downloads/Camera_LiDAR"
        # Lab PC path: "/home/student/Downloads/V2XReal_Data/Camera_LiDAR_test/test"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Stage 3: Model Analysis ───────────────────────────────
    # render_tunnel inside render_stage3 handles the stage 2→3 tunnel.
    # User clicks "Run Inference Analysis" button to trigger it.
    render_stage3(
        project_root = "/home/student/Downloads/V2X-Real",
        scenario_id  = st.session_state.scenario["id"]
        # Local path: "C:/Users/Jess/Downloads/MDS18_GitRepo/FYP/V2X-Real"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("↩  Load a different scenario"):
        # Clear all session state so everything resets cleanly
        for key in ["stage", "scenario",
                    "s3_inference_started", "s3_inference_done",
                    "s3_cards_animated",
                    "s3_video_started", "s3_video_tunnel_done"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()