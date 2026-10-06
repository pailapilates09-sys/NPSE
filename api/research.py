import json
import os
import hmac
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from npse.research import build_research
from npse import database


class handler(BaseHTTPRequestHandler):
    def send_json(self,status,payload):
        body=json.dumps(payload,default=str,allow_nan=False,separators=(',',':')).encode()
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
            query=parse_qs(urlparse(self.path).query,keep_blank_values=True)
            if 'download' in query and (query['download'] not in (['csv'], ['json']) or set(query) != {'download'}):
                return self.send_json(400,{'error':'invalid_export_query'})
            if 'rules' in query:
                from npse.corpus import summary
                return self.send_json(200,summary())
            board=build_research()
            if 'download' in query:
                from npse.exports import attachment
                body, content_type, filename = attachment(board, query['download'][0])
                self.send_response(200)
                self.send_header('Content-Type',content_type)
                self.send_header('Content-Disposition',f'attachment; filename="{filename}"')
                self.send_header('Cache-Control','no-store')
                self.send_header('X-Content-Type-Options','nosniff')
                self.send_header('Content-Length',str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if "symbol" in query:
                company=next((c for c in board["companies"] if c["symbol"]==query["symbol"][0].upper()),None)
                if company:
                    company={**company,'normalization_notes':{e['normalization_note_id']:board['normalization_notes'][e['normalization_note_id']] for e in company['selected_evidence'].values() if e.get('normalization_note_id')},
                             'trace_registry':{'sources':[s for s in board['corpus']['sources'] if s['source_id'] in company['rule_trace']['source_ids']],
                                               'sector_rules':[r for r in board['corpus']['sector_rules'] if r['rule_id'] in company['rule_trace']['rule_ids']]}}
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
            if length<0: return self.send_json(400,{'error':'invalid_content_length'})
            if length>1_000_000: return self.send_json(413,{"error":"payload_too_large"})
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict): raise ValueError('JSON object required')
            action=data.get("action")
            if action=='import' and (not isinstance(data.get('observations'),list) or not data['observations']):
                raise ValueError('A nonempty observations list is required')
            if action=='corporate_actions' and (not isinstance(data.get('actions'),list) or not data['actions']):
                raise ValueError('A nonempty primary corporate-action list is required')
            if action=="audit":
                self.send_json(200,database.audit())
            elif action=="primary_refresh":
                from npse.sources.primary import fetch_reviewed_primary
                batch=fetch_reviewed_primary()
                self.send_json(200,{'admitted':database.import_observations(batch['observations']),'verification':batch['verification']})
            elif action=="corporate_actions":
                self.send_json(200,database.import_actions(data['actions']))
            elif action=="import":
                self.send_json(200,{"admitted":database.import_observations(data["observations"])})
            elif action=="backfill":
                from npse.sources.history import fetch_history
                self.send_json(200,{"history":database.persist_history(fetch_history(data.get("symbols")))})
            elif action=="archive":
                from npse.sources.archive import fetch_archive
                self.send_json(200,{"admitted":database.import_observations(fetch_archive())})
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
