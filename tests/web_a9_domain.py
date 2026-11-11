"""A9 (2.0.6): trang thai gia nhap domain hien tren trang Tien trinh (xanh DA VAO DOMAIN / dai do + ma loi) - tien trinh rieng, bo cuc moi tam."""
import json
import os
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
c = app.test_client()
H = {"X-ConsolePi-Local": "1"}
kq = {}


def gui(duong, d, ip):
    return c.post("/api/tiendo/" + duong, data=json.dumps(d), content_type="application/json; charset=utf-8", headers=H, environ_overrides={"REMOTE_ADDR": ip})


gui("batdau", {"may": "PC-OK", "kichban": "KB", "buoc": ["Cài A", "Cài B"]}, "10.1.1.1")
gui("domain", {"may": "PC-OK", "trang_thai": "da_vao", "domain": "home.local"}, "10.1.1.1")
gui("batdau", {"may": "PC-SAI", "kichban": "KB", "buoc": ["Cài A"]}, "10.1.1.2")
gui("domain", {"may": "PC-SAI", "trang_thai": "loi", "domain": "home.local", "ma": "0x52e", "ghi_chu": "sai tài khoản hoặc mật khẩu gia nhập - sửa trong kịch bản"}, "10.1.1.2")
gui("batdau", {"may": "PC-KHONG", "kichban": "KB", "buoc": ["Cài A"]}, "10.1.1.3")
gui("domain", {"may": "PC-RAC", "trang_thai": "linh-tinh", "domain": "x"}, "10.1.1.4")
h = c.get("/api/tiendo/data", headers=H).get_json()["html"]


def khoi(ten):
    i = h.index('data-may="%s' % ten)
    j = h.find("<details", i + 10)
    return h[i: j if j > 0 else len(h)]


ok, sai, khong = khoi("PC-OK"), khoi("PC-SAI"), khoi("PC-KHONG")
kq["da_vao_domain_xanh"] = "ĐÃ VÀO DOMAIN home.local" in ok and "tt-dai-do" not in ok and "CHƯA VÀO" not in ok
kq["sai_mat_khau_dai_do_ma_loi"] = "tt-dai-do" in sai and "0x52e" in sai and "CHƯA VÀO DOMAIN" in sai and "sai tài khoản" in sai and "ĐÃ VÀO" not in sai
kq["khong_domain_khong_hien_gi"] = "tt-domain" not in khong and "tt-dai-do" not in khong
kq["trang_thai_la_bi_bo_qua"] = "PC-RAC" not in h
kq["trang_tien_trinh_mo_duoc"] = c.get("/deployos/tiendo", headers=H).status_code == 200
kq["html_thoat_ky_tu"] = True
gui("domain", {"may": "PC-OK", "trang_thai": "loi", "domain": "<script>x</script>", "ma": "0x54b", "ghi_chu": "<b>dns</b>"}, "10.1.1.1")
h2 = c.get("/api/tiendo/data", headers=H).get_json()["html"]
kq["html_thoat_ky_tu"] = "<script>x</script>" not in h2 and "0x54b" in h2
kq["lan_cuoi_thang"] = khoi_ok = "CHƯA VÀO DOMAIN" in h2[h2.index('data-may="PC-OK'):]
print("KETQUA " + json.dumps(kq, ensure_ascii=False))
