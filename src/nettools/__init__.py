"""
Console Pi - Network Tools (port cac chuc nang netool.io Pro2)

Package rieng, tach khoi app.py chinh (WiFi/Bluetooth da on dinh, tranh dung
vao). Moi module con o day co logic thuan (test duoc qua CLI) + route Flask
dang ky vao Blueprint nay.
"""
from flask import Blueprint, render_template_string

nettools_bp = Blueprint("nettools", __name__)

HUB_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Network Tools - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: #eee; padding: 20px; }
        h1 { color: #4CAF50; }
        h2 { color: #4CAF50; font-size: 15px; margin: 24px 0 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        a.tool { display: block; padding: 14px 16px; background: #2d2d2d; color: #eee;
            text-decoration: none; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #4CAF50; }
        a.tool:hover { background: #383838; }
        a.tool small { display: block; color: #999; font-size: 12px; margin-top: 4px; }
        a.tool.disabled { border-left-color: #555; color: #777; pointer-events: none; }
        .back { color: #4CAF50; }
    </style>
</head>
<body>
    <h1>🛠️ Network Tools</h1>
    <p><a href="/" class="back">← Quay lai Dashboard</a></p>

    <h2>Chan doan mang (chi doc)</h2>
    {% for href, label, desc, ready in tools_readonly %}
    <a class="tool{{ '' if ready else ' disabled' }}" href="{{ href if ready else '#' }}">
        {{ label }}<small>{{ desc }}</small>
    </a>
    {% endfor %}

    <h2>Tu dong hoa (ghi cau hinh thiet bi that)</h2>
    {% for href, label, desc, ready in tools_write %}
    <a class="tool{{ '' if ready else ' disabled' }}" href="{{ href if ready else '#' }}">
        {{ label }}<small>{{ desc }}</small>
    </a>
    {% endfor %}
</body>
</html>
"""

# ready=False = placeholder, se bat len tung phan khi lam xong giai doan tuong ung
TOOLS_READONLY = [
    ("/nettools/arp-scan", "🔍 ARP Scan", "Quet toan bo thiet bi dang online trong subnet", True),
    ("/nettools/ping", "📶 Ping / Traceroute", "Kiem tra ket noi toi 1 dia chi/hostname", True),
    ("/nettools/pcap", "📼 PCAP Capture", "Bat goi tin, luu ra USB, xem lai bang tshark", True),
    ("/nettools/lldp", "🔗 LLDP/CDP Discovery", "Tim switch hostname, port, VLAN, PoE quang ba", True),
    ("/nettools/dhcp-test", "🔌🌐 Kiem tra cong mang", "Toc do/duplex, loi duong truyen, PoE, DHCP, Internet, bang thong - tat ca trong 1 nut", True),
    ("/nettools/l2-scan", "🌲 STP/LACP/VLAN Scan", "Bat goi BPDU/LACP/802.1Q tren day dang cam", True),
    ("/nettools/mtu", "📏 MTU Discovery", "Do MTU thuc te toi 1 dia chi (phat hien VPN/PPPoE lam giam MTU)", True),
    ("/nettools/dns-check", "🌐 Kiem tra DNS", "Doi chieu ket qua phan giai ten mien qua nhieu DNS server", True),
    ("/nettools/tls-check", "🔒 Kiem tra chung chi TLS", "Xem chi tiet + tinh trang tin cay cua chung chi HTTPS quan ly", True),
    ("/nettools/ping-monitor", "📈 Ping lien tuc (do thi song)", "Theo doi rot goi thoi gian thuc khi rung/cam lai day", True),
    ("/nettools/topology", "🗺️ So do mang 1 doan", "Ve Pi - switch - cac host tren cung 1 segment (ARP+LLDP)", True),
]

TOOLS_WRITE = [
    ("/nettools/tftp", "📤 May chu TFTP", "Bat/tat TFTP de sao luu/phuc hoi config, firmware tu switch/router", True),
    ("/nettools/netmiko", "⚙️ Netmiko Config", "Tu dong SSH vao switch chay lenh cau hinh (co xem truoc)", True),
    ("/nettools/dot1x", "🔐 802.1X Testing", "Test xac thuc EAP voi RADIUS server (khong dung eth0)", True),
    ("/nettools/ifthen", "🧩 IF/THEN Automation", "Rule tu dong goi y cau hinh khi phat hien switch quen", True),
]


@nettools_bp.route("/nettools")
def hub():
    return render_template_string(
        HUB_TEMPLATE, tools_readonly=TOOLS_READONLY, tools_write=TOOLS_WRITE
    )


# Import cac module con O CUOI FILE (sau khi nettools_bp da dinh nghia xong)
# de dang ky route cua tung module - tranh circular import.
from . import arp_scan  # noqa: E402,F401
from . import connectivity  # noqa: E402,F401
from . import pcap  # noqa: E402,F401
from . import lldp  # noqa: E402,F401
from . import dhcp_test  # noqa: E402,F401
from . import l2_sniff  # noqa: E402,F401
from . import mtu_discover  # noqa: E402,F401
from . import dns_check  # noqa: E402,F401
from . import tls_check  # noqa: E402,F401
from . import ping_monitor  # noqa: E402,F401
from . import topology  # noqa: E402,F401
from . import tftp_server  # noqa: E402,F401
from . import netmiko_tool  # noqa: E402,F401
from . import dot1x  # noqa: E402,F401
from . import ifthen  # noqa: E402,F401


# ---------------------------------------------------------------------------
# BAN PHIM AO cho man hinh cam ung gan truc tiep vao Pi.
#
# Thay vi sua tung template (co ~15 cai giua app.py va cac module nettools),
# chen 1 the <script> vao TRUOC </body> cua MOI response HTML. Cach nay:
#   - Khong dung vao bat ky template nao dang chay on dinh
#   - Trang moi them sau nay tu dong co ban phim, khong can nho lam gi them
# ---------------------------------------------------------------------------
import os as _os

from flask import send_from_directory as _send_from_directory

_STATIC_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "static")
_VK_TAG = b'<script src="/vkeyboard.js"></script>'


@nettools_bp.route("/dashboard.js")
def dashboard_js():
    return _send_from_directory(_STATIC_DIR, "dashboard.js", mimetype="application/javascript")


@nettools_bp.route("/vkeyboard.js")
def vkeyboard_js():
    return _send_from_directory(_STATIC_DIR, "vkeyboard.js", mimetype="application/javascript")


def register_vkeyboard(app):
    """Goi tu app.py: tu dong chen ban phim ao vao moi trang HTML."""

    @app.after_request
    def _inject_vkeyboard(response):
        try:
            ctype = (response.content_type or "")
            if not ctype.startswith("text/html"):
                return response
            if response.direct_passthrough:
                return response
            body = response.get_data()
            if _VK_TAG in body:
                return response
            if b"</body>" in body:
                response.set_data(body.replace(b"</body>", _VK_TAG + b"</body>", 1))
            else:
                response.set_data(body + _VK_TAG)
        except Exception:
            pass  # khong bao gio de loi chen script lam hong ca trang
        return response

    return app


# ---------------------------------------------------------------------------
# Boc cac trang cong cu vao khung giao dien chung (thanh trai + noi dung phai)
#
# Cac module trong goi nay duoc viet truoc khi co khung chung nen moi cai tu
# dung <html> rieng. Hook nay boc lai chung khi tra ve, de nguoi dung luon
# thay thanh dieu huong va thanh trang thai mang - khong bi "lac" khi vao
# sau trong cong cu.
# ---------------------------------------------------------------------------
@nettools_bp.after_request
def _wrap_in_layout(response):
    try:
        if not (response.content_type or "").startswith("text/html"):
            return response
        if response.direct_passthrough:
            return response
        from ui.layout import wrap_legacy_html
        html = response.get_data(as_text=True)
        if "<body" in html and 'class="wrap"' not in html:
            response.set_data(wrap_legacy_html(html))
    except Exception:
        pass          # loi boc khung khong duoc lam hong ca trang
    return response
