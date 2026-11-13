#!/usr/bin/env python3
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""tftp-chay: chay in.tftpd chi tren cac dia chi da chon, tu tat khi nhan roi, chan day the (2.0.8 V5-2).
Doc cau hinh do dashboard ghi (CS_TFTP_CAU_HINH, mac dinh /run/console-system-tftp.json):
  {"dia_chi": ["192.168.1.5", ...], "goc": "<thu muc>"}
Moi dia chi mot tien trinh in.tftpd (in.tftpd chi bind duoc 1 dia chi). Ghi trang thai ra CS_TFTP_TRANG_THAI de trang web hien: dang nghe, con bao lau.
NHAN ROI = khong co ket noi TFTP dang chep VA khong co thay doi file trong thu muc VA khong bam 'gia han' trong NHAN_ROI giay.
Thoat 0 khi tu tat (systemd khong khoi dong lai); ExecStopPost cua don vi xoa co /run."""
import ipaddress
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time

CAU_HINH = os.environ.get("CS_TFTP_CAU_HINH", "/run/console-system-tftp.json")
TRANG_THAI = os.environ.get("CS_TFTP_TRANG_THAI", "/run/console-system-tftp.trangthai.json")
GIA_HAN = os.environ.get("CS_TFTP_GIA_HAN", "/run/console-system-tftp.giahan")
NHAN_ROI = int(os.environ.get("CS_TFTP_NHAN_ROI", "3600"))
TOI_DA_BYTE = int(os.environ.get("CS_TFTP_TOI_DA", str(1024 ** 3)))          # tong dung luong thu muc TFTP
CON_TRONG_TOI_THIEU = 200 * 1024 ** 2                                       # the con it hon thi dung ghi
NHIP = float(os.environ.get("CS_TFTP_NHIP", "20"))
TFTPD = os.environ.get("CS_TFTPD", "/usr/sbin/in.tftpd")
MAU_IP = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


def dia_chi_hop_le(ds):
    ra = []
    for a in ds or []:
        if isinstance(a, str) and MAU_IP.match(a) and all(0 <= int(x) <= 255 for x in a.split(".")) and not ipaddress.ip_address(a).is_unspecified:
            ra.append(a)
    return ra


def lenh_tftpd(dia_chi, goc):
    return [TFTPD, "--foreground", "--user", "tftp", "--address", "%s:69" % dia_chi, "--secure", "--create", goc]


def dang_chep(ss_out):
    """Co ket noi TFTP dang chep khong? Moi giao dich cua in.tftpd mo mot socket UDP rieng (cong khac 69)."""
    for dong in ss_out.splitlines():
        if "in.tftpd" in dong:
            noi_bo = next((c for c in dong.split() if ":" in c and not c.startswith("users:")), "")     # cot dia chi noi bo (co/khong cot Netid)
            if not noi_bo.endswith(":69"):
                return True
    return False


def dung_luong(goc):
    tong, moi_nhat = 0, 0.0
    try:
        moi_nhat = os.stat(goc).st_mtime
        for e in os.scandir(goc):
            try:
                st = e.stat(follow_symlinks=False)
            except OSError:
                continue
            tong += st.st_size
            moi_nhat = max(moi_nhat, st.st_mtime)
    except OSError:
        pass
    return tong, moi_nhat


def quyet_dinh(bay_gio, hoat_dong_cuoi, tong_byte, con_trong, toi_da=TOI_DA_BYTE, nhan_roi=NHAN_ROI):
    """None = tiep tuc; chuoi = ly do tu tat."""
    if tong_byte > toi_da:
        return "Thư mục TFTP vượt giới hạn dung lượng (%d MB) - đã tự tắt để không đầy thẻ nhớ" % (toi_da // 1024 ** 2)
    if con_trong < CON_TRONG_TOI_THIEU:
        return "Thẻ nhớ gần đầy - đã tự tắt TFTP"
    if bay_gio - hoat_dong_cuoi >= nhan_roi:
        return "Nhàn rỗi %d phút - đã tự tắt TFTP" % (nhan_roi // 60)
    return None


def ghi_trang_thai(nghe, het_han, ly_do=""):
    tmp = TRANG_THAI + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"nghe": nghe, "het_han": het_han, "ly_do_tat": ly_do, "cap_nhat": time.time()}, f)
    os.replace(tmp, TRANG_THAI)


def main():
    try:
        ch = json.load(open(CAU_HINH, encoding="utf-8"))
    except (OSError, ValueError):
        print("tftp-chay: khong doc duoc cau hinh", file=sys.stderr)
        return 1
    ds = dia_chi_hop_le(ch.get("dia_chi"))
    goc = ch.get("goc") or ""
    if not ds or not os.path.isdir(goc):
        print("tftp-chay: thieu dia chi nghe hoac thu muc goc", file=sys.stderr)
        return 1
    procs = [subprocess.Popen(lenh_tftpd(a, goc)) for a in ds]      # nosec B603 - dia chi da kiem tra, argv list
    dung = []
    signal.signal(signal.SIGTERM, lambda *_: dung.append("term"))
    hoat_dong = time.time()
    moi_nhat_cu = dung_luong(goc)[1]
    ly_do = ""
    try:
        while not dung:
            if any(p.poll() is not None for p in procs):
                ly_do = "in.tftpd thoát bất thường"
                break
            bay_gio = time.time()
            ss = subprocess.run(["ss", "-H", "-u", "-a", "-n", "-p"], capture_output=True, text=True, timeout=10).stdout   # nosec B603 B607
            tong, moi_nhat = dung_luong(goc)
            if dang_chep(ss) or moi_nhat != moi_nhat_cu:
                hoat_dong = bay_gio
            moi_nhat_cu = moi_nhat
            try:
                hoat_dong = max(hoat_dong, os.stat(GIA_HAN).st_mtime)
            except OSError:
                pass
            ghi_trang_thai(ds, hoat_dong + NHAN_ROI)
            lydo = quyet_dinh(bay_gio, hoat_dong, tong, shutil.disk_usage(goc).free)
            if lydo:
                ly_do = lydo
                break
            time.sleep(NHIP)
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
        for p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
        try:
            ghi_trang_thai([], 0, ly_do or "Đã tắt")
        except OSError:
            pass
    return 1 if "bất thường" in ly_do else 0          # tu tat (nhan roi/day the) la thoat BINH THUONG: systemd khong khoi dong lai


if __name__ == "__main__":
    sys.exit(main())
