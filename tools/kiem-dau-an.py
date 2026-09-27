#!/usr/bin/env python3
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Kiem tra DAU AN ban quyen zTieuYeuz trong 1 ban sao nghi ngo.

  python3 tools/kiem-dau-an.py trang.html          # tim dau an khong rong + ma nhan dien
  python3 tools/kiem-dau-an.py --iso <duong/dan/.dau-an> --khoa <file-khoa>
                                                    # xac minh chu ky ban build (HMAC)

Dau an gom 3 lop (xem ui/gioithieu.py va iso/dung-cay-build.sh):
  1. Chuoi ky tu khong rong (U+200B/U+200C giua 2 U+2060) = bit cua "zTieuYeuz"
     nam trong chan trang / trang dang nhap - dan giao dien sang dau cung theo.
  2. MA_NHAN_DIEN (hex "zTieuYeuz|ConsoleSystem") trong CSS (--zt) va header X-CS-ID.
  3. File .dau-an trong moi ban build: HMAC-SHA256 bang KHOA RIENG chi tac gia
     giu (KHONG nam trong repo/ISO) - chi nguoi co khoa moi tao/xac minh duoc,
     nen day la bang chung manh nhat ban ISO do chinh tac gia build.
"""
import hashlib
import hmac
import json
import re
import sys

MA = "7a546965755965757a7c436f6e736f6c6553797374656d"


def doc_khong_rong(s):
    ra = []
    for m in re.finditer("⁠([​‌]+)⁠", s):
        bit = "".join("1" if c == "‌" else "0" for c in m.group(1))
        try:
            ra.append(bytes(int(bit[i:i + 8], 2) for i in range(0, len(bit) - 7, 8)).decode())
        except ValueError:
            pass
    return ra


def main():
    if "--iso" in sys.argv:
        d = json.load(open(sys.argv[sys.argv.index("--iso") + 1]))
        khoa = open(sys.argv[sys.argv.index("--khoa") + 1], "rb").read().strip()
        dung = hmac.new(khoa, d["noi_dung"].encode(), hashlib.sha256).hexdigest()
        print("Noi dung :", d["noi_dung"])
        print("CHU KY HOP LE - ban build cua zTieuYeuz" if hmac.compare_digest(dung, d["chu_ky"])
              else "CHU KY SAI - khong phai ban build goc (hoac da bi sua)")
        return
    s = open(sys.argv[1], encoding="utf-8", errors="replace").read()
    print("Dau an khong rong:", doc_khong_rong(s) or "khong thay")
    print("Ma nhan dien      :", "CO" if MA in s else "khong thay")


if __name__ == "__main__":
    main()
