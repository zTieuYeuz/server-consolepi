# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Tach tu deployos.py (B4).

(B4: tach nguyen van tu deployos.py::register_deployos; ten ham/route giu nguyen.)"""
from consolesystem.core import taisan as _taisan
from consolesystem.core.nhatky import bo_qua as _bo_qua
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
from flask import (request)
from ui.layout import render_page
from ui.home import _esc



_tabs = tabs_deployos      # dung lai ten cu cho ~40 cho da goi


CSS = _taisan.doc("features/deploy_os/dosui_chung.CSS.css")


CSS_CHUNG = CSS


# JS cua thanh tien trinh - chi chen vao cac trang co form tai len
JS_PHAN_TRANG = _taisan.doc("features/deploy_os/dosui_chung.JS_PHAN_TRANG.html")


JS_PHAN_TRANG_CHUNG = JS_PHAN_TRANG


JS_TIEN_DO = _taisan.doc("features/deploy_os/dosui_chung.JS_TIEN_DO.html")


def _trang(body, title, subtitle="", active="/deployos"):
    if 'class="form-tai-len"' in body:
        body += JS_TIEN_DO
    if "data-pt=" in body:
        body += JS_PHAN_TRANG
    return render_page(body, active=active, title=title,
                       subtitle=subtitle, extra_css=CSS)


def _msg(msg, ok=True):
    return f'<div class="msg {"ok" if ok else "err"}">{_esc(msg)}</div>' if msg else ""


def register_chung(app):
    # --- Chan tang Werkzeug: ghi thang file tai len ra dia dich ---
    #
    # Werkzeug goi _get_file_stream() de lay noi ghi du lieu tai len. Mac
    # dinh no tra ve 1 file tam; o day tra ve THANG file dich. Xem giai
    # thich day du (va loi that da gap) tai _mo_file_dich() o dau file.
    lop_request_goc = app.request_class

    class RequestTaiLenThang(lop_request_goc):
        def _get_file_stream(self, total_content_length, content_type,
                             filename=None, content_length=None):
            f, duong = _mo_file_dich(self.path, filename)
            if f is None:
                return super()._get_file_stream(
                    total_content_length, content_type, filename, content_length)
            # Ghi nho duong dan de route biet file vua duoc ghi vao dau.
            # Dat tren CHINH doi tuong file vi Werkzeug se boc no vao
            # FileStorage va route lay lai duoc qua .stream
            try:
                f._cp_duong_dan = duong
            except Exception as _loi:
                _bo_qua(_loi)
            return f

    app.request_class = RequestTaiLenThang

    @app.before_request
    def _chan_som_khi_khong_du_cho():
        """
        Tu choi NGAY khi vua nhan header, TRUOC khi doc du lieu.

        LOI THAT DA GAP (anh Thoai gap that): truoc day phep kiem tra dung
        luong nam o CUOI - sau khi da nhan het file. Anh tai 1 file 4.6GB
        mat ~20 phut, den luc xong moi bao "can 10.1GB nhung chi con 10GB"
        va vut het di. Cho kiem tra dung phai la NGAY DAU, luc chua ton mot
        byte nao cua anh.
        """
        cau_hinh = THU_MUC_THEO_DUONG.get(request.path) or _thu_muc_os_theo_duong(request.path)
        if cau_hinh is None:
            return None
        can = request.content_length or 0
        if not can:
            return None
        # Ghi thang ra dia dich nen chi can DUNG BANG kich thuoc file
        # (+1GB de he thong con cho tho), khong con can gap doi/gap ba nua.
        can_gb = can / (1024 ** 3) + 1
        if _con_trong_gb() < can_gb:
            thu_muc = cau_hinh[0]
            return _trang(
                _tabs("tainguyen", "file") +
                f'<div class="msg err">File này {co_kich_thuoc(can)} nên cần '
                f'khoảng {can_gb:.1f} GB trống, nhưng chỉ còn '
                f'{_con_trong_gb()} GB. Đã dừng lại NGAY, chưa tốn thời gian '
                f'tải lên của anh. Xóa bớt file cũ hoặc cắm USB rồi thử lại.</div>',
                "Cài Windows qua mạng", "Không đủ dung lượng"), 413
        return None
