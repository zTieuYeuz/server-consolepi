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
from flask import (request, redirect, jsonify)
from ui.home import _esc
from consolesystem.features.deploy_os.dosui_chung import (_msg, _tabs, _trang)  # noqa: F401


def _trang_os(msg="", ok=True):
    ds = danh_sach_os()
    hang = ""
    for o in ds:
        trang_thai = ('<span style="color:#4CAF50;">Sẵn sàng</span>' if o["san_sang"]
                      else '<span style="color:#e0a030;">Thiếu file</span>')
        hang += f"""
            <tr>
              <td><strong>{_esc(o['ten_hien_thi'])}</strong>
                  <div style="color:#8b93a1;font-size:12px;">{_esc(o['id'])}</div></td>
              <td>{_esc(o['os_ho'])}</td>
              <td>{trang_thai}</td>
              <td>{_esc(o['kich_thuoc'])}</td>
              <td>
                <a class="btn small" href="/deployos/os/{_esc(o['id'])}">Quản lý file</a>
                <form method="POST" action="/deployos/os/xoa" style="display:inline;"
                      onsubmit="return confirm('Xóa toàn bộ hệ điều hành này?');">
                  <input type="hidden" name="os_id" value="{_esc(o['id'])}">
                  <button type="submit" class="red small">Xóa</button>
                </form>
              </td>
            </tr>"""
    bang = (f"""<div class="tbl-scroll"><table data-pt="25" data-pt-tim="1">
              <tr><th>Tên</th><th>Họ</th><th>Trạng thái</th><th>Dung lượng</th>
                  <th style="width:190px;">Thao tác</th></tr>
              {hang}
            </table></div>""" if ds else
        '<p style="color:#8b93a1;">Chưa có hệ điều hành nào.</p>')
    body = (_tabs("tainguyen", "os") + _msg(msg, ok) + f"""
        <div class="card">
          <h3>Thêm hệ điều hành mới</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
            Đặt tên (vd "Windows 10 Pro", "Windows 11 Pro") - sau khi tạo,
            vào "Quản lý file" để tải lên <code>boot.wim</code> và
            <code>install.wim</code> (lấy từ <code>sources\\</code> của
            ISO Windows thật, Pi KHÔNG tự tạo được).</p>
          <form method="POST" action="/deployos/os/tao">
            <input type="text" name="ten_hien_thi" placeholder="Tên hệ điều hành" required>
            <select name="os_ho">
              <option value="windows">Windows</option>
              <option value="linux">Linux</option>
            </select>
            <button type="submit">Tạo</button>
          </form>
        </div>
        <h2>Hệ điều hành đã có ({len(ds)})</h2>
        {bang}""")
    return _trang(body, "Deployment OS", "Hệ điều hành")


def register_os(app):
    # ------------------------- he dieu hanh (mo hinh MDT: "Operating Systems")
    @app.route("/deployos/os")
    def deployos_os():
        return _trang_os()

    @app.route("/deployos/os/tao", methods=["POST"])
    def deployos_os_tao():
        ok, msg, os_id = tao_os_moi(request.form.get("ten_hien_thi", ""),
                                    request.form.get("os_ho", "windows"))
        if ok:
            return redirect(f"/deployos/os/{os_id}")
        return _trang_os(msg, ok)

    @app.route("/deployos/os/xoa", methods=["POST"])
    def deployos_os_xoa():
        ok, msg = xoa_os(request.form.get("os_id", ""))
        return _trang_os(msg, ok)

    @app.route("/deployos/os/<os_id>")
    def deployos_os_chitiet(os_id):
        o = lay_os(os_id)
        if o is None:
            return _trang_os("Không tìm thấy hệ điều hành.", False)
        hang = ""
        for ten_file, nhan in (("boot.wim", "boot.wim (WinPE)"),
                              ("install.wim", "install.wim (ảnh cài đặt)")):
            fp = os.path.join(OS_DIR, ten_an_toan(os_id), ten_file)
            co = os.path.isfile(fp)
            kich_thuoc = co_kich_thuoc(os.path.getsize(fp)) if co else "-"
            trang_thai = ('<span style="color:#4CAF50;">Đã có</span>' if co
                          else '<span style="color:#e0a030;">Chưa có</span>')
            hang += f"""
            <tr><td>{nhan}</td><td>{trang_thai}</td><td>{kich_thuoc}</td></tr>"""
        cab = co_sxs(os_id)
        hang += ("""
            <tr><td>sxs\\*.cab (.NET 3.5 offline, không bắt buộc)</td><td>""" +
                 ('<span style="color:#4CAF50;">Đã có</span>' if cab else
                  '<span style="color:#8b93a1;">Chưa có</span>') +
                 "</td><td>" + (", ".join(_esc(x) for x in cab) if cab else "-") + "</td></tr>")
        body = (_tabs("tainguyen", "os") + f"""
        <p><a href="/deployos/os">&larr; Về danh sách hệ điều hành</a></p>
        <h2>{_esc(o['ten_hien_thi'])}</h2>
        <div class="tbl-scroll"><table>
          <tr><th>File</th><th>Trạng thái</th><th>Dung lượng</th></tr>
          {hang}
        </table></div>
        <div class="card" style="margin-top:14px;">
          <h3>Thêm ảnh hệ điều hành</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 12px;">
            Chọn cách anh đang có sẵn file trong tay:</p>
          <label for="kieu-tai">Kiểu file bạn có</label>
          <select id="kieu-tai" style="max-width:420px;">
            <option value="iso">Tôi có file ISO Windows (Pi tự tách ra) — dễ nhất</option>
            <option value="wim">Tôi đã có sẵn boot.wim / install.wim</option>
          </select>

          <!-- ===== Cach 1: tai thang file ISO ===== -->
          <div id="khoi-iso" style="margin-top:16px;">
            <div class="msg info" style="margin-top:0;">
              <strong>Cách này đơn giản nhất:</strong> anh chỉ cần tải nguyên
              file ISO Windows tải từ Microsoft lên đây. Pi sẽ tự:
              <br>1. Đọc mục lục ISO tìm 2 file cần
              <br>2. Tách riêng <code>boot.wim</code> và <code>install.wim</code> ra
              <br>3. Kiểm chứng kỹ 2 file đó (đúng dung lượng + đọc được ruột)
              <br>4. Chỉ khi kiểm chứng ĐẠT mới xoá file ISO để lấy lại dung lượng
              <br><span style="color:#8A94A6;">Nếu kiểm chứng trượt, ISO được giữ
              nguyên để tách lại — không bao giờ mất công tải lại.</span>
            </div>
            <form method="POST" action="/deployos/os/{_esc(os_id)}/len-iso"
                  enctype="multipart/form-data" class="form-tai-len"
                  data-loai="os-iso" data-os="{_esc(os_id)}"
                  data-busy="Đang tải ISO lên...">
              <input type="file" name="file" accept=".iso" required>
              <button type="submit">Tải ISO lên rồi tách tự động</button>
            </form>
            <p class="hint" style="margin-top:9px;">
              File ISO thường 4–6 GB. Tải xong Pi tách thêm khoảng 5–15 phút
              nữa (có thanh tiến trình từng bước). Cần trống khoảng
              <strong>gấp đôi</strong> dung lượng ISO trong lúc tách.</p>
          </div>

          <!-- ===== Cach 2: tai san 2 file wim ===== -->
          <div id="khoi-wim" hidden style="margin-top:16px;">
            <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
              Dùng khi anh đã tự tách sẵn 2 file từ ISO (mở ISO trên máy
              Windows, vào thư mục <code>sources\\</code> copy ra). Tên file
              phải để <strong>đúng nguyên gốc</strong>:
              <code>boot.wim</code> và <code>install.wim</code>.
              Tải lên <strong>từng file một</strong> — install.wim vài GB nên
              sẽ mất vài phút.</p>
            <form method="POST" action="/deployos/os/{_esc(os_id)}/len"
                  enctype="multipart/form-data" class="form-tai-len"
                  data-loai="os" data-os="{_esc(os_id)}"
                  data-busy="Đang tải lên...">
              <input type="file" name="file" accept=".wim" required>
              <button type="submit">Tải lên</button>
            </form>
          </div>
        </div>

        <div class="card" style="margin-top:14px;">
          <h3>Gói .NET Framework 3.5 offline (không bắt buộc)</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
            Có gói này thì khi cài Windows, tuỳ chọn <strong>"Bật .NET Framework 3.5"</strong>
            chỉ mất khoảng 1 phút (bật ngay lúc bung ảnh) thay vì tải qua mạng gần 9 phút.
            Tải ISO lên ở trên thì Pi tự lấy sẵn. Nếu anh tải sẵn 2 file wim thì chép thư mục
            <code>sources\\sxs</code> trong ISO ra, tải file
            <code>microsoft-windows-netfx3-ondemand-package~31bf3856ad364e35~amd64~~.cab</code>
            vào đây. <strong>Phải đúng bản Windows</strong> (bản Windows 10 dùng cho Windows 10,
            bản Windows 11 dùng cho Windows 11) — sai bản thì tự quay về tải qua mạng.</p>
          <form method="POST" action="/deployos/os/{_esc(os_id)}/len-sxs"
                enctype="multipart/form-data" class="form-tai-len"
                data-loai="os-sxs" data-os="{_esc(os_id)}" data-busy="Đang tải lên...">
            <input type="file" name="file" accept=".cab" required>
            <button type="submit">Tải gói .cab lên</button>
          </form>
        </div>

        <script>
        (function() {{
          var sel = document.getElementById('kieu-tai');
          var kIso = document.getElementById('khoi-iso');
          var kWim = document.getElementById('khoi-wim');
          if (!sel || !kIso || !kWim) return;
          function doi() {{
            var iso = sel.value === 'iso';
            kIso.hidden = !iso;
            kWim.hidden = iso;
          }}
          sel.addEventListener('change', doi);
          doi();
        }})();
        </script>""")
        return _trang(body, "Deployment OS", f"Hệ điều hành - {o['ten_hien_thi']}")

    @app.route("/deployos/os/<os_id>/len-sxs", methods=["POST"])
    def deployos_os_len_sxs(os_id):
        f = request.files.get("file")
        if not f or not getattr(f, "filename", ""):
            return redirect(f"/deployos/os/{os_id}")
        duong = getattr(getattr(f, "stream", None), "_cp_duong_dan", None)
        ten_goc = ten_an_toan(f.filename)
        if not duong:
            return _trang_os("Chỉ nhận file .cab (gói .NET 3.5 trong thư mục sources\\sxs của ISO).", False)
        try:
            f.stream.flush()
            os.fsync(f.stream.fileno())
        except Exception:
            pass
        thu_muc = os.path.join(OS_DIR, ten_an_toan(os_id), "sxs")
        ok, msg, _d = _hoan_tat_ghi_thang(duong, thu_muc, ten_goc)
        return redirect(f"/deployos/os/{os_id}") if ok else _trang_os(msg, ok)

    @app.route("/deployos/os/<os_id>/len", methods=["POST"])
    def deployos_os_len(os_id):
        f = request.files.get("file")
        if not f or not getattr(f, "filename", ""):
            return redirect(f"/deployos/os/{os_id}")
        duong = getattr(getattr(f, "stream", None), "_cp_duong_dan", None)
        ten_goc = ten_an_toan(f.filename)
        if ten_goc not in ("boot.wim", "install.wim"):
            return _trang_os(
                f'Chỉ nhận đúng tên "boot.wim" hoặc "install.wim" '
                f'(file bạn tải lên tên là "{ten_goc}") - đổi tên lại cho '
                f'đúng như trên ISO Windows gốc.', False)
        if duong:
            try:
                f.stream.flush()
                os.fsync(f.stream.fileno())
            except Exception:
                pass
            thu_muc = os.path.join(OS_DIR, ten_an_toan(os_id))
            ok, msg, _duong_dich = _hoan_tat_ghi_thang(duong, thu_muc, ten_goc)
        else:
            ok, msg = False, "Không ghi thẳng được file - thử lại."
        if ok:
            return redirect(f"/deployos/os/{os_id}")
        return _trang_os(msg, ok)

    # ------------------------------------------- tai len ISO + tu dong tach
    @app.route("/deployos/os/<os_id>/len-iso", methods=["POST"])
    def deployos_os_len_iso(os_id):
        """
        Nhan file ISO Windows roi giao cho ui/isotach.py tach nen.

        File ISO da duoc ghi THANG ra dia trong luc tai len (xem
        _thu_muc_os_theo_duong + RequestTaiLenThang), o day chi con viec doi
        ten .part -> ten that roi bat luong tach.
        """
        from ui import isotach as _it
        f = request.files.get("file")
        if not f or not getattr(f, "filename", ""):
            return redirect(f"/deployos/os/{os_id}")
        ten_goc = ten_an_toan(f.filename)
        if not ten_goc.lower().endswith(".iso"):
            return _trang_os(f'Cần file .iso (file bạn chọn là "{ten_goc}").', False)
        if _it.dang_chay():
            return _trang_os("Đang tách một file ISO khác - đợi xong rồi làm tiếp.", False)

        duong = getattr(getattr(f, "stream", None), "_cp_duong_dan", None)
        if not duong:
            return _trang_os("Không ghi thẳng được file ISO - thử lại.", False)
        try:
            f.stream.flush()
            os.fsync(f.stream.fileno())
        except Exception:
            pass
        thu_muc = os.path.join(OS_DIR, ten_an_toan(os_id))
        ok, msg, duong_dich = _hoan_tat_ghi_thang(duong, thu_muc, ten_goc)
        if not ok:
            return _trang_os(msg, False)

        ok, msg = _it.bat_dau_tach(ten_an_toan(os_id), duong_dich)
        if not ok:
            return _trang_os(msg, False)
        return redirect(f"/deployos/os/{os_id}/tach")

    @app.route("/deployos/os/<os_id>/tach")
    def deployos_os_tach(os_id):
        """Trang theo doi tien trinh tach ISO - tu lam moi bang JS."""
        o = lay_os(os_id)
        if o is None:
            return _trang_os("Không tìm thấy hệ điều hành.", False)
        body = _tabs("tainguyen", "os") + f"""
        <p><a href="/deployos/os/{_esc(os_id)}">&larr; Về {_esc(o['ten_hien_thi'])}</a></p>
        <div class="card">
          <h3>Đang tách file ISO</h3>
          <p class="hint" style="margin:0 0 14px;">Anh có thể rời trang này,
            việc tách vẫn chạy tiếp ở máy. Quay lại đây bất cứ lúc nào để xem.</p>
          <div style="background:#0B0E14;border:1px solid #1F2733;border-radius:8px;
                      height:14px;overflow:hidden;margin-bottom:6px;">
            <div id="thanh" style="height:100%;width:0%;background:#38BDF8;
                 transition:width .4s;"></div>
          </div>
          <div class="row" style="justify-content:space-between;">
            <span id="nhan-buoc" style="color:#8A94A6;font-size:13.5px;">Đang bắt đầu...</span>
            <span id="nhan-phan-tram" style="font-family:ui-monospace,monospace;
                  font-weight:600;">0%</span>
          </div>
          <div id="ket-qua"></div>
          <div id="nhat-ky" style="margin-top:14px;"></div>
        </div>
        <script>
        (function() {{
          var thanh = document.getElementById('thanh');
          var nBuoc = document.getElementById('nhan-buoc');
          var nPt = document.getElementById('nhan-phan-tram');
          var kq = document.getElementById('ket-qua');
          var nk = document.getElementById('nhat-ky');
          var BIEU = {{ok: '\u2714', loi: '\u2716', dang: '\u22EF'}};
          var MAU = {{ok: '#4ADE80', loi: '#F87171', dang: '#38BDF8'}};

          function ve(t) {{
            thanh.style.width = t.phan_tram + '%';
            nPt.textContent = t.phan_tram + '%';
            nBuoc.textContent = t.ten_buoc
              ? ('Bước ' + t.buoc + '/' + t.tong_buoc + ': ' + t.ten_buoc)
              : 'Đang bắt đầu...';
            var h = '';
            for (var i = 0; i < t.nhat_ky.length; i++) {{
              var d = t.nhat_ky[i];
              h += '<div style="display:flex;gap:9px;padding:7px 0;border-bottom:1px solid #1F2733;">'
                 + '<span style="color:' + (MAU[d[1]] || '#8A94A6') + ';flex:none;">'
                 + (BIEU[d[1]] || '') + '</span><div><div>' + d[0] + '</div>'
                 + (d[2] ? '<div style="color:#8A94A6;font-size:12.5px;margin-top:2px;">'
                           + d[2] + '</div>' : '') + '</div></div>';
            }}
            nk.innerHTML = h;
            if (!t.chay && t.xong === true) {{
              thanh.style.background = '#4ADE80';
              kq.innerHTML = '<div class="msg ok">Tách xong! Hệ điều hành đã sẵn sàng '
                + '(mất ' + t.giay + ' giây). '
                + '<a href="/deployos/os/{_esc(os_id)}">Xem lại &rarr;</a></div>';
            }} else if (!t.chay && t.xong === false) {{
              thanh.style.background = '#F87171';
              kq.innerHTML = '<div class="msg err">' + (t.loi || 'Tách thất bại.') + '</div>';
            }}
          }}

          function hoi() {{
            fetch('/deployos/os/tach/tien-do', {{cache: 'no-store'}})
              .then(function(r) {{ return r.json(); }})
              .then(function(t) {{
                ve(t);
                if (t.chay) setTimeout(hoi, 1200);
              }})
              .catch(function() {{ setTimeout(hoi, 3000); }});
          }}
          hoi();
        }})();
        </script>"""
        return _trang(body, "Deployment OS", f"Tách ISO - {o['ten_hien_thi']}")

    @app.route("/deployos/os/tach/tien-do")
    def deployos_os_tach_tien_do():
        from ui import isotach as _it
        return jsonify(_it.trang_thai())
