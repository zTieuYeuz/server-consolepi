"""RBAC buoc 2 trong tien trinh rieng: moi route da khai; CHAN that theo vai tro (Van hanh/Chi xem/chua gan); cong khai + agent khong phien khong bi chan; cong tac CONSOLE_RBAC_GHI_NHAN."""
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


def khach(user):
    c = app.test_client()
    with c.session_transaction() as ss:
        ss["user"] = user
    return c


RB.dat_vai_tro("vh1", "van_hanh")
RB.dat_vai_tro("xem1", "chi_xem")
RB.dat_vai_tro("qt1", "quan_tri")
# 1) chua gan vai tro: bi chan ca xem lan ghi
c = khach("khongvaitro")
kq["chua_vai_tro_chan_xem"] = c.get("/logs").status_code == 403
kq["chua_vai_tro_chan_ghi"] = c.post("/ssh/xin", data={"may": "10.0.0.1:22"}).status_code == 403
kq["chua_vai_tro_json_403"] = c.get("/api/x", headers={"Accept": "application/json"}).status_code in (403, 404) and \
    c.post("/ssh/xin", headers={"Accept": "application/json"}).get_json().get("ok") is False
kq["da_ghi_nhan_su_kien"] = any(x["nguoi"] == "khongvaitro" and x["path"] == "/ssh/xin" for x in RB.su_kien_gan_day())
# 2) Van hanh: khong vao Cap nhat / Sao luu / Nguoi dung; nhung vao duoc muc khac
c = khach("vh1")
kq["van_hanh_khong_cap_nhat"] = c.get("/cap-nhat").status_code == 403
kq["van_hanh_khong_nguoi_dung"] = c.get("/nguoi-dung").status_code == 403
kq["van_hanh_vao_logs"] = c.get("/logs").status_code != 403
# 3) Chi xem: GET duoc, POST khong
c = khach("xem1")
kq["chi_xem_get"] = c.get("/logs").status_code != 403
kq["chi_xem_post_chan"] = c.post("/ssh/xin", data={"may": "10.0.0.1:22"}).status_code == 403
c = khach("qt1")
# 5) cong khai / agent khong co phien: khong bi chan
a = app.test_client()
kq["cong_khai_login"] = a.get("/login").status_code == 200
kq["healthz"] = a.get("/healthz").status_code == 200
kq["agent_khong_phien_khong_bi_rbac"] = a.get("/uem/agent/x").status_code != 403
# 6) cong tac quay ve ghi nhan
os.environ["CONSOLE_RBAC_GHI_NHAN"] = "1"
kq["cong_tac_ghi_nhan"] = khach("khongvaitro").get("/logs").status_code != 403
del os.environ["CONSOLE_RBAC_GHI_NHAN"]
print("KETQUA " + json.dumps(kq, ensure_ascii=False))
