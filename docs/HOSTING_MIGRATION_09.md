# NPSE 09 working project and hosting

The 09 repository and its recovered 09 Drive are the working authorities, confirmed 17 November 2026. The original 10 repository, old URLs and unrecovered Drive references are historical. The original Git history and nine branches were restored; the pre-hosting rollback is `rollback/before-09-hosting-20261009` at `dd457c9`.

| Surface | Working link | Role |
| --- | --- | --- |
| GitHub | [pailapilates09-sys/NPSE](https://github.com/pailapilates09-sys/NPSE) | Code, rules, documentation, and published commit history. |
| GitHub Pages | [Operating map](https://pailapilates09-sys.github.io/NPSE/) · [09 Workspace](https://pailapilates09-sys.github.io/NPSE/workspace/) | Static project entry and searchable directory of working links. |
| Google Drive | [NPSE — Recovered Research](https://drive.google.com/drive/folders/1UzBkzbPWxUbLaGD9fwVDS7y6tuazViLj) | Editable research references; the recovery inventory and branch backups are linked in the Workspace. |
| Vercel | [NPSE Decision Board](https://npse-pailapilates09.vercel.app/) | Next.js app, research screens and Python API. |
| Neon/PostgreSQL | [Research API](https://npse-pailapilates09.vercel.app/api/research) reports runtime connectivity | Historical observations and saved research results. |

## How changes reach users

- **Verify investment engine** runs the Next.js build and Python tests with disposable PostgreSQL. **Publish website** publishes the tracked `pages/` directory when `main` is updated.
- The app and Pages directory share `data/workspace-links.json`. Refresh the tracked Pages files with `python scripts/sync_workspace.py` and verify them with `python scripts/sync_workspace.py --check`. The [October recovery commit](https://github.com/pailapilates09-sys/NPSE/blob/05ce202bfcc5f6488b274d1ecec885cffb7411d5/data/workspace-links.json) preserves superseded original references.
- Verify Pages and Vercel separately. Confirm the existing Vercel project's Git link, deploy the tested commit from 09 `main`, and read back its public Workspace and research API before declaring the app updated. Hosting management access and automatic deployment from the 09 repo were unverified when this note was updated.
- Preserve the existing Vercel project and connected database across app releases. Editing a Drive research reference does not automatically import or recalculate data.
