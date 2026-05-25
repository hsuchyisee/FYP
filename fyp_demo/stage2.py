import streamlit as st
import yaml
import plotly.graph_objects as go
from pathlib import Path
from collections import Counter
from theme import COLORS, FONTS


def load_frame_yaml(agent_path: Path, frame: str = "000000") -> dict:
    yaml_path = agent_path / f"{frame}.yaml"
    if not yaml_path.exists():
        return {}
    with open(yaml_path) as f:
        return yaml.safe_load(f)


def get_agent_folders(scenario_path: Path) -> list:
    return sorted(
        [d for d in scenario_path.iterdir() if d.is_dir()],
        key=lambda x: x.name
    )


def render_agent_map(agents_data: list):
    fig = go.Figure()
    for agent in agents_data:
        color  = COLORS["infra"] if agent["is_infra"] else COLORS["vehicle"]
        symbol = "square"  if agent["is_infra"] else "circle"
        label  = f"RSU {agent['name']}" if agent["is_infra"] else f"CAV {agent['name']}"
        fig.add_trace(go.Scatter(
            x=[agent["x"]], y=[agent["y"]],
            mode="markers+text",
            marker=dict(size=18, color=color, symbol=symbol,
                        line=dict(color=COLORS["panel"], width=2)),
            text=[label], textposition="top center",
            textfont=dict(family="JetBrains Mono", size=11, color=color),
            name=label, showlegend=True
        ))
    fig.update_layout(
        paper_bgcolor=COLORS["panel"], plot_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text_muted"], family="JetBrains Mono", size=10),
        title=dict(text="Agent Positions — Top-Down View (Frame 000000)",
                   font=dict(color=COLORS["text"], size=12), x=0.02),
        xaxis=dict(showgrid=True, gridcolor=COLORS["border"], zeroline=False,
                   tickfont=dict(size=9),
                   title=dict(text="X (m)", font=dict(size=10, color=COLORS["text_dim"]))),
        yaxis=dict(showgrid=True, gridcolor=COLORS["border"], zeroline=False,
                   tickfont=dict(size=9),
                   title=dict(text="Y (m)", font=dict(size=10, color=COLORS["text_dim"])),
                   scaleanchor="x", scaleratio=1),
        legend=dict(bgcolor=COLORS["panel"], bordercolor=COLORS["border"],
                    borderwidth=1, font=dict(size=10)),
        margin=dict(l=40, r=20, t=40, b=40), height=380,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_agent_card(agent: dict, scenario_path: Path):
    """Render one agent card with metadata + camera images below."""
    is_infra   = agent["is_infra"]
    card_class = "infra"   if is_infra else "vehicle"
    badge_cls  = "badge-infra" if is_infra else "badge-vehicle"
    agent_type = "RSU" if is_infra else "CAV"
    cam_count  = 2 if is_infra else 4
    pose       = agent["pose"]
    speed      = agent["speed"]

    st.markdown(f"""
    <div class="agent-card-box {card_class}">
      <span class="agent-badge {badge_cls}">{agent_type} {agent["name"]}</span>
      <div class="agent-meta-row">
        <span>Position ·</span> ({pose[0]:.1f}, {pose[1]:.1f}) m<br>
        <span>Speed ·</span> {speed:.1f} m/s<br>
        <span>Cameras ·</span> {cam_count} feeds<br>
        <span>LiDAR ·</span> Active
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Camera images below the card — dynamically loaded
    cam_images = sorted((scenario_path / agent["name"]).glob("000000_cam*.jpeg"))

    if cam_images:
        if len(cam_images) <= 2:
            # RSU: 2 cameras side by side
            cols = st.columns(2)
            for i, (col, img) in enumerate(zip(cols, cam_images)):
                with col:
                    st.image(str(img), caption=f"cam{i+1}", use_container_width=True)
        else:
            # CAV: 4 cameras — 2 on top row, 2 on bottom row
            top_imgs = cam_images[:2]
            bot_imgs = cam_images[2:]

            top_cols = st.columns(2)
            for i, (col, img) in enumerate(zip(top_cols, top_imgs)):
                with col:
                    st.image(str(img), caption=f"cam{i+1}", use_container_width=True)

            bot_cols = st.columns(2)
            for i, (col, img) in enumerate(zip(bot_cols, bot_imgs)):
                with col:
                    st.image(str(img), caption=f"cam{i+3}", use_container_width=True)
    else:
        st.caption(f"No camera images found for {agent_type} {agent['name']}")


def render_stage2(scenario_id: str, dataset_root: str):
    scenario_path = Path(dataset_root) / scenario_id

    if not scenario_path.exists():
        st.error(f"Scenario folder not found: {scenario_path}")
        st.info("Update dataset_root in stage1_v2.py to point to a valid Camera_LiDAR directory")
        return

    agent_folders = get_agent_folders(scenario_path)
    if not agent_folders:
        st.error("No agent folders found.")
        return

    # ── Section header ─────────────────────────────────────────
    st.markdown("""
    <div class="stage-box active" style="animation:fadeIn 0.5s ease;">
      <div class="stage-label">Stage 02 · Scene Intelligence</div>
      <div class="stage-title">Multi-Agent Sensor Overview</div>
      <div class="stage-sub">
        Real-world synchronised sensor data from all cooperating agents at frame 000000.
        Vehicles (CAV) share LiDAR and camera data with roadside infrastructure (RSU)
        to achieve cooperative perception beyond individual line-of-sight.
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Load all agents ────────────────────────────────────────
    agents_data  = []
    all_vehicles = {}
    obj_types    = []
    speeds       = []

    for agent_dir in agent_folders:
        data = load_frame_yaml(agent_dir, "000000")
        if not data:
            continue
        pose     = data.get("true_ego_pose", [0]*6)
        is_infra = data.get("infra", False)
        speed    = data.get("ego_speed", 0) or 0
        agents_data.append({
            "name":     agent_dir.name,
            "dir":      agent_dir,
            "x":        pose[0],
            "y":        pose[1],
            "is_infra": is_infra,
            "speed":    speed,
            "pose":     pose,
            "data":     data,
        })
        speeds.append(speed)
        for vid, vdata in (data.get("vehicles") or {}).items():
            if vid not in all_vehicles:
                all_vehicles[vid] = vdata
                obj_types.append(vdata.get("obj_type", "Unknown"))

    # ── Stats strip ────────────────────────────────────────────
    n_cav   = sum(1 for a in agents_data if not a["is_infra"])
    n_rsu   = sum(1 for a in agents_data if a["is_infra"])
    n_obj   = len(all_vehicles)
    avg_spd = sum(speeds) / len(speeds) if speeds else 0.0
    type_counts = Counter(obj_types)

    st.markdown(f"""
    <div style="font-family:{FONTS['mono']};font-size: 19px;
         color:{COLORS['accent']};text-transform:uppercase;letter-spacing:0.15em;
         margin-bottom:12px;">Scene Statistics · Frame 000000</div>
    """, unsafe_allow_html=True)

    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    for col, label, value, color in [
        (sc1, "Total Agents",           len(agents_data), COLORS["text"]),
        (sc2, "Vehicles (CAV)",         n_cav,            COLORS["vehicle"]),
        (sc3, "Infrastructure (RSU)",   n_rsu,            COLORS["infra"]),
        (sc4, "Objects in Scene",       n_obj,            COLORS["green_dark"]),
        (sc5, "Avg Speed (m/s)",        f"{avg_spd:.1f}", "#7c3aed"),
    ]:
        with col:
            st.markdown(f"""
            <div style="background:{COLORS['panel']};border:1px solid {COLORS['border']};border-radius:10px;
                 padding:14px 12px;text-align:center;box-shadow:0 1px 3px rgba(15,23,42,0.04);">
              <div style="font-family:{FONTS['mono']};font-size: 50px;
                   font-weight:700;color:{color};line-height:1;margin-bottom:6px;">
                {value}
              </div>
              <div style="font-size: 19px;color:{COLORS['text_dim']};text-transform:uppercase;
                   letter-spacing:0.08em;font-family:{FONTS['mono']};
                   line-height:1.4;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    # Object type pills — fixed: show "Type × count" for ALL types
    color_map = {
        "Car": "car", "Pedestrian": "pedestrian",
        "Truck": "truck", "Bus": "bus", "Van": "van"
    }
    obj_parts = []
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        css = color_map.get(t, "other")
        obj_parts.append(
            f'<span class="obj-pill {css}" style="margin:0 6px;">'
            f'{t}&nbsp;&times;&nbsp;{c}</span>'
        )
    obj_sentence = f' <span style="color:{COLORS["text_faint"]};">·</span> '.join(obj_parts)
    st.markdown(f"""
    <div style="margin:12px 0 28px;line-height:2.5;">
      <span style="font-family:{FONTS['mono']};font-size: 19px;
            color:{COLORS['accent']};text-transform:uppercase;letter-spacing:0.1em;
            margin-right:12px;">Objects detected</span>
      {obj_sentence}
    </div>
    """, unsafe_allow_html=True)

    # ── Agent map full width ───────────────────────────────────
    render_agent_map(agents_data)

    st.markdown(
        f'<hr style="border:none;border-top:1px solid {COLORS["border"]};margin:28px 0;">',
        unsafe_allow_html=True,
    )

    # ── Agent cards — 2x2 grid ─────────────────────────────────
    # Separate infra and vehicle agents
    infra_agents   = [a for a in agents_data if a["is_infra"]]
    vehicle_agents = [a for a in agents_data if not a["is_infra"]]

    st.markdown(f"""
    <div style="font-family:{FONTS['mono']};font-size: 19px;
         color:{COLORS['accent']};text-transform:uppercase;letter-spacing:0.15em;
         margin-bottom:20px;">Agent Details &amp; Camera Feeds · Frame 000000</div>
    """, unsafe_allow_html=True)

    # Row 1: RSU cards
    if infra_agents:
        rsu_cols = st.columns(len(infra_agents))
        for col, agent in zip(rsu_cols, infra_agents):
            with col:
                render_agent_card(agent, scenario_path)

    st.markdown("<br>", unsafe_allow_html=True)

    # Row 2: CAV cards
    if vehicle_agents:
        cav_cols = st.columns(len(vehicle_agents))
        for col, agent in zip(cav_cols, vehicle_agents):
            with col:
                render_agent_card(agent, scenario_path)