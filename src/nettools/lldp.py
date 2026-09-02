"""
Console Pi Network Tools - LLDP/CDP Discovery (netool.io Phan 1)
Kem theo PoE passive detection qua LLDP-MED (netool.io Phan 11) - cung
1 lenh lldpcli nen khong ton them cong.

LICH SU LOI DA SUA (quan trong, doc truoc khi sua tiep):
Ban dau ham parse gia dinh sai cau truc JSON cua lldpcli: tuong rang
"chassis" la mot dict ma MOI KHOA la ten dong (dat theo hostname thiet bi
lang gieng), vi du {"RT-AX55": {"name": [...], ...}}. Thuc te (kiem chung
tren lldpd 1.0.x that, ca goi tin LLDP lan CDP) khong phai vay: "chassis" la
mot LIST chua 1 dict, va dict do co cac KHOA CO DINH ("id", "name", "descr",
"mgmt-ip", "capability"...), moi khoa lai tro toi MOT LIST khac. Code cu kiem
tra `isinstance(info, dict)` truoc khi doc - nhung "info" o day luon la list,
nen dieu kien do LUON SAI va vong lap khong bao gio chay. Hau qua: ten thiet
bi luon hien "?", Mgmt IP luon hien "-", va cot Port hien nguyen van chuoi
Python `[{'type': 'mac', 'value': '...'}]` thay vi gia tri that.
Trang web chi con dung duoc nho khoi JSON tho hien them ben duoi - nhung voi
nguoi khong quen doc JSON thi coi nhu trang nay vo dung.

Sua bang cach doc dung cau truc that: moi truong la list, phan tu dau la
dict co the co "value" (chuoi don gian) hoac ca "type" + "value" (dinh danh
nhu MAC/ifname). Ham _gt() lay ra phan tu dau do mot cach an toan du lldpd
tra ve kieu gi.
"""
import json
import subprocess

from flask import render_template_string

from . import nettools_bp


def _gt(node):
    """
    'Get first' - lay phan tu dau cua mot truong lldpcli, luon tra ve dict.
    lldpcli JSON bieu dien MOI truong duoi dang list (thuong 1 phan tu, doi
    khi rong). Ham nay chiu duoc ca truong hop hiem la dict truc tiep, va
    khong bao gio nem loi du du lieu thieu hut kieu nao.
    """
    if isinstance(node, list):
        return node[0] if node and isinstance(node[0], dict) else {}
    if isinstance(node, dict):
        return node
    return {}


def _chuoi(d, khoa, mac_dinh=""):
    """Lay truong dang chuoi don gian, vd SysName/SysDescr/MgmtIP: {"value": ...}."""
    if not isinstance(d, dict):
        return mac_dinh
    v = _gt(d.get(khoa, [])).get("value")
    return str(v) if v not in (None, "") else mac_dinh


def _dinh_danh(d, khoa="id"):
    """
    Lay truong dinh danh (ChassisID/PortID) - co ca 'type' lan 'value',
    vd {"type": "mac", "value": "aa:bb:..."} hoac {"type": "local", "value": "ten"}.
    """
    if not isinstance(d, dict):
        return ""
    node = _gt(d.get(khoa, []))
    v = str(node.get("value", "")).strip()
    t = str(node.get("type", "")).strip()
    if not v:
        return ""
    return f"{v} ({t})" if t and t not in ("mac",) else v


def _nang_luc(chassis):
    """Danh sach nang luc thiet bi dang BAT (vd Router, Bridge, Switch)."""
    caps = chassis.get("capability", [])
    caps = caps if isinstance(caps, list) else [caps]
    return [c.get("type") for c in caps
            if isinstance(c, dict) and c.get("enabled") and c.get("type")]


def get_lldp_neighbors():
    """
    Tra ve {"ok": bool, "error": str|None, "raw": dict|None, "neighbors": [...]}
    Moi neighbor: {iface, protocol, remote_name, remote_descr, chassis_id,
                   mgmt_ip, port_id, port_descr, capabilities, age, poe_info}
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
            age = iface_entry.get("age", "")

            chassis_list = iface_entry.get("chassis", [])
            chassis_list = chassis_list if isinstance(chassis_list, list) else [chassis_list]
            chassis = chassis_list[0] if chassis_list and isinstance(chassis_list[0], dict) else {}

            remote_name = _chuoi(chassis, "name")
            remote_descr = _chuoi(chassis, "descr")
            mgmt_ip = _chuoi(chassis, "mgmt-ip")
            chassis_id = _dinh_danh(chassis, "id")
            capabilities = _nang_luc(chassis)

            if not remote_name:
                # Nhieu thiet bi (dac biet IoT/consumer) khong dat SysName -
                # dung ChassisID (thuong la MAC) de con co gi do de nhan biet
                remote_name = chassis_id or "(khong ro ten)"

            port_list = iface_entry.get("port", [])
            port_list = port_list if isinstance(port_list, list) else [port_list]
            port = port_list[0] if port_list and isinstance(port_list[0], dict) else {}
            port_id = _dinh_danh(port, "id")
            port_descr = _chuoi(port, "descr")

            poe_info = _find_power_info(iface_entry)

            neighbors.append({
                "iface": iface_name, "protocol": via, "age": age,
                "remote_name": remote_name, "remote_descr": remote_descr,
                "chassis_id": chassis_id, "mgmt_ip": mgmt_ip,
                "port_id": port_id, "port_descr": port_descr,
                "capabilities": capabilities, "poe_info": poe_info,
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
        .hint { color: #999; font-size: 13px; }
        .err { background: #4a2d2d; border-left: 4px solid #f44336; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        details summary { cursor: pointer; color: #999; margin-top: 20px; }
        pre { background: #111; padding: 12px; border-radius: 4px; overflow-x: auto; font-size: 12px; max-height: 400px; }

        /* --- The thong tin cho tung thiet bi lang gieng --- */
        .card { background:#2a2a2a; border:1px solid #3a3a3a; border-left: 4px solid #4CAF50;
                border-radius: 6px; padding: 16px 18px; margin-top: 16px; }
        .card h2 { margin: 0 0 4px; font-size: 19px; color: #fff; }
        .card .badge-proto { display:inline-block; background:#333; color:#4CAF50;
                border:1px solid #4CAF50; border-radius: 4px; font-size: 11px;
                padding: 1px 7px; margin-left: 8px; vertical-align: 2px; }
        .card .via-if { color:#999; font-size: 13px; margin: 2px 0 14px; }
        .grid { display: grid; grid-template-columns: 160px 1fr; gap: 8px 14px; align-items: start; }
        .grid dt { color: #999; font-size: 13px; padding-top: 2px; }
        .grid dd { margin: 0; word-break: break-word; }
        .grid dd code { background:#151515; padding: 2px 6px; border-radius: 3px; font-size: 13px; }
        .descr-box { background:#151515; border-radius: 4px; padding: 8px 10px; font-size: 12.5px;
                white-space: pre-wrap; color:#ccc; max-height: 130px; overflow-y: auto; }
        .caps { display:flex; gap:6px; flex-wrap: wrap; }
        .cap-chip { background:#1f3a24; color:#8fd99a; border:1px solid #2e5c37;
                border-radius: 10px; padding: 2px 10px; font-size: 12px; }
        .none-val { color: #777; font-style: italic; }
    </style>
</head>
<body>
    <h1>🔗 LLDP/CDP Discovery</h1>
    <p><a href="/nettools">← Network Tools</a></p>
    <p class="hint">Thiet bi Pi lang nghe quang ba LLDP va CDP tren tung cong mang.
        Cam day vao mot switch/router co bat cac giao thuc nay, doi 10-60 giay
        (thiet bi thuong quang ba moi 30-60s) roi bam Quet lai.</p>
    <p><a class="btn" href="/nettools/lldp">🔄 Quet lai</a></p>

    {% if result.error %}
    <div class="err">Loi: {{ result.error }}</div>
    {% else %}
        {% if result.neighbors %}
            {% for n in result.neighbors %}
            <div class="card">
                <h2>{{ n.remote_name }}<span class="badge-proto">{{ n.protocol }}</span></h2>
                <p class="via-if">Thay qua cong <strong>{{ n.iface }}</strong> cua Pi
                    {% if n.age %}&middot; da thay {{ n.age }}{% endif %}</p>
                <dl class="grid">
                    <dt>Dia chi quan ly (Mgmt IP)</dt>
                    <dd>
                        {% if n.mgmt_ip %}
                            <code>{{ n.mgmt_ip }}</code>
                            &nbsp;<a href="http://{{ n.mgmt_ip }}" target="_blank" rel="noopener">Mo web ↗</a>
                        {% else %}<span class="none-val">Thiet bi khong quang ba IP quan ly</span>{% endif %}
                    </dd>

                    <dt>Cong tren thiet bi do</dt>
                    <dd>
                        {% if n.port_descr %}<strong>{{ n.port_descr }}</strong>{% endif %}
                        {% if n.port_id and n.port_id != n.port_descr %}
                            <br><code style="font-size:12px;">{{ n.port_id }}</code>
                        {% endif %}
                        {% if not n.port_descr and not n.port_id %}<span class="none-val">-</span>{% endif %}
                    </dd>

                    <dt>Chassis ID</dt>
                    <dd>{{ n.chassis_id or '<span class="none-val">-</span>'|safe }}</dd>

                    <dt>Nang luc thiet bi</dt>
                    <dd>
                        {% if n.capabilities %}
                        <div class="caps">
                            {% for c in n.capabilities %}<span class="cap-chip">{{ c }}</span>{% endfor %}
                        </div>
                        {% else %}<span class="none-val">Khong quang ba</span>{% endif %}
                    </dd>

                    <dt>PoE (LLDP-MED)</dt>
                    <dd>{{ n.poe_info or '<span class="none-val">Khong co du lieu</span>'|safe }}</dd>

                    {% if n.remote_descr %}
                    <dt>Mo ta he thong</dt>
                    <dd><div class="descr-box">{{ n.remote_descr }}</div></dd>
                    {% endif %}
                </dl>
            </div>
            {% endfor %}
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
        <summary>Xem JSON tho tu lldpcli (chi de doi chieu ky thuat neu can - khong can doc thuong xuyen)</summary>
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
