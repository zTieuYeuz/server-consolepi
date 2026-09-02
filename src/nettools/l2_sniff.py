"""
Console Pi Network Tools - STP/LACP Detection (netool.io Phan 4) +
VLAN Tag Detection (netool.io Phan 5), gop chung 1 lan sniff cho do
ton thoi gian cho.

Da xac nhan tren may nay (Pi 4, driver bcmgenet): rx-vlan-offload la
"off [fixed]" tren eth0 -> tag VLAN se tu nhien xuat hien khi sniff bang
Scapy, KHONG can mua them USB-Ethernet adapter nhu tai lieu nghien cuu
ban dau lo ngai (tai lieu do gia dinh sai la Pi 3 dung chip smsc95xx).
"""
from flask import request, render_template_string

from . import nettools_bp


def run_l2_scan(iface="eth0", duration=15):
    """
    Sniff 1 lan tren iface trong `duration` giay, phan loai goi theo STP
    (BPDU, dst MAC 01:80:c2:00:00:00), LACP (ethertype 0x8809), va VLAN
    tag (lop Dot1Q trong bat ky goi nao bat duoc).

    Tra ve: {"ok", "error", "stp": [...], "lacp": [...], "vlans": {vid: count}}
    """
    try:
        from scapy.all import sniff, STP, Dot1Q
        from scapy.contrib.lacp import LACP
    except ImportError as e:
        return {"ok": False, "error": f"Loi import scapy: {e}", "stp": [], "lacp": [], "vlans": {}}

    stp_seen = {}
    lacp_seen = {}
    vlan_counts = {}

    def handler(pkt):
        if pkt.haslayer(Dot1Q):
            vid = pkt[Dot1Q].vlan
            vlan_counts[vid] = vlan_counts.get(vid, 0) + 1

        if pkt.haslayer(STP):
            s = pkt[STP]
            key = (s.rootmac, s.bridgemac)
            stp_seen[key] = {
                "root_mac": s.rootmac,
                "root_priority": s.rootid,
                "bridge_mac": s.bridgemac,
                "bridge_priority": s.bridgeid,
                "port_id": s.portid,
                "hello_time": s.hellotime,
                "max_age": s.maxage,
                "is_root_bridge": s.rootmac == s.bridgemac,
            }

        if pkt.haslayer(LACP):
            l = pkt[LACP]
            key = (l.actor_system, l.partner_system)
            lacp_seen[key] = {
                "actor_system": l.actor_system,
                "actor_key": l.actor_key,
                "actor_port": l.actor_port_number,
                "partner_system": l.partner_system,
                "partner_key": l.partner_key,
                "partner_port": l.partner_port_number,
            }

    try:
        sniff(iface=iface, timeout=duration, prn=handler, store=False)
    except PermissionError:
        return {"ok": False, "error": "Khong du quyen sniff (can chay duoi quyen root).", "stp": [], "lacp": [], "vlans": {}}
    except OSError as e:
        return {"ok": False, "error": f"Loi khi sniff: {e}", "stp": [], "lacp": [], "vlans": {}}

    return {
        "ok": True, "error": None,
        "stp": list(stp_seen.values()),
        "lacp": list(lacp_seen.values()),
        "vlans": dict(sorted(vlan_counts.items())),
    }


L2_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>STP/LACP/VLAN Scan - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: #eee; padding: 20px; }
        h1 { color: #4CAF50; }
        h3 { color: #4CAF50; margin-top: 24px; }
        a { color: #4CAF50; }
        select, input[type=number] { padding: 8px; background: #333; color: #eee; border: 1px solid #555; }
        button { padding: 9px 18px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
        table { width: 100%; border-collapse: collapse; margin-top: 12px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #444; }
        th { background: #2d2d2d; }
        .err { background: #4a2d2d; border-left: 4px solid #f44336; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .hint { color: #999; font-size: 13px; }
        .root { color: #ffb74d; }
    </style>
</head>
<body>
    <h1>🌲 STP / LACP / VLAN Scan</h1>
    <p><a href="/nettools">← Network Tools</a></p>
    <p class="hint">Bat goi tin thu dong trong khoang thoi gian da chon, tren <strong>eth0</strong>
    VLAN offload da duoc xac nhan tat san nen tag 802.1Q se tu hien ra neu co
    traffic tagged thuc su di qua day.</p>

    <form method="POST" style="margin-top:16px;">
        <label>Interface:</label>
        <select name="iface">
            <option value="eth0" {{ 'selected' if iface=='eth0' else '' }}>eth0</option>
            <option value="wlan0" {{ 'selected' if iface=='wlan0' else '' }}>wlan0</option>
        </select>
        <label style="margin-left:10px;">Thoi gian bat (giay):</label>
        <input type="number" name="duration" value="{{ duration }}" min="5" max="60" style="width:70px;">
        <button type="submit" style="margin-left:10px;">Bat dau quet</button>
    </form>

    {% if ran %}
        {% if result.error %}
        <div class="err">Loi: {{ result.error }}</div>
        {% else %}
        <h3>Spanning Tree (STP)</h3>
        {% if result.stp %}
        <table>
            <tr><th>Root Bridge MAC</th><th>Root Priority</th><th>Bridge MAC</th><th>Bridge Priority</th><th>Port ID</th><th>Hello</th></tr>
            {% for s in result.stp %}
            <tr class="{{ 'root' if s.is_root_bridge else '' }}">
                <td>{{ s.root_mac }}</td><td>{{ s.root_priority }}</td>
                <td>{{ s.bridge_mac }}{% if s.is_root_bridge %} (ROOT BRIDGE){% endif %}</td>
                <td>{{ s.bridge_priority }}</td><td>{{ s.port_id }}</td><td>{{ s.hello_time }}s</td>
            </tr>
            {% endfor %}
        </table>
        {% else %}<p>Khong bat duoc BPDU nao (switch co the tat STP, hoac cong dang o trang thai forwarding on dinh khong gui BPDU thuong xuyen).</p>{% endif %}

        <h3>LACP (Link Aggregation)</h3>
        {% if result.lacp %}
        <table>
            <tr><th>Actor System</th><th>Actor Key</th><th>Actor Port</th><th>Partner System</th><th>Partner Key</th><th>Partner Port</th></tr>
            {% for l in result.lacp %}
            <tr>
                <td>{{ l.actor_system }}</td><td>{{ l.actor_key }}</td><td>{{ l.actor_port }}</td>
                <td>{{ l.partner_system }}</td><td>{{ l.partner_key }}</td><td>{{ l.partner_port }}</td>
            </tr>
            {% endfor %}
        </table>
        {% else %}<p>Khong bat duoc goi LACP nao (cong nay khong nam trong 1 EtherChannel/LAG).</p>{% endif %}

        <h3>VLAN Tag (802.1Q)</h3>
        {% if result.vlans %}
        <table>
            <tr><th>VLAN ID</th><th>So goi thay duoc</th></tr>
            {% for vid, cnt in result.vlans.items() %}
            <tr><td>{{ vid }}</td><td>{{ cnt }}</td></tr>
            {% endfor %}
        </table>
        {% else %}<p>Khong thay VLAN tag nao. Day la bi dong - can co traffic tagged
        THUC SU di qua day trong luc quet moi thay duoc (cong access khong tag se
        khong bao gio hien gi o day, do la binh thuong).</p>{% endif %}
        {% endif %}
    {% endif %}
</body>
</html>
"""


@nettools_bp.route("/nettools/l2-scan", methods=["GET", "POST"])
def l2_scan_route():
    iface = request.form.get("iface", "eth0")
    duration = int(request.form.get("duration", 15) or 15)
    ran = request.method == "POST"
    result = run_l2_scan(iface=iface, duration=duration) if ran else None
    return render_template_string(L2_TEMPLATE, iface=iface, duration=duration, ran=ran, result=result)


if __name__ == "__main__":
    import sys
    import json
    iface = sys.argv[1] if len(sys.argv) > 1 else "eth0"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    print(json.dumps(run_l2_scan(iface=iface, duration=duration), indent=2, ensure_ascii=False))
