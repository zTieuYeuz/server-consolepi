#!/usr/bin/env python3
"""So sanh HANH VI (khong chi trang GET) giua hai ban ma: chay cung kich ban tuong tac (wizard, tao/xoa os/ung dung/font/driver,
tai len, kho...) qua Flask test client voi du lieu tam giong nhau, ghi (phuong thuc, duong dan, ma tra ve, vet noi dung da chuan hoa).
    so-sanh-hanh-vi.py THU_MUC_SRC FILE_RA.json        roi diff hai file ra (vd: ban cu o `git worktree` vs ban moi)."""
import hashlib
import io
import json
import os
import re
import runpy
import sys
import tempfile
import threading

SRC = os.path.abspath(sys.argv[1])
RA = os.path.abspath(sys.argv[2])      # truoc khi chdir
TMP = tempfile.mkdtemp(prefix="hv-")
os.environ["CONSOLE_PI_DATA"] = TMP
sys.path.insert(0, SRC)
os.chdir(SRC)
_goc = threading.Thread.start
threading.Thread.start = lambda self: None if getattr(getattr(self, "_target", None), "__name__", "") in ("tu_dang_ky_nen", "_driver_nen", "vong") else _goc(self)
app = runpy.run_path(os.path.join(SRC, "app.py"), run_name="dev")["app"]
c = app.test_client()
H = {"X-ConsolePi-Local": "1"}
LOG = []
THU_BODY = os.environ.get("HV_BODY")          # thu muc luu noi dung da chuan hoa de diff khi can
if THU_BODY:
    os.makedirs(THU_BODY, exist_ok=True)
RE = [(re.compile(r"(/|%2F)wizard(/|%2F)(?!bat-dau)[A-Za-z0-9_\-]{12,}"), r"\1wizard\2<W>"), (re.compile(r"(kichban(?:/|%2F)luu(?:/|%2F))[A-Za-z0-9_\-]{12,}"), r"\1<W>"), (re.compile(r"[0-9a-f]{32,}"), "<H>"), (re.compile(r"\b[0-9a-f]{10}\b"), "<ID>"), (re.compile(r"\d{4}-\d\d-\d\d[ T]\d\d:\d\d(:\d\d)?"), "<T>"),
      (re.compile(r"\d\d:\d\d:\d\d"), "<t>"), (re.compile(re.escape(TMP)), "<TMP>"), (re.compile(r"hv-[a-z0-9_]{8}"), "<TMP>")]


def chuan(b):
    t = b.decode("utf-8", "replace")
    for r, th in RE:
        t = r.sub(th, t)
    return t


def go(m, p, **kw):
    r = c.open(p, method=m, headers=H, follow_redirects=False, **kw)
    body = chuan(r.get_data())
    LOG.append({"m": m, "p": chuan(re.sub(r"[0-9a-f]{10,}", "<ID>", p).encode()), "s": r.status_code, "loc": chuan(re.sub(r"[0-9a-f]{8,}", "<ID>", r.headers.get("Location", "")).encode()),
                "n": len(body) if "hatang/chay" not in p else 0, "h": hashlib.sha1(body.encode()).hexdigest()[:12] if "hatang/chay" not in p else "~"})      # hatang/chay doc trang thai may that -> chi so ma tra ve
    if THU_BODY:
        open(os.path.join(THU_BODY, "%03d.txt" % len(LOG)), "w", encoding="utf-8").write(m + " " + p + "\n" + body)
    return r, body


def tep(ten, nd=b"x" * 64):
    return (io.BytesIO(nd), ten)


# ---- du lieu mau trong kho deploy
D = os.path.join(TMP, "deploy")
for sub in ("apps", "scripts", "ungdung/kiemtra", "os", "drivers", "fonts", "boot", "kichban"):
    os.makedirs(os.path.join(D, sub), exist_ok=True)
for os_id in ("windows_10_pro", "windows_11_pro"):                # anh gia: chi can co file boot.wim + install.wim
    os.makedirs(os.path.join(D, "os", os_id), exist_ok=True)
    for f in ("boot.wim", "install.wim"):
        open(os.path.join(D, "os", os_id, f), "wb").write(b"MSWIM\0\0\0" + b"w" * 4096)
    json.dump({"ten_hien_thi": os_id, "os_ho": "windows"}, open(os.path.join(D, "os", os_id, "_thongtin.json"), "w"))
for f, nd in (("apps/winrar.exe", b"MZ" + b"w" * 200), ("apps/vlc.exe", b"MZ" + b"v" * 200), ("scripts/kiem-tra.ps1", b"Write-Host ok"), ("scripts/kiem-tra.cmd", b"@echo ok"),
              ("ungdung/kiemtra/a.txt", b"a")):
    open(os.path.join(D, f), "wb").write(nd)

# ---- GET cac trang goc
for p in ("/deployos", "/deployos/kichban", "/deployos/os", "/deployos/drivers", "/deployos/ungdung", "/deployos/font", "/deployos/o-dia", "/deployos/kho", "/deployos/caidat",
          "/deployos/caidat/hatang", "/deployos/console", "/deployos/console/apps", "/deployos/console/scripts", "/deployos/thamso", "/deployos/tien-do", "/deployos/kichban/mau-csv"):
    go("GET", p)

# ---- wizard that: 3 kich ban
KB = {
    "T1": {2: {"os_id": "windows_10_pro"}, 3: {"ten_may": "T1-COBAN", "username": "nv", "password": "Mk@1234", "mui_gio": "Asia/Ho_Chi_Minh", "bat_admin": "1", "mk_admin": "Mk@1234"},
           4: {"o_dia_che_do": "tu_dong", "o_dia_so": "0"}, 5: {}, 6: {}},
    "T2": {2: {"os_id": "windows_10_pro"}, 3: {"ten_may": "T2-DAYDU", "username": "kt", "password": "Mk@1234", "mui_gio": "Asia/Ho_Chi_Minh", "ngon_ngu": "vi-VN", "bat_admin": "1", "mk_admin": "Mk@1234"},
           4: {"o_dia_che_do": "chia_tay", "o_dia_so": "0", "pv_nhan": ["EFI", "MSR", "Windows", "Data"], "pv_cd": ["260", "16", "40000", "con_lai"], "pv_fs": ["fat32", "msr", "ntfs", "ntfs"], "pv_gan": ["EFI", "-", "C:", "D:"]},
           5: {"app": ["winrar.exe", "vlc.exe"], "dich_winrar.exe": "may", "dich_vlc.exe": "nguoi_dung", "ungdung": ["kiemtra"], "dich_ud_kiemtra": "may"},
           6: {"script": ["kiem-tra.ps1", "kiem-tra.cmd"], "lenh_them": "echo them", "tuy_chon": ["rdp", "ping", "giao_dien_toi"], "go_app": ["Microsoft.BingWeather"]}},
    "T3": {2: {"os_id": "windows_11_pro"}, 3: {"ten_may": "T3-W11", "username": "gd", "password": "Mk@1234", "mui_gio": "Asia/Ho_Chi_Minh", "bat_admin": "1", "mk_admin": "Mk@1234"},
           4: {"o_dia_che_do": "tu_dong", "o_dia_so": "0"}, 5: {"app": ["winrar.exe"], "dich_winrar.exe": "may"}, 6: {"tuy_chon": ["tat_widgets"]}},
}
for ten, buoc in KB.items():
    r, _ = go("GET", "/deployos/wizard/bat-dau")
    m = re.search(r"/deployos/wizard/([^/]+)/", r.headers.get("Location", ""))
    ma = m.group(1) if m else "x"
    for b in sorted(buoc):
        go("POST", "/deployos/wizard/%s/%d" % (ma, b), data=dict(buoc[b], huong="tiep"))
    go("GET", "/deployos/wizard/%s/7" % ma)
    go("POST", "/deployos/kichban/luu/%s" % ma, data={"ten": ten})
for p in ("/deployos/kichban", "/deployos/kichban/sua/T2", "/deployos/kichban/mau-csv"):
    go("GET", p)
go("POST", "/deployos/kichban/xoa", data={"ten": "T3"})
go("GET", "/deployos/kichban")

# ---- he dieu hanh / driver / ung dung / font: tao, xem, tai len, xoa
go("POST", "/deployos/os/tao", data={"ten": "Win10 thu", "loai": "windows"})
go("GET", "/deployos/os")
go("POST", "/deployos/drivers/tao", data={"ten": "Dell thu"})
go("GET", "/deployos/drivers")
go("POST", "/deployos/ungdung/tao", data={"ten": "Bo cai thu"})
go("GET", "/deployos/ungdung")
go("POST", "/deployos/font/tao", data={"ten": "Font cong ty"})
go("GET", "/deployos/font")
go("POST", "/deployos/console/apps/len", data={"file": tep("moi.exe", b"MZ" + b"m" * 300)}, content_type="multipart/form-data")
go("POST", "/deployos/console/apps/thamso", data={"ten": "moi.exe", "tham_so": "/S"})
go("GET", "/deployos/console/apps")
go("POST", "/deployos/console/scripts/len", data={"file": tep("moi.ps1", b"Write-Host moi")}, content_type="multipart/form-data")
go("GET", "/deployos/console/scripts")
go("POST", "/deployos/console/file/len", data={"file": tep("boot.wim", b"WIM" * 50)}, content_type="multipart/form-data")
go("GET", "/deployos/console")
go("POST", "/deployos/console/apps/xoa", data={"ten": "moi.exe"})
go("POST", "/deployos/console/scripts/xoa", data={"ten": "moi.ps1"})
go("GET", "/deployos/console/apps")
go("GET", "/deployos/o-dia")
go("POST", "/deployos/o-dia/xoa-het")
go("GET", "/deployos/kho")
go("GET", "/deployos/caidat/hatang/chay")
go("GET", "/deployos/tien-do")
# cac trang chi tiet voi id da tao
for sec in ("os", "drivers", "ungdung", "font"):
    r, body = go("GET", "/deployos/" + sec)
    for mid in sorted(set(re.findall(r'/deployos/%s/([A-Za-z0-9_\-]+)' % sec, body)))[:3]:
        if mid not in ("tao", "xoa", "len", "tach", "cho-boot", "goi-pho-bien"):
            go("GET", "/deployos/%s/%s" % (sec, mid))
json.dump(LOG, open(RA, "w"), ensure_ascii=False, indent=0)
print(len(LOG), "tuong tac")
