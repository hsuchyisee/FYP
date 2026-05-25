"""
Stage 4 — Channel Noise Robustness: data layer.

Loads the per-SNR detection metrics + feature/BEV images produced by the
noise-simulation sweep on the best model (intermediate fusion), and computes a
3-state robustness label anchored to the single-agent (ego-only) baseline.

Files expected under {dataset_root}/{scenario_id}/noise/:
    ap_vs_snr_{MODEL}_{NOISE_TYPE}.csv
    {MODEL}_feat_{suffix}.png   for suffix in clean / p30dB / p20dB / p10dB / p0dB
    {MODEL}_bev_{suffix}.png    "

Uploaded custom scenarios won't have a noise/ folder — load_noise_data()
returns {"available": False, "reason": ...} so the UI can show a graceful
fallback instead of erroring.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


MODEL      = "intermediate"        # best model used for the noise sweep
NOISE_TYPE = "rayleigh_awgn"

# Ordered SNR levels shown on the slider: clean → most noise.
# Maps each slider step to its CSV row label and image filename suffix.
SNR_LEVELS = [
    {"key": "clean", "slider_label": "Clean",  "csv_label": "∞ (clean)", "img_suffix": "clean"},
    {"key": "p30dB", "slider_label": "+30 dB", "csv_label": "+30.0 dB",  "img_suffix": "p30dB"},
    {"key": "p20dB", "slider_label": "+20 dB", "csv_label": "+20.0 dB",  "img_suffix": "p20dB"},
    {"key": "p10dB", "slider_label": "+10 dB", "csv_label": "+10.0 dB",  "img_suffix": "p10dB"},
    {"key": "p0dB",  "slider_label": "0 dB",   "csv_label": "+0.0 dB",   "img_suffix": "p0dB"},
]

EGO_ONLY_LABEL = "ego only"

# ── 3-state robustness label (anchored to the ego-only baseline) ───
STATUS_BENEFICIAL     = "beneficial"        # mAP >= single-agent baseline
STATUS_BELOW_BASELINE = "below_baseline"    # 0 < mAP < single-agent baseline
STATUS_COLLAPSE       = "collapse"          # mAP ~ 0 (no usable detections)

# mAP@0.5 below this is treated as "no usable detections" (collapse).
# 1% mAP — effectively nothing detected. The one soft cutoff; the other two
# states are anchored to the real ego-only boundary.
COLLAPSE_MAP_THRESHOLD = 0.01


def get_noise_dir(dataset_root: str, scenario_id: str) -> Path:
    return Path(dataset_root) / scenario_id / "noise"


def _csv_path(noise_dir: Path) -> Path:
    return noise_dir / f"ap_vs_snr_{MODEL}_{NOISE_TYPE}.csv"


def compute_status(map05: float, ego_only_map05: float | None) -> str:
    """3-state robustness label anchored to the ego-only baseline."""
    if map05 < COLLAPSE_MAP_THRESHOLD:
        return STATUS_COLLAPSE
    if ego_only_map05 is not None and map05 >= ego_only_map05:
        return STATUS_BENEFICIAL
    return STATUS_BELOW_BASELINE


def load_noise_data(dataset_root: str, scenario_id: str) -> dict:
    """
    Load Stage 4 noise-robustness data for a scenario.

    Returns a dict:
      {
        "available":      bool,
        "reason":         str | None,        # why unavailable, if applicable
        "model":          str,
        "noise_type":     str,
        "ego_only_map05": float | None,      # single-agent baseline (mAP@0.5)
        "levels": [
           {
             "key":          str,            # clean / p30dB / ...
             "slider_label": str,            # "Clean" / "+30 dB" / ...
             "csv_label":    str,
             "snr_db":       float,
             "mAP":          {0.3: float, 0.5: float, 0.7: float},
             "feat_img":     str | None,     # absolute path if the file exists
             "bev_img":      str | None,
             "status":       str,            # beneficial / below_baseline / collapse
           }, ...
        ],
      }
    """
    noise_dir = get_noise_dir(dataset_root, scenario_id)
    if not noise_dir.is_dir():
        return {"available": False,
                "reason": "No 'noise/' folder for this scenario.",
                "levels": []}

    csv_path = _csv_path(noise_dir)
    if not csv_path.exists():
        return {"available": False,
                "reason": f"Missing metrics CSV: {csv_path.name}",
                "levels": []}

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        return {"available": False,
                "reason": f"Could not read metrics CSV: {e}",
                "levels": []}

    # Index rows by their snr_label for lookup
    rows = {str(r["snr_label"]).strip(): r for _, r in df.iterrows()}

    def _cell(row, col) -> float:
        try:
            return float(row[col])
        except (KeyError, ValueError, TypeError):
            return 0.0

    # Single-agent baseline (mAP@0.5) — used as the status threshold
    ego_only_map05 = None
    if EGO_ONLY_LABEL in rows:
        val = _cell(rows[EGO_ONLY_LABEL], "mAP_AP@0.5")
        ego_only_map05 = val if val > 0 else None

    levels = []
    for lvl in SNR_LEVELS:
        row = rows.get(lvl["csv_label"])
        if row is None:
            continue   # CSV missing this SNR row — skip, keep the rest

        map_vals = {
            0.3: _cell(row, "mAP_AP@0.3"),
            0.5: _cell(row, "mAP_AP@0.5"),
            0.7: _cell(row, "mAP_AP@0.7"),
        }

        feat = noise_dir / f"{MODEL}_feat_{lvl['img_suffix']}.png"
        bev  = noise_dir / f"{MODEL}_bev_{lvl['img_suffix']}.png"

        levels.append({
            "key":          lvl["key"],
            "slider_label": lvl["slider_label"],
            "csv_label":    lvl["csv_label"],
            "snr_db":       _cell(row, "snr_db"),
            "mAP":          map_vals,
            "feat_img":     str(feat) if feat.exists() else None,
            "bev_img":      str(bev) if bev.exists() else None,
            "status":       compute_status(map_vals[0.5], ego_only_map05),
        })

    if not levels:
        return {"available": False,
                "reason": "Metrics CSV has no matching SNR rows.",
                "levels": []}

    return {
        "available":      True,
        "reason":         None,
        "model":          MODEL,
        "noise_type":     NOISE_TYPE,
        "ego_only_map05": ego_only_map05,
        "levels":         levels,
    }
