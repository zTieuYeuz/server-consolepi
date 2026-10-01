# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi - WINPE RIENG trong menu PXE (Sergei Strelec, Hiren's BootCD PE, ban
tu build bang Windows ADK...).

VI SAO (anh Thoai 01/10/2026: "loai 2 em nha"): muc "1. Win PE - cuu ho" chi dung
boot.wim CUA BO CAI WINDOWS va THAY man hinh khoi dong bang cua so lenh cua Console
System. WinPE rieng thi phai boot NGUYEN BAN - giu giao dien, cong cu cua no.

CACH LAM:
  - File WinPE tai len o tab "File boot" (BOOT_DIR - da co tai file lon + thanh tien
    trinh). Moi muc menu tro toi 1 file .wim trong BOOT_DIR; xoa file = muc tu mat.
  - File .iso: tach file .wim WinPE ben trong ra BOOT_DIR/<ten iso>.wim (uu tien
    sources/boot.wim - kieu Hiren's/ADK; khong co thi lay file .wim LON NHAT - kieu
    Strelec). Tach o luong nen, xong moi dua vao menu.
  - Menu iPXE: `kernel wimboot` + `initrd <file>.wim boot.wim` + `boot` - KHONG chen
    winpeshl.ini/startnet.cmd/driver nao. wimboot tu lay bootmgr.exe trong chinh file
    .wim, chon image co "Boot Index" (giong het muc cuu ho dang chay o BIOS/UEFI/SB).

GIOI HAN THAT:
  - File .wim phai la WinPE that (co Windows\\Boot\\PXE\\bootmgr.exe) - kiem luc them,
    thieu thi tu choi, khong de may khach dung o man hinh den.
  - UEFI + Secure Boot: WinPE phai ky boi Microsoft (ban ADK, Hiren's dung bootmgr
    goc thi duoc); ban tu che sua bootmgr se bi firmware chan - Console System khong
    vuot qua duoc.
"""
import json
import os
import re
import shutil
import subprocess
import threading
import time

from . import deployos as _d

FILE_DS = os.path.join(_d.DEPLOY_DIR, "winpe-rieng.json")
_KHOA = threading.Lock()
# Trang thai tach ISO dang chay (chi 1 viec 1 luc)
_TACH = {"chay": False, "file": "", "ten": "", "loi": "", "xong": "", "luc": 0}


# ------------------------------------------------------------------ danh sach
def _doc():
    try:
        with open(FILE_DS, encoding="utf-8") as f:
            ds = json.load(f)
        return [m for m in ds if isinstance(m, dict) and m.get("file")]
    except (OSError, ValueError):
        return []


def _ghi(ds):
    os.makedirs(os.path.dirname(FILE_DS), exist_ok=True)
    tam = FILE_DS + ".tmp"
    with open(tam, "w", encoding="utf-8") as f:
        json.dump(ds, f, ensure_ascii=False, indent=1)
    os.replace(tam, FILE_DS)


def danh_sach():
    """Cac muc WinPE rieng CON file that (theo thu tu them). Moi muc: ten, file, cd."""
    ra = []
    for m in _doc():
        p = _d._duong_dan_trong(_d.BOOT_DIR, m["file"])
        if p and os.path.isfile(p):
            ra.append({"ten": m.get("ten") or m["file"], "file": m["file"],
                       "cd": os.path.getsize(p)})
    return ra


def file_co_the_them():
    """File .wim/.iso trong BOOT_DIR chua co trong menu (de chon o form)."""
    da = {m["file"] for m in _doc()}
    ra = []
    try:
        for n in sorted(os.listdir(_d.BOOT_DIR)):
            if (n.lower().endswith((".wim", ".iso")) and n not in da
                    and os.path.isfile(os.path.join(_d.BOOT_DIR, n))
                    and n not in ("autounattend.img",)):
                ra.append(n)
    except OSError:
        pass
    return ra


# ------------------------------------------------------------ kiem file .wim
def kiem_wim(p):
    """
    (ok, thong_bao). File .wim phai: doc duoc, co image boot duoc (Boot Index, hoac
    chi 1 image) va image do co Windows\\Boot\\PXE\\bootmgr.exe (wimboot can file nay).
    """
    try:
        r = subprocess.run(["wiminfo", p], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, f"Không đọc được file .wim ({e})."
    if r.returncode != 0:
        return False, "File không phải ảnh .wim hợp lệ (wiminfo báo lỗi)."
    so = re.search(r"^Image Count:\s*(\d+)", r.stdout, re.M)
    bi = re.search(r"^Boot Index:\s*(\d+)", r.stdout, re.M)
    so = int(so.group(1)) if so else 0
    bi = int(bi.group(1)) if bi else 0
    if not bi:
        if so != 1:
            return False, (f"File .wim có {so} image nhưng không đánh dấu image nào để boot "
                           "(Boot Index = 0) - không phải ảnh WinPE boot được.")
        bi = 1
    try:
        r = subprocess.run(["wimlib-imagex", "dir", p, str(bi), "--path=/Windows/Boot/PXE"],
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, f"Không đọc được bên trong file .wim ({e})."
    if "bootmgr.exe" not in r.stdout.lower():
        return False, ("Image boot không có Windows\\Boot\\PXE\\bootmgr.exe - không boot qua "
                       "mạng được (wimboot cần file này). Có thể đây không phải WinPE.")
    return True, f"Ảnh WinPE hợp lệ (image {bi}/{so})."


# ------------------------------------------------------------- them / bo
def them(file, ten):
    """Them 1 file trong BOOT_DIR vao menu. .iso -> tach nen roi tu them."""
    p = _d._duong_dan_trong(_d.BOOT_DIR, file)
    if not p or not os.path.isfile(p):
        return False, "Không tìm thấy file trong tab File boot."
    ten = (ten or "").strip()[:60] or os.path.splitext(os.path.basename(p))[0]
    if p.lower().endswith(".iso"):
        return _bat_dau_tach(p, ten)
    if not p.lower().endswith(".wim"):
        return False, "Chỉ nhận file .wim hoặc .iso."
    ok, tb = kiem_wim(p)
    if not ok:
        return False, tb
    _them_vao_ds(os.path.basename(p), ten)
    return True, f'Đã đưa "{ten}" vào menu PXE. {tb}'


def _them_vao_ds(file, ten):
    with _KHOA:
        ds = [m for m in _doc() if m["file"] != file]
        ds.append({"file": file, "ten": ten})
        _ghi(ds)


def bo(file):
    """Bo khoi menu (KHONG xoa file - van nam o tab File boot)."""
    with _KHOA:
        ds = _doc()
        moi = [m for m in ds if m["file"] != file]
        if len(moi) == len(ds):
            return False, "Mục này không có trong menu."
        _ghi(moi)
    return True, "Đã bỏ khỏi menu PXE (file vẫn còn ở danh sách File boot)."


# ------------------------------------------------------------- tach tu ISO
def trang_thai_tach():
    return dict(_TACH)


def _chon_wim(iso):
    """Duong dan file .wim WinPE trong ISO: sources/boot.wim, khong co thi .wim lon nhat."""
    r = subprocess.run(["7z", "l", "-slt", iso], capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError("Không đọc được mục lục ISO (7z báo lỗi).")
    cac = []
    duong, cd = None, 0
    for dong in r.stdout.splitlines() + [""]:
        if dong.startswith("Path = "):
            duong = dong[7:].strip()
        elif dong.startswith("Size = "):
            cd = int(dong[7:].strip() or 0)
        elif not dong.strip() and duong:
            if duong.lower().endswith(".wim"):
                cac.append((duong, cd))
            duong, cd = None, 0
    if not cac:
        raise RuntimeError("Trong ISO không có file .wim nào - không phải ISO WinPE.")
    for duong, _cd in cac:
        if duong.replace("\\", "/").lower() == "sources/boot.wim":
            return duong
    return max(cac, key=lambda x: x[1])[0]


def _bat_dau_tach(iso, ten):
    with _KHOA:
        if _TACH["chay"]:
            return False, "Đang tách một ISO WinPE khác - đợi xong rồi làm tiếp."
        _TACH.update(chay=True, file=os.path.basename(iso), ten=ten, loi="", xong="",
                     luc=time.time())
    threading.Thread(target=_tach, args=(iso, ten), daemon=True).start()
    return True, f'Đang tách WinPE từ "{os.path.basename(iso)}" - xong sẽ tự vào menu PXE.'


def _tach(iso, ten):
    tam = None
    try:
        trong = _chon_wim(iso)
        dich_ten = _d.ten_an_toan(os.path.splitext(os.path.basename(iso))[0] + ".wim")
        dich = os.path.join(_d.BOOT_DIR, dich_ten)
        tam = os.path.join(_d.BOOT_DIR, f".winpe-tach-{os.getpid()}")
        shutil.rmtree(tam, ignore_errors=True)
        os.makedirs(tam)
        r = subprocess.run(["7z", "e", "-y", f"-o{tam}", iso, trong],
                           capture_output=True, text=True, timeout=3600)
        ra = os.path.join(tam, os.path.basename(trong.replace("\\", "/")))
        if r.returncode != 0 or not os.path.isfile(ra):
            raise RuntimeError("Tách file .wim khỏi ISO thất bại (đĩa đầy?).")
        ok, tb = kiem_wim(ra)
        if not ok:
            raise RuntimeError(f'"{trong}": {tb}')
        os.replace(ra, dich)
        _them_vao_ds(dich_ten, ten)
        try:
            from . import pxe as _pxe
            _pxe.cap_nhat_menu()
        except Exception:
            pass
        _TACH.update(xong=f'Đã tách "{trong}" thành {dich_ten} '
                          f'({_d.co_kich_thuoc(os.path.getsize(dich))}) và đưa "{ten}" vào menu PXE. '
                          f'Có thể xóa file ISO gốc để đỡ tốn chỗ.')
    except Exception as e:
        _TACH.update(loi=str(e) or type(e).__name__)
    finally:
        if tam:
            shutil.rmtree(tam, ignore_errors=True)
        _TACH["chay"] = False
