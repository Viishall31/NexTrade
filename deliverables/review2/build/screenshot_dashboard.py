"""Capture dashboard pages as PNGs with headless Edge over the DevTools protocol (real-time waits,
so Streamlit's websocket-driven content has rendered). Requires the dashboard at localhost:8501."""
import base64
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import websocket

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
OUT = Path(__file__).resolve().parents[1] / "figures"
PROFILE = Path(__file__).resolve().parent / "edge_profile"
PORT = 9447
PAGES = {  # file name -> (url path, scroll-to text or None, wait seconds)
    "dash_overview": ("", None, 14),
    "dash_regimes": ("regimes", None, 16),
    "dash_trading": ("trading", None, 18),
    "dash_replay": ("replay", None, 18),
}


def cdp(ws, method, params=None, _id=[0]):
    _id[0] += 1
    ws.send(json.dumps({"id": _id[0], "method": method, "params": params or {}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == _id[0]:
            return msg.get("result", {})


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen([EDGE, "--headless=new", f"--remote-debugging-port={PORT}", f"--user-data-dir={PROFILE}",
                             "--remote-allow-origins=*", "--no-first-run", "--disable-gpu", "--hide-scrollbars", "--window-size=1440,900", "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(40):
            try:
                targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json"))
                page = next(t for t in targets if t["type"] == "page")
                break
            except Exception:
                time.sleep(0.5)
        ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=60, suppress_origin=True)
        cdp(ws, "Page.enable")
        cdp(ws, "Emulation.setDeviceMetricsOverride", {"width": 1440, "height": 900, "deviceScaleFactor": 2, "mobile": False})
        only = set(sys.argv[1:])
        for name, (path, _, wait) in PAGES.items():
            if only and name not in only:
                continue
            cdp(ws, "Page.navigate", {"url": f"http://localhost:8501/{path}"})
            time.sleep(wait)
            # hide Streamlit's top toolbar/deploy button for a cleaner capture
            cdp(ws, "Runtime.evaluate", {"expression": "document.querySelectorAll('header, [data-testid=\"stToolbar\"], [data-testid=\"stDecoration\"]').forEach(e => e.style.display='none'); true"})
            time.sleep(1)
            shot = cdp(ws, "Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
            (OUT / f"{name}.png").write_bytes(base64.b64decode(shot["data"]))
            print("saved", name)
        ws.close()
    finally:
        proc.terminate()
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)


if __name__ == "__main__":
    main()
