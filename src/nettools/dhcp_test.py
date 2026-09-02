"""
Console Pi Network Tools - DHCP Testing (netool.io Phan 2)

Gui DHCPDISCOVER bang Scapy, bat DHCPOFFER de xem thong tin DHCP server
tra ve. CHI DUNG O OFFER, KHONG gui DHCPREQUEST - khong tieu ton lease
thuc su, an toan de chay nhieu lan lien tuc.

Can quyen root (raw socket) - hoat dong binh thuong khi chay qua web vi
console-pi-dashboard.service chay duoi quyen root.
"""
import random
import time

from flask import request, render_template_string

from . import nettools_bp


def run_dhcp_test(iface="eth0", timeout=5):
    """
    Tra ve {"ok": bool, "error": str|None, "offers": [...]}

    LUU Y KY THUAT: dung sniff() + sendp() rieng biet thay vi srp(), vi
    srp() tu ghep cap request/response bang IP.answers() - co logic khong
    phu hop voi DHCP (goi OFFER tra tu server IP khac, dia chi broadcast,
    khien srp() bo sot OFFER that du no da toi noi). sniff() bat moi goi
    UDP port 68 trong khoang thoi gian cho, khong phu thuoc logic ghep cap.
    """
    try:
        from scapy.all import (
            Ether, IP, UDP, BOOTP, DHCP, sendp, AsyncSniffer,
            get_if_hwaddr, mac2str, conf,
        )
    except ImportError as e:
        return {"ok": False, "error": f"Loi import scapy: {e}", "offers": []}

    conf.verb = 0

    try:
        hw = mac2str(get_if_hwaddr(iface))
    except Exception as e:
        return {"ok": False, "error": f"Khong lay duoc MAC cua {iface}: {e}", "offers": []}

    xid = random.randint(1, 0xFFFFFFFF)
    pkt = (
        Ether(dst="ff:ff:ff:ff:ff:ff") /
        IP(src="0.0.0.0", dst="255.255.255.255") /
        UDP(sport=68, dport=67) /
        BOOTP(chaddr=hw, xid=xid, flags=0x8000) /
        DHCP(options=[("message-type", "discover"), "end"])
    )

    captured = []
    sniffer = AsyncSniffer(
        iface=iface, filter="udp and port 68", store=True,
        prn=lambda p: captured.append(p),
    )
    try:
        sniffer.start()
        time.sleep(0.3)  # dam bao sniffer da san sang truoc khi gui
        sendp(pkt, iface=iface, verbose=0)
        time.sleep(timeout)
    except PermissionError:
        sniffer.stop()
        return {"ok": False, "error": "Khong du quyen mo raw socket (can chay duoi quyen root).", "offers": []}
    except OSError as e:
        sniffer.stop()
        return {"ok": False, "error": f"Loi khi gui goi tin: {e}", "offers": []}
    else:
        sniffer.stop()

    offers = []
    for recv in captured:
        if not recv.haslayer(DHCP) or not recv.haslayer(BOOTP):
            continue
        if recv[BOOTP].xid != xid:
            continue  # bo qua goi cua phien DHCP khac dang chay tren cung day
        opts = {k: v for k, v in
                ((o[0], o[1]) for o in recv[DHCP].options if isinstance(o, tuple))}
        if opts.get("message-type") != 2:  # 2 = DHCPOFFER
            continue
        offers.append({
            "offered_ip": recv[BOOTP].yiaddr,
            "server_id": opts.get("server_id", "?"),
            "subnet_mask": opts.get("subnet_mask", "?"),
            "router": opts.get("router", "?"),
            "name_server": opts.get("name_server", "?"),
            "lease_time": opts.get("lease_time", "?"),
        })

    return {"ok": True, "error": None, "offers": offers}


DHCP_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>DHCP Testing - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: #eee; padding: 20px; }
        h1 { color: #4CAF50; }
        a { color: #4CAF50; }
        select { padding: 8px; background: #333; color: #eee; border: 1px solid #555; }
        button { padding: 9px 18px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
        table { width: 100%; border-collapse: collapse; margin-top: 16px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #444; }
        th { background: #2d2d2d; }
        .err { background: #4a2d2d; border-left: 4px solid #f44336; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .hint { color: #999; font-size: 13px; }
    </style>
</head>
<body>
    <h1>🌐 DHCP Testing</h1>
    <p><a href="/nettools">← Network Tools</a></p>
    <p class="hint">Khuyen nghi dung <strong>eth0</strong> (day mang) - da xac nhan hoat dong dung.
    Tren <strong>wlan0</strong>, nhieu driver WiFi khong the "tiem" (inject) goi tin da tao san
    qua interface dang ket noi WPA2, nen co the KHONG thay OFFER du mang van binh thuong
    (khong phai loi cong cu).</p>
    <p class="hint">Gui 1 goi DHCPDISCOVER va cho DHCPOFFER tra ve. Khong hoan tat
    handshake (khong gui REQUEST) nen khong chiem lease that - an toan chay lai nhieu lan.</p>

    <form method="POST" style="margin-top:16px;">
        <label>Interface:</label>
        <select name="iface">
            <option value="eth0" {{ 'selected' if iface=='eth0' else '' }}>eth0</option>
            <option value="wlan0" {{ 'selected' if iface=='wlan0' else '' }}>wlan0</option>
        </select>
        <button type="submit" style="margin-left:10px;">Gui DHCPDISCOVER</button>
    </form>

    {% if ran %}
        {% if result.error %}
        <div class="err">Loi: {{ result.error }}</div>
        {% else %}
        <p style="margin-top:16px;">Nhan duoc <strong>{{ result.offers|length }}</strong> OFFER:</p>
        <table>
            <tr><th>IP cap</th><th>DHCP Server</th><th>Subnet</th><th>Gateway</th><th>DNS</th><th>Lease (s)</th></tr>
            {% for o in result.offers %}
            <tr>
                <td>{{ o.offered_ip }}</td><td>{{ o.server_id }}</td><td>{{ o.subnet_mask }}</td>
                <td>{{ o.router }}</td><td>{{ o.name_server }}</td><td>{{ o.lease_time }}</td>
            </tr>
            {% endfor %}
        </table>
        {% if not result.offers %}<p>Khong co OFFER nao tra ve trong thoi gian cho (co the khong co DHCP server tren day nay).</p>{% endif %}
        {% endif %}
    {% endif %}
</body>
</html>
"""


@nettools_bp.route("/nettools/dhcp-test", methods=["GET", "POST"])
def dhcp_test_route():
    iface = request.form.get("iface", "eth0")
    ran = request.method == "POST"
    result = run_dhcp_test(iface=iface) if ran else None
    return render_template_string(DHCP_TEMPLATE, iface=iface, ran=ran, result=result)


if __name__ == "__main__":
    import sys
    import json
    iface = sys.argv[1] if len(sys.argv) > 1 else "eth0"
    print(json.dumps(run_dhcp_test(iface=iface), indent=2, ensure_ascii=False))
