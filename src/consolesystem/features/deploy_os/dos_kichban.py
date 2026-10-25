# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Deploy OS - KICH BAN (task sequence): luu/doc/xoa, wizard, cau hinh mac dinh, kiem tra san sang, phan vung mac dinh.

(B4: tach nguyen van tu deployos.py; ten ham/hang giu nguyen, nguon van re-export.)"""
import json
import os
import re
import secrets
import time
from ui.duongdan import DEPLOY_DIR, BOOT_DIR, APPS_DIR, SCRIPTS_DIR, KICHBAN_DIR, OS_DIR, DRIVERS_DIR, UNGDUNG_DIR, FONTS_DIR, EXT_SCRIPT  # noqa: F401  (B3: khai bao o core/duongdan.py)
from ui import datten as _dt
from consolesystem.features.deploy_os.dos_chung import (_bao_dam_thu_muc, _duong_dan_trong, _liet_ke, ten_an_toan)  # noqa: F401
from consolesystem.features.deploy_os.dos_hangso import (BAN_PHIM, EXT_BOOT, MUI_GIO, NGON_NGU)  # noqa: F401
from consolesystem.features.deploy_os.dos_os import (lay_os)  # noqa: F401


# ------------------------------------------------------------ kich ban (2.4)
def danh_sach_kichban():
    _bao_dam_thu_muc()
    ra = []
    try:
        for n in sorted(os.listdir(KICHBAN_DIR)):
            if not n.endswith(".json"):
                continue
            p = os.path.join(KICHBAN_DIR, n)
            try:
                with open(p) as f:
                    d = json.load(f)
            except Exception:
                continue
            d["_file"] = n
            d["_ngay"] = time.strftime("%Y-%m-%d %H:%M",
                                       time.localtime(os.stat(p).st_mtime))
            ra.append(d)
    except OSError:
        pass
    return ra

def doc_kichban(ten_file):
    p = _duong_dan_trong(KICHBAN_DIR, ten_file)
    if not p or not os.path.isfile(p):
        return None
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return None

def luu_kichban(cauhinh, ten):
    """Luu kich ban. File de quyen 600 vi co the chua mat khau may dich."""
    _bao_dam_thu_muc()
    ten = (ten or "").strip()
    if not ten:
        return False, "Chưa đặt tên kịch bản."
    ten_file = ten_an_toan(ten.replace(" ", "_")) + ".json"
    if ten_file == ".json":
        return False, "Tên kịch bản không hợp lệ."
    p = os.path.join(KICHBAN_DIR, ten_file)

    d = dict(cauhinh)
    d["ten_kichban"] = ten
    d["tao_luc"] = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        # Mo bang O_CREAT|O_WRONLY voi quyen 600 ngay tu luc tao - khong de
        # co khe thoi gian nao file nam do voi quyen rong hon.
        fd = os.open(p, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.chmod(p, 0o600)
    except OSError as e:
        return False, f"Không lưu được: {e}"
    return True, f"Đã lưu kịch bản \"{ten}\"."

def xoa_kichban(ten_file):
    p = _duong_dan_trong(KICHBAN_DIR, ten_file)
    if not p or not os.path.isfile(p):
        return False, "Không tìm thấy kịch bản."
    try:
        os.remove(p)
    except OSError as e:
        return False, f"Không xóa được: {e}"
    return True, "Đã xóa kịch bản."

# ------------------------------------------------------- kiem tra san sang
def kiem_tra_san_sang(cauhinh):
    """
    Doc trang thai THAT tren may xem da du dieu kien boot qua mang chua.
    KHONG bao gio bao "san sang" neu chua kiem chung duoc - moi muc o day
    deu la mot phep kiem tra that (co file khong / dich vu co that khong).

    Tra ve danh sach (dat, nhan, chi_tiet).
    """
    ra = []

    # 1. Co file boot nao chua
    ds_boot = _liet_ke(BOOT_DIR, EXT_BOOT)
    ra.append((
        bool(ds_boot),
        "File boot đã tải lên",
        (f"{len(ds_boot)} file trong {BOOT_DIR}" if ds_boot else
         "Chưa có file nào - vào tab \"Tài nguyên\" > \"WinPE\" để tải lên"),
    ))

    # 2. Bootloader iPXE (giai doan 1 cua PXE: TFTP phat file nho nay truoc)
    # Tu 1.5.0 kem san ban ky chinh thuc (src/pxe-boot) - khong can tai len.
    from ui import pxe as _pxe
    co_ipxe = _pxe._file_kem_du()
    ra.append((
        co_ipxe,
        "Bootloader iPXE + wimboot",
        ("Kèm sẵn bản ký chính thức - máy BIOS, UEFI và UEFI bật Secure Boot"
         if co_ipxe else "THIẾU file kèm sẵn - cài lại/cập nhật Console System"),
    ))

    # Muc "cau hinh PXE cua dnsmasq" TUNG nam o day nhu 1 gach dau dong tinh
    # ("chua dung, GIAI DOAN KE TIEP"). Da bo: ui/pxe.py gio TU SINH file
    # /etc/dnsmasq-pxe.conf moi lan bam "Bat PXE" (xem bat_pxe()), nen kiem
    # tra "da co san file do chua" o day la SAI Y NGHIA - no se luon bao
    # "chua co" cho toi khi nguoi dung bam nut bat, tao vong luan quan (nut
    # bat lai nam trong khoi chi hien khi kiem tra nay dat). Trang thai PXE
    # that su gio xem o bang rieng cua ui/pxe.py (trang_thai_chuan_bi()),
    # hien ngay duoi bang nay trong buoc 7 khi che_do la "chay".

    # 3. Anh WinPE/install.wim cua HE DIEU HANH da chon (chi can khi cai
    #    Windows) - LOI THAT DA GAP: muc nay TUNG kiem tra file "boot.wim"
    #    nam ngay trong BOOT_DIR (ha tang PXE dung chung), la cau truc CU
    #    TRUOC KHI tach rieng tung he dieu hanh vao "os/<os_id>/" (xem
    #    danh_sach_os()) - sau khi tach, boot.wim khong con nam trong
    #    BOOT_DIR nua nen muc nay LUON bao sai "chua co" du da tai len
    #    day du qua tab "Tai nguyen > He dieu hanh". Sua lai doc dung
    #    os_id cua kich ban dang xet.
    if (cauhinh or {}).get("os_ho") == "windows":
        os_id = (cauhinh or {}).get("os_id", "")
        o = lay_os(os_id) if os_id else None
        if not os_id:
            ra.append((
                False, "Hệ điều hành",
                "Chưa chọn hệ điều hành ở bước 1 của kịch bản.",
            ))
        elif not o:
            ra.append((
                False, "Hệ điều hành",
                f'Không tìm thấy hệ điều hành "{os_id}" (có thể đã bị xóa) - '
                "chọn lại ở bước 1.",
            ))
        else:
            ra.append((
                o["co_boot_wim"], "Ảnh WinPE (boot.wim)",
                (f"Đã có trong os/{os_id}/" if o["co_boot_wim"] else
                 f'Chưa tải boot.wim cho "{o["ten_hien_thi"]}" - vào tab '
                 '"Tài nguyên > Hệ điều hành" để tải lên.'),
            ))
            ra.append((
                o["co_install_wim"], "Ảnh cài đặt (install.wim)",
                (f"Đã có trong os/{os_id}/" if o["co_install_wim"] else
                 f'Chưa tải install.wim cho "{o["ten_hien_thi"]}" - vào tab '
                 '"Tài nguyên > Hệ điều hành" để tải lên.'),
            ))

    return ra

# ============================================================ trang thai wizard
#
# Giu trang thai cua trinh tu tu chon O PHIA MAY CHU (khong nhet vao cookie
# phien): cau hinh co danh sach phan vung/phan mem/script nen de vuot qua
# gioi han ~4KB cua cookie, luc do phien dang nhap se hong theo. Cach nay
# giong het _SCAN_CACHE trong ui/network.py va _PING_STATE trong
# nettools/ping_monitor.py - da chay on dinh tu truoc.
#
# Danh doi da biet: khoi dong lai dashboard thi trinh tu dang lam do mat
# (phai chon lai tu buoc 1). Chap nhan duoc vi kich ban da luu thi nam tren
# dia, khong mat.
_WIZARD = {}

_WIZARD_HAN = 6 * 3600          # don cac phien bo do qua 6 tieng

def _don_wizard_cu():
    nay = time.time()
    for k in [k for k, v in _WIZARD.items() if nay - v.get("_luc", 0) > _WIZARD_HAN]:
        _WIZARD.pop(k, None)

def _wizard_moi(che_do):
    """che_do: 'chay' = dung ngay | 'luu' = luu thanh kich ban."""
    _don_wizard_cu()
    ma = secrets.token_urlsafe(12)
    _WIZARD[ma] = _cauhinh_mac_dinh(che_do)
    return ma

def _cauhinh_mac_dinh(che_do):
    """Gia tri mac dinh cua 1 trinh tu (tach ra de menu PXE dung chung)."""
    return {
        "_luc": time.time(),
        "che_do": che_do,
        "kieu_boot": "truc_tiep",
        "os_ho": "", "os_id": "", "driver_ids": [],
        "ten_may": "", "username": "", "password": "",
        # 1.9.4: cach dat ten may (xem ui/datten.py) - mac dinh "co_dinh" = hanh vi cu.
        "ten_may_che_do": "co_dinh", "ten_may_tiento": "", "ten_may_tiento_ngau": "",
        "ten_may_csv": {}, "ten_may_csv_ten": "",
        "ssh": False, "mui_gio": MUI_GIO[0],
        # Tai khoan Administrator co san cua Windows: MAC DINH TAT (dung
        # dung cach Windows lam). Chi bat khi anh Thoai tich chon va dat
        # mat khau - tai khoan nay khong bi khoa man hinh dang nhap nhu
        # tai khoan thuong, nen bat ma de trong mat khau la rat nguy hiem.
        "bat_admin": False, "mk_admin": "",
        # Tu dong dang nhap (may kiosk/trung bay) + danh sach app kem san
        # can go (xem ui/unattend.py: APP_RAC).
        "tu_dang_nhap": False, "go_app": [],
        # Ngon ngu / ban phim / key Windows. Truoc day 3 thu nay deu bi
        # GHI CUNG trong ui/unattend.py (en-US + key KMS cong khai), nguoi
        # dung khong doi duoc.
        "ngon_ngu": NGON_NGU[0][0], "ban_phim": BAN_PHIM[0][0],
        "product_key": "",
        "o_dia_che_do": "tu_dong", "o_dia_so": "0", "o_dia_bang": "tu_dong",
        # Cach chon o dich (1.9.0): so | co_windows | dung_luong | model | nho_nhat | lon_nhat
        "o_dia_chon": "so", "o_dia_gb": "", "o_dia_dungsai": "10", "o_dia_model": "",
        "tu_dong_c_gb": "", "tu_dong_d": False, "tu_dong_c_nhan": "Windows", "tu_dong_d_nhan": "DuLieu",
        "phan_vung": [],
        "apps": [], "ungdung": [], "fonts": [], "scripts": [], "lenh_them": "",
        # Gia nhap domain + cac tuy chon Windows sau khi cai (mo hinh MDT).
        # Xem ui/unattend.py: TUY_CHON_WINDOWS, _khoi_gia_nhap_domain().
        "domain": "", "domain_ou": "", "domain_user": "", "domain_pass": "",
        "tuy_chon": [],
    }

# Cac truong cua kich ban da luu duoc nap vao trinh tu khi "Dung".
_TRUONG_KICHBAN = (
    "kieu_boot", "os_ho", "os_id", "driver_ids", "ten_may",
    "ten_may_che_do", "ten_may_tiento", "ten_may_tiento_ngau", "ten_may_csv", "ten_may_csv_ten",
    "username", "password", "ssh", "mui_gio", "o_dia_che_do",
    "o_dia_so", "o_dia_bang", "o_dia_chon", "o_dia_gb", "o_dia_dungsai", "o_dia_model", "tu_dong_c_gb", "tu_dong_d", "tu_dong_c_nhan", "tu_dong_d_nhan", "phan_vung", "apps", "ungdung", "fonts",
    "scripts", "lenh_them",
    "domain", "domain_ou", "domain_user", "domain_pass",
    "tuy_chon",
    "bat_admin", "mk_admin", "ngon_ngu", "ban_phim",
    "product_key", "tu_dang_nhap", "go_app")

def cauhinh_tu_kichban(kb):
    """
    Dict cau hinh day du tu 1 kich ban da luu - Y HET cach nut "Dung" nap
    kich ban (mac dinh cua trinh tu + cac truong da luu). Dung chung cho
    nut "Dung" va menu PXE (ui/pxemenu.py) de 2 duong KHONG BAO GIO lech
    nhau: cung 1 kich ban thi anh dia dung ra phai giong het.
    """
    d = _cauhinh_mac_dinh("chay")
    for k in _TRUONG_KICHBAN:
        if k in kb:
            d[k] = kb[k]
    d["tu_kichban"] = kb.get("ten_kichban", "")
    # Kich ban da luu thi lua chon "go app" trong do la CHINH THUC -
    # kho chon app phai hien dung no, khong duoc tich lai theo mac dinh
    # (xem _khoi_go_app). Ke ca kich ban khong go app nao.
    d["_da_qua_buoc6"] = True
    return d

def thieu_gi(d):
    """Danh sach nhung thu con thieu de chay duoc 1 cau hinh (rong = du)."""
    thieu = []
    if not d["os_ho"]:
        thieu.append("chưa chọn OS")
    if not d["ten_may"] and not _dt.la_dong(d):
        thieu.append("chưa có tên máy")
    if d["os_ho"] == "linux":
        if not d["username"]:
            thieu.append("chưa có tên đăng nhập")
        if not d["password"]:
            thieu.append("chưa đặt mật khẩu")
    elif not d.get("mk_admin"):
        # Windows: chi dung tai khoan Administrator (khong tao user rieng)
        thieu.append("chưa đặt mật khẩu Administrator")
    if not d.get("os_id"):
        thieu.append("chưa chọn hệ điều hành")
    return thieu

def loi_bat_buoc(d):
    """
    Nhung cho SAI/THIEU bat buoc, kem buoc can sua: [(buoc, thong_bao)]. Rong = luu duoc.
    Truoc day moi buoc tu chan "Tiep theo" nen khong can; tu khi bam nhay tu do giua cac
    buoc (01/10/2026) thi buoc Tong ket + luu kich ban phai kiem lai o day.
    """
    ra = []
    if not d.get("os_id"):
        ra.append((2, "chưa chọn hệ điều hành"))
    tm = d.get("ten_may") or ""
    if _dt.che_do_cua(d) == "csv" and not d.get("ten_may_csv"):
        ra.append((3, "chưa tải danh sách CSV (serial → tên máy)"))
    if _dt.la_dong(d):
        pass                                    # ten may dong: tinh luc may chon kich ban (ui/datten.py)
    elif not tm:
        ra.append((3, "chưa điền tên máy"))
    elif not re.fullmatch(r"[A-Za-z0-9-]{1,15}", tm):
        ra.append((3, "tên máy chỉ dùng chữ không dấu, số, dấu gạch ngang, tối đa 15 ký tự"))
    if d.get("os_ho") == "linux":
        if not d.get("username"):
            ra.append((3, "chưa điền tên đăng nhập"))
    elif not d.get("mk_admin"):
        ra.append((3, "chưa đặt mật khẩu cho tài khoản Administrator"))
    return ra

def _wizard_lay(ma):
    d = _WIZARD.get(ma)
    if d is not None:
        d["_luc"] = time.time()
    return d

def _u_tuychon():
    """
    Bang tuy chon Windows - lay tu ui/unattend.py de giao dien va phan
    sinh XML dung CHUNG mot nguon, khong the lech nhau. Import trong ham
    (khong phai dau file) vi unattend.py da import nguoc lai deployos.py.
    """
    from ui import unattend as _u
    return _u.TUY_CHON_WINDOWS

def _khoi_go_app(d, esc):
    """
    Khoi chon cac ung dung kem san can go (buoc 6).

    LAN DAU vao trinh tu thi tich san cac app duoc danh dau nen go trong
    ui/unattend.py (APP_RAC) - de anh Thoai khong phai tich tay 22 o moi
    lan tao kich ban. Nhung khi NAP LAI 1 kich ban da luu thi phai ton
    trong dung lua chon da luu, KE CA khi kich ban do co y khong go app
    nao: neu cu tich san theo mac dinh thi kich ban "giu nguyen may" se
    am tham bien thanh kich ban "go 22 app" - rat nguy hiem.
    Phan biet hai truong hop bang co "_da_qua_buoc6".
    """
    from ui import unattend as _u
    if d.get("_da_qua_buoc6"):
        da_chon = set(d.get("go_app") or [])
    else:
        da_chon = {ma for ma, _ten, nen_go in _u.APP_RAC if nen_go}
    o = ""
    for ma, ten, nen_go in _u.APP_RAC:
        ch = " checked" if ma in da_chon else ""
        goi_y = ("" if nen_go else
                 ' <span style="color:#8b93a1;">(cân nhắc - nhiều người vẫn dùng)</span>')
        o += f"""
        <label class="chon">
          <input type="checkbox" name="go_app" value="{esc(ma)}"{ch}>
          <span class="t">{esc(ten)}</span>
          <div class="d">{esc(ma)}{goi_y}</div>
        </label>"""
    return f"""
              <div class="card">
                <h3>Gỡ ứng dụng kèm sẵn của Windows</h3>
                <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
                  Gỡ cả bản đang cài lẫn "mầm" trong ảnh hệ điều hành, nên tài
                  khoản tạo mới sau này cũng không bị cài lại. Danh sách này đã
                  lọc sẵn - Microsoft Store, Máy tính, Ảnh, Paint, Notepad,
                  Snipping Tool đều được giữ lại vì gỡ đi sẽ gây khó chịu hoặc
                  hỏng chức năng.</p>
                <details class="gap">
                  <summary>Chọn ứng dụng cần gỡ
                    <span class="dem">{len(da_chon)} / {len(_u.APP_RAC)} đã chọn</span></summary>
                  <div class="gap-trong" data-pt="25" data-pt-tim="1">{o}</div>
                </details>
              </div>"""

def _dong_tongket_windows(d, esc):
    """
    Cac dong rieng cua Windows trong bang tong ket: ngon ngu, ban phim,
    key, tai khoan Administrator. Linux khong co nhung muc nay nen tra ve
    rong (khong hien dong trong gay hieu nham).

    Hien TEN DOC DUOC chu khong hien ma (vi-VN, 0409:00000409...) - bang
    tong ket la de anh Thoai doi chieu truoc khi bam chay, doc ma so thi
    khong doi chieu duoc gi.
    """
    if d.get("os_ho") == "linux":
        return ""
    ten_nn = dict(NGON_NGU).get(d.get("ngon_ngu"), d.get("ngon_ngu") or "?")
    ten_bp = dict(BAN_PHIM).get(d.get("ban_phim"), d.get("ban_phim") or "?")
    if d.get("product_key"):
        # Chi hien 5 ky tu cuoi: bang tong ket hay bi chup man hinh gui
        # cho nhau, khong nen de nguyen key ra day.
        o_key = ("&bull;" * 5 + "-" * 1 + "&bull;" * 5 + "-&hellip;-"
                 + esc(d["product_key"][-5:])
                 + ' <span style="color:#8b93a1;">(đã nhập)</span>')
    else:
        o_key = ('<span style="color:#8b93a1;">Key KMS mặc định &mdash; '
                 'máy sẽ ở trạng thái chưa kích hoạt</span>')
    if d.get("tu_dang_nhap"):
        o_tdn = ('<span style="color:#f59e0b;">Bật &mdash; bật máy vào thẳng '
                 'desktop, không hỏi mật khẩu</span>')
    else:
        o_tdn = '<span style="color:#8b93a1;">Tắt (vẫn hỏi mật khẩu)</span>'
    ds_go = d.get("go_app") or []
    if ds_go:
        from ui import unattend as _u
        ten_theo_ma = {ma: ten for ma, ten, _ng in _u.APP_RAC}
        o_go = (f"{len(ds_go)} ứng dụng: "
                + ", ".join(esc(ten_theo_ma.get(m, m)) for m in ds_go))
    else:
        o_go = '<span style="color:#8b93a1;">Không gỡ ứng dụng nào</span>'
    return (f"<tr><td>Ngôn ngữ Windows</td><td>{esc(ten_nn)}</td></tr>\n"
            f"            <tr><td>Kiểu bàn phím</td><td>{esc(ten_bp)}</td></tr>\n"
            f"            <tr><td>Key Windows</td><td>{o_key}</td></tr>\n"
            f"            <tr><td>Tự động đăng nhập</td><td>{o_tdn}</td></tr>\n"
            f"            <tr><td>Gỡ ứng dụng kèm sẵn</td><td>{o_go}</td></tr>")

def _phan_vung_mac_dinh(os_ho):
    """
    Bo phan vung goi y khi chuyen sang che do chia tay - de nguoi dung sua
    tu day thay vi go lai tu dau.

    Vi sao la bo nay (khong phai bia): day la bo phan vung chuan cua may
    UEFI/GPT.
      - Windows: EFI (FAT32) + MSR (Microsoft Reserved, khong dinh dang) +
        o he thong NTFS. MSR la yeu cau cua Windows tren GPT.
      - Linux: EFI (FAT32) + vung trao doi (swap) + o goc (ext4).
    """
    if os_ho == "windows":
        return [
            {"nhan": "EFI", "cd": "260", "fs": "fat32", "gan": "EFI"},
            {"nhan": "MSR", "cd": "16", "fs": "msr", "gan": "-"},
            {"nhan": "Windows", "cd": "con_lai", "fs": "ntfs", "gan": "C:"},
        ]
    return [
        {"nhan": "EFI", "cd": "512", "fs": "fat32", "gan": "/boot/efi"},
        {"nhan": "swap", "cd": "2048", "fs": "swap", "gan": "-"},
        {"nhan": "root", "cd": "con_lai", "fs": "ext4", "gan": "/"},
    ]

def _pv_win(*phan):
    """Bo phan vung Windows GPT: EFI + MSR + cac phan vung du lieu (nhan, MB hoac con_lai, ghi chu o)."""
    ra = [{"nhan": "EFI", "cd": "260", "fs": "fat32", "gan": "EFI"},
          {"nhan": "MSR", "cd": "16", "fs": "msr", "gan": "-"}]
    for nhan, cd, gan in phan:
        ra.append({"nhan": nhan, "cd": str(cd), "fs": "ntfs", "gan": gan})
    return ra

# 5 mau bo phan vung cho che do "Chia bang tay" (Windows). Phan vung dau tien sau MSR la o he dieu hanh.
MAU_PHAN_VUNG_WINDOWS = [
    {"ten": "Chuẩn: 1 ổ C dùng hết ổ",
     "mo_ta": "EFI + MSR + ổ C dùng hết ổ. Chạy được trên mọi ổ từ 64 GB.",
     "pv": _pv_win(("Windows", "con_lai", "C:"))},
    {"ten": "C: 100 GB + D: dữ liệu",
     "mo_ta": "Ổ C 100 GB cho Windows và phần mềm, phần còn lại là ổ dữ liệu. Cần ổ từ 128 GB trở lên.",
     "pv": _pv_win(("Windows", 102400, "C:"), ("DuLieu", "con_lai", "D:"))},
    {"ten": "C: 200 GB + D: dữ liệu",
     "mo_ta": "Ổ C 200 GB (nhiều phần mềm nặng) và ổ dữ liệu phần còn lại. Cần ổ từ 256 GB trở lên.",
     "pv": _pv_win(("Windows", 204800, "C:"), ("DuLieu", "con_lai", "D:"))},
    {"ten": "Máy văn phòng: C 120 GB + D phần mềm + E dữ liệu",
     "mo_ta": "C: 120 GB hệ điều hành, D: 100 GB phần mềm, E: phần còn lại cho tài liệu. Cần ổ từ 256 GB trở lên.",
     "pv": _pv_win(("Windows", 122880, "C:"), ("PhanMem", 102400, "D:"), ("DuLieu", "con_lai", "E:"))},
    {"ten": "Máy chủ nhỏ: C 80 GB + D ứng dụng + E nhật ký + F dữ liệu",
     "mo_ta": "C: 80 GB hệ thống, D: 50 GB ứng dụng, E: 100 GB nhật ký/sao lưu, F: phần còn lại cho dữ liệu. Cần ổ từ 256 GB trở lên.",
     "pv": _pv_win(("HeThong", 81920, "C:"), ("UngDung", 51200, "D:"), ("NhatKy", 102400, "E:"), ("DuLieu", "con_lai", "F:"))},
]
