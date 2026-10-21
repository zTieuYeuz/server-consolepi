# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# Test DAI HAN cho he thong Nhat ky (chay sau moi lan sua giao dien/ha tang): python3 thu-nhat-ky.py
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# TEST DAI HAN cho he thong Nhat ky (19/10/2026): "log rat quan trong" - chay lai sau MOI lan sua giao dien/ ha tang.
# Dung thu muc log tam (khong dung /var/log that), flask test_client, khong can mang.
import sys, os, time, gzip, json, tempfile, logging, re
sys.path.insert(0, "/root/consolepi-toolkit/src")
dat = hong = 0
def kt(ten, ok, ct=""):
    global dat, hong
    print(("  OK   " if ok else "  HONG ") + ten + ("" if ok else "  -> " + str(ct)[:220]))
    if ok: dat += 1
    else: hong += 1
tmp = tempfile.mkdtemp(prefix="nk-")
from ui import errlog, logs
errlog.THU_MUC_LOG = tmp
errlog.LOG_FILE = os.path.join(tmp, "console-pi-errors.log")
errlog.LOG_THAO_TAC = os.path.join(tmp, "console-pi-audit.log")
logs.LOG_FILE = errlog.LOG_FILE; logs.LOG_THAO_TAC = errlog.LOG_THAO_TAC
def ghi(ten, noi, tuoi_ngay=0, gz=False):
    p = os.path.join(tmp, ten + (".gz" if gz else ""))
    (gzip.open if gz else open)(p, "wt", encoding="utf-8").write(noi)
    t = time.time() - tuoi_ngay * 86400; os.utime(p, (t, t))

# 1. ghi_loi ghi that, co traceback
try: 1 / 0
except Exception as e: errlog.ghi_loi("/thu/loi", "ZeroDivisionError: thu", ngoai_le=e)
x = open(errlog.LOG_FILE, encoding="utf-8").read()
kt("ghi_loi ghi dong co thoi gian + nguon + traceback", "[/thu/loi]" in x and "ZeroDivisionError" in x and "Traceback" in x)
# 2. logrotate: file hien tai rong, loi nam o .1 -> tab Loi ung dung PHAI van thay (loi that 19/10/2026)
os.replace(errlog.LOG_FILE, errlog.LOG_FILE + ".1"); open(errlog.LOG_FILE, "w").close()
kt("Loi trong ban .1 (sau logrotate) van hien o doc_nhat_ky", "[/thu/loi]" in errlog.doc_nhat_ky(300))
ghi("console-pi-errors.log.2", "2026-10-01 00:00:00 | [/cu/nho] loi cu 10 ngay\n", tuoi_ngay=10, gz=True)
kt("Ban log cu hon 7 ngay KHONG hien", "/cu/nho" not in errlog.doc_nhat_ky(300))
ghi("console-pi-errors.log.3", "2026-10-15 00:00:00 | [/gz/trong7] loi trong gz 3 ngay\n", tuoi_ngay=3, gz=True)
kt("Ban .gz trong 7 ngay doc duoc", "/gz/trong7" in errlog.doc_nhat_ky(300))
errlog.ghi_loi("/moi/nhat", "loi moi nhat")
dong = errlog.doc_nhat_ky(300).strip().splitlines()
kt("Thu tu: cu truoc, moi nhat o duoi cung", dong and "/moi/nhat" in dong[-1], dong[-2:])
# 3. so dong gioi han
for i in range(400): errlog.ghi_loi("/n", f"d{i}")
kt("Gioi han N dong cuoi", len(errlog.doc_nhat_ky(50).strip().splitlines()) == 50)
# 4. ghi_thao_tac: khong ghi mat khau, 1 dong 1 thao tac, ke ca khi nhieu dong trong noi dung
errlog.ghi_thao_tac("Đăng nhập thành công", "x\nINJECT dong gia", nguoi="admin", ip="10.0.0.5")
y = open(errlog.LOG_THAO_TAC, encoding="utf-8").read().splitlines()
kt("ghi_thao_tac: dung dinh dang nguoi@ip + hanh dong, khong tach dong gia", len(y) == 1 and "admin@10.0.0.5 | Đăng nhập thành công" in y[0], y)
# 5. Flask: trang /logs
from flask import Flask
app = Flask(__name__); app.secret_key = "t"
logs.register_logs(app)
c = app.test_client()
def lay(u): r = c.get(u); return r.status_code, r.get_data(as_text=True)
for tab in ("loi", "dichvu", "log", "thaotac", "sai-tab"):
    st, h = lay(f"/logs?tab={tab}")
    kt(f"/logs?tab={tab} tra 200", st == 200, st)
st, h = lay("/logs?tab=loi")
kt("Tab Loi ung dung hien noi dung nhat ky (300 dong cuoi)", "[/n]" in h)
st, h = lay("/logs?tab=thaotac")
kt("Tab Thao tac hien dong thao tac", "Đăng nhập thành công" in h and "INJECT" in h and "admin@10.0.0.5" in h)
# 6. nguon file + bo loc + tim khong dau
ghi("console-pi-selftest.log", "OK san sang\nLỗi: không thấy cổng ttyUSB0\nCảnh báo: ổ đĩa đầy 91%\nbinh thuong\n", tuoi_ngay=0)
ghi("console-pi-selftest.log.1", "dong cu hon trong 5 ngay co loi mang\n", tuoi_ngay=5)
st, h = lay("/logs?tab=log&nguon=console-pi-selftest.log&khoang=7d")
kt("Nguon file doc ca ban .1 trong 7 ngay", "trong 5 ngay" in h and "Lỗi: không thấy" in h)
st, h = lay("/logs?tab=log&nguon=console-pi-selftest.log&khoang=24h")
kt("Khoang 24h bo ban .1 (5 ngay)", "trong 5 ngay" not in h and "Lỗi: không thấy" in h)
st, h = lay("/logs?tab=log&nguon=console-pi-selftest.log&khoang=7d&tim=canh bao")
kt("Tim 'canh bao' (khong dau) ra 'Cảnh báo'", "Cảnh báo: ổ đĩa" in h and "binh thuong" not in h)
st, h = lay("/logs?tab=log&nguon=console-pi-selftest.log&khoang=7d&muc=loi")
kt("Muc 'Chi loi' loc dung", "Lỗi: không thấy" in h and "OK san sang" not in h)
st, h = lay("/logs?tab=log&nguon=console-pi-selftest.log&khoang=7d&muc=canh")
kt("Muc 'Canh bao tro len' gom ca loi + canh bao", "Cảnh báo: ổ đĩa" in h and "Lỗi: không thấy" in h and "binh thuong" not in h)
# 7. an toan tham so
st, h = lay("/logs?tab=log&nguon=../../etc/passwd&khoang=7d")
kt("nguon=../../etc/passwd bi bo (khong lo noi dung)", st == 200 and "root:x:0" not in h)
st, h = lay("/logs?tab=log&dv=ssh;id&khoang=zzz&muc=zzz")
kt("Tham so la: khong loi 500", st == 200, st)
st, h = lay("/logs?tab=log&tim=%3Cscript%3Ealert(1)%3C/script%3E&nguon=console-pi-selftest.log")
kt("Tu khoa chua <script> duoc thoat HTML", st == 200 and "<script>alert(1)</script>" not in h)
# 8. tai ve
r = c.get("/logs/tai?nguon=console-pi-selftest.log&khoang=7d&tim=loi")
t = r.get_data(as_text=True)
kt("/logs/tai: tep .txt, co dau # va dong khop", r.status_code == 200 and "attachment" in r.headers.get("Content-Disposition", "") and t.startswith("# Console System") and "Lỗi: không thấy" in t, t[:80])
# 9. tim nhanh khop tim cham (tuong duong)
dong = ["Đăng nhập thất bại", "Dang nhap that bai", "cai dat", "Cài đặt", "xyz", "Nguồn điện: tắt"]
co = logs._bo_loc(("DANG NHAP",)); kt("Tim khong dau + hoa thuong khop ca 2 kieu viet", [d for d in dong if co(d)] == dong[:2])
co = logs._bo_loc(("cai dat",)); kt("Tim 'cai dat' khop 'Cài đặt'", [d for d in dong if co(d)] == dong[2:4])
big = ["2026-10-19T09:00:00 host sshd[1]: Accepted password for admin from 10.0.0.%d" % (i % 255) for i in range(200000)]
t0 = time.time(); co = logs._bo_loc(("accepted",)); n = sum(1 for d in big if co(d)); dt = time.time() - t0
kt(f"Loc 200.000 dong ASCII duoi 1.5 giay ({dt:.2f}s)", n == 200000 and dt < 1.5, dt)
# 10. thu muc log trong: khong sap
for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))
st, h = lay("/logs?tab=loi"); kt("Chua co file log nao: tab van 200 + thong bao 'tot'", st == 200 and "chưa có lỗi nào" in h)
st, h = lay("/logs?tab=thaotac"); kt("Chua co thao tac: thong bao ro", st == 200 and "chưa có thao tác" in h)
# 11. ghi vao thu muc khong ghi duoc thi KHONG nem loi
errlog.LOG_FILE = "/proc/khong/ton/tai/x.log"; errlog.LOG_THAO_TAC = "/proc/khong/ton/tai/y.log"
try: errlog.ghi_loi("/x", "m"); errlog.ghi_thao_tac("a", "b", nguoi="u", ip="i"); kt("Khong ghi duoc file: im lang, khong sap", True)
except Exception as e: kt("Khong ghi duoc file: im lang, khong sap", False, e)
# 12. tu dong ghi thao tac POST: khong ghi mat khau
errlog.LOG_THAO_TAC = os.path.join(tmp, "console-pi-audit.log")
from flask import request as rq
app2 = Flask(__name__); app2.secret_key = "t"
@app2.route("/deployos/kichban/xoa", methods=["POST"])
def _x(): return "ok"
@app2.route("/settings/doi", methods=["POST"])
def _y(): return "ok"
@app2.route("/api/thu", methods=["POST"])
def _z(): return "ok"
@app2.after_request
def _a(r): errlog.ghi_thao_tac_tu_dong(rq, r); return r
c2 = app2.test_client()
c2.post("/deployos/kichban/xoa", data={"ten": "Cai-moi", "mat_khau": "BI-MAT-123", "token": "TOK"})
c2.post("/settings/doi", data={"password": "BI-MAT-456", "id": "7"})
c2.post("/api/thu", data={"ten": "khong-ghi"})
c2.get("/deployos/kichban/xoa")
au = open(errlog.LOG_THAO_TAC, encoding="utf-8").read() if os.path.exists(errlog.LOG_THAO_TAC) else ""
kt("POST duoc ghi (ten doi tuong), GET khong ghi", "POST /deployos/kichban/xoa | ten=Cai-moi" in au and "POST /settings/doi | id=7" in au and au.count("kichban/xoa") == 1, au)
kt("KHONG ghi mat khau / token", "BI-MAT" not in au and "TOK" not in au)
kt("POST /api/* khong ghi (nhieu, khong phai thao tac nguoi dung)", "khong-ghi" not in au)

# 13. Bo loc nhat ky truy cap (app.py): bo dong ON AO thanh cong, giu dong that (ke ca dong co ma mau ANSI)
src = open("/root/consolepi-toolkit/src/app.py", encoding="utf8").read()
a = src.index("class _LocTruyCap"); b = src.index('_logging.getLogger("werkzeug")')
ns = {"_logging": logging, "_re": re}; exec(src[a:b], ns)
fl = ns["_LocTruyCap"]()
def _r(m): return logging.LogRecord("werkzeug", 20, "x", 1, m, None, None)
CA = [('127.0.0.1 - - [x] "GET /api/suckhoe HTTP/1.1" 200 -', False), ('127.0.0.1 - - [x] "\x1b[36mGET /dashboard.js HTTP/1.1\x1b[0m" 304 -', False),
      ('127.0.0.1 - - [x] "GET /thuong-hieu/a.woff2 HTTP/1.1" 304 -', False), ('127.0.0.1 - - [x] "GET /phien/api/ds HTTP/1.1" 200 -', False),
      ('127.0.0.1 - - [x] "GET /deployos/kho/tien-do HTTP/1.1" 200 -', False), ('127.0.0.1 - - [x] "GET /api/suckhoe HTTP/1.1" 500 -', True),
      ('127.0.0.1 - - [x] "GET /nettools/ping HTTP/1.1" 200 -', True), ('127.0.0.1 - - [x] "POST /nettools/ping HTTP/1.1" 200 -', True),
      ('127.0.0.1 - - [x] "GET /missing HTTP/1.1" 404 -', True), ('Running on http://127.0.0.1:5000', True)]
loi = [m for m, ky in CA if fl.filter(_r(m)) != ky]
kt("Bo loc truy cap: bo on ao 2xx/3xx, giu trang/POST/loi 4xx-5xx (ke ca dong co ma mau)", not loi, loi)
print("KET QUA:", dat, "dat,", hong, "hong")
sys.exit(0 if not hong else 1)
