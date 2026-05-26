import streamlit as st
from pathlib import Path
from config import MEDIA_DIR

# ── Helper: show image or a warning if file missing ───────────
def show_frame(path: Path, caption: str):
    st.markdown(f"**{caption}**")
    if path.exists():
        st.image(str(path), use_container_width=True)
    else:
        st.warning(f"File not found: {path}")


# ── Main render function called by app.py ─────────────────────
def render_media(model: str, scenario: str):
    # ── Section 1: Video ──────────────────────────────────────
    st.subheader("Video Output")
    video_path = Path(MEDIA_DIR) / "videos" / model / f"{scenario}.mp4"

    if video_path.exists():
        with open(video_path, "rb") as video_file:
            st.video(video_file.read(), autoplay=True, loop=True, muted=True)
    else:
        st.warning(f"No video found: {video_path}")

    st.divider()

    # ── Section 2: Frame-by-frame comparison ──────────────────
    st.subheader("Frame-by-Frame Comparison")

    # Build the 3 frame paths
    nofusion_path = Path(MEDIA_DIR) / "frames" / "nofusion" / model / f"{scenario}.png"  # ← added / model
    raw_path      = Path(MEDIA_DIR) / "frames" / model / "raw"      / f"{scenario}.png"
    improved_path = Path(MEDIA_DIR) / "frames" / model / "improved" / f"{scenario}.png"

    # 3 equal columns — left, middle, right
    col1, col2, col3 = st.columns(3)

    with col1:   # leftmost — nofusion baseline (only changes with scenario)
        show_frame(nofusion_path, "No Fusion (Baseline)")
    with col2:   # middle — raw model (changes with model + scenario)
        show_frame(raw_path, f"Raw Model ({model})")
    with col3:   # rightmost — improved model (changes with model + scenario)
        show_frame(improved_path, f"Improved Model ({model})")