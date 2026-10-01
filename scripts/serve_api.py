"""Local Python API for functional QA; production uses Vercel Python functions."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from http.server import ThreadingHTTPServer
from api.research import handler as Research
from api.dashboard import handler as Dashboard

class Handler(Research, Dashboard):
    def do_GET(self):
        if self.path.startswith("/api/dashboard"):
            return Dashboard.do_GET(self)
        return super().do_GET()

if __name__=="__main__":
    ThreadingHTTPServer(("127.0.0.1",8000),Handler).serve_forever()
