# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Deploy OS - tien ich chung: duong dan an toan, liet ke file, luu tai len, ten khong dau.

(B4: tach nguyen van tu deployos.py; ten ham/hang giu nguyen, nguon van re-export.)"""
import os
import re
import time
import unicodedata
from ui.duongdan import DEPLOY_DIR, BOOT_DIR, APPS_DIR, SCRIPTS_DIR, KICHBAN_DIR, OS_DIR, DRIVERS_DIR, UNGDUNG_DIR, FONTS_DIR, EXT_SCRIPT  # noqa: F401  (B3: khai bao o core/duongdan.py)
from consolesystem.features.deploy_os.dos_hangso import (EXT_UNGDUNG_ZIP, MIN_FREE_GB, TEN_BUOC)  # noqa: F401


BUOC_DAU = TEN_BUOC[0][0]

SO_BUOC = TEN_BUOC[-1][0]

def so_hien_thi(buoc):
    """So buoc hien cho nguoi dung (buoc noi bo 2 -> "1")."""
    return buoc - BUOC_DAU + 1

# ---------------------------------------------------------------- tien ich
def _bao_dam_thu_muc():
    """Tao san cac thu muc. Kich ban de 700 vi co the chua mat khau."""
    for d in (DEPLOY_DIR, BOOT_DIR, APPS_DIR, SCRIPTS_DIR, OS_DIR, DRIVERS_DIR,
              UNGDUNG_DIR, FONTS_DIR):
        try:
            os.makedirs(d, exist_ok=True)
        except OSError:
            pass
    try:
        os.makedirs(KICHBAN_DIR, exist_ok=True)
        os.chmod(KICHBAN_DIR, 0o700)
    except OSError:
        pass

def bo_dau(s):
    """
    Bo dau tieng Viet + ha chu thuong, de tim kiem khong phu thuoc dau (go tieng
    Viet co dau tren man hinh cam ung rat cham - moi o tim trong du an deu phai
    tim duoc bang chu khong dau). Phai thay tay 'đ'/'Đ': unicodedata khong tach duoc.
    (Chuyen tu ui/thamso.py khi bo tab Tham so cai dat.)
    """
    if not s:
        return ""
    s = str(s).replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower().strip()

def _bo_dau_py(s):
    """
    Bo dau tieng Viet de tim kiem khong phu thuoc dau (xem bo_dau ben tren).
    """
    return bo_dau(s)

def ten_an_toan(name):
    """
    Chi giu ten file tran, bo moi thanh phan duong dan (chan '..' va duong
    dan tuyet doi). Dung chung y het ui/storage.py - da kiem chung on dinh.
    """
    name = os.path.basename(name or "").strip()
    name = re.sub(r"[^A-Za-z0-9._+ -]", "_", name)
    name = name.lstrip(".")
    return name[:150]

def _duong_dan_trong(thu_muc, ten):
    """
    Tra ve duong dan that neu ten hop le VA nam dung trong thu_muc, nguoc
    lai tra None. Kiem tra sau khi giai duong dan that - chan moi kieu vuot
    thu muc (symlink, '..', duong dan tuyet doi).
    """
    ten = ten_an_toan(ten)
    if not ten:
        return None
    p = os.path.join(thu_muc, ten)
    if os.path.realpath(p) != os.path.join(os.path.realpath(thu_muc), ten):
        return None
    return p

def co_kich_thuoc(n):
    for don_vi in ("B", "KB", "MB", "GB"):
        if n < 1024 or don_vi == "GB":
            return f"{n:.1f} {don_vi}" if don_vi != "B" else f"{int(n)} B"
        n /= 1024.0
    return f"{n:.1f} GB"

def _con_trong_gb():
    try:
        import shutil
        return shutil.disk_usage(DEPLOY_DIR).free // (1024 ** 3)
    except Exception:
        return 0

def _liet_ke(thu_muc, duoi_cho_phep):
    _bao_dam_thu_muc()
    ra = []
    try:
        for n in sorted(os.listdir(thu_muc)):
            p = os.path.join(thu_muc, n)
            if not os.path.isfile(p) or n.startswith("_"):
                continue
            if os.path.splitext(n)[1].lower() not in duoi_cho_phep:
                continue
            st = os.stat(p)
            ra.append({
                "ten": n,
                "cd": st.st_size,
                "ngay": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)),
            })
    except OSError:
        pass
    return ra

# ==================================================== ghi THANG ra dia dich
#
# LOI THAT DA GAP (anh Thoai bao: "task manager het bao dung luong ben tab
# network ma trang os van quay hoai"): mot file tai len phai di qua BA lan
# chep tren the nho truoc khi xong:
#   1. nginx nhan tu trinh duyet -> ghi ra /var/lib/nginx/body
#   2. nginx day sang Flask -> Werkzeug ghi ra file tam
#   3. ma cua minh chep tu file tam sang cho luu that
# The nho cua Pi chi ghi duoc ~13 MB/s (da do that), nen voi bo cai Windows
# 5GB thi rieng viec chep di chep lai da ton ~19 phut, va HAI GIAI DOAN CUOI
# xay ra SAU KHI trinh duyet da gui xong - dung luc nguoi dung thay mang im
# lang ma trang van quay, khong biet may con dang lam gi.
#
# Sua tan goc: chan ngay o tang Werkzeug, cho no ghi THANG vao file dich
# (duoi dang <ten>.part) thay vi ghi ra file tam. Cong voi
# "proxy_request_buffering off" ben nginx (xem config/nginx-console-pi.conf),
# du lieu chay THANG mot mach tu trinh duyet -> nginx -> Flask -> file dich:
#   - chi con 1 lan ghi thay vi 3 (nhanh gap ~3 lan, do SD wear gap 3)
#   - chi can dung bang kich thuoc file thay vi gap 3 lan dung luong trong
#   - va quan trong nhat: % tren thanh tien trinh cua trinh duyet BAM SAT
#     tien do that, vi byte nao trinh duyet gui di la byte do da nam tren dia
THU_MUC_THEO_DUONG = {}          # {duong_dan_URL: (thu_muc, duoi_cho_phep)}

EXT_OS_WIM = {".wim"}

EXT_OS_ISO = {".iso"}

EXT_SXS = {".cab"}      # goi .NET 3.5 offline (sources\\sxs cua ISO) - xem co_sxs()

EXT_DRIVER = {".inf", ".sys", ".cat", ".zip", ".dll", ".cab", ".7z", ".exe"}

def _thu_muc_os_theo_duong(duong_url):
    """
    Duong tai len file OS la DONG (/deployos/os/<os_id>/len) vi co vo so
    os_id khac nhau - khong the khai bao tinh trong THU_MUC_THEO_DUONG nhu
    cac tab khac. Tu tach os_id ra khoi duong dan o day.
    """
    phan = duong_url.strip("/").split("/")
    if len(phan) == 4 and phan[0] == "deployos" and phan[1] == "os" and phan[3] == "len":
        os_id = ten_an_toan(phan[2])
        if os_id:
            return os.path.join(OS_DIR, os_id), EXT_OS_WIM
    # Tai len ca file ISO Windows (Pi tu tach boot.wim/install.wim ra - xem
    # ui/isotach.py). File ISO 5-6GB nen BAT BUOC phai ghi thang ra dia y
    # nhu .wim, khong duoc di duong mac dinh cua Werkzeug.
    if len(phan) == 4 and phan[0] == "deployos" and phan[1] == "os" and phan[3] == "len-sxs":
        os_id = ten_an_toan(phan[2])
        if os_id:
            return os.path.join(OS_DIR, os_id, "sxs"), EXT_SXS
    if len(phan) == 4 and phan[0] == "deployos" and phan[1] == "os" and phan[3] == "len-iso":
        os_id = ten_an_toan(phan[2])
        if os_id:
            return os.path.join(OS_DIR, os_id), EXT_OS_ISO
    if len(phan) == 4 and phan[0] == "deployos" and phan[1] == "drivers" and phan[3] == "len":
        driver_id = ten_an_toan(phan[2])
        if driver_id:
            return os.path.join(DRIVERS_DIR, driver_id), EXT_DRIVER
    if len(phan) == 4 and phan[0] == "deployos" and phan[1] == "ungdung" and phan[3] == "len":
        # Ghi THANG file .zip (co the vai GB nhu bo Office 365) vao dung
        # thu muc ung dung do - tranh giu ca file trong RAM luc tai len.
        ung_id = ten_an_toan(phan[2])
        if ung_id:
            return os.path.join(UNGDUNG_DIR, ung_id), EXT_UNGDUNG_ZIP
    return None

def _mo_file_dich(duong_url, filename):
    """
    Mo san file dich de Werkzeug ghi thang vao. Tra ve (fileobj, duong_dan)
    hoac (None, None) neu duong nay khong phai duong tai len cua tab nao.
    """
    cau_hinh = THU_MUC_THEO_DUONG.get(duong_url) or _thu_muc_os_theo_duong(duong_url)
    if cau_hinh is None:
        return None, None
    thu_muc, duoi_cho_phep = cau_hinh

    ten = ten_an_toan(filename or "")
    if not ten or os.path.splitext(ten)[1].lower() not in duoi_cho_phep:
        # Duoi file khong hop le: van phai nuot het du lieu (khong thi trinh
        # duyet bao loi mang kho hieu) nhung DO THANG VAO THUNG RAC, tuyet
        # doi khong giu trong RAM - file la co the vai GB.
        return open(os.devnull, "wb+"), None

    _bao_dam_thu_muc()
    try:
        os.makedirs(thu_muc, exist_ok=True)
    except OSError:
        pass
    tam = os.path.join(thu_muc, ten + ".part")
    try:
        return open(tam, "wb+"), tam
    except OSError:
        return None, None

def _don_file_do_dang(thu_muc, qua_gio=6):
    """
    Xoa cac file .part con sot lai tu lan tai len bi dut giua chung (rut day
    mang, dong trinh duyet...). Chi xoa cai da cu hon 6 tieng de khong bao
    gio dung nham vao file dang duoc tai len that.
    """
    nay = time.time()
    try:
        for n in os.listdir(thu_muc):
            if not n.endswith(".part"):
                continue
            p = os.path.join(thu_muc, n)
            try:
                if nay - os.stat(p).st_mtime > qua_gio * 3600:
                    os.remove(p)
            except OSError:
                pass
    except OSError:
        pass

def _hoan_tat_ghi_thang(tam, thu_muc, ten_goc):
    """
    Doi ten <ten>.part thanh ten that sau khi da ghi xong.

    Tra ve (ok, msg, duong_dich) - them duong_dich (None neu that bai) de
    noi goi (vd giai nen zip cua ung_dung) biet chinh xac file vua ghi nam
    o dau, khong phai tu doan lai ten sau khi co the da bi doi ten do
    trung (xem nhanh "da co file cung ten" ben duoi).
    """
    try:
        cd = os.path.getsize(tam)
    except OSError:
        return False, "Không đọc được file vừa tải lên.", None
    if cd == 0:
        try:
            os.remove(tam)
        except OSError:
            pass
        return False, "File tải lên rỗng (0 byte).", None

    ten = ten_an_toan(ten_goc)
    dich = os.path.join(thu_muc, ten)
    if os.path.exists(dich):
        goc, duoi = os.path.splitext(ten)
        ten = f"{goc}_{time.strftime('%H%M%S')}{duoi}"
        dich = os.path.join(thu_muc, ten)
    try:
        os.replace(tam, dich)
    except OSError as e:
        return False, f"Không lưu được: {e}", None
    return True, f"Đã lưu {ten} ({co_kich_thuoc(cd)}).", dich

def _luu_tai_len(fileobj, thu_muc, duoi_cho_phep, nhan):
    """
    Duong DU PHONG: chep tu file tam cua Werkzeug sang cho luu that theo
    tung khoi 1MB. Binh thuong khong chay toi day nua (da co duong ghi thang
    o tren), chi dung khi vi ly do gi do Werkzeug khong dung duoc file dich.
    """
    _bao_dam_thu_muc()
    ten = ten_an_toan(getattr(fileobj, "filename", ""))
    if not ten:
        return False, "Chưa chọn file."
    if os.path.splitext(ten)[1].lower() not in duoi_cho_phep:
        return False, (f"Không nhận đuôi file này cho mục {nhan}. Chỉ nhận: "
                       f"{', '.join(sorted(duoi_cho_phep))}")
    if _con_trong_gb() < MIN_FREE_GB:
        return False, (f"Chỉ còn {_con_trong_gb()} GB trống - cần ít nhất "
                       f"{MIN_FREE_GB} GB. Xóa bớt file trước khi tải thêm.")

    # Can GAP DOI kich thuoc file, khong phai 1 lan: Werkzeug do file tai len
    # ra 1 file tam truoc (xem ghi chu ve /tmp trong app.py), roi ham nay moi
    # chep tu file tam do sang cho luu that - hai ban ton tai cung luc. Voi bo
    # cai Windows 6GB thi can ~12GB trong. Chan tu dau con hon de tai nua
    # chung roi moi bao het cho (mat cong cho hang chuc phut).
    try:
        from flask import request as _rq
        can = _rq.content_length or 0
    except Exception:
        can = 0
    if can:
        can_gb = (can * 2) / (1024 ** 3) + 1        # +1GB de du an toan
        if _con_trong_gb() < can_gb:
            return False, (
                f"File này {co_kich_thuoc(can)} nên cần khoảng "
                f"{can_gb:.1f} GB trống (file tạm + bản lưu thật), nhưng chỉ "
                f"còn {_con_trong_gb()} GB. Xóa bớt file cũ, hoặc cắm USB và "
                f"chuyển bớt dữ liệu sang đó trước.")

    dich = os.path.join(thu_muc, ten)
    if os.path.exists(dich):
        goc, duoi = os.path.splitext(ten)
        ten = f"{goc}_{time.strftime('%H%M%S')}{duoi}"
        dich = os.path.join(thu_muc, ten)

    tam = dich + ".part"
    da_ghi = 0
    try:
        with open(tam, "wb") as f:
            while True:
                khoi = fileobj.read(1024 * 1024)
                if not khoi:
                    break
                f.write(khoi)
                da_ghi += len(khoi)
                # Kiem tra moi ~200MB (goi statvfs moi khoi rat ton)
                if da_ghi % (200 * 1024 * 1024) < 1024 * 1024:
                    if _con_trong_gb() < 1:
                        raise OSError("Hết dung lượng trong lúc đang ghi")
        os.replace(tam, dich)
    except Exception as e:
        try:
            os.remove(tam)
        except OSError:
            pass
        return False, f"Lỗi khi lưu: {e}"
    return True, f"Đã lưu {ten} ({co_kich_thuoc(da_ghi)})."

def _xoa_file(thu_muc, ten):
    p = _duong_dan_trong(thu_muc, ten)
    if not p:
        return False, "Tên file không hợp lệ."
    if not os.path.isfile(p):
        return False, "Không tìm thấy file."
    try:
        os.remove(p)
    except OSError as e:
        return False, f"Không xóa được: {e}"
    return True, f"Đã xóa {os.path.basename(p)}."
