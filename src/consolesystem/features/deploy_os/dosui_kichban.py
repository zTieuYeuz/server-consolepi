# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Tach tu deployos.py (B4).

(B4: tach nguyen van tu deployos.py::register_deployos; ten ham/route giu nguyen.)"""
import json
import os
import re
import secrets
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
from consolesystem.features.deploy_os.dos_giaodien import (_JS_TAI_FONT, _tabs_trienkhai, ngu_canh_trienkhai, tabs_deployos, ve_bao_cao_o_dia)  # noqa: F401  (B4: nguyen van o module nay)
from flask import (request, redirect, flash, get_flashed_messages)
from ui.home import _esc
from consolesystem.features.deploy_os.dosui_chung import (_msg, _tabs, _trang)  # noqa: F401


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


def _nap_kichban_vao_trinh_tu(ten):
    """Nap 1 kich ban da luu vao 1 trinh tu moi. Tra ve (ma, kb)."""
    kb = doc_kichban(ten)
    if kb is None:
        return None, None
    _don_wizard_cu()
    ma = secrets.token_urlsafe(12)
    _WIZARD[ma] = cauhinh_tu_kichban(kb)
    return ma, kb


def _het_han():
    return _trang(
        _tabs("kichban") +
        '<div class="msg warn">Trình tự này đã hết hạn hoặc dashboard vừa '
        'khởi động lại nên không còn giữ được lựa chọn đang dở. '
        '<a href="/deployos/boot">Bắt đầu lại</a> - kịch bản đã lưu trên '
        'đĩa thì không mất.</div>',
        "Deployment OS")


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


_thieu_gi = thieu_gi


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


def register_kichban(app):
    # =================================================== 1. TAB "BOOT OS"
    @app.route("/deployos")
    def deployos_home():
        return redirect("/deployos/kichban")

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

    # 01/10/2026 (anh Thoai: "bo tham so cai dat tren Console Pi va ISO, chi giu tren
    # kho"): tab "Tham so cai dat" da bo. Bang tra tham so cai im lang gio chi quan ly
    # tren trang kho (muc "Tham so cai dat"); tham so cua TUNG phan mem van dat o
    # tab "Phan mem" hoac di kem luc tai tu kho. Link cu chuyen ve Tai nguyen.
    @app.route("/deployos/thamso")
    def deployos_thamso_da_bo():
        return redirect("/deployos/os")
