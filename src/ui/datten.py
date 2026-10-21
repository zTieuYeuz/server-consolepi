# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Cach dat TEN MAY khi cai Windows qua mang (Deployment OS) - them 1.9.4.

VAN DE: kich ban chi co 1 ten may co dinh -> cai nhieu may bang cung 1 kich ban thi may nao cung
trung ten (khong gia nhap domain duoc, trang Tien trinh tron lan). 5 cach:

  co_dinh     Ten co dinh (nhu truoc) - dung cho 1 may.
  serial      Tien to + so serial cua may (SMBIOS), vd PC-5CG1234ABC. Serial do iPXE gui ve luc may chon
              kich ban (xem pxe.deployos_pxeboot_cs_may) -> server tinh san ten, ghi vao cs-may.cmd.
  csv         Danh sach doi chieu serial -> ten may (file CSV nguoi dung tai len; co file mau de tai).
              May khong co trong danh sach -> roi ve cach "serial".
  ngau_nhien  Tien to + chuoi ngau nhien (vd PC-K7Q2M9X), khong trung may khac dang cai.
  hoi         WinPE hien cua so cmd hoi ten, go xong bam Enter moi chay tiep (xem unattend.sinh_deploy_cmd).

Quy tac ten Windows (NetBIOS): chu khong dau, so, dau gach ngang; toi da 15 ky tu; khong chi toan so;
khong bat dau/ket thuc bang gach ngang.
"""
import csv
import io
import re
import secrets

CHE_DO = ("co_dinh", "serial", "csv", "ngau_nhien", "hoi")
TOI_DA = 15
TIENTO_TOI_DA = 8
MAX_DONG_CSV = 5000
MAX_BYTE_CSV = 512 * 1024
RE_TEN = re.compile(r"[A-Za-z0-9-]{1,15}")
# Serial "gia" ma nhieu hang de nguyen trong BIOS - coi nhu khong co.
_SERIAL_GIA = {"", "NONE", "DEFAULTSTRING", "TOBEFILLEDBYOEM", "NOTSPECIFIED", "SYSTEMSERIALNUMBER",
               "SERIALNUMBER", "UNKNOWN", "NA", "NULL", "123456789", "1234567890", "0123456789",
               "OEM", "SYSTEMSERIAL", "00000000", "0"}
_BANG_NGAU_NHIEN = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"   # bo I, O, 0, 1 cho de doc


def che_do_cua(d):
    c = (d or {}).get("ten_may_che_do") or "co_dinh"
    return c if c in CHE_DO else "co_dinh"


def la_dong(d):
    """True neu ten may KHONG co dinh trong kich ban (tinh luc may chon kich ban / luc cai)."""
    return che_do_cua(d) != "co_dinh"


def lam_sach(s):
    """Chi giu A-Z 0-9 (viet hoa) - dung de so khop serial va ghep ten."""
    return re.sub(r"[^A-Z0-9]", "", str(s or "").upper())


def tien_to_sach(s):
    t = re.sub(r"[^A-Za-z0-9-]", "", str(s or "").strip())[:TIENTO_TOI_DA]
    return t.strip("-")


def serial_hop_le(s):
    x = lam_sach(s)
    if x in _SERIAL_GIA or len(x) < 3:
        return False
    return len(set(x)) > 1          # toan 1 ky tu lap (0000000, FFFFFFF) = gia


def _mac_cuoi(mac):
    h = re.sub(r"[^0-9a-fA-F]", "", str(mac or "")).upper()
    return h[-6:] if len(h) >= 6 else ""


def _dep(ten):
    """Cat toi 15, bo gach ngang o hai dau, khong de toan so."""
    ten = ten[:TOI_DA].strip("-")
    if not ten or ten.isdigit():
        ten = ("PC-" + ten)[:TOI_DA].strip("-")
    return ten


def ghep(tien_to, phan):
    """tien_to + '-' + phan (phan bi cat tu DAU de giu duoi - duoi serial moi phan biet duoc may)."""
    tt = tien_to_sach(tien_to)
    phan = lam_sach(phan)
    if not tt:
        return _dep(phan[-TOI_DA:])
    cho = TOI_DA - len(tt) - 1
    if cho < 1:
        return _dep(tt)
    return _dep(f"{tt}-{phan[-cho:]}")


def ten_ngau_nhien(tien_to="PC", da_co=()):
    """Tien to + ngau nhien, khong trung cac ten trong da_co (khong phan biet hoa thuong)."""
    tt = tien_to_sach(tien_to) or "PC"
    cho = TOI_DA - len(tt) - 1
    if cho < 4:
        tt = tt[:TOI_DA - 5].strip("-") or "PC"
        cho = TOI_DA - len(tt) - 1
    n = min(7, cho)
    co = {str(x).upper() for x in da_co}
    ten = ""
    for _ in range(50):
        ten = tt + "-" + "".join(secrets.choice(_BANG_NGAU_NHIEN) for _ in range(n))
        if ten.upper() not in co:
            return ten
    return ten


def ten_theo_serial(tien_to, serial, mac=""):
    """(ten, ghi_chu). Serial khong dung duoc -> 6 so cuoi cua MAC (ghi chu noi ro)."""
    if serial_hop_le(serial):
        return ghep(tien_to or "PC", serial), ""
    m = _mac_cuoi(mac)
    if m:
        return ghep(tien_to or "PC", m), "máy không có serial hợp lệ, dùng 6 số cuối MAC"
    return ten_ngau_nhien(tien_to or "PC"), "máy không có serial và không biết MAC, dùng tên ngẫu nhiên"


# ----------------------------------------------------------------- CSV doi chieu
def mau_csv():
    """File CSV mau de nguoi dung tai ve (UTF-8 co BOM de Excel mo dung)."""
    dong = ["serial,ten_may",
            "5CG1234ABC,PC-KETOAN-01",
            "5CG1234ABD,PC-KETOAN-02",
            "PF2XYZ77,PC-KHO-01"]
    return "﻿" + "\r\n".join(dong) + "\r\n"


def kiem_tra_ten(ten):
    """Quy tac dat ten may cua Microsoft (NetBIOS): '' neu hop le, nguoc lai cau giai thich loi."""
    if len(ten) > TOI_DA:
        return f"dài {len(ten)} ký tự, tối đa {TOI_DA}"
    if not ten:
        return "tên trống"
    sai = sorted({c for c in ten if not re.fullmatch(r"[A-Za-z0-9-]", c)})
    if sai:
        return "có ký tự không được phép (" + " ".join(repr(c)[1:-1] if c != " " else "dấu cách" for c in sai[:5]) + "): chỉ dùng chữ không dấu, số, dấu -"
    if ten.startswith("-") or ten.endswith("-"):
        return "không được bắt đầu hoặc kết thúc bằng dấu -"
    if ten.isdigit():
        return "không được chỉ toàn số"
    return ""


def doc_csv(raw):
    """
    Doc CSV (serial,ten_may) va KIEM TRA nghiem theo quy tac ten may cua Microsoft.
    Tra ve (ds, loi, canh_bao): ds = {serial_viet_hoa_chi_chu_so: ten}; `loi` = loi CHAN (co loi la khong
    nap file: dong sai ten, thieu cot, hai may cung ten); `canh_bao` = nhac nhe (serial lap, bo bot dong).
    Chap nhan dau phay / cham phay / tab, co hoac khong co dong tieu de, UTF-8 (co/khong BOM) hoac ANSI.
    """
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    loi, canh_bao = [], []
    if len(raw) > MAX_BYTE_CSV:
        return {}, [f"File quá lớn (tối đa {MAX_BYTE_CSV // 1024} KB)."], canh_bao
    try:
        van_ban = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        van_ban = raw.decode("cp1258", errors="replace")
    mau = van_ban[:2000]
    dau = max((",", ";", "\t"), key=lambda c: mau.count(c))
    ds, dong_cua = {}, {}
    for so, dong in enumerate(csv.reader(io.StringIO(van_ban), delimiter=dau), 1):
        if not dong or not any(c.strip() for c in dong):
            continue
        if len(ds) >= MAX_DONG_CSV:
            canh_bao.append(f"Quá {MAX_DONG_CSV} dòng, bỏ phần còn lại.")
            break
        a = dong[0].strip()
        b = dong[1].strip() if len(dong) > 1 else ""
        if so == 1 and a.lower().replace(" ", "").replace("_", "") in ("serial", "serialnumber", "sn", "soserial"):
            continue                       # dong tieu de
        if not a or not b:
            loi.append(f"Dòng {so}: thiếu serial hoặc tên máy.")
            continue
        k = lam_sach(a)
        if not k:
            loi.append(f"Dòng {so}: serial \"{a[:20]}\" không hợp lệ.")
            continue
        v = kiem_tra_ten(b)
        if v:
            loi.append(f"Dòng {so}: tên máy \"{b[:24]}\" {v}.")
            continue
        if k in ds and ds[k] != b:
            canh_bao.append(f"Dòng {so}: serial {a} bị lặp, lấy tên máy ở dòng này ({b}).")
        ds[k] = b
        dong_cua[k] = so
    theo_ten = {}
    for k, v in ds.items():
        theo_ten.setdefault(v.upper(), []).append(k)
    for v, ks in theo_ten.items():
        if len(ks) > 1:
            loi.append(f"Tên máy {v} bị gán cho {len(ks)} serial khác nhau (dòng " + ", ".join(str(dong_cua[k]) for k in ks[:5])
                       + ") - các máy đó sẽ trùng tên.")
    return ds, loi, canh_bao


# ----------------------------------------------------------------- tinh ten khi may chon kich ban
def tinh_ten(kb, serial="", mac="", da_co=()):
    """
    Tra ve (ten, ghi_chu) cho che do tinh san tren server; (None, "") neu khong tinh o day
    (co_dinh: dung ten trong kich ban; hoi: WinPE hoi nguoi dung).
    """
    c = che_do_cua(kb)
    if c == "serial":
        return ten_theo_serial(kb.get("ten_may_tiento", ""), serial, mac)
    if c == "csv":
        k = lam_sach(serial)
        ten = (kb.get("ten_may_csv") or {}).get(k) if serial_hop_le(serial) else None
        if ten and RE_TEN.fullmatch(ten):
            return ten, ""
        ten, gc = ten_theo_serial("PC", serial, mac)      # may ngoai danh sach: PC-<serial> (khong trung)
        return ten, ("serial " + (k or "(trống)") + " không có trong danh sách CSV, dùng PC + serial"
                     + (f" ({gc})" if gc else ""))
    if c == "ngau_nhien":
        return ten_ngau_nhien(kb.get("ten_may_tiento_ngau", ""), da_co), ""
    return None, ""


def mo_ta(d):
    """Mo ta ngan hien o trang tong ket / danh sach kich ban."""
    c = che_do_cua(d)
    if c == "serial":
        return f"{tien_to_sach(d.get('ten_may_tiento')) or 'PC'}-<số serial>"
    if c == "csv":
        n = len(d.get("ten_may_csv") or {})
        return f"theo danh sách CSV ({n} máy), máy ngoài danh sách: PC-<số serial>"
    if c == "ngau_nhien":
        return f"{tien_to_sach(d.get('ten_may_tiento_ngau')) or 'PC'}-<ngẫu nhiên>"
    if c == "hoi":
        return "hỏi khi bật máy cài"
    return d.get("ten_may") or ""
