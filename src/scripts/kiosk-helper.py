#!/usr/bin/env python3
"""
Console Pi - Tro giup kiosk: tiem nut "Ve Dashboard" + ban phim ao vao MOI
trang web ma kiosk dang mo (khong rieng gi trang cua Console Pi)

LICH SU / LY DO (khong doan, da kiem chung that):

  1. Nut "Ve Dashboard": sau su co that nguoi dung bi ket cung tren mot
     website khac (bam link trong YouTube, bi dua sang datbike.vn, "vuot
     canh man hinh" khong dua ve duoc, phai remote vao chay
     `systemctl restart console-pi-kiosk` moi cuu duoc man hinh) - xem
     them trong ui/youtube.py. Giai phap: dieu khien Chromium tu ben ngoai
     qua giao thuc DevTools cua chinh no de TIEM 1 nut noi luon xuat hien
     tren MOI trang, bam la ve dashboard, khong phu thuoc cu chi cam ung.

  2. Ban phim ao tren cac trang KHAC (vd o tim kiem/binh luan/chat that su
     cua chinh youtube.com): vkeyboard.js (dashboard cua Console Pi) chi
     chay duoc tren trang CUA CHINH NO - khong gan duoc vao website khac.
     Da thu tim cach he thong hien ban phim ao dung chung cho moi ung dung
     (cai wvkbd, squeekboard - hai ban phim ao Wayland pho bien) va chay
     thu tren chinh phien man hinh kiosk dang song: CA HAI DEU THAT BAI,
     bao loi ngay "khong co layer shell" - vi bo dieu phoi man hinh dung
     cho kiosk (`cage`) la loai toi gian, khong cai dat giao thuc
     "wlr-layer-shell" ma cac ban phim ao he thong nay can (xac nhan bang
     `strings $(which cage) | grep layer_shell` - khong ra dong nao).

     NHUNG: mot khi da co CDP de tiem nut Ve Dashboard, cung CO THE dung
     chinh co che do de tiem mot ban phim ao dang HTML/JS THUAN (giong het
     cach vkeyboard.js lam tren trang cua minh) vao BEN TRONG trang dang
     mo - cach nay KHONG can layer-shell hay bat ky quyen he thong nao ca,
     vi no chi la DOM/JS binh thuong chay trong chinh trang do (nhu the la
     script cua trang tu viet ra). Day la ly do "khong co ban phim ao
     chung cho kiosk" (ket luan dung cho ban phim ao HE THONG) khac voi
     "khong the co ban phim ao tren trang khac" (sai - lam duoc bang cach
     nay).

     Gioi han that con lai: chi go duoc vao <input>/<textarea>/phan tu
     contenteditable tieu chuan. Dung "trinh dat gia tri goc" (native value
     setter) thay vi gan .value truc tiep de tuong thich voi cac trang
     dung framework kieu React (React ghi de setter mac dinh cua trinh
     duyet de theo doi thay doi - gan truc tiep se bi React "khong thay"
     thay doi). Cac o nhap dac biet phuc tap (vd trinh soan thao rich-text
     nhieu lop) co the khong go duoc day du - chua kiem chung tung truong
     hop cu the, se sua tiep neu gap.

Ca hai tinh nang duoc tiem CHUNG 1 lan qua `Page.addScriptToEvaluateOnNewDocument`
- lenh nay dang ky de Chromium TU DONG chay lai doan script moi khi co 1
tai lieu moi duoc tai (moi lan dieu huong), khong can script Python nay can
thiep lai tu lan thu hai tro di. Script Python chi con nhiem vu GIU KET NOI
WebSocket song (dang ky mat hieu luc neu ngat ket noi) va TU NOI LAI neu
Chromium khoi dong lai (kiosk restart = tien trinh Chromium moi = phai dang
ky lai tu dau).

Da kiem chung that (khong doan): tiem xong, dieu huong qua nhieu trang cuc
bo khac nhau va xac nhan nut/ban phim van con moi lan; tat/bat lai kiosk de
mo phong Chromium bi restart va xac nhan tu ket noi lai thanh cong.
"""
import json
import time
import urllib.error
import urllib.request

import websocket

CDP_BASE = "http://127.0.0.1:9222"
DASHBOARD_ORIGIN = "http://127.0.0.1:8880"

# Placeholder duoc thay the bang str.replace() o duoi - KHONG dung f-string/
# .format() cho toan bo khoi JS nay vi no co qua nhieu dau { } that su cua
# JavaScript, de nham voi cu phap the cho cua Python.
INJECT_JS_TEMPLATE = r"""
(function() {
  if (location.origin === "__DASHBOARD_ORIGIN__") return;   // trang cua minh, da co san moi thu
  if (window.__cpKioskHelper) return;
  window.__cpKioskHelper = true;

  function onReady(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  // ============================================================ Nut Ve Dashboard
  onReady(function () {
    var b = document.createElement("button");
    b.textContent = "🏠 Console Pi";
    b.type = "button";
    b.style.cssText = [
      "position:fixed", "left:10px", "top:10px", "z-index:2147483647",
      "background:#4CAF50", "color:#fff", "border:none", "border-radius:20px",
      "padding:9px 15px", "font-size:14px", "font-family:system-ui,Arial,sans-serif",
      "box-shadow:0 3px 14px rgba(0,0,0,.5)", "cursor:pointer",
      "touch-action:manipulation", "-webkit-user-select:none", "user-select:none",
      "opacity:0.88"
    ].join(";");
    b.addEventListener("pointerdown", function (ev) {
      ev.preventDefault();
      location.href = "__DASHBOARD_ORIGIN__/";
    });
    document.documentElement.appendChild(b);
  });

  // ============================================================ Ban phim ao
  // Ban sao rut gon cua nettools/static/vkeyboard.js, dieu chinh de go duoc
  // vao trang CUA NGUOI KHAC (dung native setter cho React, ho tro
  // contenteditable) thay vi trang cua chinh Console Pi.
  var kbTarget = null, shift = false, symbols = false, kb = null;

  var ROWS_LETTERS = [
    ["1","2","3","4","5","6","7","8","9","0"],
    ["q","w","e","r","t","y","u","i","o","p"],
    ["a","s","d","f","g","h","j","k","l"],
    ["z","x","c","v","b","n","m"]
  ];
  var ROWS_SYMBOLS = [
    ["!","@","#","$","%","^","&","*","(",")"],
    ["-","_","=","+","[","]","{","}","\\","|"],
    [";",":","'","\"",",",".","<",">"],
    ["/","?","~","`"]
  ];

  function isTypable(el) {
    if (!el || !el.tagName) return false;
    if (el.isContentEditable) return true;
    if (el.tagName === "TEXTAREA") return true;
    if (el.tagName !== "INPUT") return false;
    return ["text","search","email","url","tel","password","number"]
             .indexOf((el.type || "text").toLowerCase()) !== -1;
  }

  function nativeValueSetter(el) {
    var proto = el.tagName === "TEXTAREA"
      ? window.HTMLTextAreaElement.prototype
      : window.HTMLInputElement.prototype;
    var d = Object.getOwnPropertyDescriptor(proto, "value");
    return d && d.set;
  }

  function fireInput(el) {
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function fireEnterKey(el) {
    ["keydown", "keypress", "keyup"].forEach(function (type) {
      el.dispatchEvent(new KeyboardEvent(type, {
        key: "Enter", code: "Enter", keyCode: 13, which: 13, bubbles: true
      }));
    });
  }

  function insert(text) {
    if (!kbTarget) return;
    if (kbTarget.isContentEditable) {
      kbTarget.focus();
      document.execCommand("insertText", false, text);
      return;
    }
    var setter = nativeValueSetter(kbTarget);
    var s = kbTarget.selectionStart, e = kbTarget.selectionEnd;
    var val = kbTarget.value || "";
    var next;
    if (typeof s === "number" && typeof e === "number") {
      next = val.slice(0, s) + text + val.slice(e);
    } else {
      next = val + text;
    }
    if (setter) { setter.call(kbTarget, next); } else { kbTarget.value = next; }
    if (typeof s === "number") {
      try { kbTarget.selectionStart = kbTarget.selectionEnd = s + text.length; } catch (e2) {}
    }
    fireInput(kbTarget);
  }

  function backspace() {
    if (!kbTarget) return;
    if (kbTarget.isContentEditable) {
      kbTarget.focus();
      document.execCommand("delete", false);
      return;
    }
    var setter = nativeValueSetter(kbTarget);
    var s = kbTarget.selectionStart, e = kbTarget.selectionEnd;
    var val = kbTarget.value || "";
    var next; var pos;
    if (typeof s === "number" && s !== e) {
      next = val.slice(0, s) + val.slice(e); pos = s;
    } else if (typeof s === "number" && s > 0) {
      next = val.slice(0, s - 1) + val.slice(s); pos = s - 1;
    } else {
      next = val.slice(0, -1); pos = next.length;
    }
    if (setter) { setter.call(kbTarget, next); } else { kbTarget.value = next; }
    try { kbTarget.selectionStart = kbTarget.selectionEnd = pos; } catch (e3) {}
    fireInput(kbTarget);
  }

  function enter() {
    if (!kbTarget) return;
    if (kbTarget.tagName === "TEXTAREA") { insert("\n"); return; }
    fireEnterKey(kbTarget);
  }

  var css = [
    "#cpkbk{position:fixed!important;left:0!important;right:0!important;bottom:0!important;",
    "z-index:2147483647!important;background:#1c1f23!important;border-top:2px solid #4CAF50!important;",
    "padding:clamp(4px,1vh,9px) 8px!important;display:none;box-shadow:0 -6px 22px rgba(0,0,0,.7)!important;",
    "font-family:system-ui,Arial,sans-serif!important;}",
    "#cpkbk.on{display:block!important;}",
    "#cpkbk *{box-sizing:border-box!important;}",
    "#cpkbk .r{display:flex!important;justify-content:center!important;gap:6px!important;",
    "margin:clamp(3px,0.9vh,7px) 0!important;width:100%!important;}",
    "#cpkbk .r button{flex:0 0 calc((100% - 54px) / 10)!important;width:auto!important;",
    "min-width:0!important;max-width:none!important;height:clamp(40px,7.5vh,54px)!important;",
    "min-height:40px!important;margin:0!important;padding:0 4px!important;",
    "font-size:clamp(16px,3vh,20px)!important;line-height:1!important;background:#33383e!important;",
    "color:#e9edf2!important;border:1px solid #454b52!important;border-radius:7px!important;",
    "cursor:pointer!important;touch-action:manipulation!important;-webkit-user-select:none!important;",
    "user-select:none!important;font-family:inherit!important;}",
    "#cpkbk button:active{background:#4CAF50!important;color:#fff!important;}",
    "#cpkbk .r.last button{flex:1 1 0!important;}",
    "#cpkbk .r.last button.w{flex:1.4 1 0!important;font-size:clamp(13px,2.2vh,15px)!important;}",
    "#cpkbk .r.last button.sp{flex:4 1 0!important;font-size:clamp(14px,2.4vh,16px)!important;}",
    "#cpkbk button.act{background:#454b52!important;font-size:clamp(12px,2vh,14px)!important;}",
    "#cpkbk button.on{background:#4CAF50!important;color:#fff!important;}",
    "#cpkbk .bar{text-align:center!important;color:#93a0b0!important;font-size:11px!important;",
    "padding-bottom:3px!important;}"
  ].join("");

  function buildKb() {
    var style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);
    kb = document.createElement("div");
    kb.id = "cpkbk";
    document.documentElement.appendChild(kb);
  }

  function key(label, cls, fn) {
    var b = document.createElement("button");
    b.type = "button";
    b.textContent = label;
    if (cls) b.className = cls;
    var fired = false;
    b.addEventListener("pointerdown", function (ev) {
      ev.preventDefault();
      fired = true;
      setTimeout(fn, 0);
    });
    b.addEventListener("click", function (ev) {
      ev.preventDefault();
      if (!fired) setTimeout(fn, 0);
      fired = false;
    });
    return b;
  }

  function renderKb() {
    // KHONG duoc dung kb.innerHTML = "" - LOI THAT DA TIM RA (khong doan):
    // YouTube ep chinh sach Trusted Types (CSP "require-trusted-types-for
    // 'script'"), chan TUYET DOI moi gan .innerHTML bang chuoi thuong (ke
    // ca chuoi rong) - nem TypeError ngay lap tuc va lam dut ca ham nay
    // giua chung, khien ban phim khong bao gio kip hien len
    // (kb.classList.add("on") nam sau doan bi nem loi nen khong chay toi).
    // Dung vong lap xoa tung con bang removeChild - la DOM API an toan,
    // khong bi Trusted Types dong toi.
    while (kb.firstChild) kb.removeChild(kb.firstChild);
    var bar = document.createElement("div");
    bar.className = "bar";
    bar.textContent = "⌨ Ban phim ao Console Pi";
    kb.appendChild(bar);

    (symbols ? ROWS_SYMBOLS : ROWS_LETTERS).forEach(function (row) {
      var r = document.createElement("div");
      r.className = "r";
      row.forEach(function (k) {
        var lb = (!symbols && shift) ? k.toUpperCase() : k;
        r.appendChild(key(lb, "", function () {
          insert(lb);
          if (shift && !symbols) { shift = false; renderKb(); }
        }));
      });
      kb.appendChild(r);
    });

    var last = document.createElement("div");
    last.className = "r last";
    last.appendChild(key(symbols ? "ABC" : "?123", "w act" + (symbols ? " on" : ""),
                         function () { symbols = !symbols; renderKb(); }));
    if (!symbols) {
      last.appendChild(key("⇧", "w act" + (shift ? " on" : ""),
                           function () { shift = !shift; renderKb(); }));
    }
    last.appendChild(key(".", "", function () { insert("."); }));
    last.appendChild(key("Space", "sp", function () { insert(" "); }));
    last.appendChild(key("⌫", "w act", backspace));
    last.appendChild(key("↵", "w act", enter));
    kb.appendChild(last);
  }

  function showKb(el) {
    if (!kb) buildKb();
    kbTarget = el;
    shift = false; symbols = false;
    renderKb();
    kb.classList.add("on");
  }

  function hideKb() {
    if (kb) kb.classList.remove("on");
    kbTarget = null;
  }

  document.addEventListener("focusin", function (e) {
    if (isTypable(e.target)) showKb(e.target);
  });
  document.addEventListener("focusout", function () {
    setTimeout(function () {
      if (isTypable(document.activeElement)) return;
      hideKb();
    }, 150);
  });
})();
"""

INJECT_JS = INJECT_JS_TEMPLATE.replace("__DASHBOARD_ORIGIN__", DASHBOARD_ORIGIN)


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
        print("Da dang ky nut Ve Dashboard + ban phim ao, giu ket noi song.", flush=True)
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
