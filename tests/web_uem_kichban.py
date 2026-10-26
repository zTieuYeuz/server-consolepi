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
kq["rd_trang"] = c.get("/rustdesk", headers=H).status_code == 200
t = c.get("/rustdesk/api/trang-thai", headers=H).get_json()
kq["rd_tt_chua_cai"] = t["da_cai"] is False and t["ban"] == RD.VER_SERVER
kq["rd_host_xau"] = post("/rustdesk/api/cau-hinh", {"host": "a b;c"}).get_json()["ok"] is False
kq["rd_host_ok"] = post("/rustdesk/api/cau-hinh", {"host": "rd.example.com"}).get_json()["ok"] is True and RD.host_hieu_luc() == "rd.example.com"
kq["rd_script_chua_co_khoa"] = c.get("/rustdesk/client-cai.ps1", headers=H).status_code == 409
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
post("/rustdesk/api/cau-hinh", {"host": "rustdesk.example.com", "ws": True})
sc2 = RD.script_client("abcdef123456", "rustdesk.example.com", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
kq["rd_ws_bat"] = RD.dung_ws() and "allow-websocket = 'Y'" in sc2 and "'rustdesk.example.com'" in sc2 and ":21116" not in sc2
post("/rustdesk/api/cau-hinh", {"host": "rustdesk.example.com", "ws": False})
sc3 = RD.script_client("abcdef123456", "rustdesk.example.com", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
kq["rd_ws_tat"] = (not RD.dung_ws()) and "allow-websocket" not in sc3 and ":21116" in sc3
print("KETQUA " + json.dumps(kq))
