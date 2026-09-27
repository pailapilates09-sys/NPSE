from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler

from npse.engine import build_dashboard


class handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict):
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "public, s-maxage=300, stale-while-revalidate=600")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try:
            self._send(200, build_dashboard())
        except Exception as exc:
            self._send(502, {
                "error": "upstream_unavailable",
                "message": "NPSE could not assemble a fresh dashboard from the configured upstream adapter.",
                "detail": str(exc)[:300],
            })
