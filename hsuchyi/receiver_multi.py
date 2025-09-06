import socket
import threading
import struct
import json
import time

HOST = '127.0.0.1'
PORT = 5001  # different port to avoid clashing with previous demo

# Shared storage for incoming detections
lock = threading.Lock()
all_reports = []  # each report: dict with keys: vehicle_id, timestamp, detections (list)


def recv_exact(conn, n):
    """Receive exactly n bytes or raise RuntimeError on EOF."""
    buf = bytearray()
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise RuntimeError('connection closed')
        buf.extend(chunk)
    return bytes(buf)


def handle_client(conn, addr):
    try:
        while True:
            # Read 8-byte big-endian length
            hdr = conn.recv(8)
            if not hdr:
                break
            if len(hdr) < 8:
                # try to read remaining
                hdr += recv_exact(conn, 8 - len(hdr))
            length = struct.unpack('>Q', hdr)[0]
            payload = recv_exact(conn, length)
            # For this demo payload is JSON text
            msg = json.loads(payload.decode('utf-8'))
            msg['recv_time'] = time.time()
            with lock:
                all_reports.append(msg)
            print(f"[server] Received report from {msg.get('vehicle_id')} with {len(msg.get('detections', []))} detections")
    except Exception as e:
        print(f"[server] client {addr} disconnected or error: {e}")
    finally:
        conn.close()


def fuse_reports(reports):
    # Simple late-fusion: union detections, merging those within distance threshold
    fused = []
    tol = 1.0  # distance tolerance to consider same object

    def close(a, b):
        dx = a['x'] - b['x']
        dy = a['y'] - b['y']
        return (dx*dx + dy*dy) ** 0.5 <= tol

    for r in reports:
        for d in r['detections']:
            placed = False
            for f in fused:
                if close(f, d):
                    # simple merge: keep object with higher confidence
                    if d.get('confidence', 0) > f.get('confidence', 0):
                        f.update(d)
                    placed = True
                    break
            if not placed:
                fused.append(d.copy())
    return fused


def server_loop():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"[server] Listening on {HOST}:{PORT}")
        # Accept clients in background threads
        def accept_loop():
            while True:
                conn, addr = s.accept()
                print(f"[server] Connection from {addr}")
                t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                t.start()

        threading.Thread(target=accept_loop, daemon=True).start()

        # Main loop: periodically fuse what we have and print stats
        try:
            while True:
                time.sleep(1.0)
                with lock:
                    if not all_reports:
                        continue
                    # copy and clear to simulate batch fusion of received reports
                    batch = all_reports[:]
                    all_reports.clear()
                fused = fuse_reports(batch)
                total_in = sum(len(r['detections']) for r in batch)
                print(f"[server] Batch received {len(batch)} reports, {total_in} detections -> fused {len(fused)} objects")
                # Print fused detections briefly
                for i, obj in enumerate(fused):
                    print(f"  fused[{i}]: id={obj.get('id')} x={obj.get('x'):.2f} y={obj.get('y'):.2f} conf={obj.get('confidence'):.2f}")
        except KeyboardInterrupt:
            print('\n[server] Interrupted, exiting')


if __name__ == '__main__':
    server_loop()
