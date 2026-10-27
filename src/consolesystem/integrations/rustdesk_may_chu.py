# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
[integrations] Logic may chu RustDesk (khong giao dien): may chu RustDesk (hbbs = ID/rendezvous, hbbr = relay) chay ngay tren Console System + cai client RustDesk len may Windows.

  * "Cai may chu": tai ban phat hanh CHINH THUC cua rustdesk/rustdesk-server tu GitHub (ghim phien ban + SHA-256 trong ma), giai nen hbbs/hbbr,
    tao 2 dich vu systemd console-system-rustdesk-hbbs / -hbbr (chi tao khi nguoi dung bam Cai, khong tu bat luc cai Console System).
  * Khoa: hbbs tu tao cap khoa id_ed25519(.pub) o lan chay dau; chay voi `-k _` nen client PHAI co khoa moi ket noi duoc.
  * Danh sach thiet bi: doc (chi doc) co so du lieu hbbs db_v2.sqlite3, bang peer. Ban mien phi cua RustDesk Server KHONG co trang quan tri web
    (trang quan tri co nguoi dung/nhom/chia se la ban Pro tra phi) - trang nay hien thi nhung gi hbbs thuc su luu.
  * Client Windows: script PowerShell tai ban cai CHINH THUC (ghim SHA-256), cai im lang, dien san May chu ID + May chu chuyen tiep + Key,
    dat mat khau co dinh. Dung chung cho: nut Cai tren trang RustDesk (agent), buoc "RustDesk" cua Trien khai phan mem (WinRM), file .ps1 cai tay.
  * Ra Internet: nhap ten mien / IP cong cong + cong NGOAI (router) cua May chu ID (P) va chuyen tiep (R). Router chuyen tiep P-1/TCP -> 21115,
    P/TCP+UDP -> 21116, R/TCP -> 21117 (RustDesk tu dung cong P-1 de kiem tra NAT). File cai dat (luu vao kho Trien khai phan mem) dien san tat ca. Client RustDesk dung giao thuc rieng (TCP/UDP), khong di qua Cloudflare Tunnel (chi HTTP) duoc.
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
CONG_ID, CONG_RELAY = 21116, 21117                     # cong NOI BO cua hbbs / hbbr (cong ngoai router co the khac, luu trong cau hinh)
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
    d.setdefault("relay", "")
    d.setdefault("cong_id", CONG_ID)
    d.setdefault("cong_relay", CONG_RELAY)
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
    return True, "Đã lưu mật khẩu chung, đang áp dụng xuống các máy. " + cap_nhat_kho()[1]


def script_dat_mk(mk):
    if not MAU_MK.fullmatch(mk or ""):
        raise RuntimeError("Mật khẩu không hợp lệ.")
    return ("$rd = Join-Path $env:ProgramFiles 'RustDesk\\rustdesk.exe'\n"
            "if (-not (Test-Path $rd)) { throw 'Máy chưa cài RustDesk.' }\n"
            "& $rd --password '%s' | Out-Null\n'RUSTDESK_MK_OK'" % mk)


def host_hieu_luc():
    """May chu ID ma client se dung: cau hinh tay (ten mien / IP cong cong), neu chua co thi IP LAN (chi dung duoc trong mang noi bo)."""
    return doc_cfg().get("host") or ip_lan()


def relay_hieu_luc():
    """May chu chuyen tiep (relay): cau hinh rieng, neu de trong thi trung May chu ID."""
    d = doc_cfg()
    return d.get("relay") or d.get("host") or ip_lan()


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
            "cong": {str(c): _cong_nghe(c) for c in (21115, 21116, 21117)}, "khoa": khoa_cong_khai(), "host": cfg["host"], "relay": cfg["relay"],
            "cong_id": cfg["cong_id"], "cong_relay": cfg["cong_relay"], "ten_nat": cfg.get("ten_nat", ""), "ten_udp": cfg.get("ten_udp", ""), "mk_chung": cfg.get("mk_chung", ""), "dia_chi": dia_chi(),
            "kho": tep_kho_tt(), "host_hieu_luc": host_hieu_luc(), "relay_hieu_luc": relay_hieu_luc(), "ip_lan": ip_lan(), "cai": dict(_CAI)}


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
    relay = relay_hieu_luc()
    if not MAU_HOST.fullmatch(relay or ""):
        raise RuntimeError("Chưa có địa chỉ máy chủ hợp lệ. Nhập tên miền hoặc IP ở mục Cấu hình.")
    os.makedirs(_chay_dir(), mode=0o700, exist_ok=True)
    f = {DV_HBBS: _unit(DV_HBBS, "Console System - RustDesk ID server (hbbs)", "%s/hbbs -r %s -k _" % (_bin(), dia_chi()["relay"])),
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
        _CAI.update(ok=True, tb="Đã cài và chạy RustDesk Server %s. %s" % (VER_SERVER, cap_nhat_kho()[1]))
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


def _cong(x, mac_dinh):
    try:
        x = int(str(x if x is not None else "").strip() or mac_dinh)
    except ValueError:
        return None
    return x if 2 <= x <= 65535 else None


def dia_chi():
    """Dia chi client dung: May chu ID 'host[:P]', chuyen tiep 'relay[:R]' (bo cong neu la cong mac dinh), rendezvous 'host:P', cong ngoai P/R."""
    d = doc_cfg()
    h, r = host_hieu_luc(), relay_hieu_luc()
    p, q = int(d.get("cong_id") or CONG_ID), int(d.get("cong_relay") or CONG_RELAY)
    return {"id": h if p == CONG_ID else "%s:%d" % (h, p), "relay": r if q == CONG_RELAY else "%s:%d" % (r, q), "rv": "%s:%d" % (h, p),
            "cong_id": p, "cong_relay": q}


def dat_may_chu(host, relay="", cong_id=None, cong_relay=None, ten_nat="", ten_udp=""):
    """Luu ten mien / IP cong cong + cong ngoai cua May chu ID va chuyen tiep. Khoi dong lai hbbs (bao dung dia chi relay), cap nhat file cai trong kho."""
    host, relay = (host or "").strip().lower(), (relay or "").strip().lower()
    ten_nat, ten_udp = (ten_nat or "").strip().lower(), (ten_udp or "").strip().lower()
    for x in (host, relay, ten_nat, ten_udp):
        if x and not MAU_HOST.fullmatch(x):
            return False, "Tên miền / IP không hợp lệ (chỉ chữ, số, dấu chấm, gạch ngang; cổng nhập ở ô riêng)."
    p, q = _cong(cong_id, CONG_ID), _cong(cong_relay, CONG_RELAY)
    if not p or not q or len({p - 1, p, q}) < 3:
        return False, "Cổng không hợp lệ: số từ 2 đến 65535, cổng chuyển tiếp phải khác cổng ID và cổng ID - 1."
    d = doc_cfg()
    d.update(host=host, relay=relay, cong_id=p, cong_relay=q, ten_nat=ten_nat, ten_udp=ten_udp)   # ten_nat/ten_udp: chi de huong dan NAT
    d.pop("ws", None)
    luu_cfg(d)
    if da_cai():
        hanh_dong("restart")
    tb = "Đã lưu. "
    if host and not re.fullmatch(r"[0-9.]+", host):
        try:
            tb += "Tên miền %s đang trỏ về IP %s. " % (host, socket.gethostbyname(host))
        except OSError:
            tb += "Cảnh báo: chưa phân giải được tên miền %s (kiểm tra bản ghi DNS / DDNS). " % host
    return True, tb + cap_nhat_kho()[1]


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
TAI_VE = r"""$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$exe = Join-Path $env:TEMP ('rustdesk-setup-' + [guid]::NewGuid().ToString('N') + '%(duoi)s')
$ok = $false
for ($i = 1; $i -le 3 -and -not $ok; $i++) {
    try {
        Invoke-WebRequest -UseBasicParsing -Uri '%(url)s' -OutFile $exe
        $ok = ((Get-FileHash $exe -Algorithm SHA256).Hash.ToLower() -eq '%(sha)s')
    } catch { Start-Sleep 5 }
    if (-not $ok) { Remove-Item $exe -Force -ErrorAction SilentlyContinue }
}
if (-not $ok) { throw 'Không tải được RustDesk hoặc file không khớp SHA-256 (đã thử 3 lần).' }
"""
MAU_KHOA = re.compile(r"[A-Za-z0-9+/=]{20,100}")

# Ghi cau hinh cho DICH VU RustDesk (chay duoi LocalService) roi dung lenh --option cua RustDesk cho chac. allow-websocket = 'N': ve duong UDP/TCP thuong
# (may tung bat WebSocket o ban truoc se tu tat).
KHOI_CAU_HINH = r"""$cfg = 'C:\Windows\ServiceProfiles\LocalService\AppData\Roaming\RustDesk\config'
New-Item -ItemType Directory -Force -Path $cfg | Out-Null
@"
rendezvous_server = '%(rv)s'
nat_type = 1
serial = 0

[options]
custom-rendezvous-server = '%(id)s'
relay-server = '%(relay)s'
key = '%(khoa)s'
allow-websocket = 'N'
approve-mode = '%(duyet)s'
"@ | Set-Content -Path (Join-Path $cfg 'RustDesk2.toml') -Encoding ASCII
try { Restart-Service RustDesk -ErrorAction Stop } catch { Start-Sleep 5; Start-Service RustDesk -ErrorAction SilentlyContinue }
Start-Sleep 5
& $rd --option custom-rendezvous-server '%(id)s' | Out-Null
& $rd --option relay-server '%(relay)s' | Out-Null
& $rd --option key '%(khoa)s' | Out-Null
& $rd --option allow-websocket N | Out-Null
& $rd --option approve-mode %(duyet)s | Out-Null
"""


def _may_chu(host=None, relay=None, khoa=None):
    host = host or host_hieu_luc()
    relay = relay or (relay_hieu_luc() if host == host_hieu_luc() else host)
    khoa = khoa or khoa_cong_khai()
    if not MAU_HOST.fullmatch(host or "") or not MAU_HOST.fullmatch(relay or "") or not MAU_KHOA.fullmatch(khoa or ""):
        raise RuntimeError("Máy chủ RustDesk chưa sẵn sàng (chưa cài, chưa có khóa hoặc chưa có địa chỉ).")
    dc = dia_chi()
    p, q = (dc["cong_id"], dc["cong_relay"]) if host == host_hieu_luc() else (CONG_ID, CONG_RELAY)
    return {"host": host, "khoa": khoa, "duyet": "click" if doc_cfg().get("duyet") else "password", "rv": "%s:%d" % (host, p), "id": host if p == CONG_ID else "%s:%d" % (host, p),
            "relay": relay if q == CONG_RELAY else "%s:%d" % (relay, q)}


def script_cau_hinh(host=None, khoa=None, relay=None):
    """Chay qua agent (SYSTEM): neu may CO RustDesk thi doi May chu ID / chuyen tiep / khoa o ca cau hinh DICH VU lan cau hinh cua TUNG NGUOI DUNG
    (app RustDesk cua nguoi dung doc cau hinh rieng trong %AppData%), roi in ID. May chua cai RustDesk: bo qua (RUSTDESK_CHUA_CAI). Khong doi mat khau."""
    t = _may_chu(host, relay, khoa)
    return ("$rd = Join-Path $env:ProgramFiles 'RustDesk\\rustdesk.exe'\nif (-not (Test-Path $rd)) { 'RUSTDESK_CHUA_CAI'; return }\n"
            + KHOI_CAU_HINH % t + "\n" + _khoi_tung_nguoi(t) + "\n$id = ((& $rd --get-id | Out-String).Trim())\n'RUSTDESK_ID=' + $id\n'RUSTDESK_CFG_OK'")


def _khoi_tung_nguoi(t):
    """Ghi May chu ID / chuyen tiep / khoa vao cau hinh RIENG cua tung nguoi dung (C:\\Users\\*\\AppData\\Roaming\\RustDesk): app RustDesk cua nguoi dung
    doc file nay, may tung tro may chu khac se van bao dia chi cu neu chi doi cau hinh dich vu."""
    tung_nguoi = r"""
Get-Process rustdesk -ErrorAction SilentlyContinue | Where-Object { $_.SessionId -ne 0 } | Stop-Process -Force
Start-Sleep 2
$set = [ordered]@{ 'custom-rendezvous-server' = '@HOST@'; 'relay-server' = '@RELAY@'; 'key' = '@KEY@'; 'allow-websocket' = 'N'; 'approve-mode' = '@DUYET@' }
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
    $t = [regex]::Replace($t, '(?m)^rendezvous_server = .*$', "rendezvous_server = '@RV@'")
    [IO.File]::WriteAllText($f, $t, (New-Object Text.UTF8Encoding($false)))
  }
}"""
    return tung_nguoi.replace("@RV@", t["rv"]).replace("@HOST@", t["id"]).replace("@RELAY@", t["relay"]).replace("@KEY@", t["khoa"]).replace("@DUYET@", t["duyet"])


def script_cau_hinh_nguoi_dung(host=None, khoa=None, relay=None):
    """Script cho nguoi dung tu chay tren MAY MINH DANG NGOI (khong can agent): doi May chu ID / chuyen tiep / khoa cua RustDesk da cai.
    Dung lenh --option cua RustDesk nen ghi dung cau hinh cua nguoi dang dang nhap va cua dich vu."""
    t = _may_chu(host, relay, khoa)
    return ("$ErrorActionPreference = 'Stop'\n"
            "$rd = Join-Path $env:ProgramFiles 'RustDesk\\rustdesk.exe'\n"
            "if (-not (Test-Path $rd)) { throw 'Máy này chưa cài RustDesk (cần bản cài đặt, không phải bản chạy trực tiếp).' }\n"
            "Get-Process rustdesk -ErrorAction SilentlyContinue | Stop-Process -Force\nStart-Sleep 2\n"
            "& $rd --option custom-rendezvous-server '%(id)s' | Out-Null\n& $rd --option relay-server '%(relay)s' | Out-Null\n"
            "& $rd --option key '%(khoa)s' | Out-Null\n& $rd --option allow-websocket N | Out-Null\n& $rd --option approve-mode %(duyet)s | Out-Null\n"
            "Start-Process $rd\nWrite-Host 'Đã đổi RustDesk sang máy chủ ID %(id)s, chuyển tiếp %(relay)s. Đợi vài giây cho góc dưới RustDesk báo Ready.' -ForegroundColor Green\n"
            "Read-Host 'Nhan Enter de dong'\n") % t


def script_client(mat_khau, host=None, khoa=None, relay=None, url=None, sha=None, ben_canh=False):
    """PowerShell cai RustDesk client roi DIEN SAN May chu ID / chuyen tiep / Key, dat mat khau co dinh, in ra ID.
    Mac dinh tai ban chinh thuc tu GitHub (SHA-256 ghim); url/sha cho phep dung file .exe/.msi trong Tai nguyen cua Console System;
    ben_canh=True: dung bo cai rustdesk-setup.exe nam CANH script (goi MSI), khong can Internet de tai."""
    t = _may_chu(host, relay, khoa)
    if not (re.fullmatch(r"[A-Za-z0-9]{8,64}", mat_khau) or MAU_MK.fullmatch(mat_khau)):
        raise RuntimeError("Mật khẩu không hợp lệ.")
    url, sha = url or URL_CLIENT, (sha or SHA_CLIENT).lower()
    if not re.fullmatch(r"https?://[A-Za-z0-9._:/%?=&+\-]{4,500}", url) or not re.fullmatch(r"[0-9a-f]{64}", sha):
        raise RuntimeError("Đường tải bộ cài RustDesk không hợp lệ.")
    msi = url.lower().split("?")[0].endswith(".msi")
    # Bo cai chay qua WMI (Win32_Process.Create) de TACH khoi phien WinRM: WinRM dong phien thi giet moi tien trinh con, bo cai dang go/cai lai
    # dich vu se bi cat ngang (may mat dich vu RustDesk). --silent-install khong tu thoat nen khong cho no; cho DICH VU MOI chay (bat dau sau luc cai).
    lenh = ("msiexec.exe /i \"' + $exe + '\" /qn /norestart" if msi else "\"' + $exe + '\" --silent-install")
    cai = "$t0 = Get-Date\n$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = ('%s') }\n" % lenh + \
          "if ($r.ReturnValue -ne 0) { throw ('Không chạy được bộ cài RustDesk (mã ' + $r.ReturnValue + ').') }"
    tai = TAI_VE if not ben_canh else (
        "$ErrorActionPreference = 'Stop'\n$goc = Join-Path $PSScriptRoot 'rustdesk-setup.exe'\n"
        "if (-not (Test-Path $goc) -or (Get-FileHash $goc -Algorithm SHA256).Hash.ToLower() -ne '%(sha)s') { throw 'Bộ cài RustDesk trong gói bị thiếu hoặc sai SHA-256.' }\n"
        "$exe = Join-Path $env:TEMP ('rustdesk-setup-' + [guid]::NewGuid().ToString('N') + '.exe')\nCopy-Item $goc $exe -Force\n")
    tai = tai % {"url": url, "sha": sha, "duoi": ".msi" if msi else ".exe"}
    return (tai + r"""%(cai)s
$rd = Join-Path $env:ProgramFiles 'RustDesk\rustdesk.exe'
$ErrorActionPreference = 'Continue'
$moi = $false
$goi_dv = $false
for ($i = 0; $i -lt 90 -and -not $moi; $i++) {
    Start-Sleep 2
    $s = Get-CimInstance Win32_Service -Filter "Name='RustDesk'" -ErrorAction SilentlyContinue
    # Bo cai da chep rustdesk.exe ma khong tao dich vu (gap khi chay trong goi MSI / may con sot ban cu): tu tao bang lenh chinh thuc
    if (-not $s -and -not $goi_dv -and $i -ge 15 -and (Test-Path $rd)) {
        Write-Host 'Chua co dich vu RustDesk, chay rustdesk.exe --install-service'
        $goi_dv = $true
        $null = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = ('"' + $rd + '" --install-service') }
    }
    if ($s -and $s.State -ne 'Running' -and $i -ge 20) { Start-Service RustDesk -ErrorAction SilentlyContinue }
    if ($s -and $s.State -eq 'Running' -and (Test-Path $rd)) {
        $p = Get-Process -Id $s.ProcessId -ErrorAction SilentlyContinue
        $moi = [bool]($p -and $p.StartTime -gt $t0)
    }
}
Start-Sleep 8
Remove-Item $exe -Force -ErrorAction SilentlyContinue
if (-not (Test-Path $rd) -or -not (Get-Service RustDesk -ErrorAction SilentlyContinue)) { throw 'Không thấy rustdesk.exe hoặc dịch vụ RustDesk sau khi cài (đã chờ 3 phút).' }
%(khoi)s& $rd --password '%(mk)s' | Out-Null
%(tung_nguoi)s
$id = ((& $rd --get-id | Out-String).Trim())
'RUSTDESK_ID=' + $id""" % {"mk": mat_khau, "cai": cai, "khoi": KHOI_CAU_HINH % t, "tung_nguoi": _khoi_tung_nguoi(t)})


def la_bo_cai_rustdesk(ten):
    """File trong Tai nguyen co phai bo cai RustDesk khong (de Trien khai phan mem cai kem cau hinh may chu)."""
    return bool(re.fullmatch(r"rustdesk[^\\/]*\.(exe|msi)", os.path.basename(ten or "").lower()))


def sha256_tep(duong):
    h = hashlib.sha256()
    with open(duong, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def cai_va_ghi(chay_ps, may_id, url=None, sha=None):
    """Cai RustDesk len 1 may KEM May chu ID / chuyen tiep / Key va mat khau (mat khau chung neu co, khong thi giu mat khau cu / tao moi),
    roi luu ID vao danh sach may. chay_ps(script) -> (ok, out) la cach chay tren may (agent hoac WinRM). Tra (ok, thong_diep, id)."""
    ban = doc_cfg()["may"].get(may_id) or {}
    mk = mk_chung() or ban.get("mk") or secrets.token_hex(6)
    try:
        sc = script_client(mk, url=url, sha=sha)
    except RuntimeError as e:
        return False, str(e), ""
    ok, out = chay_ps(sc)
    ma = re.search(r"RUSTDESK_ID=(\d{6,12})", out or "")
    if not ok or not ma:
        return False, re.sub(r"\s+", " ", out or "Không lấy được ID RustDesk.")[-400:], ""
    if may_id:
        cfg = doc_cfg()
        cfg["may"][may_id] = {"id": ma.group(1), "mk": mk, "luc": int(time.time()), "dong_bo": True}
        luu_cfg(cfg)
    return True, "Đã cài RustDesk (máy chủ ID %s, chuyển tiếp %s), ID %s." % (dia_chi()["id"], dia_chi()["relay"], ma.group(1)), ma.group(1)


def dat_duyet(bat):
    """Bat buoc nguoi ngoi may bam 'Chap nhan' tren RustDesk moi lan co nguoi ket noi (approve-mode = click). Chi ap dung cho file cai / may cau hinh sau do."""
    d = doc_cfg()
    d["duyet"] = bool(bat)
    luu_cfg(d)
    return True, "Đã %s chế độ bắt buộc duyệt trên máy. " % ("bật" if bat else "tắt") + cap_nhat_kho()[1] + " Máy đã cài: bấm Áp dụng địa chỉ xuống máy đã cài (trang bước 4)."


def ghi_may(may_id, id_, mk=None):
    """Ghi ID RustDesk cua 1 may (vd sau khi chay file cai tu kho bang Trien khai phan mem) de tab Ho tro tu xa ket noi duoc."""
    if not may_id or not re.fullmatch(r"\d{6,12}", id_ or ""):
        return
    cfg = doc_cfg()
    mk = mk or mk_chung() or (cfg["may"].get(may_id) or {}).get("mk", "")
    cfg["may"][may_id] = {"id": id_, "mk": mk, "luc": int(time.time()), "dong_bo": bool(mk) and mk == cfg.get("mk_chung")}
    luu_cfg(cfg)


# ------------------------------------------------------------------ file cai dat MSI (tai ve + kho Trien khai phan mem)
# 1 file .msi duy nhat: chua san bo cai RustDesk chinh thuc (SHA-256 ghim) + script dien may chu ID / chuyen tiep / key / mat khau.
# Cai bang bam dup, msiexec /qn, GPO, buoc "Phan mem" cua Trien khai phan mem... Custom action chay script bang SYSTEM (deferred, khong impersonate).
TEN_MSI = "Cai-RustDesk-ConsoleSystem.msi"
_KHO = {"dang": False, "tb": ""}
WXS = """<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" Name="Console System - RustDesk (@ID@)" Language="1033" Codepage="1252" Version="@VER@" Manufacturer="Console System" UpgradeCode="7E2D41C3-9A58-4B6F-8E17-3C0A9D5F2B84">
    <Package Id="*" Description="RustDesk + cau hinh may chu Console System" Manufacturer="Console System" InstallerVersion="200" Compressed="yes" InstallScope="perMachine" />
    <Media Id="1" Cabinet="rd.cab" EmbedCab="yes" />
    <MajorUpgrade DowngradeErrorMessage="Da co ban moi hon." AllowSameVersionUpgrades="yes" />
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFiles64Folder">
        <Directory Id="CSDIR" Name="ConsoleSystem">
          <Directory Id="INSTALLDIR" Name="RustDeskSetup">
            <Component Id="RdSetup" Guid="5C1E7A20-8B3D-4F61-9A2C-1D4E6F8A0B35" Win64="yes">
              <File Id="RdSetupExe" Name="rustdesk-setup.exe" Source="rustdesk-setup.exe" KeyPath="yes" />
            </Component>
            <Component Id="RdScript" Guid="6D2F8B31-9C4E-4072-8B3D-2E5F709B1C46" Win64="yes">
              <File Id="RdScriptPs1" Name="cai-rustdesk.ps1" Source="cai-rustdesk.ps1" KeyPath="yes" />
            </Component>
          </Directory>
        </Directory>
      </Directory>
    </Directory>
    <Feature Id="Main" Title="RustDesk" Level="1">
      <ComponentRef Id="RdSetup" />
      <ComponentRef Id="RdScript" />
    </Feature>
    <CustomAction Id="RdDatPs" Property="RDPSEXE" Value="[System64Folder]WindowsPowerShell\\v1.0\\powershell.exe" />
    <CustomAction Id="RdCai" Property="RDPSEXE" Execute="deferred" Impersonate="no" Return="check"
      ExeCommand="-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File &quot;[INSTALLDIR]cai-rustdesk.ps1&quot;" />
    <InstallExecuteSequence>
      <Custom Action="RdDatPs" Sequence="1001">NOT REMOVE</Custom>
      <Custom Action="RdCai" Sequence="6590">NOT REMOVE</Custom>
    </InstallExecuteSequence>
  </Product>
</Wix>
"""


def _exe_client():
    """Bo cai RustDesk client chinh thuc, tai 1 lan va giu trong thu muc du lieu (kiem SHA-256)."""
    d = os.path.join(_goc(), "client")
    os.makedirs(d, exist_ok=True)
    f = os.path.join(d, "rustdesk-%s-x86_64.exe" % VER_CLIENT)
    if not (os.path.isfile(f) and sha256_tep(f) == SHA_CLIENT):
        _tai(URL_CLIENT, f + ".tai", SHA_CLIENT)
        os.replace(f + ".tai", f)
    return f


def script_tep_cai():
    """Script trong goi MSI: mat khau CHUNG (bat buoc, de Ho tro tu xa ket noi duoc), ghi nhat ky C:\\Windows\\Temp\\cs-rustdesk-cai.log."""
    mk = mk_chung()
    if not mk:
        raise RuntimeError("Chưa đặt mật khẩu chung (bước 2). File cài cần mật khẩu này để Hỗ trợ từ xa kết nối được.")
    dc = dia_chi()
    return ("# Console System - cai RustDesk kem May chu ID %s, chuyen tiep %s. Tao luc %s.\n" % (dc["id"], dc["relay"], time.strftime("%Y-%m-%d %H:%M"))
            + "Start-Transcript -Path (Join-Path $env:windir 'Temp\\cs-rustdesk-cai.log') -Force | Out-Null\ntry {\n"
            + _danh_dau(script_client(mk, ben_canh=True)) + "\n} catch {\n" + CHAN_DOAN + "\n  exit 1\n} finally { Stop-Transcript | Out-Null }\n")


# Ghi tung buoc vao nhat ky (Write-Host di vao transcript) de biet goi MSI dung o dau
CHAN_DOAN = r"""  Write-Host ('LOI: ' + $_.Exception.Message)
  Write-Host ('Dich vu RustDesk: ' + ((Get-Service RustDesk -ErrorAction SilentlyContinue).Status))
  Write-Host ('Co rustdesk.exe: ' + (Test-Path (Join-Path $env:ProgramFiles 'RustDesk\rustdesk.exe')))
  Get-CimInstance Win32_Process -Filter "Name like 'rustdesk%'" -ErrorAction SilentlyContinue | ForEach-Object { Write-Host ('Tien trinh: ' + $_.ProcessId + ' ' + $_.CommandLine) }
  foreach ($d in @("$env:windir\System32\config\systemprofile\AppData\Roaming\RustDesk\log", "$env:windir\ServiceProfiles\LocalService\AppData\Roaming\RustDesk\log")) {
    Get-ChildItem $d -Recurse -Filter *.log -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 2 | ForEach-Object {
      Write-Host ('--- ' + $_.FullName); Get-Content $_.FullName -Tail 25 | ForEach-Object { Write-Host $_ } } }"""


def _danh_dau(sc):
    for moc, chu in (("$t0 = Get-Date", "[1] Chay bo cai RustDesk"), ("$moi = $false", "[2] Cho dich vu RustDesk chay"),
                     ("$cfg = 'C:\\Windows\\ServiceProfiles", "[3] Ghi cau hinh may chu"), ("$id = ((& $rd --get-id", "[4] Lay ID")):
        sc = sc.replace(moc, "Write-Host '%s'\n%s" % (chu, moc), 1)
    return sc


def tao_msi(dich):
    """Dong goi MSI vao `dich` (can wixl)."""
    import shutil
    import subprocess
    import tempfile
    wixl = shutil.which("wixl")
    if not wixl:
        raise RuntimeError("Máy chủ chưa có công cụ wixl để đóng gói MSI (sudo apt install wixl).")
    sc = script_tep_cai()
    tmp = tempfile.mkdtemp(prefix="cs-rd-msi-")
    try:
        shutil.copyfile(_exe_client(), os.path.join(tmp, "rustdesk-setup.exe"))
        with open(os.path.join(tmp, "cai-rustdesk.ps1"), "w", encoding="utf-8-sig", newline="\r\n") as f:
            f.write(sc)
        tg = time.localtime()
        ver = "1.%d.%d" % (tg.tm_year % 100, tg.tm_yday * 100 + tg.tm_hour * 4 + tg.tm_min // 15)
        wxs = WXS.replace("@VER@", ver).replace("@ID@", re.sub(r"[^A-Za-z0-9.:\-]", "", dia_chi()["id"]))
        with open(os.path.join(tmp, "rd.wxs"), "w", encoding="utf-8") as f:
            f.write(wxs)
        r = subprocess.run([wixl, "-a", "x64", "-o", "out.msi", "rd.wxs"], cwd=tmp, capture_output=True, text=True, timeout=300)
        if r.returncode != 0 or not os.path.isfile(os.path.join(tmp, "out.msi")):
            raise RuntimeError("wixl lỗi: " + (r.stderr or r.stdout)[-300:])
        os.makedirs(os.path.dirname(dich), exist_ok=True)
        shutil.move(os.path.join(tmp, "out.msi"), dich + ".moi")
        os.chmod(dich + ".moi", 0o644)
        os.replace(dich + ".moi", dich)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _duong_kho():
    return os.path.join(_DD.APPS_DIR, TEN_MSI)


def tep_kho_tt():
    try:
        return {"ten": TEN_MSI, "co": True, "luc": int(os.path.getmtime(_duong_kho())), "dang": _KHO["dang"], "tb": _KHO["tb"]}
    except OSError:
        return {"ten": TEN_MSI, "co": False, "luc": 0, "dang": _KHO["dang"], "tb": _KHO["tb"]}


def _kho_nen():
    try:
        tao_msi(_duong_kho())
        try:                                         # ban cu (script .ps1) khong dung nua
            os.unlink(os.path.join(_DD.SCRIPTS_DIR, "Cai-RustDesk-ConsoleSystem.ps1"))
        except OSError:
            pass
        _KHO["tb"] = "Đã tạo %s trong kho Triển khai phần mềm (Tài nguyên, Phần mềm)." % TEN_MSI
    except Exception as e:                           # tai bo cai / wixl / quyen: bao cho nguoi dung
        _KHO["tb"] = "Lỗi tạo file MSI: %s" % e
    finally:
        _KHO["dang"] = False


def cap_nhat_kho(cho=False):
    """Tao lai file MSI trong kho (chay nen, lan dau phai tai bo cai RustDesk). cho=True: chay ngay va doi xong. (ok, thong_diep)."""
    try:
        script_tep_cai()
        _may_chu()
    except RuntimeError as e:
        return False, "File cài chưa tạo được: %s" % e
    for _ in range(600 if cho else 0):             # cho=True: doi lan tao dang chay xong roi tao lai voi cau hinh moi nhat
        if not _KHO["dang"]:
            break
        time.sleep(1)
    with _KHOA:
        if _KHO["dang"]:
            return True, "Đang tạo file MSI..."
        _KHO.update(dang=True, tb="Đang tạo file MSI (lần đầu phải tải bộ cài RustDesk)...")
    if cho:
        _kho_nen()
        return not _KHO["tb"].startswith("Lỗi"), _KHO["tb"]
    threading.Thread(target=_kho_nen, daemon=True, name="rustdesk-msi").start()
    return True, "Đang tạo lại file MSI trong kho Triển khai phần mềm."
