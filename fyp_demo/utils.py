import streamlit as st
import time
from theme import COLORS, FONTS


DEFAULT_STATUS_MSGS = [
    (0,  "Processing..."),
    (35, "Loading pipeline..."),
    (65, "Processing data..."),
    (88, "Finalising..."),
]


def _tunnel_color(pct: int) -> str:
    """Progress color ramp: blue → cyan → green."""
    if pct < 40:
        return COLORS["tunnel_blue"]
    elif pct < 80:
        return COLORS["tunnel_cyan"]
    else:
        return COLORS["tunnel_green"]


def _tunnel_html(
    pct: int,
    c: str,
    gradient_start: str,
    header_text: str | None,
    show_done_inline: bool,
    done_label: str,
) -> str:
    """Render a single tunnel frame's HTML — shared by animated + static states.

    Returned as a flush-left single-line string so Streamlit's markdown parser
    treats it as one HTML block (any leading whitespace / blank lines would
    cause indented chunks to render as literal code blocks).
    """
    h = min(int((pct / 100) * 120), 120)
    track = COLORS["tunnel_track"]
    cyan = COLORS["tunnel_cyan"]
    mono = FONTS["mono"]

    header_html = ""
    if header_text:
        header_html = (
            f'<div style="font-family:{mono};font-size:10px;color:{c};'
            f'letter-spacing:0.15em;text-transform:uppercase;margin-bottom:12px;">'
            f'{header_text}</div>'
        )

    footer_extra = f"<br>{done_label}" if show_done_inline else ""
    footer_color = COLORS["green_dark"] if show_done_inline else c

    return (
        f'<div style="display:flex;flex-direction:column;align-items:center;padding:4px 0;">'
        f'{header_html}'
        f'<div style="position:relative;width:4px;height:120px;'
        f'background:{track};border-radius:4px;overflow:visible;">'
        f'<div style="width:12px;height:12px;border-radius:50%;background:{c};'
        f'box-shadow:0 0 12px {c},0 0 24px {c}88;'
        f'position:absolute;top:-6px;left:50%;transform:translateX(-50%);"></div>'
        f'<div style="position:absolute;left:0;top:0;width:100%;height:{h}px;'
        f'border-radius:4px;'
        f'background:linear-gradient(to bottom,{gradient_start},{cyan},{c});'
        f'box-shadow:0 0 14px {c}bb,0 0 28px {c}44;"></div>'
        f'<div style="width:12px;height:12px;border-radius:50%;background:{c};'
        f'box-shadow:0 0 12px {c},0 0 24px {c}88;'
        f'position:absolute;bottom:-6px;left:50%;transform:translateX(-50%);"></div>'
        f'</div>'
        f'<div style="font-family:{mono};font-size:11px;color:{footer_color};'
        f'margin-top:12px;text-align:center;line-height:1.8;">'
        f'{pct}%{footer_extra}'
        f'</div>'
        f'</div>'
    )


def render_tunnel(
    label: str = "Processing...",
    done_label: str = "✓ Done",
    *,
    steps: int = 30,
    step_delay: float = 0.04,
    header_label: str | None = None,
    header_done_label: str | None = None,
    status_msgs: list | None = None,
    gradient_start: str | None = None,
    animate: bool = True,
    persist: bool = True,
):
    """
    Reusable neon tunnel — single source of truth for every stage-transition tunnel.

    Args:
        label             : default rotating status text shown beneath the tunnel
                            (only used if status_msgs is None)
        done_label        : text inlined below '100%' once finished
        steps             : number of animation frames (higher = smoother / longer)
        step_delay        : seconds between frames (higher = slower)
        header_label      : optional small caption shown ABOVE the tunnel during loading
        header_done_label : optional caption above the tunnel when complete
                            (falls back to header_label if not given)
        status_msgs       : optional [(threshold_pct, text), ...] list overriding defaults
        gradient_start    : top color of progress gradient (defaults to tunnel_blue)
        animate           : if False, skip animation and render only the static 100% state
        persist           : if False, clear the tunnel after animation finishes
                            (ignored when animate=False — static state always persists)
    """
    if status_msgs is None:
        status_msgs = [(0, label)] + DEFAULT_STATUS_MSGS[1:]
    if gradient_start is None:
        gradient_start = COLORS["tunnel_blue"]

    tunnel_ph = st.empty()
    status_ph = st.empty()

    if animate:
        for i in range(steps + 1):
            pct = int((i / steps) * 100)
            c   = _tunnel_color(pct)

            msg = status_msgs[0][1]
            for threshold, text in status_msgs:
                if pct >= threshold:
                    msg = text

            header = header_label if pct < 100 else (header_done_label or header_label)
            tunnel_ph.markdown(
                _tunnel_html(pct, c, gradient_start, header,
                             show_done_inline=False, done_label=done_label),
                unsafe_allow_html=True,
            )
            status_ph.markdown(f"""
            <div style="text-align:center;font-family:{FONTS['mono']};
                 font-size:11px;color:{COLORS['text_dim']};margin-top:2px;">
              {msg if pct < 100 else ''}
            </div>
            """, unsafe_allow_html=True)
            time.sleep(step_delay)

    if persist or not animate:
        # Final 100% state with done_label inlined — used for both
        # the animate=True persisted end and the animate=False static render.
        g = COLORS["tunnel_green"]
        tunnel_ph.markdown(
            _tunnel_html(100, g, gradient_start,
                         header_done_label or header_label,
                         show_done_inline=True, done_label=done_label),
            unsafe_allow_html=True,
        )
        status_ph.empty()
    else:
        tunnel_ph.empty()
        status_ph.empty()
