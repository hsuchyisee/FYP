#!/usr/bin/env python3
"""
Vehicle Detection Integration Demo

This script demonstrates the complete vehicle detection integration pipeline.
It shows how to:
1. Start the enhanced fusion server
2. Send detections from multiple sources
3. Monitor fusion results

Usage:
  python demo_detection_integration.py --mode all
  python demo_detection_integration.py --mode camera_only
  python demo_detection_integration.py --mode synthetic_only
"""

import argparse
import subprocess
import time
import threading
import signal
import sys
import os
from typing import List

class DetectionDemo:
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = True
        
    def start_fusion_server(self, port: int = 5001):
        """Start the enhanced fusion server"""
        print(f"🚀 Starting enhanced fusion server on port {port}")
        
        cmd = [
            sys.executable, 
            'receiver_detection_fusion.py',
            '--port', str(port),
            '--fusion-method', 'confidence_weighted'
        ]
        
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            self.processes.append(proc)
            
            # Monitor server output in background
            def monitor_server():
                while self.running and proc.poll() is None:
                    line = proc.stdout.readline()
                    if line:
                        print(f"[FUSION] {line.strip()}")
                        
            threading.Thread(target=monitor_server, daemon=True).start()
            
            # Wait for server to start and check if it's actually running
            time.sleep(3)
            if proc.poll() is not None:
                print(f"❌ Fusion server failed to start (exit code: {proc.returncode})")
                return False
                
            print("✅ Fusion server started successfully")
            return True
            
        except FileNotFoundError:
            print("❌ receiver_detection_fusion.py not found")
            return False
        except Exception as e:
            print(f"❌ Failed to start fusion server: {e}")
            return False
    
    def start_synthetic_publisher(self):
        """Start synthetic detection publisher"""
        print("🤖 Starting synthetic detection publisher")
        
        try:
            proc = subprocess.Popen(
                [sys.executable, 'publisher_node.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            self.processes.append(proc)
            
            def monitor_synthetic():
                while self.running and proc.poll() is None:
                    line = proc.stdout.readline()
                    if line:
                        print(f"[SYNTHETIC] {line.strip()}")
                        
            threading.Thread(target=monitor_synthetic, daemon=True).start()
            time.sleep(1)
            print("✅ Synthetic publisher started")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start synthetic publisher: {e}")
            return False
    
    def start_camera_detection(self, camera_id: int = 0):
        """Start camera-based detection"""
        print(f"📷 Starting camera detection (device {camera_id})")
        
        if not os.path.exists('publisher_yolo_detection.py'):
            print("❌ publisher_yolo_detection.py not found")
            return False
            
        try:
            # Check if YOLO is available
            import ultralytics
            print("✅ YOLO available")
        except ImportError:
            print("⚠️  YOLO not available - install with: pip install ultralytics")
            return False
            
        try:
            cmd = [
                sys.executable,
                'publisher_yolo_detection.py',
                '--camera', str(camera_id),
                '--vehicle-id', 'ego_camera',
                '--display'
            ]
            
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            self.processes.append(proc)
            
            def monitor_camera():
                while self.running and proc.poll() is None:
                    line = proc.stdout.readline()
                    if line:
                        print(f"[CAMERA] {line.strip()}")
                        
            threading.Thread(target=monitor_camera, daemon=True).start()
            time.sleep(1)
            print("✅ Camera detection started")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start camera detection: {e}")
            return False
    
    def start_kitti_detection(self):
        """Start KITTI-based detection (if data available)"""
        print("📊 Checking for KITTI detection...")
        
        # Check if KITTI data and publisher are available
        kitti_paths = [
            '/Users/hsuchyi/Downloads/2011_09_26',
            '/Users/hsuchyi/FYP/training/label_2'
        ]
        
        available_path = None
        for path in kitti_paths:
            if os.path.exists(path):
                available_path = path
                break
                
        if not available_path:
            print("⚠️  No KITTI data found - skipping KITTI detection")
            return False
            
        if not os.path.exists('publisher_detection_enhanced.py'):
            print("❌ publisher_detection_enhanced.py not found")
            return False
            
        try:
            if 'training' in available_path:
                # Use local test data
                cmd = [
                    sys.executable,
                    'publisher_detection_enhanced.py',
                    '--basedir', '/Users/hsuchyi/FYP',
                    '--date', '2011_09_26', 
                    '--drive', '2011_09_26_drive_0011_sync',
                    '--frame', '0',
                    '--vehicle-id', 'ego_kitti'
                ]
            else:
                # Use full KITTI data
                cmd = [
                    sys.executable,
                    'publisher_detection_enhanced.py',
                    '--basedir', '/Users/hsuchyi/Downloads',
                    '--date', '2011_09_26',
                    '--drive', '2011_09_26_drive_0011_sync', 
                    '--frame', '0',
                    '--use-lidar-detection',
                    '--vehicle-id', 'ego_kitti'
                ]
                
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            self.processes.append(proc)
            
            def monitor_kitti():
                while self.running and proc.poll() is None:
                    line = proc.stdout.readline()
                    if line:
                        print(f"[KITTI] {line.strip()}")
                        
            threading.Thread(target=monitor_kitti, daemon=True).start()
            time.sleep(1)
            print(f"✅ KITTI detection started using {available_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start KITTI detection: {e}")
            return False
    
    def cleanup(self):
        """Stop all processes"""
        print("\n🛑 Stopping all processes...")
        self.running = False
        
        for proc in self.processes:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    
        print("✅ All processes stopped")
    
    def run_demo(self, mode: str = 'all'):
        """Run the detection integration demo"""
        print(f"🎯 Starting Vehicle Detection Integration Demo (mode: {mode})")
        print("="*60)
        
        # Setup signal handler for cleanup
        def signal_handler(signum, frame):
            self.cleanup()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Start fusion server
            if not self.start_fusion_server():
                print("❌ Failed to start fusion server - exiting")
                return
                
            # Start detection sources based on mode
            sources_started = 0
            
            if mode in ['all', 'synthetic_only', 'synthetic']:
                if self.start_synthetic_publisher():
                    sources_started += 1
                    
            if mode in ['all', 'camera_only', 'camera']:
                if self.start_camera_detection():
                    sources_started += 1
                    
            if mode in ['all', 'kitti']:
                if self.start_kitti_detection():
                    sources_started += 1
            
            if sources_started == 0:
                print("❌ No detection sources started - exiting")
                self.cleanup()
                return
                
            print(f"\n🎉 Demo running with {sources_started} detection source(s)")
            print("📈 Watch the fusion server output for detection results")
            print("🔄 Publishers will send detections continuously")
            print("⏹️  Press Ctrl+C to stop the demo\n")
            
            # Keep demo running
            while self.running:
                time.sleep(1)
                
                # Check if any process died
                for proc in self.processes:
                    if proc.poll() is not None:
                        return_code = proc.returncode
                        if return_code != 0:
                            print(f"⚠️  Process died with code {return_code}")
                            
        except KeyboardInterrupt:
            print("\n👋 Demo interrupted by user")
        except Exception as e:
            print(f"❌ Demo error: {e}")
        finally:
            self.cleanup()

def main():
    parser = argparse.ArgumentParser(description='Vehicle Detection Integration Demo')
    parser.add_argument('--mode', choices=['all', 'synthetic_only', 'camera_only', 'kitti'], 
                       default='all', help='Demo mode')
    
    args = parser.parse_args()
    
    # Check working directory
    if not os.path.exists('receiver_detection_fusion.py'):
        print("❌ Please run this demo from the project root directory")
        print("   (where receiver_detection_fusion.py is located)")
        sys.exit(1)
        
    demo = DetectionDemo()
    demo.run_demo(args.mode)

if __name__ == '__main__':
    main()
