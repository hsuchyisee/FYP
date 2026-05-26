"""Design tokens and CSS generators for the SemanticV2V dashboard.

Edit COLORS / FONTS here once and the change propagates across
stage1_v2.py, stage2.py, stage3.py, and utils.py.
"""

# ── Design tokens ──────────────────────────────────────────────
COLORS = {
    # Backgrounds
    "bg":            "#f8fafc",  # page
    "panel":         "#ffffff",  # card / panel
    "panel_alt":     "#f1f5f9",  # subtle alt panel

    # Borders
    "border":        "#e2e8f0",
    "border_strong": "#cbd5e1",
    "border_accent": "#bfdbfe",

    # Text
    "text":          "#0f172a",
    "text_muted":    "#475569",
    "text_dim":      "#64748b",
    "text_faint":    "#94a3b8",

    # Primary accent (blue)
    "accent":        "#2563eb",
    "accent_dark":   "#1d4ed8",
    "accent_soft":   "#dbeafe",
    "accent_bg":     "#eff6ff",

    # Agent role colors
    "vehicle":       "#2563eb",  # CAV
    "infra":         "#d97706",  # RSU

    # Status colors
    "green":         "#10b981",
    "green_dark":    "#059669",
    "green_soft":    "#d1fae5",
    "green_bg":      "#ecfdf5",
    "amber":         "#d97706",
    "amber_soft":    "#fef3c7",
    "amber_bg":      "#fffbeb",
    "red":           "#dc2626",
    "red_dark":      "#b91c1c",
    "red_soft":      "#fecaca",
    "red_bg":        "#fef2f2",

    # Tunnel gradient (kept saturated — works on light bg)
    "tunnel_blue":   "#3b82f6",
    "tunnel_cyan":   "#22d3ee",
    "tunnel_green":  "#10b981",
    "tunnel_track":  "#e2e8f0",

    # Object pill colors
    "obj_car":         "#2563eb",
    "obj_pedestrian":  "#059669",
    "obj_truck":       "#d97706",
    "obj_bus":         "#7c3aed",
    "obj_van":         "#ea580c",
    "obj_other":       "#64748b",
}

FONTS = {
    "mono": "'JetBrains Mono', monospace",
    "sans": "'Inter', sans-serif",
}

SHADOWS = {
    "panel": "0 1px 3px rgba(15, 23, 42, 0.04)",
    "card":  "0 2px 8px rgba(15, 23, 42, 0.06)",
}


def make_global_css() -> str:
    """Page-level styling: html/body, hero, stage box, filepath bar,
    scenario card, locked state, selectbox, button, section header,
    pipeline, divider, fadeIn keyframe."""
    c = COLORS
    return f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;600&display=swap');

  html, body, [class*="css"] {{
    font-family: {FONTS['sans']};
    background-color: {c['bg']};
    color: {c['text']};
  }}
  .stApp {{ background-color: {c['bg']}; }}
  .block-container {{ padding-top: 32px; max-width: 1300px; }}
  #MainMenu, footer, header {{ visibility: hidden; }}

  /* Hero */
  .hero {{
    background: linear-gradient(135deg, {c['panel']} 0%, {c['panel_alt']} 60%, {c['panel']} 100%);
    border: 1px solid {c['border_accent']};
    border-radius: 20px;
    padding: 52px 48px 44px;
    margin-bottom: 40px;
    position: relative;
    overflow: hidden;
    box-shadow: {SHADOWS['panel']};
  }}
  .hero::after {{
    content: '';
    position: absolute;
    top: -80px; right: -80px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, {c['accent']}22 0%, transparent 65%);
    border-radius: 50%;
    pointer-events: none;
  }}
  .hero-eyebrow {{
    font-family: {FONTS['mono']};
    font-size: 21px;
    color: {c['accent']};
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 14px;
  }}
  .hero-title {{
    font-size: 46px;
    font-weight: 600;
    color: {c['text']};
    line-height: 1.2;
    margin-bottom: 12px;
  }}
  .hero-title span {{ color: {c['accent']}; }}
  .hero-sub {{
    font-size: 27px;
    color: {c['text_muted']};
    max-width: 560px;
    line-height: 1.8;
  }}

  /* Stage box */
  .stage-box {{
    background: {c['panel']};
    border: 1px solid {c['border']};
    border-radius: 16px;
    padding: 32px 36px;
    margin-bottom: 0;
    box-shadow: {SHADOWS['panel']};
  }}
  .stage-box.active {{ border-color: {c['border_accent']}; }}
  .stage-label {{
    font-family: {FONTS['mono']};
    font-size: 19px;
    color: {c['accent']};
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 8px;
  }}
  .stage-title {{
    font-size: 38px;
    font-weight: 600;
    color: {c['text']};
    margin-bottom: 6px;
  }}
  .stage-sub {{
    font-size: 26px;
    color: {c['text_dim']};
    margin-bottom: 24px;
    line-height: 1.6;
  }}

  /* Filepath bar */
  .filepath-bar {{
    display: flex;
    align-items: center;
    gap: 0;
    background: {c['panel']};
    border: 1px solid {c['border_strong']};
    border-radius: 8px;
    padding: 0;
    margin-bottom: 16px;
    overflow: hidden;
    font-family: {FONTS['mono']};
    font-size: 22px;
  }}
  .filepath-icon {{
    background: {c['accent_soft']};
    border-right: 1px solid {c['border_strong']};
    padding: 10px 14px;
    color: {c['accent']};
    font-size: 27px;
  }}
  .filepath-text {{
    flex: 1;
    padding: 10px 14px;
    color: {c['text_faint']};
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .filepath-text.filled {{ color: {c['accent_dark']}; }}

  /* Scenario detected card */
  .scenario-detected {{
    background: {c['accent_bg']};
    border: 1px solid {c['border_accent']};
    border-left: 3px solid {c['accent']};
    border-radius: 10px;
    padding: 16px 20px;
    margin-top: 16px;
    font-family: {FONTS['mono']};
    font-size: 22px;
  }}
  .scenario-detected .s-label {{
    color: {c['text_dim']};
    font-size: 19px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 4px;
  }}
  .scenario-detected .s-value {{ color: {c['accent_dark']}; font-size: 29px; font-weight: 600; margin-bottom: 8px; }}
  .scenario-detected .s-meta  {{ color: {c['text_muted']}; font-size: 21px; line-height: 2.0; }}
  .scenario-detected .s-meta span {{ color: {c['text_dim']}; }}

  /* Stage 2 locked */
  .stage2-locked {{
    background: {c['panel_alt']};
    border: 1px dashed {c['border_strong']};
    border-radius: 16px;
    padding: 52px 36px;
    text-align: center;
    color: {c['text_faint']};
    font-family: {FONTS['mono']};
    font-size: 22px;
    letter-spacing: 0.1em;
  }}

  /* Selectbox */
  [data-testid="stSelectbox"] > div > div {{
    background: {c['panel']} !important;
    border: 1px solid {c['border_strong']} !important;
    border-radius: 8px !important;
    font-family: {FONTS['mono']} !important;
    font-size: 22px !important;
    color: {c['accent_dark']} !important;
  }}

  /* Button */
  .stButton > button {{
    background: {c['accent']} !important;
    border: 1px solid {c['accent']} !important;
    color: #ffffff !important;
    font-family: {FONTS['mono']} !important;
    font-size: 22px !important;
    border-radius: 8px !important;
    padding: 8px 20px !important;
    letter-spacing: 0.05em !important;
  }}
  .stButton > button:hover {{
    background: {c['accent_dark']} !important;
    border-color: {c['accent_dark']} !important;
    color: #ffffff !important;
  }}

  /* Section header + pipeline */
  .section-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 32px 0 16px;
  }}
  .section-num {{
    font-family: {FONTS['mono']};
    font-size: 21px;
    color: {c['accent']};
    background: {c['accent_soft']};
    padding: 3px 8px;
    border-radius: 4px;
    letter-spacing: 0.05em;
  }}
  .section-title {{
    font-size: 35px;
    font-weight: 600;
    color: {c['text']};
  }}
  .pipeline {{
    display: flex;
    align-items: center;
    gap: 0;
    background: {c['panel']};
    border: 1px solid {c['border']};
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 8px;
    overflow-x: auto;
    box-shadow: {SHADOWS['panel']};
  }}
  .pipe-step {{
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 110px;
  }}
  .pipe-icon {{
    width: 44px; height: 44px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 38px;
    margin-bottom: 8px;
  }}
  .pipe-icon.active   {{ background: {c['accent_soft']}; box-shadow: 0 0 16px {c['accent']}22; }}
  .pipe-icon.inactive {{ background: {c['panel_alt']}; }}
  .pipe-label {{
    font-size: 21px;
    color: {c['text_muted']};
    text-align: center;
    font-family: {FONTS['mono']};
  }}
  .pipe-label.active {{ color: {c['accent_dark']}; }}
  .pipe-arrow {{
    font-size: 35px;
    color: {c['border_strong']};
    margin: 0 6px;
    padding-bottom: 20px;
  }}
  .custom-divider {{
    border: none;
    border-top: 1px solid {c['border']};
    margin: 24px 0;
  }}

  /* Reusable compact download icon (shares a header row, with hover tooltip) */
  .dl-header {{
    display: flex; align-items: center; justify-content: space-between;
    gap: 12px;
  }}
  .dl-icon {{
    flex: 0 0 auto; position: relative;
    width: 30px; height: 30px; border-radius: 7px;
    display: inline-flex; align-items: center; justify-content: center;
    background: {c['panel']}; border: 1px solid {c['border_strong']};
    color: {c['accent']}; text-decoration: none; font-size: 27px;
    cursor: pointer; transition: background 0.15s, box-shadow 0.15s;
  }}
  .dl-icon:hover {{
    background: {c['accent_soft']};
    box-shadow: 0 0 12px {c['accent']}44;
  }}
  .dl-icon::after {{
    content: attr(data-tip);
    position: absolute; top: 50%; right: 120%; transform: translateY(-50%);
    white-space: nowrap; background: {c['text']}; color: #ffffff;
    font-family: {FONTS['mono']}; font-size: 19px;
    padding: 5px 9px; border-radius: 6px;
    opacity: 0; pointer-events: none; transition: opacity 0.15s; z-index: 10;
  }}
  .dl-icon:hover::after {{ opacity: 1; }}

  /* Shared animation */
  @keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}
</style>
"""


def make_stage2_css() -> str:
    """Stage 2 only: object pills, agent cards, agent badges."""
    c = COLORS
    return f"""
<style>
  .obj-pill {{
    display: inline-block;
    font-family: {FONTS['mono']};
    font-size: 19px;
    padding: 2px 8px;
    border-radius: 4px;
    margin: 2px 3px 2px 0;
    background: {c['panel']};
    color: {c['text_muted']};
    border: 1px solid {c['border']};
  }}
  .obj-pill.car        {{ color: {c['obj_car']};        border-color: {c['border_accent']}; background: {c['accent_bg']}; }}
  .obj-pill.pedestrian {{ color: {c['obj_pedestrian']}; border-color: #a7f3d0; background: {c['green_bg']}; }}
  .obj-pill.truck      {{ color: {c['obj_truck']};      border-color: #fcd34d; background: {c['amber_bg']}; }}
  .obj-pill.bus        {{ color: {c['obj_bus']};        border-color: #ddd6fe; background: #f5f3ff; }}
  .obj-pill.van        {{ color: {c['obj_van']};        border-color: #fed7aa; background: #fff7ed; }}
  .obj-pill.other      {{ color: {c['obj_other']};      border-color: {c['border']}; }}

  .agent-card-box {{
    background: {c['panel']};
    border: 1px solid {c['border']};
    border-radius: 12px;
    padding: 18px 20px;
    height: 100%;
    box-shadow: {SHADOWS['panel']};
  }}
  .agent-card-box.vehicle {{ border-left: 3px solid {c['vehicle']}; }}
  .agent-card-box.infra   {{ border-left: 3px solid {c['infra']}; }}

  .agent-badge {{
    display: inline-block;
    font-family: {FONTS['mono']};
    font-size: 19px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.08em;
    margin-bottom: 10px;
  }}
  .badge-vehicle {{ background: {c['accent_bg']}; color: {c['vehicle']}; border: 1px solid {c['border_accent']}; }}
  .badge-infra   {{ background: {c['amber_bg']};  color: {c['infra']};   border: 1px solid #fcd34d; }}

  .agent-meta-row {{
    font-family: {FONTS['mono']};
    font-size: 21px;
    color: {c['text_muted']};
    line-height: 2.1;
  }}
  .agent-meta-row span {{ color: {c['text_dim']}; }}
</style>
"""


def make_stage3_css() -> str:
    """Stage 3 only: model comparison cards, recommendation card,
    config block, proceed hint, video controls hide."""
    c = COLORS
    return f"""
<style>
  /* Hide video controls */
  video::-webkit-media-controls {{ display: none !important; }}
  video {{ pointer-events: none; }}

  /* Model compare cards */
  .mc-card {{
    background: {c['panel']};
    border: 1px solid {c['border']};
    border-radius: 12px;
    padding: 20px 16px;
    position: relative;
    transition: border-color 0.5s, box-shadow 0.5s;
    box-shadow: {SHADOWS['panel']};
  }}
  .mc-card.best-glow {{
    border-color: {c['green']};
    box-shadow: 0 0 28px {c['green']}33, 0 0 56px {c['green']}11;
  }}
  .mc-card.best-glow::before {{
    content: '★  BEST';
    position: absolute;
    top: -10px; left: 50%;
    transform: translateX(-50%);
    background: {c['green_dark']};
    color: #ffffff;
    font-family: {FONTS['mono']};
    font-size: 18px; font-weight: 700;
    letter-spacing: 0.15em;
    padding: 2px 10px;
    border-radius: 10px;
    white-space: nowrap;
  }}
  .mc-model-name {{
    font-family: {FONTS['mono']};
    font-size: 21px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em;
    color: {c['text_dim']};
    margin-bottom: 14px;
    text-align: center;
  }}
  .mc-model-name.best {{ color: {c['green_dark']}; }}

  .mc-row {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-family: {FONTS['mono']};
    font-size: 21px;
    color: {c['text_muted']};
    padding: 4px 0;
    border-bottom: 1px solid {c['border']};
  }}
  .mc-row:last-child {{ border-bottom: none; }}
  .mc-row-label {{ color: {c['text_dim']}; font-size: 19px; }}
  .mc-row-vals  {{ display: inline-flex; align-items: baseline; gap: 4px; }}
  .mc-row-raw   {{ color: {c['text_dim']}; font-size: 21px; font-weight: 600; }}
  .mc-row-arrow {{ color: {c['text_faint']}; font-size: 19px; }}
  .mc-row-val   {{ color: {c['text']}; font-size: 26px; font-weight: 700; }}
  .mc-row-val.improved {{ color: {c['accent']}; }}
  .mc-row-val.best-val {{ color: {c['green_dark']}; }}
  .mc-delta-inline {{
    font-size: 18px;
    margin-left: 2px;
    font-weight: 600;
  }}
  .mc-delta-inline.up   {{ color: {c['green_dark']}; }}
  .mc-delta-inline.down {{ color: {c['red']}; }}

  /* Recommendation card */
  .rec-card {{
    position: relative;
    max-width: 880px;
    background: {c['green_bg']};
    border: 1px solid {c['green']}66;
    border-left: 4px solid {c['green']};
    border-radius: 12px;
    padding: 28px 32px;
    margin: 24px 0;
    animation: recFadeIn 0.7s ease;
    box-shadow: {SHADOWS['card']};
  }}

  /* Corner download icon + hover tooltip */
  .rec-download {{
    position: absolute; top: 16px; right: 18px;
    width: 34px; height: 34px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    background: {c['panel']}; border: 1px solid {c['green']}66;
    color: {c['green_dark']}; text-decoration: none; font-size: 30px;
    cursor: pointer; transition: background 0.15s, box-shadow 0.15s;
  }}
  .rec-download:hover {{
    background: {c['green_soft']};
    box-shadow: 0 0 14px {c['green']}44;
  }}
  .rec-download::after {{
    content: attr(data-tip);
    position: absolute; top: 50%; right: 120%;
    transform: translateY(-50%);
    white-space: nowrap;
    background: {c['text']}; color: #ffffff;
    font-family: {FONTS['mono']}; font-size: 19px;
    padding: 5px 9px; border-radius: 6px;
    opacity: 0; pointer-events: none; transition: opacity 0.15s;
  }}
  .rec-download:hover::after {{ opacity: 1; }}
  @keyframes recFadeIn {{
    from {{ opacity:0; transform:translateY(12px); }}
    to   {{ opacity:1; transform:translateY(0); }}
  }}
  .rec-eyebrow {{
    font-family: {FONTS['mono']};
    font-size: 19px; color: {c['green_dark']};
    text-transform: uppercase; letter-spacing: 0.18em;
    margin-bottom: 6px;
  }}
  .rec-model-name {{
    font-size: 50px; font-weight: 600;
    color: {c['green_dark']}; margin-bottom: 16px;
  }}
  .rec-delta-cards {{
    display: flex; gap: 10px; flex-wrap: wrap;
    margin-bottom: 20px;
  }}
  .rec-delta-card {{
    background: {c['panel']};
    border: 1px solid {c['green']}55;
    border-radius: 8px;
    padding: 10px 16px;
    text-align: center;
    min-width: 100px;
  }}
  .rec-delta-val {{
    font-family: {FONTS['mono']};
    font-size: 38px; font-weight: 700;
    color: {c['green_dark']}; line-height: 1;
    margin-bottom: 3px;
  }}
  .rec-delta-label {{
    font-family: {FONTS['mono']};
    font-size: 18px; color: {c['green_dark']};
    text-transform: uppercase; letter-spacing: 0.1em;
  }}
  .rec-divider {{ border:none; border-top:1px solid {c['green']}33; margin:16px 0; }}
  .rec-section-label {{
    font-family: {FONTS['mono']};
    font-size: 19px; color: {c['green_dark']};
    text-transform: uppercase; letter-spacing: 0.12em;
    margin-bottom: 8px; font-weight: 600;
  }}
  .config-block {{
    background: {c['panel']};
    border: 1px solid {c['green']}33;
    border-radius: 8px;
    padding: 14px 18px;
    font-family: {FONTS['mono']};
    font-size: 21px; color: {c['text_muted']}; line-height: 2.2;
  }}
  .ck {{ color: {c['green_dark']}; }}
  .cv {{ color: {c['text']}; font-weight: 600; }}
  .rec-body {{ font-size: 26px; color: {c['text_muted']}; line-height: 1.8; }}

  .proceed-hint {{
    text-align: center;
    font-family: {FONTS['mono']};
    font-size: 21px; color: {c['text_dim']};
    letter-spacing: 0.1em; margin-bottom: 8px;
    text-transform: uppercase;
  }}

  /* Frame-by-frame comparison table */
  .fc-table {{
    border: 1px solid {c['border']}; border-radius: 12px; overflow: hidden;
    background: {c['panel']}; box-shadow: {SHADOWS['panel']}; margin-bottom: 18px;
  }}
  .fc-row {{ display: flex; align-items: stretch; border-bottom: 1px solid {c['border']}; }}
  .fc-row:last-child {{ border-bottom: none; }}
  .fc-metric-label {{
    flex: 0 0 96px; padding: 9px 14px;
    font-family: {FONTS['mono']}; font-size: 21px; color: {c['text_dim']};
    display: flex; align-items: center;
    background: {c['panel_alt']}; border-right: 1px solid {c['border']};
  }}
  .fc-cell {{
    flex: 1; padding: 9px 12px; text-align: center;
    font-family: {FONTS['mono']}; font-size: 27px; font-weight: 700; color: {c['text']};
    border-right: 1px solid {c['border']};
  }}
  .fc-cell:last-child {{ border-right: none; }}
  .fc-cell.best {{ background: {c['green_bg']}; color: {c['green_dark']}; }}
  .fc-head {{ background: {c['panel_alt']}; }}
  .fc-head .fc-cell {{ font-size: 21px; font-weight: 600; color: {c['text']}; line-height: 1.4; }}
  .fc-head .fc-cell span {{
    display: block; font-size: 18px; color: {c['text_dim']};
    font-weight: 400; margin-top: 2px;
  }}
  .fc-row.f1 .fc-metric-label {{ color: {c['accent']}; font-weight: 700; }}
  .fc-row.f1 .fc-cell {{ font-size: 30px; }}
  .fc-row.f1 .fc-cell.best {{ color: {c['green_dark']}; }}
  .fc-img-label {{
    font-family: {FONTS['mono']}; font-size: 21px; color: {c['text_muted']};
    margin: 16px 0 6px; font-weight: 600;
  }}
  .fc-img-label span {{ color: {c['text_dim']}; font-weight: 400; }}
</style>
"""


def make_nav_css() -> str:
    """Shared top-nav bar styling used across all pages."""
    return """
<style>
 @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;600&display=swap');
 html { background-color: #f8fafc !important; }
 html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
 @keyframes v2vFadeIn {
   from { opacity: 0; transform: translateY(6px); }
   to   { opacity: 1; transform: translateY(0); }
 }
 .stApp, [data-testid="stAppViewContainer"] {
   background-color: #f8fafc !important;
   color: #0f172a !important;
   animation: v2vFadeIn 0.25s ease forwards;
 }
 [data-testid="stHeader"] { background-color: #f8fafc !important; }
 #MainMenu, footer, header { visibility: hidden; }
 [data-testid="stSidebarNav"] { display: none !important; }
 [data-testid="stSidebar"] { display: none !important; }
 [data-testid="collapsedControl"] { display: none !important; }
 .block-container { padding-top: 32px !important; max-width: 1300px !important; }
 h1, h2, h3, h4, h5, h6, .stMarkdown p, p, label { color: #0f172a !important; }
 hr { border-color: #B0B8C8 !important; }
 .stCaption, medium { color: #4B5563 !important; }
 .v2v-site-title {
   font-size: 45px;
   font-weight: 700;
   color: #111827 !important;
   margin: 0;
   padding: 8px 0 14px;
   letter-spacing: -0.01em;
   line-height: 1.1;
 }
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
   font-family: 'Inter', sans-serif !important;
   font-size: 18px !important;
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
</style>
"""


def make_stage4_css() -> str:
    """Stage 4 only: channel-noise metric strip, status badge, image rows
    with selected-column glow, BEV legend, and explanatory note."""
    c = COLORS
    return f"""
<style>
  /* Metric strip */
  .s4-metric-wrap {{
    display: flex; align-items: stretch; gap: 14px;
    margin: 8px 0 6px; flex-wrap: wrap;
  }}
  .s4-metric-card {{
    background: {c['panel']};
    border: 1px solid {c['border']};
    border-radius: 12px;
    padding: 16px 22px;
    box-shadow: {SHADOWS['panel']};
    min-width: 150px;
  }}
  .s4-metric-label {{
    font-family: {FONTS['mono']}; font-size: 18px;
    color: {c['text_dim']}; text-transform: uppercase;
    letter-spacing: 0.12em; margin-bottom: 6px;
  }}
  .s4-metric-val {{
    font-family: {FONTS['mono']}; font-size: 58px;
    font-weight: 700; line-height: 1; color: {c['text']};
  }}
  .s4-metric-sub {{
    font-family: {FONTS['mono']}; font-size: 19px;
    color: {c['text_faint']}; margin-top: 6px;
  }}

  /* Status badge */
  .s4-status {{
    display: flex; flex-direction: column; justify-content: center;
    border-radius: 12px; padding: 16px 22px; min-width: 220px;
    border: 1px solid transparent;
  }}
  .s4-status.beneficial     {{ background: {c['green_bg']}; border-color: {c['green']}66; }}
  .s4-status.below_baseline {{ background: {c['amber_bg']}; border-color: {c['amber']}66; }}
  .s4-status.collapse       {{ background: {c['red_bg']};   border-color: {c['red']}66; }}
  .s4-status-label {{
    font-family: {FONTS['mono']}; font-size: 27px; font-weight: 700;
    letter-spacing: 0.03em; margin-bottom: 4px;
  }}
  .s4-status.beneficial     .s4-status-label {{ color: {c['green_dark']}; }}
  .s4-status.below_baseline .s4-status-label {{ color: {c['amber']}; }}
  .s4-status.collapse       .s4-status-label {{ color: {c['red_dark']}; }}
  .s4-status-desc {{
    font-family: {FONTS['mono']}; font-size: 19px;
    color: {c['text_muted']}; line-height: 1.5;
  }}

  /* Ego-only reference line */
  .s4-baseline {{
    font-family: {FONTS['mono']}; font-size: 21px;
    color: {c['text_muted']}; background: {c['panel_alt']};
    border: 1px dashed {c['border_strong']}; border-radius: 8px;
    padding: 8px 14px; margin: 10px 0 4px; line-height: 1.6;
  }}
  .s4-baseline b {{ color: {c['text']}; }}

  /* Row label */
  .s4-row-label {{
    font-family: {FONTS['mono']}; font-size: 19px;
    color: {c['accent']}; text-transform: uppercase;
    letter-spacing: 0.15em; margin: 22px 0 12px;
  }}
  .s4-row-label span {{ color: {c['text_dim']}; text-transform: none; letter-spacing: 0; }}

  /* Image rows */
  .s4-row {{
    display: flex; gap: 10px; align-items: flex-start;
    overflow-x: auto; padding: 6px 2px 4px;
  }}
  .s4-cell {{ flex: 1 1 0; min-width: 150px; text-align: center; }}
  .s4-cell a {{ display: block; }}
  .s4-cell img {{
    width: 100%; height: auto; display: block;
    border-radius: 8px; border: 2px solid {c['border']};
    background: #0a0e1a;
    transition: box-shadow 0.25s, border-color 0.25s;
  }}
  .s4-cell.sel img {{
    border-color: {c['green']};
    box-shadow: 0 0 18px {c['green']}66, 0 0 40px {c['green']}22;
  }}
  .s4-cap {{
    font-family: {FONTS['mono']}; font-size: 19px;
    color: {c['text_dim']}; margin-top: 6px; line-height: 1.4;
  }}
  .s4-cell.sel .s4-cap {{ color: {c['green_dark']}; font-weight: 700; }}
  .s4-cell-missing {{
    width: 100%; aspect-ratio: 2 / 1; border-radius: 8px;
    border: 2px dashed {c['border_strong']}; background: {c['panel_alt']};
    display: flex; align-items: center; justify-content: center;
    font-family: {FONTS['mono']}; font-size: 19px; color: {c['text_faint']};
  }}

  /* BEV large-selected view + thumbnail strip */
  .s4-bev-large {{ max-width: 760px; margin: 0 auto; }}
  .s4-bev-large img {{
    width: 100%; height: auto; display: block;
    border-radius: 10px; border: 2px solid {c['green']};
    box-shadow: 0 0 18px {c['green']}66, 0 0 40px {c['green']}22;
  }}
  .s4-bev-large .s4-cap {{ text-align: center; margin-top: 8px; }}
  .s4-row.thumbs {{ margin-top: 10px; }}
  .s4-row.thumbs .s4-cell {{ min-width: 88px; }}
  .s4-row.thumbs .s4-cap {{ font-size: 18px; }}

  /* BEV legend */
  .s4-legend {{
    display: flex; gap: 20px; flex-wrap: wrap; align-items: center;
    margin: 4px 0 10px; font-family: {FONTS['mono']}; font-size: 21px;
    color: {c['text_muted']};
  }}
  .s4-legend-item {{ display: inline-flex; align-items: center; gap: 7px; }}
  .s4-swatch {{ width: 22px; height: 13px; border-radius: 2px; }}
  .s4-swatch.tp {{ border: 2px solid {c['green']}; }}
  .s4-swatch.fp {{ border: 2px solid {c['red']}; }}
  .s4-swatch.fn {{ border: 2px dotted {c['accent']}; }}

  /* Explanatory note */
  .s4-note {{
    background: {c['panel_alt']};
    border: 1px solid {c['border']};
    border-left: 3px solid {c['accent']};
    border-radius: 8px; padding: 12px 16px; margin-top: 12px;
    font-family: {FONTS['mono']}; font-size: 21px;
    color: {c['text_muted']}; line-height: 1.8;
  }}
  .s4-note b {{ color: {c['text']}; }}
</style>
"""
