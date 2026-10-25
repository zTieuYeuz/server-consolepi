# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Deploy OS - tom tat kich ban cho giao dien (ten OS, tom tat day du, o tom tat, mo ta ngan).

(B4: tach nguyen van tu deployos.py; ten ham/hang giu nguyen, nguon van re-export.)"""
import re
from ui.duongdan import DEPLOY_DIR, BOOT_DIR, APPS_DIR, SCRIPTS_DIR, KICHBAN_DIR, OS_DIR, DRIVERS_DIR, UNGDUNG_DIR, FONTS_DIR, EXT_SCRIPT  # noqa: F401  (B3: khai bao o core/duongdan.py)
from ui import datten as _dt
from consolesystem.features.deploy_os.dos_font import (chuan_hoa_fonts, lay_bo_font)  # noqa: F401
from consolesystem.features.deploy_os.dos_hangso import (BAN_PHIM, NGON_NGU, _unattend)  # noqa: F401
from consolesystem.features.deploy_os.dos_os import (lay_os)  # noqa: F401
from consolesystem.features.deploy_os.dos_phanmem import (chuan_hoa_apps, chuan_hoa_ungdung)  # noqa: F401


def _ten_os(d):
    o = lay_os(d.get("os_id", ""))
    return o["ten_hien_thi"] if o else "Chưa chọn"

def _tom_tat_day_du(k, esc):
    """
    Bang tom tat DAY DU cua 1 kich ban - hien trong hop thoai khi bam nut
    "Tóm tắt" o danh sach.

    VI SAO TACH RA (anh Thoai: "phan tom tat khong can dai du vay dau"):
    truoc day toan bo noi dung nay bi nhoi vao 1 o cua bang danh sach, lam
    moi hang cao nghen ngang, nhin ca danh sach rat kho. Nay o do chi con
    2 dong (cat bang CSS), muon xem het thi bam nut - khong mat thong tin
    nao ca, chi doi cho hien.
    """
    from ui import unattend as _u
    dong = []

    def them(nhan, gt):
        if gt:
            dong.append(f"<tr><td style='color:#8b93a1;white-space:nowrap;'>"
                        f"{esc(nhan)}</td><td>{gt}</td></tr>")

    # (Dong "Kieu boot" da bo 25/09/2026: che do mang chon khi bat PXE, khong
    # con thuoc kich ban - xem ui/pxemenu.py.)
    them("Hệ điều hành", esc(_ten_os(k)))
    them("Tên máy", esc(_dt.mo_ta(k)))
    them("Tài khoản", esc(k.get("username") or "") if k.get("os_ho") == "linux"
         else "Administrator")
    them("Múi giờ", esc(k.get("mui_gio") or ""))

    if k.get("os_ho") != "linux":
        ten_nn = dict(NGON_NGU).get(k.get("ngon_ngu"), k.get("ngon_ngu") or "")
        ten_bp = dict(BAN_PHIM).get(k.get("ban_phim"), k.get("ban_phim") or "")
        them("Ngôn ngữ", esc(ten_nn))
        them("Bàn phím", esc(ten_bp))
        them("Key Windows", "đã nhập" if k.get("product_key")
             else "<span style='color:#8b93a1;'>key KMS mặc định</span>")
        them("Tự đăng nhập", "mãi mãi" if k.get("tu_dang_nhap")
             else "chỉ lần đầu (sau đó hỏi mật khẩu)")

    if k.get("domain"):
        mo = esc(k["domain"])
        if k.get("domain_ou"):
            mo += f" &mdash; OU: {esc(k['domain_ou'])}"
        them("Gia nhập domain", mo)

    ds_app = chuan_hoa_apps(k.get("apps"))
    if ds_app:
        them("Phần mềm", "<br>".join(
            f"{esc(a['ten'])} <small style='color:#8b93a1;'>"
            f"({'máy' if a.get('dich') == 'may' else 'người dùng'})</small>"
            for a in ds_app))

    ds_ud = chuan_hoa_ungdung(k.get("ungdung"))
    if ds_ud:
        them("Ứng dụng nhiều file", "<br>".join(
            f"{esc(u['id'])} <small style='color:#8b93a1;'>"
            f"({'máy' if u.get('dich') == 'may' else 'người dùng'})</small>"
            for u in ds_ud))

    ds_font = chuan_hoa_fonts(k.get("fonts"))
    if ds_font:
        them("Font chữ", "<br>".join(
            esc(lay_bo_font(b)["ten_hien_thi"]) if lay_bo_font(b)
            else f"{esc(b)} <small style='color:#ef4444;'>(bộ font không còn)</small>"
            for b in ds_font))

    if k.get("scripts"):
        them("Script", "<br>".join(esc(s) for s in k["scripts"]))

    da_chon = set(k.get("tuy_chon") or [])
    if da_chon:
        them("Tùy chọn Windows", "<br>".join(
            esc(nhan) for ma, nhan, _m, _p, _l in _u.TUY_CHON_WINDOWS
            if ma in da_chon))

    go = k.get("go_app") or []
    if go:
        ten_theo_ma = {ma: ten for ma, ten, _n in _u.APP_RAC}
        them("Gỡ ứng dụng kèm sẵn",
             f"{len(go)} ứng dụng: "
             + ", ".join(esc(ten_theo_ma.get(m, m)) for m in go))

    if (k.get("lenh_them") or "").strip():
        them("Lệnh thêm",
             f"<pre style='margin:0;white-space:pre-wrap;'>"
             f"{esc(k['lenh_them'])}</pre>")

    od = k.get("o_dia_che_do")
    them("Ổ đĩa", ("tự động (%s, GPT/MBR tự nhận theo máy; %s)" % (esc(_unattend().mo_ta_chon_o(k)), esc(_unattend().mo_ta_tu_dong(k)))
                   if od == "tu_dong" else "chia tay (%s)" % esc(_unattend().mo_ta_chon_o(k))))
    return "<table class='tt-bang'>" + "".join(dong) + "</table>"

def _o_tom_tat(k, esc):
    """1 o bang: tom tat 2 dong + nut mo hop thoai xem day du."""
    ma = "tt-" + re.sub(r"[^A-Za-z0-9_-]", "_", k.get("_file", ""))
    return f"""
      <div class="tt-gon">{esc(_mo_ta_ngan(k))}</div>
      <button type="button" class="tt-nut"
              onclick="document.getElementById('{ma}').showModal()">Tóm tắt</button>
      <dialog id="{ma}" class="tt-hop">
        <h3>{esc(k.get('ten_kichban', k.get('_file', '')))}</h3>
        {_tom_tat_day_du(k, esc)}
        <form method="dialog" style="margin-top:14px;">
          <button class="gray">Đóng</button>
        </form>
      </dialog>"""

def _mo_ta_ngan(k):
    """
    Tom tat cho bang danh sach kich ban.

    LY DO PHAI GHI DAY DU (anh Thoai: "nhieu khi sau nay sao anh biet
    duoc kich ban do da co nhung cai gi option gi"): truoc day dong nay
    chi ghi OS + ten may + so luong phan mem/script, nen nhin vao danh
    sach khong the biet kich ban do cai PHAN MEM NAO, bat TUY CHON gi,
    co gia nhap domain khong - phai bam "Dung" vao tung cai moi biet.
    Gio liet ke thang ten phan mem va ten tuy chon.
    """
    phan = [_ten_os(k)]
    if _dt.mo_ta(k):
        phan.append(_dt.mo_ta(k))
    if k.get("domain"):
        phan.append("domain: " + k["domain"])

    ds_app = chuan_hoa_apps(k.get("apps"))
    if ds_app:
        phan.append("phần mềm: " + ", ".join(a["ten"] for a in ds_app))

    ds_ud = chuan_hoa_ungdung(k.get("ungdung"))
    if ds_ud:
        phan.append("ứng dụng: " + ", ".join(u["id"] for u in ds_ud))

    ds_font = chuan_hoa_fonts(k.get("fonts"))
    if ds_font:
        phan.append("font: " + ", ".join(ds_font))

    n_sc = len(k.get("scripts") or [])
    if n_sc:
        phan.append(f"{n_sc} script")

    da_chon = set(k.get("tuy_chon") or [])
    if da_chon:
        from ui import unattend as _u
        ten_tc = [nhan for ma, nhan, _m, _p, _l in _u.TUY_CHON_WINDOWS
                  if ma in da_chon]
        phan.append("tùy chọn: " + ", ".join(ten_tc))

    if (k.get("lenh_them") or "").strip():
        phan.append("có lệnh thêm")

    return " - ".join(phan)
