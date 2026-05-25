"""
Stage 3 — model inference results: data layer.

Reads per-model AP / mAP from {dataset_root}/{scenario_id}/model_results.csv
(generated from inference.py runs). Feeds the model-comparison cards, the
recommendation card, and the CSV download button.

Uploaded / un-evaluated scenarios won't have this CSV — load_model_results()
returns {"available": False, ...} so Stage 3 can show a graceful fallback.

CSV layout (one row per model+variant):
    model,variant,<class>_AP@{0.3,0.5,0.7}...,mAP@0.3,mAP@0.5,mAP@0.7
  variants: raw / improved for the fusion models, baseline for nofusion.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml


CSV_NAME = "model_results.csv"


# ── Config-diff: detect tuned hyperparameters from real config.yaml files ──
class _TolerantLoader(yaml.SafeLoader):
    """SafeLoader that ignores embedded !!python/... tags (e.g. numpy blobs)
    in the opencood config files, so the rest of the YAML still parses."""


_TolerantLoader.add_multi_constructor(
    "tag:yaml.org,2002:python/", lambda loader, suffix, node: None
)

# Friendly labels for known config paths; unknown paths fall back to the dotted key.
PARAM_LABELS = {
    "optimizer.lr":            "Learning Rate",
    "optimizer.args.weight_decay": "Weight Decay",
    "lr_scheduler.step_size":  "LR Step Size",
    "lr_scheduler.gamma":      "LR Gamma",
    "train_params.epoches":    "Epochs",
    "train_params.batch_size": "Batch Size",
    "loss.args.cls_weight":    "Class Loss Weight",
    "loss.args.reg":           "Reg Loss Weight",
    "model.args.compression":  "Feature Compression",
    "postprocess.nms_thresh":  "NMS Threshold",
    "postprocess.target_args.score_threshold": "Score Threshold",
}

# Fusion models shown as comparison cards (display order). nofusion is a baseline.
CARD_MODELS    = ["early", "late", "intermediate"]
BASELINE_MODEL = "nofusion"
BEST_MODEL     = "intermediate"

MODEL_LABELS = {
    "early":        "Early Fusion",
    "late":         "Late Fusion",
    "intermediate": "Intermediate Fusion",
    "nofusion":     "No Fusion",
}

IOUS = [0.3, 0.5, 0.7]


def get_csv_path(dataset_root: str, scenario_id: str) -> Path:
    return Path(dataset_root) / scenario_id / CSV_NAME


def load_model_results(dataset_root: str, scenario_id: str) -> dict:
    """
    Returns a dict:
      {
        "available": bool,
        "reason":    str | None,
        "csv_path":  str | None,
        "models": {
            "early": {"label": str,
                      "raw":      {0.3: float, 0.5: float, 0.7: float},
                      "improved": {0.3: float, 0.5: float, 0.7: float}},
            ... late, intermediate ...
        },
        "baseline": {"label": str, "mAP": {0.3: float, 0.5: float, 0.7: float}} | None,
        "best_model": str,
      }
    """
    csv_path = get_csv_path(dataset_root, scenario_id)
    if not csv_path.exists():
        return {"available": False,
                "reason": f"No {CSV_NAME} for this scenario.",
                "csv_path": None, "models": {}, "baseline": None,
                "best_model": BEST_MODEL}

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        return {"available": False,
                "reason": f"Could not read {CSV_NAME}: {e}",
                "csv_path": None, "models": {}, "baseline": None,
                "best_model": BEST_MODEL}

    def _row(model: str, variant: str):
        sub = df[(df["model"] == model) & (df["variant"] == variant)]
        return sub.iloc[0] if len(sub) else None

    def _map(row) -> dict:
        out = {}
        for iou in IOUS:
            try:
                out[iou] = float(row[f"mAP@{iou}"])
            except (KeyError, ValueError, TypeError):
                out[iou] = 0.0
        return out

    models = {}
    for m in CARD_MODELS:
        r = _row(m, "raw")
        i = _row(m, "improved")
        if r is None or i is None:
            continue
        models[m] = {
            "label":    MODEL_LABELS.get(m, m.title()),
            "raw":      _map(r),
            "improved": _map(i),
        }

    if not models:
        return {"available": False,
                "reason": f"{CSV_NAME} has no usable model rows.",
                "csv_path": str(csv_path), "models": {}, "baseline": None,
                "best_model": BEST_MODEL}

    baseline = None
    br = _row(BASELINE_MODEL, "baseline")
    if br is not None:
        baseline = {"label": MODEL_LABELS.get(BASELINE_MODEL, "No Fusion"),
                    "mAP": _map(br)}

    return {
        "available":  True,
        "reason":     None,
        "csv_path":   str(csv_path),
        "models":     models,
        "baseline":   baseline,
        "best_model": BEST_MODEL,
    }


# ── Frame-by-frame comparison (Stage 3, after LiDAR video) ─────────
FRAME_COMPARISON_DIR = "frame_comparison"
FC_CSV               = "overall_metrics.csv"

# Display order: no cooperation → cooperation → cooperation + tuning.
# `key` matches both the CSV model column and the {key}.png image stem.
FRAME_COMPARISON_STAGES = [
    {"key": "nofusion",       "label": "No Fusion",                "sub": "single-agent baseline"},
    {"key": "inter_raw",      "label": "Intermediate · Raw",       "sub": "cooperative perception"},
    {"key": "inter_improved", "label": "Intermediate · Improved",  "sub": "cooperative + tuned"},
]

# Metric → higher-is-better? (False = lower is better, e.g. FP / FN)
FC_METRICS = [
    ("precision", "Precision", True),
    ("recall",    "Recall",    True),
    ("f1",        "F1",        True),
    ("tp",        "TP",        True),
    ("fp",        "FP",        False),
    ("fn",        "FN",        False),
]


def load_frame_comparison(dataset_root: str, scenario_id: str) -> dict:
    """
    Reads {scenario}/frame_comparison/overall_metrics.csv + the per-stage images
    ({key}.png in the same folder).

    Returns:
      {
        "available": bool,
        "reason":    str | None,
        "stages": [
            {"key": str, "label": str, "sub": str,
             "metrics": {"precision": float, "recall": float, "f1": float,
                         "tp": float, "fp": float, "fn": float},
             "image": str | None},   # absolute path if the png exists
            ...
        ],
      }
    """
    fc_dir   = Path(dataset_root) / scenario_id / FRAME_COMPARISON_DIR
    csv_path = fc_dir / FC_CSV

    if not csv_path.exists():
        return {"available": False,
                "reason": f"No {FRAME_COMPARISON_DIR}/{FC_CSV} for this scenario.",
                "stages": []}

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        return {"available": False,
                "reason": f"Could not read {FC_CSV}: {e}", "stages": []}

    rows = {str(r["model"]).strip(): r for _, r in df.iterrows()}

    stages = []
    for spec in FRAME_COMPARISON_STAGES:
        row = rows.get(spec["key"])
        if row is None:
            continue
        metrics = {}
        for col, _label, _hib in FC_METRICS:
            try:
                metrics[col] = float(row[col])
            except (KeyError, ValueError, TypeError):
                metrics[col] = 0.0
        img = fc_dir / f"{spec['key']}.png"
        stages.append({
            "key":     spec["key"],
            "label":   spec["label"],
            "sub":     spec["sub"],
            "metrics": metrics,
            "image":   str(img) if img.exists() else None,
        })

    if not stages:
        return {"available": False, "reason": f"{FC_CSV} has no matching model rows.",
                "csv_path": None, "stages": []}

    return {"available": True, "reason": None,
            "csv_path": str(csv_path), "stages": stages}


def _tolerant_load(path: Path):
    with open(path) as f:
        return yaml.load(f, Loader=_TolerantLoader)


def _flatten(d, prefix: str = "") -> dict:
    """Flatten a nested dict to {dotted.path: leaf_value}. Lists are leaves."""
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(_flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    else:
        out[prefix] = d
    return out


def load_config_diff(dataset_root: str, scenario_id: str, model_key: str) -> dict:
    """
    Detect tuned hyperparameters by diffing the real config.yaml files at
    {scenario}/{model_key}_raw/config.yaml vs {model_key}_improved/config.yaml.

    Returns:
      {"available": bool, "reason": str | None,
       "changes": [(label, raw_str, improved_str), ...]}   # file order preserved
    """
    base  = Path(dataset_root) / scenario_id
    raw_p = base / f"{model_key}_raw" / "config.yaml"
    imp_p = base / f"{model_key}_improved" / "config.yaml"

    if not raw_p.exists() or not imp_p.exists():
        return {"available": False,
                "reason": f"config.yaml missing for {model_key}_raw / {model_key}_improved.",
                "changes": []}

    try:
        raw = _flatten(_tolerant_load(raw_p))
        imp = _flatten(_tolerant_load(imp_p))
    except Exception as e:
        return {"available": False,
                "reason": f"Could not parse config.yaml: {e}", "changes": []}

    changes = []
    for key, rv in raw.items():
        if key in imp and imp[key] != rv:
            label = PARAM_LABELS.get(key, key)
            changes.append((label, str(rv), str(imp[key])))

    if not changes:
        return {"available": False,
                "reason": "No differences between raw and improved config.",
                "changes": []}

    return {"available": True, "reason": None, "changes": changes}
