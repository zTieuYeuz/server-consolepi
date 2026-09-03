"""
Console Pi Network Tools - So do mang 1 doan (topology)

Gop 2 cong cu da co san (ARP Scan + LLDP/CDP Discovery) thanh MOT so do
truc quan: Pi -> switch dang cam vao (neu switch co quang ba LLDP/CDP) ->
cac thiet bi tren cung doan mang (tu ARP scan).

GIOI HAN THAT - phai noi ro tren giao dien, khong duoc de nguoi dung hieu
lam: day CHI la so do 1 DOAN MANG (segment) noi truc tiep vao cong dang
quet. Khong ve duoc nhieu switch noi tiep nhau (can SNMP walk bang MAC-
address-table cua tung switch lien tiep, ngoai pham vi cong cu nay).

Ve SVG bang Python thuan phia server (khong dung thu vien bieu do/JS ngoai,
dung tinh than cua du an: it phu thuoc, tu kiem soat hoan toan noi dung).
"""
import html
import re

from flask import request, render_template_string

from . import nettools_bp
from .arp_scan import run_arp_scan
from .lldp import get_lldp_neighbors

# So host toi da ve truc tiep tren SVG - qua nhieu thi hinh roi rac, chuyen
# sang chi ghi "+N nua, xem bang ben duoi".
SO_HOST_TOI_DA_TREN_HINH = 20


def xay_dung_topo(iface="eth0"):
    """
    Tra ve {"ok", "error", "iface", "switch": {...}|None, "hosts": [...],
            "svg": str, "gioi_han": str}
    """
    lldp_kq = get_lldp_neighbors()
    arp_kq = run_arp_scan(iface=iface)

    if not arp_kq.get("ok"):
        return {"ok": False, "error": f"ARP scan loi: {arp_kq.get('error')}",
                "iface": iface, "switch": None, "hosts": [], "svg": "", "gioi_han": ""}

    switch = None
    if lldp_kq.get("ok"):
        for n in lldp_kq.get("neighbors", []):
            if n.get("iface") == iface:
                switch = n
                break

    hosts = arp_kq.get("hosts", [])
    svg = _ve_svg(iface, switch, hosts)

    gioi_han = ("Chi ve duoc 1 doan mang (segment) noi truc tiep vao cong nay - "
               "khong quet duoc cac switch/segment ke tiep qua nhieu hop (can SNMP "
               "walk lien switch, ngoai pham vi cong cu nay).")

    return {"ok": True, "error": None, "iface": iface, "switch": switch,
            "hosts": hosts, "svg": svg, "gioi_han": gioi_han}


def _thoat_svg(s):
    return html.escape(str(s or ""), quote=True)


def _ve_svg(iface, switch, hosts):
    """Ve 3 tang: Pi -> switch (hoac o net dut neu khong phat hien) -> hosts."""
    RONG, CAO = 900, 340
    Y_PI, Y_SWITCH, Y_HOST = 40, 150, 270

    phan = []
    phan.append(
        f'<svg viewBox="0 0 {RONG} {CAO}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;height:auto;background:#111;border-radius:8px;">'
    )
    phan.append(
        '<style>text{font-family:Arial,sans-serif;fill:#eee;}'
        '.hop{fill:#262626;stroke:#4CAF50;stroke-width:2;}'
        '.hop-mo{fill:#262626;stroke:#666;stroke-width:2;stroke-dasharray:5,4;}'
        '.duong{stroke:#4CAF50;stroke-width:1.5;opacity:0.6;}'
        '.nhan{font-size:11px;fill:#999;}'
        '.ten{font-size:13px;font-weight:600;}</style>'
    )

    # --- Nut Pi (luon co) ---
    x_pi = RONG / 2
    phan.append(f'<rect class="hop" x="{x_pi-70}" y="{Y_PI-22}" width="140" height="44" rx="8"/>')
    phan.append(f'<text class="ten" x="{x_pi}" y="{Y_PI+5}" text-anchor="middle">🖥 Console Pi</text>')

    # --- Nut switch ---
    x_switch = RONG / 2
    if switch:
        ten_switch = _thoat_svg(switch.get("remote_name") or "(khong ro ten)")
        cong_switch = _thoat_svg(switch.get("port_descr") or switch.get("port_id") or "")
        phan.append(f'<line class="duong" x1="{x_pi}" y1="{Y_PI+22}" x2="{x_switch}" y2="{Y_SWITCH-22}"/>')
        phan.append(f'<rect class="hop" x="{x_switch-100}" y="{Y_SWITCH-22}" width="200" height="44" rx="8"/>')
        phan.append(f'<text class="ten" x="{x_switch}" y="{Y_SWITCH-2}" text-anchor="middle">🔀 {ten_switch}</text>')
        if cong_switch:
            phan.append(f'<text class="nhan" x="{x_switch}" y="{Y_SWITCH+14}" text-anchor="middle">{cong_switch}</text>')
        diem_bat_dau_host = (x_switch, Y_SWITCH + 22)
    else:
        phan.append(f'<line class="duong" x1="{x_pi}" y1="{Y_PI+22}" x2="{x_switch}" y2="{Y_SWITCH-22}"/>')
        phan.append(f'<rect class="hop-mo" x="{x_switch-110}" y="{Y_SWITCH-22}" width="220" height="44" rx="8"/>')
        phan.append(f'<text class="ten" x="{x_switch}" y="{Y_SWITCH+2}" text-anchor="middle" fill="#888">'
                    '(khong phat hien switch qua LLDP/CDP)</text>')
        diem_bat_dau_host = (x_switch, Y_SWITCH + 22)

    # --- Cac host ---
    hien_thi = hosts[:SO_HOST_TOI_DA_TREN_HINH]
    n = len(hien_thi)
    if n:
        khoang_cach = RONG / (n + 1)
        for i, h in enumerate(hien_thi):
            x = khoang_cach * (i + 1)
            phan.append(f'<line class="duong" x1="{diem_bat_dau_host[0]}" y1="{diem_bat_dau_host[1]}" '
                       f'x2="{x}" y2="{Y_HOST-18}"/>')
            phan.append(f'<rect class="hop" x="{x-58}" y="{Y_HOST-18}" width="116" height="40" rx="6"/>')
            phan.append(f'<text class="ten" x="{x}" y="{Y_HOST-2}" text-anchor="middle" '
                       f'style="font-size:11px;">{_thoat_svg(h["ip"])}</text>')
            ten_vendor = h.get("vendor", "")[:16]
            phan.append(f'<text class="nhan" x="{x}" y="{Y_HOST+14}" text-anchor="middle">{_thoat_svg(ten_vendor)}</text>')

    if len(hosts) > SO_HOST_TOI_DA_TREN_HINH:
        phan.append(f'<text class="nhan" x="{RONG-10}" y="{CAO-8}" text-anchor="end">'
                   f'+{len(hosts) - SO_HOST_TOI_DA_TREN_HINH} thiet bi nua - xem bang ben duoi</text>')

    if not hosts:
        phan.append(f'<text class="nhan" x="{RONG/2}" y="{Y_HOST}" text-anchor="middle">'
                   'Khong tim thay thiet bi nao qua ARP scan</text>')

    phan.append('</svg>')
    return "".join(phan)


TOPOLOGY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>So do mang - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: #eee; padding: 20px; }
        h1 { color: #4CAF50; } h3 { color: #4CAF50; margin-top: 22px; }
        a { color: #4CAF50; }
        select { padding: 8px; background: #333; color: #eee; border: 1px solid #555; }
        button { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 12px; }
        th, td { padding: 9px 10px; text-align: left; border-bottom: 1px solid #444; }
        th { background: #2d2d2d; }
        .card { background:#262626; border:1px solid #3a3a3a; border-left:4px solid #4CAF50;
                border-radius:6px; padding:14px 16px; margin-top:16px; }
        .err { background: #4a2d2d; border-left: 4px solid #f44336; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .hint { color: #999; font-size: 13px; }
    </style>
</head>
<body>
    <h1>🗺️ So do mang 1 doan</h1>
    <p><a href="/nettools">← Network Tools</a></p>
    <p class="hint">Ghep ARP Scan + LLDP/CDP Discovery thanh 1 so do: Pi → switch dang cam vao
    (neu co quang ba LLDP/CDP) → cac thiet bi tren cung doan mang.</p>
    <p class="hint">⚠️ <strong>Gioi han:</strong> chi ve duoc 1 doan mang noi truc tiep vao cong
    nay - khong ve duoc nhieu switch noi tiep qua nhieu hop.</p>

    <form method="POST" style="margin-top:16px;">
        <label>Interface:</label>
        <select name="iface">
            <option value="eth0" {{ 'selected' if iface=='eth0' else '' }}>eth0</option>
            <option value="wlan0" {{ 'selected' if iface=='wlan0' else '' }}>wlan0</option>
        </select>
        <button type="submit" style="margin-left:10px;" data-busy="Dang quet ARP + LLDP...">Ve so do</button>
    </form>

    {% if ran %}
        {% if not result.ok %}
        <div class="err">{{ result.error }}</div>
        {% else %}
        <div class="card">{{ result.svg|safe }}</div>

        <h3>Chi tiet ({{ result.hosts|length }} thiet bi)</h3>
        <table>
            <tr><th>IP</th><th>MAC</th><th>Vendor</th></tr>
            {% for h in result.hosts %}
            <tr><td>{{ h.ip }}</td><td>{{ h.mac }}</td><td>{{ h.vendor }}</td></tr>
            {% endfor %}
        </table>
        {% if not result.hosts %}<p>Khong tim thay thiet bi nao.</p>{% endif %}
        {% endif %}
    {% endif %}
</body>
</html>
"""


@nettools_bp.route("/nettools/topology", methods=["GET", "POST"])
def topology_route():
    iface = request.form.get("iface", "eth0")
    ran = request.method == "POST"
    result = xay_dung_topo(iface=iface) if ran else None
    return render_template_string(TOPOLOGY_TEMPLATE, iface=iface, ran=ran, result=result)


if __name__ == "__main__":
    import sys
    import json
    iface = sys.argv[1] if len(sys.argv) > 1 else "eth0"
    kq = xay_dung_topo(iface=iface)
    kq_gon = {k: v for k, v in kq.items() if k != "svg"}
    kq_gon["svg_do_dai"] = len(kq.get("svg", ""))
    print(json.dumps(kq_gon, indent=2, ensure_ascii=False))
