#!/usr/bin/env python3
"""C1: kiem mot goi .cspkg nhu may khach se kiem (khong cai). Chi can KHOA CONG KHAI goc + tai lieu tin cay (+ khoa goi neu muon giai ma).
    kiem-goi.py GOI.cspkg --goc goc.khoa-cong-khai.json --tin-cay tin-cay.json [--khoa-goi GOI.cspkg.khoa-goi.json --thu-muc-cai DIR
                --hien-tai-phien-ban 2.0.0 --hien-tai-so-phat-hanh 1 --kien-truc amd64 --kenh on-dinh]"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from consolesystem.core.capnhat import goi as G  # noqa: E402
from consolesystem.core.capnhat import khoa as K  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("goi")
    ap.add_argument("--goc", required=True)
    ap.add_argument("--tin-cay", required=True)
    ap.add_argument("--khoa-goi")
    ap.add_argument("--thu-muc-cai")
    ap.add_argument("--hien-tai-phien-ban")
    ap.add_argument("--hien-tai-so-phat-hanh", type=int, default=0)
    ap.add_argument("--kien-truc", default="amd64")
    ap.add_argument("--kenh", default="on-dinh")
    a = ap.parse_args(argv)
    try:
        pub_goc, _ = K.doc_khoa_cong_khai(a.goc)
        khoa_hl, so_hieu = K.khoa_hop_le(json.load(open(a.tin_cay, encoding="utf-8")), pub_goc, "phat-hanh")
        with open(a.goi, "rb") as f:
            dau, dau_b, cs = G.doc_dau(f)
            id_ky = G.kiem_chu_ky(dau, dau_b, cs, khoa_hl)
        m = dau["manifest"]
        print("CHU KY HOP LE (khoa %s, tai lieu tin cay so_hieu %s): %s %s, so_phat_hanh %s, %s/%s, %d file" % (
            id_ky, so_hieu, m["ten"], m["phien_ban"], m["so_phat_hanh"], m["kien_truc"], m["kenh"], len(m["tep"])))
        if a.khoa_goi and a.thu_muc_cai:
            dek = K.unb64(json.load(open(a.khoa_goi, encoding="utf-8"))["khoa_goi"])
            ht = {"phien_ban": a.hien_tai_phien_ban, "so_phat_hanh": a.hien_tai_so_phat_hanh, "kien_truc": a.kien_truc, "kenh": a.kenh}
            ten, _m = G.cai_goi(a.goi, dek, khoa_hl, ht, a.thu_muc_cai)
            print("DA GIAI NEN + KIEM TUNG FILE vao %s/%s" % (a.thu_muc_cai, ten))
    except (K.LoiKhoa, G.LoiGoi) as e:
        print("LOI:", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
