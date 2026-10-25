#!/usr/bin/env python3
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Bo nang cap/ha cap CHAY RIENG (don vi systemd), khong phu thuoc dashboard. Chay bang root.
    console-system-nang-cap.py chay         chay (hoac tiep tuc) cong viec dang cho trong updates/job.json
    console-system-nang-cap.py phuc-hoi     luc KHOI DONG MAY: cong viec do dang (mat dien) -> tiep tuc hoac hoan tac an toan
    console-system-nang-cap.py kiem-tra     hoi kho ngay va in trang thai
    console-system-nang-cap.py trang-thai   in cong viec hien tai (JSON)
QUAN TRONG: ma duoc GHIM vao ban dang chay LUC BAT DAU (realpath cua lien ket current) va nap san moi module can dung, de sau khi doi
`current` giua chung ban nang cap van chay bang ma CU (khong tron ma hai phien ban)."""
import json
import os
import sys

GOC_MA = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, GOC_MA)
from consolesystem.core.capnhat import may as M  # noqa: E402
from consolesystem.core.capnhat import nangcap as N  # noqa: E402
from consolesystem.features.backup import saoluu  # noqa: E402,F401  (nap san - dung khi hoan tac)
from consolesystem.features.deploy_os import khotrungtam  # noqa: E402,F401
from consolesystem.features.updates import thuc_te  # noqa: E402


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    moi = thuc_te.moi_thuc()
    lenh = argv[0]
    if lenh == "chay":
        j = N.chay_job(moi)
        print(json.dumps(thuc_te.mo_ta_job(j), ensure_ascii=False))
        return 0 if (j or {}).get("trang_thai") in ("xong", None) else 2
    if lenh == "phuc-hoi":
        hd, j = N.phuc_hoi(moi)
        print("phuc-hoi:", hd, (j or {}).get("trang_thai", ""))
        return 0
    if lenh == "kiem-tra":
        print(json.dumps(M.kiem_tra(moi, bat_buoc=True), ensure_ascii=False, indent=1))
        return 0
    if lenh == "trang-thai":
        print(json.dumps(thuc_te.mo_ta_job(N.doc_job(moi)), ensure_ascii=False, indent=1))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
