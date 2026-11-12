#!/usr/bin/env python3
"""Liet ke moi route POST/PUT/PATCH/DELETE o muc "ghi" (Van hanh dung duoc, Chi xem khong): TAT CA route khong-GET tru danh sach huy diet
(core.rbac.PHA_HUY va dich vu chi-quan-tri). Moi dong = dich vu <tab> phuong thuc <tab> duong dan. NV4/CEO duyet file tests/hop-dong/route-ghi.txt;
them route POST moi thi file doi -> test do -> phai co nguoi doc va duyet muc quyen. Dung: xuat-route-ghi.py [file-dau-ra]."""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import app  # noqa: E402
from consolesystem.core import rbac as RB  # noqa: E402

dong = []
for r in app.app.url_map.iter_rules():
    pt = sorted(m for m in r.methods if m in ("POST", "PUT", "PATCH", "DELETE"))
    if not pt:
        continue
    p = re.sub(r"<[^>]+>", "x", r.rule)
    if RB.la_cong_khai(p):
        continue
    dv = RB.dich_vu_cua(p) or "(CHUA KHAI)"
    if RB.muc_can("POST", p) == "quan_tri":
        continue
    dong.append("%s\t%s\t%s" % (dv, ",".join(pt), r.rule))
out = "\n".join(sorted(dong)) + "\n"
if len(sys.argv) > 1:
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        f.write(out)
else:
    sys.stdout.write(out)
