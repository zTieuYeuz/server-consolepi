# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Deploy OS - thanh tab dung chung (tabs_deployos), ngu canh Trien khai, JS tai font, bao cao o dia.

(B4: tach nguyen van tu deployos.py; ten ham/hang giu nguyen, nguon van re-export.)"""
from consolesystem.core import taisan as _taisan
from ui.duongdan import DEPLOY_DIR, BOOT_DIR, APPS_DIR, SCRIPTS_DIR, KICHBAN_DIR, OS_DIR, DRIVERS_DIR, UNGDUNG_DIR, FONTS_DIR, EXT_SCRIPT  # noqa: F401  (B3: khai bao o core/duongdan.py)
from consolesystem.features.deploy_os.dos_chung import (BUOC_DAU, EXT_DRIVER, EXT_OS_ISO, EXT_OS_WIM, EXT_SXS, SO_BUOC, THU_MUC_THEO_DUONG, _bao_dam_thu_muc, _bo_dau_py, _con_trong_gb, _don_file_do_dang, _duong_dan_trong, _hoan_tat_ghi_thang, _liet_ke, _luu_tai_len, _mo_file_dich, _thu_muc_os_theo_duong, _xoa_file, bo_dau, co_kich_thuoc, so_hien_thi, ten_an_toan)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_phanmem import (GOI_Y_THAM_SO, HAU_TO_GO, _an_toan_trong_zip, _doc_meta_ungdung, _ghi_meta_ungdung, chuan_hoa_apps, chuan_hoa_ungdung, danh_sach_app, danh_sach_ungdung, dat_lenh_cai_ungdung, doc_thongtin_app, ghi_thongtin_app, giai_nen_ungdung, lay_ungdung, liet_ke_muc_ungdung, tao_ungdung_moi, tham_so_mac_dinh_app, xoa_muc_trong_ungdung, xoa_ungdung)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_font import (MAX_FONT_BYTE, MAX_ZIP_FONT_BYTE, _doc_meta_bo_font, _don_tam_cu, _giai_nen_font_zip, _id_bo_font_tu_ten, _luu_font_hop_le, _xoa_tam, chuan_hoa_fonts, danh_sach_bo_font, duong_bo_font, lay_bo_font, tao_bo_font, them_font_vao_bo, xoa_bo_font, xoa_font_trong_bo)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_os import (_CACHE_CHI_SO_PRO, chi_so_anh_pro, co_sxs, danh_sach_os, duong_boot_wim, duong_install_wim, lay_os, tao_os_moi, xoa_os)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_driver import (EXT_GOI_NEN_DRIVER, _tu_may, danh_sach_driver, dat_driver_cho_boot, dat_model_driver, driver_hop_model, giai_nen_goi_driver, khop_model, tao_driver_moi, xoa_driver, xoa_file_trong_driver)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_kichban import (MAU_PHAN_VUNG_WINDOWS, _TRUONG_KICHBAN, _WIZARD, _WIZARD_HAN, _cauhinh_mac_dinh, _don_wizard_cu, _dong_tongket_windows, _khoi_go_app, _phan_vung_mac_dinh, _pv_win, _u_tuychon, _wizard_lay, _wizard_moi, cauhinh_tu_kichban, danh_sach_kichban, doc_kichban, kiem_tra_san_sang, loi_bat_buoc, luu_kichban, thieu_gi, xoa_kichban)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_tomtat import (_mo_ta_ngan, _o_tom_tat, _ten_os, _tom_tat_day_du)  # noqa: F401  (B4: nguyen van o module nay)
from consolesystem.features.deploy_os.dos_hangso import (APPS_META, BAN_PHIM, DANH_SACH_OS, EXT_APP, EXT_BOOT, EXT_UNGDUNG_ZIP, EXT_WINPE, KIEU_BOOT, MIN_FREE_GB, MUI_GIO, NGON_NGU, TEN_BUOC, _unattend)  # noqa: F401  (B4: nguyen van o module nay)



def ngu_canh_trienkhai():
    """True khi nguoi dung dang o muc "Trien khai phan mem" (cac trang Tai nguyen / Kho dung chung voi Deployment OS,
    chi khac thanh tab va khong hien He dieu hanh / Driver / WinPE). Dat boi ui/deploysw.py (before_request)."""
    try:
        from flask import session
        return session.get("nc") == "tk"
    except Exception:
        return False

# "Tai nguyen may" (Kho luu tru): HDH, phan mem, ung dung, font, driver, script, WinPE, nhom tai nguyen.
# Truoc la tab "Tai nguyen" lap lai o Deployment OS va Trien khai phan mem LAN; anh Thoai gom ve 1 muc (28/10/2026).
TAB_TAI_NGUYEN = [
    ("os", "Hệ điều hành", "/deployos/os"),
    ("apps", "Phần mềm", "/deployos/console/apps"),
    ("ungdung", "Ứng dụng (nhiều file)", "/deployos/ungdung"),
    ("font", "Font chữ", "/deployos/font"),
    ("drivers", "Driver", "/deployos/drivers"),
    ("scripts", "Script", "/deployos/console/scripts"),
    ("file", "WinPE", "/deployos/console"),
    ("nhom", "Nhóm tài nguyên", "/deployos/trienkhai/nhom-tn"),
]
from consolesystem.web.chon_may import la_tai_nguyen  # noqa: E402,F401  (dung chung voi web/layout)


def _tabs_tai_nguyen(phu):
    return '<div class="dep-tabs">' + "".join(
        f'<a href="{href}" class="dep-tab{" on" if ma == phu else ""}">{nhan}</a>' for ma, nhan, href in TAB_TAI_NGUYEN) + "</div>"


def _tabs_trienkhai(chinh, phu=""):
    tab_chinh = [
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
    if la_tai_nguyen():
        return _tabs_tai_nguyen(phu)
    if ngu_canh_trienkhai():
        return _tabs_trienkhai(chinh, phu)
    tab_chinh = [
        ("kichban", "Kịch bản", "/deployos/kichban"),
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

_JS_TAI_FONT = _taisan.doc("features/deploy_os/dos_giaodien._JS_TAI_FONT.html")

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
