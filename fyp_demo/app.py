import streamlit as st
from components.media_viewer import render_media
from components.analysis_viewer import render_analysis
from config import MODELS, SCENARIOS
from components.plotly_viewer import render_plotly_analysis
from theme import make_nav_css

st.set_page_config(page_title="V2V Dashboard", layout="wide")

st.markdown(make_nav_css(), unsafe_allow_html=True)
st.markdown("""
<div class="v2v-site-title">Semantic V2V Communication</div>
<nav class="v2v-nav">
  <a href="/" class="v2v-tab active" target="_self">Dashboard</a>
  <a href="/analysis" class="v2v-tab" target="_self">Analysis</a>
  <a href="/tensorboard" class="v2v-tab" target="_self">Summary</a>
</nav>
""", unsafe_allow_html=True)

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
