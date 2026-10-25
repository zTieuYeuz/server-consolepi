#!/usr/bin/env python3
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Lenh migration du lieu (A2). Khong can dich vu web.
    dichuyen.py trangthai | chay [--den N] | hoantac [--ve N]     [--thu-muc DUONG]
Mac dinh thu muc du lieu = $CONSOLE_PI_DATA hoac /var/lib/console-pi."""
import argparse
import importlib.util
import os
import sys

_M = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ui", "dichuyen.py")
_spec = importlib.util.spec_from_file_location("dichuyen", _M)
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lenh", choices=("trangthai", "chay", "hoantac"))
    ap.add_argument("--thu-muc", default=os.environ.get("CONSOLE_PI_DATA", "/var/lib/console-pi"))
    ap.add_argument("--den", type=int)
    ap.add_argument("--ve", type=int)
    a = ap.parse_args(argv)
    try:
        if a.lenh == "trangthai":
            print("phien ban du lieu: %d / ma biet toi: %d" % (M.doc_phien_ban(a.thu_muc), len(M.MIGRATIONS)))
        elif a.lenh == "chay":
            print("xong, phien ban du lieu:", M.chay(a.thu_muc, M.MIGRATIONS, den=a.den))
        else:
            print("xong, phien ban du lieu:", M.hoan_tac(a.thu_muc, M.MIGRATIONS, ve=a.ve))
    except M.LoiDichuyen as e:
        print("LOI:", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
