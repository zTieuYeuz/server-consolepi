# Test nhom phien: tao nhom truoc, chon nhom khi luu phien, doi ten, xoa (phien khong bi xoa)  (19/10/2026)
import sys, time, json, urllib.request; sys.path.insert(0, "/root/dev-giaodien")
from cdp import Trinh
BASE = "http://127.0.0.1:5099"; dat = hong = 0
def kt(ten, ok, ct=""):
    global dat, hong
    print(("  OK   " if ok else "  HONG ") + ten + ("" if ok else "  -> " + str(ct)[:200]))
    if ok: dat += 1
    else: hong += 1
def api(u, du=None):
    r = urllib.request.Request(BASE + u, data=json.dumps(du).encode() if du is not None else None,
        headers={"Content-Type": "application/json", "X-Console-Pi": "fetch", "X-ConsolePi-Local": "1"})
    return json.load(urllib.request.urlopen(r))
# don truoc (neu lan truoc bo do)
for g in ("Nhóm Thử A", "Nhóm Thử B", "Nhóm Đổi Tên"): api("/phien/api/nhom/xoa", {"ten": g})
t = Trinh(cong=9531, cao=900)
try:
    t.cookie("cs_che_do", "pc"); t.mo(BASE + "/healthz", cho=.2); t.js("localStorage.clear();localStorage.setItem('cpvk_enabled','0')")
    t.mo(BASE + "/phien", cho=2.5)
    kt("Co nut Tao nhom", t.js("document.getElementById('nut-nhom').innerText.indexOf('Tạo nhóm')>=0"))
    t.bam('#nut-nhom'); time.sleep(.5)
    kt("Hop quan ly nhom mo", t.js("document.getElementById('md-nhom').classList.contains('on')"))
    t.js("document.getElementById('nh-ten').value='Nhóm Thử A';document.getElementById('nh-them').click()"); time.sleep(1)
    t.js("document.getElementById('nh-ten').value='Nhóm Thử B';document.getElementById('nh-them').click()"); time.sleep(1)
    kt("Hop liet ke 2 nhom moi", t.js("document.getElementById('nh-ds').innerText.indexOf('Nhóm Thử A')>=0 && document.getElementById('nh-ds').innerText.indexOf('Nhóm Thử B')>=0"))
    t.js("document.getElementById('nh-ten').value='Máy này';document.getElementById('nh-them').click()"); time.sleep(.8)
    kt("Ten nhom he thong bi tu choi", t.js("!document.getElementById('nh-loi').hidden"))
    t.js("document.getElementById('nh-ten').value='nhóm thử a';document.getElementById('nh-them').click()"); time.sleep(.8)
    kt("Trung ten (khac hoa thuong) khong tao them", len([g for g in api("/phien/api/ds")["nhom"] if g.lower() == "nhóm thử a"]) == 1)
    t.bam('#nh-dong'); time.sleep(.3)
    kt("Danh sach ben trai hien nhom trong", t.js("document.getElementById('ds').innerText.indexOf('Nhóm Thử A')>=0 && document.getElementById('ds').innerText.indexOf('Chưa có phiên')>=0"))
    # form phien: chon nhom tu danh sach tha xuong
    t.bam('#nut-moi'); time.sleep(.6)
    opts = t.js("[...document.querySelectorAll('#f-nhom option')].map(o=>o.textContent).join('|')")
    kt("Form phien co danh sach nhom tha xuong", "Nhóm Thử A" in opts and "Nhóm Thử B" in opts and "(Không nhóm)" in opts and "Tạo nhóm mới" in opts, opts)
    t.js("var f=document.getElementById('f-ten');f.value='Phien thu nhom';document.getElementById('f-host').value='10.254.254.1';"
         "var s=document.getElementById('f-nhom');s.value='Nhóm Thử B';s.dispatchEvent(new Event('change'))")
    t.js("document.getElementById('f-luu').click()"); time.sleep(1.2)
    ds = api("/phien/api/ds")
    p = next((x for x in ds["phien"] if x.get("ten") == "Phien thu nhom"), None)
    kt("Phien duoc luu vao dung nhom", bool(p) and p.get("nhom") == "Nhóm Thử B", p)
    kt("Dem phien trong nhom = 1", ds["nhom_dem"].get("Nhóm Thử B") == 1, ds.get("nhom_dem"))
    # tao nhom nhanh trong form
    t.mo(BASE + "/phien", cho=2); t.bam('#nut-moi'); time.sleep(.5)
    t.js("var s=document.getElementById('f-nhom');s.value='__moi__';s.dispatchEvent(new Event('change'))"); time.sleep(.4)
    kt("Chon '+ Tao nhom moi' hien o nhap", t.js("!document.getElementById('f-nhom-moi').hidden"))
    t.js("document.getElementById('f-nhom-ten').value='Nhóm Đổi Tên';document.getElementById('f-nhom-tao').click()"); time.sleep(1.2)
    kt("Tao nhom nhanh xong tu chon nhom do", t.js("document.getElementById('f-nhom').value") == "Nhóm Đổi Tên")
    t.js("document.getElementById('f-huy').click()")
    # doi ten + xoa qua API (kiem logic)
    r = api("/phien/api/nhom/doi-ten", {"cu": "Nhóm Thử B", "moi": "Nhóm Thử C"})
    ds = api("/phien/api/ds"); p = next(x for x in ds["phien"] if x.get("ten") == "Phien thu nhom")
    kt("Doi ten nhom cap nhat ca phien", r["ok"] and p["nhom"] == "Nhóm Thử C" and "Nhóm Thử B" not in ds["nhom"], (r, p.get("nhom")))
    r = api("/phien/api/nhom/xoa", {"ten": "Nhóm Thử C"})
    ds = api("/phien/api/ds"); p = next((x for x in ds["phien"] if x.get("ten") == "Phien thu nhom"), None)
    kt("Xoa nhom: phien con, chuyen ve khong nhom", r["ok"] and p and not p.get("nhom") and r["so_phien"] == 1, (r, p))
finally:
    # don dep
    try:
        ds = api("/phien/api/ds")
        for x in ds["phien"]:
            if x.get("ten") == "Phien thu nhom": api("/phien/api/xoa", {"ma": x["ma"]})
        for g in ("Nhóm Thử A", "Nhóm Thử B", "Nhóm Thử C", "Nhóm Đổi Tên"): api("/phien/api/nhom/xoa", {"ten": g})
    except Exception as e: print("don dep loi", e)
    t.dong()
print("KET QUA:", dat, "dat,", hong, "hong")
