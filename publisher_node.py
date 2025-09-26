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
        {'id': 'a', 'x': 5.0, 'y': 2.0, 'confidence': 0.7, 'class': 'car'},
        {'id': 'b', 'x': 8.0, 'y': -1.0, 'confidence': 0.6, 'class': 'car'}
    ]

    # RSU: covers further area and a blindspot behind ego
    rsu_dets = [
        {'id': 'b', 'x': 8.2, 'y': -1.1, 'confidence': 0.8, 'class': 'car'},
        {'id': 'c', 'x': 20.0, 'y': 0.5, 'confidence': 0.9, 'class': 'truck'}
    ]

    print("Starting synthetic publisher - sending detections continuously...")
    print("Press Ctrl+C to stop")
    
    try:
        frame_count = 0
        while True:
            # Add some variation to positions to simulate movement
            varied_ego_dets = []
            for det in ego_dets:
                varied_det = det.copy()
                varied_det['x'] += random.uniform(-0.5, 0.5)
                varied_det['y'] += random.uniform(-0.2, 0.2)
                varied_det['id'] = f"{det['id']}_{frame_count}"
                varied_ego_dets.append(varied_det)
                
            varied_rsu_dets = []
            for det in rsu_dets:
                varied_det = det.copy()
                varied_det['x'] += random.uniform(-0.3, 0.3)
                varied_det['y'] += random.uniform(-0.1, 0.1)
                varied_det['id'] = f"{det['id']}_{frame_count}"
                varied_rsu_dets.append(varied_det)

            # Send reports
            try:
                send_report('ego', varied_ego_dets)
                time.sleep(0.1)
                send_report('rsu', varied_rsu_dets)
                
                frame_count += 1
                print(f"Sent frame {frame_count} with {len(varied_ego_dets)} ego + {len(varied_rsu_dets)} RSU detections")
                
            except ConnectionRefusedError:
                print("Connection refused - is fusion server running?")
                time.sleep(2)  # Wait before retrying
                continue
            except Exception as e:
                print(f"Error sending detections: {e}")
                time.sleep(1)
                continue
                
            time.sleep(2.0)  # Send every 2 seconds
            
    except KeyboardInterrupt:
        print("\nSynthetic publisher stopped")

        # You can run multiple instances with different synthetic detections or delays

