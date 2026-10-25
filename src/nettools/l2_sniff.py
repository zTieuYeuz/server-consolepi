# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi Network Tools - STP/LACP Detection (netool.io Phan 4) +
VLAN Tag Detection (netool.io Phan 5), gop chung 1 lan sniff cho do
ton thoi gian cho.

Da xac nhan tren may nay (Pi 4, driver bcmgenet): rx-vlan-offload la
"off [fixed]" tren eth0 -> tag VLAN se tu nhien xuat hien khi sniff bang
Scapy, KHONG can mua them USB-Ethernet adapter nhu tai lieu nghien cuu
ban dau lo ngai (tai lieu do gia dinh sai la Pi 3 dung chip smsc95xx).
"""
from consolesystem.core import taisan as _taisan
from flask import request, render_template_string

from . import nettools_bp


def _cong_mac_dinh():
    """Cong mac dinh cho o chon - cong co day that cua may nay (xem
    ui/phancung.py). Truoc day viet cung "eth0" nen chi dung tren Pi."""
    from ui.phancung import cong_mac_dinh
    return cong_mac_dinh()


def _o_chon_cong(dang_chon=""):
    """Cac the <option> liet ke dung cac cong THAT dang co tren may."""
    from ui.phancung import o_chon_cong
    return o_chon_cong(dang_chon)


def run_l2_scan(iface=None, duration=15):
    """
    Sniff 1 lan tren iface trong `duration` giay, phan loai goi theo STP
    (BPDU, dst MAC 01:80:c2:00:00:00), LACP (ethertype 0x8809), va VLAN
    tag (lop Dot1Q trong bat ky goi nao bat duoc).

    Tra ve: {"ok", "error", "stp": [...], "lacp": [...], "vlans": {vid: count}}
    """
    if iface is None:
        iface = _cong_mac_dinh()
    try:
        from scapy.all import sniff, STP, Dot1Q
        from scapy.contrib.lacp import LACP
    except ImportError as e:
        return {"ok": False, "error": f"Lỗi import scapy: {e}", "stp": [], "lacp": [], "vlans": {}}

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
        return {"ok": False, "error": "Không đủ quyền sniff (cần chạy dưới quyền root).", "stp": [], "lacp": [], "vlans": {}}
    except OSError as e:
        return {"ok": False, "error": f"Lỗi khi sniff: {e}", "stp": [], "lacp": [], "vlans": {}}

    return {
        "ok": True, "error": None,
        "stp": list(stp_seen.values()),
        "lacp": list(lacp_seen.values()),
        "vlans": dict(sorted(vlan_counts.items())),
    }


L2_TEMPLATE = _taisan.doc("nettools/l2_sniff.L2_TEMPLATE.html")


@nettools_bp.route("/nettools/l2-scan", methods=["GET", "POST"])
def l2_scan_route():
    iface = request.form.get("iface") or _cong_mac_dinh()
    duration = int(request.form.get("duration", 15) or 15)
    ran = request.method == "POST"
    result = run_l2_scan(iface=iface, duration=duration) if ran else None
    return render_template_string(L2_TEMPLATE, o_chon_cong=_o_chon_cong(iface), iface=iface, duration=duration, ran=ran, result=result)


if __name__ == "__main__":
    import sys
    import json
    iface = sys.argv[1] if len(sys.argv) > 1 else _cong_mac_dinh()
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    print(json.dumps(run_l2_scan(iface=iface, duration=duration), indent=2, ensure_ascii=False))
