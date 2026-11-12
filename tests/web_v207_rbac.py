"""RBAC buoc 1 trong tien trinh rieng: moi route da khai; ghi nhan KHONG chan (nguoi khong co vai tro van vao nhu cu); trang Nguoi dung chi cho Quan tri."""
import json
import os
import re
import runpy
import sys
import threading

os.environ.setdefault("CONSOLE_PI_LOG", __import__("tempfile").mkdtemp(prefix="cs-test-log-"))
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC)
os.chdir(SRC)
_goc = threading.Thread.start
threading.Thread.start = lambda self: None if getattr(getattr(self, "_target", None), "__name__", "") in ("tu_dang_ky_nen", "_driver_nen", "vong", "vong_kiem_tra_nen") else _goc(self)
app = runpy.run_path(os.path.join(SRC, "app.py"), run_name="dev")["app"]
from consolesystem.core import rbac as RB  # noqa: E402

kq = {}
chua = []
for rule in app.url_map.iter_rules():
    p = re.sub(r"<[^>]+>", "x", rule.rule)
    if not RB.la_cong_khai(p) and RB.dich_vu_cua(p) is None:
        chua.append(p)
kq["moi_route_da_khai"] = not chua or chua
c = app.test_client()
with c.session_transaction() as s:
    s["user"] = "khongvaitro"                                  # tai khoan thuong, KHONG sudo, KHONG co vai tro
r1 = c.get("/logs")
kq["ghi_nhan_khong_chan_xem"] = r1.status_code in (200, 302)
r2 = c.post("/ssh/xin", data={"may": "10.0.0.1:22"})
kq["ghi_nhan_khong_chan_ghi"] = r2.status_code != 403
kq["da_ghi_nhan_su_kien"] = any(x["nguoi"] == "khongvaitro" and x["path"] == "/ssh/xin" for x in RB.su_kien_gan_day())
r3 = c.get("/nguoi-dung")
kq["trang_nguoi_dung_chi_quan_tri"] = r3.status_code == 403
print("KETQUA " + json.dumps(kq, ensure_ascii=False))
