"""Chay tren Console: test that nhieu chuc nang qua HTTP (dau man hinh tai cho)."""
import io, json, sys, tarfile, urllib.request, urllib.parse, uuid
MID = sys.argv[1]
G = "http://127.0.0.1:5000"
H = {"X-ConsolePi-Local": "1"}
kq = {}
def goi(p, data=None, js=None, timeout=300, raw=False):
    hd = dict(H)
    if js is not None:
        data = json.dumps(js).encode(); hd["Content-Type"] = "application/json"
    elif isinstance(data, dict):
        data = urllib.parse.urlencode(data, doseq=True).encode()
    r = urllib.request.urlopen(urllib.request.Request(G + p, data=data, headers=hd), timeout=timeout)
    b = r.read()
    return (r.status, b) if raw else (r.status, b.decode("utf-8", "replace"))
def ca(ma, f):
    try:
        kq[ma] = f()
    except Exception as e:
        kq[ma] = "LOI " + type(e).__name__ + ": " + str(e)[:150]
    print(ma, "->", kq[ma], flush=True)
def dv():
    j = json.loads(goi("/uem/may/%s/dich-vu/api" % MID, js={"viec": "ds"})[1]); return "DAT %d dich vu" % len(j["ds"]) if j.get("ok") and len(j["ds"]) > 50 else j
def tt():
    j = json.loads(goi("/uem/may/%s/tien-trinh/api" % MID, js={"viec": "ds"})[1]); return "DAT %d tien trinh" % len(j["ds"]) if j.get("ok") and len(j["ds"]) > 20 else j
def file_():
    s, b = goi("/uem/may/%s/duyet-file/tai?p=%s" % (MID, urllib.parse.quote(r"C:\Windows\win.ini")), raw=True)
    return "DAT tai win.ini %d byte" % len(b) if s == 200 and b"fonts" in b.lower() else (s, b[:80])
def ping():
    s, h = goi("/nettools/ping", {"host": "192.168.110.34", "count": "2"}); return "DAT" if "ttl" in h.lower() or "0% " in h else "KHONG THAY KET QUA PING"
def dns():
    s, h = goi("/nettools/dns-check", {"ten": "google.com", "host": "google.com", "domain": "google.com"}); return "DAT" if s == 200 and ("google" in h) else s
def tls():
    s, h = goi("/nettools/tls-check", {"host": "kho-console.home-server.id.vn", "port": "443"}); return "DAT" if s == 200 and ("hết hạn" in h.lower() or "het han" in h.lower() or "valid" in h.lower() or "Không" in h) else s
def kho_file():
    ten = "cs-thu-%s.txt" % uuid.uuid4().hex[:6]
    bd = "----cs" + uuid.uuid4().hex
    body = ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\nContent-Type: text/plain\r\n\r\nnoi dung thu\r\n--%s--\r\n" % (bd, ten, bd)).encode()
    r = urllib.request.Request(G + "/storage/len", data=body, headers=dict(H, **{"Content-Type": "multipart/form-data; boundary=" + bd}))
    urllib.request.urlopen(r, timeout=60)
    s, b = goi("/storage/tai/" + ten, raw=True)
    ok = s == 200 and b.strip() == b"noi dung thu"
    goi("/storage/xoa", {"name": ten, "ten": ten})
    s2, h = goi("/storage")
    return "DAT len/tai/xoa" if ok and ten not in h else ("LOI", ok, ten in h)
def logs():
    s, b = goi("/logs/tai", raw=True); return "DAT %d byte" % len(b) if s == 200 and len(b) > 100 else s
def sao_luu():
    s, b = goi("/settings/sao-luu", raw=True, timeout=600)
    t = tarfile.open(fileobj=io.BytesIO(b), mode="r:gz")
    ten = t.getnames()
    m = json.load(t.extractfile("_console-system-sao-luu.json"))
    return "DAT %d muc, co data/console.db: %s, secrets: %s" % (len(ten), "data/console.db" in ten, any(x.startswith("secrets/") for x in ten))
for ma, f in (("5.8 dich vu", dv), ("5.9 tien trinh", tt), ("5.10 tai file", file_), ("9.1 ping", ping), ("9.1 dns", dns), ("9.1 tls", tls),
              ("12.1 kho file", kho_file), ("13.4 nhat ky", logs), ("13.2 sao luu cau hinh", sao_luu)):
    ca(ma, f)
