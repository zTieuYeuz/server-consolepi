# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi - Tab "Deployment OS" (trien khai he dieu hanh qua mang)

Muc dich: khi gap 1 may PC hong ngoai hien truong, cam day mang vao Console
Pi roi boot thang vao moi truong cai dat qua mang (PXE), tu dong cai lai
Windows/Linux + phan mem + script tuy chinh - khong can mang theo USB cai
dat rieng, khong phai go tay tung buoc.

Mo hinh tham khao: MDT (Microsoft Deployment Toolkit) - vong chay tren
Windows Server. MDT KHONG cai len Linux/Pi duoc, nhung co che ben duoi no
dung (PXE -> WinPE -> script chia o/ap anh/cai driver/cai phan mem) thi
dung lai duoc bang cong cu Linux co san. Xem ke hoach day du:
docs/ke-hoach-pxe-winpe-tu-dong-cai-windows.md

-----------------------------------------------------------------------
TRANG THAI THAT CUA TINH NANG (KHONG BIA - doc ky truoc khi dung)
-----------------------------------------------------------------------
File nay lam phan GIAO DIEN + LUU CAU HINH: chon kieu boot, chon OS, khai
bao thong tin may, chia o dia, chon phan mem/script, luu thanh "kich ban"
dung lai nhieu lan.

Phan PHUC VU BOOT THAT SU (dnsmasq cau hinh PXE, bootloader iPXE, anh
WinPE, script chia o/ap anh chay trong WinPE) la GIAI DOAN KE TIEP, CHUA
duoc dung. Vi vay buoc cuoi cua trinh tu tu chon KHONG "gia vo" boot -
no chay 1 bang KIEM TRA SAN SANG doc trang thai THAT tren may (co file
boot chua, co iPXE chua, dnsmasq da cau hinh PXE chua) va noi ro con
thieu gi. Dung nguyen tac cua du an: khong bao gio bao "xong" khi chua
kiem chung duoc that.

-----------------------------------------------------------------------
LUU Y AN TOAN
-----------------------------------------------------------------------
1. Tab nay cho tai len file .exe/.msi/.bat/.ps1/.cmd - la nhung dinh dang
   MA LENH. Chung TUYET DOI KHONG duoc chay tren chinh con Pi: Pi chi LUU
   va PHUC VU chung cho may dich (may dang duoc cai lai) tai ve. Khong co
   duong nao trong file nay goi subprocess chay cac file do ca. Ngoai ra
   toan bo tab da nam sau dang nhap (xem ui/auth.py) nhu moi tab khac.
2. Kich ban co the chua mat khau cua tai khoan SE TAO tren may dich (can
   cho unattend.xml). Vi vay thu muc kich ban de quyen 700 va tung file
   600 (chi root doc duoc - dashboard chay quyen root), va giao dien KHONG
   bao gio hien lai mat khau ra man hinh (chi hien ***).
3. Duong dan luu CO DINH (/opt/console-pi/deploy), khong tu chuyen sang
   USB nhu tab Kho file. Ly do giong het tab TFTP: dich vu mang (dnsmasq/
   nginx) can duong dan ON DINH, khong duoc doi giua chung khi cam/rut USB.
"""
import sys as _sys
_sys.modules["ui.deployos"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import json
import os
import re
import secrets
import shutil
import subprocess
import time
import unicodedata

# ---------------------------------------------------------------- duong dan
# Duong dan du lieu khai bao tap trung o duongdan.py (xem ly do that o do:
# du lieu tung nam chung voi ma nguon nen `uninstall.sh` xoa sach ca bo cai
# Office 3.6GB lan toan bo kich ban).
from ui.duongdan import DEPLOY_DIR, BOOT_DIR, APPS_DIR, SCRIPTS_DIR, KICHBAN_DIR, OS_DIR, DRIVERS_DIR, UNGDUNG_DIR, FONTS_DIR, EXT_SCRIPT  # noqa: F401  (B3: khai bao o core/duongdan.py)
from ui import datten as _dt
from consolesystem.features.deploy_os.dos_chung import (BUOC_DAU, EXT_DRIVER, EXT_OS_ISO, EXT_OS_WIM, EXT_SXS, SO_BUOC, THU_MUC_THEO_DUONG, _bao_dam_thu_muc, _bo_dau_py, _con_trong_gb, _don_file_do_dang, _duong_dan_trong, _hoan_tat_ghi_thang, _liet_ke, _luu_tai_len, _mo_file_dich, _thu_muc_os_theo_duong, _xoa_file, bo_dau, co_kich_thuoc, so_hien_thi, ten_an_toan)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_phanmem import (GOI_Y_THAM_SO, HAU_TO_GO, _an_toan_trong_zip, _doc_meta_ungdung, _ghi_meta_ungdung, chuan_hoa_apps, chuan_hoa_ungdung, danh_sach_app, danh_sach_ungdung, dat_lenh_cai_ungdung, doc_thongtin_app, ghi_thongtin_app, giai_nen_ungdung, lay_ungdung, liet_ke_muc_ungdung, tao_ungdung_moi, tham_so_mac_dinh_app, xoa_muc_trong_ungdung, xoa_ungdung)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_font import (MAX_FONT_BYTE, MAX_ZIP_FONT_BYTE, _doc_meta_bo_font, _don_tam_cu, _giai_nen_font_zip, _id_bo_font_tu_ten, _luu_font_hop_le, _xoa_tam, chuan_hoa_fonts, danh_sach_bo_font, duong_bo_font, lay_bo_font, tao_bo_font, them_font_vao_bo, xoa_bo_font, xoa_font_trong_bo)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_os import (_CACHE_CHI_SO_PRO, chi_so_anh_pro, co_sxs, danh_sach_os, duong_boot_wim, duong_install_wim, lay_os, tao_os_moi, xoa_os)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_driver import (EXT_GOI_NEN_DRIVER, _tu_may, danh_sach_driver, dat_driver_cho_boot, dat_model_driver, driver_hop_model, giai_nen_goi_driver, khop_model, tao_driver_moi, xoa_driver, xoa_file_trong_driver)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_kichban import (MAU_PHAN_VUNG_WINDOWS, _TRUONG_KICHBAN, _WIZARD, _WIZARD_HAN, _cauhinh_mac_dinh, _don_wizard_cu, _dong_tongket_windows, _khoi_go_app, _phan_vung_mac_dinh, _pv_win, _u_tuychon, _wizard_lay, _wizard_moi, cauhinh_tu_kichban, danh_sach_kichban, doc_kichban, kiem_tra_san_sang, loi_bat_buoc, luu_kichban, thieu_gi, xoa_kichban)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_tomtat import (_mo_ta_ngan, _o_tom_tat, _ten_os, _tom_tat_day_du)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_hangso import (APPS_META, BAN_PHIM, DANH_SACH_OS, EXT_APP, EXT_BOOT, EXT_UNGDUNG_ZIP, EXT_WINPE, KIEU_BOOT, MIN_FREE_GB, MUI_GIO, NGON_NGU, TEN_BUOC, _unattend)  # noqa: F401  (B4: nguyen van o module nay)




































































































































































































# ==================================================================== giao dien
# ------------------------------------------------------------ khung tab
CSS_CHUNG = ""     # gan trong register_deployos
JS_PHAN_TRANG_CHUNG = ""


def ngu_canh_trienkhai():
    """True khi nguoi dung dang o muc "Trien khai phan mem" (cac trang Tai nguyen / Kho dung chung voi Deployment OS,
    chi khac thanh tab va khong hien He dieu hanh / Driver / WinPE). Dat boi ui/deploysw.py (before_request)."""
    try:
        from flask import session
        return session.get("nc") == "tk"
    except Exception:
        return False


def _tabs_trienkhai(chinh, phu=""):
    tab_chinh = [
        ("tainguyen", "Tài nguyên", "/deployos/console/apps"),
        ("kho", "Kho trung tâm", "/deployos/kho"),
        ("lich", "Lập lịch", "/deployos/trienkhai/lich"),
        ("may", "Máy - nhóm máy", "/deployos/trienkhai/may"),
        ("kichban", "Kịch bản", "/deployos/trienkhai/kichban"),
        ("chay", "Triển khai", "/deployos/trienkhai"),
        ("khac", "Kiểm tra bảo mật", "/deployos/trienkhai/khac"),
    ]
    phu_ds = {"tainguyen": [
        ("apps", "Phần mềm", "/deployos/console/apps"),
        ("ungdung", "Ứng dụng (nhiều file)", "/deployos/ungdung"),
        ("font", "Font chữ", "/deployos/font"),
        ("scripts", "Script", "/deployos/console/scripts"),
        ("nhom", "Nhóm tài nguyên", "/deployos/trienkhai/nhom-tn"),
    ], "may": [
        ("ds", "Danh sách máy", "/deployos/trienkhai/may"),
        ("nhom", "Nhóm máy", "/deployos/trienkhai/may/nhom"),
        ("quet", "Quét mạng", "/deployos/trienkhai/may/quet"),
        ("tk", "Tài khoản quản trị", "/deployos/trienkhai/may/taikhoan"),
    ]}
    h = '<div class="dep-tabs">' + "".join(
        f'<a href="{href}" class="dep-tab{" on" if ma == chinh else ""}">{nhan}</a>' for ma, nhan, href in tab_chinh) + "</div>"
    if phu and phu_ds.get(chinh):
        h += '<div class="dep-tabs sub">' + "".join(
            f'<a href="{href}" class="dep-tab{" on" if ma == phu else ""}">{nhan}</a>' for ma, nhan, href in phu_ds[chinh]) + "</div>"
    return h


def tabs_deployos(chinh, phu=""):
    """
    Thanh tab chinh + tab phu, dung chung cho moi trang cua muc nay.

    CAU TRUC CU (anh Thoai chi ra la SAI): "Kich ban" nam AN duoi 2 noi
    khac nhau ("Boot OS > Kich ban" VA "Console boot > 2.4 Kich ban")
    - kiem chung that: ca 2 cung doc/ghi CHUNG 1 du lieu
    (danh_sach_kichban()), chi la trung lap gay roi, khong phai hong du
    lieu. SUA (mo hinh MDT - "Task Sequences" la 1 nut GOC rieng, ngang
    hang voi "Operating Systems"/"Applications", khong nam lot duoi
    muc nao ca): dua "Kich ban" thanh 1 TAB GOC rieng, gop moi "tai
    nguyen" (He dieu hanh, Phan mem, Driver, Script, File boot) vao 1
    tab GOC khac.
    """
    if ngu_canh_trienkhai():
        return _tabs_trienkhai(chinh, phu)
    tab_chinh = [
        ("kichban", "Kịch bản", "/deployos/kichban"),
        ("tainguyen", "Tài nguyên", "/deployos/os"),
        ("kho", "Kho trung tâm", "/deployos/kho"),
        ("tiendo", "Tiến trình", "/deployos/tiendo"),
        ("caidat", "Cài đặt", "/deployos/caidat"),
    ]
    phu_theo_chinh = {
        "kichban": [
            ("ds", "Kịch bản", "/deployos/kichban"),
            ("odia", "Ổ đĩa đã dò", "/deployos/o-dia"),
        ],
        "tainguyen": [
            ("os", "Hệ điều hành", "/deployos/os"),
            ("apps", "Phần mềm", "/deployos/console/apps"),
            ("ungdung", "Ứng dụng (nhiều file)", "/deployos/ungdung"),
            ("font", "Font chữ", "/deployos/font"),
            ("drivers", "Driver", "/deployos/drivers"),
            ("scripts", "Script", "/deployos/console/scripts"),
            ("file", "WinPE", "/deployos/console"),
        ],
        "tiendo": [
            ("dang", "Đang cài", "/deployos/tiendo"),
            ("lichsu", "Lịch sử", "/deployos/lichsu"),
        ],
        "caidat": [
            ("pxe", "Bật / Tắt PXE", "/deployos/caidat"),
            ("hatang", "Kiểm tra sẵn sàng", "/deployos/caidat/hatang"),
            ("wol", "Bật máy từ xa", "/deployos/caidat/wol"),
        ],
    }
    h = '<div class="dep-tabs">'
    for ma, nhan, href in tab_chinh:
        h += (f'<a href="{href}" class="dep-tab{" on" if ma == chinh else ""}">'
              f'{nhan}</a>')
    h += "</div>"
    if phu:
        h += '<div class="dep-tabs sub">'
        for ma, nhan, href in phu_theo_chinh.get(chinh, []):
            h += (f'<a href="{href}" class="dep-tab{" on" if ma == phu else ""}">'
                  f'{nhan}</a>')
        h += "</div>"
    return h


_JS_TAI_FONT = """
<script>
(function () {
  "use strict";
  var URL_LEN = "__URL__";
  var DUOI = /\\.(ttf|otf|ttc|otc|zip|woff2?)$/i;
  var hang = [], dang = false, tong = 0, xong = 0, them = 0, loi = [], batDau = 0;
  var tha = document.getElementById("fo-tha"), tt = document.getElementById("fo-tt"),
      thanh = document.getElementById("fo-thanh"), chu = document.getElementById("fo-chu"),
      kq = document.getElementById("fo-ketqua");
  function esc(t) { var d = document.createElement("div"); d.textContent = t; return d.innerHTML; }
  function co(n) {
    if (n < 1048576) return Math.round(n / 1024) + " KB";
    return (n / 1048576).toFixed(1) + " MB";
  }
  function hien() {
    var pt = tong ? Math.round(xong * 100 / tong) : 0;
    thanh.style.width = pt + "%";
    chu.textContent = "Đang tải: " + xong + " / " + tong + " file (đã thêm " + them + " font)";
  }
  function them_vao(files) {
    var bo = [];
    Array.prototype.forEach.call(files, function (f) {
      if (DUOI.test(f.name)) { hang.push(f); tong++; } else { bo.push(f.name); }
    });
    if (bo.length) loi.push("Bỏ qua " + bo.length + " file không phải font: " +
      bo.slice(0, 5).join(", ") + (bo.length > 5 ? "..." : ""));
    if (!hang.length && !dang) { ketThuc(); return; }
    if (!dang) { dang = true; batDau = Date.now(); tt.style.display = "block"; kq.innerHTML = ""; hien(); tiep(); }
  }
  function tiep() {
    var f = hang.shift();
    if (!f) { ketThuc(); return; }
    var x = new XMLHttpRequest();
    x.open("POST", URL_LEN, true);
    x.onload = function () {
      var r;
      try { r = JSON.parse(x.responseText); }
      catch (e) { r = { ok: false, msg: f.name + ": máy trả lời lạ (mã " + x.status + ")", them: 0, bo_qua: [] }; }
      if (r.ok) them += r.them; else loi.push(r.msg);
      (r.bo_qua || []).forEach(function (m) { loi.push(m); });
      xong++; hien(); tiep();
    };
    x.onerror = function () { loi.push(f.name + ": mất kết nối tới máy, file này chưa được lưu"); xong++; hien(); tiep(); };
    var fd = new FormData();
    fd.append("file", f, f.name);
    x.send(fd);
  }
  function ketThuc() {
    dang = false;
    var giay = Math.max(1, Math.round((Date.now() - batDau) / 1000));
    var h = '<div style="color:' + (them ? "#6ee7a0" : "#f59e0b") + ';">Xong: đã thêm <strong>' + them +
            "</strong> font (" + giay + " giây).</div>";
    if (loi.length) {
      h += '<div style="color:#f59e0b;margin-top:6px;">Có ' + loi.length + " thông báo:</div><ul style='margin:4px 0 0;padding-left:20px;color:#fbbf24;'>" +
           loi.slice(0, 40).map(function (m) { return "<li>" + esc(m) + "</li>"; }).join("") +
           (loi.length > 40 ? "<li>... và " + (loi.length - 40) + " thông báo nữa</li>" : "") + "</ul>";
    }
    if (them) h += '<div style="margin-top:10px;"><a class="btn" href="">Tải lại trang để xem danh sách</a></div>';
    kq.innerHTML = h;
    tt.style.display = "none";
    tong = xong = them = 0; loi = [];
    if (!kq.querySelector("li") && h.indexOf("btn") > -1) setTimeout(function () { location.reload(); }, 1500);
  }
  document.getElementById("fo-file").addEventListener("change", function () { them_vao(this.files); this.value = ""; });
  document.getElementById("fo-thumuc").addEventListener("change", function () { them_vao(this.files); this.value = ""; });

  function layFiles(entry) {
    return new Promise(function (res) {
      if (entry.isFile) { entry.file(function (f) { res([f]); }, function () { res([]); }); return; }
      var r = entry.createReader(), tat = [];
      (function doc() {
        r.readEntries(async function (es) {
          if (!es.length) { res(tat); return; }
          for (var i = 0; i < es.length; i++) tat = tat.concat(await layFiles(es[i]));
          doc();
        }, function () { res(tat); });
      })();
    });
  }
  ["dragenter", "dragover"].forEach(function (ev) {
    tha.addEventListener(ev, function (e) { e.preventDefault(); tha.classList.add("keo"); });
  });
  ["dragleave", "drop"].forEach(function (ev) {
    tha.addEventListener(ev, function (e) { e.preventDefault(); tha.classList.remove("keo"); });
  });
  tha.addEventListener("drop", async function (e) {
    var items = e.dataTransfer && e.dataTransfer.items, tat = [];
    if (items && items.length && items[0].webkitGetAsEntry) {
      var entries = [];
      for (var i = 0; i < items.length; i++) { var en = items[i].webkitGetAsEntry(); if (en) entries.push(en); }
      for (var j = 0; j < entries.length; j++) tat = tat.concat(await layFiles(entries[j]));
    } else { tat = Array.prototype.slice.call(e.dataTransfer.files); }
    them_vao(tat);
  });
  var loc = document.getElementById("fo-loc");
  if (loc) loc.addEventListener("input", function () {
    var q = loc.value.toLowerCase().trim();
    Array.prototype.forEach.call(document.querySelectorAll("#fo-bang tr[data-t]"), function (tr) {
      tr.style.display = (!q || tr.getAttribute("data-t").indexOf(q) > -1) ? "" : "none";
    });
  });
})();
</script>
"""


def ve_bao_cao_o_dia(kq, nut_chon=False):
    """HTML cho 1 bao cao "Do o dia" (ui/doodia.py). nut_chon=True: moi o co nut dien so o
    vao o "O dia so" cua buoc chia o (kich ban)."""
    from ui.home import _esc
    from ui import doodia as _od
    may = " ".join(x for x in (kq.get("hang"), kq.get("model")) if x) or "Máy không rõ tên"
    phu = [f"MAC {', '.join(kq['mac'])}" if kq.get("mac") else "",
           f"IP {', '.join(kq['ip'])}" if kq.get("ip") else "",
           kq.get("firmware") or "", "dò lúc " + _od.gio(kq["luc"])]
    hang = ""
    for o in kq.get("o", []):
        vol = "<br>".join(
            f"<code>{_esc(v['chu'] + ':') if v['chu'] else '&nbsp;&nbsp;'}</code> "
            f"{_esc(v['nhan'] or '(không nhãn)')} &middot; {_esc(v['fs'] or '?')} &middot; "
            f"{_esc(v['dung_luong'])}" + (f" <small style='color:#8b93a1;'>{_esc(v['info'])}</small>"
                                          if v['info'] else "")
            for v in o["volume"])
        if not vol:
            vol = ("<span style='color:#8b93a1;'>Không có phân vùng nào có hệ thống file</span>"
                   if not o["phan_vung"] else
                   f"<span style='color:#8b93a1;'>{len(o['phan_vung'])} phân vùng, không có ổ đọc được "
                   "(BitLocker / Linux / chưa định dạng?)</span>")
        pv = ", ".join(f"{p['kieu']} {p['dung_luong']}" for p in o["phan_vung"])
        loai = (o.get("loai") or "").upper()
        canh = ""
        if loai in ("USB", "SD", "MMC"):
            canh = ("<div style='color:#f59e0b;font-size:12px;'>Ổ USB/thẻ nhớ - thường KHÔNG "
                    "phải ổ để cài Windows</div>")
        if o["volume"] and any((v.get("fs") or "").upper() == "NTFS" for v in o["volume"]):
            canh += ("<div style='color:#fca5a5;font-size:12px;'>Đang có dữ liệu Windows/NTFS - "
                     "cài lên ổ này sẽ XÓA SẠCH</div>")
        nut = (f'<button type="button" class="small" onclick="var i=document.querySelector(\'[name=o_dia_so]\');'
               f'if(i){{i.value={o["so"]};i.focus();}}">Dùng ổ {o["so"]}</button>' if nut_chon else "")
        hang += f"""
          <tr>
            <td style="font-size:20px;font-weight:700;text-align:center;">{o['so']}</td>
            <td><strong>{_esc(o['model'] or '?')}</strong><br>
                <small style="color:#8b93a1;">{_esc(o.get('loai') or '?')} &middot;
                {'GPT' if o.get('gpt') else ('MBR / chưa chia' if o['phan_vung'] or o['volume'] else 'chưa chia')}
                &middot; còn trống {_esc(o.get('trong') or '?')}</small>{canh}</td>
            <td style="white-space:nowrap;">{_esc(o.get('dung_luong') or '?')}</td>
            <td>{vol}<br><small style="color:#6b7280;">{_esc(pv)}</small></td>
            {'<td>' + nut + '</td>' if nut_chon else ''}
          </tr>"""
    if not hang:
        hang = ('<tr><td colspan="5" style="color:#f59e0b;">Không thấy ổ đĩa nào - xem cảnh báo '
                'phía trên và bản gốc bên dưới.</td></tr>')
    khung = ""
    for muc, nd in _od.canh_bao_may(kq):
        mau = ("#7f1d1d", "#fecaca") if muc == "do" else ("#78350f", "#fde68a")
        khung += (f'<div style="background:{mau[0]}33;border:1px solid {mau[0]};color:{mau[1]};border-radius:8px;'
                  f'padding:8px 12px;margin:0 0 8px;font-size:13px;">{"⛔" if muc == "do" else "⚠️"} {_esc(nd)}</div>')
    return f"""
      <div class="card">
        <h3 style="margin-bottom:2px;">{_esc(may)}</h3>
        <p style="color:#8b93a1;font-size:13px;margin:0 0 10px;">
          {_esc(' · '.join(x for x in phu if x))}</p>
        {khung}
        <div class="tbl-scroll"><table>
          <tr><th style="width:56px;">Ổ số</th><th>Ổ đĩa</th><th style="width:90px;">Dung lượng</th>
              <th>Phân vùng (chữ ổ · tên · định dạng · dung lượng)</th>
              {'<th style="width:90px;"></th>' if nut_chon else ''}</tr>
          {hang}
        </table></div>
        <details style="margin-top:8px;"><summary style="cursor:pointer;color:#8b93a1;font-size:13px;">
          Bản gốc (diskpart)</summary>
          <pre style="max-height:320px;overflow:auto;font-size:12px;">{_esc(kq['noi_dung'])}</pre>
        </details>
      </div>"""


def register_deployos(app):
    from flask import (request, redirect, send_from_directory, abort, jsonify,
                       flash, get_flashed_messages, session, g)
    from ui.layout import render_page, doi_mau_viet_cung
    from ui.home import _esc

    # --- Khai bao cac duong tai len duoc phep ghi THANG ra dia dich ---
    THU_MUC_THEO_DUONG.update({
        "/deployos/console/file/len": (BOOT_DIR, EXT_WINPE),
        "/deployos/console/apps/len": (APPS_DIR, EXT_APP),
        "/deployos/console/scripts/len": (SCRIPTS_DIR, EXT_SCRIPT),
    })

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
            except Exception:
                pass
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
            except Exception:
                pass
            ok, msg, _duong_dich = _hoan_tat_ghi_thang(duong, thu_muc, f.filename)
            return ok, msg
        # Khong ghi thang duoc (vd duoi file khong hop le -> da do vao
        # /dev/null): bao loi ro rang thay vi im lang
        ten = ten_an_toan(f.filename)
        if os.path.splitext(ten)[1].lower() not in duoi_cho_phep:
            return False, (f"Không nhận đuôi file này cho mục {nhan}. Chỉ nhận: "
                           f"{', '.join(sorted(duoi_cho_phep))}")
        return _luu_tai_len(f, thu_muc, duoi_cho_phep, nhan)

    @app.route("/deployos/tien-do")
    def deployos_tien_do():
        """
        Bao cho trang biet may DA GHI DUOC bao nhieu byte xuong dia that.

        Doc thang kich thuoc file <ten>.part dang duoc ghi. Nho vay thanh
        tien trinh bam theo tien do THAT tren dia, khong phai chi theo so
        byte trinh duyet da gui di (hai so nay lech nhau khi mang nhanh hon
        the nho - dung tinh huong lam anh Thoai tuong may bi treo).
        """
        loai = request.args.get("loai", "")
        ten = ten_an_toan(request.args.get("ten", ""))
        # Thu muc he dieu hanh la DONG (moi os_id mot thu muc) nen khong nam
        # trong bang tra co dinh ben duoi - form gui kem "os_id" rieng.
        # Thieu nhanh nay thi thanh tien trinh cua trang He dieu hanh (ke ca
        # duong tai ISO 5GB moi them) luon bao "da ghi 0" du may dang ghi
        # binh thuong - nhin y het bi treo.
        if loai in ("os", "os-iso", "os-sxs"):
            os_id = ten_an_toan(request.args.get("os_id", ""))
            thu_muc = os.path.join(OS_DIR, os_id) if os_id else None
            if thu_muc and loai == "os-sxs":
                thu_muc = os.path.join(thu_muc, "sxs")
        else:
            thu_muc = {"file": BOOT_DIR, "apps": APPS_DIR,
                       "scripts": SCRIPTS_DIR}.get(loai)
        if not thu_muc or not ten:
            return jsonify({"da_ghi": 0, "xong": False})
        p = os.path.join(thu_muc, ten + ".part")
        try:
            return jsonify({"da_ghi": os.path.getsize(p), "xong": False})
        except OSError:
            # Khong con .part: hoac chua bat dau, hoac da doi ten -> xong
            xong = os.path.isfile(os.path.join(thu_muc, ten))
            return jsonify({"da_ghi": 0, "xong": xong})

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
    # Trang cua module khac (lichsu, wol...) dung chung CSS nay (phan trang .pt-an...)
    global CSS_CHUNG, JS_PHAN_TRANG_CHUNG
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

    # =================================================== 1. TAB "BOOT OS"
    @app.route("/deployos")
    def deployos_home():
        return redirect("/deployos/kichban")

    def _khoi_dang_phuc_vu():
        """
        Dong trang thai PXE o dau trang Kich ban / buoc tong ket. Tu
        25/09/2026 khong con "kich ban dang Dung": PXE bat = menu, may khach
        tu chon - chi can noi PXE bat chua, che do nao, menu co may muc.
        """
        from ui import pxe as _pxe
        from ui import pxemenu as _pm
        if not _pxe.dang_bat():
            return ('<div class="msg warn"><strong>PXE đang tắt</strong> &mdash; '
                    'máy boot qua mạng chưa thấy menu. Bật ở '
                    '<a href="/deployos/caidat">Cài đặt &rarr; Bật / Tắt PXE</a>.</div>')
        kieu = _pxe.kieu_dang_bat()
        ten_kieu = dict((k, t) for k, t, _ in KIEU_BOOT).get(kieu, kieu)
        return (f'<div class="msg ok"><strong>PXE đang bật</strong> ({_esc(ten_kieu)}) '
                f'&mdash; menu có <strong>{len(_pm.muc_menu())}</strong> kịch bản, '
                f'máy khách tự chọn khi boot qua mạng. '
                f'<a href="/deployos/caidat">Cài đặt PXE</a></div>')

    @app.route("/deployos/kichban")
    def deployos_boot():
        """
        Trang GOC duy nhat cho "Kich ban" (mo hinh MDT: nut "Task
        Sequences") - danh sach kich ban da luu la NOI DUNG CHINH, "Tao
        kich ban moi" la 1 nut dan toi trinh tu tung buoc (wizard). Thay
        cho 2 trang trung lap truoc day (xem ghi chu tai _tabs()).
        """
        from ui import pxemenu as _pm
        ds_kb = danh_sach_kichban()
        if ds_kb:
            hang = ""
            for k in ds_kb:
                hang += f"""
                <tr>
                  <td><strong>{_esc(k.get('ten_kichban', k['_file']))}</strong></td>
                  <td>{_o_tom_tat(k, _esc)}</td>
                  <td style="color:#8b93a1;">{_esc(k.get('_ngay', ''))}</td>
                  <td>{_pm.trang_thai_html(k, _esc)}</td>
                  <td>
                    <a class="btn small gray"
                       href="/deployos/kichban/sua/{_esc(k['_file'])}">Chỉnh sửa</a>
                    <form method="POST" action="/deployos/kichban/xoa" style="display:inline;"
                          onsubmit="return confirm('Xóa kịch bản này?');">
                      <input type="hidden" name="ten" value="{_esc(k['_file'])}">
                      <button type="submit" class="red small">Xóa</button>
                    </form>
                  </td>
                </tr>"""
            noi_dung = f"""
            <div class="tbl-scroll"><table>
              <tr><th>Tên kịch bản</th><th>Tóm tắt</th>
                  <th style="width:140px;">Ngày tạo</th>
                  <th style="width:140px;">Menu PXE</th>
                  <th style="width:150px;">Thao tác</th></tr>
              {hang}
            </table></div>"""
        else:
            noi_dung = ('<p style="color:#8b93a1;">Chưa có kịch bản nào. '
                       'Bấm "Tạo kịch bản mới" bên dưới để tạo cái đầu tiên.</p>')

        # Thong diep ket qua sau khi bam "Dung" (chay ngay kich ban) -
        # nut do redirect ve day nen phai hien flash o day, khong thi
        # nguoi dung khong biet chay duoc hay khong.
        flash_html = "".join(
            _msg(nd, cat == "ok")
            for cat, nd in get_flashed_messages(with_categories=True))
        body = _tabs("kichban", "ds") + flash_html + _khoi_dang_phuc_vu() + f"""
        <div class="card">
          <h3>Tạo kịch bản mới</h3>
          <p style="color:#8b93a1;font-size:13.5px;margin:0 0 13px;">
            Đi qua {len(TEN_BUOC)} bước: chọn OS &rarr; thông tin
            máy &rarr; chia ổ đĩa &rarr; phần mềm/driver &rarr; chỉnh sửa
            cài đặt &rarr; tổng kết. Lưu lại để dùng nhiều lần, không phải
            chọn lại từ đầu.</p>
          <a class="btn" href="/deployos/wizard/bat-dau?che_do=chay">
            Tạo kịch bản mới &rarr;</a>
        </div>

        <h2>Kịch bản đã lưu ({len(ds_kb)})</h2>
        {noi_dung}"""
        return _trang(body, "Deployment OS",
                      "Triển khai hệ điều hành qua mạng cho máy cần cài lại")

    @app.route("/deployos/kichban/xoa", methods=["POST"])
    def deployos_kichban_xoa():
        ok, msg = xoa_kichban(request.form.get("ten", ""))
        if ok:
            # Menu PXE liet ke TAT CA kich ban Windows - xoa thi bo khoi menu
            # (va xoa anh dia cua no) ngay, khong phai tat-bat lai PXE.
            from ui import pxe as _pxe
            them = _pxe.cap_nhat_menu()
            if them:
                flash(msg + them, "ok")
        return redirect("/deployos/kichban")

    def _nap_kichban_vao_trinh_tu(ten):
        """Nap 1 kich ban da luu vao 1 trinh tu moi. Tra ve (ma, kb)."""
        kb = doc_kichban(ten)
        if kb is None:
            return None, None
        _don_wizard_cu()
        ma = secrets.token_urlsafe(12)
        _WIZARD[ma] = cauhinh_tu_kichban(kb)
        return ma, kb

    @app.route("/deployos/kichban/mau-csv")
    def deployos_kichban_mau_csv():
        """File CSV mau (serial,ten_may) cho cach dat ten may 'doi chieu danh sach' (ui/datten.py)."""
        from flask import Response
        return Response(_dt.mau_csv().encode("utf-8"), mimetype="text/csv",
                        headers={"Content-Disposition": "attachment; filename=danh-sach-may-mau.csv"})

    @app.route("/deployos/kichban/sua/<ten>")
    def deployos_sua_kichban(ten):
        """
        "Chinh sua" = nap kich ban vao trinh tu roi vao TUNG BUOC de sua,
        cuoi cung luu lai (nut "Luu de len kich ban ..." o buoc tong ket).
        """
        ma, _kb = _nap_kichban_vao_trinh_tu(ten)
        if ma is None:
            flash("Không tìm thấy kịch bản.", "err")
            return redirect("/deployos/kichban")
        return redirect(f"/deployos/wizard/{ma}/{BUOC_DAU}")

    # ================================================ TRINH TU TU CHON (wizard)
    @app.route("/deployos/wizard/bat-dau")
    def deployos_wizard_batdau():
        che_do = request.args.get("che_do", "chay")
        if che_do not in ("chay", "luu"):
            che_do = "chay"
        ma = _wizard_moi(che_do)
        return redirect(f"/deployos/wizard/{ma}/{BUOC_DAU}")

    def _het_han():
        return _trang(
            _tabs("kichban") +
            '<div class="msg warn">Trình tự này đã hết hạn hoặc dashboard vừa '
            'khởi động lại nên không còn giữ được lựa chọn đang dở. '
            '<a href="/deployos/boot">Bắt đầu lại</a> - kịch bản đã lưu trên '
            'đĩa thì không mất.</div>',
            "Deployment OS")

    @app.route("/deployos/wizard/<ma>/<int:buoc>", methods=["GET", "POST"])
    def deployos_wizard(ma, buoc):
        d = _wizard_lay(ma)
        if d is None:
            return _het_han()
        if buoc < BUOC_DAU or buoc > SO_BUOC:
            return redirect(f"/deployos/wizard/{ma}/{BUOC_DAU}")

        if request.method == "POST":
            loi = _nhan_du_lieu_buoc(d, buoc, request.form)
            huong = request.form.get("huong", "tiep")
            if huong == "lui":
                return redirect(f"/deployos/wizard/{ma}/{max(BUOC_DAU, buoc - 1)}")
            # Bam thang vao o buoc tren thanh tien do (anh Thoai 01/10/2026: "linh hoat
            # bam vao o muon toi"): LUON nhay, KHONG giu lai vi thieu du lieu - phan da
            # nhap van duoc ghi. Cho thieu/sai chi nhac o trang dich, va buoc Tong ket
            # chan luu cho toi khi sua xong (xem loi_bat_buoc).
            den = request.form.get("den", "")
            if den.isdigit() and BUOC_DAU <= int(den) <= SO_BUOC:
                if loi:
                    from flask import flash
                    flash(f"Bước {so_hien_thi(buoc)} ({dict(TEN_BUOC)[buoc]}) còn lỗi: {loi} "
                          "- quay lại sửa trước khi lưu.", "loi")
                return redirect(f"/deployos/wizard/{ma}/{int(den)}")
            if loi:
                return _ve_buoc(ma, d, buoc, loi=loi)
            if buoc < SO_BUOC:
                return redirect(f"/deployos/wizard/{ma}/{buoc + 1}")
            return redirect(f"/deployos/wizard/{ma}/{SO_BUOC}")

        return _ve_buoc(ma, d, buoc)

    def _nhan_du_lieu_buoc(d, buoc, form):
        """Ghi lua chon cua 1 buoc vao trang thai. Tra ve chuoi loi neu thieu."""
        if buoc == 1:
            v = form.get("kieu_boot", "")
            if v not in [k for k, _, _ in KIEU_BOOT]:
                return "Chưa chọn kiểu boot."
            d["kieu_boot"] = v

        elif buoc == 2:
            os_id = form.get("os_id", "")
            o = lay_os(os_id)
            if o is None:
                return "Chưa chọn hệ điều hành (hoặc chưa tạo hệ điều hành nào - vào tab Tài nguyên > Hệ điều hành)."
            if not o["san_sang"]:
                return f'"{o["ten_hien_thi"]}" còn thiếu boot.wim/install.wim - vào "Tài nguyên > Hệ điều hành" tải lên trước.'
            # Doi OS ho khac thi bo phan vung chia tay cu di (bo phan vung
            # cua Windows va Linux khac han nhau - giu lai se sai)
            if d.get("os_ho") and d["os_ho"] != o["os_ho"]:
                d["phan_vung"] = []
            d["os_id"] = os_id
            d["os_ho"] = o["os_ho"]
            d["driver_ids"] = form.getlist("driver_ids")

        elif buoc == 3:
            d["ten_may"] = (form.get("ten_may") or "").strip()
            # --- 1.9.4: 5 cach dat ten may (ui/datten.py) ---
            che = form.get("ten_may_che_do") or "co_dinh"
            d["ten_may_che_do"] = che if che in _dt.CHE_DO else "co_dinh"
            for truong, nguon in (("ten_may_tiento", "ten_may_tiento"), ("ten_may_tiento_ngau", "ten_may_tiento_ngau")):
                if nguon in form:
                    tho = (form.get(nguon) or "").strip()
                    if tho and (len(tho) > _dt.TIENTO_TOI_DA or not re.fullmatch(r"[A-Za-z0-9-]+", tho)
                                or tho.startswith("-") or tho.endswith("-")):
                        return (f"Tiền tố tên máy \"{tho[:20]}\" không hợp lệ: chỉ chữ không dấu, số, dấu gạch "
                                f"ngang, tối đa {_dt.TIENTO_TOI_DA} ký tự.")
                    d[truong] = tho
            d["_ten_may_csv_canhbao"] = []
            if form.get("ten_may_csv_xoa"):
                d["ten_may_csv"], d["ten_may_csv_ten"] = {}, ""
            tep = request.files.get("ten_may_csv_file")
            if tep is not None and tep.filename:
                ds_csv, loi_csv, canh_csv = _dt.doc_csv(tep.read(_dt.MAX_BYTE_CSV + 1))
                if loi_csv or not ds_csv:
                    return ("File CSV không được nạp vì có lỗi (sửa file rồi chọn lại): "
                            + (" · ".join(loi_csv[:8]) or "không có dòng hợp lệ nào")
                            + (f" · ... và {len(loi_csv) - 8} lỗi nữa" if len(loi_csv) > 8 else "")
                            + ". Tải file mẫu ở khung này để xem đúng định dạng (serial,ten_may).")
                d["ten_may_csv"], d["ten_may_csv_ten"] = ds_csv, os.path.basename(tep.filename)[:80]
                d["_ten_may_csv_canhbao"] = canh_csv[:10]
            if d["ten_may_che_do"] == "csv" and not d.get("ten_may_csv"):
                return "Chưa chọn file CSV danh sách máy. Bấm \"Tải file CSV mẫu\", điền serial và tên máy, rồi chọn file đó."
            # Linux: tai khoan thuong (username/password). Windows: KHONG tao user,
            # chi dung Administrator co san (anh Thoai 04/10/2026) - mat khau o mk_admin.
            if d.get("os_ho") == "linux":
                d["username"] = (form.get("username") or "").strip()
            else:
                d["username"] = "Administrator"
            # Chi ghi de mat khau khi nguoi dung go moi. Ly do: o mat khau
            # KHONG duoc dien san gia tri cu ra trang (xem _noi_dung_buoc) -
            # neu o day cu ghi de bang chuoi rong thi moi lan quay lui roi
            # tiep tuc la mat khau da nhap bi xoa mat ma khong ai biet.
            mk_moi = form.get("password") or ""
            if mk_moi and d.get("os_ho") == "linux":
                d["password"] = mk_moi
            d["ssh"] = bool(form.get("ssh")) if d.get("os_ho") == "linux" else False
            mg = form.get("mui_gio", MUI_GIO[0])
            d["mui_gio"] = mg if mg in MUI_GIO else MUI_GIO[0]

            # ---- Ngon ngu / ban phim / key Windows / tai khoan Administrator
            # (chi co y nghia voi Windows - Linux bo qua het)
            if d.get("os_ho") != "linux":
                nn = form.get("ngon_ngu") or NGON_NGU[0][0]
                d["ngon_ngu"] = nn if any(nn == m for m, _ in NGON_NGU) else NGON_NGU[0][0]
                bp = form.get("ban_phim") or BAN_PHIM[0][0]
                d["ban_phim"] = bp if any(bp == m for m, _ in BAN_PHIM) else BAN_PHIM[0][0]

                # Key Windows: bo het dau cach/gach noi thua roi chuan hoa
                # ve dang 5 nhom 5 ky tu. De TRONG la hop le - luc do dung
                # key KMS cong khai mac dinh (xem ui/unattend.py).
                pk = re.sub(r"[^A-Za-z0-9]", "", form.get("product_key") or "").upper()
                if pk:
                    if len(pk) != 25:
                        return ("Key Windows phải đúng 25 ký tự (5 nhóm 5 ký "
                                "tự). Để trống nếu muốn dùng key mặc định.")
                    pk = "-".join(pk[i:i + 5] for i in range(0, 25, 5))
                d["product_key"] = pk

                d["tu_dang_nhap"] = bool(form.get("tu_dang_nhap"))
                # Administrator LUON mo, bat buoc co mat khau (khong con tuy chon tat)
                d["bat_admin"] = True
                mk_ad_moi = form.get("mk_admin") or ""
                if mk_ad_moi:
                    d["mk_admin"] = mk_ad_moi
                if not d["mk_admin"]:
                    return ("Phải đặt mật khẩu cho tài khoản Administrator. Đây là "
                            "tài khoản duy nhất để đăng nhập vào máy sau khi cài.")

            if not d["ten_may"] and not _dt.la_dong(d):
                return "Chưa điền tên máy."
            if d.get("os_ho") == "linux" and not d["username"]:
                return "Chưa điền tên đăng nhập."
            # Ten may: theo quy tac chung cua ca Windows lan Linux (chu, so,
            # dau gach ngang; khong dau cach) - de tranh loi luc cai
            if (not _dt.la_dong(d) or d["ten_may"]) and not re.fullmatch(r"[A-Za-z0-9-]{1,15}", d["ten_may"]):
                return ("Tên máy chỉ được dùng chữ không dấu, số và dấu gạch "
                        "ngang, tối đa 15 ký tự (quy tắc chung của cả Windows "
                        "lẫn Linux).")

        elif buoc == 4:
            che = form.get("o_dia_che_do", "tu_dong")
            d["o_dia_che_do"] = "chia_tay" if che == "chia_tay" else "tu_dong"
            so = (form.get("o_dia_so") or "0").strip()
            d["o_dia_so"] = so if so.isdigit() else "0"
            chon = form.get("o_dia_chon", "so")
            d["o_dia_chon"] = chon if chon in _unattend().CACH_CHON_O else "so"
            gb = (form.get("o_dia_gb") or "").strip()
            d["o_dia_gb"] = gb if gb.isdigit() and int(gb) > 0 else ""
            ds = (form.get("o_dia_dungsai") or "10").strip()
            d["o_dia_dungsai"] = ds if ds.isdigit() and 1 <= int(ds) <= 40 else "10"
            d["o_dia_model"] = re.sub(r"[^A-Za-z0-9 ._-]", "", form.get("o_dia_model") or "").strip()[:40]
            if d["o_dia_chon"] == "dung_luong" and not d["o_dia_gb"]:
                return "Chọn ổ theo dung lượng thì phải điền dung lượng (GB), ví dụ 256."
            if d["o_dia_chon"] == "model" and not d["o_dia_model"]:
                return "Chọn ổ theo tên/model thì phải điền chuỗi cần tìm, ví dụ Samsung hoặc WD."
            # Tuy chon phan chia tu dong (Windows): o C co dinh GB + o du lieu phan con lai
            if d.get("os_ho") == "windows":
                if form.get("tu_dong_kieu") == "c_gb":
                    cg = (form.get("tu_dong_c_gb") or "").strip()
                    if not (cg.isdigit() and int(cg) >= 40):
                        return "Ổ C có dung lượng cố định thì phải điền số GB từ 40 trở lên (Windows 11 nên từ 64 GB)."
                    d["tu_dong_c_gb"] = cg
                    d["tu_dong_d"] = bool(form.get("tu_dong_d"))
                else:
                    d["tu_dong_c_gb"] = ""
                    d["tu_dong_d"] = False
                d["tu_dong_c_nhan"] = re.sub(r"[^A-Za-z0-9 _-]", "", form.get("tu_dong_c_nhan") or "").strip()[:24] or "Windows"
                d["tu_dong_d_nhan"] = re.sub(r"[^A-Za-z0-9 _-]", "", form.get("tu_dong_d_nhan") or "").strip()[:24] or "DuLieu"
            # Tu 1.5.0 deploy.cmd TU chon theo may (UEFI -> GPT, BIOS -> MBR),
            # xem unattend.sinh_diskpart_txt. Truoc do o chon GPT/MBR nay BI
            # BO QUA (luon chia GPT) - chon MBR cung khong co tac dung.
            d["o_dia_bang"] = "tu_dong"
            if d["o_dia_che_do"] == "chia_tay":
                nhan = form.getlist("pv_nhan")
                cd = form.getlist("pv_cd")
                fs = form.getlist("pv_fs")
                gan = form.getlist("pv_gan")
                pv = []
                for i in range(len(nhan)):
                    ten = (nhan[i] or "").strip()
                    if not ten:
                        continue
                    pv.append({
                        "nhan": ten[:24],
                        "cd": (cd[i] if i < len(cd) else "").strip() or "con_lai",
                        "fs": (fs[i] if i < len(fs) else "").strip() or "ntfs",
                        "gan": (gan[i] if i < len(gan) else "").strip() or "-",
                    })
                if not pv:
                    return "Che do chia tay can it nhat 1 phan vung."
                d["phan_vung"] = pv

        elif buoc == 5:
            # Moi phan mem/ung dung cai o phien dang nhap DAU (xem chuan_hoa_apps).
            d["apps"] = chuan_hoa_apps(form.getlist("app"))
            # Ung dung kieu thu muc (mo hinh MDT) - xem danh_sach_ungdung().
            d["ungdung"] = chuan_hoa_ungdung([{"id": uid} for uid in form.getlist("ungdung")])
            # Bo font chu (xem muc BO FONT) - cai cho MOI tai khoan tren may
            d["fonts"] = chuan_hoa_fonts(form.getlist("font"))

        elif buoc == 6:
            d["scripts"] = form.getlist("script")
            d["lenh_them"] = (form.get("lenh_them") or "").strip()[:4000]
            d["domain"] = (form.get("domain") or "").strip()
            d["domain_ou"] = (form.get("domain_ou") or "").strip()
            d["domain_user"] = (form.get("domain_user") or "").strip()
            # Mat khau domain: chi ghi de khi go moi - giong het cach xu ly
            # mat khau may o buoc 3 (o mat khau khong dien san gia tri cu ra
            # trang, neu ghi de bang chuoi rong thi quay lui 1 lan la mat).
            mk_domain = form.get("domain_pass") or ""
            if mk_domain:
                d["domain_pass"] = mk_domain
            # Kiem tra + chuan hoa thong tin domain (de TRONG ca 4 o = khong vao domain).
            # Windows tu choi gia nhap neu Username co dang CONGTY\user hoac user@congty.local
            # nen cat bo phan thua thay vi de may cai xong roi moi bao loi.
            if d["domain"]:
                if not re.fullmatch(r"[A-Za-z0-9]([A-Za-z0-9.-]{0,251}[A-Za-z0-9])?", d["domain"]):
                    return ("Tên domain không hợp lệ (chỉ gồm chữ, số, dấu chấm và gạch ngang, "
                            "ví dụ: congty.local).")
                u = d["domain_user"]
                if "\\" in u:
                    u = u.split("\\", 1)[1]
                elif "@" in u:
                    u = u.split("@", 1)[0]
                d["domain_user"] = u.strip()
                if not d["domain_user"]:
                    return "Đã điền domain thì phải điền Tài khoản gia nhập (chỉ tên, ví dụ: svc-join)."
                if not d.get("domain_pass"):
                    return "Đã điền domain thì phải điền Mật khẩu của tài khoản gia nhập."
                if d["domain_ou"] and not re.fullmatch(
                        r"(?:(?:OU|CN|DC)=[^,=]+)(?:,\s*(?:OU|CN|DC)=[^,=]+)*", d["domain_ou"], re.I):
                    return ("OU không đúng dạng. Ví dụ: OU=May tram,DC=congty,DC=local "
                            "(để trống nếu không cần).")
            else:
                d["domain_ou"] = d["domain_user"] = ""
            hop_le = {ma for ma, _n, _m, _p, _l in _u_tuychon()}
            d["tuy_chon"] = [t for t in form.getlist("tuy_chon") if t in hop_le]

            from ui import unattend as _u
            hop_le_app = {ma for ma, _ten, _ng in _u.APP_RAC}
            d["go_app"] = [a for a in form.getlist("go_app") if a in hop_le_app]
            # Danh dau da di qua buoc 6 it nhat 1 lan. Tu day tro di khoi
            # chon app phai hien dung lua chon da luu chu khong tich lai
            # theo mac dinh (xem _khoi_go_app).
            d["_da_qua_buoc6"] = True

        return ""

    # --------------------------------------------------------- ve tung buoc
    def _thanh_buoc(buoc):
        h = '<div class="buoc-bar">'
        for so, ten in TEN_BUOC:
            cls = "nay" if so == buoc else ("qua" if so < buoc else "")
            h += (f'<div class="buoc-o {cls}" role="button" tabindex="0" data-den="{so}" '
                  f'title="Bấm để chuyển tới bước này ">'
                  f'<span class="so">{so_hien_thi(so)}</span>{_esc(ten)}</div>')
        h += """</div>
        <script>
        document.querySelectorAll('.buoc-o[data-den]').forEach(function(o){
          function di(){
            if(o.classList.contains('nay')){ return; }
            var f = document.querySelector('form[method="POST"][action^="/deployos/wizard/"]');
            if(!f){ location.href = location.pathname.replace(/\\/\\d+$/, '/' + o.dataset.den); return; }
            var i = document.createElement('input');
            i.type='hidden'; i.name='den'; i.value=o.dataset.den; f.appendChild(i);
            f.submit();   // khong dung requestSubmit: o 'required' chua dien se chan, khong nhay duoc
          }
          o.addEventListener('click', di);
          o.addEventListener('keydown', function(e){ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); di(); }});
        });
        </script>"""
        return h

    def _nut_dieu_huong(buoc, nhan_tiep="Tiếp theo &rarr;"):
        lui = ('<button type="submit" name="huong" value="lui" class="gray">'
               '&larr; Quay lại</button>' if buoc > BUOC_DAU else "")
        return f"""
        <div class="row" style="margin-top:20px;gap:10px;">
          {lui}
          <button type="submit" name="huong" value="tiep">{nhan_tiep}</button>
        </div>"""

    def _ve_buoc(ma, d, buoc, loi=""):
        from flask import get_flashed_messages
        # Thong diep tu cac hanh dong PXE that (Bat/Tat/Trich bootmgr) - xem
        # ui/pxe.py: _ve_lai(). Dung flash() vi cac hanh dong do redirect
        # ve day, khong render truc tiep duoc nhu cac form khac trong wizard.
        flash_html = "".join(_msg(nd, cat == "ok")
                             for cat, nd in get_flashed_messages(with_categories=True))
        than = (_tabs("kichban") + _thanh_buoc(buoc) + _msg(loi, False) +
                flash_html + _noi_dung_buoc(ma, d, buoc))
        tieu_de = ("Tạo kịch bản" if d.get("che_do") == "luu"
                   else "Deployment OS")
        return _trang(than, tieu_de,
                      f"Bước {so_hien_thi(buoc)}/{len(TEN_BUOC)}: {dict(TEN_BUOC)[buoc]}",
                      active="/deployos")

    def _noi_dung_buoc(ma, d, buoc):
        act = f'action="/deployos/wizard/{ma}/{buoc}"'

        # ---------------------------------------------- 1.1.1 kieu boot
        if buoc == 1:
            o = ""
            for gt, ten, mo_ta in KIEU_BOOT:
                ch = " checked" if d["kieu_boot"] == gt else ""
                o += f"""
                <label class="chon">
                  <input type="radio" name="kieu_boot" value="{gt}"{ch}>
                  <span class="t">{_esc(ten)}</span>
                  <div class="d">{_esc(mo_ta)}</div>
                </label>"""
            return f"""
            <form method="POST" {act}>
              <div class="card"><h3>Chọn kiểu boot</h3>{o}</div>
              {_nut_dieu_huong(buoc)}
            </form>"""

        # ------------------------------------------------- 1.1.2 chon OS
        if buoc == 2:
            ds_os = danh_sach_os()
            muc_os = ""
            for o in ds_os:
                ch = " checked" if d.get("os_id") == o["id"] else ""
                nhan_trang_thai = ("" if o["san_sang"] else
                                   ' <span style="color:#e0a030;">(thiếu file)</span>')
                muc_os += f"""
                <label class="chon" style="margin-bottom:8px;">
                  <input type="radio" name="os_id" value="{_esc(o['id'])}"{ch} required>
                  <span class="t">{_esc(o['ten_hien_thi'])}{nhan_trang_thai}</span>
                  <div class="d">{_esc(o['os_ho'])} - {_esc(o['kich_thuoc'])}</div>
                </label>"""
            if not ds_os:
                khoi_os = ("""<div class="msg warn">Chưa có hệ điều hành nào.
                Vào <a href="/deployos/os">Tài nguyên &gt; Hệ điều hành</a>
                để thêm trước.</div>""")
            else:
                # Windows 11 tren may khong du chuan (anh Thoai 14/10/2026, muc 1): deploy.cmd
                # bung anh bang DISM, KHONG chay setup.exe -> khong co buoc kiem tra TPM/CPU/
                # Secure Boot/RAM nao. Ghi ro de ky su khong phai di tim cach "bypass".
                ghi_chu_w11 = ("" if not any("11" in (o.get("ten_hien_thi") or "") for o in ds_os) else
                    '<p style="color:#8b93a1;font-size:13px;margin:0 0 10px;">'
                    '<strong>Windows 11 cài được cả máy không có TPM 2.0, CPU đời cũ, máy BIOS/Legacy</strong>: '
                    'Console System bung ảnh trực tiếp, không qua bước kiểm tra phần cứng của bộ cài. '
                    'Riêng CPU phải có SSE4.2/POPCNT (Intel đời Core i 2008 trở về sau, AMD 2011+) - '
                    'bản 24H2 trở lên không chạy trên CPU cũ hơn. Muốn sau này nâng cấp lên bản Windows 11 '
                    'mới bằng bộ cài, tick "Cho phép nâng cấp Windows 11 trên máy không đủ chuẩn" ở bước 6.</p>')
                khoi_os = f'<div class="card"><h3>Chọn hệ điều hành</h3>{ghi_chu_w11}<div data-pt="25" data-pt-tim="1">{muc_os}</div></div>'

            ds_driver = danh_sach_driver()
            da_chon_driver = set(d.get("driver_ids") or [])
            if ds_driver:
                muc_driver = ""
                for dr in ds_driver:
                    ch = " checked" if dr["id"] in da_chon_driver else ""
                    # Thu gon 1 dong/goi (anh Thoai 20/10/2026): ten + so file cung 1 dong.
                    muc_driver += f"""
                    <label class="chon" style="margin-bottom:6px;padding:9px 14px;">
                      <input type="checkbox" name="driver_ids" value="{_esc(dr['id'])}"{ch}>
                      <span class="t">{_esc(dr['ten_hien_thi'])}</span>
                      <span class="d" style="display:inline;margin-left:8px;">· {dr['so_file']} file</span>
                    </label>"""
                khoi_driver = f"""
                <div class="card">
                  <h3>Driver tiêm kèm (không bắt buộc)
                    <span id="dem-driver" style="font-weight:600;font-size:14px;margin-left:8px;color:#8b93a1;"></span></h3>
                  <p style="color:#8b93a1;font-size:13px;margin:0 0 9px;">
                    Chọn 0 hoặc nhiều gói - Windows Setup sẽ tự quét và cài
                    driver phù hợp trong lúc chạy (giống "Out-of-Box
                    Drivers" của MDT). Mỗi trang hiện tối đa 10 gói.</p>
                  <div id="ds-driver" data-pt="10" data-pt-tim="1">{muc_driver}</div>
                  <script>
                  (function () {{
                    var ds = document.getElementById('ds-driver'), dem = document.getElementById('dem-driver');
                    function cap() {{
                      var n = ds.querySelectorAll('input[type=checkbox]:checked').length, t = ds.querySelectorAll('input[type=checkbox]').length;
                      dem.textContent = 'Đã chọn ' + n + ' / ' + t + ' gói';
                      dem.style.color = n ? '#4CAF50' : '#8b93a1';
                    }}
                    ds.addEventListener('change', cap); cap();
                  }})();
                  </script>
                </div>"""
            else:
                khoi_driver = """
                <div class="msg info" style="font-size:13px;">
                  Chưa có gói driver nào (không bắt buộc) - thêm ở
                  <a href="/deployos/drivers">Tài nguyên &gt; Driver</a> nếu
                  máy cần cài có phần cứng ít gặp (mạng/WiFi đời mới/RAID...).
                </div>"""

            return f"""
            <form method="POST" {act}>
              {khoi_os}
              {khoi_driver}
              {_nut_dieu_huong(buoc)}
            </form>"""

        # -------------------------------------------- 1.1.3 thong tin OS
        if buoc == 3:
            if not d["os_ho"]:
                return ('<div class="msg warn">Chưa chọn hệ điều hành ở bước 1. '
                        f'<a href="/deployos/wizard/{ma}/2">Quay lại bước 1</a>.</div>')
            la_linux = d["os_ho"] == "linux"
            o_ssh = ""
            if la_linux:
                ch = " checked" if d.get("ssh") else ""
                o_ssh = f"""
                <label class="chon" style="margin-top:14px;">
                  <input type="checkbox" name="ssh" value="1"{ch}>
                  <span class="t">Bật SSH ngay sau khi cài</span>
                  <div class="d">Cài sẵn openssh-server và bật dịch vụ - vào
                  được máy từ xa ngay, không phải ra tận nơi bật tay.</div>
                </label>"""

            opt_tz = ""
            for tz in MUI_GIO:
                s = " selected" if d["mui_gio"] == tz else ""
                opt_tz += f'<option value="{tz}"{s}>{tz}</option>'

            # ---- Khoi rieng cho Windows: ngon ngu, ban phim, key, Administrator
            khoi_windows = ""
            if not la_linux:
                opt_nn = ""
                for ma_nn, ten_nn in NGON_NGU:
                    s = " selected" if d.get("ngon_ngu") == ma_nn else ""
                    opt_nn += f'<option value="{ma_nn}"{s}>{_esc(ten_nn)}</option>'
                opt_bp = ""
                for ma_bp, ten_bp in BAN_PHIM:
                    s = " selected" if d.get("ban_phim") == ma_bp else ""
                    opt_bp += f'<option value="{ma_bp}"{s}>{_esc(ten_bp)}</option>'
                ad_ch = " checked" if d.get("bat_admin") else ""
                tdn_ch = " checked" if d.get("tu_dang_nhap") else ""
                # O mat khau Administrator an/hien theo o tich - lam bang
                # thuoc tinh `hidden` + 1 doan JS ngan, khong dung thu vien.
                an_mk = "" if d.get("bat_admin") else " hidden"
                nhac_mk_ad = ("Đã đặt rồi - để trống nếu không đổi"
                              if d.get("mk_admin") else "Mật khẩu cho Administrator")
                khoi_windows = f"""
                <label>Ngôn ngữ hiển thị của Windows</label>
                <select name="ngon_ngu">{opt_nn}</select>
                <p style="color:#8b93a1;font-size:12.5px;margin:7px 0 0;">
                  Chỉ đổi được nếu bản Windows đang cài CÓ SẴN gói ngôn ngữ đó.
                  Ảnh Windows tải về thường chỉ có một ngôn ngữ - chọn thứ
                  không có thì Windows lặng lẽ quay về English chứ không báo lỗi.</p>

                <label>Kiểu bàn phím</label>
                <select name="ban_phim">{opt_bp}</select>
                <p style="color:#8b93a1;font-size:12.5px;margin:7px 0 0;">
                  Khác với ngôn ngữ hiển thị - đây là cách các phím được hiểu,
                  luôn có tác dụng. Tiếng Việt dùng bàn phím US rồi gõ bằng
                  Unikey/EVKey, nên cứ để US là đúng.</p>

                <label>Key Windows (để trống nếu không có)</label>
                <input type="text" name="product_key"
                       value="{_esc(d.get('product_key') or '')}"
                       placeholder="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"
                       autocapitalize="characters" autocomplete="off">
                <p style="color:#8b93a1;font-size:12.5px;margin:7px 0 0;">
                  Để trống thì dùng key KMS công khai chính thức của Microsoft
                  (cài được nhưng máy ở trạng thái CHƯA kích hoạt cho tới khi
                  anh nhập key thật hoặc máy gặp máy chủ KMS của công ty).</p>

                <div id="khoi_mk_admin">
                  <label>Tài khoản đăng nhập: <strong>Administrator</strong> (mặc định, luôn mở)</label>
                  <input type="password" name="mk_admin" value=""{"" if d.get("mk_admin") else " required"}
                         autocomplete="new-password"
                         placeholder="{nhac_mk_ad}">
                  <p style="color:#f59e0b;font-size:12.5px;margin:7px 0 0;">
                    Máy sau khi cài chỉ có tài khoản Administrator, vào thẳng
                    tài khoản này. Bắt buộc đặt mật khẩu. Tài khoản này có toàn
                    quyền và KHÔNG bị khoá sau nhiều lần nhập sai - hãy đặt mật
                    khẩu mạnh.</p>
                </div>

                <label class="chon" style="margin-top:14px;">
                  <input type="checkbox" name="tu_dang_nhap" value="1"{tdn_ch}>
                  <span class="t">Giữ tự động đăng nhập MÃI MÃI</span>
                  <div class="d">Lần đầu sau khi cài xong thì máy <strong>luôn
                  tự đăng nhập</strong> (giống MDT) — để phần mềm cài nốt và
                  hiện được bảng báo cáo. Tích ô này nghĩa là những lần bật máy
                  sau <em>cũng</em> không hỏi mật khẩu: tiện cho máy kiosk, máy
                  trưng bày, nhưng ai chạm vào máy cũng dùng được. Không tích
                  thì từ lần thứ hai trở đi máy hỏi mật khẩu bình thường.</div>
                </label>
"""

            khoi_tk_linux = ""
            if la_linux:
                khoi_tk_linux = f"""
                <label>Tên đăng nhập (username)</label>
                <input type="text" name="username" value="{_esc(d['username'])}"
                       placeholder="ví dụ: admin" autocapitalize="off">
                <label>Mật khẩu</label>
                <input type="password" name="password" value=""
                       placeholder="{'Đã đặt rồi - để trống nếu không đổi' if d['password'] else 'Mật khẩu cho tài khoản trên máy đó'}">
                <p style="color:#8b93a1;font-size:12.5px;margin:7px 0 0;">
                  Đây là mật khẩu cho tài khoản SẼ TẠO trên máy đang cài lại,
                  không phải mật khẩu của Console Pi. Nếu lưu thành kịch bản,
                  file kịch bản được để quyền chỉ root đọc được (600).
                  {'<br>Đã có mật khẩu - để trống ô này thì giữ nguyên cái cũ.' if d['password'] else ''}</p>"""
            # 1.9.4: 5 cach dat ten may (Windows) - xem ui/datten.py. Linux giu o ten co dinh.
            che_tm = _dt.che_do_cua(d)
            ck_tm = {c: (" checked" if che_tm == c else "") for c in _dt.CHE_DO}
            canh_bao_csv = "".join(f"<li>{_esc(x)}</li>" for x in (d.get("_ten_may_csv_canhbao") or []))
            if d.get("ten_may_csv"):
                tt_csv = (f'<div class="d" style="color:#7bd88f;">Đã nạp <strong>{_esc(d.get("ten_may_csv_ten") or "danh sách")}</strong>: '
                          f'{len(d["ten_may_csv"])} máy. Chọn file khác để thay thế. '
                          '<label style="display:inline;"><input type="checkbox" name="ten_may_csv_xoa" value="1"> xóa danh sách</label></div>')
            else:
                tt_csv = '<div class="d" style="color:#f59e0b;">Chưa có danh sách. Bấm tải file mẫu, điền serial và tên máy, rồi chọn file đó.</div>'
            if canh_bao_csv:
                tt_csv += f'<ul class="d" style="color:#f59e0b;margin:4px 0 0 18px;">{canh_bao_csv}</ul>'
            if la_linux:
                khoi_ten_may = f"""
                <label>Tên máy (hostname)</label>
                <input type="text" name="ten_may" value="{_esc(d['ten_may'])}"
                       placeholder="ví dụ: PC-KETOAN-01" autocapitalize="off">"""
            else:
                _nhan_tm = (("co_dinh", "Tên cố định"), ("serial", "Tiền tố + số serial của máy"),
                            ("csv", "Đối chiếu danh sách (CSV): serial → tên máy"),
                            ("ngau_nhien", "Tên máy ngẫu nhiên"), ("hoi", "Hỏi tên máy lúc cài"))
                opt_tm = "".join(f'<option value="{k}"{" selected" if k == che_tm else ""}>{v}</option>' for k, v in _nhan_tm)
                an = lambda k: "" if k == che_tm else ' style="display:none;"'
                khoi_ten_may = f"""
                <label>Tên máy (hostname) - cách đặt tên</label>
                <select name="ten_may_che_do" id="tm-che-do" onchange="doiCachTenMay()">{opt_tm}</select>
                <p style="color:#8b93a1;font-size:12.5px;margin:7px 0 10px;">Cài <strong>nhiều máy bằng một kịch bản</strong> thì mỗi máy phải
                  có tên riêng (trùng tên thì không gia nhập domain được).</p>
                <div id="tm-co_dinh"{an('co_dinh')}>
                  <input type="text" name="ten_may" value="{_esc(d['ten_may'])}" placeholder="ví dụ: PC-KETOAN-01" autocapitalize="off">
                  <p style="color:#8b93a1;font-size:12.5px;margin:7px 0 0;">Một tên cho máy này. Dùng khi chỉ cài một máy.</p>
                </div>
                <div id="tm-serial"{an('serial')}>
                  <label>Tiền tố (tối đa 8 ký tự, bỏ trống = PC)</label>
                  <input type="text" name="ten_may_tiento" value="{_esc(d.get('ten_may_tiento') or '')}" maxlength="8"
                       placeholder="ví dụ: PC" autocapitalize="off" style="max-width:200px;">
                  <p style="color:#8b93a1;font-size:12.5px;margin:7px 0 0;">Máy tự lấy số serial trong BIOS ghép sau tiền tố, ví dụ <strong>PC-5CG1234ABC</strong>.
                    Tên dài quá 15 ký tự thì giữ phần đuôi serial. Máy không có serial hợp lệ (nhiều máy ảo, bo mạch rẻ) dùng 6 số cuối địa chỉ MAC.</p>
                </div>
                <div id="tm-csv"{an('csv')}>
                  <a class="btn small" href="/deployos/kichban/mau-csv">Tải file CSV mẫu</a>
                  <span style="color:#8b93a1;font-size:12.5px;margin-left:8px;">Cột 1: serial, cột 2: tên máy</span>
                  <div style="margin-top:8px;"><input type="file" name="ten_may_csv_file" accept=".csv,.txt"></div>
                  {tt_csv}
                  <p style="color:#8b93a1;font-size:12.5px;margin:7px 0 0;">Máy có serial nằm trong danh sách nhận đúng tên đó. Tên máy được kiểm tra theo quy tắc của Microsoft: tối đa 15 ký tự, chỉ chữ không dấu, số, dấu -, không chỉ toàn số, không bắt đầu/kết thúc bằng dấu -; file có tên sai hoặc trùng thì không được nạp. Máy ngoài danh sách tự dùng tên PC + số serial.</p>
                </div>
                <div id="tm-ngau_nhien"{an('ngau_nhien')}>
                  <label>Tiền tố (tối đa 8 ký tự, bỏ trống = PC)</label>
                  <input type="text" name="ten_may_tiento_ngau" value="{_esc(d.get('ten_may_tiento_ngau') or '')}" maxlength="8"
                       placeholder="ví dụ: PC" autocapitalize="off" style="max-width:200px;">
                  <p style="color:#8b93a1;font-size:12.5px;margin:7px 0 0;">Mỗi máy tự nhận một tên khác nhau, ví dụ <strong>PC-K7Q2M9X</strong>.</p>
                </div>
                <div id="tm-hoi"{an('hoi')}>
                  <p style="color:#8b93a1;font-size:12.5px;margin:0;">Khi máy khởi động vào bộ cài, cửa sổ lệnh hỏi bạn muốn đặt tên gì. Gõ tên rồi bấm
                    <strong>Enter</strong> thì máy mới bắt đầu cài toàn bộ. Dùng khi có người đứng cạnh máy (cần bàn phím cắm vào máy đó).</p>
                </div>
                <script>
                function doiCachTenMay() {{
                  var v = document.getElementById('tm-che-do').value;
                  ['co_dinh','serial','csv','ngau_nhien','hoi'].forEach(function(k) {{
                    var e = document.getElementById('tm-' + k); if (e) e.style.display = (k === v) ? '' : 'none';
                  }});
                }}
                </script>"""
            return f"""
            <form method="POST" enctype="multipart/form-data" {act}>
              <div class="card">
                <h3>Thông tin máy sẽ cài</h3>
                {khoi_ten_may}
                {khoi_tk_linux}
                <!-- O mat khau KHONG dien san gia tri cu: dien san thi mat
                     khau nam thang trong ma nguon trang, ai xem nguon (hoac
                     anh chup man hinh dev tools) deu doc duoc. -->

                <label>Múi giờ</label>
                <select name="mui_gio">{opt_tz}</select>
                {khoi_windows}
                {o_ssh}
              </div>
              {_nut_dieu_huong(buoc)}
            </form>"""

        # ------------------------------------------ 1.1.4 phan chia o dia
        if buoc == 4:
            tu_dong_ch = " checked" if d["o_dia_che_do"] == "tu_dong" else ""
            tay_ch = " checked" if d["o_dia_che_do"] == "chia_tay" else ""
            _oc = _unattend().o_chon(d) if d.get("os_ho") == "windows" else {"chon": "so", "gb": 0, "dungsai": 10, "model": ""}
            _ck = {k: (" checked" if (d.get("o_dia_chon") or "so") == k else "")
                   for k in ("so", "co_windows", "dung_luong", "model", "nho_nhat", "lon_nhat")}
            if not any(_ck.values()):
                _ck["so"] = " checked"
            khoi_chon_o = "" if d.get("os_ho") != "windows" else f"""
              <div class="card">
                <h3>Cài vào ổ nào?</h3>
                <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
                  Máy có nhiều ổ cứng (ví dụ 1 ổ Windows + 1 ổ dữ liệu) thì <strong>số ổ có thể khác nhau giữa các máy</strong>
                  (ổ Windows lúc là Disk 0, lúc là Disk 1). Chọn ổ theo <strong>đặc điểm</strong> thì cùng một kịch bản cài đúng ổ
                  trên mọi máy. Chỉ ổ được chọn bị xóa; các ổ khác không bị đụng tới. Ổ USB / thẻ nhớ không bao giờ được chọn.
                  Nếu không có đúng 1 ổ khớp, máy <strong>dừng lại và không xóa gì</strong>.</p>
                <label class="chon"><input type="radio" name="o_dia_chon" value="so"{_ck['so']}>
                  <span class="t">Theo số ổ (như trước đây)</span>
                  <div class="d">Dùng khi mọi máy giống hệt nhau. Số ổ do thứ tự cắm cáp/khe quyết định (xem bảng "Ổ đĩa đã dò").
                    <div style="margin-top:6px;"><label>Ổ đĩa số</label>
                      <input type="number" name="o_dia_so" value="{_esc(d['o_dia_so'])}" min="0" max="15" style="max-width:130px;"></div></div></label>
                <label class="chon"><input type="radio" name="o_dia_chon" value="co_windows"{_ck['co_windows']}>
                  <span class="t">Ổ đang chứa Windows</span>
                  <div class="d">Cài lại đúng ổ đang có Windows (tìm thấy thư mục Windows). Phải có đúng 1 ổ như vậy.</div></label>
                <label class="chon"><input type="radio" name="o_dia_chon" value="dung_luong"{_ck['dung_luong']}>
                  <span class="t">Theo dung lượng</span>
                  <div class="d">Ổ có dung lượng gần bằng giá trị này (xem số GB ở bảng "Ổ đĩa đã dò"; ổ ghi 256 GB thường hiện ~238 GB).
                    <div class="row" style="margin-top:6px;">
                      <div><label>Dung lượng (GB)</label>
                        <input type="number" name="o_dia_gb" value="{_esc(str(_oc['gb'] or ''))}" min="1" style="max-width:130px;"></div>
                      <div><label>Sai lệch cho phép (%)</label>
                        <input type="number" name="o_dia_dungsai" value="{_esc(str(_oc['dungsai']))}" min="1" max="40" style="max-width:110px;"></div>
                    </div></div></label>
                <label class="chon"><input type="radio" name="o_dia_chon" value="model"{_ck['model']}>
                  <span class="t">Theo tên / model ổ</span>
                  <div class="d">Ổ có tên chứa chuỗi này (không phân biệt hoa thường), ví dụ <code>Samsung</code>, <code>WD</code>, <code>NVMe</code>.
                    <div style="margin-top:6px;"><input type="text" name="o_dia_model" value="{_esc(_oc['model'])}" maxlength="40"
                      placeholder="ví dụ: Samsung SSD" style="max-width:260px;"></div></div></label>
                <label class="chon"><input type="radio" name="o_dia_chon" value="nho_nhat"{_ck['nho_nhat']}>
                  <span class="t">Ổ nhỏ nhất</span>
                  <div class="d">Thường là ổ SSD chứa Windows khi ổ dữ liệu lớn hơn. Hai ổ bằng nhau thì máy dừng, không đoán.</div></label>
                <label class="chon"><input type="radio" name="o_dia_chon" value="lon_nhat"{_ck['lon_nhat']}>
                  <span class="t">Ổ lớn nhất</span>
                  <div class="d">Ổ có dung lượng lớn nhất của máy (không tính USB).</div></label>
                <div class="msg warn" style="margin-top:14px;"><strong>Cảnh báo thật:</strong> ổ được chọn sẽ bị XÓA SẠCH trước khi cài (cả khi chia tự động lẫn chia bằng tay);
                  các ổ khác không bị đụng tới.</div>
              </div>
"""
            pv = d["phan_vung"] or _phan_vung_mac_dinh(d["os_ho"])

            fs_lua = (["ntfs", "fat32", "msr", "ext4", "swap", "xfs", "btrfs"]
                      if d["os_ho"] == "linux" else
                      ["ntfs", "fat32", "msr", "ext4"])
            hang = ""
            for p in pv:
                opt_fs = ""
                for f in fs_lua:
                    s = " selected" if p.get("fs") == f else ""
                    opt_fs += f'<option value="{f}"{s}>{f}</option>'
                hang += f"""
                <div class="pv-hang">
                  <input type="text" name="pv_nhan" value="{_esc(p.get('nhan',''))}" placeholder="Nhãn">
                  <input type="text" name="pv_cd" value="{_esc(p.get('cd',''))}" placeholder="MB hoặc con_lai">
                  <select name="pv_fs">{opt_fs}</select>
                  <input type="text" name="pv_gan" value="{_esc(p.get('gan',''))}" placeholder="C: hoặc /">
                  <button type="button" class="red small" onclick="this.parentNode.remove()">Xóa</button>
                </div>"""

            la_win = d.get("os_ho") == "windows"
            tt = _unattend().tuychon_tu_dong(d) if la_win else {"c_gb": 0, "d_tao": False, "c_nhan": "Windows", "d_nhan": "DuLieu"}
            # Ngoai "Cai vao o nao?" cho Windows, Linux chi co o so o.
            khoi_so_o_linux = "" if la_win else f"""
              <div class="card">
                <h3>Chọn ổ đĩa</h3>
                <label>Ổ đĩa số</label>
                <input type="number" name="o_dia_so" value="{_esc(d['o_dia_so'])}" min="0" max="15" style="max-width:130px;">
                <div class="msg warn" style="margin-top:14px;"><strong>Cảnh báo thật:</strong> chia ổ đĩa là thao tác GHI ĐÈ -
                  toàn bộ dữ liệu trên ổ được chọn sẽ mất. Máy có nhiều ổ thì kiểm tra kỹ số ổ trước khi chạy.</div>
              </div>"""
            mau_json = json.dumps(MAU_PHAN_VUNG_WINDOWS, ensure_ascii=False) if la_win else "[]"
            nut_mau = ""
            if la_win:
                for i, m in enumerate(MAU_PHAN_VUNG_WINDOWS):
                    nut_mau += (f'<button type="button" class="gray small" style="margin:0 6px 6px 0;" title="{_esc(m["mo_ta"])}" '
                                f'onclick="apMau({i})">{_esc(m["ten"])}</button>')
            khoi_mau = "" if not la_win else f"""
                <div style="margin:0 0 12px;">
                  <div style="color:#8b93a1;font-size:13px;margin-bottom:6px;"><strong>Mẫu có sẵn</strong> - bấm để điền sẵn danh sách rồi sửa lại cho vừa ý
                    (ổ phải đủ lớn cho các phân vùng cố định; phân vùng cuối ghi <code>con_lai</code> lấy phần còn lại):</div>
                  {nut_mau}
                  <div id="mau-mota" style="color:#8b93a1;font-size:12.5px;min-height:18px;"></div>
                </div>"""
            khoi_tu_dong_win = "" if not la_win else f"""
                <label class="chon"><input type="radio" name="tu_dong_kieu" value="het"{'' if tt['c_gb'] else ' checked'}>
                  <span class="t">1 ổ C dùng hết ổ (mặc định)</span>
                  <div class="d">Toàn bộ ổ cho Windows. Hợp khi ổ chỉ để chạy hệ điều hành.</div></label>
                <label class="chon"><input type="radio" name="tu_dong_kieu" value="c_gb"{' checked' if tt['c_gb'] else ''}>
                  <span class="t">Ổ C có dung lượng cố định</span>
                  <div class="d">Phần còn lại của ổ có thể để trống hoặc làm ổ dữ liệu riêng (ví dụ ổ D) - sau này cài lại Windows chỉ cần chọn đúng ổ C.
                    <div class="row" style="margin-top:6px;">
                      <div><label>Dung lượng ổ C (GB)</label>
                        <input type="number" name="tu_dong_c_gb" value="{_esc(str(tt['c_gb'] or ''))}" min="40" style="max-width:130px;"
                          placeholder="vd 100"><div style="color:#8b93a1;font-size:12px;">Windows 11 nên từ 64 GB trở lên.</div></div>
                      <div><label>Nhãn ổ C</label>
                        <input type="text" name="tu_dong_c_nhan" value="{_esc(tt['c_nhan'])}" maxlength="24" style="max-width:180px;"></div>
                    </div>
                    <label style="display:block;margin-top:8px;"><input type="checkbox" name="tu_dong_d" value="1"{' checked' if tt['d_tao'] else ''}>
                      Tạo ổ dữ liệu từ phần còn lại của ổ</label>
                    <div style="margin-top:4px;"><label>Nhãn ổ dữ liệu</label>
                      <input type="text" name="tu_dong_d_nhan" value="{_esc(tt['d_nhan'])}" maxlength="24" style="max-width:180px;"></div>
                    <div style="color:#8b93a1;font-size:12px;margin-top:4px;">Chữ cái ổ (D:, E:...) do Windows tự gán lúc khởi động lần đầu.</div>
                  </div></label>"""
            khoi_tu_dong = f"""
              <div class="card" id="khoi-tu-dong"{'' if d['o_dia_che_do'] == 'tu_dong' else ' style="display:none;"'}>
                <h3>Tuỳ chọn phân chia tự động</h3>
                <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">Ổ được chọn ở trên bị xóa sạch rồi chia theo bộ chuẩn của máy:
                  <strong>UEFI &rarr; GPT</strong> (phân vùng EFI 260 MB + MSR 16 MB + ổ C), <strong>BIOS/Legacy &rarr; MBR</strong> (phân vùng hệ thống + ổ C).
                  Máy nhận ra UEFI hay BIOS lúc cài, không cần chọn.</p>
                {"" if la_win else '<p style="margin:0;">Với Linux, bộ phân vùng chuẩn là EFI + swap + root (ext4).</p>'}
                {khoi_tu_dong_win}
              </div>"""
            return f"""
            <form method="POST" {act}>
              <div class="card">
                <h3>Cách chia ổ đĩa</h3>
                <label class="chon">
                  <input type="radio" name="o_dia_che_do" value="tu_dong"{tu_dong_ch} onchange="doiCheDoChiaO()">
                  <span class="t">Phân chia tự động</span>
                  <div class="d">Xóa sạch ổ được chọn rồi chia theo bộ phân vùng chuẩn của hệ điều hành
                  (có thể đặt ổ C cố định và tạo ổ dữ liệu). Bấm vào đây để xem các tuỳ chọn.</div>
                </label>
                <label class="chon">
                  <input type="radio" name="o_dia_che_do" value="chia_tay"{tay_ch} onchange="doiCheDoChiaO()">
                  <span class="t">Chia bằng tay</span>
                  <div class="d">Tự khai báo từng phân vùng (nhãn, dung lượng, định dạng), có sẵn 5 mẫu. Dùng khi
                  muốn chia thêm ổ D: để chứa dữ liệu riêng hoặc cần bố cục đặc biệt. Bấm vào đây để xem danh sách phân vùng.</div>
                </label>
              </div>

              {_khoi_o_dia_da_do()}
              {khoi_chon_o}
              {khoi_so_o_linux}
              {khoi_tu_dong}

              <div class="card" id="khoi-chia-tay"{'' if d['o_dia_che_do'] == 'chia_tay' else ' style="display:none;"'}>
                <h3>Danh sách phân vùng</h3>
                {khoi_mau}
                <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
                  Dung lượng điền bằng MB, hoặc gõ <code>con_lai</code> để lấy
                  hết chỗ trống còn lại. Cột cuối là ổ/điểm gắn
                  ({'vd <code>/</code>, <code>/home</code>' if d['os_ho'] == 'linux' else 'ghi chú ý định, vd <code>C:</code>, <code>D:</code> - Windows tự gán chữ cái lúc khởi động lần đầu'}).
                  Với Windows trên GPT bắt buộc phải có phân vùng <code>EFI</code>
                  và <code>MSR</code> - đã điền sẵn theo đúng chuẩn.</p>
                <div id="pvbox">{hang}</div>
                <button type="button" class="gray small" onclick="themPV()">+ Thêm phân vùng</button>
              </div>

              {_nut_dieu_huong(buoc)}
            </form>
            <script>
            var MAU_PV = {mau_json};
            function themPV() {{
              var box = document.getElementById("pvbox");
              var mau = box.querySelector(".pv-hang");
              if (!mau) return;
              var moi = mau.cloneNode(true);
              moi.querySelectorAll("input").forEach(function (i) {{ i.value = ""; }});
              box.appendChild(moi);
            }}
            function doiCheDoChiaO() {{
              var tay = document.querySelector('input[name=o_dia_che_do][value=chia_tay]');
              var td = document.getElementById("khoi-tu-dong"), ct = document.getElementById("khoi-chia-tay");
              var laTay = tay && tay.checked;
              if (td) td.style.display = laTay ? "none" : "";
              if (ct) ct.style.display = laTay ? "" : "none";
            }}
            function apMau(i) {{
              var m = MAU_PV[i], box = document.getElementById("pvbox");
              var mau = box.querySelector(".pv-hang");
              if (!m || !mau) return;
              var goc = mau.cloneNode(true);
              box.innerHTML = "";
              m.pv.forEach(function (p) {{
                var h = goc.cloneNode(true), ins = h.querySelectorAll("input"), sel = h.querySelector("select");
                ins[0].value = p.nhan; ins[1].value = p.cd; ins[2].value = p.gan; sel.value = p.fs;
                box.appendChild(h);
              }});
              var mt = document.getElementById("mau-mota"); if (mt) mt.textContent = m.mo_ta;
            }}
            doiCheDoChiaO();
            // Go/tich vao o phu cua 1 lua chon thi tu chon luon lua chon do (khoi phai bam radio roi moi go)
            document.querySelectorAll('.chon input[type=text], .chon input[type=number], .chon .d input[type=checkbox]').forEach(function (i) {{
              ['focus', 'input', 'change'].forEach(function (ev) {{
                i.addEventListener(ev, function () {{
                  var r = i.closest('.chon').querySelector('input[type=radio]');
                  if (r && !r.checked) r.checked = true;
                }});
              }});
            }});
            </script>"""

        # ------------------------------------------------- 1.1.5 phan mem
        if buoc == 5:
            ds = danh_sach_app()
            if not ds:
                than = """
                <div class="msg warn">Chưa có phần mềm nào được tải lên.
                Vào tab <a href="/deployos/console/apps">Phần mềm</a> để
                tải file .msi/.exe lên trước, rồi quay lại bước này.
                Bỏ qua bước này cũng được - lúc đó máy chỉ cài OS, không cài
                thêm phần mềm.</div>"""
            else:
                da_chon = {a["ten"] for a in chuan_hoa_apps(d.get("apps"))}
                o = ""
                for a in ds:
                    ch = " checked" if a["ten"] in da_chon else ""
                    tsm = a["tham_so"] or tham_so_mac_dinh_app(a["ten"])
                    ts = (f'<code>{_esc(tsm)}</code>' if tsm
                          else '<span style="color:#f59e0b;">chưa điền tham số '
                               'cài im lặng - bộ cài có thể hiện giao diện và '
                               'làm treo quá trình cài</span>')
                    o += f"""
                    <label class="chon">
                      <input type="checkbox" name="app" value="{_esc(a['ten'])}"{ch}>
                      <span class="t">{_esc(a['ten'])}</span>
                      <div class="d">{co_kich_thuoc(a['cd'])} &middot; tham so: {ts}</div>
                    </label>"""
                than = f"""
                <div class="card"><h3>Chọn phần mềm sẽ cài</h3><div data-pt="25" data-pt-tim="1">{o}</div></div>
                <div class="card">
                  <h3>Khi nào phần mềm được cài</h3>
                  <p style="margin:0;">Mọi phần mềm và ứng dụng được cài <strong>khi
                    đăng nhập Windows lần đầu</strong>. Lúc đó trên máy hiện <strong>bảng
                    tiến trình</strong> (đang cài gì, còn bao nhiêu), đồng thời theo dõi
                    được từ xa ở tab <a href="/deployos/tiendo">Tiến trình</a>.</p>
                  <p style="color:#8b93a1;font-size:12.5px;margin:10px 0 0;">
                    Tham số cài im lặng đặt ở tab
                    <a href="/deployos/console/apps">Phần mềm</a> (theo từng
                    file, dùng chung cho mọi kịch bản).</p>
                </div>"""

            ds_ud = danh_sach_ungdung()
            khoi_ungdung = ""
            if ds_ud:
                da_chon_ud = {u["id"] for u in chuan_hoa_ungdung(d.get("ungdung"))}
                o_ud = ""
                for u in ds_ud:
                    ch = " checked" if u["id"] in da_chon_ud else ""
                    lenh = (f'<code>{_esc(u["lenh_cai"])}</code>' if u["lenh_cai"]
                            else '<span style="color:#f59e0b;">chưa đặt lệnh cài - '
                                 'vào Ứng dụng để đặt trước khi dùng</span>')
                    o_ud += f"""
                    <label class="chon">
                      <input type="checkbox" name="ungdung" value="{_esc(u['id'])}"{ch}>
                      <span class="t">{_esc(u['ten_hien_thi'])}</span>
                      <div class="d">{u['so_file']} file &middot; {_esc(u['kich_thuoc'])}
                        &middot; lệnh: {lenh}</div>
                    </label>"""
                khoi_ungdung = f"""
                <div class="card">
                  <h3>Ứng dụng nhiều file (Office 365, bộ cài phức tạp)</h3>
                  <div data-pt="25" data-pt-tim="1">{o_ud}</div>
                </div>"""
            else:
                khoi_ungdung = """
                <div class="msg info" style="font-size:13px;">
                  Chưa có ứng dụng kiểu thư mục nào. Vào tab
                  <a href="/deployos/ungdung">Ứng dụng (nhiều file)</a> nếu
                  cần cài Office 365 hoặc bộ cài nhiều file khác.
                </div>"""

            ds_font = danh_sach_bo_font()
            da_chon_font = set(chuan_hoa_fonts(d.get("fonts")))
            o_font = ""
            for b in ds_font:
                ch = " checked" if b["id"] in da_chon_font else ""
                o_font += f"""
                    <label class="chon">
                      <input type="checkbox" name="font" value="{_esc(b['id'])}"{ch}>
                      <span class="t">{_esc(b['ten_hien_thi'])}</span>
                      <div class="d">{b['so_font']} font &middot; {_esc(b['kich_thuoc'])}</div>
                    </label>"""
            # Bo font da chon nhung da bi xoa: bao do, khong am tham bo qua
            for mat in sorted(da_chon_font - {b["id"] for b in ds_font}):
                o_font += f"""
                    <label class="chon">
                      <input type="checkbox" name="font" value="{_esc(mat)}" checked>
                      <span class="t">{_esc(mat)}</span>
                      <div class="d" style="color:#ef4444;">Bộ font này không còn - bỏ tick
                        (hoặc tạo lại cùng tên ở tab Font chữ)</div>
                    </label>"""
            if o_font:
                khoi_font = f"""
                <div class="card">
                  <h3>Font chữ</h3>
                  <p style="color:#8b93a1;font-size:13px;margin:0 0 9px;">
                    Cài sẵn các font này cho <strong>mọi tài khoản</strong> trên máy.
                    Thêm font ở tab <a href="/deployos/font">Font chữ</a>.</p>
                  <div data-pt="25" data-pt-tim="1">{o_font}</div>
                </div>"""
            else:
                khoi_font = """
                <div class="msg info" style="font-size:13px;">
                  Chưa có bộ font nào. Nếu máy cần font riêng của công ty, tạo bộ font ở tab
                  <a href="/deployos/font">Font chữ</a> rồi quay lại tick chọn ở đây.
                </div>"""

            return f"""
            <form method="POST" {act}>
              {than}
              {khoi_ungdung}
              {khoi_font}
              {_nut_dieu_huong(buoc)}
            </form>"""

        # -------------------------------------------- 1.1.6 chinh sua cai dat
        if buoc == 6:
            ds = _liet_ke(SCRIPTS_DIR, EXT_SCRIPT)
            if ds:
                o = ""
                for s in ds:
                    ch = " checked" if s["ten"] in d["scripts"] else ""
                    o += f"""
                    <label class="chon">
                      <input type="checkbox" name="script" value="{_esc(s['ten'])}"{ch}>
                      <span class="t">{_esc(s['ten'])}</span>
                      <div class="d">{co_kich_thuoc(s['cd'])} &middot; tai len {_esc(s['ngay'])}</div>
                    </label>"""
                khoi_script = f'<div class="card"><h3>Script chạy sau khi cài xong</h3><div data-pt="25" data-pt-tim="1">{o}</div></div>'
            else:
                khoi_script = """
                <div class="msg warn">Chưa có script nào. Tải lên ở tab
                <a href="/deployos/console/scripts">Script</a>
                (.bat / .ps1 / .cmd).</div>"""

            # --- Gia nhap domain + tuy chon Windows (chi cho Windows) ---
            khoi_domain = ""
            khoi_tuychon = ""
            if d.get("os_ho") == "windows":
                da_chon = set(d.get("tuy_chon") or [])
                o_may, o_nd = "", ""
                for ma_tc, nhan, mo_ta, pha, _lenh in _u_tuychon():
                    ch = " checked" if ma_tc in da_chon else ""
                    o = f"""
                    <label class="chon">
                      <input type="checkbox" name="tuy_chon" value="{_esc(ma_tc)}"{ch}>
                      <span class="t">{_esc(nhan)}</span>
                      <div class="d">{_esc(mo_ta)}</div>
                    </label>"""
                    # Tu 03/10/2026 MOI muc deu tac dung cap may / moi tai
                    # khoan - chia 2 nhom theo LOAI cho de tim, khong con
                    # muc nao chi cho rieng 1 nguoi dung.
                    if pha == "ho_so":
                        o_nd += o
                    else:
                        o_may += o
                # Gap lai thanh 2 khoi bam-de-mo. LY DO THAT (anh Thoai:
                # "nhieu cai no dai qua nguoi chon keo xuong duoi kha la
                # met"): 44 tuy chon + 30 ung dung go = hon 70 o tich xep
                # thang mot cot, phai keo man hinh rat lau moi qua duoc
                # buoc nay - ma phan lon lan cai deu khong dung toi chung.
                # Dem san so da chon ngay tren tieu de de khong phai mo ra
                # mới biết minh da chon gi.
                so_may = sum(1 for m, *_x in _u_tuychon()
                             if m in da_chon and _x[2] != "ho_so")
                so_nd = len(da_chon) - so_may
                khoi_tuychon = f"""
              <div class="card">
                <h3>Tùy chọn Windows sau khi cài</h3>
                <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
                  Các mục này Windows làm sẵn bằng lệnh hệ thống - không cần
                  viết script. Thứ gì đặc thù hơn thì dùng ô "Lệnh thêm" bên
                  dưới hoặc tải script riêng lên.</p>

                <details class="gap"{' open' if so_may else ''}>
                  <summary>Hệ thống &mdash; áp dụng cho cả máy
                    <span class="dem">{so_may} đã chọn</span></summary>
                  <div class="gap-trong" data-pt="25">{o_may}</div>
                </details>

                <details class="gap"{' open' if so_nd else ''}>
                  <summary>Giao diện &mdash; áp dụng cho MỌI tài khoản (cả tài khoản tạo sau)
                    <span class="dem">{so_nd} đã chọn</span></summary>
                  <div class="gap-trong" data-pt="25">{o_nd}</div>
                </details>
              </div>
              {_khoi_go_app(d, _esc)}"""

                khoi_domain = f"""
              <div class="card">
                <h3>Gia nhập domain (tùy chọn)</h3>
                <p style="color:#8b93a1;font-size:13px;margin:0 0 9px;">
                  Để trống nếu không gia nhập domain. Tài khoản điền ở đây
                  phải có quyền THÊM MÁY vào domain (không nhất thiết phải
                  là Domain Admin). Windows tự làm việc này lúc cài - giống
                  hệt cách MDT làm.</p>
                <p style="color:#fbbf24;font-size:13px;margin:0 0 9px;">
                  <b>Lưu ý DNS:</b> máy đang cài phải tìm được domain qua DNS.
                  Hãy dùng PXE chế độ <b>"Mạng đã có DHCP sẵn"</b> (DNS lấy từ
                  mạng công ty, trỏ về máy chủ domain). Nếu Console System tự
                  cấp IP thì máy sẽ <b>không tìm thấy domain</b> và gia nhập
                  thất bại. Tài khoản gia nhập chỉ điền <b>tên</b> (svc-join),
                  không điền CONGTY\\svc-join; tên máy tối đa 15 ký tự.</p>
                <label>Tên domain</label>
                <input type="text" name="domain" value="{_esc(d.get('domain',''))}"
                       placeholder="ví dụ: congty.local" autocapitalize="off">
                <label style="margin-top:10px;">OU chứa máy (tùy chọn)</label>
                <input type="text" name="domain_ou" value="{_esc(d.get('domain_ou',''))}"
                       placeholder="ví dụ: OU=May tram,DC=congty,DC=local"
                       autocapitalize="off">
                <label style="margin-top:10px;">Tài khoản gia nhập</label>
                <input type="text" name="domain_user"
                       value="{_esc(d.get('domain_user',''))}"
                       placeholder="ví dụ: svc-join" autocapitalize="off">
                <label style="margin-top:10px;">Mật khẩu tài khoản gia nhập</label>
                <input type="password" name="domain_pass" autocomplete="new-password"
                       placeholder="{'(đã có - để trống nếu không đổi)' if d.get('domain_pass') else ''}">
              </div>"""

            return f"""
            <form method="POST" {act}>
              {khoi_tuychon}
              {khoi_domain}
              {khoi_script}
              <div class="card">
                <h3>Lệnh thêm (tùy chọn)</h3>
                <p style="color:#8b93a1;font-size:13px;margin:0 0 9px;">
                  Mỗi dòng 1 lệnh, chạy khi người dùng đăng nhập lần đầu
                  (sau khi cài xong). Dòng bắt đầu bằng # được bỏ qua.</p>
                <textarea name="lenh_them" style="max-width:none;"
                  placeholder="ví dụ: powercfg /h off">{_esc(d['lenh_them'])}</textarea>
              </div>
              {_nut_dieu_huong(buoc)}
            </form>"""

        # -------------------------------------------------- 1.1.7 tong ket
        if buoc == 7:
            return _ve_tongket(ma, d)

        return ""

    # ------------------------------------------------------- buoc 7: tong ket
    def _ve_tongket(ma, d):
        os_ten = _ten_os(d)

        if d["o_dia_che_do"] == "tu_dong":
            o_dia = (f"Tự động trên {_esc(_unattend().mo_ta_chon_o(d))} (GPT/MBR tự nhận theo máy) - "
                     f"{_esc(_unattend().mo_ta_tu_dong(d)) if d.get('os_ho') == 'windows' else 'bộ phân vùng chuẩn'}")
        else:
            pv = d["phan_vung"] or _phan_vung_mac_dinh(d["os_ho"])
            dong = "".join(
                f"<div>&bull; {_esc(p['nhan'])} &mdash; "
                f"{'hết chỗ còn lại' if p['cd'] == 'con_lai' else _esc(p['cd']) + ' MB'} "
                f"&mdash; {_esc(p['fs'])} &mdash; {_esc(p['gan'])}</div>"
                for p in pv)
            o_dia = (f"Chia bằng tay trên {_esc(_unattend().mo_ta_chon_o(d))} "
                     f"(GPT/MBR tự nhận theo máy)<div style='margin-top:6px;'>{dong}</div>")

        ds_app = chuan_hoa_apps(d.get("apps"))
        apps = ("<br>".join("&bull; " + _esc(a["ten"]) for a in ds_app)
            if ds_app else
            "<span style='color:#8b93a1;'>Không cài thêm phần mềm</span>")
        ds_ud = chuan_hoa_ungdung(d.get("ungdung"))
        ung_dung_html = ("<br>".join(
            "&bull; " + _esc(lay_ungdung(u["id"])["ten_hien_thi"]
                             if lay_ungdung(u["id"]) else u["id"])
            for u in ds_ud)
            if ds_ud else
            "<span style='color:#8b93a1;'>Không có</span>")
        font_html = ("<br>".join(
            "&bull; " + (_esc(lay_bo_font(b)["ten_hien_thi"]) + f" ({lay_bo_font(b)['so_font']} font)"
                         if lay_bo_font(b) else
                         f"<span style='color:#ef4444;'>{_esc(b)} - bộ font không còn</span>")
            for b in chuan_hoa_fonts(d.get("fonts")))
            if chuan_hoa_fonts(d.get("fonts")) else
            "<span style='color:#8b93a1;'>Không có</span>")
        scripts = ("<br>".join("&bull; " + _esc(s) for s in d["scripts"])
                   if d["scripts"] else "<span style='color:#8b93a1;'>Không có</span>")
        lenh = (f"<pre style='margin:6px 0 0;'>{_esc(d['lenh_them'])}</pre>"
                if d["lenh_them"] else "<span style='color:#8b93a1;'>Không có</span>")

        # LOI THAT DA GAP (anh Thoai: "xac nhan dung kich ban nay thi ngay
        # lap tuc no nhay sang phan tong ket lan nua la sao ta"): bam "Dung"
        # o 1 kich ban DA LUU se nap kich ban do vao trinh tu roi nhay thang
        # toi buoc 7 - nhung buoc 7 lai hien y HET nhu "Tong ket" cua trinh
        # tu tao moi (co ca form "Luu thanh kich ban" va nut "Sua lai tu
        # buoc 1"), nen nhin khong ra la dang CHAY 1 kich ban co san. Truong
        # d["tu_kichban"] da duoc dat san tu truoc nhung KHONG he duoc dung
        # o dau ca. Sua: khi den tu 1 kich ban da luu thi noi ro dang chay
        # kich ban nao, va bo form luu (luu lai se tao ban trung).
        tu_kb = d.get("tu_kichban") or ""
        tieu_de_bang = (f"Kịch bản: {_esc(tu_kb)}" if tu_kb
                        else "Tổng kết lựa chọn")
        ghi_chu_kb = (
            '<p style="color:#8b93a1;font-size:12.5px;margin:-4px 0 12px;">'
            'Đây là kịch bản đã lưu - sửa xong nhớ bấm <strong>"Lưu đè kịch '
            'bản"</strong> bên dưới. Kịch bản Windows tự có trong menu PXE '
            '(máy khách tự chọn) &mdash; PXE đang bật thì menu cập nhật ngay '
            'khi lưu.</p>'
            if tu_kb else "")

        bang = f"""
        <div class="card">
          <h3>{tieu_de_bang}</h3>
          {ghi_chu_kb}
          <table class="tt-bang">
            <tr><td>Hệ điều hành</td><td>{_esc(os_ten)}</td></tr>
            <tr><td>Driver kèm theo</td><td>{
                (', '.join(_esc(x) for x in d.get('driver_ids') or [])
                 or "<span style='color:#8b93a1;'>Không có</span>")}</td></tr>
            <tr><td>Tên máy</td><td>{_esc(_dt.mo_ta(d))}</td></tr>
            <tr><td>Tài khoản</td><td>{_esc(d['username'] if d['os_ho'] == 'linux' else 'Administrator')}</td></tr>
            <tr><td>Mật khẩu</td><td>{'&bull;' * 8 + ' <span style="color:#8b93a1;">(đã đặt)</span>' if (d['password'] if d['os_ho'] == 'linux' else d.get('mk_admin')) else '<span style="color:#f59e0b;">Chưa đặt</span>'}</td></tr>
            <tr><td>SSH</td><td>{'Bật' if d.get('ssh') else ('Tắt' if d['os_ho'] == 'linux' else '<span style="color:#8b93a1;">Không áp dụng cho Windows</span>')}</td></tr>
            <tr><td>Múi giờ</td><td>{_esc(d['mui_gio'])}</td></tr>
            {_dong_tongket_windows(d, _esc)}
            <tr><td>Gia nhập domain</td><td>{
                (_esc(d.get('domain')) +
                 (f" &mdash; OU: {_esc(d.get('domain_ou'))}" if d.get('domain_ou') else "") +
                 f" &mdash; tài khoản: {_esc(d.get('domain_user') or '(chưa điền)')}")
                if d.get('domain')
                else "<span style='color:#8b93a1;'>Không gia nhập</span>"}</td></tr>
            <tr><td>Tùy chọn Windows</td><td>{
                ("<br>".join("&bull; " + _esc(nhan)
                             for ma_tc, nhan, _m, _p, _l in _u_tuychon()
                             if ma_tc in (d.get('tuy_chon') or []))
                 or "<span style='color:#8b93a1;'>Không bật tùy chọn nào</span>")}</td></tr>
            <tr><td>Ổ đĩa</td><td>{o_dia}</td></tr>
            <tr><td>Phần mềm<br><small style="color:#8b93a1;">cài khi đăng nhập lần đầu</small></td><td>{apps}</td></tr>
            <tr><td>Ứng dụng (nhiều file)</td><td>{ung_dung_html}</td></tr>
            <tr><td>Font chữ</td><td>{font_html}</td></tr>
            <tr><td>Script sau cài</td><td>{scripts}</td></tr>
            <tr><td>Lệnh thêm</td><td>{lenh}</td></tr>
          </table>
        </div>"""

        ve_ds_kichban = ('<a class="btn gray" href="/deployos/kichban">'
                         '&larr; Về danh sách kịch bản</a>' if tu_kb else "")
        sua_lai = f"""
        <div class="row" style="margin-top:4px;">
          {ve_ds_kichban}
          <a class="btn gray" href="/deployos/wizard/{ma}/{BUOC_DAU}">&larr; Sửa lại từ bước 1</a>
          <a class="btn gray" href="/deployos/wizard/{ma}/6">&larr; Quay lại bước 5</a>
        </div>"""

        loi_bb = loi_bat_buoc(d)
        if loi_bb:
            dong_loi = "".join(
                f'<li>{_esc(nd)} &mdash; <a href="/deployos/wizard/{ma}/{b}">sửa ở bước '
                f'{so_hien_thi(b)} ({_esc(dict(TEN_BUOC)[b])})</a></li>' for b, nd in loi_bb)
            return f"""
            {bang}
            <div class="msg err"><strong>Chưa lưu được kịch bản</strong> - còn chỗ thiếu/sai:
              <ul style="margin:6px 0 0 18px;padding:0;">{dong_loi}</ul></div>
            {sua_lai}"""

        # --- che do LUU: dat ten kich ban ---
        if d.get("che_do") == "luu":
            thieu = _thieu_gi(d)
            canh = (f'<div class="msg warn">Vẫn lưu được, nhưng còn thiếu: '
                    f'{_esc(", ".join(thieu))}.</div>' if thieu else "")
            return f"""
            {bang}
            {canh}
            <form method="POST" action="/deployos/kichban/luu/{ma}">
              <div class="card">
                <h3>Đặt tên kịch bản</h3>
                <label>Tên kịch bản</label>
                <input type="text" name="ten" required
                       placeholder="ví dụ: Win11 văn phòng + Chrome" autocapitalize="off">
                <p style="color:#8b93a1;font-size:12.5px;margin:8px 0 0;">
                  Kịch bản sẽ hiện ở tab <strong>Kịch bản</strong> để chọn
                  nhanh lần sau.</p>
                <div class="row" style="margin-top:16px;">
                  <button type="submit" data-busy="Đang lưu... (PXE đang bật thì cập nhật menu luôn)">Lưu kịch bản</button>
                </div>
              </div>
            </form>
            {sua_lai}"""

        # --- che do CHAY: kiem tra san sang that ---
        kt = kiem_tra_san_sang(d)
        hang = ""
        for dat, nhan, chi_tiet in kt:
            bieu = ('<span style="color:#4CAF50;">&#10004;</span>' if dat
                    else '<span style="color:#f59e0b;">&#33;</span>')
            hang += (f"<tr><td style='width:34px;'>{bieu}</td>"
                     f"<td><strong>{_esc(nhan)}</strong><br>"
                     f"<small style='color:#8b93a1;'>{_esc(chi_tiet)}</small></td></tr>")
        du_dieu_kien = all(dat for dat, _, _ in kt)

        ket_luan = ("""
            <div class="msg ok">Tất cả điều kiện cơ bản đã đạt.</div>"""
            if du_dieu_kien else """
            <div class="msg warn"><strong>Chưa thể boot thật.</strong> Những
            mục còn thiếu ở trên phải làm xong trước. Lựa chọn của anh không
            mất: lưu lại thành kịch bản để dùng ngay khi đã đủ điều kiện.</div>""")

        # LOI THAT DA GAP (anh Thoai: "em đem bật tắt pxe ra ngoài trang
        # deployment os đi, để trong kịch bản đâu có ý nghĩa"): nut bat/tat
        # PXE TUNG nam o day (trong tung kich ban) - nhung PXE la TRANG THAI
        # HA TANG DUNG CHUNG (chi co 1 cong eth0, 1 dich vu dnsmasq-pxe cho
        # CA HE THONG), khong phai thuoc tinh rieng cua 1 kich ban. Dat no o
        # day khien nguoi dung phai mo dung 1 kich ban roi vao toi buoc 7
        # moi bat/tat duoc, dung sai cho. Da chuyen han sang trang danh sach
        # kich ban (xem _khoi_pxe_toan_cuc(), goi tu deployos_boot()) - loi
        # nhac da gop chung vao ghi_chu_kb o dau ham nay, khong lap lai o day.

        # Dang chay 1 kich ban DA LUU thi khong hien form luu nua - luu lai
        # chi tao ra 1 ban trung ten khac, gay roi danh sach kich ban.
        # LOI THAT DA GAP (anh Thoai: "sua kich ban them phan mem va them
        # option thi bam save lai lan dau thi co nhung qua trang khac quay
        # lai thi ko co"): o vong sua truoc, khi mo 1 kich ban DA LUU thi
        # form luu bi AN HAN di (voi ly do "luu lai se tao ban trung ten").
        # Hau qua nghiem trong hon nhieu: KHONG CON CACH NAO luu thay doi
        # vao chinh kich ban do - anh sua xong, lua chon chi nam trong bo
        # nho cua trinh tu, roi trang la mat sach (kiem chung that: file
        # Install_windows_10_-_DHCP.json van giu nguyen "apps": [] va moc
        # thoi gian cu, trong khi phan mem da duoc tai len tu lau).
        # Sua dung: van cho luu DE LEN chinh kich ban dang mo (nut chinh),
        # va van cho luu ra ten MOI (nut phu) - khong bo mat duong nao.
        if tu_kb:
            form_luu = f"""
        <div class="card">
          <h3>Lưu thay đổi</h3>
          <form method="POST" action="/deployos/kichban/luu/{ma}">
            <input type="hidden" name="ten" value="{_esc(tu_kb)}">
            <button type="submit" data-busy="Đang lưu... (PXE đang bật thì cập nhật menu luôn)">
              Lưu đè kịch bản "{_esc(tu_kb)}"</button>
          </form>
          <div style="border-top:1px solid #2a2f3a;margin:16px 0 12px;"></div>
          <form method="POST" action="/deployos/kichban/luu/{ma}">
            <label>Hoặc lưu thành kịch bản mới (đặt tên khác)</label>
            <input type="text" name="ten" required
                   placeholder="ví dụ: Win10 văn phòng + Chrome" autocapitalize="off">
            <div class="row" style="margin-top:12px;">
              <button type="submit" class="gray" data-busy="Đang lưu... (PXE đang bật thì cập nhật menu luôn)">
                Lưu thành kịch bản mới</button>
            </div>
          </form>
        </div>"""
        else:
            form_luu = f"""
        <form method="POST" action="/deployos/kichban/luu/{ma}">
          <div class="card">
            <h3>Lưu lựa chọn này thành kịch bản</h3>
            <label>Tên kịch bản</label>
            <input type="text" name="ten" required
                   placeholder="ví dụ: Win11 văn phòng + Chrome" autocapitalize="off">
            <div class="row" style="margin-top:14px;">
              <button type="submit" data-busy="Đang lưu... (PXE đang bật thì cập nhật menu luôn)">Lưu thành kịch bản</button>
            </div>
          </div>
        </form>"""

        return f"""
        {_khoi_dang_phuc_vu()}
        {bang}
        <div class="card">
          <h3>Kiểm tra sẵn sàng (đọc trạng thái thật trên máy)</h3>
          <table>{hang}</table>
        </div>
        {ket_luan}
        {form_luu}
        {sua_lai}"""

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
                nut = f"""
                <button type="submit"
                  data-busy="Đang bật PXE... chỉ vài giây, KHÔNG bấm lại">
                  Bật PXE</button>"""
            else:
                nut = ('<div class="msg err">Chưa đủ điều kiện để bật &mdash; '
                       'xem tab <a href="/deployos/caidat/hatang">Kiểm tra '
                       'hạ tầng</a>.</div>')
            trang_thai = f"""
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
        return _trang(body, "Cài đặt Deployment OS",
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

    _thieu_gi = thieu_gi

    @app.route("/deployos/kichban/luu/<ma>", methods=["POST"])
    def deployos_luu_kichban(ma):
        d = _wizard_lay(ma)
        if d is None:
            return _het_han()
        if loi_bat_buoc(d):
            return redirect(f"/deployos/wizard/{ma}/{SO_BUOC}")
        cauhinh = {k: v for k, v in d.items() if not k.startswith("_")}
        cauhinh.pop("che_do", None)
        # "tu_kichban" chi la dau vet cho biet trinh tu nay duoc nap tu
        # kich ban nao - KHONG phai noi dung cua kich ban. Neu luu ca no
        # vao file thi kich ban moi se mang ten kich ban khac trong ruot,
        # rat de gay hieu nham khi doc lai file sau nay.
        cauhinh.pop("tu_kichban", None)
        ok, msg = luu_kichban(cauhinh, request.form.get("ten", ""))
        if ok:
            # Kich ban moi/da sua hien ngay trong menu PXE neu PXE dang bat
            # (dung/dung lai anh dia cua no). PXE tat thi khong lam gi.
            from ui import pxe as _pxe
            msg += _pxe.cap_nhat_menu()
        ds = danh_sach_kichban()
        body = (_tabs("kichban") + _msg(msg, ok) +
                _bang_kichban(ds, _esc) +
                '<div class="row" style="margin-top:8px;">'
                '<a class="btn" href="/deployos/kichban">Về danh sách kịch bản</a></div>')
        return _trang(body, "Deployment OS", "Kịch bản")

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

    # ------------------------- he dieu hanh (mo hinh MDT: "Operating Systems")
    @app.route("/deployos/os")
    def deployos_os():
        return _trang_os()

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

    # ----------------------------- driver (mo hinh MDT: "Out-of-Box Drivers")
    @app.route("/deployos/drivers")
    def deployos_drivers():
        return _trang_drivers()

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
        return _trang(body, "Deployment OS", "Driver")

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

    # 01/10/2026 (anh Thoai: "bo tham so cai dat tren Console Pi va ISO, chi giu tren
    # kho"): tab "Tham so cai dat" da bo. Bang tra tham so cai im lang gio chi quan ly
    # tren trang kho (muc "Tham so cai dat"); tham so cua TUNG phan mem van dat o
    # tab "Phan mem" hoac di kem luc tai tu kho. Link cu chuyen ve Tai nguyen.
    @app.route("/deployos/thamso")
    def deployos_thamso_da_bo():
        return redirect("/deployos/os")

    # ==================================== TAB "KHO TRUNG TÂM"
    # Xem ui/khotrungtam.py cho phan goi HTTP thuc su. O day chi la giao
    # dien: ket noi (ma 6 ky tu), tim/loc, tai o nen vao dung thu muc cuc
    # bo (APPS_DIR / SCRIPTS_DIR / 1 he dieu hanh moi trong OS_DIR).
    TEN_LOAI_KHO = {"phanmem": "Phần mềm", "ungdung": "Ứng dụng nhiều file", "script": "Script", "os": "Hệ điều hành",
                    "winpe": "WinPE", "font": "Font chữ"}

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
            body = _tabs("kho") + _msg(msg, ok) + f"""
            <div class="card">
              <h3>Máy đang tự kết nối kho</h3>
              <p style="margin:0 0 10px;">Máy tự kết nối kho khi có Internet, không cần điền gì.
                Lần thử gần nhất: <strong>{_esc(tu_msg)}</strong></p>
              <a href="/deployos/kho"><button type="button">🔄 Thử lại ngay</button></a>
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
            return _trang(body, "Deployment OS", "Kho trung tâm - chưa kết nối")

        ok_ds, ket_qua = _kt.danh_sach(cauhinh)
        if not ok_ds:
            body = _tabs("kho") + _msg(msg, ok) + f"""
            <div class="msg err">Không lấy được danh sách từ kho: {_esc(ket_qua)}</div>
            <div class="card">
              <a href="/deployos/kho"><button type="button">Thử lại</button></a>
            </div>"""
            return _trang(body, "Deployment OS", "Kho trung tâm - lỗi kết nối")

        ds = ket_qua
        if ngu_canh_trienkhai():     # Trien khai phan mem: khong co He dieu hanh / WinPE
            ds = [m for m in ds if m.get("loai") not in ("os", "winpe")]
        cac_os = danh_sach_os()
        du_lieu_js = json.dumps([
            {"id": m.get("id", ""),
             "tim": bo_dau(" ".join(str(m.get(k, "")) for k in
                                        ("ten", "mo_ta", "du_lieu", "ten_file")))}
            for m in ds], ensure_ascii=False)

        ten_loai_hien = {k: v for k, v in TEN_LOAI_KHO.items()
                         if not (ngu_canh_trienkhai() and k in ("os", "winpe"))}
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
                      {'onsubmit="return confirm(&#39;Tải lại và ghi đè bản đang có?&#39;);"' if da_co else ''}>
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
              <td>{nhan_loai}</td>
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

        body = _tabs("kho") + _msg(msg, ok) + f"""
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
            if (co && !confirm(co + ' mục đã có trên máy sẽ được tải lại và ghi đè. Tiếp tục?')) {{
              e.preventDefault(); return; }}
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
            if (!confirm('HUỶ TẢI "' + ten + '"?\\n\\nMọi thứ đã tải về và đang xử lý cho mục này sẽ bị XOÁ SẠCH.\\nMuốn dùng lại phải tải lại từ đầu.'))
              e.preventDefault();
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
              location.replace('/deployos/kho');
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
        return _trang(body, "Deployment OS", "Kho trung tâm")

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
        return redirect("/deployos/kho")

    @app.route("/deployos/kho")
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
        return redirect("/deployos/kho")

    @app.route("/deployos/kho/xoa-xong", methods=["POST"])
    def deployos_kho_xoa_xong():
        from ui import khotrungtam as _kt
        _kt.xoa_viec_xong()
        return redirect("/deployos/kho")

    def _con_trong(thu_muc):
        try:
            st = os.statvfs(thu_muc)
            return st.f_bavail * st.f_frsize
        except OSError:
            return 0

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
                return True, f'Đã tải "{ten_hien_thi}": {so_them} font trong Tài nguyên → Font chữ.'

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

    # ------------------------- ung dung thu muc (mo hinh MDT: "Application
    # with source files" - xem chi tiet trong docstring cua danh_sach_ungdung()
    # o dau file. Dung cho bo cai NHIEU FILE nhu Office 365 (Office Deployment
    # Tool: thu muc Office\ + setup.exe + configuration.xml).
    @app.route("/deployos/ungdung")
    def deployos_ungdung():
        return _trang_ungdung()

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
        return _trang(body, "Deployment OS", "Ứng dụng (nhiều file)")

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
        return _trang(body, "Deployment OS", f"Ứng dụng - {u['ten_hien_thi']}")

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
        except Exception:
            pass
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

    # ------------------------- bo font chu (xem muc BO FONT o dau file).
    # Font chu rieng cua cong ty, thuong hang tram file: tai len NHIEU FILE / ca THU MUC /
    # file .zip trong 1 lan (trinh duyet gui TUNG file mot, co thanh tien trinh), moi file
    # duoc doc that de kiem tra la font hop le.
    def _khoi_o_dia_da_do():
        """The o buoc chia o: 3 bao cao "Do o dia" moi nhat, nut dien so o."""
        from ui import doodia as _od
        ds = _od.danh_sach_bao_cao()[:3]
        if not ds:
            return """<div class="msg info" style="font-size:13px;">Chưa biết máy có những ổ nào?
              Cho máy boot qua mạng, chọn <strong>3. Do o dia</strong> trong menu PXE (chỉ đọc,
              không xóa gì) - kết quả hiện ở <a href="/deployos/o-dia">Ổ đĩa đã dò</a> và ngay
              tại đây để chọn đúng ổ.</div>"""
        return ("""<div class="card" style="border-left:4px solid #3dd3ff;"><h3>Ổ đĩa đã dò
              (bấm "Dùng ổ ..." để điền số ổ)</h3>
              <p style="color:#8b93a1;font-size:13px;margin:0;">3 lần dò gần nhất - xem tất cả ở
              <a href="/deployos/o-dia">Ổ đĩa đã dò</a>.</p></div>""" +
                "".join(ve_bao_cao_o_dia(kq, nut_chon=True) for kq in ds))

    # ------------------------- o dia da do (ui/doodia.py): may khach boot muc PXE "Do o dia",
    # gui ve danh sach o dia + phan vung -> ky su xem roi chon DUNG so o cho kich ban.
    @app.route("/deployos/o-dia")
    def deployos_o_dia():
        return _trang_o_dia()

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
        return _trang(body, "Deployment OS", "Ổ đĩa đã dò")

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

    @app.route("/deployos/font")
    def deployos_font():
        return _trang_font()

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
        return _trang(body, "Deployment OS", "Font chữ")

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
        return _trang(body, "Deployment OS", f"Font chữ - {b['ten_hien_thi']}")

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

    @app.route("/deployos/drivers/<driver_id>")
    def deployos_drivers_chitiet(driver_id):
        return _trang_driver_chitiet(driver_id)

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
        return _trang(body, "Deployment OS", f"Driver - {dr['ten_hien_thi']}")

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
            except Exception:
                pass
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

    # ------------------------------------------------------ 2.1 file boot
    @app.route("/deployos/console")
    def deployos_console():
        return _trang_file_boot()

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
        return _trang(body, "Deployment OS", "2.1 - WinPE")

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

        <datalist id="goiy-thamso">""" + "".join(
            f'<option value="{_esc(gt)}">{_esc(mo_ta)}</option>'
            for gt, mo_ta in GOI_Y_THAM_SO) + """</datalist>

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
                             list="goiy-thamso" autocapitalize="off">
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

        thanh_cong_cu = f"""
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
        return _trang(body, "Deployment OS", "2.2 - Phần mềm")

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
        return _trang(body, "Deployment OS", "2.3 - Script")

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

    # -------------------------------------------------------- 2.4 kich ban
    def _bang_kichban(ds, esc):
        if not ds:
            return ('<p style="color:#8b93a1;">Chưa có kịch bản nào. Bấm '
                    '"Tạo kịch bản mới" để tạo cái đầu tiên.</p>')
        hang = ""
        for k in ds:
            hang += f"""
            <tr>
              <td><strong>{esc(k.get('ten_kichban', k['_file']))}</strong></td>
              <td>{_o_tom_tat(k, esc)}</td>
              <td style="color:#8b93a1;">{esc(k.get('_ngay', ''))}</td>
              <td>
                <a class="btn small gray" href="/deployos/kichban/sua/{esc(k['_file'])}">Chỉnh sửa</a>
                <form method="POST" action="/deployos/kichban/xoa" style="display:inline;"
                      onsubmit="return confirm('Xóa kịch bản này?');">
                  <input type="hidden" name="ten" value="{esc(k['_file'])}">
                  <button type="submit" class="red small">Xóa</button>
                </form>
              </td>
            </tr>"""
        return f"""
        <div class="tbl-scroll"><table>
          <tr><th>Tên kịch bản</th><th>Tóm tắt</th>
              <th style="width:140px;">Ngày tạo</th><th style="width:150px;">Thao tác</th></tr>
          {hang}
        </table></div>"""

    return app








