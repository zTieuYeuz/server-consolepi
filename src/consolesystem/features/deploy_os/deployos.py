# Console System - (c) 2026 zTieuYeuz. All rights reserved.
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
import sys as _sys
_sys.modules["ui.deployos"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import json
import os
import re
import secrets
import shutil
import subprocess
import time
import unicodedata

# ---------------------------------------------------------------- duong dan
# Duong dan du lieu khai bao tap trung o duongdan.py (xem ly do that o do:
# du lieu tung nam chung voi ma nguon nen `uninstall.sh` xoa sach ca bo cai
# Office 3.6GB lan toan bo kich ban).
from ui.duongdan import DEPLOY_DIR, BOOT_DIR, APPS_DIR, SCRIPTS_DIR, KICHBAN_DIR, OS_DIR, DRIVERS_DIR, UNGDUNG_DIR, FONTS_DIR, EXT_SCRIPT  # noqa: F401  (B3: khai bao o core/duongdan.py)
from ui import datten as _dt
from consolesystem.features.deploy_os.dos_chung import (BUOC_DAU, EXT_DRIVER, EXT_OS_ISO, EXT_OS_WIM, EXT_SXS, SO_BUOC, THU_MUC_THEO_DUONG, _bao_dam_thu_muc, _bo_dau_py, _con_trong_gb, _don_file_do_dang, _duong_dan_trong, _hoan_tat_ghi_thang, _liet_ke, _luu_tai_len, _mo_file_dich, _thu_muc_os_theo_duong, _xoa_file, bo_dau, co_kich_thuoc, so_hien_thi, ten_an_toan)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_phanmem import (GOI_Y_THAM_SO, HAU_TO_GO, _an_toan_trong_zip, _doc_meta_ungdung, _ghi_meta_ungdung, chuan_hoa_apps, chuan_hoa_ungdung, danh_sach_app, danh_sach_ungdung, dat_lenh_cai_ungdung, doc_thongtin_app, ghi_thongtin_app, giai_nen_ungdung, lay_ungdung, liet_ke_muc_ungdung, tao_ungdung_moi, tham_so_mac_dinh_app, xoa_muc_trong_ungdung, xoa_ungdung)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_font import (MAX_FONT_BYTE, MAX_ZIP_FONT_BYTE, _doc_meta_bo_font, _don_tam_cu, _giai_nen_font_zip, _id_bo_font_tu_ten, _luu_font_hop_le, _xoa_tam, chuan_hoa_fonts, danh_sach_bo_font, duong_bo_font, lay_bo_font, tao_bo_font, them_font_vao_bo, xoa_bo_font, xoa_font_trong_bo)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_os import (_CACHE_CHI_SO_PRO, chi_so_anh_pro, co_sxs, danh_sach_os, duong_boot_wim, duong_install_wim, lay_os, tao_os_moi, xoa_os)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_driver import (EXT_GOI_NEN_DRIVER, _tu_may, danh_sach_driver, dat_driver_cho_boot, dat_model_driver, driver_hop_model, giai_nen_goi_driver, khop_model, tao_driver_moi, xoa_driver, xoa_file_trong_driver)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_kichban import (MAU_PHAN_VUNG_WINDOWS, _TRUONG_KICHBAN, _WIZARD, _WIZARD_HAN, _cauhinh_mac_dinh, _don_wizard_cu, _dong_tongket_windows, _khoi_go_app, _phan_vung_mac_dinh, _pv_win, _u_tuychon, _wizard_lay, _wizard_moi, cauhinh_tu_kichban, danh_sach_kichban, doc_kichban, kiem_tra_san_sang, loi_bat_buoc, luu_kichban, thieu_gi, xoa_kichban)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_tomtat import (_mo_ta_ngan, _o_tom_tat, _ten_os, _tom_tat_day_du)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_hangso import (APPS_META, BAN_PHIM, DANH_SACH_OS, EXT_APP, EXT_BOOT, EXT_UNGDUNG_ZIP, EXT_WINPE, KIEU_BOOT, MIN_FREE_GB, MUI_GIO, NGON_NGU, TEN_BUOC, _unattend)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_giaodien import (_JS_TAI_FONT, _tabs_trienkhai, ngu_canh_trienkhai, tabs_deployos, ve_bao_cao_o_dia)  # noqa: F401  (B4: nguyen van o module nay)


# ==================================================================== giao dien
# CSS/JS dung chung cua cac trang Deploy OS (cac module khac doc qua `ui.deployos.CSS_CHUNG`): dinh nghia o dosui_chung (B4)
from consolesystem.features.deploy_os.dosui_chung import CSS_CHUNG, JS_PHAN_TRANG_CHUNG  # noqa: F401


from consolesystem.features.deploy_os.dosui_chung import register_chung
from consolesystem.features.deploy_os.dosui_tiendo import register_tiendo
from consolesystem.features.deploy_os.dosui_kichban import register_kichban
from consolesystem.features.deploy_os.dosui_caidat import register_caidat
from consolesystem.features.deploy_os.dosui_os import register_os
from consolesystem.features.deploy_os.dosui_driver import register_driver
from consolesystem.features.deploy_os.dosui_kho import register_kho
from consolesystem.features.deploy_os.dosui_ungdung import register_ungdung
from consolesystem.features.deploy_os.dosui_o_dia import register_o_dia
from consolesystem.features.deploy_os.dosui_font import register_font
from consolesystem.features.deploy_os.dosui_console import register_console


def register_deployos(app):
    """Dang ky MOI route cua muc Deploy OS (B4: moi nhom chuc nang co register_<nhom> rieng trong dosui_*.py)."""
    register_chung(app)
    register_tiendo(app)
    register_kichban(app)
    register_caidat(app)
    register_os(app)
    register_driver(app)
    register_kho(app)
    register_ungdung(app)
    register_o_dia(app)
    register_font(app)
    register_console(app)
