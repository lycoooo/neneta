# Deploying the Netflix Trial Sender (free)

## Important reality check
This tool runs a **real browser** (Playwright) and streams status for ~30 seconds.
Vercel's **free** serverless functions have a **60s limit**, no persistent
process, and can't run a browser — so the **engine can't live on Vercel**.

The free setup that works:

```
┌──────────────┐   https   ┌───────────────┐   https   ┌───────────────────────┐
│  Vercel UI   │ ────────▶ │  Your machine │ ───────▶ │  Vercel-hosted UI      │
│ (index.html) │   tunnel  │ python server │  CORS    │ calls /api/run on the  │
└──────────────┘           │  .py + browser│          │ tunnel URL (backend)   │
                           └───────────────┘          └───────────────────────┘
```

---

## Option 1 — Vercel front-end + Cloudflare Tunnel backend (recommended)

### Step 1: Deploy the UI to Vercel (free)
Only these files are needed on Vercel: `index.html`, `style.css`, `script.js`,
`config.js`, `vercel.json`.

**Via GitHub (no installs):**
1. Create a repo and push the folder above.
2. Go to https://vercel.com → **Add New → Project** → import the repo.
3. Framework preset: **Other** (it's a static site). Click **Deploy**.
4. You get a URL like `https://your-app.vercel.app`.

**Via CLI:**
```bash
npm i -g vercel
cd C:\Users\Lyco\Downloads\netflix
vercel            # first time: log in, project setup
vercel --prod
```

### Step 2: Run the engine on your PC (keep this window open)
```powershell
python server.py
```

### Step 3: Expose it with a free tunnel
Download `cloudflared` from https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```
Copy the `https://xxxx-xxxx.trycloudflare.com` URL it prints.

> Tip: `trycloudflare` URLs change every run. For a permanent URL, create a
> **named tunnel** with your own domain (also free) and use `--hostname`.

### Step 4: Point the UI at your engine
Edit `config.js`:
```js
window.API_BASE = "https://xxxx-xxxx.trycloudflare.com";
```
Re-deploy (push to GitHub, or `vercel --prod`). Done — the Vercel page now
streams status from the engine on your PC (CORS is already enabled).

---

## Option 2 — Skip Vercel entirely (simplest, still free)
The whole app (UI + API) can be served straight from your PC:
```powershell
python server.py
cloudflared tunnel --url http://127.0.0.1:8000
```
Open the printed `https://xxxx.trycloudflare.com` URL — it's the complete tool.
No `config.js` change needed. To host the UI on Vercel but keep this simpler
flow, just leave `window.API_BASE = ""` in the deployed copy? No — with an
empty base the UI expects the API on the same origin, which Vercel doesn't
serve. So for a Vercel UI you must set `API_BASE` (Option 1, Step 4).

---

## Option 3 — Always-on host (Render free)
Possible but not recommended:
- Render **free** web services sleep after 15 minutes idle.
- A datacenter IP is far more likely to be blocked/bot-flagged by Netflix.
- Needs a Dockerfile that installs Chromium (heavy, slow cold starts).

If you still want it: create a `Dockerfile` installing `playwright` +
`playwright install --with-deps chromium`, run `python server.py` on port
8000, add `PORT=8000` env var.

---

## Notes & warnings
- The URL is public — anyone who has it can use the tool. Keep it private, and
  consider adding a simple password check if you share it.
- You still must keep `python server.py` running on your PC for the engine to
  work (that's the browser part that Vercel can't run).
- Don't use this for spam; it's a personal automation tool.
