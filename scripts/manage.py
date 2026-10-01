"""Run locally/CI with authorized DATABASE_URL; no credentials enter the repository."""
import sys
import json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from npse import database

if __name__=="__main__":
    if sys.argv[1]=="migrate": database.migrate()
    elif sys.argv[1]=="import": print(database.import_observations(json.loads(Path(sys.argv[2]).read_text())))
    elif sys.argv[1]=="status": print(database.status())
