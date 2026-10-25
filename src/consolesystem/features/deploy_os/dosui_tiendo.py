# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Tach tu deployos.py (B4).

(B4: tach nguyen van tu deployos.py::register_deployos; ten ham/route giu nguyen.)"""
import os
from ui.duongdan import DEPLOY_DIR, BOOT_DIR, APPS_DIR, SCRIPTS_DIR, KICHBAN_DIR, OS_DIR, DRIVERS_DIR, UNGDUNG_DIR, FONTS_DIR, EXT_SCRIPT  # noqa: F401  (B3: khai bao o core/duongdan.py)
from consolesystem.features.deploy_os.dos_chung import (BUOC_DAU, EXT_DRIVER, EXT_OS_ISO, EXT_OS_WIM, EXT_SXS, SO_BUOC, THU_MUC_THEO_DUONG, _bao_dam_thu_muc, _bo_dau_py, _con_trong_gb, _don_file_do_dang, _duong_dan_trong, _hoan_tat_ghi_thang, _liet_ke, _luu_tai_len, _mo_file_dich, _thu_muc_os_theo_duong, _xoa_file, bo_dau, co_kich_thuoc, so_hien_thi, ten_an_toan)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_phanmem import (GOI_Y_THAM_SO, HAU_TO_GO, _an_toan_trong_zip, _doc_meta_ungdung, _ghi_meta_ungdung, chuan_hoa_apps, chuan_hoa_ungdung, danh_sach_app, danh_sach_ungdung, dat_lenh_cai_ungdung, doc_thongtin_app, ghi_thongtin_app, giai_nen_ungdung, lay_ungdung, liet_ke_muc_ungdung, tao_ungdung_moi, tham_so_mac_dinh_app, xoa_muc_trong_ungdung, xoa_ungdung)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_font import (MAX_FONT_BYTE, MAX_ZIP_FONT_BYTE, _doc_meta_bo_font, _don_tam_cu, _giai_nen_font_zip, _id_bo_font_tu_ten, _luu_font_hop_le, _xoa_tam, chuan_hoa_fonts, danh_sach_bo_font, duong_bo_font, lay_bo_font, tao_bo_font, them_font_vao_bo, xoa_bo_font, xoa_font_trong_bo)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_os import (_CACHE_CHI_SO_PRO, chi_so_anh_pro, co_sxs, danh_sach_os, duong_boot_wim, duong_install_wim, lay_os, tao_os_moi, xoa_os)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_driver import (EXT_GOI_NEN_DRIVER, _tu_may, danh_sach_driver, dat_driver_cho_boot, dat_model_driver, driver_hop_model, giai_nen_goi_driver, khop_model, tao_driver_moi, xoa_driver, xoa_file_trong_driver)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_kichban import (MAU_PHAN_VUNG_WINDOWS, _TRUONG_KICHBAN, _WIZARD, _WIZARD_HAN, _cauhinh_mac_dinh, _don_wizard_cu, _dong_tongket_windows, _khoi_go_app, _phan_vung_mac_dinh, _pv_win, _u_tuychon, _wizard_lay, _wizard_moi, cauhinh_tu_kichban, danh_sach_kichban, doc_kichban, kiem_tra_san_sang, loi_bat_buoc, luu_kichban, thieu_gi, xoa_kichban)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_tomtat import (_mo_ta_ngan, _o_tom_tat, _ten_os, _tom_tat_day_du)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_hangso import (APPS_META, BAN_PHIM, DANH_SACH_OS, EXT_APP, EXT_BOOT, EXT_UNGDUNG_ZIP, EXT_WINPE, KIEU_BOOT, MIN_FREE_GB, MUI_GIO, NGON_NGU, TEN_BUOC, _unattend)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_giaodien import (_JS_TAI_FONT, _tabs_trienkhai, ngu_canh_trienkhai, tabs_deployos, ve_bao_cao_o_dia)  # noqa: F401  (B4: nguyen van o module nay)
from flask import (request, jsonify)



def register_tiendo(app):
    @app.route("/deployos/tien-do")
    def deployos_tien_do():
        """
        Bao cho trang biet may DA GHI DUOC bao nhieu byte xuong dia that.

        Doc thang kich thuoc file <ten>.part dang duoc ghi. Nho vay thanh
        tien trinh bam theo tien do THAT tren dia, khong phai chi theo so
        byte trinh duyet da gui di (hai so nay lech nhau khi mang nhanh hon
        the nho - dung tinh huong lam anh Thoai tuong may bi treo).
        """
        loai = request.args.get("loai", "")
        ten = ten_an_toan(request.args.get("ten", ""))
        # Thu muc he dieu hanh la DONG (moi os_id mot thu muc) nen khong nam
        # trong bang tra co dinh ben duoi - form gui kem "os_id" rieng.
        # Thieu nhanh nay thi thanh tien trinh cua trang He dieu hanh (ke ca
        # duong tai ISO 5GB moi them) luon bao "da ghi 0" du may dang ghi
        # binh thuong - nhin y het bi treo.
        if loai in ("os", "os-iso", "os-sxs"):
            os_id = ten_an_toan(request.args.get("os_id", ""))
            thu_muc = os.path.join(OS_DIR, os_id) if os_id else None
            if thu_muc and loai == "os-sxs":
                thu_muc = os.path.join(thu_muc, "sxs")
        else:
            thu_muc = {"file": BOOT_DIR, "apps": APPS_DIR,
                       "scripts": SCRIPTS_DIR}.get(loai)
        if not thu_muc or not ten:
            return jsonify({"da_ghi": 0, "xong": False})
        p = os.path.join(thu_muc, ten + ".part")
        try:
            return jsonify({"da_ghi": os.path.getsize(p), "xong": False})
        except OSError:
            # Khong con .part: hoac chua bat dau, hoac da doi ten -> xong
            xong = os.path.isfile(os.path.join(thu_muc, ten))
            return jsonify({"da_ghi": 0, "xong": xong})
