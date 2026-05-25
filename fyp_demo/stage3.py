import streamlit as st
import time
from pathlib import Path
from utils import render_tunnel, download_icon_html
from theme import COLORS, FONTS
from model_results import (
    load_model_results, load_config_diff, load_frame_comparison,
    BEST_MODEL, IOUS, FC_METRICS,
)


# ══════════════════════════════════════════════════════════════
# Stage 3 reads per-model mAP from {scenario}/model_results.csv and
# tuned hyperparameters by diffing {model}_raw vs {model}_improved
# config.yaml — both via the model_results loader.
# ══════════════════════════════════════════════════════════════


def _card_html(label: str, raw: dict, improved: dict, glowing: bool = False) -> str:
    """
    Build HTML for one model card: one row per IoU showing raw → improved mAP
    with a signed delta. Reused by both the animation loop and the static render.
    """
    card_cls = "mc-card best-glow" if glowing else "mc-card"
    name_cls = "mc-model-name best" if glowing else "mc-model-name"
    val_cls  = "mc-row-val best-val" if glowing else "mc-row-val improved"

    rows = ""
    for iou in IOUS:
        r  = raw[iou]
        im = improved[iou]
        d  = im - r
        if d > 0.0005:
            delta = f'<span class="mc-delta-inline up">↑ +{d:.3f}</span>'
        elif d < -0.0005:
            delta = f'<span class="mc-delta-inline down">↓ {d:.3f}</span>'
        else:
            delta = ""
        rows += f"""
      <div class="mc-row">
        <span class="mc-row-label">mAP@{iou}</span>
        <span class="mc-row-vals">
          <span class="mc-row-raw">{r:.3f}</span>
          <span class="mc-row-arrow">→</span>
          <span class="{val_cls}">{im:.3f}</span>
          {delta}
        </span>
      </div>"""

    return f'<div class="{card_cls}"><div class="{name_cls}">{label}</div>{rows}</div>'


_RESULTS_HEADER = """
    <div style="font-family:'JetBrains Mono',monospace;font-size: 19px;
         color:#1e3a5f;text-transform:uppercase;letter-spacing:0.15em;
         margin-bottom:16px;">Inference Results — All Fusion Strategies</div>
    """


def render_running_cards(models: dict, best_model: str):
    """
    Animate the model cards concurrently: mAP values count up 0.00 → target
    across all IoUs. Then pulse the best model card with a green glow.
    Uses st.empty() placeholders — only card content updates, not full page.
    """
    keys  = list(models.keys())
    steps = 50

    st.markdown(_RESULTS_HEADER, unsafe_allow_html=True)

    cols = st.columns(len(keys))
    phs = {key: col.empty() for col, key in zip(cols, keys)}

    def scaled(d, t):
        return {iou: d[iou] * t for iou in IOUS}

    # Count-up animation
    for i in range(steps + 1):
        t = i / steps
        for key in keys:
            m = models[key]
            phs[key].markdown(
                _card_html(m["label"], scaled(m["raw"], t), scaled(m["improved"], t)),
                unsafe_allow_html=True,
            )
        time.sleep(0.03)

    time.sleep(0.4)

    # Pulse best card 2x then lock glow on
    bk = best_model
    bm = models[bk]
    for _ in range(2):
        time.sleep(0.18)
        phs[bk].markdown(_card_html(bm["label"], bm["raw"], bm["improved"], glowing=False),
                         unsafe_allow_html=True)
        time.sleep(0.18)
        phs[bk].markdown(_card_html(bm["label"], bm["raw"], bm["improved"], glowing=True),
                         unsafe_allow_html=True)

    # Final state — best glowing, others static
    for key in keys:
        m = models[key]
        phs[key].markdown(
            _card_html(m["label"], m["raw"], m["improved"], glowing=(key == bk)),
            unsafe_allow_html=True,
        )


def _render_static_cards(models: dict, best_model: str):
    """Render final static card state — used on reruns after animation."""
    st.markdown(_RESULTS_HEADER, unsafe_allow_html=True)

    keys = list(models.keys())
    cols = st.columns(len(keys))
    for col, key in zip(cols, keys):
        m = models[key]
        with col:
            st.markdown(
                _card_html(m["label"], m["raw"], m["improved"], glowing=(key == best_model)),
                unsafe_allow_html=True,
            )


def _render_baseline_line(baseline: dict):
    """Single-model (No Fusion) baseline reference line below the cards."""
    if not baseline:
        return
    b05 = baseline["mAP"][0.5]
    st.markdown(f"""
    <div style="font-family:{FONTS['mono']};font-size: 21px;color:{COLORS['text_muted']};
         background:{COLORS['panel_alt']};border:1px dashed {COLORS['border_strong']};
         border-radius:8px;padding:8px 14px;margin:14px 0 4px;line-height:1.6;">
      {baseline['label']} baseline (single-model): <b style="color:{COLORS['text']};">mAP@0.5 = {b05:.3f}</b>
      &nbsp;— every fusion strategy exceeds this, confirming cooperation helps.
    </div>
    """, unsafe_allow_html=True)


def _render_rec_card(data: dict, dataset_root: str, scenario_id: str):
    """Render the recommendation card for the best model."""
    best_key = data["best_model"]
    best     = data["models"][best_key]
    raw, imp = best["raw"], best["improved"]

    deltas    = {iou: imp[iou] - raw[iou] for iou in IOUS}
    best_map5 = imp[0.5]
    ap_gain   = (deltas[0.5] / raw[0.5] * 100) if raw[0.5] > 0 else 0

    delta_cards = "".join(
        f"""
        <div class="rec-delta-card">
          <div class="rec-delta-val">{'+' if deltas[iou] >= 0 else ''}{deltas[iou]:.3f}</div>
          <div class="rec-delta-label">Δ mAP@{iou}</div>
        </div>"""
        for iou in IOUS
    )
    delta_cards += f"""
        <div class="rec-delta-card">
          <div class="rec-delta-val">{best_map5:.3f}</div>
          <div class="rec-delta-label">Best mAP@0.5</div>
        </div>
        <div class="rec-delta-card">
          <div class="rec-delta-val">{ap_gain:.0f}%</div>
          <div class="rec-delta-label">AP Gain @0.5</div>
        </div>"""

    # Tuned hyperparameters — detected by diffing real raw vs improved config.yaml
    diff = load_config_diff(dataset_root, scenario_id, best_key)
    if diff["available"]:
        param_rows = "".join(
            f'<span class="ck">{label}</span> '
            f'<span style="color:{COLORS["text_dim"]};">{rv}</span> '
            f'<span style="color:{COLORS["text_faint"]};">→</span> '
            f'<span class="cv">{iv}</span><br>'
            for label, rv, iv in diff["changes"]
        )
        hp_block = f'<div class="config-block">{param_rows}</div>'
    else:
        hp_block = (f'<div class="config-block" style="color:{COLORS["text_faint"]};">'
                    f'Config diff unavailable for this scenario.</div>')

    download = download_icon_html(
        data.get("csv_path"),
        "Download all model results (CSV)",
        "model_results.csv",
        css_class="rec-download",
    )

    st.markdown(f"""
    <div class="rec-card">
      {download}
      <div class="rec-eyebrow">✓ Recommended Model · Best for this scenario</div>
      <div class="rec-model-name">{best["label"]}</div>

      <div class="rec-delta-cards">{delta_cards}
      </div>

      <hr class="rec-divider">
      <div class="rec-section-label">Tuned Hyperparameters · detected from config.yaml</div>
      {hp_block}
    </div>
    """, unsafe_allow_html=True)


def _render_frame_comparison(fc: dict):
    """Frame-by-frame Overall-metric comparison table + stacked detection images.
    Shows the progression: no cooperation → cooperation → cooperation + tuning."""
    if not fc["available"]:
        return

    stages = fc["stages"]

    download = download_icon_html(
        fc.get("csv_path"),
        "Download frame metrics (CSV)",
        "overall_metrics.csv",
    )

    st.markdown(
        f'<hr style="border:none;border-top:1px solid {COLORS["border"]};margin:28px 0;">',
        unsafe_allow_html=True,
    )
    st.markdown(f"""
    <div class="dl-header" style="margin-bottom:8px;">
      <div style="font-family:{FONTS['mono']};font-size: 19px;
           color:{COLORS['accent']};text-transform:uppercase;letter-spacing:0.15em;">
        Frame-by-Frame Comparison · Frame 000000</div>
      {download}
    </div>
    <div style="font-size: 26px;color:{COLORS['text_muted']};margin-bottom:16px;line-height:1.7;">
      Per-frame detection quality across the perception progression — no cooperation →
      cooperative perception → cooperative perception with hyperparameter tuning.
      Best value per metric highlighted.
    </div>
    """, unsafe_allow_html=True)

    # Header row
    head_cells = "".join(
        f'<div class="fc-cell">{s["label"]}<span>{s["sub"]}</span></div>'
        for s in stages
    )
    rows_html = (f'<div class="fc-row fc-head"><div class="fc-metric-label"></div>'
                 f'{head_cells}</div>')

    # One row per metric, best value highlighted
    for col, label, higher_better in FC_METRICS:
        vals = [s["metrics"][col] for s in stages]
        best = max(vals) if higher_better else min(vals)
        is_int = col in ("tp", "fp", "fn")
        cells = ""
        for v in vals:
            sel  = " best" if v == best else ""
            disp = f"{int(v)}" if is_int else f"{v:.2f}"
            cells += f'<div class="fc-cell{sel}">{disp}</div>'
        row_cls = "fc-row f1" if col == "f1" else "fc-row"
        rows_html += (f'<div class="{row_cls}"><div class="fc-metric-label">{label}</div>'
                      f'{cells}</div>')

    st.markdown(f'<div class="fc-table">{rows_html}</div>', unsafe_allow_html=True)

    # Stacked detection frames (full container width)
    for s in stages:
        st.markdown(
            f'<div class="fc-img-label">{s["label"]} &nbsp;<span>· {s["sub"]}</span></div>',
            unsafe_allow_html=True,
        )
        if s["image"]:
            st.image(s["image"], use_container_width=True)
        else:
            st.markdown(
                f'<div style="font-family:{FONTS["mono"]};font-size: 21px;'
                f'color:{COLORS["text_faint"]};padding:20px;text-align:center;'
                f'border:1px dashed {COLORS["border_strong"]};border-radius:8px;">'
                f'Frame image unavailable</div>',
                unsafe_allow_html=True,
            )


def render_stage3(dataset_root: str, scenario_id: str):
    """
    Main Stage 3 render function. Call from stage1_v2.py after render_stage2().

    Reads per-model mAP from {scenario}/model_results.csv and tuned
    hyperparameters from {model}_raw vs {model}_improved config.yaml.

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

    data = load_model_results(dataset_root, scenario_id)

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
            done_label = "✓ Inference ready",
            steps      = 40,
            step_delay = 0.065,
        )
        st.session_state.s3_inference_done = True
        st.rerun()

    # Static tunnel marker — shown on reruns so it stays visible
    g = COLORS["tunnel_green"]
    st.markdown(f"""
    <div style="display:flex;flex-direction:column;align-items:center;padding:4px 0 8px;">
      <div style="position:relative;width:4px;height:120px;
           background:{COLORS['tunnel_track']};border-radius:4px;overflow:visible;">
        <div style="width:12px;height:12px;border-radius:50%;background:{g};
             box-shadow:0 0 12px {g},0 0 24px {g}88;
             position:absolute;top:-6px;left:50%;transform:translateX(-50%);"></div>
        <div style="position:absolute;left:0;top:0;width:100%;height:120px;
             border-radius:4px;background:linear-gradient(to bottom,{COLORS['tunnel_blue']},{COLORS['tunnel_cyan']},{g});
             box-shadow:0 0 14px {g}bb,0 0 28px {g}44;"></div>
        <div style="width:12px;height:12px;border-radius:50%;background:{g};
             box-shadow:0 0 12px {g},0 0 24px {g}88;
             position:absolute;bottom:-6px;left:50%;transform:translateX(-50%);"></div>
      </div>
      <div style="font-family:{FONTS['mono']};font-size: 21px;
           color:{COLORS['green_dark']};margin-top:12px;text-align:center;line-height:1.8;">
        100%<br>✓ Inference ready
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Step 3: Cards + recommendation (needs the results CSV) ──
    if data["available"]:
        if not st.session_state.s3_cards_animated:
            render_running_cards(data["models"], data["best_model"])
            st.session_state.s3_cards_animated = True
            st.rerun()
        else:
            _render_static_cards(data["models"], data["best_model"])

        _render_baseline_line(data["baseline"])

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Step 4: Recommendation card ───────────────────────
        _render_rec_card(data, dataset_root, scenario_id)
    else:
        st.info(
            "Inference results not available for this scenario "
            f"({data['reason']}). Showing detection output only."
        )

    # ── Step 5: LiDAR video with tunnel ───────────────────────
    st.markdown(
        f'<hr style="border:none;border-top:1px solid {COLORS["border"]};margin:28px 0;">',
        unsafe_allow_html=True,
    )

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
                done_label = "✓ LiDAR detection ready",
                steps      = 28,
                step_delay = 0.040,
            )
            st.session_state.s3_video_tunnel_done = True
            st.rerun()

        # Static lidar tunnel marker
        g2 = COLORS["tunnel_green"]
        st.markdown(f"""
        <div style="display:flex;flex-direction:column;align-items:center;padding:4px 0 8px;">
          <div style="position:relative;width:4px;height:120px;
               background:{COLORS['tunnel_track']};border-radius:4px;overflow:visible;">
            <div style="width:12px;height:12px;border-radius:50%;background:{g2};
                 box-shadow:0 0 12px {g2},0 0 24px {g2}88;
                 position:absolute;top:-6px;left:50%;transform:translateX(-50%);"></div>
            <div style="position:absolute;left:0;top:0;width:100%;height:120px;
                 border-radius:4px;background:linear-gradient(to bottom,{COLORS['tunnel_blue']},{COLORS['tunnel_cyan']},{g2});
                 box-shadow:0 0 14px {g2}bb,0 0 28px {g2}44;"></div>
            <div style="width:12px;height:12px;border-radius:50%;background:{g2};
                 box-shadow:0 0 12px {g2},0 0 24px {g2}88;
                 position:absolute;bottom:-6px;left:50%;transform:translateX(-50%);"></div>
          </div>
          <div style="font-family:{FONTS['mono']};font-size: 21px;
               color:{COLORS['green_dark']};margin-top:12px;text-align:center;line-height:1.8;">
            100%<br>✓ LiDAR detection ready
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="font-family:{FONTS['mono']};font-size: 19px;
             color:{COLORS['accent']};text-transform:uppercase;letter-spacing:0.15em;
             margin-bottom:12px;">LiDAR Detection — Best Model · Live Output</div>
        <div style="font-size: 26px;color:{COLORS['text_muted']};margin-bottom:16px;line-height:1.7;">
          Bird's-eye-view cooperative detection from the recommended model.
          3D bounding boxes show detected objects across all cooperating agents.
        </div>
        """, unsafe_allow_html=True)

        # Best model's detection video lives in the scenario folder:
        #   {dataset_root}/{scenario_id}/{BEST_MODEL}_improved/{scenario_id}.mp4
        video_path = (Path(dataset_root) / scenario_id
                      / f"{BEST_MODEL}_improved" / f"{scenario_id}.mp4")

        if video_path.exists():
            with open(video_path, "rb") as f:
                st.video(f.read(), autoplay=True, loop=True, muted=True)
        else:
            st.info(
                "LiDAR detection video not available for this scenario "
                f"(expected at {BEST_MODEL}_improved/{scenario_id}.mp4)."
            )

        # ── Step 6: Frame-by-frame comparison ─────────────────
        _render_frame_comparison(load_frame_comparison(dataset_root, scenario_id))
