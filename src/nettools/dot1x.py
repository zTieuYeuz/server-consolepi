# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi Network Tools - 802.1X Testing (netool.io Phan 10)

Dung eapol_test (di kem goi eapoltest) de test truc tiep voi RADIUS server
qua UDP - HOAN TOAN KHONG dung toi bat ky interface mang nao (eth0/wlan0),
vi eapol_test tu lam ca vai tro Authenticator lan Supplicant noi bo, chi
noi UDP toi RADIUS server. Vi vay AN TOAN, khong lam gian doan ket noi
hien tai tren bat ky cong nao.

(Che do khac - wpa_supplicant -D wired -i eth0 - se CHIEM QUYEN dieu khien
that su cong Ethernet va co the lam rot ket noi hien tai. KHONG trien khai
che do do trong ban nay de tranh rui ro lam mat ket noi quan ly toi Pi;
eapol_test da du de kiem tra cau hinh RADIUS/EAP truoc khi trien khai that.)
"""
from consolesystem.core import taisan as _taisan
import os
import subprocess
import tempfile

from flask import request, render_template_string

from . import nettools_bp

EAP_METHODS = ["PEAP", "TTLS", "MD5", "MSCHAPV2"]
PHASE2_METHODS = ["PAP", "MSCHAPV2", "MD5", "GTC"]


def build_conf(eap, identity, password, phase2=None):
    lines = ["network={", "    key_mgmt=IEEE8021X", f'    eap={eap}']
    lines.append(f'    identity="{identity}"')
    lines.append(f'    anonymous_identity="{identity}"')
    lines.append(f'    password="{password}"')
    if eap in ("PEAP", "TTLS") and phase2:
        lines.append(f'    phase2="auth={phase2}"')
    lines.append("    eapol_flags=0")
    lines.append("}")
    return "\n".join(lines)


def run_eapol_test(radius_ip, radius_port, radius_secret, eap, identity, password, phase2=None, timeout=15):
    """
    Tra ve {"ok": bool, "error": str|None, "success": bool|None, "output": str}
    success=None nghia la khong ket luan duoc (vd RADIUS khong phan hoi).
    """
    # Kiem tra truoc khi goi eapol_test. LOI THAT (thu ban ISO 23/09/2026):
    # bam Chay voi o trong -> eapol_test chet voi "wpa_init_conf: Assertion
    # `0' failed" hien nguyen cho nguoi dung. Dau "-" o dau cung bi chan de
    # gia tri khong bi hieu nham thanh tuy chon dong lenh.
    radius_ip = (radius_ip or "").strip()
    identity = (identity or "").strip()
    try:
        radius_port = int(str(radius_port).strip() or 1812)
    except ValueError:
        radius_port = 0
    loi = None
    if not radius_ip or radius_ip.startswith("-") or " " in radius_ip:
        loi = "Nhập địa chỉ IP của RADIUS server."
    elif not 1 <= radius_port <= 65535:
        loi = "Cổng RADIUS phải là số từ 1 đến 65535 (thường là 1812)."
    elif not radius_secret:
        loi = "Nhập Shared Secret (khoá chung cấu hình trên RADIUS server)."
    elif not identity:
        loi = "Nhập Identity/Username để thử đăng nhập."
    if loi:
        return {"ok": False, "error": loi, "success": None, "output": ""}

    conf_text = build_conf(eap, identity, password, phase2)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
        f.write(conf_text)
        conf_path = f.name

    try:
        cmd = [
            "eapol_test", f"-c{conf_path}", f"-a{radius_ip}",
            f"-p{radius_port}", f"-s{radius_secret}", f"-t{timeout}",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
        except FileNotFoundError:
            return {"ok": False, "error": "Chưa cài eapoltest (thiếu eapol_test).", "success": None, "output": ""}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "Quá thời gian chờ phản hồi RADIUS.", "success": None, "output": ""}
    finally:
        try:
            os.unlink(conf_path)
        except OSError:
            pass

    output = result.stdout + result.stderr
    if "SUCCESS" in output and "CTRL-EVENT-EAP-SUCCESS" in output:
        success = True
    elif "CTRL-EVENT-EAP-FAILURE" in output or "FAILURE" in output:
        success = False
    else:
        success = None

    return {"ok": True, "error": None, "success": success, "output": output}


DOT1X_TEMPLATE = _taisan.doc("nettools/dot1x.DOT1X_TEMPLATE.html")


@nettools_bp.route("/nettools/dot1x", methods=["GET", "POST"])
def dot1x_route():
    ran = request.method == "POST"
    f = request.form

    result = None
    if ran:
        result = run_eapol_test(
            f.get("radius_ip", ""), f.get("radius_port", 1812), f.get("radius_secret", ""),
            f.get("eap", "PEAP"), f.get("identity", ""), f.get("password", ""),
            f.get("phase2", "MSCHAPV2"),
        )

    return render_template_string(
        DOT1X_TEMPLATE, ran=ran, result=result,
        eap_methods=EAP_METHODS, phase2_methods=PHASE2_METHODS,
        radius_ip=f.get("radius_ip") if ran else None,
        radius_port=f.get("radius_port") if ran else 1812,
        radius_secret=f.get("radius_secret") if ran else None,
        eap=f.get("eap") if ran else "PEAP",
        phase2=f.get("phase2") if ran else "MSCHAPV2",
        identity=f.get("identity") if ran else None,
        password=f.get("password") if ran else None,
    )


if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) < 5:
        print("Usage: python3 -m nettools.dot1x <radius_ip> <secret> <identity> <password> [eap] [phase2]")
        sys.exit(1)
    radius_ip, secret, identity, password = sys.argv[1:5]
    eap = sys.argv[5] if len(sys.argv) > 5 else "PEAP"
    phase2 = sys.argv[6] if len(sys.argv) > 6 else "MSCHAPV2"
    print(json.dumps(
        run_eapol_test(radius_ip, 1812, secret, eap, identity, password, phase2),
        indent=2, ensure_ascii=False
    ))
