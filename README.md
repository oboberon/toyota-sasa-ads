# Toyota Sasa — Ads Performance

Static dashboard of Facebook Inbox campaigns per salesperson (Meta ad account 1853027781593614).
Deployed on Vercel from `main`. Data is refreshed every Monday ~05:00 (Asia/Bangkok) by a Claude scheduled task.

- `index.html` — the page (d3 from cdnjs, no build step)
- `data.json` — compact data (campaign dictionary + weekly/monthly/daily rows). Daily rows power the drill-down chart: pick one month → bars per week; pick one week → bars per day
- `scripts/build.py RAW_DIR` — turns raw Meta Ads API pulls (w_*.json, m_*.json) into weekly.json / monthly.json
- `scripts/pack.py weekly.json monthly.json UPDATED_ISO data.json [--daily daily.json --prev data.json --daily-out full_daily.json]` — packs them into `data.json`; with `--prev`, day rows older than the re-pulled window are kept from the previous `data.json`

## Access
The whole site (page and `data.json`) sits behind a PIN screen (`middleware.js`, Vercel Routing Middleware).
The PIN is the project env var `DASHBOARD_PIN` — change it in Vercel → Settings → Environment Variables, then redeploy;
changing it logs everyone out. A correct PIN keeps a browser signed in for 30 days.
