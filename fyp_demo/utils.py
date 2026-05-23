import streamlit as st
import time


def render_tunnel(label: str = "Processing...", done_label: str = "✓ Done"):
    """
    Reusable neon tunnel animation flowing top → bottom.
    Stays visible after completion showing done_label.
    Used between every stage — pass different labels each time.

    Args:
        label      : status text shown during loading
        done_label : text shown at bottom when 100% reached — stays visible
    """
    tunnel_ph  = st.empty()
    status_ph  = st.empty()
    steps = 30

    status_msgs = [
        (0,  label),
        (35, "Loading pipeline..."),
        (65, "Processing data..."),
        (88, "Finalising..."),
    ]

    for i in range(steps + 1):
        pct = int((i / steps) * 100)
        h   = int((pct / 100) * 120)
        c   = "#3b82f6" if pct < 40 else "#22d3ee" if pct < 80 else "#4ade80"

        msg = status_msgs[0][1]
        for threshold, text in status_msgs:
            if pct >= threshold:
                msg = text

        tunnel_ph.markdown(f"""
        <div style="display:flex;flex-direction:column;align-items:center;padding:4px 0;">
          <div style="position:relative;width:4px;height:120px;
               background:#0f1929;border-radius:4px;overflow:visible;">
            <div style="width:12px;height:12px;border-radius:50%;background:{c};
                 box-shadow:0 0 12px {c},0 0 24px {c}88;
                 position:absolute;top:-6px;left:50%;transform:translateX(-50%);"></div>
            <div style="position:absolute;left:0;top:0;width:100%;
                 height:{min(h,120)}px;border-radius:4px;
                 background:linear-gradient(to bottom,#3b82f6,#22d3ee,{c});
                 box-shadow:0 0 14px {c}bb,0 0 28px {c}44;"></div>
            <div style="width:12px;height:12px;border-radius:50%;background:{c};
                 box-shadow:0 0 12px {c},0 0 24px {c}88;
                 position:absolute;bottom:-6px;left:50%;transform:translateX(-50%);"></div>
          </div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:11px;
               color:{c};margin-top:12px;text-align:center;line-height:1.8;">
            {pct}%
          </div>
        </div>
        """, unsafe_allow_html=True)

        status_ph.markdown(f"""
        <div style="text-align:center;font-family:'JetBrains Mono',monospace;
             font-size:11px;color:#334155;margin-top:2px;">
          {msg if pct < 100 else ''}
        </div>
        """, unsafe_allow_html=True)

        time.sleep(0.04)

    # ── Stay visible at 100% with done_label ───────────────────
    # Do NOT call .empty() — let it persist on screen
    tunnel_ph.markdown(f"""
    <div style="display:flex;flex-direction:column;align-items:center;padding:4px 0;">
      <div style="position:relative;width:4px;height:120px;
           background:#0f1929;border-radius:4px;overflow:visible;">
        <div style="width:12px;height:12px;border-radius:50%;background:#4ade80;
             box-shadow:0 0 12px #4ade80,0 0 24px #4ade8088;
             position:absolute;top:-6px;left:50%;transform:translateX(-50%);"></div>
        <div style="position:absolute;left:0;top:0;width:100%;height:120px;
             border-radius:4px;
             background:linear-gradient(to bottom,#3b82f6,#22d3ee,#4ade80);
             box-shadow:0 0 14px #4ade80bb,0 0 28px #4ade8044;"></div>
        <div style="width:12px;height:12px;border-radius:50%;background:#4ade80;
             box-shadow:0 0 12px #4ade80,0 0 24px #4ade8088;
             position:absolute;bottom:-6px;left:50%;transform:translateX(-50%);"></div>
      </div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:11px;
           color:#4ade80;margin-top:12px;text-align:center;line-height:1.8;">
        100%<br>{done_label}
      </div>
    </div>
    """, unsafe_allow_html=True)

    status_ph.empty()  # clear the rotating status text only
