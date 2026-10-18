# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi - Network Tools (port cac chuc nang netool.io Pro2)

Package rieng, tach khoi app.py chinh (WiFi/Bluetooth da on dinh, tranh dung
vao). Moi module con o day co logic thuan (test duoc qua CLI) + route Flask
dang ky vao Blueprint nay.
"""
from flask import Blueprint, render_template_string

nettools_bp = Blueprint("nettools", __name__)

HUB_CSS = """
        .nt-mo { color: var(--chu-mo); font-size: 14.5px; margin: -2px 0 16px; max-width: 62ch; }
        .nt-luoi { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
        .nt-luoi:not(.co-dai) > a:last-child:nth-child(odd), .nt-luoi.co-dai > a:last-child:nth-child(even) { grid-column: 1 / -1; }
        a.nt-o { position: relative; display: flex; gap: 14px; align-items: flex-start; padding: 16px 18px;
            background: var(--the); border: 1px solid var(--vien); border-radius: var(--bo); color: var(--chu); overflow: hidden;
            transition: border-color .2s, transform .2s var(--muot), background-color .2s; }
        a.nt-o:hover { border-color: var(--vien-ro); transform: translateY(-2px); color: var(--chu); background: var(--the); }
        a.nt-o:active { transform: scale(.99); }
        a.nt-o .bi { flex: none; width: 42px; height: 42px; border-radius: 10px; display: grid; place-items: center;
            background: var(--nhan-mo); color: var(--nhan); }
        a.nt-o svg.ph { width: 24px; height: 24px; }
        a.nt-o b { display: block; font-size: 15.5px; font-weight: 620; letter-spacing: -.01em; }
        a.nt-o small { display: block; color: var(--chu-mo); font-size: 13.5px; line-height: 1.5; margin-top: 3px; }
        a.nt-o.dai { padding: 24px 26px; align-items: center; grid-column: 1 / -1;
            background: radial-gradient(120% 100% at 100% 0%, var(--nhan-mo), transparent 60%), var(--the);
            border-color: color-mix(in srgb, var(--nhan) 32%, var(--vien)); }
        a.nt-o.dai .bi { width: 56px; height: 56px; border-radius: 14px; }
        a.nt-o.dai svg.ph { width: 32px; height: 32px; }
        a.nt-o.dai b { font-size: 21px; letter-spacing: -.025em; font-weight: 630; }
        a.nt-o.dai small { font-size: 14.5px; max-width: 70ch; }
        a.nt-o.tat { opacity: .5; pointer-events: none; }
        .nt-luu-y { margin: 0 0 14px; padding: 12px 16px; border-radius: 10px; font-size: 14px;
            background: var(--vang-mo); border: 1px solid rgba(232,176,74,.35); border-left-width: 3px; border-left-color: var(--vang); color: var(--msg-warn); }
        @media (max-width: 760px) { .nt-luoi { grid-template-columns: 1fr; } }
        @media (prefers-reduced-motion: no-preference) {
            .nt-luoi > a { animation: nt-vao .5s var(--muot) both; animation-delay: calc(var(--i, 0) * 45ms); }
            @keyframes nt-vao { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: none; } }
        }
    """

HUB_BODY = """
    <h2>Chẩn đoán mạng</h2>
    <p class="nt-mo">Chỉ đọc: các công cụ này quan sát mạng, không thay đổi gì trên thiết bị hay mạng của khách.</p>
    <div class="nt-luoi co-dai">
    {% for href, label, desc, ready in tools_readonly %}
    <a class="nt-o{{ ' dai' if loop.first else '' }}{{ '' if ready else ' tat' }}" style="--i: {{ loop.index0 }}" href="{{ href if ready else '#' }}">
        <span class="bi">{{ icon(href)|safe }}</span><span><b>{{ label }}</b><small>{{ desc }}</small></span>
    </a>
    {% endfor %}
    </div>

    <h2>Tự động hóa</h2>
    <p class="nt-luu-y">Các công cụ này ghi thay đổi lên thiết bị thật. Kiểm tra kỹ trước khi chạy.</p>
    <div class="nt-luoi">
    {% for href, label, desc, ready in tools_write %}
    <a class="nt-o{{ '' if ready else ' tat' }}" style="--i: {{ loop.index0 }}" href="{{ href if ready else '#' }}">
        <span class="bi">{{ icon(href)|safe }}</span><span><b>{{ label }}</b><small>{{ desc }}</small></span>
    </a>
    {% endfor %}
    </div>
"""

# Icon Phosphor cho tung cong cu (duong dan -> ten icon, xem ui/ph_icons.py)
ICON_CONG_CU = {
    "/nettools/dhcp-test": "plugs-connected", "/nettools/arp-scan": "magnifying-glass",
    "/nettools/ping": "wifi-high", "/nettools/pcap": "cassette-tape", "/nettools/lldp": "link",
    "/nettools/l2-scan": "tree-structure", "/nettools/mtu": "ruler", "/nettools/dns-check": "globe",
    "/nettools/tls-check": "lock", "/nettools/topology": "map-trifold",
    "/nettools/tftp": "upload-simple", "/nettools/console-backup": "usb",
    "/nettools/netmiko": "gear-six", "/nettools/dot1x": "shield-check", "/nettools/ifthen": "flow-arrow",
}


def _icon(href):
    from ui.ph_icons import ph_icon
    return ph_icon(ICON_CONG_CU.get(href, "link"))


# ready=False = placeholder, se bat len tung phan khi lam xong giai doan tuong ung
TOOLS_READONLY = [
    ("/nettools/arp-scan", "ARP Scan", "Quét toàn bộ thiết bị đang online trong subnet", True),
    ("/nettools/ping", "Ping / Traceroute", "Kiểm tra kết nối tới 1 địa chỉ/hostname", True),
    ("/nettools/pcap", "PCAP Capture", "Bắt gói tin, lưu ra USB, xem lại bằng tshark", True),
    ("/nettools/lldp", "LLDP/CDP Discovery", "Tìm switch hostname, port, VLAN, PoE quảng bá", True),
    ("/nettools/dhcp-test", "Kiểm tra cổng mạng", "Tốc độ/duplex, lỗi đường truyền, PoE, DHCP, Internet, băng thông - tất cả trong 1 nút", True),
    ("/nettools/l2-scan", "STP/LACP/VLAN Scan", "Bắt gói BPDU/LACP/802.1Q trên dây đang cắm", True),
    ("/nettools/mtu", "MTU Discovery", "Đo MTU thực tế tới 1 địa chỉ (phát hiện VPN/PPPoE làm giảm MTU)", True),
    ("/nettools/dns-check", "Kiểm tra DNS", "Đối chiếu kết quả phân giải tên miền qua nhiều DNS server", True),
    ("/nettools/tls-check", "Kiểm tra chứng chỉ TLS", "Xem chi tiết và tình trạng tin cậy của chứng chỉ HTTPS quản lý", True),
    ("/nettools/topology", "Sơ đồ mạng 1 đoạn", "Vẽ Pi - switch - các host trên cùng 1 segment (ARP+LLDP)", True),
]

TOOLS_WRITE = [
    ("/nettools/tftp", "Máy chủ TFTP", "Bật/tắt TFTP để sao lưu/phục hồi config, firmware từ switch/router", True),
    ("/nettools/console-backup", "Sao lưu qua cáp console", "Backup cấu hình khi thiết bị mất IP quản lý - chỉ cần dây console", True),
    ("/nettools/netmiko", "Netmiko Config", "Tự động SSH vào switch chạy lệnh cấu hình (có xem trước)", True),
    ("/nettools/dot1x", "802.1X Testing", "Test xác thực EAP với RADIUS server (không đụng eth0)", True),
    ("/nettools/ifthen", "IF/THEN Automation", "Rule tự động gợi ý cấu hình khi phát hiện switch quen", True),
]


@nettools_bp.route("/nettools")
def hub():
    # Kiem tra cong mang (1 nut lam het) len dau, thanh o noi bat
    ds = sorted(TOOLS_READONLY, key=lambda t: 0 if t[0] == "/nettools/dhcp-test" else 1)
    from ui.layout import render_page
    noi_dung = render_template_string(HUB_BODY, tools_readonly=ds, tools_write=TOOLS_WRITE, icon=_icon)
    return render_page(noi_dung, active="/nettools", title="Network Tools",
                       subtitle="Công cụ chẩn đoán và tự động hóa mạng", extra_css=HUB_CSS)


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
from . import topology  # noqa: E402,F401
from . import tftp_server  # noqa: E402,F401
from . import console_backup  # noqa: E402,F401
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


def register_no_cache_json(app):
    """
    Goi tu app.py: chan CDN/proxy trung gian (vd Cloudflare Tunnel) cache
    nham cac endpoint JSON sinh du lieu song (ping-monitor/data, api/status...).

    LOI THAT DA GAP: fetch(url, {cache:"no-store"}) o phia trinh duyet CHI
    dieu khien cache CUC BO cua trinh duyet, KHONG ngan duoc mot proxy trung
    gian (Cloudflare) tu y cache response neu server goc khong noi ro trong
    header. Nguoi dung qua Cloudflare Tunnel bam "Bat dau" ping lien tuc,
    request /data dau tien bi Cloudflare cache lai (vi luc do co the dang
    tra ve 404/loi tam thoi), moi request /data sau do deu duoc Cloudflare
    tra thang tu cache ma KHONG BAO GIO cham toi Pi that su - xac nhan qua
    log nginx tren Pi khong thay request nao toi tu trinh duyet nguoi dung.

    Chan tan goc bang cach ep MOI response JSON (mimetype application/json)
    tren TOAN BO app (khong rieng nettools - "/api/status" cua ui/home.py
    dung chung 1 nguy co) phai co Cache-Control: no-store, de cac cong cu
    polling JSON sau nay tu dong duoc bao ve, khong lap lai loi nay.
    """

    @app.after_request
    def _khong_cache_json(response):
        try:
            if (response.content_type or "").startswith("application/json"):
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                response.headers["Pragma"] = "no-cache"
        except Exception:
            pass
        return response

    return app
