#!/usr/bin/env python3
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Lenh migration du lieu (A2). Khong can dich vu web.
    dichuyen.py trangthai | chay [--den N] | hoantac [--ve N]     [--thu-muc DUONG]
    dichuyen.py bo-cuc-moi [--tu /var/lib/console-pi] [--opt /opt/console-pi] [--moi /var/lib/console-system]
    dichuyen.py khoi-tao-moi [--moi ...]     (may cai moi, chua co du lieu cu)
    dichuyen.py kiem-bo-cuc [--moi ...] | hoantac-bo-cuc [--moi ...]       (DUNG dich vu truoc khi chuyen)
Mac dinh thu muc du lieu = $CONSOLE_PI_DATA hoac /var/lib/console-pi."""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from consolesystem.core import dichuyen as M  # noqa: E402     (chi dung thu vien chuan, khong keo flask)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lenh", choices=("trangthai", "chay", "hoantac", "bo-cuc-moi", "kiem-bo-cuc", "hoantac-bo-cuc", "khoi-tao-moi"))
    ap.add_argument("--thu-muc", default=os.environ.get("CONSOLE_PI_DATA") or (
        "/var/lib/console-system" if os.path.exists("/var/lib/console-system/.bo-cuc-moi") else "/var/lib/console-pi"))
    ap.add_argument("--tu", default="/var/lib/console-pi")
    ap.add_argument("--opt", default="/opt/console-pi")
    ap.add_argument("--moi", default="/var/lib/console-system")
    ap.add_argument("--den", type=int)
    ap.add_argument("--ve", type=int)
    a = ap.parse_args(argv)
    try:
        if a.lenh == "trangthai":
            print("phien ban du lieu: %d / ma biet toi: %d" % (M.doc_phien_ban(a.thu_muc), len(M.MIGRATIONS)))
        elif a.lenh == "chay":
            print("xong, phien ban du lieu:", M.chay(a.thu_muc, M.MIGRATIONS, den=a.den))
        elif a.lenh == "bo-cuc-moi":
            print("da chep %d file sang %s; ban cu giu nguyen o %s" % (M.dua_ve_bo_cuc_moi(a.tu, a.opt, a.moi), a.moi, a.tu))
        elif a.lenh == "khoi-tao-moi":
            print("da tao bo cuc moi o %s" % a.moi if M.tao_bo_cuc_moi(a.moi) else "%s da la bo cuc moi" % a.moi)
        elif a.lenh == "kiem-bo-cuc":
            sai = M.kiem_bo_cuc_moi(a.moi)
            print("file sai: %s" % (sai or "khong"))
            return 1 if sai else 0
        elif a.lenh == "hoantac-bo-cuc":
            print("da chuyen di cho khac:", M.hoan_tac_bo_cuc(a.moi))
        else:
            print("xong, phien ban du lieu:", M.hoan_tac(a.thu_muc, M.MIGRATIONS, ve=a.ve))
    except M.LoiDichuyen as e:
        print("LOI:", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
