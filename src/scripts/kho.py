#!/usr/bin/env python3
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Xem / xuat cac kho du lieu LON (SQLite, console.db) - de chan doan hoac HOAN TAC ve JSON (B1b). Chay bang root.
    kho.py ds                          liet ke kho + so muc
    kho.py xuat TEN [--ra FILE]        ghi mot kho ra JSON (mac dinh in ra man hinh)
    kho.py xuat-het THU_MUC            ghi moi kho ra THU_MUC/<TEN>.json (dat vao <du lieu>/trienkhai/ roi CS_KHO_JSON=1 de quay ve JSON)"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from ui import tk_dulieu as DL  # noqa: E402
from ui import uem_dulieu as UD  # noqa: E402

KHO = {"may": DL.MAY, "chay": DL.TRANG_THAI, "uem_tac_vu": UD.BAO_CAO_TAC_VU, "uem_trien_khai": UD.TRIEN_KHAI,
       "uem_profile_tt": UD.TRANG_THAI_PROFILE}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lenh", choices=("ds", "xuat", "xuat-het"))
    ap.add_argument("ten", nargs="?")
    ap.add_argument("--ra")
    a = ap.parse_args(argv)
    if a.lenh == "ds":
        for t, k in KHO.items():
            print("%-16s %6d muc  (%s)" % (t, len(k.doc()), type(k).__name__))
    elif a.lenh == "xuat":
        if a.ten not in KHO:
            print("LOI: kho khong co: %s (co: %s)" % (a.ten, ", ".join(KHO)), file=sys.stderr)
            return 1
        d = KHO[a.ten].doc()
        if a.ra:
            from consolesystem.core.store import ghi_nguyen_tu
            ghi_nguyen_tu(a.ra, json.dumps(d, ensure_ascii=False, indent=1).encode("utf-8"))
            print("da ghi %s" % a.ra)
        else:
            print(json.dumps(d, ensure_ascii=False, indent=1))
    else:
        from consolesystem.core.store import ghi_nguyen_tu
        for t, k in KHO.items():
            ghi_nguyen_tu(os.path.join(a.ten, t + ".json"), json.dumps(k.doc(), ensure_ascii=False, indent=1).encode("utf-8"))
            print("da ghi %s.json" % t)
    return 0


if __name__ == "__main__":
    sys.exit(main())
