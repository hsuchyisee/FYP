# Vehicle Detection Integration for Cooperative Perception

This document explains how to integrate real-time vehicle detection into your cooperative perception system.

# COMMANDS

## to kill: 
pkill -f publisher_node && pkill -f receiver_detection
## Terminal 1: Start fusion server
python receiver_detection_fusion.py --port 5001 --fusion-method confidence_weighted
## Terminal 2: Start publishers  
synthetic: python publisher_node.py
## Camera
python publisher_yolo_detection.py --camera 0 --vehicle-id ego --display
## Add another camera/RSU:
python publisher_yolo_detection.py --camera 1 --vehicle-id rsu --display
## Add LiDAR detection:
python publisher_lidar_detection.py --kitti-velodyne /path/to/lidar/data

## Quick Start

### 1. Install Dependencies

```bash
# Install basic detection requirements
pip install -r requirements_detection.txt

# For advanced LiDAR processing (optional)
pip install open3d

# For advanced 3D detection (optional) 
pip install mmcv mmdet mmdet3d
```

### 2. Start the Enhanced Fusion Server

```bash
# Start enhanced fusion server with confidence weighting
python receiver_detection_fusion.py --port 5001 --fusion-method confidence_weighted
```

### 3. Run Detection Publishers

#### Option A: Real-time Camera Detection
```bash
# Ego vehicle with camera detection
python publisher_yolo_detection.py --camera 0 --vehicle-id ego --display

# RSU with video file
python publisher_yolo_detection.py --video path/to/traffic_video.mp4 --vehicle-id rsu
```

#### Option B: LiDAR-based Detection
```bash
# Process KITTI LiDAR data
python publisher_lidar_detection.py --kitti-velodyne /path/to/kitti/velodyne_points/data --frame 0000000000

# Process custom LiDAR data
python publisher_lidar_detection.py --lidar-data /path/to/lidar_files --fps 10
```

#### Option C: Enhanced Multi-modal Detection
```bash
# KITTI dataset with optional LiDAR detection
python publisher_detection_enhanced.py \
  --basedir /path/to/KITTI \
  --date 2011_09_26 \
  --drive 2011_09_26_drive_0011_sync \
  --frame 0 \
  --use-lidar-detection

# Real-time camera detection
python publisher_detection_enhanced.py --camera 0 --vehicle-id ego
```

## System Architecture

### Detection Flow

```
[Camera] → [YOLO Detection] → [World Coordinate Transform] → [Detection Report]
    ↓
[LiDAR] → [Point Cloud Processing] → [Clustering] → [Vehicle Classification] → [Detection Report]
    ↓
[KITTI Labels] → [Static Ground Truth] → [Pose Transform] → [Detection Report]
    ↓
[Fusion Server] ← [All Detection Reports] → [Confidence-Weighted Fusion] → [Fused Detections]
```

### Detection Report Format

```json
{
  "vehicle_id": "ego",
  "timestamp": 1634567890.123,
  "detections": [
    {
      "id": "ego_det_001",
      "class": "car",
      "x": 10.5,
      "y": -2.3,
      "x_world": 10.5,
      "y_world": -2.3,
      "confidence": 0.85,
      "detection_type": "camera",
      "bbox": [100, 200, 300, 400]  // For camera detections
    }
  ]
}
```

## Integration Points

### 1. Camera-Based Detection

**File**: `publisher_yolo_detection.py`

**Features**:
- YOLOv8 vehicle detection
- Real-time camera or video processing
- 2D bounding box to world coordinate conversion
- Confidence filtering and NMS

**Usage**:
```python
from publisher_yolo_detection import YOLODetectionPublisher

detector = YOLODetectionPublisher('ego')
detections = detector.process_frame(camera_frame)
```

### 2. LiDAR-Based Detection

**File**: `publisher_lidar_detection.py`

**Features**:
- Point cloud preprocessing and filtering
- Euclidean clustering for object segmentation
- Geometric vehicle classification
- 3D bounding box estimation

**Usage**:
```python
from publisher_lidar_detection import LiDARDetectionPublisher

detector = LiDARDetectionPublisher('ego')
detections = detector.process_point_cloud(lidar_points)
```

### 3. Enhanced Multi-Modal Publisher

**File**: `publisher_detection_enhanced.py`

**Features**:
- Combines existing KITTI functionality with live detection
- Multi-source detection fusion
- Compatible with existing pose/calibration system
- Flexible detection source configuration

### 4. Enhanced Fusion Server

**File**: `receiver_detection_fusion.py`

**Features**:
- Confidence-weighted fusion algorithm
- Multi-modal detection handling
- Performance metrics and monitoring
- Advanced fusion methods (tracking-based, etc.)

**Fusion Methods**:
- `simple`: Distance-based fusion (original algorithm)
- `confidence_weighted`: Weighted position fusion with confidence
- `tracking`: Simple tracking-based fusion (extensible)

## Detection Types and Confidence Handling

### Detection Sources

1. **Camera (YOLO)**: `detection_type: "camera"`
   - High precision for visible vehicles
   - Weather and lighting dependent
   - 2D bounding boxes converted to world coordinates

2. **LiDAR (Clustering)**: `detection_type: "lidar"`
   - Weather-independent 3D detection
   - Accurate distance and size estimation
   - Can detect partially occluded vehicles

3. **Static Labels**: `detection_type: "kitti_label"`
   - Ground truth from KITTI dataset
   - Perfect for validation and testing
   - Static frame-by-frame data

### Confidence Fusion

The enhanced fusion server uses confidence weighting:

```python
# Weighted position calculation
weighted_x = sum(det.x * det.confidence) / sum(confidences)

# Multi-modal bonus (camera + LiDAR)
if multiple_detection_types:
    confidence *= 1.2  # 20% bonus for multi-modal confirmation

# Conservative confidence fusion (harmonic mean)
fused_confidence = n / sum(1/confidence_i)
```

## Performance Optimization

### Real-time Processing Tips

1. **Camera Detection**:
   ```python
   # Use smaller YOLO model for speed
   detector = YOLODetectionPublisher(model_path='yolov8n.pt')  # nano model
   
   # Process every Nth frame for speed
   if frame_count % 3 == 0:  # Process every 3rd frame
       detections = detector.process_frame(frame)
   ```

2. **LiDAR Processing**:
   ```python
   # Reduce point cloud density
   points = points[::2]  # Use every 2nd point
   
   # Limit processing region
   filtered_points = preprocess_point_cloud(points, x_range=(-20, 20))
   ```

3. **Fusion Server**:
   ```bash
   # Increase batch processing interval for high-frequency data
   python receiver_detection_fusion.py --batch-interval 0.5  # 500ms batching
   ```

### Hardware Requirements

- **Minimum**: CPU-only processing, basic camera detection
- **Recommended**: NVIDIA GPU with CUDA for real-time YOLO inference
- **Advanced**: GPU + sufficient RAM for large LiDAR point clouds

## Extending the System

### Adding New Detection Models

1. **Create detection class**:
   ```python
   class CustomDetector:
       def detect_vehicles(self, input_data):
           # Your detection logic
           return detections
   ```

2. **Integrate with publisher**:
   ```python
   detector = CustomDetector()
   detections = detector.detect_vehicles(data)
   send_report('vehicle_id', detections)
   ```

### Advanced Fusion Algorithms

1. **Implement tracking**:
   ```python
   def advanced_tracking_fusion(reports):
       # Kalman filtering
       # Hungarian assignment
       # Multi-object tracking
       return tracked_detections
   ```

2. **Add to fusion server**:
   ```python
   fusion_functions['advanced_tracking'] = advanced_tracking_fusion
   ```

## Troubleshooting

### Common Issues

1. **"ultralytics not found"**:
   ```bash
   pip install ultralytics
   ```

2. **"Connection refused"**:
   - Start fusion server first
   - Check port conflicts with `lsof -i:5001`

3. **Low detection accuracy**:
   - Adjust confidence thresholds
   - Use larger YOLO model (yolov8m.pt, yolov8l.pt)
   - Calibrate camera-to-world coordinate conversion

4. **High CPU usage**:
   - Reduce processing frequency
   - Use GPU acceleration
   - Optimize point cloud preprocessing

### Performance Monitoring

```bash
# Monitor fusion server performance
python receiver_detection_fusion.py --fusion-method confidence_weighted

# Check metrics output:
# [metrics] Total reports: 150, detections: 450, fused: 120, avg fusion time: 0.015s
```

## Examples and Test Data

### Test with Synthetic Data

```bash
# Start fusion server
python receiver_detection_fusion.py

# Send synthetic detections (existing)
python publisher_node.py

# Add camera detection
python publisher_yolo_detection.py --camera 0 --vehicle-id ego
```

### Test with KITTI Data

```bash
# Enhanced KITTI processing
python publisher_detection_enhanced.py \
  --basedir /Users/hsuchyi/Downloads \
  --date 2011_09_26 \
  --drive 2011_09_26_drive_0011_sync \
  --frame 0 \
  --use-lidar-detection
```

This integration provides a complete vehicle detection pipeline that extends your existing cooperative perception system with real-time detection capabilities while maintaining compatibility with your current KITTI-based workflow.
