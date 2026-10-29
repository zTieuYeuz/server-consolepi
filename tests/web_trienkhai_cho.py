"""Chay trong tien trinh rieng (CONSOLE_PI_DATA = bo cuc moi tam): dot trien khai kieu Endpoint Central -
may tat thi cho, bat lai thi tu chay, thu lai khi loi, het han, huy / chay lai, dot luu dia."""
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
from ui import tk_dongco as DC, tk_dulieu as DL, uem_agent as UA, uem_dulieu as UD, uem_ketnoi as UK, uem_trienkhai as UT  # noqa: E402

c = app.test_client()
H = {"X-ConsolePi-Local": "1"}
kq = {}
loi_may = set()
UK.ket_noi = lambda m, bat_buoc_winrm=False: (object(), "", "agent")
DC.danh_sach_kho = lambda: [{"ten": "7z.exe", "tham_so": "/S"}]
DC.cai_tu_kho = lambda cl, ip, ten, may: (False, "ma thoat 1603") if may["id"] in loi_may else (True, "7z.exe: xong (mã thoát 0)")
UT.UBC.chay_nen = lambda mid: None
DL.MAY.sua(lambda ds: ds.extend([{"id": i, "ip": "10.8.8.%d" % n, "ten": i.upper(), "giam_sat": True, "agent": {"serie": "s-" + i, "luc_cuoi": 1}}
                                 for n, i in enumerate(("m-bat", "m-tat", "m-loi"), 1)]))


def song(mid):
    UA._NHIP[mid] = {"luc": time.time(), "ban": "2.3.5", "may": mid, "ip": "x", "luu_luc": time.time()}


def cho(dot, dk, giay=5):
    het = time.time() + giay
    while time.time() < het:
        s = UT.trang_thai(dot)
        if dk(s):
            return s
        time.sleep(0.05)
    return UT.trang_thai(dot)


song("m-bat")
song("m-loi")
loi_may.add("m-loi")
dot, loi = UT.bat_dau("kho", "7z.exe", "7z.exe", ["m-bat", "m-tat", "m-loi"], thu_lai=1, het_han_ngay=7)
s = cho(dot, lambda s: s["dang"] == 0)
kq["may_bat_chay_ngay"] = s["may"]["m-bat"]["tt"] == "da_lam"
kq["may_tat_cho"] = s["may"]["m-tat"]["tt"] == "cho_online" and s["cho"] >= 1
kq["may_loi_cho_thu_lai"] = s["may"]["m-loi"]["tt"] == "thu_lai" and s["may"]["m-loi"]["lan"] == 1
kq["api_tom_tat"] = c.get("/uem/trien-khai/tt/" + dot, headers=H).get_json()["dang"] == 0
kq["lich_su_chi_ghi_ket_qua_cuoi"] = len(UD.TRIEN_KHAI.doc()) == 1

# may tat bat len: agent bao nhip -> quet -> tu cai
song("m-tat")
UT._quet()
s = cho(dot, lambda s: s["may"]["m-tat"]["tt"] == "da_lam")
kq["may_bat_lai_tu_cai"] = s["may"]["m-tat"]["tt"] == "da_lam"

# thu lai: chua toi gio thi khong chay; toi gio ma van loi -> loi cuoi
UT._quet()
kq["thu_lai_cho_toi_gio"] = UT.trang_thai(dot)["may"]["m-loi"]["tt"] == "thu_lai"
UT.DOT_TK.sua(lambda ds: ds[dot]["may"]["m-loi"].__setitem__("tiep", 0))
UT._quet()
s = cho(dot, lambda s: s["may"]["m-loi"]["tt"] == "loi")
kq["het_luot_thu_lai_thanh_loi"] = s["may"]["m-loi"]["tt"] == "loi" and s["may"]["m-loi"]["lan"] == 2

# chay lai may loi (da sua nguyen nhan)
loi_may.discard("m-loi")
r = c.post(f"/uem/trien-khai/dot/{dot}/chay-lai", headers=H)
UT._quet()
s = cho(dot, lambda s: s["may"]["m-loi"]["tt"] == "da_lam")
kq["chay_lai_may_loi"] = r.status_code == 302 and s["may"]["m-loi"]["tt"] == "da_lam" and s["xong"] == 3

# het han + huy
DL.MAY.sua(lambda ds: ds.append({"id": "m-xa", "ip": "10.8.8.9", "ten": "XA", "giam_sat": True, "agent": {"serie": "s-xa", "luc_cuoi": 1}}))
d2, _ = UT.bat_dau("kho", "7z.exe", "7z.exe", ["m-xa"])
d3, _ = UT.bat_dau("kho", "7z.exe", "7z.exe", ["m-xa"])
UT.DOT_TK.sua(lambda ds: ds[d2].__setitem__("het_han", time.time() - 1))
UT._quet()
kq["qua_han"] = UT.trang_thai(d2)["may"]["m-xa"]["tt"] == "het_han"
r = c.post(f"/uem/trien-khai/dot/{d3}/huy", headers=H)
kq["huy_may_cho"] = UT.trang_thai(d3)["may"]["m-xa"]["tt"] == "huy"

# Console khoi dong lai giua chung: viec dang chay -> cho chay lai
UT.DOT_TK.sua(lambda ds: ds[d3]["may"]["m-xa"].__setitem__("tt", "dang_chay"))
UT._BAT_DAU = False
UT.khoi_dong_bo_lap()
kq["phuc_hoi_sau_khoi_dong"] = UT.trang_thai(d3)["may"]["m-xa"]["tt"] == "cho_online"

# may dang chay kich ban Agent: dot moi nhuong (thu_lai), kich ban xong thi dot tu chay
DC._DANG.add(("kb-gia", "m-bat"))
d4, _ = UT.bat_dau("kho", "7z.exe", "7z.exe", ["m-bat"])
kq["nhuong_kich_ban"] = UT.trang_thai(d4)["may"]["m-bat"]["tt"] == "thu_lai"
DC._DANG.discard(("kb-gia", "m-bat"))
UT._quet()
kq["het_ban_thi_chay"] = cho(d4, lambda s: s["may"]["m-bat"]["tt"] == "da_lam") is not None and UT.trang_thai(d4)["may"]["m-bat"]["tt"] == "da_lam"

# giao dien
h = c.get("/uem/trien-khai/dot", headers=H).get_data(as_text=True)
kq["trang_dot"] = "Trạng thái triển khai" in h and f"/uem/trien-khai/dot/{dot}" in h
h = c.get(f"/uem/trien-khai/dot/{d2}", headers=H).get_data(as_text=True)
kq["trang_chi_tiet"] = "Hết hạn" in h and "Chạy lại 1 máy" in h
h = c.get("/uem/trien-khai/goi?kho=1&id=7z.exe", headers=H).get_data(as_text=True)
kq["chinh_sach_tren_form"] = 'name="thu_lai"' in h and 'name="het_han_ngay"' in h and 'name="wol"' in h
r = c.post("/uem/trien-khai/chay", headers=H, data={"hanh_dong": "kho", "goi_id": "7z.exe", "ten_goi": "7z", "may": ["m-xa"], "thu_lai": "0", "het_han_ngay": "3"})
kq["form_chay"] = r.status_code == 302 and "dot=" in r.headers.get("Location", "")
print("KETQUA " + json.dumps(kq))
