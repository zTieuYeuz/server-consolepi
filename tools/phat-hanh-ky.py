#!/usr/bin/env python3
"""C1: dong goi + ky ban phat hanh va danh muc. Mat khau khoa phat-hanh: CS_KHOA_MAT_KHAU_PHAT_HANH hoac CS_KHOA_MAT_KHAU hoac o nhap an.
    phat-hanh-ky.py goi --khoa THU_MUC_KHOA --ban CAY_RELEASE --phien-ban 2.0.1 --so-phat-hanh 2 --kien-truc amd64 --kenh on-dinh
                         [--ban-truoc 2.0.0] [--ghi-chu "..."] [--ha-cap-toi-thieu 2.0.0] [--khong-khoi-dong-lai] --ra FILE.cspkg
        -> FILE.cspkg + FILE.cspkg.khoa-goi.json (khoa giai ma goi, 0600 - giao cho KHO, KHONG dua vao goi)
    phat-hanh-ky.py danh-muc --khoa THU_MUC_KHOA --kenh on-dinh --so-hieu N [--han-ngay 7] --ra FILE.json GOI.cspkg [GOI.cspkg ...]"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from consolesystem.core.capnhat import danhmuc as DM  # noqa: E402
from consolesystem.core.capnhat import goi as G  # noqa: E402
from consolesystem.core.capnhat import khoa as K  # noqa: E402


def _khoa_phat_hanh(thu_muc):
    pub, _ = K.doc_khoa_cong_khai(os.path.join(thu_muc, "phat-hanh.khoa-cong-khai.json"))
    priv = K.doc_khoa_rieng(os.path.join(thu_muc, "phat-hanh.khoa-rieng.json"), K.lay_mat_khau(vai_tro="phat-hanh"))
    return priv, K.dau_van_tay(pub)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sp = ap.add_subparsers(dest="lenh", required=True)
    g = sp.add_parser("goi")
    g.add_argument("--khoa", required=True)
    g.add_argument("--ban", required=True)
    g.add_argument("--phien-ban", required=True)
    g.add_argument("--so-phat-hanh", type=int, required=True)
    g.add_argument("--kien-truc", required=True)
    g.add_argument("--kenh", required=True)
    g.add_argument("--ban-truoc")
    g.add_argument("--ghi-chu", default="")
    g.add_argument("--ha-cap-toi-thieu")
    g.add_argument("--khong-khoi-dong-lai", action="store_true")
    g.add_argument("--ra", required=True)
    d = sp.add_parser("danh-muc")
    d.add_argument("--khoa", required=True)
    d.add_argument("--kenh", required=True)
    d.add_argument("--so-hieu", type=int, required=True)
    d.add_argument("--han-ngay", type=float, default=7)
    d.add_argument("--ra", required=True)
    d.add_argument("goi", nargs="+")
    a = ap.parse_args(argv)
    try:
        priv, id_khoa = _khoa_phat_hanh(a.khoa)
        if a.lenh == "goi":
            tt = {"phien_ban": a.phien_ban, "so_phat_hanh": a.so_phat_hanh, "kien_truc": a.kien_truc, "kenh": a.kenh,
                  "ban_truoc_bat_buoc": a.ban_truoc, "ghi_chu": a.ghi_chu, "can_khoi_dong_lai": not a.khong_khoi_dong_lai,
                  "ban_toi_thieu_ha_cap": a.ha_cap_toi_thieu}
            manifest, dek = G.dong_goi(a.ban, tt, priv, id_khoa, a.ra)
            sha = hashlib.sha256(open(a.ra, "rb").read()).hexdigest()
            fd = os.open(a.ra + ".khoa-goi.json", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump({"ten": manifest["ten"], "phien_ban": a.phien_ban, "khoa_goi": K.b64(dek), "sha256_goi": sha}, f, indent=1)
            print("da tao %s (%d file, %d byte, sha256 %s...)" % (a.ra, len(manifest["tep"]), os.path.getsize(a.ra), sha[:12]))
        else:
            cac = []
            for p in a.goi:
                with open(p, "rb") as f:
                    dau, _b, _c = G.doc_dau(f)
                m = dau["manifest"]
                cac.append({"phien_ban": m["phien_ban"], "so_phat_hanh": m["so_phat_hanh"], "kien_truc": m["kien_truc"], "ban_truoc_bat_buoc": m.get("ban_truoc_bat_buoc"),
                            "kich_thuoc": os.path.getsize(p), "sha256_goi": hashlib.sha256(open(p, "rb").read()).hexdigest(), "ghi_chu": m.get("ghi_chu", ""),
                            "ten_goi": os.path.basename(p)})
            doc = DM.tao_danh_muc(a.kenh, a.so_hieu, cac, priv, id_khoa, han=int(a.han_ngay * 86400))
            json.dump(doc, open(a.ra, "w", encoding="utf-8"), indent=1)
            print("da ky danh muc kenh %s so_hieu=%d (%d ban), het han sau %.1f ngay -> %s" % (a.kenh, a.so_hieu, len(cac), a.han_ngay, a.ra))
    except (K.LoiKhoa, G.LoiGoi) as e:
        print("LOI:", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
