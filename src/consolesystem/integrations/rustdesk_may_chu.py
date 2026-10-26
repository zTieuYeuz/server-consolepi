# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
[integrations] Logic may chu RustDesk (khong giao dien): may chu RustDesk (hbbs = ID/rendezvous, hbbr = relay) chay ngay tren Console System + cai client RustDesk len may Windows.

  * "Cai may chu": tai ban phat hanh CHINH THUC cua rustdesk/rustdesk-server tu GitHub (ghim phien ban + SHA-256 trong ma), giai nen hbbs/hbbr,
    tao 2 dich vu systemd console-system-rustdesk-hbbs / -hbbr (chi tao khi nguoi dung bam Cai, khong tu bat luc cai Console System).
  * Khoa: hbbs tu tao cap khoa id_ed25519(.pub) o lan chay dau; chay voi `-k _` nen client PHAI co khoa moi ket noi duoc.
  * Danh sach thiet bi: doc (chi doc) co so du lieu hbbs db_v2.sqlite3, bang peer. Ban mien phi cua RustDesk Server KHONG co trang quan tri web
    (trang quan tri co nguoi dung/nhom/chia se la ban Pro tra phi) - trang nay hien thi nhung gi hbbs thuc su luu.
  * Client Windows: script PowerShell tai ban cai CHINH THUC (ghim SHA-256), cai im lang, tro ve may chu nay va dat mat khau co dinh. Chay duoc qua
    agent (1 nut) HOAC dan thu cong tren may o ngoai Internet (script tai ve tu trang nay).
  * Ra Internet: can chuyen tiep cong tren router toi may nay: TCP 21115-21119 va UDP 21116, va nhap ten mien / IP cong cong o muc Cau hinh.
    (Duong ham Cloudflare khong chuyen duoc giao thuc RustDesk.)
"""
import hashlib
import json
import os
import platform
import re
import secrets
import socket
import sqlite3
import threading
import time
import urllib.request
import zipfile

from consolesystem.core import lenh as _lenh
from consolesystem.core import duongdan as _DD
from consolesystem.core.esc import esc_html as _esc
from consolesystem.core.nhatky import bo_qua as _bo_qua
from consolesystem.core.store import ghi_nguyen_tu

VER_SERVER = "1.1.16"
URL_SERVER = "https://github.com/rustdesk/rustdesk-server/releases/download/%s/rustdesk-server-linux-%%s.zip" % VER_SERVER
SHA_SERVER = {
    "amd64": "0565c41affe6c3f409b0bddfaf5a24ccbf3f64f5f8e3fec250b69a0d5f6bdbcf",
    "arm64v8": "6a4ae3c5ca257a4278ded72fd17eb2ca4eeb0356a5425e63a3e7fcb0ec6c155c",
    "armv7": "2e832e901680bc4eb8d5d17df867e2bc9731c0bdf064b27c35084494fc279be2",
    "i386": "a10d2db36ceabec730ea2458dc0466b9fb46eda3f2ee90ab29a0bff8f92a7c22",
}
KIEN_TRUC = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64v8", "arm64": "arm64v8", "armv7l": "armv7", "i686": "i386", "i386": "i386"}
VER_CLIENT = "1.5.0"
URL_CLIENT = "https://github.com/rustdesk/rustdesk/releases/download/%s/rustdesk-%s-x86_64.exe" % (VER_CLIENT, VER_CLIENT)
SHA_CLIENT = "8555777215510d83d2d61c9dc984e4fcc838bd7e79f9d18a42585431f5e8bb47"
DV_HBBS, DV_HBBR = "console-system-rustdesk-hbbs", "console-system-rustdesk-hbbr"
CONG_TCP = (21115, 21116, 21117, 21118, 21119)
MAU_HOST = re.compile(r"[A-Za-z0-9][A-Za-z0-9.\-]{0,253}")


def _goc():
    return os.path.join(_DD.THU_MUC_DU_LIEU, "rustdesk")


def _bin():
    return os.path.join(_goc(), "bin")


def _chay_dir():
    return os.path.join(_goc(), "chay")


def _cfg_file():
    return os.path.join(_goc(), "rustdesk.json")


def doc_cfg():
    try:
        with open(_cfg_file(), encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        d = {}
    d.setdefault("host", "")
    d.setdefault("may", {})
    return d


def luu_cfg(d):
    os.makedirs(_goc(), mode=0o700, exist_ok=True)
    ghi_nguyen_tu(_cfg_file(), json.dumps(d, ensure_ascii=False, indent=1).encode("utf-8"), 0o600)


def ip_lan():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return ""


MAU_MK = re.compile(r"[A-Za-z0-9!@#%^*._\-]{8,64}")


def mk_chung():
    return doc_cfg().get("mk_chung", "")


def dat_mk_chung(mk):
    """Dat mat khau co dinh CHUNG cho moi may. Danh dau moi may la chua dong bo (se day xuong qua agent)."""
    mk = (mk or "").strip()
    if not MAU_MK.fullmatch(mk):
        return False, "Mật khẩu 8 đến 64 ký tự, chỉ gồm chữ, số và các ký hiệu ! @ # % ^ * . _ -"
    d = doc_cfg()
    d["mk_chung"] = mk
    for v in d["may"].values():
        v["dong_bo"] = v.get("mk") == mk
    luu_cfg(d)
    return True, "Đã lưu mật khẩu chung, đang áp dụng xuống các máy."


def script_dat_mk(mk):
    if not MAU_MK.fullmatch(mk or ""):
        raise RuntimeError("Mật khẩu không hợp lệ.")
    return ("$rd = Join-Path $env:ProgramFiles 'RustDesk\\rustdesk.exe'\n"
            "if (-not (Test-Path $rd)) { throw 'Máy chưa cài RustDesk.' }\n"
            "& $rd --password '%s' | Out-Null\n'RUSTDESK_MK_OK'" % mk)


def host_hieu_luc():
    """Dia chi ma client se dung: cau hinh tay, neu chua co thi IP LAN (chi dung duoc trong mang noi bo)."""
    return doc_cfg().get("host") or ip_lan()


def kien_truc():
    return KIEN_TRUC.get(platform.machine().lower())


def da_cai():
    return all(os.path.isfile(os.path.join(_bin(), x)) for x in ("hbbs", "hbbr"))


def khoa_cong_khai():
    try:
        with open(os.path.join(_chay_dir(), "id_ed25519.pub"), encoding="ascii") as f:
            return f.read().strip()
    except OSError:
        return ""


def _hoat_dong(dv):
    return _lenh.chay(["systemctl", "is-active", dv], timeout=8).out.strip() == "active"


def _cong_nghe(cong):
    s = socket.socket()
    s.settimeout(0.6)
    try:
        return s.connect_ex(("127.0.0.1", cong)) == 0
    finally:
        s.close()


def trang_thai():
    cfg = doc_cfg()
    return {"kien_truc": kien_truc(), "ban": VER_SERVER, "da_cai": da_cai(), "hbbs": _hoat_dong(DV_HBBS), "hbbr": _hoat_dong(DV_HBBR),
            "cong": {str(c): _cong_nghe(c) for c in (21115, 21116, 21117)}, "khoa": khoa_cong_khai(), "host": cfg["host"], "ws": bool(cfg.get("ws")), "host_hieu_luc": host_hieu_luc(),
            "ip_lan": ip_lan(), "cai": dict(_CAI)}


# ------------------------------------------------------------------ cai may chu
_CAI = {"dang": False, "tb": "", "ok": None}
_KHOA = threading.Lock()


def _tai(url, dich, sha, tien_do=None):
    req = urllib.request.Request(url, headers={"User-Agent": "ConsoleSystem"})
    h = hashlib.sha256()
    with urllib.request.urlopen(req, timeout=60) as r, open(dich, "wb") as f:
        while True:
            b = r.read(1 << 16)
            if not b:
                break
            h.update(b)
            f.write(b)
    if h.hexdigest() != sha:
        os.unlink(dich)
        raise RuntimeError("Tệp tải về không khớp mã SHA-256 đã ghim (%s). Không cài." % h.hexdigest()[:12])


def _unit(ten, mo_ta, lenh_chay):
    return ("[Unit]\nDescription=%s\nAfter=network.target\n\n[Service]\nType=simple\nWorkingDirectory=%s\nExecStart=%s\nRestart=always\nRestartSec=3\n\n"
            "[Install]\nWantedBy=multi-user.target\n" % (mo_ta, _chay_dir(), lenh_chay))


def ghi_dich_vu():
    host = host_hieu_luc()
    if not MAU_HOST.fullmatch(host or ""):
        raise RuntimeError("Chưa có địa chỉ máy chủ hợp lệ. Nhập tên miền hoặc IP ở mục Cấu hình.")
    os.makedirs(_chay_dir(), mode=0o700, exist_ok=True)
    f = {DV_HBBS: _unit(DV_HBBS, "Console System - RustDesk ID server (hbbs)", "%s/hbbs -r %s:21117 -k _" % (_bin(), host)),
         DV_HBBR: _unit(DV_HBBR, "Console System - RustDesk relay (hbbr)", "%s/hbbr -k _" % _bin())}
    for ten, nd in f.items():
        ghi_nguyen_tu("/etc/systemd/system/%s.service" % ten, nd.encode("utf-8"), 0o644)
    _lenh.chay(["systemctl", "daemon-reload"], timeout=30)


def _cai_nen():
    try:
        ar = kien_truc()
        if not ar:
            raise RuntimeError("Kiến trúc %s chưa được hỗ trợ." % platform.machine())
        os.makedirs(_bin(), mode=0o755, exist_ok=True)
        tam = os.path.join(_goc(), "tai-%s.zip" % secrets.token_hex(3))
        _CAI["tb"] = "Đang tải RustDesk Server %s..." % VER_SERVER
        _tai(URL_SERVER % ar, tam, SHA_SERVER[ar])
        with zipfile.ZipFile(tam) as z:
            for ten in ("hbbs", "hbbr"):
                nd = z.read("%s/%s" % (ar, ten))
                dich = os.path.join(_bin(), ten)
                with open(dich + ".moi", "wb") as f:
                    f.write(nd)
                os.chmod(dich + ".moi", 0o755)
                os.replace(dich + ".moi", dich)
        os.unlink(tam)
        _CAI["tb"] = "Đang tạo dịch vụ..."
        ghi_dich_vu()
        for dv in (DV_HBBR, DV_HBBS):
            _lenh.chay(["systemctl", "enable", "--now", dv], timeout=30)
        for _ in range(20):
            if khoa_cong_khai():
                break
            time.sleep(0.5)
        _CAI.update(ok=True, tb="Đã cài và chạy RustDesk Server %s." % VER_SERVER)
    except Exception as e:                       # tai ve / giai nen / quyen: hien nguyen nhan cho nguoi dung
        _CAI.update(ok=False, tb="Lỗi: %s" % e)
    finally:
        _CAI["dang"] = False


def bat_dau_cai():
    with _KHOA:
        if _CAI["dang"]:
            return False
        _CAI.update(dang=True, ok=None, tb="Bắt đầu...")
    threading.Thread(target=_cai_nen, daemon=True, name="rustdesk-cai").start()
    return True


def hanh_dong(viec):
    if not da_cai():
        return False, "Chưa cài máy chủ RustDesk."
    if viec == "go":
        for dv in (DV_HBBS, DV_HBBR):
            _lenh.chay(["systemctl", "disable", "--now", dv], timeout=30)
            try:
                os.unlink("/etc/systemd/system/%s.service" % dv)
            except OSError as _loi:
                _bo_qua(_loi)
        _lenh.chay(["systemctl", "daemon-reload"], timeout=30)
        return True, "Đã dừng và gỡ dịch vụ (khóa và danh sách thiết bị vẫn giữ trong thư mục dữ liệu)."
    if viec not in ("start", "stop", "restart"):
        return False, "Hành động không hợp lệ."
    if viec != "stop":
        try:
            ghi_dich_vu()
        except RuntimeError as e:
            return False, str(e)
    for dv in (DV_HBBR, DV_HBBS):
        _lenh.chay(["systemctl", viec, dv], timeout=30)
    return True, {"start": "Đã chạy", "stop": "Đã dừng", "restart": "Đã khởi động lại"}[viec] + " RustDesk Server."


def dung_ws():
    return bool(doc_cfg().get("ws"))


def dat_ws(bat):
    d = doc_cfg()
    d["ws"] = bool(bat)
    luu_cfg(d)
    return True, "Đã %s chế độ WebSocket (đường Cloudflare) cho máy cài mới." % ("bật" if bat else "tắt")


def dat_host(host):
    host = (host or "").strip()
    if host and not MAU_HOST.fullmatch(host):
        return False, "Địa chỉ không hợp lệ (chỉ chữ, số, dấu chấm, gạch ngang)."
    d = doc_cfg()
    d["host"] = host
    luu_cfg(d)
    if da_cai():
        hanh_dong("restart")
    return True, "Đã lưu địa chỉ máy chủ RustDesk."


# ------------------------------------------------------------------ thiet bi (doc DB cua hbbs)
def thiet_bi():
    db = os.path.join(_chay_dir(), "db_v2.sqlite3")
    if not os.path.isfile(db):
        return []
    try:
        c = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=3)
        c.row_factory = sqlite3.Row
        ds = []
        for r in c.execute("SELECT id, created_at, user, status, note, info FROM peer ORDER BY created_at DESC LIMIT 1000"):
            try:
                info = json.loads(r["info"] or "{}")
            except ValueError:
                info = {}
            ds.append({"id": r["id"], "tao": r["created_at"], "ip": str(info.get("ip", "")).replace("::ffff:", ""), "ghi_chu": r["note"] or ""})
        c.close()
        return ds
    except sqlite3.Error as e:
        _bo_qua(e)
        return []


# ------------------------------------------------------------------ client Windows
def script_client(mat_khau, host=None, khoa=None):
    """PowerShell cai RustDesk client (ban chinh thuc, SHA-256 ghim), tro ve may chu nay, dat mat khau co dinh, in ra ID."""
    host, khoa = host or host_hieu_luc(), khoa or khoa_cong_khai()
    ws = dung_ws()
    if not MAU_HOST.fullmatch(host or "") or not re.fullmatch(r"[A-Za-z0-9+/=]{20,100}", khoa or ""):
        raise RuntimeError("Máy chủ RustDesk chưa sẵn sàng (chưa cài, chưa có khóa hoặc chưa có địa chỉ).")
    if not (re.fullmatch(r"[A-Za-z0-9]{8,64}", mat_khau) or MAU_MK.fullmatch(mat_khau)):
        raise RuntimeError("Mật khẩu không hợp lệ.")
    return r"""$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$exe = Join-Path $env:TEMP ('rustdesk-setup-' + [guid]::NewGuid().ToString('N') + '.exe')
$ok = $false
for ($i = 1; $i -le 3 -and -not $ok; $i++) {
    try {
        Invoke-WebRequest -UseBasicParsing -Uri '%(url)s' -OutFile $exe
        $ok = ((Get-FileHash $exe -Algorithm SHA256).Hash.ToLower() -eq '%(sha)s')
    } catch { Start-Sleep 5 }
    if (-not $ok) { Remove-Item $exe -Force -ErrorAction SilentlyContinue }
}
if (-not $ok) { throw 'Không tải được RustDesk hoặc file không khớp SHA-256 (đã thử 3 lần).' }
# KHONG dung -Wait: --silent-install mo ung dung/dich vu va khong thoat, se treo vo han. Doi file cai xong roi di tiep.
Start-Process $exe -ArgumentList '--silent-install'
$rd = Join-Path $env:ProgramFiles 'RustDesk\rustdesk.exe'
for ($i = 0; $i -lt 60 -and -not (Test-Path $rd); $i++) { Start-Sleep 2 }
Start-Sleep 12
Remove-Item $exe -Force -ErrorAction SilentlyContinue
if (-not (Test-Path $rd)) { throw 'Không thấy rustdesk.exe sau khi cài.' }
$cfg = 'C:\Windows\ServiceProfiles\LocalService\AppData\Roaming\RustDesk\config'
New-Item -ItemType Directory -Force -Path $cfg | Out-Null
@"
rendezvous_server = '%(host)s%(cong)s'
nat_type = 1
serial = 0

[options]
custom-rendezvous-server = '%(host)s'
relay-server = '%(host)s'
key = '%(khoa)s'%(ws_toml)s
"@ | Set-Content -Path (Join-Path $cfg 'RustDesk2.toml') -Encoding ASCII
Restart-Service RustDesk -ErrorAction SilentlyContinue
Start-Sleep 5
& $rd --option custom-rendezvous-server '%(host)s' | Out-Null
& $rd --option relay-server '%(host)s' | Out-Null
& $rd --option key '%(khoa)s' | Out-Null%(ws_opt)s
& $rd --password '%(mk)s' | Out-Null
$id = ((& $rd --get-id | Out-String).Trim())
'RUSTDESK_ID=' + $id""" % {"url": URL_CLIENT, "sha": SHA_CLIENT, "host": host, "khoa": khoa, "mk": mat_khau,
           "cong": "" if ws else ":21116", "ws_toml": "\nallow-websocket = 'Y'" if ws else "", "ws_opt": "\n& $rd --option allow-websocket Y | Out-Null" if ws else ""}
