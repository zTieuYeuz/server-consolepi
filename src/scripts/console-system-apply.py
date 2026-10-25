#!/usr/bin/env python3
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""console-system-apply: dua file he thong (don vi systemd, nginx, smb.conf, logrotate, udev) cua ban dang dung ra /etc.
So ma bam, sao luu ban cu vao <du lieu>/backups/etc-*, kiem nginx -t / testparm truoc khi nap, loi thi tra ve.
    console-system-apply.py [--ban TEN] [--thu] [--khoi-dong-lai]"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from ui import duongdan as DD  # noqa: E402
from ui import phathanh as P  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ban")
    ap.add_argument("--opt", default=P.GOC_OPT)
    ap.add_argument("--thu", action="store_true", help="chi liet ke, khong ghi")
    ap.add_argument("--khoi-dong-lai", action="store_true")
    a = ap.parse_args(argv)
    ten = a.ban or P.hien_tai(a.opt)
    if not ten:
        print("LOI: chua co ban nao dang dung (current)", file=sys.stderr)
        return 1
    bc = P.ap_dung(os.path.join(a.opt, "releases", ten), os.path.join(DD.GOC, "backups"), thu=a.thu)
    print("ban %s: doi %d, khong doi %d, bo qua (may khong cai) %d%s" % (ten, len(bc["doi"]), bc["khong_doi"], len(bc["bo_qua"]), " [CHI THU]" if a.thu else ""))
    for x in bc["doi"]:
        print("  doi:", x)
    for x in bc["loi"]:
        print("  LOI:", x, file=sys.stderr)
    if a.khoi_dong_lai and bc["unit_doi"]:
        for u in bc["unit_doi"]:
            subprocess.run(["systemctl", "try-restart", u], capture_output=True)
    return 1 if bc["loi"] else 0


if __name__ == "__main__":
    sys.exit(main())
