#!/usr/bin/env python3
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Mo khoa may NGAY TREN CONSOLE (khi khong vao duoc web). Chay bang root.
    console-system-mo-khoa.py trang-thai
    console-system-mo-khoa.py mo            (hoi ma mo khoa bang o nhap an; hoac bien moi truong CS_MA_MO_KHOA)"""
import getpass
import json
import os
import sys

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
from consolesystem.core.capnhat import khoa_lenh as KL  # noqa: E402
from consolesystem.core.capnhat import may as M  # noqa: E402


def main(argv):
    moi = M.Moi()
    if argv[:1] == ["trang-thai"]:
        d = KL.trang_thai(moi)
        print(json.dumps({k: d.get(k) for k in ("trang_thai", "id_lenh", "luc", "khoa_luc", "mo_luc")}, ensure_ascii=False))
        return 0
    if argv[:1] == ["mo"]:
        ma = os.environ.get("CS_MA_MO_KHOA") or getpass.getpass("Ma mo khoa: ")
        try:
            print("Da mo khoa, khoi phuc %d file bi mat. Khoi dong lai dich vu de ap dung." % KL.mo_khoa(moi, ma))
            return 0
        except KL.LoiKhoaLenh as e:
            print("LOI:", e, file=sys.stderr)
            return 1
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
