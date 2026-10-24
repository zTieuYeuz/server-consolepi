# Test giao dien Nhat ky moi (bo xem chung): cac tab, tim khong dau, chip muc/thoi gian, dao thu tu, chi tiet, gop dong lap, XSS.
import sys, time, shutil, os
sys.path.insert(0, "/root/dev-giaodien")
from cdp import Trinh
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5099"
AUD = "/var/log/console-pi-audit.log"; ERR = "/var/log/console-pi-errors.log"
for p in (AUD, ERR): shutil.copy(p, "/tmp/" + os.path.basename(p) + ".truoc-test")
DAT, HONG = [], []
def kt(ten, dk, ct=""):
    (DAT if dk else HONG).append(ten); print(("  OK   " if dk else "  HONG ") + ten + ("" if dk or not ct else f"  -> {ct}"), flush=True)
now = time.strftime("%Y-%m-%d %H:%M:%S")
with open(AUD, "a") as f:
    for _ in range(3): f.write(f"{now} | admin@10.9.9.9 | POST /commands/delete | ten=Thu-lap\n")
    f.write(f"{now} | admin@10.9.9.9 | dang nhap THAT BAI | ten=<img src=x onerror=window.__xss=1>\n")
    f.write(f"{now} | admin@10.9.9.9 | POST /deployos/kichban/xoa | ten=Cài đặt Kế toán\n")
with open(ERR, "a") as f:
    f.write(f"{now} | [/thu/nhat-ky] ValueError: gia tri sai\nTraceback (most recent call last):\n  File \"x.py\", line 1, in <module>\nValueError: gia tri sai\n")
def so_h(t): return t.js("document.querySelectorAll('.nk-h2').length")
def nhap(t, v):
    t.js("var i=document.querySelector('#nk-tim'); i.value=%r; i.dispatchEvent(new Event('input',{bubbles:true}))" % v); time.sleep(0.3)
t = Trinh(cong=9343)
try:
    t.mo(BASE + "/healthz", cho=0.3); t.js("localStorage.setItem('cpvk_enabled','0')")
    for cd, nen in (("pc", "toi"), ("cu", "sang")):
        print(f"== {cd}/{nen}"); t.cookie("cs_che_do", cd); t.cookie("cs_nen", nen)
        t.mo(BASE + "/logs?tab=thaotac", cho=1.8)
        kt("tab Thao tac co su kien", so_h(t) >= 3, str(so_h(t)))
        kt("3 dong giong het gop thanh x3", bool(t.js("[...document.querySelectorAll('.nk-x')].some(x=>x.textContent.indexOf('3')>=0)")))
        kt("ten thao tac doc duoc ('Xoa tap lenh')", bool(t.js("[...document.querySelectorAll('.nk-nd')].some(x=>x.textContent.indexOf('Xóa tập lệnh')===0)")))
        kt("ten kich ban co dau hien dung", bool(t.js("[...document.querySelectorAll('.nk-nd')].some(x=>x.textContent.indexOf('Cài đặt Kế toán')>=0)")))
        kt("khong chay ma chen (XSS)", not t.js("window.__xss") and t.js("document.querySelectorAll('.nk-ds img').length") == 0)
        kt("dong dang nhap that bai duoc danh dau canh bao", bool(t.js("[...document.querySelectorAll('.nk-h2.canh')].some(x=>x.textContent.indexOf('THAT BAI')>=0)")))
        n_all = so_h(t)
        nhap(t, "ke toan")
        kt("tim 'ke toan' (khong dau) khop 'Kế toán'", 1 <= so_h(t) < n_all, str(so_h(t)))
        kt("tu khoa duoc to sang", t.js("document.querySelectorAll('.nk-nd mark').length") >= 1)
        nhap(t, "zzzkhongco")
        kt("khong khop -> bao khong co", bool(t.js("(document.querySelector('.nk-rong')||{}).textContent")))
        t.js("document.querySelector('#nk-xoa').click()"); time.sleep(0.3)
        kt("nut xoa o tim tra lai du dong", so_h(t) == n_all)
        t.js("document.querySelector('#nk-muc button[data-v=canh]').click()"); time.sleep(0.3)
        kt("chip 'Canh bao' chi con dong canh bao", 1 <= so_h(t) < n_all, str(so_h(t)))
        t.js("document.querySelector('#nk-muc button[data-v=\"\"]').click()"); time.sleep(0.3)
        g1 = t.js("document.querySelector('.nk-h2 .nk-gio').textContent")
        t.js("document.querySelector('#nk-moi').click()"); time.sleep(0.3)
        kt("bam 'Moi nhat o tren' dao thu tu", t.js("document.querySelector('#nk-moi').classList.contains('on')") is False)
        t.js("document.querySelector('#nk-dong').click()"); time.sleep(0.3)
        kt("tat 'Xuong dong' them lop nk-wrap-off", bool(t.js("document.querySelector('#nk-ds').classList.contains('nk-wrap-off')")))
        t.mo(BASE + "/logs?tab=loi", cho=1.8)
        kt("tab Loi co traceback gap lai", bool(t.js("!!document.querySelector('.nk-h2.co-ct')")))
        t.js("document.querySelector('.nk-h2.co-ct').click()"); time.sleep(0.3)
        kt("bam vao dong mo chi tiet", bool(t.js("!!document.querySelector('.nk-ct')")))
        t.js("document.querySelector('.nk-h2.co-ct').click()"); time.sleep(0.3)
        kt("bam lan nua dong chi tiet", not t.js("!!document.querySelector('.nk-ct')"))
        t.js("document.querySelector('#nk-kh button[data-v=\"3600\"]').click()"); time.sleep(0.3)
        kt("chip '1 gio' loc theo thoi gian (loi cu 14/10 bi an)", t.js("[...document.querySelectorAll('.nk-nd')].every(x=>x.textContent.indexOf('JS_PHAN_TRANG')<0)"))
        t.mo(BASE + "/logs?tab=dichvu", cho=1.8)
        kt("tab Canh bao dich vu hien khung xem", bool(t.js("!!document.querySelector('#nk-ds')")))
        t.mo(BASE + "/logs?tab=log&khoang=1h", cho=2.5)
        kt("tab Log toan bo co su kien journal", so_h(t) > 0, str(so_h(t)))
        kt("o tim tab Log co form GET gui du bo loc", t.js("[...document.querySelectorAll('.nk-o input[type=hidden]')].map(i=>i.name).sort().join(',')") == "dv,khoang,muc,nguon,tab")
        for tab in ("loi", "thaotac", "dichvu", "log"):
            t.mo(BASE + "/logs/tai?tab=" + tab, cho=0.6)
        import urllib.request
        for tab in ("loi", "thaotac", "dichvu", "log"):
            tt = urllib.request.urlopen(BASE + "/logs/tai?tab=" + tab).read().decode()
            kt(f"tai ve tab {tab} co dong tieu de", tt.startswith("# Console System - nhat ky"))
finally:
    for p in (AUD, ERR): shutil.copy("/tmp/" + os.path.basename(p) + ".truoc-test", p)
    try: t.dong()
    except Exception: pass
print(f"TONG: {len(DAT)} dat, {len(HONG)} hong")
sys.exit(1 if HONG else 0)
