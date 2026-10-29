# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Quan ly may tram - DIEU KHIEN TU XA bang VNC ngay trong trinh duyet (noVNC), mo phong "Remote assistance" cua OpenUEM.

Cach lam (khac OpenUEM o diem dich vu, giong o diem mat khau tam):
  * Cai TightVNC server (ban GPL chinh thuc, kiem SHA-256) dang DICH VU nhung o che do THU CONG va DANG TAT: dich vu cua
    TightVNC chay o session 0 nhung phuc vu man hinh dang hien (ke ca man hinh dang nhap / UAC) - khong can agent trong phien nguoi dung.
  * Moi phien: tao ma PIN ngau nhien 8 ky tu, ma hoa DES kieu VNC ngay tren may dich (PowerShell), ghi HKLM\\SOFTWARE\\TightVNC\\Server,
    chi cho DIA CHI CUA CONSOLE SYSTEM ket noi (IpAccessControl cua TightVNC + luat tuong lua Windows), roi bat dich vu.
  * Console System mo cau noi WebSocket<->TCP ngay tren 127.0.0.1:8895 (nginx chuyen /uem-vnc-ws/<ma phien>, da dang nhap moi vao duoc);
    trinh duyet chay noVNC (MPL-2.0, nettools/static/novnc).
  * Dong tab / bam Ket thuc / het 2 gio: tat dich vu va doi PIN.
"""
from consolesystem.core.nhatky import bo_qua as _bo_qua
from consolesystem.core import ws_cau as _WS
import sys as _sys
_sys.modules["ui.uem_vnc"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import base64
import hashlib
import ipaddress
import os
import re
import secrets
import socket
import struct
import threading
import time
import urllib.request

from ui import tk_dongco as DC
from ui import tk_dulieu as DL
from ui import uem_dulieu as UD
from ui import uem_ketnoi as UK

CONG_WS = 8895
CONG_VNC = 5900
HET_HAN_GIAY = 2 * 3600
MSI = {
    "64": ("tightvnc-2.8.85-gpl-setup-64bit.msi", "d8fbed7b27ebab86df6f780f6e86f723668f3715cee521ccaa4568812aef5f3e"),
    "32": ("tightvnc-2.8.85-gpl-setup-32bit.msi", "a4929bb1dcfc7aa245a44e8b4b7240cccc94bcad7240282409c144efe3912ae9"),
}
URL_GOC = "https://www.tightvnc.com/download/2.8.85/"
THU_MUC = os.path.join(DL.DIR, "vnc")
_KHOA = threading.Lock()
PHIEN = {}          # ma_phien -> {may_id, ip, pin, luc, kenh, dang_ket_noi}
_BRIDGE_CHAY = False
_ALPHA = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


# ----------------------------------------------------------------- MSI tren Console System
def lay_msi(bits):
    """Duong dan file MSI da kiem hash tren Console System (tai ve neu chua co). Raise RuntimeError neu khong lay duoc."""
    ten, sha = MSI[bits]
    os.makedirs(THU_MUC, exist_ok=True)
    duong = os.path.join(THU_MUC, ten)

    def dung(p):
        try:
            with open(p, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest() == sha
        except OSError:
            return False
    if dung(duong):
        return duong
    tam = duong + ".tmp"
    try:
        rq = urllib.request.Request(URL_GOC + ten, headers={"User-Agent": "ConsoleSystem-UEM"})
        with urllib.request.urlopen(rq, timeout=90) as r, open(tam, "wb") as f:
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                f.write(b)
        if not dung(tam):
            raise RuntimeError("file tải về không khớp mã SHA-256")
        os.replace(tam, duong)
        return duong
    except Exception as e:
        try:
            os.remove(tam)
        except OSError:
            pass
        raise RuntimeError(f"Console System chưa có file {ten} và không tải được từ tightvnc.com ({str(e)[:100]}). "
                           f"Chép thủ công file này vào thư mục {THU_MUC} rồi thử lại.")


# ----------------------------------------------------------------- script PowerShell
_DES = ("$k=[byte[]](0xe8,0x4a,0xd6,0x60,0xc4,0x72,0x1a,0xe0); $d=New-Object System.Security.Cryptography.DESCryptoServiceProvider; $d.Mode='ECB'; $d.Padding='None'; $d.Key=$k; "
        "$b=New-Object byte[] 8; $pb=[Text.Encoding]::ASCII.GetBytes($pin); [Array]::Copy($pb,$b,[Math]::Min(8,$pb.Length)); $enc=$d.CreateEncryptor().TransformFinalBlock($b,0,8); ")
_REG = "$r='HKLM:\\SOFTWARE\\TightVNC\\Server'; "


def _ip_ok(ip):
    return str(ipaddress.ip_address(ip))


def ps_cai(url64, url32, pi_ip):
    pi = _ip_ok(pi_ip)
    return ("$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; "
            "if (-not (Get-Service tvnserver -ErrorAction SilentlyContinue)) { "
            f"if ([Environment]::Is64BitOperatingSystem) {{ $u={DC._q(url64)}; $h={DC._q(MSI['64'][1].upper())} }} else {{ $u={DC._q(url32)}; $h={DC._q(MSI['32'][1].upper())} }}; "
            "$tmp=Join-Path $env:TEMP ('cs-vnc-' + [guid]::NewGuid().ToString('N') + '.msi'); "
            "try { if ($u -match '^https?://') { Invoke-WebRequest -UseBasicParsing -Uri $u -OutFile $tmp } else { Copy-Item -LiteralPath $u -Destination $tmp -ErrorAction Stop } } "
            "catch { 'ST=LOI TAI_LOI BITS=' + $(if ([Environment]::Is64BitOperatingSystem) { '64' } else { '32' }); return }; "
            "if ((Get-FileHash -LiteralPath $tmp -Algorithm SHA256).Hash -ne $h) { Remove-Item -LiteralPath $tmp -Force; 'ST=LOI File TightVNC tai ve khong khop ma SHA-256'; return }; "
            "$pw = -join ((48..57)+(65..90)+(97..122) | Get-Random -Count 8 | ForEach-Object { [char]$_ }); "
            "$ar='/i \"' + $tmp + '\" /quiet /norestart ADDLOCAL=\"Server\" SERVER_REGISTER_AS_SERVICE=1 SERVER_ADD_FIREWALL_EXCEPTION=0 SET_USEVNCAUTHENTICATION=1 VALUE_OF_USEVNCAUTHENTICATION=1 SET_PASSWORD=1 VALUE_OF_PASSWORD=' + $pw + ' SET_CONTROLPASSWORD=1 VALUE_OF_CONTROLPASSWORD=' + $pw; "
            "$p=Start-Process msiexec.exe -ArgumentList $ar -Wait -PassThru -WindowStyle Hidden; Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue; "
            "if ($p.ExitCode -notin 0,3010,1641) { 'ST=LOI msiexec ma ' + $p.ExitCode; return } } else { $da=$true }; "
            "Stop-Service tvnserver -Force -ErrorAction SilentlyContinue; Set-Service tvnserver -StartupType Manual; "
            + _REG +
            f"Set-ItemProperty $r -Name IpAccessControl -Value '{pi}-{pi}:0,0.0.0.0-255.255.255.255:1' -Type String; "
            "Set-ItemProperty $r -Name AcceptHttpConnections -Value 0 -Type DWord; "
            "Remove-NetFirewallRule -DisplayName 'ConsoleSystem VNC' -ErrorAction SilentlyContinue; "
            f"New-NetFirewallRule -DisplayName 'ConsoleSystem VNC' -Direction Inbound -Protocol TCP -LocalPort {CONG_VNC} -RemoteAddress {pi} -Action Allow -Profile Any | Out-Null; "
            "if ($da) { 'ST=DA_DAT Da cai san, da cau hinh lai' } else { 'ST=DA_LAM Da cai TightVNC (dich vu thu cong, dang tat)' }")


def ps_bat(pin, pi_ip, thong_bao, loopback=False):
    """loopback=True: che do TUNNEL (agent mo ket noi NGUOC qua TLS) - TightVNC chi nghe 127.0.0.1, khong lo cong ra mang."""
    pi = _ip_ok(pi_ip)
    if not re.fullmatch(r"[A-Za-z0-9]{8}", pin):
        raise ValueError("pin")
    msg = ""
    if thong_bao:
        msg = "try { & msg.exe * /TIME:25 'Quan tri vien dang ho tro tu xa may nay (Console System).' } catch {}; "
    chedo = ("Set-ItemProperty $r -Name AllowLoopback -Value 1 -Type DWord; Set-ItemProperty $r -Name LoopbackOnly -Value 1 -Type DWord; "
             "Set-ItemProperty $r -Name IpAccessControl -Value '127.0.0.1-127.0.0.1:0,0.0.0.0-255.255.255.255:1' -Type String; " if loopback else
             f"Set-ItemProperty $r -Name AllowLoopback -Value 0 -Type DWord; Set-ItemProperty $r -Name LoopbackOnly -Value 0 -Type DWord; "
             f"Set-ItemProperty $r -Name IpAccessControl -Value '{pi}-{pi}:0,0.0.0.0-255.255.255.255:1' -Type String; ")
    return ("$ErrorActionPreference='Stop'; if (-not (Get-Service tvnserver -ErrorAction SilentlyContinue)) { 'ST=LOI Chua cai TightVNC tren may nay'; return }; "
            f"$pin={DC._q(pin)}; " + _DES + _REG +
            "Set-ItemProperty $r -Name Password -Value $enc -Type Binary; Set-ItemProperty $r -Name UseVncAuthentication -Value 1 -Type DWord; "
            "Set-ItemProperty $r -Name AcceptHttpConnections -Value 0 -Type DWord; " + chedo +
            "Restart-Service tvnserver; $ok=$false; "
            f"1..24 | ForEach-Object {{ if (Get-NetTCPConnection -LocalPort {CONG_VNC} -State Listen -ErrorAction SilentlyContinue) {{ $ok=$true }} else {{ Start-Sleep -Milliseconds 500 }} }}; "
            "if (-not $ok) { 'ST=LOI Dich vu TightVNC khong mo duoc cong " + str(CONG_VNC) + "'; return }; " + msg + "'ST=DA_LAM San sang'")


PS_DUNG = ("$ErrorActionPreference='SilentlyContinue'; if (-not (Get-Service tvnserver)) { 'ST=DA_DAT Chua cai' ; return }; "
           "Stop-Service tvnserver -Force; Get-Process tvnserver | Stop-Process -Force; "
           "$pin=-join ((48..57)+(65..90)+(97..122) | Get-Random -Count 8 | ForEach-Object { [char]$_ }); " + _DES + _REG +
           "Set-ItemProperty $r -Name Password -Value $enc -Type Binary; 'ST=DA_LAM Da tat dich vu va doi ma PIN'")

PS_GO = ("$ErrorActionPreference='Stop'; Stop-Service tvnserver -Force -ErrorAction SilentlyContinue; Get-Process tvnserver -ErrorAction SilentlyContinue | Stop-Process -Force; "
         "$g=Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*','HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*' -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -like 'TightVNC*' } | Select-Object -First 1; "
         "Remove-NetFirewallRule -DisplayName 'ConsoleSystem VNC' -ErrorAction SilentlyContinue; "
         "if (-not $g) { 'ST=DA_DAT Chua cai TightVNC' ; return }; $id=($g.PSChildName); "
         "$p=Start-Process msiexec.exe -ArgumentList ('/x ' + $id + ' /qn /norestart') -Wait -PassThru -WindowStyle Hidden; "
         "if ($p.ExitCode -in 0,3010,1641) { Remove-Item -LiteralPath 'HKLM:\\SOFTWARE\\TightVNC' -Recurse -Force -ErrorAction SilentlyContinue; 'ST=DA_LAM Da go TightVNC' } else { 'ST=LOI msiexec ma ' + $p.ExitCode }")

PS_KIEM_TRA = ("$s=Get-Service tvnserver -ErrorAction SilentlyContinue; if (-not $s) { 'VNC=KHONG' } else { "
               "$v=(Get-Item \"$env:ProgramFiles\\TightVNC\\tvnserver.exe\" -ErrorAction SilentlyContinue).VersionInfo.ProductVersion; 'VNC=CO ' + $s.Status + ' ' + ($v -replace '[, ]+','.').Trim('.') }")


def _st(out, err):
    m = re.search(r"ST=(DA_DAT|DA_LAM|LOI)\s*(.*)", out or "")
    if not m:
        return False, ("Không nhận được kết quả từ máy. " + (err or (out or "").strip())[:300]).strip()
    return m.group(1) != "LOI", m.group(2).strip()[:300]


def _may(mid):
    m = DL.tim(DL.MAY.doc(), mid)
    if not m:
        raise UK.LoiMay("Không tìm thấy máy.")
    return m


def _luu_trang_thai(mid, **kw):
    def ghi(ds):
        m = DL.tim(ds, mid)
        if m is not None:
            m.setdefault("vnc", {}).update(kw, luc=time.time())
    DL.MAY.sua(ghi)


# ----------------------------------------------------------------- thao tac
def cai(mid):
    """Cai/cau hinh TightVNC tren may. (ok, thong_diep)"""
    try:
        m = _may(mid)
        c, mk, loai = UK.ket_noi(m)
        pi = DC.ip_pi_toi(m["ip"])
        if not pi:
            return False, "Không xác định được địa chỉ Console System để máy đích kết nối về."
        u64 = DC.url_tai(m["ip"], lay_msi("64"))
        u32 = DC.url_tai(m["ip"], lay_msi("32"))
        out, err = DC._chay_ps(c, ps_cai(u64, u32, pi))
        ok, tb = _st(out, err)
        mm = re.search(r"TAI_LOI BITS=(64|32)", tb)
        if not ok and mm and loai == "winrm":          # may dich khong tai duoc tu Console System (tuong lua?) -> day thang file 2 MB qua WinRM
            dich = "C:\\Windows\\Temp\\cs-vnc-" + mm.group(1) + ".msi"
            c.copy(lay_msi(mm.group(1)), dich)
            out, err = DC._chay_ps(c, ps_cai(dich, dich, pi))
            ok, tb = _st(out, err)
            DC._chay_ps(c, f"Remove-Item -LiteralPath {DC._q(dich)} -Force -ErrorAction SilentlyContinue")
    except UK.LoiMay as e:
        ok, tb = False, str(e)
    except RuntimeError as e:
        ok, tb = False, str(e)
    except Exception as e:
        ok, tb = False, DC._loi_dep(e)
    if ok:
        _luu_trang_thai(mid, da_cai=True)
    UD.ghi_tac_vu(mid, "tu_xa", "Cài TightVNC (điều khiển từ xa)", ok, tb)
    return ok, tb


def go(mid):
    try:
        m = _may(mid)
        c, mk, loai = UK.ket_noi(m)
        out, err = DC._chay_ps(c, PS_GO)
        ok, tb = _st(out, err)
    except UK.LoiMay as e:
        ok, tb = False, str(e)
    except Exception as e:
        ok, tb = False, DC._loi_dep(e)
    if ok:
        _luu_trang_thai(mid, da_cai=False)
    UD.ghi_tac_vu(mid, "tu_xa", "Gỡ TightVNC", ok, tb)
    return ok, tb


def kiem_tra(mid):
    try:
        m = _may(mid)
        c, mk, loai = UK.ket_noi(m)
        out, err = DC._chay_ps(c, PS_KIEM_TRA)
        mm = re.search(r"VNC=(KHONG|CO)\s*(\S*)\s*(\S*)", out)
        if not mm:
            return False, "Không đọc được trạng thái. " + (err or out)[:200]
        da = mm.group(1) == "CO"
        _luu_trang_thai(mid, da_cai=da, ban=mm.group(3), dich_vu=mm.group(2))
        return True, ("Đã cài TightVNC " + mm.group(3) + ", dịch vụ " + mm.group(2)) if da else "Chưa cài TightVNC."
    except UK.LoiMay as e:
        return False, str(e)
    except Exception as e:
        return False, DC._loi_dep(e)


def mo_phien(mid, thong_bao=True, hoi_phep=False):
    """Tao phien dieu khien. Tra ve (ma_phien hoac None, thong_diep).
    May co AGENT: che do TUNNEL (agent mo ket noi nguoc qua mTLS, TightVNC chi nghe 127.0.0.1, co the xin phep nguoi dang dung may).
    May chi co WinRM: che do TRUC TIEP (Console System ket noi toi cong 5900, chi cho dung IP Console System)."""
    with _KHOA:
        for t, p in PHIEN.items():
            if p["may_id"] == mid and not p.get("shell") and time.time() - p["luc"] < HET_HAN_GIAY:
                return t, "Phiên đang mở, dùng lại."
    try:
        m = _may(mid)
        c, mk, loai = UK.ket_noi(m)
        pi = DC.ip_pi_toi(m["ip"])
        if not pi:
            return None, "Không xác định được địa chỉ Console System để máy đích kết nối về."
        tunnel = loai == "agent"
        if tunnel and hoi_phep:
            from ui import uem_agent as UA
            kq = UA.hoi_phep(mid, "Quản trị viên muốn xem và điều khiển màn hình máy này (Console System). Cho phép?", 40)
            if kq in ("TU_CHOI", "HET_GIO"):
                UD.ghi_tac_vu(mid, "tu_xa", "Xin phép điều khiển từ xa", False, "Người dùng từ chối" if kq == "TU_CHOI" else "Người dùng không trả lời")
                return None, "Người đang dùng máy " + ("đã từ chối." if kq == "TU_CHOI" else "không trả lời trong 40 giây.")
        pin = "".join(secrets.choice(_ALPHA) for _ in range(8))
        out, err = DC._chay_ps(c, ps_bat(pin, pi, thong_bao, loopback=tunnel))
        ok, tb = _st(out, err)
    except UK.LoiMay as e:
        return None, str(e)
    except Exception as e:
        return None, DC._loi_dep(e)
    UD.ghi_tac_vu(mid, "tu_xa", "Mở điều khiển từ xa (VNC" + (", tunnel mTLS)" if tunnel else ")"), ok, tb)
    if not ok:
        return None, tb
    tok = secrets.token_urlsafe(24)
    with _KHOA:
        PHIEN[tok] = {"may_id": mid, "ip": m["ip"], "pin": pin, "luc": time.time(), "kenh": 0, "tunnel": tunnel, "agent_sock": None, "agent_xong": threading.Event()}
    khoi_dong_bridge()
    return tok, "Đã sẵn sàng."


def mo_phien_shell(mid, loai):
    """Phien cua so dong lenh truc tiep (chi may co agent): dung chung cau WebSocket voi VNC tunnel, agent chay cmd/PowerShell."""
    from ui import uem_agent as UA
    m = _may(mid)
    if not UA.con_song(m):
        return None, "Cửa sổ dòng lệnh trực tiếp cần agent đang chạy trên máy."
    tok = secrets.token_urlsafe(24)
    with _KHOA:
        PHIEN[tok] = {"may_id": mid, "ip": m["ip"], "pin": "", "luc": time.time(), "kenh": 0, "tunnel": True, "shell": "powershell" if loai == "powershell" else "cmd",
                      "agent_sock": None, "agent_xong": threading.Event()}
    khoi_dong_bridge()
    UD.ghi_tac_vu(mid, "cli", "Mở cửa sổ " + ("PowerShell" if loai == "powershell" else "CMD") + " trực tiếp", True, "")
    return tok, "Đã sẵn sàng."


def thong_tin_phien(tok):
    with _KHOA:
        p = PHIEN.get(tok)
        return dict(p) if p and time.time() - p["luc"] < HET_HAN_GIAY else None


def ket_thuc(tok):
    """Tat dich vu VNC + doi PIN (chay ngam, khong chan)."""
    with _KHOA:
        p = PHIEN.pop(tok, None)
    if not p:
        return False
    if p.get("shell"):
        return True                                  # agent tu diet cmd/PowerShell khi WebSocket dong

    def viec():
        try:
            m = _may(p["may_id"])
            c, mk, loai = UK.ket_noi(m)
            out, err = DC._chay_ps(c, PS_DUNG)
            ok, tb = _st(out, err)
        except Exception as e:
            ok, tb = False, str(e)[:200]
        UD.ghi_tac_vu(p["may_id"], "tu_xa", "Kết thúc điều khiển từ xa", ok, tb)
    threading.Thread(target=viec, daemon=True, name="uem-vnc-dung").start()
    return True


# ----------------------------------------------------------------- cau noi WebSocket <-> TCP (chi lang nghe 127.0.0.1)
_GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def _doc_du(s, n):
    b = b""
    while len(b) < n:
        d = s.recv(n - len(b))
        if not d:
            raise ConnectionError
        b += d
    return b


def _khung(op, data):
    n = len(data)
    h = bytes([0x80 | op])
    if n < 126:
        h += bytes([n])
    elif n < 65536:
        h += bytes([126]) + struct.pack(">H", n)
    else:
        h += bytes([127]) + struct.pack(">Q", n)
    return h + data


def _doc_khung(s):
    b1, b2 = _doc_du(s, 2)
    op, n = b1 & 0x0F, b2 & 0x7F
    if n == 126:
        n = struct.unpack(">H", _doc_du(s, 2))[0]
    elif n == 127:
        n = struct.unpack(">Q", _doc_du(s, 8))[0]
    if n > 4 * 1024 * 1024:
        raise ConnectionError
    mask = _doc_du(s, 4) if b2 & 0x80 else None
    d = _doc_du(s, n) if n else b""
    if mask:
        d = bytes(x ^ mask[i % 4] for i, x in enumerate(d)) if n < 4096 else _xor_lon(d, mask)
    return b1 & 0x80, op, d


def _xor_lon(d, mask):
    k = (mask * ((len(d) // 4) + 1))[:len(d)]
    return (int.from_bytes(d, "big") ^ int.from_bytes(k, "big")).to_bytes(len(d), "big")


class _Hdr(dict):
    """Header khong phan biet hoa thuong (de dung lai uem_agent.nhan_dien)."""
    def get(self, k, d=None):
        return dict.get(self, k.lower(), d)


def _bat_tay(cs):
    """Doc yeu cau HTTP Upgrade. Tra ve (duong, header, khoa) hoac None (da tra loi loi)."""
    cs.settimeout(10)
    dau = b""
    while b"\r\n\r\n" not in dau:
        d = cs.recv(2048)
        if not d or len(dau) > 8192:
            return None
        dau += d
    dong = dau.decode("latin-1").split("\r\n")
    mm = re.match(r"GET (/uem-(?:vnc|agent)-ws/[A-Za-z0-9_-]{20,64})(?:\?[^ ]*)? HTTP/1\.[01]$", dong[0])   # ?... : guacamole-common-js tu them
    hdr = _Hdr({k.strip().lower(): v.strip() for k, v in (x.split(":", 1) for x in dong[1:] if ":" in x)})
    key = hdr.get("sec-websocket-key")
    if not mm or not key or "websocket" not in hdr.get("upgrade", "").lower():
        cs.sendall(b"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n")
        return None
    return mm.group(1), hdr, key


def _tra_101(cs, hdr, key):
    acc = base64.b64encode(hashlib.sha1(key.encode() + _GUID, usedforsecurity=False).digest()).decode()
    sub = "\r\nSec-WebSocket-Protocol: binary" if "binary" in hdr.get("sec-websocket-protocol", "") else ""
    cs.sendall(f"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {acc}{sub}\r\n\r\n".encode())
    cs.settimeout(None)


def _bom_ws(nguon, dich, xong):
    """Chuyen khung WebSocket tu `nguon` sang `dich` (ca hai deu la phia may chu: doc khung co mask, ghi khung khong mask)."""
    try:
        while not xong.is_set():
            fin, op, d = _doc_khung(nguon)
            if op == 8:
                break
            if op == 9:
                nguon.sendall(_khung(10, d))
            elif op in (0, 1, 2):
                dich.sendall(_khung(2, d))
    except (OSError, ConnectionError):
        pass
    finally:
        xong.set()
        for s in (nguon, dich):
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass


def _xu_ly(cs):
    tcp = None
    tok = None
    la_trinh_duyet = False
    try:
        r = _bat_tay(cs)
        if not r:
            return
        duong, hdr, key = r
        tok = duong.rsplit("/", 1)[1].split("?", 1)[0]
        ngoai = _WS.lay(tok)
        if ngoai:                                   # phien cua tinh nang khac (vd Remote Desktop) dung chung cau noi nay
            _WS.bo(tok)                             # ma phien chi dung 1 lan
            tok = None
            ngoai(cs, hdr, key, _doc_khung, _khung)
            return
        p = thong_tin_phien(tok)
        if not p:
            cs.sendall(b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n")
            return
        if duong.startswith("/uem-agent-ws/"):
            # ---- phia AGENT (qua nginx 8443, mTLS): chi nhan dung agent cua may chua phien nay
            from ui import uem_agent as UA
            m = UA.nhan_dien(hdr, "127.0.0.1")
            if not p.get("tunnel") or not m or m["id"] != p["may_id"] or p.get("agent_sock") is not None:
                cs.sendall(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
                return
            _tra_101(cs, hdr, key)
            with _KHOA:
                PHIEN[tok]["agent_sock"] = cs
            p["agent_xong"].wait(HET_HAN_GIAY)        # trinh duyet bom du lieu; luong nay chi giu socket mo
            tok = None
            return
        # ---- phia TRINH DUYET (qua nginx 80, da dang nhap)
        la_trinh_duyet = True
        _tra_101(cs, hdr, key)
        with _KHOA:
            if tok in PHIEN:
                PHIEN[tok]["kenh"] += 1
        if p.get("tunnel"):
            from ui import uem_agent as UA
            with _KHOA:
                PHIEN[tok]["agent_sock"] = None
            if p.get("shell"):
                threading.Thread(target=lambda: UA.mo_shell(p["may_id"], tok, p["shell"]), daemon=True).start()
            else:
                threading.Thread(target=lambda: UA.mo_tunnel(p["may_id"], tok, CONG_VNC), daemon=True).start()
            for _ in range(300):                     # cho agent mo tunnel (toi da 30 giay)
                time.sleep(0.1)
                with _KHOA:
                    ag = PHIEN.get(tok, {}).get("agent_sock")
                if ag is not None:
                    break
            else:
                return
            xong = threading.Event()
            t1 = threading.Thread(target=_bom_ws, args=(ag, cs, xong), daemon=True)
            t1.start()
            _bom_ws(cs, ag, xong)
            with _KHOA:
                if tok in PHIEN:
                    PHIEN[tok]["agent_sock"] = None
                    ev = PHIEN[tok]["agent_xong"]
                    ev.set()
                    PHIEN[tok]["agent_xong"] = threading.Event()
            return
        tcp = socket.create_connection((p["ip"], CONG_VNC), timeout=8)
        tcp.settimeout(None)
        xong = threading.Event()

        def vnc_den_web():
            try:
                while not xong.is_set():
                    d = tcp.recv(65536)
                    if not d:
                        break
                    cs.sendall(_khung(2, d))
            except OSError:
                pass
            finally:
                xong.set()
                try:
                    cs.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
        threading.Thread(target=vnc_den_web, daemon=True).start()
        try:
            while not xong.is_set():
                fin, op, d = _doc_khung(cs)
                if op == 8:
                    break
                if op == 9:
                    cs.sendall(_khung(10, d))
                elif op in (0, 1, 2):
                    tcp.sendall(d)
        except (OSError, ConnectionError):
            pass
        finally:
            xong.set()
    except Exception as _loi:
        _bo_qua(_loi)
    finally:
        for s in (tcp, cs):
            try:
                if s:
                    s.close()
            except OSError:
                pass
        if tok and la_trinh_duyet:
            with _KHOA:
                if tok in PHIEN:
                    PHIEN[tok]["kenh"] = max(0, PHIEN[tok]["kenh"] - 1)
                    het = PHIEN[tok]["kenh"] == 0
                else:
                    het = False
            if het:
                threading.Timer(8.0, _neu_van_dong, args=(tok,)).start()     # cho trinh duyet kip noi lai (F5) truoc khi tat


def _neu_van_dong(tok):
    with _KHOA:
        p = PHIEN.get(tok)
        dong = p is not None and p["kenh"] == 0
    if dong:
        ket_thuc(tok)


def _lang_nghe():
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", CONG_WS))
    srv.listen(16)
    while True:
        cs, _a = srv.accept()
        threading.Thread(target=_xu_ly, args=(cs,), daemon=True).start()


def _canh_gac():
    while True:
        time.sleep(60)
        with _KHOA:
            qua = [t for t, p in PHIEN.items() if time.time() - p["luc"] >= HET_HAN_GIAY]
        for t in qua:
            ket_thuc(t)


def khoi_dong_bridge():
    global _BRIDGE_CHAY
    with _KHOA:
        if _BRIDGE_CHAY:
            return True
        _BRIDGE_CHAY = True
    try:
        socket.socket().close()
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", CONG_WS))
        s.close()
    except OSError:
        return False                    # cong dang duoc tien trinh khac giu (vd: may thu chay song song)
    threading.Thread(target=_lang_nghe, daemon=True, name="uem-vnc-bridge").start()
    threading.Thread(target=_canh_gac, daemon=True, name="uem-vnc-gac").start()
    return True


_WS.dat_khoi_dong(khoi_dong_bridge)
