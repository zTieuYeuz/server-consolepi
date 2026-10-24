# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Trien khai phan mem - LOP DU LIEU (may, nhom may, tai khoan ma hoa, nhom tai nguyen, lich, kich ban).

Moi kho la 1 file JSON trong /var/lib/console-pi/trienkhai/, ghi nguyen tu (tam + os.replace) va co khoa luong.

TAI KHOAN QUAN TRI (mat khau admin may dich): can luu lai vi kich ban "chay mai" va lich hen phai tu dang nhap
khi khong co nguoi ngoi truoc may. Ma hoa bang Fernet (AES-128-CBC + HMAC) voi khoa rieng cua thiet bi
`.khoa` (quyen 0600, sinh lan dau). THANH THAT: khoa nam cung o dia nen chi chan duoc viec doc lo file du lieu /
ban sao luu; ai la root tren thiet bi van giai ma duoc - khong co cach nao tranh duoc voi tinh nang tu chay.
Mat khau KHONG BAO GIO tra ve giao dien, khong ghi nhat ky.
"""
import calendar
import json
import os
import threading
import time
import uuid
from datetime import date, datetime, timedelta

from .duongdan import THU_MUC_DU_LIEU

DIR = os.path.join(THU_MUC_DU_LIEU, "trienkhai")
_KHOA_FILE = os.path.join(DIR, ".khoa")
_khoa_luong = threading.RLock()
THU = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]


def _bao_dam():
    os.makedirs(DIR, mode=0o750, exist_ok=True)


class Kho:
    """1 danh sach (list) hoac tu dien (dict) luu o 1 file JSON."""

    def __init__(self, ten, mac_dinh):
        self.duong = os.path.join(DIR, ten)
        self.mac_dinh = mac_dinh

    def doc(self):
        with _khoa_luong:
            try:
                with open(self.duong, encoding="utf-8") as f:
                    d = json.load(f)
                    if isinstance(d, type(self.mac_dinh)):
                        return d
            except (OSError, ValueError):
                pass
            return type(self.mac_dinh)()

    def ghi(self, d):
        with _khoa_luong:
            _bao_dam()
            tam = self.duong + ".tmp"
            with open(tam, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=1)
            os.replace(tam, self.duong)

    def sua(self, ham):
        """doc -> ham(d) (sua tai cho) -> ghi. Tra ve gia tri ham tra."""
        with _khoa_luong:
            d = self.doc()
            kq = ham(d)
            self.ghi(d)
            return kq


MAY = Kho("may.json", [])               # [{id, ten, ip, mac, ghi_chu, bao_mat:{...}}]
NHOM_MAY = Kho("nhom_may.json", [])     # [{id, ten, may:[id,...]}]
TAI_KHOAN = Kho("tai_khoan.json", [])   # [{id, ten, user, mk}]  mk = chuoi Fernet
NHOM_TN = Kho("nhom_tn.json", [])       # [{id, ten, muc:[{loai, ref, ten}]}]
LICH = Kho("lich.json", [])             # [{id, ten, kieu, gio, ...}]
KICH_BAN = Kho("kich_ban.json", [])     # [{id, ten, buoc:[...], nhom_may:[id], may:[id], lich_id, tai_khoan_id}]
TRANG_THAI = Kho("chay.json", {})       # {kb_id: {...}}


def moi_id():
    return uuid.uuid4().hex[:10]


def tim(ds, id_):
    return next((x for x in ds if x.get("id") == id_), None)


# ----------------------------------------------------------------- ma hoa mat khau
def _fernet():
    from cryptography.fernet import Fernet
    with _khoa_luong:
        _bao_dam()
        if not os.path.exists(_KHOA_FILE):
            fd = os.open(_KHOA_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(Fernet.generate_key())
        with open(_KHOA_FILE, "rb") as f:
            return Fernet(f.read().strip())


def ma_hoa(s):
    return _fernet().encrypt((s or "").encode("utf-8")).decode("ascii")


def giai_ma(s):
    try:
        return _fernet().decrypt((s or "").encode("ascii")).decode("utf-8")
    except Exception:
        return ""


def tai_khoan_cong_khai():
    """Danh sach tai khoan KHONG kem mat khau (cho giao dien)."""
    return [{"id": t["id"], "ten": t["ten"], "user": t["user"]} for t in TAI_KHOAN.doc()]


def lay_tai_khoan(tk_id):
    """(user, mat_khau) hoac (None, None). Chi dung trong luong chay, khong tra ra ngoai."""
    t = tim(TAI_KHOAN.doc(), tk_id)
    return (t["user"], giai_ma(t["mk"])) if t else (None, None)


# ----------------------------------------------------------------- lich
def chuan_lich(f):
    """Tu form -> dict lich da kiem tra. Tra ve (lich, loi)."""
    kieu = f.get("kieu", "")
    if kieu not in ("mot_lan", "hang_ngay", "hang_tuan", "hang_thang", "hang_nam"):
        return None, "Chọn kiểu lặp lại."
    gio = (f.get("gio") or "").strip()
    try:
        h, m = gio.split(":")
        if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
            raise ValueError
    except ValueError:
        return None, "Giờ không hợp lệ, viết kiểu 08:30."
    l = {"kieu": kieu, "gio": f"{int(h):02d}:{int(m):02d}"}
    try:
        if kieu == "mot_lan":
            l["ngay"] = date.fromisoformat((f.get("ngay") or "").strip()).isoformat()
        elif kieu == "hang_tuan":
            thu = sorted({int(x) for x in (f.getlist("thu") if hasattr(f, "getlist") else f.get("thu", [])) if str(x).isdigit() and 0 <= int(x) <= 6})
            if not thu:
                return None, "Chọn ít nhất một ngày trong tuần."
            l["thu"] = thu
        elif kieu in ("hang_thang", "hang_nam"):
            l["ngay_thang"] = max(1, min(31, int(f.get("ngay_thang") or 0)))
            if kieu == "hang_nam":
                l["thang"] = max(1, min(12, int(f.get("thang") or 0)))
        for k in ("tu_ngay", "den_ngay"):
            v = (f.get(k) or "").strip()
            if v:
                l[k] = date.fromisoformat(v).isoformat()
    except (ValueError, TypeError):
        return None, "Ngày không hợp lệ."
    return l, ""


def mo_ta_lich(l):
    if not l:
        return "Chạy ngay khi bấm Chạy"
    k, g = l.get("kieu"), l.get("gio", "")
    if k == "mot_lan":
        d = date.fromisoformat(l["ngay"])
        s = f"Một lần, {g} ngày {d.day:02d}/{d.month:02d}/{d.year}"
    elif k == "hang_ngay":
        s = f"Hằng ngày lúc {g}"
    elif k == "hang_tuan":
        s = "Hằng tuần, " + ", ".join(THU[i] for i in l.get("thu", [])) + f" lúc {g}"
    elif k == "hang_thang":
        s = f"Hằng tháng, ngày {l.get('ngay_thang')} lúc {g}"
    else:
        s = f"Hằng năm, ngày {l.get('ngay_thang')}/{l.get('thang')} lúc {g}"
    if l.get("tu_ngay") or l.get("den_ngay"):
        s += " (" + (f"từ {l['tu_ngay']}" if l.get("tu_ngay") else "") + (" " if l.get("tu_ngay") and l.get("den_ngay") else "") \
             + (f"đến {l['den_ngay']}" if l.get("den_ngay") else "") + ")"
    return s


def _khop_ngay(l, d):
    k = l["kieu"]
    if l.get("tu_ngay") and d < date.fromisoformat(l["tu_ngay"]):
        return False
    if l.get("den_ngay") and d > date.fromisoformat(l["den_ngay"]):
        return False
    if k == "mot_lan":
        return d == date.fromisoformat(l["ngay"])
    if k == "hang_ngay":
        return True
    if k == "hang_tuan":
        return d.weekday() in l.get("thu", [])
    cuoi = calendar.monthrange(d.year, d.month)[1]
    if k == "hang_thang":
        return d.day == min(l.get("ngay_thang", 1), cuoi)
    return d.month == l.get("thang") and d.day == min(l.get("ngay_thang", 1), cuoi)


def _gio_phut(l):
    h, m = l["gio"].split(":")
    return int(h), int(m)


def lan_hen_gan_nhat(l, bay_gio=None):
    """Thoi diem hen GAN NHAT da toi (<= bay_gio) hoac None."""
    bay_gio = bay_gio or datetime.now()
    h, m = _gio_phut(l)
    gioi_han = 1 if l["kieu"] == "mot_lan" else (400 if l["kieu"] == "hang_nam" else 70)
    cac = [date.fromisoformat(l["ngay"])] if l["kieu"] == "mot_lan" else \
          [bay_gio.date() - timedelta(days=i) for i in range(gioi_han)]
    for d in cac:
        if _khop_ngay(l, d):
            t = datetime(d.year, d.month, d.day, h, m)
            if t <= bay_gio:
                return t
    return None


def lan_hen_ke_tiep(l, bay_gio=None):
    bay_gio = bay_gio or datetime.now()
    h, m = _gio_phut(l)
    for i in range(0, 800):
        d = bay_gio.date() + timedelta(days=i)
        if _khop_ngay(l, d):
            t = datetime(d.year, d.month, d.day, h, m)
            if t > bay_gio:
                return t
        if l["kieu"] != "hang_nam" and i > 70:
            break
    return None


def dinh_dang_gio(t):
    return time.strftime("%d/%m/%Y %H:%M", time.localtime(t)) if t else ""
