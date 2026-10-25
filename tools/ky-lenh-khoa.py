#!/usr/bin/env python3
"""C6: ky LENH KHOA may va tinh MA MO KHOA (OFFLINE). Mat khau khoa lenh-khoa: CS_KHOA_MAT_KHAU_LENH_KHOA / CS_KHOA_MAT_KHAU / o nhap an.
    ky-lenh-khoa.py khoa --khoa THU_MUC_KHOA --token TOKEN_MAY   [--token-bam HEX16] --so-thu-tu N [--han-ngay 7] --ra lenh.json
        -> lenh.json (nap len kho: nap-ban.py lenh lenh.json) va IN ma mo khoa MOT LAN. Ghi ma ra giay/noi an toan.
    ky-lenh-khoa.py tinh-ma --khoa THU_MUC_KHOA --id-lenh ID     (tinh lai ma mo khoa tu id lenh, khong can ma da in)
--token-bam la 16 ky tu dau cua sha256(token) (kho hien trang 'May nghi ngo'), dung khi khong co token day du."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from consolesystem.core.capnhat import khoa as K  # noqa: E402
from consolesystem.core.capnhat import khoa_lenh as KL  # noqa: E402


def _khoa(thu_muc):
    pub, _ = K.doc_khoa_cong_khai(os.path.join(thu_muc, "lenh-khoa.khoa-cong-khai.json"))
    priv = K.doc_khoa_rieng(os.path.join(thu_muc, "lenh-khoa.khoa-rieng.json"), K.lay_mat_khau(vai_tro="lenh-khoa"))
    return priv, K.dau_van_tay(pub)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sp = ap.add_subparsers(dest="lenh", required=True)
    k = sp.add_parser("khoa")
    k.add_argument("--khoa", required=True)
    k.add_argument("--token")
    k.add_argument("--token-bam")
    k.add_argument("--so-thu-tu", type=int, required=True)
    k.add_argument("--han-ngay", type=int, default=7)
    k.add_argument("--ra", required=True)
    t = sp.add_parser("tinh-ma")
    t.add_argument("--khoa", required=True)
    t.add_argument("--id-lenh", required=True)
    a = ap.parse_args(argv)
    priv, idk = _khoa(a.khoa)
    if a.lenh == "khoa":
        tb = a.token_bam or (KL.token_bam(a.token) if a.token else None)
        if not tb:
            ap.error("can --token hoac --token-bam")
        pb, ma = KL.tao_lenh_khoa(priv, idk, tb, a.so_thu_tu, a.han_ngay * 86400)
        json.dump(pb, open(a.ra, "w"))
        print("Da ky lenh khoa cho may %s -> %s" % (tb, a.ra))
        print("MA MO KHOA (ghi lai, chi hien lan nay; tinh lai duoc bang `tinh-ma`):", ma)
    else:
        print(KL.hien_thi_ma(KL.ma_mo_khoa(K._raw_priv(priv), a.id_lenh)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
