import socket
import time
import pickle  # for serializing Python objects

# Simple publisher example
# ------------------------
# This script demonstrates the minimal steps to send a Python object
# (here a small dict) to a TCP receiver on the same machine.
#
# Steps performed:
# 1. Prepare a Python object (data).
# 2. Serialize it to bytes using pickle.dumps (for this demo).
# 3. Open a TCP socket and connect to the receiver (HOST, PORT).
# 4. Send all bytes with s.sendall(...).
# 5. Close the socket (context manager does this) which signals EOF to the receiver.

# Example data (could be an image array, detection results, or plain text)
data = {"frame_id": 1, "content": "dummy_fused_data"}

# Serialize to bytes. NOTE: pickle is convenient but unsafe for untrusted data.
# For text use UTF-8 encoded bytes or JSON (json.dumps(...).encode('utf-8')).
serialized_data = pickle.dumps(data)

# Setup socket
HOST = "127.0.0.1"  # loopback (same machine)
PORT = 5000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # Connect to the listening receiver
    s.connect((HOST, PORT))
    start = time.time()
    # sendall ensures all bytes are pushed to the OS for delivery
    s.sendall(serialized_data)
    end = time.time()

print(f"Sent {len(serialized_data)} bytes in {end - start:.6f} sec")

# How to extend this for different content types (conceptual):
# - Text messages:
#   * Use JSON or plain UTF-8 text. E.g. payload = json.dumps(obj).encode('utf-8')
#   * Optionally prepend a small header with content-type and length.
# - Images:
#   * Encode the image to bytes (e.g., JPEG via OpenCV: _, buf = cv2.imencode('.jpg', img); payload = buf.tobytes()).
#   * Send a header with length and mime/type so receiver knows how to decode.
# - Videos / large files:
#   * Stream in chunks. Use a length-prefix or multipart framing so the receiver knows
#     when a frame/file is complete.
#   * For live video you may send repeated frame messages (each with a small header:
#     frame_id, timestamp, payload_length) and the receiver can process frames as they arrive.
#
# Example robust framing approach (recommended for production):
# 1) Send a fixed-size header (e.g. 4 or 8 bytes) containing the payload length (big-endian integer).
# 2) Optionally send a short type string or JSON metadata block describing content type and encoding.
# 3) Then send exactly `length` bytes of payload.
# Receiver reads the header, then reads exactly `length` bytes (looping until all bytes are read).
