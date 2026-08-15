// Front-end for the Netflix trial sender.
// Clean professional status display; email is never saved.
const $ = (id) => document.getElementById(id);
const emailEl = $("email");
const btn = $("start");
const logEl = $("log");
const statusEl = $("status");
const statusText = $("statusText");
const API_BASE = (window.API_BASE || "").replace(/\/+$/, "");

function setStatus(text, cls) {
  statusText.textContent = text;
  statusEl.className = "status" + (cls ? " " + cls : "");
}

function updateStatus(line) {
  const l = line.toLowerCase();
  if (l.includes("starting") || l.includes("checking") ||
      l.includes("connecting") || l.includes("confirming") ||
      l.includes("re-checking") || l.includes("sending")) {
    setStatus("Working\u2026", "warn");
  } else if (l.includes("session ready")) {
    setStatus("Session ready", "ok");
  } else if (l.includes("trial detected")) {
    setStatus("Trial confirmed", "ok");
  } else if (l.includes("successfully sent")) {
    setStatus("Complete", "ok");
  } else if (l.includes("was not used") || l.includes("rejected") ||
             l.includes("not found") || l.includes("returned an error")) {
    setStatus("Skipped", "err");
  }
}

function append(text) {
  const div = document.createElement("div");
  div.textContent = text;
  logEl.appendChild(div);
  logEl.scrollTop = logEl.scrollHeight;
}

btn.addEventListener("click", async () => {
  const email = emailEl.value.trim();
  if (!email || !email.includes("@")) {
    append("[!] Please enter a valid email address.");
    return;
  }

  btn.disabled = true;
  btn.textContent = "Working...";
  logEl.innerHTML = "";
  setStatus("Working\u2026", "warn");

  try {
    const res = await fetch(API_BASE + "/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    if (!res.ok) {
      setStatus("Error", "err");
      append("Server error: HTTP " + res.status);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let finished = false;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buffer.indexOf("\n")) >= 0) {
        const line = buffer.slice(0, idx).replace(/\r$/, "");
        buffer = buffer.slice(idx + 1);
        if (line === "__DONE__") {
          finished = true;
          break;
        }
        if (line) {
          updateStatus(line);
          append(line);
        }
      }
      if (finished) break;
    }

    if (!finished) setStatus("Error", "err");
  } catch (err) {
    setStatus("Error", "err");
    append("[!] " + (err && err.message ? err.message : err));
  } finally {
    btn.disabled = false;
    btn.textContent = "Start";
  }
});

emailEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter") btn.click();
});
