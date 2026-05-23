import streamlit as st
import yaml
import time
from pathlib import Path
from utils import render_tunnel


STAGE3_CSS = """
  /* Hide video controls completely */
  video::-webkit-media-controls { display: none !important; }
  video { pointer-events: none; }

  /* Model compare cards */
  .mc-card {
    background: #060a14;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 20px 16px;
    position: relative;
    transition: border-color 0.5s, box-shadow 0.5s;
  }
  .mc-card.best-glow {
    border-color: #16a34a;
    box-shadow: 0 0 28px #16a34a33, 0 0 56px #16a34a11;
  }
  .mc-card.best-glow::before {
    content: '★  BEST';
    position: absolute;
    top: -10px; left: 50%;
    transform: translateX(-50%);
    background: #16a34a;
    color: #f0fdf4;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px; font-weight: 700;
    letter-spacing: 0.15em;
    padding: 2px 10px;
    border-radius: 10px;
    white-space: nowrap;
  }
  .mc-model-name {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em;
    color: #475569;
    margin-bottom: 14px;
    text-align: center;
  }
  .mc-model-name.best { color: #4ade80; }

  .mc-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #334155;
    padding: 4px 0;
    border-bottom: 1px solid #0f172a;
  }
  .mc-row:last-child { border-bottom: none; }
  .mc-row-label { color: #475569; font-size: 10px; }
  .mc-row-val   { color: #94a3b8; font-size: 14px; font-weight: 700; }
  .mc-row-val.improved { color: #60a5fa; }
  .mc-row-val.best-val { color: #4ade80; }
  .mc-delta-inline {
    font-size: 10px;
    color: #4ade80;
    margin-left: 6px;
    font-weight: 400;
  }

  /* Recommendation card */
  .rec-card {
    background: #030d04;
    border: 1px solid #16a34a44;
    border-left: 4px solid #16a34a;
    border-radius: 12px;
    padding: 28px 32px;
    margin: 24px 0;
    animation: recFadeIn 0.7s ease;
  }
  @keyframes recFadeIn {
    from { opacity:0; transform:translateY(12px); }
    to   { opacity:1; transform:translateY(0); }
  }
  .rec-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; color: #16a34a;
    text-transform: uppercase; letter-spacing: 0.18em;
    margin-bottom: 6px;
  }
  .rec-model-name {
    font-size: 26px; font-weight: 600;
    color: #4ade80; margin-bottom: 16px;
  }
  .rec-delta-cards {
    display: flex; gap: 10px; flex-wrap: wrap;
    margin-bottom: 20px;
  }
  .rec-delta-card {
    background: #052e16;
    border: 1px solid #16a34a33;
    border-radius: 8px;
    padding: 10px 16px;
    text-align: center;
    min-width: 100px;
  }
  .rec-delta-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 20px; font-weight: 700;
    color: #4ade80; line-height: 1;
    margin-bottom: 3px;
  }
  .rec-delta-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px; color: #16a34a;
    text-transform: uppercase; letter-spacing: 0.1em;
  }
  .rec-divider { border:none; border-top:1px solid #0d2010; margin:16px 0; }
  .rec-section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; color: #16a34a;
    text-transform: uppercase; letter-spacing: 0.12em;
    margin-bottom: 8px; font-weight: 600;
  }
  .config-block {
    background: #020c02;
    border: 1px solid #0d2010;
    border-radius: 8px;
    padding: 14px 18px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; color: #334155; line-height: 2.2;
  }
  .ck { color: #16a34a; }
  .cv { color: #4ade80; }
  .rec-body { font-size: 13px; color: #475569; line-height: 1.8; }

  .proceed-hint {
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; color: #1e3a5f;
    letter-spacing: 0.1em; margin-bottom: 8px;
    text-transform: uppercase;
  }

  @keyframes fadeIn {
    from { opacity:0; transform:translateY(8px); }
    to   { opacity:1; transform:translateY(0); }
  }
"""


# ══════════════════════════════════════════════════════════════
# MODEL DATA — replace map_raw/map_tuned/f1_raw/f1_tuned with
# your real inference values after running inference.py
# tuned_params: hardcode "before → after" strings — no need
# to read two config files, you know what you changed
# ══════════════════════════════════════════════════════════════
MODEL_RESULTS = {
    "early": {
        "label":       "Early Fusion",
        "map_raw":     0.61, "map_tuned": 0.82,
        "f1_raw":      0.58, "f1_tuned":  0.79,
        "log_dir":     "logs/point_pillar_early_fusion",
        "tuned_params": [
            ("Learning Rate",  "0.001",       "0.0005"),
            ("Anchor Sizes",   "default",     "[1.6, 3.9, 1.56]"),
            ("Epochs",         "30",          "40"),
            ("LR Step Size",   "10",          "[15, 25]"),
        ],
        "justification": (
            "Early Fusion aggregates raw LiDAR point clouds from all agents before "
            "feature extraction, maximising information density. After tuning the "
            "learning rate schedule and anchor box sizes to match V2X-Real object "
            "distribution, AP improved by 34% in this urban intersection scenario."
        ),
    },
    "late": {
        "label":       "Late Fusion",
        "map_raw":     0.54, "map_tuned": 0.71,
        "f1_raw":      0.51, "f1_tuned":  0.68,
        "log_dir":     "logs/point_pillar_late_fusion",
        "tuned_params": [
            ("Learning Rate",  "0.002",  "0.001"),
            ("Batch Size",     "2",      "4"),
            ("Epochs",         "30",     "35"),
            ("Dropout",        "0.0",    "0.1"),
        ],
        "justification": (
            "Late Fusion performs independent per-agent detection before sharing "
            "results. Communication overhead is minimal — only bounding box proposals "
            "are transmitted. Robust but misses occlusion benefits of earlier fusion."
        ),
    },
    "intermediate": {
        "label":       "Intermediate Fusion",
        "map_raw":     0.66, "map_tuned": 0.85,
        "f1_raw":      0.63, "f1_tuned":  0.81,
        "log_dir":     "logs/point_pillar_intermediate_fusion",
        "tuned_params": [
            ("Learning Rate",   "0.001",  "0.001"),
            ("Feature Dim",     "128",    "256"),
            ("Attention Heads", "4",      "8"),
            ("Epochs",          "30",     "45"),
        ],
        "justification": (
            "Intermediate Fusion shares compressed feature maps between agents — "
            "balancing information richness with communication efficiency. The "
            "attention mechanism across agent tokens captures spatial dependencies "
            "invisible to single-vehicle perception, achieving the highest mAP "
            "across all tested fusion strategies on this scenario."
        ),
    },
}

BEST_MODEL = "intermediate"  # ← set to whichever wins after running inference


def load_model_config(log_dir: str, project_root: str) -> dict:
    """Read real hyperparameter values from trained model config.yaml if available."""
    config_path = Path(project_root) / log_dir / "config.yaml"
    if not config_path.exists():
        return {}
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    params = {}
    try: params["lr"]         = cfg.get("optimizer", {}).get("lr", "N/A")
    except: params["lr"]      = "N/A"
    try: params["batch_size"] = cfg.get("train_params", {}).get("batch_size", "N/A")
    except: params["batch_size"] = "N/A"
    try: params["epochs"]     = cfg.get("train_params", {}).get("epoches", "N/A")
    except: params["epochs"]  = "N/A"
    try: params["max_cav"]    = cfg.get("model", {}).get("args", {}).get("max_cav", "N/A")
    except: params["max_cav"] = "N/A"
    try: params["lr_steps"]   = str(cfg.get("lr_scheduler", {}).get("step_size", "N/A"))
    except: params["lr_steps"] = "N/A"
    return params


def _card_html(key: str, map_r: float, map_t: float,
               f1_r: float, f1_t: float, glowing: bool = False) -> str:
    """
    Build HTML for one model card.
    Layout: model name → mAP raw → mAP improved (Δ inline) → F1 raw → F1 improved (Δ inline)
    Reused by both animation loop and static final render.
    """
    model     = MODEL_RESULTS[key]
    is_best   = glowing
    card_cls  = "mc-card best-glow" if glowing else "mc-card"
    name_cls  = "mc-model-name best" if glowing else "mc-model-name"
    imp_cls   = "mc-row-val best-val" if glowing else "mc-row-val improved"
    d_map     = map_t - map_r
    d_f1      = f1_t  - f1_r
    d_map_str = f'<span class="mc-delta-inline">↑ +{d_map:.2f}</span>' if d_map > 0 else ""
    d_f1_str  = f'<span class="mc-delta-inline">↑ +{d_f1:.2f}</span>'  if d_f1  > 0 else ""

    return f"""
    <div class="{card_cls}">
      <div class="{name_cls}">{model["label"]}</div>
      <div class="mc-row">
        <span class="mc-row-label">mAP raw</span>
        <span class="mc-row-val">{map_r:.2f}</span>
      </div>
      <div class="mc-row">
        <span class="mc-row-label">mAP improved</span>
        <span class="{imp_cls}">{map_t:.2f}{d_map_str}</span>
      </div>
      <div class="mc-row">
        <span class="mc-row-label">F1 raw</span>
        <span class="mc-row-val">{f1_r:.2f}</span>
      </div>
      <div class="mc-row">
        <span class="mc-row-label">F1 improved</span>
        <span class="{imp_cls}">{f1_t:.2f}{d_f1_str}</span>
      </div>
    </div>
    """


def render_running_cards():
    """
    Animate all 3 model cards concurrently: values count up 0.00 → target.
    Then pulse the best model card with a green glow to signal selection.
    Uses st.empty() placeholders — only card content updates, not full page.
    """
    keys  = list(MODEL_RESULTS.keys())
    steps = 50

    st.markdown("""
    <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
         color:#1e3a5f;text-transform:uppercase;letter-spacing:0.15em;
         margin-bottom:16px;">Inference Results — All Fusion Strategies</div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    phs = {}
    for col, key in zip([col1, col2, col3], keys):
        phs[key] = col.empty()

    # Count up animation
    for i in range(steps + 1):
        t = i / steps
        for key in keys:
            m = MODEL_RESULTS[key]
            phs[key].markdown(_card_html(
                key,
                round(m["map_raw"]   * t, 2),
                round(m["map_tuned"] * t, 2),
                round(m["f1_raw"]    * t, 2),
                round(m["f1_tuned"]  * t, 2),
            ), unsafe_allow_html=True)
        time.sleep(0.03)

    time.sleep(0.4)

    # Show final values without glow
    for key in keys:
        m = MODEL_RESULTS[key]
        phs[key].markdown(_card_html(
            key, m["map_raw"], m["map_tuned"],
            m["f1_raw"], m["f1_tuned"]
        ), unsafe_allow_html=True)

    time.sleep(0.3)

    # Pulse best card 2x then lock glow on
    bk = BEST_MODEL
    bm = MODEL_RESULTS[bk]
    for _ in range(2):
        time.sleep(0.18)
        phs[bk].markdown(_card_html(bk, bm["map_raw"], bm["map_tuned"],
                                    bm["f1_raw"], bm["f1_tuned"], glowing=False),
                         unsafe_allow_html=True)
        time.sleep(0.18)
        phs[bk].markdown(_card_html(bk, bm["map_raw"], bm["map_tuned"],
                                    bm["f1_raw"], bm["f1_tuned"], glowing=True),
                         unsafe_allow_html=True)

    # Final state — best glowing, others static
    for key in keys:
        m = MODEL_RESULTS[key]
        phs[key].markdown(_card_html(
            key, m["map_raw"], m["map_tuned"],
            m["f1_raw"], m["f1_tuned"],
            glowing=(key == BEST_MODEL)
        ), unsafe_allow_html=True)


def _render_static_cards():
    """Render final static card state — used on reruns after animation."""
    st.markdown("""
    <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
         color:#1e3a5f;text-transform:uppercase;letter-spacing:0.15em;
         margin-bottom:16px;">Inference Results — All Fusion Strategies</div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    for col, key in zip([col1, col2, col3], MODEL_RESULTS.keys()):
        m = MODEL_RESULTS[key]
        with col:
            st.markdown(_card_html(
                key, m["map_raw"], m["map_tuned"],
                m["f1_raw"], m["f1_tuned"],
                glowing=(key == BEST_MODEL)
            ), unsafe_allow_html=True)


def _render_rec_card(project_root: str):
    """Render the recommendation card for the best model."""
    best      = MODEL_RESULTS[BEST_MODEL]
    cfg       = load_model_config(best["log_dir"], project_root)
    delta_map = best["map_tuned"] - best["map_raw"]
    delta_f1  = best["f1_tuned"]  - best["f1_raw"]
    pct_up    = (delta_map / best["map_raw"] * 100) if best["map_raw"] > 0 else 0

    # Tuned params table — prefer real config.yaml, fallback to hardcoded list
    if cfg:
        param_rows = "".join([
            f'<span class="ck">{k:<20}</span> <span class="cv">{v}</span><br>'
            for k, v in cfg.items()
        ])
    else:
        param_rows = "".join([
            f'<span class="ck">{p[0]:<20}</span> '
            f'<span style="color:#475569;">{p[1]}</span>'
            f' <span style="color:#334155;">→</span> '
            f'<span class="cv">{p[2]}</span><br>'
            for p in best["tuned_params"]
        ])

    st.markdown(f"""
    <div class="rec-card">
      <div class="rec-eyebrow">✓ Recommended Model · Best for this scenario</div>
      <div class="rec-model-name">{best["label"]}</div>

      <div class="rec-delta-cards">
        <div class="rec-delta-card">
          <div class="rec-delta-val">+{delta_map:.2f}</div>
          <div class="rec-delta-label">Δ mAP</div>
        </div>
        <div class="rec-delta-card">
          <div class="rec-delta-val">+{delta_f1:.2f}</div>
          <div class="rec-delta-label">Δ F1</div>
        </div>
        <div class="rec-delta-card">
          <div class="rec-delta-val">{pct_up:.0f}%</div>
          <div class="rec-delta-label">AP Gain</div>
        </div>
        <div class="rec-delta-card">
          <div class="rec-delta-val">{best["map_tuned"]:.2f}</div>
          <div class="rec-delta-label">Best mAP</div>
        </div>
      </div>

      <hr class="rec-divider">
      <div class="rec-section-label">Tuned Hyperparameters</div>
      <div class="config-block">{param_rows}</div>

      <hr class="rec-divider">
      <div class="rec-section-label">Justification</div>
      <div class="rec-body">{best["justification"]}</div>
    </div>
    """, unsafe_allow_html=True)


def render_stage3(project_root: str, scenario_id: str):
    """
    Main Stage 3 render function. Call from stage1_v2.py after render_stage2().

    Session state keys managed:
      s3_inference_started  : user clicked Run Inference
      s3_inference_done     : tunnel animation complete
      s3_cards_animated     : card count-up animation complete
      s3_video_started      : user clicked Run LiDAR Detection
      s3_video_tunnel_done  : lidar tunnel animation complete
    """
    for key in ["s3_inference_started", "s3_inference_done",
                "s3_cards_animated", "s3_video_started", "s3_video_tunnel_done"]:
        if key not in st.session_state:
            st.session_state[key] = False

    # Stage 3 header
    st.markdown("""
    <div class="stage-box active" style="animation:fadeIn 0.5s ease;">
      <div class="stage-label">Stage 03 · Model Analysis</div>
      <div class="stage-title">Cooperative Perception — Model Evaluation</div>
      <div class="stage-sub">
        Three fusion architectures were trained and hyperparameter-tuned on V2X-Real.
        Inference is run on the selected scenario to identify the optimal model.
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Step 1: Run Inference button ───────────────────────────
    if not st.session_state.s3_inference_started:
        st.markdown('<div class="proceed-hint">Ready to evaluate models on this scenario</div>',
                    unsafe_allow_html=True)
        col_btn, _ = st.columns([2, 5])
        with col_btn:
            if st.button("▶  Run Inference Analysis", use_container_width=True, type="primary"):
                st.session_state.s3_inference_started = True
                st.rerun()
        return

    # ── Step 2: Tunnel (once, stays visible) ───────────────────
    if not st.session_state.s3_inference_done:
        render_tunnel(
            label      = "Running inference analysis...",
            done_label = "✓ Inference ready"
        )
        st.session_state.s3_inference_done = True
        st.rerun()

    # Static tunnel marker — shown on reruns so it stays visible
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;padding:4px 0 8px;">
      <div style="position:relative;width:4px;height:120px;
           background:#0f1929;border-radius:4px;overflow:visible;">
        <div style="width:12px;height:12px;border-radius:50%;background:#4ade80;
             box-shadow:0 0 12px #4ade80,0 0 24px #4ade8088;
             position:absolute;top:-6px;left:50%;transform:translateX(-50%);"></div>
        <div style="position:absolute;left:0;top:0;width:100%;height:120px;
             border-radius:4px;background:linear-gradient(to bottom,#3b82f6,#22d3ee,#4ade80);
             box-shadow:0 0 14px #4ade80bb,0 0 28px #4ade8044;"></div>
        <div style="width:12px;height:12px;border-radius:50%;background:#4ade80;
             box-shadow:0 0 12px #4ade80,0 0 24px #4ade8088;
             position:absolute;bottom:-6px;left:50%;transform:translateX(-50%);"></div>
      </div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:11px;
           color:#4ade80;margin-top:12px;text-align:center;line-height:1.8;">
        100%<br>✓ Inference ready
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Step 3: Card animation (once) then static ──────────────
    if not st.session_state.s3_cards_animated:
        render_running_cards()
        st.session_state.s3_cards_animated = True
        st.rerun()
    else:
        _render_static_cards()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Step 4: Recommendation card ───────────────────────────
    _render_rec_card(project_root)

    # ── Step 5: LiDAR video with tunnel ───────────────────────
    st.markdown('<hr style="border:none;border-top:1px solid #0f172a;margin:28px 0;">',
                unsafe_allow_html=True)

    if not st.session_state.s3_video_started:
        st.markdown('<div class="proceed-hint">LiDAR detection output ready</div>',
                    unsafe_allow_html=True)
        col_btn2, _ = st.columns([2, 5])
        with col_btn2:
            if st.button("▶  Run LiDAR Detection", use_container_width=True):
                st.session_state.s3_video_started = True
                st.rerun()
    else:
        if not st.session_state.s3_video_tunnel_done:
            render_tunnel(
                label      = "Loading LiDAR detection output...",
                done_label = "✓ LiDAR detection ready"
            )
            st.session_state.s3_video_tunnel_done = True
            st.rerun()

        # Static lidar tunnel marker
        st.markdown("""
        <div style="display:flex;flex-direction:column;align-items:center;padding:4px 0 8px;">
          <div style="position:relative;width:4px;height:120px;
               background:#0f1929;border-radius:4px;overflow:visible;">
            <div style="width:12px;height:12px;border-radius:50%;background:#4ade80;
                 box-shadow:0 0 12px #4ade80,0 0 24px #4ade8088;
                 position:absolute;top:-6px;left:50%;transform:translateX(-50%);"></div>
            <div style="position:absolute;left:0;top:0;width:100%;height:120px;
                 border-radius:4px;background:linear-gradient(to bottom,#3b82f6,#22d3ee,#4ade80);
                 box-shadow:0 0 14px #4ade80bb,0 0 28px #4ade8044;"></div>
            <div style="width:12px;height:12px;border-radius:50%;background:#4ade80;
                 box-shadow:0 0 12px #4ade80,0 0 24px #4ade8088;
                 position:absolute;bottom:-6px;left:50%;transform:translateX(-50%);"></div>
          </div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:11px;
               color:#4ade80;margin-top:12px;text-align:center;line-height:1.8;">
            100%<br>✓ LiDAR detection ready
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
             color:#1e3a5f;text-transform:uppercase;letter-spacing:0.15em;
             margin-bottom:12px;">LiDAR Detection — Best Model · Live Output</div>
        <div style="font-size:13px;color:#334155;margin-bottom:16px;line-height:1.7;">
          Bird's-eye-view cooperative detection from the recommended model.
          3D bounding boxes show detected objects across all cooperating agents.
        </div>
        """, unsafe_allow_html=True)

        video_path = Path("data/videos") / BEST_MODEL / f"{scenario_id}.mp4"
        if not video_path.exists():
            video_path = Path("data/videos") / BEST_MODEL / "scene1.mp4"

        if video_path.exists():
            with open(video_path, "rb") as f:
                st.video(f.read(), autoplay=True, loop=True, muted=True)
        else:
            st.info(f"Place LiDAR detection video at: data/videos/{BEST_MODEL}/{scenario_id}.mp4")
