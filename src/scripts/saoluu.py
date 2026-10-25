#!/usr/bin/env python3
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Sao luu / khoi phuc tu dong lenh (A5). Chay bang root.
    saoluu.py tao [--toan-bo] [--ra FILE_HOAC_THU_MUC]
    saoluu.py kiem FILE
    saoluu.py khoi-phuc FILE [--yes] [--khong-dich-vu]
Khoi phuc: dung dich vu ghi du lieu -> kiem goi -> tu sao luu trang thai hien tai -> thay -> dong bo Samba/nginx -> bat lai dich vu."""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from ui import duongdan as DD  # noqa: E402
from ui import saoluu as S  # noqa: E402

DICH_VU = ("console-pi-dashboard", "console-pi-tftp")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lenh", choices=("tao", "kiem", "khoi-phuc"))
    ap.add_argument("tep", nargs="?")
    ap.add_argument("--toan-bo", action="store_true")
    ap.add_argument("--ra")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--khong-dich-vu", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.lenh == "tao":
            che_do = "toanbo" if a.toan_bo else "cauhinh"
            ra = a.ra or os.path.join(DD.GOC, "backups")
            if os.path.isdir(ra) or ra.endswith("/"):
                ra = os.path.join(ra, S.ten_goi(che_do))
            mf = S.tao_goi(DD.GOC, che_do, ra)
            print("da tao %s (%d file, che do %s)" % (ra, len(mf["tep"]), che_do))
        elif a.lenh == "kiem":
            mf = S.kiem_goi(a.tep)
            print("goi HOP LE: che do %s, %d file, tao luc %s tren %s, ma %s, schema %s" % (
                mf["che_do"], len(mf["tep"]), mf["tao_luc"], mf["may"], mf["phien_ban_ma"], mf["schema"]))
        else:
            mf = S.kiem_goi(a.tep)
            print("goi HOP LE: %s, %d file, tao luc %s" % (mf["che_do"], len(mf["tep"]), mf["tao_luc"]))
            if not a.yes and input("Khoi phuc se THAY cau hinh hien tai. Go 'dong y' de tiep tuc: ").strip() != "dong y":
                print("huy")
                return 1
            if not a.khong_dich_vu:
                for s in DICH_VU:
                    subprocess.run(["systemctl", "stop", s], capture_output=True, timeout=120)
            try:
                kq = S.khoi_phuc(a.tep)
                print("da khoi phuc %d file. Ban sao luu trang thai truoc do: %s" % (kq["so_tep"], kq["goi_truoc"]))
                for tb in S.hau_khoi_phuc():
                    print(" -", tb)
            finally:
                if not a.khong_dich_vu:
                    for s in DICH_VU:
                        subprocess.run(["systemctl", "start", s], capture_output=True, timeout=120)
    except S.LoiSaoLuu as e:
        print("LOI:", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
