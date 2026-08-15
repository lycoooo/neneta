"""Tiny local web UI for the Netflix trial sender (email is never saved).

Run:  python server.py
Then open:  http://127.0.0.1:8000

Uses only the Python standard library and reuses the exact same pipeline from
net.py, but with save_email=False so nothing is written to disk.
"""
import asyncio
import json
import os
import queue
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import net  # reuse run(), get_real_cookie(), etc.

ROOT = Path(__file__).resolve().parent
PORT = int(os.environ.get("PORT", "8000"))
DONE_MARKER = "__DONE__"


def _content_type(name: str) -> str:
    ext = Path(name).suffix.lower()
    return {
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".png": "image/png",
        ".ico": "image/x-icon",
        ".svg": "image/svg+xml",
    }.get(ext, "application/octet-stream")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep the console quiet
        pass

    def _cors(self):
        # Allow a UI hosted elsewhere (e.g. Vercel) to call this backend.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    # ---------- static files ----------
    def do_GET(self):
        clean = self.path.split("?", 1)[0].lstrip("/")
        if clean == "api/run":
            self.send_error(405)
            return
        path = ROOT / (clean or "index.html")
        try:
            path.resolve().relative_to(ROOT)
        except ValueError:
            self.send_error(403)
            return
        if not path.is_file():
            self.send_error(404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", _content_type(path.name))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except OSError:
            pass  # client disconnected mid-download - nothing to do

    # ---------- run the pipeline (streams status lines) ----------
    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/run":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
            data = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            data = {}
        email = str(data.get("email", "")).strip()
        try:
            max_attempts = int(data.get("maxAttempts", 0) or 0)
        except Exception:
            max_attempts = 0
        if max_attempts < 1:
            max_attempts = 3

        if not email or "@" not in email:
            self._send_json({"ok": False, "error": "invalid email"})
            return

        # Stream status lines as plain text, one message per line.
        try:
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
        except OSError:
            return  # client already disconnected before streaming started

        q = queue.Queue()
        threading.Thread(target=self._worker, args=(q, email, max_attempts), daemon=True).start()

        client_gone = False
        try:
            while True:
                line = q.get(timeout=120)
                if line is None:
                    break
                try:
                    self.wfile.write((line + "\n").encode("utf-8"))
                    self.wfile.flush()
                except OSError:
                    # The browser/tab closed mid-stream - stop quietly, no traceback.
                    client_gone = True
                    break
        except queue.Empty:
            if not client_gone:
                try:
                    self.wfile.write(("[!] server timeout\n").encode("utf-8"))
                except OSError:
                    client_gone = True
        finally:
            if not client_gone:
                try:
                    self.wfile.write((DONE_MARKER + "\n").encode("utf-8"))
                except OSError:
                    pass

    def _worker(self, q, email, max_attempts):
        try:
            asyncio.run(
                net.run(email, on_progress=q.put, save_email=False,
                        max_attempts=max_attempts)
            )
        except Exception as exc:
            q.put(f"[!] {exc}")
        finally:
            q.put(None)  # end-of-stream sentinel

    def _send_json(self, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Netflix Trial Sender UI -> http://127.0.0.1:{PORT}")
    print("(emails are processed WITHOUT saving them)  Close window / Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()