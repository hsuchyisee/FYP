import streamlit as st
from components.media_viewer import render_media
from components.analysis_viewer import render_analysis
from config import MODELS, SCENARIOS

st.set_page_config(page_title="V2V Dashboard", layout="wide")
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

# ── AP Analysis & Loss Curves ─────────────────────────────────
st.subheader("Training Analysis")
render_analysis()

st.divider()
st.caption("FYP — Semantic V2V Communication for Autonomous Cooperative Perception")