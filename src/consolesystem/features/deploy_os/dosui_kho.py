# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Tach tu deployos.py (B4).

(B4: tach nguyen van tu deployos.py::register_deployos; ten ham/route giu nguyen.)"""
import json
import os
import secrets
import shutil
import time
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
from flask import (request, redirect, jsonify,
                   session, g)
from ui.home import _esc
from consolesystem.features.deploy_os.dosui_chung import (_msg, _tabs, _trang)  # noqa: F401


# ==================================== TAB "KHO TRUNG TÂM"
# Xem ui/khotrungtam.py cho phan goi HTTP thuc su. O day chi la giao
# dien: ket noi (ma 6 ky tu), tim/loc, tai o nen vao dung thu muc cuc
# bo (APPS_DIR / SCRIPTS_DIR / 1 he dieu hanh moi trong OS_DIR).
TEN_LOAI_KHO = {"phanmem": "Phần mềm", "ungdung": "Ứng dụng nhiều file", "script": "Script", "os": "Hệ điều hành",
                "winpe": "WinPE", "font": "Font chữ"}


# Tai ve nam o thu muc tai nguyen CHUNG (deploy/apps, scripts, ungdung, fonts, os): ca 2 tinh nang deu doc cung cho
DUNG_CHO = {"os": "Cài Windows qua mạng", "winpe": "Cài Windows qua mạng", "phanmem": "Cả hai", "ungdung": "Cả hai", "font": "Cả hai", "script": "Cả hai"}


def _dau_kho():
    return ('<div class="card" style="padding:14px 18px;"><b>Kho dùng chung.</b> <span class="tk-ghi">Tải một lần, dùng ở cả hai nơi: '
            'Mọi thứ tải về nằm trong <a href="/tai-nguyen">Tài nguyên máy</a> (Kho lưu trữ), dùng chung cho Cài Windows qua mạng và Cài phần mềm qua LAN.</span></div>')


def _bo_font_tu_kho(muc_id):
    """Bo font da tao tu muc kho nay (ghi kho_id trong _thongtin.json), hoac None."""
    for b in danh_sach_bo_font():
        if _doc_meta_bo_font(os.path.join(FONTS_DIR, b["id"])).get("kho_id") == muc_id:
            return b
    return None


def _da_co_tu_kho(m, cac_os):
    """Muc kho nay da co tren Console Pi chua (de hien "Đã có")."""
    loai = m.get("loai", "")
    if loai == "os":
        return any(o["kho_id"] == m.get("id") and o["san_sang"] for o in cac_os)
    if loai == "ungdung":
        # Da tai VA giai nen xong (con file .zip/.part = dang tai do dang, chua tinh)
        for u in danh_sach_ungdung():
            if _doc_meta_ungdung(u["id"]).get("kho_id") == m.get("id"):
                d = os.path.join(UNGDUNG_DIR, u["id"])
                return any(not x.endswith((".zip", ".part")) and x != "_thongtin.json"
                           for x in os.listdir(d))
        return False
    if loai == "font":
        b = _bo_font_tu_kho(m.get("id"))
        return bool(b and b["so_font"])
    if loai == "winpe":
        from ui import winperieng as _wr
        ten = ten_an_toan(m.get("ten_file", ""))
        if ten.lower().endswith(".iso"):
            ten = _wr.ten_wim_tu_iso(ten)
        return any(x["file"] == ten for x in _wr.danh_sach())
    thu_muc = {"phanmem": APPS_DIR, "script": SCRIPTS_DIR}.get(loai)
    return bool(thu_muc and os.path.isfile(
        os.path.join(thu_muc, ten_an_toan(m.get("ten_file", "")))))


def _trang_kho(msg="", ok=True):
    from ui import khotrungtam as _kt

    cauhinh = _kt.doc_cauhinh()
    if not cauhinh and not msg:
        # 1.7.0: may tu ket noi kho - mo trang la thu ngay, khong bat
        # nguoi dung doi luong nen (cach nhau toi thieu 5 giay)
        tu_ok, tu_msg = _kt.thu_dang_ky_ngay(cach_toi_thieu=5)
        cauhinh = _kt.doc_cauhinh()
        if cauhinh:
            msg, ok = "Máy đã tự kết nối kho trung tâm.", True
    if not cauhinh:
        tu_msg = _kt.LAN_THU_CUOI.get("msg") or "Đang chờ kết nối..."
        body = _dau_kho() + _msg(msg, ok) + f"""
            <div class="card">
              <h3>Máy đang tự kết nối kho</h3>
              <p style="margin:0 0 10px;">Máy tự kết nối kho khi có Internet, không cần điền gì.
                Lần thử gần nhất: <strong>{_esc(tu_msg)}</strong></p>
              <a href="/kho-trung-tam"><button type="button">🔄 Thử lại ngay</button></a>
              <p style="color:#8b93a1;font-size:13px;margin:10px 0 0;">Máy tự thử lại mỗi 2 phút.
                Cắm dây mạng hoặc kết nối WiFi rồi bấm Thử lại.</p>
            </div>""" + """
            <div class="card">
              <h3>Hoặc kết nối bằng mã</h3>
              <p style="color:#8b93a1;font-size:13px;margin:0 0 12px;">
                Kho trung tâm lưu sẵn phần mềm, script và hệ điều hành (ISO) dùng
                chung cho mọi Console Pi. Trên trang kho vào mục
                <strong>Kết nối Console Pi</strong> &rarr; <strong>Tạo mã kết
                nối</strong>, rồi điền 2 ô dưới đây.</p>
              <form method="POST" action="/deployos/kho/ghep">
                <label>Địa chỉ kho</label>
                <input type="text" name="url" placeholder="Ví dụ: kho.congty.vn"
                       autocapitalize="off" autocomplete="off" required>
                <label style="margin-top:10px;display:block;">Mã kết nối (6 ký tự)</label>
                <input type="text" name="ma" maxlength="7" placeholder="Ví dụ: K7M4QX"
                       autocapitalize="characters" autocomplete="off" required
                       style="font-size:22px;letter-spacing:6px;text-transform:uppercase;
                              font-family:ui-monospace,monospace;max-width:260px;">
                <div><button type="submit" style="margin-top:12px;"
                        data-busy="Đang kết nối...">Kết nối</button></div>
              </form>
            </div>"""
        return _trang(body, "Kho trung tâm", "Kho lưu trữ dùng chung - chưa kết nối", active="/kho-trung-tam")

    ok_ds, ket_qua = _kt.danh_sach(cauhinh)
    if not ok_ds:
        body = _dau_kho() + _msg(msg, ok) + f"""
            <div class="msg err">Không lấy được danh sách từ kho: {_esc(ket_qua)}</div>
            <div class="card">
              <a href="/kho-trung-tam"><button type="button">Thử lại</button></a>
            </div>"""
        return _trang(body, "Kho trung tâm", "Kho lưu trữ dùng chung - lỗi kết nối", active="/kho-trung-tam")

    ds = ket_qua
    cac_os = danh_sach_os()
    du_lieu_js = json.dumps([
        {"id": m.get("id", ""),
         "tim": bo_dau(" ".join(str(m.get(k, "")) for k in
                                    ("ten", "mo_ta", "du_lieu", "ten_file")))}
        for m in ds], ensure_ascii=False)

    ten_loai_hien = dict(TEN_LOAI_KHO)
    dem = {k: sum(1 for m in ds if m.get("loai") == k) for k in ten_loai_hien}
    hang = ""
    for m in ds:
        loai = m.get("loai", "")
        ext = os.path.splitext(m.get("ten_file", ""))[1].lower()
        hop_le = ((loai == "phanmem" and ext in EXT_APP) or
                  (loai == "script" and ext in EXT_SCRIPT) or
                  (loai == "os" and ext == ".iso") or
                  (loai == "winpe" and ext in (".wim", ".iso")) or
                  (loai in ("ungdung", "font") and ext == ".zip"))
        nhan_loai = TEN_LOAI_KHO.get(loai, loai)
        cap_nhat = m.get("cap_nhat_luc") or 0
        luc = time.strftime("%d/%m/%Y %H:%M", time.localtime(cap_nhat)) if cap_nhat else ""
        mid = _esc(m.get("id", ""))
        da_co = False
        if not hop_le:
            nut = (f'<span class="hint">Không hỗ trợ ({_esc(ext or "?")})</span>')
        else:
            da_co = _da_co_tu_kho(m, cac_os)
            nut = f"""
                <form method="POST" action="/deployos/kho/tai" style="display:inline;"
                      {'data-ghi-de="1"' if da_co else ''}>
                  <input type="hidden" name="id" value="{mid}">
                  <button type="submit" class="small{' gray' if da_co else ''}">{
                    'Tải lại' if da_co else 'Tải về'}</button>
                </form>""" + (' <span style="color:#4ADE80;font-size:12px;">&#10003; Đã có</span>'
                          if da_co else "")
        phu = _esc(m.get("mo_ta", ""))
        if m.get("du_lieu"):
            nhan_dl = {"os": "Phiên bản", "winpe": "Tên trong menu PXE",
                       "ungdung": "Lệnh cài"}.get(loai, "Tham số")
            phu += (f'<br><span style="color:#8ad4a0;">{nhan_dl}: '
                    f'{_esc(m["du_lieu"])}</span>')
        if loai == "phanmem" and m.get("go_cai"):
            phu += (f'<br><span style="color:#e8c898;">Tham số gỡ: '
                    f'{_esc(m["go_cai"])}</span>')
        o_tich = (f'<input type="checkbox" class="tich-kho" value="{mid}" '
                  f'data-co="{1 if (hop_le and da_co) else 0}" aria-label="Chọn">'
                  if hop_le else '')
        hang += f"""
            <tr data-id="{mid}" data-loai="{_esc(loai)}">
              <td class="cot-tich">{o_tich}</td>
              <td>{nhan_loai}<br><small style="color:var(--chu-mo2);">{DUNG_CHO.get(loai, "")}</small></td>
              <td><strong>{_esc(m.get('ten',''))}</strong><br>
                  <small style="color:#8b93a1;">{phu}</small></td>
              <td>{co_kich_thuoc(m.get('kich_thuoc') or 0)}</td>
              <td>{_esc(luc)}</td>
              <td id="nut-{mid}" style="white-space:nowrap;">{nut}</td>
            </tr>"""

    bang = (f'<div class="tbl-scroll"><table id="bang-kho" data-pt="25"><thead><tr>'
            f'<th class="cot-tich"><input type="checkbox" id="tich-tat-ca" aria-label="Chọn tất cả đang hiện"></th>'
            f'<th>Loại</th><th>Tên</th><th>Kích thước</th><th>Cập nhật</th>'
            f'<th class="cot-nut">&nbsp;</th></tr></thead>'
            f'<tbody>{hang}</tbody></table></div>'
            if ds else '<p style="color:#8b93a1;">Kho chưa có mục nào.</p>')
    loc_nut = "".join(
        f'<button type="button" class="small gray loc-loai" data-loai="{k}">'
        f'{n} ({dem[k]})</button> ' for k, n in ten_loai_hien.items())

    body = _dau_kho() + _msg(msg, ok) + f"""
        <div class="card" id="khung-tai" hidden>
          <h3>Đang tải</h3>
          <div id="canh-bao-tai" hidden style="background:#3a2f12;border:1px solid #6b5418;color:#ffd98a;
               border-radius:8px;padding:8px 12px;margin:0 0 8px;font-size:13px;">
            ⚠ Đang tải — <b>xin đừng tải lại trang (F5) hoặc đóng trang này</b> cho đến khi xong.
            Khi hoàn tất sẽ có bảng thông báo.</div>
          <div id="ds-tai"></div>
        </div>

        <div class="card">
          <div style="margin-bottom:10px;">
            <button type="button" class="small loc-loai" data-loai="">Tất cả ({len(ds)})</button>
            {loc_nut}
          </div>
          <div class="hang-tim">
            <input type="search" id="o-tim-kho" autocomplete="off"
                   placeholder="Tìm trong kho: tên, mô tả... (gõ không dấu cũng được)">
            <button type="button" id="nut-xoa-tim-kho" class="gray">Xoá</button>
          </div>
          <div id="ket-qua-tim-kho" class="ket-qua"></div>
          <form method="POST" action="/deployos/kho/tai-nhieu" id="form-tai-nhieu"
                style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:10px 0;">
            <button type="submit" id="nut-tai-nhieu" disabled data-busy="Đang bắt đầu tải...">
              Tải các mục đã tích (<span id="so-tich">0</span>)</button>
            <button type="button" class="gray" id="nut-bo-tich" hidden>Bỏ chọn</button>
            <span class="hint" id="goi-y-tich">Tích ô đầu mỗi dòng (hoặc ô trên cùng để chọn tất cả mục đang hiện), rồi bấm Tải.</span>
          </form>
          {bang}
        </div>

        <style>
          .xn-nen {{ position:fixed; inset:0; background:rgba(5,8,14,.62); backdrop-filter:blur(3px); display:flex;
                    align-items:center; justify-content:center; z-index:1000; padding:16px; }}
          .xn-hop {{ background:var(--the); border:1px solid var(--vien-ro); border-radius:16px; max-width:460px; width:100%;
                    padding:22px; box-shadow:0 24px 64px rgba(5,8,14,.55); }}
          .xn-hop h3 {{ margin:0 0 10px; font-weight:600; }}
          .xn-hop p {{ margin:0; line-height:1.5; }}
          .xn-nut {{ display:flex; gap:10px; justify-content:flex-end; margin-top:18px; }}
        </style>
        <script>
        (function() {{
          var DU_LIEU = {du_lieu_js};
          var oTim = document.getElementById('o-tim-kho');
          var bang = document.getElementById('bang-kho');
          var kq = document.getElementById('ket-qua-tim-kho');
          var loaiChon = '';
          function boDau(s) {{
            return (s || '').replace(/đ/g, 'd').replace(/Đ/g, 'D')
              .normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase().trim();
          }}
          function loc() {{
            if (!bang) return;
            var q = boDau(oTim.value), tuKhoa = q.split(/\\s+/).filter(Boolean);
            var hienId = {{}};
            for (var k = 0; k < DU_LIEU.length; k++) {{
              var m = DU_LIEU[k], hop = true;
              for (var t = 0; t < tuKhoa.length; t++)
                if (m.tim.indexOf(tuKhoa[t]) === -1) {{ hop = false; break; }}
              if (hop) hienId[m.id] = true;
            }}
            var hang = bang.tBodies[0].rows, so = 0;
            for (var i = 0; i < hang.length; i++) {{
              var h = hang[i], hien = hienId[h.getAttribute('data-id')] &&
                (!loaiChon || h.getAttribute('data-loai') === loaiChon);
              if (hien) h.removeAttribute('data-loc'); else h.setAttribute('data-loc', '1'); if (hien) so++;
            }}
            if (window.csPT) window.csPT.capNhat(bang, true);
            kq.textContent = so + ' / ' + hang.length + ' mục';
            if (typeof capNhatTich === 'function') capNhatTich();
          }}
          var nutLoc = document.querySelectorAll('.loc-loai');
          nutLoc.forEach(function(b) {{
            b.addEventListener('click', function() {{
              loaiChon = b.getAttribute('data-loai');
              nutLoc.forEach(function(x) {{ x.classList.toggle('gray', x !== b); }});
              loc();
            }});
          }});
          if (oTim) {{
            oTim.addEventListener('input', loc);
            document.getElementById('nut-xoa-tim-kho').addEventListener('click',
              function() {{ oTim.value = ''; loc(); oTim.focus(); }});
          }}
          loc();

          // ---- tich chon nhieu muc roi tai 1 lan
          var tatCa = document.getElementById('tich-tat-ca'), ft = document.getElementById('form-tai-nhieu');
          // ---- popup xac nhan giua man hinh (thay confirm() cua trinh duyet)
          function hoiXN(tieu, noi, nhanOk, nguy, lam) {{
            var n = document.createElement('div'); n.className = 'xn-nen';
            n.innerHTML = '<div class="xn-hop" role="dialog" aria-modal="true"><h3></h3><p></p>'
              + '<div class="xn-nut"><button type="button" class="gray xn-huy">Thôi</button>'
              + '<button type="button" class="xn-ok' + (nguy ? ' red' : '') + '"></button></div></div>';
            n.querySelector('h3').textContent = tieu; n.querySelector('p').textContent = noi;
            n.querySelector('.xn-ok').textContent = nhanOk;
            function dong() {{ n.remove(); document.removeEventListener('keydown', phim); }}
            function phim(e) {{ if (e.key === 'Escape') dong(); }}
            n.addEventListener('click', function(e) {{ if (e.target === n) dong(); }});
            n.querySelector('.xn-huy').onclick = dong;
            n.querySelector('.xn-ok').onclick = function() {{ dong(); lam(); }};
            document.addEventListener('keydown', phim);
            document.body.appendChild(n); n.querySelector('.xn-ok').focus();
          }}
          function guiSauXN(f) {{ f.setAttribute('data-da-xn', '1'); if (f.requestSubmit) f.requestSubmit(); else f.submit(); }}
          document.addEventListener('submit', function(e) {{
            var f = e.target;
            if (f.getAttribute('data-ghi-de') !== '1' || f.getAttribute('data-da-xn') === '1') return;
            e.preventDefault();
            hoiXN('Tải lại mục này?', 'Mục này đã có trên máy. Tải lại sẽ ghi đè bản đang có.', 'Tải lại', false, function() {{ guiSauXN(f); }});
          }}, true);
          function oTich() {{ return Array.prototype.slice.call(document.querySelectorAll('.tich-kho')); }}
          function dangHien(o) {{ var tr = o.closest('tr'); return tr && !tr.hasAttribute('data-loc'); }}
          function capNhatTich() {{
            var ds = oTich(), chon = ds.filter(function(o) {{ return o.checked; }});
            document.getElementById('so-tich').textContent = chon.length;
            document.getElementById('nut-tai-nhieu').disabled = chon.length === 0;
            document.getElementById('nut-bo-tich').hidden = chon.length === 0;
            var hien = ds.filter(dangHien);
            if (tatCa) tatCa.checked = hien.length > 0 && hien.every(function(o) {{ return o.checked; }});
          }}
          document.addEventListener('change', function(e) {{
            if (e.target.classList && e.target.classList.contains('tich-kho')) capNhatTich();
          }});
          if (tatCa) tatCa.addEventListener('change', function() {{
            oTich().filter(dangHien).forEach(function(o) {{ o.checked = tatCa.checked; }});
            capNhatTich();
          }});
          document.getElementById('nut-bo-tich').addEventListener('click', function() {{
            oTich().forEach(function(o) {{ o.checked = false; }}); capNhatTich();
          }});
          ft.addEventListener('submit', function(e) {{
            var chon = oTich().filter(function(o) {{ return o.checked; }});
            if (!chon.length) {{ e.preventDefault(); return; }}
            var co = chon.filter(function(o) {{ return o.getAttribute('data-co') === '1'; }}).length;
            if (co && ft.getAttribute('data-da-xn') !== '1') {{
              e.preventDefault();
              hoiXN('Tải ' + chon.length + ' mục đã chọn?', co + ' mục đã có trên máy sẽ được tải lại và ghi đè bản đang có.',
                    'Tải về', false, function() {{ guiSauXN(ft); }});
              return; }}
            ft.removeAttribute('data-da-xn');
            Array.prototype.slice.call(ft.querySelectorAll('input[name=id]')).forEach(function(x) {{ x.remove(); }});
            chon.forEach(function(o) {{
              var h = document.createElement('input'); h.type = 'hidden'; h.name = 'id'; h.value = o.value; ft.appendChild(h);
            }});
          }});
          capNhatTich();

          // ---- tien do tai o nen
          function co(n) {{
            var d = ['B','KB','MB','GB'], i = 0;
            while (n >= 1024 && i < 3) {{ n /= 1024; i++; }}
            return (i < 2 ? n.toFixed(0) : n.toFixed(1)) + ' ' + d[i];
          }}
          function esc(s) {{ var e = document.createElement('div'); e.textContent = s || ''; return e.innerHTML; }}
          var coViecDang = false, dangHienTai = false, tenTheoId = {{}}, daThayDang = {{}};
          // Bam Huy -> hoi lai truoc (xoa sach nhung gi da tai + dang xu ly)
          document.getElementById('ds-tai').addEventListener('submit', function(e) {{
            var f = e.target;
            if (f.getAttribute('action') !== '/deployos/kho/huy') return;
            var id = f.elements['id'] ? f.elements['id'].value : '';
            var ten = tenTheoId[id] || 'mục này';
            if (f.getAttribute('data-da-xn') === '1') return;
            e.preventDefault();
            hoiXN('Huỷ tải "' + ten + '"?', 'Mọi thứ đã tải về và đang xử lý cho mục này sẽ bị xoá sạch. Muốn dùng lại phải tải lại từ đầu.',
                  'Huỷ tải', true, function() {{ guiSauXN(f); }});
          }});
          // Dang tai ma bam F5 / dong tab -> trinh duyet hoi lai
          // Nut "Tai ve" cua muc khac / "Huy" la form nam NGAY TRONG trang nay: trang tra ve van tiep tuc
          // hien tien do, nen KHONG hoi "Roi khoi trang web?" (loi that gap khi quay video 16/10/2026).
          var choRoiForm = false;
          document.addEventListener('submit', function() {{ choRoiForm = true; }}, true);
          document.addEventListener('submit', function(e) {{ if (e.defaultPrevented) choRoiForm = false; }});
          window.addEventListener('beforeunload', function(e) {{
            if (dangHienTai && !choRoiForm) {{ e.preventDefault(); e.returnValue = ''; }}
          }});
          function bangXong(ds) {{
            var dong = '', loi = false, huy = false, xong = false;
            Object.keys(daThayDang).forEach(function(id) {{
              var v = ds.filter(function(x) {{ return x.id === id; }})[0];
              if (!v) return;
              var daHuy = !v.ok && (v.thong_bao || '').indexOf('Đã huỷ') === 0;
              if (v.ok) xong = true; else if (daHuy) huy = true; else loi = true;
              dong += '<div style="margin:8px 0;">' + (v.ok ? '✅ ' : (daHuy ? '🛑 ' : '❌ ')) + '<b>' + esc(v.ten)
                   + '</b><div style="color:#8A94A6;font-size:13px;">' + esc(v.thong_bao) + '</div></div>';
            }});
            daThayDang = {{}};
            var bg = document.createElement('div');
            bg.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:99999;'
              + 'display:flex;align-items:center;justify-content:center;padding:16px;';
            bg.innerHTML = '<div style="background:#111823;border:1px solid ' + (loi ? '#7a2e2e' : (huy && !xong ? '#6b5418' : '#2e5a3a'))
              + ';border-radius:12px;padding:20px 22px;max-width:440px;width:100%;color:#E6EDF7;">'
              + '<h3 style="margin:0 0 6px;">' + (loi ? 'Có việc chưa thành công' : (huy && !xong ? '🛑 Đã huỷ' : '✅ Đã xong tất cả')) + '</h3>'
              + dong + '<button type="button" id="dong-bang-xong" style="margin-top:10px;">Đóng</button></div>';
            document.body.appendChild(bg);
            document.getElementById('dong-bang-xong').addEventListener('click', function() {{
              location.replace('/kho-trung-tam');
            }});
          }}
          function ve(ds) {{
            var khung = document.getElementById('khung-tai');
            khung.hidden = ds.length === 0;
            var h = '', dang = false;
            ds.forEach(function(v) {{
              var pt = v.tong ? Math.min(100, 100 * v.da / v.tong) : 0;
              var mau = v.dang ? '#38BDF8' : (v.ok ? '#4ADE80' : '#F87171');
              if (v.dang) {{ dang = true; daThayDang[v.id] = true; }}
              tenTheoId[v.id] = v.ten;
              var conLai = (v.dang && v.toc_do > 0 && v.tong > v.da)
                ? ' · còn khoảng ' + Math.max(1, Math.round((v.tong - v.da) / v.toc_do / 60)) + ' phút' : '';
              h += '<div style="padding:8px 0;border-bottom:1px solid #1F2733;">'
                + '<div style="display:flex;justify-content:space-between;gap:10px;">'
                + '<strong>' + esc(v.ten) + '</strong><span style="font-family:monospace;">'
                + pt.toFixed(0) + '%</span></div>'
                + '<div style="background:#0B0E14;border:1px solid #1F2733;border-radius:6px;height:10px;'
                + 'overflow:hidden;margin:6px 0;"><div style="height:100%;width:' + pt + '%;background:'
                + mau + ';"></div></div><div style="color:#8A94A6;font-size:12.5px;">'
                + co(v.da) + ' / ' + co(v.tong)
                + (v.dang && v.toc_do ? ' · ' + co(v.toc_do) + '/s' : '') + conLai
                + ' — ' + esc(v.thong_bao)
                + (v.dang ? ' <form method="POST" action="/deployos/kho/huy" style="display:inline;">'
                    + '<input type="hidden" name="id" value="' + esc(v.id) + '">'
                    + '<button type="submit" class="small gray">Huỷ</button></form>' : '')
                + '</div></div>';
              var o = document.getElementById('nut-' + v.id);
              if (o && v.dang) o.innerHTML = '<span class="hint">Đang tải...</span>';
            }});
            if (ds.some(function(v) {{ return !v.dang; }}))
              h += '<form method="POST" action="/deployos/kho/xoa-xong" style="margin-top:8px;">'
                + '<button type="submit" class="small gray">Ẩn các việc đã xong</button></form>';
            document.getElementById('ds-tai').innerHTML = h;
            document.getElementById('canh-bao-tai').hidden = !dang;
            dangHienTai = dang;
            // Vua xong TAT CA viec -> hien bang nho "da xong"; bam Dong moi tai lai
            // trang (GET) de cot "Đã co" cap nhat
            if (coViecDang && !dang) bangXong(ds);
            coViecDang = dang;
            return dang;
          }}
          function hoi() {{
            fetch('/deployos/kho/tien-do', {{cache: 'no-store'}})
              .then(function(r) {{ return r.json(); }})
              .then(function(ds) {{ setTimeout(hoi, ve(ds) ? 1500 : 6000); }})
              .catch(function() {{ setTimeout(hoi, 5000); }});
          }}
          hoi();
        }})();
        </script>"""
    return _trang(body, "Kho trung tâm", "Kho lưu trữ dùng chung cho Cài Windows qua mạng và Cài phần mềm qua LAN", active="/kho-trung-tam")


def _kho_chuyen(msg, ok=True):
    """
        POST -> luu thong bao roi CHUYEN HUONG ve GET /deployos/kho (mau
        Post/Redirect/Get). LOI THAT 30/09/2026 (may ao .19): tai Windows 11 8,4GB
        xong, tach ISO xong, roi LAI TAI TIEP tu dau - lap di lap lai. Nguyen
        nhan: POST /deployos/kho/tai tra thang trang (khong chuyen huong) nen
        dia chi trinh duyet van la /deployos/kho/tai; khi 1 viec tai xong, JS
        "location.reload()" tai lai trang -> trinh duyet GUI LAI CA POST -> bat dau
        tai lan nua (log: 4 lan POST cach nhau ~12 phut, dung bang 1 chu ky tai).
        """
    gom = getattr(g, "kho_gom", None)
    if gom is not None:                  # dang tai NHIEU muc: chi gom ket qua, chua chuyen huong
        gom.append((str(msg), bool(ok)))
        return None
    session["kho_tb"] = [str(msg)[:600], bool(ok)]
    return redirect("/kho-trung-tam")


def _con_trong(thu_muc):
    try:
        st = os.statvfs(thu_muc)
        return st.f_bavail * st.f_frsize
    except OSError:
        return 0


def _tai_mot(muc_id):
    """
        Tai 1 muc o nen. KHONG tin cac truong an trong form (ten file, loai,
        sha256...) - lay lai danh sach tu kho roi tim dung muc theo id.
        """
    from ui import khotrungtam as _kt
    cauhinh = _kt.doc_cauhinh()
    if not cauhinh:
        return _kho_chuyen("Chưa kết nối tới kho.", False)
    ok_ds, ds = _kt.danh_sach(cauhinh)
    if not ok_ds:
        return _kho_chuyen(ds, False)
    m = next((x for x in ds if x.get("id") == muc_id), None)
    if not m:
        return _kho_chuyen("Không tìm thấy mục này trên kho (có thể vừa bị xoá).", False)
    loai, ten_hien_thi = m.get("loai", ""), m.get("ten", "")
    ten_an = ten_an_toan(m.get("ten_file", ""))
    ext = os.path.splitext(ten_an)[1].lower()
    kich = int(m.get("kich_thuoc") or 0)
    _bao_dam_thu_muc()

    if loai in ("phanmem", "script"):
        thu_muc_dich = APPS_DIR if loai == "phanmem" else SCRIPTS_DIR
        duoi = EXT_APP if loai == "phanmem" else EXT_SCRIPT
        if not ten_an or ext not in duoi:
            return _kho_chuyen(f"Console System chỉ nhận {'/'.join(sorted(duoi))} cho mục "
                              f"{TEN_LOAI_KHO[loai]} - không tải \"{ten_hien_thi}\".", False)
        if kich * 1.05 + 200 * 1024 * 1024 > _con_trong(thu_muc_dich):
            return _kho_chuyen(f"Không đủ chỗ trống để tải \"{ten_hien_thi}\" "
                              f"({co_kich_thuoc(kich)}).", False)
        du_lieu = (m.get("du_lieu") or "").strip()

        def sau(duong):
            # Phan mem: gan luon tham so cai im lang di kem (neu kho co).
            go_cai = (m.get("go_cai") or "").strip()
            if loai == "phanmem" and (du_lieu or go_cai):
                meta = doc_thongtin_app()
                if du_lieu:
                    meta[ten_an] = du_lieu[:200]
                if go_cai:
                    meta[ten_an + HAU_TO_GO] = go_cai[:400]
                ghi_thongtin_app(meta)
            return True, f"Đã tải về {TEN_LOAI_KHO[loai]}."

        ok, msg = _kt.tai_nen(cauhinh, m, os.path.join(thu_muc_dich, ten_an), sau)
        return _kho_chuyen(msg, ok)

    if loai == "os":
        if ext != ".iso":
            return _kho_chuyen("Mục hệ điều hành phải là file .iso.", False)
        # ISO + boot.wim + install.wim nam cung luc truoc khi xoa ISO ->
        # can khoang 2 lan kich thuoc ISO.
        if kich * 2.1 + 500 * 1024 * 1024 > _con_trong(OS_DIR if os.path.isdir(OS_DIR) else DEPLOY_DIR):
            return _kho_chuyen(
                f"Không đủ chỗ trống: ISO {co_kich_thuoc(kich)} cần khoảng "
                f"{co_kich_thuoc(int(kich * 2.1))} trống (ISO + boot.wim + install.wim "
                f"trong lúc tách). Còn {co_kich_thuoc(_con_trong(OS_DIR if os.path.isdir(OS_DIR) else DEPLOY_DIR))}.", False)
        # Dung lai he dieu hanh da tai do dang tu kho (tai tiep file .part).
        os_id = next((o["id"] for o in danh_sach_os() if o["kho_id"] == muc_id), None)
        os_moi = False            # True: thu muc OS nay do CHINH lan tai nay tao ra
        if not os_id:
            ten_os, so = ten_hien_thi, 2
            while True:
                ok_t, msg_t, os_id = tao_os_moi(ten_os)
                if ok_t:
                    os_moi = True
                    break
                if "Da co" not in msg_t or so > 20:
                    return _kho_chuyen(msg_t, False)
                ten_os, so = f"{ten_hien_thi} ({so})", so + 1
            f_meta = os.path.join(OS_DIR, os_id, "_thongtin.json")
            with open(f_meta, encoding="utf-8") as f:
                meta = json.load(f)
            meta.update({"kho_id": muc_id, "phien_ban": m.get("du_lieu", ""),
                         "nguon": "kho"})
            with open(f_meta, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False)

        def sau_iso(duong):
            from ui import isotach as _it
            # Dang tach ISO khac -> doi (moi luc chi tach 1 file). Kiem tra
            # co Huy moi 2 giay de bam Huy la dung ngay, khong doi het.
            cho = 0
            while _it.dang_chay() and cho < 6 * 3600:
                if _kt.da_huy(muc_id):
                    return False, "Đã huỷ."
                time.sleep(2)
                cho += 2
            if _kt.da_huy(muc_id):
                return False, "Đã huỷ."
            ok_t, msg_t = _it.bat_dau_tach(os_id, duong)
            if not ok_t:
                return False, f"Tải xong nhưng không tách được ISO: {msg_t}"
            if _kt.da_huy(muc_id):            # Huy rot dung luc vua bat dau tach
                _it.huy_tach()
            time.sleep(2)
            while _it.dang_chay():
                time.sleep(1)
            t = _it.trang_thai()
            if t.get("xong"):
                return True, "Đã tải và tách xong - hệ điều hành sẵn sàng để cài."
            return False, f"Tách ISO thất bại: {t.get('loi') or '?'}"

        def khi_huy_os():
            """Bam Huy: ngat ngay tien trinh tach ISO cua HE DIEU HANH NAY."""
            from ui import isotach as _it
            if _it.dang_chay() and _it.trang_thai().get("os_id") == os_id:
                _it.huy_tach()

        def don_dep_os():
            """Sau khi huy: xoa thu tam; OS do lan tai nay tao ra ma chua co
                file nao dung duoc thi xoa luon ca thu muc (khong de OS rong)."""
            from ui import isotach as _it
            d = os.path.join(OS_DIR, os_id)
            _it.don_thu_muc_tam(d)
            if os_moi and os.path.isdir(d) and not any(
                    os.path.isfile(os.path.join(d, x))
                    for x in ("boot.wim", "install.wim", "install.esd")):
                shutil.rmtree(d, ignore_errors=True)

        ok, msg = _kt.tai_nen(cauhinh, m, os.path.join(OS_DIR, os_id, ten_an), sau_iso,
                              khi_huy_os, don_dep_os)
        return _kho_chuyen(msg, ok)

    if loai == "ungdung":
        # Ung dung NHIEU FILE (Office 2019/365...): .zip + dong lenh cai (du_lieu). Tai vao 1
        # ung dung kieu thu muc (mo hinh MDT), TU giai nen roi dat dong lenh. Tai lai lan sau:
        # dung lai DUNG ung dung cu (kho_id) - giai nen de len, khong tao ban trung.
        if ext != ".zip":
            return _kho_chuyen("Mục ứng dụng nhiều file phải là file .zip.", False)
        can = kich * 2.1 + 300 * 1024 * 1024        # zip + ban giai nen cung luc
        if can > _con_trong(UNGDUNG_DIR):
            return _kho_chuyen(f"Không đủ chỗ trống để tải \"{ten_hien_thi}\" "
                               f"(cần khoảng {co_kich_thuoc(int(can))}).", False)
        ung_id = next((u["id"] for u in danh_sach_ungdung()
                       if _doc_meta_ungdung(u["id"]).get("kho_id") == muc_id), None)
        ung_moi = False
        if not ung_id:
            ten_u, so = ten_hien_thi, 2
            while True:
                ok_t, msg_t, ung_id = tao_ungdung_moi(ten_u)
                if ok_t:
                    ung_moi = True
                    break
                if "Đã có" not in msg_t or so > 20:
                    return _kho_chuyen(msg_t, False)
                ten_u, so = f"{ten_hien_thi} ({so})", so + 1
            meta = _doc_meta_ungdung(ung_id)
            meta.update({"kho_id": muc_id, "nguon": "kho"})
            _ghi_meta_ungdung(ung_id, meta)
        lenh_kho = (m.get("du_lieu") or "").strip()

        def sau_ungdung(duong):
            ok_g, msg_g = giai_nen_ungdung(ung_id, duong)     # tu xoa .zip sau khi giai nen
            if not ok_g:
                return False, msg_g
            if lenh_kho:
                dat_lenh_cai_ungdung(ung_id, lenh_kho)
                return True, (f'Đã tải và giải nén "{ten_hien_thi}" vào Ứng dụng (nhiều file), '
                              "lệnh cài đã đặt sẵn.")
            return True, (f'Đã tải và giải nén "{ten_hien_thi}" - kho chưa có dòng lệnh cài, '
                          "vào tab Ứng dụng (nhiều file) để đặt.")

        def don_dep_ungdung():
            """Huy giua chung: ung dung do CHINH lan tai nay tao ra ma chua co gi -> xoa luon."""
            d = os.path.join(UNGDUNG_DIR, ung_id)
            if ung_moi and os.path.isdir(d) and not any(
                    x != "_thongtin.json" and not x.endswith(".part") for x in os.listdir(d)):
                shutil.rmtree(d, ignore_errors=True)

        ok, msg = _kt.tai_nen(cauhinh, m, os.path.join(UNGDUNG_DIR, ung_id, ten_an),
                              sau_ungdung, None, don_dep_ungdung)
        return _kho_chuyen(msg, ok)

    if loai == "winpe":
        # WinPE rieng (ui/winperieng.py): tai vao tab WinPE roi TU dua vao menu
        # PXE "2. Boot WinPE". ISO: tach .wim ra roi XOA ISO (kho tai lai duoc).
        if ext not in (".wim", ".iso"):
            return _kho_chuyen("Mục WinPE phải là file .wim hoặc .iso.", False)
        can = kich * (2.1 if ext == ".iso" else 1.05) + 200 * 1024 * 1024
        if can > _con_trong(BOOT_DIR):
            return _kho_chuyen(f"Không đủ chỗ trống để tải \"{ten_hien_thi}\" "
                               f"(cần khoảng {co_kich_thuoc(int(can))}).", False)
        ten_menu = (m.get("du_lieu") or "").strip() or ten_hien_thi

        def sau_winpe(duong):
            from ui import winperieng as _wr
            ok_w, msg_w = _wr.them_dong_bo(os.path.basename(duong), ten_menu)
            if ok_w and ext == ".iso":
                try:
                    os.remove(duong)
                except OSError:
                    pass
                msg_w = f'Đã tải, tách WinPE và đưa "{ten_menu}" vào menu PXE (2. Boot WinPE).'
            return ok_w, msg_w

        ok, msg = _kt.tai_nen(cauhinh, m, os.path.join(BOOT_DIR, ten_an), sau_winpe)
        return _kho_chuyen(msg, ok)

    if loai == "font":
        # FONT CHU (18/10/2026): moi muc kho = 1 file .zip cua 1 ho chu (cac file .ttf/.otf
        # + giay phep). Tai ve la TU tao 1 "bo font" cung ten trong Tai nguyen > Font chu
        # roi giai nen PHANG vao do (chi lay file font that, bo giay phep/rac). Tai lai lan sau:
        # dung lai DUNG bo font cu (kho_id), giai nen de len.
        if ext != ".zip":
            return _kho_chuyen("Mục font chữ phải là file .zip.", False)
        can = kich * 2.1 + 100 * 1024 * 1024
        if can > _con_trong(FONTS_DIR):
            return _kho_chuyen(f"Không đủ chỗ trống để tải \"{ten_hien_thi}\" "
                               f"(cần khoảng {co_kich_thuoc(int(can))}).", False)
        bo = _bo_font_tu_kho(muc_id)
        bo_id = bo["id"] if bo else None
        bo_moi = False
        if not bo_id:
            ten_b, so = ten_hien_thi, 2
            while True:
                ok_t, msg_t, bo_id = tao_bo_font(ten_b)
                if ok_t:
                    bo_moi = True
                    break
                if "Đã có" not in msg_t or so > 20:
                    return _kho_chuyen(msg_t, False)
                ten_b, so = f"{ten_hien_thi} ({so})", so + 1
            p_bo = os.path.join(FONTS_DIR, bo_id)
            meta = _doc_meta_bo_font(p_bo)
            meta.update({"kho_id": muc_id, "nguon": "kho"})
            with open(os.path.join(p_bo, "_thongtin.json"), "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=1)
        p_bo = os.path.join(FONTS_DIR, bo_id)

        def sau_font(duong):
            ok_g, msg_g, so_them, _bo_qua = _giai_nen_font_zip(p_bo, duong, ten_an)  # tu xoa .zip
            if not ok_g:
                return False, msg_g
            return True, f'Đã tải "{ten_hien_thi}": {so_them} font trong Tài nguyên máy → Font chữ.'

        def don_dep_font():
            """Huy giua chung: bo font do CHINH lan tai nay tao ra ma chua co font -> xoa luon."""
            if bo_moi and os.path.isdir(p_bo) and not any(
                    x.lower().endswith(tuple(_fontinfo_duoi())) for x in os.listdir(p_bo)):
                shutil.rmtree(p_bo, ignore_errors=True)

        ok, msg = _kt.tai_nen(cauhinh, m, os.path.join(p_bo, ".tam-kho-" + secrets.token_hex(4) + ".zip"),
                              sau_font, None, don_dep_font)
        return _kho_chuyen(msg, ok)

    return _kho_chuyen("Loại mục không hỗ trợ.", False)


def _fontinfo_duoi():
    from ui import fontinfo as _fi
    return _fi.DUOI_FONT


def register_kho(app):
    @app.route("/deployos/kho")
    def deployos_kho_cu():
        return redirect("/kho-trung-tam")

    @app.route("/kho-trung-tam")
    def deployos_kho():
        tb = session.pop("kho_tb", None)
        return _trang_kho(*tb) if tb else _trang_kho()

    @app.route("/deployos/kho/ghep", methods=["POST"])
    def deployos_kho_ghep():
        from ui import khotrungtam as _kt
        ok, msg = _kt.ghep_noi(request.form.get("url", ""), request.form.get("ma", ""))
        return _kho_chuyen(msg, ok)

    @app.route("/deployos/kho/xoa-cauhinh", methods=["POST"])
    def deployos_kho_xoa_cauhinh():
        from ui import khotrungtam as _kt
        _kt.xoa_cauhinh()
        return _kho_chuyen("Đã xoá kết nối. Nhập mã kết nối mới để kết nối lại.", True)

    @app.route("/deployos/kho/tien-do")
    def deployos_kho_tien_do():
        from ui import khotrungtam as _kt
        return jsonify(_kt.trang_thai_tai())

    @app.route("/deployos/kho/huy", methods=["POST"])
    def deployos_kho_huy():
        from ui import khotrungtam as _kt
        _kt.huy_tai(request.form.get("id", ""))
        return redirect("/kho-trung-tam")

    @app.route("/deployos/kho/xoa-xong", methods=["POST"])
    def deployos_kho_xoa_xong():
        from ui import khotrungtam as _kt
        _kt.xoa_viec_xong()
        return redirect("/kho-trung-tam")

    @app.route("/deployos/kho/tai", methods=["POST"])
    def deployos_kho_tai():
        return _tai_mot((request.form.get("id") or "").strip())

    @app.route("/deployos/kho/tai-nhieu", methods=["POST"])
    def deployos_kho_tai_nhieu():
        """Tai NHIEU muc da tich: lan luot bat dau tung muc (moi muc tai o nen nhu nut Tai ve)."""
        ids = []
        for x in request.form.getlist("id"):
            x = (x or "").strip()
            if x and x not in ids:
                ids.append(x)
        if not ids:
            return _kho_chuyen("Chưa tích mục nào để tải.", False)
        g.kho_gom = []
        try:
            for x in ids[:200]:
                _tai_mot(x)
            ket = list(g.kho_gom)
        finally:
            g.kho_gom = None
        loi = [m for m, o in ket if not o]
        if loi:
            return _kho_chuyen(f"Đã bắt đầu tải {len(ket) - len(loi)}/{len(ket)} mục. "
                               f"Chưa tải được: " + " | ".join(loi[:5]), len(loi) < len(ket))
        return _kho_chuyen(f"Đã bắt đầu tải {len(ket)} mục đã tích. Theo dõi ở khung \"Đang tải\".", True)
