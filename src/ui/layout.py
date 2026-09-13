"""
Console Pi - Khung giao dien dung chung (thanh dieu huong trai + noi dung phai)

Moi trang trong dashboard deu goi render_page() de co cung bo cuc, thay vi
tu viet lai <html> tu dau. Thiet ke cho man hinh cam ung 1280x800:
  - Nut/muc menu du lon de cham bang ngon tay (toi thieu 44px chieu cao)
  - Thanh trang thai mang luon hien tren cung (yeu cau so 2)
  - Khong dung thu vien ngoai / CDN (Pi mang di hien truong co the khong co net)
"""
import subprocess

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
NAV_ITEMS = [
    ("/", "Tổng quan", "🏠"),

    # Cac duong ket noi VAO chinh con Pi nay
    ("nhom", "Kết nối server", "📡", [
        ("/wifi", "WiFi / AP", "📶"),
        ("/bluetooth", "Bluetooth", "🔵"),
        ("/remote", "Truy cập từ xa", "🌍"),
    ]),

    # Cac duong tu Pi ket noi RA thiet bi mang can lam viec
    ("nhom", "Kết nối thiết bị", "🔌", [
        ("/console", "Console", "🖥️"),
        ("/terminal", "Terminal server", "⌨️"),
        ("/ssh", "SSH", "🔑"),
        ("/direct", "Cắm thẳng thiết bị", "🔗"),
    ]),

    ("/nettools", "Network Tools", "🛠️"),
    ("/deployos", "Deployment OS", "💿"),

    # Noi cat du lieu de dung lai
    ("nhom", "Kho lưu trữ", "📦", [
        ("/storage", "Kho file", "💾"),
        ("/commands", "Thư viện lệnh", "📚"),
    ]),

    ("/logs", "Nhật ký lỗi", "📋"),
    ("/power", "Nguồn điện", "⚡"),
    ("/giaitri", "Giải trí", "📺"),

    ("nhom", "Cài đặt", "⚙️", [
        ("/settings", "Cài đặt chung", "⚙️"),
        ("/docs", "Tài liệu", "📖"),
    ]),
]

BASE_CSS = """
* { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
html { touch-action: manipulation; }   /* bo do tre 300ms cho tap tren man hinh cam ung */
body { margin:0; font-family: system-ui, Arial, sans-serif; background:#15171a; color:#e6e6e6; }
a { color:#4CAF50; text-decoration:none; }

/* ---- Khung tong ---- */
.wrap { display:flex; min-height:100vh; }
/* Thanh menu DINH CHET theo man hinh (position:sticky + tu cuon rieng).
   Truoc day no cuon chung voi noi dung: o trang dai (Tong quan, Tai lieu,
   Nhat ky) keo xuong mot doan la menu bien mat, muon sang tab khac phai
   keo nguoc len tan dau trang - rat vuong khi dung tablet bang ngon tay. */
.side { width:206px; flex:0 0 206px; background:#1b1e22; border-right:1px solid #2c3036;
        display:flex; flex-direction:column; position:sticky; top:0;
        height:100vh; overflow-y:auto; }
.brand { padding:14px 16px; font-size:15px; font-weight:700; color:#4CAF50;
         border-bottom:1px solid #2c3036; letter-spacing:.5px;
         display:flex; align-items:center; gap:8px; }
.brand small { display:block; color:#6b7280; font-weight:400; font-size:11px; margin-top:2px; }
.brand .bten { flex:1; min-width:0; }
/* Nut thu gon: 40px de ngon tay bam trung tren man hinh cam ung */
.brand .thu { flex:none; width:40px; height:40px; border-radius:8px; cursor:pointer;
              background:#22262b; border:1px solid #2c3036; color:#8b93a1;
              font-size:16px; line-height:1; }
.brand .thu:active { background:#2c3036; }

/* ---- Nhom muc menu (the <details> chinh chu cua trinh duyet - khong
   can JS, bung/thu chay duoc ngay ca khi JS loi) ---- */
.nav .nhom > summary { display:flex; align-items:center; gap:11px;
    padding:14px 15px; min-height:50px; color:#c9ced6; font-size:15px;
    cursor:pointer; white-space:nowrap; list-style:none;
    -webkit-user-select:none; user-select:none; }
.nav .nhom > summary::-webkit-details-marker { display:none; }
/* Mui ten chi huong mo/dong - xoay khi bung ra */
.nav .nhom > summary::after { content:"\\25B8"; margin-left:auto; font-size:12px;
    color:#6b7280; transition:transform .15s; }
.nav .nhom[open] > summary::after { transform:rotate(90deg); }
.nav .nhom > summary:active { background:#2c3036; }
.nav .nhom .con a { padding-left:34px; font-size:14.5px; min-height:46px; }
.nav .nhom .con a .ic { font-size:16px; width:20px; }

/* ---- Che do THU GON: chi con day icon ----
   Dat class tren <body> (khong phai tren .side) de CSS o day doi duoc ca
   be rong cot ben trai lan hien thi cua tung muc con. */
body.thu-gon .side { width:62px; flex:0 0 62px; }
body.thu-gon .side .nl,
body.thu-gon .side .brand .bten,
body.thu-gon .side .foot { display:none; }
body.thu-gon .side .brand { justify-content:center; padding:14px 8px; }
body.thu-gon .side .nav a,
body.thu-gon .side .nav .nhom > summary { justify-content:center; padding:14px 6px; }
body.thu-gon .side .nav .nhom > summary::after { display:none; }
/* Khi thu gon thi luon bung cac nhom ra (chi con icon nen khong chiem cho),
   neu khong cac muc con se bi giau han, khong bam vao dau duoc. */
body.thu-gon .side .nav .nhom .con a { padding-left:6px; }
/* Muc menu toi thieu 48px chieu cao (khuyen nghi cho man hinh cam ung la
   >=44px) va co hieu ung bam :active - :hover khong bao gio kich hoat tren
   cam ung nen thieu no nguoi dung khong biet minh vua cham trung hay chua.
   white-space:nowrap: truoc day "Cam thang thiet bi" bi xuong 2 dong lam
   danh sach cao thap khong deu, kho nham trung muc can bam. */
.nav a { display:flex; align-items:center; gap:11px; padding:14px 15px; min-height:50px;
         color:#c9ced6; font-size:15px; border-left:3px solid transparent;
         white-space:nowrap; -webkit-user-select:none; user-select:none; }
.nav a:hover { background:#22262b; }
.nav a:active { background:#2c3036; }
.nav a.active { background:#22262b; border-left-color:#4CAF50; color:#fff; font-weight:600; }
.nav a .ic { font-size:19px; width:25px; text-align:center; flex:none; }
.side .foot { margin-top:auto; padding:10px 16px; border-top:1px solid #2c3036;
              font-size:12px; color:#6b7280; }
.side .foot a { display:inline-block; min-height:36px; line-height:36px; }

.main { flex:1; min-width:0; display:flex; flex-direction:column; }

/* ---- Thanh trang thai mang ---- */
.status { display:flex; gap:8px; padding:10px 14px; background:#1b1e22;
          border-bottom:1px solid #2c3036; flex-wrap:wrap; align-items:stretch; }
.chip { background:#22262b; border:1px solid #2c3036; border-radius:7px;
        padding:7px 12px; min-width:172px; border-left:3px solid #4b5563; }
.chip.up { border-left-color:#4CAF50; }
.chip.down { border-left-color:#6b7280; }
.chip .k { font-size:11px; color:#8b93a1; text-transform:uppercase; letter-spacing:.4px; }
.chip .v { font-size:14px; color:#fff; font-weight:600; margin-top:2px;
           font-family:ui-monospace, monospace; }
.chip .x { font-size:11px; color:#8b93a1; margin-top:1px; }
.status .spacer { flex:1; }
.status .act { display:flex; gap:8px; align-items:center; }
.status .act .btn { min-height:40px; }

/* ---- Vung noi dung ----
   Dem duoi 96px (khong phai 40px): nut ban phim ao noi o goc phai duoi cao
   58px - dem mong lam no de len dung hang/nut cuoi trang, bam khong trung. */
.content { padding:20px 22px 96px; flex:1; }
h1 { font-size:23px; color:#4CAF50; margin:0 0 4px; }
h2 { font-size:17px; color:#4CAF50; margin:26px 0 11px; }
.sub { color:#8b93a1; font-size:14px; margin:0 0 18px; }

/* ---- Thanh phan chung ---- */
.card { background:#1b1e22; border:1px solid #2c3036; border-radius:9px;
        padding:17px 19px; margin-bottom:16px; }
.card h3 { margin:0 0 11px; font-size:16px; color:#4CAF50; }
/* Bang co the rat rong (danh sach ARP, LLDP, quet WiFi). Cho no tu cuon
   NGANG BEN TRONG khung noi dung thay vi day ca trang lech sang phai -
   tren tablet ca trang bi lech ngang la rat kho keo lai cho cu. */
.tbl-scroll { overflow-x:auto; -webkit-overflow-scrolling:touch; margin-bottom:6px; }
table { width:100%; border-collapse:collapse; }
th,td { padding:13px 12px; text-align:left; border-bottom:1px solid #2c3036; font-size:15px; }
tbody tr:active, table tr:active { background:#20242a; }
th { background:#22262b; color:#a8b0bd; font-size:12px; text-transform:uppercase;
     letter-spacing:.4px; font-weight:600; }
input[type=text],input[type=password],input[type=number],select,textarea {
  padding:12px 13px; background:#22262b; color:#e6e6e6; border:1px solid #363b42;
  border-radius:6px; font-size:16px; width:100%; max-width:440px; font-family:inherit;
  min-height:44px; }
textarea { font-family:ui-monospace, monospace; min-height:110px; }
label { display:block; margin:12px 0 5px; font-size:14px; color:#a8b0bd; }
button, .btn { padding:12px 19px; background:#4CAF50; color:#fff; border:none;
  border-radius:6px; font-size:15px; cursor:pointer; display:inline-block;
  min-height:48px; font-family:inherit;    /* 48px: co thoai mai cho ngon tay tren tablet */
  -webkit-user-select:none; user-select:none; transition:transform .08s, filter .08s; }
button:hover,.btn:hover { background:#43a047; }
/* :active thay cho :hover - tren man hinh cam ung khong co chuot di qua de
   :hover kich hoat, thieu phan hoi nay nguoi dung khong biet vua cham trung
   nut hay chua va hay bam lai nhieu lan (co the go trung lenh). */
button:active,.btn:active { transform:scale(.96); filter:brightness(.88); }
button[disabled] { transform:none; }
button.gray,.btn.gray { background:#4b5563; }
button.red,.btn.red { background:#ef4444; }
button.blue,.btn.blue { background:#2563eb; }
/* Van giu nho hon nut chinh de phan biet muc do quan trong, nhung khong duoi
   nguong 40px - duoi muc nay ngon tay nguoi lon rat de bam nham nut ben canh. */
button.small { padding:10px 15px; font-size:14px; min-height:42px; }
pre { background:#0f1114; border:1px solid #2c3036; padding:13px; border-radius:6px;
      overflow-x:auto; white-space:pre-wrap; word-break:break-word; font-size:14px; }
code { font-family:ui-monospace, monospace; background:#22262b; padding:2px 6px;
       border-radius:4px; font-size:14px; }
.msg { padding:13px 16px; border-radius:6px; margin:15px 0; font-size:15px; line-height:1.55; }
.msg.ok { background:#14321c; border-left:4px solid #4CAF50; }
.msg.err { background:#3a1a1a; border-left:4px solid #ef4444; }
.msg.warn { background:#3a2f14; border-left:4px solid #f59e0b; }
.msg.info { background:#16283a; border-left:4px solid #3b82f6; }
.row { display:flex; gap:12px; flex-wrap:wrap; align-items:flex-end; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(255px,1fr)); gap:14px; }

/* ---- Man hinh nho (dien thoai) ---- */
@media (max-width: 760px) {
  .wrap { flex-direction:column; }
  /* Bo sticky/chieu cao co dinh o day: tren dien thoai menu nam NGANG tren
     cung, ep height:100vh se chiem tron man hinh. */
  .side { width:100%; flex:none; position:static; height:auto; }
  .nav { display:flex; overflow-x:auto; }
  .nav a { border-left:none; border-bottom:3px solid transparent; white-space:nowrap; }
  .nav a.active { border-left:none; border-bottom-color:#4CAF50; }
  .side .foot, .brand small { display:none; }
}
"""


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

    # --- eth0 (card LAN) ---
    up, ip, state = _iface_info("eth0")
    chips.append({
        "key": "LAN (eth0)",
        "val": ip if ip else ("Đã cắm dây" if state == "up" else "Chưa cắm dây"),
        "extra": ("link " + state) if not ip else f"link {state}",
        "up": up,
    })

    # --- wlan0 (card WiFi) ---
    up_w, ip_w, state_w = _iface_info("wlan0")
    ssid, mode = "", ""
    try:
        info = subprocess.run(["iw", "dev", "wlan0", "info"],
                              capture_output=True, text=True, timeout=4).stdout
        for line in info.splitlines():
            line = line.strip()
            if line.startswith("ssid "):
                ssid = line[5:].strip()
            elif line.startswith("type "):
                mode = line[5:].strip()
    except Exception:
        pass

    if mode == "AP":
        extra = "Đang phát AP: " + (ssid or "ConsolePi")
    elif ssid:
        extra = "Đã nối: " + ssid
    else:
        extra = "Chưa kết nối WiFi"
    chips.append({
        "key": "WiFi (wlan0)",
        "val": ip_w if ip_w else "Không có IP",
        "extra": extra,
        "up": up_w,
    })

    # --- pan0 (Bluetooth) ---
    up_b, ip_b, _ = _iface_info("pan0")
    n_bt = 0
    try:
        out = subprocess.run(["ip", "neigh", "show", "dev", "pan0"],
                             capture_output=True, text=True, timeout=4).stdout
        n_bt = sum(1 for l in out.splitlines() if "REACHABLE" in l or "STALE" in l)
    except Exception:
        pass
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
    from . import remote as _remote
    cf_cai = _remote.da_cai()
    cf_tok = _remote.co_token() if cf_cai else False
    cf_chay = _remote.dang_chay() if (cf_cai and cf_tok) else False
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

    _STATUS_CACHE["data"] = chips
    _STATUS_CACHE["at"] = time.time()
    return chips


def render_page(body_html, active="/", title="Console Pi", subtitle="", extra_css=""):
    """
    Dung 1 trang hoan chinh voi khung chung.
      body_html : phan noi dung rieng cua trang (chuoi HTML da render xong)
      active    : duong dan de to sang muc menu tuong ung
    """
    chips = get_status_chips()

    chips_html = ""
    for idx, c in enumerate(chips):
        cls = "up" if c["up"] else "down"
        chips_html += (
            f'<div class="chip {cls}" data-chip="{idx}"><div class="k">{c["key"]}</div>'
            f'<div class="v">{c["val"]}</div><div class="x">{c["extra"]}</div></div>'
        )

    def _dang_mo(href):
        """'/' chi sang khi khop tuyet doi; cac muc khac sang khi la tien to."""
        return (active == href) if href == "/" else active.startswith(href)

    def _ve_muc(href, label, icon):
        return (f'<a href="{href}" class="{"active" if _dang_mo(href) else ""}" '
                f'title="{label}">'
                f'<span class="ic">{icon}</span><span class="nl">{label}</span></a>')

    nav_html = ""
    for muc in NAV_ITEMS:
        if muc[0] != "nhom":
            nav_html += _ve_muc(*muc)
            continue
        _, ten_nhom, icon_nhom, cac_con = muc
        # Nhom chua trang dang mo thi bung san - nguoi dung luon thay minh
        # dang dung o dau ma khong phai tu mo lai sau moi lan chuyen trang.
        mo = any(_dang_mo(h) for h, _l, _i in cac_con)
        con_html = "".join(_ve_muc(*c) for c in cac_con)
        nav_html += (
            f'<details class="nhom"{" open" if mo else ""}>'
            f'<summary title="{ten_nhom}">'
            f'<span class="ic">{icon_nhom}</span>'
            f'<span class="nl">{ten_nhom}</span></summary>'
            f'<div class="con">{con_html}</div></details>'
        )

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} - Console Pi</title>
<style>{BASE_CSS}
{extra_css}</style>
</head>
<body>
<div class="wrap">
  <div class="side">
    <div class="brand">
      <span class="bten">CONSOLE PI<small>Network Toolkit</small></span>
      <button type="button" id="nut-thu" class="thu"
              title="Thu gọn / mở rộng thanh menu">&raquo;</button>
    </div>
    <div class="nav">{nav_html}</div>
    <div class="foot">
      <a href="/logout">Đăng xuất</a>
    </div>
  </div>
  <div class="main">
    <div class="status">
      {chips_html}
      <div class="spacer"></div>
      <div class="act"><a href="{active}" class="btn gray small">🔃 Lam moi</a></div>
    </div>
    <div class="content">
      <h1>{title}</h1>
      {f'<p class="sub">{subtitle}</p>' if subtitle else ''}
      {body_html}
    </div>
  </div>
</div>
<script>
/* Thu gon / mo rong thanh menu ben trai.
   Nho lua chon vao localStorage de giu nguyen khi chuyen trang - neu
   khong thi moi lan bam sang trang khac menu lai bung ra nhu cu, rat
   kho chiu. Ap dung NGAY (khong doi DOMContentLoaded) de trang khong
   bi "nhay" tu rong sang hep truoc mat nguoi dung. */
(function() {{
  var K = 'consolepi-menu-thu-gon';
  try {{
    if (localStorage.getItem(K) === '1') document.body.classList.add('thu-gon');
  }} catch (e) {{}}
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
    // Thu gon thi bung het cac nhom (chi con icon, khong ton cho) de moi
    // muc con van bam vao duoc.
    document.querySelectorAll('.nav .nhom').forEach(function(d) {{
      if (gon) d.open = true;
    }});
    veLai();
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
    body = _BACKLINK_RE.sub("", body, count=1)

    # Giu lai CSS rieng cua trang do (vd bang mau, pre...), nhung bo phan
    # dinh dang body/nen vi khung chung da lo
    css = ""
    for sm in _STYLE_RE.finditer(html):
        for rule in sm.group(1).split("}"):
            sel = rule.split("{")[0].strip()
            if sel and not sel.startswith(("body", "html", "a ", "a{", "a:")):
                css += rule + "}\n"

    return render_page(body, active=active, title=title, extra_css=css)
