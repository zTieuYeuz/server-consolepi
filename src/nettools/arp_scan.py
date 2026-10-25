# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi Network Tools - ARP Scan (netool.io Phan 3)

Quet toan bo thiet bi dang online trong subnet bang arp-scan. Hoat dong ca
voi thiet bi chan ping/firewall vi ARP khong di qua tuong lua IP.
"""
from consolesystem.core import taisan as _taisan
import re
import subprocess

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

# Dinh dang chuan cua arp-scan --localnet (moi dong 1 thiet bi):
# 192.168.1.1<TAB>aa:bb:cc:dd:ee:ff<TAB>Vendor Name Here
ARP_LINE_RE = re.compile(
    r"^(\d{1,3}(?:\.\d{1,3}){3})\t([0-9a-fA-F:]{17})\t(.*)$"
)


def run_arp_scan(iface=None, target=None, timeout=30):
    """
    Chay arp-scan tren 1 interface. Neu target (CIDR/IP) duoc chi dinh thi
    quet dai do, khong thi dung --localnet (doi hoi interface phai co IP).

    Tra ve: {"ok": bool, "error": str|None, "hosts": [{"ip","mac","vendor"}]}
    """
    if iface is None:
        iface = _cong_mac_dinh()
    cmd = ["arp-scan", f"--interface={iface}"]
    cmd += [target] if target else ["--localnet"]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError:
        return {"ok": False, "error": "Chưa cài arp-scan.", "hosts": []}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Quá thời gian chờ.", "hosts": []}

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


ARP_SCAN_TEMPLATE = _taisan.doc("nettools/arp_scan.ARP_SCAN_TEMPLATE.html")


@nettools_bp.route("/nettools/arp-scan", methods=["GET", "POST"])
def arp_scan_route():
    iface = request.form.get("iface") or _cong_mac_dinh()
    target = (request.form.get("target") or "").strip() or None
    ran = request.method == "POST"

    result = run_arp_scan(iface=iface, target=target) if ran else None

    return render_template_string(
        ARP_SCAN_TEMPLATE, o_chon_cong=_o_chon_cong(iface), iface=iface, target=target, ran=ran, result=result
    )


if __name__ == "__main__":
    import sys
    import json

    iface = sys.argv[1] if len(sys.argv) > 1 else _cong_mac_dinh()
    target = sys.argv[2] if len(sys.argv) > 2 else None
    print(json.dumps(run_arp_scan(iface=iface, target=target), indent=2, ensure_ascii=False))
