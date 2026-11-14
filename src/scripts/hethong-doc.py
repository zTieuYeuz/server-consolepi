#!/usr/bin/env python3
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""hethong-doc: in danh sach tu manifest he thong (config/hethong.json) cho install.sh. Moi dong mot muc.
    hethong-doc.py <tep.json> bat | bat-man-hinh | go | apt-core | apt-man-hinh | apt-trien-khai
Loi (khong doc duoc / sai kieu) -> thoat 1, in gi len stderr; install.sh khi do dung danh sach du phong cua no."""
import json
import re
import sys

MAU_DON_VI = re.compile(r"^[A-Za-z0-9@][A-Za-z0-9@._-]*$")      # khop core/phathanh.MAU_TEN_DON_VI
MAU_GOI = re.compile(r"^[a-z0-9][a-z0-9+.-]*$")

KHOA = {"bat": ("don_vi", "bat"), "bat-man-hinh": ("don_vi", "bat_khi_co_man_hinh"), "go": ("don_vi", "go"),
        "apt-core": ("goi_apt", "core"), "apt-man-hinh": ("goi_apt", "man_hinh"), "apt-trien-khai": ("goi_apt", "trien_khai")}


def main(argv):
    if len(argv) != 3 or argv[2] not in KHOA:
        print("dung: hethong-doc.py <tep.json> %s" % " | ".join(KHOA), file=sys.stderr)
        return 2
    try:
        d = json.load(open(argv[1], encoding="utf-8"))
        a, b = KHOA[argv[2]]
        ds = d[a][b]
        mau = MAU_GOI if a == "goi_apt" else MAU_DON_VI
        if not isinstance(ds, list) or not all(isinstance(x, str) and mau.fullmatch(x) and ".." not in x for x in ds):
            raise ValueError("danh sach khong hop le")
    except (OSError, ValueError, KeyError, TypeError) as e:
        print("hethong-doc: %s" % type(e).__name__, file=sys.stderr)
        return 1
    print("\n".join(ds))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
