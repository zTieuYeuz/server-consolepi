# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Deploy OS - he dieu hanh (anh WIM/ISO/SxS): liet ke, tao, xoa, chi so ban Pro.

(B4: tach nguyen van tu deployos.py; ten ham/hang giu nguyen, nguon van re-export.)"""
from consolesystem.core.nhatky import bo_qua as _bo_qua
import json
import os
import re
import subprocess
from ui.duongdan import DEPLOY_DIR, BOOT_DIR, APPS_DIR, SCRIPTS_DIR, KICHBAN_DIR, OS_DIR, DRIVERS_DIR, UNGDUNG_DIR, FONTS_DIR, EXT_SCRIPT  # noqa: F401  (B3: khai bao o core/duongdan.py)
from consolesystem.features.deploy_os.dos_chung import (_bao_dam_thu_muc, _duong_dan_trong, co_kich_thuoc, ten_an_toan)  # noqa: F401


# --------------------------------------- he dieu hanh (mo hinh MDT: "Operating Systems")
def danh_sach_os():
    """Danh sach cac bo OS da tai len - moi bo la 1 thu muc rieng chua
    boot.wim + install.wim, giong dung cach MDT nhap "Operating Systems"."""
    _bao_dam_thu_muc()
    ra = []
    try:
        for os_id in sorted(os.listdir(OS_DIR)):
            p = os.path.join(OS_DIR, os_id)
            if not os.path.isdir(p):
                continue
            meta = {}
            try:
                with open(os.path.join(p, "_thongtin.json")) as f:
                    meta = json.load(f)
            except Exception as _loi:
                _bo_qua(_loi)
            co_boot = os.path.isfile(os.path.join(p, "boot.wim"))
            co_install = os.path.isfile(os.path.join(p, "install.wim"))
            kich_thuoc = sum(
                os.path.getsize(os.path.join(p, t))
                for t in ("boot.wim", "install.wim")
                if os.path.isfile(os.path.join(p, t)))
            ra.append({
                "id": os_id,
                "ten_hien_thi": meta.get("ten_hien_thi") or os_id,
                "os_ho": meta.get("os_ho") or "windows",
                "co_boot_wim": co_boot,
                "co_install_wim": co_install,
                "san_sang": co_boot and co_install,
                "kich_thuoc": co_kich_thuoc(kich_thuoc) if kich_thuoc else "0 B",
                # Tai tu kho trung tam (ui/khotrungtam.py) -> id muc tren kho,
                # de trang Kho biet "da co" va tai lai vao dung cho.
                "kho_id": meta.get("kho_id", ""),
            })
    except OSError:
        pass
    return ra

def co_sxs(os_id):
    """Danh sach file .cab goi .NET 3.5 offline cua he dieu hanh (os/<id>/sxs/*.cab), rong neu khong co.
    Co thi luc bung anh Windows (WinPE) bat NetFx3 OFFLINE ~1 phut thay vi tai qua mang ~9 phut."""
    d = os.path.join(OS_DIR, ten_an_toan(os_id), "sxs")
    try:
        return sorted(n for n in os.listdir(d) if n.lower().endswith(".cab"))
    except OSError:
        return []

def lay_os(os_id):
    for o in danh_sach_os():
        if o["id"] == os_id:
            return o
    return None

def duong_boot_wim(os_id):
    return os.path.join(OS_DIR, ten_an_toan(os_id), "boot.wim")

def duong_install_wim(os_id):
    return os.path.join(OS_DIR, ten_an_toan(os_id), "install.wim")

_CACHE_CHI_SO_PRO = {}

def chi_so_anh_pro(os_id):
    """
    Chi so cua phien ban **Windows Pro** trong install.wim/esd. ISO Windows chinh hang
    chua nhieu phien ban (Home, Home N, Pro, Education...) trong 1 file; deploy.cmd
    truoc day luon bung chi so 1 nen co ISO ra Home thay vi Pro. Anh Thoai 04/10/2026:
    "tat ca cac ban Windows deu cai Pro" - nen tu tim ban Pro (Edition ID = Professional),
    khong tao lua chon. Khong co ban Pro nao (hoac wiminfo loi) thi giu chi so 1 nhu cu.
    """
    thu_muc = os.path.join(OS_DIR, ten_an_toan(os_id))
    for ten in ("install.wim", "install.esd"):
        p = os.path.join(thu_muc, ten)
        if os.path.isfile(p):
            break
    else:
        return 1
    try:
        st = os.stat(p)
    except OSError:
        return 1
    khoa = (p, st.st_mtime, st.st_size)
    if khoa in _CACHE_CHI_SO_PRO:
        return _CACHE_CHI_SO_PRO[khoa]
    chi_so = 1
    try:
        r = subprocess.run(["wiminfo", p], capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            for khoi in r.stdout.split("\n\n"):
                m_so = re.search(r"^Index:\s*(\d+)", khoi, re.M)
                m_ed = re.search(r"^Edition ID:\s*(\S+)", khoi, re.M)
                if m_so and m_ed and m_ed.group(1) == "Professional":
                    chi_so = int(m_so.group(1))
                    break
            _CACHE_CHI_SO_PRO.clear()
            _CACHE_CHI_SO_PRO[khoa] = chi_so
    except (OSError, subprocess.SubprocessError):
        pass
    return chi_so

def tao_os_moi(ten_hien_thi, os_ho="windows"):
    _bao_dam_thu_muc()
    ten_hien_thi = (ten_hien_thi or "").strip()
    if not ten_hien_thi:
        return False, "Chưa đặt tên hệ điều hành.", None
    os_id = ten_an_toan(ten_hien_thi.replace(" ", "_")).lower()
    if not os_id:
        return False, "Tên không hợp lệ.", None
    p = os.path.join(OS_DIR, os_id)
    if os.path.isdir(p):
        return False, f'Da co he dieu hanh "{os_id}" roi.', None
    try:
        os.makedirs(p, exist_ok=True)
        with open(os.path.join(p, "_thongtin.json"), "w") as f:
            json.dump({"ten_hien_thi": ten_hien_thi, "os_ho": os_ho}, f,
                      ensure_ascii=False)
    except OSError as e:
        return False, f"Không tạo được: {e}", None
    return True, f'Đã tạo "{ten_hien_thi}".', os_id

def xoa_os(os_id):
    p = _duong_dan_trong(OS_DIR, os_id)
    if not p or not os.path.isdir(p):
        return False, "Không tìm thấy hệ điều hành."
    try:
        import shutil
        shutil.rmtree(p)
    except OSError as e:
        return False, f"Không xóa được: {e}"
    return True, "Đã xóa."
