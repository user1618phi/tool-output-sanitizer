import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from tool_output_sanitizer.mcp_proxy import rewrite

MARK = "REMOVE-THIS-SENTENCE."
TEXT = f"Quarterly report: revenue grew by four percent. {MARK} Costs stayed flat for the third quarter in a row."


def stub(text: str) -> tuple[str, list[str]]:
    return (text.replace(MARK, "[removed by sanitizer]"), [MARK]) if MARK in text else (text, [])


def response(text: str) -> dict:
    return {"jsonrpc": "2.0", "id": 7, "result": {"content": [{"type": "text", "text": text}]}}


def test_strip_replaces_only_the_flagged_text():
    message, removed = rewrite(response(TEXT), stub, "strip")
    assert removed == 1
    assert MARK not in message["result"]["content"][0]["text"]
    assert "revenue grew" in message["result"]["content"][0]["text"]


def test_flag_keeps_text_and_adds_a_warning():
    message, removed = rewrite(response(TEXT), stub, "flag")
    assert removed == 1
    assert message["result"]["content"][0]["text"] == TEXT
    assert message["result"]["content"][1]["text"].startswith("[sanitizer]")


def test_clean_result_and_errors_pass_through():
    clean = response("Quarterly report: revenue grew by four percent and costs stayed flat.")
    assert rewrite(json.loads(json.dumps(clean)), stub, "strip") == (clean, 0)
    error = {"jsonrpc": "2.0", "id": 7, "error": {"code": -1, "message": "boom"}}
    assert rewrite(dict(error), stub, "strip") == (error, 0)

    def broken(text):
        raise OSError("sanitizer down")
    assert rewrite(response(TEXT), broken, "strip")[0]["result"]["content"][0]["text"] == TEXT  # fail open


FAKE_SERVER = '''
import json, sys
for line in sys.stdin:
    m = json.loads(line)
    if m.get("method") == "initialize":
        r = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "fake", "version": "0"}}
    elif m.get("method") == "tools/list":
        r = {"tools": [{"name": "report", "description": "returns a report", "inputSchema": {"type": "object"}}]}
    elif m.get("method") == "tools/call":
        r = {"content": [{"type": "text", "text": %r}]}
    else:
        continue
    print(json.dumps({"jsonrpc": "2.0", "id": m["id"], "result": r}), flush=True)
''' % TEXT


class StubSanitizer(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        start = body["text"].find(MARK)
        spans = [{"start": start, "end": start + len(MARK), "score": 1.0}] if start >= 0 else []
        payload = json.dumps({"results": {"P": {"sanitized": stub(body["text"])[0], "spans": spans}}}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


def test_proxy_end_to_end(tmp_path: Path):
    server_script = tmp_path / "fake_server.py"
    server_script.write_text(FAKE_SERVER)
    http = HTTPServer(("127.0.0.1", 0), StubSanitizer)
    threading.Thread(target=http.serve_forever, daemon=True).start()
    requests = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "report", "arguments": {}}}]
    done = subprocess.run(
        [sys.executable, "-m", "tool_output_sanitizer.mcp_proxy", "--server", f"http://127.0.0.1:{http.server_port}/api/sanitize",
         "--", sys.executable, str(server_script)],
        input="".join(json.dumps(r) + "\n" for r in requests), capture_output=True, text=True, timeout=30)
    http.shutdown()
    replies = [json.loads(line) for line in done.stdout.splitlines()]
    assert [r["id"] for r in replies] == [1, 2, 3]
    assert replies[1]["result"]["tools"][0]["name"] == "report"  # other messages are untouched
    text = replies[2]["result"]["content"][0]["text"]
    assert MARK not in text and "[removed by sanitizer]" in text and "Costs stayed flat" in text
    assert "1 fragment(s) removed" in done.stderr
