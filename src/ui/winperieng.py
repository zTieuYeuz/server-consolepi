# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi - WINPE RIENG trong menu PXE (Sergei Strelec, Hiren's BootCD PE, ban
tu build bang Windows ADK...).

VI SAO (anh Thoai 01/10/2026: "loai 2 em nha"): muc WinPE cuu ho cu chi dung
boot.wim CUA BO CAI WINDOWS va THAY man hinh khoi dong bang cua so lenh cua Console
System. WinPE rieng thi phai boot NGUYEN BAN - giu giao dien, cong cu cua no.

CACH LAM:
  - File WinPE tai len o tab "WinPE" (BOOT_DIR - da co tai file lon + thanh tien
    trinh). Moi muc menu tro toi 1 file .wim trong BOOT_DIR; xoa file = muc tu mat.
  - File .iso: tach file .wim WinPE ben trong ra BOOT_DIR/<ten iso>.wim (uu tien
    sources/boot.wim - kieu Hiren's/ADK; khong co thi lay file .wim LON NHAT - kieu
    Strelec). Tach o luong nen, xong moi dua vao menu.
  - Menu iPXE: `kernel wimboot` + `initrd <file>.wim boot.wim` + `boot` - KHONG chen
    winpeshl.ini/startnet.cmd/driver nao. wimboot tu lay bootmgr.exe trong chinh file
    .wim, chon image co "Boot Index" (giong het muc cuu ho dang chay o BIOS/UEFI/SB).

GIOI HAN THAT:
  - File .wim phai la anh boot Windows that (co winload) - kiem luc them. WinPE rut gon
    KHONG kem bootmgr (kieu WDS) thi muon bootmgr.exe/bootmgfw.efi ky Microsoft tu 1 bo
    Windows da co (_bao_dam_bootmgr) va dua kem qua wimboot.
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
# bootmgr MUON cho WinPE rut gon (xem _bao_dam_bootmgr) - ngoai BOOT_DIR de khong hien o tab WinPE
DIR_BOOTMGR = os.path.join(_d.DEPLOY_DIR, "winpe-bootmgr")
# WDS tu cap ca bo nay cho WinPE; W11x64.wim cua anh Thoai thieu het (lab 01/10/2026: thieu
# bootmgr -> tu choi; them bootmgr -> UEFI bao "\\EFI\\Microsoft\\Boot\\BCD 0xc000000f").
# EFI/ va PCAT/ = BCD + boot.sdi cua dia cai Windows (Windows\\Boot\\DVD\\...) cho UEFI / BIOS.
FILE_MUON = ("bootmgr.exe", "bootmgfw.efi", "EFI/BCD", "EFI/boot.sdi", "PCAT/BCD", "PCAT/boot.sdi")
_KHOA = threading.Lock()
# Trang thai tach ISO dang chay (chi 1 viec 1 luc)
_TACH = {"chay": False, "file": "", "ten": "", "loi": "", "xong": "", "luc": 0, "buoc": ""}


def _7z():
    """7z (trixie) hoac 7zz (bookworm - ISO 32-bit), giong ui/isotach.py."""
    return shutil.which("7z") or shutil.which("7zz") or "7z"


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
                       "cd": os.path.getsize(p), "muon_bootmgr": bool(m.get("muon_bootmgr"))})
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
    (ok, thong_bao, can_muon). File .wim phai: doc duoc, co image boot duoc (Boot Index,
    hoac chi 1 image) va image do co winload (la anh boot Windows that).

    can_muon=True: image KHONG kem bootmgr (Windows\\Boot\\PXE\\bootmgr.exe /
    Windows\\Boot\\EFI\\bootmgfw.efi) - WinPE rut gon kieu WDS (anh Thoai 01/10/2026,
    W11x64.wim: "trong WDS chi can quang file nay vo la boot"). WDS tu cap bootmgr cua no;
    o day muon bootmgr cua 1 bo Windows da co (xem _bao_dam_bootmgr).
    """
    try:
        r = subprocess.run(["wiminfo", p], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, f"Không đọc được file .wim ({e}).", False
    if r.returncode != 0:
        return False, "File không phải ảnh .wim hợp lệ (wiminfo báo lỗi).", False
    so = re.search(r"^Image Count:\s*(\d+)", r.stdout, re.M)
    bi = re.search(r"^Boot Index:\s*(\d+)", r.stdout, re.M)
    so = int(so.group(1)) if so else 0
    bi = int(bi.group(1)) if bi else 0
    if not bi:
        if so != 1:
            return False, (f"File .wim có {so} image nhưng không đánh dấu image nào để boot "
                           "(Boot Index = 0) - không phải ảnh WinPE boot được."), False
        bi = 1
    try:
        r = subprocess.run(["wimlib-imagex", "dir", p, str(bi), "--path=/Windows"],
                           capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, f"Không đọc được bên trong file .wim ({e}).", False
    ds = r.stdout.lower()
    if not re.search(r"^/windows/system32/(boot/)?winload\.(efi|exe)$", ds, re.M):
        return False, ("Image boot không có winload (Windows\\System32\\winload.efi) - "
                       "không phải ảnh WinPE / boot.wim."), False
    co = ("/windows/boot/pxe/bootmgr.exe" in ds and "/windows/boot/efi/bootmgfw.efi" in ds)
    return True, (f"Ảnh WinPE hợp lệ (image {bi}/{so})."
                  + ("" if co else " File không kèm bootmgr (kiểu WDS) - dùng bootmgr ký "
                                   "Microsoft lấy từ bộ Windows đã có.")), not co


def _build_wim(p):
    """So build Windows cua image boot trong file .wim (0 neu khong doc duoc)."""
    try:
        r = subprocess.run(["wiminfo", p], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return 0
    bd = re.findall(r"^Build:\s*(\d+)", r.stdout, re.M)
    if not bd:
        bd = re.findall(r"10\.0\.(\d{5})", r.stdout)
    return int(bd[-1]) if bd else 0


def _bao_dam_bootmgr(build_pe=0):
    """
    (ok, thong_bao). Bao dam DIR_BOOTMGR co bootmgr.exe (BIOS) + bootmgfw.efi (UEFI,
    ky Microsoft - chay ca Secure Boot), lay tu boot.wim cua bo Windows co BUILD MOI
    NHAT trong "Tai nguyen > He dieu hanh"; may chua co bo Windows nao thi tai tu kho trung
    tam (kho tach tu ISO Windows cua kho). Chi lam 1 lan; xoa thu muc de lay lai.
    """
    if all(os.path.isfile(os.path.join(DIR_BOOTMGR, f)) for f in FILE_MUON):
        return True, ""
    ung = []
    for o in _d.danh_sach_os():
        p = _d.duong_boot_wim(o["id"])
        if not os.path.isfile(p):
            continue
        try:
            r = subprocess.run(["wiminfo", p], capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            continue
        bi = re.search(r"^Boot Index:\s*(\d+)", r.stdout, re.M)
        bd = re.findall(r"^Build:\s*(\d+)", r.stdout, re.M)
        ung.append((int(bd[-1]) if bd else 0, p, int(bi.group(1)) if bi and bi.group(1) != "0" else 1))
    # 1. bo Windows co tren may - chon build GAN build WinPE nhat (lab 02/10/2026: bootmgr
    #    26H2 + WinPE 22000 -> Secure Boot 0xc000000f; bootmgr 19041 chay ca 3 kieu may).
    #    Khong biet build WinPE thi lay ban moi nhat nhu truoc.
    thu_tu = (sorted(ung, key=lambda x: abs(x[0] - build_pe)) if build_pe
              else sorted(ung, reverse=True))
    for _bd, p, bi in thu_tu:
        tam = DIR_BOOTMGR + ".tam"
        shutil.rmtree(tam, ignore_errors=True)
        os.makedirs(tam)
        r = subprocess.run(["wimlib-imagex", "extract", p, str(bi),
                            "/Windows/Boot/PXE/bootmgr.exe", "/Windows/Boot/EFI/bootmgfw.efi",
                            "/Windows/Boot/DVD/EFI", "/Windows/Boot/DVD/PCAT",
                            f"--dest-dir={tam}", "--no-acls", "--no-attributes"],
                           capture_output=True, text=True, timeout=300)
        if r.returncode == 0 and all(os.path.isfile(os.path.join(tam, f)) for f in FILE_MUON):
            shutil.rmtree(DIR_BOOTMGR, ignore_errors=True)
            os.replace(tam, DIR_BOOTMGR)
            return True, ""
        shutil.rmtree(tam, ignore_errors=True)
    # 2. May chua co bo Windows nao (anh Thoai 02/10/2026: "tai NASIBOOT ve thi bao phai co
    #    1 Windows san") -> lay tu KHO TRUNG TAM (kho tu tach tu ISO Windows tren kho).
    #    Khong nhung san vao ISO: file cua Microsoft, khong duoc phan phoi kem san pham.
    loi_kho = "máy chưa kết nối kho trung tâm"
    try:
        from . import khotrungtam as _kt
        import zipfile
        ch = _kt.doc_cauhinh()
        if ch:
            tam = DIR_BOOTMGR + ".tam"
            shutil.rmtree(tam, ignore_errors=True)
            os.makedirs(tam)
            ok, loi_kho = _kt.tai_bo_khoi_dong(ch, os.path.join(tam, "bo.zip"))
            if ok:
                with zipfile.ZipFile(os.path.join(tam, "bo.zip")) as z:
                    for f in FILE_MUON:              # CHI lay dung 6 ten biet truoc
                        dich = os.path.join(tam, *f.split("/"))
                        os.makedirs(os.path.dirname(dich), exist_ok=True)
                        with z.open(f) as nguon, open(dich, "wb") as ra:
                            shutil.copyfileobj(nguon, ra)
                os.remove(os.path.join(tam, "bo.zip"))
                shutil.rmtree(DIR_BOOTMGR, ignore_errors=True)
                os.replace(tam, DIR_BOOTMGR)
                return True, ""
            shutil.rmtree(tam, ignore_errors=True)
    except Exception as e:
        loi_kho = f"{type(e).__name__}: {e}"
        shutil.rmtree(DIR_BOOTMGR + ".tam", ignore_errors=True)
    return False, ("File WinPE này không kèm bootmgr (kiểu WDS). Cần 1 bộ Windows có boot.wim "
                   "ở \"Tài nguyên > Hệ điều hành\", hoặc kết nối kho trung tâm có ISO Windows "
                   f"(lần thử kho: {loi_kho}).")


# ------------------------------------------------------------- them / bo
def them(file, ten):
    """Them 1 file trong BOOT_DIR vao menu. .iso -> tach nen roi tu them."""
    p = _d._duong_dan_trong(_d.BOOT_DIR, file)
    if not p or not os.path.isfile(p):
        return False, "Không tìm thấy file trong tab WinPE."
    ten = (ten or "").strip()[:60] or os.path.splitext(os.path.basename(p))[0]
    if p.lower().endswith(".iso"):
        return _bat_dau_tach(p, ten)
    if not p.lower().endswith(".wim"):
        return False, "Chỉ nhận file .wim hoặc .iso."
    ok, tb, can_muon = kiem_wim(p)
    if not ok:
        return False, tb
    if can_muon:
        ok, loi = _bao_dam_bootmgr(_build_wim(p))
        if not ok:
            return False, loi
    _them_vao_ds(os.path.basename(p), ten, can_muon)
    return True, f'Đã đưa "{ten}" vào menu PXE. {tb}'


def them_dong_bo(file, ten):
    """
    Nhu them() nhung file .iso thi TACH NGAY trong luong dang goi (dung cho tai tu kho
    trung tam - da chay o luong nen, xong moi bao "xong"). Cap nhat menu PXE luon.
    """
    p = _d._duong_dan_trong(_d.BOOT_DIR, file)
    if not p or not os.path.isfile(p):
        return False, "Không tìm thấy file vừa tải."
    ten = (ten or "").strip()[:60] or os.path.splitext(os.path.basename(p))[0]
    if p.lower().endswith(".iso"):
        with _KHOA:
            if _TACH["chay"]:
                return False, "Đang tách một ISO WinPE khác - đợi xong rồi tải lại."
            _TACH.update(chay=True, file=os.path.basename(p), ten=ten, loi="", xong="",
                         luc=time.time(), buoc="")
        _tach(p, ten)                       # tu cap nhat menu PXE khi xong
        return (False, _TACH["loi"]) if _TACH["loi"] else (True, _TACH["xong"])
    ok, msg = them(file, ten)
    if ok:
        try:
            from . import pxe as _pxe
            msg += _pxe.cap_nhat_menu()
        except Exception:
            pass
    return ok, msg


def ten_wim_tu_iso(ten_iso):
    """Ten file .wim tach ra tu 1 ISO (cung quy tac voi _tach)."""
    return _d.ten_an_toan(os.path.splitext(os.path.basename(ten_iso))[0] + ".wim")


def _them_vao_ds(file, ten, muon=False):
    with _KHOA:
        ds = [m for m in _doc() if m["file"] != file]
        ds.append({"file": file, "ten": ten, "muon_bootmgr": bool(muon)})
        _ghi(ds)


def bo(file):
    """Bo khoi menu (KHONG xoa file - van nam o tab WinPE)."""
    with _KHOA:
        ds = _doc()
        moi = [m for m in ds if m["file"] != file]
        if len(moi) == len(ds):
            return False, "Mục này không có trong menu."
        _ghi(moi)
    return True, "Đã bỏ khỏi menu PXE (file vẫn còn ở danh sách File WinPE)."


# ------------------------------------------------------------- tach tu ISO
def trang_thai_tach():
    return dict(_TACH)


def _chon_wim(iso):
    """Duong dan file .wim WinPE trong ISO: sources/boot.wim, khong co thi .wim lon nhat."""
    r = subprocess.run([_7z(), "l", "-slt", iso], capture_output=True, text=True, timeout=120)
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


def _gop_apps(iso, wim, tam):
    """
    Bo cuu ho kieu USB (Anhdv Boot...) de phan lon cong cu NGOAI file .wim, trong thu muc
    \\Apps o goc USB - WinPE khoi dong xong tu quet cac o tim \\Apps\\ppApps. Boot qua mang
    khong co USB -> chi con ~10 cong cu (lab 03/10/2026, Anhdv Boot Free 26.2). WinPE do CO
    quet ca o X:, nen GOP thu muc Apps vao chinh file .wim (X:\\Apps) la du bo ~40 cong cu,
    khong can USB hay chia se mang (da boot that trong lab). True neu co gop.
    """
    r = subprocess.run([_7z(), "l", "-slt", iso], capture_output=True, text=True, timeout=120)
    co = any(dong.strip().replace("\\", "/") in ("Path = Apps", "Path = apps", "Path = APPS")
             for dong in r.stdout.splitlines())
    if not co:
        return False
    _TACH["buoc"] = "Tách thư mục công cụ Apps (vài phút)..."
    thu = os.path.join(tam, "apps")
    r = subprocess.run([_7z(), "x", "-y", f"-o{thu}", iso, "Apps"],
                       capture_output=True, text=True, timeout=3600)
    goc = next((os.path.join(thu, n) for n in os.listdir(thu) if n.lower() == "apps"), None) \
        if os.path.isdir(thu) else None
    if r.returncode != 0 or not goc:
        raise RuntimeError("Không tách được thư mục Apps khỏi ISO (đĩa đầy?).")
    _TACH["buoc"] = "Gộp thư mục Apps vào WinPE (Pi nén lại, có thể 10-20 phút)..."
    r = subprocess.run(["wimlib-imagex", "update", wim, "1", f"--command=add '{goc}' /Apps"],
                       capture_output=True, text=True, timeout=7200)
    shutil.rmtree(thu, ignore_errors=True)
    if r.returncode != 0:
        raise RuntimeError("Gộp thư mục Apps vào WinPE thất bại: " + (r.stderr or "")[-200:])
    return True


def _bat_dau_tach(iso, ten):
    with _KHOA:
        if _TACH["chay"]:
            return False, "Đang tách một ISO WinPE khác - đợi xong rồi làm tiếp."
        _TACH.update(chay=True, file=os.path.basename(iso), ten=ten, loi="", xong="",
                     luc=time.time(), buoc="")
    threading.Thread(target=_tach, args=(iso, ten), daemon=True).start()
    return True, f'Đang tách WinPE từ "{os.path.basename(iso)}" - xong sẽ tự vào menu PXE.'


def _tach(iso, ten):
    tam = None
    try:
        trong = _chon_wim(iso)
        dich_ten = ten_wim_tu_iso(iso)
        dich = os.path.join(_d.BOOT_DIR, dich_ten)
        tam = os.path.join(_d.BOOT_DIR, f".winpe-tach-{os.getpid()}")
        shutil.rmtree(tam, ignore_errors=True)
        os.makedirs(tam)
        _TACH["buoc"] = f"Tách {trong}..."
        r = subprocess.run([_7z(), "e", "-y", f"-o{tam}", iso, trong],
                           capture_output=True, text=True, timeout=3600)
        ra = os.path.join(tam, os.path.basename(trong.replace("\\", "/")))
        if r.returncode != 0 or not os.path.isfile(ra):
            raise RuntimeError("Tách file .wim khỏi ISO thất bại (đĩa đầy?).")
        ok, tb, can_muon = kiem_wim(ra)
        if not ok:
            raise RuntimeError(f'"{trong}": {tb}')
        if can_muon:
            ok, loi = _bao_dam_bootmgr(_build_wim(ra))
            if not ok:
                raise RuntimeError(loi)
        co_apps = _gop_apps(iso, ra, tam)
        os.replace(ra, dich)
        _them_vao_ds(dich_ten, ten, can_muon)
        try:
            from . import pxe as _pxe
            _pxe.cap_nhat_menu()
        except Exception:
            pass
        _TACH.update(xong=f'Đã tách "{trong}"'
                          + (' và gộp thư mục công cụ Apps' if co_apps else '')
                          + f' thành {dich_ten} ({_d.co_kich_thuoc(os.path.getsize(dich))}), '
                          f'đưa "{ten}" vào menu PXE. Có thể xóa file ISO gốc để đỡ tốn chỗ.'
                          + (' Máy khách cần RAM từ 4 GB (cả bộ công cụ nạp vào RAM).'
                             if co_apps else ''))
    except Exception as e:
        _TACH.update(loi=str(e) or type(e).__name__)
    finally:
        if tam:
            shutil.rmtree(tam, ignore_errors=True)
        _TACH["chay"] = False
