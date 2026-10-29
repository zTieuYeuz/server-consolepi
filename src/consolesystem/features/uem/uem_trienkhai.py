# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Quan ly may tram - TRIEN KHAI WinGet hang loat (mo phong menu Deploy cua OpenUEM: DeployInstall / DeployUninstall /
SelectPackageDeployment / ComputerDeployInstall / ComputerDeployUpdate / ComputerDeployUninstall).

Mot "dot" = 1 hanh dong (cai / go / nang cap / cai tu kho) cho 1 goi tren nhieu may, chay song song (toi da 4 may).
Lam theo kieu Endpoint Central (ManageEngine):
  * Dot luu DIA (DOT_TK) - Console khoi dong lai van con, may tat may tuan van doi duoc.
  * May co agent nhung dang tat -> "cho_online" (Yet to Apply). Agent bao nhip lai (uem_agent.xu_ly_nhip goi danh_thuc)
    hoac vong quet 30 giay thay may song -> tu cai. Tuy chon gui Wake-on-LAN truoc khi cho.
  * Loi -> thu lai toi da N lan, cach nhau 5/10/15... phut (Retry in progress). Agent mat lien lac giua chung -> quay ve cho.
  * Qua han (mac dinh 7 ngay) ma may van chua bat -> "het_han". Co the Huy may dang cho / Chay lai may loi.
  * Moi may chi chay 1 viec trien khai cung luc. Ghi lich su (TRIEN_KHAI) + tac vu khi may co ket qua cuoi.
May chua cai agent (vao bang WinRM) giu cach cu: chay ngay 1 lan.
"""
import sys as _sys
_sys.modules["ui.uem_trienkhai"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from ui import tk_dongco as DC
from ui import tk_dulieu as DL
from ui import uem_baocao as UBC
from ui import uem_buoc as UB
from ui import uem_dulieu as UD
from ui import uem_ketnoi as UK
from ui.tk_dulieu import KhoLon
from consolesystem.core import magic_packet as _MP
from consolesystem.core.nhatky import bo_qua as _bo_qua

_EX = ThreadPoolExecutor(max_workers=4)
_KHOA = threading.RLock()
_DANG = set()                       # may_id dang chay 1 viec trien khai (RAM)
_DANH_THUC = threading.Event()
_BAT_DAU = False
TEN_HANH_DONG = {"cai": "Cài đặt", "go": "Gỡ cài đặt", "nang": "Nâng cấp", "kho": "Cài từ kho"}
TEN_TT = {"cho": "Đang xếp hàng", "cho_online": "Chờ máy bật", "dang_chay": "Đang chạy", "thu_lai": "Chờ thử lại",
          "da_lam": "Hoàn tất", "da_dat": "Đã đúng sẵn", "loi": "Lỗi", "het_han": "Hết hạn", "huy": "Đã hủy"}
CUOI = ("da_lam", "da_dat", "loi", "het_han", "huy")      # trang thai ket thuc
CHO = ("cho_online", "thu_lai")                             # dang doi (khong co gi dang chay)
DOT_TK = KhoLon("uem_dot_tk", {})   # {dot_id: {hanh_dong, goi_id, ten_goi, bat_dau, het_han, thu_lai, wol, may: {may_id: {ten, tt, tb, lan, tiep, luc}}}}


def _ps_nang(goi_id):
    if goi_id == "*":
        return (UB._TIM_WINGET + "$ProgressPreference='SilentlyContinue'; "
                f"$o = & $w upgrade --all --silent --accept-package-agreements {UB._WG_CHUNG} 2>&1 | Out-String; "
                "if ($LASTEXITCODE -eq 0) { 'ST=DA_LAM Da nang cap tat ca goi co ban moi' } elseif ($LASTEXITCODE -eq -1978335189) { 'ST=DA_DAT Khong co goi nao can nang cap' } "
                "else { 'ST=LOI winget ma ' + $LASTEXITCODE + ' ' + $o.Substring([Math]::Max(0,$o.Length-300)) }")
    return (UB._TIM_WINGET + "$ProgressPreference='SilentlyContinue'; "
            f"& $w list --id {goi_id} -e {UB._WG_CHUNG} | Out-Null; if ($LASTEXITCODE -ne 0) {{ 'ST=LOI May chua cai goi nay'; return }}; "
            f"$o = & $w upgrade --id {goi_id} -e --scope machine --silent --accept-package-agreements {UB._WG_CHUNG} 2>&1 | Out-String; "
            "if ($LASTEXITCODE -eq 0) { 'ST=DA_LAM Da nang cap' } elseif ($LASTEXITCODE -eq -1978335189) { 'ST=DA_DAT Da la ban moi nhat' } "
            "else { 'ST=LOI winget ma ' + $LASTEXITCODE + ' ' + $o.Substring([Math]::Max(0,$o.Length-300)) }")


def _ten(m, may_id):
    return (m or {}).get("bi_danh") or (m or {}).get("ten") or (m or {}).get("ip", may_id)


def _dat(dot_id, may_id, **kw):
    """Doi trang thai 1 may trong dot (ghi dia). Tra ve ban sao dot sau khi doi (hoac None)."""
    kq = {}

    def f(ds):
        d = ds.get(dot_id)
        if d and may_id in d["may"]:
            d["may"][may_id].update(kw, luc=time.time())
            kq["d"] = d
    with _KHOA:
        DOT_TK.sua(f)
    return kq.get("d")


def _ghi_ket_qua(d, may_id, tt, tb):
    ok = tt in ("da_lam", "da_dat")
    ten = d["may"][may_id]["ten"]
    UD.TRIEN_KHAI.sua(lambda ds: (ds.append({"luc": time.time(), "may_id": may_id, "may": ten, "goi_id": d["goi_id"], "ten_goi": d["ten_goi"],
                                              "hanh_dong": d["hanh_dong"], "ok": ok, "tt": tt, "tb": tb[:300]}), ds.__setitem__(slice(None), ds[-2000:])))
    UD.ghi_tac_vu(may_id, "trien_khai", f'{TEN_HANH_DONG.get(d["hanh_dong"], d["hanh_dong"])} {d["ten_goi"]}', ok, tb)


def _lam(d, m, c):
    if d["hanh_dong"] == "kho":
        ok, tb = DC.cai_tu_kho(c, m["ip"], d["goi_id"], m)
        return ("da_lam" if ok else "loi"), tb
    if d["hanh_dong"] == "nang":
        out, err = DC._chay_ps(c, _ps_nang(d["goi_id"]))
        mm = re.search(r"ST=(DA_DAT|DA_LAM|LOI)\s*(.*)", out)
        return ({"DA_DAT": "da_dat", "DA_LAM": "da_lam", "LOI": "loi"}[mm.group(1)], mm.group(2).strip()) if mm else ("loi", (err or out)[:300])
    return UB.chay(c, m["ip"], "winget_cai" if d["hanh_dong"] == "cai" else "winget_go", {"goi_id": d["goi_id"]})


def _chay_may(dot_id, may_id):
    """Chay 1 may (da duoc danh dau dang_chay + nam trong _DANG)."""
    try:
        d = DOT_TK.doc().get(dot_id)
        if not d:
            return
        m = DL.tim(DL.MAY.doc(), may_id)
        tt, tb = "loi", "Không tìm thấy máy."
        co_ag = bool(m) and _co_agent(m)
        if m:
            try:
                c, _mk, _cach = UK.ket_noi(m)
                tt, tb = _lam(d, m, c)
            except UK.LoiMay as e:
                tt, tb = "loi", str(e)
            except Exception as e:
                tt, tb = "loi", DC._loi_dep(e)
        if tt == "loi" and co_ag and ("mất liên lạc" in tb or not _con_song(m)):
            _dat(dot_id, may_id, tt="cho_online", tb="Máy mất liên lạc khi đang chạy, sẽ chạy lại khi máy bật.")
            return
        lan = d["may"][may_id].get("lan", 0) + 1
        if tt == "loi" and co_ag and lan <= d.get("thu_lai", 0):
            _dat(dot_id, may_id, tt="thu_lai", tb=f"Lần {lan} lỗi: {tb}"[:300], lan=lan, tiep=time.time() + 300 * lan)
            return
        d = _dat(dot_id, may_id, tt=tt, tb=tb[:300], lan=lan)
        if d:
            _ghi_ket_qua(d, may_id, tt, tb)
        if m and tt == "da_lam":
            UBC.chay_nen(may_id)               # cap nhat danh sach phan mem
    except Exception as e:
        _dat(dot_id, may_id, tt="loi", tb=DC._loi_dep(e)[:300])
    finally:
        with _KHOA:
            _DANG.discard(may_id)
        _DANH_THUC.set()                       # may nay ranh: xem con viec khac cho no khong


def _co_agent(m):
    from ui import uem_agent as UA
    return UA.co_agent(m)


def _con_song(m):
    from ui import uem_agent as UA
    return UA.con_song(m)


def _giao(dot_id, may_id):
    """Danh dau dang_chay va day vao hang doi neu may chua ban. Goi trong _KHOA."""
    if may_id in _DANG:
        return False
    _DANG.add(may_id)
    _dat(dot_id, may_id, tt="dang_chay", tb="")
    _EX.submit(_chay_may, dot_id, may_id)
    return True


def _quet():
    """Xem moi dot con dang doi: may song thi giao viec, qua han thi danh het_han."""
    now = time.time()
    may = {m["id"]: m for m in DL.MAY.doc()}
    with _KHOA:
        ds = DOT_TK.doc()
        for dot_id, d in ds.items():
            for mid, x in d["may"].items():
                if x["tt"] not in CHO:
                    continue
                if now > d.get("het_han", 0):
                    dd = _dat(dot_id, mid, tt="het_han", tb="Quá hạn mà máy chưa bật / chưa cài được.")
                    if dd:
                        _ghi_ket_qua(dd, mid, "het_han", "Quá hạn mà máy chưa bật / chưa cài được.")
                    continue
                m = may.get(mid)
                if not m:
                    _dat(dot_id, mid, tt="huy", tb="Máy đã bị xóa khỏi danh sách.")
                    continue
                if x["tt"] == "thu_lai" and now < x.get("tiep", 0):
                    continue
                if _con_song(m):
                    _giao(dot_id, mid)


def danh_thuc(may_id=None):
    """Agent vua bao nhip lai (hoac co viec moi): quet ngay, khong cho vong 30 giay."""
    _DANH_THUC.set()


def khoi_dong_bo_lap():
    global _BAT_DAU
    with _KHOA:
        if _BAT_DAU:
            return
        _BAT_DAU = True

        def phuc_hoi(ds):              # viec dang chay luc Console tat da mat -> cho chay lai
            for d in ds.values():
                for x in d["may"].values():
                    if x["tt"] in ("dang_chay", "cho"):
                        x["tt"], x["tb"] = "cho_online", "Console khởi động lại khi đang chạy, sẽ chạy lại."
            for k in [k for k, d in ds.items() if all(x["tt"] in CUOI for x in d["may"].values()) and time.time() - d["bat_dau"] > 30 * 86400]:
                ds.pop(k)              # dot da xong qua 30 ngay: bo (lich su van con trong TRIEN_KHAI)
        DOT_TK.sua(phuc_hoi)

    def vong():
        while True:
            _DANH_THUC.wait(30)
            _DANH_THUC.clear()
            try:
                _quet()
            except Exception as _loi:
                _bo_qua(_loi)
    threading.Thread(target=vong, daemon=True, name="uem-trien-khai").start()


def bat_dau(hanh_dong, goi_id, ten_goi, may_ids, thu_lai=2, het_han_ngay=7, wol=False):
    """(dot_id, loi)"""
    if hanh_dong not in TEN_HANH_DONG:
        return None, "Hành động không hợp lệ."
    if hanh_dong == "kho":
        if goi_id not in [a["ten"] for a in DC.danh_sach_kho()]:
            return None, "Không có phần mềm này trong kho."
    elif goi_id != "*" and not re.fullmatch(r"[A-Za-z0-9._+-]{2,100}", goi_id or ""):
        return None, "Mã gói WinGet không hợp lệ."
    ds_may = DL.MAY.doc()
    ids = [i for i in dict.fromkeys(may_ids) if DL.tim(ds_may, i)]
    if not ids:
        return None, "Chưa chọn máy nào."
    khoi_dong_bo_lap()                 # phuc hoi dot cu truoc khi them dot moi (thuong da chay luc dang ky route)
    thu_lai = max(0, min(int(thu_lai or 0), 5))
    het_han_ngay = max(1, min(int(het_han_ngay or 7), 30))
    now = time.time()
    dot_id = UD.moi_id()
    d = {"hanh_dong": hanh_dong, "goi_id": goi_id, "ten_goi": ten_goi or goi_id, "bat_dau": now, "het_han": now + het_han_ngay * 86400,
         "thu_lai": thu_lai, "wol": bool(wol), "may": {}}
    can_danh_thuc = []
    for i in ids:
        m = DL.tim(ds_may, i)
        if _co_agent(m) and not _con_song(m):
            d["may"][i] = {"ten": _ten(m, i), "tt": "cho_online", "tb": "Máy đang tắt hoặc mất mạng, sẽ tự chạy khi máy bật.", "lan": 0, "luc": now}
            if wol and m.get("mac"):
                can_danh_thuc.append(m["mac"])
        else:
            d["may"][i] = {"ten": _ten(m, i), "tt": "cho", "tb": "", "lan": 0, "luc": now}
    with _KHOA:
        DOT_TK.sua(lambda ds: ds.__setitem__(dot_id, d))
        for i, x in d["may"].items():
            if x["tt"] == "cho":
                if i in _DANG:             # may dang chay viec khac: doi luot sau
                    _dat(dot_id, i, tt="thu_lai", tb="Máy đang chạy việc triển khai khác, sẽ chạy ngay sau đó.", tiep=0)
                else:
                    _giao(dot_id, i)
    if can_danh_thuc:
        try:
            n, _ct = _MP.gui(can_danh_thuc)
            for i, x in d["may"].items():
                if x["tt"] == "cho_online" and (DL.tim(ds_may, i) or {}).get("mac"):
                    _dat(dot_id, i, tb="Đã gửi Wake-on-LAN, chờ máy bật.")
        except Exception as e:
            _bo_qua(e)
    return dot_id, ""


def _tom_tat(d):
    may = {k: dict(v) for k, v in d["may"].items()}
    for v in may.values():
        v["xong"] = v["tt"] in CUOI
        v["nhan"] = TEN_TT.get(v["tt"], v["tt"])
    dem = {}
    for v in may.values():
        dem[v["tt"]] = dem.get(v["tt"], 0) + 1
    return {"hanh_dong": d["hanh_dong"], "goi_id": d["goi_id"], "ten_goi": d["ten_goi"], "bat_dau": d["bat_dau"], "het_han": d.get("het_han"),
            "thu_lai": d.get("thu_lai", 0), "wol": d.get("wol", False), "tong": len(may), "xong": sum(1 for v in may.values() if v["xong"]),
            "dang": sum(1 for v in may.values() if v["tt"] in ("cho", "dang_chay")), "cho": sum(1 for v in may.values() if v["tt"] in CHO),
            "dem": dem, "may": may}


def trang_thai(dot_id):
    d = DOT_TK.doc().get(dot_id)
    return None if d is None else _tom_tat(d)


def danh_sach_dot():
    """[(dot_id, tom_tat)] moi nhat truoc."""
    return sorted(((k, _tom_tat(v)) for k, v in DOT_TK.doc().items()), key=lambda x: -x[1]["bat_dau"])


def huy_cho(dot_id):
    n = 0
    for mid, x in ((DOT_TK.doc().get(dot_id) or {}).get("may") or {}).items():
        if x["tt"] in CHO:
            _dat(dot_id, mid, tt="huy", tb="Đã hủy, không chạy nữa.")
            n += 1
    return n


def chay_lai_loi(dot_id):
    """May loi / het han / da huy -> cho chay lai (gia han them 7 ngay neu dot da qua han)."""
    d = DOT_TK.doc().get(dot_id)
    if not d:
        return 0
    ids = [k for k, x in d["may"].items() if x["tt"] in ("loi", "het_han", "huy")]
    if ids and time.time() > d.get("het_han", 0) - 86400:
        DOT_TK.sua(lambda ds: ds[dot_id].__setitem__("het_han", time.time() + 7 * 86400) if dot_id in ds else None)
    for i in ids:
        _dat(dot_id, i, tt="thu_lai", tb="Chạy lại theo yêu cầu.", lan=0, tiep=0)
    danh_thuc()
    return len(ids)
