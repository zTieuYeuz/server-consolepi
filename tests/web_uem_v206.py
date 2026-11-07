"""Chay trong tien trinh rieng (CONSOLE_PI_DATA = bo cuc moi tam): cac muc sua 2.0.6 tu video (trung IP/MAC, ...)."""
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
from ui import tk_dulieu as DL, uem_baocao as UBC  # noqa: E402

c = app.test_client()
H = {"X-ConsolePi-Local": "1"}
kq = {}

# (e) ban ghi da xoa khoi quan ly (an) khong tinh la 'may khac dung IP nay'
DL.MAY.sua(lambda ds: ds.extend([
    {"id": "m-cu-an", "ip": "10.8.8.1", "ten": "PC-CU", "giam_sat": True, "an": True},
    {"id": "m-moi", "ip": "10.8.8.1", "ten": "PC-MOI", "giam_sat": True},
    {"id": "m-khac", "ip": "10.8.8.2", "ten": "PC-KHAC", "giam_sat": True}]))
c.post("/uem/may/m-moi/quan-ly", data={"ip": "10.8.8.1", "bi_danh": "May demo"}, headers=H)
t = c.get("/uem/may/m-moi/quan-ly", headers=H).get_data(as_text=True)
kq["e_sua_ten_khong_bi_chan"] = "Đã lưu." in t and "Đã có máy khác" not in t
c.post("/uem/may/m-moi/quan-ly", data={"ip": "10.8.8.2"}, headers=H)
t = c.get("/uem/may/m-moi/quan-ly", headers=H).get_data(as_text=True)
kq["e_trung_that_van_chan"] = "Đã có máy khác dùng IP này." in t

# (f) cai lai cung MAC -> gop vao ban ghi moi, ban cu an
DL.NHOM_MAY.sua(lambda ds: ds.append({"id": "g-f", "ten": "Nhom F", "may": ["m-f-cu", "m-khac"]}))
DL.MAY.sua(lambda ds: ds.extend([
    {"id": "m-f-cu", "ip": "10.8.8.5", "ten": "PC-DEMO-19", "mac": "00:0C:29:AA:BB:CC", "the": ["t1"], "ghi_chu": "ghi chu cu", "giam_sat": True},
    {"id": "m-f-moi", "ip": "10.8.8.5", "ten": "", "mac": "", "giam_sat": True}]))
UBC._tu_dien("m-f-moi", {"hostname": "PC-DEMO-32", "mac": "00-0c-29-aa-bb-cc"})
ds = {x["id"]: x for x in DL.MAY.doc()}
kq["f_ban_cu_an"] = ds["m-f-cu"].get("an") is True and ds["m-f-cu"].get("gop_vao") == "m-f-moi"
kq["f_chuyen_the_ghi_chu"] = ds["m-f-moi"].get("the") == ["t1"] and ds["m-f-moi"].get("ghi_chu") == "ghi chu cu"
kq["f_nhom_doi_sang_ban_moi"] = DL.tim(DL.NHOM_MAY.doc(), "g-f")["may"] == ["m-f-moi", "m-khac"]
kq["f_ban_moi_khong_an"] = not ds["m-f-moi"].get("an")
# ban cu con agent song -> khong gop
import time  # noqa: E402
DL.MAY.sua(lambda ds: ds.extend([
    {"id": "m-s-cu", "ip": "10.8.8.6", "ten": "SONG", "mac": "00:0C:29:11:22:33", "giam_sat": True, "agent": {"serie": "abc", "luc_cuoi": time.time()}},
    {"id": "m-s-moi", "ip": "10.8.8.7", "ten": "BANSAO", "mac": "", "giam_sat": True}]))
UBC._tu_dien("m-s-moi", {"hostname": "BANSAO", "mac": "00:0C:29:11:22:33"})
kq["f_ban_cu_song_khong_gop"] = not DL.tim(DL.MAY.doc(), "m-s-cu").get("an")

print("KETQUA " + json.dumps(kq))
