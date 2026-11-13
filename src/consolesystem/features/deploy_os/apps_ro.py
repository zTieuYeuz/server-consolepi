# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Tai khoan Samba CHI DOC cho WinPE-Apps qua mang (2.0.8 V3-3).

cs-apps.cmd duoc phat KHONG can dang nhap (WinPE chua co phien Console) va chua mat khau Samba. Truoc day do la mat khau cua consolepi-deploy
(doc ca share [deploy] gom anh OS/driver/kich ban, GHI duoc [cs-o-dia]/[cs-lich-su]). Nay dung tai khoan RIENG cs-apps-ro (nologin) CHI doc
[winpe-apps], mat khau ngau nhien DOI MOI LAN BAT PXE (khong doi giua luc dang boot: chi doi khi PXE chuyen tu tat sang bat).

AN TOAN CHO CHUC NANG CU: tao/doi mat khau loi, hoac smb.conf chua co tai khoan nay (may OTA chua ap cau hinh) -> TU LUI VE consolepi-deploy
nhu 2.0.7, khong lam hong trien khai. consolepi-deploy van dung cho deploy.cmd."""
import ipaddress
import os
import re
import secrets
import subprocess

from ui import duongdan as _DD

TAI_KHOAN = "cs-apps-ro"
TAI_KHOAN_CU = "consolepi-deploy"
SMB_CONF = "/etc/samba/smb.conf"


def _sh(cmd, input=None, timeout=20):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, input=input)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, type(e).__name__


def smb_conf_co_tai_khoan(duong=None):
    """smb.conf dang dung co cho phep cs-apps-ro tren [winpe-apps] khong (valid users)."""
    try:
        nd = open(duong or SMB_CONF, encoding="utf-8").read()
    except OSError:
        return False
    m = re.search(r"^\[winpe-apps\]\s*$(.*?)(?=^\[|\Z)", nd, re.M | re.S)
    if not m:
        return False
    for dong in m.group(1).splitlines():
        k, _, v = dong.partition("=")
        if k.strip().lower() == "valid users" and TAI_KHOAN in v.split():
            return True
    return False


def _xoa_khoa():
    try:
        os.remove(_DD.FILE_KHOA_APPS_RO)
    except OSError:
        pass


def xoay_mat_khau(sh=_sh, smb_conf=None):
    """Goi KHI PXE chuyen tu tat sang bat. Tra (ok, thong_bao). Loi -> xoa khoa de cs-apps.cmd lui ve tai khoan cu."""
    if not smb_conf_co_tai_khoan(smb_conf):
        _xoa_khoa()
        return False, "cấu hình Samba chưa có tài khoản chỉ-đọc cs-apps-ro (cập nhật cấu hình rồi bật lại PXE) - công cụ WinPE dùng tài khoản cũ"
    ok, _ = sh(["id", TAI_KHOAN])
    if not ok:
        ok, out = sh(["useradd", "--system", "--no-create-home", "--shell", "/usr/sbin/nologin", TAI_KHOAN])
        if not ok:
            _xoa_khoa()
            return False, "không tạo được tài khoản cs-apps-ro (%s) - công cụ WinPE dùng tài khoản cũ" % out[:80]
    mk = secrets.token_urlsafe(18)
    ok, out = sh(["smbpasswd", "-s", "-a", TAI_KHOAN], input="%s\n%s\n" % (mk, mk))
    ok2 = ok and sh(["smbpasswd", "-e", TAI_KHOAN])[0]
    if not ok2:
        _xoa_khoa()
        return False, "không đặt được mật khẩu Samba cho cs-apps-ro - công cụ WinPE dùng tài khoản cũ"
    try:
        os.makedirs(os.path.dirname(_DD.FILE_KHOA_APPS_RO), exist_ok=True)
        tmp = _DD.FILE_KHOA_APPS_RO + ".tmp"
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(mk)
        os.replace(tmp, _DD.FILE_KHOA_APPS_RO)
    except OSError as e:
        _xoa_khoa()
        return False, "không lưu được mật khẩu cs-apps-ro (%s) - công cụ WinPE dùng tài khoản cũ" % type(e).__name__
    return True, "ok"


def vo_hieu(sh=_sh):
    """Goi khi TAT PXE: khoa tai khoan Samba cs-apps-ro (smbpasswd -d) va xoa mat khau da luu. Bat lai PXE se bat + doi mat khau."""
    _xoa_khoa()
    ok, _ = sh(["id", TAI_KHOAN])
    if ok:
        sh(["smbpasswd", "-d", TAI_KHOAN])


def thong_tin_apps(smb_conf=None):
    """(tai_khoan, mat_khau) cho cs-apps.cmd, hoac None. Dung cs-apps-ro neu san sang, khong thi tai khoan cu."""
    if smb_conf_co_tai_khoan(smb_conf):
        try:
            mk = open(_DD.FILE_KHOA_APPS_RO, encoding="utf-8").read().strip()
        except OSError:
            mk = ""
        if mk:
            return TAI_KHOAN, mk
    try:
        mk = open(_DD.FILE_KHOA_SAMBA, encoding="utf-8").read().strip()
    except OSError:
        return None
    return TAI_KHOAN_CU, mk


def _mang_cua_cong(cong, sh=_sh):
    ok, out = sh(["ip", "-4", "-o", "addr", "show", "dev", cong])
    mang = []
    if ok:
        for m in re.finditer(r"inet\s+(\d+\.\d+\.\d+\.\d+/\d+)", out):
            try:
                mang.append(ipaddress.ip_interface(m.group(1)).network)
            except ValueError:
                pass
    return mang


def khach_trong_mang_trien_khai(ip_khach, cong, sh=_sh):
    """Chi phat cs-apps.cmd cho may o CUNG MANG voi cong PXE. Khong xac dinh duoc mang cua cong -> cho qua (khong lam hong trien khai dang chay)."""
    mang = _mang_cua_cong(cong, sh)
    if not mang:
        return True
    try:
        ip = ipaddress.ip_address((ip_khach or "").strip())
    except ValueError:
        return False
    return any(ip in n for n in mang)
