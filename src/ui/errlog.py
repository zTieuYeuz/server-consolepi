# Console System - (c) 2026 zTieuYeuz. All rights reserved.
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
  - XOAY VONG: KHONG tu xoay vong o day. Chi ghi them (append) don gian;
    viec xoay vong + giu 7 NGAY (yeu cau 27/09/2026: moi nhat ky chi giu 7
    ngay) giao het cho logrotate (config/logrotate-console-pi) - MOT co che
    duy nhat, tranh xung dot.
"""
import glob
import gzip
import os
import re
import subprocess
import time
import traceback

THU_MUC_LOG = "/var/log"
LOG_FILE = os.path.join(THU_MUC_LOG, "console-pi-errors.log")
# Nhat ky THAO TAC (19/10/2026): ai lam gi - dang nhap thanh cong / that bai, tat may, bat tat PXE...
# Khac nhat ky loi: day la dau vet hanh dong de truy lai khi can, khong phai loi phan mem.
LOG_THAO_TAC = os.path.join(THU_MUC_LOG, "console-pi-audit.log")

# Cac dich vu CHINH cua Console Pi - dung cho trang /logs doc nhanh journal
# rieng cho tung dich vu, khong phai doc ca he thong.
DICH_VU_CAN_THEO_DOI = [
    "console-pi-dashboard", "console-pi-tunnel", "console-pi-term-local",
    "console-pi-term-ssh", "console-pi-term-phien", "bluetooth", "bt-agent", "bt-nap", "nginx",
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


def doc_file_xoay_vong(duong, so_giay=7 * 86400):
    """
    Doc 1 file log CA CAC BAN DA XOAY VONG (.1 .. .7, .N.gz) con trong khoang thoi gian, cu truoc moi sau,
    tra ve list dong. LOI THAT 19/10/2026: tab "Loi ung dung" chi doc file HIEN TAI; logrotate chay luc 00:31
    lam file hien tai thanh 0 byte, toan bo loi cua may ngay truoc bien mat khoi tab dung luc can xem
    (du van con trong ban .1). Dung chung ham nay cho moi cho doc log de khong lap lai loi do.
    """
    cac = [(0, duong)] + [(i, f"{duong}.{i}") for i in range(1, 8)] + [(i, f"{duong}.{i}.gz") for i in range(1, 8)]
    moc = time.time() - so_giay
    ds = []
    for chi_so, p in cac:
        try:
            if os.path.getmtime(p) < moc:
                continue
            mo = gzip.open if p.endswith(".gz") else open
            with mo(p, "rt", encoding="utf-8", errors="replace") as f:
                ds.append((chi_so, re.sub(r"\x1b\[[0-9;]*m", "", f.read()).splitlines()))
        except OSError:
            continue
    dong = []
    # Thu tu THEO CHI SO XOAY VONG (.7 cu nhat ... .1 ... file hien tai moi nhat), KHONG theo mtime:
    # mtime cua hai file xoay vong sat nhau co the bang nhau (do phan giai he thong file) lam sai thu tu.
    for _, d in sorted(ds, key=lambda x: -x[0]):
        dong.extend(d)
    return dong


def doc_nhat_ky(so_dong=300, duong=None, so_giay=7 * 86400):
    """Doc N dong CUOI CUNG cua nhat ky loi trong 7 ngay (ca file da xoay vong), moi nhat o duoi cung."""
    try:
        dong = doc_file_xoay_vong(duong or LOG_FILE, so_giay)
        return "\n".join(dong[-so_dong:]) + ("\n" if dong else "")
    except Exception as e:
        return f"(không đọc được nhật ký: {e})"


def ghi_thao_tac(hanh_dong, chi_tiet="", nguoi=None, ip=None):
    """
    Ghi 1 dong vao nhat ky THAO TAC: "thoi gian | nguoi @ IP | hanh dong | chi tiet".
    Tu lay nguoi dung + dia chi may tu yeu cau Flask dang xu ly neu khong truyen vao. KHONG BAO GIO ghi
    mat khau. Loi ghi file thi im lang bo qua - khong duoc lam sap chuc nang chinh.
    """
    try:
        if nguoi is None or ip is None:
            try:
                from flask import request, session
                nguoi = nguoi if nguoi is not None else (session.get("user") or "-")
                ip = ip if ip is not None else (request.remote_addr or "-")
            except Exception:
                nguoi, ip = nguoi or "-", ip or "-"
        dong = (f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {nguoi}@{ip} | {hanh_dong}"
                + (f" | {chi_tiet}" if chi_tiet else ""))
        dong = dong.replace("\r", " ").replace("\n", " ")[:400]
        with open(LOG_THAO_TAC, "a", encoding="utf-8") as f:
            f.write(dong + "\n")
    except Exception:
        pass


# Cac thao tac POST KHONG ghi (da co dong ghi rieng chi tiet hon, hoac chay thuong xuyen/khong phai thao tac cua nguoi dung)
_KHONG_GHI = ("/login", "/logout", "/power/", "/deployos/pxe/bat", "/deployos/pxe/tat", "/phien/api/", "/api/",
              "/tai-len/", "/giaodien", "/_auth", "/healthz")
_TRUONG_AN_TOAN = ("ten", "id", "ma", "bo_id", "os_id", "ung_id", "ten_may", "dev", "devname", "loai", "nguon")


def ghi_thao_tac_tu_dong(request, response):
    """
    after_request: moi thao tac GHI (POST) thanh cong cua nguoi dung -> 1 dong nhat ky thao tac
    ("POST /deployos/kichban/xoa -> 200 | ten=Cai-moi"). Chi ghi cac truong dinh danh doi tuong (ten, id...)
    cat ngan - KHONG ghi gia tri truong khac nen khong lo lo mat khau / token.
    """
    try:
        if request.method != "POST" or response.status_code >= 400:
            return
        duong = request.path
        if any(duong.startswith(x) for x in _KHONG_GHI):
            return
        ct = []
        for k in _TRUONG_AN_TOAN:
            v = (request.form.get(k) or "").strip()
            if v:
                ct.append(f"{k}={v[:60]}")
        ghi_thao_tac(f"POST {duong}", " ".join(ct) + (f" -> {response.status_code}" if response.status_code != 200 else ""))
    except Exception:
        pass


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
        return r.stdout.strip() or "(không có cảnh báo/lỗi nào gần đây)"
    except Exception as e:
        return f"(không đọc được journal: {e})"
