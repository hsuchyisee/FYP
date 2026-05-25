"""
Stage 4 — Channel Noise Robustness.

Simulates Rayleigh + AWGN channel noise on the best model (intermediate fusion,
NOT trained with noise) and shows how cooperative detection degrades as SNR
drops from clean → 0 dB. Motivates the noise-aware training shown in Stage 5.

Flow:
  Run Channel Noise Test button → stage 3→4 tunnel → SNR slider →
  metric strip (mAP@0.5 + 3-state status + ego-only baseline) →
  Feature Map row (what the model receives) →
  BEV Detection row (what the model outputs) + legend + note.

Uploaded scenarios without a noise/ folder show a graceful fallback.
"""

import base64
from pathlib import Path

import streamlit as st

from theme import COLORS, FONTS
from utils import render_tunnel, download_icon_html
from stage4_data import (
    load_noise_data,
    STATUS_BENEFICIAL,
    STATUS_BELOW_BASELINE,
    STATUS_COLLAPSE,
)


# Display metadata for the 3-state status label (logic lives in stage4_data).
STATUS_DISPLAY = {
    STATUS_BENEFICIAL: {
        "label": "Cooperation beneficial",
        "desc":  "Fused detection exceeds the single-agent baseline.",
    },
    STATUS_BELOW_BASELINE: {
        "label": "Below single-agent baseline",
        "desc":  "Channel noise has dragged fusion below ego-only performance.",
    },
    STATUS_COLLAPSE: {
        "label": "Detection collapse",
        "desc":  "Near-zero detection — the model is effectively blind.",
    },
}


def _img_data_uri(path: str) -> str:
    """Base64 data URI so the image can be embedded in custom HTML (for the
    selected-column glow) and opened full-size via a click-through link."""
    data = Path(path).read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _render_image_row(levels: list, selected_idx: int, img_key: str,
                      thumb: bool = False):
    """Render one row of per-SNR images with the selected column glowing.
    img_key is 'feat_img' or 'bev_img'. thumb=True renders a compact strip."""
    cells = []
    for i, lvl in enumerate(levels):
        sel = " sel" if i == selected_idx else ""
        path = lvl.get(img_key)
        if path:
            uri = _img_data_uri(path)
            img_html = (
                f'<a href="{uri}" target="_blank" title="Open full size">'
                f'<img src="{uri}" alt="{lvl["slider_label"]}"></a>'
            )
        else:
            img_html = '<div class="s4-cell-missing">image unavailable</div>'
        cells.append(
            f'<div class="s4-cell{sel}">{img_html}'
            f'<div class="s4-cap">{lvl["slider_label"]}</div></div>'
        )
    row_class = "s4-row thumbs" if thumb else "s4-row"
    st.markdown(f'<div class="{row_class}">{"".join(cells)}</div>',
                unsafe_allow_html=True)


def _render_bev_section(levels: list, selected_idx: int):
    """BEV: one large view of the selected SNR + a thumbnail strip of all 5."""
    current = levels[selected_idx]
    path = current.get("bev_img")
    if path:
        uri = _img_data_uri(path)
        st.markdown(f"""
        <div class="s4-bev-large">
          <a href="{uri}" target="_blank" title="Open full size">
            <img src="{uri}" alt="{current['slider_label']}">
          </a>
          <div class="s4-cap sel">{current['slider_label']} — selected</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="s4-cell-missing">BEV image unavailable</div>',
                    unsafe_allow_html=True)

    _render_image_row(levels, selected_idx, "bev_img", thumb=True)


def _render_metric_strip(current: dict, ego_only_map05):
    """Headline mAP@0.5 + 3-state status badge for the selected SNR."""
    map05 = current["mAP"][0.5]
    status = current["status"]
    disp = STATUS_DISPLAY[status]

    st.markdown(f"""
    <div class="s4-metric-wrap">
      <div class="s4-metric-card">
        <div class="s4-metric-label">mAP @ 0.5 · {current['slider_label']}</div>
        <div class="s4-metric-val">{map05:.3f}</div>
        <div class="s4-metric-sub">cooperative detection</div>
      </div>
      <div class="s4-status {status}">
        <div class="s4-status-label">{disp['label']}</div>
        <div class="s4-status-desc">{disp['desc']}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if ego_only_map05 is not None:
        st.markdown(f"""
        <div class="s4-baseline">
          Single-agent baseline (no fusion): <b>mAP@0.5 = {ego_only_map05:.3f}</b>
          &nbsp;— below this line, channel noise makes cooperative fusion worse
          than not cooperating at all.
        </div>
        """, unsafe_allow_html=True)


def _render_metric_expander(current: dict):
    m = current["mAP"]
    with st.expander("All IoU thresholds (mAP@0.3 / 0.5 / 0.7)"):
        c1, c2, c3 = st.columns(3)
        for col, iou in zip((c1, c2, c3), (0.3, 0.5, 0.7)):
            with col:
                st.markdown(f"""
                <div class="s4-metric-card" style="min-width:0;">
                  <div class="s4-metric-label">mAP @ {iou}</div>
                  <div class="s4-metric-val" style="font-size: 42px;">{m[iou]:.3f}</div>
                </div>
                """, unsafe_allow_html=True)


def render_stage4(dataset_root: str, scenario_id: str):
    """
    Main Stage 4 render. Call from stage1_v2.py after render_stage3().

    Session state keys:
      s4_started      : user clicked Run Channel Noise Test
      s4_tunnel_done  : stage 3→4 tunnel animation complete
    """
    for key in ["s4_started", "s4_tunnel_done"]:
        if key not in st.session_state:
            st.session_state[key] = False

    # ── Header ─────────────────────────────────────────────────
    st.markdown("""
    <div class="stage-box active" style="animation:fadeIn 0.5s ease;">
      <div class="stage-label">Stage 04 · Channel Noise Robustness</div>
      <div class="stage-title">Semantic Communication — Noise Robustness Test</div>
      <div class="stage-sub">
        The best model (Intermediate fusion) is evaluated under simulated
        Rayleigh + AWGN channel noise. As SNR drops, the shared features corrupt
        and cooperative detection degrades — motivating the noise-aware training
        in Stage 5.
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Availability check (uploaded scenarios have no noise/ folder) ──
    data = load_noise_data(dataset_root, scenario_id)
    if not data["available"]:
        st.info(
            "Channel-noise robustness data is available for the bundled "
            f"scenarios only. ({data['reason']})"
        )
        return

    # ── Step 1: Run button ─────────────────────────────────────
    if not st.session_state.s4_started:
        st.markdown('<div class="proceed-hint">Ready to simulate channel noise on the best model</div>',
                    unsafe_allow_html=True)
        col_btn, _ = st.columns([2, 5])
        with col_btn:
            if st.button("▶  Run Channel Noise Test", use_container_width=True):
                st.session_state.s4_started = True
                st.rerun()
        return

    # ── Step 2: Tunnel (once, then static marker) ──────────────
    if not st.session_state.s4_tunnel_done:
        render_tunnel(
            label      = "Simulating channel noise...",
            done_label = "✓ Noise sweep ready",
            steps      = 34,
            step_delay = 0.05,
        )
        st.session_state.s4_tunnel_done = True
        st.rerun()

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
        100%<br>✓ Noise sweep ready
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Step 3: SNR slider ─────────────────────────────────────
    levels = data["levels"]
    slider_labels = [lvl["slider_label"] for lvl in levels]

    snr_download = download_icon_html(
        data.get("csv_path"),
        "Download noise-sweep metrics (CSV)",
        "ap_vs_snr_intermediate_rayleigh_awgn.csv",
    )
    st.markdown(f"""
    <div class="dl-header" style="margin:8px 0 4px;">
      <div style="font-family:{FONTS['mono']};font-size: 19px;
           color:{COLORS['accent']};text-transform:uppercase;letter-spacing:0.15em;">
        Channel SNR Level</div>
      {snr_download}
    </div>
    """, unsafe_allow_html=True)

    selected_label = st.select_slider(
        "Channel SNR level",
        options=slider_labels,
        value=slider_labels[0],
        label_visibility="collapsed",
        key="s4_snr_slider",
    )
    selected_idx = slider_labels.index(selected_label)
    current = levels[selected_idx]

    # ── Metric strip + expander ────────────────────────────────
    _render_metric_strip(current, data["ego_only_map05"])
    _render_metric_expander(current)

    # ── Feature Map row ────────────────────────────────────────
    st.markdown(
        '<div class="s4-row-label">Feature Map &nbsp;<span>(what the model receives)</span></div>',
        unsafe_allow_html=True,
    )
    _render_image_row(levels, selected_idx, "feat_img")

    # ── BEV Detection row ──────────────────────────────────────
    st.markdown(
        '<div class="s4-row-label">BEV Detection &nbsp;<span>(what the model outputs)</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("""
    <div class="s4-legend">
      <span class="s4-legend-item"><span class="s4-swatch tp"></span> TP — matched detection</span>
      <span class="s4-legend-item"><span class="s4-swatch fp"></span> FP — false alarm</span>
      <span class="s4-legend-item"><span class="s4-swatch fn"></span> FN — missed ground truth</span>
    </div>
    """, unsafe_allow_html=True)
    _render_bev_section(levels, selected_idx)

    st.markdown("""
    <div class="s4-note">
      <b>%</b> above a box = the model's confidence that the detection is a true positive.
      A box at the <b>same position across columns</b> is the <b>same tracked vehicle</b>,
      so you can watch its confidence fall as SNR drops from Clean → 0 dB.
      <b>“--”</b> = that vehicle was missed (FN) at this noise level.
    </div>
    """, unsafe_allow_html=True)
