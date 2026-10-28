"""Chay trong tien trinh rieng (CONSOLE_PI_DATA = bo cuc moi tam): dong lenh/dich vu/tien trinh tu xa, xoa may khoi quan ly, xoa dong tien do trien khai."""
import base64
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
from ui import tk_dulieu as DL, uem_agent as UA, uem_ketnoi as UK  # noqa: E402

kich = []


class Luong:
    error = []


class Gia:
    def execute_ps(self, script):
        kich.append(script)
        if "Win32_Service" in script:
            return json.dumps([{"Name": "Spooler", "DisplayName": "Print Spooler", "State": "Running", "StartMode": "Auto", "Mota": "in"}]), Luong(), False
        if "Get-Process" in script:
            return json.dumps({"Id": 1234, "ProcessName": "notepad", "cpu": 1.5, "mem": 10.0, "tieude": "x"}), Luong(), False      # 1 phan tu -> dict
        if "RUSTDESK_MK_OK" in script:
            return "RUSTDESK_MK_OK\r\n", Luong(), False
        if "FromBase64String" in script:
            return "ket-qua-lenh\n", Luong(), False
        return "OK", Luong(), False


UK.ket_noi = lambda m, bat_buoc_winrm=False: (Gia(), "", "agent")
DL.MAY.sua(lambda ds: ds.extend([
    {"id": "m-agent", "ip": "10.9.9.1", "ten": "MAY-AGENT-A", "giam_sat": True, "agent": {"serie": "abc", "luc_cuoi": 1}},
    {"id": "m-thuong", "ip": "10.9.9.2", "ten": "MAY-THUONG-B", "giam_sat": True}]))
c = app.test_client()
H = {"X-ConsolePi-Local": "1"}
kq = {}


def post(url, j):
    return c.post(url, json=j, headers=H)


for tab in ("cli", "dich-vu", "tien-trinh", ""):
    kq["tab_" + (tab or "tq")] = c.get("/uem/may/m-agent/" + tab, headers=H).status_code == 200
kq["tab_trien_khai_chuyen"] = c.get("/uem/may/m-agent/trien-khai", headers=H).headers.get("Location", "").endswith("/uem/trien-khai")
r = post("/uem/may/m-agent/cli/chay", {"loai": "cmd", "lenh": "ipconfig /all"}).get_json()
kq["cli_ok"] = r["ok"] and "ket-qua-lenh" in r["out"] and "ipconfig" not in kich[-1]          # lenh di bang base64, khong noi vao script
kq["cli_trong"] = post("/uem/may/m-agent/cli/chay", {"loai": "ps", "lenh": "  "}).get_json()["ok"] is False
kq["cli_loai_la"] = post("/uem/may/m-agent/cli/chay", {"loai": "bash", "lenh": "ls"}).get_json()["ok"] is False
r = post("/uem/may/m-agent/dich-vu/api", {"viec": "ds"}).get_json()
kq["dv_ds"] = r["ok"] and r["ds"][0]["Name"] == "Spooler"
kq["dv_ten_xau"] = post("/uem/may/m-agent/dich-vu/api", {"viec": "dung", "ten": "x'; Remove-Item C:\\ -Recurse #"}).get_json()["ok"] is False
kq["dv_dung"] = post("/uem/may/m-agent/dich-vu/api", {"viec": "dung", "ten": "Spooler"}).get_json()["ok"] is True and "Stop-Service -Name 'Spooler'" in kich[-1]
kq["dv_kieu_la"] = post("/uem/may/m-agent/dich-vu/api", {"viec": "khoi_dong", "ten": "Spooler", "kieu": "xxx"}).get_json()["ok"] is False
r = post("/uem/may/m-agent/tien-trinh/api", {"viec": "ds"}).get_json()
kq["tt_ds_mot_phan_tu"] = r["ok"] and r["ds"][0]["Id"] == 1234
kq["tt_kill_he_thong"] = post("/uem/may/m-agent/tien-trinh/api", {"viec": "kill", "pid": 4}).get_json()["ok"] is False
kq["tt_kill_chuoi"] = post("/uem/may/m-agent/tien-trinh/api", {"viec": "kill", "pid": "1; calc"}).get_json()["ok"] is False
kq["tt_kill"] = post("/uem/may/m-agent/tien-trinh/api", {"viec": "kill", "pid": 1234}).get_json()["ok"] is True
t = c.get("/uem/may/m-agent/tac-vu", headers=H).get_data(as_text=True)
kq["ghi_tac_vu"] = "Stop" in t or "Dịch vụ Spooler" in t
# xoa may khoi quan ly
c.post("/uem/may/m-agent/xoa", headers=H)
c.post("/uem/may/m-thuong/xoa", headers=H)
ds = {x["id"]: x for x in DL.MAY.doc()}
kq["agent_van_con_ban_ghi"] = "m-agent" in ds and ds["m-agent"].get("an") is True
kq["may_thuong_xoa_han"] = "m-thuong" not in ds
kq["danh_sach_an"] = "MAY-AGENT-A" not in c.get("/uem/may", headers=H).get_data(as_text=True)
m = DL.tim(DL.MAY.doc(), "m-agent")
UA.xu_ly_nhip(m, {"ver": "cu", "host": "A"}, "10.9.9.1")
kq["tu_hien_lai"] = not DL.tim(DL.MAY.doc(), "m-agent").get("an")
# tien do trien khai: xoa dong xong/loi
DL.KICH_BAN.sua(lambda ds: ds.append({"id": "kb1", "ten": "kb", "buoc": []}))
DL.TRANG_THAI.sua(lambda tt: tt.update(kb1={"bat": False, "may": {"1.1.1.1": {"tt": "xong"}, "1.1.1.2": {"tt": "loi"}, "1.1.1.3": {"tt": "dang"}, "1.1.1.4": {"tt": "xong"}}}))
post("/deployos/trienkhai/tt/kb1/xoa", {"loai": "xong"})
con = set(DL.TRANG_THAI.doc()["kb1"]["may"])
kq["xoa_dong_xong"] = con == {"1.1.1.2", "1.1.1.3"}
post("/deployos/trienkhai/tt/kb1/xoa", {"loai": "ca-hai"})
kq["khong_dong_may_dang_chay"] = set(DL.TRANG_THAI.doc()["kb1"]["may"]) == {"1.1.1.3"}
kq["loai_la_400"] = post("/deployos/trienkhai/tt/kb1/xoa", {"loai": "x"}).status_code == 400
kq["script_winrm"] = c.get("/deployos/trienkhai/bat-winrm.ps1", headers=H).get_data(as_text=True).startswith("<#")
kq["sl_chan_doan"] = post("/uem/may/m-agent/sua-loi/chay", {"id": "in-chan-doan"}).get_json()["ok"] is True
kq["sl_id_la"] = post("/uem/may/m-agent/sua-loi/chay", {"id": "xx"}).get_json()["ok"] is False
kq["sl_tham_xau"] = post("/uem/may/m-agent/sua-loi/chay", {"id": "cs-go-share", "tham": {"ten": "x';calc"}}).get_json()["ok"] is False
kq["sl_duong_xau"] = post("/uem/may/m-agent/sua-loi/chay", {"id": "cs-tao-share", "tham": {"ten": "D", "duong": "D:\\a;calc", "nguoi": "Everyone"}}).get_json()["ok"] is False
kq["sl_tao_share"] = post("/uem/may/m-agent/sua-loi/chay", {"id": "cs-tao-share", "tham": {"ten": "DuLieu", "duong": "D:\\DuLieu", "nguoi": "Everyone"}}).get_json()["ok"] is True and "New-SmbShare -Name 'DuLieu'" in kich[-1]
kq["sl_tab"] = c.get("/uem/may/m-agent/sua-loi", headers=H).status_code == 200
from consolesystem.integrations import rustdesk_may_chu as RD  # noqa: E402
_gia = os.path.join(os.environ["CONSOLE_PI_DATA"], "rustdesk-gia.exe")
open(_gia, "wb").write(b"MZ-gia")
RD._exe_client = lambda: _gia
kq["rd_trang"] = c.get("/rustdesk", headers=H).status_code == 200
t = c.get("/rustdesk/api/trang-thai", headers=H).get_json()
kq["rd_tt_chua_cai"] = t["da_cai"] is False and t["ban"] == RD.VER_SERVER
kq["rd_host_xau"] = post("/rustdesk/api/cau-hinh", {"host": "a b;c"}).get_json()["ok"] is False
kq["rd_host_ok"] = post("/rustdesk/api/cau-hinh", {"host": "rd.example.com"}).get_json()["ok"] is True and RD.host_hieu_luc() == "rd.example.com"
kq["rd_script_chua_co_khoa"] = c.get("/rustdesk/Cai-RustDesk-ConsoleSystem.msi", headers=H).status_code == 409
sc = RD.script_client("abcdef123456", "rd.example.com", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
kq["rd_script"] = RD.SHA_CLIENT in sc and "--silent-install" in sc and "rd.example.com" in sc and "RUSTDESK_ID=" in sc
try:
    RD.script_client("x'; calc", "rd.example.com", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
    kq["rd_mk_xau"] = False
except RuntimeError:
    kq["rd_mk_xau"] = True
try:
    RD.script_client("abcdef123456", "rd.example.com", "k'; calc")
    kq["rd_khoa_xau"] = False
except RuntimeError:
    kq["rd_khoa_xau"] = True
kq["rd_hanh_dong_chua_cai"] = post("/rustdesk/api/hanh-dong", {"viec": "start"}).get_json()["ok"] is False
kq["rd_thiet_bi"] = c.get("/rustdesk/api/thiet-bi", headers=H).get_json()["ds"] == []
t = c.get("/uem/may/m-agent/tu-xa", headers=H).get_data(as_text=True)
kq["rd_the_chua_cai"] = "Điều khiển bằng RustDesk" in t and "Chưa cài máy chủ RustDesk" in t
c.post("/uem/may/m-agent/rustdesk/luu", data={"id": "123456789", "mk": "abc123"}, headers=H)
kq["rd_luu_tay"] = RD.doc_cfg()["may"].get("m-agent", {}).get("id") == "123456789"
c.post("/uem/may/m-agent/rustdesk/luu", data={"id": "12x", "mk": "a"}, headers=H)
kq["rd_luu_xau_bi_chan"] = RD.doc_cfg()["may"]["m-agent"]["id"] == "123456789"
import time as _t  # noqa: E402
kq["mk_chung_xau"] = post("/rustdesk/api/mat-khau", {"mk": "a'b;1234567"}).get_json()["ok"] is False
kq["mk_chung_ngan"] = post("/rustdesk/api/mat-khau", {"mk": "abc"}).get_json()["ok"] is False
_c = RD.doc_cfg()
_c["may"]["m-agent"] = {"id": "123456789", "mk": "cu-cu-cu-cu", "dong_bo": True}
RD.luu_cfg(_c)
kq["mk_chung_luu"] = post("/rustdesk/api/mat-khau", {"mk": "MatKhau#Chung1"}).get_json()["ok"] is True
for _ in range(30):
    if RD.doc_cfg()["may"]["m-agent"].get("mk") == "MatKhau#Chung1":
        break
    _t.sleep(0.2)
kq["mk_chung_day_xuong_may"] = RD.doc_cfg()["may"]["m-agent"].get("mk") == "MatKhau#Chung1" and RD.doc_cfg()["may"]["m-agent"].get("dong_bo") is True
kq["mk_chung_gui_dung_lenh"] = "--password 'MatKhau#Chung1'" in kich[-1]
d = c.get("/rustdesk/api/thiet-bi", headers=H).get_json()
kq["mk_chung_hien_thi"] = d["mk_chung"] == "MatKhau#Chung1" and d["may"][0]["dong_bo"] is True
K = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
kq["rd_relay_xau"] = post("/rustdesk/api/cau-hinh", {"host": "id.example.com", "relay": "a b"}).get_json()["ok"] is False
post("/rustdesk/api/cau-hinh", {"host": "id.example.com", "relay": ""})
kq["rd_relay_mac_dinh"] = RD.relay_hieu_luc() == "id.example.com"
post("/rustdesk/api/cau-hinh", {"host": "id.example.com", "relay": "relay.example.com"})
sc2 = RD.script_client("abcdef123456", khoa=K)
kq["rd_client_id_relay"] = ("custom-rendezvous-server = 'id.example.com'" in sc2 and "relay-server = 'relay.example.com'" in sc2
                            and "rendezvous_server = 'id.example.com:21116'" in sc2 and "allow-websocket = 'N'" in sc2 and "--password 'abcdef123456'" in sc2
                            and "AppData\\Roaming\\RustDesk\\config\\RustDesk2.toml" in sc2 and "'relay-server' = 'relay.example.com'" in sc2)
sc3 = RD.script_client("abcdef123456", khoa=K, url="http://10.0.0.1/tk/tai/x/rustdesk-1.4.exe", sha="b" * 64)
kq["rd_client_file_rieng"] = "http://10.0.0.1/tk/tai/x/rustdesk-1.4.exe" in sc3 and "b" * 64 in sc3 and RD.SHA_CLIENT not in sc3
kq["rd_client_msi"] = "msiexec.exe" in RD.script_client("abcdef123456", khoa=K, url="http://10.0.0.1/a/RustDesk.msi", sha="c" * 64)
try:
    RD.script_client("abcdef123456", khoa=K, url="http://x/a'; calc", sha="c" * 64)
    kq["rd_url_xau_bi_chan"] = False
except RuntimeError:
    kq["rd_url_xau_bi_chan"] = True
kq["rd_nhan_bo_cai"] = RD.la_bo_cai_rustdesk("rustdesk-1.4.2-x86_64.exe") and RD.la_bo_cai_rustdesk("RustDesk.msi") and not RD.la_bo_cai_rustdesk("chrome.exe")
from consolesystem.integrations import tk_dongco as DC  # noqa: E402
_kb = []
DC._chay_ps = lambda cc, sc: (_kb.append(sc) or ("RUSTDESK_ID=555666777\r\n", ""))
_rk = RD.khoa_cong_khai
RD.khoa_cong_khai = lambda: K
ok_b, tb_b = DC._BUOC["rustdesk"](None, "10.9.9.1", {"loai": "rustdesk", "ref": ""}, {"id": "m-buoc", "ip": "10.9.9.1"})
kq["tk_buoc_rustdesk"] = ok_b and "555666777" in tb_b and RD.doc_cfg()["may"]["m-buoc"]["id"] == "555666777" and "relay-server = 'relay.example.com'" in _kb[-1]
kq["tk_buoc_ten"] = DC.nhan_buoc({"loai": "rustdesk", "ref": ""}).startswith("Cài RustDesk")
kq["tk_buoc_mot_lan_theo_may_chu"] = DC.giai_buoc({"buoc": [{"loai": "rustdesk", "ref": ""}]})[0]["ref"].startswith("id.example.com|relay.example.com|")
# cong ngoai + file cai + kho
kq["rd_cong_trung_bi_chan"] = post("/rustdesk/api/cau-hinh", {"host": "rd.test.com", "cong_id": "1222", "cong_relay": "1221"}).get_json()["ok"] is False
kq["rd_cong_ngoai"] = post("/rustdesk/api/cau-hinh", {"host": "rd.test.com", "cong_id": "1222", "cong_relay": "1300"}).get_json()["ok"] is True
_dc = RD.dia_chi()
kq["rd_dia_chi_cong"] = _dc["id"] == "rd.test.com:1222" and _dc["relay"] == "rd.test.com:1300" and _dc["rv"] == "rd.test.com:1222"
sc4 = RD.script_client("abcdef123456", khoa=K)
kq["rd_client_cong_ngoai"] = ("custom-rendezvous-server = 'rd.test.com:1222'" in sc4 and "relay-server = 'rd.test.com:1300'" in sc4
                              and "rendezvous_server = 'rd.test.com:1222'" in sc4 and "--option custom-rendezvous-server 'rd.test.com:1222'" in sc4)
_c = RD.doc_cfg(); _c["mk_chung"] = ""; RD.luu_cfg(_c)
kq["rd_msi_can_mk"] = RD.cap_nhat_kho(cho=True)[0] is False and c.get("/rustdesk/Cai-RustDesk-ConsoleSystem.msi", headers=H).status_code == 409
_c = RD.doc_cfg(); _c["mk_chung"] = "MatKhau#Chung1"; RD.luu_cfg(_c)
ok_k, tb_k = RD.cap_nhat_kho(cho=True)
r_msi = c.get("/rustdesk/Cai-RustDesk-ConsoleSystem.msi", headers=H)
kq["rd_msi_tao"] = ok_k and RD.tep_kho_tt()["co"] and r_msi.status_code == 200 and r_msi.data[:4] == b"\xd0\xcf\x11\xe0"
_ps = RD.script_tep_cai()
kq["rd_msi_script"] = "rd.test.com:1222" in _ps and "--password 'MatKhau#Chung1'" in _ps and "$PSScriptRoot" in _ps and "Invoke-WebRequest" not in _ps
_skb = os.path.join(DC._DD.SCRIPTS_DIR, "thu-rd.ps1")
os.makedirs(DC._DD.SCRIPTS_DIR, exist_ok=True)
open(_skb, "w").write("'x'")
ok_s, tb_s = DC._b_script(None, "10.9.9.1", {"loai": "script", "ref": "thu-rd.ps1"}, {"id": "m-script", "ip": "10.9.9.1"})
kq["tk_script_ghi_id"] = ok_s and "555666777" in tb_s and RD.doc_cfg()["may"]["m-script"]["id"] == "555666777"
kq["rd_trang_buoc"] = all(x in c.get("/rustdesk", headers=H).get_data(as_text=True) for x in ("Thông tin kết nối ra Internet", "Cai-RustDesk-ConsoleSystem.msi", "Kết nối hỗ trợ từ xa"))
post("/rustdesk/api/cau-hinh", {"host": "id.example.com", "relay": "relay.example.com"})
RD.khoa_cong_khai = _rk
kich.clear()
_c = RD.doc_cfg(); _c["may"]["m-agent"] = {"id": "123456789", "mk": "MatKhau#Chung1", "dong_bo": True}; RD.luu_cfg(_c)
RD.khoa_cong_khai = lambda: "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
Gia_execute = Gia.execute_ps
Gia.execute_ps = lambda self, script: (kich.append(script) or "RUSTDESK_ID=987654321\r\nRUSTDESK_CFG_OK\r\n", Luong(), False) if "RUSTDESK_CFG_OK" in script else Gia_execute(self, script)
kq["rd_ap_cau_hinh_api"] = post("/rustdesk/api/ap-cau-hinh", {}).get_json()["ok"] is True
for _ in range(30):
    if "xong" in (c.get("/rustdesk/api/thiet-bi", headers=H).get_json()["dong_bo"]["tb"]):
        break
    _t.sleep(0.2)
kq["rd_ap_cau_hinh_ket_qua"] = "1 máy đã đổi" in c.get("/rustdesk/api/thiet-bi", headers=H).get_json()["dong_bo"]["tb"]
kq["rd_ap_cau_hinh_tung_nguoi"] = "C:\\Users" in kich[-1] and "RUSTDESK_CHUA_CAI" in kich[-1]
kq["rd_doi_may_chu_409"] = c.get("/rustdesk/doi-may-chu.ps1", headers=H).status_code in (200, 409)
_s = RD.script_cau_hinh_nguoi_dung("rd.example.com", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
kq["rd_doi_may_chu_script"] = "--option custom-rendezvous-server 'rd.example.com'" in _s and "--option relay-server 'rd.example.com'" in _s and "--option key" in _s
t = c.get("/rustdesk/api/trang-thai", headers=H).get_json()
kq["rd_tt_relay"] = t["relay_hieu_luc"] == "relay.example.com" and "api" not in t
_rd = c.get("/rustdesk", headers=H).get_data(as_text=True)
_rd = _rd[_rd.find('<div class="content">'):_rd.find("<script>window.__csGen=0;")]   # chi noi dung trang (khung chung co JS WebSocket dung chung)
kq["rd_trang_khong_con_web"] = all(x not in _rd for x in ("rustdesk-api", "WebSocket", "itserver"))
r_vnc = c.get("/rustdesk/vnc", headers=H).get_data(as_text=True)
kq["vnc_trang"] = all(x in r_vnc for x in ("Remote VNC", "Remote RustDesk", "Tải TightVNC 64-bit", "cm-vn", "Chọn tất cả"))
_dsv = c.get("/rustdesk/vnc/api/may", headers=H).get_json()["may"]
kq["vnc_chi_may_agent"] = [x["id"] for x in _dsv] == ["m-agent"]
kq["vnc_viec_la"] = post("/rustdesk/vnc/api/chay", {"viec": "xoa-het", "may": ["m-agent"]}).get_json()["ok"] is False
kq["vnc_may_la"] = post("/rustdesk/vnc/api/chay", {"viec": "kiem", "may": ["khong-co"]}).get_json()["ok"] is False
_j = post("/rustdesk/vnc/api/chay", {"viec": "kiem", "may": ["m-agent"]}).get_json()
for _ in range(50):
    _t2 = c.get("/rustdesk/vnc/api/tt/" + _j["ma"], headers=H).get_json()
    if _t2["xong"] == _t2["tong"]:
        break
    _t.sleep(0.1)
kq["vnc_chay_xong"] = _t2["tong"] == 1 and _t2["xong"] == 1 and _t2["kq"]["m-agent"]["ok"] is not None
kq["rd_5_tab"] = all(('data-buoc="%d"' % i) in c.get("/rustdesk", headers=H).get_data(as_text=True) for i in range(1, 6))
kq["tab_trien_khai"] = "Cài qua Agent (WinGet)" in c.get("/uem/trien-khai", headers=H).get_data(as_text=True) and "Cài qua Agent (WinGet)" in c.get("/deployos/trienkhai", headers=H).get_data(as_text=True)
_c = RD.doc_cfg(); _c["may"]["m-agent"] = {"id": "123456789", "mk": "MatKhau#Chung1", "dong_bo": True}; RD.luu_cfg(_c)
_b = c.get("/rustdesk/api/bang", headers=H).get_json()
kq["kn_bang"] = any(x["mid"] == "m-agent" and x["id"] == "123456789" and x["agent"] for x in _b["may"]) and "chua_gan" in _b
_hp = []
import ui.uem_agent as _UA  # noqa: E402
from consolesystem.integrations import rustdesk_giam_sat as GS  # noqa: E402
from consolesystem.features.uem import uem_rustdesk as URD  # noqa: E402
from consolesystem.features.uem import uem_trang_b as URB  # noqa: E402


def cho_kn(r):
    for _ in range(100):
        if r.get("xong"):
            return r
        _t.sleep(0.05)
        r = c.get("/rustdesk/api/ket-noi/" + r["ma"], headers=H).get_json()
    return r


_URL = "rustdesk://connection/new/123456789?password=MatKhau#Chung1"
kq["cd_mac_dinh"] = c.get("/rustdesk/api/cai-dat", headers=H).get_json()["che_do"] == "thong_bao"
r0 = post("/rustdesk/api/ket-noi", {"mid": "m-agent"}).get_json()
kq["kn_thong_bao"] = r0["ok"] and r0["xong"] and r0["url"] == _URL and bool(GS._CHO_TEN["123456789"][1])
kq["kn_may_la"] = post("/rustdesk/api/ket-noi", {"mid": "khong-co"}).get_json()["ok"] is False
kq["cd_sai"] = post("/rustdesk/api/cai-dat", {"che_do": "bay", "ghi_hinh_gb": 5}).get_json()["ok"] is False
kq["cd_gb_sai"] = post("/rustdesk/api/cai-dat", {"che_do": "xin_phep", "ghi_hinh_gb": 0}).get_json()["ok"] is False
kq["cd_luu"] = post("/rustdesk/api/cai-dat", {"che_do": "xin_phep", "ghi_hinh": False, "ghi_hinh_gb": 5}).get_json()["ok"] and GS.cai_dat()["che_do"] == "xin_phep"
_UA.con_song = lambda m: False
kq["xp_offline"] = post("/rustdesk/api/ket-noi", {"mid": "m-agent"}).get_json()["ok"] is False
_UA.con_song = lambda m: True
_UA.hoi_phep = lambda mid, tb, giay=40: (_hp.append((mid, tb, giay)) or "CHO_PHEP")
r1 = cho_kn(post("/rustdesk/api/ket-noi", {"mid": "m-agent"}).get_json())
kq["xp_dong_y"] = r1["ok"] and r1["url"] == _URL and _hp[0][2] == 300 and "xin quyền kết nối" in _hp[0][1] and "123456789" in GS._DUYET
kq["xp_nhip_duoc_phep"] = GS.nhip({"id": "123456789", "uuid": "u1", "conns": [5]}) == {}
_UA.hoi_phep = lambda mid, tb, giay=40: "TU_CHOI"
r2 = cho_kn(post("/rustdesk/api/ket-noi", {"mid": "m-agent"}).get_json())
kq["xp_tu_choi"] = r2["ok"] is False and not r2.get("url") and "từ chối" in r2["tb"]
_UA.hoi_phep = lambda mid, tb, giay=40: "HET_GIO"
kq["xp_het_gio"] = "5 phút" in cho_kn(post("/rustdesk/api/ket-noi", {"mid": "m-agent"}).get_json())["tb"]
GS._DUYET["123456789"]["luc"] -= 400                                   # het 5 phut, phien 5 van mo -> ket noi them van duoc (cung lan dong y)
kq["xp_phien_con_mo"] = GS.nhip({"id": "123456789", "uuid": "u1", "conns": [5, 6]}) == {}
kq["xp_ngat"] = GS.nhip({"id": "123456789", "uuid": "u1", "conns": [7]}) == {"disconnect": [7]}
kq["xp_ngat_lap"] = GS.nhip({"id": "123456789", "uuid": "u1", "conns": [7]}) == {"disconnect": [7]}
kq["xp_uuid_la"] = GS.nhip({"id": "123456789", "uuid": "KHAC", "conns": [9]}) == {}
kq["xp_id_xau"] = GS.nhip({"id": "../x", "conns": [1]}) == {}
kq["an_toan_thieu_uuid"] = GS.nhip({"id": "123456789", "conns": [1]}) == {}
kq["an_toan_id_la"] = GS.nhip({"id": "111222333", "uuid": "z", "conns": [1]}) == {} and "111222333" not in GS._TT
GS.nhip({"id": "123456789", "uuid": "u1", "conns": [5, 6]}, ip="10.0.0.5")
_n0 = sum(1 for _ in GS._doc_su_kien())
GS.kiem_toan({"id": "123456789", "conn_id": 50, "peer": ["1", "gia mao"], "type": 0})
GS.kiem_toan({"id": "123456789", "uuid": "u1", "conn_id": 51, "action": "new"}, ip="10.6.6.6")
kq["an_toan_kiem_toan_gia"] = sum(1 for _ in GS._doc_su_kien()) == _n0
_tb = []
GS.dang_ky_thong_bao(lambda rid, nd: _tb.append((rid, nd)))
GS.kiem_toan({"id": "123456789", "uuid": "u1", "conn_id": 8, "action": "new", "ip": "::ffff:1.2.3.4"})
GS.kiem_toan({"id": "123456789", "uuid": "u1", "conn_id": 8, "peer": ["555666777", "kythuat"], "type": 0})
GS.kiem_toan({"id": "123456789", "uuid": "u1", "conn_id": 8, "action": "close"})
kq["xp_khong_thong_bao"] = _tb == []
post("/rustdesk/api/cai-dat", {"che_do": "thong_bao", "ghi_hinh": False, "ghi_hinh_gb": 5})
GS.dat_cho_ten("123456789", "admin")
GS.kiem_toan({"id": "123456789", "uuid": "u1", "conn_id": 10, "peer": ["555666777", "kythuat"], "type": 1})
for _ in range(40):
    if _tb:
        break
    _t.sleep(0.05)
kq["tb_thong_bao"] = bool(_tb) and _tb[0][0] == "123456789" and "admin (quản trị Console System)" in _tb[0][1] and "truyền file" in _tb[0][1]
_ps = URD.ps_thong_bao("Ai đó's test")
kq["tb_ps"] = "WTSSendMessage" in _ps and "'Ai đó''s test'" in _ps and "$false" in _ps
ls = c.get("/rustdesk/api/lich-su", headers=H).get_json()["ds"]
_p8 = [x for x in ls if x["conn"] == 8]
kq["ls_phien"] = len(_p8) == 1 and _p8[0]["ip"] == "1.2.3.4" and _p8[0]["peer"] == "555666777" and _p8[0]["kq"] == "Đã vào" and _p8[0]["ket_thuc"] and _p8[0]["may"] == "MAY-AGENT-A"
kq["ls_ngat"] = any(x["conn"] == 7 and x["kq"].startswith("Bị ngắt") for x in ls)
kq["ls_cho_phep"] = any(x["conn"] == 5 and x["nguoi_console"] for x in ls)
kq["ls_console"] = any(x["loai"] == "Yêu cầu từ Console" and "từ chối" in x["kq"] for x in ls)
with open(GS._ls_file(), "a", encoding="utf-8") as _f:
    _f.write(json.dumps({"t": _t.time() - 91 * 86400, "loai": "kn_moi", "rid": "123456789", "conn": 99}) + "\n")
GS.don_lich_su()
kq["ls_90_ngay"] = not any(x["conn"] == 99 for x in GS.lich_su()) and any(x["conn"] == 8 for x in GS.lich_su())
# may chu HTTP (cong ngau nhien thay 21114)
import urllib.request as _ur  # noqa: E402
_srv = GS.ThreadingHTTPServer(("127.0.0.1", 0), GS._XuLy)
import threading as _th  # noqa: E402
_th.Thread(target=_srv.serve_forever, daemon=True).start()
_url0 = "http://127.0.0.1:%d" % _srv.server_address[1]
def _gui(duong, j):
    return _ur.build_opener(_ur.ProxyHandler({})).open(_ur.Request(_url0 + duong, data=json.dumps(j).encode(), method="POST"), timeout=5).read().decode()
post("/rustdesk/api/cai-dat", {"che_do": "xin_phep", "ghi_hinh": False, "ghi_hinh_gb": 5})
GS._DUYET.clear()
kq["http_nhip_ngat"] = json.loads(_gui("/api/heartbeat", {"id": "123456789", "uuid": "u1", "conns": [11]})) == {"disconnect": [11]}
kq["http_audit"] = _gui("/api/audit/conn", {"id": "123456789", "uuid": "u1", "conn_id": 12, "action": "new", "ip": "9.9.9.9"}) == ""
kq["http_sysinfo"] = _gui("/api/sysinfo", {"id": "123456789"}) == "SYSINFO_UPDATED"
_srv.shutdown()
# ghi hinh: lay ve tu may, khop phien, xoa cu khi vuot dung luong
_tenghi = "incoming_123456789_%s123_display0_vp9.webm" % _t.strftime("%Y%m%d%H%M%S", _t.localtime(_p8[0]["bat_dau"] + 5))
Gia_ps0 = Gia.execute_ps
Gia.execute_ps = lambda self, script: (kich.append(script) or ("GHI=%s|10\r\nGHI=..\\bad.exe|3\r\nGHI_XONG\r\n" % _tenghi), Luong(), False) if "GHI_XONG" in script else Gia_ps0(self, script)
_UA.Client.fetch = lambda self, src, dest: open(dest, "wb").write(b"0123456789")
kq["gh_lay_ve"] = URD.thu_ghi_hinh_may(DL.tim(DL.MAY.doc(), "m-agent")) == 1 and any("Remove-Item -LiteralPath" in x and _tenghi in x for x in kich)
Gia.execute_ps = Gia_ps0
ls = c.get("/rustdesk/api/lich-su", headers=H).get_json()["ds"]
kq["gh_khop_phien"] = any(x["may"] == "MAY-AGENT-A" and any(g["ten"] == _tenghi for g in x["ghi_hinh"]) for x in ls)   # cac phien gia cung giay: chi kiem gan dung may
kq["gh_chi_1_phien"] = sum(1 for x in ls for g in x["ghi_hinh"] if g["ten"] == _tenghi) == 1
kq["gh_xem"] = c.get("/rustdesk/ghi-hinh/m-agent/" + _tenghi, headers=H).status_code == 200
kq["gh_duong_xau"] = c.get("/rustdesk/ghi-hinh/m-agent/..%2Frustdesk.json", headers=H).status_code == 404 and GS.duong_ghi_hinh("..", "a.webm") is None
_cu = os.path.join(GS.thu_muc_ghi_hinh(), "m-agent", "incoming_1_20200101000000000_display0_vp9.webm")
open(_cu, "wb").write(b"x" * 10)
os.utime(_cu, (1, 1))
_cd0 = GS.cai_dat
GS.cai_dat = lambda: dict(_cd0(), ghi_hinh_gb=15 / 1024 ** 3)
kq["gh_xoa_cu"] = GS.don_ghi_hinh() == 1 and not os.path.exists(_cu) and bool(GS.duong_ghi_hinh("m-agent", _tenghi))
GS.cai_dat = _cd0
_cdtt = c.get("/rustdesk/api/cai-dat", headers=H).get_json()
kq["cd_tt"] = _cdtt["ghi_hinh_so"] == 1 and _cdtt["cong_api_ngoai"] == 21114 and "may_chu_api" in _cdtt
kq["gh_trong_script"] = "allow-auto-record-incoming = 'N'" in RD.script_client("abcdef123456", khoa=K)
post("/rustdesk/api/cai-dat", {"che_do": "thong_bao", "ghi_hinh": True, "ghi_hinh_gb": 5})
_sc = RD.script_client("abcdef123456", khoa=K)
kq["gh_bat_script"] = "allow-auto-record-incoming = 'Y'" in _sc and "--option allow-auto-record-incoming Y" in _sc and "'allow-auto-record-incoming' = 'Y'" in _sc
kq["giu_api_server"] = "(?m)^api-server = '([^']*)'" in _sc and "api-server = '\" + $api" in _sc
kq["gh_duyet_bo"] = "approve-mode = 'password'" in _sc and "click" not in _sc
kq["kn_gan_sai"] = post("/rustdesk/api/gan", {"id": "999999999", "mid": "m-agent"}).get_json()["ok"] is False
Gia.execute_ps = lambda self, script: (kich.append(script) or "RDK=OK|1.5.0+68|Running|id.example.com|relay.example.com|Y|163846525\r\n", Luong(), False) if "RDK=" in script else Gia_execute(self, script)
kt = post("/rustdesk/api/kiem-tra", {"mid": "m-agent"}).get_json()
kq["kn_kiem_tra"] = kt["ok"] and kt["kq"]["id"] == "163846525" and kt["kq"]["dich_vu"] == "Running" and kt["kq"]["dung_may_chu"] is True and kt["kq"]["ghi_hinh"] is True
_tr = c.get("/rustdesk", headers=H).get_data(as_text=True)
kq["rd_7_tab"] = all(('data-buoc="%d"' % i) in _tr for i in range(1, 8)) and "Xin phép trước khi kết nối" in _tr and "rd-hoi" not in _tr
_rg = c.get("/rustdesk/cho-phep-trinh-duyet.reg", headers=H, base_url="http://192.168.110.30")
_rgt = _rg.data.decode("utf-16")
kq["reg_trinh_duyet"] = _rg.status_code == 200 and _rg.data[:2] == b"\xff\xfe" and _rgt.startswith("Windows Registry Editor") and '\\"allowed_origins\\": [\\"http://192.168.110.30\\"]' in _rgt and "Microsoft\\Edge" in _rgt
kq["popup_xac_nhan"] = "Mở RustDesk để kết nối?" in _tr and "location.href=d.url" not in _tr
kq["tb_do_dai_byte"] = "$m.Length * 2" in URD.ps_thong_bao("x")
# 27/10: 5 viec anh yeu cau
kq["bo_chua_ho_tro"] = c.get("/uem/chua-ho-tro", headers=H).status_code == 404 and "Chưa hỗ trợ" not in c.get("/uem", headers=H).get_data(as_text=True)
_menu = c.get("/uem", headers=H).get_data(as_text=True)
kq["remote_tren_profile"] = 0 < _menu.find('href="/rustdesk"') < _menu.find('href="/uem/profiles"')
kq["kho_trung_tam_menu"] = 'href="/kho-trung-tam"' in _menu and c.get("/deployos/kho", headers=H).headers.get("Location", "").endswith("/kho-trung-tam")
_kt = c.get("/kho-trung-tam", headers=H)
kq["kho_trung_tam_trang"] = _kt.status_code == 200 and "Kho dùng chung" in _kt.get_data(as_text=True)
kq["kho_khong_con_tab"] = "/deployos/kho" not in c.get("/deployos/os", headers=H).get_data(as_text=True) and "/deployos/kho\"" not in c.get("/deployos/trienkhai", headers=H).get_data(as_text=True)
DL.MAY.sua(lambda ds: ds.append({"id": "m-khong-agent", "ip": "10.9.9.77", "ten": "MAY-WINRM", "giam_sat": True}))
DL.NHOM_MAY.sua(lambda ds: ds.append({"id": "g-test", "ten": "Phong Ke toan", "may": ["m-agent", "m-khong-agent"]}))
_g = c.get("/uem/trien-khai/goi?id=Google.Chrome", headers=H).get_data(as_text=True)
kq["wg_chon_theo"] = 'id="cg-loai"' in _g and "Chọn máy" in _g and "Chọn group" in _g and 'id="cg-tim"' in _g and "MOI_TRANG=25" in _g
kq["wg_chi_may_agent"] = 'value="m-agent"' in _g and "MAY-WINRM" not in _g and "Phong Ke toan" in _g
from werkzeug.datastructures import MultiDict  # noqa: E402
kq["wg_gop_group"] = URB.may_tu_form(MultiDict([("may", "m-agent"), ("nhom", "g-test")])) == ["m-agent", "m-khong-agent"]
_mt = c.get("/uem/may", headers=H).get_data(as_text=True)
kq["may_tinh_chi_agent"] = "MAY-AGENT-A" in _mt and "MAY-WINRM" not in _mt and 'action="/uem/may/them"' not in _mt
print("KETQUA " + json.dumps(kq))
