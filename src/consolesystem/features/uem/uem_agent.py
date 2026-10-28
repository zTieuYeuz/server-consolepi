# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Quan ly may tram - AGENT v2 cho Windows (mo phong agent cua OpenUEM; khac cach lam: dich vu C# bien dich tai cho + HTTPS mTLS thay cho Go + NATS).

Agent la DICH VU WINDOWS (ConsoleSystemAgent, LocalSystem) viet bang C# (xem uem_agent_cs.py), duoc cai bang script PowerShell (qua WinRM
hoac dan 1 dong vao PowerShell quan tri tren may). Noi voi Console System qua https://<Pi>:8443 bang mTLS:
  * Agent xac thuc may chu bang CA GHIM (ca.pem) - khong tin ai khac. May chu xac thuc agent bang chung chi khach rieng (CN=cs-agent-<ma may>,
    uem_pki.py); thu hoi bang cach xoa so serial trong ban ghi may. Khong con token HTTP.
  * nginx cong 8443 bat buoc chung chi khach, roi chuyen cho ung dung kem header X-CS-Client-* + bi mat X-CS-TLS-Secret (chi nginx biet) -
    ung dung chi tin header khi co bi mat do (khong ai di cong 80 gia mao duoc).
  * Viec: ps, tep_len/tep_xuong (dang luong, khong gioi han 25MB), tunnel (VNC di nguoc qua TLS), hoi_phep, profile/profile_go/profile_chay.
  * PROFILE TU TRI: agent luu profile ve dia, tu ap dung theo chu ky ke ca khi Console System tat; gui ket qua bu o nhip sau.
  * Tu cap nhat: nhip bao ban cu -> may chu gui ma nguon moi -> agent tu bien dich + thay + khoi dong lai.
Gioi han that: chi chay trong mang noi bo toi duoc cong 8443 cua Console System (khong qua duong ham Cloudflare/Internet); Windows 10/Server 2016 tro len
(.NET Framework 4.x co san); viec mang mat khau (tao nguoi dung co mat khau) van chi di qua WinRM (khong luu mat khau xuong may qua bundle).
"""
from consolesystem.core.nhatky import bo_qua as _bo_qua
import sys as _sys
_sys.modules["ui.uem_agent"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import base64
import hmac
import json
import os
import re
import secrets
import threading
import time
from collections import deque

from ui import tk_dongco as DC
from ui import tk_dulieu as DL
from ui import uem_agent_cs as CS
from ui import uem_dulieu as UD
from ui import uem_pki as PKI

PHIEN_BAN = CS.VER_FILE
NHIP_GIAY = 25
SONG_GIAY = 90                  # khong nghe nhip qua ngan nay -> coi la mat lien lac
TOI_DA_BODY = 8 * 1024 * 1024
TOI_DA_TEP = 2 * 1024 ** 3
THU_MUC_TEP = os.path.join(DL.DIR, "tep-agent")
_CV = threading.Condition()
_HANG = {}                      # may_id -> deque([job])
_VIEC = {}                      # job_id -> job
_MA_CAI = {}                    # ma cai (dung 1 lan) -> {may_id, het_han}
_NHIP = {}                      # may_id -> {luc, ban, may, ip, luu_luc} - nhip chi giu trong bo nho (ghi dia moi 10 phut hoac khi doi thong tin)
_GUI = ("id", "kieu", "script", "timeout", "duong", "tok", "cong", "thong_bao", "giay", "pid", "ver", "chu_ky", "tasks", "pfx", "pfx_pass")
GIA_HAN_TRUOC_GIAY = 60 * 86400   # con it hon 60 ngay thi tu cap chung chi moi

PIN_CS = r'''using System;using System.Net;using System.Net.Security;using System.Security.Cryptography;using System.Security.Cryptography.X509Certificates;public static class CsPin{static string H(byte[] b){return BitConverter.ToString(SHA256.Create().ComputeHash(b)).Replace("-","");}public static void On(string h){ServicePointManager.ServerCertificateValidationCallback=delegate(object s,X509Certificate c,X509Chain ch,SslPolicyErrors e){try{if(H(c.GetRawCertData())==h)return true;if(ch==null)return false;bool co=false;foreach(X509ChainElement el in ch.ChainElements)if(H(el.Certificate.RawData)==h)co=true;if(!co)return false;foreach(X509ChainStatus st in ch.ChainStatus)if(st.Status!=X509ChainStatusFlags.NoError&&st.Status!=X509ChainStatusFlags.UntrustedRoot&&st.Status!=X509ChainStatusFlags.PartialChain&&st.Status!=X509ChainStatusFlags.RevocationStatusUnknown&&st.Status!=X509ChainStatusFlags.OfflineRevocation)return false;return true;}catch{return false;}};}}'''
"""Ghim luc cai: chap nhan may chu neu chung chi may chu HOAC mot chung chi trong chuoi (CA) co dau van tay SHA-256 da ghim va chuoi ky hop le.
Ghim theo CA nen IP/chung chi may chu doi khong lam hong file cai da tao."""

USER_PS = r"""# Console System - tro ly phien nguoi dung: ghi may in rieng / man hinh / nguoi dang nhap vao thu muc nd (dich vu doc va gui di)
$ErrorActionPreference = 'SilentlyContinue'
$Dir = Split-Path -Parent $MyInvocation.MyCommand.Path
function Txt($a) { if ($a -eq $null) { return '' }; $s = ''; foreach ($c in $a) { if ($c -ne 0) { $s += [char]$c } }; return $s.Trim() }
while ($true) {
  try {
    $pr = @(Get-CimInstance Win32_Printer | ForEach-Object { [ordered]@{ name = [string]$_.Name; port = [string]$_.PortName; is_default = [bool]$_.Default; is_network = [bool]$_.Network; is_shared = [bool]$_.Shared } })
    $mon = @(Get-CimInstance -Namespace root\wmi -ClassName WmiMonitorID | ForEach-Object { [ordered]@{ manufacturer = (Txt $_.ManufacturerName); model = (Txt $_.UserFriendlyName); serial = (Txt $_.SerialNumberID); week_of_manufacture = [int]$_.WeekOfManufacture; year_of_manufacture = [int]$_.YearOfManufacture } })
    $body = [ordered]@{ user = ($env:USERDOMAIN + '\' + $env:USERNAME); printers = $pr; monitors = $mon } | ConvertTo-Json -Depth 5 -Compress
    [IO.File]::WriteAllText((Join-Path $Dir ('nd\' + $env:USERNAME + '.json')), $body, (New-Object Text.UTF8Encoding($false)))
  } catch {}
  Start-Sleep -Seconds 1800
}
"""

PS_GO = r"""$ErrorActionPreference='SilentlyContinue'
Unregister-ScheduledTask -TaskName 'ConsoleSystemUserHelper' -Confirm:$false
Unregister-ScheduledTask -TaskName 'ConsoleSystemTray' -Confirm:$false
$c = @'
Start-Sleep 4
Stop-Service ConsoleSystemAgent -Force
Get-Process cs-agent | Stop-Process -Force
Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { $_.CommandLine -like '*ConsoleSystem\agent-user*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
& sc.exe delete ConsoleSystemAgent | Out-Null
Start-Sleep 2
# Xoa khoa rieng cua chung chi agent khoi kho khoa may (neu khong se con sot 1 file trong MachineKeys)
try { $d = Join-Path $env:ProgramData 'ConsoleSystem'; $cf = Get-Content (Join-Path $d 'config.json') -Raw | ConvertFrom-Json; $x = New-Object Security.Cryptography.X509Certificates.X509Certificate2 ((Join-Path $d 'client.pfx'), [string]$cf.pfx_pass, 'MachineKeySet'); $k = $x.PrivateKey; $k.PersistKeyInCsp = $false; $k.Clear() } catch {}
Remove-Item -LiteralPath (Join-Path $env:ProgramFiles 'ConsoleSystem') -Recurse -Force
Remove-Item -LiteralPath (Join-Path $env:ProgramData 'ConsoleSystem') -Recurse -Force
Remove-Item -LiteralPath $PSCommandPath -Force
'@
$f = Join-Path $env:TEMP 'cs-go-agent.ps1'
Set-Content -Path $f -Value $c -Encoding UTF8
Start-Process -FilePath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $f + '"') -WindowStyle Hidden
'ST=DA_LAM Da go agent (dich vu se dung va xoa sau vai giay)'
"""


def ps_cai(url, may_id, cert, ca_pem=None, pk="", urls=None):
    """Script cai agent v2 (chay quyen quan tri tren may Windows). cert = ket qua uem_pki.cap_khach()."""
    if not re.fullmatch(r"https://[0-9A-Za-z.\-]+(:\d+)?", url) or not re.fullmatch(r"[A-Za-z0-9]{1,32}", may_id):
        raise ValueError("tham so khong hop le")
    ca = ca_pem if ca_pem is not None else PKI.ca_pem()
    ca = ca.decode() if isinstance(ca, bytes) else ca
    pfx = base64.b64encode(cert["pfx"]).decode()
    if pk and not re.fullmatch(r"p1:\d{4,7}:[0-9a-f]{32}:[0-9a-f]{64}", pk):
        raise ValueError("passkey khong hop le")
    ds_url = [url] + [u for u in (urls or []) if u != url]
    if len(ds_url) > 5 or any(not re.fullmatch(r"https://[0-9A-Za-z.\-]+(:\d+)?", u) for u in ds_url):
        raise ValueError("danh sach dia chi khong hop le")
    cfg = json.dumps({"url": url, "urls": ds_url, "id": may_id, "pfx_pass": cert["mat_khau"]})
    return (r"""$ErrorActionPreference='Stop'
$prog = Join-Path $env:ProgramFiles 'ConsoleSystem'; $data = Join-Path $env:ProgramData 'ConsoleSystem'
$u8 = New-Object Text.UTF8Encoding($true)
# 1. Don ban cu (tac vu PowerShell v1) va dung dich vu cu neu co
Unregister-ScheduledTask -TaskName 'ConsoleSystemAgent' -Confirm:$false -ErrorAction SilentlyContinue
Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*ConsoleSystem\agent.ps1*' -and $_.ProcessId -ne $PID } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
if (Get-Service ConsoleSystemAgent -ErrorAction SilentlyContinue) { Stop-Service ConsoleSystemAgent -Force -ErrorAction SilentlyContinue; Start-Sleep 2; Get-Process cs-agent -ErrorAction SilentlyContinue | Stop-Process -Force }
New-Item -ItemType Directory -Force -Path $prog, $data, (Join-Path $data 'nd'), (Join-Path $data 'log'), (Join-Path $data 'pub') | Out-Null
# 2. Ma nguon + bien dich ngay tren may nay (csc.exe co san trong .NET Framework 4)
$exe = Join-Path $prog 'cs-agent.exe'
$daCoExe = ($env:CS_EXE_SAN -eq '1') -and (Test-Path -LiteralPath $exe)
if (-not $daCoExe) {
$src = Join-Path $data 'agent.cs'
$cs = @'
""" + CS.nguon() + r"""
'@
[IO.File]::WriteAllText($src, $cs, $u8)
$csc = Join-Path $env:windir ($(if ([Environment]::Is64BitOperatingSystem) { 'Microsoft.NET\Framework64' } else { 'Microsoft.NET\Framework' }) + '\v4.0.30319\csc.exe')
if (-not (Test-Path $csc)) { 'ST=LOI May nay khong co .NET Framework 4 (csc.exe)'; return }
$kq = & $csc /nologo /target:winexe /codepage:65001 /optimize+ ('/out:' + (Join-Path $prog 'cs-agent.exe')) /r:System.ServiceProcess.dll /r:System.Web.Extensions.dll /r:System.Windows.Forms.dll /r:System.Drawing.dll $src 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) { 'ST=LOI Bien dich agent that bai: ' + $kq.Substring(0, [Math]::Min(300, $kq.Length)); return }
}
# 3. Chung chi + cau hinh (chi SYSTEM va Administrators doc duoc)
$ca = @'
""" + ca.strip() + r"""
'@
[IO.File]::WriteAllText((Join-Path $data 'ca.pem'), $ca, $u8)
[IO.File]::WriteAllBytes((Join-Path $data 'client.pfx'), [Convert]::FromBase64String('""" + pfx + r"""'))
[IO.File]::WriteAllText((Join-Path $data 'config.json'), '""" + cfg.replace("'", "''") + r"""', $u8)
& icacls $data /inheritance:r /grant:r 'SYSTEM:(OI)(CI)F' 'Administrators:(OI)(CI)F' | Out-Null
& icacls (Join-Path $data 'nd') /grant 'Users:(OI)(CI)(W)' | Out-Null
& icacls (Join-Path $data 'pub') /grant 'Users:(OI)(CI)(RX)' | Out-Null
# 3b. Passkey (chi luu dau bam PBKDF2) + uninstall.bat (go cai dat bat buoc quyen Administrator va passkey)
$pkv = '""" + pk + r"""'
if ($pkv) { [IO.File]::WriteAllText((Join-Path $data 'passkey.json'), ('{"pk":"' + $pkv + '"}'), $u8) }
$bat = @'
@echo off
net session >nul 2>&1
if errorlevel 1 (
  echo Can chay file nay bang quyen Administrator: chuot phai uninstall.bat, chon Run as administrator.
  pause
  exit /b 1
)
start "" /wait "%~dp0cs-agent.exe" --uninstall
'@
[IO.File]::WriteAllText((Join-Path $prog 'uninstall.bat'), $bat, [Text.Encoding]::ASCII)
& icacls $prog /inheritance:r /grant:r 'SYSTEM:(OI)(CI)F' 'Administrators:(OI)(CI)F' 'Users:(OI)(CI)RX' | Out-Null
# 4. Dich vu Windows
$exe = Join-Path $prog 'cs-agent.exe'
if (-not (Get-Service ConsoleSystemAgent -ErrorAction SilentlyContinue)) { New-Service -Name ConsoleSystemAgent -BinaryPathName ('"' + $exe + '"') -DisplayName 'Console System Agent' -StartupType Automatic | Out-Null }
& sc.exe config ConsoleSystemAgent start= delayed-auto | Out-Null
& sc.exe description ConsoleSystemAgent 'Agent quan ly may tram cua Console System (mTLS).' | Out-Null
& sc.exe failure ConsoleSystemAgent reset= 86400 actions= restart/5000/restart/5000/restart/30000 | Out-Null
# 5. Tro ly phien nguoi dung (chay khi nguoi dung dang nhap, chi ghi file vao thu muc nd)
$t = @'
""" + USER_PS.strip() + r"""
'@
[IO.File]::WriteAllText((Join-Path $data 'agent-user.ps1'), $t, $u8)
& icacls (Join-Path $data 'agent-user.ps1') /grant 'Users:(R)' | Out-Null
$ps = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$ac = New-ScheduledTaskAction -Execute $ps -Argument ('-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + (Join-Path $data 'agent-user.ps1') + '"')
$st = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName 'ConsoleSystemUserHelper' -Action $ac -Trigger (New-ScheduledTaskTrigger -AtLogOn) -Principal (New-ScheduledTaskPrincipal -GroupId 'S-1-5-32-545' -RunLevel Limited) -Settings $st -Force | Out-Null
$act = New-ScheduledTaskAction -Execute $exe -Argument '--tray'
Register-ScheduledTask -TaskName 'ConsoleSystemTray' -Action $act -Trigger (New-ScheduledTaskTrigger -AtLogOn) -Principal (New-ScheduledTaskPrincipal -GroupId 'S-1-5-32-545' -RunLevel Limited) -Settings $st -Force | Out-Null
Start-Service ConsoleSystemAgent
Start-ScheduledTask -TaskName 'ConsoleSystemTray' -ErrorAction SilentlyContinue
'ST=DA_LAM Da cai agent """ + PHIEN_BAN + r""" (dich vu ConsoleSystemAgent, SYSTEM, mTLS)'
""")


# ----------------------------------------------------------------- nhan dien tu chung chi khach (header do nginx 8443 dat)
def _may(mid):
    return DL.tim(DL.MAY.doc(), mid)


def qua_tls_nginx(h, remote):
    """Yeu cau co di qua cong mTLS 8443 (bi mat nginx dung) - dung cho duong tai script cai (chua khoa, khong duoc di cong 80)."""
    if remote not in ("127.0.0.1", "::1"):
        return False
    try:
        bm = PKI.bi_mat_nginx()
    except OSError:
        return False
    return hmac.compare_digest(h.get("X-CS-TLS-Secret", ""), bm)


def nhan_dien(h, remote):
    """Tra ve ban ghi may neu yeu cau mang chung chi khach HOP LE khop serial da cap; khong thi None."""
    if not qua_tls_nginx(h, remote) or h.get("X-CS-Client-Verify") != "SUCCESS":
        return None
    mm = re.search(r"(?:^|[,/])CN=cs-agent-([A-Za-z0-9]+)", h.get("X-CS-Client-DN", ""))
    if not mm:
        return None
    m = _may(mm.group(1))
    a = (m or {}).get("agent") or {}
    gui = h.get("X-CS-Client-Serial", "").lower().lstrip("0")
    if not m or not gui:
        return None
    for khoa in ("serie", "serie_moi"):                    # dang doi chung chi: chap nhan ca cu lan moi cho den khi agent dung chung chi moi
        sr = str(a.get(khoa) or "").lower().lstrip("0")
        if sr and hmac.compare_digest(sr, gui):
            if khoa == "serie_moi":
                _chot_chung_chi_moi(m["id"], sr)
            return m
    return None


def _chot_chung_chi_moi(mid, sr):
    def ghi(ds):
        x = DL.tim(ds, mid)
        a = (x or {}).get("agent") or {}
        if x is not None and str(a.get("serie_moi") or "").lower().lstrip("0") == sr:
            a.update(serie=a["serie_moi"], han=a.get("han_moi", a.get("han")))
            a.pop("serie_moi", None)
            a.pop("han_moi", None)
            a.pop("serie_moi_luc", None)
    DL.MAY.sua(ghi)


def cap_chung_chi(mid):
    """Cap chung chi khach moi cho may (chung chi cu bi thu hoi vi serial doi). Tra ve dict cua uem_pki.cap_khach."""
    c = PKI.cap_khach(mid)

    def ghi(ds):
        m = DL.tim(ds, mid)
        if m is not None:
            m.setdefault("agent", {}).update(serie=c["serial"], han=c["han"], tao_luc=time.time())
    DL.MAY.sua(ghi)
    return c


def cap_lai_chung_chi(mid):
    """Cap chung chi moi va GUI cho agent qua kenh mTLS dang chay (gia han / cap lai). Chung chi cu van dung duoc den khi agent chuyen sang cai moi."""
    c = PKI.cap_khach(mid)

    def ghi(ds):
        m = DL.tim(ds, mid)
        if m is not None:
            m.setdefault("agent", {}).update(serie_moi=c["serial"], han_moi=c["han"], serie_moi_luc=time.time())
    DL.MAY.sua(ghi)
    return them_viec(mid, "doi_chung_chi", pfx=base64.b64encode(c["pfx"]).decode(), pfx_pass=c["mat_khau"], timeout=60)


# ----------------------------------------------------------------- trang thai agent
def luc_cuoi(m):
    return max(((m or {}).get("agent") or {}).get("luc_cuoi", 0), _NHIP.get((m or {}).get("id"), {}).get("luc", 0))


def thong_tin(m):
    a = dict((m or {}).get("agent") or {})
    n = _NHIP.get((m or {}).get("id"))
    if n and n["luc"] >= a.get("luc_cuoi", 0):
        a.update(luc_cuoi=n["luc"], ban=n["ban"], ip_nguon=n["ip"], may=n["may"])
    return a


def co_agent(m):
    return bool(((m or {}).get("agent") or {}).get("serie"))


def con_song(m):
    return co_agent(m) and time.time() - luc_cuoi(m) < SONG_GIAY


def trang_thai(m):
    """('chua_cai'|'online'|'offline', mo_ta)"""
    if not co_agent(m):
        return "chua_cai", "Chưa cài agent"
    if con_song(m):
        return "online", "Đang chạy"
    if not luc_cuoi(m):
        return "offline", "Đã cài nhưng chưa thấy báo nhịp lần nào"
    return "offline", "Mất liên lạc"


def go_token(mid):
    """Thu hoi chung chi cua agent (xoa serial) va huy moi viec dang cho."""
    DL.MAY.sua(lambda ds: [x.pop("agent", None) for x in ds if x["id"] == mid])
    _NHIP.pop(mid, None)
    with _CV:
        for j in list(_HANG.pop(mid, [])):
            _xong(j, "", "Đã gỡ agent khỏi máy.")


def url_may(ip_may):
    pi = DC.ip_pi_toi(ip_may)
    if not pi:
        raise RuntimeError("Không xác định được địa chỉ Console System để agent kết nối về.")
    return f"https://{pi}:{PKI.cong()}"


# ----------------------------------------------------------------- hang doi viec
def _xong(j, out, err):
    j["kq"] = {"out": out, "err": err}
    j["tt"] = "xong"
    j["su_kien"].set()
    _VIEC.pop(j["id"], None)


def them_viec(may_id, kieu="ps", **kw):
    j = {"id": secrets.token_hex(8), "may_id": may_id, "kieu": kieu, "timeout": kw.pop("timeout", 3600), "tt": "cho", "tao": time.time(),
         "su_kien": threading.Event(), "kq": None, "giao": 0}
    j.update(kw)
    with _CV:
        _HANG.setdefault(may_id, deque()).append(j)
        _VIEC[j["id"]] = j
        _CV.notify_all()
    return j


def cho_viec(j, timeout):
    """Cho 1 viec xong. Tra ve (out, err). Raise RuntimeError neu agent mat lien lac / het gio."""
    het = time.time() + timeout + 60
    while time.time() < het:
        if j["su_kien"].wait(3):
            break
        if not con_song(_may(j["may_id"])):
            with _CV:
                try:
                    _HANG.get(j["may_id"], deque()).remove(j)
                except ValueError:
                    pass
                _VIEC.pop(j["id"], None)
            raise RuntimeError("Agent mất liên lạc khi đang chạy việc (máy tắt hoặc mất mạng).")
    if not j["kq"]:
        raise RuntimeError("Hết thời gian chờ agent trả kết quả.")
    return j["kq"]["out"], j["kq"]["err"]


def chay_ps(may_id, script, timeout=3600):
    return cho_viec(them_viec(may_id, "ps", script=script, timeout=timeout), timeout)


class _Luong:
    def __init__(self, loi):
        self.error = [loi] if loi else []


class Client:
    """Giong pypsrp.Client o execute_ps/copy/fetch - de DC._chay_ps, uem_buoc.chay va duyet file dung nguyen xi qua agent."""
    def __init__(self, may_id):
        self.may_id = may_id
        self.loai = "agent"

    def execute_ps(self, script):
        out, err = chay_ps(self.may_id, script)
        return out, _Luong(err), bool(err)

    def fetch(self, src, dest):
        """Tai file tu may ve Console System (dang luong, toi da 2 GB)."""
        j = them_viec(self.may_id, "tep_len", duong=src, dich_local=dest)
        out, err = cho_viec(j, 3600)
        if err or not out.startswith("OK"):
            raise RuntimeError(err or out or "Không tải được file từ máy.")

    def copy(self, src, dest):
        """Day file tu Console System len may (dang luong, toi da 2 GB)."""
        if os.path.getsize(src) > TOI_DA_TEP:
            raise RuntimeError("File lớn hơn 2 GB.")
        j = them_viec(self.may_id, "tep_xuong", duong=dest, nguon_local=src)
        out, err = cho_viec(j, 3600)
        if err or not out.startswith("OK"):
            raise RuntimeError(err or out or "Không đẩy được file lên máy.")


def hoi_phep(may_id, thong_bao, giay=40):
    """Hien hop thoai Co/Khong cho nguoi dang ngoi truoc may. Tra ve 'CHO_PHEP' | 'TU_CHOI' | 'HET_GIO' | 'KHONG_CO_PHIEN'."""
    out, err = cho_viec(them_viec(may_id, "hoi_phep", thong_bao=thong_bao, giay=giay), giay + 20)
    if err:
        raise RuntimeError(err)
    return out.strip()


def mo_tunnel(may_id, tok, cong):
    out, err = cho_viec(them_viec(may_id, "tunnel", tok=tok, cong=cong), 60)
    if err or not out.startswith("OK"):
        raise RuntimeError(err or "Agent không mở được tunnel.")


# ----------------------------------------------------------------- xu ly yeu cau tu agent
def _gui(j):
    return {k: j[k] for k in _GUI if k in j}


def xu_ly_nhip(m, body, ip_nguon):
    from ui import uem_profiles as UP
    now = time.time()
    mid = m["id"]
    ban, host = str(body.get("ver", ""))[:20], str(body.get("host", ""))[:60]
    cu = _NHIP.get(mid)
    doi = m.get("an") or cu is None or cu["ban"] != ban or cu["ip"] != ip_nguon or cu["may"] != host or now - cu["luu_luc"] > 600
    _NHIP[mid] = {"luc": now, "ban": ban, "may": host, "ip": ip_nguon, "luu_luc": now if doi else cu["luu_luc"]}
    if (cu is None or now - cu["luc"] > 120) and not (m.get("ket_noi") or {"ok": True}).get("ok", True):
        try:                                         # may vua noi lai sau khi mat lien lac: lay bao cao ngay, khong cho chu ky 5 phut
            from ui import uem_baocao as UBC
            UBC.chay_nen(mid)
        except Exception as _loi:
            _bo_qua(_loi)
    if doi:                                          # chi ghi dia khi doi thong tin hoac moi 10 phut (may.json lon, khong ghi moi nhip)
        def ghi(ds):
            x = DL.tim(ds, mid)
            if x is None:
                return
            a = x.setdefault("agent", {})
            a.update(luc_cuoi=now, ban=ban, may=host, ip_nguon=ip_nguon)
            x.pop("an", None)                        # may da bi xoa khoi quan ly nay hien lai
            if ip_nguon and x.get("ip") != ip_nguon and a.get("tu_dong_ip", True):
                x["ip"] = ip_nguon                   # may doi IP (DHCP) -> cap nhat de khong mat may
        DL.MAY.sua(ghi)
    ra = {}
    nd = body.get("nd")
    if isinstance(nd, dict):
        nhan_nguoi_dung(m, nd)
    kq = [k for k in (body.get("kq_profile") or []) if isinstance(k, dict)]
    if kq:
        ra["ack_pf"] = UP.nhan_ket_qua_agent(m, kq)
    dang = {str(i) for i in (body.get("dang") or []) if isinstance(i, str)}
    with _CV:
        # viec da giao ma agent khong con giu (khoi dong lai giua luot) -> bao loi, khong de ben goi treo
        for j in [j for j in list(_VIEC.values()) if j["may_id"] == mid and j["tt"] == "giao" and now - j["giao"] > 20 and j["id"] not in dang and j["kieu"] in ("ps", "tep_len", "tep_xuong", "hoi_phep")]:
            _xong(j, "", "Agent khởi động lại giữa chừng, việc bị hủy.")
        if ban != PHIEN_BAN:
            ra["capnhat"] = {"ban": PHIEN_BAN, "cs": CS.nguon()}
            return ra
        a = (_may(mid) or {}).get("agent") or {}
        if a.get("han") and a["han"] - now < GIA_HAN_TRUOC_GIAY and now - a.get("serie_moi_luc", 0) > 86400:
            cap_lai_chung_chi(mid)                       # gia han chung chi tu dong
        han = now + NHIP_GIAY
        while True:
            q = _HANG.get(mid)
            if q:
                j = q.popleft()
                j["tt"], j["giao"] = "giao", time.time()
                ra["viec"] = _gui(j)
                return ra
            viec = UP.viec_dong_bo(m, body.get("pf") if isinstance(body.get("pf"), dict) else {})   # profile tu tri: gui bundle thieu/cu, go bundle thua
            if viec:
                ra["viec"] = viec
                return ra
            if ra.get("ack_pf"):
                return ra
            con = han - time.time()
            if con <= 0:
                return ra
            _CV.wait(min(con, 5))


def nhan_ket_qua(m, body):
    j = _VIEC.get(str(body.get("id", "")))
    if j and j["may_id"] == m["id"]:
        with _CV:
            _xong(j, str(body.get("out", ""))[:4 * 1024 * 1024], str(body.get("err", ""))[:4000])
        return True
    return False


def _chuoi(x, n=200):
    return str(x if x is not None else "")[:n]


def nhan_nguoi_dung(m, body):
    """Du lieu tro ly phien nguoi dung: CHUAN HOA ve dung kieu/khoa (khong tin dinh dang agent gui) de giao dien khong bao gio vo."""
    may_in = [{"name": _chuoi(p.get("name")), "port": _chuoi(p.get("port")), "is_default": bool(p.get("is_default")), "is_network": bool(p.get("is_network")),
               "is_shared": bool(p.get("is_shared"))} for p in (body.get("printers") or []) if isinstance(p, dict) and p.get("name")][:100]
    man = [{"manufacturer": _chuoi(x.get("manufacturer"), 60), "model": _chuoi(x.get("model"), 80), "serial": _chuoi(x.get("serial"), 60),
            "week_of_manufacture": _chuoi(x.get("week_of_manufacture"), 6), "year_of_manufacture": _chuoi(x.get("year_of_manufacture"), 6)}
           for x in (body.get("monitors") or []) if isinstance(x, dict)][:16]
    UD.sua_may(m["id"], phien_nd={"user": _chuoi(body.get("user"), 120), "printers": may_in, "monitors": man, "luc": time.time()})


def viec_tep(job_id, m):
    """Viec chuyen file (tep_len/tep_xuong) dang cho cua dung may nay, hoac None."""
    j = _VIEC.get(job_id)
    if j and j["may_id"] == m["id"] and j["kieu"] in ("tep_len", "tep_xuong"):
        return j
    return None


# ----------------------------------------------------------------- cai / go
def tao_ma_cai(mid):
    ma = secrets.token_urlsafe(24)
    with _CV:
        for k in [k for k, v in _MA_CAI.items() if v["het_han"] < time.time()]:
            _MA_CAI.pop(k, None)
        _MA_CAI[ma] = {"may_id": mid, "het_han": time.time() + 1800}
    return ma


def bam_passkey(pw):
    """Dau bam PBKDF2-HMAC-SHA1 (tuong thich .NET Framework 4: Rfc2898DeriveBytes) cua passkey: p1:so-vong:muoi-hex:bam-hex. Khong luu passkey goc."""
    import hashlib
    if not (4 <= len(pw) <= 64) or "\"" in pw:
        raise ValueError("Passkey dài 4 đến 64 ký tự và không chứa dấu nháy kép.")
    muoi = os.urandom(16)
    return "p1:100000:" + muoi.hex() + ":" + hashlib.pbkdf2_hmac("sha1", pw.encode("utf-8"), muoi, 100000, 32).hex()


def kiem_passkey(pw, bam):
    """Dung/sai: so khop passkey goc voi dau bam 'p1:so-vong:muoi-hex:bam-hex' (hang so thoi gian)."""
    import hashlib
    import hmac
    try:
        t, vong, muoi, h = (bam or "").split(":")
        if t != "p1":
            return False
        tinh = hashlib.pbkdf2_hmac("sha1", (pw or "").encode("utf-8"), bytes.fromhex(muoi), int(vong), len(bytes.fromhex(h)))
        return hmac.compare_digest(tinh.hex(), h)
    except (ValueError, TypeError):
        return False


def pk_cua_ma(ma_id):
    """Dau bam passkey cua 1 ma ghi danh ('' neu khong co)."""
    with _CV:
        return next((x.get("pk", "") for x in _gd_doc() if x["id"] == ma_id), "")


# ----------------------------------------------------------------- ma ghi danh (dung nhieu lan: MSI / trien khai hang loat)
_GD_FILE = "ghi-danh.json"
VINH_VIEN = 253402300799.0          # 31/12/9999: ma ghi danh khong het han (ngay = 0)


def _gd_doc():
    try:
        with open(PKI._p(_GD_FILE), encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else []
    except (OSError, ValueError):
        return []


def _gd_ghi(ds):
    PKI._ghi(PKI._p(_GD_FILE), json.dumps(ds, ensure_ascii=False).encode("utf-8"))


def ds_ghi_danh():
    with _CV:
        now = time.time()
        return [x for x in _gd_doc() if x["het_han"] > now]


def tao_ghi_danh(ten, url, ngay, toi_da, pk="", urls=None):
    ds_url = [url] + [u for u in (urls or []) if u != url]
    if len(ds_url) > 5 or any(not re.fullmatch(r"https://[0-9A-Za-z.\-]+:\d{1,5}", u or "") for u in ds_url):
        raise ValueError("Địa chỉ Console System không hợp lệ (ví dụ 192.168.1.10:8443 hoặc console.congty.vn:8443; tối đa 5 địa chỉ).")
    ngay = max(0, min(int(ngay), 3650))                                   # 0 = suot doi (khong het han)
    toi_da = max(0, min(int(toi_da), 100000))
    e = {"id": secrets.token_hex(4), "ten": (ten or "").strip()[:60] or "Mã ghi danh", "ma": secrets.token_urlsafe(24), "url": url,
         "tao_luc": time.time(), "het_han": time.time() + ngay * 86400 if ngay else VINH_VIEN, "toi_da": toi_da, "da_dung": 0, "pk": pk, "urls": ds_url}
    with _CV:
        ds = [x for x in _gd_doc() if x["het_han"] > time.time()]
        if len(ds) >= 50:
            raise ValueError("Có quá nhiều mã ghi danh đang dùng (tối đa 50), hãy xoá bớt.")
        ds.append(e)
        _gd_ghi(ds)
    return e


def xoa_ghi_danh(gid):
    with _CV:
        _gd_ghi([x for x in _gd_doc() if x["id"] != gid])


def _dung_ghi_danh(ma):
    """Kiem tra va tinh 1 luot dung; tra ve ban ghi hoac None."""
    with _CV:
        ds = _gd_doc()
        for x in ds:
            if hmac.compare_digest(x["ma"], ma):
                if x["het_han"] < time.time() or (x["toi_da"] and x["da_dung"] >= x["toi_da"]):
                    return None
                x["da_dung"] += 1
                _gd_ghi(ds)
                return x
    return None


def _may_ghi_danh(host, ip, ten_ma):
    """Tim hoac tao ban ghi may cho may vua ghi danh (khop ten may + IP nguon; roi toi may co san chua co agent cung IP/ten; khong thi tao moi)."""
    host = re.sub(r"[^A-Za-z0-9._-]", "", host or "")[:63]
    kq = []

    def ghi(ds):
        for x in ds:
            if host and x.get("ten") == host and x.get("ip") == ip:
                kq.append(x["id"])
                return
        # May da co trong danh sach (them tay / quet mang / Trien khai phan mem) nhung chua co agent: gan agent vao DUNG ban ghi do
        # (cung IP nguon), khong tao ban ghi thu hai. May doi IP (DHCP) thi khop theo ten may.
        for x in ds:
            if not co_agent(x) and ((x.get("ip") == ip) or (host and x.get("ten") == host)):
                x["ip"] = ip
                x["ghi_chu_agent"] = "Ghi danh bằng mã: " + ten_ma
                kq.append(x["id"])
                return
        mid = DL.moi_id()
        ds.append({"id": mid, "ten": host, "ip": ip, "mac": "", "tai_khoan_id": None, "giam_sat": True, "ghi_chu_agent": "Ghi danh bằng mã: " + ten_ma})
        kq.append(mid)
    DL.MAY.sua(ghi)
    return kq[0]


def doi_ma_cai(ma, ip_nguon, host=""):
    """Dung 1 lan (hoac ma ghi danh nhieu lan): cap chung chi moi va tra ve script cai, hoac None."""
    with _CV:
        v = _MA_CAI.pop(ma, None)
    if v:
        if v["het_han"] < time.time():
            return None
        m = _may(v["may_id"])
        if not m:
            return None
        c = cap_chung_chi(m["id"])
        return ps_cai(url_may(ip_nguon or m["ip"]), m["id"], c)
    gd = _dung_ghi_danh(ma)
    if not gd or not ip_nguon:
        return None
    mid = _may_ghi_danh(host, ip_nguon, gd["ten"])
    c = cap_chung_chi(mid)
    return ps_cai(gd["url"], mid, c, pk=gd.get("pk", ""), urls=gd.get("urls"))


def cai_qua_winrm(mid):
    """Day agent len may qua WinRM. (ok, thong_diep)"""
    from ui import uem_ketnoi as UK
    if not PKI.san_sang():
        return False, "Chưa bật cổng mTLS 8443 của Console System (bấm 'Bật kết nối an toàn' ở Quản trị, Agent)."
    try:
        m = _may(mid)
        if not m:
            return False, "Không tìm thấy máy."
        c, mk, loai = UK.ket_noi(m, bat_buoc_winrm=True)
        cc = cap_chung_chi(mid)
        out, err = DC._chay_ps(c, ps_cai(url_may(m["ip"]), mid, cc))
        if "ST=DA_LAM" not in out:
            go_token(mid)
            return False, ("Cài agent không thành công. " + (err or out.strip())[:300]).strip()
        for _ in range(40):                           # cho agent bao nhip dau tien
            time.sleep(1)
            if con_song(_may(mid)):
                return True, "Đã cài agent (dịch vụ Windows, mTLS) và agent đã báo nhịp."
        return True, "Đã cài agent nhưng chưa thấy báo nhịp (máy không tới được cổng 8443 của Console System? tường lửa chặn?). Xem nhật ký C:\\ProgramData\\ConsoleSystem\\log\\agent.log trên máy."
    except UK.LoiMay as e:
        return False, str(e)
    except Exception as e:
        go_token(mid)
        return False, DC._loi_dep(e)


def go_agent(mid):
    from ui import uem_ketnoi as UK
    try:
        m = _may(mid)
        c, mk, loai = UK.ket_noi(m)
        try:
            DC._chay_ps(c, PS_GO)
        except RuntimeError:
            pass
        go_token(mid)
        return True, "Đã gỡ agent."
    except UK.LoiMay as e:
        go_token(mid)               # may khong lien lac duoc: van thu hoi chung chi de agent (neu con) bi tu choi
        return True, "Đã thu hồi chứng chỉ (máy không liên lạc được nên chưa xóa file trên máy): " + str(e)
    except Exception as e:
        return False, DC._loi_dep(e)


def danh_sach_trang_thai():
    ra = []
    for m in DL.MAY.doc():
        tt, mt = trang_thai(m)
        ra.append((m, tt, mt))
    return ra
