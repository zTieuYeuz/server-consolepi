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
  - Tu dong XOAY VONG file (RotatingFileHandler) - khong de file phinh to
    vo han qua nhieu thang dung ngoai hien truong, la nguyen nhan hay bi
    quen trong cac du an nho.
"""
import logging
import logging.handlers
import subprocess
import traceback

LOG_FILE = "/var/log/console-pi-errors.log"

# Cac dich vu CHINH cua Console Pi - dung cho trang /logs doc nhanh journal
# rieng cho tung dich vu, khong phai doc ca he thong.
DICH_VU_CAN_THEO_DOI = [
    "console-pi-dashboard", "console-pi-tunnel", "console-pi-term-local",
    "console-pi-term-ssh", "bluetooth", "bt-agent", "bt-nap", "nginx",
]

_logger = logging.getLogger("console_pi_errors")
_logger.setLevel(logging.ERROR)
if not _logger.handlers:
    try:
        # 2MB x 3 ban cu = toi da ~8MB - du de xem lai vai tuan ma khong so
        # lo day the SD (loai the thuong dung cho Pi chi 8-32GB).
        _handler = logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8")
        _handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        _logger.addHandler(_handler)
    except Exception:
        # Khong ghi duoc file (vd quyen, dia day) thi TUYET DOI khong duoc
        # lam sap ung dung chinh - im lang bo qua, ung dung van chay tiep.
        pass


def ghi_loi(nguon, thong_diep, ngoai_le=None):
    """
    Ghi 1 dong loi vao nhat ky tap trung.

    nguon      : noi xay ra loi (vd duong dan route "/nettools/ping")
    thong_diep : mo ta ngan gon, de doc luot qua
    ngoai_le   : doi tuong Exception (neu co) - se ghi kem traceback day du
                 de con dieu tra sau, khong chi 1 dong mo ta suong
    """
    dong = f"[{nguon}] {thong_diep}"
    if ngoai_le is not None:
        try:
            dong += "\n" + "".join(traceback.format_exception(
                type(ngoai_le), ngoai_le, ngoai_le.__traceback__))
        except Exception:
            pass
    try:
        _logger.error(dong)
    except Exception:
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
