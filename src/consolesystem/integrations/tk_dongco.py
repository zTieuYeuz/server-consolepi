# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Trien khai phan mem - DONG CO CHAY (WinRM) + BO LAP LICH.

Moi "kich ban" = danh sach BUOC (cai phan mem, ung dung nhieu file, script, WinGet, bat/tat/khoi dong lai, kiem tra
bao mat) chay tuan tu tren tung MAY (tu nhom may / may le), theo LICH hoac chay ngay. Bam "Chay" la KICH HOAT: kich ban
duoc ghi nho va tu chay lai theo lich cho den khi bam "Dung" (ke ca khi dich vu khoi dong lai - trang thai luu o dia).
Moi may thu toi da 3 lan, cach nhau 5 phut (may tat/mat mang hoac buoc cai bi loi); qua 3 lan thi may do la 'Khong thanh cong'.

KENH: WinRM (PowerShell Remoting, Microsoft ho tro chinh thuc) bang thu vien pypsrp trong venv rieng
(/opt/console-pi-venv/winrm, xem tools/cai-winrm.sh). File lon (Office...) KHONG day qua WinRM (rat cham): may dich
tu TAI tu Console System qua duong dan 1 lan (token ngau nhien, het han sau 2 gio, chi cho may trong mang noi bo).

MAT KHAU: lay tu kho tai khoan ma hoa (tk_dulieu), chi nam trong RAM luc dang chay, khong ghi log.
"""
from consolesystem.core.nhatky import bo_qua as _bo_qua
import sys as _sys
from consolesystem.core.token_tai import _TOKEN, tao_token, tra_token  # noqa: F401  (B3)
_sys.modules["ui.tk_dongco"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import glob
import json
import os
import re
import shutil
import socket
import sys
import threading
import time
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from ui import tk_dulieu as DL
from consolesystem.core import duongdan as _DD
from consolesystem.core import magic_packet as _MP
from consolesystem.integrations import rustdesk_may_chu as RD

TOI_DA_SONG_SONG = 10
CONG_TAI = int(os.environ.get("TK_CONG_TAI", "80"))      # cong Console System phuc vu file (nginx 80)
THU_LAI_MAY_TAT = 300                                     # may tat / mat mang: thu lai moi 5 phut
THU_LAI_LOI_BUOC = 300                                    # buoc cai loi: thu lai sau 5 phut (toi da 3 lan)
TOI_DA_THU = 3
CUA_SO_BU = 6 * 3600                                      # bo lo gio hen toi da 6 gio van chay bu
_EX = ThreadPoolExecutor(max_workers=TOI_DA_SONG_SONG)
_KHOA = threading.RLock()
_DANG = set()                                             # (kb_id, ip) dang chay
_ZIP = {}                                                 # ung dung -> (chu ky, duong zip)
_BO_LAP_DA_CHAY = False


# ----------------------------------------------------------------- pypsrp (venv rieng)
def them_venv_vao_path():
    for g in glob.glob("/opt/console-pi-venv/winrm/lib/python3.*/site-packages"):
        if g not in sys.path:
            sys.path.insert(0, g)
    try:
        import pypsrp  # noqa: F401
        return True
    except ImportError:
        return False


def co_san():
    return them_venv_vao_path()


# ----------------------------------------------------------------- phuc vu file cho may dich (token 1 lan)
def ip_pi_toi(ip_may):
    """Dia chi cua Console System nhin tu may dich (card nao di toi may do)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((ip_may, 9))
        return s.getsockname()[0]
    except OSError:
        return ""
    finally:
        s.close()






def _noi_bo(addr):
    import ipaddress
    try:
        a = ipaddress.ip_address(addr)
        return a.is_private or a.is_loopback
    except ValueError:
        return False


def url_tai(ip_may, duong):
    pi = ip_pi_toi(ip_may)
    if not pi:
        raise RuntimeError("Không xác định được địa chỉ Console System để máy đích tải file.")
    tok = tao_token(duong)
    cong = "" if CONG_TAI == 80 else f":{CONG_TAI}"
    return f"http://{pi}{cong}/tk/tai/{tok}/{os.path.basename(duong)}"


# ----------------------------------------------------------------- may dich
class LoiKetNoi(Exception):
    """Khong vao duoc may (tat, mat mang, WinRM chua bat, sai tai khoan) - se thu lai ve sau."""


def _ket_noi(ip, user, mat_khau):
    if not them_venv_vao_path():
        raise LoiKetNoi("Chưa cài thư viện WinRM (chạy: sudo bash /opt/console-pi/tools/cai-winrm.sh).")
    from pypsrp.client import Client
    return Client(ip, username=user, password=mat_khau, ssl=False, auth="ntlm",
                  cert_validation=False, connection_timeout=12, read_timeout_sec=3600)


def _q(x):
    return "'" + str(x).replace("'", "''") + "'"


def _loi_dep(e, mat_khau=""):
    th = str(e)
    if mat_khau and mat_khau in th:
        th = th.replace(mat_khau, "***")
    tl = th.lower()
    if "401" in tl or "access is denied" in tl or "credentials were rejected" in tl or "failed to authenticate" in tl or "authentication" in tl:
        return "Sai tài khoản/mật khẩu hoặc tài khoản không phải quản trị viên trên máy đó."
    if any(k in tl for k in ("actively refused", "connection refused", "timed out", "max retries", "failed to establish",
                             "no route to host", "winrmtransport", "name or service not known", "unreachable")):
        return "Không kết nối được WinRM: máy đang tắt, mất mạng, chưa bật WinRM hoặc tường lửa chặn cổng 5985."
    return th[:300]


def _chay_ps(c, script):
    out, streams, loi = c.execute_ps(script)
    err = "; ".join(str(e) for e in streams.error)[:500] if loi else ""
    return out or "", err


def _tai_ve_may(c, ip, duong_local, dich):
    """May dich tu tai file ve `dich`. File nho (<30 MB) ma tai loi thi day thang qua WinRM."""
    if getattr(c, "loai", "") == "agent":      # agent: day thang qua kenh agent (may co the khong toi duoc Console System bang HTTP)
        _chay_ps(c, f"New-Item -ItemType Directory -Force (Split-Path {_q(dich)}) | Out-Null")
        c.copy(duong_local, dich)
        return
    try:
        url = url_tai(ip, duong_local)
        out, err = _chay_ps(c, "$ProgressPreference='SilentlyContinue'; "
                               f"New-Item -ItemType Directory -Force (Split-Path {_q(dich)}) | Out-Null; "
                               f"Invoke-WebRequest -UseBasicParsing -Uri {_q(url)} -OutFile {_q(dich)}; "
                               f"if (Test-Path {_q(dich)}) {{ 'TAI_OK' }}")
        if "TAI_OK" in out:
            return
    except LoiKetNoi:
        raise
    except Exception as _loi:
        _bo_qua(_loi)
    if os.path.getsize(duong_local) < 30 * 1024 * 1024:
        _chay_ps(c, f"New-Item -ItemType Directory -Force (Split-Path {_q(dich)}) | Out-Null")
        c.copy(duong_local, dich)
        return
    raise RuntimeError("Máy đích không tải được file từ Console System (tường lửa chặn?) và file quá lớn để đẩy qua WinRM.")


def _chay_tien_trinh(c, tep, doi_so, don=""):
    """Chay 1 file/lenh va cho xong, tra ve (ma_thoat, loi_ps)."""
    tham = f" -ArgumentList {_q(doi_so)}" if (doi_so or "").strip() else ""
    out, err = _chay_ps(c, f"$p = Start-Process -FilePath {_q(tep)}{tham} -Wait -PassThru -WindowStyle Hidden; "
                           + (f"Remove-Item -Recurse -Force {_q(don)} -ErrorAction SilentlyContinue; " if don else "")
                           + '"MA_THOAT=$($p.ExitCode)"')
    m = re.search(r"MA_THOAT=(-?\d+)", out)
    return (int(m.group(1)) if m else None), err


def _ket_qua_ma(ma, err, ten):
    if err and ma is None:
        return False, f"{ten}: {err}"
    if ma in (0, 3010, 1641):
        return True, f"{ten}: xong (mã thoát {ma})" + (", cần khởi động lại máy" if ma in (3010, 1641) else "")
    return False, f"{ten}: mã thoát {ma if ma is not None else '?'} {err}".strip()


def _dir_tep(ten):
    return "C:\\Windows\\Temp\\cs-tk-" + uuid.uuid4().hex[:8]


# ----------------------------------------------------------------- tung loai buoc
def _b_phanmem(c, ip, b, may):
    from ui import deployos as D
    ten = os.path.basename(b["ref"])
    duong = os.path.join(_DD.APPS_DIR, ten)
    if not os.path.isfile(duong):
        return False, f"Không còn file phần mềm {ten} trong Tài nguyên máy."
    meta = D.doc_thongtin_app()
    if RD.la_bo_cai_rustdesk(ten) and not (meta.get(ten) or "").strip():
        # Bo cai RustDesk trong Tai nguyen: cai bang chinh file nay (kiem SHA-256) va dien san May chu ID / chuyen tiep / Key cua Console System
        return _b_rustdesk(c, ip, b, may, url=url_tai(ip, duong), sha=RD.sha256_tep(duong))
    doi = (meta.get(ten) or "").strip() or D.tham_so_mac_dinh_app(ten)
    doi_msi = doi or "/qn /norestart"
    if ten.lower().endswith(".msi"):
        # MSI agent tao o Quan ly may tram co passkey: tu dien PASSKEY neu da luu; neu chua thi bao ro thay vi loi 1603 kho hieu
        from ui import uem_agent_goi as UG
        g = UG.tim_theo_file(duong)
        if g and g.get("co_passkey") and "passkey=" not in doi_msi.lower():
            pk = UG.passkey_trien_khai(g)
            if not pk:
                return False, (f"{ten} là gói agent có passkey nhưng Console System chưa lưu passkey này cho Triển khai phần mềm. "
                               "Vào Quản lý máy trạm, Quản trị, Agent, bấm \"Lưu passkey cho triển khai\" ở gói này rồi chạy lại.")
            doi_msi += f' PASSKEY="{pk}"'
    d = _dir_tep(ten)
    dich = d + "\\" + ten
    _tai_ve_may(c, ip, duong, dich)
    if ten.lower().endswith(".msi"):
        ma, err = _chay_tien_trinh(c, "msiexec.exe", f'/i "{dich}" {doi_msi}', d)
    else:
        ma, err = _chay_tien_trinh(c, dich, doi, d)
    ok, tb = _ket_qua_ma(ma, err, ten)
    if ok and ten == RD.TEN_MSI:                # goi RustDesk cua trang RustDesk: ghi ID de tab Ho tro tu xa ket noi duoc
        out, _e = _chay_ps(c, "& (Join-Path $env:ProgramFiles 'RustDesk\\rustdesk.exe') --get-id | Out-String")
        ma_id = re.search(r"\b(\d{6,12})\b", out or "")
        if ma_id:
            RD.ghi_may(may.get("id", ""), ma_id.group(1))
            tb += f", ID RustDesk {ma_id.group(1)}"
    return ok, tb


def danh_sach_kho():
    """Phan mem (.exe/.msi) trong Tai nguyen may, kem tham so cai im lang."""
    from ui import deployos as D
    return [{"ten": a["ten"], "tham_so": (a.get("tham_so") or D.tham_so_mac_dinh_app(a["ten"]) or "")} for a in D.danh_sach_app()]


def cai_tu_kho(c, ip, ten, may):
    """Cai 1 phan mem trong kho len may (c: client WinRM hoac agent). (ok, thong bao)"""
    return _b_phanmem(c, ip, {"ref": ten}, may)


def _chu_ky_thu_muc(p):
    tong, moi = 0, 0
    for goc, _d, fs in os.walk(p):
        for f in fs:
            try:
                st = os.stat(os.path.join(goc, f))
                tong += st.st_size
                moi = max(moi, int(st.st_mtime))
            except OSError:
                pass
    return f"{tong}-{moi}"


def _zip_ungdung(ung_id, thu_muc):
    with _KHOA:
        cs = _chu_ky_thu_muc(thu_muc)
        c = _ZIP.get(ung_id)
        if c and c[0] == cs and os.path.isfile(c[1]):
            return c[1]
        os.makedirs(os.path.join(DL.DIR, "cache"), exist_ok=True)
        duong = os.path.join(DL.DIR, "cache", f"{ung_id}.zip")
        with zipfile.ZipFile(duong, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
            for goc, _d, fs in os.walk(thu_muc):
                for f in fs:
                    if goc == thu_muc and f == "_thongtin.json":
                        continue
                    p = os.path.join(goc, f)
                    z.write(p, os.path.relpath(p, thu_muc))
        _ZIP[ung_id] = (cs, duong)
        return duong


def _b_ungdung(c, ip, b, may):
    from ui import deployos as D
    u = D.lay_ungdung(b["ref"])
    if not u:
        return False, f"Không còn ứng dụng '{b.get('ten') or b['ref']}' trong Tài nguyên máy."
    if not (u.get("lenh_cai") or "").strip():
        return False, "Ứng dụng chưa có dòng lệnh cài đặt (điền  ở Tài nguyên máy, Ứng dụng nhiều file)."
    z = _zip_ungdung(u["id"], os.path.join(_DD.UNGDUNG_DIR, u["id"]))
    d = _dir_tep(u["id"])
    _tai_ve_may(c, ip, z, d + "\\ungdung.zip")
    _chay_ps(c, f"Expand-Archive -Force -Path {_q(d + chr(92) + 'ungdung.zip')} -DestinationPath {_q(d + chr(92) + 'src')}; "
                f"Remove-Item -Force {_q(d + chr(92) + 'ungdung.zip')}")
    lenh = u["lenh_cai"].strip()
    ma, err = _chay_tien_trinh(c, "cmd.exe", f'/c cd /d "{d}\\src" && {lenh}', d)
    return _ket_qua_ma(ma, err, u.get("ten_hien_thi") or u["id"])


def _b_script(c, ip, b, may):
    from ui import deployos as D
    ten = os.path.basename(b["ref"])
    duong = os.path.join(_DD.SCRIPTS_DIR, ten)
    if not os.path.isfile(duong):
        return False, f"Không còn script {ten} trong Tài nguyên máy."
    if ten.lower().endswith(".ps1"):
        with open(duong, encoding="utf-8-sig", errors="replace") as f:
            out, err = _chay_ps(c, f.read())
        if err:
            return False, f"{ten}: lỗi: {err}"
        ma = re.search(r"RUSTDESK_ID=(\d{6,12})", out)
        if ma:                                  # file cai RustDesk (trang RustDesk luu vao kho): ghi ID de tab Ho tro tu xa ket noi duoc
            RD.ghi_may(may.get("id", ""), ma.group(1))
            return True, f"{ten}: chạy xong, ID RustDesk {ma.group(1)}."
        return True, f"{ten}: chạy xong. {out.strip()[:300]}".strip()
    d = _dir_tep(ten)
    dich = d + "\\" + ten
    _tai_ve_may(c, ip, duong, dich)
    ma, err = _chay_tien_trinh(c, "cmd.exe", f'/c "{dich}"', d)
    return _ket_qua_ma(ma, err, ten)


def _b_winget(c, ip, b, may):
    id_ = (b.get("ref") or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9._+-]{2,100}", id_):
        return False, f"Mã WinGet không hợp lệ: {id_}"
    out, err = _chay_ps(c, (
        "$ProgressPreference='SilentlyContinue'; "
        "$w = Get-ChildItem \"$env:ProgramFiles\\WindowsApps\\Microsoft.DesktopAppInstaller_*__8wekyb3d8bbwe\\winget.exe\" "
        "-ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1 -ExpandProperty FullName; "
        "if (-not $w) { $g = Get-Command winget -ErrorAction SilentlyContinue; if ($g) { $w = $g.Source } }; "
        "if (-not $w) { 'KHONG_CO_WINGET'; return }; "
        f"$o = & $w install --id {id_} -e --scope machine --silent --accept-package-agreements --accept-source-agreements "
        "--disable-interactivity 2>&1 | Out-String; $o.Substring([Math]::Max(0,$o.Length-600)); \"MA_THOAT=$LASTEXITCODE\""))
    if "KHONG_CO_WINGET" in out:
        return False, "Máy này chưa có WinGet (App Installer). Windows 11 và Windows 10 bản mới thường có sẵn."
    m = re.search(r"MA_THOAT=(-?\d+)", out)
    ma = int(m.group(1)) if m else None
    if ma == 0:
        return True, f"WinGet {id_}: cài xong."
    if ma in (-1978335189, 2316632107):
        return True, f"WinGet {id_}: máy đã có bản mới nhất."
    return False, f"WinGet {id_}: mã thoát {ma}. " + re.sub(r"\s+", " ", out)[-250:]


def _b_rustdesk(c, ip, b, may, url=None, sha=None):
    def chay(sc):
        out, err = _chay_ps(c, sc)
        return not err or "RUSTDESK_ID=" in out, (out + " " + err).strip()
    ok, tb, _id = RD.cai_va_ghi(chay, may.get("id", ""), url=url, sha=sha)
    return ok, tb


def _b_nguon(c, ip, b, may):
    hd = b.get("ref")
    if hd == "tat":
        c.execute_cmd('shutdown /s /t 10 /f /c "Console System: tắt máy theo kịch bản"')
        return True, "Đã gửi lệnh tắt máy (sau 10 giây)."
    if hd == "khoi_dong_lai":
        c.execute_cmd('shutdown /r /t 10 /f /c "Console System: khởi động lại theo kịch bản"')
        return True, "Đã gửi lệnh khởi động lại (sau 10 giây)."
    return False, "Hành động nguồn không hợp lệ."


SCRIPT_BAO_MAT = r"""
$ErrorActionPreference='SilentlyContinue'
$r=[ordered]@{}
$os=Get-CimInstance Win32_OperatingSystem
$r.os=$os.Caption; $r.build=$os.BuildNumber; $r.khoi_dong=$os.LastBootUpTime.ToString('s')
$r.ten_may=$env:COMPUTERNAME
$mp=Get-MpComputerStatus
if($mp){$r.av=[ordered]@{ten="Windows Defender";bat=[bool]$mp.AntivirusEnabled; realtime=[bool]$mp.RealTimeProtectionEnabled; mau_tuoi_ngay=[int]$mp.AntivirusSignatureAge}}
else{$sc=Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | Select-Object -First 1
  if($sc){$on=(($sc.productState -band 0xF000) -eq 0x1000);$r.av=[ordered]@{ten=[string]$sc.displayName;bat=$on;realtime=$on;mau_tuoi_ngay=$null}}else{$r.av=$null}}
$bl=Get-BitLockerVolume
if($bl){$r.bitlocker=@($bl|ForEach-Object{[ordered]@{o=[string]$_.MountPoint;bao_ve=[string]$_.ProtectionStatus;phan_tram=[int]$_.EncryptionPercentage}})}else{$r.bitlocker=$null}
$r.tuong_lua=@(Get-NetFirewallProfile|ForEach-Object{[ordered]@{ten=[string]$_.Name;bat=[bool]$_.Enabled}})
try{$s=New-Object -ComObject Microsoft.Update.Session;$k=$s.CreateUpdateSearcher().Search("IsInstalled=0 and IsHidden=0");$r.cap_nhat_cho=[int]$k.Updates.Count}catch{$r.cap_nhat_cho=$null}
$d=Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3"
$r.o_dia=@($d|ForEach-Object{[ordered]@{o=[string]$_.DeviceID;tong_gb=[math]::Round($_.Size/1GB,1);trong_gb=[math]::Round($_.FreeSpace/1GB,1)}})
"BAOMAT_JSON=" + ($r | ConvertTo-Json -Depth 5 -Compress)
"""


def _b_baomat(c, ip, b, may):
    out, err = _chay_ps(c, SCRIPT_BAO_MAT)
    m = re.search(r"BAOMAT_JSON=(\{.*\})", out)
    if not m:
        return False, f"Không đọc được thông tin bảo mật. {err}"
    try:
        d = json.loads(m.group(1))
    except ValueError:
        return False, "Thông tin bảo mật trả về không đọc được."
    d["luc"] = time.time()

    def luu(ds):
        for x in ds:
            if x.get("ip") == ip:
                x["bao_mat"] = d
    DL.MAY.sua(luu)
    return True, tom_tat_bao_mat(d)


def tom_tat_bao_mat(d):
    p = []
    av = d.get("av")
    p.append("Diệt virus: " + ("không đọc được" if av is None else ("bật" if av.get("bat") and av.get("realtime") else "TẮT/không bảo vệ thời gian thực")))
    if d.get("cap_nhat_cho") is not None:
        p.append(f"{d['cap_nhat_cho']} bản cập nhật đang chờ")
    tl = d.get("tuong_lua") or []
    if tl:
        p.append("tường lửa " + ("bật" if all(x.get("bat") for x in tl) else "có profile TẮT"))
    return "; ".join(p)


SCRIPT_KIEM_KE = r"""
$ErrorActionPreference='SilentlyContinue'
$r=[ordered]@{}
$cs=Get-CimInstance Win32_ComputerSystem; $bios=Get-CimInstance Win32_BIOS; $os=Get-CimInstance Win32_OperatingSystem
$r.ten_may=$env:COMPUTERNAME; $r.hang=[string]$cs.Manufacturer; $r.model=[string]$cs.Model; $r.serial=[string]$bios.SerialNumber
$r.cpu=[string](Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)
$r.ram_gb=[math]::Round($cs.TotalPhysicalMemory/1GB,1); $r.os=[string]$os.Caption; $r.build=[string]$os.BuildNumber
$r.ip=@(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*'} | ForEach-Object {[string]$_.IPAddress})
$r.o_dia=@(Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {[ordered]@{o=[string]$_.DeviceID;tong_gb=[math]::Round($_.Size/1GB,1);trong_gb=[math]::Round($_.FreeSpace/1GB,1)}})
$k=@('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*')
$a=@{}
foreach($p in $k){Get-ItemProperty $p | Where-Object {$_.DisplayName -and -not $_.SystemComponent} | ForEach-Object {$a[[string]$_.DisplayName]=[ordered]@{ten=[string]$_.DisplayName;pb=[string]$_.DisplayVersion;nsx=[string]$_.Publisher}}}
$r.phan_mem=@($a.Values | Sort-Object {$_.ten} | Select-Object -First 800)
"KIEMKE_JSON=" + ($r | ConvertTo-Json -Depth 5 -Compress)
"""


def _b_kiemke(c, ip, b, may):
    out, err = _chay_ps(c, SCRIPT_KIEM_KE)
    m = re.search(r"KIEMKE_JSON=(\{.*\})", out, re.S)
    if not m:
        return False, f"Không đọc được thông tin kiểm kê. {err}"
    try:
        d = json.loads(m.group(1))
    except ValueError:
        return False, "Thông tin kiểm kê trả về không đọc được."
    d["luc"] = time.time()

    def luu(ds):
        for x in ds:
            if x.get("ip") == ip:
                x["kiem_ke"] = d
    DL.MAY.sua(luu)
    return True, f"{d.get('hang', '')} {d.get('model', '')}, RAM {d.get('ram_gb')} GB, {len(d.get('phan_mem', []))} phần mềm."


_BUOC = {"kiemke": _b_kiemke, "phanmem": _b_phanmem, "ungdung": _b_ungdung, "script": _b_script, "winget": _b_winget,
         "nguon": _b_nguon, "baomat": _b_baomat, "rustdesk": _b_rustdesk}
TEN_LOAI_BUOC = {"phanmem": "Phần mềm", "ungdung": "Ứng dụng nhiều file", "script": "Script", "winget": "WinGet", "rustdesk": "RustDesk",
                 "nguon": "Nguồn điện", "baomat": "Kiểm tra bảo mật", "kiemke": "Kiểm kê máy", "nhom": "Nhóm tài nguyên"}
TEN_NGUON = {"bat": "Bật máy (Wake-on-LAN)", "tat": "Tắt máy", "khoi_dong_lai": "Khởi động lại"}


def nhan_buoc(b):
    if b["loai"] == "nguon":
        return TEN_NGUON.get(b.get("ref"), "Nguồn điện")
    if b["loai"] == "baomat":
        return "Kiểm tra bảo mật"
    if b["loai"] == "kiemke":
        return "Kiểm kê phần cứng và phần mềm"
    if b["loai"] == "rustdesk":
        return "Cài RustDesk (kèm máy chủ ID / chuyển tiếp)"
    return b.get("ten") or b.get("ref") or "?"


def giai_buoc(kb):
    """Buoc cua kich ban -> danh sach PHANG (nhom tai nguyen duoc trai ra)."""
    ra = []
    for b in kb.get("buoc", []):
        if b.get("loai") == "nhom":
            g = DL.tim(DL.NHOM_TN.doc(), b.get("ref"))
            for m in (g or {}).get("muc", []):
                ra.append({"loai": m["loai"], "ref": m["ref"], "ten": m.get("ten", m["ref"]), "mot_lan": bool(b.get("mot_lan"))})
        else:
            ref = b.get("ref", "")
            if b["loai"] == "rustdesk":       # "chi cai mot lan" tinh theo dia chi may chu: doi may chu ID / chuyen tiep / khoa thi lan sau cai lai
                ref = "%s|%s|%s" % (RD.host_hieu_luc(), RD.relay_hieu_luc(), RD.khoa_cong_khai()[:12])
            ra.append({"loai": b["loai"], "ref": ref, "ten": b.get("ten", ""), "mot_lan": bool(b.get("mot_lan"))})
    return ra


def _cho_wol(ip, mac):
    if cong_mo(ip, 5985, 1.5):
        return True, "Máy đã bật sẵn (WinRM sẵn sàng), không cần gửi Wake-on-LAN."
    mac = _MP.chuan_mac(mac)
    if not mac:
        return False, "Máy chưa có địa chỉ MAC hợp lệ để bật bằng Wake-on-LAN (thêm MAC ở Máy - nhóm máy, bấm Kiểm tra để tự lấy)."
    _MP.gui([mac])
    het = time.time() + 240
    while time.time() < het:
        if cong_mo(ip, 5985, 1.0):
            return True, "Máy đã bật và sẵn sàng."
        time.sleep(5)
    return False, "Đã gửi Wake-on-LAN nhưng máy chưa lên sau 4 phút (kiểm tra BIOS có bật Wake on LAN không)."


def cong_mo(ip, cong, giay=0.5):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(giay)
    try:
        return s.connect_ex((ip, cong)) == 0
    except OSError:
        return False
    finally:
        s.close()


# ----------------------------------------------------------------- trang thai kich ban
def _luu(ham):
    return DL.TRANG_THAI.sua(ham)


def _nhat_ky(st, ip, tb):
    st.setdefault("nhat_ky", []).append(f"{time.strftime('%H:%M:%S')}  {ip}  {tb}")
    del st["nhat_ky"][:-120]


def may_cua_kich_ban(kb):
    """[{ip, ten, mac, id}] khong trung (nhom may + may le)."""
    ds_may = DL.MAY.doc()
    ids = list(kb.get("may", []))
    for gid in kb.get("nhom_may", []):
        g = DL.tim(DL.NHOM_MAY.doc(), gid)
        ids += (g or {}).get("may", [])
    ra, thay = [], set()
    for i in ids:
        m = DL.tim(ds_may, i)
        if m and m["ip"] not in thay:
            thay.add(m["ip"])
            ra.append(m)
    return ra


def _khoi_tao_lan_chay(kb, slot):
    buoc = giai_buoc(kb)
    may = may_cua_kich_ban(kb)

    def ghi(tt):
        st = tt.setdefault(kb["id"], {})
        st.update(slot=slot, bat_dau=time.time(), xong_luc=0, buoc_ten=[nhan_buoc(b) for b in buoc])
        st["may"] = {m["ip"]: {"ten": m.get("ten") or m["ip"], "tt": "cho", "thu": 0, "tiep": 0, "cap_nhat": 0,
                               "buoc": [{"ten": nhan_buoc(b), "loai": b["loai"], "tt": "cho", "tb": "", "luc": 0} for b in buoc]}
                     for m in may}
        _nhat_ky(st, "-", f"Bắt đầu lượt chạy mới ({len(may)} máy, {len(buoc)} bước).")
    _luu(ghi)


def kich_hoat(kb_id):
    kb = DL.tim(DL.KICH_BAN.doc(), kb_id)
    if not kb:
        return False, "Không tìm thấy kịch bản."
    if not may_cua_kich_ban(kb):
        return False, "Kịch bản chưa có máy nào (chọn nhóm máy hoặc máy ở bước sửa kịch bản)."
    if not giai_buoc(kb):
        return False, "Kịch bản chưa có bước nào."
    if not kb.get("tai_khoan_id") or DL.lay_tai_khoan(kb["tai_khoan_id"])[0] is None:
        return False, "Kịch bản chưa chọn tài khoản quản trị (tạo ở Máy - nhóm máy, Tài khoản quản trị)."

    def ghi(tt):
        st = tt.setdefault(kb_id, {})
        st.update(bat=True, kich_hoat=time.time(), slot="")
        _nhat_ky(st, "-", "Đã bấm CHẠY: kịch bản được kích hoạt, chạy theo lịch cho đến khi bấm Dừng.")
    _luu(ghi)
    khoi_dong_bo_lap_lich()
    return True, "Đã kích hoạt kịch bản."


def dung(kb_id):
    def ghi(tt):
        st = tt.setdefault(kb_id, {})
        st["bat"] = False
        _nhat_ky(st, "-", "Đã bấm DỪNG.")
    _luu(ghi)
    return True, "Đã dừng kịch bản."


def _buoc_cap_nhat(kb_id, ip, i, **kw):
    def ghi(tt):
        m = tt.get(kb_id, {}).get("may", {}).get(ip)
        if m and i < len(m["buoc"]):
            m["buoc"][i].update(kw)
            m["cap_nhat"] = time.time()
    _luu(ghi)


def _may_cap_nhat(kb_id, ip, **kw):
    def ghi(tt):
        m = tt.get(kb_id, {}).get("may", {}).get(ip)
        if m:
            m.update(kw)
            m["cap_nhat"] = time.time()
    _luu(ghi)


def _chay_mot_may(kb_id, ip):
    try:
        kb = DL.tim(DL.KICH_BAN.doc(), kb_id)
        if not kb:
            return
        buoc = giai_buoc(kb)
        may = next((m for m in may_cua_kich_ban(kb) if m["ip"] == ip), {"ip": ip, "mac": ""})
        user, mk = DL.lay_tai_khoan(kb.get("tai_khoan_id"))
        _may_cap_nhat(kb_id, ip, tt="dang")
        st0 = DL.TRANG_THAI.doc().get(kb_id, {}).get("may", {}).get(ip, {})
        c = None
        for i, b in enumerate(buoc):
            if not DL.TRANG_THAI.doc().get(kb_id, {}).get("bat"):
                _may_cap_nhat(kb_id, ip, tt="dung")
                return
            if i < len(st0.get("buoc", [])) and st0["buoc"][i]["tt"] == "ok":
                continue
            khoa_buoc = f'{b["loai"]}|{b["ref"]}'
            if b.get("mot_lan") and khoa_buoc in DL.TRANG_THAI.doc().get(kb_id, {}).get("da_xong", {}).get(ip, []):
                _buoc_cap_nhat(kb_id, ip, i, tt="ok", tb="Đã cài xong ở lượt trước, bỏ qua (kịch bản đặt 'chỉ cài một lần').", luc=time.time())
                continue
            _buoc_cap_nhat(kb_id, ip, i, tt="dang", tb="Đang chạy...", luc=time.time())
            try:
                if b["loai"] == "nguon" and b["ref"] == "bat":
                    ok, tb = _cho_wol(ip, may.get("mac", ""))
                else:
                    if user is None:
                        raise LoiKetNoi("Tài khoản quản trị đã bị xóa.")
                    if c is None:
                        if not cong_mo(ip, 5985, 3.0):
                            raise LoiKetNoi("Không kết nối được WinRM: máy đang tắt, mất mạng, chưa bật WinRM hoặc tường lửa chặn cổng 5985.")
                        c = _ket_noi(ip, user, mk)
                    ok, tb = _BUOC[b["loai"]](c, ip, b, may)
            except LoiKetNoi as e:
                _thu_ket_noi(kb_id, ip, i, st0, str(e), "Chưa vào được máy")
                return
            except Exception as e:                  # loi khi chay buoc (ke ca mat ket noi giua chung)
                tb_loi = _loi_dep(e, mk)
                if "WinRM" in tb_loi or "tài khoản" in tb_loi:
                    _thu_ket_noi(kb_id, ip, i, st0, tb_loi, "Mất kết nối")
                    return
                ok, tb = False, tb_loi
            if ok:
                if b.get("mot_lan"):
                    def ghi_da(tt, kb_id=kb_id, ip=ip, k=khoa_buoc):
                        d = tt.get(kb_id, {}).setdefault("da_xong", {}).setdefault(ip, [])
                        if k not in d:
                            d.append(k)
                    _luu(ghi_da)
                _buoc_cap_nhat(kb_id, ip, i, tt="ok", tb=tb, luc=time.time())
                _ghi_nk(kb_id, ip, f"Bước {i + 1}/{len(buoc)} xong: {tb}")
            else:
                _buoc_cap_nhat(kb_id, ip, i, tt="loi", tb=tb, luc=time.time())
                thu = st0.get("thu", 0) + 1
                cuoi = thu >= TOI_DA_THU
                _may_cap_nhat(kb_id, ip, tt="loi" if cuoi else "cho_thu_lai", thu=thu,
                              tiep=0 if cuoi else time.time() + THU_LAI_LOI_BUOC)
                _ghi_nk(kb_id, ip, f"Bước {i + 1}/{len(buoc)} LỖI (lần {thu}/{TOI_DA_THU}): {tb}"
                        + (" Không thành công." if cuoi else " Thử lại sau 5 phút."))
                return
        _may_cap_nhat(kb_id, ip, tt="xong")
        _ghi_nk(kb_id, ip, "Hoàn tất tất cả các bước.")
    except Exception as e:
        _may_cap_nhat(kb_id, ip, tt="loi", tiep=0)
        _ghi_nk(kb_id, ip, f"Lỗi bất ngờ: {str(e)[:200]}")
    finally:
        with _KHOA:
            _DANG.discard((kb_id, ip))


def _thu_ket_noi(kb_id, ip, i, st0, tb, tien_to):
    """Khong vao duoc may: tinh la 1 lan thu; du TOI_DA_THU lan thi 'Khong thanh cong', chua du thi 5 phut sau thu lai."""
    thu = st0.get("thu", 0) + 1
    cuoi = thu >= TOI_DA_THU
    _buoc_cap_nhat(kb_id, ip, i, tt="loi" if cuoi else "cho", tb=tb)
    _may_cap_nhat(kb_id, ip, tt="loi" if cuoi else "offline", thu=thu,
                  tiep=0 if cuoi else time.time() + THU_LAI_MAY_TAT)
    _ghi_nk(kb_id, ip, f"{tien_to} (lần {thu}/{TOI_DA_THU}). {tb} "
            + ("Không thành công." if cuoi else "Thử lại sau 5 phút."))


def _ghi_nk(kb_id, ip, tb):
    def ghi(tt):
        st = tt.get(kb_id)
        if st is not None:
            _nhat_ky(st, ip, tb)
    _luu(ghi)


# ----------------------------------------------------------------- bo lap lich (tick moi 15 giay)
def _slot_hien_tai(kb, st, bay_gio):
    lich = DL.tim(DL.LICH.doc(), kb.get("lich_id")) if kb.get("lich_id") else None
    if not lich:
        return f"ngay-{int(st.get('kich_hoat', 0))}"
    t = DL.lan_hen_gan_nhat(lich, bay_gio)
    # Chi tinh cac lan hen SAU luc bam Chay (hen luc 02:00 ma bam Chay luc 03:00 thi cho toi hom sau, khong chay ngay);
    # lo gio hen vi Console System tat thi chay bu neu chua qua 6 gio.
    if t and t.timestamp() >= st.get("kich_hoat", 0) and (bay_gio - t).total_seconds() <= CUA_SO_BU:
        return t.isoformat()
    return st.get("slot", "") if st.get("slot", "").startswith("2") else ""


def tick():
    bay_gio = datetime.now()
    tt = DL.TRANG_THAI.doc()
    kbs = {k["id"]: k for k in DL.KICH_BAN.doc()}
    for kb_id, st in tt.items():
        kb = kbs.get(kb_id)
        if not kb or not st.get("bat"):
            continue
        slot = _slot_hien_tai(kb, st, bay_gio)
        if slot and slot != st.get("slot"):
            if not may_cua_kich_ban(kb) or not giai_buoc(kb):
                continue
            _khoi_tao_lan_chay(kb, slot)
            st = DL.TRANG_THAI.doc().get(kb_id, {})
        if not st.get("slot"):
            continue
        xong_het = True
        for ip, m in st.get("may", {}).items():
            if m["tt"] in ("xong", "loi", "dung") and not (m["tt"] == "dung"):
                continue
            xong_het = False
            with _KHOA:
                if (kb_id, ip) in _DANG:
                    continue
                if m["tt"] in ("offline", "cho_thu_lai") and m.get("tiep", 0) > time.time():
                    continue
                if m["tt"] == "dang":                      # dich vu khoi dong lai giua chung: chay lai tu buoc dang do
                    pass
                _DANG.add((kb_id, ip))
            _EX.submit(_chay_mot_may, kb_id, ip)
        if xong_het and not st.get("xong_luc"):
            def ghi(t, kb_id=kb_id):
                s = t.get(kb_id)
                if s is not None:
                    s["xong_luc"] = time.time()
                    ok = sum(1 for m in s["may"].values() if m["tt"] == "xong")
                    _nhat_ky(s, "-", f"Xong lượt chạy: {ok}/{len(s['may'])} máy thành công.")
                    if (kbs.get(kb_id) or {}).get("tam"):
                        s["bat"] = False          # chay nhanh: lam 1 lan roi tu tat, khong de 'dang kich hoat' mai
            _luu(ghi)
    # don kich ban tam (chay nhanh) cu hon 1 ngay
    try:
        cu = [k["id"] for k in DL.KICH_BAN.doc() if k.get("tam") and time.time() - k.get("tao", 0) > 3600
              and not DL.TRANG_THAI.doc().get(k["id"], {}).get("bat")]
        if cu:
            DL.KICH_BAN.sua(lambda ds: ds.__setitem__(slice(None), [k for k in ds if k["id"] not in cu]))
            DL.TRANG_THAI.sua(lambda t: [t.pop(i, None) for i in cu])
    except Exception as _loi:
        _bo_qua(_loi)


def khoi_dong_bo_lap_lich():
    global _BO_LAP_DA_CHAY
    with _KHOA:
        if _BO_LAP_DA_CHAY:
            return
        _BO_LAP_DA_CHAY = True

    def vong():
        # khoi dong lai giua luot chay: may dang "dang" ma khong co luong nao giu -> cho chay lai
        try:
            def sua(tt):
                for st in tt.values():
                    for m in st.get("may", {}).values():
                        if m.get("tt") == "dang":
                            m["tt"] = "cho"
            DL.TRANG_THAI.sua(sua)
        except Exception as _loi:
            _bo_qua(_loi)
        while True:
            try:
                tick()
            except Exception as _loi:
                _bo_qua(_loi)
            time.sleep(15)
    threading.Thread(target=vong, daemon=True, name="tk-lap-lich").start()


def chay_nhanh(ten, buoc, ids_may, tai_khoan_id):
    """Chay ngay 1 viec le (khong luu thanh kich ban). Tra ve (kb_id, loi)."""
    kb = {"id": "nhanh-" + DL.moi_id(), "ten": ten, "tam": True, "tao": time.time(), "buoc": buoc, "nhom_may": [],
          "may": ids_may, "lich_id": "", "tai_khoan_id": tai_khoan_id}
    DL.KICH_BAN.sua(lambda ds: ds.append(kb))
    ok, tb = kich_hoat(kb["id"])
    return (kb["id"], "") if ok else (None, tb)


# ----------------------------------------------------------------- quet mang
_QUET = {"dang": False, "xong": 0, "tong": 0, "ket_qua": []}
CONG_QUET = ((5985, "WinRM"), (445, "SMB"), (3389, "RDP"))


def _mang_cuc_bo():
    import ipaddress
    import subprocess
    ra = []
    try:
        out = subprocess.run(["ip", "-j", "-4", "addr"], capture_output=True, text=True, timeout=5).stdout
        for c in json.loads(out or "[]"):
            ten = c.get("ifname", "")
            if ten == "lo" or ten.startswith(("docker", "veth", "br-", "virbr")):
                continue
            for a in c.get("addr_info", []):
                if a.get("family") == "inet" and a.get("prefixlen", 32) <= 30:
                    n = ipaddress.ip_network(f"{a['local']}/{a['prefixlen']}", strict=False)
                    if n.num_addresses <= 1024:
                        ra.append(n)
    except Exception as _loi:
        _bo_qua(_loi)
    return ra


def mac_tu_arp(ip):
    import subprocess
    try:
        out = subprocess.run(["ip", "neigh", "show", ip], capture_output=True, text=True, timeout=3).stdout
        m = re.search(r"lladdr ([0-9a-f:]{17})", out)
        return m.group(1) if m else ""
    except Exception:
        return ""


def _ten_dns(ip):
    try:
        return socket.gethostbyaddr(ip)[0].split(".")[0]
    except (OSError, socket.herror):
        return ""


def bat_dau_quet(cidr_them=""):
    import ipaddress
    with _KHOA:
        if _QUET["dang"]:
            return False, "Đang quét dở, chờ xong rồi quét lại."
        mang = _mang_cuc_bo()
        if cidr_them:
            try:
                n = ipaddress.ip_network(cidr_them, strict=False)
                if n.num_addresses > 1024:
                    return False, "Dải mạng tự nhập quá rộng (tối đa /22)."
                mang.append(n)
            except ValueError:
                return False, f'Dải mạng "{cidr_them}" không hợp lệ, viết kiểu 192.168.1.0/24.'
        if not mang:
            return False, "Không tìm thấy mạng LAN nào đang có địa chỉ IP."
        dia_chi = sorted({str(h) for n in mang for h in n.hosts()})
        _QUET.update(dang=True, xong=0, tong=len(dia_chi), ket_qua=[])

    def viec(ip):
        mo = [ten for cong, ten in CONG_QUET if cong_mo(ip, cong, 0.4)]
        if mo:
            with _KHOA:
                _QUET["ket_qua"].append({"ip": ip, "ten": _ten_dns(ip), "mac": mac_tu_arp(ip), "cong": mo})
        with _KHOA:
            _QUET["xong"] += 1

    def chay():
        bua = []
        for ip in dia_chi:
            while threading.active_count() > 64:
                time.sleep(0.05)
            t = threading.Thread(target=viec, args=(ip,), daemon=True)
            t.start()
            bua.append(t)
        for t in bua:
            t.join()
        with _KHOA:
            _QUET["dang"] = False
            _QUET["ket_qua"].sort(key=lambda x: tuple(int(p) for p in x["ip"].split(".")))
    threading.Thread(target=chay, daemon=True).start()
    return True, f"Đang quét {len(dia_chi)} địa chỉ..."


def trang_thai_quet():
    with _KHOA:
        return json.loads(json.dumps(_QUET))


def passkey_agent_msi(duong):
    """Passkey da luu cua goi agent MSI (co passkey) trung voi file nay, hoac '' (khong phai goi agent / chua luu).
    Dung cho cai Windows (un_goapp_font) - cung kho goi voi Trien khai phan mem LAN o tren."""
    from ui import uem_agent_goi as UG
    g = UG.tim_theo_file(duong)
    return UG.passkey_trien_khai(g) if g and g.get("co_passkey") else ""


def dien_tham_so_app_neu_trong(ten, cai, go):
    """Dien san tham so cai / lenh go cho 1 file trong Tai nguyen, Phan mem neu dang trong (khong de len gia tri nguoi dung da sua).
    Dung khi Quan ly may tram dua goi agent MSI vao kho."""
    from ui import deployos as D
    meta = D.doc_thongtin_app()
    if not (meta.get(ten) or "").strip():
        meta[ten] = cai
    if not (meta.get(ten + D.HAU_TO_GO) or "").strip():
        meta[ten + D.HAU_TO_GO] = go
    D.ghi_thongtin_app(meta)
