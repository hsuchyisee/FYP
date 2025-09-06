import os

"""Minimal KITTI label loader.

Assumptions:
- KITTI root contains a folder like 'training/label_2' or 'label_2' with text files named 000000.txt, 000001.txt, ...
- Each label file uses the standard KITTI object detection format:
  class, truncation, occlusion, alpha, bbox_left, bbox_top, bbox_right, bbox_bottom,
  height, width, length, loc_x, loc_y, loc_z, rotation_y

This loader provides:
- list_frames(kitti_root) -> list of frame ids (zero-padded strings)
- load_detections(kitti_root, frame_id) -> list of {id, x, y, confidence, class}

The loader uses the 3D location (loc_x, loc_y, loc_z). For a simple BEV-like x/y we map
x := loc_x, y := loc_z (KITTI's z is forward). This is only for demo/fusion purposes.
"""


def _labels_dir(kitti_root):
    candidates = [
        os.path.join(kitti_root, 'training', 'label_2'),
        os.path.join(kitti_root, 'label_2'),
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c
    return None


def list_frames(kitti_root):
    labels_dir = _labels_dir(kitti_root)
    if labels_dir is None:
        return []
    files = [f for f in os.listdir(labels_dir) if f.endswith('.txt')]
    ids = sorted([os.path.splitext(f)[0] for f in files])
    return ids


def load_detections(kitti_root, frame_id):
    """Return list of detections for given frame_id.

    Each detection is a dict: {id, class, x, y, confidence}
    x,y are simple 2D coordinates derived from KITTI loc_x,loc_z.
    """
    labels_dir = _labels_dir(kitti_root)
    if labels_dir is None:
        raise FileNotFoundError(f"KITTI label directory not found under {kitti_root}")
    path = os.path.join(labels_dir, f"{frame_id}.txt")
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    dets = []
    with open(path, 'r') as fh:
        for i, line in enumerate(fh):
            parts = line.strip().split()
            if not parts:
                continue
            cls = parts[0]
            # KITTI label format: class, truncation, occlusion, alpha, bbox_l, bbox_t, bbox_r, bbox_b,
            # height, width, length, loc_x, loc_y, loc_z, rotation_y
            try:
                loc_x = float(parts[11])
                loc_y = float(parts[12])
                loc_z = float(parts[13])
            except Exception:
                # if format unexpected, skip
                continue
            # Map to simple 2D coords for demo: x := loc_x, y := loc_z
            x = loc_x
            y = loc_z
            dets.append({'id': f"{cls}_{i}", 'class': cls, 'x': x, 'y': y, 'confidence': 1.0})
    return dets
