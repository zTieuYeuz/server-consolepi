"""
Console Pi Network Tools - Netmiko tu dong cau hinh switch (netool.io Phan 6)

DAY LA CONG CU GHI THAY DOI LEN THIET BI THAT QUA SSH. Vi khong co
switch/router lab de test truoc, bat buoc phai co luong an toan:

  1. /nettools/netmiko            - form nhap thong tin
  2. /nettools/netmiko/test       - CHI chay 1 lenh doc (send_command,
                                     KHONG vao config mode) de xac nhan
                                     ket noi/quyen han truoc khi lam gi khac
  3. /nettools/netmiko/preview    - CHUA KET NOI GI CA, chi hien lai
                                     chinh xac lenh se chay de doc lai
  4. /nettools/netmiko/run        - that su ket noi + send_config_set().
                                     Checkbox "luu vinh vien" MAC DINH TAT.

Moi phien chay (test/run) deu duoc ghi log vao
/var/log/console-pi-netmiko.log (KHONG ghi mat khau vao log).
"""
import time

from flask import request, render_template_string

from . import nettools_bp

AUDIT_LOG = "/var/log/console-pi-netmiko.log"

DEVICE_TYPES = [
    "cisco_ios", "cisco_xe", "cisco_nxos", "arista_eos",
    "hp_comware", "hp_procurve", "juniper_junos",
    "mikrotik_routeros", "ubiquiti_edge", "linux",
]


def _audit(host, device_type, action, commands, result_summary):
    line = (
        f"{time.strftime('%Y-%m-%d %H:%M:%S')} | host={host} | type={device_type} | "
        f"action={action} | commands={commands!r} | result={result_summary}\n"
    )
    try:
        with open(AUDIT_LOG, "a") as f:
            f.write(line)
    except Exception:
        pass


def test_connection(host, device_type, username, password, test_cmd, port=22, timeout=10):
    """Chi chay 1 lenh DOC (exec mode), khong vao config mode. Dung de
    xac nhan ket noi/quyen han truoc khi lam gi rui ro hon."""
    try:
        from netmiko import ConnectHandler
        from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
    except ImportError as e:
        return {"ok": False, "error": f"Loi import netmiko: {e}", "output": ""}

    device = {
        "device_type": device_type, "host": host, "username": username,
        "password": password, "port": int(port), "timeout": timeout,
    }
    try:
        conn = ConnectHandler(**device)
        output = conn.send_command(test_cmd)
        conn.disconnect()
    except NetmikoAuthenticationException:
        _audit(host, device_type, "test", [test_cmd], "AUTH FAILED")
        return {"ok": False, "error": "Sai username/password hoac bi tu choi dang nhap.", "output": ""}
    except NetmikoTimeoutException:
        _audit(host, device_type, "test", [test_cmd], "TIMEOUT")
        return {"ok": False, "error": f"Khong ket noi duoc toi {host} (timeout).", "output": ""}
    except Exception as e:
        _audit(host, device_type, "test", [test_cmd], f"ERROR: {e}")
        return {"ok": False, "error": str(e), "output": ""}

    _audit(host, device_type, "test", [test_cmd], "OK")
    return {"ok": True, "error": None, "output": output}


def run_config(host, device_type, username, password, commands, save=False, port=22, timeout=10):
    """That su ket noi va chay send_config_set(). Tuy chon save_config()
    (write memory) neu save=True - MAC DINH KHONG luu."""
    try:
        from netmiko import ConnectHandler
        from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
    except ImportError as e:
        return {"ok": False, "error": f"Loi import netmiko: {e}", "output": "", "saved": False}

    device = {
        "device_type": device_type, "host": host, "username": username,
        "password": password, "port": int(port), "timeout": timeout,
    }
    try:
        conn = ConnectHandler(**device)
        output = conn.send_config_set(commands)
        saved = False
        if save:
            save_out = conn.save_config()
            output += "\n--- SAVE CONFIG ---\n" + str(save_out)
            saved = True
        conn.disconnect()
    except NetmikoAuthenticationException:
        _audit(host, device_type, "run", commands, "AUTH FAILED")
        return {"ok": False, "error": "Sai username/password hoac bi tu choi dang nhap.", "output": "", "saved": False}
    except NetmikoTimeoutException:
        _audit(host, device_type, "run", commands, "TIMEOUT")
        return {"ok": False, "error": f"Khong ket noi duoc toi {host} (timeout).", "output": "", "saved": False}
    except Exception as e:
        _audit(host, device_type, "run", commands, f"ERROR: {e}")
        return {"ok": False, "error": str(e), "output": "", "saved": False}

    _audit(host, device_type, "run", commands, "OK" + (" + SAVED" if save else ""))
    return {"ok": True, "error": None, "output": output, "saved": save}


FORM_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Netmiko Config - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: #eee; padding: 20px; }
        h1 { color: #4CAF50; }
        h3 { color: #4CAF50; margin-top: 20px; }
        a { color: #4CAF50; }
        label { display: block; margin-top: 10px; }
        input[type=text], input[type=password], input[type=number], select, textarea {
            padding: 8px; width: 100%; max-width: 480px; background: #333; color: #eee;
            border: 1px solid #555; box-sizing: border-box; font-family: monospace;
        }
        textarea { height: 120px; }
        button { padding: 9px 18px; background: #4CAF50; color: white; border: none;
            border-radius: 4px; cursor: pointer; margin-top: 12px; margin-right: 8px; }
        button.secondary { background: #607d8b; }
        pre { background: #111; padding: 12px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; }
        .err { background: #4a2d2d; border-left: 4px solid #f44336; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .ok { background: #2d4a2d; border-left: 4px solid #4CAF50; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .warn { background: #4a3d2d; border-left: 4px solid #ff9800; padding: 12px 16px; border-radius: 4px; margin: 14px 0; }
    </style>
</head>
<body>
    <h1>⚙️ Netmiko Config</h1>
    <p><a href="/nettools">← Network Tools</a> &nbsp;|&nbsp;
    {% if mode == 'test' %}
    <a href="/nettools/netmiko">Sang form Cau hinh (ghi)</a>
    {% else %}
    <a href="/nettools/netmiko/test-form">🔍 Sang form Test ket noi (chi doc)</a>
    {% endif %}
    </p>
    <div class="warn">⚠️ Cong cu nay GHI thay doi len thiet bi that qua SSH.
    Luon <strong>Test ket noi</strong> truoc, roi <strong>Xem truoc lenh</strong>,
    cuoi cung moi <strong>Xac nhan va chay</strong>. Khong tu dong luu vinh vien
    (write memory) tru khi ban tich rieng.</div>

    <form method="POST" action="{{ action_url }}">
        <label>Dia chi IP switch:</label>
        <input type="text" name="host" value="{{ host or '' }}" required placeholder="vd 192.168.1.1">

        <label>Device type:</label>
        <select name="device_type">
            {% for dt in device_types %}
            <option value="{{ dt }}" {{ 'selected' if dt==device_type else '' }}>{{ dt }}</option>
            {% endfor %}
        </select>

        <label>Port SSH:</label>
        <input type="number" name="port" value="{{ port or 22 }}" style="max-width:100px;">

        <label>Username:</label>
        <input type="text" name="username" value="{{ username or '' }}" required>

        <label>Password:</label>
        <input type="password" name="password" value="{{ password or '' }}" required>

        {% if mode == 'test' %}
        <label>Lenh doc de test (khong vao config mode):</label>
        <input type="text" name="test_cmd" value="{{ test_cmd or 'show version' }}">
        <button type="submit" class="secondary">🔍 Test ket noi (chi doc)</button>
        {% else %}
        <label>Danh sach lenh cau hinh (moi dong 1 lenh):</label>
        <textarea name="commands">{{ commands_text or '' }}</textarea>
        <button type="submit">👁 Xem truoc lenh</button>
        {% endif %}
    </form>

    {% if result %}
        {% if result.error %}
        <div class="err">Loi: {{ result.error }}</div>
        {% else %}
        <div class="ok">Thanh cong{% if result.saved %} (da luu vinh vien){% endif %}.</div>
        <h3>Output</h3>
        <pre>{{ result.output }}</pre>
        {% endif %}
    {% endif %}
</body>
</html>
"""

PREVIEW_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Xem truoc lenh - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: #eee; padding: 20px; }
        h1 { color: #4CAF50; }
        a { color: #4CAF50; }
        pre { background: #111; padding: 14px; border-radius: 4px; white-space: pre-wrap; }
        .warn { background: #4a3d2d; border-left: 4px solid #ff9800; padding: 12px 16px; border-radius: 4px; margin: 14px 0; }
        label { display: flex; align-items: center; gap: 8px; margin: 14px 0; }
        button { padding: 10px 20px; background: #f44336; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button.cancel { background: #607d8b; }
    </style>
</head>
<body>
    <h1>👁 Xem truoc - CHUA KET NOI GI CA</h1>
    <p><a href="/nettools/netmiko">← Quay lai form</a></p>

    <p>Se ket noi toi <strong>{{ host }}</strong> ({{ device_type }}) va chay CHINH XAC cac lenh sau:</p>
    <pre>{{ commands_text }}</pre>

    <div class="warn">⚠️ Day la buoc ghi cau hinh THUC SU len thiet bi. Doc lai ky truoc khi xac nhan.</div>

    <form method="POST" action="/nettools/netmiko/run"
          onsubmit="return confirm('XAC NHAN chay {{ commands|length }} lenh cau hinh tren {{ host }}?');">
        <input type="hidden" name="host" value="{{ host }}">
        <input type="hidden" name="device_type" value="{{ device_type }}">
        <input type="hidden" name="port" value="{{ port }}">
        <input type="hidden" name="username" value="{{ username }}">
        <input type="hidden" name="password" value="{{ password }}">
        <input type="hidden" name="commands" value="{{ commands_text }}">
        <label>
            <input type="checkbox" name="save" value="1">
            Cung luu vinh vien (write memory / save config) - KHO HOAN TAC, mac dinh KHONG tick
        </label>
        <button type="submit">✅ Xac nhan va chay</button>
        <a href="/nettools/netmiko" class="cancel" style="display:inline-block; padding:10px 20px; background:#607d8b; color:white; border-radius:4px; text-decoration:none;">Huy</a>
    </form>
</body>
</html>
"""


@nettools_bp.route("/nettools/netmiko", methods=["GET"])
def netmiko_form():
    return render_template_string(
        FORM_TEMPLATE, action_url="/nettools/netmiko/preview", mode="preview",
        device_types=DEVICE_TYPES, result=None,
        host=None, device_type="cisco_ios", port=22, username=None, password=None,
        commands_text=None,
    )


@nettools_bp.route("/nettools/netmiko/test-form", methods=["GET"])
def netmiko_test_form():
    return render_template_string(
        FORM_TEMPLATE, action_url="/nettools/netmiko/test", mode="test",
        device_types=DEVICE_TYPES, result=None,
        host=None, device_type="cisco_ios", port=22, username=None, password=None,
        test_cmd="show version",
    )


@nettools_bp.route("/nettools/netmiko/test", methods=["POST"])
def netmiko_test_route():
    f = request.form
    result = test_connection(
        f.get("host", ""), f.get("device_type", "cisco_ios"),
        f.get("username", ""), f.get("password", ""),
        f.get("test_cmd", "show version"), f.get("port", 22),
    )
    return render_template_string(
        FORM_TEMPLATE, action_url="/nettools/netmiko/test", mode="test",
        device_types=DEVICE_TYPES, result=result,
        host=f.get("host"), device_type=f.get("device_type"), port=f.get("port"),
        username=f.get("username"), password=f.get("password"),
        test_cmd=f.get("test_cmd"),
    )


@nettools_bp.route("/nettools/netmiko/preview", methods=["POST"])
def netmiko_preview_route():
    f = request.form
    commands_text = f.get("commands", "")
    commands = [c for c in commands_text.splitlines() if c.strip()]
    return render_template_string(
        PREVIEW_TEMPLATE,
        host=f.get("host", ""), device_type=f.get("device_type", "cisco_ios"),
        port=f.get("port", 22), username=f.get("username", ""), password=f.get("password", ""),
        commands=commands, commands_text=commands_text,
    )


@nettools_bp.route("/nettools/netmiko/run", methods=["POST"])
def netmiko_run_route():
    f = request.form
    commands_text = f.get("commands", "")
    commands = [c for c in commands_text.splitlines() if c.strip()]
    save = f.get("save") == "1"

    result = run_config(
        f.get("host", ""), f.get("device_type", "cisco_ios"),
        f.get("username", ""), f.get("password", ""),
        commands, save=save, port=f.get("port", 22),
    )
    return render_template_string(
        FORM_TEMPLATE, action_url="/nettools/netmiko/preview", mode="preview",
        device_types=DEVICE_TYPES, result=result,
        host=f.get("host"), device_type=f.get("device_type"), port=f.get("port"),
        username=f.get("username"), password=None, commands_text=commands_text,
    )


if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) < 4:
        print("Usage: python3 -m nettools.netmiko_tool <host> <device_type> <username> [password]")
        sys.exit(1)
    host, device_type, username = sys.argv[1], sys.argv[2], sys.argv[3]
    password = sys.argv[4] if len(sys.argv) > 4 else input("Password: ")
    print(json.dumps(test_connection(host, device_type, username, password, "show version"), indent=2, ensure_ascii=False))
