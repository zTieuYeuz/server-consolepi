# Console System - (c) 2026 zTieuYeuz. All rights reserved.
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
from consolesystem.core import taisan as _taisan
from consolesystem.core.nhatky import bo_qua as _bo_qua
import time

from flask import request, render_template_string

from . import nettools_bp
from ui import duongdan as _DD

AUDIT_LOG = _DD.LOG_NETMIKO

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
    except Exception as _loi:
        _bo_qua(_loi)


def test_connection(host, device_type, username, password, test_cmd, port=22, timeout=10):
    """Chi chay 1 lenh DOC (exec mode), khong vao config mode. Dung de
    xac nhan ket noi/quyen han truoc khi lam gi rui ro hon."""
    try:
        from netmiko import ConnectHandler
        from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
    except ImportError as e:
        return {"ok": False, "error": f"Lỗi import netmiko: {e}", "output": ""}

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
        return {"ok": False, "error": "Sai username/password hoặc bị từ chối đăng nhập.", "output": ""}
    except NetmikoTimeoutException:
        _audit(host, device_type, "test", [test_cmd], "TIMEOUT")
        return {"ok": False, "error": f"Không kết nối được tới {host} (timeout).", "output": ""}
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
        return {"ok": False, "error": f"Lỗi import netmiko: {e}", "output": "", "saved": False}

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
        return {"ok": False, "error": "Sai username/password hoặc bị từ chối đăng nhập.", "output": "", "saved": False}
    except NetmikoTimeoutException:
        _audit(host, device_type, "run", commands, "TIMEOUT")
        return {"ok": False, "error": f"Không kết nối được tới {host} (timeout).", "output": "", "saved": False}
    except Exception as e:
        _audit(host, device_type, "run", commands, f"ERROR: {e}")
        return {"ok": False, "error": str(e), "output": "", "saved": False}

    _audit(host, device_type, "run", commands, "OK" + (" + SAVED" if save else ""))
    return {"ok": True, "error": None, "output": output, "saved": save}


FORM_TEMPLATE = _taisan.doc("nettools/netmiko_tool.FORM_TEMPLATE.html")

PREVIEW_TEMPLATE = _taisan.doc("nettools/netmiko_tool.PREVIEW_TEMPLATE.html")


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
