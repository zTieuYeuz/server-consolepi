"""Tien trinh rieng (CONSOLE_PI_DATA = bo cuc moi tam): man hinh MAY BI KHOA qua Flask test client. In JSON ket qua."""
import json
import os
import runpy
import sys
import threading

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC)
os.chdir(SRC)
_goc = threading.Thread.start
threading.Thread.start = lambda self: None if getattr(getattr(self, "_target", None), "__name__", "") in ("tu_dang_ky_nen", "_driver_nen", "vong", "vong_kiem_tra_nen") else _goc(self)
app = runpy.run_path(os.path.join(SRC, "app.py"), run_name="dev")["app"]
from consolesystem.core import duongdan as DD  # noqa: E402
from consolesystem.core.capnhat import khoa as K, khoa_lenh as KL, may as M  # noqa: E402

H = {"X-ConsolePi-Local": "1"}
c = app.test_client()
moi = M.Moi()
kq = {"truoc_khi_khoa_vao_duoc": c.get("/settings", headers=H).status_code == 200}
kd = os.path.join(DD.GOC, "khoa-thu")
K.luu_cap_khoa(kd, "lenh-khoa", "mat-khau-test-12345", n=2 ** 14)
priv = K.doc_khoa_rieng(kd + "/lenh-khoa.khoa-rieng.json", "mat-khau-test-12345")
pub, _ = K.doc_khoa_cong_khai(kd + "/lenh-khoa.khoa-cong-khai.json")
idk = K.dau_van_tay(pub)
pb, ma = KL.tao_lenh_khoa(priv, idk, KL.token_bam("TOK"), 1)
secret = os.path.join(DD.GOC, "secrets", "flask-secret.key")
kq["co_secret"] = os.path.exists(secret)
KL.xu_ly_lenh(moi, [pb], [(idk, pub)], "TOK", [secret])
import time
time.sleep(2.2)                                                  # bo nho dem 2 giay cua cong khoa
r = c.get("/settings", headers=H)
kq["bi_chan_423"] = r.status_code == 423 and "Máy bị khóa" in r.get_data(as_text=True)
kq["secret_da_mat"] = not os.path.exists(secret)
kq["healthz_van_chay"] = c.get("/healthz").status_code == 200
r = c.post("/khoa-may", headers=H, data={"ma": "AAAA-AAAA-AAAA-AAAA-AAAA-AAAA-AAAA-AAAA"})
kq["ma_sai_van_khoa"] = r.status_code == 423 and "KHONG DUNG" in r.get_data(as_text=True)
r = c.post("/khoa-may", headers=H, data={"ma": ma})
kq["ma_dung_chuyen_huong"] = r.status_code == 302 and "/cap-nhat" in r.headers.get("Location", "")
kq["secret_tra_lai"] = os.path.exists(secret)
time.sleep(2.2)
kq["vao_lai_duoc"] = c.get("/settings", headers=H).status_code == 200
print("KETQUA " + json.dumps(kq))
