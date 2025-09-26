"""
Enhanced Fusion Server with Detection Confidence Handling

This extends the existing receiver_multi.py with:
- Detection confidence weighting
- Multi-modal fusion (camera + LiDAR)  
- Detection type awareness
- Enhanced fusion algorithms
- Real-time performance metrics

Usage:
  python receiver_detection_fusion.py --port 5001 --fusion-method confidence_weighted
"""

import socket
import threading
import struct
import json
import time
import math
from typing import List, Dict, Optional
import argparse

HOST = '127.0.0.1'
DEFAULT_PORT = 5001

# Shared storage for incoming detections
lock = threading.Lock()
all_reports = []

# Performance metrics
metrics = {
    'total_reports': 0,
    'total_detections': 0,
    'fused_detections': 0,
    'fusion_time': 0.0
}

def recv_exact(conn, n):
    """Receive exactly n bytes or raise RuntimeError on EOF"""
    data = b''
    while len(data) < n:
        chunk = conn.recv(n - len(data))
        if not chunk:
            raise RuntimeError("Connection closed unexpectedly")
        data += chunk
    return data

def handle_client(conn, addr):
    """Handle client connection and receive detection reports"""
    try:
        while True:
            # Read 8-byte length header
            hdr = conn.recv(8)
            if not hdr:
                break
            if len(hdr) < 8:
                hdr += recv_exact(conn, 8 - len(hdr))
                
            length = struct.unpack('>Q', hdr)[0]
            payload = recv_exact(conn, length)
            
            # Parse JSON report
            msg = json.loads(payload.decode('utf-8'))
            msg['recv_time'] = time.time()
            
            with lock:
                all_reports.append(msg)
                metrics['total_reports'] += 1
                metrics['total_detections'] += len(msg.get('detections', []))
                
            print(f"[server] Received report from {msg.get('vehicle_id')} "
                  f"with {len(msg.get('detections', []))} detections")
                  
    except Exception as e:
        print(f"[server] Client {addr} error: {e}")
    finally:
        conn.close()

def distance_between_detections(det1: Dict, det2: Dict) -> float:
    """Calculate distance between two detections"""
    x1, y1 = det1.get('x', 0), det1.get('y', 0)
    x2, y2 = det2.get('x', 0), det2.get('y', 0)
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

def confidence_weighted_fusion(reports: List[Dict], distance_threshold: float = 2.0) -> List[Dict]:
    """
    Fuse detections using confidence weighting.
    
    For each cluster of nearby detections:
    - Weight position by detection confidence
    - Choose class with highest confidence
    - Combine confidences using weighted average
    """
    all_detections = []
    for report in reports:
        for det in report.get('detections', []):
            det['source_vehicle'] = report.get('vehicle_id', 'unknown')
            det['report_timestamp'] = report.get('timestamp', time.time())
            all_detections.append(det)
    
    if not all_detections:
        return []
    
    fused = []
    used_indices = set()
    
    for i, det1 in enumerate(all_detections):
        if i in used_indices:
            continue
            
        # Find all detections within distance threshold
        cluster = [det1]
        cluster_indices = {i}
        
        for j, det2 in enumerate(all_detections):
            if j <= i or j in used_indices:
                continue
                
            if distance_between_detections(det1, det2) <= distance_threshold:
                cluster.append(det2)
                cluster_indices.add(j)
        
        used_indices.update(cluster_indices)
        
        # Fuse cluster using confidence weighting
        if len(cluster) == 1:
            fused.append(cluster[0])
        else:
            fused_detection = fuse_detection_cluster(cluster)
            fused.append(fused_detection)
    
    return fused

def fuse_detection_cluster(cluster: List[Dict]) -> Dict:
    """Fuse a cluster of detections using confidence weighting"""
    if not cluster:
        return {}
        
    if len(cluster) == 1:
        return cluster[0]
    
    # Calculate total confidence for weighting
    total_confidence = sum(det.get('confidence', 0.5) for det in cluster)
    
    if total_confidence == 0:
        total_confidence = len(cluster)  # Fallback to equal weighting
    
    # Weighted position calculation
    weighted_x = sum(det.get('x', 0) * det.get('confidence', 0.5) for det in cluster) / total_confidence
    weighted_y = sum(det.get('y', 0) * det.get('confidence', 0.5) for det in cluster) / total_confidence
    
    # Choose class with highest confidence
    best_class_det = max(cluster, key=lambda d: d.get('confidence', 0))
    
    # Calculate fused confidence
    detection_types = set(det.get('detection_type', 'unknown') for det in cluster)
    multi_modal_bonus = 1.2 if len(detection_types) > 1 else 1.0
    
    # Use harmonic mean for confidence fusion (conservative)
    confidences = [det.get('confidence', 0.5) for det in cluster]
    fused_confidence = len(confidences) / sum(1.0 / max(c, 0.01) for c in confidences)
    fused_confidence = min(fused_confidence * multi_modal_bonus, 1.0)
    
    # Create fused detection
    fused_detection = {
        'id': f"fused_{int(time.time()*1000)}_{hash(tuple(sorted(det.get('id', '') for det in cluster))) % 10000}",
        'class': best_class_det.get('class', 'vehicle'),
        'x': weighted_x,
        'y': weighted_y,
        'x_world': weighted_x,
        'y_world': weighted_y,
        'confidence': fused_confidence,
        'detection_type': 'fused',
        'source_count': len(cluster),
        'source_vehicles': list(set(det.get('source_vehicle', 'unknown') for det in cluster)),
        'source_types': list(detection_types),
        'fusion_method': 'confidence_weighted'
    }
    
    return fused_detection

def simple_fusion(reports: List[Dict], distance_threshold: float = 1.5) -> List[Dict]:
    """Simple fusion (original algorithm from receiver_multi.py)"""
    fused = []
    
    for report in reports:
        for det in report.get('detections', []):
            placed = False
            for fused_det in fused:
                if distance_between_detections(det, fused_det) <= distance_threshold:
                    # Keep detection with higher confidence
                    if det.get('confidence', 0) > fused_det.get('confidence', 0):
                        fused_det.update(det)
                    placed = True
                    break
                    
            if not placed:
                fused.append(det.copy())
                
    return fused

def track_based_fusion(reports: List[Dict]) -> List[Dict]:
    """
    Simple tracking-based fusion.
    
    This is a placeholder for more advanced tracking algorithms like:
    - Kalman filtering
    - Hungarian assignment
    - Multi-object tracking (MOT)
    """
    # For now, use confidence weighted fusion with tracking IDs
    fused = confidence_weighted_fusion(reports)
    
    # Add simple tracking IDs (in real implementation, use proper tracking)
    for i, det in enumerate(fused):
        det['track_id'] = f"track_{i}"
        
    return fused

def print_fusion_results(fused_detections: List[Dict], batch_reports: List[Dict]):
    """Print detailed fusion results"""
    total_input = sum(len(r.get('detections', [])) for r in batch_reports)
    
    print(f"[fusion] Input: {len(batch_reports)} reports, {total_input} detections → "
          f"Output: {len(fused_detections)} fused objects")
    
    # Group by vehicle type
    vehicle_counts = {}
    confidence_sum = 0
    
    for det in fused_detections:
        vehicle_class = det.get('class', 'unknown')
        vehicle_counts[vehicle_class] = vehicle_counts.get(vehicle_class, 0) + 1
        confidence_sum += det.get('confidence', 0)
    
    if vehicle_counts:
        print(f"[fusion] Detected vehicles: {dict(vehicle_counts)}")
        avg_confidence = confidence_sum / len(fused_detections)
        print(f"[fusion] Average confidence: {avg_confidence:.3f}")
    
    # Print top detections
    sorted_dets = sorted(fused_detections, key=lambda d: d.get('confidence', 0), reverse=True)
    for i, det in enumerate(sorted_dets[:5]):  # Show top 5
        sources = det.get('source_vehicles', ['unknown'])
        types = det.get('source_types', ['unknown'])
        print(f"  [{i+1}] {det.get('class', 'vehicle')} at ({det.get('x', 0):.1f}, {det.get('y', 0):.1f}) "
              f"conf={det.get('confidence', 0):.3f} sources={sources} types={types}")

def server_loop(port: int, fusion_method: str = 'confidence_weighted'):
    """Main server loop with enhanced fusion"""
    fusion_functions = {
        'simple': simple_fusion,
        'confidence_weighted': confidence_weighted_fusion,
        'tracking': track_based_fusion
    }
    
    fusion_func = fusion_functions.get(fusion_method, confidence_weighted_fusion)
    print(f"[server] Using fusion method: {fusion_method}")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, port))
        s.listen()
        print(f"[server] Enhanced fusion server listening on {HOST}:{port}")
        
        # Accept connections in background
        def accept_loop():
            while True:
                try:
                    conn, addr = s.accept()
                    print(f"[server] New client connected: {addr}")
                    threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
                except Exception as e:
                    print(f"[server] Accept error: {e}")
                    break
        
        threading.Thread(target=accept_loop, daemon=True).start()
        
        # Main fusion loop
        try:
            while True:
                time.sleep(1.0)  # Process every second
                
                with lock:
                    if not all_reports:
                        continue
                    batch = all_reports[:]
                    all_reports.clear()
                
                # Perform fusion
                start_time = time.time()
                fused = fusion_func(batch)
                fusion_time = time.time() - start_time
                
                # Update metrics
                metrics['fused_detections'] += len(fused)
                metrics['fusion_time'] += fusion_time
                
                if fused:
                    print_fusion_results(fused, batch)
                    print(f"[fusion] Processing time: {fusion_time:.3f}s")
                
                # Print performance metrics every 10 seconds
                if int(time.time()) % 10 == 0:
                    print(f"[metrics] Total reports: {metrics['total_reports']}, "
                          f"detections: {metrics['total_detections']}, "
                          f"fused: {metrics['fused_detections']}, "
                          f"avg fusion time: {metrics['fusion_time']/max(1, metrics['total_reports']):.3f}s")
                    
        except KeyboardInterrupt:
            print('\n[server] Shutting down fusion server')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Enhanced detection fusion server')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Server port')
    parser.add_argument('--fusion-method', choices=['simple', 'confidence_weighted', 'tracking'],
                       default='confidence_weighted', help='Fusion algorithm')
    
    args = parser.parse_args()
    
    server_loop(args.port, args.fusion_method)
