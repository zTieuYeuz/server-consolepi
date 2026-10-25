#!/usr/bin/env python3
"""C0: tao khoa ky cho he thong cap nhat. Mat khau khoa: bien moi truong CS_KHOA_MAT_KHAU_<VAI_TRO> (goc/phat-hanh/lenh-khoa) hoac CS_KHOA_MAT_KHAU,
hoac o nhap an - KHONG BAO GIO qua tham so dong lenh.
    tao-khoa-ky.py THU_MUC --vai-tro goc [--vai-tro phat-hanh] [--vai-tro lenh-khoa]     tao cap khoa (khong ghi de khoa rieng da co)
    tao-khoa-ky.py THU_MUC --tin-cay --so-hieu N [--han-ngay 365] [--ra FILE]            khoa GOC ky tai lieu tin cay liet ke khoa phat-hanh + lenh-khoa
    tao-khoa-ky.py THU_MUC --xem                                                         in dau van tay cac khoa cong khai"""
import argparse
import glob
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from consolesystem.core.capnhat import khoa as K  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("thu_muc")
    ap.add_argument("--vai-tro", action="append", choices=K.VAI_TRO)
    ap.add_argument("--tin-cay", action="store_true")
    ap.add_argument("--so-hieu", type=int, default=1)
    ap.add_argument("--han-ngay", type=int, default=365)
    ap.add_argument("--ra")
    ap.add_argument("--xem", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.xem:
            for f in sorted(glob.glob(os.path.join(a.thu_muc, "*.khoa-cong-khai.json"))):
                pub, vt = K.doc_khoa_cong_khai(f)
                print("%-10s %s" % (vt, K.dau_van_tay(pub)))
        elif a.tin_cay:
            mk = K.lay_mat_khau(vai_tro="goc")
            goc = K.doc_khoa_rieng(os.path.join(a.thu_muc, "goc.khoa-rieng.json"), mk)
            pub_goc, _ = K.doc_khoa_cong_khai(os.path.join(a.thu_muc, "goc.khoa-cong-khai.json"))
            het = int(time.time()) + a.han_ngay * 86400
            ds = []
            for vt in ("phat-hanh", "lenh-khoa"):
                p = os.path.join(a.thu_muc, vt + ".khoa-cong-khai.json")
                if os.path.exists(p):
                    pub, _ = K.doc_khoa_cong_khai(p)
                    ds.append({"vai_tro": vt, "khoa_cong_khai": K.b64(pub), "den": het})
            doc = K.tao_tai_lieu_tin_cay(ds, a.so_hieu, int(time.time()) + 30 * 86400, goc, K.dau_van_tay(pub_goc))
            ra = a.ra or os.path.join(a.thu_muc, "tin-cay.json")
            json.dump(doc, open(ra, "w", encoding="utf-8"), indent=1)
            print("da ky tai lieu tin cay so_hieu=%d (%d khoa) -> %s" % (a.so_hieu, len(ds), ra))
        else:
            if not a.vai_tro:
                ap.error("can --vai-tro, --tin-cay hoac --xem")
            for vt in a.vai_tro:
                mk = K.lay_mat_khau(xac_nhan=not os.environ.get(K.BIEN_MAT_KHAU) and not os.environ.get("%s_%s" % (K.BIEN_MAT_KHAU, vt.upper().replace("-", "_"))), vai_tro=vt)
                print("%-10s dau van tay %s" % (vt, K.luu_cap_khoa(a.thu_muc, vt, mk)))
    except K.LoiKhoa as e:
        print("LOI:", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
