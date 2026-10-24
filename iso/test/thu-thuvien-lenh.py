# Test giao dien Thu vien lenh moi (danh sach + chi tiet): chon, tim, loc the, them, sua, nhan ban, xoa, bien {{..}}, an toan XSS.
# Dung du lieu thu, khoi phuc file thu vien sau khi xong.
import sys, time, json, shutil
sys.path.insert(0, "/root/dev-giaodien")
from cdp import Trinh
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5099"
LIB = "/var/lib/console-pi/command-library.json"
GOC = "/tmp/command-library.truoc-test.json"
DAT, HONG = [], []
def kt(ten, dk, ct=""):
    (DAT if dk else HONG).append(ten); print(("  OK   " if dk else "  HONG ") + ten + ("" if dk or not ct else f"  -> {ct}"), flush=True)
def so_muc(t): return t.js("document.querySelectorAll('#tv-list li button').length")
def tieu_de(t): return t.js("(document.querySelector('#tv-ct h2')||{}).textContent")
def cho(t, js, tg=4):
    het = time.time() + tg
    while time.time() < het:
        if t.js(js): return True
        time.sleep(0.15)
    return False
shutil.copy(GOC, LIB)
t = Trinh(cong=9341)
try:
    t.mo(BASE + "/healthz", cho=0.3); t.js("localStorage.setItem('cpvk_enabled','0')")
    for cd, nen in (("pc", "toi"), ("cu", "sang")):
        print(f"== {cd}/{nen}")
        shutil.copy(GOC, LIB)
        t.cookie("cs_che_do", cd); t.cookie("cs_nen", nen)
        t.mo(BASE + "/commands", cho=1.5)
        kt("danh sach co 5 tap lenh", so_muc(t) == 5, str(so_muc(t)))
        kt("tu chon san 1 tap lenh de xem", bool(tieu_de(t)))
        t.js("document.querySelectorAll('#tv-list li button')[2].click()"); time.sleep(0.4)
        kt("bam muc trong danh sach -> chi tiet doi", tieu_de(t) == t.js("document.querySelectorAll('#tv-list li button')[2].querySelector('b').textContent"))
        # tim kiem (khong dau)
        t.js("var i=document.querySelector('#tv-tim'); i.value='vlan'; i.dispatchEvent(new Event('input',{bubbles:true}))"); time.sleep(0.3)
        kt("tim 'vlan' -> chi con tap lenh co vlan", 0 < so_muc(t) < 5, str(so_muc(t)))
        t.js("var i=document.querySelector('#tv-tim'); i.value='cau hinh ip'; i.dispatchEvent(new Event('input',{bubbles:true}))"); time.sleep(0.3)
        kt("tim khong dau 'cau hinh ip' khop 'Cau hinh IP'", so_muc(t) == 1, str(so_muc(t)))
        t.js("var i=document.querySelector('#tv-tim'); i.value='zzzkhongco'; i.dispatchEvent(new Event('input',{bubbles:true}))"); time.sleep(0.3)
        kt("khong khop -> bao khong co", bool(t.js("(document.querySelector('.tv-trong')||{}).textContent")))
        t.js("document.querySelector('#tv-xoa').click()"); time.sleep(0.3)
        kt("nut xoa o tim -> du 5 muc", so_muc(t) == 5)
        # loc the
        t.js("[...document.querySelectorAll('#tv-the button')].find(b=>/^xem/.test(b.textContent)).click()"); time.sleep(0.3)
        kt("loc the 'xem' -> 3 muc", so_muc(t) == 3, str(so_muc(t)))
        t.js("document.querySelector('#tv-the button').click()"); time.sleep(0.3)
        kt("bam 'Tat ca' -> 5 muc", so_muc(t) == 5)
        # them moi voi bien {{..}} va ky tu dac biet (XSS)
        t.js("document.querySelector('#tv-moi').click()"); time.sleep(0.4)
        kt("Them moi mo bieu mau", "Thêm tập lệnh mới" in (tieu_de(t) or ""))
        t.js("""document.querySelector('#tv-name').value='Thu <img src=x onerror=window.__xss=1> moi';
                document.querySelector('#tv-desc').value='mo ta thu';
                document.querySelector('#tv-tags').value='thu, kiem-tra';
                document.querySelector('#tv-commands').value='ping {{dia chi}}\\nshow version <script>window.__xss=2</script>'""")
        t.js("document.querySelector('.tv-f button[type=submit]').click()"); time.sleep(1.5)
        kt("them xong: 6 muc", so_muc(t) == 6, str(so_muc(t)))
        kt("them xong: dang xem dung tap lenh vua them", "Thu <img" in (tieu_de(t) or ""), str(tieu_de(t)))
        kt("co thong bao da them", bool(t.js("(document.querySelector('.tv-thongbao.ok')||{}).textContent")))
        kt("bien {{dia chi}} duoc to noi bat", t.js("document.querySelectorAll('.tv-code i').length") == 1)
        kt("khong chay ma chen (XSS)", not t.js("window.__xss"))
        kt("khong sinh the img tu ten", t.js("document.querySelectorAll('#tv-ct img').length") == 0)
        # sua
        t.js("[...document.querySelectorAll('.tv-nut')].find(b=>/Sửa/.test(b.textContent)).click()"); time.sleep(0.4)
        t.js("document.querySelector('#tv-desc').value='mo ta da sua'")
        t.js("document.querySelector('.tv-f button[type=submit]').click()"); time.sleep(1.5)
        kt("sua xong: mo ta moi hien", "mo ta da sua" in (t.js("(document.querySelector('.tv-mo-ta')||{}).textContent") or ""))
        # nhan ban
        t.js("[...document.querySelectorAll('.tv-nut')].find(b=>/Nhân bản/.test(b.textContent)).click()"); time.sleep(0.4)
        kt("nhan ban mo bieu mau co san noi dung", "(bản sao)" in (t.js("document.querySelector('#tv-name').value") or "") and bool(t.js("document.querySelector('#tv-commands').value")))
        t.js("document.querySelector('.tv-f button[type=submit]').click()"); time.sleep(1.5)
        kt("nhan ban luu xong: 7 muc", so_muc(t) == 7, str(so_muc(t)))
        # xoa (confirm tu dong dong y)
        t.js("window.confirm=function(){return true}")
        t.js("[...document.querySelectorAll('.tv-nut')].find(b=>/Xóa/.test(b.textContent)).click()"); time.sleep(1.5)
        kt("xoa xong: 6 muc", so_muc(t) == 6, str(so_muc(t)))
        # du lieu file
        d = json.load(open(LIB)); kt("file luu dung 6 tap lenh", len(d) == 6, str(len(d)))
        # nut gui + lien ket phien
        t.mo(BASE + "/commands#1", cho=1.2)
        kt("link #1 mo dung tap lenh", bool(tieu_de(t)))
        kt("co nut 'Dung trong Phien ket noi' tro dung chi so", (t.js("(document.querySelector('a.tv-nut')||{}).getAttribute('href')") or "").startswith("/phien?lenh="))
finally:
    shutil.copy(GOC, LIB)
    try: t.dong()
    except Exception: pass
print(f"TONG: {len(DAT)} dat, {len(HONG)} hong")
sys.exit(1 if HONG else 0)
