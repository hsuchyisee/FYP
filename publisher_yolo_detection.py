"""
Real-time YOLO-based Vehicle Detection Publisher

This publisher integrates YOLOv8 for real-time vehicle detection from camera feeds.
It sends detection reports to the cooperative perception fusion server.

Features:
- Real-time camera-based vehicle detection
- Confidence filtering and NMS
- World coordinate transformation 
- Compatible with existing fusion server

Usage:
  python publisher_yolo_detection.py --camera 0 --vehicle-id ego
  python publisher_yolo_detection.py --video path/to/video.mp4 --vehicle-id rsu
"""

import argparse
import struct
import json
import socket
import time
import cv2
import numpy as np
from typing import List, Dict, Tuple

try:
    from ultralytics import YOLO
except ImportError:
    print("Please install ultralytics: pip install ultralytics")
    YOLO = None

HOST = '127.0.0.1'
PORT = 5001

# Vehicle classes from COCO dataset (YOLO default)
VEHICLE_CLASSES = {
    2: 'car',
    3: 'motorcycle', 
    5: 'bus',
    7: 'truck'
}

def send_report(vehicle_id: str, detections: List[Dict]):
    """Send detection report to fusion server"""
    msg = {
        'vehicle_id': vehicle_id,
        'timestamp': time.time(),
        'detections': detections
    }
    data = json.dumps(msg).encode('utf-8')
    length = struct.pack('>Q', len(data))
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(length + data)
        print(f"[{vehicle_id}] Sent {len(detections)} detections")
    except ConnectionRefusedError:
        print(f"[{vehicle_id}] Connection refused - is fusion server running?")
    except Exception as e:
        print(f"[{vehicle_id}] Send error: {e}")

def bbox_to_world_coords(bbox: Tuple[float, float, float, float], 
                        image_shape: Tuple[int, int],
                        camera_height: float = 1.5,
                        camera_pitch: float = 0.0) -> Tuple[float, float]:
    """
    Convert 2D bounding box to approximate world coordinates.
    
    Simple approximation assuming:
    - Camera mounted at camera_height meters
    - Flat ground plane
    - Objects at ground level
    
    Args:
        bbox: (x1, y1, x2, y2) in pixel coordinates
        image_shape: (height, width) of image
        camera_height: Height of camera above ground (meters)
        camera_pitch: Camera pitch angle (radians, positive = tilted down)
    
    Returns:
        (x_world, y_world) in meters relative to ego vehicle
    """
    x1, y1, x2, y2 = bbox
    img_h, img_w = image_shape
    
    # Use bottom center of bounding box (contact point with ground)
    center_x = (x1 + x2) / 2
    bottom_y = y2
    
    # Normalize to [-1, 1] coordinates
    norm_x = (center_x / img_w) * 2 - 1
    norm_y = (bottom_y / img_h) * 2 - 1
    
    # Simple perspective projection (assumes known camera parameters)
    # This is a rough approximation - for accurate results use camera calibration
    focal_length_pixels = img_w  # rough approximation
    
    # Ground plane intersection
    if norm_y > 0:  # Object appears below horizon
        # Distance to object on ground plane
        distance = camera_height / (norm_y * (camera_height / focal_length_pixels) + camera_pitch)
        distance = max(1.0, min(distance, 100.0))  # Clamp to reasonable range
        
        # Lateral offset
        lateral_offset = norm_x * distance * 0.5  # rough approximation
        
        return lateral_offset, distance
    else:
        # Object above horizon - use default distance
        return norm_x * 10, 20.0

class YOLODetectionPublisher:
    def __init__(self, vehicle_id: str, model_path: str = 'yolov8n.pt'):
        self.vehicle_id = vehicle_id
        self.model = YOLO(model_path) if YOLO else None
        self.detection_count = 0
        
    def process_frame(self, frame: np.ndarray, send_detections: bool = True) -> List[Dict]:
        """Process single frame and return detections"""
        if self.model is None:
            return []
            
        # Run YOLO inference
        results = self.model(frame, verbose=False)
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
                
            for i, (box, conf, cls) in enumerate(zip(boxes.xyxy, boxes.conf, boxes.cls)):
                cls_id = int(cls.item())
                confidence = float(conf.item())
                
                # Filter for vehicles only
                if cls_id not in VEHICLE_CLASSES:
                    continue
                    
                # Confidence threshold
                if confidence < 0.3:
                    continue
                
                # Convert bbox to world coordinates
                x1, y1, x2, y2 = box.cpu().numpy()
                world_x, world_y = bbox_to_world_coords(
                    (x1, y1, x2, y2), frame.shape[:2]
                )
                
                detection = {
                    'id': f"{self.vehicle_id}_det_{self.detection_count}_{i}",
                    'class': VEHICLE_CLASSES[cls_id],
                    'x': float(world_x),
                    'y': float(world_y), 
                    'x_world': float(world_x),
                    'y_world': float(world_y),
                    'confidence': confidence,
                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                    'detection_type': 'camera_yolo'
                }
                detections.append(detection)
        
        self.detection_count += 1
        
        if send_detections and detections:
            send_report(self.vehicle_id, detections)
            
        return detections

def run_camera_detection(camera_id: int, vehicle_id: str, display: bool = False):
    """Run real-time detection on camera feed"""
    if YOLO is None:
        print("YOLO not available - install ultralytics")
        return
        
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"Failed to open camera {camera_id}")
        return
        
    detector = YOLODetectionPublisher(vehicle_id)
    print(f"[{vehicle_id}] Starting camera detection on device {camera_id}")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame")
                break
                
            # Process frame
            detections = detector.process_frame(frame)
            
            # Display frame with detections
            if display:
                display_frame = frame.copy()
                for det in detections:
                    bbox = det['bbox']
                    x1, y1, x2, y2 = map(int, bbox)
                    label = f"{det['class']}: {det['confidence']:.2f}"
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(display_frame, label, (x1, y1-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                cv2.imshow(f'{vehicle_id} Detection', display_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
            time.sleep(0.1)  # ~10 FPS
            
    except KeyboardInterrupt:
        print(f"\n[{vehicle_id}] Detection stopped")
    finally:
        cap.release()
        cv2.destroyAllWindows()

def run_video_detection(video_path: str, vehicle_id: str, display: bool = False):
    """Run detection on video file"""
    if YOLO is None:
        print("YOLO not available - install ultralytics")
        return
        
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Failed to open video {video_path}")
        return
        
    detector = YOLODetectionPublisher(vehicle_id)
    print(f"[{vehicle_id}] Starting video detection on {video_path}")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("End of video")
                break
                
            detections = detector.process_frame(frame)
            
            if display:
                display_frame = frame.copy()
                for det in detections:
                    bbox = det['bbox']
                    x1, y1, x2, y2 = map(int, bbox)
                    label = f"{det['class']}: {det['confidence']:.2f}"
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(display_frame, label, (x1, y1-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                cv2.imshow(f'{vehicle_id} Detection', display_frame)
                if cv2.waitKey(30) & 0xFF == ord('q'):
                    break
                    
    except KeyboardInterrupt:
        print(f"\n[{vehicle_id}] Detection stopped")
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='YOLO-based vehicle detection publisher')
    parser.add_argument('--camera', type=int, help='Camera device ID (e.g., 0)')
    parser.add_argument('--video', type=str, help='Path to video file')
    parser.add_argument('--vehicle-id', default='ego', help='Vehicle ID for reports')
    parser.add_argument('--display', action='store_true', help='Show detection visualization')
    parser.add_argument('--model', default='yolov8n.pt', help='YOLO model path')
    
    args = parser.parse_args()
    
    if args.camera is not None:
        run_camera_detection(args.camera, args.vehicle_id, args.display)
    elif args.video:
        run_video_detection(args.video, args.vehicle_id, args.display)
    else:
        print("Specify either --camera <id> or --video <path>")
