from gen_core import sc
CDM = r'Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager'
EXP = r'Software\Microsoft\Windows\CurrentVersion\Explorer'
ADV = EXP + r'\Advanced'

sc("01-go-onedrive", "Go OneDrive", "Go OneDrive va khong cho cai lai cho tai khoan tao sau",
r'''
Get-Process OneDrive -ErrorAction SilentlyContinue | Stop-Process -Force
$s = @("$env:SystemRoot\SysWOW64\OneDriveSetup.exe", "$env:SystemRoot\System32\OneDriveSetup.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
$dangCo = (Test-Path "$env:LOCALAPPDATA\Microsoft\OneDrive\OneDrive.exe") -or (Test-Path "$env:ProgramFiles\Microsoft OneDrive\OneDrive.exe") -or (Test-Path "${env:ProgramFiles(x86)}\Microsoft OneDrive\OneDrive.exe")
if ($s -and $dangCo) { $p = Start-Process $s '/uninstall' -PassThru -Wait -WindowStyle Hidden; Ghi "Go OneDrive, ma thoat $($p.ExitCode)" } else { Ghi 'OneDrive da duoc go san - khong can go lai' }
Remove-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name OneDrive -ErrorAction SilentlyContinue
if (NapHoSoMacDinh) { Lenh 'reg delete "HKU\CS_Default\Software\Microsoft\Windows\CurrentVersion\Run" /v OneDriveSetup /f' | Out-Null }
''',
r'''-not (Get-Process OneDrive) -and -not (V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' 'OneDrive')''',
undo="Cai lai OneDrive tu Microsoft")

sc("02-tat-hibernate", "Tat Hibernate", "Tat ngu dong (xoa hiberfil.sys) de lay lai vai GB o C:",
r'''
$r = Lenh 'powercfg /h off'
if ($r -ne 0) { throw "powercfg /h off loi, ma $r" }
''',
r'''(V 'HKLM:\SYSTEM\CurrentControlSet\Control\Power' 'HibernateEnabled') -eq 0''',
undo="powercfg /h on")

sc("03-tat-reserved-storage", "Tat Reserved Storage", "Tat vung dat truoc ~7 GB cho cap nhat. Nen chay truoc khi Windows Update chay",
r'''
if ($Build -lt 18362) { BoQua 'Windows nay khong co Reserved Storage' }
$o = Chay 'dism.exe /Online /Set-ReservedStorageState /State:Disabled'
Ghi $o
if ($script:Ma -ne 0) { throw "DISM ma $($script:Ma)" }
Dat 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\ReserveManager' 'ShippedWithReserves' 0
''',
r'''if ($Build -lt 18362) { $true } else { (V 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\ReserveManager' 'ShippedWithReserves') -eq 0 -and ((cmd /c 'dism.exe /Online /Get-ReservedStorageState 2>&1' | Out-String) -match 'Disabled') }''',
undo="dism /Online /Set-ReservedStorageState /State:Enabled")

sc("04-bat-storage-sense", "Bat Storage Sense", "Windows tu don file tam va thung rac (thung rac giu 30 ngay)",
"", r'''(V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\StorageSense\Parameters\StoragePolicy' '01') -eq 1''',
user=[(r'Software\Microsoft\Windows\CurrentVersion\StorageSense\Parameters\StoragePolicy', n, v, 'DWord')
      for n, v in (('01', 1), ('04', 1), ('08', 1), ('256', 30), ('32', 0))])

sc("05-tat-phim-dinh", "Tat phim dinh", "Tat hop thoai Sticky/Toggle/Filter Keys khi bam Shift 5 lan",
r'''
Dat 'Registry::HKEY_USERS\.DEFAULT\Control Panel\Accessibility\StickyKeys' 'Flags' '506' 'String'
''',
r'''(V 'HKCU:\Control Panel\Accessibility\StickyKeys' 'Flags') -eq '506' -and (V 'HKCU:\Control Panel\Accessibility\ToggleKeys' 'Flags') -eq '58' ''',
user=[(r'Control Panel\Accessibility\StickyKeys', 'Flags', '506', 'String'),
      (r'Control Panel\Accessibility\ToggleKeys', 'Flags', '58', 'String'),
      (r'Control Panel\Accessibility\Keyboard Response', 'Flags', '122', 'String')])

sc("06-dong-ho-24h", "Dong ho 24 gio", "Gio 24h (HH:mm:ss), tuan bat dau thu Hai",
"", r'''(V 'HKCU:\Control Panel\International' 'sTimeFormat') -eq 'HH:mm:ss' -and (V 'HKCU:\Control Panel\International' 'iFirstDayOfWeek') -eq '0' ''',
user=[(r'Control Panel\International', n, v, 'String') for n, v in
      (('sShortTime', 'HH:mm'), ('sTimeFormat', 'HH:mm:ss'), ('iTime', '1'), ('iTLZero', '1'), ('iFirstDayOfWeek', '0'))])

sc("07-dinh-dang-viet-nam", "Dinh dang Viet Nam", "Vung Viet Nam, dinh dang ngay dd/MM/yyyy, so, tien te (khong doi ngon ngu hien thi)",
r'''
Set-WinHomeLocation -GeoId 251
Set-Culture -CultureInfo vi-VN
if (Get-Command Copy-UserInternationalSettingsToSystem -ErrorAction SilentlyContinue) {
    Copy-UserInternationalSettingsToSystem -WelcomeScreen $true -NewUser $true
}
# Set-Culture dat lai gio/ngay theo mac dinh vi-VN -> chot lai: gio 24h, tuan bat dau thu Hai, ngay dd/MM/yyyy
foreach ($kv in @(@('sShortTime','HH:mm'), @('sTimeFormat','HH:mm:ss'), @('iTime','1'), @('iTLZero','1'), @('iFirstDayOfWeek','0'), @('sShortDate','dd/MM/yyyy'))) {
    DatUser 'Control Panel\International' $kv[0] $kv[1] 'String'
}
''',
r'''(V 'HKCU:\Control Panel\International' 'LocaleName') -eq 'vi-VN' -and (V 'HKCU:\Control Panel\International\Geo' 'Nation') -eq '251' ''',
undo="Set-Culture en-US")

sc("08-bat-clipboard-history", "Bat Clipboard history", "Bat lich su clipboard (Windows + V)",
"", r'''(V 'HKCU:\Software\Microsoft\Clipboard' 'EnableClipboardHistory') -eq 1''',
user=[(r'Software\Microsoft\Clipboard', 'EnableClipboardHistory', 1, 'DWord')])

sc("09-tat-spotlight-khoa", "Tat Spotlight man hinh khoa", "Man hinh khoa khong doi anh/quang cao Windows Spotlight",
"", r'''(V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager' 'RotatingLockScreenEnabled') -eq 0''',
user=[(CDM, n, 0, 'DWord') for n in ('RotatingLockScreenEnabled', 'RotatingLockScreenOverlayEnabled', 'SubscribedContent-338387Enabled')])

sc("10-tat-game-mode-dvr", "Tat Game Mode va Game DVR", "Tat Game Bar, quay man hinh nen va Game Mode tu bat",
r'''
Dat 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\GameDVR' 'AllowGameDVR' 0
''',
r'''(V 'HKCU:\System\GameConfigStore' 'GameDVR_Enabled') -eq 0 -and (V 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\GameDVR' 'AllowGameDVR') -eq 0''',
user=[(r'System\GameConfigStore', 'GameDVR_Enabled', 0, 'DWord'),
      (r'Software\Microsoft\GameBar', 'AutoGameModeEnabled', 0, 'DWord'),
      (r'Software\Microsoft\GameBar', 'AllowAutoGameMode', 0, 'DWord'),
      (r'Software\Microsoft\Windows\CurrentVersion\GameDVR', 'AppCaptureEnabled', 0, 'DWord')])

sc("11-tat-meo-goi-y", "Tat meo va goi y Windows", "Tat thong bao 'meo dung Windows', goi y trong Start va Settings",
"", r'''(V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager' 'SubscribedContent-338389Enabled') -eq 0 -and (V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager' 'SystemPaneSuggestionsEnabled') -eq 0''',
user=[(CDM, n, 0, 'DWord') for n in ('SubscribedContent-338389Enabled', 'SoftLandingEnabled', 'SystemPaneSuggestionsEnabled', 'SubscribedContent-353694Enabled', 'SubscribedContent-353696Enabled')])

sc("12-shortcut-cong-cu-it", "Shortcut cong cu IT", "Tao thu muc 'IT Tools' tren Desktop chung: Device Manager, Disk Management, Services, Event Viewer...",
r'''
$thu = 'C:\Users\Public\Desktop\IT Tools'
New-Item $thu -ItemType Directory -Force | Out-Null
$sh = New-Object -ComObject WScript.Shell
$ds = @(@('Device Manager','devmgmt.msc'), @('Disk Management','diskmgmt.msc'), @('Services','services.msc'), @('Event Viewer','eventvwr.msc'),
        @('Computer Management','compmgmt.msc'), @('Network Connections','ncpa.cpl'), @('Programs and Features','appwiz.cpl'),
        @('Task Scheduler','taskschd.msc'), @('Registry Editor','regedit.exe'))
foreach ($d in $ds) {
    $t = Join-Path $env:SystemRoot ('System32\' + $d[1])
    if (-not (Test-Path $t)) { $t = Join-Path $env:SystemRoot $d[1] }
    $l = $sh.CreateShortcut((Join-Path $thu ($d[0] + '.lnk')))
    $l.TargetPath = $t
    $l.Save()
}
Ghi "Da tao $($ds.Count) shortcut"
''',
r'''@(Get-ChildItem 'C:\Users\Public\Desktop\IT Tools\*.lnk').Count -ge 9''',
undo="Xoa thu muc C:\\Users\\Public\\Desktop\\IT Tools")

sc("13-bat-restore-point", "Bat System Restore va tao restore point", "Bat System Restore tren o he thong (5% dung luong) va tao diem khoi phuc 'ConsolePi - may moi'",
r'''
Dat 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SystemRestore' 'SystemRestorePointCreationFrequency' 0
Enable-ComputerRestore -Drive "$env:SystemDrive\"
Lenh "vssadmin resize shadowstorage /for=$env:SystemDrive /on=$env:SystemDrive /maxsize=5%" | Out-Null
$da = Get-ComputerRestorePoint -ErrorAction SilentlyContinue | Where-Object { $_.Description -like 'ConsolePi*' }
if (-not $da) { Checkpoint-Computer -Description 'ConsolePi - may moi' -RestorePointType MODIFY_SETTINGS; Ghi 'Da tao restore point' } else { Ghi 'Da co restore point ConsolePi' }
''',
r'''@(Get-ComputerRestorePoint | Where-Object { $_.Description -like 'ConsolePi*' }).Count -ge 1''',
undo="Disable-ComputerRestore -Drive C:\\")

sc("14-tat-doi-may-in-mac-dinh", "Tat Windows tu doi may in mac dinh", "May in mac dinh giu nguyen, khong nhay theo may in dung gan nhat",
"", r'''(V 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Windows' 'LegacyDefaultPrinterMode') -eq 1''',
user=[(r'Software\Microsoft\Windows NT\CurrentVersion\Windows', 'LegacyDefaultPrinterMode', 1, 'DWord')])

sc("15-tat-search-indexing", "Tat Windows Search indexing", "Tat dich vu lap chi muc (may yeu/o cung). Luu y: tim kiem trong Outlook/Explorer se cham hon",
r'''
if (-not (Get-Service WSearch -ErrorAction SilentlyContinue)) { BoQua 'Khong co dich vu Windows Search' }
Stop-Service WSearch -Force -ErrorAction SilentlyContinue
Set-Service WSearch -StartupType Disabled
''',
r'''if (Get-Service WSearch) { (Get-Service WSearch).StartType -eq 'Disabled' } else { $true }''',
undo="Set-Service WSearch -StartupType Automatic")

sc("16-pagefile-tu-dong", "Pagefile do he thong quan ly", "Dam bao pagefile de Windows tu quan ly kich thuoc",
r'''
$cs = Get-CimInstance Win32_ComputerSystem
if (-not $cs.AutomaticManagedPagefile) { Set-CimInstance -InputObject $cs -Property @{ AutomaticManagedPagefile = $true }; Ghi 'Da bat pagefile tu dong' } else { Ghi 'Pagefile da o che do tu dong' }
''',
r'''(Get-CimInstance Win32_ComputerSystem).AutomaticManagedPagefile -eq $true''')

sc("17-bat-wake-on-lan", "Bat Wake-on-LAN", "Bat danh thuc qua mang (magic packet) tren card mang that. May ao/card khong ho tro se duoc bo qua",
r'''
$n = 0; $bo = 0
foreach ($a in Get-NetAdapter -Physical -ErrorAction SilentlyContinue) {
    try { Set-NetAdapterPowerManagement -Name $a.Name -WakeOnMagicPacket Enabled -ErrorAction Stop; $n++ } catch { $bo++ }
}
Ghi "Bat WoL: $n card, bo qua $bo card khong ho tro"
''',
r'''-not (@(Get-NetAdapter -Physical | ForEach-Object { Get-NetAdapterPowerManagement -Name $_.Name } | Where-Object { $_.WakeOnMagicPacket -ne 'Unsupported' -and $_.WakeOnMagicPacket -ne 'Enabled' }))''',
undo="Set-NetAdapterPowerManagement -WakeOnMagicPacket Disabled")

sc("18-tat-tiet-kiem-dien-card", "Tat tiet kiem dien cua card mang va USB", "Khong cho Windows tat card Wi-Fi/LAN va USB de tiet kiem dien (hay gay roi mang)",
r'''
$cls = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}'
$guids = @(Get-NetAdapter -Physical -ErrorAction SilentlyContinue | ForEach-Object { $_.InterfaceGuid })
$n = 0
foreach ($k in Get-ChildItem $cls -ErrorAction SilentlyContinue) {
    $p = Get-ItemProperty $k.PSPath -ErrorAction SilentlyContinue
    if ($p.NetCfgInstanceId -and ($guids -contains $p.NetCfgInstanceId)) {
        New-ItemProperty $k.PSPath -Name PnPCapabilities -Value 24 -PropertyType DWord -Force | Out-Null; $n++
    }
}
Ghi "Da tat tiet kiem dien tren $n card mang (co hieu luc sau khi khoi dong lai)"
foreach ($m in 'setacvalueindex', 'setdcvalueindex') {
    $r = Lenh "powercfg /$m SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0"
    if ($r -ne 0) { throw "powercfg USB selective suspend loi ma $r" }
}
Lenh 'powercfg /setactive SCHEME_CURRENT' | Out-Null
''',
r'''$g = @(Get-NetAdapter -Physical | ForEach-Object { $_.InterfaceGuid }); $ok = $true
foreach ($k in Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}') { $p = Get-ItemProperty $k.PSPath; if ($p.NetCfgInstanceId -and ($g -contains $p.NetCfgInstanceId) -and $p.PnPCapabilities -ne 24) { $ok = $false } }
$q = (cmd /c 'powercfg /q SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226' | Out-String)
$ok -and ($q -match 'AC Power Setting Index: 0x00000000')''',
reboot="Khong (card mang co hieu luc sau khi khoi dong lai)")

sc("19-bien-ban-ban-giao", "Bien ban ban giao may", "Xuat serial, model, CPU, RAM, o cung, MAC, IP, ban Windows, phan mem va driver vao C:\\ConsolePi\\reports (HTML + CSV)",
r'''
$dir = 'C:\ConsolePi\reports'; New-Item $dir -ItemType Directory -Force | Out-Null
$pc = $env:COMPUTERNAME
$cs = Get-CimInstance Win32_ComputerSystem; $bios = Get-CimInstance Win32_BIOS; $os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$ram = [math]::Round($cs.TotalPhysicalMemory / 1GB, 1)
$disks = @(Get-CimInstance Win32_DiskDrive | ForEach-Object { '{0} ({1} GB)' -f $_.Model, [math]::Round($_.Size / 1GB) })
$nics = @(Get-NetAdapter -Physical -ErrorAction SilentlyContinue | ForEach-Object { '{0}: {1}' -f $_.Name, $_.MacAddress })
$ips = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } | ForEach-Object { $_.IPAddress })
$goc = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*', 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'
$sw = Get-ItemProperty $goc -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -and -not $_.SystemComponent } |
      Select-Object DisplayName, DisplayVersion, Publisher | Sort-Object DisplayName -Unique
$sw | Export-Csv "$dir\phan-mem-$pc.csv" -NoTypeInformation -Encoding UTF8
$drv = Get-CimInstance Win32_PnPSignedDriver -ErrorAction SilentlyContinue | Where-Object { $_.DeviceName } |
       Select-Object DeviceName, DriverProviderName, DriverVersion, DriverDate | Sort-Object DeviceName
$drv | Export-Csv "$dir\driver-$pc.csv" -NoTypeInformation -Encoding UTF8
function MaHtml([string]$s) { [System.Net.WebUtility]::HtmlEncode($s) }
$dong = @(
 @('Ten may', $pc), @('Hang / Model', "$($cs.Manufacturer) $($cs.Model)"), @('Serial', $bios.SerialNumber), @('BIOS', "$($bios.SMBIOSBIOSVersion)"),
 @('CPU', $cpu.Name.Trim()), @('RAM', "$ram GB"), @('O cung', ($disks -join '; ')), @('Card mang (MAC)', ($nics -join '; ')),
 @('Dia chi IP', ($ips -join ', ')), @('Windows', "$($os.Caption) $($os.Version) build $($os.BuildNumber)"),
 @('Ngay cai', $os.InstallDate.ToString('dd/MM/yyyy HH:mm')), @('So phan mem', "$(@($sw).Count)"), @('So driver', "$(@($drv).Count)"),
 @('Lap bao cao', (Get-Date).ToString('dd/MM/yyyy HH:mm')))
$h = "<!doctype html><meta charset=utf-8><title>Ban giao may $(MaHtml $pc)</title><style>body{font-family:Segoe UI,sans-serif;margin:24px}td,th{border:1px solid #ccc;padding:6px 10px;text-align:left}table{border-collapse:collapse}</style><h2>Bien ban ban giao may $(MaHtml $pc)</h2><table>"
foreach ($d in $dong) { $h += "<tr><th>$(MaHtml $d[0])</th><td>$(MaHtml ([string]$d[1]))</td></tr>" }
$h += "</table><h3>Phan mem da cai</h3><table><tr><th>Ten</th><th>Phien ban</th><th>Hang</th></tr>"
foreach ($s in $sw) { $h += "<tr><td>$(MaHtml $s.DisplayName)</td><td>$(MaHtml $s.DisplayVersion)</td><td>$(MaHtml $s.Publisher)</td></tr>" }
$h += '</table>'
[IO.File]::WriteAllText("$dir\ban-giao-$pc.html", $h, (New-Object Text.UTF8Encoding($true)))
Ghi "Da ghi bien ban: $dir\ban-giao-$pc.html"
''',
r'''$pc = $env:COMPUTERNAME; (Test-Path "C:\ConsolePi\reports\ban-giao-$pc.html") -and ((Get-Content -Raw "C:\ConsolePi\reports\ban-giao-$pc.html") -match $pc) -and (@(Import-Csv "C:\ConsolePi\reports\phan-mem-$pc.csv").Count -gt 0)''',
undo="Xoa file trong C:\\ConsolePi\\reports")

sc("20-suc-khoe-o-cung", "Suc khoe o cung ban dau", "Ghi tinh trang o cung (SMART), RAM luc cai may vao C:\\ConsolePi\\reports. Phat hien o cung xau cua may cu",
r'''
$dir = 'C:\ConsolePi\reports'; New-Item $dir -ItemType Directory -Force | Out-Null
$o = New-Object System.Collections.Generic.List[string]
$o.Add("May: $env:COMPUTERNAME   Ngay: $(Get-Date -Format 'dd/MM/yyyy HH:mm')")
$xau = $false
foreach ($d in Get-PhysicalDisk -ErrorAction SilentlyContinue) {
    $o.Add(("O: {0} | {1} | {2} GB | HealthStatus={3} | Operational={4}" -f $d.FriendlyName, $d.MediaType, [math]::Round($d.Size / 1GB), $d.HealthStatus, ($d.OperationalStatus -join ',')))
    if ($d.HealthStatus -ne 'Healthy') { $xau = $true }
    $r = $null; try { $r = $d | Get-StorageReliabilityCounter -ErrorAction Stop } catch { }
    if ($r) { $o.Add(("   Nhiet do={0}C  Hao mon={1}%  Gio chay={2}  Loi doc={3}  Loi ghi={4}" -f $r.Temperature, $r.Wear, $r.PowerOnHours, $r.ReadErrorsTotal, $r.WriteErrorsTotal)) }
}
foreach ($m in Get-CimInstance Win32_PhysicalMemory -ErrorAction SilentlyContinue) { $o.Add(("RAM: {0} GB {1} MHz {2}" -f [math]::Round($m.Capacity / 1GB), $m.Speed, $m.Manufacturer)) }
if ($xau) { $o.Add('CANH BAO: co o cung khong o trang thai Healthy - nen kiem tra/thay'); Ghi 'CANH BAO: co o cung khong Healthy' }
$o | Out-File "$dir\suc-khoe-o-cung-$env:COMPUTERNAME.txt" -Encoding UTF8
''',
r'''(Get-Content -Raw "C:\ConsolePi\reports\suc-khoe-o-cung-$env:COMPUTERNAME.txt") -match 'HealthStatus' ''',
undo="Xoa file bao cao")

sc("21-tat-remote-assistance", "Tat Remote Assistance", "Tat Windows Remote Assistance (moi nho). Remote Desktop khong bi anh huong",
r'''
Dat 'HKLM:\SYSTEM\CurrentControlSet\Control\Remote Assistance' 'fAllowToGetHelp' 0
Dat 'HKLM:\SYSTEM\CurrentControlSet\Control\Remote Assistance' 'fAllowFullControl' 0
try { Get-NetFirewallRule -Group '@FirewallAPI.dll,-33002' -ErrorAction Stop | Disable-NetFirewallRule } catch { Ghi 'Khong thay nhom rule firewall Remote Assistance' }
''',
r'''(V 'HKLM:\SYSTEM\CurrentControlSet\Control\Remote Assistance' 'fAllowToGetHelp') -eq 0''',
undo="Dat fAllowToGetHelp = 1")

sc("22-bat-openssh-server", "Bat OpenSSH Server", "Cai (neu chua co) va bat OpenSSH Server, tu chay cung Windows, mo cong 22",
r'''
if ($Build -lt 17763) { BoQua 'Windows qua cu, khong co OpenSSH Server' }
$cap = Get-WindowsCapability -Online -Name 'OpenSSH.Server*' -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $cap) { throw 'Khong tim thay goi OpenSSH.Server (can mang/Windows Update)' }
if ($cap.State -ne 'Installed') { Add-WindowsCapability -Online -Name $cap.Name | Out-Null; Ghi 'Da cai OpenSSH Server' }
Set-Service sshd -StartupType Automatic
if ((Get-Service sshd).Status -ne 'Running') { Start-Service sshd }
if (-not (Get-NetFirewallRule -Name 'ConsolePi-sshd' -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -Name 'ConsolePi-sshd' -DisplayName 'OpenSSH Server (ConsolePi)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 | Out-Null
}
''',
r'''$s = Get-Service sshd; $s -and $s.StartType -eq 'Automatic' -and $s.Status -eq 'Running' ''',
net="Co (neu OpenSSH chua co san)", undo="Stop-Service sshd; Set-Service sshd -StartupType Disabled")

sc("23-bat-chia-se-rieng-tu", "Bat chia se mang rieng tu", "Bat Network Discovery va chia se file/may in CHI cho mang Private/Domain (khong mo cho mang Public)",
r'''
$nhom = '@FirewallAPI.dll,-32752', '@FirewallAPI.dll,-28502'
$n = 0
foreach ($g in $nhom) {
    foreach ($r in Get-NetFirewallRule -Group $g -ErrorAction SilentlyContinue) {
        if (([string]$r.Profile) -notmatch 'Public|Any') { Set-NetFirewallRule -Name $r.Name -Enabled True; $n++ }
    }
}
foreach ($sv in 'fdPHost', 'FDResPub', 'SSDPSRV', 'upnphost') {
    if (Get-Service $sv -ErrorAction SilentlyContinue) { Set-Service $sv -StartupType Automatic; Start-Service $sv -ErrorAction SilentlyContinue }
}
Ghi "Da bat $n rule firewall (khong gom Public)"
''',
r'''$bad = 0; foreach ($g in '@FirewallAPI.dll,-32752', '@FirewallAPI.dll,-28502') { foreach ($r in Get-NetFirewallRule -Group $g) { if (([string]$r.Profile) -notmatch 'Public|Any' -and $r.Enabled -ne 'True') { $bad++ } } }
$bad -eq 0 -and (Get-Service fdPHost).StartType -eq 'Automatic' ''',
undo="Disable-NetFirewallRule -Group '@FirewallAPI.dll,-32752'")

sc("24-mang-private", "Dat mang hien tai la Private", "Mang dang Public thi doi sang Private (mang domain giu nguyen)",
r'''
foreach ($p in Get-NetConnectionProfile -ErrorAction SilentlyContinue) {
    if ($p.NetworkCategory -eq 'Public') { Set-NetConnectionProfile -InterfaceIndex $p.InterfaceIndex -NetworkCategory Private; Ghi "Doi $($p.Name) sang Private" }
}
''',
r'''-not (@(Get-NetConnectionProfile | Where-Object { $_.NetworkCategory -eq 'Public' }))''',
undo="Set-NetConnectionProfile -NetworkCategory Public")

sc("25-bat-telnet-tftp", "Bat Telnet va TFTP client", "Bat 2 tinh nang Windows Telnet Client va TFTP Client (cho dan mang cau hinh thiet bi)",
r'''
foreach ($f in 'TelnetClient', 'TFTP') {
    $ft = Get-WindowsOptionalFeature -Online -FeatureName $f -ErrorAction SilentlyContinue
    if (-not $ft) { Ghi "Khong co tinh nang $f tren ban Windows nay"; continue }
    if ($ft.State -ne 'Enabled') { Enable-WindowsOptionalFeature -Online -FeatureName $f -NoRestart | Out-Null; Ghi "Da bat $f" }
}
''',
r'''$bad = 0; foreach ($f in 'TelnetClient', 'TFTP') { $ft = Get-WindowsOptionalFeature -Online -FeatureName $f; if ($ft -and $ft.State -ne 'Enabled') { $bad++ } }; $bad -eq 0''',
undo="Disable-WindowsOptionalFeature -Online -FeatureName TelnetClient")
