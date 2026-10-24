# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Quan ly may tram - THU THAP BAO CAO may (tuong duong "agent report" cua OpenUEM, nhung khong can agent).

Nguon du lieu bam theo ma nguon OpenUEM (openuem-agent/internal/commands/report/*_windows.go):
  may tinh      Win32_ComputerSystem (hang, model, RAM) + Win32_BIOS (serial; "System Serial Number" = Unknown) +
                Win32_Processor (ten, kien truc 0=x86 5=ARM 9=x64 12=ARM64..., so nhan)
  he dieu hanh  Win32_OperatingSystem (Version, Caption, InstallDate, LastBootUpTime), EditionID (registry), Domain, UserName
  o dia logic   Win32_LogicalDisk (chi o co Size) + BitLocker qua Win32_EncryptableVolume (ProtectionStatus 0/1)
  o dia vat ly  Win32_DiskDrive          man hinh   WmiMonitorID (root\\wmi, mang ma ASCII)    khe RAM  Win32_PhysicalMemory
  card mang     Win32_NetworkAdapter (NetConnectionStatus=2) + Win32_NetworkAdapterConfiguration
  may in        Win32_Printer          thu muc chia se  Win32_Share
  diet virus    root\\SecurityCenter2 AntiVirusProduct, productState: (state & 0xF000)==0x1000 la dang bat,
                (state & 0xF0)==0 la CSDL moi (dung y isAntivirusActive / isSignatureDBUpdated cua OpenUEM)
  cap nhat      Microsoft.Update.AutoUpdate (NotificationLevel, ngay tim/cai gan nhat) + Search "IsAssigned=1 and IsHidden=0 and IsInstalled=0
                and Type='Software'" (cap nhat dang cho) + QueryHistory (lich su)
  phan mem      Uninstall registry HKLM 64/32-bit + hive cac user dang nap; CAN co DisplayName va DisplayVersion; trung ten lay ban dau
GIOI HAN SO VOI AGENT THAT (ghi ro tren giao dien): WinRM chay duoi phien quan tri KHONG phai phien nguoi dung dang ngoi may,
nen may in cai rieng cho tung user va ung dung Microsoft Store khong thay duoc.
"""
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from . import tk_dongco as DC
from . import uem_ketnoi as UK
from . import tk_dulieu as DL
from . import uem_dulieu as UD

SCRIPT = r"""
$ErrorActionPreference='SilentlyContinue'; $ProgressPreference='SilentlyContinue'
function Dv([double]$b){ $mb=[math]::Floor($b/1000000); if($mb -ge 1000){ $gb=[math]::Floor($b/1000000000); if($gb -ge 1000){ return "$([math]::Floor($b/1000000000000)) TB" }; return "$gb GB" }; return "$mb MB" }
function Dr([double]$b){ $mb=[math]::Floor($b/1048576); if($mb -ge 1000){ return "$([math]::Floor($b/1073741824)) GB" }; return "$mb MB" }
function Iso($d){ if($d){ try{ return ([datetime]$d).ToString('s') }catch{ return $null } } return $null }
function Txt($a){ if($a -eq $null){ return '' }; $s=''; foreach($c in $a){ if($c -ne 0){ $s += [char]$c } }; return $s.Trim() }
$r=[ordered]@{}
$cs=Get-CimInstance Win32_ComputerSystem; $bios=Get-CimInstance Win32_BIOS; $os=Get-CimInstance Win32_OperatingSystem
$cpu=Get-CimInstance Win32_Processor | Select-Object -First 1
$arch=@{0='x86';1='MIPS';2='Alpha';3='PowerPC';5='ARM';6='ia64';9='x64';12='ARM64'}
$serial='Unknown'; if($bios.SerialNumber -and $bios.SerialNumber -ne 'System Serial Number'){ $serial=([string]$bios.SerialNumber).Trim() }
$r.hostname=$env:COMPUTERNAME
$r.computer=[ordered]@{manufacturer=[string]$cs.Manufacturer;model=[string]$cs.Model;serial=$serial;processor=[string]$cpu.Name;processor_arch=[string]$arch[[int]$cpu.Architecture];processor_cores=[int]$cpu.NumberOfCores;memory=[string](Dr $cs.TotalPhysicalMemory)}
$ed=(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').EditionID
$r.operatingsystem=[ordered]@{version=[string]$os.Version;description=[string]$os.Caption;install_date=(Iso $os.InstallDate);edition=[string]$ed;arch=[string]$os.OSArchitecture;username=[string]$cs.UserName;last_bootup_time=(Iso $os.LastBootUpTime);domain=[string]$cs.Domain;build=[string]$os.BuildNumber}
$bl=@{}; Get-CimInstance -Namespace 'root\CIMV2\Security\MicrosoftVolumeEncryption' -ClassName Win32_EncryptableVolume | ForEach-Object { $st='Unknown'; if($_.ProtectionStatus -eq 0){$st='Unencrypted'}elseif($_.ProtectionStatus -eq 1){$st='Encrypted'}; $bl[[string]$_.DriveLetter]=$st }
$r.logicaldisks=@(Get-CimInstance Win32_LogicalDisk | Where-Object { $_.Size } | ForEach-Object { $b='Unknown'; if($bl.ContainsKey([string]$_.DeviceID)){ $b=$bl[[string]$_.DeviceID] }
  [ordered]@{label=[string]$_.DeviceID;usage=[int](100-[math]::Floor($_.FreeSpace*100/$_.Size));filesystem=[string]$_.FileSystem;size_in_units=(Dv $_.Size);remaining_space_in_units=(Dv $_.FreeSpace);volume_name=[string]$_.VolumeName;bitlocker_status=$b;drive_type=[int]$_.DriveType} })
$r.physicaldisks=@(Get-CimInstance Win32_DiskDrive | ForEach-Object { [ordered]@{device_id=[string]$_.DeviceID;model=[string]$_.Model;serial_number=([string]$_.SerialNumber).Trim();size_in_units=(Dv $_.Size)} })
$r.monitors=@(Get-CimInstance -Namespace root\wmi -ClassName WmiMonitorID | ForEach-Object { [ordered]@{manufacturer=(Txt $_.ManufacturerName);model=(Txt $_.UserFriendlyName);serial=(Txt $_.SerialNumberID);week_of_manufacture=[string]$_.WeekOfManufacture;year_of_manufacture=[string]$_.YearOfManufacture} })
$mt=@{0='Unknown';1='Other';2='DRAM';3='Synchronous DRAM';4='Cache DRAM';5='EDO';6='EDRAM';7='VRAM';8='SRAM';9='RAM';10='ROM';11='Flash';12='EEPROM';13='FEPROM';14='EPROM';15='CDRAM';16='3DRAM';17='SDRAM';18='SGRAM';19='RDRAM';20='DDR';21='DDR2';22='DDR2 FB-DIMM';24='DDR3';26='DDR4';34='DDR5'}
$r.memoryslots=@(Get-CimInstance Win32_PhysicalMemory | ForEach-Object { $t=$mt[[int]$_.SMBIOSMemoryType]; if(-not $t){$t='Unknown'}; [ordered]@{slot=[string]$_.DeviceLocator;size=(Dr $_.Capacity);type=$t;serial_number=([string]$_.SerialNumber).Trim();part_number=([string]$_.PartNumber).Trim();speed="$([int]$_.ConfiguredClockSpeed) MHz";manufacturer=([string]$_.Manufacturer).Trim()} })
$r.printers=@(Get-CimInstance Win32_Printer | ForEach-Object { [ordered]@{name=[string]$_.Name;port=[string]$_.PortName;is_default=[bool]$_.Default;is_network=[bool]$_.Network;is_shared=[bool]$_.Shared} })
$r.shares=@(Get-CimInstance Win32_Share | ForEach-Object { [ordered]@{name=[string]$_.Name;description=[string]$_.Description;path=[string]$_.Path} })
$na=@(); $cfg=@{}; Get-CimInstance Win32_NetworkAdapterConfiguration | ForEach-Object { $cfg[[int]$_.Index]=$_ }
foreach($a in (Get-CimInstance Win32_NetworkAdapter | Where-Object { $_.NetConnectionStatus -eq 2 })){
  $c=$cfg[[int]$a.Index]; $sp=[math]::Floor($a.Speed/1000000); $un='Mbps'; if($a.Speed -ge 1000000000){ $un='Gbps'; $sp=[math]::Floor($sp/1000) }
  $na += [ordered]@{name=[string]$a.Name;mac_address=[string]$a.MACAddress;addresses=[string]($c.IPAddress | Select-Object -First 1);subnet=[string]($c.IPSubnet | Select-Object -First 1);default_gateway=(@($c.DefaultIPGateway) -join ', ');dns_servers=(@($c.DNSServerSearchOrder) -join ', ');dns_domain=[string]$c.DNSDomain;dhcp_enabled=[bool]$c.DHCPEnabled;dhcp_lease_obtained=$(if($c.DHCPEnabled){Iso $c.DHCPLeaseObtained}else{$null});dhcp_lease_expired=$(if($c.DHCPEnabled){Iso $c.DHCPLeaseExpires}else{$null});speed="$sp $un";virtual=[bool]($a.PhysicalAdapter -eq $false)}
}
$r.networkadapters=$na
$av=@(Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | ForEach-Object { [ordered]@{name=[string]$_.displayName;state=[int]$_.productState;is_active=((([int]$_.productState) -band 0xF000) -eq 0x1000);is_updated=((([int]$_.productState) -band 0x00F0) -eq 0)} })
$r.antivirus_all=$av
$pick=$av | Where-Object { $_.name -eq 'Windows Defender' } | Select-Object -First 1; if(-not $pick){ $pick=$av | Where-Object { $_.is_active } | Select-Object -First 1 }; if(-not $pick){ $pick=$av | Select-Object -First 1 }
if($pick){ $r.antivirus=[ordered]@{name=$pick.name;is_active=$pick.is_active;is_updated=$pick.is_updated} } else { $r.antivirus=[ordered]@{name='';is_active=$false;is_updated=$false} }
$mp=Get-MpComputerStatus; if($mp){ $r.defender=[ordered]@{realtime=[bool]$mp.RealTimeProtectionEnabled;antispyware=[bool]$mp.AntispywareEnabled;firma_tuoi_ngay=[int]$mp.AntivirusSignatureAge;firma_ban=[string]$mp.AntivirusSignatureVersion} }
$r.firewall=@(Get-NetFirewallProfile | ForEach-Object { [ordered]@{ten=[string]$_.Name;bat=[bool]$_.Enabled} })
$smb=Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol; if($smb){ $r.smb1=[string]$smb.State }
$su=[ordered]@{status='';last_install=$null;last_search=$null;pending_updates=$false}
try{ $au=New-Object -ComObject Microsoft.Update.AutoUpdate; $su.status=[string]$au.Settings.NotificationLevel; $su.last_search=(Iso $au.Results.LastSearchSuccessDate); $su.last_install=(Iso $au.Results.LastInstallationSuccessDate) }catch{}
if(-not $su.status){ try{ $p=Get-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU' -ErrorAction SilentlyContinue
  if($p -and $p.NoAutoUpdate -eq 1){ $su.status='1' } elseif($p -and $p.AUOptions){ $su.status=[string]$p.AUOptions } else { $su.status='4' } }catch{} }
foreach($kv in @(@('last_search','Detect'),@('last_install','Install'))){ if(-not $su[$kv[0]]){ try{ $v=(Get-ItemProperty -Path ('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\Results\'+$kv[1]) -ErrorAction Stop).LastSuccessTime
  if($v){ $su[$kv[0]]=(Iso ([datetime]::SpecifyKind([datetime]::Parse($v,[Globalization.CultureInfo]::InvariantCulture),'Utc')).ToLocalTime()) } }catch{} } }
$pend=@(); $hist=@()
try{ $sess=New-Object -ComObject Microsoft.Update.Session; $sr=$sess.CreateUpdateSearcher()
  $res=$sr.Search("IsAssigned=1 and IsHidden=0 and IsInstalled=0 and Type='Software'")
  foreach($u in $res.Updates){ $pend += [ordered]@{title=[string]$u.Title;kb=(@($u.KBArticleIDs) -join ', ');critical=[bool]($u.MsrcSeverity -eq 'Critical')} }
  $n=$sr.GetTotalHistoryCount(); if($n -gt 0){ foreach($h in $sr.QueryHistory(0,[math]::Min($n,60))){ if($h.ClientApplicationID -eq 'MoUpdateOrchestrator' -and $h.Date){ $hist += [ordered]@{title=[string]$h.Title;date=(Iso $h.Date);support_url=[string]$h.SupportUrl} } } }
}catch{}
$su.pending_updates=($pend.Count -gt 0); $r.systemupdate=$su; $r.pending_updates=$pend; $r.updates=$hist
$apps=[ordered]@{}
$keys=@('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*')
foreach($h in (Get-ChildItem Registry::HKEY_USERS | Where-Object { $_.PSChildName -match '^S-1-5-21-[\d-]+$' })){ $keys += "Registry::HKEY_USERS\$($h.PSChildName)\Software\Microsoft\Windows\CurrentVersion\Uninstall\*"; $keys += "Registry::HKEY_USERS\$($h.PSChildName)\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*" }
foreach($k in $keys){ Get-ItemProperty $k | Where-Object { $_.DisplayName -and $_.DisplayVersion } | ForEach-Object { $n=([string]$_.DisplayName).Trim(); if(-not $apps.Contains($n)){ $apps[$n]=[ordered]@{name=$n;version=([string]$_.DisplayVersion).Trim();install_date=[string]$_.InstallDate;publisher=([string]$_.Publisher).Trim()} } } }
$r.applications=@($apps.Values | Sort-Object { $_.name })
$ips=@(Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object { $_.IPEnabled } | ForEach-Object { $_.IPAddress } | Where-Object { $_ -match '^\d+\.\d+\.\d+\.\d+$' }); $r.ip=($ips | Select-Object -First 1)
$r.mac=[string]($na | Select-Object -First 1).mac_address
$r.winrm_ps=[string]$PSVersionTable.PSVersion
"UEM_JSON=" + ($r | ConvertTo-Json -Depth 7 -Compress)
"""

_MA_UPDATE = {"0": "Chưa cấu hình", "1": "Tắt", "2": "Thông báo trước khi tải", "3": "Thông báo trước khi cài", "4": "Tự động tải và cài theo lịch"}
_EX = ThreadPoolExecutor(max_workers=4)
_DANG = set()
_KHOA = threading.Lock()
_BAT_DAU = False


def ten_cap_nhat_tu_dong(s):
    return _MA_UPDATE.get(str(s), str(s) or "Không rõ")


def _doc(c, mk):
    out, err = DC._chay_ps(c, SCRIPT)
    m = re.search(r"UEM_JSON=(\{.*\})", out, re.S)
    if not m:
        return None, f"Không đọc được báo cáo. {err}"[:300]
    d = json.loads(m.group(1))
    d["luc"] = time.time()
    return d, ""


def thu_thap(ip, user, mat_khau):
    """Lay bao cao qua WinRM voi thong tin truc tiep (dung cho thu nghiem). Tra ve (dict hoac None, loi)."""
    try:
        if not DC.cong_mo(ip, 5985, 3.0):
            return None, "Máy tắt, mất mạng hoặc chưa bật WinRM (cổng 5985 đóng)."
        return _doc(DC._ket_noi(ip, user, mat_khau), mat_khau)
    except DC.LoiKetNoi as e:
        return None, str(e)
    except Exception as e:
        return None, DC._loi_dep(e, mat_khau)


def thu_thap_may(m):
    """Lay bao cao cua 1 may qua agent (neu dang song) hoac WinRM. Tra ve (dict hoac None, loi, cach)."""
    try:
        c, mk, loai = UK.ket_noi(m)
        d, loi = _doc(c, mk)
        return d, loi, loai
    except UK.LoiMay as e:
        return None, str(e), ""
    except Exception as e:
        return None, DC._loi_dep(e), ""


def _chuan_mac(x):
    h = re.sub(r"[^0-9A-Fa-f]", "", x or "")
    return ":".join(h[i:i + 2] for i in range(0, 12, 2)).upper() if len(h) == 12 and h != "0" * 12 else ""


def _tu_dien(may_id, d):
    """Sau khi co thong tin may: tu dien cac o con trong cua ban ghi may (MAC cho Wake-on-LAN, ten may). KHONG ghi de o da co,
    nen nguoi dung sua tay sau do se duoc giu nguyen. IP khong doi (la khoa de ket noi)."""
    m = DL.tim(DL.MAY.doc(), may_id) or {}
    the_nic = [n for n in (d.get("networkadapters") or []) if _chuan_mac(n.get("mac_address"))]
    nic = next((n for n in the_nic if m.get("ip") and m["ip"] in (n.get("addresses") or "")), None) or (the_nic[0] if the_nic else None)
    mac = _chuan_mac(d.get("mac")) or (_chuan_mac(nic.get("mac_address")) if nic else "")
    host = re.sub(r"[^A-Za-z0-9._-]", "", d.get("hostname") or "")[:63]
    kw = {}
    if mac and not m.get("mac"):
        kw["mac"] = mac
    if host and (not m.get("ten") or m.get("ten") == m.get("ip")):
        kw["ten"] = host
    if kw:
        UD.sua_may(may_id, **kw)


def bao_cao_may(may_id):
    """Lay + luu bao cao cua 1 may (agent neu co, khong thi WinRM voi tai khoan da gan). Tra ve (ok, thong_diep)."""
    m = DL.tim(DL.MAY.doc(), may_id)
    if not m:
        return False, "Không tìm thấy máy."
    d, loi, cach = thu_thap_may(m)
    if d is None:
        UD.sua_may(may_id, ket_noi={"ok": False, "loi": loi, "luc": time.time()})
        return False, loi
    UD.sua_may(may_id, bao_cao=d, bao_cao_luc=time.time(), ket_noi={"ok": True, "loi": "", "luc": time.time(), "qua": cach})
    _tu_dien(may_id, d)
    return True, f"{d['computer'].get('manufacturer', '')} {d['computer'].get('model', '')}, {len(d.get('applications', []))} phần mềm."


def _viec(may_id):
    try:
        bao_cao_may(may_id)
    finally:
        with _KHOA:
            _DANG.discard(may_id)


def dang_chay(may_id):
    with _KHOA:
        return may_id in _DANG


def chay_nen(may_id):
    """Bao cao o nen (khong chan giao dien). False neu may dang duoc lay bao cao."""
    with _KHOA:
        if may_id in _DANG:
            return False
        _DANG.add(may_id)
    _EX.submit(_viec, may_id)
    return True


def _tick():
    cd = UD.cai_dat()
    if not cd.get("tu_dong_giam_sat", True):
        return
    chu_ky = max(5, int(cd.get("tan_suat_bao_cao", 60))) * 60
    now = time.time()
    for m in DL.MAY.doc():
        if not m.get("giam_sat", True) or not UK.co_the_ket_noi(m):
            continue
        lan_cuoi = max(m.get("bao_cao_luc", 0), (m.get("ket_noi") or {}).get("luc", 0))
        loi = not (m.get("ket_noi") or {"ok": True}).get("ok", True)
        cho = 300 if loi else chu_ky          # may loi/tat: thu lai moi 5 phut
        if now - lan_cuoi >= cho:
            chay_nen(m["id"])


def khoi_dong_bo_lap():
    global _BAT_DAU
    with _KHOA:
        if _BAT_DAU:
            return
        _BAT_DAU = True

    def vong():
        time.sleep(20)
        while True:
            try:
                _tick()
            except Exception:
                pass
            time.sleep(30)
    threading.Thread(target=vong, daemon=True, name="uem-bao-cao").start()
