# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi - Tu dong hoa Windows Setup (autounattend.xml) cho Deployment OS

Tiep noi ui/pxe.py: sau khi boot qua PXE vao duoc man hinh "Windows Setup"
that (da kiem chung that - anh Thoai xac nhan bang anh chup man hinh), muc
nay lam cho Windows Setup TU CHAY het cac buoc (chon ngon ngu, chia o dia,
dat ten may, tao tai khoan, mui gio, bo qua OOBE) THEO DUNG cac lua chon
anh Thoai da chon o 7 buoc cua wizard - khong con phai bam Next thu cong.

CO CHE (dung tai lieu unattend.xml chinh thuc cua Microsoft, khong doan):
Windows Setup tu dong quet moi O DIA RIENG (kho ca dia cung/USB/dia mem ao)
tim file ten dung `autounattend.xml` o thu muc goc ngay tu buoc dau tien
(windowsPE pass) - khong can chi duong dan gi ca, chi can file co mat va
dung ten.

wimboot (dang dung de nap WinPE qua mang - xem ui/pxe.py) ho tro nap them
1 "dia mem ao" (floppy image) cung luc voi boot.wim: Windows Setup nhin
thay dia mem ao nay y het 1 o dia that, tu tim thay autounattend.xml
trong do. Day la cach lam CHINH THUC cua chinh du an wimboot cho truong
hop nay (khong phai tu nghi ra).

GIOI HAN THAT (khong bia): phan tu dong CAI PHAN MEM (FirstLogonCommands)
CAN duong mang toi noi luu file .msi/.exe (Samba hoac HTTP tu chinh Pi) -
HA TANG NAY CHUA DUNG (xem docs/ke-hoach-pxe-winpe-tu-dong-cai-windows.md,
muc "Samba"). File autounattend.xml o day moi lam duoc phan CAI DAT HE
DIEU HANH tu dong hoan toan (dia, ten may, tai khoan, mui gio, OOBE) -
CHUA tu dong cai phan mem sau do. Se bao ro trong ket qua kiem tra san
sang, khong gia vo da lam xong.
"""
import sys as _sys
_sys.modules["ui.unattend"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import os
import re
import subprocess
import xml.sax.saxutils as _x

from ui import deployos as _d
from ui import datten as _tm
from consolesystem.features.deploy_os.un_hangso import (DAU_TEN_MAY, DUOI_PS1_CO_BOM, TEN_DIA_GPT_TU_DONG, TEN_MAY_SAMBA, TEN_NHUNG_DRIVER, TEN_TAI_KHOAN_SAMBA, TEN_WIM_DRIVER, THU_MUC_NHUNG, _doc_mat_khau_samba, _khoi_credentials_samba, _khoi_dia_windows, _khoi_driverpaths, _sh)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.un_xml import (sinh_autounattend_xml)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.un_kiemtra import (GIAY_TOI_DA_MOI_BUOC, KIEM_TRA_DAC_BIET, _RE_BAT_CMD, _danh_sach_buoc_nguoi_dung, _muc_kiem_tra, _nhan_tuy_chon, _phan_tich_lenh_reg, _ps_chuoi, _them_call)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.un_tientrinh import (sinh_script_tien_trinh)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.un_baocao import (_lenh_khong_thay_o, _lenh_kiem_tra_card_mang, sinh_script_bao_cao)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.un_chonodia import (CACH_CHON_O, _ham_chon_o, _lenh_chon_o, mo_ta_chon_o, mo_ta_tu_dong, o_chon, sinh_diskpart_txt, tuychon_tu_dong)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.un_deploycmd import (_lenh_bao_lich_su, _lenh_chep_app_script, _lenh_chep_unattend, _lenh_chon_unattend, _lenh_dat_ten, sinh_autounattend_goi_script, sinh_deploy_cmd)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.un_tuychon import (TUY_CHON_WINDOWS, _khoi_gia_nhap_domain)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.un_goapp_font import (APP_RAC, DUONG_PS_GO_APP, TEN_PS_CAI_FONT, TEN_PS_GO_APP, THU_MUC_TREN_MAY, THU_MUC_UNGDUNG_TREN_MAY, _PS_CAI_FONT, _bo_font_cai_duoc, _ds_go_app, _lenh_cai_app, _lenh_cai_bo_font, _lenh_cai_ungdung, _lenh_chep_go_app, _lenh_go_app, _lenh_mot_script, _lenh_net35_offline, _lenh_script, _lenh_theo_pha, _lenh_tiem_driver_offline, sinh_ps_cai_font, sinh_ps_go_app)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.un_offline import (BUILD_TOI_THIEU_HEADLESS, LENH_MO_TIEN_TRINH, LENH_MO_TIEN_TRINH_CU, _HIVE_HS, _HIVE_HS_CLASS, _LENH_PS_TIEN_TRINH, _khoi_firstlogon, _khoi_runsync_specialize, _lenh_bat_administrator, _lenh_ho_so_mac_dinh, _lenh_tat_hoi_mang, sinh_unattend_offline_xml)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.un_iso import (DUNG_LUONG_FLOPPY_KB, TEN_AUTOUNATTEND, TEN_FLOPPY, TEN_ISO_TU_DONG, _CAC_FILE_BOOT_ISO, _GIOI_HAN_ISO9660, chuan_bi_autounattend, co_san_autounattend, co_san_dia_mem_autounattend, co_san_iso_tu_dong, dung_iso_tu_dong, tao_dia_mem_ao)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.un_nhung import (dung_wim_driver, ghi_file_nhung, sinh_file_nhung, sinh_winpeshl_ini)  # noqa: F401  (B4: nguyen van o module nay)






# Duong dan file khoa Samba - xem install.sh (khoi "Samba: kho trien khai
# Windows qua PXE"): tu sinh ngau nhien 1 lan duy nhat luc cai, quyen 600.
#
# TUYET DOI KHONG viet mat khau thang vao code: repo nay la PUBLIC tren
# GitHub, code se bi doc boi bat ky ai - hang chuc nghin nguoi. Mat khau
# tung bi viet cung o day (da phat hien va sua truoc khi commit lan dau,
# chua tung bi day len GitHub).
from ui.duongdan import FILE_KHOA_SAMBA as _FILE_KHOA_SAMBA
from consolesystem.core.esc import esc_xml as _esc
from consolesystem.core import duongdan as _DD
































































































































































