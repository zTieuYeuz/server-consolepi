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
from flask import (request, redirect)
from ui.home import _esc
from consolesystem.features.deploy_os.dosui_chung import (_msg, _tabs, _trang)  # noqa: F401


def _trang_font(msg="", ok=True):
    ds = danh_sach_bo_font()
    hang = ""
    for b in ds:
        hang += f"""
            <tr>
              <td><strong>{_esc(b['ten_hien_thi'])}</strong></td>
              <td>{b['so_font']} font &middot; {_esc(b['kich_thuoc'])}</td>
              <td>
                <a class="btn small" href="/deployos/font/{_esc(b['id'])}">Quản lý</a>
                <form method="POST" action="/deployos/font/xoa" style="display:inline;"
                      onsubmit="return confirm('Xóa toàn bộ bộ font này ({b['so_font']} font)?');">
                  <input type="hidden" name="bo_id" value="{_esc(b['id'])}">
                  <button type="submit" class="red small">Xóa</button>
                </form>
              </td>
            </tr>"""
    bang = (f"""<div class="tbl-scroll"><table>
              <tr><th>Tên bộ font</th><th style="width:190px;">Nội dung</th>
                  <th style="width:150px;">Thao tác</th></tr>
              {hang}
            </table></div>""" if ds else
        '<p style="color:#8b93a1;">Chưa có bộ font nào.</p>')
    body = (_tabs("tainguyen", "font") + _msg(msg, ok) + f"""
        <div class="card">
          <h3>Font chữ cho máy Windows</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0;">
            Gom font của công ty thành các <strong>bộ font</strong> (ví dụ "Font nhận diện
            thương hiệu", "Font in ấn"). Mỗi kịch bản cài Windows chọn bộ nào cần dùng ở
            bước <em>Phần mềm</em> &mdash; máy cài xong là có sẵn font cho <strong>mọi tài
            khoản</strong>, các ứng dụng (Word, Photoshop...) thấy ngay. Nhận file
            <code>.ttf</code> <code>.otf</code> <code>.ttc</code> <code>.otc</code>, hoặc
            nén cả thư mục font thành <code>.zip</code> rồi tải lên một lần.</p>
        </div>
        {bang}
        <div class="card">
          <h3>Tạo bộ font mới</h3>
          <form method="POST" action="/deployos/font/tao">
            <input type="text" name="ten_hien_thi" maxlength="80" required
                   placeholder="ví dụ: Font công ty" style="max-width:420px;">
            <button type="submit">Tạo</button>
          </form>
        </div>""")
    return _trang(body, "Cài Windows qua mạng", "Font chữ")


def register_font(app):
    @app.route("/deployos/font")
    def deployos_font():
        return _trang_font()

    @app.route("/deployos/font/tao", methods=["POST"])
    def deployos_font_tao():
        ok, msg, bo_id = tao_bo_font(request.form.get("ten_hien_thi", ""))
        if ok:
            return redirect(f"/deployos/font/{bo_id}")
        return _trang_font(msg, ok)

    @app.route("/deployos/font/xoa", methods=["POST"])
    def deployos_font_xoa():
        ok, msg = xoa_bo_font(request.form.get("bo_id", ""))
        return _trang_font(msg, ok)

    @app.route("/deployos/font/<bo_id>")
    def deployos_font_chitiet(bo_id):
        b = lay_bo_font(bo_id)
        if b is None:
            return _trang_font("Không tìm thấy bộ font.", False)
        hang = ""
        for m in b["fonts"]:
            hang += f"""
            <tr data-t="{_esc((m['ten'] + ' ' + m['ho'] + ' ' + m['file']).lower())}">
              <td><strong>{_esc(m['ten'])}</strong></td>
              <td>{_esc(m['kieu'])}</td>
              <td>{_esc(m['loai'])}</td>
              <td><code>{_esc(m['file'])}</code></td>
              <td>{_esc(co_kich_thuoc(m['byte']))}</td>
              <td><form method="POST" action="/deployos/font/{_esc(b['id'])}/xoa-font"
                        style="display:inline;"
                        onsubmit="return confirm('Xóa font {_esc(m["ten"])}?');">
                    <input type="hidden" name="ten" value="{_esc(m['file'])}">
                    <button type="submit" class="red small">Xóa</button>
                  </form></td>
            </tr>"""
        bang = (f"""
        <input type="search" id="fo-loc" placeholder="Lọc theo tên font..."
               style="max-width:340px;margin:0 0 10px;">
        <div class="tbl-scroll"><table id="fo-bang">
          <tr><th>Tên font</th><th>Kiểu</th><th>Loại</th><th>File</th>
              <th style="width:90px;">Dung lượng</th><th style="width:80px;">Thao tác</th></tr>
          {hang}
        </table></div>""" if b["fonts"] else
            '<p style="color:#8b93a1;">Bộ font đang trống. Tải font lên ở khung trên.</p>')
        js = _JS_TAI_FONT.replace("__URL__", f"/deployos/font/{b['id']}/len")
        body = (_tabs("tainguyen", "font") + f"""
        <p><a href="/deployos/font">&larr; Về danh sách bộ font</a></p>
        <h2>{_esc(b['ten_hien_thi'])}</h2>
        <p style="color:#8b93a1;margin-top:-6px;">{b['so_font']} font &middot; {_esc(b['kich_thuoc'])}</p>

        <div class="card">
          <h3>Thêm font</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 10px;">
            Chọn nhiều file cùng lúc, chọn cả thư mục, hoặc kéo thả vào khung. File
            <code>.zip</code> chứa font cũng được (tự giải nén, bỏ qua file không phải
            font). Mỗi file được kiểm tra là font thật; file hỏng hoặc web font
            (<code>.woff</code>) sẽ bị báo và bỏ qua. Font trùng tên file sẽ được thay mới.</p>
          <div id="fo-tha" class="fo-tha">
            <div style="margin-bottom:10px;">Kéo thả font / thư mục / file .zip vào đây</div>
            <label class="btn">Chọn file
              <input type="file" id="fo-file" multiple hidden
                     accept=".ttf,.otf,.ttc,.otc,.zip"></label>
            <label class="btn gray">Chọn cả thư mục
              <input type="file" id="fo-thumuc" multiple hidden webkitdirectory></label>
          </div>
          <div id="fo-tt" style="display:none;margin-top:12px;">
            <div style="background:#1b2430;border-radius:6px;height:14px;overflow:hidden;">
              <div id="fo-thanh" style="background:#3dd3ff;height:100%;width:0%;"></div></div>
            <div id="fo-chu" style="margin-top:7px;font-size:13px;color:#a8b0bd;"></div>
          </div>
          <div id="fo-ketqua" style="margin-top:10px;font-size:13px;"></div>
        </div>

        <h3>Font trong bộ</h3>
        {bang}
        <style>
          .fo-tha {{ border:2px dashed #3a4656;border-radius:10px;padding:22px;text-align:center; }}
          .fo-tha.keo {{ border-color:#3dd3ff;background:rgba(61,211,255,.07); }}
        </style>
        {js}""")
        return _trang(body, "Cài Windows qua mạng", f"Font chữ - {b['ten_hien_thi']}")

    @app.route("/deployos/font/<bo_id>/len", methods=["POST"])
    def deployos_font_len(bo_id):
        """Nhan 1 file (font hoac .zip) - tra JSON de trang tai len hien ket qua tung file."""
        from flask import jsonify
        f = request.files.get("file")
        if not f or not getattr(f, "filename", ""):
            return jsonify({"ok": False, "msg": "Chưa chọn file.", "them": 0, "bo_qua": []}), 400
        ok, msg, them, bo_qua = them_font_vao_bo(bo_id, f)
        return jsonify({"ok": ok, "msg": msg, "them": them, "bo_qua": bo_qua})

    @app.route("/deployos/font/<bo_id>/xoa-font", methods=["POST"])
    def deployos_font_xoa_font(bo_id):
        ok, msg = xoa_font_trong_bo(bo_id, request.form.get("ten", ""))
        if not ok:
            return _trang_font(msg, ok)
        return redirect(f"/deployos/font/{bo_id}")
