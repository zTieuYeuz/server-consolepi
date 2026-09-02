"""
Console Pi - Duong vao danh cho MAY (API + tai lieu tu mo ta).

Muc dich: dua Pi toi diem xa, o do co the la mot AI hoac mot ky thuat vien
khong biet gi ve thiet bi nay. Ho chi can MOT duong dan va MOT chuoi token,
doc xong la biet toan bo he thong co gi va goi duoc ngay.

Ba manh ghep:
  GET /ai            - tai lieu tu mo ta, viet cho AI doc. Khong co token thi
                       chi bao "can token", khong lo bat ky thong tin he thong
  GET /api/system    - toan bo trang thai thiet bi trong MOT lan goi
  /api/console/...   - doc va go lenh vao cong console dang cam

BAO MAT - day la duong ra Internet qua Cloudflare nen phai chat:
  - Mac dinh TAT. Phai tu bat va tu tao token trong dashboard
  - Token sinh ngau nhien 32 byte, chi HIEN MOT LAN, trong may chi luu ban bam
    SHA256 -> lo file cau hinh cung khong lay lai duoc token
  - Hai muc quyen: 'read' chi doc (chan moi phuong thuc khac GET),
    'full' moi duoc go lenh vao thiet bi mang
  - Moi lan goi deu ghi vao /var/log/console-pi-api.log
  - Thu hoi token bang mot nut, hieu luc ngay
"""
import hashlib
import hmac
import json
import os
import secrets
import subprocess
import time

from flask import request, jsonify

CONFIG_FILE = "/opt/console-pi/config.json"
AUDIT_LOG = "/var/log/console-pi-api.log"
SCOPES = ("read", "full")


# --------------------------------------------------------------- cau hinh
def _load():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save(cfg):
    # Ghi ra file tam roi doi ten: neu mat dien giua chung thi config cu van
    # nguyen ven, khong bi cut mat nua chung
    tmp = CONFIG_FILE + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    os.replace(tmp, CONFIG_FILE)


def api_enabled():
    return bool(_load().get("api_enabled", False))


def api_info():
    """Thong tin hien cho nguoi dung xem (KHONG bao gio gom token that)."""
    cfg = _load()
    return {
        "enabled": bool(cfg.get("api_enabled", False)),
        "has_token": bool(cfg.get("api_token_hash")),
        "scope": cfg.get("api_token_scope", "read"),
        "created": cfg.get("api_token_created", ""),
        "last_used": cfg.get("api_token_last_used", ""),
    }


def tao_token(scope="read"):
    """Sinh token moi. Tra ve chuoi that MOT LAN duy nhat - sau do chi con bam."""
    if scope not in SCOPES:
        scope = "read"
    token = secrets.token_urlsafe(32)
    cfg = _load()
    cfg["api_enabled"] = True
    cfg["api_token_hash"] = hashlib.sha256(token.encode()).hexdigest()
    cfg["api_token_scope"] = scope
    cfg["api_token_created"] = time.strftime("%Y-%m-%d %H:%M")
    cfg.pop("api_token_last_used", None)
    _save(cfg)
    return token


def thu_hoi_token():
    cfg = _load()
    for k in ("api_token_hash", "api_token_scope", "api_token_created",
              "api_token_last_used"):
        cfg.pop(k, None)
    cfg["api_enabled"] = False
    _save(cfg)


# --------------------------------------------------------------- xac thuc
def _token_tu_request():
    """Chap nhan ca 'Authorization: Bearer x' lan 'X-ConsolePi-Token: x'."""
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return (request.headers.get("X-ConsolePi-Token") or "").strip()


def quyen_cua_request():
    """
    Tra ve 'read' / 'full' neu token hop le, None neu khong.
    Dung hmac.compare_digest de so sanh - tranh do doan token qua thoi gian
    phan hoi.
    """
    if not api_enabled():
        return None
    token = _token_tu_request()
    if not token:
        return None
    cfg = _load()
    luu = cfg.get("api_token_hash") or ""
    if not luu:
        return None
    if not hmac.compare_digest(hashlib.sha256(token.encode()).hexdigest(), luu):
        return None
    return cfg.get("api_token_scope", "read")


def ghi_nhat_ky(quyen, ghi_chu=""):
    ip = request.headers.get("X-Forwarded-For",
                             request.remote_addr or "?").split(",")[0].strip()
    dong = (f"{time.strftime('%Y-%m-%d %H:%M:%S')} {ip} {request.method} "
            f"{request.path} quyen={quyen} {ghi_chu}\n")
    try:
        fd = os.open(AUDIT_LOG, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a") as f:
            f.write(dong)
    except OSError:
        pass


def _danh_dau_da_dung():
    try:
        cfg = _load()
        if cfg.get("api_token_hash"):
            cfg["api_token_last_used"] = time.strftime("%Y-%m-%d %H:%M")
            _save(cfg)
    except Exception:
        pass


def kiem_tra_truy_cap():
    """
    Goi tu auth.py truoc moi request. Tra ve:
      None        - khong co token (de auth.py xu ly nhu binh thuong)
      "ok"        - token hop le, cho di tiep
      (body, ma)  - token co nhung bi tu choi
    """
    quyen = quyen_cua_request()
    if quyen is None:
        # Co gui token nhung sai -> ghi lai de con biet co ai do do token
        if _token_tu_request():
            ghi_nhat_ky("SAI-TOKEN")
            return jsonify({"error": "Token khong hop le hoac API dang tat."}), 401
        return None

    # Token chi doc thi chan moi thao tac ghi - ke ca ngoai /api/
    if quyen == "read" and request.method not in ("GET", "HEAD", "OPTIONS"):
        ghi_nhat_ky(quyen, "TU-CHOI-chi-co-quyen-doc")
        return jsonify({
            "error": "Token nay chi co quyen doc.",
            "goi_y": "Chu thiet bi can tao token quyen 'full' trong tab Truy cap tu xa."
        }), 403

    ghi_nhat_ky(quyen)
    _danh_dau_da_dung()
    return "ok"


# ------------------------------------------------------- gom trang thai he thong
def _tmux_co(phien):
    r = subprocess.run(["tmux", "has-session", "-t", phien],
                       capture_output=True, timeout=6)
    return r.returncode == 0


def doc_console(dev, so_dong=200):
    """
    Doc man hinh console dang hien. Dung tmux capture-pane tren dung phien ma
    ttyd da tao - nen AI doc duoc DUNG nhung gi nguoi ngoi truoc man hinh thay.
    """
    phien = f"console-{dev}"
    if not _tmux_co(phien):
        return None, (f"Chua co phien cho {dev}. Mo mot lan bang trinh duyet "
                      f"(hoac goi POST /api/console/{dev}/send) de tao phien.")
    r = subprocess.run(
        ["tmux", "capture-pane", "-p", "-t", phien, "-S", f"-{int(so_dong)}"],
        capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        return None, r.stderr.strip()[:200]
    return r.stdout, None


def go_console(dev, van_ban, enter=True):
    """
    Go chu vao console. Dung load-buffer + paste-buffer (bracketed paste) chu
    khong phai send-keys tung dong: gui nhieu dong bang send-keys bi noi lien
    thanh mot dong - da gap that voi thu vien lenh.
    """
    phien = f"console-{dev}"
    if not _tmux_co(phien):
        subprocess.run(["systemctl", "start", f"console-pi-ttyd@{dev}"],
                       capture_output=True, timeout=20)
        for _ in range(20):
            time.sleep(0.5)
            if _tmux_co(phien):
                break
        else:
            return False, f"Khong tao duoc phien console cho {dev}."

    p = subprocess.run(["tmux", "load-buffer", "-b", "cpapi", "-"],
                       input=van_ban, text=True, capture_output=True, timeout=10)
    if p.returncode != 0:
        return False, p.stderr.strip()[:200]
    subprocess.run(["tmux", "paste-buffer", "-d", "-b", "cpapi", "-t", phien],
                   capture_output=True, timeout=10)
    if enter:
        subprocess.run(["tmux", "send-keys", "-t", phien, "Enter"],
                       capture_output=True, timeout=10)
    return True, "Da go."


def trang_thai_he_thong():
    """Toan bo nhung gi mot AI can biet, trong MOT lan goi."""
    from .home import get_ports, iface_detail, service_states, SERVICES
    from . import health, network, direct, storage

    mang = {}
    for ten in ("eth0", "wlan0", "pan0"):
        d = iface_detail(ten)
        if d:
            mang[ten] = {"ip": d["ip"], "mac": d["mac"],
                         "trang_thai": d["state"], "toc_do": d["speed"]}

    che_do, ssid, wlan_ip = network.get_net_status()

    cong = []
    for p in get_ports():
        phien = f"console-{p['devname']}"
        cong.append({
            "thiet_bi": p["devname"],
            "ten_goi_nho": p["name"],
            "chip": p.get("chip", ""),
            "phien_dang_mo": _tmux_co(phien),
            "doc": f"/api/console/{p['devname']}/read",
            "go_lenh": f"/api/console/{p['devname']}/send",
        })

    h = health.snapshot()
    th = h.get("throttle") or {}

    try:
        thu_muc, tren_usb, tep = storage.list_files()
        kho = {"thu_muc": thu_muc, "tren_usb": tren_usb,
               "so_tep": len(tep),
               "tep": [{"ten": t["name"], "byte": t["size"]} for t in tep[:30]]}
    except Exception:
        kho = {}

    try:
        bt = [{"mac": m, "ten": network.bt_device_info(m)["name"],
               "loai": network.bt_device_info(m)["cls"]["label"],
               "dang_ket_noi": network.bt_device_info(m)["connected"]}
              for m, _ in network.get_bt_paired_devices()]
    except Exception:
        bt = []

    return {
        "thiet_bi": "Console Pi",
        "phien_ban": _doc_version(),
        "thoi_diem": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mang": mang,
        "wifi": {"che_do": che_do, "ssid": ssid, "ip": wlan_ip},
        "cong_console": cong,
        "suc_khoe": {
            "nhiet_do_cpu": h.get("temp"),
            "sut_ap_dang_xay_ra": th.get("now", []),
            "sut_ap_da_tung": th.get("past", []),
            "thoi_gian_chay": h.get("uptime"),
            "tai": h.get("load"),
            "ram_mb": h.get("mem"),
            "dia_gb": h.get("disk"),
            "pin": h.get("battery"),
        },
        "bluetooth": bt,
        "kho_file": kho,
        "che_do_cam_thang": direct.dang_bat(),
        "dich_vu": service_states([s for s, _ in SERVICES]),
    }


def _doc_version():
    try:
        with open("/opt/console-pi/VERSION") as f:
            return f.read().strip()
    except OSError:
        return "?"


# ------------------------------------------------------------ tai lieu cho AI
TAI_LIEU = """# Console Pi — huong dan dieu khien tu xa

Ban dang noi chuyen voi mot **Console Pi**: mot Raspberry Pi dong vai tro
console server + bo cong cu chan doan mang, dat tai hien truong. No cam day
console (RS232/USB) vao switch/router va cho phep dieu khien qua HTTP.

Thiet bi nay thuong duoc dung khi **thiet bi mang da hong** va khong con
duong nao khac vao. Hay lam viec can trong.

## Xac thuc

Moi lenh phai kem token trong header:

    Authorization: Bearer {TOKEN}

Token hien tai co quyen: **{QUYEN}**
- `read`: chi doc. Moi POST/PUT/DELETE se bi tu choi voi ma 403.
- `full`: doc va **go duoc lenh vao thiet bi mang**.

Dia chi goc: `{GOC}`

## Buoc dau tien - luon lam truoc

    curl -H "Authorization: Bearer $TOKEN" {GOC}/api/system

Tra ve toan bo trang thai trong mot lan goi: cac card mang va IP, che do WiFi,
**danh sach cong console dang cam**, suc khoe phan cung (nhiet do, sut ap),
thiet bi Bluetooth, kho file, va trang thai tung dich vu.

Doc ky muc `cong_console` — moi phan tu co san duong dan `doc` va `go_lenh`
cho dung cong do.

## Lam viec voi thiet bi mang qua console

### 1. Xem man hinh console dang hien

    curl -H "Authorization: Bearer $TOKEN" \\
         "{GOC}/api/console/ttyUSB0/read?dong=200"

Tra ve dung nhung gi nguoi ngoi truoc man hinh dang thay. **Luon doc truoc
khi go**, de biet thiet bi dang o dau: dang hoi mat khau, dang o che do
enable, hay dang giua mot trang `--More--`.

### 2. Go lenh (can quyen `full`)

    curl -X POST -H "Authorization: Bearer $TOKEN" \\
         -H "Content-Type: application/json" \\
         -d '{{"van_ban": "show version", "enter": true}}' \\
         {GOC}/api/console/ttyUSB0/send

Sau khi go, **doi 1-2 giay roi goi lai `/read`** de xem ket qua. Thiet bi that
tra loi cham, doc ngay se thay man hinh chua kip cap nhat.

Go nhieu dong thi dat xuong dong that trong `van_ban` — he thong dung
bracketed paste nen cac dong khong bi noi lien nhau.

Gui phim dac biet: dat `enter` la `false` va go ky tu can thiet. Vi du de
thoat trang `--More--` cua Cisco thi gui mot dau cach voi `enter: false`.

## Quy tac an toan - hay tuan thu

1. **Doc truoc, go sau.** Khong bao gio go mu.
2. **Khong go lenh xoa cau hinh** (`erase`, `write erase`, `delete`,
   `format`, `reload` khong xac nhan) tru khi nguoi dung yeu cau ro rang trong
   chinh cuoc hoi thoai nay.
3. **Khong tu luu cau hinh** (`write memory`, `copy run start`) tru khi duoc
   bao. Cau hinh chua luu con cuu duoc bang cach khoi dong lai thiet bi.
4. Neu man hinh console dang o dau nhac la (bootloader, rommon, hoi mat khau),
   **hay bao lai cho nguoi dung** thay vi doan.
5. Moi lan goi deu duoc ghi nhat ky tren thiet bi.

## Cac duong dan khac

| Duong dan | Y nghia |
|---|---|
| `GET /api/system` | Toan bo trang thai (bat dau tu day) |
| `GET /api/console` | Danh sach cong console dang cam |
| `GET /api/console/<dev>/read?dong=N` | Doc man hinh console |
| `POST /api/console/<dev>/send` | Go lenh (can quyen `full`) |
| `GET /api/health` | Rieng suc khoe phan cung |
| `GET /ai` | Chinh tai lieu nay |

Giao dien cho nguoi dung o `{GOC}/` — dang nhap bang tai khoan Linux cua may.

## Khi gap loi

- `401` — token sai, hoac chu thiet bi da tat API.
- `403` — token chi co quyen doc, ma ban dang thu ghi.
- `"Chua co phien cho ttyUSB0"` — cong do chua duoc mo lan nao. Cu goi
  `/send`, he thong se tu mo phien roi go.
"""


TAI_LIEU_CHUA_CO_TOKEN = """# Console Pi

Day la duong vao danh cho may cua mot thiet bi Console Pi.

Ban can mot token de dung. Hay hoi nguoi so huu thiet bi: trong dashboard,
tab **Truy cap tu xa** co muc *Cho AI / may khac truy cap* de tao token.

Sau do goi lai duong dan nay kem header:

    Authorization: Bearer <token>

va ban se nhan duoc tai lieu day du.
"""


# ------------------------------------------------------------------- routes
def _dev_hop_le(dev):
    """Chi cho ttyUSB0-9 va ttyACM0-9 - chan moi thu khac truoc khi vao lenh."""
    import re
    return bool(re.fullmatch(r"tty(USB|ACM)\d{1,2}", dev or ""))


def register_api(app):
    from flask import Response

    def _goc():
        """Dia chi goc dung nhu AI vua goi toi - qua Cloudflare thi la ten mien."""
        proto = request.headers.get("X-Forwarded-Proto", "http")
        return f"{proto}://{request.host}"

    @app.route("/ai")
    def ai_doc():
        quyen = quyen_cua_request()
        if not quyen:
            return Response(TAI_LIEU_CHUA_CO_TOKEN, mimetype="text/markdown",
                            status=401)
        noi_dung = (TAI_LIEU
                    .replace("{TOKEN}", "<token cua ban>")
                    .replace("{QUYEN}", quyen)
                    .replace("{GOC}", _goc()))
        return Response(noi_dung, mimetype="text/markdown")

    @app.route("/api/system")
    def api_system():
        return jsonify(trang_thai_he_thong())

    @app.route("/api/health")
    def api_health():
        from . import health
        return jsonify(health.snapshot())

    @app.route("/api/console")
    def api_console_list():
        return jsonify(trang_thai_he_thong()["cong_console"])

    @app.route("/api/console/<dev>/read")
    def api_console_read(dev):
        if not _dev_hop_le(dev):
            return jsonify({"error": "Ten thiet bi khong hop le."}), 400
        try:
            dong = max(1, min(int(request.args.get("dong", 200)), 5000))
        except ValueError:
            dong = 200
        noi_dung, loi = doc_console(dev, dong)
        if loi:
            return jsonify({"error": loi}), 404
        return jsonify({"thiet_bi": dev, "man_hinh": noi_dung,
                        "so_dong": len(noi_dung.splitlines())})

    @app.route("/api/console/<dev>/send", methods=["POST"])
    def api_console_send(dev):
        if not _dev_hop_le(dev):
            return jsonify({"error": "Ten thiet bi khong hop le."}), 400
        du_lieu = request.get_json(silent=True) or {}
        van_ban = du_lieu.get("van_ban", du_lieu.get("text", ""))
        if not isinstance(van_ban, str) or not van_ban:
            return jsonify({"error": "Thieu truong 'van_ban'."}), 400
        if len(van_ban) > 8000:
            return jsonify({"error": "Van ban qua dai (toi da 8000 ky tu)."}), 400
        enter = bool(du_lieu.get("enter", True))
        ok_g, tb = go_console(dev, van_ban, enter)
        ghi_nhat_ky("full", f"go={van_ban.splitlines()[0][:60]!r}")
        if not ok_g:
            return jsonify({"error": tb}), 500
        return jsonify({"ok": True, "thong_bao": tb,
                        "goi_y": "Doi 1-2 giay roi goi /read de xem ket qua."})

    return app
