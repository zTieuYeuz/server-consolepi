"""
Console Pi Network Tools - ARP Scan (netool.io Phan 3)

Quet toan bo thiet bi dang online trong subnet bang arp-scan. Hoat dong ca
voi thiet bi chan ping/firewall vi ARP khong di qua tuong lua IP.
"""
import re
import subprocess

from flask import request, render_template_string

from . import nettools_bp

# Dinh dang chuan cua arp-scan --localnet (moi dong 1 thiet bi):
# 192.168.1.1<TAB>aa:bb:cc:dd:ee:ff<TAB>Vendor Name Here
ARP_LINE_RE = re.compile(
    r"^(\d{1,3}(?:\.\d{1,3}){3})\t([0-9a-fA-F:]{17})\t(.*)$"
)


def run_arp_scan(iface="eth0", target=None, timeout=30):
    """
    Chay arp-scan tren 1 interface. Neu target (CIDR/IP) duoc chi dinh thi
    quet dai do, khong thi dung --localnet (doi hoi interface phai co IP).

    Tra ve: {"ok": bool, "error": str|None, "hosts": [{"ip","mac","vendor"}]}
    """
    cmd = ["arp-scan", f"--interface={iface}"]
    cmd += [target] if target else ["--localnet"]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError:
        return {"ok": False, "error": "Chua cai arp-scan.", "hosts": []}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Qua thoi gian cho.", "hosts": []}

    if result.returncode != 0 and not result.stdout.strip():
        err = result.stderr.strip() or f"arp-scan tra ve loi (exit {result.returncode})"
        return {"ok": False, "error": err, "hosts": []}

    hosts = []
    for line in result.stdout.splitlines():
        m = ARP_LINE_RE.match(line)
        if m:
            hosts.append({
                "ip": m.group(1),
                "mac": m.group(2).lower(),
                "vendor": m.group(3).strip() or "(khong ro)",
            })

    return {"ok": True, "error": None, "hosts": hosts}


ARP_SCAN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>ARP Scan - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: #eee; padding: 20px; }
        h1 { color: #4CAF50; }
        a { color: #4CAF50; }
        table { width: 100%; border-collapse: collapse; margin-top: 16px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #444; }
        th { background: #2d2d2d; }
        select, input[type=text] { padding: 8px; background: #333; color: #eee; border: 1px solid #555; }
        button { padding: 9px 18px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .err { background: #4a2d2d; border-left: 4px solid #f44336; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .hint { color: #999; font-size: 13px; margin-top: 6px; }
    </style>
</head>
<body>
    <h1>🔍 ARP Scan</h1>
    <p><a href="/nettools">← Network Tools</a></p>

    <form method="POST" style="margin-top:16px;">
        <label>Interface:</label>
        <select name="iface">
            <option value="eth0" {{ 'selected' if iface=='eth0' else '' }}>eth0 (day mang)</option>
            <option value="wlan0" {{ 'selected' if iface=='wlan0' else '' }}>wlan0 (WiFi)</option>
        </select>
        <label style="margin-left:12px;">Dai IP (tuy chon):</label>
        <input type="text" name="target" value="{{ target or '' }}" placeholder="vd 192.168.1.0/24 - de trong = tu localnet">
        <button type="submit" style="margin-left:12px;">Quet</button>
        <div class="hint">Neu interface chua co dia chi IP (cam vao trunk port khong DHCP), phai nhap tay dai CIDR.</div>
    </form>

    {% if ran %}
        {% if result.error %}
        <div class="err">Loi: {{ result.error }}</div>
        {% else %}
        <p style="margin-top:16px;">Tim thay <strong>{{ result.hosts|length }}</strong> thiet bi tren {{ iface }}:</p>
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


@nettools_bp.route("/nettools/arp-scan", methods=["GET", "POST"])
def arp_scan_route():
    iface = request.form.get("iface", "eth0")
    target = (request.form.get("target") or "").strip() or None
    ran = request.method == "POST"

    result = run_arp_scan(iface=iface, target=target) if ran else None

    return render_template_string(
        ARP_SCAN_TEMPLATE, iface=iface, target=target, ran=ran, result=result
    )


if __name__ == "__main__":
    import sys
    import json

    iface = sys.argv[1] if len(sys.argv) > 1 else "eth0"
    target = sys.argv[2] if len(sys.argv) > 2 else None
    print(json.dumps(run_arp_scan(iface=iface, target=target), indent=2, ensure_ascii=False))
