"""VoiceMeet local demo server with shared recording storage.
Run with: python server.py
This is for local testing only; add authentication and HTTPS before production use.
"""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json, base64, re, mimetypes, os, threading

ROOT = Path(__file__).resolve().parent
RECORDINGS_DIR = ROOT / "recordings"
METADATA_FILE = RECORDINGS_DIR / "recordings.json"
RECORDINGS_DIR.mkdir(exist_ok=True)
LOCK = threading.Lock()


def read_metadata():
    try:
        return json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def write_metadata(items):
    tmp = METADATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(METADATA_FILE)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/api/recordings":
            with LOCK:
                items = read_metadata()
            payload = json.dumps(items, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        return super().do_GET()

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/recordings":
            self.send_error(404, "Unknown API endpoint")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 60 * 1024 * 1024:
                self.send_error(413, "Recording payload is empty or larger than 60 MB")
                return
            body = self.rfile.read(length)
            incoming = json.loads(body.decode("utf-8"))
            data_url = incoming.pop("dataUrl", "")
            match = re.match(r"^data:(audio/[^;,]+)(?:;[^,]*)?;base64,(.+)$", data_url, re.S)
            if not match:
                self.send_error(400, "Audio data must be a base64 audio data URL")
                return
            mime = match.group(1)
            audio_bytes = base64.b64decode(match.group(2), validate=True)
            if not audio_bytes:
                self.send_error(400, "Empty audio recording")
                return
            raw_name = str(incoming.get("filename") or "voicemeet-recording.webm")
            safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", Path(raw_name).name)
            if not safe_name.lower().endswith((".webm", ".ogg", ".wav", ".mp4", ".m4a")):
                safe_name += ".webm"
            # Avoid overwriting if two users generate the same filename.
            target = RECORDINGS_DIR / safe_name
            counter = 1
            while target.exists():
                target = RECORDINGS_DIR / f"{Path(safe_name).stem}_{counter}{Path(safe_name).suffix}"
                counter += 1
            target.write_bytes(audio_bytes)
            item = {k: incoming.get(k) for k in ("id", "sessionId", "meetingId", "meetingTitle", "speakerId", "speakerName", "createdAt", "duration", "mime", "filename")}
            item["filename"] = target.name
            item["mime"] = mime
            item["audioUrl"] = "/recordings/" + target.name
            with LOCK:
                items = read_metadata()
                items.insert(0, item)
                write_metadata(items)
            payload = json.dumps(item, ensure_ascii=False).encode("utf-8")
            self.send_response(201)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            self.send_error(400, f"Invalid recording payload: {exc}")
        except Exception as exc:
            self.log_error("Recording upload failed: %s", exc)
            self.send_error(500, "Could not save recording on server")

    def log_message(self, fmt, *args):
        print("[VoiceMeet] " + fmt % args)


if __name__ == "__main__":
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("0.0.0.0", 8000), Handler)
    print("VoiceMeet server running at http://localhost:8000")
    print("Host portal: http://localhost:8000/host.html")
    print("User portal: http://localhost:8000/user.html")
    print("Shared audio files are saved in the recordings folder.")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nVoiceMeet server stopped.")
    finally:
        server.server_close()
