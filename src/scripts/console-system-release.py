#!/usr/bin/env python3
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Quan ly ban phat hanh (A6). Chay bang root.
    console-system-release.py cai --nguon CAY_NGUON [--khong-khoi-dong-lai]   dung ban moi, chuyen current, ap dung he thong, khoi dong lai
    console-system-release.py ds | kiem [TEN] | lui | don
Lan DAU tren may con /opt/console-pi la thu muc that: tu dung dich vu, chep trang thai sang du lieu, doi thanh lien ket (thu muc cu giu lai .cu-*)."""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from ui import duongdan as DD  # noqa: E402
from ui import phathanh as P  # noqa: E402

DICH_VU = ("console-pi-dashboard", "console-pi-tftp")


def _sc(*a):
    return subprocess.run(["systemctl", *a], capture_output=True, text=True)


def khoi_dong_lai(dv_them=()):
    for s in dv_them:
        _sc("try-restart", s)
    _sc("restart", "console-pi-dashboard")
    _sc("try-restart", "console-pi-tftp")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lenh", choices=("cai", "ds", "kiem", "lui", "don"))
    ap.add_argument("ten", nargs="?")
    ap.add_argument("--nguon")
    ap.add_argument("--opt", default=P.GOC_OPT)
    ap.add_argument("--khong-khoi-dong-lai", action="store_true")
    a = ap.parse_args(argv)
    sao_luu = os.path.join(DD.GOC, "backups")
    try:
        if a.lenh == "ds":
            hien = P.hien_tai(a.opt)
            for t in P.danh_sach(a.opt):
                print(("* " if t == hien else "  ") + t)
        elif a.lenh == "kiem":
            ten = a.ten or P.hien_tai(a.opt)
            sai = P.kiem_ban(a.opt, ten)
            print("ban %s: %s" % (ten, "NGUYEN VEN" if not sai else "SAI %d file: %s" % (len(sai), ", ".join(sai[:8]))))
            return 1 if sai else 0
        elif a.lenh == "don":
            print("da xoa:", P.don_ban_cu(a.opt) or "khong co")
        elif a.lenh == "lui":
            truoc = P.ban_truoc(a.opt)
            if not truoc:
                print("LOI: khong co ban de lui", file=sys.stderr)
                return 1
            P.chuyen_ban(a.opt, truoc)
            bc = P.ap_dung(os.path.join(a.opt, "releases", truoc), sao_luu)
            print("da lui ve %s; he thong doi: %s; loi: %s" % (truoc, bc["doi"] or "khong", bc["loi"] or "khong"))
            if not a.khong_khoi_dong_lai:
                khoi_dong_lai(bc["unit_doi"])
        else:
            if not a.nguon:
                print("LOI: can --nguon", file=sys.stderr)
                return 1
            if not DD.BO_CUC_MOI:
                print("LOI: may chua o bo cuc du lieu moi (chay dichuyen.py bo-cuc-moi truoc)", file=sys.stderr)
                return 1
            la_thu_muc_that = os.path.isdir(P.TEN_CU) and not os.path.islink(P.TEN_CU)
            if la_thu_muc_that:
                for s in DICH_VU:
                    _sc("stop", s)
                ten, cu = P.nhap_khau_cu(a.opt, P.TEN_CU, DD.GOC, a.nguon)
                print("da chuyen %s thanh lien ket; thu muc cu giu o %s" % (P.TEN_CU, cu))
            else:
                ten = P.tao_ban(a.nguon, a.opt, mang_theo=os.path.realpath(P.TEN_CU) if os.path.exists(P.TEN_CU) else None)
                P.chuyen_ban(a.opt, ten)
                if not os.path.islink(P.TEN_CU):
                    os.symlink(os.path.join(a.opt, "current"), P.TEN_CU)
            bc = P.ap_dung(os.path.join(a.opt, "releases", ten), sao_luu)
            print("ban %s dang dung. he thong doi: %s; loi: %s" % (ten, bc["doi"] or "khong", bc["loi"] or "khong"))
            print("da xoa ban cu:", P.don_ban_cu(a.opt) or "khong")
            if not a.khong_khoi_dong_lai:
                khoi_dong_lai(bc["unit_doi"])
    except P.LoiPhatHanh as e:
        print("LOI:", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
