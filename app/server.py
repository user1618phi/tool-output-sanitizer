"""Local sanitizer server: keeps the trained models in memory and answers over HTTP.

Usage: uv run python app/server.py --models-dir models --port 8000

    GET  /api/models    -> {"models": ["P"]}
    POST /api/sanitize  {"text": "...", "models": ["P"]}
                        -> {"results": {"P": {"score", "latency_ms", "sanitized", "spans"}}}

The MCP proxy and the Claude Code hook send tool results to this server.
"""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from tool_output_sanitizer.sanitizer import Sanitizer

MODELS: dict[str, Sanitizer] = {}


class Handler(BaseHTTPRequestHandler):
    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path.split("?")[0] == "/api/models":
            return self._json({"models": sorted(MODELS)})
        self._json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        except ValueError:
            return self._json({"error": "expected a JSON body"}, 400)
        if self.path != "/api/sanitize" or "text" not in body:
            return self._json({"error": "not found"}, 404)
        text = str(body["text"])[:60_000]
        out = {}
        for name in body.get("models") or sorted(MODELS):
            if name not in MODELS:
                continue
            result = MODELS[name].sanitize(text)
            out[name] = {"score": result.score, "latency_ms": result.latency_ms, "sanitized": result.sanitized,
                         "spans": [{"start": s.start, "end": s.end, "score": s.score} for s in result.spans]}
        self._json({"results": out})

    def log_message(self, *args) -> None:
        pass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models-dir", default="models")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--threshold", type=float, default=0.5)
    args = ap.parse_args()
    for path in sorted(Path(args.models_dir).iterdir()):
        if (path / "config.json").exists():
            tuned = path / "threshold.json"  # per-model operating point chosen on a development set
            threshold = json.loads(tuned.read_text())["threshold"] if tuned.exists() else args.threshold
            MODELS[path.name] = Sanitizer(path, threshold=threshold)
            MODELS[path.name].sanitize("warm up")
            print("loaded", path.name, flush=True)
    print(f"http://127.0.0.1:{args.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
