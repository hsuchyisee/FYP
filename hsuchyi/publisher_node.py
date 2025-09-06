import socket
import struct
import json
import time
import random

HOST = '127.0.0.1'
PORT = 5001

# Publisher that can act as ego vehicle or RSU (roadside unit)
# Sends a JSON message with metadata and a list of detections.


def send_report(vehicle_id, detections, delay=0.0):
    msg = {
        'vehicle_id': vehicle_id,
        'timestamp': time.time(),
        'detections': detections
    }
    data = json.dumps(msg).encode('utf-8')
    length = struct.pack('>Q', len(data))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        if delay:
            time.sleep(delay)
        s.sendall(length + data)
    print(f"[pub:{vehicle_id}] Sent {len(data)} bytes")


if __name__ == '__main__':
    # Example usage: create 2 publishers (ego and RSU)
    # Ego: sees only close objects
    ego_dets = [
        {'id': 'a', 'x': 5.0, 'y': 2.0, 'confidence': 0.7},
        {'id': 'b', 'x': 8.0, 'y': -1.0, 'confidence': 0.6}
    ]

    # RSU: covers further area and a blindspot behind ego
    rsu_dets = [
        {'id': 'b', 'x': 8.2, 'y': -1.1, 'confidence': 0.8},
        {'id': 'c', 'x': 20.0, 'y': 0.5, 'confidence': 0.9}
    ]

    # send ego report
    send_report('ego', ego_dets)
    time.sleep(0.1)
    # send RSU report
    send_report('rsu', rsu_dets)

        # You can run multiple instances with different synthetic detections or delays

