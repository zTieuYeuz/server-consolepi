#!/usr/bin/env python3
"""Nhung KHOA CONG KHAI goc vao ma (src/consolesystem/core/capnhat/khoa_goc.json) - lam 1 lan, TRUOC khi dung ban phat hanh dau tien (ISO 2.0).
    gan-khoa-goc.py THU_MUC_KHOA/goc.khoa-cong-khai.json
Chi doc file khoa CONG KHAI; khong dung toi khoa rieng. Ghi dau van tay ra man hinh de doi chieu voi ban ghi ngoai tuyen."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from consolesystem.core.capnhat import khoa as K  # noqa: E402

DICH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "consolesystem", "core", "capnhat", "khoa_goc.json")


def main(a):
    if len(a) != 1:
        print(__doc__)
        return 1
    pub, vai_tro = K.doc_khoa_cong_khai(a[0])
    if vai_tro != "goc" or len(pub) != 32:
        print("LOI: day khong phai khoa cong khai vai tro 'goc'", file=sys.stderr)
        return 1
    json.dump({"ghi_chu": "Khoa CONG KHAI goc cua nha phat hanh (Ed25519). Doi khoa nay = phai phat hanh lai ma nguon/ISO.", "khoa_cong_khai": K.b64(pub),
               "id": K.dau_van_tay(pub)}, open(DICH, "w", encoding="utf-8"), indent=1)
    print("da nhung khoa goc, dau van tay %s -> %s" % (K.dau_van_tay(pub), os.path.normpath(DICH)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
