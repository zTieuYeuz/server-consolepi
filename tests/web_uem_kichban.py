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
print("KETQUA " + json.dumps(kq))
