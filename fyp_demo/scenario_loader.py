"""
Scenario zip-upload validation and extraction for the V2X-Real demo dashboard.

Expected zip layouts (any one is accepted):
  A. <scenario_id>/<agent>/000000.yaml   ← wrapped (preferred)
  B. <agent>/000000.yaml                 ← bare-agent layout (no wrapper)
  C. <anything>/.../<scenario_id>/<agent>/000000.yaml  ← nested fallback

Camera images (000000_camN.jpeg) are optional — stage 2 already handles
missing-image agents with a built-in placeholder caption.
"""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

import yaml


REQUIRED_FRAME_YAML = "000000.yaml"
MAX_ZIP_BYTES       = 500 * 1024 * 1024   # 500 MB safety cap


class ScenarioValidationError(Exception):
    """Raised when an uploaded scenario zip fails validation."""


def validate_and_extract_zip(uploaded_file) -> dict:
    """
    Validate an uploaded scenario zip and extract it to a fresh temp directory.

    Args:
        uploaded_file: a Streamlit UploadedFile (file-like with .name and .size)

    Returns:
        scenario dict matching the shape of SCENARIOS entries in stage1_v2.py,
        plus a `dataset_root` field pointing at the parent of the scenario folder.

    Raises:
        ScenarioValidationError with a human-readable message on any failure.
    """
    # ── Size check ─────────────────────────────────────────────────
    size = getattr(uploaded_file, "size", None)
    if size is not None and size > MAX_ZIP_BYTES:
        raise ScenarioValidationError(
            f"Zip too large ({size / 1e6:.1f} MB). "
            f"Max allowed: {MAX_ZIP_BYTES / 1e6:.0f} MB."
        )

    # ── Extract to fresh temp dir ──────────────────────────────────
    extract_root = Path(tempfile.mkdtemp(prefix="v2x_scenario_"))
    try:
        try:
            zf = zipfile.ZipFile(uploaded_file)
        except zipfile.BadZipFile:
            raise ScenarioValidationError("File is not a valid zip archive.")

        with zf:
            names = zf.namelist()
            if not names:
                raise ScenarioValidationError("Zip is empty.")
            # Reject paths that would write outside the extract dir
            for n in names:
                parts = Path(n).parts
                if Path(n).is_absolute() or ".." in parts:
                    raise ScenarioValidationError(f"Unsafe path in zip: {n}")
            zf.extractall(extract_root)
    except ScenarioValidationError:
        shutil.rmtree(extract_root, ignore_errors=True)
        raise

    # ── Detect scenario root ───────────────────────────────────────
    scenario_root = _detect_scenario_root(extract_root)
    if scenario_root is None:
        shutil.rmtree(extract_root, ignore_errors=True)
        raise ScenarioValidationError(
            "Could not find any agent subfolder containing '000000.yaml'. "
            "Expected layout: scenario_id/<agent_name>/000000.yaml"
        )

    # ── Validate each agent folder ─────────────────────────────────
    agent_dirs = sorted([d for d in scenario_root.iterdir() if d.is_dir()])
    valid_agents: list[str] = []
    cav_count = 0
    infra_count = 0
    yaml_errors: list[str] = []

    for agent_dir in agent_dirs:
        yaml_path = agent_dir / REQUIRED_FRAME_YAML
        if not yaml_path.exists():
            continue
        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
        except Exception as e:
            yaml_errors.append(f"{agent_dir.name}/{REQUIRED_FRAME_YAML}: {e}")
            continue
        if not isinstance(data, dict):
            yaml_errors.append(
                f"{agent_dir.name}/{REQUIRED_FRAME_YAML}: not a YAML mapping"
            )
            continue
        valid_agents.append(agent_dir.name)
        if data.get("infra", False):
            infra_count += 1
        else:
            cav_count += 1

    if not valid_agents:
        shutil.rmtree(extract_root, ignore_errors=True)
        msg = "No valid agent folders found (none have a parseable 000000.yaml)."
        if yaml_errors:
            msg += " Errors: " + "; ".join(yaml_errors[:3])
        raise ScenarioValidationError(msg)

    # ── Build scenario dict ────────────────────────────────────────
    scenario_id  = scenario_root.name
    dataset_root = str(scenario_root.parent)

    if cav_count and infra_count:
        scenario_type = "V2V + Infrastructure"
    elif infra_count:
        scenario_type = "Infrastructure only"
    else:
        scenario_type = "V2V only"

    return {
        "id":           scenario_id,
        "label":        f"Uploaded · {scenario_id}",
        "frames":       1,           # demo only loads frame 000000
        "agents":       len(valid_agents),
        "type":         scenario_type,
        "description":  (
            f"User-uploaded scenario · {cav_count} CAV(s), {infra_count} RSU(s) "
            f"at frame 000000."
        ),
        "dataset_root": dataset_root,
        "_uploaded":    True,
        "_extract_root": str(extract_root),   # for later cleanup
    }


def cleanup_extracted(scenario: dict) -> None:
    """Delete the temp dir created for a previously uploaded scenario, if any."""
    if not scenario:
        return
    root = scenario.get("_extract_root")
    if root:
        shutil.rmtree(root, ignore_errors=True)


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────

def _looks_like_scenario(p: Path) -> bool:
    """True if p has at least one agent subfolder containing 000000.yaml."""
    if not p.is_dir():
        return False
    for child in p.iterdir():
        if child.is_dir() and (child / REQUIRED_FRAME_YAML).exists():
            return True
    return False


def _detect_scenario_root(extract_root: Path) -> Optional[Path]:
    """Walk the extracted tree and find the scenario folder."""
    # Skip dotfiles / __MACOSX cruft
    def _visible(p: Path) -> bool:
        return not p.name.startswith(".") and p.name != "__MACOSX"

    top_entries = [p for p in extract_root.iterdir() if _visible(p)]

    # Case A: single top-level folder = scenario wrapper
    if len(top_entries) == 1 and top_entries[0].is_dir():
        if _looks_like_scenario(top_entries[0]):
            return top_entries[0]

    # Case B: bare agent folders at the root
    if _looks_like_scenario(extract_root):
        return extract_root

    # Case C: search deeper
    for p in extract_root.rglob("*"):
        if p.is_dir() and _visible(p) and _looks_like_scenario(p):
            return p

    return None
