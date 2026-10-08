"""
Tiger-192 Avalanche Explorer - HTTP API & Static Web Server.
Built with Python standard library (zero external dependencies).
"""

import sys
import os
import json
import mimetypes
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any

import tiger
import avalanche

PORT = int(os.environ.get("PORT", 8000))
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")


class TigerAPIHandler(SimpleHTTPRequestHandler):
    """HTTP request handler supporting both REST API endpoints and static frontend files."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def _send_json(self, status_code: int, data: Any):
        response_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path.rstrip("/")

        if path == "/api/health":
            self._send_json(200, {
                "status": "healthy",
                "algorithm": "Tiger-192",
                "digest_bits": 192,
                "passes": 3,
                "block_size_bits": 512,
                "version": "1.0.0"
            })
            return

        elif path == "/api/test-vectors":
            vectors = []
            for msg, expected in avalanche.TEST_VECTORS.items():
                computed = tiger.tiger_hex(msg)
                vectors.append({
                    "input": msg,
                    "expected": expected,
                    "computed": computed,
                    "valid": (computed == expected)
                })
            self._send_json(200, {"vectors": vectors})
            return

        # Serve frontend static files
        super().do_GET()

    def do_POST(self):
        url = urlparse(self.path)
        path = url.path.rstrip("/")

        # Read JSON request payload
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON payload"})
            return

        try:
            if path == "/api/hash":
                text = payload.get("text", "")
                digest_bytes = tiger.tiger(text)
                digest_hex = digest_bytes.hex()
                digest_bits = avalanche.bytes_to_bits(digest_bytes)

                self._send_json(200, {
                    "text": text,
                    "hex": digest_hex,
                    "bits": digest_bits,
                    "total_bits": 192,
                    "bytes_length": 24
                })
                return

            elif path == "/api/avalanche":
                msg1 = payload.get("msg1", "The quick brown fox jumps over the lazy dog")
                msg2 = payload.get("msg2")

                # If msg2 is not provided, generate a mutant based on mode
                mode = payload.get("mode", "char")
                index = int(payload.get("index", 0))

                if msg2 is None:
                    if mode == "bit":
                        b1 = msg1.encode("utf-8")
                        b2 = avalanche.single_bit_flip(b1, index)
                        result = avalanche.analyze_avalanche(b1, b2)
                    else:
                        msg2 = avalanche.single_char_flip(msg1, index)
                        result = avalanche.analyze_avalanche(msg1, msg2)
                else:
                    result = avalanche.analyze_avalanche(msg1, msg2)

                self._send_json(200, result)
                return

            elif path == "/api/passes":
                msg1 = payload.get("msg1", "The quick brown fox jumps over the lazy dog")
                msg2 = payload.get("msg2")
                if msg2 is None:
                    msg2 = avalanche.single_char_flip(msg1, 0)

                progression = avalanche.analyze_pass_progression(msg1, msg2)
                self._send_json(200, {
                    "msg1": msg1,
                    "msg2": msg2,
                    "progression": progression
                })
                return

            elif path == "/api/simulate":
                message = payload.get("message", "The quick brown fox jumps over the lazy dog")
                trials = int(payload.get("trials", 300))
                # Bound trials to reasonable execution time
                trials = max(10, min(1000, trials))

                stats = avalanche.run_statistical_simulation(base_msg=message, num_trials=trials)
                self._send_json(200, stats)
                return

            else:
                self._send_json(404, {"error": f"Unknown endpoint: {path}"})
                return

        except Exception as e:
            self._send_json(500, {"error": str(e)})


def run_server(port: int = None, host: str = None) -> None:
    """Starts the Tiger-192 HTTP web server."""
    os.makedirs(FRONTEND_DIR, exist_ok=True)

    if port is None:
        port = int(os.environ.get("PORT", PORT))
    if host is None:
        host = os.environ.get("HOST", "0.0.0.0")

    # Attempt to bind to requested port or fallback to alternatives
    chosen_port = port
    server = None
    ports_to_try = [chosen_port]
    # Only try fallbacks if not running in a container/cloud environment where PORT is strictly assigned
    if "PORT" not in os.environ:
        ports_to_try.extend([chosen_port + 1, chosen_port + 80, 8080, 5000])

    for p in ports_to_try:
        try:
            server = ThreadingHTTPServer((host, p), TigerAPIHandler)
            chosen_port = p
            break
        except OSError:
            continue

    if not server:
        print(f"Error: Could not bind to port {port} or fallback ports.")
        sys.exit(1)

    display_host = "localhost" if host == "0.0.0.0" else host
    url = f"http://{display_host}:{chosen_port}"
    print(f"\n=======================================================")
    print(f"  Tiger-192 Avalanche Explorer Web Server Running!")
    print(f"  Listening on: {host}:{chosen_port}")
    print(f"  Local URL:    {url}")
    print(f"  API Docs:")
    print(f"    - GET  {url}/api/health")
    print(f"    - GET  {url}/api/test-vectors")
    print(f"    - POST {url}/api/hash")
    print(f"    - POST {url}/api/avalanche")
    print(f"    - POST {url}/api/passes")
    print(f"    - POST {url}/api/simulate")
    print(f"=======================================================\n")
    print("Press Ctrl+C to stop the server.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()


if __name__ == "__main__":
    cli_port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None
    run_server(port=cli_port)

