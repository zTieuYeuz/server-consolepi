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
NAV_ITEMS = [
    ("/", "Tong quan", "🏠"),
    ("/wifi", "WiFi / AP", "📶"),
    ("/bluetooth", "Bluetooth", "🔵"),
    ("/nettools", "Network Tools", "🛠️"),
    ("/terminal", "Terminal", "⌨️"),
    ("/ssh", "SSH", "🔑"),
    ("/commands", "Thu vien lenh", "📚"),
    ("/docs", "Tai lieu", "📖"),
    ("/settings", "Cai dat", "⚙️"),
]

BASE_CSS = """
* { box-sizing: border-box; }
body { margin:0; font-family: system-ui, Arial, sans-serif; background:#15171a; color:#e6e6e6; }
a { color:#4CAF50; text-decoration:none; }

/* ---- Khung tong ---- */
.wrap { display:flex; min-height:100vh; }
.side { width:190px; flex:0 0 190px; background:#1b1e22; border-right:1px solid #2c3036;
        display:flex; flex-direction:column; }
.brand { padding:14px 16px; font-size:15px; font-weight:700; color:#4CAF50;
         border-bottom:1px solid #2c3036; letter-spacing:.5px; }
.brand small { display:block; color:#6b7280; font-weight:400; font-size:11px; margin-top:2px; }
.nav a { display:flex; align-items:center; gap:10px; padding:13px 16px; color:#c9ced6;
         font-size:14px; border-left:3px solid transparent; }
.nav a:hover { background:#22262b; }
.nav a.active { background:#22262b; border-left-color:#4CAF50; color:#fff; font-weight:600; }
.nav a .ic { font-size:17px; width:22px; text-align:center; }
.side .foot { margin-top:auto; padding:10px 16px; border-top:1px solid #2c3036;
              font-size:11px; color:#6b7280; }

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

/* ---- Vung noi dung ---- */
.content { padding:18px 20px 40px; flex:1; }
h1 { font-size:21px; color:#4CAF50; margin:0 0 4px; }
h2 { font-size:16px; color:#4CAF50; margin:22px 0 10px; }
.sub { color:#8b93a1; font-size:13px; margin:0 0 16px; }

/* ---- Thanh phan chung ---- */
.card { background:#1b1e22; border:1px solid #2c3036; border-radius:9px;
        padding:15px 17px; margin-bottom:14px; }
.card h3 { margin:0 0 10px; font-size:15px; color:#4CAF50; }
table { width:100%; border-collapse:collapse; }
th,td { padding:10px 11px; text-align:left; border-bottom:1px solid #2c3036; font-size:14px; }
th { background:#22262b; color:#a8b0bd; font-size:12px; text-transform:uppercase;
     letter-spacing:.4px; font-weight:600; }
input[type=text],input[type=password],input[type=number],select,textarea {
  padding:11px 12px; background:#22262b; color:#e6e6e6; border:1px solid #363b42;
  border-radius:6px; font-size:15px; width:100%; max-width:440px; font-family:inherit; }
textarea { font-family:ui-monospace, monospace; min-height:110px; }
label { display:block; margin:11px 0 4px; font-size:13px; color:#a8b0bd; }
button, .btn { padding:11px 18px; background:#4CAF50; color:#fff; border:none;
  border-radius:6px; font-size:14px; cursor:pointer; display:inline-block;
  min-height:44px; font-family:inherit; }   /* 44px = co toi thieu de cham ngon tay */
button:hover,.btn:hover { background:#43a047; }
button.gray,.btn.gray { background:#4b5563; }
button.red,.btn.red { background:#ef4444; }
button.blue,.btn.blue { background:#2563eb; }
button.small { padding:7px 13px; font-size:13px; min-height:36px; }
pre { background:#0f1114; border:1px solid #2c3036; padding:12px; border-radius:6px;
      overflow-x:auto; white-space:pre-wrap; word-break:break-word; font-size:13px; }
code { font-family:ui-monospace, monospace; background:#22262b; padding:1px 5px;
       border-radius:4px; font-size:13px; }
.msg { padding:12px 15px; border-radius:6px; margin:14px 0; font-size:14px; }
.msg.ok { background:#14321c; border-left:4px solid #4CAF50; }
.msg.err { background:#3a1a1a; border-left:4px solid #ef4444; }
.msg.warn { background:#3a2f14; border-left:4px solid #f59e0b; }
.msg.info { background:#16283a; border-left:4px solid #3b82f6; }
.row { display:flex; gap:10px; flex-wrap:wrap; align-items:flex-end; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(255px,1fr)); gap:13px; }

/* ---- Man hinh nho (dien thoai) ---- */
@media (max-width: 760px) {
  .wrap { flex-direction:column; }
  .side { width:100%; flex:none; }
  .nav { display:flex; overflow-x:auto; }
  .nav a { border-left:none; border-bottom:3px solid transparent; white-space:nowrap; }
  .nav a.active { border-left:none; border-bottom-color:#4CAF50; }
  .side .foot, .brand small { display:none; }
}
"""


def _iface_info(name):
    """Tra ve (co_ip, ip, chi_tiet) cua 1 interface."""
    ip = ""
    try:
        out = subprocess.run(["ip", "-4", "-o", "addr", "show", name],
                             capture_output=True, text=True, timeout=4).stdout
        for tok in out.split():
            if "/" in tok and tok.count(".") == 3:
                ip = tok.split("/")[0]
                break
    except Exception:
        pass

    state = ""
    try:
        with open(f"/sys/class/net/{name}/operstate") as f:
            state = f.read().strip()
    except Exception:
        state = "?"

    return bool(ip), ip, state


def get_status_chips():
    """
    Thong tin cho thanh trang thai: card LAN, card WiFi, Bluetooth PAN.
    Yeu cau so 2 cua anh: co IP thi hien IP.
    """
    chips = []

    # --- eth0 (card LAN) ---
    up, ip, state = _iface_info("eth0")
    chips.append({
        "key": "LAN (eth0)",
        "val": ip if ip else ("Da cam day" if state == "up" else "Chua cam day"),
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
        extra = "Dang phat AP: " + (ssid or "ConsolePi")
    elif ssid:
        extra = "Da noi: " + ssid
    else:
        extra = "Chua ket noi WiFi"
    chips.append({
        "key": "WiFi (wlan0)",
        "val": ip_w if ip_w else "Khong co IP",
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
        "val": ip_b if ip_b else "Chua bat",
        "extra": (f"{n_bt} thiet bi dang noi" if n_bt else "Chua co thiet bi"),
        "up": up_b,
    })

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

    nav_html = ""
    for href, label, icon in NAV_ITEMS:
        # "/" chi active khi khop tuyet doi; cac muc khac active khi la tien to
        is_active = (active == href) if href == "/" else active.startswith(href)
        nav_html += (
            f'<a href="{href}" class="{"active" if is_active else ""}">'
            f'<span class="ic">{icon}</span><span>{label}</span></a>'
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
    <div class="brand">CONSOLE PI<small>Network Toolkit</small></div>
    <div class="nav">{nav_html}</div>
    <div class="foot">
      <a href="/logout">Dang xuat</a>
    </div>
  </div>
  <div class="main">
    <div class="status">
      {chips_html}
      <div class="spacer"></div>
      <div class="act"><a href="{active}" class="btn gray small">🔄 Lam moi</a></div>
    </div>
    <div class="content">
      <h1>{title}</h1>
      {f'<p class="sub">{subtitle}</p>' if subtitle else ''}
      {body_html}
    </div>
  </div>
</div>
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
