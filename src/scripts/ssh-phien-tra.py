#!/usr/bin/env python3
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Cho scripts/phien-mo.sh: ssh-phien-tra.py <ma> -> in "<rw|ro> <ten_tmux>" (exit 1 neu ma khong co). Ma la chuoi ngau nhien chi chu phien biet."""
import json
import os
import re
import sys

ma = sys.argv[1] if len(sys.argv) > 1 else ""
if not re.fullmatch(r"(ssh|xem)-[0-9a-f]{16}", ma):
    sys.exit(1)
def _du_lieu():
    """Cung quy tac voi ui/duongdan.py va phien-chay.py (tien trinh doc lap)."""
    goc = os.environ.get("CONSOLE_PI_DATA")
    if not goc:
        moi = "/var/lib/console-system"
        goc = moi if os.path.exists(os.path.join(moi, ".bo-cuc-moi")) else "/var/lib/console-pi"
    return os.path.join(goc, "data") if os.path.exists(os.path.join(goc, ".bo-cuc-moi")) else goc


f = os.environ.get("CS_SSH_PHIEN") or os.path.join(_du_lieu(), "ssh-phien.json")
try:
    p = json.load(open(f, encoding="utf-8"))["phien"][ma]
except (OSError, ValueError, KeyError):
    sys.exit(1)
if not re.fullmatch(r"ssh-[a-z0-9]{1,24}", p["tmux"]):
    sys.exit(1)
print(("ro" if p.get("chi_xem") else "rw"), p["tmux"])
