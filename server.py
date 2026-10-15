"""Axioma Lexis G2 HTTP Server & API Dispatcher (Port 8090).

Serves the mobile-first PWA and zero-friction REST endpoints:
- GET  /                     -> Serves pwa_dashboard.html (Direct-to-card launch)
- GET  /api/state            -> Returns system state and card counts
- GET  /api/review/next      -> Returns active capped micro-session (3-5 cards)
- POST /api/review/answer    -> Evaluates dwell, applies humane 1-tier step-back decay
- POST /api/capture/hydrate  -> Zero-typing single-word instant hydration
- POST /api/rollback         -> Functorial 1-tap Undo (Cmd+Z)
- GET  /api/notifications/next -> Returns curiosity snippet push prompt
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict
import argparse
import json
import logging

from .core import LexisCoreEngine
from .types import ReviewOutcome

logger = logging.getLogger("AxiomaLexisG2")


class LexisRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Axioma Lexis G2."""

    engine: LexisCoreEngine = None  # Bound at server startup
    html_content: str = ""

    def _send_json(self, data: Dict[str, Any], status_code: int = 200) -> None:
        """Sends JSON payload."""
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        """Handles GET requests."""
        if self.path in ("/", "/index.html", "/pwa", "/dashboard.html"):
            html_path = Path(__file__).parent / "pwa_dashboard.html"
            payload = html_path.read_text(encoding="utf-8").encode("utf-8") if html_path.exists() else self.html_content.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        elif self.path == "/manifest.json":
            manifest_path = Path(__file__).parent / "manifest.json"
            payload = manifest_path.read_text(encoding="utf-8").encode("utf-8") if manifest_path.exists() else b"{}"
            self.send_response(200)
            self.send_header("Content-Type", "application/manifest+json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        elif self.path == "/sw.js":
            sw_path = Path(__file__).parent / "sw.js"
            payload = sw_path.read_text(encoding="utf-8").encode("utf-8") if sw_path.exists() else b""
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        elif self.path in ("/icon.svg", "/favicon.ico"):
            icon_path = Path(__file__).parent / "icon.svg"
            payload = icon_path.read_bytes() if icon_path.exists() else b""
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        elif self.path in ("/download", "/download/apk", "/app.apk", "/app-debug.apk", "/app-release.apk"):
            release_apk = Path(__file__).parent / "android" / "app" / "build" / "outputs" / "apk" / "release" / "app-release.apk"
            debug_apk = Path(__file__).parent / "android" / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
            apk_path = release_apk if release_apk.exists() else debug_apk
            if apk_path.exists():
                payload = apk_path.read_bytes()
                filename = "axioma-lexis.apk" if apk_path == release_apk else "axioma-lexis-debug.apk"
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.android.package-archive")
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(payload)
            else:
                self._send_json({"error": "APK not found at build path"}, 404)

        elif self.path == "/api/state":
            summary = self.engine.get_system_summary()
            self._send_json(summary, 200)

        elif self.path.startswith("/api/review/next"):
            allow_cram = "cram=true" in self.path
            session = self.engine.get_or_create_micro_session(allow_early_cram=allow_cram)
            self._send_json({
                "success": True,
                "session": session.to_dict(),
                "all_caught_up": (len(session.cards) == 0 or session.completed)
            }, 200)

        elif self.path in ("/api/cards", "/api/lexicon"):
            cards = self.engine.get_all_cards()
            self._send_json({"success": True, "cards": [c.to_dict() for c in cards], "total": len(cards)}, 200)

        elif self.path == "/api/notifications/next":
            notif = self.engine.get_curiosity_notification()
            self._send_json({"success": True, "notification": notif.to_dict()}, 200)

        else:
            self._send_json({"error": "Not Found", "path": self.path}, 404)

    def do_POST(self) -> None:
        """Handles POST requests."""
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)
        body = {}
        if body_bytes:
            try:
                body = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                body = {}

        if self.path == "/api/capture/hydrate":
            word = body.get("word", "")
            if not word:
                self._send_json({"error": "Word cannot be empty"}, 400)
                return
            card = self.engine.add_word(word=word, custom_sentence=body.get("sentence"))
            self._send_json({"success": True, "card": card.to_dict()}, 200)

        elif self.path == "/api/cards/update":
            card_id = body.get("card_id")
            if not card_id:
                self._send_json({"error": "card_id required"}, 400)
                return
            try:
                updated = self.engine.update_card(card_id, body)
                self._send_json({"success": True, "card": updated.to_dict()}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)

        elif self.path == "/api/cards/delete":
            card_id = body.get("card_id")
            if not card_id:
                self._send_json({"error": "card_id required"}, 400)
                return
            try:
                deleted = self.engine.delete_card(card_id)
                self._send_json({"success": deleted, "card_id": card_id}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)

        elif self.path == "/api/review/answer":
            card_id = body.get("card_id")
            outcome_str = body.get("outcome", "MASTERED")
            dwell_seconds = float(body.get("dwell_seconds", 0.0))

            try:
                outcome = ReviewOutcome(outcome_str)
            except ValueError:
                outcome = ReviewOutcome.MASTERED

            try:
                res = self.engine.answer_active_card(card_id, outcome, dwell_seconds=dwell_seconds)
                self._send_json(res, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)

        elif self.path == "/api/rollback":
            restored = self.engine.undo_last_review()
            if restored:
                self._send_json({"success": True, "card": restored.to_dict()}, 200)
            else:
                self._send_json({"success": False, "message": "No action to undo"}, 200)

        else:
            self._send_json({"error": "Not Found", "path": self.path}, 404)

    def log_message(self, format: str, *args: Any) -> None:
        """Suppresses default noisy stderr logs."""
        pass


def run_lexis_server(port: int = 8090, host: str = "0.0.0.0") -> HTTPServer:
    """Initializes and runs the Axioma Lexis G2 server."""
    html_path = Path(__file__).parent / "pwa_dashboard.html"
    html_content = html_path.read_text(encoding="utf-8") if html_path.exists() else "<h1>Axioma Lexis G2</h1>"

    data_file = Path(__file__).parent / "deck_data.json"
    engine = LexisCoreEngine(data_file=data_file, seed_default=True)

    LexisRequestHandler.engine = engine
    LexisRequestHandler.html_content = html_content

    server = HTTPServer((host, port), LexisRequestHandler)
    print(f"[*] Axioma Lexis G2 running at http://{host}:{port}/")
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Axioma Lexis G2 Server")
    parser.add_argument("--port", type=int, default=8090, help="Port to bind (default: 8090)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface (default: 0.0.0.0)")
    args = parser.parse_args()

    srv = run_lexis_server(port=args.port, host=args.host)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Shutting down Axioma Lexis G2 server.")
        srv.server_close()
