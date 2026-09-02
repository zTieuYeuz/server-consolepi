"""
Console Pi Network Tools - LLDP/CDP Discovery (netool.io Phan 1)
Kem theo PoE passive detection qua LLDP-MED (netool.io Phan 11) - cung
1 lenh lldpcli nen khong ton them cong.

LUU Y: cau truc JSON cua lldpcli (`-f json0`) co the khac nhau it nhieu
giua cac phien ban lldpd, dac biet phan "chassis" duoc lldpd dat ten key
dong theo hostname cua thiet bi lang gieng. Ham parse duoi day co gang
doan mot cach phong thu (dung .get(), khong crash neu thieu truong), va
trang web LUON hien them JSON tho ben duoi de doi chieu neu phan tich
tu dong doan sai.
"""
import json
import subprocess

from flask import render_template_string

from . import nettools_bp


def get_lldp_neighbors():
    """
    Tra ve {"ok": bool, "error": str|None, "raw": dict|None, "neighbors": [...]}
    Moi neighbor: {iface, protocol, remote_name, remote_descr, mgmt_ip,
                   port_id, port_descr, poe_info}
    """
    try:
        result = subprocess.run(
            ["lldpcli", "show", "neighbors", "-f", "json0"],
            capture_output=True, text=True, timeout=15
        )
    except FileNotFoundError:
        return {"ok": False, "error": "Chua cai lldpd/lldpcli.", "raw": None, "neighbors": []}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Qua thoi gian cho lldpcli.", "raw": None, "neighbors": []}

    if result.returncode != 0:
        return {"ok": False, "error": result.stderr.strip() or "lldpcli loi.", "raw": None, "neighbors": []}

    try:
        raw = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return {"ok": False, "error": "Khong doc duoc JSON tu lldpcli.", "raw": result.stdout, "neighbors": []}

    neighbors = []
    lldp_section = raw.get("lldp")
    entries = lldp_section if isinstance(lldp_section, list) else [lldp_section] if lldp_section else []

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        ifaces = entry.get("interface", [])
        ifaces = ifaces if isinstance(ifaces, list) else [ifaces]
        for iface_entry in ifaces:
            if not isinstance(iface_entry, dict):
                continue
            iface_name = iface_entry.get("name", "?")
            via = iface_entry.get("via", "LLDP")

            chassis_list = iface_entry.get("chassis", [])
            chassis_list = chassis_list if isinstance(chassis_list, list) else [chassis_list]
            remote_name, remote_descr, mgmt_ip = "?", "", ""
            for c in chassis_list:
                if not isinstance(c, dict):
                    continue
                for name_key, info in c.items():
                    if not isinstance(info, dict):
                        continue
                    remote_name = info.get("name", name_key)
                    remote_descr = info.get("descr", "")
                    mgmt = info.get("mgmt-ip", [])
                    if isinstance(mgmt, list) and mgmt:
                        mgmt_ip = mgmt[0]
                    elif isinstance(mgmt, str):
                        mgmt_ip = mgmt

            port_list = iface_entry.get("port", [])
            port_list = port_list if isinstance(port_list, list) else [port_list]
            port_id, port_descr = "", ""
            for p in port_list:
                if isinstance(p, dict):
                    pid = p.get("id", {})
                    port_id = pid.get("value", "") if isinstance(pid, dict) else str(pid)
                    port_descr = p.get("descr", "")

            # Tim TLV lien quan PoE/power o bat ky cap nao (ten key khac nhau
            # giua cac ban lldpd: "med-power", "power", "power-via-mdi"...)
            poe_info = _find_power_info(iface_entry)

            neighbors.append({
                "iface": iface_name, "protocol": via,
                "remote_name": remote_name, "remote_descr": remote_descr,
                "mgmt_ip": mgmt_ip, "port_id": port_id, "port_descr": port_descr,
                "poe_info": poe_info,
            })

    return {"ok": True, "error": None, "raw": raw, "neighbors": neighbors}


def _find_power_info(node, depth=0):
    """Tim de quy bat ky key nao chua 'power' (khong phan biet hoa/thuong)."""
    if depth > 6:
        return None
    if isinstance(node, dict):
        for k, v in node.items():
            if "power" in k.lower():
                return v
        for v in node.values():
            found = _find_power_info(v, depth + 1)
            if found is not None:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_power_info(item, depth + 1)
            if found is not None:
                return found
    return None


LLDP_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>LLDP/CDP Discovery - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: #eee; padding: 20px; }
        h1 { color: #4CAF50; }
        h3 { color: #4CAF50; margin-top: 24px; }
        a { color: #4CAF50; }
        a.btn { display:inline-block; padding: 9px 16px; background: #4CAF50; color: white;
            text-decoration: none; border-radius: 4px; }
        table { width: 100%; border-collapse: collapse; margin-top: 16px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #444; }
        th { background: #2d2d2d; }
        pre { background: #111; padding: 12px; border-radius: 4px; overflow-x: auto; font-size: 12px; max-height: 400px; }
        .err { background: #4a2d2d; border-left: 4px solid #f44336; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        details summary { cursor: pointer; color: #999; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>🔗 LLDP/CDP Discovery</h1>
    <p><a href="/nettools">← Network Tools</a></p>
    <p><a class="btn" href="/nettools/lldp">🔄 Quet lai</a></p>

    {% if result.error %}
    <div class="err">Loi: {{ result.error }}</div>
    {% else %}
        {% if result.neighbors %}
        <table>
            <tr><th>Interface</th><th>Giao thuc</th><th>Ten thiet bi</th><th>Mgmt IP</th><th>Port</th><th>PoE (LLDP-MED)</th></tr>
            {% for n in result.neighbors %}
            <tr>
                <td>{{ n.iface }}</td>
                <td>{{ n.protocol }}</td>
                <td>{{ n.remote_name }}<br><small style="color:#999;">{{ n.remote_descr }}</small></td>
                <td>{{ n.mgmt_ip or '-' }}</td>
                <td>{{ n.port_descr or n.port_id or '-' }}</td>
                <td>{{ n.poe_info or 'Khong co du lieu' }}</td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p style="margin-top:16px;">Chua thay thiet bi lang gieng nao qua LLDP/CDP. Co the do:</p>
        <ul>
            <li>Switch dang cam khong bat LLDP/CDP</li>
            <li>Vua cam day, can doi 30-60s de trao doi TLV dau tien</li>
            <li>lldpd chua bat che do tuong thich CDP (kiem tra /etc/default/lldpd)</li>
        </ul>
        {% endif %}
    {% endif %}

    <details>
        <summary>Xem JSON tho tu lldpcli (de doi chieu neu bang tren thieu/sai)</summary>
        <pre>{{ raw_json }}</pre>
    </details>
</body>
</html>
"""


@nettools_bp.route("/nettools/lldp")
def lldp_route():
    result = get_lldp_neighbors()
    raw_json = json.dumps(result.get("raw"), indent=2, ensure_ascii=False) if result.get("raw") else "(khong co)"
    return render_template_string(LLDP_TEMPLATE, result=result, raw_json=raw_json)


if __name__ == "__main__":
    print(json.dumps(get_lldp_neighbors(), indent=2, ensure_ascii=False))
