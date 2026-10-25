# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Tach tu deployos.py (B4).

(B4: tach nguyen van tu deployos.py::register_deployos; ten ham/route giu nguyen.)"""
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


CSS = """
    /* ---- Khoi bam-de-mo (gap lai cho do dai) ----
       Dung <details> chinh chu cua trinh duyet: bung/thu chay duoc ngay
       ca khi JS loi, va trinh duyet tu lo phan tro nang tiep can. */
    .gap { border:1px solid #2c3036; border-radius:8px; margin-bottom:10px;
           background:#1d2025; }
    .gap > summary { padding:14px 15px; min-height:52px; cursor:pointer;
        display:flex; align-items:center; gap:10px; font-size:14.5px;
        font-weight:600; color:#e6e9ee; list-style:none;
        -webkit-user-select:none; user-select:none; }
    .gap > summary::-webkit-details-marker { display:none; }
    .gap > summary::before { content:"\\25B8"; color:#6b7280; font-size:12px;
        transition:transform .15s; flex:none; }
    .gap[open] > summary::before { transform:rotate(90deg); }
    .gap > summary:active { background:#22262b; }
    .gap .dem { margin-left:auto; font-weight:400; font-size:12.5px;
        color:#8b93a1; background:#22262b; border:1px solid #2c3036;
        padding:3px 10px; border-radius:20px; white-space:nowrap; }
    .gap-trong { padding:0 12px 12px; }

    /* ---- Phan trang danh sach dai (toi da 25 muc / trang) ---- */
    .pt-an { display:none !important; }
    .pt-thanh { display:flex; flex-wrap:wrap; gap:6px; align-items:center; margin:8px 0; }
    .pt-thanh .pt-tt { color:#8b93a1; font-size:13px; margin-right:auto; }
    .pt-thanh button { min-width:34px; }
    .pt-thanh .pt-cham { color:#8b93a1; padding:0 2px; }
    .pt-tim { width:100%; max-width:380px; margin:6px 0 4px; }

    /* ---- O "Tom tat" trong bang danh sach kich ban ----
       Cat dung 2 DONG roi them "..." bang -webkit-line-clamp, khong cat
       theo so KY TU: cat theo ky tu thi tren man hinh rong se thua cho
       trong, tren man hinh hep (RasPad doc) lai van tran 3-4 dong. */
    .tt-gon { display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;
              overflow:hidden; color:#c9ced6; font-size:13px; line-height:1.45; }
    .tt-nut { margin-top:6px; min-height:34px; padding:4px 12px; font-size:12.5px;
              background:#22262b; border:1px solid #2c3036; color:#c9ced6;
              border-radius:6px; }
    .tt-hop { border:1px solid #2c3036; border-radius:10px; background:#1b1e22;
              color:#e6e9ee; max-width:min(640px, 92vw); width:100%; padding:18px; }
    .tt-hop::backdrop { background:rgba(0,0,0,.6); }
    .tt-hop h3 { margin:0 0 12px; color:#4CAF50; }
    .tt-bang { width:100%; border-collapse:collapse; font-size:13.5px; }
    .tt-bang td { padding:7px 9px; border-bottom:1px solid #2c3036;
                  vertical-align:top; }

    /* ---- Bang tra tham so cai dat ---- */
    .hang-tim { display:flex; gap:8px; margin-bottom:8px; }
    .hang-tim input[type=search] { flex:1; min-height:48px; font-size:15px; }
    .ket-qua { color:#8b93a1; font-size:12.5px; margin-bottom:10px; }
    .khong-thay { color:#f59e0b; font-size:13.5px; padding:14px 4px; }
    /* Bang rong hon man hinh thi cho cuon NGANG trong khung nay, khong
       de ca trang bi keo ngang (RasPad man hinh nho). */
    .bang-cuon { overflow-x:auto; -webkit-overflow-scrolling:touch; }
    .bang-ts { width:100%; border-collapse:collapse; font-size:13.5px; }
    .bang-ts th, .bang-ts td { text-align:left; vertical-align:top;
      padding:9px 10px; border-bottom:1px solid #2c3036; }
    .bang-ts th { color:#8b93a1; font-weight:600; font-size:12.5px;
      white-space:nowrap; position:sticky; top:0; background:#1b1e22; }
    .bang-ts td:first-child { font-weight:600; color:#e6e9ee; min-width:150px; }
    .bang-ts code { display:block; white-space:pre-wrap; word-break:break-all;
      font-size:12.5px; color:#a8d8b0; background:#1f2429; padding:6px 8px;
      border-radius:5px; border:1px solid #2c3036; }
    .bang-ts code.chep { cursor:pointer; position:relative; }
    .nhan-ng { display:inline-block; font-size:10.5px; font-weight:600; padding:1px 6px;
      border-radius:5px; margin-top:4px; white-space:nowrap; }
    .nhan-ng.kho { background:#12324a; color:#7cc8ff; }
    .nhan-ng.tu { background:#2a2140; color:#c8a8ff; }
    .nhan-ng.sua { background:#3a2a12; color:#ffcf7a; }
    .nhan-ng.xoa { background:#3a1616; color:#ff9b9b; }
    .bang-ts code.chep:active { transform:scale(.99); }
    .bang-ts code.da-chep { border-color:#4CAF50; background:#1f3a26; }
    .nhan-chep { position:absolute; right:6px; top:5px; font-size:11px;
      color:#4CAF50; background:#12331a; padding:1px 6px; border-radius:4px; }
    .cot-nut { white-space:nowrap; width:1%; }
    .cot-tich { width:1%; text-align:center; }
    .cot-tich input { width:18px; height:18px; cursor:pointer; }
    .cot-nut form { display:inline; }
    .nut-sua, .nut-huy { display:inline-flex; align-items:center;
      min-height:38px; padding:6px 13px; border-radius:6px; font-size:13px;
      background:#22262b; border:1px solid #2c3036; color:#c9ced6;
      margin-right:5px; }
    .bang-ts button.nho { min-height:38px; padding:6px 13px; font-size:13px; }
    .bang-ts button.do { background:#5a2222; border-color:#7a2e2e; }
    .o-sua { width:100%; min-width:160px; font-size:13px; }
    tr.dang-sua { background:#1f2a20; }
    .luoi-them { display:grid; gap:9px;
      grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); }
    .luoi-them textarea { width:100%; font-size:13.5px; }

    /* .dep-tab: dung kieu chung trong layout.py (co ca nen sang/toi) */

    /* Vach tien do cac buoc cua trinh tu tu chon */
    .buoc-bar { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:18px; }
    .buoc-o { flex:1; min-width:92px; padding:9px 8px; border-radius:6px;
      background:#22262b; border:1px solid #2c3036; text-align:center;
      font-size:12px; color:#8b93a1; }
    .buoc-o[data-den] { cursor:pointer; }
    .buoc-o[data-den]:hover { border-color:#4CAF50; color:#fff; }
    .buoc-o.qua { border-color:#4CAF50; color:#a8d5ab; }
    .buoc-o.nay { background:#1f3a26; border-color:#4CAF50; color:#fff; font-weight:600; }
    .buoc-o .so { display:block; font-size:15px; font-weight:700; margin-bottom:1px; }

    /* The lua chon lon (bam ca o, khong phai bam trung dung nut tron nho) */
    .chon { display:block; background:#22262b; border:2px solid #2c3036;
      border-radius:8px; padding:14px 16px; margin-bottom:10px; cursor:pointer; }
    .chon:active { transform:scale(.995); }
    .chon input { margin-right:9px; transform:scale(1.25); vertical-align:-1px; }
    .chon input[type=text], .chon input[type=number] { transform:none; margin:0; vertical-align:baseline; }
    .chon .d input[type=checkbox] { transform:none; margin-right:6px; vertical-align:middle; }
    .chon .t { font-size:15px; font-weight:600; color:#fff; }
    .chon .d { color:#8b93a1; font-size:13px; margin-top:5px; line-height:1.5; }
    .chon:has(> input:checked) { border-color:#4CAF50; background:#1f3a26; }

    .pv-hang { display:flex; gap:8px; margin-bottom:8px; flex-wrap:wrap; align-items:center; }
    .pv-hang input, .pv-hang select { max-width:none; width:auto; flex:1; min-width:110px; }
    .tt-bang td { vertical-align:top; }
    .tt-bang td:first-child { color:#8b93a1; width:190px; }

    /* Thanh tien do tai len */
    .tt-khung { margin-top:6px; }
    .tt-ten { font-size:14px; color:#fff; margin-bottom:9px; word-break:break-all; }
    .tt-thanh-ngoai { width:100%; height:22px; background:#22262b; border-radius:7px;
      overflow:hidden; border:1px solid #2c3036; }
    .tt-thanh { height:100%; width:0%; background:#4CAF50; border-radius:7px;
      transition:width .3s ease; }
    .tt-so { display:flex; justify-content:space-between; margin-top:9px;
      font-size:14px; flex-wrap:wrap; gap:8px; }
    .tt-phantram { font-weight:700; color:#4CAF50; font-family:ui-monospace,monospace;
      font-size:17px; }
    .tt-chitiet { color:#a8b0bd; font-family:ui-monospace,monospace; }
    .tt-dia { margin-top:9px; font-size:13px; color:#8b93a1; min-height:19px; }
    """


CSS_CHUNG = CSS


# JS cua thanh tien trinh - chi chen vao cac trang co form tai len
JS_PHAN_TRANG = r"""
    <script>
    (function () {
      var PER = 25;
      function boDau(s) {
        return (s || '').replace(/đ/g, 'd').replace(/Đ/g, 'D')
          .normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
      }
      function mucCua(c) {
        var ds = [], i, j;
        if (c.tagName === 'TABLE') {
          for (i = 0; i < c.rows.length; i++) {
            var r = c.rows[i], chiTh = r.cells.length > 0;
            for (j = 0; j < r.cells.length; j++) if (r.cells[j].tagName !== 'TH') { chiTh = false; break; }
            if (!chiTh) ds.push(r);
          }
        } else {
          for (i = 0; i < c.children.length; i++) {
            var e = c.children[i];
            if (e.classList.contains('chon') || e.hasAttribute('data-pt-muc')) ds.push(e);
          }
        }
        return ds;
      }
      function nutBam(st, thanh, nhan, trang, dangO, tat) {
        var b = document.createElement('button');
        b.type = 'button'; b.className = 'small' + (dangO ? '' : ' gray');
        b.textContent = nhan; b.disabled = !!tat;
        b.addEventListener('click', function () {
          st.trang = trang; ve(st);
          if (thanh === st.duoi) (st.tim || st.tren).scrollIntoView({block: 'start'});
        });
        return b;
      }
      function veThanh(st, thanh, tong, tu, den, trangMax, chon) {
        thanh.innerHTML = '';
        thanh.hidden = trangMax <= 1 && !st.q.length;
        if (thanh.hidden) return;
        var tt = document.createElement('span'); tt.className = 'pt-tt';
        tt.textContent = tong ? ('Hiện ' + (tu + 1) + '–' + den + ' / ' + tong + ' mục') : 'Không có mục nào khớp';
        if (chon !== null) tt.textContent += ' · Đã chọn: ' + chon;
        thanh.appendChild(tt);
        if (trangMax <= 1) return;
        var t = st.trang;
        thanh.appendChild(nutBam(st, thanh, '«', 1, false, t === 1));
        thanh.appendChild(nutBam(st, thanh, '‹ Trước', t - 1, false, t === 1));
        var last = 0;
        for (var n = 1; n <= trangMax; n++) {
          if (n === 1 || n === trangMax || Math.abs(n - t) <= 2) {
            if (n - last > 1) { var c = document.createElement('span'); c.className = 'pt-cham'; c.textContent = '…'; thanh.appendChild(c); }
            thanh.appendChild(nutBam(st, thanh, String(n), n, n === t, false));
            last = n;
          }
        }
        thanh.appendChild(nutBam(st, thanh, 'Sau ›', t + 1, false, t === trangMax));
        thanh.appendChild(nutBam(st, thanh, '»', trangMax, false, t === trangMax));
      }
      function ve(st, chiDem) {
        var ds = mucCua(st.c), khop = [], i, k;
        for (i = 0; i < ds.length; i++) {
          var e = ds[i];
          if (e.__tim === undefined) e.__tim = boDau(e.textContent);
          var ok = !e.hasAttribute('data-loc');
          for (k = 0; ok && k < st.q.length; k++) if (e.__tim.indexOf(st.q[k]) === -1) ok = false;
          if (ok) khop.push(e);
        }
        var tong = khop.length, trangMax = Math.max(1, Math.ceil(tong / st.per));
        if (st.trang > trangMax) st.trang = trangMax;
        if (st.trang < 1) st.trang = 1;
        var tu = (st.trang - 1) * st.per, den = Math.min(tong, tu + st.per);
        if (!chiDem) {
          for (i = 0; i < ds.length; i++) ds[i].classList.add('pt-an');
          for (i = tu; i < den; i++) khop[i].classList.remove('pt-an');
        }
        var coO = st.c.querySelector('input[type=checkbox]');
        var chon = coO ? st.c.querySelectorAll('input[type=checkbox]:checked').length : null;
        if (st.tim) st.tim.hidden = ds.length <= st.per;
        veThanh(st, st.tren, tong, tu, den, trangMax, chon);
        veThanh(st, st.duoi, tong, tu, den, trangMax, chon);
      }
      function tao(c) {
        var st = {c: c, per: parseInt(c.getAttribute('data-pt'), 10) || PER, trang: 1, q: [], tim: null};
        var goc = (c.tagName === 'TABLE' && c.parentNode.classList.contains('tbl-scroll')) ? c.parentNode : c;
        st.tren = document.createElement('div'); st.tren.className = 'pt-thanh';
        st.duoi = document.createElement('div'); st.duoi.className = 'pt-thanh';
        if (c.hasAttribute('data-pt-tim')) {
          st.tim = document.createElement('input');
          st.tim.type = 'search'; st.tim.className = 'pt-tim'; st.tim.autocomplete = 'off';
          st.tim.placeholder = 'Tìm trong danh sách... (gõ không dấu cũng được)';
          st.tim.addEventListener('input', function () {
            st.q = boDau(st.tim.value).split(/\s+/).filter(Boolean); st.trang = 1; ve(st);
          });
          goc.parentNode.insertBefore(st.tim, goc);
        }
        goc.parentNode.insertBefore(st.tren, goc);
        goc.parentNode.insertBefore(st.duoi, goc.nextSibling);
        c.addEventListener('change', function () { ve(st, true); });
        c.__pt = st;
        return st;
      }
      window.csPT = {capNhat: function (c, veTrang1) {
        var st = c.__pt || tao(c);
        if (veTrang1) st.trang = 1;
        ve(st);
      }};
      var ds = document.querySelectorAll('[data-pt]');
      for (var i = 0; i < ds.length; i++) window.csPT.capNhat(ds[i], true);
    })();
    </script>"""


JS_PHAN_TRANG_CHUNG = JS_PHAN_TRANG


JS_TIEN_DO = """
<script>
(function () {
  "use strict";
  function co(n) {
    if (n < 1024) return n + " B";
    var d = ["KB","MB","GB"], i = -1;
    do { n /= 1024; i++; } while (n >= 1024 && i < 2);
    return n.toFixed(1) + " " + d[i];
  }
  function thoiGian(giay) {
    if (!isFinite(giay) || giay < 0) return "";
    giay = Math.round(giay);
    if (giay < 60) return giay + " giay";
    var p = Math.floor(giay / 60), g = giay % 60;
    return p + " phut " + (g < 10 ? "0" : "") + g + " giay";
  }

  Array.prototype.forEach.call(
    document.querySelectorAll("form.form-tai-len"), function (form) {
    var khung = form.parentNode.querySelector(".tt-khung");
    if (!khung || !window.XMLHttpRequest || !window.FormData) return;  // de form thuong lo

    var thanh = khung.querySelector(".tt-thanh");
    var phantram = khung.querySelector(".tt-phantram");
    var chitiet = khung.querySelector(".tt-chitiet");
    var tenO = khung.querySelector(".tt-ten");
    var diaO = khung.querySelector(".tt-dia");
    var nutHuy = khung.querySelector(".tt-huy");
    var loai = form.getAttribute("data-loai") || "";
    var xhr = null, hen = null;

    form.addEventListener("submit", function (e) {
      var o = form.querySelector('input[type="file"]');
      if (!o || !o.files || !o.files.length) return;   // khong co file: de form bao loi
      e.preventDefault();

      var file = o.files[0];
      var batDau = Date.now();
      form.style.display = "none";
      khung.style.display = "block";
      tenO.textContent = file.name + "  (" + co(file.size) + ")";

      // Hoi may xem da ghi duoc bao nhieu XUONG DIA that. So nay moi la su
      // that cuoi cung - so byte trinh duyet gui di co the chay truoc no.
      function hoiDia() {
        if (!loai) return;
        var q = new XMLHttpRequest();
        q.open("GET", "/deployos/tien-do?loai=" + encodeURIComponent(loai) +
                      "&os_id=" + encodeURIComponent(form.getAttribute("data-os") || "") +
                      "&ten=" + encodeURIComponent(file.name), true);
        q.onload = function () {
          try {
            var d = JSON.parse(q.responseText);
            if (d.da_ghi > 0) {
              diaO.textContent = "Đã ghi xuống đĩa: " + co(d.da_ghi) +
                " / " + co(file.size);
            }
          } catch (err) { /* bo qua, khong lam hong viec tai len */ }
        };
        q.send();
      }
      hen = setInterval(hoiDia, 2000);

      xhr = new XMLHttpRequest();
      xhr.open("POST", form.getAttribute("action"), true);

      xhr.upload.onprogress = function (ev) {
        if (!ev.lengthComputable) return;
        var pt = Math.round(ev.loaded * 100 / ev.total);
        thanh.style.width = pt + "%";
        phantram.textContent = pt + "%";
        var giay = (Date.now() - batDau) / 1000;
        var tocDo = giay > 0 ? ev.loaded / giay : 0;
        var conLai = tocDo > 0 ? (ev.total - ev.loaded) / tocDo : Infinity;
        chitiet.textContent = co(ev.loaded) + " / " + co(ev.total) +
          "  -  " + co(tocDo) + "/s  -  con " + thoiGian(conLai);
      };

      xhr.upload.onload = function () {
        // Trinh duyet gui xong roi, nhung may co the con dang ghi not
        phantram.textContent = "100%";
        thanh.style.width = "100%";
        chitiet.textContent = "Da gui xong, dang hoan tat luu tren may...";
      };

      xhr.onload = function () {
        clearInterval(hen);
        // May tra ve nguyen trang ket qua -> thay the trang hien tai
        document.open();
        document.write(xhr.responseText);
        document.close();
      };
      xhr.onerror = function () {
        clearInterval(hen);
        diaO.innerHTML = '<span style="color:#ef4444;">Mất kết nối tới máy. ' +
          'File chưa được lưu - thử lại.</span>';
      };
      xhr.onabort = function () {
        clearInterval(hen);
        diaO.innerHTML = '<span style="color:#f59e0b;">Da huy tai len.</span>';
      };

      var fd = new FormData();
      fd.append("file", file);
      xhr.send(fd);
    });

    nutHuy.addEventListener("click", function () {
      if (xhr) xhr.abort();
      form.style.display = "";
      khung.style.display = "none";
      thanh.style.width = "0%";
      phantram.textContent = "0%";
      chitiet.textContent = "";
      diaO.textContent = "";
    });
  });
})();
</script>"""


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
                "Deployment OS", "Không đủ dung lượng"), 413
        return None
