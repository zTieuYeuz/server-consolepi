"""Chay trong tien trinh rieng (CONSOLE_PI_DATA = bo cuc moi tam): kich ban Cai phan mem qua Agent kieu Endpoint Central -
chon phan mem kho > may/group > tai khoan cai > thoi gian; chay, may tat cho, dung / tiep tuc, Run As, lich rieng, xoa."""
import json
import os
import runpy
import sys
import threading
import time

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC)
os.chdir(SRC)
_goc = threading.Thread.start
threading.Thread.start = lambda self: None if getattr(getattr(self, "_target", None), "__name__", "") in ("tu_dang_ky_nen", "_driver_nen", "vong", "vong_kiem_tra_nen") else _goc(self)
app = runpy.run_path(os.path.join(SRC, "app.py"), run_name="dev")["app"]
from ui import tk_dongco as DC, tk_dulieu as DL, uem_agent as UA  # noqa: E402

c = app.test_client()
H = {"X-ConsolePi-Local": "1"}
kq = {}
goi = []                     # (may_id, phan mem, cai_bang)
chan = {"ten": None, "su_kien": threading.Event(), "vao": threading.Event()}
DC.danh_sach_kho = lambda: [{"ten": t, "tham_so": "/S"} for t in ("a.exe", "b.exe", "c.exe")]


def gia_buoc(cl, ip, b, may):
    if b["ref"] == chan["ten"]:
        chan["vao"].set()
        chan["su_kien"].wait(10)
    goi.append((may["id"], b["ref"], getattr(DC._CAI_BANG, "tk", None)))
    return True, b["ref"] + ": xong (mã thoát 0)"


DC._BUOC["phanmem"] = gia_buoc
UA.Client = lambda mid: object()
DL.MAY.sua(lambda ds: ds.extend([{"id": i, "ip": "10.7.7.%d" % n, "ten": i.upper(), "giam_sat": True, "agent": {"serie": "s-" + i, "luc_cuoi": 1}}
                                 for n, i in enumerate(("m-bat", "m-tat"), 1)]))
DL.NHOM_MAY.sua(lambda ds: ds.append({"id": "g1", "ten": "Phong A", "may": ["m-bat"]}))


def song(mid):
    UA._NHIP[mid] = {"luc": time.time(), "ban": "2.3.5", "may": mid, "ip": "x", "luu_luc": time.time()}


def st(kb):
    return DL.TRANG_THAI.doc().get(kb, {})


def cho(kb, dk, giay=6):
    het = time.time() + giay
    while time.time() < het:
        DC.tick()
        if dk(st(kb)):
            return True
        time.sleep(0.1)
    return False


def kb_ten(ten):
    return next(k for k in DL.KICH_BAN.doc() if k["ten"] == ten)


song("m-bat")
# 1) tao + chay ngay: may bat cai ca 3, may tat cho
r = c.post("/uem/trien-khai/kich-ban/luu", headers=H, data={"ten": "KB1", "pm": ["a.exe", "c.exe", "b.exe", "khong-co.exe"], "may": ["m-tat"], "nhom": ["g1"],
                                                            "tai_khoan_id": "", "thoi_gian": "ngay", "sau": "chay"})
k1 = kb_ten("KB1")
kq["luu_kich_ban"] = r.status_code == 302 and k1["kenh"] == "agent" and [b["ref"] for b in k1["buoc"]] == ["a.exe", "b.exe", "c.exe"] and k1["nhom_may"] == ["g1"]
kq["may_bat_cai_het"] = cho(k1["id"], lambda s: s.get("may", {}).get("m-bat", {}).get("tt") == "xong")
kq["thu_tu_buoc"] = [g[1] for g in goi if g[0] == "m-bat"] == ["a.exe", "b.exe", "c.exe"] and all(g[2] is None for g in goi)
kq["may_tat_cho_bat"] = cho(k1["id"], lambda s: s.get("may", {}).get("m-tat", {}).get("tt") == "offline") and st(k1["id"])["may"]["m-tat"]["thu"] == 0
DC.tick()
kq["cho_may_bat_khong_ghi_lap"] = sum("chờ máy bật" in x for x in st(k1["id"]).get("nhat_ky", [])) == 1
# may tat bat len -> tu chay
song("m-tat")
DL.TRANG_THAI.sua(lambda t: t[k1["id"]]["may"]["m-tat"].__setitem__("tiep", 0))
kq["may_bat_lai_tu_cai"] = cho(k1["id"], lambda s: s["may"]["m-tat"]["tt"] == "xong") and cho(k1["id"], lambda s: s.get("xong_luc"))

# 2) dung giua chung roi tiep tuc: buoc da xong khong chay lai
goi.clear()
chan["ten"] = "b.exe"
c.post("/uem/trien-khai/kich-ban/luu", headers=H, data={"ten": "KB2", "pm": ["a.exe", "b.exe", "c.exe"], "may": ["m-bat"], "thoi_gian": "ngay", "sau": "chay"})
k2 = kb_ten("KB2")
DC.tick()
chan["vao"].wait(5)
c.post(f"/uem/trien-khai/kich-ban/{k2['id']}/dung", headers=H)
chan["su_kien"].set()
kq["dung_sau_buoc_dang_lam"] = cho(k2["id"], lambda s: s["may"]["m-bat"]["tt"] == "dung") and [g[1] for g in goi] == ["a.exe", "b.exe"]
h = c.get(f"/uem/trien-khai/kich-ban/{k2['id']}", headers=H).get_data(as_text=True)
kq["nut_tiep_tuc"] = "Tiếp tục" in h and "Đã dừng" in h
c.post(f"/uem/trien-khai/kich-ban/{k2['id']}/tiep-tuc", headers=H)
kq["tiep_tuc_chay_phan_con_lai"] = cho(k2["id"], lambda s: s["may"]["m-bat"]["tt"] == "xong") and [g[1] for g in goi] == ["a.exe", "b.exe", "c.exe"]
chan["ten"] = None

# 3) cai bang tai khoan (Run As User)
DL.TAI_KHOAN.sua(lambda ds: ds.append({"id": "tk1", "ten": "Admin", "user": "quantri", "mk": DL.ma_hoa("MatKhau#1")}))
goi.clear()
c.post("/uem/trien-khai/kich-ban/luu", headers=H, data={"ten": "KB3", "pm": ["a.exe"], "may": ["m-bat"], "tai_khoan_id": "tk1", "thoi_gian": "ngay", "sau": "chay"})
k3 = kb_ten("KB3")
kq["run_as_dung_tai_khoan"] = cho(k3["id"], lambda s: s["may"]["m-bat"]["tt"] == "xong") and goi == [("m-bat", "a.exe", ("quantri", "MatKhau#1"))]
kq["run_as_xoa_sau_khi_chay"] = getattr(DC._CAI_BANG, "tk", None) is None

# 4) hen gio rieng: tao lich rieng, khong chay ngay, khong hien ben LAN
r = c.post("/uem/trien-khai/kich-ban/luu", headers=H, data={"ten": "KB4", "pm": ["a.exe"], "may": ["m-bat"], "thoi_gian": "rieng", "kieu": "hang_tuan",
                                                            "gio": "02:30", "thu": ["5"], "sau": "chay"})
k4 = kb_ten("KB4")
l4 = DL.tim(DL.LICH.doc(), k4["lich_id"])
DC.tick()
kq["lich_rieng"] = bool(l4) and l4.get("rieng") == k4["id"] and l4["gio"] == "02:30" and st(k4["id"]).get("bat") and not st(k4["id"]).get("slot")
kq["lan_khong_thay_kich_ban_agent"] = "KB1" not in c.get("/deployos/trienkhai", headers=H).get_data(as_text=True) and \
    "KB1" not in c.get("/deployos/trienkhai/kichban", headers=H).get_data(as_text=True) and "Riêng: KB4" not in c.get("/deployos/trienkhai/lich", headers=H).get_data(as_text=True)
h = c.get("/uem/trien-khai/kich-ban/sua?id=" + k4["id"], headers=H).get_data(as_text=True)
kq["sua_giu_lua_chon"] = 'value="rieng" selected' in h and 'value="02:30"' in h and 'value="m-bat" checked' in h
c.post(f"/uem/trien-khai/kich-ban/{k4['id']}/xoa", headers=H)
kq["xoa_kich_ban_va_lich_rieng"] = not DL.tim(DL.KICH_BAN.doc(), k4["id"]) and not DL.tim(DL.LICH.doc(), l4["id"]) and k4["id"] not in DL.TRANG_THAI.doc()

# 5) trang + kiem tra dau vao
h = c.get("/uem/trien-khai/kich-ban", headers=H).get_data(as_text=True)
kq["trang_danh_sach"] = "KB1" in h and "Tạo kịch bản mới" in h and "Kịch bản" in h
r = c.post("/uem/trien-khai/kich-ban/luu", headers=H, data={"ten": "X", "pm": ["khong-co.exe"], "may": ["m-bat"], "thoi_gian": "ngay"})
kq["tu_choi_phan_mem_la"] = not any(k["ten"] == "X" for k in DL.KICH_BAN.doc())
r = c.post("/uem/trien-khai/kich-ban/luu", headers=H, data={"ten": "Y", "pm": ["a.exe"], "thoi_gian": "ngay"})
kq["tu_choi_khong_chon_may"] = not any(k["ten"] == "Y" for k in DL.KICH_BAN.doc())
print("KETQUA " + json.dumps(kq))
