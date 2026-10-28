# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Tach tu deployos.py (B4).

(B4: tach nguyen van tu deployos.py::register_deployos; ten ham/route giu nguyen.)"""
from consolesystem.core.nhatky import bo_qua as _bo_qua
import os
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
from flask import (request, send_from_directory, abort)
from ui.home import _esc
from consolesystem.features.deploy_os.dosui_chung import (_msg, _tabs, _trang)  # noqa: F401


def _nhan_tai_len(thu_muc, duoi_cho_phep, nhan):
    """
        Nhan file vua tai len. Binh thuong du lieu DA nam san tren dia dich
        (do RequestTaiLenThang ghi thang), chi con doi ten .part -> ten that.
        Duong du phong (_luu_tai_len) chi chay khi vi ly do gi do khong ghi
        thang duoc.
        """
    f = request.files.get("file")
    if not f or not getattr(f, "filename", ""):
        return False, "Chưa chọn file."
    duong = getattr(getattr(f, "stream", None), "_cp_duong_dan", None)
    if duong:
        try:
            f.stream.flush()
            os.fsync(f.stream.fileno())
        except Exception as _loi:
            _bo_qua(_loi)
        ok, msg, _duong_dich = _hoan_tat_ghi_thang(duong, thu_muc, f.filename)
        return ok, msg
    # Khong ghi thang duoc (vd duoi file khong hop le -> da do vao
    # /dev/null): bao loi ro rang thay vi im lang
    ten = ten_an_toan(f.filename)
    if os.path.splitext(ten)[1].lower() not in duoi_cho_phep:
        return False, (f"Không nhận đuôi file này cho mục {nhan}. Chỉ nhận: "
                       f"{', '.join(sorted(duoi_cho_phep))}")
    return _luu_tai_len(f, thu_muc, duoi_cho_phep, nhan)


# ================================================ 2. TAB "CONSOLE BOOT"
def _khoi_tai_len(hanh_dong, nhan, duoi, ghi_chu="", loai=""):
    """
        Khung tai len co THANH TIEN TRINH that.

        LOI THAT DA GAP (anh Thoai bao: "task manager het bao dung luong ben
        tab network ma trang os van quay hoai luon, ko biet no toi dau"):
        truoc day day chi la 1 form thuong - bam xong la trang dung yen quay
        vong tron hang chuc phut, khong biet dang o dau, con bao lau, hay da
        treo. Voi file 5GB tren the nho cham thi cho nhu vay la khong the
        chap nhan duoc.

        Gio dung XMLHttpRequest de biet SO BYTE DA GUI, dong thoi hoi may
        (/deployos/tien-do) xem DA GHI DUOC bao nhieu xuong dia that - hien
        ca hai, kem toc do va thoi gian con lai. Neu trinh duyet khong chay
        duoc JavaScript thi form van gui duoc nhu cu (chi la khong co thanh
        tien trinh), khong bao gio mat duong tai len.
        """
    return f"""
        <div class="card">
          <h3>Tải lên {_esc(nhan)}</h3>
          {ghi_chu}
          <form method="POST" action="{hanh_dong}" enctype="multipart/form-data"
                class="form-tai-len" data-loai="{_esc(loai)}">
            <label>Chọn file ({', '.join(sorted(duoi))})</label>
            <input type="file" name="file" required>
            <div class="row" style="margin-top:13px;">
              <button type="submit" data-busy="Đang tải lên, đừng đóng trang...">
                Tải lên</button>
              <span style="color:#8b93a1;font-size:13px;">
                File lớn mất vài phút. Sẽ có thanh tiến trình báo rõ đang tới đâu.</span>
            </div>
          </form>

          <div class="tt-khung" style="display:none;">
            <div class="tt-ten"></div>
            <div class="tt-thanh-ngoai"><div class="tt-thanh"></div></div>
            <div class="tt-so">
              <span class="tt-phantram">0%</span>
              <span class="tt-chitiet"></span>
            </div>
            <div class="tt-dia"></div>
            <div style="margin-top:12px;">
              <button type="button" class="red small tt-huy">Hủy tải lên</button>
            </div>
          </div>
        </div>"""


def _bang_file(ds, duong_xoa, duong_tai):
    if not ds:
        return '<p style="color:#8b93a1;">Chưa có file nào.</p>'
    hang = ""
    for f in ds:
        hang += f"""
            <tr>
              <td><strong>{_esc(f['ten'])}</strong></td>
              <td>{co_kich_thuoc(f['cd'])}</td>
              <td style="color:#8b93a1;">{_esc(f['ngay'])}</td>
              <td>
                <a class="btn small gray" href="{duong_tai}/{_esc(f['ten'])}">Tải về</a>
                <form method="POST" action="{duong_xoa}" style="display:inline;"
                      onsubmit="return confirm('Xóa {_esc(f['ten'])}?');">
                  <input type="hidden" name="ten" value="{_esc(f['ten'])}">
                  <button type="submit" class="red small">Xóa</button>
                </form>
              </td>
            </tr>"""
    return f"""
        <div class="tbl-scroll"><table data-pt="25" data-pt-tim="1">
          <tr><th>Tên file</th><th style="width:110px;">Kích thước</th>
              <th style="width:140px;">Ngày tải lên</th><th style="width:180px;">Thao tác</th></tr>
          {hang}
        </table></div>"""


def _trang_file_boot(msg="", ok=True):
    _don_file_do_dang(BOOT_DIR)
    # Chi hien file WinPE (.wim/.iso); file he thong cua PXE (iPXE, wimboot, BCD,
    # autounattend...) tu quan ly, an di (anh Thoai 03/10/2026).
    ds = _liet_ke(BOOT_DIR, EXT_WINPE)
    ghi_chu = """
        <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
          Nhận file WinPE: <code>.wim</code> hoặc <code>.iso</code> (Strelec, Hiren's, bản
          tự build bằng Windows ADK...). Bootloader iPXE + wimboot đã
          <strong>kèm sẵn bản ký chính thức</strong> - không cần tải lên. Tải lên xong, thêm
          vào menu PXE ở khung <strong>Boot WinPE</strong> bên dưới.</p>"""
    body = (_tabs("tainguyen", "file") + _msg(msg, ok) +
            _khoi_tai_len("/deployos/console/file/len", "WinPE", EXT_WINPE, ghi_chu, "file") +
            _khoi_winpe_rieng() +
            f"<h2>File WinPE đang có ({len(ds)})</h2>" +
            _bang_file(ds, "/deployos/console/file/xoa", "/deployos/console/file/tai"))
    return _trang(body, "Cài Windows qua mạng", "2.1 - WinPE")


def _khoi_winpe_rieng():
    """Khung WinPE RIENG (Strelec, Hiren's, ban ADK) trong menu PXE - xem ui/winperieng.py."""
    from ui import winperieng as _wr
    ds = _wr.danh_sach()
    t = _wr.trang_thai_tach()
    tach = ""
    if t["chay"]:
        tach = (f'<div class="msg info">Đang tách WinPE từ <strong>{_esc(t["file"])}</strong>'
                f' ({int(time.time() - t["luc"])} giây)... {_esc(t.get("buoc") or "")} - trang tự làm mới.</div>'
                '<script>setTimeout(function(){location.reload();}, 4000);</script>')
    elif t["loi"]:
        tach = _msg(f'Tách WinPE từ "{t["file"]}" thất bại: {t["loi"]}', False)
    elif t["xong"] and time.time() - t["luc"] < 900:
        tach = _msg(t["xong"], True)
    hang = "".join(f"""
            <tr><td><strong>{_esc(m['ten'])}</strong></td>
              <td style="color:#8b93a1;">{_esc(m['file'])}</td><td>{co_kich_thuoc(m['cd'])}</td>
              <td><form method="POST" action="/deployos/winpe-rieng/bo" style="display:inline;"
                        onsubmit="return confirm('Bỏ {_esc(m['ten'])} khỏi menu PXE? (file vẫn giữ)');">
                <input type="hidden" name="file" value="{_esc(m['file'])}">
                <button type="submit" class="gray small">Bỏ khỏi menu</button></form></td></tr>"""
        for m in ds)
    bang = (f'<div class="tbl-scroll"><table><tr><th>Tên trong menu</th><th>File</th>'
            f'<th style="width:100px;">Kích thước</th><th style="width:130px;"></th></tr>{hang}</table></div>'
            if ds else '<p style="color:#8b93a1;margin:0 0 10px;">Chưa có WinPE nào trong menu.</p>')
    chon = _wr.file_co_the_them()
    form = (f"""
          <form method="POST" action="/deployos/winpe-rieng/them" style="margin-top:12px;">
            <div class="row" style="gap:10px;align-items:flex-end;flex-wrap:wrap;">
              <div style="flex:1;min-width:200px;"><label>File (.wim hoặc .iso đã tải lên ở trên)</label>
                <select name="file">{''.join(f'<option>{_esc(n)}</option>' for n in chon)}</select></div>
              <div style="flex:1;min-width:200px;"><label>Tên hiện trong menu</label>
                <input type="text" name="ten" maxlength="60" placeholder="ví dụ: Hiren's BootCD PE"></div>
              <button type="submit" data-busy="Đang kiểm tra file...">Đưa vào menu PXE</button>
            </div>
          </form>""" if chon else
        '<p class="hint" style="margin:8px 0 0;">Tải file .wim (hoặc .iso) WinPE lên bằng khung ở trên '
        'rồi quay lại đây chọn.</p>')
    return f"""
        <div class="card">
          <h3>Boot WinPE (menu PXE)</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
            Sergei Strelec, Hiren's BootCD PE, bản tự build bằng Windows ADK...
            Máy khách boot qua mạng chọn <strong>2. Boot WinPE</strong>: boot
            <strong>nguyên bản</strong>, không chèn gì. File .iso thì Console System tự tách
            file .wim bên trong ra. Máy UEFI bật Secure Boot chỉ boot được WinPE ký bởi Microsoft.</p>
          {tach}{bang}{form}
        </div>"""


def _trang_apps(msg="", ok=True):
    _don_file_do_dang(APPS_DIR)
    ds = danh_sach_app()
    ghi_chu = """
        <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
          Nhận file cài đặt .msi và .exe. Sau khi tải lên, điền tham số cài
          IM LẶNG cho từng file ở bảng bên dưới (mỗi hãng một kiểu:
          <code>/S</code>, <code>/silent</code>, <code>/verysilent</code>,
          <code>/quiet</code>...). File .msi thì không bắt buộc - mặc định
          dùng <code>/qn /norestart</code>.</p>

        <!-- Goi y tham so: bang toi tu ve (datalist cua trinh duyet hien hop trang, khong doi mau duoc - anh Thoai che 28/10/2026) -->
        <div id="goiy-thamso" hidden style="position:absolute;z-index:50;width:520px;max-width:92vw;max-height:320px;overflow-y:auto;overflow-x:hidden;
             background:#141A23;border:1px solid #2B3746;border-radius:10px;box-shadow:0 10px 28px rgba(0,0,0,.45);">
          <table style="margin:0;width:100%;min-width:0;table-layout:fixed;">""" + "".join(
        f'<tr class="goiy-o" data-gt="{_esc(gt)}" style="cursor:pointer;"><td style="width:55%;word-break:break-all;padding:8px 10px;"><code>{_esc(gt)}</code></td>'
        f'<td style="color:#8b93a1;font-size:12.5px;padding:8px 10px;white-space:normal;">{_esc(mo_ta)}</td></tr>'
        for gt, mo_ta in GOI_Y_THAM_SO) + """</table></div>
        <style>#goiy-thamso tr.goiy-o:hover td,#goiy-thamso tr.goiy-o.chon td{background:#1C2533;}</style>
        <script>
        (function(){
          var hop=document.getElementById('goiy-thamso'), o=null, vt=-1;
          function hang(){return [].slice.call(hop.querySelectorAll('tr.goiy-o')).filter(function(r){return !r.hidden;});}
          function loc(){var q=o.value===o.dataset.goc?'':(o.value||'').toLowerCase();
            hop.querySelectorAll('tr.goiy-o').forEach(function(r){r.hidden=!!q&&r.textContent.toLowerCase().indexOf(q)<0;});
            vt=-1; hop.querySelectorAll('tr.chon').forEach(function(r){r.classList.remove('chon');});}
          function mo(i){o=i; var b=i.getBoundingClientRect(); hop.style.left=(b.left+scrollX)+'px'; hop.style.top=(b.bottom+scrollY+4)+'px'; hop.hidden=false; o.dataset.goc=i.value; loc();}
          function dong(){hop.hidden=true; o=null;}
          function chon(r){if(!o)return; o.value=r.dataset.gt; o.focus(); dong();}
          document.addEventListener('focusin',function(e){if(e.target.matches&&e.target.matches('input[data-goiy]'))mo(e.target);});
          document.addEventListener('input',function(e){if(e.target===o)loc();});
          document.addEventListener('mousedown',function(e){var r=e.target.closest&&e.target.closest('#goiy-thamso tr.goiy-o');
            if(r){e.preventDefault();chon(r);} else if(o&&e.target!==o&&!hop.contains(e.target))dong();});
          document.addEventListener('keydown',function(e){if(!o||hop.hidden)return; var h=hang();
            if(e.key==='Escape'){dong();return;}
            if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault(); if(!h.length)return; if(h[vt])h[vt].classList.remove('chon');
              vt=(vt+(e.key==='ArrowDown'?1:-1)+h.length)%h.length; h[vt].classList.add('chon'); h[vt].scrollIntoView({block:'nearest'});}
            else if(e.key==='Enter'&&h[vt]){e.preventDefault(); chon(h[vt]);}});
          window.addEventListener('resize',dong);
        })();
        </script>

        <!-- Bang tra cuu nam trong HOP THOAI (the <dialog> chinh chu cua
             trinh duyet: tu co lop phu mo, bam Esc la dong, khong can thu
             vien ngoai - Pi mang di hien truong co the khong co mang).
             Truoc day bang nay trai thang ra trang, chiem gan nua man hinh
             va day danh sach phan mem that xuong duoi - anh Thoai phai cuon
             qua no moi lan vao trang du chi thinh thoang can tra. -->
        <dialog id="hop-tra-cuu" style="border:1px solid #2B3746;border-radius:12px;
                background:#141A23;color:#E3E8EF;padding:0;max-width:760px;width:94vw;">
          <div style="display:flex;align-items:center;gap:12px;padding:16px 20px;
                      border-bottom:1px solid #1F2733;position:sticky;top:0;
                      background:#141A23;">
            <strong style="flex:1;font-size:16px;">Tra tham số cài im lặng theo loại bộ cài</strong>
            <button type="button" class="gray small" data-dong-hop>Đóng</button>
          </div>
          <div style="padding:16px 20px;max-height:66vh;overflow:auto;">
            <p class="hint" style="margin:0 0 12px;">
              Mỗi hãng dùng một bộ đóng gói khác nhau nên tham số khác nhau -
              KHÔNG có tham số nào dùng chung cho tất cả. Cách nhận biết
              nhanh: bấm chuột phải file .exe &rarr; Properties &rarr; tab
              Details, xem "Original filename"/"Product name". Nếu không rõ,
              chạy file với tham số <code>/?</code> trên một máy bất kỳ -
              phần lớn bộ cài sẽ hiện danh sách tham số.</p>
            <div class="tbl-scroll"><table>
              <tr><th style="width:230px;">Tham số</th><th>Dùng cho</th></tr>""" + "".join(
        f'<tr><td><code>{_esc(gt)}</code></td><td>{_esc(mo_ta)}</td></tr>'
        for gt, mo_ta in GOI_Y_THAM_SO) + """
            </table></div>
            <p class="hint" style="margin:12px 0 0;">
              Ô điền tham số ở bảng phần mềm cũng có sẵn gợi ý này - bấm vào
              ô đó là hiện ra chọn, không phải gõ tay.</p>
          </div>
        </dialog>"""

    if ds:
        hang = ""
        for a in ds:
            goi_y = ("msiexec /i ... /quiet /norestart (mac dinh)"
                     if a["la_msi"] else "vd: /S hoac /verysilent")
            hang += f"""
                <tr data-ten="{_esc(_bo_dau_py(a['ten']))}">
                  <td><strong>{_esc(a['ten'])}</strong><br>
                      <small style="color:#8b93a1;">{co_kich_thuoc(a['cd'])} &middot; {_esc(a['ngay'])}</small></td>
                  <td>
                    <form method="POST" action="/deployos/console/apps/thamso" class="row" style="gap:8px;">
                      <input type="hidden" name="ten" value="{_esc(a['ten'])}">
                      <input type="text" name="tham_so" value="{_esc(a['tham_so'])}"
                             placeholder="{goi_y}" style="max-width:250px;"
                             data-goiy autocomplete="off" autocapitalize="off">
                      <button type="submit" class="small gray">Lưu</button>
                    </form>
                  </td>
                  <td>
                    <form method="POST" action="/deployos/console/apps/thamso" class="row" style="gap:8px;">
                      <input type="hidden" name="ten" value="{_esc(a['ten'])}">
                      <input type="hidden" name="kieu" value="go">
                      <input type="text" name="go_cai" value="{_esc(a['go_cai'])}"
                             placeholder="vd: msiexec /x {{GUID}} /qn" style="max-width:290px;"
                             autocapitalize="off">
                      <button type="submit" class="small gray">Lưu</button>
                    </form>
                  </td>
                  <td>
                    <a class="btn small gray" href="/deployos/console/apps/tai/{_esc(a['ten'])}">Tải về</a>
                    <form method="POST" action="/deployos/console/apps/xoa" style="display:inline;"
                          onsubmit="return confirm('Xoa {_esc(a['ten'])}?');">
                      <input type="hidden" name="ten" value="{_esc(a['ten'])}">
                      <button type="submit" class="red small">Xóa</button>
                    </form>
                  </td>
                </tr>"""
        bang = f"""
            <div class="tbl-scroll"><table id="bang-apps" data-pt="25">
              <thead><tr><th>Phần mềm</th><th style="width:340px;">Tham số cài im lặng</th>
                  <th style="width:380px;">Tham số gỡ cài đặt</th>
                  <th style="width:180px;">Thao tác</th></tr></thead>
              <tbody>{hang}</tbody>
            </table></div>
            <div id="apps-khong-thay" class="hint" hidden
                 style="padding:12px 2px;"></div>"""
    else:
        bang = '<p style="color:#8b93a1;">Chưa có phần mềm nào.</p>'

    thanh_cong_cu = """
        <div class="row" style="margin:0 0 12px;align-items:center;">
          <input type="search" id="tim-app" autocomplete="off"
                 placeholder="Tìm phần mềm... (gõ không dấu cũng được)"
                 style="flex:1;min-width:220px;max-width:420px;">
          <button type="button" class="gray" data-mo-hop="hop-tra-cuu">
            Tra cứu tham số cài im lặng</button>
          <span id="dem-app" class="hint"></span>
        </div>"""

    body = (_tabs("tainguyen", "apps") + _msg(msg, ok) +
            _khoi_tai_len("/deployos/console/apps/len", "phần mềm", EXT_APP, ghi_chu, "apps") +
            f"<h2>Phần mềm đang có ({len(ds)})</h2>" + thanh_cong_cu + bang +
            """
                <div class="msg info">Các file này KHÔNG bao giờ được chạy trên
                chính Console Pi - Pi chỉ lưu và gửi chúng cho máy đang được
                cài lại tải về.</div>
                <script>
                (function() {
                  // Hop thoai tra cuu do bo xu ly dung chung trong
                  // dashboard.js lo (data-mo-hop / data-dong-hop) - o day
                  // chi con viec loc danh sach.
                  // --- O tim phan mem ---
                  var o = document.getElementById('tim-app');
                  var bang = document.getElementById('bang-apps');
                  var dem = document.getElementById('dem-app');
                  var trong = document.getElementById('apps-khong-thay');
                  if (!o || !bang) return;
                  function boDau(s) {
                    return (s || '').replace(/đ/g, 'd').replace(/Đ/g, 'D')
                      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
                      .toLowerCase().trim();
                  }
                  function loc() {
                    var q = boDau(o.value);
                    var hang = bang.tBodies[0].rows, hien = 0;
                    for (var i = 0; i < hang.length; i++) {
                      var t = hang[i].getAttribute('data-ten') || '';
                      var khop = !q || t.indexOf(q) !== -1;
                      if (khop) hang[i].removeAttribute('data-loc'); else hang[i].setAttribute('data-loc', '1');
                      if (khop) hien++;
                    }
                    if (window.csPT) window.csPT.capNhat(bang, true);
                    if (dem) dem.textContent = q ? (hien + '/' + hang.length + ' phần mềm')
                                                 : (hang.length + ' phần mềm');
                    if (trong) {
                      trong.hidden = hien > 0;
                      trong.textContent = 'Không có phần mềm nào khớp "' + o.value + '".';
                    }
                  }
                  o.addEventListener('input', loc);
                  loc();
                })();
                </script>""")
    return _trang(body, "Cài Windows qua mạng", "2.2 - Phần mềm")


def _trang_scripts(msg="", ok=True):
    _don_file_do_dang(SCRIPTS_DIR)
    ds = _liet_ke(SCRIPTS_DIR, EXT_SCRIPT)
    ghi_chu = """
        <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
          Nhận .bat, .cmd (Windows) và .ps1 (PowerShell). Các script này sẽ
          chạy TRÊN MÁY ĐANG ĐƯỢC CÀI sau khi cài xong OS và phần mềm, không
          chạy trên Console Pi.</p>"""
    body = (_tabs("tainguyen", "scripts") + _msg(msg, ok) +
            _khoi_tai_len("/deployos/console/scripts/len", "script", EXT_SCRIPT, ghi_chu, "scripts") +
            f"<h2>Script đang có ({len(ds)})</h2>" +
            _bang_file(ds, "/deployos/console/scripts/xoa",
                       "/deployos/console/scripts/tai"))
    return _trang(body, "Cài Windows qua mạng", "2.3 - Script")


def register_console(app):
    # ------------------------------------------------------ 2.1 file boot
    @app.route("/deployos/console")
    def deployos_console():
        return _trang_file_boot()

    @app.route("/deployos/winpe-rieng/them", methods=["POST"])
    def deployos_winpe_rieng_them():
        from ui import winperieng as _wr
        ok, msg = _wr.them(request.form.get("file", ""), request.form.get("ten", ""))
        if ok and not _wr.trang_thai_tach()["chay"]:
            from ui import pxe as _pxe
            msg += _pxe.cap_nhat_menu()
        return _trang_file_boot(msg, ok)

    @app.route("/deployos/winpe-rieng/bo", methods=["POST"])
    def deployos_winpe_rieng_bo():
        from ui import winperieng as _wr
        ok, msg = _wr.bo(request.form.get("file", ""))
        if ok:
            from ui import pxe as _pxe
            msg += _pxe.cap_nhat_menu()
        return _trang_file_boot(msg, ok)

    @app.route("/deployos/console/file/len", methods=["POST"])
    def deployos_boot_len():
        f = request.files.get("file")
        if not f:
            return _trang_file_boot("Chua chon file.", False)
        ok, msg = _nhan_tai_len(BOOT_DIR, EXT_WINPE, "WinPE")
        return _trang_file_boot(msg, ok)

    @app.route("/deployos/console/file/xoa", methods=["POST"])
    def deployos_boot_xoa():
        ten = request.form.get("ten", "")
        ok, msg = _xoa_file(BOOT_DIR, ten)
        if ok:
            # xoa file .wim that su -> don luon thu muc Apps qua mang di kem (winperieng.bo giu lai)
            from ui import winperieng as _wr
            if not any(m["file"] == ten for m in _wr.danh_sach()):
                shutil.rmtree(os.path.join(_wr.DIR_APPS, ten_an_toan(os.path.splitext(os.path.basename(ten))[0])),
                              ignore_errors=True)
        return _trang_file_boot(msg, ok)

    @app.route("/deployos/console/file/tai/<ten>")
    def deployos_boot_tai(ten):
        p = _duong_dan_trong(BOOT_DIR, ten)
        if not p or not os.path.isfile(p):
            abort(404)
        return send_from_directory(BOOT_DIR, os.path.basename(p), as_attachment=True)

    # ------------------------------------------------------- 2.2 phan mem
    @app.route("/deployos/console/apps")
    def deployos_apps():
        return _trang_apps()

    @app.route("/deployos/console/apps/len", methods=["POST"])
    def deployos_apps_len():
        f = request.files.get("file")
        if not f:
            return _trang_apps("Chua chon file.", False)
        ok, msg = _nhan_tai_len(APPS_DIR, EXT_APP, "phần mềm")
        return _trang_apps(msg, ok)

    @app.route("/deployos/console/apps/thamso", methods=["POST"])
    def deployos_apps_thamso():
        ten = ten_an_toan(request.form.get("ten", ""))
        if not ten or not os.path.isfile(os.path.join(APPS_DIR, ten)):
            return _trang_apps("Không tìm thấy phần mềm đó.", False)
        meta = doc_thongtin_app()
        if request.form.get("kieu") == "go":
            go = (request.form.get("go_cai") or "").strip()[:400]
            if go:
                meta[ten + HAU_TO_GO] = go
            else:
                meta.pop(ten + HAU_TO_GO, None)
            return _trang_apps("Đã lưu tham số gỡ cài đặt." if ghi_thongtin_app(meta) else "Không ghi được.", True)
        ts = (request.form.get("tham_so") or "").strip()[:200]
        if ts:
            meta[ten] = ts
        else:
            meta.pop(ten, None)
        ok = ghi_thongtin_app(meta)
        return _trang_apps("Đã lưu tham số." if ok else "Không ghi được.", ok)

    @app.route("/deployos/console/apps/xoa", methods=["POST"])
    def deployos_apps_xoa():
        ten = ten_an_toan(request.form.get("ten", ""))
        ok, msg = _xoa_file(APPS_DIR, ten)
        if ok:
            meta = doc_thongtin_app()
            da_co = meta.pop(ten, None) is not None
            da_co = (meta.pop(ten + HAU_TO_GO, None) is not None) or da_co
            if da_co:
                ghi_thongtin_app(meta)
        return _trang_apps(msg, ok)

    @app.route("/deployos/console/apps/tai/<ten>")
    def deployos_apps_tai(ten):
        p = _duong_dan_trong(APPS_DIR, ten)
        if not p or not os.path.isfile(p):
            abort(404)
        return send_from_directory(APPS_DIR, os.path.basename(p), as_attachment=True)

    # --------------------------------------------------------- 2.3 script
    @app.route("/deployos/console/scripts")
    def deployos_scripts():
        return _trang_scripts()

    @app.route("/deployos/console/scripts/len", methods=["POST"])
    def deployos_scripts_len():
        f = request.files.get("file")
        if not f:
            return _trang_scripts("Chua chon file.", False)
        ok, msg = _nhan_tai_len(SCRIPTS_DIR, EXT_SCRIPT, "script")
        return _trang_scripts(msg, ok)

    @app.route("/deployos/console/scripts/xoa", methods=["POST"])
    def deployos_scripts_xoa():
        ok, msg = _xoa_file(SCRIPTS_DIR, request.form.get("ten", ""))
        return _trang_scripts(msg, ok)

    @app.route("/deployos/console/scripts/tai/<ten>")
    def deployos_scripts_tai(ten):
        p = _duong_dan_trong(SCRIPTS_DIR, ten)
        if not p or not os.path.isfile(p):
            abort(404)
        return send_from_directory(SCRIPTS_DIR, os.path.basename(p), as_attachment=True)
