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
            "ip_lan": ip_lan(), "cai": dict(_CAI), "api": trang_thai_api()}


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
    if api_da_cai():
        hanh_dong_api("restart")
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
KHOI_CAU_HINH = r"""$cfg = 'C:\Windows\ServiceProfiles\LocalService\AppData\Roaming\RustDesk\config'
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
"""


def _tham_so(host, khoa, mat_khau=""):
    ws = dung_ws()
    return {"host": host, "khoa": khoa, "mk": mat_khau, "cong": "" if ws else ":21116", "ws_toml": "\nallow-websocket = '%s'" % ("Y" if ws else "N"),
            "ws_opt": "\n& $rd --option allow-websocket %s | Out-Null" % ("Y" if ws else "N")}


def script_cau_hinh(host=None, khoa=None):
    """Chay qua agent (SYSTEM): neu may CO RustDesk thi doi dia chi may chu/khoa/WebSocket o ca cau hinh DICH VU lan cau hinh cua TUNG NGUOI DUNG
    (app RustDesk cua nguoi dung doc cau hinh rieng trong %AppData%), roi in ID. May chua cai RustDesk: bo qua (RUSTDESK_CHUA_CAI). Khong doi mat khau."""
    host, khoa = host or host_hieu_luc(), khoa or khoa_cong_khai()
    if not MAU_HOST.fullmatch(host or "") or not re.fullmatch(r"[A-Za-z0-9+/=]{20,100}", khoa or ""):
        raise RuntimeError("Máy chủ RustDesk chưa sẵn sàng (chưa cài, chưa có khóa hoặc chưa có địa chỉ).")
    ws = dung_ws()
    khoi = KHOI_CAU_HINH % _tham_so(host, khoa)
    tung_nguoi = r"""
Get-Process rustdesk -ErrorAction SilentlyContinue | Where-Object { $_.SessionId -ne 0 } | Stop-Process -Force
Start-Sleep 2
$set = [ordered]@{ 'custom-rendezvous-server' = '@HOST@'; 'relay-server' = '@HOST@'; 'key' = '@KEY@' }@WS@
Get-ChildItem C:\Users -Directory -ErrorAction SilentlyContinue | ForEach-Object {
  $f = Join-Path $_.FullName 'AppData\Roaming\RustDesk\config\RustDesk2.toml'
  if (Test-Path -LiteralPath $f) {
    $t = [IO.File]::ReadAllText($f)
    if ($t -notmatch '(?m)^\[options\]') { $t = $t.TrimEnd() + "`r`n[options]`r`n" }
    foreach ($k in $set.Keys) {
      $line = $k + " = '" + $set[$k] + "'"
      $re = '(?m)^' + [regex]::Escape($k) + ' = .*$'
      if ($t -match $re) { $t = [regex]::Replace($t, $re, $line.Replace('$', '$$')) } else { $t = [regex]::Replace($t, '(?m)^\[options\]', '[options]' + "`r`n" + $line.Replace('$', '$$')) }
    }
    $t = [regex]::Replace($t, '(?m)^rendezvous_server = .*$', "rendezvous_server = '@HOST@@CONG@'")
    [IO.File]::WriteAllText($f, $t, (New-Object Text.UTF8Encoding($false)))
  }
}
$id = ((& $rd --get-id | Out-String).Trim())
'RUSTDESK_ID=' + $id
'RUSTDESK_CFG_OK'"""
    tung_nguoi = (tung_nguoi.replace("@HOST@", host).replace("@KEY@", khoa).replace("@CONG@", "" if ws else ":21116")
                  .replace("@WS@", "\n$set['allow-websocket'] = '%s'" % ("Y" if ws else "N")))
    return ("$rd = Join-Path $env:ProgramFiles 'RustDesk\\rustdesk.exe'\nif (-not (Test-Path $rd)) { 'RUSTDESK_CHUA_CAI'; return }\n" + khoi + "\n" + tung_nguoi)


def script_cau_hinh_nguoi_dung(host=None, khoa=None):
    """Script cho nguoi dung tu chay tren MAY MINH DANG NGOI (khong can agent): doi dia chi may chu/khoa/WebSocket cua RustDesk da cai.
    Dung lenh --option cua RustDesk nen ghi dung cau hinh cua nguoi dang dang nhap va cua dich vu."""
    host, khoa = host or host_hieu_luc(), khoa or khoa_cong_khai()
    if not MAU_HOST.fullmatch(host or "") or not re.fullmatch(r"[A-Za-z0-9+/=]{20,100}", khoa or ""):
        raise RuntimeError("Máy chủ RustDesk chưa sẵn sàng (chưa cài, chưa có khóa hoặc chưa có địa chỉ).")
    ws = "\n& $rd --option allow-websocket %s | Out-Null" % ("Y" if dung_ws() else "N")
    return ("$ErrorActionPreference = 'Stop'\n"
            "$rd = Join-Path $env:ProgramFiles 'RustDesk\\rustdesk.exe'\n"
            "if (-not (Test-Path $rd)) { throw 'Máy này chưa cài RustDesk (cần bản cài đặt, không phải bản chạy trực tiếp).' }\n"
            "Get-Process rustdesk -ErrorAction SilentlyContinue | Stop-Process -Force\nStart-Sleep 2\n"
            "& $rd --option custom-rendezvous-server '%(h)s' | Out-Null\n& $rd --option relay-server '%(h)s' | Out-Null\n"
            "& $rd --option key '%(k)s' | Out-Null%(w)s\n"
            "Start-Process $rd\nWrite-Host 'Đã đổi RustDesk sang máy chủ %(h)s. Đợi vài giây cho góc dưới RustDesk báo Ready.' -ForegroundColor Green\n"
            "Read-Host 'Nhan Enter de dong'\n") % {"h": host, "k": khoa, "w": ws}


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
%(khoi)s& $rd --password '%(mk)s' | Out-Null
$id = ((& $rd --get-id | Out-String).Trim())
'RUSTDESK_ID=' + $id""" % {"url": URL_CLIENT, "sha": SHA_CLIENT, "mk": mat_khau, "khoi": KHOI_CAU_HINH % _tham_so(host, khoa, mat_khau)}


# ------------------------------------------------------------------ rustdesk-api (lejianwen, MIT): trang quan tri web + web client
VER_API = "v2.7"
URL_API = "https://github.com/lejianwen/rustdesk-api/releases/download/%s/linux-%%s.tar.gz" % VER_API
SHA_API = {
    "amd64": "d0689a353fd756815cfe560ce7cb98f764602de60d0403b51db4e5a9bd84d22a",
    "arm64v8": "830bbab588c39c7d39130e28fe4aa01f00150ebaa0385a48d1fc664cba33ccfc",
    "armv7": "9e3b520999cc060441c56c0713fc4d49387ec957670ce9a6e8453352882c75f3",
}
TEN_GOI_API = {"amd64": "amd64", "arm64v8": "arm64", "armv7": "armv7l"}
DV_API = "console-system-rustdesk-api"
CONG_API = 21114
_CAI_API = {"dang": False, "tb": "", "ok": None}


def _api_dir():
    return os.path.join(_goc(), "api")


def api_da_cai():
    return os.path.isfile(os.path.join(_api_dir(), "apimain"))


def web_host():
    return doc_cfg().get("web_host", "")


def dat_web_host(h):
    h = (h or "").strip().lower()
    if h and not MAU_HOST.fullmatch(h):
        return False, "Tên miền web không hợp lệ."
    d = doc_cfg()
    d["web_host"] = h
    luu_cfg(d)
    if api_da_cai():
        ghi_dich_vu_api()
        _lenh.chay(["systemctl", "restart", DV_API], timeout=30)
    return True, "Đã lưu tên miền web."


def _env_api():
    """Bien moi truong cho rustdesk-api: ID/relay = dia chi client dung (UDP 21116), API va WebSocket = ten mien web (Cloudflare) neu co."""
    h, w = host_hieu_luc(), web_host()
    if not MAU_HOST.fullmatch(h or ""):
        raise RuntimeError("Chưa có địa chỉ máy chủ hợp lệ.")
    env = {"RUSTDESK_API_LANG": "en", "RUSTDESK_API_RUSTDESK_ID_SERVER": "%s:21116" % h, "RUSTDESK_API_RUSTDESK_RELAY_SERVER": "%s:21117" % h,
           "RUSTDESK_API_RUSTDESK_API_SERVER": ("https://%s" % w) if w else ("http://%s:%d" % (h, CONG_API)),
           "RUSTDESK_API_RUSTDESK_KEY_FILE": os.path.join(_chay_dir(), "id_ed25519.pub"),
           "RUSTDESK_API_RUSTDESK_WS_HOST": ("wss://%s" % w) if w else "",
           "RUSTDESK_API_GIN_API_ADDR": "0.0.0.0:%d" % CONG_API, "RUSTDESK_API_APP_REGISTER": "false"}
    return env


SHIM_WS = r"""/* Console System: web client RustDesk (v1) luon goi wss://<may>:21118 va :21119. Qua Cloudflare/HTTPS chi co cong 443 nen doi sang
   duong dan /ws/id va /ws/relay cua chinh ten mien dang mo trang (Cloudflare Tunnel chuyen ve hbbs/hbbr). Mo trong LAN bang http thi giu nguyen. */
(function () {
  if (location.protocol !== "https:" || !window.WebSocket) return;
  var W = window.WebSocket;
  function doi(u) {
    try {
      var x = new URL(u);
      if (x.port === "21118") return "wss://" + location.host + "/ws/id";
      if (x.port === "21119") return "wss://" + location.host + "/ws/relay";
    } catch (e) {}
    return u;
  }
  function P(u, p) { return p === undefined ? new W(doi(u)) : new W(doi(u), p); }
  P.prototype = W.prototype;
  P.CONNECTING = 0; P.OPEN = 1; P.CLOSING = 2; P.CLOSED = 3;
  window.WebSocket = P;
})();
"""


def va_web_client(thu_muc=None):
    """Chen SHIM_WS vao resources/web/index.html cua rustdesk-api (lam lai sau moi lan cai/cap nhat; khong chen 2 lan)."""
    web = os.path.join(thu_muc or _api_dir(), "resources", "web")
    idx = os.path.join(web, "index.html")
    if not os.path.isfile(idx):
        return False
    with open(os.path.join(web, "cs-ws-shim.js"), "w", encoding="utf-8") as f:
        f.write(SHIM_WS)
    with open(idx, encoding="utf-8") as f:
        h = f.read()
    if "cs-ws-shim.js" not in h:
        h = h.replace("<head>", '<head>\n  <script src="cs-ws-shim.js"></script>', 1)
        with open(idx, "w", encoding="utf-8") as f:
            f.write(h)
    return True


def ghi_dich_vu_api():
    env = "".join("Environment=%s=%s\n" % (k, v) for k, v in _env_api().items())
    nd = ("[Unit]\nDescription=Console System - RustDesk API (trang quan tri web + web client)\nAfter=network.target %s.service\n\n[Service]\nType=simple\n"
          "WorkingDirectory=%s\n%sExecStart=%s/apimain\nRestart=always\nRestartSec=3\n\n[Install]\nWantedBy=multi-user.target\n"
          % (DV_HBBS, _api_dir(), env, _api_dir()))
    ghi_nguyen_tu("/etc/systemd/system/%s.service" % DV_API, nd.encode("utf-8"), 0o644)
    _lenh.chay(["systemctl", "daemon-reload"], timeout=30)


def _cai_api_nen():
    import shutil
    import tarfile
    try:
        ar = kien_truc()
        if ar not in SHA_API:
            raise RuntimeError("Kiến trúc %s chưa có bản rustdesk-api." % platform.machine())
        if not khoa_cong_khai():
            raise RuntimeError("Cài và chạy máy chủ RustDesk (hbbs) trước để có khóa.")
        os.makedirs(_goc(), mode=0o700, exist_ok=True)
        tam = os.path.join(_goc(), "api-%s.tgz" % secrets.token_hex(3))
        _CAI_API["tb"] = "Đang tải rustdesk-api %s..." % VER_API
        _tai(URL_API % TEN_GOI_API[ar], tam, SHA_API[ar])
        giai = os.path.join(_goc(), "api-moi")
        shutil.rmtree(giai, ignore_errors=True)
        with tarfile.open(tam) as t:
            for m in t.getmembers():                      # chong file doc hai trong goi (duong dan tuyet doi / ..)
                if m.name.startswith("/") or ".." in m.name.split("/") or m.issym() or m.islnk():
                    raise RuntimeError("Gói rustdesk-api có đường dẫn lạ: %s" % m.name)
            t.extractall(giai)
        os.unlink(tam)
        moi = os.path.join(giai, "release")
        cu = _api_dir()
        for giu in ("data", "runtime"):                    # giu co so du lieu (tai khoan, so dia chi) khi cai lai
            if os.path.isdir(os.path.join(cu, giu)):
                shutil.rmtree(os.path.join(moi, giu), ignore_errors=True)
                shutil.move(os.path.join(cu, giu), os.path.join(moi, giu))
        _lenh.chay(["systemctl", "stop", DV_API], timeout=30)
        shutil.rmtree(cu, ignore_errors=True)
        shutil.move(moi, cu)
        shutil.rmtree(giai, ignore_errors=True)
        os.chmod(os.path.join(cu, "apimain"), 0o755)
        va_web_client(cu)
        _CAI_API["tb"] = "Đang tạo dịch vụ..."
        ghi_dich_vu_api()
        _lenh.chay(["systemctl", "enable", "--now", DV_API], timeout=30)
        d = doc_cfg()
        if not d.get("api_mk"):
            # Dat mat khau admin ngau nhien va luu lai (lan dau rustdesk-api chi in mat khau ra nhat ky). Lan chay dau con dang tao CSDL -> thu lai vai lan.
            mk = secrets.token_urlsafe(9)
            env = dict(os.environ, **_env_api())
            for _ in range(8):
                time.sleep(3)
                r = _lenh.chay([os.path.join(cu, "apimain"), "reset-admin-pwd", mk], timeout=30, cwd=cu, env=env)
                if r.ok and "success" in (r.out + r.err):
                    d = doc_cfg()
                    d["api_mk"] = mk
                    luu_cfg(d)
                    break
        _CAI_API.update(ok=True, tb="Đã cài và chạy rustdesk-api %s." % VER_API)
    except Exception as e:                       # tai ve / giai nen / quyen: hien nguyen nhan
        _CAI_API.update(ok=False, tb="Lỗi: %s" % e)
    finally:
        _CAI_API["dang"] = False


def bat_dau_cai_api():
    with _KHOA:
        if _CAI_API["dang"]:
            return False
        _CAI_API.update(dang=True, ok=None, tb="Bắt đầu...")
    threading.Thread(target=_cai_api_nen, daemon=True, name="rustdesk-api-cai").start()
    return True


def hanh_dong_api(viec):
    if not api_da_cai():
        return False, "Chưa cài rustdesk-api."
    if viec == "go":
        _lenh.chay(["systemctl", "disable", "--now", DV_API], timeout=30)
        try:
            os.unlink("/etc/systemd/system/%s.service" % DV_API)
        except OSError as _loi:
            _bo_qua(_loi)
        _lenh.chay(["systemctl", "daemon-reload"], timeout=30)
        return True, "Đã gỡ dịch vụ rustdesk-api (dữ liệu vẫn giữ)."
    if viec not in ("start", "stop", "restart"):
        return False, "Hành động không hợp lệ."
    if viec != "stop":
        va_web_client()
        try:
            ghi_dich_vu_api()
        except RuntimeError as e:
            return False, str(e)
    _lenh.chay(["systemctl", viec, DV_API], timeout=30)
    return True, "Xong."


def trang_thai_api():
    d = doc_cfg()
    w = d.get("web_host", "")
    lan = "http://%s:%d" % (ip_lan(), CONG_API)
    return {"ban": VER_API, "da_cai": api_da_cai(), "chay": _hoat_dong(DV_API), "cong": _cong_nghe(CONG_API), "web_host": w,
            "admin_user": "admin", "admin_mk": d.get("api_mk", ""), "url_lan": lan, "url_web": ("https://%s" % w) if w else "", "cai": dict(_CAI_API)}
