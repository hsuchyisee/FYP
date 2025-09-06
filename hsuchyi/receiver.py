import socket
import pickle
import time

HOST = "127.0.0.1"
PORT = 5000


def receive_all(conn, bufsize=4096):
    """Read all data from conn until the peer closes the connection.

    This helper repeatedly calls conn.recv until recv() returns an empty bytes
    object which indicates the peer has closed the sending side (EOF).

    For a single-message protocol where the sender calls close() after sending,
    this is a simple way to collect the full payload. For multi-message or
    streaming protocols, prefer a length-prefixed framing (see notes below).
    """
    chunks = []
    while True:
        chunk = conn.recv(bufsize)
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # SO_REUSEADDR allows the server to re-bind the port even if the OS
        # considers it in TIME_WAIT from the last run. This helps during
        # development where you stop/start the server frequently.
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print("Receiver is listening...")

        # Accept a single connection (for demo). For a persistent server,
        # wrap the following in a loop and optionally handle each client in
        # a new thread/process.
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            start = time.time()
            # Read until sender closes the connection
            data = receive_all(conn)
            end = time.time()

            if not data:
                print("No data received.")
            else:
                # The publisher used pickle.dumps to serialize the object.
                # Pickle is convenient but insecure for untrusted data.
                received_obj = pickle.loads(data)
                print(f"Received: {received_obj}")
                print(f"Received {len(data)} bytes in {end - start:.6f} sec")
except KeyboardInterrupt:
    print('\nReceiver interrupted by user')
except Exception as e:
    print(f"Receiver error: {e}")


# Extension notes: how to add text, images, and videos
# ----------------------------------------------------
# 1) Text (simple):
#    - Publisher: payload = json.dumps(obj).encode('utf-8')
#    - Send the payload the same way. Receiver: data.decode('utf-8') then json.loads(...).
#
# 2) Images (single image per message):
#    - Option A (encode bytes): Use OpenCV's imencode to compress image to JPEG/PNG bytes:
#        _, buf = cv2.imencode('.jpg', image)
#        payload = buf.tobytes()
#      Receiver decodes with np.frombuffer + cv2.imdecode.
#    - Option B (raw arrays): Serialize numpy arrays directly with np.save to a BytesIO,
#      or use pickle (but size may be larger). Prefer encoded image bytes for network efficiency.

# 3) Video / large files / streaming frames:
#    - Use framing. A simple framing protocol:
#        * Sender: send 8-byte big-endian unsigned integer length L, then send L bytes of payload.
#        * Receiver: first read 8 bytes, parse L, then call a helper that reads exactly L bytes
#          (looping recv until total L bytes read). Process that payload as one message/frame.
#    - This lets you send multiple messages over one TCP connection without closing the socket.

# 4) Example read-exact helper (pseudo):
#    def recv_exact(conn, n):
#        buf = bytearray()
#        while len(buf) < n:
#            chunk = conn.recv(min(4096, n - len(buf)))
#            if not chunk:
#                raise RuntimeError('connection closed before receiving required bytes')
#            buf.extend(chunk)
#        return bytes(buf)

# 5) Metadata + content-type:
#    - It's useful to send a small JSON metadata block before each payload describing:
#        {"type": "text" | "image" | "frame", "encoding": "utf-8" | "jpg", "length": 12345}
#      Then the receiver reads that metadata (length-prefixed or newline-terminated) and knows how
#      to decode the following bytes.

# Security reminder: avoid unpickling data from untrusted sources. Use JSON for simple data
# or sign/verify messages if you need authentication.

