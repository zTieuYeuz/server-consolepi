"""
Console Pi - Nhat ky loi tap trung

VI SAO CAN: truoc day moi loi Python khong duoc bat rieng (unhandled
exception trong 1 route Flask) chi hien 1 trang loi chung chung tren trinh
duyet roi BIEN MAT - khong con dau vet nao de xem lai SAU KHI su co da qua.
Ngoai hien truong (cong ty, mang la) nguoi dung khong the goi ai hoi ngay
luc do; can 1 cho de tu xem lai "luc nay co loi gi khong" bat cu khi nao,
khong can nho lenh journalctl.

File nay:
  - `ghi_loi()`  : goi tu bat ky dau trong app de ghi 1 dong loi, kem
                   traceback day du neu co.
  - `doc_nhat_ky()`: doc lai de hien tren trang web /logs.
  - XOAY VONG: KHONG con tu xoay vong o day (truoc dung RotatingFileHandler
    cua Python). Ly do doi: yeu cau thuc te la giu it nhat 60 NGAY cho moi
    nhat ky cua Console Pi (dung o hien truong khong SSH duoc, phai doi ve
    nha moi xem lai). RotatingFileHandler chi xoay theo DUNG LUONG (2MB) -
    khong dam bao thoi gian, ngay bi loi lap lai nhieu co the xoa mat du
    lieu cu chi trong vai gio. Nay chi ghi them (append) don gian; viec
    xoay vong + giu 60 ngay giao het cho logrotate (xem
    config/logrotate-console-pi) - MOT co che duy nhat, tranh xung dot.
"""
import subprocess
import time
import traceback

LOG_FILE = "/var/log/console-pi-errors.log"

# Cac dich vu CHINH cua Console Pi - dung cho trang /logs doc nhanh journal
# rieng cho tung dich vu, khong phai doc ca he thong.
DICH_VU_CAN_THEO_DOI = [
    "console-pi-dashboard", "console-pi-tunnel", "console-pi-term-local",
    "console-pi-term-ssh", "bluetooth", "bt-agent", "bt-nap", "nginx",
]


def ghi_loi(nguon, thong_diep, ngoai_le=None):
    """
    Ghi 1 dong loi vao nhat ky tap trung.

    nguon      : noi xay ra loi (vd duong dan route "/nettools/ping")
    thong_diep : mo ta ngan gon, de doc luot qua
    ngoai_le   : doi tuong Exception (neu co) - se ghi kem traceback day du
                 de con dieu tra sau, khong chi 1 dong mo ta suong
    """
    dong = f"{time.strftime('%Y-%m-%d %H:%M:%S')} | [{nguon}] {thong_diep}"
    if ngoai_le is not None:
        try:
            dong += "\n" + "".join(traceback.format_exception(
                type(ngoai_le), ngoai_le, ngoai_le.__traceback__))
        except Exception:
            pass
    try:
        # copytruncate cua logrotate co the cat file giua luc ghi - "a" mo
        # lai file moi lan goi (khong giu handle mo lau dai) nen luon ghi
        # dung vao file HIEN TAI, khong bao gio ghi lac vao ban da xoay vong.
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(dong + "\n")
    except Exception:
        # Khong ghi duoc file (vd quyen, dia day) thi TUYET DOI khong duoc
        # lam sap ung dung chinh - im lang bo qua, ung dung van chay tiep.
        pass


def doc_nhat_ky(so_dong=300):
    """Doc N dong CUOI CUNG cua nhat ky loi (moi nhat o duoi cung)."""
    try:
        with open(LOG_FILE, encoding="utf-8", errors="replace") as f:
            dong = f.readlines()
        return "".join(dong[-so_dong:])
    except FileNotFoundError:
        return ""
    except Exception as e:
        return f"(khong doc duoc nhat ky: {e})"


def doc_journal_dich_vu(ten_dich_vu, so_dong=60):
    """
    Doc N dong journal GAN NHAT cua 1 dich vu systemd - chi bao gom
    canh bao/loi (loc theo `-p warning`) de khong bi nhieu boi cac dong
    thong bao binh thuong (vd "GET / 200").
    """
    try:
        r = subprocess.run(
            ["journalctl", "-u", ten_dich_vu, "-p", "warning", "-n", str(so_dong),
             "--no-pager", "-o", "short-iso"],
            capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or "(khong co canh bao/loi nao gan day)"
    except Exception as e:
        return f"(khong doc duoc journal: {e})"
