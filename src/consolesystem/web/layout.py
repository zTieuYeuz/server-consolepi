# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi - Khung giao dien dung chung (thanh dieu huong trai + noi dung phai)

Moi trang trong dashboard deu goi render_page() de co cung bo cuc, thay vi
tu viet lai <html> tu dau. Thiet ke cho man hinh cam ung 1280x800:
  - Nut/muc menu du lon de cham bang ngon tay (toi thieu 44px chieu cao)
  - Thanh trang thai mang luon hien tren cung (yeu cau so 2)
  - Khong dung thu vien ngoai / CDN (Pi mang di hien truong co the khong co net)
"""
from consolesystem.core import taisan as _taisan
from consolesystem.core.nhatky import bo_qua as _bo_qua
import sys as _sys
_sys.modules["ui.layout"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import os
import subprocess
from consolesystem.integrations import cloudflare as _CF

# (duong dan, nhan, icon)
#
# LOI THAT DA TIM RA (nguoi dung bao icon Nguon dien/reboot "bi loi" tren man
# hinh cam ung RasPad): ky tu ⏻ (U+23FB, khoi Unicode "Miscellaneous
# Technical") KHONG nam trong pham vi ma font Noto Color Emoji mac dinh cua
# Pi OS Lite phu toi - hien thanh o vuong trong (tofu) thay vi bieu tuong.
# Da doi sang ⚡ (khoi Emoji chuan, luon co san). Tuyet doi khong dung lai cac
# ky tu trong khoi U+2300-23FF (⏯ ⏸ ⏹ ⏻ ⏼ ⏽...) cho icon hien tren man hinh
# nay - chi dung emoji thuoc khoi chuan (mat cuoi, con vat, do vat thong
# thuong) da kiem chung la luon co san tren Pi OS.
# Thanh menu ben trai.
#
# GOM NHOM thay vi 16 muc phang nhu truoc: 16 dong lam thanh menu dai hon
# man hinh RasPad, phai cuon moi thay het - va cac muc lien quan nhau
# (WiFi/Bluetooth/Truy cap tu xa deu la "duong vao Pi") lai nam rai rac
# xen ke voi thu khong lien quan.
#
# Cau truc: ("href", "ten", "icon")                     -> muc don
#           ("nhom", "ten", "icon", [cac muc con...])   -> nhom mo/dong
#
# Nhom nao chua trang dang mo thi TU DONG bung ra (xem render_page) - de
# nguoi dung luon nhin thay minh dang o dau, khong phai tu mo lai.
# ---------------------------------------------------------------- thuong hieu
#
# Ten HIEN THI cho nguoi dung. Khai o day mot cho de doi ten la doi mot lan
# (anh Thoai 19/09/2026: "chuyen thanh ten console system").
#
# CO Y KHONG doi cac ten NOI BO: duong dan /opt/console-pi, ten dich vu
# console-system-dashboard, ten kho ma nguon... Doi chung phai sua 15 file, 7
# don vi systemd, cau hinh nginx va ca ban da cai tren may dang chay - rui
# ro cao ma nguoi dung khong nhin thay mot chut loi ich nao. Ten hien thi
# la thu duy nhat nguoi dung thay.
TEN_HE_THONG = "CONSOLE SYSTEM"
TEN_NGAN = "Console System"
KHAU_HIEU = "Network Engineer Toolkit"

NAV_ITEMS = [
    ("/", "Tổng quan", "🏠"),

    # Cac duong ket noi VAO chinh con Pi nay
    ("nhom", "Kết nối Console System", "📡", [
        ("/wifi", "WiFi / AP", "📶"),
        ("/bluetooth", "Bluetooth", "🔵"),
        ("/remote", "Truy cập từ xa", "🌍"),
    ]),

    # Cac duong tu Pi ket noi RA thiet bi mang can lam viec
    ("nhom", "Quản lý và kết nối thiết bị", "🔌", [
        ("/phien", "Phiên kết nối", "🗂️"),
        ("/console", "Console", "🖥️"),
        ("/direct", "Cắm thẳng thiết bị", "🔗"),
    ]),

    # Quan ly may tram (kieu OpenUEM): kiem ke, bao mat, trien khai WinGet, profiles
    ("nhom", "Quản lý máy trạm", "🖥️", [
        ("/uem", "Tổng quan máy trạm", "📊"),
        ("/uem/may", "Máy tính", "💻"),
        ("/uem/phan-mem", "Phần mềm", "📦"),
        ("/uem/bao-mat", "Bảo mật", "🛡️"),
        ("/uem/trien-khai", "Triển khai phần mềm", "🚀"),
        ("/rustdesk", "Phần mềm remote", "🛰️"),
        ("/uem/profiles", "Profiles", "📋"),
        ("/uem/bao-cao", "Báo cáo", "📄"),
        ("/uem/quan-tri", "Quản trị", "⚙️"),
    ]),

    ("nhom", "System Utilities", "🛠️", [
        ("/nettools", "Network Tools", "🛠️"),
        ("/deployos", "Deployment OS", "💿"),
        ("/deployos/trienkhai", "Triển khai phần mềm LAN", "🚀"),
    ]),

    # Noi cat du lieu de dung lai
    ("nhom", "Kho lưu trữ", "📦", [
        ("/storage", "Kho file", "💾"),
        ("/kho-trung-tam", "Kho trung tâm", "☁️"),
        ("/commands", "Thư viện lệnh", "📚"),
    ]),

    ("nhom", "Cài đặt", "⚙️", [
        ("/settings", "Cài đặt chung", "⚙️"),
        ("/logs", "Nhật ký", "📋"),
        ("/power", "Nguồn điện", "⚡"),
        ("/gopy", "Góp ý", "💬"),
        ("/giaitri", "Giải trí", "📺"),
        ("/docs", "Tài liệu", "📖"),
    ]),
]

BASE_CSS = _taisan.doc("web/layout.BASE_CSS.css")


import socket
import struct
import time

# Thanh trang thai duoc goi lai moi 30 giay tu MOI trang dang mo. Nho ket qua
# vai giay de khong lam viec trung lap - dang ke tren Pi doi thap.
_STATUS_CACHE = {"data": None, "at": 0.0}
STATUS_TTL = 4.0


def _ipv4_of(name):
    """
    Lay dia chi IPv4 cua 1 interface bang ioctl - KHONG spawn tien trinh.
    Truoc day goi lenh `ip` cho tung interface (3 lan moi lan tai trang);
    tren Pi 3/Zero moi lan spawn ton hang chuc mili giay.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sk:
            packed = struct.pack("256s", name.encode()[:15])
            return socket.inet_ntoa(
                __import__("fcntl").ioctl(sk.fileno(), 0x8915, packed)[20:24]
            )
    except Exception:
        return ""


def _iface_info(name):
    """Tra ve (co_ip, ip, trang_thai_link) cua 1 interface."""
    ip = _ipv4_of(name)
    try:
        with open(f"/sys/class/net/{name}/operstate") as f:
            state = f.read().strip()
    except Exception:
        state = "?"
    return bool(ip), ip, state


def get_status_chips(use_cache=True):
    """
    Thong tin cho thanh trang thai: card LAN, card WiFi, Bluetooth PAN.
    Co IP thi hien IP, khong thi ghi ro ly do.
    """
    if use_cache and _STATUS_CACHE["data"] is not None:
        if time.time() - _STATUS_CACHE["at"] < STATUS_TTL:
            return _STATUS_CACHE["data"]

    chips = []

    # Ten cong KHONG con viet cung "eth0"/"wlan0" nua - hoi ui/phancung.py.
    # Tren Pi van ra dung eth0/wlan0 nhu cu; tren laptop/may ban ra
    # enp3s0/wlp2s0, tren may ao VMware ra ens192. Nhan cua o trang thai
    # cung hien dung ten that de nguoi dung biet may minh dang dung cong nao.
    from ui import phancung as _pc
    ten_day = _pc.cong_day()
    ten_wifi = _pc.cong_wifi()

    # --- Cong co day (LAN) ---
    if ten_day:
        up, ip, state = _iface_info(ten_day)
        chips.append({
            "key": f"LAN ({ten_day})",
            "val": ip if ip else ("Đã cắm dây" if state == "up" else "Chưa cắm dây"),
            "extra": ("link " + state) if not ip else f"link {state}",
            "up": up,
        })
    else:
        # Noi that la may khong co cong day, thay vi hien 1 o "eth0" trong
        # ma nguoi dung khong hieu vi sao no khong bao gio len.
        chips.append({"key": "LAN", "val": "Không có cổng dây",
                      "extra": "máy này không có card mạng có dây", "up": False})

    # --- Cong WiFi ---
    # KHONG duoc thoat som o day du may khong co WiFi: phia duoi con chip
    # Bluetooth va Cloudflare, thoat som la mat ca hai.
    if not ten_wifi:
        chips.append({"key": "WiFi", "val": "Không có card WiFi",
                      "extra": "máy này không có card WiFi", "up": False})
    else:
        up_w, ip_w, state_w = _iface_info(ten_wifi)
        ssid, mode = "", ""
        try:
            info = subprocess.run(["iw", "dev", ten_wifi, "info"],
                                  capture_output=True, text=True, timeout=4).stdout
            for line in info.splitlines():
                line = line.strip()
                if line.startswith("ssid "):
                    ssid = line[5:].strip()
                elif line.startswith("type "):
                    mode = line[5:].strip()
        except Exception as _loi:
            _bo_qua(_loi)

        if mode == "AP":
            extra = "Đang phát AP: " + (ssid or "ConsolePi")
        elif ssid:
            extra = "Đã nối: " + ssid
        else:
            extra = "Chưa kết nối WiFi"
        chips.append({
            "key": f"WiFi ({ten_wifi})",
            "val": ip_w if ip_w else "Không có IP",
            "extra": extra,
            "up": up_w,
        })

    # --- pan0 (Bluetooth) ---
    # pan0 do chinh du an tao ra (bt-pan0.service) va chi dung tren Pi. Tren
    # may khong co no thi bo han chip nay di, thay vi hien "Chua bat" mai
    # mai lam nguoi dung tuong minh cau hinh thieu.
    if not os.path.exists("/sys/class/net/pan0"):
        return _xong_chips(chips)
    up_b, ip_b, _ = _iface_info("pan0")
    n_bt = 0
    try:
        out = subprocess.run(["ip", "neigh", "show", "dev", "pan0"],
                             capture_output=True, text=True, timeout=4).stdout
        n_bt = sum(1 for l in out.splitlines() if "REACHABLE" in l or "STALE" in l)
    except Exception as _loi:
        _bo_qua(_loi)
    chips.append({
        "key": "Bluetooth (pan0)",
        "val": ip_b if ip_b else "Chưa bật",
        "extra": (f"{n_bt} thiết bị đang nối" if n_bt else "Chưa có thiết bị"),
        "up": up_b,
    })

    # --- Cloudflare Tunnel (yeu cau: muon thay trang thai nay ngay tren thanh
    # trang thai, ngang hang voi LAN/WiFi/Bluetooth thay vi phai vao rieng
    # tab Truy cap tu xa moi biet duong ham co dang chay hay khong) ---
    # Import cho vao trong ham (khong dat o dau file): remote.py co import
    # nguoc lai render_page tu chinh file nay - dat import o dau file se tao
    # vong lap import. Cac ham duoc goi o day deu re (shutil.which/os.path,
    # toi da 1 lenh systemctl is-active), cung muc chi phi voi cac chip khac.
    cf_cai = _CF.da_cai()
    cf_tok = _CF.co_token() if cf_cai else False
    cf_chay = _CF.dang_chay() if (cf_cai and cf_tok) else False
    if not cf_cai:
        cf_val, cf_extra = "Chưa cài đặt", "Xem tab Truy cập từ xa"
    elif not cf_tok:
        cf_val, cf_extra = "Chưa cấu hình", "Thiếu token đường hầm"
    elif cf_chay:
        cf_val, cf_extra = "Đang chạy", "Ra Internet qua Cloudflare"
    else:
        cf_val, cf_extra = "Đã tắt", "Đường hầm đang không bật"
    chips.append({
        "key": "Cloudflare",
        "val": cf_val,
        "extra": cf_extra,
        "up": cf_chay,
    })

    return _xong_chips(chips)


def _xong_chips(chips):
    """Luu cache roi tra ve - tach rieng de cho nao thoat som cung dung
    duoc, khong bi quen cap nhat cache."""
    _STATUS_CACHE["data"] = chips
    _STATUS_CACHE["at"] = time.time()
    return chips


from ui.gioithieu import dau_an_an as _dau_an_an
_DAU_AN = _dau_an_an()


# ---------------------------------------------------------------------------
# DOI MAU VIET CUNG -> BIEN MAU (de NEN SANG khong vo trang)
#
# Cac trang viet tu truoc ghi cung hon 500 cho mau toi (nen #1e1e1e, chu
# #eee, chu mo #8b93a1...). Bat nen sang ma de nguyen thi thanh chu trang
# tren nen trang. Thay vi sua tay 30 file (de sot, de lech), render_page
# chuyen moi mau viet cung trong noi dung trang sang bien mau cua he thong
# theo NGHIA cua mau: xam sang -> --chu, xam vua -> --chu-mo, nen toi trung
# tinh -> --the..., do/vang/xanh -> dung bien trang thai tuong ung.
# Mau nen DAM va SANG (nut xanh #4CAF50 chu trang...) thi GIU NGUYEN: chu
# tren no van doc duoc o ca 2 nen.
# ---------------------------------------------------------------------------
_RE_MAU = _re_mau = __import__("re").compile(
    r'(?<![\w-])(color|background-color|background|border-color|border|'
    r'border-(?:left|right|top|bottom)(?:-color)?)(\s*:\s*[^;"\'{}<>]*?)'
    r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b')
_MAU_CACHE = {}


def _phan_loai_mau(hx):
    if len(hx) == 3:
        hx = "".join(c * 2 for c in hx)
    r, g, b = (int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4))
    mx, mn = max(r, g, b), min(r, g, b)
    sang = (mx + mn) / 2
    bao_hoa = 0 if mx == mn else (mx - mn) / (1 - abs(2 * sang - 1) + 1e-9)
    if bao_hoa < 0.18 or (mx - mn) < 0.07:
        sac = "xam"
    elif r >= g and r >= b:
        sac = "vang" if g > 0.55 * r and g > b * 1.4 else "do"
    elif g >= r and g >= b:
        sac = "vang" if r > 0.8 * g and b < 0.6 * g else "xanh"
    else:
        sac = "nhan" if g > 0.55 * b else "tim"
    return sang, sac, mx - mn


def _mau_moi(thuoc_tinh, hx):
    khoa = (thuoc_tinh, hx.lower())
    if khoa in _MAU_CACHE:
        return _MAU_CACHE[khoa]
    sang, sac, do_dam = _phan_loai_mau(hx)
    kq = None
    if thuoc_tinh == "color":
        if sac == "xam":
            if sang >= 0.80 and sang < 0.999:
                kq = "var(--chu)"
            elif 0.40 <= sang < 0.80:
                kq = "var(--chu-mo)"
            elif 0.30 <= sang < 0.40:
                kq = "var(--chu-mo2)"
        elif sang >= 0.35:
            kq = {"xanh": "var(--xanh)", "do": "var(--do)", "vang": "var(--vang)",
                  "nhan": "var(--nhan)"}.get(sac)
    elif thuoc_tinh.startswith("background"):
        if sang < 0.30:
            if sac == "xam":
                kq = ("var(--nen)" if sang < 0.10 else
                      "var(--the)" if sang < 0.16 else "var(--the-noi)")
            else:
                kq = {"xanh": "var(--xanh-mo)", "do": "var(--do-mo)", "vang": "var(--vang-mo)",
                      "nhan": "var(--nhan-mo)"}.get(sac, "var(--the-noi)")
    else:   # vien
        if sac == "xam" and sang < 0.45:
            kq = "var(--vien-ro)"
        elif sac != "xam" and sang >= 0.30:
            kq = {"xanh": "var(--xanh)", "do": "var(--do)", "vang": "var(--vang)",
                  "nhan": "var(--nhan)"}.get(sac)
        elif sac != "xam":
            kq = {"xanh": "rgba(74,222,128,.35)", "do": "rgba(248,113,113,.35)",
                  "vang": "rgba(251,191,36,.35)", "nhan": "rgba(108,156,255,.35)"}.get(sac)
    _MAU_CACHE[khoa] = kq
    return kq


def doi_mau_viet_cung(html):
    """Chuyen mau viet cung trong HTML/CSS cua trang sang bien mau (xem tren)."""
    if not html or "#" not in html:
        return html

    def _thay(m):
        moi = _mau_moi(m.group(1), m.group(3))
        return m.group(0) if moi is None else m.group(1) + m.group(2) + moi
    html = _RE_MAU.sub(_thay, html)
    # Chu TRANG tren nen vua bi doi sang bien (vd tab dang chon: nen xanh
    # toi + chu trang) -> o nen sang thanh chu trang tren nen xanh nhat, mat
    # chu. Trong CUNG khoi CSS / thuoc tinh style, doi chu trang -> --chu.
    return _RE_KHOI.sub(_sua_chu_trang, html)


_RE_KHOI = __import__("re").compile(r'\{[^{}]*\}|style="[^"]*"|style=\'[^\']*\'')
_RE_CHU_TRANG = __import__("re").compile(r'(?<![\w-])color(\s*:\s*)#(?:fff|ffffff|FFF|FFFFFF)\b')
_RE_NEN_BIEN = __import__("re").compile(r'(?<![\w-])background(?:-color)?\s*:\s*var\(--')


_RE_NEN_CUNG = __import__("re").compile(
    r'(?<![\w-])background(?:-color)?\s*:\s*(?:#|rgb|linear-gradient|radial-gradient)')


def _sua_chu_trang(m):
    """
    Chu TRANG (#fff) chi giu khi CUNG khoi co nen mau dac viet cung (nut xanh,
    nut do...) - chu trang tren nen do van doc duoc o ca 2 nen. Con lai (chu
    trang dung tren nen toi cua trang, hoac tren nen vua doi sang bien) thi
    doi sang --chu, neu khong o nen sang se thanh chu trang tren nen trang.
    """
    k = m.group(0)
    if "#f" not in k.lower() or _RE_NEN_CUNG.search(k):
        return k
    return _RE_CHU_TRANG.sub(lambda x: "color" + x.group(1) + "var(--chu)", k)


# ---------------------------------------------------------------- icon SVG
#
# Icon net mat (SVG noi tuyen, ve bang duong vien) thay cho emoji tren menu.
# Emoji tren Pi OS Lite co cai thieu font (xem ghi chu U+23FB o tren), lai
# moi cai mot mau loe loet. SVG thi luon hien dung, theo mau chu, va KHONG
# can tai gi tu Internet (Pi mang ra hien truong co the khong co mang).
_SVG = {
 "home": '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
 "radar": '<circle cx="12" cy="12" r="2"/><path d="M16.2 7.8a6 6 0 010 8.4M7.8 16.2a6 6 0 010-8.4M19 5a10 10 0 010 14M5 19A10 10 0 015 5"/>',
 "wifi": '<path d="M2 8.5a15 15 0 0120 0M5 12a10 10 0 0114 0M8.5 15.5a5 5 0 017 0"/><circle cx="12" cy="19" r="1"/>',
 "bt": '<path d="M7 7l10 10-5 4V3l5 4L7 17"/>',
 "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 010 18M12 3a14 14 0 000 18"/>',
 "plug": '<path d="M9 2v5M15 2v5M6 7h12v4a6 6 0 01-12 0zM12 17v5"/>',
 "list": '<path d="M8 6h13M8 12h13M8 18h13"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/>',
 "term": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 9l3 3-3 3M13 15h4"/>',
 "kbd": '<rect x="2" y="6" width="20" height="12" rx="2"/><path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M7 14h10"/>',
 "key": '<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M17 6l3 3"/>',
 "link": '<path d="M10 14a4 4 0 005.7 0l3-3a4 4 0 00-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 00-5.7 0l-3 3a4 4 0 005.7 5.7l1-1"/>',
 "net": '<rect x="9" y="3" width="6" height="5" rx="1"/><rect x="3" y="16" width="6" height="5" rx="1"/><rect x="15" y="16" width="6" height="5" rx="1"/><path d="M12 8v4M6 16v-2h12v2"/>',
 "disk": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="2.5"/>',
 "box": '<path d="M3 7l9-4 9 4-9 4-9-4z"/><path d="M3 7v10l9 4 9-4V7M12 11v10"/>',
 "save": '<path d="M5 3h11l3 3v15H5z"/><path d="M8 3v5h7V3M8 21v-7h8v7"/>',
 "book": '<path d="M4 4h6a3 3 0 013 3v13a2 2 0 00-2-2H4zM20 4h-6a3 3 0 00-3 3v13a2 2 0 012-2h7z"/>',
 "log": '<path d="M6 3h9l4 4v14H6z"/><path d="M9 11h7M9 15h7M9 7h4"/>',
 "bolt": '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
 "tv": '<rect x="3" y="5" width="18" height="12" rx="2"/><path d="M8 21h8M12 17v4"/>',
 "chat": '<path d="M21 12a8 8 0 01-11.6 7.1L3 21l1.9-6.4A8 8 0 1121 12z"/>',
 "set": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M2 12h3M19 12h3M4.9 19.1L7 17M17 7l2.1-2.1"/>',
 "doc": '<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5"/>',
 "search": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
 "back": '<path d="M15 6l-6 6 6 6"/>',
 "menu": '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
 "pow": '<path d="M12 3v9"/><path d="M6.3 7a8 8 0 1011.4 0"/>',
 "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
 "moon": '<path d="M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z"/>',
 "pc": '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
 "hand": '<path d="M8 13V5a2 2 0 014 0v6M12 11V4a2 2 0 014 0v7M16 11V6a2 2 0 014 0v8a8 8 0 01-8 8h-1a7 7 0 01-6-3.4L3 15a2 2 0 013.4-2L8 15"/>',
 "refresh": '<path d="M20 11a8 8 0 10-2.3 5.7M20 4v7h-7"/>',
 "win": '<path d="M3 5l8-1v8H3zM13 3.8L21 3v9h-8zM3 13h8v8l-8-1zM13 13h8v8l-8-1z"/>',
 "warn": '<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.01"/>',
 "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.01"/>',
 "usb": '<path d="M12 2v15M8 6l4-4 4 4"/><circle cx="12" cy="19" r="2.5"/><path d="M12 12l-5-3V7M12 14l5-3V9"/>',
 "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
 "temp": '<path d="M14 14.8V4a2 2 0 00-4 0v10.8a4 4 0 104 0z"/>',
 "go": '<path d="M5 12h14M13 6l6 6-6 6"/>',
 "send": '<path d="M4 12l16-8-6 16-3-7z"/><path d="M11 13l9-9"/>',
 "plus": '<path d="M12 5v14M5 12h14"/>',
 "x": '<path d="M6 6l12 12M18 6L6 18"/>',
 "chip": '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
}

# Icon cho tung muc menu (theo duong dan). Muc nao khong co thi dung "doc".
ICON_MUC = {
    "/": "home", "nhom:Kết nối Console System": "radar", "/wifi": "wifi", "/bluetooth": "bt",
    "/remote": "globe", "nhom:Quản lý và kết nối thiết bị": "plug", "nhom:System Utilities": "net", "/phien": "list",
    "/console": "term", "/terminal": "kbd", "/ssh": "key", "/direct": "link", "/deployos/trienkhai": "send", "nhom:Quản lý máy trạm": "pc", "/uem": "home", "/uem/may": "pc", "/uem/phan-mem": "box",
    "/uem/bao-mat": "key", "/uem/trien-khai": "send", "/uem/profiles": "list", "/uem/bao-cao": "doc", "/uem/quan-tri": "set", "/kho-trung-tam": "box",
    "/nettools": "net", "/deployos": "disk", "nhom:Kho lưu trữ": "box",
    "/storage": "save", "/commands": "book", "/logs": "log", "/power": "pow",
    "/giaitri": "tv", "/gopy": "chat", "nhom:Cài đặt": "set", "/settings": "set",
    "/docs": "doc",
}


def svg_icon(ten, lop="i"):
    """1 icon SVG net mat (xem _SVG). Dung chung cho cac trang khac."""
    return f'<svg class="{lop}" viewBox="0 0 24 24" aria-hidden="true">{_SVG.get(ten, _SVG["doc"])}</svg>'


# Cac trang CON (khong nam tren menu) - them vao o tim nhanh de go la thay.
# (nhan, duong dan, nhom, tu khoa them)
TIM_THEM = [
    ("SSH / Telnet (phiên mới)", "/phien#moi", "Phiên kết nối", "ssh telnet ket noi thiet bi"),
    ("Terminal máy này", "/phien?mo=local", "Phiên kết nối", "terminal shell dong lenh may nay"),
    ("Thư viện lệnh trong phiên", "/phien?thuvien=1", "Phiên kết nối", "lenh co san gui tap lenh"),
    ("Kịch bản cài Windows", "/deployos/kichban", "Deployment OS", "pxe win cai dat"),
    ("Tạo kịch bản mới", "/deployos/wizard/bat-dau?che_do=chay", "Deployment OS", "wizard cai windows"),
    ("Ổ đĩa đã dò", "/deployos/o-dia", "Deployment OS", "disk o cung"),
    ("Hệ điều hành (bộ cài)", "/deployos/os", "Deployment OS", "iso wim windows"),
    ("Phần mềm cài kèm", "/deployos/console/apps", "Deployment OS", "app office"),
    ("Ứng dụng nhiều file", "/deployos/ungdung", "Deployment OS", "app"),
    ("Font chữ", "/deployos/font", "Deployment OS", "font"),
    ("Driver theo dòng máy", "/deployos/drivers", "Deployment OS", "driver model"),
    ("Script", "/deployos/console/scripts", "Deployment OS", "script cmd ps1"),
    ("WinPE / file boot", "/deployos/console", "Deployment OS", "winpe boot"),
    ("Kho trung tâm", "/kho-trung-tam", "Kho lưu trữ", "kho tai ve phan mem os iso"),
    ("Máy đang cài", "/deployos/tiendo", "Deployment OS", "tien trinh tien do"),
    ("Lịch sử cài đặt", "/deployos/lichsu", "Deployment OS", "lich su csv"),
    ("Bật / Tắt PXE", "/deployos/caidat", "Deployment OS", "pxe dhcp tftp"),
    ("Kiểm tra sẵn sàng", "/deployos/caidat/hatang", "Deployment OS", "san sang ha tang kiem tra"),
    ("Bật máy từ xa (Wake-on-LAN)", "/deployos/caidat/wol", "Deployment OS", "wol wake danh thuc"),
    ("ARP Scan", "/nettools/arp-scan", "Network Tools", "quet thiet bi"),
    ("Ping / Traceroute", "/nettools/ping", "Network Tools", "ping"),
    ("PCAP Capture", "/nettools/pcap", "Network Tools", "bat goi tshark"),
    ("LLDP / CDP Discovery", "/nettools/lldp", "Network Tools", "lldp cdp switch"),
    ("Kiểm tra cổng mạng", "/nettools/dhcp-test", "Network Tools", "dhcp poe toc do"),
    ("STP / LACP / VLAN Scan", "/nettools/l2-scan", "Network Tools", "stp vlan"),
    ("MTU Discovery", "/nettools/mtu", "Network Tools", "mtu"),
    ("Kiểm tra DNS", "/nettools/dns-check", "Network Tools", "dns"),
    ("Kiểm tra chứng chỉ TLS", "/nettools/tls-check", "Network Tools", "tls ssl https"),
    ("Sơ đồ mạng 1 đoạn", "/nettools/topology", "Network Tools", "topology so do"),
    ("Máy chủ TFTP", "/nettools/tftp", "Network Tools", "tftp"),
    ("Sao lưu qua cáp console", "/nettools/console-backup", "Network Tools", "backup"),
    ("Netmiko Config", "/nettools/netmiko", "Network Tools", "netmiko ssh cau hinh"),
    ("802.1X Testing", "/nettools/dot1x", "Network Tools", "dot1x radius"),
    ("IF/THEN Automation", "/nettools/ifthen", "Network Tools", "ifthen rule"),
    ("Sao lưu cấu hình", "/settings/sao-luu", "Cài đặt", "backup sao luu"),
    ("Cập nhật", "/cap-nhat", "Cài đặt", "cap nhat update phien ban nang cap ha cap"),
    ("Đăng xuất", "/logout", "Tài khoản", "logout thoat"),
]


def che_do_giao_dien():
    """
    'pc' hoac 'cu' (cam ung). Lua chon nho bang cookie RIENG TUNG MAY (tung
    trinh duyet) - doi tren laptop khong lam doi man hinh RasPad.
    Chua chon bao gio: man hinh gan tren Pi (cong 8880, xem auth) -> cam ung,
    con lai (laptop/PC vao qua mang) -> PC.
    """
    try:
        from flask import request
        c = request.cookies.get("cs_che_do")
        if c in ("pc", "cu"):
            return c
        from ui.auth import _is_local_screen
        return "cu" if _is_local_screen() else "pc"
    except Exception:
        return "pc"


def nen_giao_dien(che_do=None):
    """'sang' / 'toi'. Mac dinh: cam ung -> sang (doc ro ngoai troi), PC -> toi."""
    try:
        from flask import request
        c = request.cookies.get("cs_nen")
        if c in ("sang", "toi"):
            return c
    except Exception as _loi:
        _bo_qua(_loi)
    return "sang" if (che_do or che_do_giao_dien()) == "cu" else "toi"


def _duong_hien_tai(mac_dinh="/"):
    try:
        from flask import request
        p = request.full_path if request.query_string else request.path
        return p or mac_dinh
    except Exception:
        return mac_dinh


def _link_doi(**kv):
    from urllib.parse import urlencode
    kv["next"] = _duong_hien_tai()
    return "/giaodien?" + urlencode(kv)


def _ds_tim_nhanh():
    """Danh sach cho o tim nhanh: moi muc menu + cac trang con o TIM_THEM."""
    import json as _json
    ds = []
    for muc in NAV_ITEMS:
        if muc[0] != "nhom":
            ds.append([muc[1], muc[0], "Menu", ""])
        else:
            for h, l, _i in muc[3]:
                ds.append([l, h, muc[1], ""])
    for nhan, href, nhom, tk in TIM_THEM:
        ds.append([nhan, href, nhom, tk])
    return _json.dumps(ds, ensure_ascii=False).replace("</", "<\\/")


def gan_phien_tmux(html, session):
    """Bao ban phim ao (vkeyboard.js) go phim vao phien tmux nao: them data-tmux-session vao the <body ...>.
    LOI DA GAP (21/10/2026, anh Thoai: bam vao Console/SSH tren man hinh cam ung khong thay ban phim ao du da bat):
    truoc day cac trang dung html.replace("<body>", ...) - tu khi giao dien moi co chu thich CSS chua chu "<body>"
    (khop dau tien) va the that mang class cd-*/nen-*, thuoc tinh KHONG bao gio vao the that, vkeyboard.js khong biet
    day la trang terminal."""
    ra, n = _re.subn(r'<body(?=\s+class="cd-)', f'<body data-tmux-session="{session}"', html, count=1)
    if n:
        return ra
    # Khong tim thay the <body class="cd-..."> that: KHONG dung "<body>" dau tien (co the nam trong chu thich CSS)
    # ma tim the <body> dung ngay truoc noi dung, o cuoi phan <head>.
    return _re.sub(r"(</head>\s*)<body>", lambda m: m.group(1) + f'<body data-tmux-session="{session}">', html, count=1)


def render_page(body_html, active="/", title=TEN_NGAN, subtitle="", extra_css="", an_tieu_de=False):
    if active == "/deployos":        # o muc Trien khai phan mem (cac trang dung chung voi Deployment OS) thi sang muc do
        try:
            from flask import session as _ss
            if _ss.get("nc") == "tk":
                active = "/deployos/trienkhai"
                if title == "Deployment OS":
                    title = "Triển khai phần mềm LAN"
        except Exception as _loi:
            _bo_qua(_loi)
    """
    Dung 1 trang hoan chinh voi khung chung.
      body_html : phan noi dung rieng cua trang (chuoi HTML da render xong)
      active    : duong dan de to sang muc menu tuong ung
    Cung 1 HTML cho ca Che do PC va Che do cam ung - lop tren <body> quyet
    dinh cach bay (xem phan "GIAO DIEN 2 CHE DO" trong BASE_CSS).
    """
    chips = get_status_chips()
    che_do = che_do_giao_dien()
    try:                                  # chuong bao co ban cap nhat moi (chi doc trang thai da luu; xem core/capnhat/may.py)
        from consolesystem.core.capnhat.may import co_ban_moi_nhanh
        chuong_html = ('<a href="/cap-nhat" class="btn" title="Có bản cập nhật mới - bấm để xem" style="position:relative">🔔'
                       '<span style="position:absolute;top:2px;right:2px;width:9px;height:9px;border-radius:50%;background:#F87171"></span></a>') if co_ban_moi_nhanh() else ""
    except Exception:
        chuong_html = ""
    body_html = doi_mau_viet_cung(body_html)
    extra_css = doi_mau_viet_cung(extra_css)
    nen = nen_giao_dien(che_do)

    chips_html = ""
    for idx, c in enumerate(chips):
        cls = "up" if c["up"] else "down"
        # O thu 3 tro di (Bluetooth, Cloudflare) an bot tren man hep
        phu = " phu" if idx >= 2 else ""
        chips_html += (
            f'<div class="chip {cls}{phu}" data-chip="{idx}" title="{c["extra"]}"><div class="k"><span class="kt"><span class="kl">{c["key"].split(" (")[0]}</span><span class="kd">{(" (" + c["key"].split(" (", 1)[1]) if " (" in c["key"] else ""}</span></span></div>'
            f'<div class="v">{c["val"]}</div><div class="x">{c["extra"]}</div></div>'
        )

    def _dang_mo(href):
        """'/' chi sang khi khop tuyet doi; cac muc khac sang khi la tien to."""
        if href == "/deployos" and active.startswith("/deployos/trienkhai"):
            return False                      # dang o Trien khai phan mem: khong sang them muc Deployment OS
        return (active == href) if href in ("/", "/uem") else active.startswith(href)

    def _ve_muc(href, label, icon):
        return (f'<a href="{href}" class="{"active" if _dang_mo(href) else ""}" '
                f'title="{label}">'
                f'<span class="ic">{svg_icon(ICON_MUC.get(href, "doc"))}</span><span class="nl">{label}</span></a>')

    nav_html = '<span class="ind" id="nav-ind" aria-hidden="true"></span>'
    o_to_html = ""          # menu o to cua Che do cam ung
    for muc in NAV_ITEMS:
        if muc[0] != "nhom":
            nav_html += _ve_muc(*muc)
            o_to_html += (f'<a class="o-to{" on" if _dang_mo(muc[0]) else ""}" href="{muc[0]}">'
                          f'<span class="bi">{svg_icon(ICON_MUC.get(muc[0], "doc"))}</span><b>{muc[1]}</b></a>')
            continue
        _, ten_nhom, icon_nhom, cac_con = muc
        co_act = any(_dang_mo(c[0]) for c in cac_con)
        nav_html += (f'<div class="gr" data-g="{ten_nhom}"><button type="button" class="ngr gh" aria-expanded="true" title="{ten_nhom}">'
                     f'<span class="gt">{ten_nhom}</span><svg class="chev" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" '
                     f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg></button>'
                     f'<div class="gc"><div>' + "".join(_ve_muc(*c) for c in cac_con) + '</div></div></div>')
        for h, l, _i in cac_con:
            o_to_html += (f'<a class="o-to{" on" if _dang_mo(h) else ""}" href="{h}">'
                          f'<span class="bi">{svg_icon(ICON_MUC.get(h, "doc"))}</span><b>{l}</b><small>{ten_nhom}</small></a>')

    # Nut ve trang chu - khong hien khi dang O trang chu (ve chinh no thi vo ich).
    # Che do cam ung an nut nay vi thanh duoi da co "Trang chu".
    nut_home = ("" if active == "/" else
                '<a href="/" class="nut-home" title="Về trang chủ" '
                f'aria-label="Về trang chủ">{svg_icon("home")}</a>')

    if che_do == "cu":
        nut_doi_cd = (f'<a href="{_link_doi(che_do="pc")}" class="btn doi-cd" '
                      f'title="Chuyển sang giao diện laptop / PC">{svg_icon("pc")}<span class="nl-nut"> Chế độ PC</span></a>')
    else:
        nut_doi_cd = (f'<a href="{_link_doi(che_do="cu")}" class="btn doi-cd" '
                      f'title="Chuyển sang giao diện cảm ứng (ô to, thanh dưới)">{svg_icon("hand")}<span class="nl-nut"> Chế độ cảm ứng</span></a>')
    if nen == "sang":
        nut_nen = (f'<a href="{_link_doi(nen="toi")}" class="btn gray" title="Chuyển nền tối">'
                   f'{svg_icon("moon")}<span class="nl-nen">Tối</span></a>')
    else:
        nut_nen = (f'<a href="{_link_doi(nen="sang")}" class="btn gray" title="Chuyển nền sáng">'
                   f'{svg_icon("sun")}<span class="nl-nen">Sáng</span></a>')

    dock_html = (
        f'<nav class="dock" aria-label="Điều hướng">'
        f'<a href="/" class="{"on" if active == "/" else ""}">{svg_icon("home")}Trang chủ</a>'
        f'<a href="/" onclick="if(history.length>1){{history.back();return false;}}">{svg_icon("back")}Quay lại</a>'
        f'<a href="#cs-menu" data-tim="1">{svg_icon("search")}Tìm</a>'
        f'<a href="#cs-menu">{svg_icon("menu")}Menu</a>'
        f'<a href="/power" class="{"on" if active.startswith("/power") else ""}">{svg_icon("pow")}Nguồn</a>'
        f'</nav>')

    menu_cu = (
        f'<div class="menu-cu" id="cs-menu">'
        f'<div class="dau"><b>Tất cả chức năng</b>'
        f'<a href="#" class="btn gray" onclick="if(history.length>1&&location.hash==\'#cs-menu\'){{history.back();return false;}}">Đóng</a></div>'
        f'<div class="luoi">{o_to_html}</div></div>')

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} - {TEN_NGAN}</title>
<link rel="icon" href="/favicon.ico">
<style>{BASE_CSS}
{extra_css}</style>
</head>
<body class="cd-{che_do} nen-{nen}">
<div class="wrap">
  <div class="side">
    <div class="brand">
      <a href="/" class="blogo" title="Console System - zTieuYeuz"><img src="/thuong-hieu/logo-mark.svg" alt=""></a>
      <span class="bten">{TEN_HE_THONG}<small>by <b class="zt"><i>z</i>TieuYeu<i>z</i></b></small></span>
      <button type="button" id="nut-thu" class="thu"
              title="Thu gọn / mở rộng thanh menu">&raquo;</button>
    </div>
    <div class="nav">{nav_html}</div>
    <div class="foot">
      <a href="/logout">Đăng xuất</a>
      <div style="font-size:11px;color:var(--chu-mo2);margin-top:6px;">&copy; 2026{_DAU_AN} <b style="color:var(--chu-mo);"><span style="color:#22D3EE;">z</span>TieuYeu<span style="color:#22D3EE;">z</span></b></div>
    </div>
  </div>
  <div class="main">
    <div class="top status">
      <a href="/" class="ten-cu"><img src="/thuong-hieu/logo-mark.svg" alt="">Console System</a>
      <button type="button" class="tim" id="mo-tim" title="Tìm nhanh chức năng (Ctrl+K)">{svg_icon("search")}<span class="tim-chu">Tìm chức năng…</span><kbd>Ctrl&nbsp;K</kbd></button>
      <div class="chips">{chips_html}</div>
      <div class="spacer"></div>
      <div class="act">
        {chuong_html}<a href="{_duong_hien_tai(active)}" class="btn gray" title="Làm mới trang">{svg_icon("refresh")}</a>
        {nut_nen}
        {nut_doi_cd}
      </div>
    </div>
    <div class="content">
      {"" if an_tieu_de else f"<h1>{title}</h1>"}
      {f'<p class="sub">{subtitle}</p>' if (subtitle and not an_tieu_de) else ''}
      {body_html}
    </div>
  </div>
</div>
{nut_home}
{dock_html}
{menu_cu}
<div class="tim-nhanh" id="tim-nhanh" role="dialog" aria-label="Tìm nhanh"><div class="h">
  <form id="tim-form" action="/" method="get" role="search">
  <input type="search" id="tim-o" placeholder="Gõ để tìm… ví dụ: pxe, wol, console, wifi" autocomplete="off">
  </form>
  <ul id="tim-ds"></ul>
</div></div>
<script>
/* Thu gon / mo rong thanh menu ben trai (Che do PC).
   Nho lua chon vao localStorage de giu nguyen khi chuyen trang. */
(function() {{
  var KN = 'consolepi-menu-nhom', dong = {{}};
  try {{ dong = JSON.parse(localStorage.getItem(KN) || '{{}}') || {{}}; }} catch (e) {{}}
  document.querySelectorAll('.nav .gr').forEach(function(g) {{
    var id = g.getAttribute('data-g'), b = g.querySelector('.gh');
    if (dong[id] && !g.querySelector('a.active')) g.classList.add('dong');
    b.setAttribute('aria-expanded', g.classList.contains('dong') ? 'false' : 'true');
    b.addEventListener('click', function() {{
      var d = g.classList.toggle('dong'); b.setAttribute('aria-expanded', d ? 'false' : 'true'); dong[id] = d;
      try {{ localStorage.setItem(KN, JSON.stringify(dong)); }} catch (e) {{}}
      setTimeout(function() {{ if (window.csNavInd) window.csNavInd(); }}, 340);
    }});
  }});
  requestAnimationFrame(function() {{ document.body.classList.add('nav-ready'); }});
}})();
(function() {{
  var K = 'consolepi-menu-thu-gon', mq = matchMedia('(max-width:1100px)');
  /* Chua tung chon thi tu thu gon thanh menu khi man hinh hep (<1100px), mo lai khi rong */
  function tuDong() {{
    var v = null; try {{ v = localStorage.getItem(K); }} catch (e) {{}}
    if (v === '1') document.body.classList.add('thu-gon');
    else if (v === '0') document.body.classList.remove('thu-gon');
    else document.body.classList.toggle('thu-gon', mq.matches);
  }}
  tuDong();
  if (mq.addEventListener) mq.addEventListener('change', function() {{ tuDong(); if (window.csNavInd) setTimeout(window.csNavInd, 340); }});
  var n = document.getElementById('nut-thu');
  if (!n) return;
  function veLai() {{
    var gon = document.body.classList.contains('thu-gon');
    n.innerHTML = gon ? '&laquo;' : '&raquo;';
  }}
  veLai();
  n.addEventListener('click', function() {{
    var gon = document.body.classList.toggle('thu-gon');
    try {{ localStorage.setItem(K, gon ? '1' : '0'); }} catch (e) {{}}
    veLai();
  }});
}})();
/* Thanh tren: tu co gian cac chip trang thai theo cho trong thuc te. */
(function() {{
  var top = document.querySelector('.top'), cs = top && top.querySelector('.chips');
  if (!top || !cs) return;
  function tran() {{
    var tong = 0, n = 0;
    cs.querySelectorAll('.chip').forEach(function(c) {{ if (c.offsetParent) {{ tong += c.offsetWidth; n++; }} }});
    return tong + Math.max(0, n - 1) * 7 > cs.clientWidth + 1;
  }}
  var cho = 0;
  function vua() {{
    top.classList.remove('f1', 'f2', 'f3');
    /* Khong bao gio bo chip: bo (ten card) -> thu nho -> xuong dong rieng. Luon thay LAN / WiFi / Bluetooth / Cloudflare. */
    if (tran()) top.classList.add('f1');
    if (tran()) top.classList.add('f2');
    if (tran()) {{ top.classList.remove('f1', 'f2'); top.classList.add('f3'); }}
  }}
  function hen() {{ cancelAnimationFrame(cho); cho = requestAnimationFrame(vua); }}
  vua();
  addEventListener('resize', hen);
  if (window.ResizeObserver) new ResizeObserver(hen).observe(top);
  if (window.MutationObserver) new MutationObserver(hen).observe(cs, {{ subtree: true, childList: true, characterData: true }});
  setTimeout(vua, 400);
}})();
/* Vach chon menu trai truot theo con tro (chi che do PC). */
(function() {{
  var nav = document.querySelector('.side .nav'), ind = document.getElementById('nav-ind');
  if (!nav || !ind || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var cur = nav.querySelector('a.active');
  function den(a, hov) {{
    ind.style.height = a.offsetHeight + 'px';
    ind.style.transform = 'translateY(' + a.offsetTop + 'px)';
    ind.style.opacity = 1; ind.classList.toggle('hov', !!hov);
  }}
  window.csNavInd = function() {{ var a = nav.querySelector('a.active'); if (a && a.offsetParent) {{ den(a, false); }} }};
  document.body.classList.add('ind-on');
  if (cur) {{ ind.style.transition = 'none'; den(cur, false);
    requestAnimationFrame(function() {{ ind.style.transition = ''; }}); }}
  nav.querySelectorAll('a').forEach(function(a) {{
    a.addEventListener('pointerenter', function() {{ den(a, a !== cur); }});
  }});
  nav.addEventListener('pointerleave', function() {{ if (cur) den(cur, false); else ind.style.opacity = 0; }});
  var n = document.getElementById('nut-thu');
  if (n) n.addEventListener('click', function() {{ setTimeout(function() {{ if (cur) den(cur, false); }}, 30); }});
  addEventListener('resize', function() {{ if (cur) den(cur, false); }});
}})();
/* Tim nhanh: Ctrl+K (PC) hoac nut "Tim" o thanh duoi (cam ung).
   Go khong dau van tim duoc ("cai dat" ra "Cài đặt"). JS loi thi nut Tim
   van mo menu o to (#cs-menu) - khong bao gio thanh nut chet. */
(function() {{
  var DS = {_ds_tim_nhanh()};
  var hop = document.getElementById('tim-nhanh'), o = document.getElementById('tim-o'),
      ul = document.getElementById('tim-ds'), chon = 0, kq = [];
  if (!hop || !o || !ul) return;
  function bo(s) {{ return (s || '').normalize('NFD').replace(/[\\u0300-\\u036f]/g, '')
      .replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase(); }}
  function ve() {{
    var q = bo(o.value).trim(), tu = q.split(/\\s+/).filter(Boolean);
    kq = DS.filter(function(d) {{
      var t = bo(d[0] + ' ' + d[2] + ' ' + d[3] + ' ' + d[1]);
      return tu.every(function(w) {{ return t.indexOf(w) >= 0; }});
    }}).slice(0, 40);
    if (chon >= kq.length) chon = 0;
    ul.innerHTML = '';
    if (!kq.length) {{ ul.innerHTML = '<li class="rong">Không thấy chức năng nào khớp.</li>'; return; }}
    kq.forEach(function(d, i) {{
      var li = document.createElement('li'), a = document.createElement('a');
      a.href = d[1]; if (i === chon) a.className = 'sel';
      a.appendChild(document.createTextNode(d[0]));
      var sm = document.createElement('small'); sm.textContent = d[2]; a.appendChild(sm);
      li.appendChild(a); ul.appendChild(li);
    }});
  }}
  function mo() {{ hop.classList.add('on'); o.value = ''; chon = 0; ve(); setTimeout(function() {{ o.focus(); }}, 20); }}
  function dong() {{ hop.classList.remove('on'); }}
  var nt = document.getElementById('mo-tim'); if (nt) nt.addEventListener('click', mo);
  document.querySelectorAll('[data-tim]').forEach(function(a) {{
    a.addEventListener('click', function(e) {{ e.preventDefault(); mo(); }});
  }});
  o.addEventListener('input', function() {{ chon = 0; ve(); }});
  /* Phim Enter cua ban phim THAT va phim ↵ cua BAN PHIM AO (vkeyboard.js goi
     requestSubmit cua form) deu di qua day -> mo ket qua dang chon. */
  var fm = document.getElementById('tim-form');
  if (fm) fm.addEventListener('submit', function(e) {{
    e.preventDefault();
    if (kq[chon]) location.href = kq[chon][1];
  }});
  o.addEventListener('keydown', function(e) {{
    if (e.key === 'ArrowDown') {{ chon = Math.min(chon + 1, kq.length - 1); ve(); e.preventDefault(); }}
    else if (e.key === 'ArrowUp') {{ chon = Math.max(chon - 1, 0); ve(); e.preventDefault(); }}
  }});
  hop.addEventListener('click', function(e) {{ if (e.target === hop) dong(); }});
  document.addEventListener('keydown', function(e) {{
    if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {{ e.preventDefault(); mo(); }}
    else if (e.key === 'Escape') dong();
  }});
}})();
</script>
<script src="/dashboard.js"></script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Boc lai trang cu vao khung moi
#
# 9 cong cu trong goi nettools/ duoc viet truoc khi co khung giao dien chung,
# moi cai tu dung <html> rieng. Thay vi sua 9 file (nhieu rui ro), ham nay
# boc lai phan noi dung cua chung vao khung chung - 1 diem sua duy nhat,
# va cong cu moi them sau nay cung tu dong duoc boc.
# ---------------------------------------------------------------------------
import re as _re

_BODY_RE = _re.compile(r"<body[^>]*>(.*?)</body>", _re.S | _re.I)
_STYLE_RE = _re.compile(r"<style[^>]*>(.*?)</style>", _re.S | _re.I)
_TITLE_RE = _re.compile(r"<title[^>]*>(.*?)</title>", _re.S | _re.I)
_H1_RE = _re.compile(r"<h1[^>]*>.*?</h1>", _re.S | _re.I)
# Dong "← Network Tools" / "← Quay lai Dashboard" - da thua vi co thanh trai
_BACKLINK_RE = _re.compile(r"<p>\s*<a href=\"/(?:nettools)?\"[^>]*>←[^<]*</a>\s*</p>", _re.I)


def _nut_quay_ve():
    """
    Nut "Quay lai Network Tools" cho cac trang cong cu.

    LY DO THAT (anh Thoai 19/09/2026: "khi anh nhap vao 1 chuc nang nao do
    anh muon quay ve thi no thieu nut quay ve"): truoc day khung chung XOA
    dong quay lai cua tung trang di, voi ly do "da co thanh menu ben trai
    nen thua". Nhung thanh menu trai chi co muc "Network Tools" chung -
    dang o trong 1 cong cu (vd Kiem tra DNS) muon ve danh sach cong cu thi
    phai bam vao muc do roi no nap lai trang, hoac bam Back cua trinh
    duyet. Tren man hinh cam ung khong co phim Back, va thanh menu co the
    dang bi thu gon - luc do that su khong co duong ve.

    Nay chen mot nut CHUAN o dau moi trang cong cu, thay cho cac dong quay
    lai viet tay moi trang mot kieu truoc day. Trang danh sach cong cu thi
    khong chen (khong ai can nut quay ve chinh no).
    """
    try:
        from flask import request
        duong = (request.path or "").rstrip("/")
    except Exception:
        return ""                      # ngoai ngu canh request thi bo qua
    if duong in ("", "/nettools"):
        return ""
    return ('<p style="margin:12px 0 20px;">'
            '<a class="btn gray small" href="/nettools">'
            '&larr; Tất cả công cụ mạng</a></p>')


_THE_TRAN = {"h1", "h2", "h3", "table", "th", "td", "tr", "input", "select", "textarea",
             "button", "pre", "label", "code", "a", "p"}


def _chi_the_tran(sel):
    """
    Bo chon CHI gom the HTML tran (vd 'th', 'input[type=text], select',
    'button:hover'). Trang cu tu to mau cho cac the nay (nut xanh la, chu
    tieu de xanh la, o nhap nen #333) - giu lai thi trang cong cu lech
    han phong cach chung va vo o nen sang. Bo di de khung chung lo.
    Bo chon co class/id (.card, #kq...) thi GIU - do la phan rieng cua trang.
    """
    for phan in sel.split(","):
        p = phan.strip()
        if _re.match(r"^(a|button)?\.btn(:[\w-]+)?$", p):
            continue          # nut .btn: khung chung da co kieu (ca sang/toi)
        goc = _re.split(r"[\[:\s>+~]", p, 1)[0]
        if not goc or goc not in _THE_TRAN or "." in p or "#" in p:
            return False
    return True


def wrap_legacy_html(html, active="/nettools"):
    """Boc 1 trang HTML hoan chinh (kieu cu) vao khung giao dien chung."""
    m = _BODY_RE.search(html)
    if not m:
        return html                      # khong nhan dang duoc thi de nguyen

    body = m.group(1)

    title = "Network Tools"
    tm = _TITLE_RE.search(html)
    if tm:
        title = tm.group(1).split(" - ")[0].strip()

    # Bo <h1> va link quay lai cu (khung moi da co tieu de + thanh dieu huong)
    body = _H1_RE.sub("", body, count=1)
    # Bo dong "<- Network Tools" cu cua tung trang (moi trang viet mot kieu,
    # cho tren cho duoi khong dong nhat) roi CHEN LAI mot nut chuan o ngay
    # dau trang - xem _nut_quay_ve() ben duoi.
    body = _BACKLINK_RE.sub("", body, count=1)
    body = _nut_quay_ve() + body

    # Giu lai CSS rieng cua trang do (vd bang mau, pre...), nhung bo phan
    # dinh dang body/nen vi khung chung da lo
    css = ""
    for sm in _STYLE_RE.finditer(html):
        for rule in sm.group(1).split("}"):
            sel = rule.split("{")[0].strip()
            if sel and not sel.startswith(("body", "html", "a ", "a{", "a:")) \
                    and not _chi_the_tran(sel):
                # Gioi han CSS cu trong vung noi dung (.content): trang cu co
                # quy tac nhu "a.btn {nen xanh la}" / ".chip {...}" trung ten
                # voi nut va o trang thai cua thanh tren -> lam meo thanh tren.
                than = rule.split("{", 1)[1]
                sel_moi = ", ".join(".content " + p.strip() for p in sel.split(",") if p.strip())
                css += sel_moi + " {" + than + "}\n"

    return render_page(body, active=active, title=title, extra_css=css)


def register_giaodien(app):
    """
    /giaodien?che_do=pc|cu&nen=sang|toi&next=/duong-dan
    Luu lua chon vao cookie cua RIENG trinh duyet nay roi quay lai trang cu.
    Dung link thuong (khong can JS) nen nut doi che do luon bam duoc.
    """
    from flask import request, redirect

    @app.route("/giaodien")
    def doi_giao_dien():
        nxt = request.args.get("next", "/") or "/"
        # Chi cho quay ve duong dan NOI BO - chan chuyen huong ra ngoai
        if not nxt.startswith("/") or nxt.startswith("//") or nxt.startswith("/\\"):
            nxt = "/"
        r = redirect(nxt)
        nam = 3600 * 24 * 365
        cd = request.args.get("che_do")
        if cd in ("pc", "cu"):
            r.set_cookie("cs_che_do", cd, max_age=nam, samesite="Lax", httponly=True)
        nen = request.args.get("nen")
        if nen in ("sang", "toi"):
            r.set_cookie("cs_nen", nen, max_age=nam, samesite="Lax", httponly=True)
        return r
