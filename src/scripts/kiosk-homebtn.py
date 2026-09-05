#!/usr/bin/env python3
"""
Console Pi - Tiem nut noi "Ve Dashboard" vao MOI trang web ma kiosk dang mo

Boi canh: tab YouTube (ui/youtube.py) tung co nut dieu huong thang sang
youtube.com that. Su co that da xay ra: nguoi dung bam vao 1 lien ket ben
trong YouTube, bi dua sang mot website khac (vd datbike.vn) roi KET CUNG
luon o do - man hinh kiosk khong co thanh dia chi/nut Back, va co che "vuot
canh de lui" cua Chromium khong dang tin cay tren man hinh cam ung Linux
(da kiem chung that, khong doan). Phai remote vao chay
`systemctl restart console-pi-kiosk` moi cuu duoc man hinh.

Giai phap dung o day: mot nut nho, luon noi CO DINH tren man hinh, xuat
hien tren MOI trang duoc tai (khong rieng gi trang cua Console Pi) - bam
vao la ve thang dashboard, bat ke dang o dau. Lam duoc dieu nay bang cach
DIEU KHIEN CHROMIUM TU BEN NGOAI qua giao thuc DevTools (CDP) cua chinh no
(giong cach cac cong cu tu dong hoa trinh duyet nhu Puppeteer/Selenium van
lam - khong phai extension, khong can quyen gi them):

  1. kiosk-start.sh bat Chromium voi --remote-debugging-port=9222 - CHI
     nghe tren 127.0.0.1 (mac dinh cua Chromium khi khong chi ro dia chi
     khac), da xac nhan bang `ss -tlnp` khong lo ra mang ngoai.
  2. Script nay ket noi vao dung "trang" (page target) cua kiosk qua
     WebSocket, roi goi lenh CDP `Page.addScriptToEvaluateOnNewDocument` -
     lenh nay dang ky 1 doan JavaScript de Chromium TU DONG chay lai MOI
     KHI co 1 tai lieu moi duoc tai (tuc la moi lan dieu huong sang trang
     khac), khong can script nay can thiep lai tu lan thu hai tro di. Da
     kiem chung that: dieu huong qua nhieu trang khac nhau, nut van con.
  3. Script nay chi con nhiem vu GIU KET NOI WebSocket song (dang ky se mat
     hieu luc neu ngat ket noi) va TU NOI LAI neu Chromium khoi dong lai
     (kiosk restart tao process Chromium moi = phai dang ky lai tu dau).

Nut nay TU AN tren chinh cac trang cua Console Pi (da co thanh dieu huong
rieng, thua nut nay).
"""
import json
import time
import urllib.error
import urllib.request

import websocket

CDP_BASE = "http://127.0.0.1:9222"
DASHBOARD_ORIGIN = "http://127.0.0.1:8880"

# Chay truc tiep trong ngu canh cua trang (nhu the la script cua chinh
# trang do) - khong phu thuoc CDP con song hay khong sau khi da chay.
INJECT_JS = f"""
(function() {{
  if (location.origin === "{DASHBOARD_ORIGIN}") return;   // trang cua minh, khong can nut nay
  if (window.__cpHomeBtnInjected) return;
  window.__cpHomeBtnInjected = true;

  function attach() {{
    var b = document.createElement("button");
    b.textContent = "🏠 Console Pi";
    b.setAttribute("type", "button");
    b.style.cssText = [
      "position:fixed", "left:10px", "bottom:10px", "z-index:2147483647",
      "background:#4CAF50", "color:#fff", "border:none", "border-radius:24px",
      "padding:12px 18px", "font-size:15px", "font-family:system-ui,Arial,sans-serif",
      "box-shadow:0 3px 14px rgba(0,0,0,.5)", "cursor:pointer",
      "touch-action:manipulation", "-webkit-user-select:none", "user-select:none",
      "opacity:0.88"
    ].join(";");
    b.addEventListener("pointerdown", function(ev) {{
      ev.preventDefault();
      location.href = "{DASHBOARD_ORIGIN}/";
    }});
    document.documentElement.appendChild(b);
  }}

  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", attach);
  }} else {{
    attach();
  }}
}})();
"""


def _cdp_call(ws, msg_id, method, params=None):
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == msg_id:
            return resp


def _find_page_target():
    with urllib.request.urlopen(f"{CDP_BASE}/json", timeout=5) as r:
        targets = json.loads(r.read())
    for t in targets:
        if t.get("type") == "page":
            return t.get("webSocketDebuggerUrl")
    return None


def run_once():
    ws_url = _find_page_target()
    if not ws_url:
        return False

    ws = websocket.create_connection(ws_url, timeout=10, suppress_origin=True)
    try:
        _cdp_call(ws, 1, "Page.enable")
        _cdp_call(ws, 2, "Page.addScriptToEvaluateOnNewDocument", {"source": INJECT_JS})
        print("Da dang ky nut Ve Dashboard, giu ket noi song.", flush=True)
        # Giu ket noi mo (dang ky mat hieu luc neu ngat) - doc thu dong,
        # Chromium se dong socket neu tab/trinh duyet dong lai.
        ws.settimeout(30)
        while True:
            try:
                ws.recv()
            except websocket.WebSocketTimeoutException:
                # Ping nhe de phat hien som neu ket noi da chet
                _cdp_call(ws, 99, "Page.getNavigationHistory")
    finally:
        try:
            ws.close()
        except Exception:
            pass
    return True


def main():
    while True:
        try:
            run_once()
        except (urllib.error.URLError, ConnectionError, OSError,
                websocket.WebSocketException, TimeoutError):
            pass
        except Exception as e:
            print(f"Loi khong luong truoc: {e}", flush=True)
        time.sleep(3)   # Chromium chua san sang hoac vua khoi dong lai - thu lai


if __name__ == "__main__":
    main()
