#!/bin/bash
# Cai thu vien WinRM (pypsrp) cho tinh nang "Trien khai phan mem" vao venv rieng, khong dong vao Python he thong.
set -e
[ "$(id -u)" = 0 ] || { echo "Chay bang sudo."; exit 1; }
python3 -m venv /opt/console-pi-venv/winrm --system-site-packages
/opt/console-pi-venv/winrm/bin/pip install --quiet pypsrp requests-ntlm
/opt/console-pi-venv/winrm/bin/python3 -c "from pypsrp.client import Client; print('pypsrp OK')"
