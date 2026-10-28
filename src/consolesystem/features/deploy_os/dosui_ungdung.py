# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Tach tu deployos.py (B4).

(B4: tach nguyen van tu deployos.py::register_deployos; ten ham/route giu nguyen.)"""
from consolesystem.core.nhatky import bo_qua as _bo_qua
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
from flask import (request, redirect)
from ui.home import _esc
from consolesystem.features.deploy_os.dosui_chung import (_msg, _tabs, _trang)  # noqa: F401


def _trang_ungdung(msg="", ok=True):
    ds = danh_sach_ungdung()
    hang = ""
    for u in ds:
        hang += f"""
            <tr>
              <td><strong>{_esc(u['ten_hien_thi'])}</strong></td>
              <td>{u['so_file']} file &middot; {_esc(u['kich_thuoc'])}</td>
              <td>{'<code>' + _esc(u['lenh_cai']) + '</code>' if u['lenh_cai'] else
                  '<span style="color:#f59e0b;">chưa đặt lệnh cài</span>'}</td>
              <td>
                <a class="btn small" href="/deployos/ungdung/{_esc(u['id'])}">Quản lý</a>
                <form method="POST" action="/deployos/ungdung/xoa" style="display:inline;"
                      onsubmit="return confirm('Xóa toàn bộ ứng dụng này?');">
                  <input type="hidden" name="ung_id" value="{_esc(u['id'])}">
                  <button type="submit" class="red small">Xóa</button>
                </form>
              </td>
            </tr>"""
    bang = (f"""<div class="tbl-scroll"><table>
              <tr><th>Tên</th><th style="width:170px;">Nội dung</th>
                  <th>Lệnh cài</th><th style="width:150px;">Thao tác</th></tr>
              {hang}
            </table></div>""" if ds else
        '<p style="color:#8b93a1;">Chưa có ứng dụng nào.</p>')
    body = (_tabs("tainguyen", "ungdung") + _msg(msg, ok) + f"""
        <!-- Phan giai thich chuyen vao HOP THOAI: no dai gan nua man hinh ma
             chi can doc DUNG MOT LAN luc dau lam quen, nhung lai nam chan
             ngay tren danh sach ung dung that - moi lan vao trang deu phai
             cuon qua no. Nay thanh 1 nut, ai can thi bam. -->
        <div class="row" style="margin:0 0 14px;align-items:center;">
          <button type="button" class="gray" data-mo-hop="hop-giai-thich">
            Khác gì với mục &quot;Phần mềm&quot;?</button>
          <span class="hint">Bấm để xem giải thích và ví dụ Office 365.</span>
        </div>
        <dialog id="hop-giai-thich" style="border:1px solid #2B3746;border-radius:12px;
                background:#141A23;color:#E3E8EF;padding:0;max-width:720px;width:94vw;">
          <div style="display:flex;align-items:center;gap:12px;padding:16px 20px;
                      border-bottom:1px solid #1F2733;">
            <strong style="flex:1;font-size:16px;">&quot;Ứng dụng&quot; khác &quot;Phần mềm&quot; chỗ nào?</strong>
            <button type="button" class="gray small" data-dong-hop>Đóng</button>
          </div>
          <div style="padding:16px 20px;max-height:66vh;overflow:auto;">
            <table class="tt-bang">
              <tr><td style="width:150px;">Phần mềm</td>
                  <td>1 file .msi/.exe duy nhất, tự suy tham số cài theo đuôi
                  file. Hợp cho bộ cài đơn giản (7-Zip, TeamViewer...).</td></tr>
              <tr><td>Ứng dụng (đây)</td>
                  <td>1 <strong>thư mục</strong> - chứa bao nhiêu file/thư mục
                  con cũng được - kèm 1 <strong>dòng lệnh cài tự do</strong> do
                  anh tự gõ. Đúng mô hình &quot;Application with source files&quot; của
                  MDT.</td></tr>
            </table>
            <div class="msg info" style="margin-bottom:0;">
              <strong>Ví dụ hay dùng nhất - Office 365:</strong> trên một máy
              Windows, dùng Office Deployment Tool chạy
              <code>setup.exe /download configuration.xml</code> để tải sẵn bộ
              cài về. Nén cả thư mục đó thành <code>.zip</code>, tải lên đây,
              rồi đặt lệnh cài là
              <code>setup.exe /configure configuration.xml</code>.
            </div>
          </div>
        </dialog>
        <div class="card">
          <h3>Tạo ứng dụng mới</h3>
          <form method="POST" action="/deployos/ungdung/tao">
            <input type="text" name="ten_hien_thi" placeholder="Tên ứng dụng"
                   required autocapitalize="off">
            <button type="submit">Tạo</button>
          </form>
        </div>
        <h2>Ứng dụng đã có ({len(ds)})</h2>
        {bang}""")
    return _trang(body, "Cài Windows qua mạng", "Ứng dụng (nhiều file)")


def register_ungdung(app):
    # ------------------------- ung dung thu muc (mo hinh MDT: "Application
    # with source files" - xem chi tiet trong docstring cua danh_sach_ungdung()
    # o dau file. Dung cho bo cai NHIEU FILE nhu Office 365 (Office Deployment
    # Tool: thu muc Office\ + setup.exe + configuration.xml).
    @app.route("/deployos/ungdung")
    def deployos_ungdung():
        return _trang_ungdung()

    @app.route("/deployos/ungdung/tao", methods=["POST"])
    def deployos_ungdung_tao():
        ok, msg, ung_id = tao_ungdung_moi(request.form.get("ten_hien_thi", ""))
        if ok:
            return redirect(f"/deployos/ungdung/{ung_id}")
        return _trang_ungdung(msg, ok)

    @app.route("/deployos/ungdung/xoa", methods=["POST"])
    def deployos_ungdung_xoa():
        ok, msg = xoa_ungdung(request.form.get("ung_id", ""))
        return _trang_ungdung(msg, ok)

    @app.route("/deployos/ungdung/<ung_id>")
    def deployos_ungdung_chitiet(ung_id):
        u = lay_ungdung(ung_id)
        if u is None:
            return _trang_ungdung("Không tìm thấy ứng dụng.", False)
        muc = liet_ke_muc_ungdung(ung_id)
        hang = ""
        for m in muc:
            bieu = "📁" if m["la_thu_muc"] else "📄"
            chi_tiet = (f"{m['so_file']} file bên trong" if m["la_thu_muc"]
                       else m["kich_thuoc"])
            hang += f"""
            <tr><td>{bieu} {_esc(m['ten'])}</td><td>{chi_tiet}</td>
                <td><form method="POST" action="/deployos/ungdung/{_esc(ung_id)}/xoa-muc"
                          style="display:inline;"
                          onsubmit="return confirm('Xóa {_esc(m["ten"])}?');">
                      <input type="hidden" name="ten" value="{_esc(m['ten'])}">
                      <button type="submit" class="red small">Xóa</button>
                    </form></td></tr>"""
        bang = (f"""<div class="tbl-scroll"><table>
              <tr><th>Tên</th><th>Chi tiết</th><th style="width:90px;">Thao tác</th></tr>
              {hang}
            </table></div>""" if muc else
            '<p style="color:#8b93a1;">Thư mục ứng dụng đang trống.</p>')
        body = (_tabs("tainguyen", "ungdung") + f"""
        <p><a href="/deployos/ungdung">&larr; Về danh sách ứng dụng</a></p>
        <h2>{_esc(u['ten_hien_thi'])}</h2>

        <div class="card">
          <h3>Dòng lệnh cài</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 9px;">
            Lúc cài, hệ thống tự <code>cd</code> vào đúng thư mục này rồi chạy
            dòng lệnh - chỉ cần gõ tên file, không cần đường dẫn đầy đủ. Ví
            dụ Office 365: <code>setup.exe /configure configuration.xml</code>.</p>
          <form method="POST" action="/deployos/ungdung/{_esc(ung_id)}/lenh">
            <input type="text" name="lenh_cai" value="{_esc(u['lenh_cai'])}"
                   placeholder="ví dụ: setup.exe /configure configuration.xml"
                   style="max-width:none;" autocapitalize="off">
            <div class="row" style="margin-top:10px;">
              <button type="submit">Lưu lệnh cài</button>
            </div>
          </form>
        </div>

        <div class="card">
          <h3>Tải lên bộ cài (.zip)</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 9px;">
            Nén TOÀN BỘ thư mục nguồn (giữ nguyên thư mục con bên trong) rồi
            tải lên đây - hệ thống tự giải nén, giữ đúng cấu trúc thư mục.
            File lớn (vài GB) vẫn tải lên được, ghi thẳng ra đĩa không qua
            RAM - chỉ là sẽ mất thời gian theo tốc độ mạng.</p>
          <form method="POST" action="/deployos/ungdung/{_esc(ung_id)}/len"
                enctype="multipart/form-data" data-busy="Đang tải lên và giải nén...">
            <input type="file" name="file" accept=".zip" required>
            <button type="submit">Tải lên</button>
          </form>
        </div>

        <div class="card">
          <h3>Thay 1 file lẻ (vd file cấu hình .xml)</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 9px;">
            Dùng khi chỉ cần sửa/thay 1 file nhỏ (cấu hình, script...) mà
            không muốn nén lại cả bộ - tải file này lên sẽ đặt thẳng vào
            gốc thư mục ứng dụng, <strong>ghi đè</strong> nếu đã có file
            trùng tên.</p>
          <form method="POST" action="/deployos/ungdung/{_esc(ung_id)}/len-file"
                enctype="multipart/form-data" data-busy="Đang tải lên...">
            <input type="file" name="file" required>
            <button type="submit" class="gray">Tải lên (ghi đè)</button>
          </form>
        </div>

        <h3>Nội dung hiện có</h3>
        {bang}""")
        return _trang(body, "Cài Windows qua mạng", f"Ứng dụng - {u['ten_hien_thi']}")

    @app.route("/deployos/ungdung/<ung_id>/lenh", methods=["POST"])
    def deployos_ungdung_lenh(ung_id):
        ok, msg = dat_lenh_cai_ungdung(ung_id, request.form.get("lenh_cai", ""))
        if not ok:
            return _trang_ungdung(msg, ok)
        return redirect(f"/deployos/ungdung/{ung_id}")

    @app.route("/deployos/ungdung/<ung_id>/xoa-muc", methods=["POST"])
    def deployos_ungdung_xoa_muc(ung_id):
        ok, msg = xoa_muc_trong_ungdung(ung_id, request.form.get("ten", ""))
        if not ok:
            return _trang_ungdung(msg, ok)
        return redirect(f"/deployos/ungdung/{ung_id}")

    @app.route("/deployos/ungdung/<ung_id>/len", methods=["POST"])
    def deployos_ungdung_len(ung_id):
        f = request.files.get("file")
        if not f or not getattr(f, "filename", ""):
            return redirect(f"/deployos/ungdung/{ung_id}")
        duong = getattr(getattr(f, "stream", None), "_cp_duong_dan", None)
        if not duong:
            return _trang_ungdung(
                "Chỉ nhận file .zip - đổi đuôi file cho đúng rồi thử lại.", False)
        try:
            f.stream.flush()
            os.fsync(f.stream.fileno())
        except Exception as _loi:
            _bo_qua(_loi)
        ok, msg, duong_dich = _hoan_tat_ghi_thang(
            duong, os.path.join(UNGDUNG_DIR, ten_an_toan(ung_id)), f.filename)
        if not ok:
            return _trang_ungdung(msg, ok)
        ok, msg = giai_nen_ungdung(ung_id, duong_dich)
        if not ok:
            return _trang_ungdung(msg, ok)
        return redirect(f"/deployos/ungdung/{ung_id}")

    @app.route("/deployos/ungdung/<ung_id>/len-file", methods=["POST"])
    def deployos_ungdung_len_file(ung_id):
        """
        Tai LE 1 file (khong can nen .zip) vao goc thu muc ung dung - GHI
        DE neu trung ten. Sinh ra tu chinh su co that: anh Thoai can THAY
        1 file cau hinh nho (vai KB) trong 1 ung dung da co san hang GB
        (Office 365) - truoc day CHI co duong tai .zip, buoc phai nen ca
        1 file nho thanh zip moi thay duoc, rat bat tien.

        Dung f.save() binh thuong (khong qua co che ghi thang danh cho
        file lon nhu .zip) vi day chi de danh cho file cau hinh/script nho.
        """
        u = lay_ungdung(ung_id)
        if u is None:
            return _trang_ungdung("Không tìm thấy ứng dụng.", False)
        f = request.files.get("file")
        if not f or not getattr(f, "filename", ""):
            return redirect(f"/deployos/ungdung/{ung_id}")
        ten = ten_an_toan(f.filename)
        if not ten or ten == "_thongtin.json":
            return _trang_ungdung("Tên file không hợp lệ.", False)
        thu_muc = os.path.join(UNGDUNG_DIR, ten_an_toan(ung_id))
        try:
            f.save(os.path.join(thu_muc, ten))
        except OSError as e:
            return _trang_ungdung(f"Không lưu được: {e}", False)
        return redirect(f"/deployos/ungdung/{ung_id}")
