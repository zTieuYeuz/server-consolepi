# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Tach tu deployos.py (B4).

(B4: tach nguyen van tu deployos.py::register_deployos; ten ham/route giu nguyen.)"""
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
from ui.home import _esc
from consolesystem.features.deploy_os.dosui_chung import (_msg, _tabs, _trang)  # noqa: F401


def _trang_o_dia(msg="", ok=True):
    from ui import doodia as _od
    ds = _od.danh_sach_bao_cao()
    khoi = "".join(ve_bao_cao_o_dia(kq) + f"""
          <form method="POST" action="/deployos/o-dia/xoa" style="margin:-6px 0 18px;">
            <input type="hidden" name="ten" value="{_esc(kq['ten'])}">
            <button type="submit" class="red small">Xóa báo cáo này</button>
          </form>""" for kq in ds)
    if not ds:
        khoi = """<div class="msg info">Chưa có báo cáo nào. Bật PXE, cho máy cần cài boot
              qua mạng, chọn <strong>3. Do o dia</strong> trong menu - máy chỉ ĐỌC thông tin ổ đĩa
              (không xóa gì), hiện trên màn hình và gửi về đây.</div>"""
    xoa_het = ("""<form method="POST" action="/deployos/o-dia/xoa-het" style="display:inline;"
              onsubmit="return confirm('Xóa tất cả báo cáo ổ đĩa?');">
              <button type="submit" class="red small">Xóa tất cả</button></form>""" if ds else "")
    body = (_tabs("kichban", "odia") + _msg(msg, ok) + f"""
        <div class="card">
          <h3>Ổ đĩa đã dò</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 8px;">
            Trước khi tạo kịch bản cho máy có nhiều ổ (SSD + HDD, ổ USB...), cho máy boot qua mạng
            và chọn <strong>3. Do o dia</strong> trong menu PXE. Máy chỉ <strong>đọc</strong> -
            không xóa, không chia, không ghi gì vào ổ - rồi hiện danh sách ổ ngay trên màn hình
            và gửi về đây. Số ở cột <strong>Ổ số</strong> là số cần nhập vào bước
            <em>Chia ổ đĩa</em> của kịch bản (ở bước đó cũng có nút "Dùng ổ ..." điền sẵn).</p>
          <p style="color:#8b93a1;font-size:13px;margin:0;">Lưu ý: số ổ do thứ tự cắm cáp/khe
            quyết định - <strong>dò lại</strong> nếu đã tháo lắp ổ, cắm thêm USB, hoặc máy khác đời.
            {xoa_het}</p>
        </div>
        {khoi}""")
    return _trang(body, "Cài Windows qua mạng", "Ổ đĩa đã dò")


def register_o_dia(app):
    # ------------------------- o dia da do (ui/doodia.py): may khach boot muc PXE "Do o dia",
    # gui ve danh sach o dia + phan vung -> ky su xem roi chon DUNG so o cho kich ban.
    @app.route("/deployos/o-dia")
    def deployos_o_dia():
        return _trang_o_dia()

    @app.route("/deployos/o-dia/xoa", methods=["POST"])
    def deployos_o_dia_xoa():
        from ui import doodia as _od
        ok, msg = _od.xoa_bao_cao(request.form.get("ten", ""))
        return _trang_o_dia(msg, ok)

    @app.route("/deployos/o-dia/xoa-het", methods=["POST"])
    def deployos_o_dia_xoa_het():
        from ui import doodia as _od
        ok, msg = _od.xoa_het()
        return _trang_o_dia(msg, ok)
