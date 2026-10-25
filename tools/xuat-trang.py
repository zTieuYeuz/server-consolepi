#!/usr/bin/env python3
"""Hop dong dau ra trang: GET moi route khong tham so (du lieu gia, thu muc tam) -> ma tra ve, loai noi dung,
ma bam than trang da chuan hoa. Dung: xuat-trang.py [file-dau-ra]. So voi tests/hop-dong/trang.txt."""
import hashlib
import os
import re
import runpy
import signal
import sys
import tempfile
import threading

DAU_RA = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else None     # truoc khi chdir
TMP = os.environ.get("CS_XUAT_DATA") or tempfile.mkdtemp(prefix="trang-")   # CS_XUAT_DATA: thu muc du lieu mau (nen la BAN SAO)
os.environ["CONSOLE_PI_DATA"] = TMP
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC)
os.chdir(SRC)
_goc = threading.Thread.start
threading.Thread.start = lambda self: None if getattr(getattr(self, "_target", None), "__name__", "") in ("tu_dang_ky_nen", "_driver_nen", "vong") else _goc(self)
app = runpy.run_path(os.path.join(SRC, "app.py"), run_name="dev")["app"]
# GET co tac dung phu hoac chay mai khong dung -> khong goi
BO_QUA = re.compile(r"power|reboot|shutdown|restart|stream|/ws|events|download|tai-xuong|xoa|stop|dung|huy|capture|logs/live|vnc|terminal/|tail|poll")


def chuan(b):
    b = re.sub(rb"\d{1,2}:\d\d(:\d\d)?", b"<T>", b)
    b = re.sub(rb"\d{4}-\d\d-\d\d", b"<D>", b)
    b = re.sub(rb"[0-9a-f]{32,}", b"<H>", b)
    return b

# trang doc trang thai may that (dung luong o, suc khoe...) -> khac nhau giua cac lan chay, chi so ma tra ve
THEO_MAY = {"/", "/api/suckhoe", "/settings", "/storage", "/logs", "/deployos/caidat/hatang/chay"}


class QuaGio(Exception):
    pass


def main():
    c = app.test_client()
    H = {"X-ConsolePi-Local": "1"}
    signal.signal(signal.SIGALRM, lambda *a: (_ for _ in ()).throw(QuaGio()))
    dong = []
    for r in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        if "GET" not in r.methods or "<" in r.rule or BO_QUA.search(r.rule):
            continue
        signal.alarm(8)
        try:
            resp = c.get(r.rule, headers=H, follow_redirects=False)
            ct = (resp.content_type or "").split(";")[0]
            h = "-"
            if ct in ("text/html", "application/json"):
                h = hashlib.sha1(chuan(resp.get_data())).hexdigest()[:10]
                h2 = hashlib.sha1(chuan(c.get(r.rule, headers=H).get_data())).hexdigest()[:10]
                if h != h2 or r.rule in THEO_MAY:
                    h = "~"     # noi dung doi moi lan (gio, so ngau nhien...) -> chi so ma tra ve
            dong.append("%s\t%s\t%s\t%s" % (r.rule, resp.status_code, ct, h))
        except QuaGio:
            dong.append("%s\tQUA-GIO\t-\t-" % r.rule)
        except Exception as e:
            dong.append("%s\tLOI\t%s\t-" % (r.rule, type(e).__name__))
        finally:
            signal.alarm(0)
    out = "\n".join(dong) + "\n"
    if DAU_RA:
        open(DAU_RA, "w", encoding="utf-8").write(out)
    else:
        sys.stdout.write(out)


main()
