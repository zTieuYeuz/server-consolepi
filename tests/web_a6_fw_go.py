"""A6 (2.0.6): xoa tac vu quy tac tuong lua -> go quy tac tren may; nhan DA DAT SAN / DA LAM o ket qua tung may.
Chay trong tien trinh rieng (CONSOLE_PI_DATA = bo cuc moi tam)."""
import json
import os
import runpy
import sys
import threading
import time

os.environ.setdefault("CONSOLE_PI_LOG", __import__("tempfile").mkdtemp(prefix="cs-test-log-"))
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC)
os.chdir(SRC)
_goc = threading.Thread.start
threading.Thread.start = lambda self: None if getattr(getattr(self, "_target", None), "__name__", "") in ("tu_dang_ky_nen", "_driver_nen", "vong", "vong_kiem_tra_nen") else _goc(self)
app = runpy.run_path(os.path.join(SRC, "app.py"), run_name="dev")["app"]
from ui import tk_dulieu as DL, uem_buoc as UB, uem_dulieu as UD, uem_ketnoi as UK, uem_profiles as UP  # noqa: E402

c = app.test_client()
H = {"X-ConsolePi-Local": "1"}
kq = {}
may = {"song": True, "goi": [], "tra": "da_lam"}


def gia_ket_noi(m, bat_buoc_winrm=False):
    if not may["song"]:
        raise UK.LoiMay("Máy tắt, mất mạng hoặc chưa bật WinRM (cổng 5985 đóng).")
    return object(), "", "winrm"


def gia_chay(cl, ip, loai, ts):
    may["goi"].append((loai, ts.get("ten")))
    return may["tra"], "Đã gỡ 1 quy tắc"


UK.ket_noi = gia_ket_noi
UB.chay = gia_chay
DL.MAY.sua(lambda ds: ds.extend([{"id": i, "ip": "10.8.8.%d" % n, "ten": i.upper(), "giam_sat": True} for n, i in enumerate(("m1", "m2"), 1)]))


def tk(ten):
    return {"id": DL.moi_id(), "loai": "fw_quy_tac", "bat": True, "ver": DL.moi_id(),
            "tham_so": {"ten": ten, "chieu": "Inbound", "hanh_dong": "Allow", "giao_thuc": "TCP", "cong": "8080", "ho_so": "Any"}}


t1, t2, t3 = tk("Web 8080"), tk("Chung ten"), tk("Chung ten")
UD.PROFILES.sua(lambda ds: ds.extend([
    {"id": "p1", "ten": "Tuong lua A", "bat": True, "ap_dung_tat_ca": True, "the": [], "tasks": [t1, t2]},
    {"id": "p2", "ten": "Tuong lua B", "bat": True, "ap_dung_tat_ca": True, "the": [], "tasks": [t3]}]))
UD.TRANG_THAI_PROFILE.sua(lambda d: d.update({"p1": {"m1": {"trang_thai": "ok", "tasks": {t1["id"]: {"tt": "da_lam", "tb": "Đã tạo quy tắc"}, t2["id"]: {"tt": "da_dat", "tb": "Quy tắc đã đúng"}}},
                                                   "m2": {"trang_thai": "ok", "tasks": {t1["id"]: {"tt": "da_dat", "tb": ""}}}}}))

# 1) nhan ket qua tung may
h = c.get("/uem/profiles/p1", headers=H).get_data(as_text=True)
kq["nhan_da_dat_da_lam"] = "ĐÃ ĐẶT SẴN" in h and "ĐÃ LÀM" in h and "CHƯA CHẠY" in h
kq["hoi_xoa_noi_go_quy_tac"] = "sẽ được gỡ khỏi các máy" in h
# 2) xoa tac vu: ca 2 may duoc go
r = c.post(f"/uem/profiles/p1/task/{t1['id']}/hanh-dong", headers=H, data={"viec": "xoa"})
for _ in range(50):
    if len(may["goi"]) >= 2 and not UD.DON_DEP.doc():
        break
    time.sleep(0.1)
kq["xoa_task_go_quy_tac_ca_2_may"] = r.status_code == 302 and sorted(may["goi"]) == [("fw_go_cua_console", "Web 8080")] * 2 and UD.DON_DEP.doc() == []
kq["tac_vu_da_xoa_khoi_profile"] = [t["id"] for t in DL.tim(UD.PROFILES.doc(), "p1")["tasks"]] == [t2["id"]]
kq["ghi_lich_su_may"] = any("gỡ quy tắc tường lửa" in x["ten"] and x["ok"] for x in UD.BAO_CAO_TAC_VU.doc().get("m1", []))
# 3) ten con duoc profile khac khai bao -> KHONG go
may["goi"].clear()
c.post(f"/uem/profiles/p1/task/{t2['id']}/hanh-dong", headers=H, data={"viec": "xoa"})
time.sleep(0.5)
kq["ten_con_dung_o_profile_khac_khong_go"] = may["goi"] == [] and UD.DON_DEP.doc() == []
# 4) may tat -> giu viec, bat len thi go
t4 = tk("Mo cong 9000")
UD.PROFILES.sua(lambda ds: DL.tim(ds, "p1")["tasks"].append(t4))
UD.TRANG_THAI_PROFILE.sua(lambda d: d["p1"].setdefault("m1", {"tasks": {}}).setdefault("tasks", {}).update({t4["id"]: {"tt": "da_lam"}}))
may["song"] = False
c.post(f"/uem/profiles/p1/task/{t4['id']}/hanh-dong", headers=H, data={"viec": "xoa"})
time.sleep(0.6)
dd = UD.DON_DEP.doc()
kq["may_tat_giu_viec_cho"] = len(dd) == 1 and dd[0]["ten"] == "Mo cong 9000" and dd[0]["thu"] == 1 and may["goi"] == []
may["song"] = True
UD.DON_DEP.sua(lambda ds: [x.update(tiep=0) for x in ds])
UP.xu_ly_don_dep()
kq["may_bat_len_thi_go"] = may["goi"] == [("fw_go_cua_console", "Mo cong 9000")] and UD.DON_DEP.doc() == []
# 5) doi ten quy tac = go quy tac ten cu
t5 = tk("Ten cu")
UD.PROFILES.sua(lambda ds: DL.tim(ds, "p1")["tasks"].append(t5))
UD.TRANG_THAI_PROFILE.sua(lambda d: d["p1"].setdefault("m2", {"tasks": {}}).setdefault("tasks", {}).update({t5["id"]: {"tt": "da_lam"}}))
may["goi"].clear()
c.post("/uem/profiles/p1/task/luu", headers=H, data={"loai_tac_vu": "fw_quy_tac", "task_id": t5["id"], "ten": "Ten moi", "chieu": "Inbound", "hanh_dong": "Allow",
                                                     "giao_thuc": "TCP", "cong": "8080", "ho_so": "Any"})
for _ in range(30):
    if may["goi"]:
        break
    time.sleep(0.1)
kq["doi_ten_go_quy_tac_cu"] = may["goi"] == [("fw_go_cua_console", "Ten cu")]
# 6) xoa tac vu khong phai tuong lua: khong dung toi viec go
t6 = {"id": DL.moi_id(), "loai": "dv_cau_hinh", "bat": True, "ver": "x", "tham_so": {"ten": "Spooler", "khoi_dong": "Disabled", "trang_thai": "Stopped"}}
UD.PROFILES.sua(lambda ds: DL.tim(ds, "p1")["tasks"].append(t6))
UD.TRANG_THAI_PROFILE.sua(lambda d: d["p1"]["m1"]["tasks"].update({t6["id"]: {"tt": "da_lam"}}))
may["goi"].clear()
c.post(f"/uem/profiles/p1/task/{t6['id']}/hanh-dong", headers=H, data={"viec": "xoa"})
time.sleep(0.4)
kq["xoa_tac_vu_khac_khong_go_gi"] = may["goi"] == [] and UD.DON_DEP.doc() == []
# 7) kich ban go: chi nham rule nhom Console System
ps = UB.tao_kich_ban.__wrapped__ if hasattr(UB.tao_kich_ban, "__wrapped__") else UB.tao_kich_ban
s = ps("fw_go_cua_console", {"ten": "Web 8080"})
kq["kich_ban_go_chi_nhom_console"] = "Get-NetFirewallRule -Group 'Console System'" in s and "Remove-NetFirewallRule" in s and "ST=DA_DAT" in s and "ST=DA_LAM" in s
print("KETQUA " + json.dumps(kq, ensure_ascii=False))
