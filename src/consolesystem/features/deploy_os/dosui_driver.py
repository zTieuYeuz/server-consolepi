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


def _trang_drivers(msg="", ok=True):
    ds = danh_sach_driver()
    hang = ""
    for dr in ds:
        hang += f"""
            <tr>
              <td><strong>{_esc(dr['ten_hien_thi'])}</strong>{
                '' if dr['so_inf'] else '<br><small style="color:#f59e0b;">chưa có file .inf nào</small>'}</td>
              <td>{dr['so_inf']} .inf</td>
              <td>{_o_model(dr['id'], dr['model'], 'ds') if not dr['cho_boot'] else
                   '<small style="color:#8b93a1;">mọi máy (đã nạp vào ảnh boot)</small>'}</td>
              <td>{
                '<span style="color:#4CAF50;">Có - nạp vào WinPE</span>'
                if dr['cho_boot'] else
                '<span style="color:#8b93a1;">Không</span>'}
                <form method="POST" action="/deployos/drivers/cho-boot"
                      style="display:inline;margin-left:6px;">
                  <input type="hidden" name="driver_id" value="{_esc(dr['id'])}">
                  <input type="hidden" name="bat" value="{'0' if dr['cho_boot'] else '1'}">
                  <button type="submit" class="small gray">{
                    'Bỏ' if dr['cho_boot'] else 'Đánh dấu'}</button>
                </form>
              </td>
              <td>
                <a class="btn small" href="/deployos/drivers/{_esc(dr['id'])}">Quản lý file</a>
                <form method="POST" action="/deployos/drivers/xoa" style="display:inline;"
                      onsubmit="return confirm('Xóa gói driver này?');">
                  <input type="hidden" name="driver_id" value="{_esc(dr['id'])}">
                  <button type="submit" class="red small">Xóa</button>
                </form>
              </td>
            </tr>"""
    bang = (f"""<div class="tbl-scroll"><table>
              <tr><th>Tên gói</th><th style="width:70px;">Driver</th>
                  <th>Tự nạp cho dòng máy</th>
                  <th style="width:210px;">Nạp vào ảnh boot</th>
                  <th style="width:190px;">Thao tác</th></tr>
              {hang}
            </table></div>""" if ds else
        '<p style="color:#8b93a1;">Chưa có gói driver nào.</p>')
    body = (_tabs("tainguyen", "drivers") + _msg(msg, ok) + _khoi_goi_pho_bien()
            + f"""
        <div class="card">
          <h3>Thêm gói driver mới</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
            Đặt tên để nhận biết (vd "Dell Latitude 5420 - LAN+WiFi"). Sau
            khi tạo, vào "Quản lý file" để tải lên driver: file lẻ
            .inf/.sys/.cat hoặc cả gói của hãng (Dell .cab, HP .exe, .zip).
            Ghi <strong>dòng máy</strong> cho gói thì máy đúng dòng đó cài qua PXE
            sẽ tự được nạp gói, không cần chọn trong từng kịch bản.</p>
          <form method="POST" action="/deployos/drivers/tao">
            <input type="text" name="ten_hien_thi" placeholder="Tên gói driver" required>
            <button type="submit">Tạo</button>
          </form>
        </div>
        <h2>Gói driver đã có ({len(ds)})</h2>
        {bang}{_datalist_model() if ds else ""}""")
    return _trang(body, "Cài Windows qua mạng", "Driver")


def _khoi_goi_pho_bien():
    """Khung "Goi driver pho bien" - xem ui/goidriver.py."""
    from ui import goidriver as _gd
    ds = _gd.danh_sach_goi()
    if not ds:
        return ""
    dang = any(g["dang_tai"] for g in ds)
    hang = ""
    for g in ds:
        if g["dang_tai"]:
            tt = f'<span style="color:#f59e0b;">{_esc(g["thong_bao"])}</span>'
        elif g["da_tai"]:
            tt = '<span style="color:#4CAF50;">&#10003; Đã có - nạp vào ảnh boot</span>'
        else:
            tt = '<span style="color:#8b93a1;">Chưa tải</span>'
        if g["thong_bao"] and not g["dang_tai"]:
            tt += f'<br><small style="color:#8b93a1;">{_esc(g["thong_bao"])}</small>'
        nut = "" if g["dang_tai"] else f"""
                <form method="POST" action="/deployos/drivers/goi-pho-bien/tai" style="display:inline;">
                  <input type="hidden" name="ma" value="{_esc(g['ma'])}">
                  <button type="submit" class="small{' gray' if g['da_tai'] else ''}">{
                    'Tải lại' if g['da_tai'] else 'Tải'}</button>
                </form>"""
        hang += (f"<tr><td><strong>{_esc(g['ten_hien_thi'])}</strong><br>"
                 f"<small style='color:#8b93a1;'>{_esc(g.get('mo_ta', ''))}<br>"
                 f"Nguồn: {_esc(g.get('nguon', ''))}</small></td>"
                 f"<td style='width:90px;'>{co_kich_thuoc(g.get('dung_luong', 0))}</td>"
                 f"<td style='width:230px;'>{tt}</td><td style='width:90px;'>{nut}</td></tr>")
    lam_moi = '<meta http-equiv="refresh" content="4">' if dang else ""
    so_co = sum(1 for g in ds if g["da_tai"])
    # Mac dinh: dang tai / con goi chua co -> MO (de thay can lam gi); da co du ->
    # THU GON cho trang ngan. Nguoi dung bam tieu de de thu gon / mo rong, lua chon duoc
    # nho (localStorage) - trang tu lam moi luc dang tai khong lam mat lua chon do.
    mo = " open" if (dang or so_co < len(ds)) else ""
    return f"""{lam_moi}
        <div class="card">
         <details id="goi-pho-bien"{mo}>
          <summary style="cursor:pointer;">
            <h3 style="display:inline;">Gói driver phổ biến cho ảnh boot (tải từ Microsoft)</h3>
            <span style="color:#8b93a1;font-size:13px;margin-left:10px;">{so_co}/{len(ds)} gói đã có
              &middot; bấm vào đây để thu gọn / mở rộng</span>
          </summary>
          <p style="color:#8b93a1;font-size:13px;margin:10px 0 10px;">
            WinPE của Windows 10/11 KHÔNG có sẵn driver cho các card mạng / bộ
            điều khiển ổ đĩa dưới đây - máy dùng chúng sẽ không có mạng hoặc
            không thấy ổ cứng khi cài. Bấm <strong>Tải</strong>: Console Pi tự tải
            gói driver chính thức (đã được Microsoft ký) từ Microsoft Update
            Catalog, giải nén và đánh dấu nạp vào ảnh boot. Windows sau khi cài
            cũng dùng luôn các driver này.
            <strong>Máy tự tải các gói còn thiếu ngay khi có Internet</strong>
            (15 gói card mạng + ổ đĩa, tổng khoảng 6 MB); riêng 3 gói <strong>VirtIO</strong> đã có sẵn
            trong ISO, dùng được cả khi không có mạng.</p>
          <form method="POST" action="/deployos/drivers/goi-pho-bien/tai" style="margin-bottom:10px;">
            <input type="hidden" name="ma" value="__tat_ca__">
            <button type="submit"{' disabled' if dang else ''}>Tải tất cả gói chưa có</button>
          </form>
          <div class="tbl-scroll"><table>
            <tr><th>Gói</th><th>Dung lượng</th><th>Trạng thái</th><th></th></tr>
            {hang}
          </table></div>
          <p style="color:#8b93a1;font-size:12px;margin:10px 0 0;">
            <strong>Máy ảo VMware dùng "LSI Logic Parallel"</strong>: Microsoft
            không có driver loại này cho Windows 10/11 (đã bỏ từ Windows 8), nên
            không gói nào tải được. Đổi bộ điều khiển ổ đĩa của máy ảo sang
            <strong>LSI Logic SAS</strong> (WinPE có sẵn), <strong>NVMe</strong>
            hoặc <strong>VMware Paravirtual</strong> (tải gói PVSCSI ở trên).
            Card mạng nên chọn <strong>E1000E</strong> hoặc
            <strong>VMXNET3</strong> (tải gói ở trên), tránh E1000.</p>
         </details>
        </div>
        <script>
        (function() {{
          var d = document.getElementById('goi-pho-bien');
          if (!d) return;
          try {{
            var v = localStorage.getItem('goi-pho-bien');
            if (v === '1') d.open = true; else if (v === '0') d.open = false;
          }} catch (e) {{}}
          d.addEventListener('toggle', function() {{
            try {{ localStorage.setItem('goi-pho-bien', d.open ? '1' : '0'); }} catch (e) {{}}
          }});
        }})();
        </script>"""


def _goi_y_model():
    """Hang + model cac may da cai (trang Lich su) - goi y khi gan dong may."""
    try:
        from ui import lichsu as _ls
        thay = []
        for b in _ls.danh_sach():
            t = " ".join(x for x in (b.get("hang"), b.get("model")) if x)
            if t and t not in thay:
                thay.append(t)
            if b.get("phien_ban") and b["phien_ban"] not in thay:
                thay.append(b["phien_ban"])
        return thay[:50]
    except Exception:
        return []


def _datalist_model():
    goi_y = "".join(f'<option value="{_esc(m)}">' for m in _goi_y_model())
    return f'<datalist id="goi-y-model">{goi_y}</datalist>'


def _o_model(driver_id, model, ve=""):
    return f"""
          <form method="POST" action="/deployos/drivers/{_esc(driver_id)}/model"
                style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin:0;">
            <input type="hidden" name="ve" value="{_esc(ve)}">
            <input type="text" name="model" list="goi-y-model" value="{_esc(', '.join(model))}"
                   placeholder="vd: Latitude 5420, EliteBook 840 G8" style="min-width:200px;flex:1;">
            <button type="submit" class="small">Lưu</button>
          </form>"""


def _trang_driver_chitiet(driver_id, msg="", ok=True):
    ds = danh_sach_driver()
    dr = next((x for x in ds if x["id"] == driver_id), None)
    if dr is None:
        return _trang_drivers("Không tìm thấy gói driver.", False)
    p = os.path.join(DRIVERS_DIR, ten_an_toan(driver_id))
    hang = ""
    try:
        for n in sorted(os.listdir(p)):
            if n == "_thongtin.json":
                continue
            fp = os.path.join(p, n)
            if os.path.isdir(fp):
                so = sum(1 for _g, _d2, fs in os.walk(fp) for x in fs
                         if x.lower().endswith(".inf"))
                hang += f"""
                <tr><td>&#128193; {_esc(n)}<br><small style="color:#8b93a1;">thư mục đã giải nén &middot; {so} file .inf</small></td><td></td>
                    <td><form method="POST" action="/deployos/drivers/{_esc(driver_id)}/xoa-file"
                              style="display:inline;" onsubmit="return confirm('Xóa cả thư mục này?');">
                          <input type="hidden" name="ten" value="{_esc(n)}">
                          <button type="submit" class="red small">Xóa</button>
                        </form></td></tr>"""
                continue
            if not os.path.isfile(fp):
                continue
            hang += f"""
                <tr><td>{_esc(n)}</td><td>{co_kich_thuoc(os.path.getsize(fp))}</td>
                    <td><form method="POST" action="/deployos/drivers/{_esc(driver_id)}/xoa-file"
                              style="display:inline;">
                          <input type="hidden" name="ten" value="{_esc(n)}">
                          <button type="submit" class="red small">Xóa</button>
                        </form></td></tr>"""
    except OSError:
        pass
    bang = (f"""<div class="tbl-scroll"><table>
              <tr><th>File</th><th>Dung lượng</th><th style="width:90px;">Thao tác</th></tr>
              {hang}
            </table></div>""" if hang else
        '<p style="color:#8b93a1;">Chưa có file nào trong gói này.</p>')
    body = (_tabs("tainguyen", "drivers") + _msg(msg, ok) + f"""
        <p><a href="/deployos/drivers">&larr; Về danh sách driver</a></p>
        <h2>{_esc(dr['ten_hien_thi'])}</h2>
        <p style="color:#8b93a1;">{dr['so_inf']} file .inf trong gói.</p>
        <div class="card">
          <h3>Dùng cho dòng máy</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 10px;">
            Ghi các dòng máy cần gói này, cách nhau dấu phẩy. Khi máy cài qua PXE,
            Console System đọc hãng/model trong BIOS của máy: khớp dòng nào thì
            <strong>tự nạp gói này</strong> vào Windows, không cần chọn trong kịch bản.
            Không phân biệt hoa thường; "Latitude 5420" khớp "Dell Inc. Latitude 5420".
            Model các máy đã cài (tab Tiến trình &rarr; Lịch sử) được gợi ý khi gõ.
            Để trống = chỉ dùng khi chọn gói trong kịch bản.</p>
          {_o_model(driver_id, dr['model'])}{_datalist_model()}
        </div>
        {bang}
        <div class="card" style="margin-top:14px;">
          <h3>Tải lên file driver</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 10px;">
            Nhận file lẻ .inf/.sys/.cat/.dll, hoặc <strong>cả gói của hãng</strong>:
            Dell Driver Pack (.cab), HP SoftPaq (.exe), file .zip/.7z &mdash; Console
            System tự giải nén (gói lớn mất vài phút, đừng tắt trang).</p>
          <form method="POST" action="/deployos/drivers/{_esc(driver_id)}/len"
                enctype="multipart/form-data" class="form-tai-len">
            <input type="file" name="file" required>
            <button type="submit">Tải lên</button>
          </form>
        </div>""")
    return _trang(body, "Cài Windows qua mạng", f"Driver - {dr['ten_hien_thi']}")


def register_driver(app):
    # ----------------------------- driver (mo hinh MDT: "Out-of-Box Drivers")
    @app.route("/deployos/drivers")
    def deployos_drivers():
        return _trang_drivers()

    @app.route("/deployos/drivers/goi-pho-bien/tai", methods=["POST"])
    def deployos_drivers_goi_tai():
        from ui import goidriver as _gd
        ma = request.form.get("ma", "")
        if ma == "__tat_ca__":
            cac = [g["ma"] for g in _gd.danh_sach_goi() if not g["da_tai"]]
        else:
            cac = [ma]
        ok, msg = _gd.tai_goi(cac)
        if ok:
            # Ve trang GET de the meta refresh tu lam moi khong gui lai POST
            return redirect("/deployos/drivers")
        return _trang_drivers(msg, ok)

    @app.route("/deployos/drivers/tao", methods=["POST"])
    def deployos_drivers_tao():
        ok, msg, driver_id = tao_driver_moi(request.form.get("ten_hien_thi", ""))
        if ok:
            return redirect(f"/deployos/drivers/{driver_id}")
        return _trang_drivers(msg, ok)

    @app.route("/deployos/drivers/xoa", methods=["POST"])
    def deployos_drivers_xoa():
        ok, msg = xoa_driver(request.form.get("driver_id", ""))
        return _trang_drivers(msg, ok)

    @app.route("/deployos/drivers/cho-boot", methods=["POST"])
    def deployos_drivers_cho_boot():
        ok, msg = dat_driver_cho_boot(request.form.get("driver_id", ""),
                                      request.form.get("bat") == "1")
        return _trang_drivers(msg, ok)

    @app.route("/deployos/drivers/<driver_id>")
    def deployos_drivers_chitiet(driver_id):
        return _trang_driver_chitiet(driver_id)

    @app.route("/deployos/drivers/<driver_id>/len", methods=["POST"])
    def deployos_drivers_len(driver_id):
        f = request.files.get("file")
        if not f or not getattr(f, "filename", ""):
            return redirect(f"/deployos/drivers/{driver_id}")
        duong = getattr(getattr(f, "stream", None), "_cp_duong_dan", None)
        if duong:
            try:
                f.stream.flush()
                os.fsync(f.stream.fileno())
            except Exception as _loi:
                _bo_qua(_loi)
            thu_muc = os.path.join(DRIVERS_DIR, ten_an_toan(driver_id))
            ok, msg, _duong_dich = _hoan_tat_ghi_thang(duong, thu_muc, f.filename)
            if ok and os.path.splitext(_duong_dich)[1].lower() in EXT_GOI_NEN_DRIVER:
                ok, msg = giai_nen_goi_driver(driver_id, _duong_dich)
        else:
            ok, msg = False, ("Đuôi file không được nhận (.inf/.sys/.cat/"
                              ".dll/.zip/.cab/.7z/.exe) hoặc không ghi thẳng được.")
        return _trang_driver_chitiet(driver_id, msg, ok)

    @app.route("/deployos/drivers/<driver_id>/model", methods=["POST"])
    def deployos_drivers_model(driver_id):
        ok, msg = dat_model_driver(driver_id, request.form.get("model", ""))
        if request.form.get("ve") == "ds":
            return _trang_drivers(msg, ok)
        return _trang_driver_chitiet(driver_id, msg, ok)

    @app.route("/deployos/drivers/<driver_id>/xoa-file", methods=["POST"])
    def deployos_drivers_xoa_file(driver_id):
        ok, msg = xoa_file_trong_driver(driver_id, request.form.get("ten", ""))
        if ok:
            return redirect(f"/deployos/drivers/{driver_id}")
        return _trang_drivers(msg, ok)
