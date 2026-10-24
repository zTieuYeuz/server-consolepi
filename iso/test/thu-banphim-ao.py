# Ban phim ao phai hien o trang Terminal/SSH (thuoc tinh data-tmux-session tren the <body> that) va o trang Phien ket noi
# (thuoc tinh do JS dat SAU khi trang tai). Loi that 21/10/2026: anh Thoai cham vao Console/SSH tren man hinh cam ung khong thay ban phim.
import sys, time
sys.path.insert(0, "/root/dev-giaodien")
from cdp import Trinh
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5099"
DAT, HONG = [], []
def kt(ten, dk, ct=""):
    (DAT if dk else HONG).append(ten); print(("  OK   " if dk else "  HONG ") + ten + ("" if dk or not ct else f"  -> {ct}"), flush=True)
t = Trinh(cong=9336)
try:
    t.mo(BASE + "/healthz", cho=0.3)
    t.js("localStorage.setItem('cpvk_enabled','1')")
    for duong in ("/terminal", "/ssh"):
        t.mo(BASE + duong, cho=1.5)
        kt(duong + ": the body that co data-tmux-session", bool(t.js("!!document.body.getAttribute('data-tmux-session')")))
        kt(duong + ": ban phim ao hien san", bool(t.js("(function(){var k=document.querySelector('#cpvk'); return !!(k && k.classList.contains('on'))})()")))
    t.mo(BASE + "/phien", cho=1.5)
    kt("/phien: chua mo phien thi chua co ban phim", not t.js("document.body.hasAttribute('data-tmux-session')"))
    t.js("document.body.setAttribute('data-tmux-session','console-thu')"); time.sleep(0.6)
    kt("/phien: mo phien (JS dat thuoc tinh sau) -> ban phim hien", bool(t.js("(function(){var k=document.querySelector('#cpvk'); return !!(k && k.classList.contains('on'))})()")),
       str(t.js("document.querySelector('[id*=vk]') && document.querySelector('[id*=vk]').outerHTML.slice(0,80)")))
    t.js("document.body.removeAttribute('data-tmux-session')"); time.sleep(0.6)
    kt("/phien: dong het phien -> ban phim an", not t.js("(function(){var k=document.querySelector('#cpvk'); return !!(k && k.classList.contains('on'))})()"))
    # --- ban phim khong duoc che khung terminal; cham vao terminal thi hien lai (anh Thoai 21/10/2026, lan 2) ---
    for cd in ("pc", "cu"):
        t.cookie("cs_che_do", cd)
        for duong in ("/terminal", "/ssh"):
            t.mo(BASE + duong, cho=1.8)
            g = t.js("(function(){var f=document.querySelector('iframe'),k=document.querySelector('#cpvk');var a=f.getBoundingClientRect(),b=k.getBoundingClientRect();return [a.top,a.bottom,b.top,a.height,window.innerHeight,k.classList.contains('on')]})()")
            kt(f"{cd} {duong}: khung terminal nam tron tren ban phim", bool(g and g[5] and g[1] <= g[2] + 1 and g[3] >= 140 and g[0] >= 0), str(g))
            t.js("document.querySelector('#cpvk .cpclose').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}))"); time.sleep(0.5)
            g = t.js("(function(){var f=document.querySelector('iframe');return [document.querySelector('#cpvk').classList.contains('on'), f.style.height]})()")
            kt(f"{cd} {duong}: dong ban phim thi khung tra kich thuoc cu", g and (not g[0]) and "calc" in g[1], str(g))
            t.js("document.querySelector('iframe').focus()"); time.sleep(0.8)
            kt(f"{cd} {duong}: cham vao terminal thi ban phim hien lai", bool(t.js("document.querySelector('#cpvk').classList.contains('on')")))
        t.mo(BASE + "/phien", cho=1.5)
        t.js("document.body.setAttribute('data-tmux-session','console-thu')"); time.sleep(0.8)
        g = t.js("(function(){var f=document.querySelector('.ph-khung'),k=document.querySelector('#cpvk');var a=f.getBoundingClientRect(),b=k.getBoundingClientRect();return [a.bottom,b.top,a.height]})()")
        kt(f"{cd} /phien: khung phien nam tron tren ban phim", bool(g and g[0] <= g[1] + 1 and g[2] >= 140), str(g))
    # --- lan 3: cham lai o/terminal dang co tieu diem sau khi bam Dong phai hien lai ---
    t.cookie("cs_che_do", "cu")
    t.mo(BASE + "/ssh", cho=1.8)
    t.js("document.querySelector('#cpvk .cpclose').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}))"); time.sleep(0.5)
    t.js("document.querySelector('iframe').contentDocument.body.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}))"); time.sleep(0.6)
    kt("/ssh: dong ban phim roi cham lai trong khung terminal -> hien lai", bool(t.js("document.querySelector('#cpvk').classList.contains('on')")))
    t.mo(BASE + "/nettools/ping", cho=1.5)
    t.bam('input[name=host]'); time.sleep(0.6)
    kt("o nhap lieu: focus -> ban phim hien", bool(t.js("document.querySelector('#cpvk').classList.contains('on')")))
    t.js("document.querySelector('#cpvk .cpclose').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}))"); time.sleep(0.5)
    t.bam('input[name=host]'); time.sleep(0.6)
    kt("o nhap lieu: dong roi cham lai o dang chon -> hien lai", bool(t.js("document.querySelector('#cpvk').classList.contains('on')")))
finally:
    try: t.dong()
    except Exception: pass
print(f"DAT {len(DAT)} HONG {len(HONG)}")
sys.exit(1 if HONG else 0)
