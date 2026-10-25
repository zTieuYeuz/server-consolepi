"""Tien trinh rieng: moi route /cap-nhat* va /khoa-may phai bat dang nhap khi truy cap tu mang (khong co dau man hinh cam ung)."""
import json
import os
import runpy
import sys
import threading

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC)
os.chdir(SRC)
_goc = threading.Thread.start
threading.Thread.start = lambda self: None if getattr(getattr(self, "_target", None), "__name__", "") in ("tu_dang_ky_nen", "_driver_nen", "vong", "vong_kiem_tra_nen") else _goc(self)
app = runpy.run_path(os.path.join(SRC, "app.py"), run_name="dev")["app"]
c = app.test_client()
kq = {}
for rule in app.url_map.iter_rules():
    p = str(rule)
    if not (p.startswith("/cap-nhat") or p == "/khoa-may"):
        continue
    for m in sorted(rule.methods - {"HEAD", "OPTIONS"}):
        r = c.open(p, method=m, environ_overrides={"REMOTE_ADDR": "192.168.1.50"})
        kq["%s %s" % (m, p)] = r.status_code in (302, 401, 403) and (r.status_code != 302 or "/login" in r.headers.get("Location", ""))
print("KETQUA " + json.dumps(kq))
