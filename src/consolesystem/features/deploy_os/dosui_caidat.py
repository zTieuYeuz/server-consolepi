# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Tach tu deployos.py (B4).

(B4: tach nguyen van tu deployos.py::register_deployos; ten ham/route giu nguyen.)"""
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
from flask import (jsonify,
                   get_flashed_messages)
from ui.layout import doi_mau_viet_cung
from ui.home import _esc
from consolesystem.features.deploy_os.dosui_chung import (_msg, _tabs, _trang)  # noqa: F401


# ======================================= TAB "CAI DAT" cua Deployment OS
#
# LOI THAT DA GAP (anh Thoai: "nut pxe anh ma bam tat tu nhien dau mat
# tieu luon khong hien lai sao anh bat len duoc"): khoi dieu khien cu
# CHI co nut "Tat PXE" khi dang bat, con khi da tat thi KHONG co nut
# "Bat PXE" nao ca - chi hien 1 dong chu bao vao kich ban bam "Dung".
# Tuc la bam tat 1 cai la ket, khong co duong quay lai tu chinh trang
# do. Sua: LUON co nut cua trang thai nguoc lai, o ngay day.
#
# Bat PXE o day phuc vu ANH DIA DANG CO SAN (lan dung gan nhat), khong
# dung lai anh moi - dung cho truong hop "lo bam tat, bat lai de chay
# tiep". Muon doi sang kich ban KHAC thi van phai bam "Dung" o kich ban
# do (vi phai dung lai anh dia theo cau hinh cua no).
def _trang_caidat_pxe(msg="", ok=True):
    """
        Trang DUY NHAT bat/tat PXE (25/09/2026 - chi con menu, bo nut "Dung"
        o tung kich ban): chon che do mang + so giay cho -> Bat PXE. May
        khach boot qua mang luon thay menu va TU CHON kich ban.

        LOI THAT (25/09/2026): trang nay TUNG khong hien flash() - bam Bat
        PXE xong thong bao ket qua (thanh cong / loi gi) bi nuot mat, anh
        Thoai khong biet PXE co bat duoc khong.
        """
    from ui import pxe as _pxe
    from ui import pxemenu as _pm
    flash_html = "".join(_msg(nd, cat == "ok")
                         for cat, nd in get_flashed_messages(with_categories=True))
    dang_bat = _pxe.dang_bat()
    c = _pm.doc_cauhinh()
    muc = _pm.muc_menu()
    ten_kieu = dict((k, t) for k, t, _ in KIEU_BOOT)

    if dang_bat:
        kieu_dang_chay = _pxe.kieu_dang_bat() or c["kieu_boot"]
        trang_thai = f"""
            <div class="msg ok">PXE đang <strong>BẬT</strong> &mdash;
              chế độ <strong>{_esc(ten_kieu.get(kieu_dang_chay, kieu_dang_chay))}</strong>,
              cổng {_pxe.cong()}, Pi là {_esc(_pxe._dia_chi_pi_that(kieu_dang_chay))}.
              Menu có <strong>{len(muc)}</strong> kịch bản.<br>
              <span style="font-size:12.5px;">{_esc(_pxe.mo_ta_ket_noi(kieu_dang_chay))}</span></div>"""
        dieu_khien = f"""
            <form method="POST" action="/deployos/menu-pxe/luu" style="margin-bottom:12px;">
              <input type="hidden" name="ve" value="/deployos/caidat">
              <label style="display:block;margin-bottom:10px;">Không ai bấm thì
                khởi động ổ cứng sau
                <input type="number" name="cho_giay" min="0" max="{_pm.CHO_TOI_DA}"
                       value="{c['cho_giay']}" style="width:80px;"> giây
                <small style="color:#8b93a1;">(0 = chờ mãi)</small></label>
              <button type="submit" class="gray"
                data-busy="Đang cập nhật menu... KHÔNG bấm lại">
                Cập nhật menu</button>
              <small style="color:#8b93a1;margin-left:8px;">Dựng ảnh cho kịch
                bản mới/đã sửa (lưu kịch bản lúc PXE bật cũng tự làm).</small>
            </form>
            <form method="POST" action="/deployos/pxe/tat">
              <input type="hidden" name="ve" value="/deployos/caidat">
              <button type="submit" class="red" data-busy="Đang tắt...">
                Tắt PXE</button>
              <small style="color:#8b93a1;margin-left:8px;">Muốn đổi chế độ
                mạng: tắt rồi bật lại.</small>
            </form>"""
    else:
        o = ""
        for gt, ten, mo_ta in KIEU_BOOT:
            ch = " checked" if c["kieu_boot"] == gt else ""
            o += f"""
                <label class="chon">
                  <input type="radio" name="kieu_boot" value="{gt}"{ch}>
                  <span class="t">{_esc(ten)}</span>
                  <div class="d">{_esc(mo_ta)}</div>
                </label>"""
        if _pxe.san_sang_bat():
            nut = """
                <button type="submit"
                  data-busy="Đang bật PXE... chỉ vài giây, KHÔNG bấm lại">
                  Bật PXE</button>"""
        else:
            nut = ('<div class="msg err">Chưa đủ điều kiện để bật &mdash; '
                   'xem tab <a href="/deployos/caidat/hatang">Kiểm tra '
                   'hạ tầng</a>.</div>')
        trang_thai = """
            <div class="msg warn">PXE đang <strong>TẮT</strong>. Chọn chế độ
              mạng rồi bấm <strong>Bật PXE</strong>. Không chắc thì chọn
              <strong>"mạng có sẵn DHCP"</strong> &mdash; Pi không cấp IP nên
              không bao giờ tranh với router của mạng đó.</div>"""
        dieu_khien = f"""
            <form method="POST" action="/deployos/pxe/bat">
              <input type="hidden" name="ve" value="/deployos/caidat">
              {o}
              <label style="display:block;margin:12px 0;">Không ai bấm thì
                khởi động ổ cứng sau
                <input type="number" name="cho_giay" min="0" max="{_pm.CHO_TOI_DA}"
                       value="{c['cho_giay']}" style="width:80px;"> giây
                <small style="color:#8b93a1;">(0 = chờ mãi)</small></label>
              {nut}
            </form>"""

    # Kich ban trong menu - nguon that: file nhung (wimboot) co tren dia.
    ds = [k for k in danh_sach_kichban() if k.get("os_ho") == "windows"]
    co_anh = {n for n, *_r in muc}
    hang = ""
    for k in ds:
        ten = k.get("ten_kichban", k["_file"])
        thieu = _pm.thieu_cua(k)
        if thieu:
            tt = f'<span style="color:#f59e0b;">thiếu: {_esc(", ".join(thieu))}</span>'
        elif ten in co_anh:
            tt = '<span style="color:#4CAF50;">&#10003; có trong menu</span>'
        elif dang_bat:
            tt = ('<span style="color:#f59e0b;">chưa vào menu &mdash; bấm '
                  '"Cập nhật menu"</span>')
        else:
            tt = '<span style="color:#8b93a1;">vào menu khi bật PXE</span>'
        hang += f"<tr><td>{_esc(ten)}</td><td>{tt}</td></tr>"
    bang = (f"<table><tr><th>Kịch bản Windows</th><th>Trạng thái</th></tr>{hang}</table>"
            if ds else '<p style="color:#8b93a1;">Chưa có kịch bản Windows nào &mdash; '
                       'tạo ở tab <a href="/deployos/kichban">Kịch bản</a>.</p>')

    # ---- Cong mang dung cho PXE (chi hien o tuy chon khi may co tu 2 cong day)
    from ui import phancung as _pc
    cac_day = [x for x in _pc.danh_sach_cong() if not x["wifi"]]
    chon_tay = _pc._doc_chon_tay().get("day", "")
    cong_hien = _pxe.cong()
    if len(cac_day) >= 2:
        tuy = f'<option value=""{" selected" if not chon_tay else ""}>Tự chọn (cổng đang có tín hiệu)</option>'
        for x in cac_day:
            mo = "đang có tín hiệu" if x["co_day"] else "chưa cắm dây"
            tuy += (f'<option value="{_esc(x["ten"])}"{" selected" if x["ten"] == chon_tay else ""}>'
                    f'{_esc(x["ten"])} ({mo}) {_esc(x["mac"])}</option>')
        khoa = " disabled" if dang_bat else ""
        ghi = ('<small style="color:#f59e0b;">PXE đang bật: tắt PXE rồi mới đổi được cổng.</small>'
               if dang_bat else
               '<small style="color:#8b93a1;">Chọn đúng cổng cắm sang máy cần cài (hoặc vào switch của mạng cài).</small>')
        khung_cong = f"""
        <div class="card">
          <h3>Cổng mạng dùng cho PXE</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 8px;">Máy này có {len(cac_day)} cổng mạng dây.
            Đang dùng: <strong>{_esc(cong_hien)}</strong>{" (đã chọn tay)" if chon_tay else " (tự chọn)"}.
            Máy ảo/mini PC 2 card nên chọn tay để PXE không gắn nhầm vào cổng ra Internet hoặc cổng quản lý.</p>
          <form method="POST" action="/deployos/pxe/cong">
            <input type="hidden" name="ve" value="/deployos/caidat">
            <select name="cong"{khoa} style="min-width:320px;">{tuy}</select>
            <button type="submit" class="gray"{khoa}>Dùng cổng này</button>
            {ghi}
          </form>
        </div>"""
    else:
        khung_cong = ""

    man_chinh, man_con = _pm._xem_truoc(c, muc)
    kieu_pre = ("background:#000;color:#ddd;padding:12px;border-radius:6px;"
                "overflow-x:auto;font-size:13px;line-height:1.5;margin:6px 0 12px;")
    body = _tabs("caidat", "pxe") + _msg(msg, ok) + flash_html + f"""
        <div class="card">
          <h3>Bật / Tắt PXE</h3>
          {trang_thai}
          {dieu_khien}
        </div>
        {khung_cong}
        <div class="card">
          <h3>Menu máy khách sẽ thấy</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 8px;">
            Máy khách boot qua mạng thấy menu này và <strong>tự chọn kịch
            bản</strong> (phím mũi tên + Enter). Chỉ cài khi có người chọn;
            không ai bấm thì khởi động ổ cứng. Mọi kịch bản Windows đủ thông
            tin đều có trong menu.</p>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 8px;">
            <strong>Máy báo "Secure Boot Violation" / "Security Violation"</strong> khi nạp
            Windows: máy đời mới chỉ tin chứng chỉ Secure Boot 2023 của Microsoft. Trong
            menu chọn <strong>"4. May moi..."</strong> (bật chế độ dùng trình khởi động ký
            2023 - cần bộ cài Windows 11 24H2 trở lên) rồi chọn kịch bản như bình thường.
            Máy cũ thì để chế độ này tắt. Vẫn không được: cập nhật BIOS, hoặc tạm tắt
            Secure Boot lúc cài rồi bật lại.</p>
          {bang}
          <details style="margin-top:12px;">
            <summary>Xem trước màn hình máy khách</summary>
            <div style="color:#8b93a1;font-size:13px;margin-top:10px;">Menu chính:</div>
            <pre style="{kieu_pre}">{_esc(man_chinh)}</pre>
            <div style="color:#8b93a1;font-size:13px;">Sau khi chọn "1. Install Windows":</div>
            <pre style="{kieu_pre}">{_esc(man_con)}</pre>
          </details>
        </div>"""
    return _trang(body, "Cài đặt - Cài Windows qua mạng",
                  "Bật/tắt PXE và kiểm tra hạ tầng", active="/deployos")


def _trang_caidat_hatang(msg="", ok=True):
    """
        Kiem tra san sang (ui/sansang.py, 1.8.7) - thay bang "Kiem tra ha tang" cu (chi co
        1 dong file boot). Trang hien khung truoc, ket qua lay bang fetch (~5 giay vi phai
        nghe DHCP 3 giay) de nguoi dung thay ngay la dang kiem, khong tuong trang treo.
        """
    body = _tabs("caidat", "hatang") + _msg(msg, ok) + """
        <div class="card">
          <h3>Kiểm tra sẵn sàng trước khi cài</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 10px;">
            Kiểm tra trong khoảng 5 giây: dây mạng và tốc độ, máy chủ DHCP lạ trên mạng,
            dịch vụ PXE, chỗ trống, đồng hồ, file Windows của từng kịch bản, DNS của domain.
            Mục <span style="color:#ff6b6b;">đỏ</span> = cài bây giờ sẽ hỏng;
            <span style="color:#f59e0b;">vàng</span> = vẫn cài được nhưng nên sửa.
            Nên bấm lại sau khi cắm Pi vào mạng của khách.</p>
          <button type="button" id="ss-chay">Kiểm tra lại</button>
          <div id="ss-kq" style="margin-top:12px;"><p style="color:#8b93a1;">Đang kiểm tra...</p></div>
        </div>
        <script>
        (function() {
          var nut = document.getElementById('ss-chay'), kq = document.getElementById('ss-kq');
          function chay() {
            nut.disabled = true;
            kq.innerHTML = '<p style="color:#8b93a1;">Đang kiểm tra... (khoảng 5 giây)</p>';
            fetch('/deployos/caidat/hatang/chay', {cache: 'no-store'})
              .then(function(r) { return r.json(); })
              .then(function(d) { kq.innerHTML = d.html; })
              .catch(function() { kq.innerHTML = '<div class="msg err">Không chạy được kiểm tra.</div>'; })
              .then(function() { nut.disabled = false; });
          }
          nut.addEventListener('click', chay);
          chay();
        })();
        </script>"""
    return _trang(body, "Kiểm tra sẵn sàng",
                  "Mạng, DHCP, dịch vụ, file Windows, domain", active="/deployos")


def register_caidat(app):
    @app.route("/deployos/caidat/hatang/chay")
    def deployos_caidat_hatang_chay():
        from ui import sansang as _ss
        kq = _ss.kiem_tra()
        ten_kieu = dict((k, t) for k, t, _ in KIEU_BOOT)
        bieu = {"ok": ('&#10004;', '#4CAF50'), "canh": ('!', '#f59e0b'),
                "loi": ('&#10006;', '#ff6b6b'), "info": ('i', '#38bdf8')}
        hang = ""
        for x in kq["muc"]:
            b, mau = bieu.get(x["muc_do"], ("?", "#8b93a1"))
            sua = (f"<br><small style='color:#cbd5e1;'>Cách sửa: {_esc(x['sua'])}</small>"
                   if x["sua"] and x["muc_do"] != "ok" else "")
            hang += (f"<tr><td style='width:34px;color:{mau};font-weight:bold;text-align:center;'>{b}</td>"
                     f"<td><strong>{_esc(x['muc'])}</strong><br>"
                     f"<small style='color:#8b93a1;'>{_esc(x['noi_dung'])}</small>{sua}</td></tr>")
        if kq["so_loi"]:
            tom = (f'<div class="msg err"><strong>{kq["so_loi"]} lỗi</strong> cần sửa trước khi cài'
                   + (f', {kq["so_canh"]} cảnh báo' if kq["so_canh"] else "") + ".</div>")
        elif kq["so_canh"]:
            tom = f'<div class="msg warn">Cài được, còn <strong>{kq["so_canh"]} cảnh báo</strong> nên xem.</div>'
        else:
            tom = '<div class="msg ok"><strong>Sẵn sàng</strong> - không thấy vấn đề nào.</div>'
        tom += (f'<p style="color:#8b93a1;font-size:12.5px;margin:6px 0;">Chế độ mạng: '
                f'<strong>{_esc(ten_kieu.get(kq["kieu"], kq["kieu"]))}</strong> &middot; cổng '
                f'{_esc(kq["cong"])} &middot; PXE {"đang bật" if kq["pxe_bat"] else "đang tắt"} &middot; '
                f'{time.strftime("%H:%M:%S")}</p>')
        return jsonify({"html": doi_mau_viet_cung(tom + f"<div class='tbl-scroll'><table>{hang}</table></div>"),
                        "so_loi": kq["so_loi"], "so_canh": kq["so_canh"]})

    @app.route("/deployos/caidat")
    def deployos_caidat():
        return _trang_caidat_pxe()

    @app.route("/deployos/caidat/hatang")
    def deployos_caidat_hatang():
        return _trang_caidat_hatang()
