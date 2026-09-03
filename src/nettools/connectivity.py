"""
Console Pi Network Tools - Ping / Traceroute (netool.io: Connectivity Test)
"""
import re
import subprocess

from flask import request, render_template_string

from . import nettools_bp

# LO HONG DA VA (ra soat lai code, khong phai da gap that): truoc day
# khong kiem tra gi ca truoc khi dua "host" thang vao subprocess.run(). Vi
# goi dang list (khong shell=True) nen KHONG the chen lenh shell duoc, NHUNG
# neu "host" bat dau bang dau "-" (vd "--flood" hoac "-f") thi ping/
# traceroute co the hieu nham do la MOT CO LENH thay vi ten may - va "ping
# --flood" can quyen root de chay (ma tien trinh Flask nay CHINH LA root).
# Rui ro thuc te thap (chi admin da dang nhap moi goi duoc, va ho da co
# quyen root qua Terminal roi) nhung van nen chan cho chac, phong truong hop
# co lo hong CSRF khac khien trinh duyet cua admin tu dong gui form nay ma
# ho khong hay biet.
_MAU_HOST_HOP_LE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-:]{0,253}$")


def _host_hop_le(host):
    return bool(host) and bool(_MAU_HOST_HOP_LE.fullmatch(host))


def run_ping(host, iface="eth0", count=4, timeout=2):
    cmd = ["ping", "-c", str(count), "-W", str(timeout), "-I", iface, host]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=count * timeout + 10)
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "(qua thoi gian cho)"
    except Exception as e:
        return f"(loi: {e})"


def run_traceroute(host, iface="eth0", max_hops=20, timeout=2):
    cmd = ["traceroute", "-n", "-w", str(timeout), "-m", str(max_hops), "-i", iface, host]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=max_hops * timeout + 15)
        return result.stdout + result.stderr
    except FileNotFoundError:
        return "(chua cai traceroute)"
    except subprocess.TimeoutExpired:
        return "(qua thoi gian cho)"
    except Exception as e:
        return f"(loi: {e})"


PING_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Ping / Traceroute - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: #eee; padding: 20px; }
        h1 { color: #4CAF50; }
        h3 { color: #4CAF50; margin-top: 20px; }
        a { color: #4CAF50; }
        input[type=text], select { padding: 8px; background: #333; color: #eee; border: 1px solid #555; }
        button { padding: 9px 18px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
        pre { background: #111; padding: 12px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; word-break: break-all; }
    </style>
</head>
<body>
    <h1>📶 Ping / Traceroute</h1>
    <p><a href="/nettools">← Network Tools</a></p>

    <form method="POST" style="margin-top:16px;">
        <label>Host/IP:</label>
        <input type="text" name="host" value="{{ host or '' }}" placeholder="vd 8.8.8.8 hoac google.com" required>
        <label style="margin-left:10px;">Interface:</label>
        <select name="iface">
            <option value="eth0" {{ 'selected' if iface=='eth0' else '' }}>eth0</option>
            <option value="wlan0" {{ 'selected' if iface=='wlan0' else '' }}>wlan0</option>
        </select>
        <button type="submit" style="margin-left:10px;">Chay ca 2</button>
    </form>

    {% if ran %}
    <h3>Ping</h3>
    <pre>{{ ping_out }}</pre>
    <h3>Traceroute</h3>
    <pre>{{ trace_out }}</pre>
    {% endif %}
</body>
</html>
"""


@nettools_bp.route("/nettools/ping", methods=["GET", "POST"])
def ping_route():
    host = (request.form.get("host") or "").strip()
    iface = request.form.get("iface", "eth0")
    ran = request.method == "POST" and bool(host)

    ping_out = trace_out = ""
    if ran:
        if not _host_hop_le(host):
            ping_out = trace_out = ("(dia chi khong hop le - chi cho chu, so va "
                                    "cac dau . - : , khong duoc bat dau bang dau -)")
        else:
            ping_out = run_ping(host, iface=iface)
            trace_out = run_traceroute(host, iface=iface)

    return render_template_string(
        PING_TEMPLATE, host=host, iface=iface, ran=ran,
        ping_out=ping_out, trace_out=trace_out,
    )


if __name__ == "__main__":
    import sys
    host = sys.argv[1] if len(sys.argv) > 1 else "8.8.8.8"
    iface = sys.argv[2] if len(sys.argv) > 2 else "eth0"
    print("=== PING ===")
    print(run_ping(host, iface=iface))
    print("=== TRACEROUTE ===")
    print(run_traceroute(host, iface=iface))
