# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Quan ly may tram - TRIEN KHAI WinGet hang loat (mo phong menu Deploy cua OpenUEM: DeployInstall / DeployUninstall /
SelectPackageDeployment / ComputerDeployInstall / ComputerDeployUpdate / ComputerDeployUninstall).

Mot "dot" = 1 hanh dong (cai / go / nang cap) cho 1 goi WinGet tren nhieu may; moi may chay song song (toi da 4),
dung tai khoan da gan cho may do. Ket qua ghi vao lich su (TRIEN_KHAI) va tac vu cua tung may. Xong thi tu lay lai bao cao
may do (de danh sach phan mem cap nhat). Dot luu RAM de xem tien do; lich su luu dia.
"""
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from . import tk_dongco as DC
from . import tk_dulieu as DL
from . import uem_baocao as UBC
from . import uem_buoc as UB
from . import uem_dulieu as UD
from . import uem_ketnoi as UK

_EX = ThreadPoolExecutor(max_workers=4)
_DOT = {}
_KHOA = threading.Lock()
TEN_HANH_DONG = {"cai": "Cài đặt", "go": "Gỡ cài đặt", "nang": "Nâng cấp"}


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


def _chay_may(dot_id, may_id):
    d = _DOT[dot_id]
    m = DL.tim(DL.MAY.doc(), may_id)
    ten_may = (m or {}).get("bi_danh") or (m or {}).get("ten") or (m or {}).get("ip", "?")
    tt, tb = "loi", "Không tìm thấy máy."
    try:
        if m:
            c, mk, _cach = UK.ket_noi(m)
            if d["hanh_dong"] == "nang":
                out, err = DC._chay_ps(c, _ps_nang(d["goi_id"]))
                mm = re.search(r"ST=(DA_DAT|DA_LAM|LOI)\s*(.*)", out)
                tt, tb = ({"DA_DAT": "da_dat", "DA_LAM": "da_lam", "LOI": "loi"}[mm.group(1)], mm.group(2).strip()) if mm else ("loi", (err or out)[:300])
            else:
                tt, tb = UB.chay(c, m["ip"], "winget_cai" if d["hanh_dong"] == "cai" else "winget_go", {"goi_id": d["goi_id"]})
    except UK.LoiMay as e:
        tt, tb = "loi", str(e)
    except Exception as e:
        tt, tb = "loi", DC._loi_dep(e)
    ok = tt != "loi"
    with _KHOA:
        d["may"][may_id] = {"ten": ten_may, "tt": tt, "tb": tb, "xong": True}
        d["xong"] += 1
    UD.TRIEN_KHAI.sua(lambda ds: (ds.append({"luc": time.time(), "may_id": may_id, "may": ten_may, "goi_id": d["goi_id"], "ten_goi": d["ten_goi"],
                                              "hanh_dong": d["hanh_dong"], "ok": ok, "tt": tt, "tb": tb[:300]}), ds.__setitem__(slice(None), ds[-2000:])))
    UD.ghi_tac_vu(may_id, "trien_khai", f'{TEN_HANH_DONG[d["hanh_dong"]]} {d["ten_goi"]}', ok, tb)
    if m and ok and tt == "da_lam":
        UBC.chay_nen(may_id)               # cap nhat danh sach phan mem


def bat_dau(hanh_dong, goi_id, ten_goi, may_ids):
    """(dot_id, loi)"""
    if hanh_dong not in TEN_HANH_DONG:
        return None, "Hành động không hợp lệ."
    if goi_id != "*" and not re.fullmatch(r"[A-Za-z0-9._+-]{2,100}", goi_id or ""):
        return None, "Mã gói WinGet không hợp lệ."
    ds_may = DL.MAY.doc()
    ids = [i for i in dict.fromkeys(may_ids) if DL.tim(ds_may, i)]
    if not ids:
        return None, "Chưa chọn máy nào."
    dot_id = UD.moi_id()
    with _KHOA:
        _DOT[dot_id] = {"hanh_dong": hanh_dong, "goi_id": goi_id, "ten_goi": ten_goi or goi_id, "bat_dau": time.time(), "tong": len(ids), "xong": 0,
                        "may": {i: {"ten": (DL.tim(ds_may, i).get("bi_danh") or DL.tim(ds_may, i).get("ten") or DL.tim(ds_may, i)["ip"]), "tt": "cho", "tb": "", "xong": False} for i in ids}}
        for k in [k for k, v in _DOT.items() if time.time() - v["bat_dau"] > 6 * 3600]:
            _DOT.pop(k, None)
    for i in ids:
        _EX.submit(_chay_may, dot_id, i)
    return dot_id, ""


def trang_thai(dot_id):
    with _KHOA:
        d = _DOT.get(dot_id)
        return None if d is None else {k: (dict(v) if isinstance(v, dict) else v) for k, v in d.items()}
