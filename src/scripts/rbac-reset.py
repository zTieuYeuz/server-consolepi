#!/usr/bin/env python3
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""rbac-reset: xoa rbac.json ve mac dinh (root/sudo = Quan tri, nguoi khac chua co vai tro). Chay tren Pi bang quyen root:
    sudo python3 /opt/console-pi/scripts/rbac-reset.py
Dung khi lo gan sai vai tro. Khong can dang nhap web. Khong dung toi du lieu khac."""
import os
import sys

goc = os.environ.get("CONSOLE_PI_DATA")
if not goc:
    moi = "/var/lib/console-system"
    goc = moi if os.path.exists(os.path.join(moi, ".bo-cuc-moi")) else "/var/lib/console-pi"
du_lieu = os.path.join(goc, "data") if os.path.exists(os.path.join(goc, ".bo-cuc-moi")) else goc
f = os.path.join(du_lieu, "rbac.json")
try:
    os.remove(f)
    print("Da xoa %s: moi nguoi ve mac dinh (root/sudo = Quan tri)." % f)
except FileNotFoundError:
    print("Chua co %s (dang la mac dinh)." % f)
except OSError as e:
    print("Khong xoa duoc %s: %s" % (f, e))
    sys.exit(1)
