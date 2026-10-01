import os
import hmac
from api.research import handler as ResearchHandler
from npse.research import build_research
from npse import database
from npse.sources.market import fetch_market


class handler(ResearchHandler):
    def do_GET(self):
        secret=os.environ.get("CRON_SECRET")
        if not secret or not hmac.compare_digest(self.headers.get("Authorization",""),"Bearer "+secret):
            return self.send_json(401,{"error":"authentication_required"})
        if not database.status()["connected"]:
            return self.send_json(503,{"error":"database_not_connected"})
        try:
            feed=fetch_market()
            board=build_research(market_feed=feed)
            database.persist_market(board["companies"],feed,feed["url"],feed["retrieved_at"])
            from npse.sources.history import fetch_history
            history = database.persist_history(fetch_history())
            self.send_json(200,{"snapshot_id":database.save_snapshot(build_research(market_feed=feed)),"history":history})
        except Exception:
            self.send_json(503,{"error":"refresh_failed"})
