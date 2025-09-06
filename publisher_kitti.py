"""Publisher that reads KITTI labels and sends them to the fusion server.

Usage examples:
  python publisher_kitti.py --kitti-root /path/to/KITTI --frame 000000 --vehicle-id ego
  python publisher_kitti.py --kitti-root /path/to/KITTI --frame 000010 --vehicle-id rsu

If KITTI root is missing or frame not found the script will exit with a helpful error.
"""
import argparse
import struct
import json
import socket
import time
import os

from dataset_kitti import list_frames, load_detections
import math

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


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--kitti-root', default='./kitti', help='Path to KITTI dataset root')
    p.add_argument('--frame', default=None, help='Frame id (zero padded) to send')
    p.add_argument('--vehicle-id', default='ego', help='Vehicle id string to include in report')
    p.add_argument('--send-rsu', action='store_true', help='Also synthesize and send an RSU report')
    p.add_argument('--rsu-offset', nargs=2, type=float, metavar=('DX','DY'), default=[-15.0, 0.0],
                   help='RSU offset (meters) relative to ego as DX DY (default: -15 0)')
    p.add_argument('--rsu-range', type=float, default=80.0, help='RSU max detection range in meters')
    p.add_argument('--rsu-fov', type=float, default=120.0, help='RSU horizontal field-of-view in degrees')
    p.add_argument('--rsu-confidence-scale', type=float, default=1.0, help='Scale RSU confidences by this factor')
    args = p.parse_args()

    kroot = args.kitti_root
    if not os.path.isdir(kroot):
        print(f"KITTI root not found: {kroot}")
        print("Please download KITTI labels and point the --kitti-root to the dataset folder.")
        raise SystemExit(1)

    frames = list_frames(kroot)
    if not frames:
        print(f"No KITTI label files found under {kroot}")
        raise SystemExit(1)

    frame = args.frame if args.frame is not None else frames[0]
    if frame not in frames:
        print(f"Frame {frame} not found. Available example frames: {frames[:5]}")
        raise SystemExit(1)

    dets = load_detections(kroot, frame)

    # send ego report (we treat detection x,y returned by loader as ground/BEV coords)
    send_report(args.vehicle_id, dets)

    # optionally synthesize RSU detections from the same data source
    if args.send_rsu:
        dx, dy = args.rsu_offset
        rsu_x = dx  # ego is assumed at origin (0,0) in this quick simulation
        rsu_y = dy
        maxr = args.rsu_range
        fov_rad = math.radians(args.rsu_fov)
        rsu_dets = []
        for det in dets:
            # det contains 'x' and 'y' from dataset_kitti mapping (x=loc_x, y=loc_z)
            x = det.get('x', 0.0)
            y = det.get('y', 0.0)
            # relative to RSU position
            rx = x - rsu_x
            ry = y - rsu_y
            # assume forward axis is +y (dataset mapped z->y); use bearing = atan2(rx, ry)
            dist = math.hypot(rx, ry)
            if dist > maxr:
                continue
            bearing = math.atan2(rx, ry)
            if abs(bearing) > fov_rad / 2.0:
                continue
            # visible -> copy detection but adjust confidence
            new_det = det.copy()
            new_det['confidence'] = float(new_det.get('confidence', 1.0)) * float(args.rsu_confidence_scale)
            rsu_dets.append(new_det)

        # use vehicle-id 'rsu' by default when sending synthesized RSU
        send_report('rsu', rsu_dets)
