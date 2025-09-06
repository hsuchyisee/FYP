"""PKITTI-based publisher (quick pose-mode)

This script uses pykitti to read vehicle poses for a drive and then sends
KITTI detections (from dataset_kitti) transformed into world coordinates
using the vehicle pose. It then synthesizes an RSU at an offset relative
to the ego vehicle (offset expressed in ego vehicle frame by default)
and sends both ego and RSU detection reports to the fusion server.

Note: This is a practical, approximate implementation that maps KITTI
label loc_x/loc_z into world coordinates by translating by the vehicle
pose. For more exact transforms use camera-to-vehicle calibration (Tr)
and apply full camera->vehicle->world chains.

Usage:
  python publisher_pykitti.py --basedir /path/to/KITTI --date 2011_09_26 \
      --drive 2011_09_26_drive_0011_sync --frame 000000 --vehicle-id ego --send-rsu

Requires: pykitti (pip install pykitti)
"""
import argparse
import struct
import json
import socket
import time
import math
import numpy as np
import os

try:
    import pykitti
except Exception as e:
    pykitti = None

from dataset_kitti import load_detections

HOST = '127.0.0.1'
PORT = 5001


def send_report(vehicle_id, detections):
    msg = {
        'vehicle_id': vehicle_id,
        'timestamp': time.time(),
        'detections': detections
    }
    data = json.dumps(msg).encode('utf-8')
    length = struct.pack('>Q', len(data))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(length + data)
    print(f"[pub:{vehicle_id}] Sent {len(data)} bytes with {len(detections)} detections")


def yaw_from_rot(R):
    # Extract yaw (around up axis) from 3x3 rotation matrix. This is a simple
    # method assuming conventional vehicle axes; it's approximate but ok for demo.
    # yaw = atan2(R[1,0], R[0,0])
    return math.atan2(R[1,0], R[0,0])


def build_world_points(dets, vehicle_pose):
    """Map detection local coords into world coordinates using vehicle_pose.
    vehicle_pose is a 4x4 matrix (vehicle -> world).
    We assume det['x'] = loc_x (camera right), det['y'] = loc_z (camera forward),
    and produce world positions by translating by vehicle position and (optionally)
    rotating by vehicle orientation. This is a simplified mapping for a quick test.
    """
    world_pts = []
    R = vehicle_pose[:3,:3]
    t = vehicle_pose[:3,3]
    for d in dets:
        local_x = float(d.get('x', 0.0))
        local_y = float(d.get('y', 0.0))
        # local in vehicle frame approx: forward = local_y, right = local_x
        # assemble vector in vehicle coords (x_right, y_up, z_forward)
        p_vehicle = np.array([local_x, 0.0, local_y])
        p_world = R @ p_vehicle + t
        world_pts.append((p_world, d))
    return world_pts


def simulate_rsu_from_world(world_pts, rsu_world_pose, max_range=80.0, fov_deg=120.0, conf_scale=1.0):
    inv = np.linalg.inv(rsu_world_pose)
    fov_rad = math.radians(fov_deg)
    out = []
    for idx, (wp, det) in enumerate(world_pts):
        p_world_h = np.array([wp[0], wp[1], wp[2], 1.0])
        p_local = inv @ p_world_h
        lx, ly, lz = p_local[0], p_local[1], p_local[2]
        # require forward (lz) > 0
        if lz <= 0:
            continue
        dist = math.hypot(lx, lz)
        if dist > max_range:
            continue
        bearing = math.atan2(lx, lz)
        if abs(bearing) > fov_rad/2.0:
            continue
        new_det = det.copy()
        new_det['confidence'] = float(new_det.get('confidence', 1.0)) * conf_scale
        # use world XY for fusion convenience
        new_det['x_world'] = float(wp[0])
        new_det['y_world'] = float(wp[2])
        out.append(new_det)
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--basedir', required=True, help='KITTI base directory (e.g. /data/KITTI)')
    p.add_argument('--date', required=True, help='date directory, e.g. 2011_09_26')
    p.add_argument('--drive', required=True, help='drive folder name, e.g. 2011_09_26_drive_0011_sync')
    p.add_argument('--frame', default='000000', help='frame id (zero padded) to send')
    p.add_argument('--vehicle-id', default='ego', help='vehicle id for ego report')
    p.add_argument('--send-rsu', action='store_true', help='also synthesize RSU report')
    p.add_argument('--rsu-offset', nargs=2, type=float, default=[-15.0, 0.0],
                   help='RSU offset (dx dy) in ego VEHICLE frame (meters)')
    p.add_argument('--rsu-range', type=float, default=80.0)
    p.add_argument('--rsu-fov', type=float, default=120.0)
    p.add_argument('--rsu-confidence-scale', type=float, default=1.0)
    args = p.parse_args()

    if pykitti is None:
        print('pykitti is not installed. Install with `pip install pykitti`')
        raise SystemExit(1)

    # Help users who accidentally pass the full folder name as --drive
    # pykitti.raw expects the shorter drive id (e.g. '0011') because it
    # constructs the full folder name as <date>_drive_<drive>_<dataset>.
    drive_arg = args.drive
    # If user passed something like '2011_09_26_drive_0011_sync', extract
    # the part after 'drive_' so we don't duplicate the date string.
    if args.date in drive_arg and 'drive' in drive_arg:
        # split on 'drive_' and take the remainder
        drive_arg = drive_arg.split('drive_', 1)[-1]
    # strip a trailing dataset suffix if provided (e.g. '_sync')
    if drive_arg.endswith('_' + 'sync'):
        drive_arg = drive_arg[: -len('_' + 'sync')]

    resolved_drive_folder = f"{args.date}_drive_{drive_arg}_sync"
    resolved_data_path = os.path.join(args.basedir, args.date, resolved_drive_folder)
    print(f"pykitti: resolved data_path = {resolved_data_path}")

    dataset = pykitti.raw(args.basedir, args.date, drive_arg)
    # load poses (list of 4x4 numpy arrays)
    # Newer pykitti versions populate `dataset.oxts` (list of OxtsData(packet, T_w_imu)).
    poses = None
    if hasattr(dataset, 'oxts') and dataset.oxts:
        poses = [o.T_w_imu for o in dataset.oxts]
    else:
        # Some older variants may provide `poses`; try that as a fallback
        poses = getattr(dataset, 'poses', None)

    if not poses:
        print('No poses found in dataset. Ensure OXTS/odometry files are present under the drive (oxts/data/*.txt) or use a dataset with poses.')
        raise SystemExit(1)

    # map frame id string to index (simple cast)
    idx = int(args.frame)
    if idx < 0 or idx >= len(poses):
        print(f'frame index {idx} out of range (0..{len(poses)-1})')
        raise SystemExit(1)

    vehicle_pose = poses[idx]

    # load detections from dataset_kitti (assumes labels exist in expected tree)
    # Reuse previous loader which maps loc_x->x, loc_z->y for BEV
    # We expect det['x'], det['y'] in local camera coordinates (approx vehicle local)
    # The publisher_kitti loader expects labels under a label_2 folder; here we build a path
    # that points to the same drive's label folder if available; otherwise, user can point
    # the loader at a separate labels folder.
    # We try to find label file in args.basedir/<date>_<drive>/label_2 or common locations.

    # For simplicity, expect a labels folder at args.basedir/label_2 or args.basedir/training/label_2
    # If your labels are elsewhere, run publisher_kitti.py directly with --kitti-root.
    labels_root_guess = args.basedir
    # attempt typical raw layout
    labels_dir_candidates = [
        f"{args.basedir}/{args.date}/{args.drive}/label_2",
        f"{args.basedir}/{args.date}/{args.drive}/data/label_2",
        f"{args.basedir}/training/label_2",
        f"{args.basedir}/label_2",
    ]
    kroot = None
    for c in labels_dir_candidates:
        if os.path.isdir(c):
            kroot = os.path.dirname(c) if c.endswith('/label_2') else c
            # if we found label dir, set kroot to parent so dataset_kitti._labels_dir finds it
            kroot = os.path.dirname(c)
            break
    if kroot is None:
        print('Could not locate label_2 folder automatically. Please provide labels with publisher_kitti instead.')
        raise SystemExit(1)

    frame_id = f"{idx:06d}"
    dets = load_detections(kroot, frame_id)

    # build world points
    world_pts = build_world_points(dets, vehicle_pose)

    # prepare ego report (attach world coords)
    ego_report = []
    for wp, det in world_pts:
        rec = det.copy()
        rec['x_world'] = float(wp[0])
        rec['y_world'] = float(wp[2])
        ego_report.append(rec)

    send_report(args.vehicle_id, ego_report)

    if args.send_rsu:
        dx, dy = args.rsu_offset
        # build RSU world pose by applying offset in ego VEHICLE frame
        # rotation = vehicle_pose[:3,:3]; translation = vehicle_pose[:3,3]
        R = vehicle_pose[:3,:3]
        t = vehicle_pose[:3,3]
        # offset expressed in vehicle coordinates (right, up, forward) -> here we use (dx right, 0, dy forward)
        off_vehicle = np.array([dx, 0.0, dy])
        off_world = R @ off_vehicle
        rsu_pose = vehicle_pose.copy()
        rsu_pose[:3,3] = t + off_world

        rsu_dets = simulate_rsu_from_world(world_pts, rsu_pose, max_range=args.rsu_range,
                                           fov_deg=args.rsu_fov, conf_scale=args.rsu_confidence_scale)
        send_report('rsu', rsu_dets)

    print('done')
