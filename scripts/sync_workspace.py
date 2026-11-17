"""Publish the same active link catalogue on the app and GitHub Pages."""

import argparse
import json
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = "https://npse-pailapilates09.vercel.app"
CATALOGUE = ROOT / "data/workspace-links.json"
PAGES = ROOT / "pages/workspace"


def card(entry):
    target = entry["url"]
    if target.startswith("/") and not target.startswith("//"):
        target = APP + target
    if not target.startswith("https://"):
        raise ValueError(f"Unsupported workspace URL for {entry['id']}")
    text = {key: escape(entry[key]) for key in ("group", "status", "title", "purpose", "how", "note")}
    return (
        f'      <article>\n'
        f'        <p class="meta">{text["group"]} · {text["status"]}</p>\n'
        f'        <h2><a href="{escape(target, quote=True)}">{text["title"]}</a></h2>\n'
        f'        <p>{text["purpose"]}</p>\n'
        f'        <p><strong>How:</strong> {text["how"]}</p>\n'
        f'        <p class="note">{text["note"]}</p>\n'
        f'      </article>'
    )


def render(manifest):
    cards = "\n".join(card(entry) for entry in manifest["entries"])
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <title>NPSE 09 · Working research workspace</title>
  <style>
    body{font:1rem/1.55 system-ui,sans-serif;margin:0;background:#f4f8f6;color:#17342e}
    main{max-width:69rem;margin:auto;padding:clamp(1rem,4vw,2rem)}
    a{color:#125f50;text-underline-offset:.16em}
    a:focus-visible,input:focus-visible{outline:3px solid #986300;outline-offset:4px}
    h1{font-size:clamp(1.9rem,5vw,2.8rem);line-height:1.2}
    .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,17rem),1fr));gap:1rem}
    article{padding:1rem 1.15rem;border:1px solid #aac9bd;border-radius:.7rem;background:#fff;overflow-wrap:anywhere}
    h2{font-size:1.13rem;line-height:1.3;margin:.45rem 0}
    article p{margin:.45rem 0}
    .meta,.note{color:#465c55;font-size:.9rem}
    label{display:block;font-weight:650;margin:1.3rem 0 .25rem}
    input{box-sizing:border-box;width:min(100%,36rem);padding:.65rem;border:1px solid #678b7d;border-radius:.45rem;font:inherit}
  </style>
</head>
<body>
  <main>
    <nav aria-label="Project links"><a href="../">NPSE 09 home</a> · <a href="../#operating-map">Project tree</a> · <a href="https://npse-pailapilates09.vercel.app/">Decision Board</a></nav>
    <h1>NPSE 09 Working Workspace</h1>
    <p>Open the working Drive, research files, GitHub repository or live decision engine. The recovered records are editable references; the engine reads its historical data from PostgreSQL.</p>
    <label for="search">Find a tool or document</label>
    <input id="search" type="search" placeholder="Try Drive, source, formula or Actions">
    <p id="count" role="status"></p>
    <noscript><p>All resources are listed below. Search requires JavaScript.</p></noscript>
    <div class="cards">
""" + cards + """
    </div>
  </main>
  <script>
    const search = document.querySelector('#search');
    const cards = [...document.querySelectorAll('.cards article')];
    const count = document.querySelector('#count');
    function filter() {
      const query = search.value.trim().toLowerCase();
      let visible = 0;
      for (const card of cards) {
        card.hidden = !card.textContent.toLowerCase().includes(query);
        if (!card.hidden) visible++;
      }
      count.textContent = `${visible} of ${cards.length} resources shown`;
    }
    search.addEventListener('input', filter);
    filter();
  </script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify the tracked Pages files match the catalogue.")
    args = parser.parse_args()
    source = CATALOGUE.read_text(encoding="utf-8")
    workspace = json.loads(source)
    files = {"links.json": source, "index.html": render(workspace)}
    if args.check:
        stale = [name for name, text in files.items() if not (PAGES / name).exists() or (PAGES / name).read_text(encoding="utf-8") != text]
        if stale:
            parser.exit(1, f"Outdated Workspace files: {', '.join(stale)}. Run python scripts/sync_workspace.py.\n")
        print(f"Workspace files match {len(workspace['entries'])} links.")
        return
    for name, text in files.items():
        (PAGES / name).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
