#!/usr/bin/env python3
"""Xuat hop dong route: moi dong = duong dan <tab> phuong thuc <tab> ham xu ly.
Dung: xuat-route.py [file-dau-ra]. So sanh voi tests/hop-dong/routes.txt."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import app  # noqa: E402

dong = sorted(
    "%s\t%s\t%s" % (r.rule, ",".join(sorted(m for m in r.methods if m not in ("HEAD", "OPTIONS"))), r.endpoint)
    for r in app.app.url_map.iter_rules()
)
out = "\n".join(dong) + "\n"
if len(sys.argv) > 1:
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        f.write(out)
else:
    sys.stdout.write(out)
