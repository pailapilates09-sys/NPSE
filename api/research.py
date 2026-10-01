import json
import os
import hmac
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from npse.research import build_research
from npse import database


class handler(BaseHTTPRequestHandler):
    def send_json(self,status,payload):
        body=json.dumps(payload,default=str,allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def authorized(self):
        secret=os.environ.get("INGEST_TOKEN")
        return bool(secret) and hmac.compare_digest(self.headers.get("Authorization",""),"Bearer "+secret)

    def do_GET(self):
        try:
            board=build_research()
            query=parse_qs(urlparse(self.path).query)
            if "symbol" in query:
                company=next((c for c in board["companies"] if c["symbol"]==query["symbol"][0].upper()),None)
                return self.send_json(200 if company else 404,company or {"error":"unknown_symbol"})
            if "sector" in query:
                sector=next((s for s in board["sectors"] if s["slug"]==query["sector"][0]),None)
                return self.send_json(200 if sector else 404, {**sector,"companies":[c for c in board["companies"] if c["sector"]==sector["slug"]]} if sector else {"error":"unknown_sector"})
            self.send_json(200,board)
        except Exception:
            self.send_json(503,{"error":"research_unavailable","message":"Research inputs could not be validated. No ranking issued."})

    def do_POST(self):
        if not self.authorized(): return self.send_json(401,{"error":"authentication_required"})
        try:
            length=int(self.headers.get("Content-Length","0"))
            if length>1_000_000: return self.send_json(413,{"error":"payload_too_large"})
            data=json.loads(self.rfile.read(length))
            action=data.get("action")
            if action=="import":
                self.send_json(200,{"admitted":database.import_observations(data["observations"])})
            elif action=="refresh":
                from npse.sources.market import fetch_market
                from npse.sources.registry import UNIVERSE
                feed=fetch_market()
                board=build_research(market_feed=feed)
                database.persist_market(board["companies"],feed,feed["url"],feed["retrieved_at"])
                self.send_json(200,{"snapshot_id":database.save_snapshot(build_research(market_feed=feed)),"database":database.status()})
            else: self.send_json(400,{"error":"unknown_action"})
        except ValueError as exc:
            self.send_json(400,{"error":"validation_failed","message":str(exc)[:200]})
        except Exception:
            self.send_json(503,{"error":"persistence_unavailable"})
