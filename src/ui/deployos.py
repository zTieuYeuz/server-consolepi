"""
Console Pi - Tab "Deployment OS" (trien khai he dieu hanh qua mang)

Muc dich: khi gap 1 may PC hong ngoai hien truong, cam day mang vao Console
Pi roi boot thang vao moi truong cai dat qua mang (PXE), tu dong cai lai
Windows/Linux + phan mem + script tuy chinh - khong can mang theo USB cai
dat rieng, khong phai go tay tung buoc.

Mo hinh tham khao: MDT (Microsoft Deployment Toolkit) - vong chay tren
Windows Server. MDT KHONG cai len Linux/Pi duoc, nhung co che ben duoi no
dung (PXE -> WinPE -> script chia o/ap anh/cai driver/cai phan mem) thi
dung lai duoc bang cong cu Linux co san. Xem ke hoach day du:
docs/ke-hoach-pxe-winpe-tu-dong-cai-windows.md

-----------------------------------------------------------------------
TRANG THAI THAT CUA TINH NANG (KHONG BIA - doc ky truoc khi dung)
-----------------------------------------------------------------------
File nay lam phan GIAO DIEN + LUU CAU HINH: chon kieu boot, chon OS, khai
bao thong tin may, chia o dia, chon phan mem/script, luu thanh "kich ban"
dung lai nhieu lan.

Phan PHUC VU BOOT THAT SU (dnsmasq cau hinh PXE, bootloader iPXE, anh
WinPE, script chia o/ap anh chay trong WinPE) la GIAI DOAN KE TIEP, CHUA
duoc dung. Vi vay buoc cuoi cua trinh tu tu chon KHONG "gia vo" boot -
no chay 1 bang KIEM TRA SAN SANG doc trang thai THAT tren may (co file
boot chua, co iPXE chua, dnsmasq da cau hinh PXE chua) va noi ro con
thieu gi. Dung nguyen tac cua du an: khong bao gio bao "xong" khi chua
kiem chung duoc that.

-----------------------------------------------------------------------
LUU Y AN TOAN
-----------------------------------------------------------------------
1. Tab nay cho tai len file .exe/.msi/.bat/.ps1/.cmd - la nhung dinh dang
   MA LENH. Chung TUYET DOI KHONG duoc chay tren chinh con Pi: Pi chi LUU
   va PHUC VU chung cho may dich (may dang duoc cai lai) tai ve. Khong co
   duong nao trong file nay goi subprocess chay cac file do ca. Ngoai ra
   toan bo tab da nam sau dang nhap (xem ui/auth.py) nhu moi tab khac.
2. Kich ban co the chua mat khau cua tai khoan SE TAO tren may dich (can
   cho unattend.xml). Vi vay thu muc kich ban de quyen 700 va tung file
   600 (chi root doc duoc - dashboard chay quyen root), va giao dien KHONG
   bao gio hien lai mat khau ra man hinh (chi hien ***).
3. Duong dan luu CO DINH (/opt/console-pi/deploy), khong tu chuyen sang
   USB nhu tab Kho file. Ly do giong het tab TFTP: dich vu mang (dnsmasq/
   nginx) can duong dan ON DINH, khong duoc doi giua chung khi cam/rut USB.
"""
import json
import os
import re
import secrets
import time

# ---------------------------------------------------------------- duong dan
# Duong dan du lieu khai bao tap trung o duongdan.py (xem ly do that o do:
# du lieu tung nam chung voi ma nguon nen `uninstall.sh` xoa sach ca bo cai
# Office 3.6GB lan toan bo kich ban).
from .duongdan import DEPLOY_DIR
BOOT_DIR = os.path.join(DEPLOY_DIR, "boot")
APPS_DIR = os.path.join(DEPLOY_DIR, "apps")
SCRIPTS_DIR = os.path.join(DEPLOY_DIR, "scripts")
KICHBAN_DIR = os.path.join(DEPLOY_DIR, "kichban")
OS_DIR = os.path.join(DEPLOY_DIR, "os")
DRIVERS_DIR = os.path.join(DEPLOY_DIR, "drivers")
UNGDUNG_DIR = os.path.join(DEPLOY_DIR, "ungdung")
APPS_META = os.path.join(APPS_DIR, "_thongtin.json")

# Con lai duoi muc nay thi khong cho tai them (giong ui/storage.py)
MIN_FREE_GB = 3

EXT_BOOT = {".iso", ".wim", ".esd", ".img", ".vhd", ".vhdx", ".efi", ".kpxe", ".ipxe"}
EXT_APP = {".msi", ".exe"}
EXT_SCRIPT = {".bat", ".ps1", ".cmd"}

# ---------------------------------------------------------------- lua chon
KIEU_BOOT = [
    ("truc_tiep", "Boot OS trực tiếp với máy cần cài",
     "Cắm dây mạng THẲNG từ Pi sang máy cần cài. Pi tự cấp IP và chỉ đường "
     "boot. Không đụng chạm gì tới mạng của khách - chắc ăn nhất."),
    ("mang_khong_dhcp", "Boot OS qua mạng không có DHCP",
     "Pi và máy cần cài cùng cắm vào 1 switch, nhưng mạng đó KHÔNG có "
     "DHCP server nào. Pi đóng luôn vai trò cấp IP và chỉ đường boot."),
    ("mang_co_dhcp", "Boot OS qua mạng có sẵn DHCP",
     "Mang da co DHCP san (router cong ty). Pi chi chay proxyDHCP - CHI "
     "tra loi 'file boot o dau', KHONG cap IP, tranh dung do 2 DHCP."),
]

DANH_SACH_OS = [
    ("windows", "Windows", [("10", "Windows 10"), ("11", "Windows 11")]),
    ("linux", "Linux", [("ubuntu", "Ubuntu"), ("debian", "Debian")]),
]

MUI_GIO = [
    "Asia/Ho_Chi_Minh", "Asia/Bangkok", "Asia/Singapore", "Asia/Tokyo",
    "Asia/Seoul", "Asia/Shanghai", "UTC",
]

# Ngon ngu hien thi cua Windows (ma BCP-47 that su Windows dung cho
# <UILanguage>/<SystemLocale>).
#
# LUU Y QUAN TRONG (de tranh hieu nham): doi muc nay chi doi duoc neu
# BAN WINDOWS DANG CAI CO SAN goi ngon ngu do. Anh Windows tai ve
# thuong chi co 1 ngon ngu; chon tieng Viet tren 1 anh chi co en-US thi
# Windows se im lang quay ve en-US chu khong bao loi. Muon that su doi
# ngon ngu phai dung anh da tich hop goi ngon ngu do.
NGON_NGU = [
    ("en-US", "English (United States)"),
    ("vi-VN", "Tiếng Việt"),
    ("ja-JP", "日本語 (Nhật)"),
    ("ko-KR", "한국어 (Hàn)"),
    ("zh-CN", "中文 (Trung giản thể)"),
    ("fr-FR", "Français"),
    ("de-DE", "Deutsch"),
]

# Kieu ban phim (<InputLocale>). Khac han ngon ngu hien thi: day la cach
# cac phim tren ban phim duoc hieu, KHONG phu thuoc vao goi ngon ngu co
# trong anh hay khong, nen doi muc nay luon co tac dung.
#
# Tieng Viet KHONG co kieu ban phim rieng tren Windows - nguoi Viet go
# bang Unikey/EVKey tren ban phim US, nen mac dinh dung US la dung.
BAN_PHIM = [
    ("0409:00000409", "US - Mỹ (dùng cho tiếng Việt, Unikey/EVKey)"),
    ("0809:00000809", "United Kingdom - Anh"),
    ("040c:0000040c", "French - Pháp (AZERTY)"),
    ("0407:00000407", "German - Đức (QWERTZ)"),
    ("0411:00000411", "Japanese - Nhật"),
    ("0412:00000412", "Korean - Hàn"),
    ("0804:00000804", "Chinese Simplified - Trung"),
]

# Cac buoc cua trinh tu tu chon (dung chung cho ca 2 che do: chay ngay va
# luu thanh kich ban - chi khac o buoc cuoi)
TEN_BUOC = [
    (1, "Kiểu boot"),
    (2, "Chọn OS"),
    (3, "Thông tin OS"),
    (4, "Phân chia ổ đĩa"),
    (5, "Phần mềm"),
    (6, "Chỉnh sửa cài đặt"),
    (7, "Tổng kết"),
]
SO_BUOC = len(TEN_BUOC)


# ---------------------------------------------------------------- tien ich
def _bao_dam_thu_muc():
    """Tao san cac thu muc. Kich ban de 700 vi co the chua mat khau."""
    for d in (DEPLOY_DIR, BOOT_DIR, APPS_DIR, SCRIPTS_DIR, OS_DIR, DRIVERS_DIR,
              UNGDUNG_DIR):
        try:
            os.makedirs(d, exist_ok=True)
        except OSError:
            pass
    try:
        os.makedirs(KICHBAN_DIR, exist_ok=True)
        os.chmod(KICHBAN_DIR, 0o700)
    except OSError:
        pass


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
EXT_DRIVER = {".inf", ".sys", ".cat", ".zip", ".dll"}


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
        return False, "Khong doc duoc file vua tai len.", None
    if cd == 0:
        try:
            os.remove(tam)
        except OSError:
            pass
        return False, "File tai len rong (0 byte).", None

    ten = ten_an_toan(ten_goc)
    dich = os.path.join(thu_muc, ten)
    if os.path.exists(dich):
        goc, duoi = os.path.splitext(ten)
        ten = f"{goc}_{time.strftime('%H%M%S')}{duoi}"
        dich = os.path.join(thu_muc, ten)
    try:
        os.replace(tam, dich)
    except OSError as e:
        return False, f"Khong luu duoc: {e}", None
    return True, f"Da luu {ten} ({co_kich_thuoc(cd)}).", dich


def _luu_tai_len(fileobj, thu_muc, duoi_cho_phep, nhan):
    """
    Duong DU PHONG: chep tu file tam cua Werkzeug sang cho luu that theo
    tung khoi 1MB. Binh thuong khong chay toi day nua (da co duong ghi thang
    o tren), chi dung khi vi ly do gi do Werkzeug khong dung duoc file dich.
    """
    _bao_dam_thu_muc()
    ten = ten_an_toan(getattr(fileobj, "filename", ""))
    if not ten:
        return False, "Chua chon file."
    if os.path.splitext(ten)[1].lower() not in duoi_cho_phep:
        return False, (f"Khong nhan duoi file nay cho muc {nhan}. Chi nhan: "
                       f"{', '.join(sorted(duoi_cho_phep))}")
    if _con_trong_gb() < MIN_FREE_GB:
        return False, (f"Chi con {_con_trong_gb()} GB trong - can it nhat "
                       f"{MIN_FREE_GB} GB. Xoa bot file truoc khi tai them.")

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
                f"File nay {co_kich_thuoc(can)} nen can khoang "
                f"{can_gb:.1f} GB trong (file tam + ban luu that), nhung chi "
                f"con {_con_trong_gb()} GB. Xoa bot file cu, hoac cam USB va "
                f"chuyen bot du lieu sang do truoc.")

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
                        raise OSError("Het dung luong trong luc dang ghi")
        os.replace(tam, dich)
    except Exception as e:
        try:
            os.remove(tam)
        except OSError:
            pass
        return False, f"Loi khi luu: {e}"
    return True, f"Da luu {ten} ({co_kich_thuoc(da_ghi)})."


def _xoa_file(thu_muc, ten):
    p = _duong_dan_trong(thu_muc, ten)
    if not p:
        return False, "Ten file khong hop le."
    if not os.path.isfile(p):
        return False, "Khong tim thay file."
    try:
        os.remove(p)
    except OSError as e:
        return False, f"Khong xoa duoc: {e}"
    return True, f"Da xoa {os.path.basename(p)}."


# ------------------------------------------------- thong tin phan mem (2.2)
def doc_thongtin_app():
    """
    Tham so cai dat im lang cua tung phan mem, vd {"teamviewer.exe": "/S"}.
    Moi hang dat 1 kieu cho rieng (/S, /silent, /quiet, /verysilent...) nen
    phai cho nguoi dung tu dien, khong doan gium.
    """
    try:
        with open(APPS_META) as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def ghi_thongtin_app(d):
    _bao_dam_thu_muc()
    try:
        tam = APPS_META + ".tmp"
        with open(tam, "w") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.replace(tam, APPS_META)
        return True
    except OSError:
        return False


def danh_sach_app():
    meta = doc_thongtin_app()
    ra = _liet_ke(APPS_DIR, EXT_APP)
    for a in ra:
        a["tham_so"] = meta.get(a["ten"], "")
        a["la_msi"] = a["ten"].lower().endswith(".msi")
    return ra


# Goi y tham so cai im lang theo tung ho trinh cai dat - de nguoi dung
# chon thay vi phai tu tra cuu tieng Anh. Dung chung cho tab "Phan mem"
# va buoc 5 cua kich ban.
GOI_Y_THAM_SO = [
    ("/qn /norestart", "MSI chuẩn - im lặng hoàn toàn"),
    ("/qn /norestart ALLUSERS=1", "MSI - cài cho MỌI người dùng trên máy"),
    ("/S", "NSIS (7-Zip, Notepad++, VLC...) - chữ S HOA"),
    ("/VERYSILENT /SUPPRESSMSGBOXES /NORESTART", "Inno Setup"),
    ("/quiet /norestart", "WiX Burn (.NET, Visual C++ Redist...)"),
    ('/s /v"/qn"', "InstallShield"),
    ("-ms", "Firefox"),
    ("--silent", "Squirrel (một số app kiểu Electron)"),
]


def tham_so_mac_dinh_app(ten):
    """Tham so hop ly nhat khi chua ai dien gi - .msi thi chac chan dung."""
    return "/qn /norestart" if (ten or "").lower().endswith(".msi") else ""


def chuan_hoa_apps(apps):
    """
    Dua danh sach phan mem cua kich ban ve dang chuan:
        [{"ten": "chrome.msi", "dich": "may" | "nguoi_dung"}, ...]

    Kich ban CU luu dang danh sach TEN FILE (chuoi) - van doc duoc binh
    thuong (mac dinh coi la cai cap may), khong lam hong kich ban da luu.
    """
    ra = []
    for a in apps or []:
        if isinstance(a, str):
            ra.append({"ten": a, "dich": "may"})
        elif isinstance(a, dict) and a.get("ten"):
            ra.append({
                "ten": a["ten"],
                "dich": "nguoi_dung" if a.get("dich") == "nguoi_dung" else "may",
            })
    return ra


# ------------------------------- ung dung THU MUC (mo hinh MDT: "Application
# with source files") - KHAC voi "Phan mem" o tren (1 file .msi/.exe suy tham
# so theo duoi): 1 ung dung o day la CA 1 THU MUC (bao nhieu file/thu muc con
# cung duoc) + 1 DONG LENH CAI TU DO nguoi dung tu go, dung y het cach
# Deployment Workbench cua MDT lam ("Source Files" + "Command line" + MDT tu
# cd vao dung thu muc do roi chay lenh). Sinh ra de dap ung cac bo cai nhieu
# file (vd Office 365 qua Office Deployment Tool: thu muc Office\ + setup.exe
# + configuration.xml) ma kieu "1 file" o tren khong the mo ta duoc.
EXT_UNGDUNG_ZIP = {".zip"}


def danh_sach_ungdung():
    """Danh sach ung dung kieu thu muc - moi ung dung la 1 thu muc rieng
    trong UNGDUNG_DIR, co the chua bao nhieu file/thu muc con cung duoc."""
    _bao_dam_thu_muc()
    ra = []
    try:
        for ung_id in sorted(os.listdir(UNGDUNG_DIR)):
            p = os.path.join(UNGDUNG_DIR, ung_id)
            if not os.path.isdir(p):
                continue
            meta = {}
            try:
                with open(os.path.join(p, "_thongtin.json")) as f:
                    meta = json.load(f)
            except Exception:
                pass
            so_file = 0
            tong_byte = 0
            for goc, _dirs, files in os.walk(p):
                for ten in files:
                    if goc == p and ten == "_thongtin.json":
                        continue
                    so_file += 1
                    try:
                        tong_byte += os.path.getsize(os.path.join(goc, ten))
                    except OSError:
                        pass
            ra.append({
                "id": ung_id,
                "ten_hien_thi": meta.get("ten_hien_thi") or ung_id,
                "lenh_cai": meta.get("lenh_cai") or "",
                "so_file": so_file,
                "kich_thuoc": co_kich_thuoc(tong_byte) if tong_byte else "0 B",
            })
    except OSError:
        pass
    return ra


def lay_ungdung(ung_id):
    for u in danh_sach_ungdung():
        if u["id"] == ung_id:
            return u
    return None


def _doc_meta_ungdung(ung_id):
    p = os.path.join(UNGDUNG_DIR, ten_an_toan(ung_id), "_thongtin.json")
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return {}


def _ghi_meta_ungdung(ung_id, meta):
    p = os.path.join(UNGDUNG_DIR, ten_an_toan(ung_id), "_thongtin.json")
    try:
        with open(p, "w") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
        return True
    except OSError:
        return False


def tao_ungdung_moi(ten_hien_thi):
    _bao_dam_thu_muc()
    ten_hien_thi = (ten_hien_thi or "").strip()
    if not ten_hien_thi:
        return False, "Chưa đặt tên ứng dụng.", None
    ung_id = ten_an_toan(ten_hien_thi.replace(" ", "_")).lower()
    if not ung_id:
        return False, "Tên không hợp lệ.", None
    p = os.path.join(UNGDUNG_DIR, ung_id)
    if os.path.isdir(p):
        return False, "Đã có ứng dụng cùng tên.", None
    try:
        os.makedirs(p)
        _ghi_meta_ungdung(ung_id, {"ten_hien_thi": ten_hien_thi, "lenh_cai": ""})
    except OSError as e:
        return False, f"Không tạo được: {e}", None
    return True, f'Đã tạo "{ten_hien_thi}".', ung_id


def xoa_ungdung(ung_id):
    import shutil
    p = _duong_dan_trong(UNGDUNG_DIR, ung_id)
    if not p or not os.path.isdir(p):
        return False, "Không tìm thấy ứng dụng."
    try:
        shutil.rmtree(p)
    except OSError as e:
        return False, f"Không xóa được: {e}"
    return True, "Đã xóa ứng dụng."


def dat_lenh_cai_ungdung(ung_id, lenh_cai):
    """
    Luu dong lenh cai TU DO - dung y het "Command line" cua MDT. Nguoi dung
    tu go nguyen dong (vd "setup.exe /configure configuration.xml" cho
    Office 365, hoac "msiexec /i goi.msi /qn" cho MSI thuong). Deploy.cmd se
    tu `cd` vao dung thu muc ung dung nay TRUOC khi chay dong lenh, nen chi
    can go ten file, khong can duong dan day du.
    """
    p = os.path.join(UNGDUNG_DIR, ten_an_toan(ung_id))
    if not os.path.isdir(p):
        return False, "Không tìm thấy ứng dụng."
    lenh_cai = (lenh_cai or "").strip()[:500]
    meta = _doc_meta_ungdung(ung_id)
    meta["lenh_cai"] = lenh_cai
    if not _ghi_meta_ungdung(ung_id, meta):
        return False, "Không ghi được lệnh cài."
    return True, "Đã lưu dòng lệnh cài."


def _an_toan_trong_zip(ten_muc):
    """Chan zip-slip (../../etc/passwd) khi giai nen - kiem tra THAT bang
    os.path.normpath, khong tin vao chinh chuoi trong file zip."""
    chuan = os.path.normpath(ten_muc)
    return not (chuan.startswith("..") or os.path.isabs(chuan))


def giai_nen_ungdung(ung_id, duong_zip):
    """
    Giai nen 1 file .zip da tai len THANG vao thu muc ung dung (giu nguyen
    cau truc thu muc con ben trong zip - dung cho bo cai nhieu file/thu muc
    long nhau nhu Office 365: thu muc Office\\Data\\..., setup.exe,
    configuration.xml). Xoa file .zip sau khi giai nen xong.
    """
    import zipfile
    p = os.path.join(UNGDUNG_DIR, ten_an_toan(ung_id))
    if not os.path.isdir(p):
        return False, "Không tìm thấy ứng dụng."
    try:
        with zipfile.ZipFile(duong_zip) as z:
            for info in z.infolist():
                if not _an_toan_trong_zip(info.filename):
                    continue
                z.extract(info, p)
    except zipfile.BadZipFile:
        return False, "File không phải .zip hợp lệ (hoặc bị hỏng khi tải lên)."
    except OSError as e:
        return False, f"Lỗi khi giải nén: {e}"
    finally:
        try:
            os.remove(duong_zip)
        except OSError:
            pass
    return True, "Đã giải nén xong vào ứng dụng."


def liet_ke_muc_ungdung(ung_id):
    """Liet ke CAP 1 (file/thu muc con ngay duoi goc) de hien tren giao
    dien - khong liet ke sau hon vi Office co the co hang ngan file con."""
    p = os.path.join(UNGDUNG_DIR, ten_an_toan(ung_id))
    ra = []
    try:
        for ten in sorted(os.listdir(p)):
            if ten == "_thongtin.json":
                continue
            fp = os.path.join(p, ten)
            if os.path.isdir(fp):
                so_con = sum(len(files) for _g, _d, files in os.walk(fp))
                ra.append({"ten": ten, "la_thu_muc": True, "so_file": so_con,
                          "kich_thuoc": ""})
            else:
                ra.append({"ten": ten, "la_thu_muc": False, "so_file": 0,
                          "kich_thuoc": co_kich_thuoc(os.path.getsize(fp))})
    except OSError:
        pass
    return ra


def xoa_muc_trong_ungdung(ung_id, ten_muc):
    """Xoa 1 file HOAC 1 thu muc con o CAP 1 (khong cho xoa xuyen thu muc
    cha bang duong dan co '/' hay '..')."""
    p = _duong_dan_trong(UNGDUNG_DIR, ung_id)
    if not p or not os.path.isdir(p):
        return False, "Không tìm thấy ứng dụng."
    ten_muc = ten_an_toan(ten_muc)
    if not ten_muc or ten_muc == "_thongtin.json":
        return False, "Không tìm thấy mục cần xóa."
    fp = os.path.join(p, ten_muc)
    if not os.path.exists(fp):
        return False, "Không tìm thấy mục cần xóa."
    import shutil
    try:
        if os.path.isdir(fp):
            shutil.rmtree(fp)
        else:
            os.remove(fp)
    except OSError as e:
        return False, f"Không xóa được: {e}"
    return True, "Đã xóa."


def chuan_hoa_ungdung(ds):
    """Dua danh sach ung dung (thu muc) cua kich ban ve dang chuan:
        [{"id": "office365", "dich": "may" | "nguoi_dung"}, ...]"""
    ra = []
    for a in ds or []:
        if isinstance(a, dict) and a.get("id"):
            ra.append({
                "id": a["id"],
                "dich": "nguoi_dung" if a.get("dich") == "nguoi_dung" else "may",
            })
    return ra


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
            except Exception:
                pass
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
            })
    except OSError:
        pass
    return ra


def lay_os(os_id):
    for o in danh_sach_os():
        if o["id"] == os_id:
            return o
    return None


def duong_boot_wim(os_id):
    return os.path.join(OS_DIR, ten_an_toan(os_id), "boot.wim")


def duong_install_wim(os_id):
    return os.path.join(OS_DIR, ten_an_toan(os_id), "install.wim")


def tao_os_moi(ten_hien_thi, os_ho="windows"):
    _bao_dam_thu_muc()
    ten_hien_thi = (ten_hien_thi or "").strip()
    if not ten_hien_thi:
        return False, "Chua dat ten he dieu hanh.", None
    os_id = ten_an_toan(ten_hien_thi.replace(" ", "_")).lower()
    if not os_id:
        return False, "Ten khong hop le.", None
    p = os.path.join(OS_DIR, os_id)
    if os.path.isdir(p):
        return False, f'Da co he dieu hanh "{os_id}" roi.', None
    try:
        os.makedirs(p, exist_ok=True)
        with open(os.path.join(p, "_thongtin.json"), "w") as f:
            json.dump({"ten_hien_thi": ten_hien_thi, "os_ho": os_ho}, f,
                      ensure_ascii=False)
    except OSError as e:
        return False, f"Khong tao duoc: {e}", None
    return True, f'Da tao "{ten_hien_thi}".', os_id


def xoa_os(os_id):
    p = _duong_dan_trong(OS_DIR, os_id)
    if not p or not os.path.isdir(p):
        return False, "Khong tim thay he dieu hanh."
    try:
        import shutil
        shutil.rmtree(p)
    except OSError as e:
        return False, f"Khong xoa duoc: {e}"
    return True, "Da xoa."


# ---------------------------- driver (mo hinh MDT: "Out-of-Box Drivers")
def danh_sach_driver():
    """Danh sach cac goi driver da tai len - moi goi la 1 thu muc rieng
    (co the chua nhieu file .inf/.sys/.cat cho 1 thiet bi/dong may)."""
    _bao_dam_thu_muc()
    ra = []
    try:
        for driver_id in sorted(os.listdir(DRIVERS_DIR)):
            p = os.path.join(DRIVERS_DIR, driver_id)
            if not os.path.isdir(p):
                continue
            meta = {}
            try:
                with open(os.path.join(p, "_thongtin.json")) as f:
                    meta = json.load(f)
            except Exception:
                pass
            so_file = sum(
                1 for n in os.listdir(p)
                if n != "_thongtin.json" and os.path.isfile(os.path.join(p, n)))
            ra.append({
                "id": driver_id,
                "ten_hien_thi": meta.get("ten_hien_thi") or driver_id,
                "so_file": so_file,
                # Driver CHO ANH BOOT (WinPE) - xem giai thich trong
                # docstring cua dat_driver_cho_boot().
                "cho_boot": bool(meta.get("cho_boot")),
            })
    except OSError:
        pass
    return ra


def dat_driver_cho_boot(driver_id, bat):
    r"""
    Danh dau 1 goi driver la "nap vao anh boot (WinPE)" hay khong.

    VAN DE THAT (anh Thoai da gap voi MDT: "boot vao may nhung no
    khong nhan vi file boot MDT khong co driver card mang cua may
    do") - va da KIEM CHUNG lai tren chinh boot.wim cua Console Pi
    bang cach trich cac file .inf trong DriverStore ra doc ma phan
    cung that:

        CO   : Intel I219 doi 2016-2019 (DEV_15B7/15B8/15BB/15BE,
               15D6/15D7/15D8/15E3), Realtek RTL8111/8168, RTL8125,
               Broadcom NetXtreme, USB-LAN ASIX AX88179 + RTL8153
        THIEU: Intel I219 tu doi Comet Lake 2020 tro di (0D4E/0D4F,
               15FB/15FC, 1A1C-1A1F, 550A-550D, 0DC5-0DC7) va toan bo
               Intel I225/I226 2.5G (15F2/15F3, 125B/125C/125D)

    Nghia la may HP/Dell/Lenovo doi 2020 tro lai day dung LAN Intel
    se KHONG CO MANG trong WinPE -> khong tai duoc install.wim ->
    dung hinh, dung y het hien tuong anh gap voi MDT.

    Driver danh dau "cho_boot" se duoc CHEP THANG vao trong boot.wim
    luc dung anh dia (xem ui/unattend.py), va script trien khai chay
    `drvload` nap chung NGAY TRUOC khi khoi tao mang - nho vay card
    mang doi moi hoat dong duoc. Khac han voi driver thuong (chi
    tiem cho Windows SAU khi da cai xong, luc do da co mang roi).
    """
    p = os.path.join(DRIVERS_DIR, ten_an_toan(driver_id))
    if not os.path.isdir(p):
        return False, "Không tìm thấy gói driver."
    f_meta = os.path.join(p, "_thongtin.json")
    meta = {}
    try:
        with open(f_meta) as f:
            meta = json.load(f)
    except Exception:
        pass
    meta["cho_boot"] = bool(bat)
    try:
        with open(f_meta, "w") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
    except OSError as e:
        return False, f"Không ghi được: {e}"
    return True, ("Đã đánh dấu nạp vào ảnh boot." if bat
                  else "Đã bỏ đánh dấu nạp vào ảnh boot.")


def tao_driver_moi(ten_hien_thi):
    _bao_dam_thu_muc()
    ten_hien_thi = (ten_hien_thi or "").strip()
    if not ten_hien_thi:
        return False, "Chua dat ten goi driver.", None
    driver_id = ten_an_toan(ten_hien_thi.replace(" ", "_")).lower()
    if not driver_id:
        return False, "Ten khong hop le.", None
    p = os.path.join(DRIVERS_DIR, driver_id)
    if os.path.isdir(p):
        return False, f'Da co goi driver "{driver_id}" roi.', None
    try:
        os.makedirs(p, exist_ok=True)
        with open(os.path.join(p, "_thongtin.json"), "w") as f:
            json.dump({"ten_hien_thi": ten_hien_thi}, f, ensure_ascii=False)
    except OSError as e:
        return False, f"Khong tao duoc: {e}", None
    return True, f'Da tao "{ten_hien_thi}".', driver_id


def xoa_driver(driver_id):
    p = _duong_dan_trong(DRIVERS_DIR, driver_id)
    if not p or not os.path.isdir(p):
        return False, "Khong tim thay goi driver."
    try:
        import shutil
        shutil.rmtree(p)
    except OSError as e:
        return False, f"Khong xoa duoc: {e}"
    return True, "Da xoa."


def xoa_file_trong_driver(driver_id, ten_file):
    p = _duong_dan_trong(DRIVERS_DIR, driver_id)
    if not p or not os.path.isdir(p):
        return False, "Khong tim thay goi driver."
    fp = _duong_dan_trong(p, ten_file)
    if not fp or not os.path.isfile(fp) or os.path.basename(fp) == "_thongtin.json":
        return False, "Khong tim thay file."
    try:
        os.remove(fp)
    except OSError as e:
        return False, f"Khong xoa duoc: {e}"
    return True, "Da xoa."


# ------------------------------------------------------------ kich ban (2.4)
def danh_sach_kichban():
    _bao_dam_thu_muc()
    ra = []
    try:
        for n in sorted(os.listdir(KICHBAN_DIR)):
            if not n.endswith(".json"):
                continue
            p = os.path.join(KICHBAN_DIR, n)
            try:
                with open(p) as f:
                    d = json.load(f)
            except Exception:
                continue
            d["_file"] = n
            d["_ngay"] = time.strftime("%Y-%m-%d %H:%M",
                                       time.localtime(os.stat(p).st_mtime))
            ra.append(d)
    except OSError:
        pass
    return ra


def doc_kichban(ten_file):
    p = _duong_dan_trong(KICHBAN_DIR, ten_file)
    if not p or not os.path.isfile(p):
        return None
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return None


def luu_kichban(cauhinh, ten):
    """Luu kich ban. File de quyen 600 vi co the chua mat khau may dich."""
    _bao_dam_thu_muc()
    ten = (ten or "").strip()
    if not ten:
        return False, "Chua dat ten kich ban."
    ten_file = ten_an_toan(ten.replace(" ", "_")) + ".json"
    if ten_file == ".json":
        return False, "Ten kich ban khong hop le."
    p = os.path.join(KICHBAN_DIR, ten_file)

    d = dict(cauhinh)
    d["ten_kichban"] = ten
    d["tao_luc"] = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        # Mo bang O_CREAT|O_WRONLY voi quyen 600 ngay tu luc tao - khong de
        # co khe thoi gian nao file nam do voi quyen rong hon.
        fd = os.open(p, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.chmod(p, 0o600)
    except OSError as e:
        return False, f"Khong luu duoc: {e}"
    return True, f"Da luu kich ban \"{ten}\"."


def xoa_kichban(ten_file):
    p = _duong_dan_trong(KICHBAN_DIR, ten_file)
    if not p or not os.path.isfile(p):
        return False, "Khong tim thay kich ban."
    try:
        os.remove(p)
    except OSError as e:
        return False, f"Khong xoa duoc: {e}"
    return True, "Da xoa kich ban."


# ------------------------------------------------------- kiem tra san sang
def kiem_tra_san_sang(cauhinh):
    """
    Doc trang thai THAT tren may xem da du dieu kien boot qua mang chua.
    KHONG bao gio bao "san sang" neu chua kiem chung duoc - moi muc o day
    deu la mot phep kiem tra that (co file khong / dich vu co that khong).

    Tra ve danh sach (dat, nhan, chi_tiet).
    """
    ra = []

    # 1. Co file boot nao chua
    ds_boot = _liet_ke(BOOT_DIR, EXT_BOOT)
    ra.append((
        bool(ds_boot),
        "File boot đã tải lên",
        (f"{len(ds_boot)} file trong {BOOT_DIR}" if ds_boot else
         "Chưa có file nào - vào tab \"Tài nguyên\" > \"File boot\" để tải lên"),
    ))

    # 2. Bootloader iPXE (giai doan 1 cua PXE: TFTP phat file nho nay truoc)
    co_ipxe = any(
        os.path.isfile(os.path.join(BOOT_DIR, t))
        for t in ("undionly.kpxe", "ipxe.efi", "snponly.efi")
    )
    ra.append((
        co_ipxe,
        "Bootloader iPXE",
        ("Đã có trong thư mục boot" if co_ipxe else
         "Chưa có (cần undionly.kpxe cho máy BIOS đời cũ / ipxe.efi cho máy "
         "UEFI - tải từ ipxe.org rồi tải lên ở tab File boot)"),
    ))

    # Muc "cau hinh PXE cua dnsmasq" TUNG nam o day nhu 1 gach dau dong tinh
    # ("chua dung, GIAI DOAN KE TIEP"). Da bo: ui/pxe.py gio TU SINH file
    # /etc/dnsmasq-pxe.conf moi lan bam "Bat PXE" (xem bat_pxe()), nen kiem
    # tra "da co san file do chua" o day la SAI Y NGHIA - no se luon bao
    # "chua co" cho toi khi nguoi dung bam nut bat, tao vong luan quan (nut
    # bat lai nam trong khoi chi hien khi kiem tra nay dat). Trang thai PXE
    # that su gio xem o bang rieng cua ui/pxe.py (trang_thai_chuan_bi()),
    # hien ngay duoi bang nay trong buoc 7 khi che_do la "chay".

    # 3. Anh WinPE/install.wim cua HE DIEU HANH da chon (chi can khi cai
    #    Windows) - LOI THAT DA GAP: muc nay TUNG kiem tra file "boot.wim"
    #    nam ngay trong BOOT_DIR (ha tang PXE dung chung), la cau truc CU
    #    TRUOC KHI tach rieng tung he dieu hanh vao "os/<os_id>/" (xem
    #    danh_sach_os()) - sau khi tach, boot.wim khong con nam trong
    #    BOOT_DIR nua nen muc nay LUON bao sai "chua co" du da tai len
    #    day du qua tab "Tai nguyen > He dieu hanh". Sua lai doc dung
    #    os_id cua kich ban dang xet.
    if (cauhinh or {}).get("os_ho") == "windows":
        os_id = (cauhinh or {}).get("os_id", "")
        o = lay_os(os_id) if os_id else None
        if not os_id:
            ra.append((
                False, "Hệ điều hành",
                "Chưa chọn hệ điều hành ở bước 2 của kịch bản.",
            ))
        elif not o:
            ra.append((
                False, "Hệ điều hành",
                f'Không tìm thấy hệ điều hành "{os_id}" (có thể đã bị xóa) - '
                "chọn lại ở bước 2.",
            ))
        else:
            ra.append((
                o["co_boot_wim"], "Ảnh WinPE (boot.wim)",
                (f"Đã có trong os/{os_id}/" if o["co_boot_wim"] else
                 f'Chưa tải boot.wim cho "{o["ten_hien_thi"]}" - vào tab '
                 '"Tài nguyên > Hệ điều hành" để tải lên.'),
            ))
            ra.append((
                o["co_install_wim"], "Ảnh cài đặt (install.wim)",
                (f"Đã có trong os/{os_id}/" if o["co_install_wim"] else
                 f'Chưa tải install.wim cho "{o["ten_hien_thi"]}" - vào tab '
                 '"Tài nguyên > Hệ điều hành" để tải lên.'),
            ))

    return ra


# ============================================================ trang thai wizard
#
# Giu trang thai cua trinh tu tu chon O PHIA MAY CHU (khong nhet vao cookie
# phien): cau hinh co danh sach phan vung/phan mem/script nen de vuot qua
# gioi han ~4KB cua cookie, luc do phien dang nhap se hong theo. Cach nay
# giong het _SCAN_CACHE trong ui/network.py va _PING_STATE trong
# nettools/ping_monitor.py - da chay on dinh tu truoc.
#
# Danh doi da biet: khoi dong lai dashboard thi trinh tu dang lam do mat
# (phai chon lai tu buoc 1). Chap nhan duoc vi kich ban da luu thi nam tren
# dia, khong mat.
_WIZARD = {}
_WIZARD_HAN = 6 * 3600          # don cac phien bo do qua 6 tieng


def _don_wizard_cu():
    nay = time.time()
    for k in [k for k, v in _WIZARD.items() if nay - v.get("_luc", 0) > _WIZARD_HAN]:
        _WIZARD.pop(k, None)


def _wizard_moi(che_do):
    """che_do: 'chay' = dung ngay | 'luu' = luu thanh kich ban."""
    _don_wizard_cu()
    ma = secrets.token_urlsafe(12)
    _WIZARD[ma] = {
        "_luc": time.time(),
        "che_do": che_do,
        "kieu_boot": "truc_tiep",
        "os_ho": "", "os_id": "", "driver_ids": [],
        "ten_may": "", "username": "", "password": "",
        "ssh": False, "mui_gio": MUI_GIO[0],
        # Tai khoan Administrator co san cua Windows: MAC DINH TAT (dung
        # dung cach Windows lam). Chi bat khi anh Thoai tich chon va dat
        # mat khau - tai khoan nay khong bi khoa man hinh dang nhap nhu
        # tai khoan thuong, nen bat ma de trong mat khau la rat nguy hiem.
        "bat_admin": False, "mk_admin": "",
        # Tu dong dang nhap (may kiosk/trung bay) + danh sach app kem san
        # can go (xem ui/unattend.py: APP_RAC).
        "tu_dang_nhap": False, "go_app": [],
        # Ngon ngu / ban phim / key Windows. Truoc day 3 thu nay deu bi
        # GHI CUNG trong ui/unattend.py (en-US + key KMS cong khai), nguoi
        # dung khong doi duoc.
        "ngon_ngu": NGON_NGU[0][0], "ban_phim": BAN_PHIM[0][0],
        "product_key": "",
        "o_dia_che_do": "tu_dong", "o_dia_so": "0", "o_dia_bang": "gpt",
        "phan_vung": [],
        "apps": [], "ungdung": [], "scripts": [], "lenh_them": "",
        # Gia nhap domain + cac tuy chon Windows sau khi cai (mo hinh MDT).
        # Xem ui/unattend.py: TUY_CHON_WINDOWS, _khoi_gia_nhap_domain().
        "domain": "", "domain_ou": "", "domain_user": "", "domain_pass": "",
        "tuy_chon": [],
    }
    return ma


def _wizard_lay(ma):
    d = _WIZARD.get(ma)
    if d is not None:
        d["_luc"] = time.time()
    return d


def _u_tuychon():
    """
    Bang tuy chon Windows - lay tu ui/unattend.py de giao dien va phan
    sinh XML dung CHUNG mot nguon, khong the lech nhau. Import trong ham
    (khong phai dau file) vi unattend.py da import nguoc lai deployos.py.
    """
    from . import unattend as _u
    return _u.TUY_CHON_WINDOWS


def _khoi_go_app(d, esc):
    """
    Khoi chon cac ung dung kem san can go (buoc 6).

    LAN DAU vao trinh tu thi tich san cac app duoc danh dau nen go trong
    ui/unattend.py (APP_RAC) - de anh Thoai khong phai tich tay 22 o moi
    lan tao kich ban. Nhung khi NAP LAI 1 kich ban da luu thi phai ton
    trong dung lua chon da luu, KE CA khi kich ban do co y khong go app
    nao: neu cu tich san theo mac dinh thi kich ban "giu nguyen may" se
    am tham bien thanh kich ban "go 22 app" - rat nguy hiem.
    Phan biet hai truong hop bang co "_da_qua_buoc6".
    """
    from . import unattend as _u
    if d.get("_da_qua_buoc6"):
        da_chon = set(d.get("go_app") or [])
    else:
        da_chon = {ma for ma, _ten, nen_go in _u.APP_RAC if nen_go}
    o = ""
    for ma, ten, nen_go in _u.APP_RAC:
        ch = " checked" if ma in da_chon else ""
        goi_y = ("" if nen_go else
                 ' <span style="color:#8b93a1;">(cân nhắc - nhiều người vẫn dùng)</span>')
        o += f"""
        <label class="chon">
          <input type="checkbox" name="go_app" value="{esc(ma)}"{ch}>
          <span class="t">{esc(ten)}</span>
          <div class="d">{esc(ma)}{goi_y}</div>
        </label>"""
    return f"""
              <div class="card">
                <h3>Gỡ ứng dụng kèm sẵn của Windows</h3>
                <p style="color:#8b93a1;font-size:13px;margin:0 0 9px;">
                  Gỡ cả bản đang cài lẫn "mầm" trong ảnh hệ điều hành, nên tài
                  khoản tạo mới sau này cũng không bị cài lại. Danh sách này đã
                  lọc sẵn - Microsoft Store, Máy tính, Ảnh, Paint, Notepad,
                  Snipping Tool đều được giữ lại vì gỡ đi sẽ gây khó chịu hoặc
                  hỏng chức năng.</p>
                {o}
              </div>"""


def _dong_tongket_windows(d, esc):
    """
    Cac dong rieng cua Windows trong bang tong ket: ngon ngu, ban phim,
    key, tai khoan Administrator. Linux khong co nhung muc nay nen tra ve
    rong (khong hien dong trong gay hieu nham).

    Hien TEN DOC DUOC chu khong hien ma (vi-VN, 0409:00000409...) - bang
    tong ket la de anh Thoai doi chieu truoc khi bam chay, doc ma so thi
    khong doi chieu duoc gi.
    """
    if d.get("os_ho") == "linux":
        return ""
    ten_nn = dict(NGON_NGU).get(d.get("ngon_ngu"), d.get("ngon_ngu") or "?")
    ten_bp = dict(BAN_PHIM).get(d.get("ban_phim"), d.get("ban_phim") or "?")
    if d.get("product_key"):
        # Chi hien 5 ky tu cuoi: bang tong ket hay bi chup man hinh gui
        # cho nhau, khong nen de nguyen key ra day.
        o_key = ("&bull;" * 5 + "-" * 1 + "&bull;" * 5 + "-&hellip;-"
                 + esc(d["product_key"][-5:])
                 + ' <span style="color:#8b93a1;">(đã nhập)</span>')
    else:
        o_key = ('<span style="color:#8b93a1;">Key KMS mặc định &mdash; '
                 'máy sẽ ở trạng thái chưa kích hoạt</span>')
    if d.get("bat_admin"):
        o_admin = ('<span style="color:#f59e0b;">Đã mở &mdash; có đặt mật '
                   'khẩu riêng</span>')
    else:
        o_admin = '<span style="color:#8b93a1;">Khoá (mặc định của Windows)</span>'
    if d.get("tu_dang_nhap"):
        o_tdn = ('<span style="color:#f59e0b;">Bật &mdash; bật máy vào thẳng '
                 'desktop, không hỏi mật khẩu</span>')
    else:
        o_tdn = '<span style="color:#8b93a1;">Tắt (vẫn hỏi mật khẩu)</span>'
    ds_go = d.get("go_app") or []
    if ds_go:
        from . import unattend as _u
        ten_theo_ma = {ma: ten for ma, ten, _ng in _u.APP_RAC}
        o_go = (f"{len(ds_go)} ứng dụng: "
                + ", ".join(esc(ten_theo_ma.get(m, m)) for m in ds_go))
    else:
        o_go = '<span style="color:#8b93a1;">Không gỡ ứng dụng nào</span>'
    return (f"<tr><td>Ngôn ngữ Windows</td><td>{esc(ten_nn)}</td></tr>\n"
            f"            <tr><td>Kiểu bàn phím</td><td>{esc(ten_bp)}</td></tr>\n"
            f"            <tr><td>Key Windows</td><td>{o_key}</td></tr>\n"
            f"            <tr><td>Tài khoản Administrator</td><td>{o_admin}</td></tr>\n"
            f"            <tr><td>Tự động đăng nhập</td><td>{o_tdn}</td></tr>\n"
            f"            <tr><td>Gỡ ứng dụng kèm sẵn</td><td>{o_go}</td></tr>")


def _phan_vung_mac_dinh(os_ho):
    """
    Bo phan vung goi y khi chuyen sang che do chia tay - de nguoi dung sua
    tu day thay vi go lai tu dau.

    Vi sao la bo nay (khong phai bia): day la bo phan vung chuan cua may
    UEFI/GPT.
      - Windows: EFI (FAT32) + MSR (Microsoft Reserved, khong dinh dang) +
        o he thong NTFS. MSR la yeu cau cua Windows tren GPT.
      - Linux: EFI (FAT32) + vung trao doi (swap) + o goc (ext4).
    """
    if os_ho == "windows":
        return [
            {"nhan": "EFI", "cd": "260", "fs": "fat32", "gan": "EFI"},
            {"nhan": "MSR", "cd": "16", "fs": "msr", "gan": "-"},
            {"nhan": "Windows", "cd": "con_lai", "fs": "ntfs", "gan": "C:"},
        ]
    return [
        {"nhan": "EFI", "cd": "512", "fs": "fat32", "gan": "/boot/efi"},
        {"nhan": "swap", "cd": "2048", "fs": "swap", "gan": "-"},
        {"nhan": "root", "cd": "con_lai", "fs": "ext4", "gan": "/"},
    ]


# ==================================================================== giao dien
def register_deployos(app):
    from flask import (request, redirect, send_from_directory, abort, jsonify,
                       flash, get_flashed_messages)
    from .layout import render_page
    from .home import _esc

    # --- Khai bao cac duong tai len duoc phep ghi THANG ra dia dich ---
    THU_MUC_THEO_DUONG.update({
        "/deployos/console/file/len": (BOOT_DIR, EXT_BOOT),
        "/deployos/console/apps/len": (APPS_DIR, EXT_APP),
        "/deployos/console/scripts/len": (SCRIPTS_DIR, EXT_SCRIPT),
    })

    # --- Chan tang Werkzeug: ghi thang file tai len ra dia dich ---
    #
    # Werkzeug goi _get_file_stream() de lay noi ghi du lieu tai len. Mac
    # dinh no tra ve 1 file tam; o day tra ve THANG file dich. Xem giai
    # thich day du (va loi that da gap) tai _mo_file_dich() o dau file.
    lop_request_goc = app.request_class

    class RequestTaiLenThang(lop_request_goc):
        def _get_file_stream(self, total_content_length, content_type,
                             filename=None, content_length=None):
            f, duong = _mo_file_dich(self.path, filename)
            if f is None:
                return super()._get_file_stream(
                    total_content_length, content_type, filename, content_length)
            # Ghi nho duong dan de route biet file vua duoc ghi vao dau.
            # Dat tren CHINH doi tuong file vi Werkzeug se boc no vao
            # FileStorage va route lay lai duoc qua .stream
            try:
                f._cp_duong_dan = duong
            except Exception:
                pass
            return f

    app.request_class = RequestTaiLenThang

    @app.before_request
    def _chan_som_khi_khong_du_cho():
        """
        Tu choi NGAY khi vua nhan header, TRUOC khi doc du lieu.

        LOI THAT DA GAP (anh Thoai gap that): truoc day phep kiem tra dung
        luong nam o CUOI - sau khi da nhan het file. Anh tai 1 file 4.6GB
        mat ~20 phut, den luc xong moi bao "can 10.1GB nhung chi con 10GB"
        va vut het di. Cho kiem tra dung phai la NGAY DAU, luc chua ton mot
        byte nao cua anh.
        """
        cau_hinh = THU_MUC_THEO_DUONG.get(request.path) or _thu_muc_os_theo_duong(request.path)
        if cau_hinh is None:
            return None
        can = request.content_length or 0
        if not can:
            return None
        # Ghi thang ra dia dich nen chi can DUNG BANG kich thuoc file
        # (+1GB de he thong con cho tho), khong con can gap doi/gap ba nua.
        can_gb = can / (1024 ** 3) + 1
        if _con_trong_gb() < can_gb:
            thu_muc = cau_hinh[0]
            return _trang(
                _tabs("tainguyen", "file") +
                f'<div class="msg err">File nay {co_kich_thuoc(can)} nen can '
                f'khoang {can_gb:.1f} GB trong, nhung chi con '
                f'{_con_trong_gb()} GB. Da dung lai NGAY, chua ton thoi gian '
                f'tai len cua anh. Xoa bot file cu hoac cam USB roi thu lai.</div>',
                "Deployment OS", "Khong du dung luong"), 413
        return None

    def _nhan_tai_len(thu_muc, duoi_cho_phep, nhan):
        """
        Nhan file vua tai len. Binh thuong du lieu DA nam san tren dia dich
        (do RequestTaiLenThang ghi thang), chi con doi ten .part -> ten that.
        Duong du phong (_luu_tai_len) chi chay khi vi ly do gi do khong ghi
        thang duoc.
        """
        f = request.files.get("file")
        if not f or not getattr(f, "filename", ""):
            return False, "Chua chon file."
        duong = getattr(getattr(f, "stream", None), "_cp_duong_dan", None)
        if duong:
            try:
                f.stream.flush()
                os.fsync(f.stream.fileno())
            except Exception:
                pass
            ok, msg, _duong_dich = _hoan_tat_ghi_thang(duong, thu_muc, f.filename)
            return ok, msg
        # Khong ghi thang duoc (vd duoi file khong hop le -> da do vao
        # /dev/null): bao loi ro rang thay vi im lang
        ten = ten_an_toan(f.filename)
        if os.path.splitext(ten)[1].lower() not in duoi_cho_phep:
            return False, (f"Khong nhan duoi file nay cho muc {nhan}. Chi nhan: "
                           f"{', '.join(sorted(duoi_cho_phep))}")
        return _luu_tai_len(f, thu_muc, duoi_cho_phep, nhan)

    @app.route("/deployos/tien-do")
    def deployos_tien_do():
        """
        Bao cho trang biet may DA GHI DUOC bao nhieu byte xuong dia that.

        Doc thang kich thuoc file <ten>.part dang duoc ghi. Nho vay thanh
        tien trinh bam theo tien do THAT tren dia, khong phai chi theo so
        byte trinh duyet da gui di (hai so nay lech nhau khi mang nhanh hon
        the nho - dung tinh huong lam anh Thoai tuong may bi treo).
        """
        loai = request.args.get("loai", "")
        ten = ten_an_toan(request.args.get("ten", ""))
        thu_muc = {"file": BOOT_DIR, "apps": APPS_DIR,
                   "scripts": SCRIPTS_DIR}.get(loai)
        if not thu_muc or not ten:
            return jsonify({"da_ghi": 0, "xong": False})
        p = os.path.join(thu_muc, ten + ".part")
        try:
            return jsonify({"da_ghi": os.path.getsize(p), "xong": False})
        except OSError:
            # Khong con .part: hoac chua bat dau, hoac da doi ten -> xong
            xong = os.path.isfile(os.path.join(thu_muc, ten))
            return jsonify({"da_ghi": 0, "xong": xong})

    # ------------------------------------------------------------ khung tab
    def _tabs(chinh, phu=""):
        """
        Thanh tab chinh + tab phu, dung chung cho moi trang cua muc nay.

        CAU TRUC CU (anh Thoai chi ra la SAI): "Kich ban" nam AN duoi 2 noi
        khac nhau ("Boot OS > Kich ban" VA "Console boot > 2.4 Kich ban")
        - kiem chung that: ca 2 cung doc/ghi CHUNG 1 du lieu
        (danh_sach_kichban()), chi la trung lap gay roi, khong phai hong du
        lieu. SUA (mo hinh MDT - "Task Sequences" la 1 nut GOC rieng, ngang
        hang voi "Operating Systems"/"Applications", khong nam lot duoi
        muc nao ca): dua "Kich ban" thanh 1 TAB GOC rieng, gop moi "tai
        nguyen" (He dieu hanh, Phan mem, Driver, Script, File boot) vao 1
        tab GOC khac.
        """
        tab_chinh = [
            ("kichban", "Kịch bản", "/deployos/kichban"),
            ("tainguyen", "Tài nguyên", "/deployos/os"),
            ("thamso", "Tham số cài đặt", "/deployos/thamso"),
            ("tiendo", "Tiến trình", "/deployos/tiendo"),
            ("caidat", "Cài đặt", "/deployos/caidat"),
        ]
        phu_theo_chinh = {
            "tainguyen": [
                ("os", "Hệ điều hành", "/deployos/os"),
                ("apps", "Phần mềm", "/deployos/console/apps"),
                ("ungdung", "Ứng dụng (nhiều file)", "/deployos/ungdung"),
                ("drivers", "Driver", "/deployos/drivers"),
                ("scripts", "Script", "/deployos/console/scripts"),
                ("file", "File boot", "/deployos/console"),
            ],
            "caidat": [
                ("pxe", "Bật / Tắt PXE", "/deployos/caidat"),
                ("hatang", "Kiểm tra hạ tầng", "/deployos/caidat/hatang"),
            ],
        }
        h = '<div class="dep-tabs">'
        for ma, nhan, href in tab_chinh:
            h += (f'<a href="{href}" class="dep-tab{" on" if ma == chinh else ""}">'
                  f'{nhan}</a>')
        h += "</div>"
        if phu:
            h += '<div class="dep-tabs sub">'
            for ma, nhan, href in phu_theo_chinh.get(chinh, []):
                h += (f'<a href="{href}" class="dep-tab{" on" if ma == phu else ""}">'
                      f'{nhan}</a>')
            h += "</div>"
        return h

    CSS = """
    /* ---- O "Tom tat" trong bang danh sach kich ban ----
       Cat dung 2 DONG roi them "..." bang -webkit-line-clamp, khong cat
       theo so KY TU: cat theo ky tu thi tren man hinh rong se thua cho
       trong, tren man hinh hep (RasPad doc) lai van tran 3-4 dong. */
    .tt-gon { display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;
              overflow:hidden; color:#c9ced6; font-size:13px; line-height:1.45; }
    .tt-nut { margin-top:6px; min-height:34px; padding:4px 12px; font-size:12.5px;
              background:#22262b; border:1px solid #2c3036; color:#c9ced6;
              border-radius:6px; }
    .tt-hop { border:1px solid #2c3036; border-radius:10px; background:#1b1e22;
              color:#e6e9ee; max-width:min(640px, 92vw); width:100%; padding:18px; }
    .tt-hop::backdrop { background:rgba(0,0,0,.6); }
    .tt-hop h3 { margin:0 0 12px; color:#4CAF50; }
    .tt-bang { width:100%; border-collapse:collapse; font-size:13.5px; }
    .tt-bang td { padding:7px 9px; border-bottom:1px solid #2c3036;
                  vertical-align:top; }

    /* ---- Bang tra tham so cai dat ---- */
    .hang-tim { display:flex; gap:8px; margin-bottom:8px; }
    .hang-tim input[type=search] { flex:1; min-height:48px; font-size:15px; }
    .ket-qua { color:#8b93a1; font-size:12.5px; margin-bottom:10px; }
    .khong-thay { color:#f59e0b; font-size:13.5px; padding:14px 4px; }
    /* Bang rong hon man hinh thi cho cuon NGANG trong khung nay, khong
       de ca trang bi keo ngang (RasPad man hinh nho). */
    .bang-cuon { overflow-x:auto; -webkit-overflow-scrolling:touch; }
    .bang-ts { width:100%; border-collapse:collapse; font-size:13.5px; }
    .bang-ts th, .bang-ts td { text-align:left; vertical-align:top;
      padding:9px 10px; border-bottom:1px solid #2c3036; }
    .bang-ts th { color:#8b93a1; font-weight:600; font-size:12.5px;
      white-space:nowrap; position:sticky; top:0; background:#1b1e22; }
    .bang-ts td:first-child { font-weight:600; color:#e6e9ee; min-width:150px; }
    .bang-ts code { display:block; white-space:pre-wrap; word-break:break-all;
      font-size:12.5px; color:#a8d8b0; background:#1f2429; padding:6px 8px;
      border-radius:5px; border:1px solid #2c3036; }
    .bang-ts code.chep { cursor:pointer; position:relative; }
    .bang-ts code.chep:active { transform:scale(.99); }
    .bang-ts code.da-chep { border-color:#4CAF50; background:#1f3a26; }
    .nhan-chep { position:absolute; right:6px; top:5px; font-size:11px;
      color:#4CAF50; background:#12331a; padding:1px 6px; border-radius:4px; }
    .cot-nut { white-space:nowrap; width:1%; }
    .cot-nut form { display:inline; }
    .nut-sua, .nut-huy { display:inline-flex; align-items:center;
      min-height:38px; padding:6px 13px; border-radius:6px; font-size:13px;
      background:#22262b; border:1px solid #2c3036; color:#c9ced6;
      margin-right:5px; }
    .bang-ts button.nho { min-height:38px; padding:6px 13px; font-size:13px; }
    .bang-ts button.do { background:#5a2222; border-color:#7a2e2e; }
    .o-sua { width:100%; min-width:160px; font-size:13px; }
    tr.dang-sua { background:#1f2a20; }
    .luoi-them { display:grid; gap:9px;
      grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); }
    .luoi-them textarea { width:100%; font-size:13.5px; }

    .dep-tabs { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:12px; }
    .dep-tabs.sub { margin-top:-4px; margin-bottom:18px; }
    .dep-tab { padding:11px 17px; min-height:46px; display:inline-flex;
      align-items:center; background:#22262b; border:1px solid #2c3036;
      border-radius:7px; color:#c9ced6; font-size:14px; }
    .dep-tab:active { transform:scale(.97); }
    .dep-tab.on { background:#1f3a26; border-color:#4CAF50; color:#fff; font-weight:600; }
    .dep-tabs.sub .dep-tab { padding:9px 14px; min-height:42px; font-size:13px; }

    /* Vach tien do cac buoc cua trinh tu tu chon */
    .buoc-bar { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:18px; }
    .buoc-o { flex:1; min-width:92px; padding:9px 8px; border-radius:6px;
      background:#22262b; border:1px solid #2c3036; text-align:center;
      font-size:12px; color:#8b93a1; }
    .buoc-o.qua { border-color:#4CAF50; color:#a8d5ab; }
    .buoc-o.nay { background:#1f3a26; border-color:#4CAF50; color:#fff; font-weight:600; }
    .buoc-o .so { display:block; font-size:15px; font-weight:700; margin-bottom:1px; }

    /* The lua chon lon (bam ca o, khong phai bam trung dung nut tron nho) */
    .chon { display:block; background:#22262b; border:2px solid #2c3036;
      border-radius:8px; padding:14px 16px; margin-bottom:10px; cursor:pointer; }
    .chon:active { transform:scale(.995); }
    .chon input { margin-right:9px; transform:scale(1.25); vertical-align:-1px; }
    .chon .t { font-size:15px; font-weight:600; color:#fff; }
    .chon .d { color:#8b93a1; font-size:13px; margin-top:5px; line-height:1.5; }
    .chon:has(input:checked) { border-color:#4CAF50; background:#1f3a26; }

    .pv-hang { display:flex; gap:8px; margin-bottom:8px; flex-wrap:wrap; align-items:center; }
    .pv-hang input, .pv-hang select { max-width:none; width:auto; flex:1; min-width:110px; }
    .tt-bang td { vertical-align:top; }
    .tt-bang td:first-child { color:#8b93a1; width:190px; }

    /* Thanh tien do tai len */
    .tt-khung { margin-top:6px; }
    .tt-ten { font-size:14px; color:#fff; margin-bottom:9px; word-break:break-all; }
    .tt-thanh-ngoai { width:100%; height:22px; background:#22262b; border-radius:7px;
      overflow:hidden; border:1px solid #2c3036; }
    .tt-thanh { height:100%; width:0%; background:#4CAF50; border-radius:7px;
      transition:width .3s ease; }
    .tt-so { display:flex; justify-content:space-between; margin-top:9px;
      font-size:14px; flex-wrap:wrap; gap:8px; }
    .tt-phantram { font-weight:700; color:#4CAF50; font-family:ui-monospace,monospace;
      font-size:17px; }
    .tt-chitiet { color:#a8b0bd; font-family:ui-monospace,monospace; }
    .tt-dia { margin-top:9px; font-size:13px; color:#8b93a1; min-height:19px; }
    """

    # JS cua thanh tien trinh - chi chen vao cac trang co form tai len
    JS_TIEN_DO = """
<script>
(function () {
  "use strict";
  function co(n) {
    if (n < 1024) return n + " B";
    var d = ["KB","MB","GB"], i = -1;
    do { n /= 1024; i++; } while (n >= 1024 && i < 2);
    return n.toFixed(1) + " " + d[i];
  }
  function thoiGian(giay) {
    if (!isFinite(giay) || giay < 0) return "";
    giay = Math.round(giay);
    if (giay < 60) return giay + " giay";
    var p = Math.floor(giay / 60), g = giay % 60;
    return p + " phut " + (g < 10 ? "0" : "") + g + " giay";
  }

  Array.prototype.forEach.call(
    document.querySelectorAll("form.form-tai-len"), function (form) {
    var khung = form.parentNode.querySelector(".tt-khung");
    if (!khung || !window.XMLHttpRequest || !window.FormData) return;  // de form thuong lo

    var thanh = khung.querySelector(".tt-thanh");
    var phantram = khung.querySelector(".tt-phantram");
    var chitiet = khung.querySelector(".tt-chitiet");
    var tenO = khung.querySelector(".tt-ten");
    var diaO = khung.querySelector(".tt-dia");
    var nutHuy = khung.querySelector(".tt-huy");
    var loai = form.getAttribute("data-loai") || "";
    var xhr = null, hen = null;

    form.addEventListener("submit", function (e) {
      var o = form.querySelector('input[type="file"]');
      if (!o || !o.files || !o.files.length) return;   // khong co file: de form bao loi
      e.preventDefault();

      var file = o.files[0];
      var batDau = Date.now();
      form.style.display = "none";
      khung.style.display = "block";
      tenO.textContent = file.name + "  (" + co(file.size) + ")";

      // Hoi may xem da ghi duoc bao nhieu XUONG DIA that. So nay moi la su
      // that cuoi cung - so byte trinh duyet gui di co the chay truoc no.
      function hoiDia() {
        if (!loai) return;
        var q = new XMLHttpRequest();
        q.open("GET", "/deployos/tien-do?loai=" + encodeURIComponent(loai) +
                      "&ten=" + encodeURIComponent(file.name), true);
        q.onload = function () {
          try {
            var d = JSON.parse(q.responseText);
            if (d.da_ghi > 0) {
              diaO.textContent = "Da ghi xuong dia: " + co(d.da_ghi) +
                " / " + co(file.size);
            }
          } catch (err) { /* bo qua, khong lam hong viec tai len */ }
        };
        q.send();
      }
      hen = setInterval(hoiDia, 2000);

      xhr = new XMLHttpRequest();
      xhr.open("POST", form.getAttribute("action"), true);

      xhr.upload.onprogress = function (ev) {
        if (!ev.lengthComputable) return;
        var pt = Math.round(ev.loaded * 100 / ev.total);
        thanh.style.width = pt + "%";
        phantram.textContent = pt + "%";
        var giay = (Date.now() - batDau) / 1000;
        var tocDo = giay > 0 ? ev.loaded / giay : 0;
        var conLai = tocDo > 0 ? (ev.total - ev.loaded) / tocDo : Infinity;
        chitiet.textContent = co(ev.loaded) + " / " + co(ev.total) +
          "  -  " + co(tocDo) + "/s  -  con " + thoiGian(conLai);
      };

      xhr.upload.onload = function () {
        // Trinh duyet gui xong roi, nhung may co the con dang ghi not
        phantram.textContent = "100%";
        thanh.style.width = "100%";
        chitiet.textContent = "Da gui xong, dang hoan tat luu tren may...";
      };

      xhr.onload = function () {
        clearInterval(hen);
        // May tra ve nguyen trang ket qua -> thay the trang hien tai
        document.open();
        document.write(xhr.responseText);
        document.close();
      };
      xhr.onerror = function () {
        clearInterval(hen);
        diaO.innerHTML = '<span style="color:#ef4444;">Mat ket noi toi may. ' +
          'File chua duoc luu - thu lai.</span>';
      };
      xhr.onabort = function () {
        clearInterval(hen);
        diaO.innerHTML = '<span style="color:#f59e0b;">Da huy tai len.</span>';
      };

      var fd = new FormData();
      fd.append("file", file);
      xhr.send(fd);
    });

    nutHuy.addEventListener("click", function () {
      if (xhr) xhr.abort();
      form.style.display = "";
      khung.style.display = "none";
      thanh.style.width = "0%";
      phantram.textContent = "0%";
      chitiet.textContent = "";
      diaO.textContent = "";
    });
  });
})();
</script>"""

    def _trang(body, title, subtitle="", active="/deployos"):
        if 'class="form-tai-len"' in body:
            body += JS_TIEN_DO
        return render_page(body, active=active, title=title,
                           subtitle=subtitle, extra_css=CSS)

    def _msg(msg, ok=True):
        return f'<div class="msg {"ok" if ok else "err"}">{_esc(msg)}</div>' if msg else ""

    # =================================================== 1. TAB "BOOT OS"
    @app.route("/deployos")
    def deployos_home():
        return redirect("/deployos/kichban")

    def _khoi_dang_phuc_vu():
        """
        Bang bao "may can cai dang duoc phuc vu theo kich ban nao".

        LY DO THAT (anh Thoai yeu cau sau 1 lan cai xong ma mat khau khong
        phai cua minh): anh dia cai dat la MOT file dung chung, ai dung
        sau de len nguoi truoc. Truoc day giao dien khong he noi anh dia
        DANG phuc vu la cua kich ban nao - nen khong tai nao biet no da bi
        ghi de. Bang nay doc dau vet that (ui/unattend.py: doc_dau_kichban)
        chu KHONG suy doan.
        """
        from . import pxe as _pxe
        from . import unattend as _u
        dang_bat = _pxe.dang_bat()
        dau = _u.doc_dau_kichban()

        if not dang_bat:
            return ('<div class="msg warn"><strong>Không chạy kịch bản nào.'
                    '</strong> PXE đang tắt - máy cắm vào sẽ không boot qua '
                    'mạng được. Bấm <em>Dùng</em> ở một kịch bản bên dưới để '
                    'chạy.</div>')

        if not dau:
            return ('<div class="msg warn"><strong>PXE đang bật nhưng chưa '
                    'dựng ảnh đĩa từ kịch bản nào.</strong> Máy cần cài sẽ '
                    'boot vào ảnh đĩa cũ (không rõ của ai). Bấm <em>Dùng</em> '
                    'ở kịch bản muốn chạy để dựng lại cho chắc.</div>')

        ten_kb = dau.get("ten_kichban") or ""
        nhan = (f"kịch bản <strong>{_esc(ten_kb)}</strong>" if ten_kb else
                "<strong>lựa chọn trực tiếp</strong> (chưa lưu thành kịch bản)")
        return f"""
        <div class="msg ok">
          <strong>Đang phục vụ {nhan}.</strong><br>
          <span style="font-size:12.5px;">
            Hệ điều hành: {_esc(dau.get('os_id') or '?')} &nbsp;&bull;&nbsp;
            Tên máy: {_esc(dau.get('ten_may') or '?')} &nbsp;&bull;&nbsp;
            Tài khoản: {_esc(dau.get('username') or '?')} &nbsp;&bull;&nbsp;
            Dựng ảnh đĩa lúc: {_esc(dau.get('dung_luc') or '?')}
          </span>
        </div>"""

    @app.route("/deployos/kichban")
    def deployos_boot():
        """
        Trang GOC duy nhat cho "Kich ban" (mo hinh MDT: nut "Task
        Sequences") - danh sach kich ban da luu la NOI DUNG CHINH, "Tao
        kich ban moi" la 1 nut dan toi trinh tu tung buoc (wizard). Thay
        cho 2 trang trung lap truoc day (xem ghi chu tai _tabs()).
        """
        ds_kb = danh_sach_kichban()
        if ds_kb:
            hang = ""
            for k in ds_kb:
                hang += f"""
                <tr>
                  <td><strong>{_esc(k.get('ten_kichban', k['_file']))}</strong></td>
                  <td>{_o_tom_tat(k, _esc)}</td>
                  <td style="color:#8b93a1;">{_esc(k.get('_ngay', ''))}</td>
                  <td>
                    <form method="POST"
                          action="/deployos/kichban/dung/{_esc(k['_file'])}"
                          style="display:inline;">
                      <button type="submit" class="small"
                        data-busy="Đang dựng ảnh đĩa... có thể mất 1 phút">
                        Dùng</button>
                    </form>
                    <a class="btn small gray"
                       href="/deployos/kichban/sua/{_esc(k['_file'])}">Chỉnh sửa</a>
                    <form method="POST" action="/deployos/kichban/xoa" style="display:inline;"
                          onsubmit="return confirm('Xóa kịch bản này?');">
                      <input type="hidden" name="ten" value="{_esc(k['_file'])}">
                      <button type="submit" class="red small">Xóa</button>
                    </form>
                  </td>
                </tr>"""
            noi_dung = f"""
            <div class="tbl-scroll"><table>
              <tr><th>Tên kịch bản</th><th>Tóm tắt</th>
                  <th style="width:140px;">Ngày tạo</th><th style="width:200px;">Thao tác</th></tr>
              {hang}
            </table></div>"""
        else:
            noi_dung = ('<p style="color:#8b93a1;">Chưa có kịch bản nào. '
                       'Bấm "Tạo kịch bản mới" bên dưới để tạo cái đầu tiên.</p>')

        # Thong diep ket qua sau khi bam "Dung" (chay ngay kich ban) -
        # nut do redirect ve day nen phai hien flash o day, khong thi
        # nguoi dung khong biet chay duoc hay khong.
        flash_html = "".join(
            _msg(nd, cat == "ok")
            for cat, nd in get_flashed_messages(with_categories=True))
        body = _tabs("kichban") + flash_html + _khoi_dang_phuc_vu() + f"""
        <div class="card">
          <h3>Tạo kịch bản mới</h3>
          <p style="color:#8b93a1;font-size:13.5px;margin:0 0 13px;">
            Đi qua {SO_BUOC} bước: kiểu boot &rarr; chọn OS &rarr; thông tin
            máy &rarr; chia ổ đĩa &rarr; phần mềm/driver &rarr; chỉnh sửa
            cài đặt &rarr; tổng kết. Lưu lại để dùng nhiều lần, không phải
            chọn lại từ đầu.</p>
          <a class="btn" href="/deployos/wizard/bat-dau?che_do=chay">
            Tạo kịch bản mới &rarr;</a>
        </div>

        <h2>Kịch bản đã lưu ({len(ds_kb)})</h2>
        {noi_dung}"""
        return _trang(body, "Deployment OS",
                      "Triển khai hệ điều hành qua mạng cho máy cần cài lại")

    @app.route("/deployos/kichban/xoa", methods=["POST"])
    def deployos_kichban_xoa():
        ok, msg = xoa_kichban(request.form.get("ten", ""))
        return redirect("/deployos/kichban")

    def _nap_kichban_vao_trinh_tu(ten):
        """Nap 1 kich ban da luu vao 1 trinh tu moi. Tra ve (ma, kb)."""
        kb = doc_kichban(ten)
        if kb is None:
            return None, None
        ma = _wizard_moi("chay")
        d = _WIZARD[ma]
        for k in ("kieu_boot", "os_ho", "os_id", "driver_ids", "ten_may",
                  "username", "password", "ssh", "mui_gio", "o_dia_che_do",
                  "o_dia_so", "o_dia_bang", "phan_vung", "apps", "ungdung",
                  "scripts", "lenh_them",
                  "domain", "domain_ou", "domain_user", "domain_pass",
                  "tuy_chon",
                  "bat_admin", "mk_admin", "ngon_ngu", "ban_phim",
                  "product_key", "tu_dang_nhap", "go_app"):
            if k in kb:
                d[k] = kb[k]
        d["tu_kichban"] = kb.get("ten_kichban", "")
        # Kich ban da luu thi lua chon "go app" trong do la CHINH THUC -
        # kho chon app phai hien dung no, khong duoc tich lai theo mac dinh
        # (xem _khoi_go_app). Ke ca kich ban khong go app nao.
        d["_da_qua_buoc6"] = True
        return ma, kb

    @app.route("/deployos/kichban/dung/<ten>", methods=["POST"])
    def deployos_dung_kichban(ten):
        """
        "Dung" = CHAY NGAY kich ban: dung lai anh dia cai dat theo dung
        kich ban nay roi bat PXE - khong bat nguoi dung phai vao them 1
        trang nua rui bam them 1 lan nua.

        (Truoc day nut nay chi NAP kich ban vao trinh tu roi nhay toi
        trang tong ket, phai bam tiep "Ap dung" o trong do - anh Thoai
        phan anh la thua 1 buoc. Viec chinh sua da tach han sang nut
        "Chinh sua" ben canh.)
        """
        ma, kb = _nap_kichban_vao_trinh_tu(ten)
        if ma is None:
            flash("Không tìm thấy kịch bản.", "err")
            return redirect("/deployos/kichban")

        d = _WIZARD[ma]
        thieu = _thieu_gi(d)
        if thieu:
            flash("Chưa chạy được: " + ", ".join(thieu) +
                  '. Bấm "Chỉnh sửa" để bổ sung.', "err")
            return redirect("/deployos/kichban")

        from . import pxe as _pxe
        ok, msg = _pxe.bat_pxe(d.get("kieu_boot", "truc_tiep"), d)
        flash(msg, "ok" if ok else "err")
        return redirect("/deployos/kichban")

    @app.route("/deployos/kichban/sua/<ten>")
    def deployos_sua_kichban(ten):
        """
        "Chinh sua" = nap kich ban vao trinh tu roi vao TUNG BUOC de sua,
        cuoi cung luu lai (nut "Luu de len kich ban ..." o buoc tong ket).
        """
        ma, _kb = _nap_kichban_vao_trinh_tu(ten)
        if ma is None:
            flash("Không tìm thấy kịch bản.", "err")
            return redirect("/deployos/kichban")
        return redirect(f"/deployos/wizard/{ma}/1")

    # ================================================ TRINH TU TU CHON (wizard)
    @app.route("/deployos/wizard/bat-dau")
    def deployos_wizard_batdau():
        che_do = request.args.get("che_do", "chay")
        if che_do not in ("chay", "luu"):
            che_do = "chay"
        ma = _wizard_moi(che_do)
        return redirect(f"/deployos/wizard/{ma}/1")

    def _het_han():
        return _trang(
            _tabs("kichban") +
            '<div class="msg warn">Trinh tu nay da het han hoac dashboard vua '
            'khoi dong lai nen khong con giu duoc lua chon dang do. '
            '<a href="/deployos/boot">Bat dau lai</a> - kich ban da luu tren '
            'dia thi khong mat.</div>',
            "Deployment OS")

    @app.route("/deployos/wizard/<ma>/<int:buoc>", methods=["GET", "POST"])
    def deployos_wizard(ma, buoc):
        d = _wizard_lay(ma)
        if d is None:
            return _het_han()
        if buoc < 1 or buoc > SO_BUOC:
            return redirect(f"/deployos/wizard/{ma}/1")

        if request.method == "POST":
            loi = _nhan_du_lieu_buoc(d, buoc, request.form)
            huong = request.form.get("huong", "tiep")
            if huong == "lui":
                return redirect(f"/deployos/wizard/{ma}/{max(1, buoc - 1)}")
            if loi:
                return _ve_buoc(ma, d, buoc, loi=loi)
            if buoc < SO_BUOC:
                return redirect(f"/deployos/wizard/{ma}/{buoc + 1}")
            return redirect(f"/deployos/wizard/{ma}/{SO_BUOC}")

        return _ve_buoc(ma, d, buoc)

    def _nhan_du_lieu_buoc(d, buoc, form):
        """Ghi lua chon cua 1 buoc vao trang thai. Tra ve chuoi loi neu thieu."""
        if buoc == 1:
            v = form.get("kieu_boot", "")
            if v not in [k for k, _, _ in KIEU_BOOT]:
                return "Chưa chọn kiểu boot."
            d["kieu_boot"] = v

        elif buoc == 2:
            os_id = form.get("os_id", "")
            o = lay_os(os_id)
            if o is None:
                return "Chưa chọn hệ điều hành (hoặc chưa tạo hệ điều hành nào - vào tab Tài nguyên > Hệ điều hành)."
            if not o["san_sang"]:
                return f'"{o["ten_hien_thi"]}" còn thiếu boot.wim/install.wim - vào "Tài nguyên > Hệ điều hành" tải lên trước.'
            # Doi OS ho khac thi bo phan vung chia tay cu di (bo phan vung
            # cua Windows va Linux khac han nhau - giu lai se sai)
            if d.get("os_ho") and d["os_ho"] != o["os_ho"]:
                d["phan_vung"] = []
            d["os_id"] = os_id
            d["os_ho"] = o["os_ho"]
            d["driver_ids"] = form.getlist("driver_ids")

        elif buoc == 3:
            d["ten_may"] = (form.get("ten_may") or "").strip()
            d["username"] = (form.get("username") or "").strip()
            # Chi ghi de mat khau khi nguoi dung go moi. Ly do: o mat khau
            # KHONG duoc dien san gia tri cu ra trang (xem _noi_dung_buoc) -
            # neu o day cu ghi de bang chuoi rong thi moi lan quay lui roi
            # tiep tuc la mat khau da nhap bi xoa mat ma khong ai biet.
            mk_moi = form.get("password") or ""
            if mk_moi:
                d["password"] = mk_moi
            d["ssh"] = bool(form.get("ssh")) if d.get("os_ho") == "linux" else False
            mg = form.get("mui_gio", MUI_GIO[0])
            d["mui_gio"] = mg if mg in MUI_GIO else MUI_GIO[0]

            # ---- Ngon ngu / ban phim / key Windows / tai khoan Administrator
            # (chi co y nghia voi Windows - Linux bo qua het)
            if d.get("os_ho") != "linux":
                nn = form.get("ngon_ngu") or NGON_NGU[0][0]
                d["ngon_ngu"] = nn if any(nn == m for m, _ in NGON_NGU) else NGON_NGU[0][0]
                bp = form.get("ban_phim") or BAN_PHIM[0][0]
                d["ban_phim"] = bp if any(bp == m for m, _ in BAN_PHIM) else BAN_PHIM[0][0]

                # Key Windows: bo het dau cach/gach noi thua roi chuan hoa
                # ve dang 5 nhom 5 ky tu. De TRONG la hop le - luc do dung
                # key KMS cong khai mac dinh (xem ui/unattend.py).
                pk = re.sub(r"[^A-Za-z0-9]", "", form.get("product_key") or "").upper()
                if pk:
                    if len(pk) != 25:
                        return ("Key Windows phải đúng 25 ký tự (5 nhóm 5 ký "
                                "tự). Để trống nếu muốn dùng key mặc định.")
                    pk = "-".join(pk[i:i + 5] for i in range(0, 25, 5))
                d["product_key"] = pk

                d["tu_dang_nhap"] = bool(form.get("tu_dang_nhap"))
                d["bat_admin"] = bool(form.get("bat_admin"))
                mk_ad_moi = form.get("mk_admin") or ""
                if mk_ad_moi:
                    d["mk_admin"] = mk_ad_moi
                if not d["bat_admin"]:
                    # Bo tich thi xoa luon mat khau da luu - khong giu lai
                    # mat khau cua mot tai khoan dang tat.
                    d["mk_admin"] = ""
                elif not d["mk_admin"]:
                    return ("Đã chọn mở tài khoản Administrator thì phải đặt "
                            "mật khẩu cho nó. Tài khoản này có toàn quyền và "
                            "không bị giới hạn như tài khoản thường.")

            if not d["ten_may"]:
                return "Chua dien ten may."
            if not d["username"]:
                return "Chua dien ten dang nhap."
            # Ten may: theo quy tac chung cua ca Windows lan Linux (chu, so,
            # dau gach ngang; khong dau cach) - de tranh loi luc cai
            if not re.fullmatch(r"[A-Za-z0-9-]{1,15}", d["ten_may"]):
                return ("Ten may chi duoc dung chu khong dau, so va dau gach "
                        "ngang, toi da 15 ky tu (quy tac chung cua ca Windows "
                        "lan Linux).")

        elif buoc == 4:
            che = form.get("o_dia_che_do", "tu_dong")
            d["o_dia_che_do"] = "chia_tay" if che == "chia_tay" else "tu_dong"
            so = (form.get("o_dia_so") or "0").strip()
            d["o_dia_so"] = so if so.isdigit() else "0"
            bang = form.get("o_dia_bang", "gpt")
            d["o_dia_bang"] = bang if bang in ("gpt", "mbr") else "gpt"
            if d["o_dia_che_do"] == "chia_tay":
                nhan = form.getlist("pv_nhan")
                cd = form.getlist("pv_cd")
                fs = form.getlist("pv_fs")
                gan = form.getlist("pv_gan")
                pv = []
                for i in range(len(nhan)):
                    ten = (nhan[i] or "").strip()
                    if not ten:
                        continue
                    pv.append({
                        "nhan": ten[:24],
                        "cd": (cd[i] if i < len(cd) else "").strip() or "con_lai",
                        "fs": (fs[i] if i < len(fs) else "").strip() or "ntfs",
                        "gan": (gan[i] if i < len(gan) else "").strip() or "-",
                    })
                if not pv:
                    return "Che do chia tay can it nhat 1 phan vung."
                d["phan_vung"] = pv

        elif buoc == 5:
            # Moi phan mem duoc chon kem 1 lua chon "cai cho ai": cap MAY
            # (moi nguoi dung deu dung duoc, chay truoc khi co ai dang
            # nhap) hay cap NGUOI DUNG (chay trong phien dang nhap dau).
            d["apps"] = [
                {"ten": ten,
                 "dich": ("nguoi_dung"
                          if form.get(f"dich_{ten}") == "nguoi_dung" else "may")}
                for ten in form.getlist("app")
            ]
            # Ung dung kieu thu muc (mo hinh MDT) - xem giai thich trong
            # danh_sach_ungdung() o deployos.py.
            d["ungdung"] = [
                {"id": uid,
                 "dich": ("nguoi_dung"
                          if form.get(f"dich_ud_{uid}") == "nguoi_dung" else "may")}
                for uid in form.getlist("ungdung")
            ]

        elif buoc == 6:
            d["scripts"] = form.getlist("script")
            d["lenh_them"] = (form.get("lenh_them") or "").strip()[:4000]
            d["domain"] = (form.get("domain") or "").strip()
            d["domain_ou"] = (form.get("domain_ou") or "").strip()
            d["domain_user"] = (form.get("domain_user") or "").strip()
            # Mat khau domain: chi ghi de khi go moi - giong het cach xu ly
            # mat khau may o buoc 3 (o mat khau khong dien san gia tri cu ra
            # trang, neu ghi de bang chuoi rong thi quay lui 1 lan la mat).
            mk_domain = form.get("domain_pass") or ""
            if mk_domain:
                d["domain_pass"] = mk_domain
            hop_le = {ma for ma, _n, _m, _p, _l in _u_tuychon()}
            d["tuy_chon"] = [t for t in form.getlist("tuy_chon") if t in hop_le]

            from . import unattend as _u
            hop_le_app = {ma for ma, _ten, _ng in _u.APP_RAC}
            d["go_app"] = [a for a in form.getlist("go_app") if a in hop_le_app]
            # Danh dau da di qua buoc 6 it nhat 1 lan. Tu day tro di khoi
            # chon app phai hien dung lua chon da luu chu khong tich lai
            # theo mac dinh (xem _khoi_go_app).
            d["_da_qua_buoc6"] = True

        return ""

    # --------------------------------------------------------- ve tung buoc
    def _thanh_buoc(buoc):
        h = '<div class="buoc-bar">'
        for so, ten in TEN_BUOC:
            cls = "nay" if so == buoc else ("qua" if so < buoc else "")
            h += f'<div class="buoc-o {cls}"><span class="so">{so}</span>{_esc(ten)}</div>'
        return h + "</div>"

    def _nut_dieu_huong(buoc, nhan_tiep="Tiếp theo &rarr;"):
        lui = ('<button type="submit" name="huong" value="lui" class="gray">'
               '&larr; Quay lại</button>' if buoc > 1 else "")
        return f"""
        <div class="row" style="margin-top:20px;gap:10px;">
          {lui}
          <button type="submit" name="huong" value="tiep">{nhan_tiep}</button>
        </div>"""

    def _ve_buoc(ma, d, buoc, loi=""):
        from flask import get_flashed_messages
        # Thong diep tu cac hanh dong PXE that (Bat/Tat/Trich bootmgr) - xem
        # ui/pxe.py: _ve_lai(). Dung flash() vi cac hanh dong do redirect
        # ve day, khong render truc tiep duoc nhu cac form khac trong wizard.
        flash_html = "".join(_msg(nd, cat == "ok")
                             for cat, nd in get_flashed_messages(with_categories=True))
        than = (_tabs("kichban") + _thanh_buoc(buoc) + _msg(loi, False) +
                flash_html + _noi_dung_buoc(ma, d, buoc))
        tieu_de = ("Tao kich ban" if d.get("che_do") == "luu"
                   else "Deployment OS")
        return _trang(than, tieu_de,
                      f"Bước {buoc}/{SO_BUOC}: {dict(TEN_BUOC)[buoc]}",
                      active="/deployos")

    def _noi_dung_buoc(ma, d, buoc):
        act = f'action="/deployos/wizard/{ma}/{buoc}"'

        # ---------------------------------------------- 1.1.1 kieu boot
        if buoc == 1:
            o = ""
            for gt, ten, mo_ta in KIEU_BOOT:
                ch = " checked" if d["kieu_boot"] == gt else ""
                o += f"""
                <label class="chon">
                  <input type="radio" name="kieu_boot" value="{gt}"{ch}>
                  <span class="t">{_esc(ten)}</span>
                  <div class="d">{_esc(mo_ta)}</div>
                </label>"""
            return f"""
            <form method="POST" {act}>
              <div class="card"><h3>Chọn kiểu boot</h3>{o}</div>
              {_nut_dieu_huong(buoc)}
            </form>"""

        # ------------------------------------------------- 1.1.2 chon OS
        if buoc == 2:
            ds_os = danh_sach_os()
            muc_os = ""
            for o in ds_os:
                ch = " checked" if d.get("os_id") == o["id"] else ""
                nhan_trang_thai = ("" if o["san_sang"] else
                                   ' <span style="color:#e0a030;">(thiếu file)</span>')
                muc_os += f"""
                <label class="chon" style="margin-bottom:8px;">
                  <input type="radio" name="os_id" value="{_esc(o['id'])}"{ch} required>
                  <span class="t">{_esc(o['ten_hien_thi'])}{nhan_trang_thai}</span>
                  <div class="d">{_esc(o['os_ho'])} - {_esc(o['kich_thuoc'])}</div>
                </label>"""
            if not ds_os:
                khoi_os = ("""<div class="msg warn">Chưa có hệ điều hành nào.
                Vào <a href="/deployos/os">Tài nguyên &gt; Hệ điều hành</a>
                để thêm trước.</div>""")
            else:
                khoi_os = f'<div class="card"><h3>Chọn hệ điều hành</h3>{muc_os}</div>'

            ds_driver = danh_sach_driver()
            da_chon_driver = set(d.get("driver_ids") or [])
            if ds_driver:
                muc_driver = ""
                for dr in ds_driver:
                    ch = " checked" if dr["id"] in da_chon_driver else ""
                    muc_driver += f"""
                    <label class="chon" style="margin-bottom:8px;">
                      <input type="checkbox" name="driver_ids" value="{_esc(dr['id'])}"{ch}>
                      <span class="t">{_esc(dr['ten_hien_thi'])}</span>
                      <div class="d">{dr['so_file']} file</div>
                    </label>"""
                khoi_driver = f"""
                <div class="card">
                  <h3>Driver tiêm kèm (không bắt buộc)</h3>
                  <p style="color:#8b93a1;font-size:13px;margin:0 0 9px;">
                    Chọn 0 hoặc nhiều gói - Windows Setup sẽ tự quét và cài
                    driver phù hợp trong lúc chạy (giống "Out-of-Box
                    Drivers" của MDT).</p>
                  {muc_driver}
                </div>"""
            else:
                khoi_driver = """
                <div class="msg info" style="font-size:13px;">
                  Chưa có gói driver nào (không bắt buộc) - thêm ở
                  <a href="/deployos/drivers">Tài nguyên &gt; Driver</a> nếu
                  máy cần cài có phần cứng ít gặp (mạng/WiFi đời mới/RAID...).
                </div>"""

            return f"""
            <form method="POST" {act}>
              {khoi_os}
              {khoi_driver}
              {_nut_dieu_huong(buoc)}
            </form>"""

        # -------------------------------------------- 1.1.3 thong tin OS
        if buoc == 3:
            if not d["os_ho"]:
                return ('<div class="msg warn">Chưa chọn hệ điều hành ở bước 2. '
                        f'<a href="/deployos/wizard/{ma}/2">Quay lại bước 2</a>.</div>')
            la_linux = d["os_ho"] == "linux"
            o_ssh = ""
            if la_linux:
                ch = " checked" if d.get("ssh") else ""
                o_ssh = f"""
                <label class="chon" style="margin-top:14px;">
                  <input type="checkbox" name="ssh" value="1"{ch}>
                  <span class="t">Bật SSH ngay sau khi cài</span>
                  <div class="d">Cài sẵn openssh-server và bật dịch vụ - vào
                  được máy từ xa ngay, không phải ra tận nơi bật tay.</div>
                </label>"""

            opt_tz = ""
            for tz in MUI_GIO:
                s = " selected" if d["mui_gio"] == tz else ""
                opt_tz += f'<option value="{tz}"{s}>{tz}</option>'

            # ---- Khoi rieng cho Windows: ngon ngu, ban phim, key, Administrator
            khoi_windows = ""
            if not la_linux:
                opt_nn = ""
                for ma_nn, ten_nn in NGON_NGU:
                    s = " selected" if d.get("ngon_ngu") == ma_nn else ""
                    opt_nn += f'<option value="{ma_nn}"{s}>{_esc(ten_nn)}</option>'
                opt_bp = ""
                for ma_bp, ten_bp in BAN_PHIM:
                    s = " selected" if d.get("ban_phim") == ma_bp else ""
                    opt_bp += f'<option value="{ma_bp}"{s}>{_esc(ten_bp)}</option>'
                ad_ch = " checked" if d.get("bat_admin") else ""
                tdn_ch = " checked" if d.get("tu_dang_nhap") else ""
                # O mat khau Administrator an/hien theo o tich - lam bang
                # thuoc tinh `hidden` + 1 doan JS ngan, khong dung thu vien.
                an_mk = "" if d.get("bat_admin") else " hidden"
                nhac_mk_ad = ("Đã đặt rồi - để trống nếu không đổi"
                              if d.get("mk_admin") else "Mật khẩu cho Administrator")
                khoi_windows = f"""
                <label>Ngôn ngữ hiển thị của Windows</label>
                <select name="ngon_ngu">{opt_nn}</select>
                <p style="color:#8b93a1;font-size:12.5px;margin:7px 0 0;">
                  Chỉ đổi được nếu bản Windows đang cài CÓ SẴN gói ngôn ngữ đó.
                  Ảnh Windows tải về thường chỉ có một ngôn ngữ - chọn thứ
                  không có thì Windows lặng lẽ quay về English chứ không báo lỗi.</p>

                <label>Kiểu bàn phím</label>
                <select name="ban_phim">{opt_bp}</select>
                <p style="color:#8b93a1;font-size:12.5px;margin:7px 0 0;">
                  Khác với ngôn ngữ hiển thị - đây là cách các phím được hiểu,
                  luôn có tác dụng. Tiếng Việt dùng bàn phím US rồi gõ bằng
                  Unikey/EVKey, nên cứ để US là đúng.</p>

                <label>Key Windows (để trống nếu không có)</label>
                <input type="text" name="product_key"
                       value="{_esc(d.get('product_key') or '')}"
                       placeholder="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"
                       autocapitalize="characters" autocomplete="off">
                <p style="color:#8b93a1;font-size:12.5px;margin:7px 0 0;">
                  Để trống thì dùng key KMS công khai chính thức của Microsoft
                  (cài được nhưng máy ở trạng thái CHƯA kích hoạt cho tới khi
                  anh nhập key thật hoặc máy gặp máy chủ KMS của công ty).</p>

                <label class="chon" style="margin-top:14px;">
                  <input type="checkbox" name="bat_admin" value="1"{ad_ch}
                         id="o_bat_admin">
                  <span class="t">Mở tài khoản Administrator có sẵn</span>
                  <div class="d">Windows vốn khoá sẵn tài khoản này. Mở ra thì
                  có một tài khoản toàn quyền dự phòng - vào được máy kể cả khi
                  tài khoản chính hỏng hoặc quên mật khẩu.</div>
                </label>
                <div id="khoi_mk_admin"{an_mk}>
                  <label>Mật khẩu cho Administrator</label>
                  <input type="password" name="mk_admin" value=""
                         autocomplete="new-password"
                         placeholder="{nhac_mk_ad}">
                  <p style="color:#f59e0b;font-size:12.5px;margin:7px 0 0;">
                    Tài khoản này có toàn quyền và KHÔNG bị khoá sau nhiều lần
                    nhập sai như tài khoản thường - hãy đặt mật khẩu mạnh.</p>
                </div>

                <label class="chon" style="margin-top:14px;">
                  <input type="checkbox" name="tu_dang_nhap" value="1"{tdn_ch}>
                  <span class="t">Giữ tự động đăng nhập MÃI MÃI</span>
                  <div class="d">Lần đầu sau khi cài xong thì máy <strong>luôn
                  tự đăng nhập</strong> (giống MDT) — để phần mềm cài nốt và
                  hiện được bảng báo cáo. Tích ô này nghĩa là những lần bật máy
                  sau <em>cũng</em> không hỏi mật khẩu: tiện cho máy kiosk, máy
                  trưng bày, nhưng ai chạm vào máy cũng dùng được. Không tích
                  thì từ lần thứ hai trở đi máy hỏi mật khẩu bình thường.</div>
                </label>
                <script>
                (function() {{
                  var o = document.getElementById('o_bat_admin');
                  var k = document.getElementById('khoi_mk_admin');
                  if (o && k) o.addEventListener('change', function() {{
                    k.hidden = !o.checked;
                  }});
                }})();
                </script>"""

            return f"""
            <form method="POST" {act}>
              <div class="card">
                <h3>Thông tin máy sẽ cài</h3>
                <label>Tên máy (hostname)</label>
                <input type="text" name="ten_may" value="{_esc(d['ten_may'])}"
                       placeholder="vd: PC-KETOAN-01" autocapitalize="off">
                <label>Tên đăng nhập (username)</label>
                <input type="text" name="username" value="{_esc(d['username'])}"
                       placeholder="vd: admin" autocapitalize="off">
                <label>Mật khẩu</label>
                <input type="password" name="password" value=""
                       placeholder="{'Đã đặt rồi - để trống nếu không đổi' if d['password'] else 'Mật khẩu cho tài khoản trên máy đó'}">
                <p style="color:#8b93a1;font-size:12.5px;margin:7px 0 0;">
                  Đây là mật khẩu cho tài khoản SẼ TẠO trên máy đang cài lại,
                  không phải mật khẩu của Console Pi. Nếu lưu thành kịch bản,
                  file kịch bản được để quyền chỉ root đọc được (600).
                  {'<br>Da co mat khau - de trong o nay thi giu nguyen cai cu.' if d['password'] else ''}</p>
                <!-- O mat khau KHONG dien san gia tri cu: dien san thi mat
                     khau nam thang trong ma nguon trang, ai xem nguon (hoac
                     anh chup man hinh dev tools) deu doc duoc. -->

                <label>Mui gio</label>
                <select name="mui_gio">{opt_tz}</select>
                {khoi_windows}
                {o_ssh}
              </div>
              {_nut_dieu_huong(buoc)}
            </form>"""

        # ------------------------------------------ 1.1.4 phan chia o dia
        if buoc == 4:
            tu_dong_ch = " checked" if d["o_dia_che_do"] == "tu_dong" else ""
            tay_ch = " checked" if d["o_dia_che_do"] == "chia_tay" else ""
            pv = d["phan_vung"] or _phan_vung_mac_dinh(d["os_ho"])

            fs_lua = (["ntfs", "fat32", "msr", "ext4", "swap", "xfs", "btrfs"]
                      if d["os_ho"] == "linux" else
                      ["ntfs", "fat32", "msr", "ext4"])
            hang = ""
            for p in pv:
                opt_fs = ""
                for f in fs_lua:
                    s = " selected" if p.get("fs") == f else ""
                    opt_fs += f'<option value="{f}"{s}>{f}</option>'
                hang += f"""
                <div class="pv-hang">
                  <input type="text" name="pv_nhan" value="{_esc(p.get('nhan',''))}" placeholder="Nhãn">
                  <input type="text" name="pv_cd" value="{_esc(p.get('cd',''))}" placeholder="MB hoặc con_lai">
                  <select name="pv_fs">{opt_fs}</select>
                  <input type="text" name="pv_gan" value="{_esc(p.get('gan',''))}" placeholder="C: hoặc /">
                  <button type="button" class="red small" onclick="this.parentNode.remove()">Xóa</button>
                </div>"""

            return f"""
            <form method="POST" {act}>
              <div class="card">
                <h3>Cách chia ổ đĩa</h3>
                <label class="chon">
                  <input type="radio" name="o_dia_che_do" value="tu_dong"{tu_dong_ch}>
                  <span class="t">Phân chia tự động</span>
                  <div class="d">Dùng ổ đĩa số 0 (ổ đầu tiên máy nhìn thấy),
                  xóa sạch và chia theo bộ phân vùng chuẩn của hệ điều hành
                  đã chọn.</div>
                </label>
                <label class="chon">
                  <input type="radio" name="o_dia_che_do" value="chia_tay"{tay_ch}>
                  <span class="t">Chia bằng tay</span>
                  <div class="d">Tự khai báo từng phân vùng bên dưới. Dùng khi
                  máy có nhiều ổ cứng, hoặc muốn chia thêm ổ D: để chứa dữ liệu
                  riêng.</div>
                </label>
              </div>

              <div class="card">
                <h3>Thông số ổ đĩa</h3>
                <div class="row">
                  <div>
                    <label>Ổ đĩa số</label>
                    <input type="number" name="o_dia_so" value="{_esc(d['o_dia_so'])}"
                           min="0" max="15" style="max-width:130px;">
                  </div>
                  <div>
                    <label>Bảng phân vùng</label>
                    <select name="o_dia_bang" style="max-width:260px;">
                      <option value="gpt"{' selected' if d['o_dia_bang'] == 'gpt' else ''}>GPT (máy UEFI - hầu hết máy từ 2012)</option>
                      <option value="mbr"{' selected' if d['o_dia_bang'] == 'mbr' else ''}>MBR (máy BIOS đời cũ)</option>
                    </select>
                  </div>
                </div>
                <div class="msg warn" style="margin-top:14px;">
                  <strong>Cảnh báo thật:</strong> chia ổ đĩa là thao tác GHI ĐÈ -
                  toàn bộ dữ liệu trên ổ đĩa được chọn sẽ mất. Nếu máy có
                  nhiều ổ cứng, kiểm tra kỹ "ổ đĩa số" trước khi chạy.
                </div>
              </div>

              <div class="card">
                <h3>Danh sách phân vùng (chỉ dùng khi chọn "chia bằng tay")</h3>
                <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
                  Dung lượng điền bằng MB, hoặc gõ <code>con_lai</code> để lấy
                  hết chỗ trống còn lại. Cột cuối là ổ/điểm gắn
                  ({'vd <code>/</code>, <code>/home</code>' if d['os_ho'] == 'linux' else 'vd <code>C:</code>, <code>D:</code>'}).
                  Với Windows trên GPT bắt buộc phải có phân vùng <code>EFI</code>
                  và <code>MSR</code> - đã điền sẵn theo đúng chuẩn.</p>
                <div id="pvbox">{hang}</div>
                <button type="button" class="gray small" onclick="themPV()">+ Thêm phân vùng</button>
              </div>

              {_nut_dieu_huong(buoc)}
            </form>
            <script>
            function themPV() {{
              var box = document.getElementById("pvbox");
              var mau = box.querySelector(".pv-hang");
              if (!mau) return;
              var moi = mau.cloneNode(true);
              moi.querySelectorAll("input").forEach(function (i) {{ i.value = ""; }});
              box.appendChild(moi);
            }}
            </script>"""

        # ------------------------------------------------- 1.1.5 phan mem
        if buoc == 5:
            ds = danh_sach_app()
            if not ds:
                than = """
                <div class="msg warn">Chưa có phần mềm nào được tải lên.
                Vào tab <a href="/deployos/console/apps">Phần mềm</a> để
                tải file .msi/.exe lên trước, rồi quay lại bước này.
                Bỏ qua bước này cũng được - lúc đó máy chỉ cài OS, không cài
                thêm phần mềm.</div>"""
            else:
                da_chon = {a["ten"]: a["dich"]
                           for a in chuan_hoa_apps(d.get("apps"))}
                o = ""
                for a in ds:
                    ch = " checked" if a["ten"] in da_chon else ""
                    tsm = a["tham_so"] or tham_so_mac_dinh_app(a["ten"])
                    ts = (f'<code>{_esc(tsm)}</code>' if tsm
                          else '<span style="color:#f59e0b;">chưa điền tham số '
                               'cài im lặng - bộ cài có thể hiện giao diện và '
                               'làm treo quá trình cài</span>')
                    dich = da_chon.get(a["ten"], "may")
                    o += f"""
                    <label class="chon">
                      <input type="checkbox" name="app" value="{_esc(a['ten'])}"{ch}>
                      <span class="t">{_esc(a['ten'])}</span>
                      <div class="d">{co_kich_thuoc(a['cd'])} &middot; tham so: {ts}</div>
                      <div class="d" style="margin-top:6px;">
                        Cài cho:
                        <select name="dich_{_esc(a['ten'])}"
                                style="width:auto;display:inline-block;padding:3px 6px;">
                          <option value="may"{' selected' if dich == 'may' else ''}
                            >Máy (mọi người dùng)</option>
                          <option value="nguoi_dung"{' selected' if dich == 'nguoi_dung' else ''}
                            >Chỉ người dùng đăng nhập đầu</option>
                        </select>
                      </div>
                    </label>"""
                than = f"""
                <div class="card"><h3>Chọn phần mềm sẽ cài</h3>{o}</div>
                <div class="card">
                  <h3>Cài cho "Máy" và "Người dùng" khác nhau chỗ nào</h3>
                  <table class="tt-bang">
                    <tr><td style="width:150px;">Máy</td>
                        <td>Chạy TRƯỚC khi có ai đăng nhập, với quyền hệ thống.
                        Mọi người dùng trên máy đều dùng được phần mềm. Hợp
                        với .msi và các bộ cài im lặng. <strong>Nếu bộ cài đòi
                        hiện giao diện thì sẽ làm treo</strong> - lúc đó chọn
                        mục dưới.</td></tr>
                    <tr><td>Người dùng</td>
                        <td>Chạy khi người dùng đầu tiên đăng nhập. Hợp với
                        phần mềm chỉ cài riêng cho 1 người, hoặc bộ cài cần
                        môi trường đăng nhập đầy đủ.</td></tr>
                  </table>
                  <p style="color:#8b93a1;font-size:12.5px;margin:10px 0 0;">
                    Tham số cài im lặng đặt ở tab
                    <a href="/deployos/console/apps">Phần mềm</a> (theo từng
                    file, dùng chung cho mọi kịch bản).</p>
                </div>"""

            ds_ud = danh_sach_ungdung()
            khoi_ungdung = ""
            if ds_ud:
                da_chon_ud = {u["id"]: u["dich"]
                             for u in chuan_hoa_ungdung(d.get("ungdung"))}
                o_ud = ""
                for u in ds_ud:
                    ch = " checked" if u["id"] in da_chon_ud else ""
                    dich_ud = da_chon_ud.get(u["id"], "may")
                    lenh = (f'<code>{_esc(u["lenh_cai"])}</code>' if u["lenh_cai"]
                            else '<span style="color:#f59e0b;">chưa đặt lệnh cài - '
                                 'vào Ứng dụng để đặt trước khi dùng</span>')
                    o_ud += f"""
                    <label class="chon">
                      <input type="checkbox" name="ungdung" value="{_esc(u['id'])}"{ch}>
                      <span class="t">{_esc(u['ten_hien_thi'])}</span>
                      <div class="d">{u['so_file']} file &middot; {_esc(u['kich_thuoc'])}
                        &middot; lệnh: {lenh}</div>
                      <div class="d" style="margin-top:6px;">
                        Cài cho:
                        <select name="dich_ud_{_esc(u['id'])}"
                                style="width:auto;display:inline-block;padding:3px 6px;">
                          <option value="may"{' selected' if dich_ud == 'may' else ''}
                            >Máy (mọi người dùng)</option>
                          <option value="nguoi_dung"{' selected' if dich_ud == 'nguoi_dung' else ''}
                            >Chỉ người dùng đăng nhập đầu</option>
                        </select>
                      </div>
                    </label>"""
                khoi_ungdung = f"""
                <div class="card">
                  <h3>Ứng dụng nhiều file (Office 365, bộ cài phức tạp)</h3>
                  {o_ud}
                </div>"""
            else:
                khoi_ungdung = """
                <div class="msg info" style="font-size:13px;">
                  Chưa có ứng dụng kiểu thư mục nào. Vào tab
                  <a href="/deployos/ungdung">Ứng dụng (nhiều file)</a> nếu
                  cần cài Office 365 hoặc bộ cài nhiều file khác.
                </div>"""

            return f"""
            <form method="POST" {act}>
              {than}
              {khoi_ungdung}
              {_nut_dieu_huong(buoc)}
            </form>"""

        # -------------------------------------------- 1.1.6 chinh sua cai dat
        if buoc == 6:
            ds = _liet_ke(SCRIPTS_DIR, EXT_SCRIPT)
            if ds:
                o = ""
                for s in ds:
                    ch = " checked" if s["ten"] in d["scripts"] else ""
                    o += f"""
                    <label class="chon">
                      <input type="checkbox" name="script" value="{_esc(s['ten'])}"{ch}>
                      <span class="t">{_esc(s['ten'])}</span>
                      <div class="d">{co_kich_thuoc(s['cd'])} &middot; tai len {_esc(s['ngay'])}</div>
                    </label>"""
                khoi_script = f'<div class="card"><h3>Script chạy sau khi cài xong</h3>{o}</div>'
            else:
                khoi_script = """
                <div class="msg warn">Chưa có script nào. Tải lên ở tab
                <a href="/deployos/console/scripts">Script</a>
                (.bat / .ps1 / .cmd).</div>"""

            # --- Gia nhap domain + tuy chon Windows (chi cho Windows) ---
            khoi_domain = ""
            khoi_tuychon = ""
            if d.get("os_ho") == "windows":
                da_chon = set(d.get("tuy_chon") or [])
                o_may, o_nd = "", ""
                for ma_tc, nhan, mo_ta, pha, _lenh in _u_tuychon():
                    ch = " checked" if ma_tc in da_chon else ""
                    o = f"""
                    <label class="chon">
                      <input type="checkbox" name="tuy_chon" value="{_esc(ma_tc)}"{ch}>
                      <span class="t">{_esc(nhan)}</span>
                      <div class="d">{_esc(mo_ta)}</div>
                    </label>"""
                    if pha == "may":
                        o_may += o
                    else:
                        o_nd += o
                khoi_tuychon = f"""
              <div class="card">
                <h3>Tùy chọn Windows sau khi cài</h3>
                <p style="color:#8b93a1;font-size:13px;margin:0 0 9px;">
                  Các mục này Windows làm sẵn bằng lệnh hệ thống - không cần
                  viết script. Thứ gì đặc thù hơn thì dùng ô "Lệnh thêm" bên
                  dưới hoặc tải script riêng lên.</p>
                {o_may}
                <div style="color:#8b93a1;font-size:12.5px;margin:12px 0 6px;">
                  Áp dụng cho người dùng đăng nhập đầu tiên:</div>
                {o_nd}
              </div>
              {_khoi_go_app(d, _esc)}"""

                khoi_domain = f"""
              <div class="card">
                <h3>Gia nhập domain (tùy chọn)</h3>
                <p style="color:#8b93a1;font-size:13px;margin:0 0 9px;">
                  Để trống nếu không gia nhập domain. Tài khoản điền ở đây
                  phải có quyền THÊM MÁY vào domain (không nhất thiết phải
                  là Domain Admin). Windows tự làm việc này lúc cài - giống
                  hệt cách MDT làm.</p>
                <label>Tên domain</label>
                <input type="text" name="domain" value="{_esc(d.get('domain',''))}"
                       placeholder="vd: congty.local" autocapitalize="off">
                <label style="margin-top:10px;">OU chứa máy (tùy chọn)</label>
                <input type="text" name="domain_ou" value="{_esc(d.get('domain_ou',''))}"
                       placeholder="vd: OU=May tram,DC=congty,DC=local"
                       autocapitalize="off">
                <label style="margin-top:10px;">Tài khoản gia nhập</label>
                <input type="text" name="domain_user"
                       value="{_esc(d.get('domain_user',''))}"
                       placeholder="vd: svc-join" autocapitalize="off">
                <label style="margin-top:10px;">Mật khẩu tài khoản gia nhập</label>
                <input type="password" name="domain_pass" autocomplete="new-password"
                       placeholder="{'(đã có - để trống nếu không đổi)' if d.get('domain_pass') else ''}">
              </div>"""

            return f"""
            <form method="POST" {act}>
              {khoi_tuychon}
              {khoi_domain}
              {khoi_script}
              <div class="card">
                <h3>Lệnh thêm (tùy chọn)</h3>
                <p style="color:#8b93a1;font-size:13px;margin:0 0 9px;">
                  Mỗi dòng 1 lệnh, chạy khi người dùng đăng nhập lần đầu
                  (sau khi cài xong). Dòng bắt đầu bằng # được bỏ qua.</p>
                <textarea name="lenh_them" style="max-width:none;"
                  placeholder="vd: powercfg /h off">{_esc(d['lenh_them'])}</textarea>
              </div>
              {_nut_dieu_huong(buoc)}
            </form>"""

        # -------------------------------------------------- 1.1.7 tong ket
        if buoc == 7:
            return _ve_tongket(ma, d)

        return ""

    # ------------------------------------------------------- buoc 7: tong ket
    def _ve_tongket(ma, d):
        os_ten = _ten_os(d)
        kieu_ten = dict((k, t) for k, t, _ in KIEU_BOOT).get(d["kieu_boot"], d["kieu_boot"])

        if d["o_dia_che_do"] == "tu_dong":
            o_dia = f"Tu dong tren o dia so {_esc(d['o_dia_so'])} ({d['o_dia_bang'].upper()})"
        else:
            pv = d["phan_vung"] or _phan_vung_mac_dinh(d["os_ho"])
            dong = "".join(
                f"<div>&bull; {_esc(p['nhan'])} &mdash; "
                f"{'het cho con lai' if p['cd'] == 'con_lai' else _esc(p['cd']) + ' MB'} "
                f"&mdash; {_esc(p['fs'])} &mdash; {_esc(p['gan'])}</div>"
                for p in pv)
            o_dia = (f"Chia tay tren o dia so {_esc(d['o_dia_so'])} "
                     f"({d['o_dia_bang'].upper()})<div style='margin-top:6px;'>{dong}</div>")

        ds_app = chuan_hoa_apps(d.get("apps"))
        apps = ("<br>".join(
            "&bull; " + _esc(a["ten"]) +
            (" <span style='color:#8b93a1;'>(cài cho máy)</span>"
             if a["dich"] == "may"
             else " <span style='color:#8b93a1;'>(chỉ người dùng đầu)</span>")
            for a in ds_app)
            if ds_app else
            "<span style='color:#8b93a1;'>Không cài thêm phần mềm</span>")
        ds_ud = chuan_hoa_ungdung(d.get("ungdung"))
        ung_dung_html = ("<br>".join(
            "&bull; " + _esc(lay_ungdung(u["id"])["ten_hien_thi"]
                             if lay_ungdung(u["id"]) else u["id"]) +
            (" <span style='color:#8b93a1;'>(cài cho máy)</span>"
             if u["dich"] == "may"
             else " <span style='color:#8b93a1;'>(chỉ người dùng đầu)</span>")
            for u in ds_ud)
            if ds_ud else
            "<span style='color:#8b93a1;'>Không có</span>")
        scripts = ("<br>".join("&bull; " + _esc(s) for s in d["scripts"])
                   if d["scripts"] else "<span style='color:#8b93a1;'>Không có</span>")
        lenh = (f"<pre style='margin:6px 0 0;'>{_esc(d['lenh_them'])}</pre>"
                if d["lenh_them"] else "<span style='color:#8b93a1;'>Không có</span>")

        # LOI THAT DA GAP (anh Thoai: "xac nhan dung kich ban nay thi ngay
        # lap tuc no nhay sang phan tong ket lan nua la sao ta"): bam "Dung"
        # o 1 kich ban DA LUU se nap kich ban do vao trinh tu roi nhay thang
        # toi buoc 7 - nhung buoc 7 lai hien y HET nhu "Tong ket" cua trinh
        # tu tao moi (co ca form "Luu thanh kich ban" va nut "Sua lai tu
        # buoc 1"), nen nhin khong ra la dang CHAY 1 kich ban co san. Truong
        # d["tu_kichban"] da duoc dat san tu truoc nhung KHONG he duoc dung
        # o dau ca. Sua: khi den tu 1 kich ban da luu thi noi ro dang chay
        # kich ban nao, va bo form luu (luu lai se tao ban trung).
        tu_kb = d.get("tu_kichban") or ""
        tieu_de_bang = (f"Kịch bản: {_esc(tu_kb)}" if tu_kb
                        else "Tổng kết lựa chọn")
        ghi_chu_kb = (
            '<p style="color:#8b93a1;font-size:12.5px;margin:-4px 0 12px;">'
            'Đây là kịch bản đã lưu - sửa xong nhớ bấm <strong>"Lưu đè kịch '
            'bản"</strong> bên dưới. Muốn dựng ảnh đĩa và bật PXE thì bấm '
            '<em>Dùng</em> ở kịch bản này trên trang '
            '<a href="/deployos/kichban">danh sách kịch bản</a>.</p>'
            if tu_kb else "")

        bang = f"""
        <div class="card">
          <h3>{tieu_de_bang}</h3>
          {ghi_chu_kb}
          <table class="tt-bang">
            <tr><td>Kiểu boot</td><td>{_esc(kieu_ten)}</td></tr>
            <tr><td>Hệ điều hành</td><td>{_esc(os_ten)}</td></tr>
            <tr><td>Driver kèm theo</td><td>{
                (', '.join(_esc(x) for x in d.get('driver_ids') or [])
                 or "<span style='color:#8b93a1;'>Không có</span>")}</td></tr>
            <tr><td>Tên máy</td><td>{_esc(d['ten_may'])}</td></tr>
            <tr><td>Tài khoản</td><td>{_esc(d['username'])}</td></tr>
            <tr><td>Mật khẩu</td><td>{'&bull;' * 8 + ' <span style="color:#8b93a1;">(đã đặt)</span>' if d['password'] else '<span style="color:#f59e0b;">Chưa đặt</span>'}</td></tr>
            <tr><td>SSH</td><td>{'Bật' if d.get('ssh') else ('Tắt' if d['os_ho'] == 'linux' else '<span style="color:#8b93a1;">Không áp dụng cho Windows</span>')}</td></tr>
            <tr><td>Múi giờ</td><td>{_esc(d['mui_gio'])}</td></tr>
            {_dong_tongket_windows(d, _esc)}
            <tr><td>Gia nhập domain</td><td>{
                (_esc(d.get('domain')) +
                 (f" &mdash; OU: {_esc(d.get('domain_ou'))}" if d.get('domain_ou') else "") +
                 f" &mdash; tài khoản: {_esc(d.get('domain_user') or '(chưa điền)')}")
                if d.get('domain')
                else "<span style='color:#8b93a1;'>Không gia nhập</span>"}</td></tr>
            <tr><td>Tùy chọn Windows</td><td>{
                ("<br>".join("&bull; " + _esc(nhan)
                             for ma_tc, nhan, _m, _p, _l in _u_tuychon()
                             if ma_tc in (d.get('tuy_chon') or []))
                 or "<span style='color:#8b93a1;'>Không bật tùy chọn nào</span>")}</td></tr>
            <tr><td>Ổ đĩa</td><td>{o_dia}</td></tr>
            <tr><td>Phần mềm</td><td>{apps}</td></tr>
            <tr><td>Ứng dụng (nhiều file)</td><td>{ung_dung_html}</td></tr>
            <tr><td>Script sau cài</td><td>{scripts}</td></tr>
            <tr><td>Lệnh thêm</td><td>{lenh}</td></tr>
          </table>
        </div>"""

        ve_ds_kichban = ('<a class="btn gray" href="/deployos/kichban">'
                         '&larr; Về danh sách kịch bản</a>' if tu_kb else "")
        sua_lai = f"""
        <div class="row" style="margin-top:4px;">
          {ve_ds_kichban}
          <a class="btn gray" href="/deployos/wizard/{ma}/1">&larr; Sửa lại từ bước 1</a>
          <a class="btn gray" href="/deployos/wizard/{ma}/6">&larr; Quay lại bước 6</a>
        </div>"""

        # --- che do LUU: dat ten kich ban ---
        if d.get("che_do") == "luu":
            thieu = _thieu_gi(d)
            canh = (f'<div class="msg warn">Vẫn lưu được, nhưng còn thiếu: '
                    f'{_esc(", ".join(thieu))}.</div>' if thieu else "")
            return f"""
            {bang}
            {canh}
            <form method="POST" action="/deployos/kichban/luu/{ma}">
              <div class="card">
                <h3>Đặt tên kịch bản</h3>
                <label>Tên kịch bản</label>
                <input type="text" name="ten" required
                       placeholder="vd: Win11 van phong + Chrome" autocapitalize="off">
                <p style="color:#8b93a1;font-size:12.5px;margin:8px 0 0;">
                  Kịch bản sẽ hiện ở tab <strong>Kịch bản</strong> để chọn
                  nhanh lần sau.</p>
                <div class="row" style="margin-top:16px;">
                  <button type="submit" data-busy="Đang lưu...">Lưu kịch bản</button>
                </div>
              </div>
            </form>
            {sua_lai}"""

        # --- che do CHAY: kiem tra san sang that ---
        kt = kiem_tra_san_sang(d)
        hang = ""
        for dat, nhan, chi_tiet in kt:
            bieu = ('<span style="color:#4CAF50;">&#10004;</span>' if dat
                    else '<span style="color:#f59e0b;">&#33;</span>')
            hang += (f"<tr><td style='width:34px;'>{bieu}</td>"
                     f"<td><strong>{_esc(nhan)}</strong><br>"
                     f"<small style='color:#8b93a1;'>{_esc(chi_tiet)}</small></td></tr>")
        du_dieu_kien = all(dat for dat, _, _ in kt)

        ket_luan = ("""
            <div class="msg ok">Tất cả điều kiện cơ bản đã đạt.</div>"""
            if du_dieu_kien else """
            <div class="msg warn"><strong>Chưa thể boot thật.</strong> Những
            mục còn thiếu ở trên phải làm xong trước. Lựa chọn của anh không
            mất: lưu lại thành kịch bản để dùng ngay khi đã đủ điều kiện.</div>""")

        # LOI THAT DA GAP (anh Thoai: "em đem bật tắt pxe ra ngoài trang
        # deployment os đi, để trong kịch bản đâu có ý nghĩa"): nut bat/tat
        # PXE TUNG nam o day (trong tung kich ban) - nhung PXE la TRANG THAI
        # HA TANG DUNG CHUNG (chi co 1 cong eth0, 1 dich vu dnsmasq-pxe cho
        # CA HE THONG), khong phai thuoc tinh rieng cua 1 kich ban. Dat no o
        # day khien nguoi dung phai mo dung 1 kich ban roi vao toi buoc 7
        # moi bat/tat duoc, dung sai cho. Da chuyen han sang trang danh sach
        # kich ban (xem _khoi_pxe_toan_cuc(), goi tu deployos_boot()) - loi
        # nhac da gop chung vao ghi_chu_kb o dau ham nay, khong lap lai o day.

        # Dang chay 1 kich ban DA LUU thi khong hien form luu nua - luu lai
        # chi tao ra 1 ban trung ten khac, gay roi danh sach kich ban.
        # LOI THAT DA GAP (anh Thoai: "sua kich ban them phan mem va them
        # option thi bam save lai lan dau thi co nhung qua trang khac quay
        # lai thi ko co"): o vong sua truoc, khi mo 1 kich ban DA LUU thi
        # form luu bi AN HAN di (voi ly do "luu lai se tao ban trung ten").
        # Hau qua nghiem trong hon nhieu: KHONG CON CACH NAO luu thay doi
        # vao chinh kich ban do - anh sua xong, lua chon chi nam trong bo
        # nho cua trinh tu, roi trang la mat sach (kiem chung that: file
        # Install_windows_10_-_DHCP.json van giu nguyen "apps": [] va moc
        # thoi gian cu, trong khi phan mem da duoc tai len tu lau).
        # Sua dung: van cho luu DE LEN chinh kich ban dang mo (nut chinh),
        # va van cho luu ra ten MOI (nut phu) - khong bo mat duong nao.
        if tu_kb:
            form_luu = f"""
        <div class="card">
          <h3>Lưu thay đổi</h3>
          <form method="POST" action="/deployos/kichban/luu/{ma}">
            <input type="hidden" name="ten" value="{_esc(tu_kb)}">
            <button type="submit" data-busy="Dang luu...">
              Lưu đè kịch bản "{_esc(tu_kb)}"</button>
          </form>
          <div style="border-top:1px solid #2a2f3a;margin:16px 0 12px;"></div>
          <form method="POST" action="/deployos/kichban/luu/{ma}">
            <label>Hoặc lưu thành kịch bản mới (đặt tên khác)</label>
            <input type="text" name="ten" required
                   placeholder="vd: Win10 van phong + Chrome" autocapitalize="off">
            <div class="row" style="margin-top:12px;">
              <button type="submit" class="gray" data-busy="Đang lưu...">
                Lưu thành kịch bản mới</button>
            </div>
          </form>
        </div>"""
        else:
            form_luu = f"""
        <form method="POST" action="/deployos/kichban/luu/{ma}">
          <div class="card">
            <h3>Lưu lựa chọn này thành kịch bản</h3>
            <label>Tên kịch bản</label>
            <input type="text" name="ten" required
                   placeholder="vd: Win11 van phong + Chrome" autocapitalize="off">
            <div class="row" style="margin-top:14px;">
              <button type="submit" data-busy="Đang lưu...">Lưu thành kịch bản</button>
            </div>
          </div>
        </form>"""

        return f"""
        {_khoi_dang_phuc_vu()}
        {bang}
        <div class="card">
          <h3>Kiểm tra sẵn sàng (đọc trạng thái thật trên máy)</h3>
          <table>{hang}</table>
        </div>
        {ket_luan}
        {form_luu}
        {sua_lai}"""

    # ======================================= TAB "CAI DAT" cua Deployment OS
    #
    # LOI THAT DA GAP (anh Thoai: "nut pxe anh ma bam tat tu nhien dau mat
    # tieu luon khong hien lai sao anh bat len duoc"): khoi dieu khien cu
    # CHI co nut "Tat PXE" khi dang bat, con khi da tat thi KHONG co nut
    # "Bat PXE" nao ca - chi hien 1 dong chu bao vao kich ban bam "Dung".
    # Tuc la bam tat 1 cai la ket, khong co duong quay lai tu chinh trang
    # do. Sua: LUON co nut cua trang thai nguoc lai, o ngay day.
    #
    # Bat PXE o day phuc vu ANH DIA DANG CO SAN (lan dung gan nhat), khong
    # dung lai anh moi - dung cho truong hop "lo bam tat, bat lai de chay
    # tiep". Muon doi sang kich ban KHAC thi van phai bam "Dung" o kich ban
    # do (vi phai dung lai anh dia theo cau hinh cua no).
    def _trang_caidat_pxe(msg="", ok=True):
        from . import pxe as _pxe
        from . import unattend as _u
        dang_bat = _pxe.dang_bat()
        dau_kb = _u.doc_dau_kichban()

        if dang_bat:
            try:
                kieu_dang_chay = open(_pxe.STATE_FLAG).read().strip() or "truc_tiep"
            except OSError:
                kieu_dang_chay = "truc_tiep"
            dia_chi_that = _pxe._dia_chi_pi_that(kieu_dang_chay)
            trang_thai = f"""
            <div class="msg ok">PXE đang <strong>BẬT</strong> trên cổng
              {_pxe.IFACE} &mdash; Pi là {_esc(dia_chi_that)}.</div>"""
            nut = """
            <form method="POST" action="/deployos/pxe/tat">
              <input type="hidden" name="ve" value="/deployos/caidat">
              <button type="submit" class="red" data-busy="Đang tắt...">
                Tắt PXE</button>
            </form>"""
        else:
            trang_thai = f"""
            <div class="msg warn">PXE đang <strong>TẮT</strong>. Bật lên sẽ
              CẮT DHCP trên cổng {_pxe.IFACE} (giống hệt cảnh báo của
              &quot;Cắm thẳng thiết bị&quot;) &mdash; chỉ bật khi đã cắm dây
              mạng từ Pi sang đúng máy cần cài.</div>"""
            if _pxe.san_sang_bat():
                kieu = (dau_kb or {}).get("kieu_boot", "truc_tiep")
                nut = f"""
                <form method="POST" action="/deployos/pxe/bat">
                  <input type="hidden" name="ve" value="/deployos/caidat">
                  <input type="hidden" name="kieu_boot" value="{_esc(kieu)}">
                  <button type="submit" data-busy="Đang bật...">
                    Bật PXE lại (dùng ảnh đĩa đang có)</button>
                </form>"""
            else:
                nut = ('<div class="msg err">Chưa đủ điều kiện để bật &mdash; '
                       'xem tab <a href="/deployos/caidat/hatang">Kiểm tra '
                       'hạ tầng</a>.</div>')

        if dau_kb:
            dang_phuc_vu = f"""
            <table style="margin-top:6px;">
              <tr><td>Kịch bản của ảnh đĩa</td>
                  <td><strong>{_esc(dau_kb.get('ten_kichban') or '?')}</strong></td></tr>
              <tr><td>Tên máy sẽ đặt</td><td>{_esc(dau_kb.get('ten_may') or '?')}</td></tr>
              <tr><td>Tài khoản</td><td>{_esc(dau_kb.get('username') or '?')}</td></tr>
              <tr><td>Dựng lúc</td><td>{_esc(dau_kb.get('dung_luc') or '?')}</td></tr>
            </table>"""
        else:
            dang_phuc_vu = ('<p style="color:#8b93a1;font-size:13px;">Chưa dựng '
                            'ảnh đĩa lần nào &mdash; bấm <em>Dùng</em> ở một '
                            'kịch bản để dựng.</p>')

        body = _tabs("caidat", "pxe") + _msg(msg, ok) + f"""
        <div class="card">
          <h3>Bật / Tắt PXE</h3>
          {trang_thai}
          {nut}
        </div>
        <div class="card">
          <h3>Ảnh đĩa đang phục vụ</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 4px;">
            Bật PXE ở trang này phục vụ đúng ảnh đĩa dưới đây. Muốn chạy kịch
            bản khác thì bấm <em>Dùng</em> ở kịch bản đó (phải dựng lại ảnh).</p>
          {dang_phuc_vu}
        </div>"""
        return _trang(body, "Cài đặt Deployment OS",
                      "Bật/tắt PXE và kiểm tra hạ tầng", active="/deployos")

    def _trang_caidat_hatang(msg="", ok=True):
        """Bang kiem tra ha tang PXE (bootloader/wimboot/bootmgr/BCD) - tach
        khoi trang danh sach kich ban vi day la thu chi xem khi co su co,
        khong phai thu nhin moi ngay."""
        from . import pxe as _pxe
        hang = ""
        for dat, nhan, chi_tiet in _pxe.trang_thai_chuan_bi():
            bieu = ('<span style="color:#4CAF50;">&#10004;</span>' if dat
                    else '<span style="color:#f59e0b;">&#33;</span>')
            hang += (f"<tr><td style='width:34px;'>{bieu}</td>"
                     f"<td><strong>{_esc(nhan)}</strong><br>"
                     f"<small style='color:#8b93a1;'>{_esc(chi_tiet)}</small></td></tr>")

        trich_can = (not _pxe._co_bootmgr_pxe()
                     and os.path.isfile(_pxe._duong("boot.wim")))
        nut_trich = """
        <form method="POST" action="/deployos/pxe/trich-bootmgr" style="margin-top:10px;">
          <input type="hidden" name="ve" value="/deployos/caidat/hatang">
          <button type="submit" class="gray" data-busy="Đang trích...">
            Trích bootmgr từ boot.wim</button>
        </form>""" if trich_can else ""

        body = _tabs("caidat", "hatang") + _msg(msg, ok) + f"""
        <div class="card">
          <h3>Sẵn sàng PXE (giai đoạn phục vụ boot thật sự)</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 10px;">
            Các thành phần hạ tầng cần có để máy khác boot được qua mạng.
            Dấu <span style="color:#f59e0b;">!</span> nghĩa là còn thiếu.</p>
          <table>{hang}</table>
          {nut_trich}
        </div>"""
        return _trang(body, "Kiểm tra hạ tầng PXE",
                      "Bootloader, wimboot, bootmgr, BCD", active="/deployos")

    @app.route("/deployos/caidat")
    def deployos_caidat():
        return _trang_caidat_pxe()

    @app.route("/deployos/caidat/hatang")
    def deployos_caidat_hatang():
        return _trang_caidat_hatang()

    def _thieu_gi(d):
        thieu = []
        if not d["os_ho"]:
            thieu.append("chưa chọn OS")
        if not d["ten_may"]:
            thieu.append("chưa có tên máy")
        if not d["username"]:
            thieu.append("chưa có tên đăng nhập")
        if not d["password"]:
            thieu.append("chưa đặt mật khẩu")
        if not d.get("os_id"):
            thieu.append("chưa chọn hệ điều hành")
        return thieu

    @app.route("/deployos/kichban/luu/<ma>", methods=["POST"])
    def deployos_luu_kichban(ma):
        d = _wizard_lay(ma)
        if d is None:
            return _het_han()
        cauhinh = {k: v for k, v in d.items() if not k.startswith("_")}
        cauhinh.pop("che_do", None)
        # "tu_kichban" chi la dau vet cho biet trinh tu nay duoc nap tu
        # kich ban nao - KHONG phai noi dung cua kich ban. Neu luu ca no
        # vao file thi kich ban moi se mang ten kich ban khac trong ruot,
        # rat de gay hieu nham khi doc lai file sau nay.
        cauhinh.pop("tu_kichban", None)
        ok, msg = luu_kichban(cauhinh, request.form.get("ten", ""))
        ds = danh_sach_kichban()
        body = (_tabs("kichban") + _msg(msg, ok) +
                _bang_kichban(ds, _esc) +
                '<div class="row" style="margin-top:8px;">'
                '<a class="btn" href="/deployos/kichban">Ve danh sach kich ban</a></div>')
        return _trang(body, "Deployment OS", "Kich ban")

    # ================================================ 2. TAB "CONSOLE BOOT"
    def _khoi_tai_len(hanh_dong, nhan, duoi, ghi_chu="", loai=""):
        """
        Khung tai len co THANH TIEN TRINH that.

        LOI THAT DA GAP (anh Thoai bao: "task manager het bao dung luong ben
        tab network ma trang os van quay hoai luon, ko biet no toi dau"):
        truoc day day chi la 1 form thuong - bam xong la trang dung yen quay
        vong tron hang chuc phut, khong biet dang o dau, con bao lau, hay da
        treo. Voi file 5GB tren the nho cham thi cho nhu vay la khong the
        chap nhan duoc.

        Gio dung XMLHttpRequest de biet SO BYTE DA GUI, dong thoi hoi may
        (/deployos/tien-do) xem DA GHI DUOC bao nhieu xuong dia that - hien
        ca hai, kem toc do va thoi gian con lai. Neu trinh duyet khong chay
        duoc JavaScript thi form van gui duoc nhu cu (chi la khong co thanh
        tien trinh), khong bao gio mat duong tai len.
        """
        return f"""
        <div class="card">
          <h3>Tai len {_esc(nhan)}</h3>
          {ghi_chu}
          <form method="POST" action="{hanh_dong}" enctype="multipart/form-data"
                class="form-tai-len" data-loai="{_esc(loai)}">
            <label>Chon file ({', '.join(sorted(duoi))})</label>
            <input type="file" name="file" required>
            <div class="row" style="margin-top:13px;">
              <button type="submit" data-busy="Dang tai len, dung dong trang...">
                Tai len</button>
              <span style="color:#8b93a1;font-size:13px;">
                File lớn mất vài phút. Sẽ có thanh tiến trình báo rõ đang tới đâu.</span>
            </div>
          </form>

          <div class="tt-khung" style="display:none;">
            <div class="tt-ten"></div>
            <div class="tt-thanh-ngoai"><div class="tt-thanh"></div></div>
            <div class="tt-so">
              <span class="tt-phantram">0%</span>
              <span class="tt-chitiet"></span>
            </div>
            <div class="tt-dia"></div>
            <div style="margin-top:12px;">
              <button type="button" class="red small tt-huy">Huy tai len</button>
            </div>
          </div>
        </div>"""

    def _bang_file(ds, duong_xoa, duong_tai):
        if not ds:
            return '<p style="color:#8b93a1;">Chua co file nao.</p>'
        hang = ""
        for f in ds:
            hang += f"""
            <tr>
              <td><strong>{_esc(f['ten'])}</strong></td>
              <td>{co_kich_thuoc(f['cd'])}</td>
              <td style="color:#8b93a1;">{_esc(f['ngay'])}</td>
              <td>
                <a class="btn small gray" href="{duong_tai}/{_esc(f['ten'])}">Tải về</a>
                <form method="POST" action="{duong_xoa}" style="display:inline;"
                      onsubmit="return confirm('Xoa {_esc(f['ten'])}?');">
                  <input type="hidden" name="ten" value="{_esc(f['ten'])}">
                  <button type="submit" class="red small">Xóa</button>
                </form>
              </td>
            </tr>"""
        return f"""
        <div class="tbl-scroll"><table>
          <tr><th>Ten file</th><th style="width:110px;">Kich thuoc</th>
              <th style="width:140px;">Ngay tai len</th><th style="width:180px;">Thao tác</th></tr>
          {hang}
        </table></div>"""

    # ------------------------- he dieu hanh (mo hinh MDT: "Operating Systems")
    @app.route("/deployos/os")
    def deployos_os():
        return _trang_os()

    def _trang_os(msg="", ok=True):
        ds = danh_sach_os()
        hang = ""
        for o in ds:
            trang_thai = ('<span style="color:#4CAF50;">Sẵn sàng</span>' if o["san_sang"]
                          else '<span style="color:#e0a030;">Thiếu file</span>')
            hang += f"""
            <tr>
              <td><strong>{_esc(o['ten_hien_thi'])}</strong>
                  <div style="color:#8b93a1;font-size:12px;">{_esc(o['id'])}</div></td>
              <td>{_esc(o['os_ho'])}</td>
              <td>{trang_thai}</td>
              <td>{_esc(o['kich_thuoc'])}</td>
              <td>
                <a class="btn small" href="/deployos/os/{_esc(o['id'])}">Quản lý file</a>
                <form method="POST" action="/deployos/os/xoa" style="display:inline;"
                      onsubmit="return confirm('Xóa toàn bộ hệ điều hành này?');">
                  <input type="hidden" name="os_id" value="{_esc(o['id'])}">
                  <button type="submit" class="red small">Xóa</button>
                </form>
              </td>
            </tr>"""
        bang = (f"""<div class="tbl-scroll"><table>
              <tr><th>Tên</th><th>Họ</th><th>Trạng thái</th><th>Dung lượng</th>
                  <th style="width:190px;">Thao tác</th></tr>
              {hang}
            </table></div>""" if ds else
            '<p style="color:#8b93a1;">Chưa có hệ điều hành nào.</p>')
        body = (_tabs("tainguyen", "os") + _msg(msg, ok) + f"""
        <div class="card">
          <h3>Thêm hệ điều hành mới</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
            Đặt tên (vd "Windows 10 Pro", "Windows 11 Pro") - sau khi tạo,
            vào "Quản lý file" để tải lên <code>boot.wim</code> và
            <code>install.wim</code> (lấy từ <code>sources\\</code> của
            ISO Windows thật, Pi KHÔNG tự tạo được).</p>
          <form method="POST" action="/deployos/os/tao">
            <input type="text" name="ten_hien_thi" placeholder="Tên hệ điều hành" required>
            <select name="os_ho">
              <option value="windows">Windows</option>
              <option value="linux">Linux</option>
            </select>
            <button type="submit">Tạo</button>
          </form>
        </div>
        <h2>Hệ điều hành đã có ({len(ds)})</h2>
        {bang}""")
        return _trang(body, "Deployment OS", "Hệ điều hành")

    @app.route("/deployos/os/tao", methods=["POST"])
    def deployos_os_tao():
        ok, msg, os_id = tao_os_moi(request.form.get("ten_hien_thi", ""),
                                    request.form.get("os_ho", "windows"))
        if ok:
            return redirect(f"/deployos/os/{os_id}")
        return _trang_os(msg, ok)

    @app.route("/deployos/os/xoa", methods=["POST"])
    def deployos_os_xoa():
        ok, msg = xoa_os(request.form.get("os_id", ""))
        return _trang_os(msg, ok)

    @app.route("/deployos/os/<os_id>")
    def deployos_os_chitiet(os_id):
        o = lay_os(os_id)
        if o is None:
            return _trang_os("Không tìm thấy hệ điều hành.", False)
        hang = ""
        for ten_file, nhan in (("boot.wim", "boot.wim (WinPE)"),
                              ("install.wim", "install.wim (ảnh cài đặt)")):
            fp = os.path.join(OS_DIR, ten_an_toan(os_id), ten_file)
            co = os.path.isfile(fp)
            kich_thuoc = co_kich_thuoc(os.path.getsize(fp)) if co else "-"
            trang_thai = ('<span style="color:#4CAF50;">Đã có</span>' if co
                          else '<span style="color:#e0a030;">Chưa có</span>')
            hang += f"""
            <tr><td>{nhan}</td><td>{trang_thai}</td><td>{kich_thuoc}</td></tr>"""
        body = (_tabs("tainguyen", "os") + f"""
        <p><a href="/deployos/os">&larr; Về danh sách hệ điều hành</a></p>
        <h2>{_esc(o['ten_hien_thi'])}</h2>
        <div class="tbl-scroll"><table>
          <tr><th>File</th><th>Trạng thái</th><th>Dung lượng</th></tr>
          {hang}
        </table></div>
        <div class="card" style="margin-top:14px;">
          <h3>Tải lên file (dùng TÊN GỐC từ ISO Windows - boot.wim / install.wim)</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
            Lấy 2 file này từ thư mục <code>sources\\</code> của ISO Windows
            thật (mount ISO trên 1 máy Windows rồi copy ra). Tải lên từng
            file một - install.wim thường vài GB, sẽ mất vài phút.</p>
          <form method="POST" action="/deployos/os/{_esc(os_id)}/len"
                enctype="multipart/form-data" data-busy="Đang tải lên...">
            <input type="file" name="file" required>
            <button type="submit">Tải lên</button>
          </form>
        </div>""")
        return _trang(body, "Deployment OS", f"Hệ điều hành - {o['ten_hien_thi']}")

    @app.route("/deployos/os/<os_id>/len", methods=["POST"])
    def deployos_os_len(os_id):
        f = request.files.get("file")
        if not f or not getattr(f, "filename", ""):
            return redirect(f"/deployos/os/{os_id}")
        duong = getattr(getattr(f, "stream", None), "_cp_duong_dan", None)
        ten_goc = ten_an_toan(f.filename)
        if ten_goc not in ("boot.wim", "install.wim"):
            return _trang_os(
                f'Chỉ nhận đúng tên "boot.wim" hoặc "install.wim" '
                f'(file anh tải lên tên là "{ten_goc}") - đổi tên lại cho '
                f'đúng như trên ISO Windows gốc.', False)
        if duong:
            try:
                f.stream.flush()
                os.fsync(f.stream.fileno())
            except Exception:
                pass
            thu_muc = os.path.join(OS_DIR, ten_an_toan(os_id))
            ok, msg, _duong_dich = _hoan_tat_ghi_thang(duong, thu_muc, ten_goc)
        else:
            ok, msg = False, "Không ghi thẳng được file - thử lại."
        if ok:
            return redirect(f"/deployos/os/{os_id}")
        return _trang_os(msg, ok)

    # ----------------------------- driver (mo hinh MDT: "Out-of-Box Drivers")
    @app.route("/deployos/drivers")
    def deployos_drivers():
        return _trang_drivers()

    def _trang_drivers(msg="", ok=True):
        ds = danh_sach_driver()
        hang = ""
        for dr in ds:
            hang += f"""
            <tr>
              <td><strong>{_esc(dr['ten_hien_thi'])}</strong></td>
              <td>{dr['so_file']} file</td>
              <td>{
                '<span style="color:#4CAF50;">Có - nạp vào WinPE</span>'
                if dr['cho_boot'] else
                '<span style="color:#8b93a1;">Không</span>'}
                <form method="POST" action="/deployos/drivers/cho-boot"
                      style="display:inline;margin-left:6px;">
                  <input type="hidden" name="driver_id" value="{_esc(dr['id'])}">
                  <input type="hidden" name="bat" value="{'0' if dr['cho_boot'] else '1'}">
                  <button type="submit" class="small gray">{
                    'Bỏ' if dr['cho_boot'] else 'Đánh dấu'}</button>
                </form>
              </td>
              <td>
                <a class="btn small" href="/deployos/drivers/{_esc(dr['id'])}">Quản lý file</a>
                <form method="POST" action="/deployos/drivers/xoa" style="display:inline;"
                      onsubmit="return confirm('Xóa gói driver này?');">
                  <input type="hidden" name="driver_id" value="{_esc(dr['id'])}">
                  <button type="submit" class="red small">Xóa</button>
                </form>
              </td>
            </tr>"""
        bang = (f"""<div class="tbl-scroll"><table>
              <tr><th>Tên gói</th><th style="width:80px;">Số file</th>
                  <th style="width:210px;">Nạp vào ảnh boot</th>
                  <th style="width:190px;">Thao tác</th></tr>
              {hang}
            </table></div>""" if ds else
            '<p style="color:#8b93a1;">Chưa có gói driver nào.</p>')
        body = (_tabs("tainguyen", "drivers") + _msg(msg, ok) + f"""
        <div class="card">
          <h3>Hai loại driver - khác nhau ở thời điểm nạp</h3>
          <table class="tt-bang">
            <tr><td style="width:180px;">Driver thường</td>
                <td>Tiêm cho <strong>Windows sau khi đã cài xong</strong>.
                Lúc đó máy đã có mạng rồi. Dùng cho card màn hình, âm thanh,
                vân tay, chipset...</td></tr>
            <tr><td>Nạp vào ảnh boot</td>
                <td>Nạp vào <strong>WinPE ngay lúc mới boot</strong>, trước
                khi máy xin IP. <strong>Chỉ cần cho card mạng (LAN).</strong>
                Nếu WinPE không có driver LAN của máy đó thì máy không có
                mạng, không tải được ảnh cài đặt và sẽ đứng ngay từ đầu.</td></tr>
          </table>
        </div>

        <div class="msg warn" style="font-size:13px;">
          <strong>Ảnh WinPE hiện tại thiếu driver LAN của máy đời mới.</strong>
          Đã kiểm chứng bằng cách đọc mã phần cứng thật trong chính
          <code>boot.wim</code> đang dùng:
          <br><br>
          <strong>Đã có sẵn</strong> - không cần làm gì: Intel I219 đời
          2016-2019, Realtek RTL8111/8168 và RTL8125, Broadcom NetXtreme,
          và card USB-LAN (ASIX AX88179, Realtek RTL8153).
          <br><br>
          <strong>Thiếu</strong> - phải tải driver rồi đánh dấu "nạp vào ảnh
          boot": <strong>Intel I219 từ đời 2020 trở đi</strong> (Comet Lake,
          Tiger Lake, Alder Lake, Raptor Lake, Meteor Lake) và
          <strong>toàn bộ Intel I225/I226 2.5G</strong>. Đây là card LAN của
          hầu hết máy HP / Dell / Lenovo đời 2020 trở lại đây - đúng nguyên
          nhân làm máy boot vào nhưng không nhận mạng.
          <br><br>
          <strong>Lấy driver ở đâu:</strong> Dell và HP có sẵn gói riêng cho
          WinPE (Dell "WinPE Driver Pack", HP "WinPE Driver Pack") - tải về,
          giải nén, lấy thư mục network. Lenovo có driver pack theo từng dòng
          máy. Asus thì tải driver LAN theo model trên trang hỗ trợ. Chỉ cần
          phần <strong>LAN/Ethernet</strong>, không cần cả gói.
          <br><br>
          <strong>Mẹo đỡ phải làm:</strong> dùng một cái USB-LAN loại
          ASIX AX88179 hoặc Realtek RTL8153 - hai loại này WinPE đã có sẵn
          driver, cắm vào là chạy được trên mọi máy, kể cả laptop không có
          cổng mạng.
        </div>

        <div class="msg info" style="font-size:13px;">
          Driver thường được TIÊM vào lúc cài (không sửa boot.wim/install.wim) qua
          <code>DriverPaths</code> của unattend.xml - Windows Setup tự quét
          và cài driver phù hợp trong lúc chạy, giống đúng cơ chế
          "Out-of-Box Drivers" của MDT.</div>
        <div class="card">
          <h3>Thêm gói driver mới</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
            Đặt tên để nhận biết (vd "Dell Latitude 5420 - LAN+WiFi"). Sau
            khi tạo, vào "Quản lý file" để tải lên các file .inf/.sys/.cat
            của driver.</p>
          <form method="POST" action="/deployos/drivers/tao">
            <input type="text" name="ten_hien_thi" placeholder="Tên gói driver" required>
            <button type="submit">Tạo</button>
          </form>
        </div>
        <h2>Gói driver đã có ({len(ds)})</h2>
        {bang}""")
        return _trang(body, "Deployment OS", "Driver")

    @app.route("/deployos/drivers/tao", methods=["POST"])
    def deployos_drivers_tao():
        ok, msg, driver_id = tao_driver_moi(request.form.get("ten_hien_thi", ""))
        if ok:
            return redirect(f"/deployos/drivers/{driver_id}")
        return _trang_drivers(msg, ok)

    @app.route("/deployos/drivers/xoa", methods=["POST"])
    def deployos_drivers_xoa():
        ok, msg = xoa_driver(request.form.get("driver_id", ""))
        return _trang_drivers(msg, ok)

    @app.route("/deployos/drivers/cho-boot", methods=["POST"])
    def deployos_drivers_cho_boot():
        ok, msg = dat_driver_cho_boot(request.form.get("driver_id", ""),
                                      request.form.get("bat") == "1")
        return _trang_drivers(msg, ok)

    # ============================================ TAB "THAM SO CAI DAT"
    # Bang tra tham so cai im lang cua tung phan mem (/S, /qn,
    # /VERYSILENT...). Xem ly do va mo ta du lieu trong ui/thamso.py.
    @app.route("/deployos/thamso")
    def deployos_thamso():
        return _trang_thamso(sua_ma=request.args.get("sua", ""))

    def _trang_thamso(msg="", ok=True, sua_ma=""):
        from . import thamso as _ts
        ds = _ts.danh_sach()

        # Du lieu cho JS tim kiem: kem san ban DA BO DAU de khoi phai bo
        # dau lai moi lan go phim (bang co the len hang tram dong).
        du_lieu_js = json.dumps([
            {"id": x.get("id", ""),
             "tim": "  ".join(_ts.bo_dau(x.get(k, ""))
                                    for k, _n in _ts.CAC_COT)}
            for x in ds], ensure_ascii=False)

        hang = ""
        for x in ds:
            ma = _esc(x.get("id", ""))
            if x.get("id") == sua_ma:
                # Dong dang sua: bien thanh form ngay tai cho
                o = ""
                for khoa, nhan in _ts.CAC_COT:
                    o += (f'<td data-cot="{_esc(nhan)}">'
                          f'<textarea name="{khoa}" rows="2" class="o-sua"'
                          f' placeholder="{_esc(nhan)}">'
                          f'{_esc(x.get(khoa, ""))}</textarea></td>')
                hang += f"""
                <tr class="dang-sua">
                  <form method="POST" action="/deployos/thamso/sua">
                    <input type="hidden" name="id" value="{ma}">
                    {o}
                    <td class="cot-nut">
                      <button type="submit" class="nho">Lưu</button>
                      <a href="/deployos/thamso" class="nut-huy">Huỷ</a>
                    </td>
                  </form>
                </tr>"""
                continue
            o = ""
            for khoa, nhan in _ts.CAC_COT:
                gt = x.get(khoa, "")
                # Cot tham so: cho bam de chep nhanh - day la thu nguoi
                # dung thuc su can lam sau khi tra duoc (dan vao o tham so
                # cua phan mem), go tay lai rat de sai 1 ky tu.
                if khoa in ("cai_dat", "go_cai") and gt:
                    o += (f'<td data-cot="{_esc(nhan)}">'
                          f'<code class="chep" title="Bấm để chép">'
                          f'{_esc(gt)}</code></td>')
                else:
                    o += f'<td data-cot="{_esc(nhan)}">{_esc(gt)}</td>'
            hang += f"""
            <tr data-id="{ma}">
              {o}
              <td class="cot-nut">
                <a href="/deployos/thamso?sua={ma}" class="nut-sua">Sửa</a>
                <form method="POST" action="/deployos/thamso/xoa"
                      onsubmit="return confirm('Xoá dòng này?');">
                  <input type="hidden" name="id" value="{ma}">
                  <button type="submit" class="nho do">Xoá</button>
                </form>
              </td>
            </tr>"""

        tieu_de = "".join(f"<th>{_esc(n)}</th>" for _k, n in _ts.CAC_COT)
        o_them = "".join(
            f'<textarea name="{k}" rows="2" placeholder="{_esc(n)}"></textarea>'
            for k, n in _ts.CAC_COT)

        body = _tabs("thamso") + _msg(msg, ok) + f"""
        <div class="card">
          <h3>Tra tham số cài đặt im lặng</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 12px;">
            Mỗi bộ cài có một kiểu tham số cài im lặng riêng - không đoán được,
            chỉ tra. Bấm vào ô tham số để chép, rồi dán vào mục
            <a href="/deployos/console/apps">Phần mềm</a>.</p>

          <div class="hang-tim">
            <input type="search" id="o-tim" autocomplete="off"
                   placeholder="Tìm: tên phần mềm, tham số, ghi chú... (gõ không dấu cũng được)">
            <button type="button" id="nut-xoa-tim" class="gray">Xoá</button>
          </div>
          <div id="ket-qua-tim" class="ket-qua"></div>

          <div class="bang-cuon">
            <table class="bang-ts" id="bang">
              <thead><tr>{tieu_de}<th class="cot-nut">&nbsp;</th></tr></thead>
              <tbody>{hang}</tbody>
            </table>
          </div>
          <div id="khong-thay" class="khong-thay" hidden></div>
        </div>

        <div class="card">
          <h3>Thêm dòng mới</h3>
          <form method="POST" action="/deployos/thamso/them">
            <div class="luoi-them">{o_them}</div>
            <button type="submit" style="margin-top:12px;">Thêm vào bảng</button>
          </form>
        </div>

        <script>
        (function() {{
          var DU_LIEU = {du_lieu_js};
          var oTim = document.getElementById('o-tim');
          var bang = document.getElementById('bang');
          var kq = document.getElementById('ket-qua-tim');
          var khongThay = document.getElementById('khong-thay');
          var tong = DU_LIEU.length;

          // Bo dau tieng Viet - phai khop y het ham bo_dau() ben Python,
          // ke ca viec thay 'd' truoc (NFD khong tach duoc chu 'd').
          function boDau(s) {{
            return (s || '').replace(/đ/g, 'd').replace(/Đ/g, 'D')
              .normalize('NFD').replace(/[\\u0300-\\u036f]/g, '')
              .toLowerCase().trim();
          }}

          // Khoang cach sua doi (Levenshtein) co GIOI HAN: chi dung de
          // goi y khi khong tim thay gi, nen khong can chinh xac tuyet doi
          // va phai dung som de khong lam cham may.
          function gan(a, b, toiDa) {{
            if (Math.abs(a.length - b.length) > toiDa) return toiDa + 1;
            var truoc = [], nay = [], i, j;
            for (j = 0; j <= b.length; j++) truoc[j] = j;
            for (i = 1; i <= a.length; i++) {{
              nay[0] = i; var nhoNhat = i;
              for (j = 1; j <= b.length; j++) {{
                nay[j] = Math.min(truoc[j] + 1, nay[j-1] + 1,
                         truoc[j-1] + (a[i-1] === b[j-1] ? 0 : 1));
                if (nay[j] < nhoNhat) nhoNhat = nay[j];
              }}
              if (nhoNhat > toiDa) return toiDa + 1;
              truoc = nay.slice();
            }}
            return truoc[b.length];
          }}

          // 1 tu khoa khop neu: nam trong chuoi, HOAC gan giong mot tu nao
          // do trong chuoi (go sai 1-2 ky tu van ra).
          function tuKhop(tu, chuoi) {{
            if (chuoi.indexOf(tu) !== -1) return true;
            if (tu.length < 4) return false;   // tu qua ngan thi de khop bua
            var toiDa = tu.length >= 7 ? 2 : 1;
            var cacTu = chuoi.split(/[^a-z0-9]+/);
            for (var i = 0; i < cacTu.length; i++) {{
              if (cacTu[i].length >= 3 && gan(tu, cacTu[i], toiDa) <= toiDa)
                return true;
            }}
            return false;
          }}

          function loc() {{
            var q = boDau(oTim.value);
            var hang = bang.tBodies[0].rows;
            if (!q) {{
              for (var i = 0; i < hang.length; i++) hang[i].hidden = false;
              kq.textContent = tong + ' dòng';
              khongThay.hidden = true;
              return;
            }}
            var tuKhoa = q.split(/\\s+/).filter(Boolean);
            var hienId = {{}}, soHien = 0, gapGanDung = false;
            for (var k = 0; k < DU_LIEU.length; k++) {{
              var m = DU_LIEU[k], hop = true, canGan = false;
              for (var t = 0; t < tuKhoa.length; t++) {{
                if (m.tim.indexOf(tuKhoa[t]) !== -1) continue;
                if (tuKhop(tuKhoa[t], m.tim)) {{ canGan = true; continue; }}
                hop = false; break;
              }}
              if (hop) {{ hienId[m.id] = true; soHien++; if (canGan) gapGanDung = true; }}
            }}
            for (var i = 0; i < hang.length; i++) {{
              var id = hang[i].getAttribute('data-id');
              hang[i].hidden = !(id && hienId[id]);
            }}
            kq.textContent = soHien + ' / ' + tong + ' dòng khớp'
                           + (gapGanDung ? '  (có kết quả gần đúng)' : '');
            khongThay.hidden = soHien > 0;
            if (soHien === 0)
              khongThay.textContent = 'Không tìm thấy "' + oTim.value
                + '". Thử bớt từ khoá, hoặc thêm dòng mới ở dưới.';
          }}

          oTim.addEventListener('input', loc);
          document.getElementById('nut-xoa-tim').addEventListener('click',
            function() {{ oTim.value = ''; loc(); oTim.focus(); }});
          loc();

          // Bam vao tham so = chep. Dung clipboard API neu co, khong thi
          // quay ve cach cu (textarea + execCommand) - trinh duyet kiosk
          // chay qua HTTP thuong khong cho dung clipboard API.
          document.addEventListener('click', function(e) {{
            var el = e.target.closest('.chep');
            if (!el) return;
            var s = el.textContent;
            var xong = function() {{
              var cu = el.getAttribute('data-cu') || el.textContent;
              el.classList.add('da-chep');
              var nhan = document.createElement('span');
              nhan.className = 'nhan-chep'; nhan.textContent = 'đã chép';
              el.appendChild(nhan);
              setTimeout(function() {{
                el.classList.remove('da-chep');
                if (nhan.parentNode) nhan.parentNode.removeChild(nhan);
              }}, 1200);
            }};
            if (navigator.clipboard && window.isSecureContext) {{
              navigator.clipboard.writeText(s).then(xong, function() {{}});
            }} else {{
              var t = document.createElement('textarea');
              t.value = s; t.style.position = 'fixed'; t.style.opacity = '0';
              document.body.appendChild(t); t.select();
              try {{ document.execCommand('copy'); xong(); }} catch (err) {{}}
              document.body.removeChild(t);
            }}
          }});
        }})();
        </script>"""
        return _trang(body, "Tham số cài đặt",
                      "Tra tham số cài im lặng của từng phần mềm",
                      active="/deployos")

    @app.route("/deployos/thamso/them", methods=["POST"])
    def deployos_thamso_them():
        from . import thamso as _ts
        ok, msg = _ts.them(request.form)
        return _trang_thamso(msg, ok)

    @app.route("/deployos/thamso/sua", methods=["POST"])
    def deployos_thamso_sua():
        from . import thamso as _ts
        ok, msg = _ts.sua(request.form.get("id", ""), request.form)
        return _trang_thamso(msg, ok)

    @app.route("/deployos/thamso/xoa", methods=["POST"])
    def deployos_thamso_xoa():
        from . import thamso as _ts
        ok, msg = _ts.xoa(request.form.get("id", ""))
        return _trang_thamso(msg, ok)

    # ------------------------- ung dung thu muc (mo hinh MDT: "Application
    # with source files" - xem chi tiet trong docstring cua danh_sach_ungdung()
    # o dau file. Dung cho bo cai NHIEU FILE nhu Office 365 (Office Deployment
    # Tool: thu muc Office\ + setup.exe + configuration.xml).
    @app.route("/deployos/ungdung")
    def deployos_ungdung():
        return _trang_ungdung()

    def _trang_ungdung(msg="", ok=True):
        ds = danh_sach_ungdung()
        hang = ""
        for u in ds:
            hang += f"""
            <tr>
              <td><strong>{_esc(u['ten_hien_thi'])}</strong></td>
              <td>{u['so_file']} file &middot; {_esc(u['kich_thuoc'])}</td>
              <td>{'<code>' + _esc(u['lenh_cai']) + '</code>' if u['lenh_cai'] else
                  '<span style="color:#f59e0b;">chưa đặt lệnh cài</span>'}</td>
              <td>
                <a class="btn small" href="/deployos/ungdung/{_esc(u['id'])}">Quản lý</a>
                <form method="POST" action="/deployos/ungdung/xoa" style="display:inline;"
                      onsubmit="return confirm('Xóa toàn bộ ứng dụng này?');">
                  <input type="hidden" name="ung_id" value="{_esc(u['id'])}">
                  <button type="submit" class="red small">Xóa</button>
                </form>
              </td>
            </tr>"""
        bang = (f"""<div class="tbl-scroll"><table>
              <tr><th>Tên</th><th style="width:170px;">Nội dung</th>
                  <th>Lệnh cài</th><th style="width:150px;">Thao tác</th></tr>
              {hang}
            </table></div>""" if ds else
            '<p style="color:#8b93a1;">Chưa có ứng dụng nào.</p>')
        body = (_tabs("tainguyen", "ungdung") + _msg(msg, ok) + f"""
        <div class="card">
          <h3>Khác gì với "Phần mềm"?</h3>
          <table class="tt-bang">
            <tr><td style="width:150px;">Phần mềm</td>
                <td>1 file .msi/.exe duy nhất, tự suy tham số cài theo đuôi
                file. Hợp cho bộ cài đơn giản (7-Zip, TeamViewer...).</td></tr>
            <tr><td>Ứng dụng (đây)</td>
                <td>1 <strong>thư mục</strong> - chứa bao nhiêu file/thư mục
                con cũng được - kèm 1 <strong>dòng lệnh cài tự do</strong> do
                anh tự gõ. Đúng mô hình "Application with source files" của
                MDT. Dùng cho bộ cài nhiều file như <strong>Office 365</strong>
                (Office Deployment Tool): tải bộ Office đã tải sẵn bằng
                <code>setup.exe /download</code> lên đây (nén .zip), đặt lệnh
                cài là <code>setup.exe /configure configuration.xml</code>.</td></tr>
          </table>
        </div>
        <div class="card">
          <h3>Tạo ứng dụng mới</h3>
          <form method="POST" action="/deployos/ungdung/tao">
            <input type="text" name="ten_hien_thi" placeholder="Tên ứng dụng"
                   required autocapitalize="off">
            <button type="submit">Tạo</button>
          </form>
        </div>
        <h2>Ứng dụng đã có ({len(ds)})</h2>
        {bang}""")
        return _trang(body, "Deployment OS", "Ứng dụng (nhiều file)")

    @app.route("/deployos/ungdung/tao", methods=["POST"])
    def deployos_ungdung_tao():
        ok, msg, ung_id = tao_ungdung_moi(request.form.get("ten_hien_thi", ""))
        if ok:
            return redirect(f"/deployos/ungdung/{ung_id}")
        return _trang_ungdung(msg, ok)

    @app.route("/deployos/ungdung/xoa", methods=["POST"])
    def deployos_ungdung_xoa():
        ok, msg = xoa_ungdung(request.form.get("ung_id", ""))
        return _trang_ungdung(msg, ok)

    @app.route("/deployos/ungdung/<ung_id>")
    def deployos_ungdung_chitiet(ung_id):
        u = lay_ungdung(ung_id)
        if u is None:
            return _trang_ungdung("Không tìm thấy ứng dụng.", False)
        muc = liet_ke_muc_ungdung(ung_id)
        hang = ""
        for m in muc:
            bieu = "📁" if m["la_thu_muc"] else "📄"
            chi_tiet = (f"{m['so_file']} file bên trong" if m["la_thu_muc"]
                       else m["kich_thuoc"])
            hang += f"""
            <tr><td>{bieu} {_esc(m['ten'])}</td><td>{chi_tiet}</td>
                <td><form method="POST" action="/deployos/ungdung/{_esc(ung_id)}/xoa-muc"
                          style="display:inline;"
                          onsubmit="return confirm('Xóa {_esc(m["ten"])}?');">
                      <input type="hidden" name="ten" value="{_esc(m['ten'])}">
                      <button type="submit" class="red small">Xóa</button>
                    </form></td></tr>"""
        bang = (f"""<div class="tbl-scroll"><table>
              <tr><th>Tên</th><th>Chi tiết</th><th style="width:90px;">Thao tác</th></tr>
              {hang}
            </table></div>""" if muc else
            '<p style="color:#8b93a1;">Thư mục ứng dụng đang trống.</p>')
        body = (_tabs("tainguyen", "ungdung") + f"""
        <p><a href="/deployos/ungdung">&larr; Về danh sách ứng dụng</a></p>
        <h2>{_esc(u['ten_hien_thi'])}</h2>

        <div class="card">
          <h3>Dòng lệnh cài</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 9px;">
            Lúc cài, hệ thống tự <code>cd</code> vào đúng thư mục này rồi chạy
            dòng lệnh - chỉ cần gõ tên file, không cần đường dẫn đầy đủ. Ví
            dụ Office 365: <code>setup.exe /configure configuration.xml</code>.</p>
          <form method="POST" action="/deployos/ungdung/{_esc(ung_id)}/lenh">
            <input type="text" name="lenh_cai" value="{_esc(u['lenh_cai'])}"
                   placeholder="vd: setup.exe /configure configuration.xml"
                   style="max-width:none;" autocapitalize="off">
            <div class="row" style="margin-top:10px;">
              <button type="submit">Lưu lệnh cài</button>
            </div>
          </form>
        </div>

        <div class="card">
          <h3>Tải lên bộ cài (.zip)</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 9px;">
            Nén TOÀN BỘ thư mục nguồn (giữ nguyên thư mục con bên trong) rồi
            tải lên đây - hệ thống tự giải nén, giữ đúng cấu trúc thư mục.
            File lớn (vài GB) vẫn tải lên được, ghi thẳng ra đĩa không qua
            RAM - chỉ là sẽ mất thời gian theo tốc độ mạng.</p>
          <form method="POST" action="/deployos/ungdung/{_esc(ung_id)}/len"
                enctype="multipart/form-data" data-busy="Đang tải lên và giải nén...">
            <input type="file" name="file" accept=".zip" required>
            <button type="submit">Tải lên</button>
          </form>
        </div>

        <div class="card">
          <h3>Thay 1 file lẻ (vd file cấu hình .xml)</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 9px;">
            Dùng khi chỉ cần sửa/thay 1 file nhỏ (cấu hình, script...) mà
            không muốn nén lại cả bộ - tải file này lên sẽ đặt thẳng vào
            gốc thư mục ứng dụng, <strong>ghi đè</strong> nếu đã có file
            trùng tên.</p>
          <form method="POST" action="/deployos/ungdung/{_esc(ung_id)}/len-file"
                enctype="multipart/form-data" data-busy="Đang tải lên...">
            <input type="file" name="file" required>
            <button type="submit" class="gray">Tải lên (ghi đè)</button>
          </form>
        </div>

        <h3>Nội dung hiện có</h3>
        {bang}""")
        return _trang(body, "Deployment OS", f"Ứng dụng - {u['ten_hien_thi']}")

    @app.route("/deployos/ungdung/<ung_id>/lenh", methods=["POST"])
    def deployos_ungdung_lenh(ung_id):
        ok, msg = dat_lenh_cai_ungdung(ung_id, request.form.get("lenh_cai", ""))
        if not ok:
            return _trang_ungdung(msg, ok)
        return redirect(f"/deployos/ungdung/{ung_id}")

    @app.route("/deployos/ungdung/<ung_id>/xoa-muc", methods=["POST"])
    def deployos_ungdung_xoa_muc(ung_id):
        ok, msg = xoa_muc_trong_ungdung(ung_id, request.form.get("ten", ""))
        if not ok:
            return _trang_ungdung(msg, ok)
        return redirect(f"/deployos/ungdung/{ung_id}")

    @app.route("/deployos/ungdung/<ung_id>/len", methods=["POST"])
    def deployos_ungdung_len(ung_id):
        f = request.files.get("file")
        if not f or not getattr(f, "filename", ""):
            return redirect(f"/deployos/ungdung/{ung_id}")
        duong = getattr(getattr(f, "stream", None), "_cp_duong_dan", None)
        if not duong:
            return _trang_ungdung(
                "Chỉ nhận file .zip - đổi đuôi file cho đúng rồi thử lại.", False)
        try:
            f.stream.flush()
            os.fsync(f.stream.fileno())
        except Exception:
            pass
        ok, msg, duong_dich = _hoan_tat_ghi_thang(
            duong, os.path.join(UNGDUNG_DIR, ten_an_toan(ung_id)), f.filename)
        if not ok:
            return _trang_ungdung(msg, ok)
        ok, msg = giai_nen_ungdung(ung_id, duong_dich)
        if not ok:
            return _trang_ungdung(msg, ok)
        return redirect(f"/deployos/ungdung/{ung_id}")

    @app.route("/deployos/ungdung/<ung_id>/len-file", methods=["POST"])
    def deployos_ungdung_len_file(ung_id):
        """
        Tai LE 1 file (khong can nen .zip) vao goc thu muc ung dung - GHI
        DE neu trung ten. Sinh ra tu chinh su co that: anh Thoai can THAY
        1 file cau hinh nho (vai KB) trong 1 ung dung da co san hang GB
        (Office 365) - truoc day CHI co duong tai .zip, buoc phai nen ca
        1 file nho thanh zip moi thay duoc, rat bat tien.

        Dung f.save() binh thuong (khong qua co che ghi thang danh cho
        file lon nhu .zip) vi day chi de danh cho file cau hinh/script nho.
        """
        u = lay_ungdung(ung_id)
        if u is None:
            return _trang_ungdung("Không tìm thấy ứng dụng.", False)
        f = request.files.get("file")
        if not f or not getattr(f, "filename", ""):
            return redirect(f"/deployos/ungdung/{ung_id}")
        ten = ten_an_toan(f.filename)
        if not ten or ten == "_thongtin.json":
            return _trang_ungdung("Tên file không hợp lệ.", False)
        thu_muc = os.path.join(UNGDUNG_DIR, ten_an_toan(ung_id))
        try:
            f.save(os.path.join(thu_muc, ten))
        except OSError as e:
            return _trang_ungdung(f"Không lưu được: {e}", False)
        return redirect(f"/deployos/ungdung/{ung_id}")

    @app.route("/deployos/drivers/<driver_id>")
    def deployos_drivers_chitiet(driver_id):
        ds = danh_sach_driver()
        dr = next((x for x in ds if x["id"] == driver_id), None)
        if dr is None:
            return _trang_drivers("Khong tim thay goi driver.", False)
        p = os.path.join(DRIVERS_DIR, ten_an_toan(driver_id))
        hang = ""
        try:
            for n in sorted(os.listdir(p)):
                if n == "_thongtin.json":
                    continue
                fp = os.path.join(p, n)
                if not os.path.isfile(fp):
                    continue
                hang += f"""
                <tr><td>{_esc(n)}</td><td>{co_kich_thuoc(os.path.getsize(fp))}</td>
                    <td><form method="POST" action="/deployos/drivers/{_esc(driver_id)}/xoa-file"
                              style="display:inline;">
                          <input type="hidden" name="ten" value="{_esc(n)}">
                          <button type="submit" class="red small">Xóa</button>
                        </form></td></tr>"""
        except OSError:
            pass
        bang = (f"""<div class="tbl-scroll"><table>
              <tr><th>File</th><th>Dung luong</th><th style="width:90px;">Thao tac</th></tr>
              {hang}
            </table></div>""" if hang else
            '<p style="color:#8b93a1;">Chua co file nao trong goi nay.</p>')
        body = (_tabs("tainguyen", "drivers") + f"""
        <p><a href="/deployos/drivers">&larr; Ve danh sach driver</a></p>
        <h2>{_esc(dr['ten_hien_thi'])}</h2>
        {bang}
        <div class="card" style="margin-top:14px;">
          <h3>Tai len file driver (.inf/.sys/.cat/.dll/.zip)</h3>
          <form method="POST" action="/deployos/drivers/{_esc(driver_id)}/len"
                enctype="multipart/form-data">
            <input type="file" name="file" required>
            <button type="submit">Tải lên</button>
          </form>
        </div>""")
        return _trang(body, "Deployment OS", f"Driver - {dr['ten_hien_thi']}")

    @app.route("/deployos/drivers/<driver_id>/len", methods=["POST"])
    def deployos_drivers_len(driver_id):
        f = request.files.get("file")
        if not f or not getattr(f, "filename", ""):
            return redirect(f"/deployos/drivers/{driver_id}")
        duong = getattr(getattr(f, "stream", None), "_cp_duong_dan", None)
        if duong:
            try:
                f.stream.flush()
                os.fsync(f.stream.fileno())
            except Exception:
                pass
            thu_muc = os.path.join(DRIVERS_DIR, ten_an_toan(driver_id))
            ok, msg, _duong_dich = _hoan_tat_ghi_thang(duong, thu_muc, f.filename)
        else:
            ok, msg = False, ("Duoi file khong duoc nhan (.inf/.sys/.cat/"
                              ".dll/.zip) hoac khong ghi thang duoc.")
        if ok:
            return redirect(f"/deployos/drivers/{driver_id}")
        return _trang_drivers(msg, ok)

    @app.route("/deployos/drivers/<driver_id>/xoa-file", methods=["POST"])
    def deployos_drivers_xoa_file(driver_id):
        ok, msg = xoa_file_trong_driver(driver_id, request.form.get("ten", ""))
        if ok:
            return redirect(f"/deployos/drivers/{driver_id}")
        return _trang_drivers(msg, ok)

    # ------------------------------------------------------ 2.1 file boot
    @app.route("/deployos/console")
    def deployos_console():
        return _trang_file_boot()

    def _trang_file_boot(msg="", ok=True):
        _don_file_do_dang(BOOT_DIR)
        ds = _liet_ke(BOOT_DIR, EXT_BOOT)
        ghi_chu = """
        <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
          Nhận ảnh cài đặt (.iso/.wim/.esd/.img/.vhd) và bootloader iPXE
          (undionly.kpxe cho máy BIOS đời cũ, ipxe.efi cho máy UEFI - tải từ
          <code>ipxe.org</code>). Ảnh WinPE (boot.wim) phải tạo sẵn trên 1 máy
          Windows có Windows ADK - Pi không tự tạo được, chỉ lưu và phục vụ.</p>"""
        body = (_tabs("tainguyen", "file") + _msg(msg, ok) +
                _khoi_tai_len("/deployos/console/file/len", "file boot", EXT_BOOT, ghi_chu, "file") +
                f"<h2>File boot đang có ({len(ds)})</h2>" +
                _bang_file(ds, "/deployos/console/file/xoa", "/deployos/console/file/tai"))
        return _trang(body, "Deployment OS", "2.1 - File boot")

    @app.route("/deployos/console/file/len", methods=["POST"])
    def deployos_boot_len():
        f = request.files.get("file")
        if not f:
            return _trang_file_boot("Chua chon file.", False)
        ok, msg = _nhan_tai_len(BOOT_DIR, EXT_BOOT, "file boot")
        return _trang_file_boot(msg, ok)

    @app.route("/deployos/console/file/xoa", methods=["POST"])
    def deployos_boot_xoa():
        ok, msg = _xoa_file(BOOT_DIR, request.form.get("ten", ""))
        return _trang_file_boot(msg, ok)

    @app.route("/deployos/console/file/tai/<ten>")
    def deployos_boot_tai(ten):
        p = _duong_dan_trong(BOOT_DIR, ten)
        if not p or not os.path.isfile(p):
            abort(404)
        return send_from_directory(BOOT_DIR, os.path.basename(p), as_attachment=True)

    # ------------------------------------------------------- 2.2 phan mem
    @app.route("/deployos/console/apps")
    def deployos_apps():
        return _trang_apps()

    def _trang_apps(msg="", ok=True):
        _don_file_do_dang(APPS_DIR)
        ds = danh_sach_app()
        ghi_chu = """
        <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
          Nhận file cài đặt .msi và .exe. Sau khi tải lên, điền tham số cài
          IM LẶNG cho từng file ở bảng bên dưới (mỗi hãng một kiểu:
          <code>/S</code>, <code>/silent</code>, <code>/verysilent</code>,
          <code>/quiet</code>...). File .msi thì không bắt buộc - mặc định
          dùng <code>/qn /norestart</code>.</p>

        <datalist id="goiy-thamso">""" + "".join(
            f'<option value="{_esc(gt)}">{_esc(mo_ta)}</option>'
            for gt, mo_ta in GOI_Y_THAM_SO) + """</datalist>

        <div class="card">
          <h3>Tra cứu nhanh: tham số cài im lặng theo từng loại bộ cài</h3>
          <p style="color:#8b93a1;font-size:12.5px;margin:0 0 10px;">
            Mỗi hãng phần mềm dùng một bộ đóng gói khác nhau nên tham số
            khác nhau - KHÔNG có tham số nào dùng cho tất cả. Cách nhận
            biết nhanh: bấm chuột phải file .exe &rarr; Properties &rarr;
            tab Details, xem mục "Original filename"/"Product name". Nếu
            không rõ, chạy thử file với tham số <code>/?</code> trên 1 máy
            bất kỳ - phần lớn bộ cài sẽ hiện danh sách tham số.</p>
          <div class="tbl-scroll"><table>
            <tr><th style="width:210px;">Tham số</th><th>Dùng cho</th></tr>""" + "".join(
            f'<tr><td><code>{_esc(gt)}</code></td><td>{_esc(mo_ta)}</td></tr>'
            for gt, mo_ta in GOI_Y_THAM_SO) + """
          </table></div>
          <p style="color:#8b93a1;font-size:12.5px;margin:10px 0 0;">
            Ô điền tham số bên dưới có sẵn gợi ý - bấm vào ô đó sẽ hiện
            danh sách này để chọn, không phải gõ tay.</p>
        </div>"""

        if ds:
            hang = ""
            for a in ds:
                goi_y = ("msiexec /i ... /quiet /norestart (mac dinh)"
                         if a["la_msi"] else "vd: /S hoac /verysilent")
                hang += f"""
                <tr>
                  <td><strong>{_esc(a['ten'])}</strong><br>
                      <small style="color:#8b93a1;">{co_kich_thuoc(a['cd'])} &middot; {_esc(a['ngay'])}</small></td>
                  <td>
                    <form method="POST" action="/deployos/console/apps/thamso" class="row" style="gap:8px;">
                      <input type="hidden" name="ten" value="{_esc(a['ten'])}">
                      <input type="text" name="tham_so" value="{_esc(a['tham_so'])}"
                             placeholder="{goi_y}" style="max-width:250px;"
                             list="goiy-thamso" autocapitalize="off">
                      <button type="submit" class="small gray">Lưu</button>
                    </form>
                  </td>
                  <td>
                    <a class="btn small gray" href="/deployos/console/apps/tai/{_esc(a['ten'])}">Tải về</a>
                    <form method="POST" action="/deployos/console/apps/xoa" style="display:inline;"
                          onsubmit="return confirm('Xoa {_esc(a['ten'])}?');">
                      <input type="hidden" name="ten" value="{_esc(a['ten'])}">
                      <button type="submit" class="red small">Xóa</button>
                    </form>
                  </td>
                </tr>"""
            bang = f"""
            <div class="tbl-scroll"><table>
              <tr><th>Phần mềm</th><th style="width:340px;">Tham số cài im lặng</th>
                  <th style="width:180px;">Thao tác</th></tr>
              {hang}
            </table></div>"""
        else:
            bang = '<p style="color:#8b93a1;">Chưa có phần mềm nào.</p>'

        body = (_tabs("tainguyen", "apps") + _msg(msg, ok) +
                _khoi_tai_len("/deployos/console/apps/len", "phan mem", EXT_APP, ghi_chu, "apps") +
                f"<h2>Phần mềm đang có ({len(ds)})</h2>" + bang +
                """
                <div class="msg info">Các file này KHÔNG bao giờ được chạy trên
                chính Console Pi - Pi chỉ lưu và gửi chúng cho máy đang được
                cài lại tải về.</div>""")
        return _trang(body, "Deployment OS", "2.2 - Phan mem")

    @app.route("/deployos/console/apps/len", methods=["POST"])
    def deployos_apps_len():
        f = request.files.get("file")
        if not f:
            return _trang_apps("Chua chon file.", False)
        ok, msg = _nhan_tai_len(APPS_DIR, EXT_APP, "phan mem")
        return _trang_apps(msg, ok)

    @app.route("/deployos/console/apps/thamso", methods=["POST"])
    def deployos_apps_thamso():
        ten = ten_an_toan(request.form.get("ten", ""))
        if not ten or not os.path.isfile(os.path.join(APPS_DIR, ten)):
            return _trang_apps("Khong tim thay phan mem do.", False)
        meta = doc_thongtin_app()
        ts = (request.form.get("tham_so") or "").strip()[:200]
        if ts:
            meta[ten] = ts
        else:
            meta.pop(ten, None)
        ok = ghi_thongtin_app(meta)
        return _trang_apps("Da luu tham so." if ok else "Khong ghi duoc.", ok)

    @app.route("/deployos/console/apps/xoa", methods=["POST"])
    def deployos_apps_xoa():
        ten = ten_an_toan(request.form.get("ten", ""))
        ok, msg = _xoa_file(APPS_DIR, ten)
        if ok:
            meta = doc_thongtin_app()
            if meta.pop(ten, None) is not None:
                ghi_thongtin_app(meta)
        return _trang_apps(msg, ok)

    @app.route("/deployos/console/apps/tai/<ten>")
    def deployos_apps_tai(ten):
        p = _duong_dan_trong(APPS_DIR, ten)
        if not p or not os.path.isfile(p):
            abort(404)
        return send_from_directory(APPS_DIR, os.path.basename(p), as_attachment=True)

    # --------------------------------------------------------- 2.3 script
    @app.route("/deployos/console/scripts")
    def deployos_scripts():
        return _trang_scripts()

    def _trang_scripts(msg="", ok=True):
        _don_file_do_dang(SCRIPTS_DIR)
        ds = _liet_ke(SCRIPTS_DIR, EXT_SCRIPT)
        ghi_chu = """
        <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
          Nhận .bat, .cmd (Windows) và .ps1 (PowerShell). Các script này sẽ
          chạy TRÊN MÁY ĐANG ĐƯỢC CÀI sau khi cài xong OS và phần mềm, không
          chạy trên Console Pi.</p>"""
        body = (_tabs("tainguyen", "scripts") + _msg(msg, ok) +
                _khoi_tai_len("/deployos/console/scripts/len", "script", EXT_SCRIPT, ghi_chu, "scripts") +
                f"<h2>Script đang có ({len(ds)})</h2>" +
                _bang_file(ds, "/deployos/console/scripts/xoa",
                           "/deployos/console/scripts/tai"))
        return _trang(body, "Deployment OS", "2.3 - Script")

    @app.route("/deployos/console/scripts/len", methods=["POST"])
    def deployos_scripts_len():
        f = request.files.get("file")
        if not f:
            return _trang_scripts("Chua chon file.", False)
        ok, msg = _nhan_tai_len(SCRIPTS_DIR, EXT_SCRIPT, "script")
        return _trang_scripts(msg, ok)

    @app.route("/deployos/console/scripts/xoa", methods=["POST"])
    def deployos_scripts_xoa():
        ok, msg = _xoa_file(SCRIPTS_DIR, request.form.get("ten", ""))
        return _trang_scripts(msg, ok)

    @app.route("/deployos/console/scripts/tai/<ten>")
    def deployos_scripts_tai(ten):
        p = _duong_dan_trong(SCRIPTS_DIR, ten)
        if not p or not os.path.isfile(p):
            abort(404)
        return send_from_directory(SCRIPTS_DIR, os.path.basename(p), as_attachment=True)

    # -------------------------------------------------------- 2.4 kich ban
    def _bang_kichban(ds, esc):
        if not ds:
            return ('<p style="color:#8b93a1;">Chua co kich ban nao. Bam '
                    '"Tao kich ban moi" de tao cai dau tien.</p>')
        hang = ""
        for k in ds:
            hang += f"""
            <tr>
              <td><strong>{esc(k.get('ten_kichban', k['_file']))}</strong></td>
              <td>{_o_tom_tat(k, esc)}</td>
              <td style="color:#8b93a1;">{esc(k.get('_ngay', ''))}</td>
              <td>
                <a class="btn small gray" href="/deployos/kichban/sua/{esc(k['_file'])}">Chinh sua</a>
                <form method="POST" action="/deployos/kichban/xoa" style="display:inline;"
                      onsubmit="return confirm('Xóa kịch bản này?');">
                  <input type="hidden" name="ten" value="{esc(k['_file'])}">
                  <button type="submit" class="red small">Xóa</button>
                </form>
              </td>
            </tr>"""
        return f"""
        <div class="tbl-scroll"><table>
          <tr><th>Tên kịch bản</th><th>Tóm tắt</th>
              <th style="width:140px;">Ngay tao</th><th style="width:150px;">Thao tac</th></tr>
          {hang}
        </table></div>"""

    return app


def _ten_os(d):
    o = lay_os(d.get("os_id", ""))
    return o["ten_hien_thi"] if o else "Chưa chọn"


def _tom_tat_day_du(k, esc):
    """
    Bang tom tat DAY DU cua 1 kich ban - hien trong hop thoai khi bam nut
    "Tóm tắt" o danh sach.

    VI SAO TACH RA (anh Thoai: "phan tom tat khong can dai du vay dau"):
    truoc day toan bo noi dung nay bi nhoi vao 1 o cua bang danh sach, lam
    moi hang cao nghen ngang, nhin ca danh sach rat kho. Nay o do chi con
    2 dong (cat bang CSS), muon xem het thi bam nut - khong mat thong tin
    nao ca, chi doi cho hien.
    """
    from . import unattend as _u
    dong = []

    def them(nhan, gt):
        if gt:
            dong.append(f"<tr><td style='color:#8b93a1;white-space:nowrap;'>"
                        f"{esc(nhan)}</td><td>{gt}</td></tr>")

    them("Hệ điều hành", esc(_ten_os(k)))
    them("Tên máy", esc(k.get("ten_may") or ""))
    them("Tài khoản", esc(k.get("username") or ""))
    them("Múi giờ", esc(k.get("mui_gio") or ""))

    if k.get("os_ho") != "linux":
        ten_nn = dict(NGON_NGU).get(k.get("ngon_ngu"), k.get("ngon_ngu") or "")
        ten_bp = dict(BAN_PHIM).get(k.get("ban_phim"), k.get("ban_phim") or "")
        them("Ngôn ngữ", esc(ten_nn))
        them("Bàn phím", esc(ten_bp))
        them("Key Windows", "đã nhập" if k.get("product_key")
             else "<span style='color:#8b93a1;'>key KMS mặc định</span>")
        them("Administrator", "<span style='color:#f59e0b;'>đã mở</span>"
             if k.get("bat_admin") else "khoá (mặc định)")
        them("Tự đăng nhập", "mãi mãi" if k.get("tu_dang_nhap")
             else "chỉ lần đầu (sau đó hỏi mật khẩu)")

    if k.get("domain"):
        mo = esc(k["domain"])
        if k.get("domain_ou"):
            mo += f" &mdash; OU: {esc(k['domain_ou'])}"
        them("Gia nhập domain", mo)

    ds_app = chuan_hoa_apps(k.get("apps"))
    if ds_app:
        them("Phần mềm", "<br>".join(
            f"{esc(a['ten'])} <small style='color:#8b93a1;'>"
            f"({'máy' if a.get('dich') == 'may' else 'người dùng'})</small>"
            for a in ds_app))

    ds_ud = chuan_hoa_ungdung(k.get("ungdung"))
    if ds_ud:
        them("Ứng dụng nhiều file", "<br>".join(
            f"{esc(u['id'])} <small style='color:#8b93a1;'>"
            f"({'máy' if u.get('dich') == 'may' else 'người dùng'})</small>"
            for u in ds_ud))

    if k.get("scripts"):
        them("Script", "<br>".join(esc(s) for s in k["scripts"]))

    da_chon = set(k.get("tuy_chon") or [])
    if da_chon:
        them("Tùy chọn Windows", "<br>".join(
            esc(nhan) for ma, nhan, _m, _p, _l in _u.TUY_CHON_WINDOWS
            if ma in da_chon))

    go = k.get("go_app") or []
    if go:
        ten_theo_ma = {ma: ten for ma, ten, _n in _u.APP_RAC}
        them("Gỡ ứng dụng kèm sẵn",
             f"{len(go)} ứng dụng: "
             + ", ".join(esc(ten_theo_ma.get(m, m)) for m in go))

    if (k.get("lenh_them") or "").strip():
        them("Lệnh thêm",
             f"<pre style='margin:0;white-space:pre-wrap;'>"
             f"{esc(k['lenh_them'])}</pre>")

    od = k.get("o_dia_che_do")
    them("Ổ đĩa", ("tự động (ổ %s, %s)" % (k.get("o_dia_so", "0"),
                                           (k.get("o_dia_bang") or "gpt").upper())
                   if od == "tu_dong" else "chia tay"))
    return "<table class='tt-bang'>" + "".join(dong) + "</table>"


def _o_tom_tat(k, esc):
    """1 o bang: tom tat 2 dong + nut mo hop thoai xem day du."""
    ma = "tt-" + re.sub(r"[^A-Za-z0-9_-]", "_", k.get("_file", ""))
    return f"""
      <div class="tt-gon">{esc(_mo_ta_ngan(k))}</div>
      <button type="button" class="tt-nut"
              onclick="document.getElementById('{ma}').showModal()">Tóm tắt</button>
      <dialog id="{ma}" class="tt-hop">
        <h3>{esc(k.get('ten_kichban', k.get('_file', '')))}</h3>
        {_tom_tat_day_du(k, esc)}
        <form method="dialog" style="margin-top:14px;">
          <button class="gray">Đóng</button>
        </form>
      </dialog>"""


def _mo_ta_ngan(k):
    """
    Tom tat cho bang danh sach kich ban.

    LY DO PHAI GHI DAY DU (anh Thoai: "nhieu khi sau nay sao anh biet
    duoc kich ban do da co nhung cai gi option gi"): truoc day dong nay
    chi ghi OS + ten may + so luong phan mem/script, nen nhin vao danh
    sach khong the biet kich ban do cai PHAN MEM NAO, bat TUY CHON gi,
    co gia nhap domain khong - phai bam "Dung" vao tung cai moi biet.
    Gio liet ke thang ten phan mem va ten tuy chon.
    """
    phan = [_ten_os(k)]
    if k.get("ten_may"):
        phan.append(k["ten_may"])
    if k.get("domain"):
        phan.append("domain: " + k["domain"])

    ds_app = chuan_hoa_apps(k.get("apps"))
    if ds_app:
        phan.append("phần mềm: " + ", ".join(a["ten"] for a in ds_app))

    ds_ud = chuan_hoa_ungdung(k.get("ungdung"))
    if ds_ud:
        phan.append("ứng dụng: " + ", ".join(u["id"] for u in ds_ud))

    n_sc = len(k.get("scripts") or [])
    if n_sc:
        phan.append(f"{n_sc} script")

    da_chon = set(k.get("tuy_chon") or [])
    if da_chon:
        from . import unattend as _u
        ten_tc = [nhan for ma, nhan, _m, _p, _l in _u.TUY_CHON_WINDOWS
                  if ma in da_chon]
        phan.append("tùy chọn: " + ", ".join(ten_tc))

    if (k.get("lenh_them") or "").strip():
        phan.append("có lệnh thêm")

    return " - ".join(phan)
