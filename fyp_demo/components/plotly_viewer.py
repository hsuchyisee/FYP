import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import defaultdict

from components.chart_data import (
    FILTERED_RUNS, EPOCH_MAP, EPOCH_MAP_ALL_RUNS, LR_SCHEDULE, HYPERPARAM_RUNS
)

IOUS        = [0.3, 0.5, 0.7]
CLASSES     = ['vehicle', 'pedestrian', 'truck']
IOU         = 0.5

MODEL_COLORS = {
    'early':        '#4C72B0',
    'late':         '#DD8452',
    'intermediate': '#55A868',
    'v2xvit':       '#C44E52',
}

CLASS_COLORS = {
    'vehicle':    '#729ECE',
    'pedestrian': '#FF9E4A',
    'truck':      '#67BF5C',
}

IOU_OPACITY = {0.3: 0.45, 0.5: 0.9, 0.7: 0.6}


# ── Chart 1: mAP @ IoU 0.3 / 0.5 / 0.7 ──────────────────────────────────────

def chart_map_overview():
    runs = FILTERED_RUNS
    x = [r['display'].upper() + ' [' + r['tag'] + ']<br>' + r['date'] for r in runs]
    fig = go.Figure()
    for iou in IOUS:
        fig.add_trace(go.Bar(
            name=f'IoU {iou}',
            x=x,
            y=[r['mAP'][iou] for r in runs],
            marker_color=[MODEL_COLORS[r['display']] for r in runs],
            opacity=IOU_OPACITY[iou],
            hovertemplate='%{x}<br>mAP: %{y:.3f}<extra>IoU ' + str(iou) + '</extra>',
        ))
    fig.update_layout(
        title='mAP @ IoU 0.3 / 0.5 / 0.7 — All Runs',
        barmode='group',
        yaxis=dict(title='mAP', range=[0, 0.75]),
        legend_title='IoU Threshold',
        height=420,
    )
    return fig


# ── Chart 2: Per-class AP @ IoU 0.5 ──────────────────────────────────────────

def chart_per_class(iou=IOU):
    runs = FILTERED_RUNS
    x = [r['display'].upper() + ' [' + r['tag'] + ']' for r in runs]
    fig = go.Figure()
    for cls in CLASSES:
        fig.add_trace(go.Bar(
            name=cls.capitalize(),
            x=x,
            y=[r['per_class'][cls][iou] for r in runs],
            marker_color=CLASS_COLORS[cls],
            hovertemplate='%{x}<br>AP: %{y:.3f}<extra>' + cls.capitalize() + '</extra>',
        ))
    fig.update_layout(
        title=f'Per-Class AP @ IoU {iou}',
        barmode='group',
        yaxis=dict(title=f'AP @ IoU {iou}', range=[0, 0.85]),
        legend_title='Class',
        height=420,
    )
    return fig


# ── Chart 3: Faceted epoch mAP curves (one panel per model) ──────────────────

def chart_epoch_map(iou=IOU):
    models   = ['early', 'intermediate', 'late', 'v2xvit']
    titles   = [m.upper() for m in models]
    fig = make_subplots(
        rows=1, cols=4,
        subplot_titles=titles,
        shared_yaxes=True,
    )

    # Muted palette for non-best runs
    OTHER_COLORS = ['#aaaaaa', '#bbbbbb', '#cccccc']

    for col_idx, model in enumerate(models, start=1):
        color   = MODEL_COLORS.get(model, '#888')
        runs    = EPOCH_MAP_ALL_RUNS.get(model, [])
        sched   = LR_SCHEDULE.get(model, {})
        steps   = sorted(sched.get('steps', []))
        other_i = 0

        for run in runs:
            is_best = run['is_best']
            ep_map  = run['epochs']
            epochs  = sorted(ep_map)
            maps    = [ep_map[e] for e in epochs]
            label   = run['label']

            if is_best:
                line_color = color
                dash       = 'solid'
                width      = 2.5
                opacity    = 1.0
                marker_sz  = 6
            else:
                line_color = OTHER_COLORS[other_i % len(OTHER_COLORS)]
                other_i   += 1
                dash       = 'dash'
                width      = 1.5
                opacity    = 0.75
                marker_sz  = 4

            fig.add_trace(go.Scatter(
                x=epochs, y=maps,
                mode='lines+markers',
                name=label,
                legendgroup=model,
                showlegend=(col_idx == 1),   # only show legend once per group
                line=dict(color=line_color, width=width, dash=dash),
                marker=dict(size=marker_sz, color=line_color),
                opacity=opacity,
                hovertemplate='Epoch %{x}<br>mAP: %{y:.4f}<extra>' + label + '</extra>',
            ), row=1, col=col_idx)

        # LR step annotations
        for step in steps:
            fig.add_vline(
                x=step, line_width=1, line_dash='dot',
                line_color=color, opacity=0.5,
                row=1, col=col_idx,
            )

    fig.update_layout(
        title='mAP @ IoU 0.5 over Training Epochs — Best run (solid), other runs (dashed)',
        height=420,
        showlegend=False,
    )
    fig.update_yaxes(title_text=f'mAP @ IoU {iou}', col=1)
    for col_idx in range(1, 5):
        fig.update_xaxes(title_text='Epoch', row=1, col=col_idx)
    return fig


# ── Chart 4: LR value effect ──────────────────────────────────────────────────

def chart_lr_effect(iou=IOU):
    lr_best = {}
    for r in HYPERPARAM_RUNS:
        key = (r['display'], r['lr'])
        if key not in lr_best or r['mAP_05'] > lr_best[key]:
            lr_best[key] = r['mAP_05']

    model_lrs = defaultdict(dict)
    for (model, lr), val in lr_best.items():
        model_lrs[model][lr] = val
    models = {m: lrs for m, lrs in model_lrs.items() if len(lrs) > 1}
    if not models:
        return None

    all_lrs = sorted({lr for lrs in models.values() for lr in lrs})
    fig = go.Figure()
    palette = ['#5B9BD5', '#ED7D31']
    for i, lr_val in enumerate(all_lrs):
        vals = [models[m].get(lr_val, 0) for m in models]
        fig.add_trace(go.Bar(
            name=f'lr = {lr_val}',
            x=[m.upper() for m in models],
            y=vals,
            marker_color=palette[i % len(palette)],
            text=[f'{v:.3f}' for v in vals],
            textposition='outside',
            hovertemplate='%{x}<br>mAP: %{y:.3f}<extra>lr=' + str(lr_val) + '</extra>',
        ))
    fig.update_layout(
        title='Learning Rate Effect on Final mAP',
        barmode='group',
        yaxis=dict(title='mAP @ IoU 0.5', range=[0, 0.6]),
        height=380,
    )
    return fig


# ── Chart 5: Epochs effect ────────────────────────────────────────────────────

def chart_epochs_effect():
    ep_best = defaultdict(dict)
    for r in HYPERPARAM_RUNS:
        ep    = r['epoches'] or 0
        model = r['display']
        if r['mAP_05'] > ep_best[model].get(ep, 0):
            ep_best[model][ep] = r['mAP_05']

    models = {m: eps for m, eps in ep_best.items() if len(eps) > 1}
    if not models:
        return None

    fig = go.Figure()
    for model, ep_map in sorted(models.items()):
        eps  = sorted(ep_map)
        maps = [ep_map[e] for e in eps]
        color = MODEL_COLORS.get(model, '#888')
        fig.add_trace(go.Scatter(
            x=eps, y=maps,
            mode='lines+markers+text',
            name=model.upper(),
            line=dict(color=color, width=2),
            marker=dict(size=8),
            text=[f'{v:.3f}' for v in maps],
            textposition='top center',
            hovertemplate='Epochs: %{x}<br>mAP: %{y:.3f}<extra>' + model.upper() + '</extra>',
        ))
    fig.update_layout(
        title='Training Duration Effect on Final mAP',
        xaxis_title='Epochs Trained',
        yaxis=dict(title='mAP @ IoU 0.5', range=[0, 0.55]),
        height=380,
    )
    return fig


# ── Chart 6: CAV count (V2X-ViT) ─────────────────────────────────────────────

def chart_cav_effect():
    cav_best = {}
    for r in HYPERPARAM_RUNS:
        if r['display'] == 'v2xvit' and r['max_cav'] is not None and r['mAP_05'] > 0.01:
            cav = r['max_cav']
            if r['mAP_05'] > cav_best.get(cav, 0):
                cav_best[cav] = r['mAP_05']
    if not cav_best:
        return None

    cavs = sorted(cav_best)
    vals = [cav_best[c] for c in cavs]
    fig = go.Figure(go.Bar(
        x=[str(c) for c in cavs],
        y=vals,
        marker_color=MODEL_COLORS['v2xvit'],
        text=[f'{v:.3f}' for v in vals],
        textposition='outside',
        hovertemplate='CAV=%{x}<br>mAP: %{y:.3f}<extra></extra>',
    ))
    fig.update_layout(
        title='V2X-ViT: CAV Count Effect on mAP',
        xaxis_title='Max Connected Vehicles',
        yaxis=dict(title='mAP @ IoU 0.5', range=[0, max(vals) * 1.3]),
        height=380,
    )
    return fig


# ── Main render ───────────────────────────────────────────────────────────────

def render_plotly_analysis():
    st.subheader('AP Overview')
    st.plotly_chart(chart_map_overview(), use_container_width=True)

    st.subheader('Per-Class AP')
    st.plotly_chart(chart_per_class(), use_container_width=True)

    st.subheader('Epoch mAP Curves')
    st.plotly_chart(chart_epoch_map(), use_container_width=True)
