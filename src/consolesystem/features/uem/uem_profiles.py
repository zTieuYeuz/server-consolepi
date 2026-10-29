# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Quan ly may tram - PROFILES (mo phong Profiles cua OpenUEM: openuem-console .../profiles.go + tasks.go).

Profile = danh sach TAC VU khai bao trang thai mong muon (cai/go WinGet, registry, nguoi dung/nhom cuc bo, MSI, PowerShell),
ap dung cho cac may theo THE (tag) hoac TAT CA may. Moi 30 phut (cai dat duoc) Console System kiem tra tung may: lam
dung cac tac vu CHUA dung trang thai (xem uem_buoc.py: kiem tra truoc, khong lam lai thu da dung). Tac vu loi:
  - mac dinh DUNG o do va danh dau may co VAN DE (trang "Van de" cua profile, giong ProfileIssues cua OpenUEM);
  - neu tac vu bat "bo qua loi" thi chay tiep tac vu sau.
May tat / mat mang: thu lai moi 5 phut. Tac vu PowerShell "chay mot lan" thanh cong roi khong chay lai.
"""
from consolesystem.core.nhatky import bo_qua as _bo_qua
import sys as _sys
_sys.modules["ui.uem_profiles"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import hashlib
import json
import re
import secrets
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from ui import tk_dongco as DC
from ui import tk_dulieu as DL
from ui import uem_buoc as UB
from ui import uem_dulieu as UD
from ui import uem_ketnoi as UK

_EX = ThreadPoolExecutor(max_workers=4)
_KHOA = threading.Lock()
_DANG = set()
_BAT_DAU = False


def may_ap_dung(p):
    return UD.may_theo_the(p.get("the", []), tat_ca=bool(p.get("ap_dung_tat_ca")), nhom_ids=p.get("nhom_may", []))


def thu_tu_task(p):
    return list(p.get("tasks", []))


def tu_tri(t):
    """Tac vu tu chua duoc (agent co the tu ap dung khi Console System tat): khong can mat khau, khong can file tren Console System."""
    ts = t.get("tham_so", {})
    if t["loai"] == "user_them" and ts.get("mat_khau"):
        return False
    if t["loai"] == "msi_cai":
        d = ts.get("duong_dan", "")
        if d.lower().endswith(".msi") and not re.match(r"^(https?://|[A-Za-z]:\\|\\\\)", d):
            return False                      # file MSI trong kho trung tam: link tai chi song 2 gio, phai do Console System dua
    return True


def _chu_ky_phut():
    return max(5, int(UD.cai_dat().get("tan_suat_profile", 30)))


def _task_tu_tri(p):
    return [t for t in p.get("tasks", []) if t.get("bat", True) and tu_tri(t)]


def _ver_bundle(p):
    mo = [(t["id"], str(t.get("ver")), t["loai"], json.dumps(t["tham_so"], sort_keys=True), bool(t.get("bo_qua_loi"))) for t in _task_tu_tri(p)]
    return hashlib.sha1(json.dumps([mo, _chu_ky_phut(), p["id"]]).encode(), usedforsecurity=False).hexdigest()[:12]


def mong_muon(m):
    """{profile_id: ver} cac profile agent cua may nay PHAI giu de tu ap dung."""
    ra = {}
    if not m.get("giam_sat", True):
        return ra
    for p in UD.PROFILES.doc():
        if p.get("bat") and _task_tu_tri(p) and any(x["id"] == m["id"] for x in may_ap_dung(p)):
            ra[p["id"]] = _ver_bundle(p)
    return ra


def tao_bundle(m, pid):
    p = DL.tim(UD.PROFILES.doc(), pid)
    return {"id": secrets.token_hex(8), "kieu": "profile", "pid": pid, "ver": _ver_bundle(p), "chu_ky": _chu_ky_phut(),
            "tasks": [{"id": t["id"], "loai": t["loai"], "script": UB.tao_kich_ban(t["loai"], t["tham_so"], m["ip"]), "bo_qua_loi": bool(t.get("bo_qua_loi")),
                       "mot_lan": t["loai"] == "powershell" and t["tham_so"].get("chay", "mot_lan") != "luon", "ver": str(t.get("ver")), "timeout": 3600}
                      for t in _task_tu_tri(p)]}


def viec_dong_bo(m, pf):
    """Viec dong bo profile tu tri cho agent (1 viec moi nhip): gui bundle thieu/cu, go bundle thua. None neu da khop."""
    mong = mong_muon(m)
    for pid, ver in mong.items():
        if pf.get(pid) != ver:
            return tao_bundle(m, pid)
    for pid in pf:
        if pid not in mong:
            return {"id": secrets.token_hex(8), "kieu": "profile_go", "pid": str(pid)}
    return None


def nhan_ket_qua_agent(m, items):
    """Ket qua profile do agent TU ap dung (gui bu o nhip sau). Tra ve danh sach 'pid|luc' de agent xoa khoi hang cho gui."""
    mid, acks = m["id"], []
    for it in items:
        pid, luc = str(it.get("pid", "")), it.get("luc")
        acks.append(f"{pid}|{luc}")
        p = DL.tim(UD.PROFILES.doc(), pid)
        if not p or not isinstance(it.get("tasks"), dict):
            continue
        ten_task = {t["id"]: t for t in p.get("tasks", [])}

        def luu(tt):
            st = tt.setdefault(pid, {}).setdefault(mid, {"tasks": {}})
            st.setdefault("tasks", {})
            for tid, r in it["tasks"].items():
                if tid not in ten_task or not isinstance(r, dict):
                    continue
                cu = st["tasks"].get(tid, {})
                tt_ = str(r.get("tt", ""))[:20]
                st["tasks"][tid] = {"tt": tt_, "tb": str(r.get("tb", ""))[:400], "luc": r.get("luc") or luc, "ver": ten_task[tid].get("ver"),
                                    "ok_luc": (r.get("luc") or luc) if tt_ != "loi" else cu.get("ok_luc", 0)}
            hop_le = [t["id"] for t in p.get("tasks", []) if t.get("bat", True)]
            co_loi = any(st["tasks"].get(i, {}).get("tt") == "loi" for i in hop_le)
            st.update(luc=luc, trang_thai="loi" if co_loi else "ok",
                      tom_tat=("Có tác vụ lỗi, xem chi tiết." if co_loi else (f"Agent đã tự áp dụng {it.get('lam')} thay đổi." if it.get("lam") else "Máy đã đúng cấu hình.")))
        UD.TRANG_THAI_PROFILE.sua(luu)
        for tid, r in it["tasks"].items():
            if tid in ten_task and isinstance(r, dict) and r.get("tt") in ("da_lam", "loi"):
                UD.ghi_tac_vu(mid, "profile", f'{p["ten"]}: {UB.mo_ta(ten_task[tid]["loai"], ten_task[tid]["tham_so"])} (agent tự áp dụng)', r.get("tt") == "da_lam", str(r.get("tb", "")))
    return acks


def chay_profile_may(pid, mid):
    """Ap dung 1 profile len 1 may. Ket qua luu o TRANG_THAI_PROFILE[pid][mid]. Tra ve tom tat."""
    p = DL.tim(UD.PROFILES.doc(), pid)
    m = DL.tim(DL.MAY.doc(), mid)
    if not p or not m:
        return "Không tìm thấy profile hoặc máy."
    t0 = time.time()
    cu = UD.TRANG_THAI_PROFILE.doc().get(pid, {}).get(mid, {}).get("tasks", {})
    kq = {"luc": t0, "trang_thai": "dang", "tasks": dict(cu)}

    def luu(tt):
        tt.setdefault(pid, {})[mid] = kq
    UD.TRANG_THAI_PROFILE.sua(luu)
    tasks = [t for t in thu_tu_task(p) if t.get("bat", True)]
    tat_ca_id = {t["id"] for t in tasks}
    if UK.co_agent(m) and all(tu_tri(t) for t in tasks):
        try:                                      # agent tu ap dung: chi bao no chay ngay, ket qua se tu ve o nhip sau
            from ui import uem_agent as UA
            UA.them_viec(m["id"], "profile_chay", pid=pid, timeout=60)
            return "Đã yêu cầu agent áp dụng ngay (kết quả sẽ về sau ít phút)."
        except Exception as e:
            return f"Không gửi được yêu cầu cho agent: {e}"
    if not UK.co_the_ket_noi(m):
        kq.update(trang_thai="loi", tom_tat="Máy chưa gán tài khoản quản trị và chưa có agent.")
        UD.TRANG_THAI_PROFILE.sua(luu)
        return kq["tom_tat"]
    try:
        c, mk, cach = UK.ket_noi(m)
    except UK.LoiMay as e:
        kq.update(trang_thai="offline", tom_tat=str(e), luc=t0)
        UD.TRANG_THAI_PROFILE.sua(luu)
        return kq["tom_tat"]
    except Exception as e:
        kq.update(trang_thai="offline", tom_tat=DC._loi_dep(e))
        UD.TRANG_THAI_PROFILE.sua(luu)
        return kq["tom_tat"]
    c_winrm = [c if cach == "winrm" else None]
    da_lam = loi = 0
    dung = False
    if cach == "agent":
        tasks = [t for t in tasks if not tu_tri(t)]          # phan con lai agent tu lam (bundle); o day chi chay tac vu can Console System
    for t in tasks:
        ts_old = kq["tasks"].get(t["id"], {})
        if dung:
            kq["tasks"][t["id"]] = {"tt": "bo_qua", "tb": "Bỏ qua vì tác vụ trước bị lỗi.", "luc": time.time(), "ok_luc": ts_old.get("ok_luc", 0)}
            continue
        if t["loai"] == "powershell" and t["tham_so"].get("chay", "mot_lan") != "luon" and ts_old.get("ok_luc") and ts_old.get("ver") == t.get("ver"):
            kq["tasks"][t["id"]] = dict(ts_old, tt="da_chay_truoc", tb="Đã chạy thành công trước đó (chế độ chạy một lần).")
            continue
        try:
            cc = c
            if t["loai"] == "user_them" and t["tham_so"].get("mat_khau") and cach == "agent":
                # mat khau khong di qua agent (HTTP khong ma hoa): chuyen sang WinRM neu co tai khoan, khong thi tu choi
                if c_winrm[0] is None:
                    c_winrm[0] = UK.ket_noi(m, bat_buoc_winrm=True)[0]
                cc = c_winrm[0]
            tt, tb = UB.chay(cc, m["ip"], t["loai"], t["tham_so"])
        except UK.LoiMay as e:
            tt, tb = "loi", "Tác vụ mang mật khẩu chỉ chạy qua WinRM: " + str(e)
        except Exception as e:
            tt, tb = "loi", DC._loi_dep(e, mk)
        kq["tasks"][t["id"]] = {"tt": tt, "tb": tb, "luc": time.time(), "ver": t.get("ver"),
                                "ok_luc": time.time() if tt != "loi" else (ts_old.get("ok_luc", 0) if ts_old.get("ver") == t.get("ver") else 0)}
        if tt == "da_lam":
            da_lam += 1
            UD.ghi_tac_vu(mid, "profile", f'{p["ten"]}: {UB.mo_ta(t["loai"], t["tham_so"])}', True, tb)
        elif tt == "loi":
            loi += 1
            UD.ghi_tac_vu(mid, "profile", f'{p["ten"]}: {UB.mo_ta(t["loai"], t["tham_so"])}', False, tb)
            if not t.get("bo_qua_loi"):
                dung = True
        UD.TRANG_THAI_PROFILE.sua(luu)
    for tid in [x for x in kq["tasks"] if x not in tat_ca_id]:
        kq["tasks"].pop(tid, None)
    loi = loi or sum(1 for r in kq["tasks"].values() if r.get("tt") == "loi")
    kq.update(luc=time.time(), trang_thai="loi" if loi else "ok",
              tom_tat=("Có tác vụ lỗi, xem chi tiết." if loi else (f"Đã áp dụng {da_lam} thay đổi." if da_lam else "Máy đã đúng cấu hình.")))
    UD.TRANG_THAI_PROFILE.sua(luu)
    return kq["tom_tat"]


def _viec(pid, mid):
    try:
        chay_profile_may(pid, mid)
    except Exception as e:
        loi = f"Lỗi bất ngờ: {str(e)[:200]}"

        def luu(tt):
            tt.setdefault(pid, {})[mid] = {"luc": time.time(), "trang_thai": "loi", "tom_tat": loi, "tasks": {}}
        UD.TRANG_THAI_PROFILE.sua(luu)
    finally:
        with _KHOA:
            _DANG.discard((pid, mid))


def chay_nen(pid, mid):
    with _KHOA:
        if (pid, mid) in _DANG:
            return False
        _DANG.add((pid, mid))
    _EX.submit(_viec, pid, mid)
    return True


def dang_chay(pid, mid):
    with _KHOA:
        return (pid, mid) in _DANG


def ap_dung_ngay(pid):
    """Ap dung profile len moi may thuoc pham vi ngay bay gio. Tra ve so may dua vao hang doi."""
    p = DL.tim(UD.PROFILES.doc(), pid)
    if not p:
        return 0
    n = 0
    for m in may_ap_dung(p):
        if UK.co_the_ket_noi(m) and chay_nen(pid, m["id"]):
            n += 1
    return n


def _tick():
    chu_ky = max(5, int(UD.cai_dat().get("tan_suat_profile", 30))) * 60
    now = time.time()
    tt = UD.TRANG_THAI_PROFILE.doc()
    for p in UD.PROFILES.doc():
        if not p.get("bat") or not p.get("tasks"):
            continue
        for m in may_ap_dung(p):
            if not UK.co_the_ket_noi(m):
                continue
            if UK.co_agent(m) and all(tu_tri(t) for t in p["tasks"] if t.get("bat", True)):
                continue                      # agent TU ap dung profile nay (ke ca khi Console System tat) - ket qua tu ve qua nhip
            st = tt.get(p["id"], {}).get(m["id"], {})
            cho = 300 if st.get("trang_thai") in ("offline",) else chu_ky
            if st.get("trang_thai") == "dang":
                cho = 600                     # dich vu khoi dong lai giua luot: chay lai sau 10 phut
            if now - st.get("luc", 0) >= cho:
                chay_nen(p["id"], m["id"])


def khoi_dong_bo_lap():
    global _BAT_DAU
    with _KHOA:
        if _BAT_DAU:
            return
        _BAT_DAU = True

    def vong():
        time.sleep(40)
        while True:
            try:
                _tick()
            except Exception as _loi:
                _bo_qua(_loi)
            time.sleep(30)
    threading.Thread(target=vong, daemon=True, name="uem-profiles").start()


def van_de(pid):
    """[(may, task_ten, thong_diep)] cac tac vu dang loi cua profile (trang 'Van de')."""
    p = DL.tim(UD.PROFILES.doc(), pid)
    if not p:
        return []
    ra = []
    tt = UD.TRANG_THAI_PROFILE.doc().get(pid, {})
    ten_task = {t["id"]: UB.mo_ta(t["loai"], t["tham_so"]) for t in p.get("tasks", [])}
    for m in may_ap_dung(p):
        st = tt.get(m["id"], {})
        if st.get("trang_thai") == "offline":
            ra.append((m, "(chưa kết nối được)", st.get("tom_tat", "")))
        for tid, r in st.get("tasks", {}).items():
            if r.get("tt") == "loi" and tid in ten_task:
                ra.append((m, ten_task[tid], r.get("tb", "")))
    return ra
