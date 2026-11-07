"""Chay trong tien trinh rieng (CONSOLE_PI_DATA = bo cuc moi tam): cac muc sua 2.0.6 tu video (trung IP/MAC, ...)."""
import json
import os
import runpy
import time
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
DL.MAY.sua(lambda ds: ds.extend([
    {"id": "m-s-cu", "ip": "10.8.8.6", "ten": "SONG", "mac": "00:0C:29:11:22:33", "giam_sat": True, "agent": {"serie": "abc", "luc_cuoi": time.time()}},
    {"id": "m-s-moi", "ip": "10.8.8.7", "ten": "BANSAO", "mac": "", "giam_sat": True}]))
UBC._tu_dien("m-s-moi", {"hostname": "BANSAO", "mac": "00:0C:29:11:22:33"})
kq["f_ban_cu_song_khong_gop"] = not DL.tim(DL.MAY.doc(), "m-s-cu").get("an")

# (l) Nguon dien: may khong phai Pi (khong co cam bien) -> khong co nut tat/khoi dong lai; Pi van co
from ui import health as HL  # noqa: E402
_goc_snap = HL.snapshot
HL.snapshot = lambda: dict(_goc_snap(), throttle=None)
t = c.get("/power", headers=H).get_data(as_text=True)
kq["l_khong_pi_an_nut"] = "Không áp dụng" in t and "/power/reboot" not in t and "/power/poweroff" not in t
HL.snapshot = lambda: dict(_goc_snap(), throttle={"now": [], "past": []})
t = c.get("/power", headers=H).get_data(as_text=True)
kq["l_pi_van_co_nut"] = "/power/reboot" in t and "/power/poweroff" in t
HL.snapshot = _goc_snap

# (m) tab Log: dung MOT input name=tim
t = c.get("/logs?tab=log&tim=abc", headers=H).get_data(as_text=True)
kq["m_mot_input_tim"] = t.count('name="tim"') == 1 and "nkGuiNguon" in t

# (n) Profile moi: Ap dung cho KHONG tick 'tat ca may'; luu khong tick thi van khong
r = c.post("/uem/profiles/tao", data={"ten": "PF thu 206"}, headers=H)
pid = r.headers["Location"].rsplit("/", 1)[-1]
t = c.get("/uem/profiles/" + pid, headers=H).get_data(as_text=True)
kq["n_mac_dinh_khong_tick_tat_ca"] = 'id="pf-tatca" checked' not in t and 'id="pf-tatca"' in t
kq["n_canh_bao_khi_bat_tat_ca"] = "áp dụng cho TẤT CẢ máy" in t

# (P2) bo loc an nhip agent o tab Thao tac / Log; khong ghi dong nhip vao nhat ky thao tac
kq["p2_nut_an_nhip"] = 'id="nk-nhip"' in c.get("/logs?tab=thaotac", headers=H).get_data(as_text=True) and 'id="nk-nhip"' not in c.get("/logs?tab=loi", headers=H).get_data(as_text=True)

# (P2) nhat ky Thao tac dien giai thanh cau cho thao tac tu xa
from ui import errlog as EL, uem_dulieu as UD  # noqa: E402
UD.ghi_tac_vu("m-moi", "tu_xa", "Dịch vụ Spooler: dừng", True, "")
UD.ghi_tac_vu("m-moi", "tu_xa", "Tải file C:\\a.txt", False, "khong doc duoc")
UD.ghi_tac_vu("m-moi", "profile", "PF: x", True, "")                      # nguon khac: khong ghi them
_nk = open(EL.LOG_THAO_TAC, encoding="utf-8").read()
kq["p2_cau_dich_vu"] = "Dịch vụ Spooler: dừng trên máy May demo: thành công" in _nk
kq["p2_cau_duyet_file_loi"] = "Tải file C:\\a.txt trên máy May demo: thất bại | khong doc duoc" in _nk
kq["p2_nguon_khac_khong_ghi"] = "PF: x" not in _nk

# (P2) loc RAM / loai o o danh sach May tinh
DL.MAY.sua(lambda ds: ds.append({"id": "m-ram", "ip": "10.8.9.1", "ten": "PC-RAM6", "giam_sat": True, "agent": {"serie": "abc", "luc_cuoi": time.time()},
                                 "bao_cao": {"computer": {"memory": "6 GB", "manufacturer": "Dell", "model": "X"},
                                             "physicaldisks": [{"device_id": "d0", "model": "Samsung SSD 860", "serial_number": "1", "size_in_units": "256 GB", "media_type": "SSD"}]}}))
t = c.get("/uem/may", headers=H).get_data(as_text=True)
kq["p2_loc_ram_loai_o"] = 'data-ram="lt8|lt16"' in t and 'data-dia="SSD"' in t and 'data-k="ram"' in t and 'data-k="dia"' in t

# (P2) trang Bao mat: loc may co van de, nhan BitLocker, nut lam moi, cot bao cao luc
DL.MAY.sua(lambda ds: ds.extend([
    {"id": "m-tot", "ip": "10.8.9.2", "ten": "PC-TOT", "giam_sat": True, "bao_cao_luc": time.time(), "bao_cao": {
        "antivirus": {"name": "Defender", "is_active": True, "is_updated": True}, "firewall": [{"ten": "Domain", "bat": True}], "smb1": "Disabled",
        "logicaldisks": [{"label": "C:", "bitlocker_status": "Unknown"}]}},
    {"id": "m-xau", "ip": "10.8.9.3", "ten": "PC-XAU", "giam_sat": True, "bao_cao": {
        "antivirus": {"name": "Defender", "is_active": True, "is_updated": True}, "firewall": [{"ten": "Private", "bat": False}], "smb1": "Disabled",
        "logicaldisks": [{"label": "C:", "bitlocker_status": "Unencrypted"}]}}]))
t = c.get("/uem/bao-mat", headers=H).get_data(as_text=True)
kq["p2_bm_loc_van_de"] = 'data-k="vd"' in t and "Chỉ máy có vấn đề" in t and "Tường lửa tắt: Private" in t
import re as _re  # noqa: E402
_hang = {m_.group(1): m_.group(0) for m_ in _re.finditer(r'<tr data-t="([^"]*)" data-vd="[^"]*">.*?</tr>', t, _re.S)}
kq["p2_bm_vd_dung_may"] = any('data-vd="1"' in v and "pc-xau" in k for k, v in _hang.items()) and any('data-vd=""' in v and "pc-tot" in k for k, v in _hang.items())
kq["p2_bm_bitlocker_nhan"] = "Chưa bật" in t and "Không hỗ trợ / không đọc được" in t
_da_xep = []
UBC.chay_nen = lambda i: _da_xep.append(i) or True        # khong that su lay bao cao (cho agent timeout)
kq["p2_bm_lam_moi"] = ("/uem/bao-mat/lam-moi" in t and "Báo cáo lúc" in t and c.post("/uem/bao-mat/lam-moi", headers=H).status_code == 302)

kq["p2_bm_lam_moi_xep_lich"] = len(_da_xep) > 0 and "m-ram" in _da_xep

print("KETQUA " + json.dumps(kq))
