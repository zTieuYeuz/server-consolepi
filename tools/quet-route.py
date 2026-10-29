#!/usr/bin/env python3
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Quet MOI route GET tren may that (chay ngay tren Console, goi 127.0.0.1:5000 kem dau man hinh tai cho).
Route co tham so duoc dien gia tri mau (id may/kich ban that neu co). Bao: route nao tra 5xx hoac treo.
Dung: sudo python3 tools/quet-route.py [--goc http://127.0.0.1:5000]"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, "/opt/console-system/current")


def mau():
    """Gia tri that cho tham so (lay tu du lieu dang co) de trang chi tiet duoc ve day du."""
    m = {}
    try:
        from ui import tk_dulieu as DL
        may = DL.MAY.doc()
        if may:
            m["mid"] = may[-1]["id"]
        kb = DL.KICH_BAN.doc()
        if kb:
            m["kb_id"] = kb[0]["id"]
    except Exception as e:                      # noqa: BLE001 - cong cu chan doan, khong duoc chet
        print("canh bao: khong doc duoc du lieu mau:", e)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--goc", default="http://127.0.0.1:5000")
    a = ap.parse_args()
    tt = mau()
    routes = []
    for dong in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "hop-dong", "routes.txt")):
        p, ms = dong.split("\t")[:2]
        if "GET" in ms:
            routes.append(p)
    loi, dem = [], 0
    for p in routes:
        if p.startswith(("/uem/agent/", "/deployos/pxeboot", "/tk/tai", "/static/", "/thuong-hieu/", "/uem/novnc/", "/logout")):
            continue                            # route cong khai/agent/tep tinh: test rieng
        u = p
        for k, v in (("<mid>", tt.get("mid", "khong-co")), ("<kb_id>", tt.get("kb_id", "khong-co")), ("<tab>", "phan-cung")):
            u = u.replace(k, v)
        u = re.sub(r"<[^>]+>", "khong-co", u)
        req = urllib.request.Request(a.goc + u, headers={"X-ConsolePi-Local": "1"})
        t0 = time.time()
        try:
            ma = urllib.request.urlopen(req, timeout=60).status
        except urllib.error.HTTPError as e:
            ma = e.code
        except Exception as e:                  # noqa: BLE001
            ma = "LOI " + type(e).__name__
        dem += 1
        if not isinstance(ma, int) or ma >= 500 or time.time() - t0 > 20:
            loi.append((u, ma, round(time.time() - t0, 1)))
    print(json.dumps({"da_quet": dem, "loi": loi}, ensure_ascii=False, indent=1))
    return 1 if loi else 0


if __name__ == "__main__":
    sys.exit(main())
