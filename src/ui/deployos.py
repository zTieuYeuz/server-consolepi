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
DEPLOY_DIR = "/opt/console-pi/deploy"
BOOT_DIR = os.path.join(DEPLOY_DIR, "boot")
APPS_DIR = os.path.join(DEPLOY_DIR, "apps")
SCRIPTS_DIR = os.path.join(DEPLOY_DIR, "scripts")
KICHBAN_DIR = os.path.join(DEPLOY_DIR, "kichban")
APPS_META = os.path.join(APPS_DIR, "_thongtin.json")

# Con lai duoi muc nay thi khong cho tai them (giong ui/storage.py)
MIN_FREE_GB = 3

EXT_BOOT = {".iso", ".wim", ".esd", ".img", ".vhd", ".vhdx", ".efi", ".kpxe", ".ipxe"}
EXT_APP = {".msi", ".exe"}
EXT_SCRIPT = {".bat", ".ps1", ".cmd"}

# ---------------------------------------------------------------- lua chon
KIEU_BOOT = [
    ("truc_tiep", "Boot OS truc tiep voi client",
     "Cam day mang THANG tu Pi sang may can cai. Pi tu cap IP + chi duong "
     "boot. Khong dung cham gi toi mang cua khach - chac an nhat."),
    ("mang_khong_dhcp", "Boot OS qua mang khong DHCP",
     "Pi va may can cai cung cam vao 1 switch, nhung mang do KHONG co "
     "DHCP server nao. Pi dong luon vai tro cap IP + chi duong boot."),
    ("mang_co_dhcp", "Boot OS qua mang co DHCP",
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

# Cac buoc cua trinh tu tu chon (dung chung cho ca 2 che do: chay ngay va
# luu thanh kich ban - chi khac o buoc cuoi)
TEN_BUOC = [
    (1, "Kieu boot"),
    (2, "Chon OS"),
    (3, "Thong tin OS"),
    (4, "Phan chia o dia"),
    (5, "Phan mem"),
    (6, "Chinh sua cai dat"),
    (7, "Tong ket"),
]
SO_BUOC = len(TEN_BUOC)


# ---------------------------------------------------------------- tien ich
def _bao_dam_thu_muc():
    """Tao san cac thu muc. Kich ban de 700 vi co the chua mat khau."""
    for d in (DEPLOY_DIR, BOOT_DIR, APPS_DIR, SCRIPTS_DIR):
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


def _mo_file_dich(duong_url, filename):
    """
    Mo san file dich de Werkzeug ghi thang vao. Tra ve (fileobj, duong_dan)
    hoac (None, None) neu duong nay khong phai duong tai len cua tab nay.
    """
    cau_hinh = THU_MUC_THEO_DUONG.get(duong_url)
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
    """Doi ten <ten>.part thanh ten that sau khi da ghi xong."""
    try:
        cd = os.path.getsize(tam)
    except OSError:
        return False, "Khong doc duoc file vua tai len."
    if cd == 0:
        try:
            os.remove(tam)
        except OSError:
            pass
        return False, "File tai len rong (0 byte)."

    ten = ten_an_toan(ten_goc)
    dich = os.path.join(thu_muc, ten)
    if os.path.exists(dich):
        goc, duoi = os.path.splitext(ten)
        ten = f"{goc}_{time.strftime('%H%M%S')}{duoi}"
        dich = os.path.join(thu_muc, ten)
    try:
        os.replace(tam, dich)
    except OSError as e:
        return False, f"Khong luu duoc: {e}"
    return True, f"Da luu {ten} ({co_kich_thuoc(cd)})."


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
        "File boot da tai len",
        (f"{len(ds_boot)} file trong {BOOT_DIR}" if ds_boot else
         "Chua co file nao - vao tab \"Console boot\" > \"File boot\" de tai len"),
    ))

    # 2. Bootloader iPXE (giai doan 1 cua PXE: TFTP phat file nho nay truoc)
    co_ipxe = any(
        os.path.isfile(os.path.join(BOOT_DIR, t))
        for t in ("undionly.kpxe", "ipxe.efi", "snponly.efi")
    )
    ra.append((
        co_ipxe,
        "Bootloader iPXE",
        ("Da co trong thu muc boot" if co_ipxe else
         "Chua co (can undionly.kpxe cho may BIOS doi cu / ipxe.efi cho may "
         "UEFI - tai tu ipxe.org roi tai len o tab File boot)"),
    ))

    # 3. dnsmasq da co cau hinh PXE chua
    co_pxe_conf = os.path.isfile("/etc/dnsmasq-pxe.conf")
    ra.append((
        co_pxe_conf,
        "Cau hinh PXE cua dnsmasq",
        ("Da co /etc/dnsmasq-pxe.conf" if co_pxe_conf else
         "Chua dung - day la GIAI DOAN KE TIEP cua ke hoach "
         "(docs/ke-hoach-pxe-winpe-tu-dong-cai-windows.md)"),
    ))

    # 4. Anh WinPE (chi can khi cai Windows)
    if (cauhinh or {}).get("os_ho") == "windows":
        co_winpe = any(
            n.lower() in ("boot.wim", "winpe.wim")
            for n in [f["ten"] for f in ds_boot]
        )
        ra.append((
            co_winpe,
            "Anh WinPE (boot.wim)",
            ("Da co" if co_winpe else
             "Chua co. Anh WinPE phai tao tren 1 may Windows co cai Windows "
             "ADK - Pi/Linux khong tu tao duoc, chi luu va phuc vu"),
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
        "os_ho": "", "os_ban": "", "file_boot": "",
        "ten_may": "", "username": "", "password": "",
        "ssh": False, "mui_gio": MUI_GIO[0],
        "o_dia_che_do": "tu_dong", "o_dia_so": "0", "o_dia_bang": "gpt",
        "phan_vung": [],
        "apps": [], "scripts": [], "lenh_them": "",
    }
    return ma


def _wizard_lay(ma):
    d = _WIZARD.get(ma)
    if d is not None:
        d["_luc"] = time.time()
    return d


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
    from flask import request, redirect, send_from_directory, abort, jsonify
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
        if request.path not in THU_MUC_THEO_DUONG:
            return None
        can = request.content_length or 0
        if not can:
            return None
        # Ghi thang ra dia dich nen chi can DUNG BANG kich thuoc file
        # (+1GB de he thong con cho tho), khong con can gap doi/gap ba nua.
        can_gb = can / (1024 ** 3) + 1
        if _con_trong_gb() < can_gb:
            thu_muc = THU_MUC_THEO_DUONG[request.path][0]
            return _trang(
                _tabs("console", "file") +
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
            return _hoan_tat_ghi_thang(duong, thu_muc, f.filename)
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
        """Thanh tab chinh + tab phu, dung chung cho moi trang cua muc nay."""
        tab_chinh = [
            ("boot", "1. Boot OS", "/deployos/boot"),
            ("console", "2. Console boot", "/deployos/console"),
        ]
        phu_theo_chinh = {
            "boot": [
                ("tuchon", "Tu lua chon", "/deployos/boot"),
                ("kichban", "Kich ban", "/deployos/boot/kichban"),
            ],
            "console": [
                ("file", "2.1 File boot", "/deployos/console"),
                ("apps", "2.2 Phan mem", "/deployos/console/apps"),
                ("scripts", "2.3 Script", "/deployos/console/scripts"),
                ("kichban", "2.4 Kich ban", "/deployos/console/kichban"),
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
        return redirect("/deployos/boot")

    @app.route("/deployos/boot")
    def deployos_boot():
        """1.1 - man hinh mo dau: chon tu lua chon hay dung kich ban co san."""
        ds_kb = danh_sach_kichban()
        body = _tabs("boot", "tuchon") + f"""
        <div class="msg info">
          <strong>Tinh nang dang lam dan tung phan.</strong> Phan chon cau
          hinh + luu kich ban o day da chay that. Phan PHUC VU BOOT that su
          (PXE/iPXE/WinPE) la giai doan ke tiep - buoc cuoi se cho anh biet
          chinh xac con thieu gi, khong bao "xong" khi chua that su xong.
        </div>

        <div class="card">
          <h3>Tu lua chon tung buoc</h3>
          <p style="color:#8b93a1;font-size:13.5px;margin:0 0 13px;">
            Di qua {SO_BUOC} buoc: kieu boot &rarr; chon OS &rarr; thong tin
            may &rarr; chia o dia &rarr; phan mem &rarr; chinh sua cai dat
            &rarr; tong ket. Moi buoc deu quay lui duoc de sua lai.</p>
          <a class="btn" href="/deployos/wizard/bat-dau?che_do=chay">
            Bat dau chon &rarr;</a>
        </div>

        <div class="card">
          <h3>Hoac dung kich ban da luu ({len(ds_kb)})</h3>
          <p style="color:#8b93a1;font-size:13.5px;margin:0 0 13px;">
            Kich ban duoc tao san o tab <a href="/deployos/console/kichban">
            2.4 Kich ban</a> - chon 1 cai la co ngay toan bo lua chon, khong
            phai chon lai tu dau.</p>
          <a class="btn gray" href="/deployos/boot/kichban">Xem kich ban &rarr;</a>
        </div>"""
        return _trang(body, "Deployment OS",
                      "Trien khai he dieu hanh qua mang cho may can cai lai")

    @app.route("/deployos/boot/kichban")
    def deployos_boot_kichban():
        """1.2 - chon 1 kich ban da tao tu 2.4."""
        ds = danh_sach_kichban()
        if ds:
            hang = ""
            for k in ds:
                hang += f"""
                <tr>
                  <td><strong>{_esc(k.get('ten_kichban', k['_file']))}</strong></td>
                  <td>{_esc(_mo_ta_ngan(k))}</td>
                  <td style="color:#8b93a1;">{_esc(k.get('_ngay', ''))}</td>
                  <td>
                    <a class="btn small" href="/deployos/boot/dung-kichban/{_esc(k['_file'])}">
                      Dung kich ban nay</a>
                  </td>
                </tr>"""
            noi_dung = f"""
            <div class="tbl-scroll"><table>
              <tr><th>Ten kich ban</th><th>Tom tat</th>
                  <th style="width:140px;">Ngay tao</th><th style="width:170px;">Thao tac</th></tr>
              {hang}
            </table></div>"""
        else:
            noi_dung = """
            <div class="msg warn">Chua co kich ban nao. Tao o tab
            <a href="/deployos/console/kichban">2.4 Kich ban</a>.</div>"""

        body = _tabs("boot", "kichban") + f"""
        <h2>Kich ban da luu</h2>
        {noi_dung}"""
        return _trang(body, "Deployment OS", "Chon 1 kich ban da tao san")

    @app.route("/deployos/boot/dung-kichban/<ten>")
    def deployos_dung_kichban(ten):
        """Nap kich ban vao trinh tu roi nhay thang toi buoc tong ket."""
        kb = doc_kichban(ten)
        if kb is None:
            return _trang(_tabs("boot", "kichban") +
                          _msg("Khong tim thay kich ban.", False),
                          "Deployment OS")
        ma = _wizard_moi("chay")
        d = _WIZARD[ma]
        for k in ("kieu_boot", "os_ho", "os_ban", "file_boot", "ten_may",
                  "username", "password", "ssh", "mui_gio", "o_dia_che_do",
                  "o_dia_so", "o_dia_bang", "phan_vung", "apps", "scripts",
                  "lenh_them"):
            if k in kb:
                d[k] = kb[k]
        d["tu_kichban"] = kb.get("ten_kichban", "")
        return redirect(f"/deployos/wizard/{ma}/7")

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
            _tabs("boot", "tuchon") +
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
                return "Chua chon kieu boot."
            d["kieu_boot"] = v

        elif buoc == 2:
            v = form.get("os", "")
            if "/" not in v:
                return "Chua chon he dieu hanh."
            ho, ban = v.split("/", 1)
            hop_le = any(ho == h and ban in [b for b, _ in ds]
                         for h, _, ds in DANH_SACH_OS)
            if not hop_le:
                return "Lua chon he dieu hanh khong hop le."
            # Doi ho OS thi bo phan vung chia tay cu di (bo phan vung cua
            # Windows va Linux khac han nhau - giu lai se sai)
            if d.get("os_ho") and d["os_ho"] != ho:
                d["phan_vung"] = []
            d["os_ho"], d["os_ban"] = ho, ban
            d["file_boot"] = form.get("file_boot", "")

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
            d["apps"] = form.getlist("app")

        elif buoc == 6:
            d["scripts"] = form.getlist("script")
            d["lenh_them"] = (form.get("lenh_them") or "").strip()[:4000]

        return ""

    # --------------------------------------------------------- ve tung buoc
    def _thanh_buoc(buoc):
        h = '<div class="buoc-bar">'
        for so, ten in TEN_BUOC:
            cls = "nay" if so == buoc else ("qua" if so < buoc else "")
            h += f'<div class="buoc-o {cls}"><span class="so">{so}</span>{_esc(ten)}</div>'
        return h + "</div>"

    def _nut_dieu_huong(buoc, nhan_tiep="Tiep theo &rarr;"):
        lui = ('<button type="submit" name="huong" value="lui" class="gray">'
               '&larr; Quay lai</button>' if buoc > 1 else "")
        return f"""
        <div class="row" style="margin-top:20px;gap:10px;">
          {lui}
          <button type="submit" name="huong" value="tiep">{nhan_tiep}</button>
        </div>"""

    def _ve_buoc(ma, d, buoc, loi=""):
        chinh = "console" if d.get("che_do") == "luu" else "boot"
        phu = "kichban" if d.get("che_do") == "luu" else "tuchon"
        than = (_tabs(chinh, phu) + _thanh_buoc(buoc) + _msg(loi, False) +
                _noi_dung_buoc(ma, d, buoc))
        tieu_de = ("Tao kich ban" if d.get("che_do") == "luu"
                   else "Deployment OS")
        return _trang(than, tieu_de,
                      f"Buoc {buoc}/{SO_BUOC}: {dict(TEN_BUOC)[buoc]}",
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
              <div class="card"><h3>Chon kieu boot</h3>{o}</div>
              {_nut_dieu_huong(buoc)}
            </form>"""

        # ------------------------------------------------- 1.1.2 chon OS
        if buoc == 2:
            cot = ""
            for ho, ten_ho, ds in DANH_SACH_OS:
                muc = ""
                for ban, ten_ban in ds:
                    gt = f"{ho}/{ban}"
                    ch = " checked" if f'{d["os_ho"]}/{d["os_ban"]}' == gt else ""
                    muc += f"""
                    <label class="chon" style="margin-bottom:8px;">
                      <input type="radio" name="os" value="{gt}"{ch}>
                      <span class="t">{_esc(ten_ban)}</span>
                    </label>"""
                cot += f'<div class="card"><h3>{_esc(ten_ho)}</h3>{muc}</div>'

            ds_boot = _liet_ke(BOOT_DIR, EXT_BOOT)
            if ds_boot:
                opt = '<option value="">-- Chua chon (de sau cung duoc) --</option>'
                for f in ds_boot:
                    s = " selected" if d.get("file_boot") == f["ten"] else ""
                    opt += (f'<option value="{_esc(f["ten"])}"{s}>'
                            f'{_esc(f["ten"])} ({co_kich_thuoc(f["cd"])})</option>')
                chon_file = f"""
                <div class="card">
                  <h3>File boot dung cho lan nay (khong bat buoc)</h3>
                  <p style="color:#8b93a1;font-size:13px;margin:0 0 9px;">
                    Lay tu cac file da tai len o tab
                    <a href="/deployos/console">2.1 File boot</a>.</p>
                  <select name="file_boot">{opt}</select>
                </div>"""
            else:
                chon_file = """
                <div class="msg warn">Chua co file boot nao duoc tai len.
                Van chon OS binh thuong duoc - tai file sau o tab
                <a href="/deployos/console">2.1 File boot</a>.</div>"""

            return f"""
            <form method="POST" {act}>
              <div class="grid">{cot}</div>
              {chon_file}
              {_nut_dieu_huong(buoc)}
            </form>"""

        # -------------------------------------------- 1.1.3 thong tin OS
        if buoc == 3:
            if not d["os_ho"]:
                return ('<div class="msg warn">Chua chon he dieu hanh o buoc 2. '
                        f'<a href="/deployos/wizard/{ma}/2">Quay lai buoc 2</a>.</div>')
            la_linux = d["os_ho"] == "linux"
            o_ssh = ""
            if la_linux:
                ch = " checked" if d.get("ssh") else ""
                o_ssh = f"""
                <label class="chon" style="margin-top:14px;">
                  <input type="checkbox" name="ssh" value="1"{ch}>
                  <span class="t">Bat SSH ngay sau khi cai</span>
                  <div class="d">Cai san openssh-server va bat dich vu - vao
                  duoc may tu xa ngay, khong phai ra tan noi bat tay.</div>
                </label>"""

            opt_tz = ""
            for tz in MUI_GIO:
                s = " selected" if d["mui_gio"] == tz else ""
                opt_tz += f'<option value="{tz}"{s}>{tz}</option>'

            return f"""
            <form method="POST" {act}>
              <div class="card">
                <h3>Thong tin may se cai</h3>
                <label>Ten may (hostname)</label>
                <input type="text" name="ten_may" value="{_esc(d['ten_may'])}"
                       placeholder="vd: PC-KETOAN-01" autocapitalize="off">
                <label>Ten dang nhap (username)</label>
                <input type="text" name="username" value="{_esc(d['username'])}"
                       placeholder="vd: admin" autocapitalize="off">
                <label>Mat khau</label>
                <input type="password" name="password" value=""
                       placeholder="{'Da dat roi - de trong neu khong doi' if d['password'] else 'Mat khau cho tai khoan tren may do'}">
                <p style="color:#8b93a1;font-size:12.5px;margin:7px 0 0;">
                  Day la mat khau cho tai khoan SE TAO tren may dang cai lai,
                  khong phai mat khau cua Console Pi. Neu luu thanh kich ban,
                  file kich ban duoc de quyen chi root doc duoc (600).
                  {'<br>Da co mat khau - de trong o nay thi giu nguyen cai cu.' if d['password'] else ''}</p>
                <!-- O mat khau KHONG dien san gia tri cu: dien san thi mat
                     khau nam thang trong ma nguon trang, ai xem nguon (hoac
                     anh chup man hinh dev tools) deu doc duoc. -->

                <label>Mui gio</label>
                <select name="mui_gio">{opt_tz}</select>
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
                  <input type="text" name="pv_nhan" value="{_esc(p.get('nhan',''))}" placeholder="Nhan">
                  <input type="text" name="pv_cd" value="{_esc(p.get('cd',''))}" placeholder="MB hoac con_lai">
                  <select name="pv_fs">{opt_fs}</select>
                  <input type="text" name="pv_gan" value="{_esc(p.get('gan',''))}" placeholder="C: hoac /">
                  <button type="button" class="red small" onclick="this.parentNode.remove()">Xoa</button>
                </div>"""

            return f"""
            <form method="POST" {act}>
              <div class="card">
                <h3>Cach chia o dia</h3>
                <label class="chon">
                  <input type="radio" name="o_dia_che_do" value="tu_dong"{tu_dong_ch}>
                  <span class="t">Phan chia tu dong</span>
                  <div class="d">Dung o dia so 0 (o dau tien may nhin thay),
                  xoa sach va chia theo bo phan vung chuan cua he dieu hanh
                  da chon.</div>
                </label>
                <label class="chon">
                  <input type="radio" name="o_dia_che_do" value="chia_tay"{tay_ch}>
                  <span class="t">Chia bang tay</span>
                  <div class="d">Tu khai bao tung phan vung ben duoi. Dung khi
                  may co nhieu o cung, hoac muon chia them o D: de chua du lieu
                  rieng.</div>
                </label>
              </div>

              <div class="card">
                <h3>Thong so o dia</h3>
                <div class="row">
                  <div>
                    <label>O dia so</label>
                    <input type="number" name="o_dia_so" value="{_esc(d['o_dia_so'])}"
                           min="0" max="15" style="max-width:130px;">
                  </div>
                  <div>
                    <label>Bang phan vung</label>
                    <select name="o_dia_bang" style="max-width:260px;">
                      <option value="gpt"{' selected' if d['o_dia_bang'] == 'gpt' else ''}>GPT (may UEFI - hau het may tu 2012)</option>
                      <option value="mbr"{' selected' if d['o_dia_bang'] == 'mbr' else ''}>MBR (may BIOS doi cu)</option>
                    </select>
                  </div>
                </div>
                <div class="msg warn" style="margin-top:14px;">
                  <strong>Canh bao that:</strong> chia o dia la thao tac GHI DE -
                  toan bo du lieu tren o dia duoc chon se mat. Neu may co
                  nhieu o cung, kiem tra ky "o dia so" truoc khi chay.
                </div>
              </div>

              <div class="card">
                <h3>Danh sach phan vung (chi dung khi chon "chia bang tay")</h3>
                <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
                  Dung luong dien bang MB, hoac go <code>con_lai</code> de lay
                  het cho trong con lai. Cot cuoi la o/diem gan
                  ({'vd <code>/</code>, <code>/home</code>' if d['os_ho'] == 'linux' else 'vd <code>C:</code>, <code>D:</code>'}).
                  Voi Windows tren GPT bat buoc phai co phan vung <code>EFI</code>
                  va <code>MSR</code> - da dien san theo dung chuan.</p>
                <div id="pvbox">{hang}</div>
                <button type="button" class="gray small" onclick="themPV()">+ Them phan vung</button>
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
                <div class="msg warn">Chua co phan mem nao duoc tai len.
                Vao tab <a href="/deployos/console/apps">2.2 Phan mem</a> de
                tai file .msi/.exe len truoc, roi quay lai buoc nay.
                Bo qua buoc nay cung duoc - luc do may chi cai OS, khong cai
                them phan mem.</div>"""
            else:
                o = ""
                for a in ds:
                    ch = " checked" if a["ten"] in d["apps"] else ""
                    ts = (f'<code>{_esc(a["tham_so"])}</code>' if a["tham_so"]
                          else ('<span style="color:#8b93a1;">msiexec /quiet '
                                '(mac dinh cho .msi)</span>' if a["la_msi"]
                                else '<span style="color:#f59e0b;">chua dien '
                                     'tham so cai im lang</span>'))
                    o += f"""
                    <label class="chon">
                      <input type="checkbox" name="app" value="{_esc(a['ten'])}"{ch}>
                      <span class="t">{_esc(a['ten'])}</span>
                      <div class="d">{co_kich_thuoc(a['cd'])} &middot; tham so: {ts}</div>
                    </label>"""
                than = f'<div class="card"><h3>Chon phan mem se cai</h3>{o}</div>'

            return f"""
            <form method="POST" {act}>
              {than}
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
                khoi_script = f'<div class="card"><h3>Script chay sau khi cai xong</h3>{o}</div>'
            else:
                khoi_script = """
                <div class="msg warn">Chua co script nao. Tai len o tab
                <a href="/deployos/console/scripts">2.3 Script</a>
                (.bat / .ps1 / .cmd).</div>"""

            return f"""
            <form method="POST" {act}>
              {khoi_script}
              <div class="card">
                <h3>Lenh them (tuy chon)</h3>
                <p style="color:#8b93a1;font-size:13px;margin:0 0 9px;">
                  Moi dong 1 lenh, chay sau khi cai xong OS va phan mem.</p>
                <textarea name="lenh_them" style="max-width:none;"
                  placeholder="vd: powercfg /h off">{_esc(d['lenh_them'])}</textarea>
              </div>
              <div class="msg info">
                Danh sach cac tuy chinh san (tat cap nhat tu dong, doi ten
                mang, bat Remote Desktop...) se duoc bo sung o vong sau -
                anh Thoai va em se cung choi cu the tung muc.
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

        apps = ("<br>".join("&bull; " + _esc(a) for a in d["apps"])
                if d["apps"] else "<span style='color:#8b93a1;'>Khong cai them phan mem</span>")
        scripts = ("<br>".join("&bull; " + _esc(s) for s in d["scripts"])
                   if d["scripts"] else "<span style='color:#8b93a1;'>Khong co</span>")
        lenh = (f"<pre style='margin:6px 0 0;'>{_esc(d['lenh_them'])}</pre>"
                if d["lenh_them"] else "<span style='color:#8b93a1;'>Khong co</span>")

        bang = f"""
        <div class="card">
          <h3>Tong ket lua chon</h3>
          <table class="tt-bang">
            <tr><td>Kieu boot</td><td>{_esc(kieu_ten)}</td></tr>
            <tr><td>He dieu hanh</td><td>{_esc(os_ten)}</td></tr>
            <tr><td>File boot</td><td>{_esc(d['file_boot']) or "<span style='color:#8b93a1;'>Chua chon</span>"}</td></tr>
            <tr><td>Ten may</td><td>{_esc(d['ten_may'])}</td></tr>
            <tr><td>Tai khoan</td><td>{_esc(d['username'])}</td></tr>
            <tr><td>Mat khau</td><td>{'&bull;' * 8 + ' <span style="color:#8b93a1;">(da dat)</span>' if d['password'] else '<span style="color:#f59e0b;">Chua dat</span>'}</td></tr>
            <tr><td>SSH</td><td>{'Bat' if d.get('ssh') else ('Tat' if d['os_ho'] == 'linux' else '<span style="color:#8b93a1;">Khong ap dung cho Windows</span>')}</td></tr>
            <tr><td>Mui gio</td><td>{_esc(d['mui_gio'])}</td></tr>
            <tr><td>O dia</td><td>{o_dia}</td></tr>
            <tr><td>Phan mem</td><td>{apps}</td></tr>
            <tr><td>Script sau cai</td><td>{scripts}</td></tr>
            <tr><td>Lenh them</td><td>{lenh}</td></tr>
          </table>
        </div>"""

        sua_lai = f"""
        <div class="row" style="margin-top:4px;">
          <a class="btn gray" href="/deployos/wizard/{ma}/1">&larr; Sua lai tu buoc 1</a>
          <a class="btn gray" href="/deployos/wizard/{ma}/6">&larr; Quay lai buoc 6</a>
        </div>"""

        # --- che do LUU: dat ten kich ban ---
        if d.get("che_do") == "luu":
            thieu = _thieu_gi(d)
            canh = (f'<div class="msg warn">Van luu duoc, nhung con thieu: '
                    f'{_esc(", ".join(thieu))}.</div>' if thieu else "")
            return f"""
            {bang}
            {canh}
            <form method="POST" action="/deployos/kichban/luu/{ma}">
              <div class="card">
                <h3>Dat ten kich ban</h3>
                <label>Ten kich ban</label>
                <input type="text" name="ten" required
                       placeholder="vd: Win11 van phong + Chrome" autocapitalize="off">
                <p style="color:#8b93a1;font-size:12.5px;margin:8px 0 0;">
                  Kich ban se hien o tab <strong>1.2 Kich ban</strong> de chon
                  nhanh lan sau.</p>
                <div class="row" style="margin-top:16px;">
                  <button type="submit" data-busy="Dang luu...">Luu kich ban</button>
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
            <div class="msg ok">Tat ca dieu kien deu dat. Buoc chay that su
            (phat PXE + phuc vu file boot) se duoc noi vao o giai doan ke
            tiep - hien tai chua co duong nao thuc thi, nen nut duoi day chi
            luu lai lua chon chu chua khoi dong dich vu nao.</div>"""
            if du_dieu_kien else """
            <div class="msg warn"><strong>Chua the boot that.</strong> Nhung
            muc con thieu o tren phai lam xong truoc - phan lon nam trong
            giai doan ke tiep cua ke hoach
            (docs/ke-hoach-pxe-winpe-tu-dong-cai-windows.md). Lua chon cua
            anh khong mat: luu lai thanh kich ban de dung ngay khi phan boot
            that duoc bat.</div>""")

        return f"""
        {bang}
        <div class="card">
          <h3>Kiem tra san sang (doc trang thai that tren may)</h3>
          <table>{hang}</table>
        </div>
        {ket_luan}
        <form method="POST" action="/deployos/kichban/luu/{ma}">
          <div class="card">
            <h3>Luu lua chon nay thanh kich ban</h3>
            <label>Ten kich ban</label>
            <input type="text" name="ten" required
                   placeholder="vd: Win11 van phong + Chrome" autocapitalize="off">
            <div class="row" style="margin-top:14px;">
              <button type="submit" data-busy="Dang luu...">Luu thanh kich ban</button>
            </div>
          </div>
        </form>
        {sua_lai}"""

    def _thieu_gi(d):
        thieu = []
        if not d["os_ho"]:
            thieu.append("chua chon OS")
        if not d["ten_may"]:
            thieu.append("chua co ten may")
        if not d["username"]:
            thieu.append("chua co ten dang nhap")
        if not d["password"]:
            thieu.append("chua dat mat khau")
        if not d["file_boot"]:
            thieu.append("chua chon file boot")
        return thieu

    @app.route("/deployos/kichban/luu/<ma>", methods=["POST"])
    def deployos_luu_kichban(ma):
        d = _wizard_lay(ma)
        if d is None:
            return _het_han()
        cauhinh = {k: v for k, v in d.items() if not k.startswith("_")}
        cauhinh.pop("che_do", None)
        ok, msg = luu_kichban(cauhinh, request.form.get("ten", ""))
        ds = danh_sach_kichban()
        body = (_tabs("console", "kichban") + _msg(msg, ok) +
                _bang_kichban(ds, _esc) +
                '<div class="row" style="margin-top:8px;">'
                '<a class="btn" href="/deployos/console/kichban">Ve danh sach kich ban</a>'
                '<a class="btn gray" href="/deployos/boot">Sang tab Boot OS</a></div>')
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
                File lon mat vai phut. Se co thanh tien trinh bao ro dang toi dau.</span>
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
                <a class="btn small gray" href="{duong_tai}/{_esc(f['ten'])}">Tai ve</a>
                <form method="POST" action="{duong_xoa}" style="display:inline;"
                      onsubmit="return confirm('Xoa {_esc(f['ten'])}?');">
                  <input type="hidden" name="ten" value="{_esc(f['ten'])}">
                  <button type="submit" class="red small">Xoa</button>
                </form>
              </td>
            </tr>"""
        return f"""
        <div class="tbl-scroll"><table>
          <tr><th>Ten file</th><th style="width:110px;">Kich thuoc</th>
              <th style="width:140px;">Ngay tai len</th><th style="width:180px;">Thao tac</th></tr>
          {hang}
        </table></div>"""

    # ------------------------------------------------------ 2.1 file boot
    @app.route("/deployos/console")
    def deployos_console():
        return _trang_file_boot()

    def _trang_file_boot(msg="", ok=True):
        _don_file_do_dang(BOOT_DIR)
        ds = _liet_ke(BOOT_DIR, EXT_BOOT)
        ghi_chu = """
        <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
          Nhan anh cai dat (.iso/.wim/.esd/.img/.vhd) va bootloader iPXE
          (undionly.kpxe cho may BIOS doi cu, ipxe.efi cho may UEFI - tai tu
          <code>ipxe.org</code>). Anh WinPE (boot.wim) phai tao san tren 1 may
          Windows co Windows ADK - Pi khong tu tao duoc, chi luu va phuc vu.</p>"""
        body = (_tabs("console", "file") + _msg(msg, ok) +
                _khoi_tai_len("/deployos/console/file/len", "file boot", EXT_BOOT, ghi_chu, "file") +
                f"<h2>File boot dang co ({len(ds)})</h2>" +
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
          Nhan file cai dat .msi va .exe. Sau khi tai len, dien tham so cai
          IM LANG cho tung file o bang ben duoi (moi hang moi kieu:
          <code>/S</code>, <code>/silent</code>, <code>/verysilent</code>,
          <code>/quiet</code>...). File .msi thi khong bat buoc - mac dinh
          dung <code>msiexec /i &lt;file&gt; /quiet /norestart</code>.</p>"""

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
                             placeholder="{goi_y}" style="max-width:250px;">
                      <button type="submit" class="small gray">Luu</button>
                    </form>
                  </td>
                  <td>
                    <a class="btn small gray" href="/deployos/console/apps/tai/{_esc(a['ten'])}">Tai ve</a>
                    <form method="POST" action="/deployos/console/apps/xoa" style="display:inline;"
                          onsubmit="return confirm('Xoa {_esc(a['ten'])}?');">
                      <input type="hidden" name="ten" value="{_esc(a['ten'])}">
                      <button type="submit" class="red small">Xoa</button>
                    </form>
                  </td>
                </tr>"""
            bang = f"""
            <div class="tbl-scroll"><table>
              <tr><th>Phan mem</th><th style="width:340px;">Tham so cai im lang</th>
                  <th style="width:180px;">Thao tac</th></tr>
              {hang}
            </table></div>"""
        else:
            bang = '<p style="color:#8b93a1;">Chua co phan mem nao.</p>'

        body = (_tabs("console", "apps") + _msg(msg, ok) +
                _khoi_tai_len("/deployos/console/apps/len", "phan mem", EXT_APP, ghi_chu, "apps") +
                f"<h2>Phan mem dang co ({len(ds)})</h2>" + bang +
                """
                <div class="msg info">Cac file nay KHONG bao gio duoc chay tren
                chinh Console Pi - Pi chi luu va gui chung cho may dang duoc
                cai lai tai ve.</div>""")
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
          Nhan .bat, .cmd (Windows) va .ps1 (PowerShell). Cac script nay se
          chay TREN MAY DANG DUOC CAI sau khi cai xong OS va phan mem, khong
          chay tren Console Pi.</p>"""
        body = (_tabs("console", "scripts") + _msg(msg, ok) +
                _khoi_tai_len("/deployos/console/scripts/len", "script", EXT_SCRIPT, ghi_chu, "scripts") +
                f"<h2>Script dang co ({len(ds)})</h2>" +
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
              <td>{esc(_mo_ta_ngan(k))}</td>
              <td style="color:#8b93a1;">{esc(k.get('_ngay', ''))}</td>
              <td>
                <a class="btn small gray" href="/deployos/boot/dung-kichban/{esc(k['_file'])}">Dung</a>
                <form method="POST" action="/deployos/console/kichban/xoa" style="display:inline;"
                      onsubmit="return confirm('Xoa kich ban nay?');">
                  <input type="hidden" name="ten" value="{esc(k['_file'])}">
                  <button type="submit" class="red small">Xoa</button>
                </form>
              </td>
            </tr>"""
        return f"""
        <div class="tbl-scroll"><table>
          <tr><th>Ten kich ban</th><th>Tom tat</th>
              <th style="width:140px;">Ngay tao</th><th style="width:150px;">Thao tac</th></tr>
          {hang}
        </table></div>"""

    @app.route("/deployos/console/kichban")
    def deployos_console_kichban():
        ds = danh_sach_kichban()
        body = _tabs("console", "kichban") + f"""
        <div class="card">
          <h3>Tao kich ban moi</h3>
          <p style="color:#8b93a1;font-size:13.5px;margin:0 0 13px;">
            Di qua dung {SO_BUOC} buoc nhu tab Boot OS, buoc cuoi dat ten de
            luu lai. Lan sau chi can chon ten kich ban la co ngay toan bo
            lua chon.</p>
          <a class="btn" href="/deployos/wizard/bat-dau?che_do=luu">
            Tao kich ban moi &rarr;</a>
        </div>

        <h2>Kich ban da luu ({len(ds)})</h2>
        {_bang_kichban(ds, _esc)}"""
        return _trang(body, "Deployment OS", "2.4 - Kich ban")

    @app.route("/deployos/console/kichban/xoa", methods=["POST"])
    def deployos_kichban_xoa():
        ok, msg = xoa_kichban(request.form.get("ten", ""))
        ds = danh_sach_kichban()
        body = (_tabs("console", "kichban") + _msg(msg, ok) +
                f"<h2>Kich ban da luu ({len(ds)})</h2>" + _bang_kichban(ds, _esc))
        return _trang(body, "Deployment OS", "2.4 - Kich ban")

    return app


def _ten_os(d):
    for ho, ten_ho, ds in DANH_SACH_OS:
        if ho == d.get("os_ho"):
            for ban, ten_ban in ds:
                if ban == d.get("os_ban"):
                    return ten_ban
            return ten_ho
    return "Chua chon"


def _mo_ta_ngan(k):
    """Tom tat 1 dong cho bang danh sach kich ban."""
    phan = [_ten_os(k)]
    if k.get("ten_may"):
        phan.append(k["ten_may"])
    n_app = len(k.get("apps") or [])
    if n_app:
        phan.append(f"{n_app} phan mem")
    n_sc = len(k.get("scripts") or [])
    if n_sc:
        phan.append(f"{n_sc} script")
    return " - ".join(phan)
