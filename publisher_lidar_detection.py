"""
LiDAR-based Vehicle Detection Publisher

This publisher processes LiDAR point clouds for 3D vehicle detection.
Uses simple clustering and geometric features for vehicle detection.

For more advanced detection, integrate with:
- PointPillars
- PointNet++  
- OpenPCDet

Usage:
  python publisher_lidar_detection.py --lidar-data /path/to/lidar --vehicle-id ego
  python publisher_lidar_detection.py --kitti-velodyne /path/to/kitti --frame 000000
"""

import argparse
import struct
import json
import socket
import time
import numpy as np
import os
from typing import List, Dict, Tuple, Optional

try:
    import open3d as o3d
except ImportError:
    print("Please install Open3D: pip install open3d")
    o3d = None

HOST = '127.0.0.1'
PORT = 5001

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

def load_kitti_velodyne(velodyne_path: str) -> np.ndarray:
    """Load KITTI velodyne point cloud"""
    if not os.path.exists(velodyne_path):
        raise FileNotFoundError(f"Velodyne file not found: {velodyne_path}")
    
    points = np.fromfile(velodyne_path, dtype=np.float32)
    points = points.reshape((-1, 4))  # [x, y, z, intensity]
    return points[:, :3]  # Return only XYZ

def preprocess_point_cloud(points: np.ndarray, 
                          x_range: Tuple[float, float] = (-40, 40),
                          y_range: Tuple[float, float] = (-40, 40), 
                          z_range: Tuple[float, float] = (-3, 1)) -> np.ndarray:
    """Filter point cloud to region of interest"""
    mask = (
        (points[:, 0] >= x_range[0]) & (points[:, 0] <= x_range[1]) &
        (points[:, 1] >= y_range[0]) & (points[:, 1] <= y_range[1]) &
        (points[:, 2] >= z_range[0]) & (points[:, 2] <= z_range[1])
    )
    return points[mask]

def ground_removal(points: np.ndarray, threshold: float = 0.2) -> np.ndarray:
    """Simple ground removal using height threshold"""
    if o3d is None:
        # Simple height-based filtering
        return points[points[:, 2] > threshold]
    
    # Use Open3D for more sophisticated ground removal
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    
    # RANSAC plane fitting for ground removal
    plane_model, inliers = pcd.segment_plane(distance_threshold=0.2,
                                           ransac_n=3,
                                           num_iterations=1000)
    
    # Keep points not on the ground plane
    non_ground_pcd = pcd.select_by_index(inliers, invert=True)
    return np.asarray(non_ground_pcd.points)

def euclidean_clustering(points: np.ndarray, 
                        eps: float = 0.5, 
                        min_points: int = 10) -> List[np.ndarray]:
    """Cluster points using Euclidean clustering"""
    if o3d is None:
        # Simple clustering fallback
        return [points]  # Return all points as one cluster
    
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    
    # DBSCAN clustering
    labels = np.array(pcd.cluster_dbscan(eps=eps, min_points=min_points))
    
    clusters = []
    for cluster_id in np.unique(labels):
        if cluster_id == -1:  # Noise points
            continue
        cluster_mask = labels == cluster_id
        cluster_points = points[cluster_mask]
        if len(cluster_points) >= min_points:
            clusters.append(cluster_points)
    
    return clusters

def classify_cluster(cluster: np.ndarray) -> Tuple[str, float]:
    """
    Simple vehicle classification based on cluster geometry.
    Returns (class_name, confidence)
    """
    if len(cluster) < 10:
        return "unknown", 0.1
    
    # Calculate bounding box dimensions
    min_coords = np.min(cluster, axis=0)
    max_coords = np.max(cluster, axis=0)
    dimensions = max_coords - min_coords
    
    length, width, height = dimensions[0], dimensions[1], dimensions[2]
    
    # Simple heuristic classification
    if 3.0 <= length <= 6.0 and 1.5 <= width <= 2.5 and 1.0 <= height <= 2.0:
        return "car", 0.8
    elif length > 6.0 and width > 2.0 and height > 2.0:
        return "truck", 0.7
    elif 2.0 <= length <= 4.0 and 0.5 <= width <= 1.5:
        return "motorcycle", 0.6
    else:
        return "vehicle", 0.5

class LiDARDetectionPublisher:
    def __init__(self, vehicle_id: str):
        self.vehicle_id = vehicle_id
        self.detection_count = 0
        
    def process_point_cloud(self, points: np.ndarray, send_detections: bool = True) -> List[Dict]:
        """Process point cloud and return vehicle detections"""
        detections = []
        
        # 1. Preprocess point cloud
        filtered_points = preprocess_point_cloud(points)
        if len(filtered_points) < 100:
            return detections
        
        # 2. Ground removal
        non_ground_points = ground_removal(filtered_points)
        if len(non_ground_points) < 50:
            return detections
        
        # 3. Clustering
        clusters = euclidean_clustering(non_ground_points, eps=0.6, min_points=15)
        
        # 4. Classification and detection creation
        for i, cluster in enumerate(clusters):
            if len(cluster) < 15:  # Skip small clusters
                continue
                
            # Get cluster center and dimensions
            center = np.mean(cluster, axis=0)
            min_coords = np.min(cluster, axis=0)
            max_coords = np.max(cluster, axis=0)
            dimensions = max_coords - min_coords
            
            # Classify cluster
            vehicle_class, confidence = classify_cluster(cluster)
            
            # Filter out low-confidence detections
            if confidence < 0.4:
                continue
            
            detection = {
                'id': f"{self.vehicle_id}_lidar_{self.detection_count}_{i}",
                'class': vehicle_class,
                'x': float(center[0]),  # Forward/backward
                'y': float(center[1]),  # Left/right
                'z': float(center[2]),  # Up/down
                'x_world': float(center[0]),
                'y_world': float(center[1]),
                'confidence': confidence,
                'dimensions': {
                    'length': float(dimensions[0]),
                    'width': float(dimensions[1]), 
                    'height': float(dimensions[2])
                },
                'num_points': len(cluster),
                'detection_type': 'lidar_clustering'
            }
            detections.append(detection)
        
        self.detection_count += 1
        
        if send_detections and detections:
            send_report(self.vehicle_id, detections)
            
        return detections

def run_kitti_detection(velodyne_dir: str, vehicle_id: str, frame_id: str):
    """Run detection on KITTI velodyne data"""
    velodyne_file = os.path.join(velodyne_dir, f"{frame_id}.bin")
    
    if not os.path.exists(velodyne_file):
        print(f"Velodyne file not found: {velodyne_file}")
        return
    
    detector = LiDARDetectionPublisher(vehicle_id)
    print(f"[{vehicle_id}] Processing KITTI frame {frame_id}")
    
    try:
        # Load point cloud
        points = load_kitti_velodyne(velodyne_file)
        print(f"Loaded {len(points)} points")
        
        # Process and send detections
        detections = detector.process_point_cloud(points)
        print(f"Found {len(detections)} vehicle detections")
        
        # Print detection summary
        for det in detections:
            print(f"  {det['class']} at ({det['x']:.1f}, {det['y']:.1f}) "
                  f"conf={det['confidence']:.2f} points={det['num_points']}")
                  
    except Exception as e:
        print(f"Error processing frame: {e}")

def run_continuous_detection(lidar_data_dir: str, vehicle_id: str, fps: float = 10.0):
    """Run continuous detection on LiDAR data files"""
    if not os.path.exists(lidar_data_dir):
        print(f"LiDAR data directory not found: {lidar_data_dir}")
        return
    
    # Find all .bin files
    bin_files = sorted([f for f in os.listdir(lidar_data_dir) if f.endswith('.bin')])
    if not bin_files:
        print("No .bin files found in directory")
        return
    
    detector = LiDARDetectionPublisher(vehicle_id)
    print(f"[{vehicle_id}] Starting continuous LiDAR detection")
    print(f"Found {len(bin_files)} files, running at {fps} FPS")
    
    try:
        for bin_file in bin_files:
            bin_path = os.path.join(lidar_data_dir, bin_file)
            
            # Load and process point cloud
            points = load_kitti_velodyne(bin_path)
            detections = detector.process_point_cloud(points)
            
            print(f"Frame {bin_file}: {len(detections)} detections")
            
            time.sleep(1.0 / fps)
            
    except KeyboardInterrupt:
        print(f"\n[{vehicle_id}] Detection stopped")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='LiDAR-based vehicle detection publisher')
    parser.add_argument('--kitti-velodyne', help='Path to KITTI velodyne_points/data directory')
    parser.add_argument('--lidar-data', help='Path to directory with .bin LiDAR files')
    parser.add_argument('--frame', default='0000000000', help='Frame ID for KITTI mode')
    parser.add_argument('--vehicle-id', default='ego', help='Vehicle ID for reports')
    parser.add_argument('--fps', type=float, default=10.0, help='Processing FPS for continuous mode')
    
    args = parser.parse_args()
    
    if args.kitti_velodyne:
        run_kitti_detection(args.kitti_velodyne, args.vehicle_id, args.frame)
    elif args.lidar_data:
        run_continuous_detection(args.lidar_data, args.vehicle_id, args.fps)
    else:
        print("Specify either --kitti-velodyne <dir> or --lidar-data <dir>")
