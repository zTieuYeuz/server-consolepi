"""Chay trong tien trinh rieng (can CONSOLE_PI_DATA = bo cuc moi tam). In JSON ket qua. KHONG goi systemctl that."""
import io
import json
import os
import runpy
import subprocess
import sys
import threading

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC)
os.chdir(SRC)
_goc = threading.Thread.start
threading.Thread.start = lambda self: None if getattr(getattr(self, "_target", None), "__name__", "") in ("tu_dang_ky_nen", "_driver_nen", "vong") else _goc(self)
app = runpy.run_path(os.path.join(SRC, "app.py"), run_name="dev")["app"]
from ui import duongdan as DD, saoluu as SL, settings as ST  # noqa: E402

goi_lenh = []
subprocess.run = lambda *a, **k: goi_lenh.append(("run", a[0])) or subprocess.CompletedProcess(a[0], 0, "", "")      # noqa: E731
subprocess.Popen = lambda *a, **k: goi_lenh.append(("popen", a[0]))                                               # noqa: E731
SL.hau_khoi_phuc = lambda goc=None: ["gia lap"]
c = app.test_client()
H = {"X-ConsolePi-Local": "1"}
kq = {"bo_cuc_moi": DD.BO_CUC_MOI}
r = c.get("/settings", headers=H)
t = r.get_data(as_text=True)
kq["trang_co_the_moi"] = "Tải sao lưu toàn bộ" in t and r.status_code == 200
r = c.get("/settings/sao-luu?che_do=cauhinh", headers=H)
data = r.get_data()
kq["tai_ve_ok"] = r.status_code == 200 and "filename=" in r.headers.get("Content-Disposition", "") and len(data) > 100
open("/tmp/goi-web.tar.gz", "wb").write(data)
kq["goi_kiem_duoc"] = SL.kiem_goi("/tmp/goi-web.tar.gz")["che_do"]
r = c.post("/settings/nap-sao-luu", headers=H, data={"file": (io.BytesIO(data), "g.tar.gz")}, content_type="multipart/form-data")
t = r.get_data(as_text=True)
kq["tai_len_hop_le"] = "File hợp lệ" in t and "Xác nhận khôi phục" in t
import re
m = re.search(r'name="ten" value="([^"]+)"', t)
ten = m.group(1) if m else ""
# file hong
hong = bytearray(data)
hong[len(hong) // 2] ^= 0xFF
r = c.post("/settings/nap-sao-luu", headers=H, data={"file": (io.BytesIO(bytes(hong)), "h.tar.gz")}, content_type="multipart/form-data")
kq["file_hong_bi_chan"] = "KHÔNG dùng được" in r.get_data(as_text=True)
kq["khong_con_file_hong"] = sorted(x for x in os.listdir(os.path.join(DD.GOC, "backups")) if x.startswith("tai-len-")) == [ten]
# pha hong du lieu roi khoi phuc
cfg = os.path.join(DD.GOC, "config", "config.json")
open(cfg, "w").write("HONG")
r = c.post("/settings/khoi-phuc", headers=H, data={"ten": ten})
t = r.get_data(as_text=True)
kq["khoi_phuc_ok"] = "Đã khôi phục" in t and open(cfg).read() != "HONG"
kq["da_hen_khoi_dong_lai"] = any(x[0] == "popen" for x in goi_lenh)
kq["file_tai_len_da_xoa"] = not os.path.exists(os.path.join(DD.GOC, "backups", ten))
r = c.post("/settings/khoi-phuc", headers=H, data={"ten": "../../etc/passwd"})
kq["ten_nguy_hiem_bi_chan"] = "Không tìm thấy" in r.get_data(as_text=True)
print("KETQUA " + json.dumps(kq))
