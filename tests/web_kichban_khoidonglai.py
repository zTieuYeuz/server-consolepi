"""A5 (2.0.6): kich ban Agent co buoc script + khoi dong lai: cai app -> script -> khoi dong lai -> doi may bat lai -> buoc sau chay tiep.
Chay trong tien trinh rieng (CONSOLE_PI_DATA = bo cuc moi tam). Mo phong agent: gio khoi dong may, song/tat."""
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
from ui import tk_dongco as DC, tk_dulieu as DL, uem_agent as UA  # noqa: E402

c = app.test_client()
H = {"X-ConsolePi-Local": "1"}
kq = {}
nk = []                                   # thu tu cac viec da chay tren may
may = {"song": True, "boot": "2026-11-11T08:00:00", "lenh": []}
DC.LUC_TOI_THIEU_KHOI_DONG = 0
DC.danh_sach_kho = lambda: [{"ten": t, "tham_so": "/S"} for t in ("a.exe", "b.exe")]
DC._BUOC["phanmem"] = lambda cl, ip, b, m: (nk.append("app:" + b["ref"]) or True, b["ref"] + ": xong")
DC._BUOC["script"] = lambda cl, ip, b, m: (nk.append("script:" + b["ref"]) or True, b["ref"] + ": chạy xong")


class GiaClient:
    def __init__(self, mid):
        self.loai = "agent"

    def execute_ps(self, script):
        if "LastBootUpTime" in script:
            return may["boot"], type("S", (), {"error": []})(), False
        return "", type("S", (), {"error": []})(), False

    def execute_cmd(self, lenh):
        may["lenh"].append(lenh)
        return "", "", 0


UA.Client = GiaClient
UA.con_song = lambda m: may["song"]
DL.MAY.sua(lambda ds: ds.append({"id": "m1", "ip": "10.7.7.1", "ten": "M1", "giam_sat": True, "agent": {"serie": "s-m1", "luc_cuoi": 1}}))
DC.danh_sach_ungdung = lambda: []
from consolesystem.features.uem import uem_kichban as K  # noqa: E402
K._tai_nguyen = lambda: {"phanmem": [{"ref": t, "ten": t, "mo_ta": ""} for t in ("a.exe", "b.exe")], "ungdung": [],
                         "script": [{"ref": "doi-ten.ps1", "ten": "doi-ten.ps1", "mo_ta": ""}]}


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


def buoc_json(mot_lan=False):
    mot = {"mot_lan": True} if mot_lan else {}
    kich = [] if mot_lan else [{"loai": "script", "ref": "doi-ten.ps1"}]      # script luon chay moi luot -> khi do khoi dong lai la dung
    return json.dumps([dict(loai="phanmem", ref="a.exe", **mot)] + kich + [{"loai": "nguon", "ref": "khoi_dong_lai"},
                       dict(loai="phanmem", ref="b.exe", **mot), {"loai": "nguon", "ref": "bat"}, {"loai": "baomat", "ref": ""}])


r = c.post("/uem/trien-khai/kich-ban/luu", headers=H, data={"ten": "KB-RS", "buoc_json": buoc_json(), "may": ["m1"], "thoi_gian": "ngay", "sau": "chay"})
k = next(x for x in DL.KICH_BAN.doc() if x["ten"] == "KB-RS")
kq["luu_dung_thu_tu_va_loc_loai_la"] = r.status_code == 302 and [(b["loai"], b["ref"]) for b in k["buoc"]] == [
    ("phanmem", "a.exe"), ("script", "doi-ten.ps1"), ("nguon", "khoi_dong_lai"), ("phanmem", "b.exe")]
# 1) chay den buoc khoi dong lai: gui lenh, buoc sau CHUA chay
cho(k["id"], lambda s: any(b.get("gui_luc") for b in s.get("may", {}).get("m1", {}).get("buoc", [])))
b3 = st(k["id"])["may"]["m1"]["buoc"][2]
kq["gui_lenh_khoi_dong_lai"] = nk == ["app:a.exe", "script:doi-ten.ps1"] and len(may["lenh"]) == 1 and "shutdown /r" in may["lenh"][0] and b3["tt"] == "dang"
for _ in range(3):
    DL.TRANG_THAI.sua(lambda t: t[k["id"]]["may"]["m1"].__setitem__("tiep", 0))
    DC.tick()
    time.sleep(0.3)
kq["lenh_chua_thuc_hien_thi_chua_chay_tiep"] = "app:b.exe" not in nk and len(may["lenh"]) == 1 and st(k["id"])["may"]["m1"]["tt"] == "offline"
# 2) may tat roi bat lai nhung gio khoi dong khong doi -> van doi (khong tinh la da khoi dong lai)
may["song"] = False
DL.TRANG_THAI.sua(lambda t: t[k["id"]]["may"]["m1"].__setitem__("tiep", 0))
DC.tick()
time.sleep(0.3)
kq["may_dang_tat_thi_doi"] = "app:b.exe" not in nk
# 3) may bat lai, gio khoi dong moi -> chay tiep buoc sau, khong gui lenh khoi dong lai lan 2
may["song"] = True
may["boot"] = "2026-11-11T08:05:00"
DL.TRANG_THAI.sua(lambda t: t[k["id"]]["may"]["m1"].__setitem__("tiep", 0))
kq["chay_tiep_sau_khi_may_bat_lai"] = cho(k["id"], lambda s: s["may"]["m1"]["tt"] == "xong") and nk == ["app:a.exe", "script:doi-ten.ps1", "app:b.exe"] and len(may["lenh"]) == 1
kq["buoc_khoi_dong_lai_ghi_ket_qua"] = "khởi động lại" in st(k["id"])["may"]["m1"]["buoc"][2]["tb"] and st(k["id"])["may"]["m1"]["buoc"][2]["tt"] == "ok"
# 4) 'chi cai mot lan': luot sau khong co gi moi chay thi khong khoi dong lai may vo ich
nk.clear()
may["lenh"].clear()
c.post("/uem/trien-khai/kich-ban/luu", headers=H, data={"id": k["id"], "ten": "KB-RS", "buoc_json": buoc_json(True), "may": ["m1"], "thoi_gian": "ngay"})
for a in ("a.exe", "b.exe"):
    DL.TRANG_THAI.sua(lambda t, a=a: t.setdefault(k["id"], {}).setdefault("da_xong", {}).setdefault("m1", []).append("phanmem|" + a))
c.post(f"/uem/trien-khai/kich-ban/{k['id']}/chay", headers=H)
ok = cho(k["id"], lambda s: s.get("may", {}).get("m1", {}).get("tt") == "xong")
kq["mot_lan_bo_qua_khoi_dong_lai"] = ok and may["lenh"] == [] and nk == [] and "Bỏ qua khởi động lại" in st(k["id"])["may"]["m1"]["buoc"][1]["tb"]
# 5) trang sua hien dung cac buoc da luu va cho phep chon script / khoi dong lai
h = c.get("/uem/trien-khai/kich-ban/sua?id=" + k["id"], headers=H).get_data(as_text=True)
kq["trang_sua_co_buoc_script_va_khoi_dong_lai"] = 'id="buoc-json"' in h and "khoi_dong_lai" in h and "doi-ten.ps1" in h and '"loai": ["phanmem", "ungdung", "script", "winget", "nguon", "nhom"]' in h
# 6) khong gui lenh khi may tat
may["song"] = False
may["lenh"].clear()
c.post("/uem/trien-khai/kich-ban/luu", headers=H, data={"ten": "KB-RS2", "buoc_json": json.dumps([{"loai": "nguon", "ref": "khoi_dong_lai"}]), "may": ["m1"], "thoi_gian": "ngay", "sau": "chay"})
k2 = next(x for x in DL.KICH_BAN.doc() if x["ten"] == "KB-RS2")
cho(k2["id"], lambda s: s.get("may", {}).get("m1", {}).get("tt") == "offline")
kq["may_tat_khong_gui_lenh"] = may["lenh"] == [] and st(k2["id"])["may"]["m1"]["tt"] == "offline"
print("KETQUA " + json.dumps(kq, ensure_ascii=False))
