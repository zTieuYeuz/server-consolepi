"""Chay trong tien trinh rieng (CONSOLE_PI_DATA = bo cuc moi tam): cac muc sua 2.0.6 tu video (trung IP/MAC, ...)."""
import json
import os
import runpy
import time
import sys
import threading

os.environ.setdefault("CONSOLE_PI_LOG", __import__("tempfile").mkdtemp(prefix="cs-test-log-"))   # nhat ky cua lan chay nay vao thu muc tam, khong ghi /var/log that
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

# (f0) cung MAC nhung KHAC IP -> khong gop
DL.MAY.sua(lambda ds: ds.extend([
    {"id": "m-vpn-a", "ip": "10.8.7.1", "ten": "VPN-A", "mac": "00:0C:29:77:88:99", "the": ["tx"], "giam_sat": True},
    {"id": "m-vpn-b", "ip": "10.8.7.2", "ten": "", "mac": "", "giam_sat": True}]))
UBC._tu_dien("m-vpn-b", {"hostname": "VPN-B", "mac": "00:0c:29:77:88:99"})
kq["f_khac_ip_khong_gop"] = not DL.tim(DL.MAY.doc(), "m-vpn-a").get("an") and not DL.tim(DL.MAY.doc(), "m-vpn-b").get("the")

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

# (A1 / LOI-003) mat khau RustDesk KHONG nam trong HTML / JSON danh sach; chi tra khi bam Hien / Ket noi, co ghi nhat ky
import tempfile  # noqa: E402
from consolesystem.integrations import rustdesk_may_chu as RD  # noqa: E402
from consolesystem.features.uem import uem_rustdesk as URD  # noqa: E402
from ui import errlog as _el  # noqa: E402
_el.LOG_THAO_TAC = os.path.join(tempfile.mkdtemp(), "audit.log")
RD.trang_thai = lambda: {"da_cai": True, "dia_chi": {"id": "id.demo", "relay": "relay.demo"}}
_MKC, _MKM = "MkChungQa-7391", "MkMayRieng-5527"
DL.MAY.sua(lambda ds: ds.extend([
    {"id": "m-rd-co", "ip": "10.8.10.1", "ten": "PC-RD-CO", "giam_sat": True},
    {"id": "m-rd-chua", "ip": "10.8.10.2", "ten": "PC-RD-CHUA", "giam_sat": True}]))
_cfg = RD.doc_cfg(); _cfg["mk_chung"] = _MKC; _cfg["may"]["m-rd-co"] = {"id": "123456789", "mk": _MKM, "dong_bo": True}; RD.luu_cfg(_cfg)
_html = [c.get("/uem/may/m-rd-co/tu-xa", headers=H).get_data(as_text=True), c.get("/uem/may/m-rd-chua/tu-xa", headers=H).get_data(as_text=True),
         c.get("/rustdesk", headers=H).get_data(as_text=True)]
_json = [c.get(u, headers=H).get_data(as_text=True) for u in ("/rustdesk/api/thiet-bi", "/rustdesk/api/bang", "/rustdesk/api/trang-thai")]
kq["a1_html_khong_co_mat_khau"] = all(_MKC not in x and _MKM not in x for x in _html) and "123456789" in _html[0]
kq["a1_json_danh_sach_khong_co_mat_khau"] = all(_MKC not in x and _MKM not in x for x in _json)
kq["a1_form_chua_co_id_khong_dien_san"] = 'name="mk"' in _html[1] and "value=\"" + _MKC not in _html[1] and "Để trống = dùng mật khẩu chung" in _html[1]
kq["a1_khong_con_password_trong_href"] = "?password=" not in _html[0] and "data-mk" not in _html[0]
_r = c.post("/rustdesk/api/xem-mat-khau", json={"mid": "m-rd-co"}, headers=H)
kq["a1_hien_may_tra_dung"] = _r.get_json() == {"ok": True, "mk": _MKM} and "no-store" in _r.headers.get("Cache-Control", "")
kq["a1_hien_chung_tra_dung"] = c.post("/rustdesk/api/xem-mat-khau", json={"mid": "chung"}, headers=H).get_json()["mk"] == _MKC
kq["a1_may_khong_co_mat_khau_bi_tu_choi"] = c.post("/rustdesk/api/xem-mat-khau", json={"mid": "m-rd-chua"}, headers=H).get_json()["ok"] is False
_nk = open(_el.LOG_THAO_TAC, encoding="utf-8").read()
kq["a1_co_ghi_nhat_ky_khong_lo_mat_khau"] = "Xem mật khẩu RustDesk chung" in _nk and "Xem mật khẩu RustDesk trên máy" in _nk and _MKC not in _nk and _MKM not in _nk
# luu cho may chua co ID: de trong mat khau -> dung mat khau chung
c.post("/uem/may/m-rd-chua/rustdesk/luu", data={"id": "987654321", "mk": ""}, headers=H)
kq["a1_luu_de_trong_dung_mat_khau_chung"] = RD.doc_cfg()["may"].get("m-rd-chua", {}).get("mk") == _MKC

# (A10) mat khau WiFi AP + mat khau terminal: KHONG nam trong HTML, chi lay khi bam Hien, co ghi nhat ky
from consolesystem.features.network import network as _NW  # noqa: E402
from consolesystem.features.settings import settings as _ST  # noqa: E402
_MKAP, _MKTM = "MkWifiAp-6612", "MkTerm-9048"
_NW._doc_ap = lambda: ("ConsolePi-demo", _MKAP)
_ST.get_term_credential = lambda: ("console", _MKTM)
_h = [c.get("/wifi", headers=H).get_data(as_text=True), c.get("/settings", headers=H).get_data(as_text=True)]
kq["a10_html_khong_co_mat_khau_ap_terminal"] = all(_MKAP not in x and _MKTM not in x and "data-mk" not in x for x in _h) and "xem-mat-khau-ap" in _h[0] and "xem-mat-khau-terminal" in _h[1]
_r1 = c.post("/wifi/api/xem-mat-khau-ap", headers=H)
_r2 = c.post("/settings/api/xem-mat-khau-terminal", headers=H)
kq["a10_hien_tra_dung"] = _r1.get_json() == {"ok": True, "mk": _MKAP} and _r2.get_json() == {"ok": True, "mk": _MKTM} and "no-store" in _r1.headers.get("Cache-Control", "")
_nk = open(_el.LOG_THAO_TAC, encoding="utf-8").read()
kq["a10_co_ghi_nhat_ky_khong_lo_mat_khau"] = "Xem mật khẩu WiFi phát sóng (AP)" in _nk and "Xem mật khẩu terminal" in _nk and _MKAP not in _nk and _MKTM not in _nk and "POST /wifi/api" not in _nk

# (A10b) Key Windows trong kich ban cai: khong dien san ra trang, de trong = giu, tick Xoa = bo; netmiko/dot1x khong tra lai mat khau vua go
from werkzeug.datastructures import MultiDict  # noqa: E402
from consolesystem.features.deploy_os import dosui_kichban as _KB  # noqa: E402
_KEY = "AAAAA-BBBBB-CCCCC-DDDDD-EEEEE"
_d = {"os_ho": "windows", "ten_may": "PC1", "ten_may_che_do": "co_dinh", "mk_admin": "x", "product_key": _KEY, "bat_admin": True}
with app.test_request_context("/"):
    _loi1 = _KB._nhan_du_lieu_buoc(_d, 3, MultiDict({"ten_may": "PC1", "ten_may_che_do": "co_dinh", "product_key": ""}))
    kq["a10_key_de_trong_giu_nguyen"] = not _loi1 and _d["product_key"] == _KEY
    _tr = _KB._noi_dung_buoc("ma1", _d, 3)
    _tr = _tr if isinstance(_tr, str) else " ".join(str(x) for x in _tr)
    kq["a10_key_khong_dien_san_chi_goi_y"] = _KEY not in _tr and "AAAAA-BBBBB" not in _tr and "EEEEE" in _tr and "xoa_product_key" in _tr
    _loi2 = _KB._nhan_du_lieu_buoc(_d, 3, MultiDict({"ten_may": "PC1", "ten_may_che_do": "co_dinh", "product_key": "11111-22222-33333-44444-55555"}))
    kq["a10_key_nhap_moi_ghi_de"] = not _loi2 and _d["product_key"] == "11111-22222-33333-44444-55555"
    _loi3 = _KB._nhan_du_lieu_buoc(_d, 3, MultiDict({"ten_may": "PC1", "ten_may_che_do": "co_dinh", "product_key": "", "xoa_product_key": "1"}))
    kq["a10_key_xoa"] = not _loi3 and _d["product_key"] == ""
    _loi4 = _KB._nhan_du_lieu_buoc(_d, 3, MultiDict({"ten_may": "PC1", "ten_may_che_do": "co_dinh", "product_key": "ABC"}))
    kq["a10_key_sai_do_dai_van_bi_chan"] = bool(_loi4)
from nettools import netmiko_tool as _NM, dot1x as _D1  # noqa: E402
_NM.test_connection = lambda *a, **k: {"ok": True, "output": "ok", "error": ""}
_D1.run_eapol_test = lambda *a, **k: {"ok": True, "output": "EAP-SUCCESS", "error": ""}
_MKN = "MkThietBi-4417"
_t1 = c.post("/nettools/netmiko/test", data={"host": "10.0.0.1", "device_type": "cisco_ios", "port": "22", "username": "u", "password": _MKN, "test_cmd": "show version"}, headers=H).get_data(as_text=True)
_t2 = c.post("/nettools/netmiko/preview", data={"host": "10.0.0.1", "device_type": "cisco_ios", "port": "22", "username": "u", "password": _MKN, "commands": "conf t"}, headers=H).get_data(as_text=True)
_t3 = c.post("/nettools/dot1x", data={"radius_ip": "10.0.0.2", "radius_port": "1812", "radius_secret": _MKN + "S", "eap": "PEAP", "phase2": "MSCHAPV2", "identity": "u", "password": _MKN}, headers=H).get_data(as_text=True)
kq["a10_netmiko_dot1x_khong_tra_lai_mat_khau"] = all(_MKN not in x for x in (_t1, _t2, _t3)) and _MKN + "S" not in _t3 and 'name="radius_secret"' in _t3
kq["a10_netmiko_preview_nhap_lai_mat_khau"] = 'type="hidden" name="password"' not in _t2 and 'type="password" name="password"' in _t2 and len(_t1) > 1000 and len(_t3) > 1000

print("KETQUA " + json.dumps(kq))
