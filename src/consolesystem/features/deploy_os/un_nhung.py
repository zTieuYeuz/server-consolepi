# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Unattend - bo file nhung vao WinPE (sinh_file_nhung, ghi_file_nhung, wim driver).

(B4: tach nguyen van tu unattend.py; ten ham/hang giu nguyen, nguon van re-export.)"""
import os
from ui import deployos as _d
from ui import datten as _tm
from consolesystem.core import duongdan as _DD
from consolesystem.features.deploy_os.un_baocao import (sinh_script_bao_cao)  # noqa: F401
from consolesystem.features.deploy_os.un_chonodia import (sinh_diskpart_txt)  # noqa: F401
from consolesystem.features.deploy_os.un_deploycmd import (sinh_autounattend_goi_script, sinh_deploy_cmd)  # noqa: F401
from consolesystem.features.deploy_os.un_goapp_font import (TEN_PS_CAI_FONT, TEN_PS_GO_APP, _bo_font_cai_duoc, _ds_go_app, sinh_ps_cai_font, sinh_ps_go_app)  # noqa: F401
from consolesystem.features.deploy_os.un_hangso import (DAU_TEN_MAY, DUOI_PS1_CO_BOM, THU_MUC_NHUNG, _sh)  # noqa: F401
from consolesystem.features.deploy_os.un_offline import (sinh_unattend_offline_xml)  # noqa: F401
from consolesystem.features.deploy_os.un_tientrinh import (sinh_script_tien_trinh)  # noqa: F401


def sinh_winpeshl_ini():
    return ("[LaunchApps]\r\n"
            f"X:\\sources\\setup.exe, /unattend:{THU_MUC_NHUNG}\\autounattend.xml\r\n")

def sinh_file_nhung(d, dia_chi_pi):
    """{ten file: noi dung} - moi file wimboot se chen cho 1 kich ban."""
    ra = {
        "winpeshl.ini": sinh_winpeshl_ini(),
        # autounattend.xml : chi de GOI deploy.cmd (sinh_autounattend_goi_script)
        "autounattend.xml": sinh_autounattend_goi_script(),
        # deploy.cmd : script trien khai kieu MDT (lam het moi viec)
        "deploy.cmd": sinh_deploy_cmd(d, dia_chi_pi),
        # 2 ban chia o - deploy.cmd tu chon theo BIOS/UEFI cua may
        "diskpart.txt": sinh_diskpart_txt(d),
        "diskpart-mbr.txt": sinh_diskpart_txt(d, mbr=True),
        # unattend.xml : cau hinh Windows sau khi bung (chep vao Panther)
        "unattend.xml": sinh_unattend_offline_xml(d),
        # ban cho Windows < 1809 (khong co conhost --headless) - deploy.cmd tu chon
        "unattend-cu.xml": sinh_unattend_offline_xml(d, kieu_cu=True),
        # Bao cao + tien trinh: nam trong chinh luc boot, KHONG qua Samba -
        # co mat ke ca khi mang chap chon.
        "bao-cao.ps1": sinh_script_bao_cao(d),
        "tien-trinh.ps1": sinh_script_tien_trinh(d, dia_chi_pi),
    }
    if _tm.la_dong(d):
        # Ten may dong (1.9.4): WinPE khong co powershell/sed -> deploy.cmd ghep
        # nua-truoc + ten + nua-sau bang `copy /b`. Chi sinh khi can (che do co dinh giu nguyen nhu cu).
        for tenf, cu in ((("una-a.xml", "una-b.xml"), False), (("una-cu-a.xml", "una-cu-b.xml"), True)):
            truoc, sau = sinh_unattend_offline_xml(d, kieu_cu=cu, ten_override=DAU_TEN_MAY).split(DAU_TEN_MAY, 1)
            ra[tenf[0]], ra[tenf[1]] = truoc, sau
    if _ds_go_app(d):
        ra[TEN_PS_GO_APP] = sinh_ps_go_app(d)
    if _bo_font_cai_duoc(d)[0]:
        ra[TEN_PS_CAI_FONT] = sinh_ps_cai_font()
    return ra

def ghi_file_nhung(d, dia_chi_pi, thu_muc):
    """
    Ghi bo file nhung cua 1 kich ban vao thu_muc (thay ca bo mot luc - may
    dang boot giua chung khong bao gio thay nua cu nua moi). Vai chuc KB,
    duoi 1 giay - khong con "dung anh" nua.
    """
    import shutil
    tam = thu_muc + ".moi"
    shutil.rmtree(tam, ignore_errors=True)
    try:
        os.makedirs(tam)
        for ten, noi_dung in sinh_file_nhung(d, dia_chi_pi).items():
            # File .ps1 PHAI co BOM. Windows PowerShell 5.1 doc .ps1 khong BOM
            # theo bang ma ANSI -> moi chu tieng Viet co dau thanh ky tu rac.
            ma_hoa = "utf-8-sig" if ten.lower().endswith(DUOI_PS1_CO_BOM) else "utf-8"
            with open(os.path.join(tam, ten), "w", encoding=ma_hoa, newline="") as f:
                f.write(noi_dung)
        cu = thu_muc + ".cu"
        shutil.rmtree(cu, ignore_errors=True)
        if os.path.isdir(thu_muc):
            os.replace(thu_muc, cu)
        os.replace(tam, thu_muc)
        shutil.rmtree(cu, ignore_errors=True)
        return True, ""
    except Exception as e:
        shutil.rmtree(tam, ignore_errors=True)
        return False, str(e)

def dung_wim_driver(duong_wim):
    """
    Dong cac goi driver "cho anh boot" vao 1 file .wim (wimboot chi chen
    duoc FILE PHANG, khong chen duoc thu muc driver). deploy.cmd bung no ra
    X:\\ConsolePiDrivers bang dism roi drvload - xem ly do (boot.wim thieu
    driver LAN Intel doi moi) trong deployos.dat_driver_cho_boot().

    Tra ve (ok, thong_bao). Khong co driver nao -> xoa file, ok. Chi dung lai
    khi danh sach/noi dung driver doi (dau van tay luu canh file).
    """
    import hashlib
    import shutil
    import tempfile
    cac = []
    for dr in _d.danh_sach_driver():
        thu_muc = os.path.join(_DD.DRIVERS_DIR, dr["id"])
        if dr.get("cho_boot") and os.path.isdir(thu_muc):
            cac.append((dr["id"], thu_muc))
    dau_file = duong_wim + ".dau"
    if not cac:
        for x in (duong_wim, dau_file):
            try:
                os.remove(x)
            except OSError:
                pass
        return True, ""
    h = hashlib.sha256()
    for ma, thu_muc in sorted(cac):
        for goc, _ds, fs in sorted(os.walk(thu_muc)):
            for f in sorted(fs):
                try:
                    st = os.stat(os.path.join(goc, f))
                except OSError:
                    continue
                h.update(f"{ma}/{os.path.relpath(goc, thu_muc)}/{f}:{st.st_size}:{int(st.st_mtime)}".encode())
    dau = h.hexdigest()
    try:
        with open(dau_file) as f:
            if f.read().strip() == dau and os.path.isfile(duong_wim):
                return True, ""
    except OSError:
        pass
    tam = tempfile.mkdtemp(prefix="drv-", dir=os.path.dirname(duong_wim))
    try:
        for ma, thu_muc in cac:
            os.symlink(thu_muc, os.path.join(tam, ma))
        ok, out = _sh(["wimlib-imagex", "capture", tam, duong_wim + ".moi",
                       "ConsolePiDrivers", "--dereference"], timeout=600)
        if not ok:
            return False, f"Không đóng gói được driver cho ảnh boot: {out[-300:]}"
        os.replace(duong_wim + ".moi", duong_wim)
        with open(dau_file, "w") as f:
            f.write(dau)
        return True, ""
    finally:
        shutil.rmtree(tam, ignore_errors=True)
        try:
            os.remove(duong_wim + ".moi")
        except OSError:
            pass
