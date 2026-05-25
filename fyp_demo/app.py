import streamlit as st
from components.media_viewer import render_media
from components.analysis_viewer import render_analysis
from config import MODELS, SCENARIOS
from components.plotly_viewer import render_plotly_analysis
from theme import make_nav_css

st.set_page_config(page_title="V2V Dashboard", layout="wide")

<<<<<<< Updated upstream
st.markdown(make_nav_css(), unsafe_allow_html=True)
st.markdown("""
<div class="v2v-site-title">Semantic V2V Communication</div>
<nav class="v2v-nav">
  <a href="/" class="v2v-tab active" target="_self">Dashboard</a>
  <a href="/analysis" class="v2v-tab" target="_self">Analysis</a>
  <a href="/tensorboard" class="v2v-tab" target="_self">TensorBoard</a>
</nav>
""", unsafe_allow_html=True)

=======
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
  .stCaption, small { color: #4B5563 !important; font-size: 1rem !important; }

  /* ── Site title ── */
  .v2v-site-title {
    font-size: 35px;
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
    font-size: 0.95rem;
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
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="v2v-site-title">Semantic V2V Communication</div>
<nav class="v2v-nav">
  <a href="/" class="v2v-tab active">Dashboard</a>
  <a href="/analysis" class="v2v-tab">Analysis</a>
</nav>
""", unsafe_allow_html=True)

st.divider()

>>>>>>> Stashed changes
st.title("Semantic V2V Communication Dashboard")
st.caption("Select a model and scenario below to view results.")

st.divider()

# ── Dropdowns — side by side ──────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    selected_model    = st.selectbox("Select Model", MODELS)
with col_b:
    selected_scenario = st.selectbox("Select Scenario", SCENARIOS)

st.divider()

# ── Pass both selections into render_media ────────────────────
render_media(selected_model, selected_scenario)

st.divider()
st.caption("FYP — Semantic V2V Communication for Autonomous Cooperative Perception")

render_plotly_analysis()
