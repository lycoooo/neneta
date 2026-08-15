// ============================================================
//  Backend API base URL
// ============================================================
//  The UI (Vercel) and the engine (Render) live on DIFFERENT
//  domains, so this MUST be the public URL of the Render backend.
//
//  This is the live Render backend URL:
//
//     window.API_BASE = "https://ahabon.onrender.com";
//
//  (no trailing slash — the page appends /api/run itself)
//
//  Local mode only (python server.py on your PC + opening
//  http://127.0.0.1:8000 yourself) can keep this as "".
//  If you deploy the UI to Vercel and leave it empty, the
//  browser asks Vercel for /api/run -> HTTP 404 (what you saw).
// ============================================================
window.API_BASE = "https://ahabon.onrender.com";
