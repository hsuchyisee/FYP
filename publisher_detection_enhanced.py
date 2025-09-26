"""
Enhanced Detection-Integrated Publisher

This extends your existing publisher_pykitti.py with real-time detection capabilities.
Supports both static KITTI labels and live detection models.

Features:
- Integrates with existing KITTI pose/calibration system
- Supports YOLO camera detection
- Supports LiDAR clustering detection  
- Maintains compatibility with fusion server
- Confidence-based filtering and fusion

Usage:
  # Use static KITTI labels (existing functionality)
  python publisher_detection_enhanced.py --basedir /path/to/KITTI --date 2011_09_26 --drive drive_0011_sync --frame 0
  
  # Add real-time camera detection
  python publisher_detection_enhanced.py --camera 0 --vehicle-id ego
  
  # Add LiDAR detection from KITTI
  python publisher_detection_enhanced.py --basedir /path/to/KITTI --date 2011_09_26 --drive drive_0011_sync --frame 0 --use-lidar-detection
"""

import argparse
import struct
import json
import socket
import time
import math
import numpy as np
import os
import cv2
from typing import List, Dict, Tuple, Optional

# Import existing modules
from dataset_kitti import load_detections

# Import detection modules (with fallbacks)
try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

try:
    import open3d as o3d
except ImportError:
    o3d = None

try:
    import pykitti
except ImportError:
    pykitti = None

HOST = '127.0.0.1'
PORT = 5001

# Vehicle classes from COCO/KITTI
VEHICLE_CLASSES = {
    2: 'car',  # COCO
    3: 'motorcycle',
    5: 'bus', 
    7: 'truck',
    'Car': 'car',  # KITTI
    'Van': 'van',
    'Truck': 'truck',
    'Pedestrian': 'pedestrian',
    'Cyclist': 'cyclist'
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
        return True
    except ConnectionRefusedError:
        print(f"[{vehicle_id}] Connection refused - is fusion server running?")
        return False
    except Exception as e:
        print(f"[{vehicle_id}] Send error: {e}")
        return False

class CameraDetector:
    """YOLO-based camera detection"""
    
    def __init__(self, model_path: str = 'yolov8n.pt'):
        self.model = YOLO(model_path) if YOLO else None
        self.detection_count = 0
        
    def detect_vehicles(self, frame: np.ndarray) -> List[Dict]:
        """Detect vehicles in camera frame"""
        if self.model is None:
            return []
            
        results = self.model(frame, verbose=False)
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
                
            for i, (box, conf, cls) in enumerate(zip(boxes.xyxy, boxes.conf, boxes.cls)):
                cls_id = int(cls.item())
                confidence = float(conf.item())
                
                # Filter for vehicles
                if cls_id not in VEHICLE_CLASSES or confidence < 0.3:
                    continue
                
                # Convert to world coordinates (simple approximation)
                x1, y1, x2, y2 = box.cpu().numpy()
                world_x, world_y = self._bbox_to_world(
                    (x1, y1, x2, y2), frame.shape[:2]
                )
                
                detection = {
                    'id': f"cam_det_{self.detection_count}_{i}",
                    'class': VEHICLE_CLASSES[cls_id],
                    'x': float(world_x),
                    'y': float(world_y),
                    'x_world': float(world_x),
                    'y_world': float(world_y), 
                    'confidence': confidence,
                    'detection_type': 'camera'
                }
                detections.append(detection)
        
        self.detection_count += 1
        return detections
    
    def _bbox_to_world(self, bbox: Tuple, image_shape: Tuple) -> Tuple[float, float]:
        """Simple bbox to world coordinate conversion"""
        x1, y1, x2, y2 = bbox
        img_h, img_w = image_shape
        
        center_x = (x1 + x2) / 2
        bottom_y = y2
        
        # Normalize and estimate distance
        norm_x = (center_x / img_w) * 2 - 1
        norm_y = (bottom_y / img_h) * 2 - 1
        
        # Simple distance estimation
        distance = max(5.0, 20.0 * (1.0 - norm_y))
        lateral = norm_x * distance * 0.3
        
        return lateral, distance

class LiDARDetector:
    """Simple LiDAR clustering detection"""
    
    def __init__(self):
        self.detection_count = 0
        
    def detect_vehicles(self, points: np.ndarray) -> List[Dict]:
        """Detect vehicles in LiDAR point cloud"""
        detections = []
        
        # Preprocess points
        filtered_points = self._filter_points(points)
        if len(filtered_points) < 100:
            return detections
            
        # Simple clustering (without Open3D dependency)
        clusters = self._simple_clustering(filtered_points)
        
        for i, cluster in enumerate(clusters):
            if len(cluster) < 20:
                continue
                
            center = np.mean(cluster, axis=0)
            dims = np.max(cluster, axis=0) - np.min(cluster, axis=0)
            
            # Simple vehicle classification
            vehicle_class, confidence = self._classify_cluster(dims)
            if confidence < 0.4:
                continue
                
            detection = {
                'id': f"lidar_det_{self.detection_count}_{i}",
                'class': vehicle_class,
                'x': float(center[0]),
                'y': float(center[1]),
                'x_world': float(center[0]),
                'y_world': float(center[1]),
                'confidence': confidence,
                'detection_type': 'lidar'
            }
            detections.append(detection)
            
        self.detection_count += 1
        return detections
    
    def _filter_points(self, points: np.ndarray) -> np.ndarray:
        """Filter points to region of interest"""
        mask = (
            (points[:, 0] > -40) & (points[:, 0] < 40) &
            (points[:, 1] > -40) & (points[:, 1] < 40) &
            (points[:, 2] > -2) & (points[:, 2] < 2)
        )
        return points[mask]
    
    def _simple_clustering(self, points: np.ndarray, eps: float = 1.0) -> List[np.ndarray]:
        """Simple distance-based clustering"""
        if len(points) == 0:
            return []
            
        clusters = []
        visited = np.zeros(len(points), dtype=bool)
        
        for i, point in enumerate(points):
            if visited[i]:
                continue
                
            # Find nearby points
            distances = np.linalg.norm(points - point, axis=1)
            nearby = distances < eps
            cluster_points = points[nearby]
            
            if len(cluster_points) > 20:
                clusters.append(cluster_points)
                visited[nearby] = True
                
        return clusters
    
    def _classify_cluster(self, dimensions: np.ndarray) -> Tuple[str, float]:
        """Classify cluster based on dimensions"""
        length, width, height = dimensions
        
        if 3.0 <= length <= 6.0 and 1.5 <= width <= 2.5:
            return "car", 0.8
        elif length > 6.0:
            return "truck", 0.7
        elif length < 3.0 and width < 1.5:
            return "motorcycle", 0.6
        else:
            return "vehicle", 0.5

class EnhancedDetectionPublisher:
    """Enhanced publisher with multiple detection modes"""
    
    def __init__(self, vehicle_id: str):
        self.vehicle_id = vehicle_id
        self.camera_detector = None
        self.lidar_detector = None
        
        # Initialize detectors
        if YOLO:
            self.camera_detector = CameraDetector()
            print(f"[{vehicle_id}] Camera detector initialized")
            
        self.lidar_detector = LiDARDetector()
        print(f"[{vehicle_id}] LiDAR detector initialized")
    
    def get_kitti_detections(self, kitti_root: str, frame_id: str) -> List[Dict]:
        """Get detections from KITTI labels (existing functionality)"""
        try:
            return load_detections(kitti_root, frame_id)
        except Exception as e:
            print(f"Failed to load KITTI labels: {e}")
            return []
    
    def get_camera_detections(self, camera_id: int = 0) -> List[Dict]:
        """Get real-time camera detections"""
        if self.camera_detector is None:
            print("Camera detector not available")
            return []
            
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"Failed to open camera {camera_id}")
            return []
            
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return []
            
        return self.camera_detector.detect_vehicles(frame)
    
    def get_lidar_detections(self, velodyne_path: str) -> List[Dict]:
        """Get LiDAR-based detections"""
        if not os.path.exists(velodyne_path):
            print(f"Velodyne file not found: {velodyne_path}")
            return []
            
        try:
            # Load KITTI velodyne format
            points = np.fromfile(velodyne_path, dtype=np.float32)
            points = points.reshape((-1, 4))[:, :3]  # Keep only XYZ
            
            return self.lidar_detector.detect_vehicles(points)
        except Exception as e:
            print(f"Failed to process LiDAR data: {e}")
            return []
    
    def fuse_detections(self, detection_lists: List[List[Dict]]) -> List[Dict]:
        """Fuse detections from multiple sources"""
        all_detections = []
        for det_list in detection_lists:
            all_detections.extend(det_list)
            
        if not all_detections:
            return []
            
        # Simple distance-based fusion
        fused = []
        distance_threshold = 2.0
        
        for det in all_detections:
            # Check if close to existing detection
            merged = False
            for fused_det in fused:
                dx = det['x'] - fused_det['x'] 
                dy = det['y'] - fused_det['y']
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < distance_threshold:
                    # Merge with higher confidence detection
                    if det['confidence'] > fused_det['confidence']:
                        fused_det.update(det)
                    merged = True
                    break
                    
            if not merged:
                fused.append(det)
                
        return fused

def run_enhanced_detection(args):
    """Main detection loop with multiple modes"""
    publisher = EnhancedDetectionPublisher(args.vehicle_id)
    
    # Mode 1: KITTI static labels with pose (existing functionality)
    if args.basedir and args.date and args.drive:
        print("Mode: KITTI static detection")
        
        if pykitti is None:
            print("pykitti not available")
            return
            
        # Setup KITTI dataset (adapted from publisher_pykitti.py)
        drive_arg = args.drive
        if args.date in drive_arg and 'drive' in drive_arg:
            drive_arg = drive_arg.split('drive_', 1)[-1]
        if drive_arg.endswith('_sync'):
            drive_arg = drive_arg[:-5]
            
        try:
            dataset = pykitti.raw(args.basedir, args.date, drive_arg)
            poses = [o.T_w_imu for o in dataset.oxts] if hasattr(dataset, 'oxts') else []
            
            if not poses:
                print("No poses found in dataset")
                return
                
            frame_idx = int(args.frame)
            vehicle_pose = poses[frame_idx]
            
            # Get detections
            detection_sources = []
            
            # Static KITTI labels
            kitti_dets = publisher.get_kitti_detections(args.basedir, f"{frame_idx:06d}")
            if kitti_dets:
                detection_sources.append(kitti_dets)
                print(f"Loaded {len(kitti_dets)} KITTI label detections")
            
            # Optional: LiDAR detection
            if args.use_lidar_detection:
                velodyne_path = os.path.join(
                    args.basedir, args.date, f"{args.date}_drive_{drive_arg}_sync",
                    "velodyne_points", "data", f"{frame_idx:010d}.bin"
                )
                lidar_dets = publisher.get_lidar_detections(velodyne_path)
                if lidar_dets:
                    detection_sources.append(lidar_dets)
                    print(f"Generated {len(lidar_dets)} LiDAR detections")
            
            # Fuse detections
            fused_detections = publisher.fuse_detections(detection_sources)
            
            # Send report
            if fused_detections:
                success = send_report(args.vehicle_id, fused_detections)
                if success:
                    print(f"Sent {len(fused_detections)} fused detections")
                    
        except Exception as e:
            print(f"KITTI detection error: {e}")
            
    # Mode 2: Real-time camera detection
    elif args.camera is not None:
        print(f"Mode: Real-time camera detection (device {args.camera})")
        
        try:
            while True:
                detections = publisher.get_camera_detections(args.camera)
                if detections:
                    success = send_report(args.vehicle_id, detections)
                    if success:
                        print(f"Sent {len(detections)} camera detections")
                        
                time.sleep(1.0)  # 1 FPS for demo
                
        except KeyboardInterrupt:
            print(f"\n[{args.vehicle_id}] Stopped camera detection")
            
    else:
        print("No detection mode specified. Use --basedir + --date + --drive or --camera")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Enhanced detection-integrated publisher')
    
    # KITTI static mode
    parser.add_argument('--basedir', help='KITTI base directory')
    parser.add_argument('--date', help='KITTI date directory')
    parser.add_argument('--drive', help='KITTI drive directory')
    parser.add_argument('--frame', default='0', help='Frame index')
    parser.add_argument('--use-lidar-detection', action='store_true', 
                       help='Add LiDAR detection to KITTI mode')
    
    # Real-time mode
    parser.add_argument('--camera', type=int, help='Camera device ID for real-time detection')
    
    # Common options
    parser.add_argument('--vehicle-id', default='ego', help='Vehicle ID for reports')
    
    args = parser.parse_args()
    
    run_enhanced_detection(args)
