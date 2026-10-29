# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Cloudflare Tunnel: trang thai (da cai, co token, dang chay) - tach tu remote.py o B3 de layout/web khong phai import tinh nang remote."""
import os
import shutil
import subprocess


from consolesystem.core import duongdan as _DD

TOKEN_FILE = _DD.FILE_CF_TOKEN                 # 2.0: trong secrets/ (sao luu cung thu muc du lieu); unit tunnel doc file nay
CONF_DIR = os.path.dirname(TOKEN_FILE)


SERVICE = "console-system-tunnel"


def da_cai():
    return shutil.which("cloudflared") is not None


def co_token():
    return os.path.exists(TOKEN_FILE) and os.path.getsize(TOKEN_FILE) > 40


def dang_chay():
    r = subprocess.run(["systemctl", "is-active", SERVICE],
                       capture_output=True, text=True, timeout=8)
    return r.stdout.strip() == "active"
