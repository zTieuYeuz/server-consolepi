# Console System - (c) 2026 zTieuYeuz. All rights reserved.
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
from consolesystem.core import taisan as _taisan
import json
import subprocess

from flask import render_template_string

from . import nettools_bp



def _ip_mo_duoc(ip):
    """IP quan ly co mo duoc tu may nay khong (khong phai loopback/0.0.0.0/link-local)."""
    import ipaddress
    try:
        a = ipaddress.ip_address((ip or "").strip())
    except ValueError:
        return False
    return not (a.is_loopback or a.is_unspecified or a.is_link_local or a.is_multicast)

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
        return {"ok": False, "error": "Chưa cài lldpd/lldpcli.", "raw": None, "neighbors": []}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Quá thời gian chờ lldpcli.", "raw": None, "neighbors": []}

    if result.returncode != 0:
        return {"ok": False, "error": result.stderr.strip() or "lldpcli loi.", "raw": None, "neighbors": []}

    try:
        raw = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return {"ok": False, "error": "Không đọc được JSON từ lldpcli.", "raw": result.stdout, "neighbors": []}

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
                # Router nha (vd ASUS RT-AX55) quang ba 127.0.0.1 - bam "Mo web"
                # se mo nham CHINH may nguoi dung. Chi cho mo IP dung duoc.
                "mgmt_mo_duoc": _ip_mo_duoc(mgmt_ip),
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


LLDP_TEMPLATE = _taisan.doc("nettools/lldp.LLDP_TEMPLATE.html")


@nettools_bp.route("/nettools/lldp")
def lldp_route():
    result = get_lldp_neighbors()
    raw_json = json.dumps(result.get("raw"), indent=2, ensure_ascii=False) if result.get("raw") else "(khong co)"
    return render_template_string(LLDP_TEMPLATE, result=result, raw_json=raw_json)


if __name__ == "__main__":
    print(json.dumps(get_lldp_neighbors(), indent=2, ensure_ascii=False))
