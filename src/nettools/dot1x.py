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
            return {"ok": False, "error": "Chua cai eapoltest (thieu eapol_test).", "success": None, "output": ""}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "Qua thoi gian cho phan hoi RADIUS.", "success": None, "output": ""}
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


DOT1X_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>802.1X Testing - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: #eee; padding: 20px; }
        h1 { color: #4CAF50; }
        a { color: #4CAF50; }
        label { display: block; margin-top: 10px; }
        input[type=text], input[type=password], input[type=number], select {
            padding: 8px; width: 100%; max-width: 420px; background: #333; color: #eee;
            border: 1px solid #555; box-sizing: border-box;
        }
        button { padding: 9px 18px; background: #4CAF50; color: white; border: none;
            border-radius: 4px; cursor: pointer; margin-top: 14px; }
        pre { background: #111; padding: 12px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; }
        .err { background: #4a2d2d; border-left: 4px solid #f44336; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .ok { background: #2d4a2d; border-left: 4px solid #4CAF50; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .unknown { background: #4a3d2d; border-left: 4px solid #ff9800; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .hint { color: #999; font-size: 13px; }
    </style>
</head>
<body>
    <h1>🔐 802.1X Testing</h1>
    <p><a href="/nettools">← Network Tools</a></p>
    <p class="hint">Dung <code>eapol_test</code> - chi noi UDP truc tiep toi RADIUS server,
    <strong>KHONG dung den eth0/wlan0</strong>, nen an toan khong lam gian doan ket noi hien tai.
    Neu khong co RADIUS server that, cong cu van chay duoc nhung se bao "khong ket luan duoc"
    thay vi thanh cong/that bai ro rang.</p>

    <form method="POST">
        <label>RADIUS Server IP:</label>
        <input type="text" name="radius_ip" value="{{ radius_ip or '' }}" required placeholder="vd 192.168.1.10">
        <label>RADIUS Port:</label>
        <input type="number" name="radius_port" value="{{ radius_port or 1812 }}" style="max-width:100px;">
        <label>Shared Secret:</label>
        <input type="text" name="radius_secret" value="{{ radius_secret or '' }}" required>

        <label>EAP Method:</label>
        <select name="eap" id="eapSel" onchange="togglePhase2()">
            {% for m in eap_methods %}
            <option value="{{ m }}" {{ 'selected' if m==eap else '' }}>{{ m }}</option>
            {% endfor %}
        </select>

        <div id="phase2box">
            <label>Phase 2 Auth (chi ap dung PEAP/TTLS):</label>
            <select name="phase2">
                {% for p in phase2_methods %}
                <option value="{{ p }}" {{ 'selected' if p==phase2 else '' }}>{{ p }}</option>
                {% endfor %}
            </select>
        </div>

        <label>Identity/Username:</label>
        <input type="text" name="identity" value="{{ identity or '' }}" required>
        <label>Password:</label>
        <input type="password" name="password" value="{{ password or '' }}" required>

        <button type="submit">Chay Test</button>
    </form>
    <script>
      function togglePhase2(){
        var eap = document.getElementById('eapSel').value;
        document.getElementById('phase2box').style.display =
          (eap === 'PEAP' || eap === 'TTLS') ? 'block' : 'none';
      }
      togglePhase2();
    </script>

    {% if ran %}
        {% if result.error %}
        <div class="err">Loi: {{ result.error }}</div>
        {% elif result.success is sameas true %}
        <div class="ok">✅ EAP-SUCCESS - Xac thuc thanh cong.</div>
        {% elif result.success is sameas false %}
        <div class="err">❌ EAP-FAILURE - Xac thuc that bai (kiem tra lai username/password/cau hinh RADIUS).</div>
        {% else %}
        <div class="unknown">⚠️ Khong ket luan duoc (co the RADIUS server khong phan hoi, sai IP/secret,
        hoac khong co RADIUS that trong moi truong nay).</div>
        {% endif %}
        <h3 style="color:#4CAF50;">Output day du</h3>
        <pre>{{ result.output }}</pre>
    {% endif %}
</body>
</html>
"""


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
