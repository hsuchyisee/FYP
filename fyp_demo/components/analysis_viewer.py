import streamlit as st
from pathlib import Path
from config import ANALYSIS_DIR


def render_analysis():
    ap_path   = Path(ANALYSIS_DIR) / "ap_analysis.png"
    loss_path = Path(ANALYSIS_DIR) / "loss_curves.png"

    st.markdown("**AP Analysis**")
    if ap_path.exists():
        st.image(str(ap_path), use_column_width=True)
    else:
        st.warning(f"File not found: {ap_path}")

    st.markdown("**Loss Curves**")
    if loss_path.exists():
        st.image(str(loss_path), use_column_width=True)
    else:
        st.warning(f"File not found: {loss_path}")
