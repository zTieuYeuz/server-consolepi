from gen_core import sc
EXP = r'Software\Microsoft\Windows\CurrentVersion\Explorer'
ADV = EXP + r'\Advanced'
POLEXP = r'Software\Microsoft\Windows\CurrentVersion\Policies\Explorer'

sc("26-tat-delivery-optimization", "Tat Delivery Optimization", "Windows Update chi tai tu Microsoft, khong chia se bang thong len/xuong cho may khac",
r'''
Dat 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization' 'DODownloadMode' 0
''', r'''(V 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization' 'DODownloadMode') -eq 0''')

sc("27-mat-khau-khong-het-han", "Mat khau local khong het han", "Cac tai khoan local dang bat khong bi bat doi mat khau dinh ky (tai khoan domain khong bi anh huong)",
r'''
Lenh 'net accounts /maxpwage:unlimited' | Out-Null
foreach ($u in Get-LocalUser | Where-Object { $_.Enabled }) { Set-LocalUser -Name $u.Name -PasswordNeverExpires $true }
''', r'''-not (@(Get-LocalUser | Where-Object { $_.Enabled -and $_.PasswordExpires }))''',
undo="net accounts /maxpwage:42")

sc("28-khong-doi-mat-khau-khi-thuc", "Khong doi mat khau khi thuc may", "Khong yeu cau nhap lai mat khau khi may thuc day tu ngu/tat man hinh (ha thap bao mat: chi dung cho may de ban/van phong)",
r'''
$pol = 'HKLM:\SOFTWARE\Policies\Microsoft\Power\PowerSettings\0e796bdb-100d-47d6-a2d5-f7d2daa51f51'
Dat $pol 'ACSettingIndex' 0
Dat $pol 'DCSettingIndex' 0
foreach ($m in 'setacvalueindex', 'setdcvalueindex') { Lenh "powercfg /$m SCHEME_CURRENT SUB_NONE 0e796bdb-100d-47d6-a2d5-f7d2daa51f51 0" | Out-Null }
Lenh 'powercfg /setactive SCHEME_CURRENT' | Out-Null
''', r'''$pol = 'HKLM:\SOFTWARE\Policies\Microsoft\Power\PowerSettings\0e796bdb-100d-47d6-a2d5-f7d2daa51f51'; (V $pol 'ACSettingIndex') -eq 0 -and (V $pol 'DCSettingIndex') -eq 0''',
undo="Xoa khoa chinh sach Power\\PowerSettings\\0e796bdb-...")

sc("29-bat-defender-realtime", "Bat Defender real-time", "Dam bao Microsoft Defender bat bao ve thoi gian thuc. Neu may dung phan mem diet virus khac thi bo qua",
r'''
try { $st = Get-MpComputerStatus -ErrorAction Stop } catch { BoQua 'Defender khong chay (co the dang dung phan mem diet virus khac)' }
if (-not $st.AMServiceEnabled) { BoQua 'Defender khong bat (phan mem diet virus khac dang quan ly)' }
foreach ($k in 'HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender', 'HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection') {
    foreach ($n in 'DisableAntiSpyware', 'DisableRealtimeMonitoring') { Remove-ItemProperty -LiteralPath $k -Name $n -ErrorAction SilentlyContinue }
}
Set-MpPreference -DisableRealtimeMonitoring $false
''', r'''try { (Get-MpPreference -ErrorAction Stop).DisableRealtimeMonitoring -eq $false } catch { $true }''')

sc("30-bat-firewall", "Bat Windows Firewall", "Dam bao Firewall bat o ca 3 profile (Domain, Private, Public)",
r'''
Set-NetFirewallProfile -Profile Domain, Private, Public -Enabled True
''', r'''-not (@(Get-NetFirewallProfile | Where-Object { $_.Enabled -ne 'True' }))''',
undo="Set-NetFirewallProfile -Enabled False (khong nen)")

sc("31-tat-autorun-autoplay", "Tat AutoRun va AutoPlay", "USB/dia cắm vao khong tu chay file va khong hien AutoPlay (chong lay virus qua USB)",
r'''
Dat 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer' 'NoDriveTypeAutoRun' 255
''', r'''(V 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer' 'NoDriveTypeAutoRun') -eq 255 -and (V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\AutoplayHandlers' 'DisableAutoplay') -eq 1''',
user=[(EXP + r'\AutoplayHandlers', 'DisableAutoplay', 1, 'DWord')])

sc("32-tat-smbv1", "Tat SMBv1", "Tat giao thuc SMBv1 cu va nhieu lo hong (client + server)",
r'''
try { Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force -Confirm:$false } catch { Ghi "Khong tat duoc SMB1 server: $($_.Exception.Message)" }
$ft = Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -ErrorAction SilentlyContinue
if ($ft -and $ft.State -eq 'Enabled') { Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart | Out-Null; Ghi 'Da tat tinh nang SMB1Protocol' }
''', r'''(Get-SmbServerConfiguration).EnableSMB1Protocol -eq $false''',
undo="Set-SmbServerConfiguration -EnableSMB1Protocol $true")

sc("33-hien-thong-tin-dang-nhap", "Hien thong tin chi tiet khi dang nhap", "Man hinh 'Dang chuan bi...' hien ro Windows dang lam gi (de chan doan may khoi dong cham)",
r'''
Dat 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' 'VerboseStatus' 1
''', r'''(V 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' 'VerboseStatus') -eq 1''')

sc("34-tat-error-reporting", "Tat Windows Error Reporting", "Windows khong gui bao cao loi ve Microsoft va khong hien hop thoai bao loi",
r'''
Dat 'HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting' 'Disabled' 1
Dat 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Windows Error Reporting' 'Disabled' 1
if (Get-Service WerSvc -ErrorAction SilentlyContinue) { Stop-Service WerSvc -Force -ErrorAction SilentlyContinue; Set-Service WerSvc -StartupType Disabled }
''', r'''(V 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Windows Error Reporting' 'Disabled') -eq 1''',
undo="Xoa 2 khoa Disabled va dat WerSvc ve Manual")

sc("35-chan-driver-qua-update", "Chan Windows Update tu cai driver", "Windows Update khong tu thay driver da cai san (tranh vo driver chinh hang)",
r'''
Dat 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate' 'ExcludeWUDriversInQualityUpdate' 1
''', r'''(V 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate' 'ExcludeWUDriversInQualityUpdate') -eq 1''')

sc("36-dat-mo-ta-may", "Dat mo ta may = Model + Serial", "Ghi mo ta may (hien trong mang/AD) dang 'Hang Model | SN serial', toi da 48 ky tu",
r'''
$cs = Get-CimInstance Win32_ComputerSystem; $b = Get-CimInstance Win32_BIOS
$sn = if ($b.SerialNumber) { $b.SerialNumber.Trim() } else { 'N/A' }
$mt = ("{0} {1} | SN {2}" -f $cs.Manufacturer.Trim(), $cs.Model.Trim(), $sn)
if ($mt.Length -gt 48) { $mt = $mt.Substring(0, 48) }
$os = Get-CimInstance Win32_OperatingSystem
Set-CimInstance -InputObject $os -Property @{ Description = $mt }
Ghi "Mo ta may: $mt"
''', r'''(Get-CimInstance Win32_OperatingSystem).Description -match 'SN ' ''',
undo="Set-CimInstance ... Description = ''")

sc("37-bat-sandbox", "Bat Windows Sandbox", "Bat tinh nang Windows Sandbox (Windows Pro/Enterprise, can ao hoa). Ban Home se duoc bo qua. CHAY CUOI KICH BAN",
r'''
$ft = Get-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM -ErrorAction SilentlyContinue
if (-not $ft) { BoQua 'Ban Windows nay khong co Windows Sandbox (can Pro/Enterprise)' }
if ($ft.State -ne 'Enabled') { Enable-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM -All -NoRestart | Out-Null; Ghi 'Da bat Windows Sandbox (can khoi dong lai)' }
''', r'''$ft = Get-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM; (-not $ft) -or $ft.State -in 'Enabled', 'EnablePending' ''',
reboot="Co", undo="Disable-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM", cuoi=True)

sc("38-bat-hyperv", "Bat Hyper-V", "Bat Hyper-V (Windows Pro/Enterprise, can CPU ao hoa). Ban Home se duoc bo qua. CHAY CUOI KICH BAN",
r'''
$ft = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -ErrorAction SilentlyContinue
if (-not $ft) { BoQua 'Ban Windows nay khong co Hyper-V (can Pro/Enterprise)' }
if ($ft.State -ne 'Enabled') { Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -All -NoRestart | Out-Null; Ghi 'Da bat Hyper-V (can khoi dong lai)' }
''', r'''$ft = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All; (-not $ft) -or $ft.State -in 'Enabled', 'EnablePending' ''',
reboot="Co", undo="Disable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All", cuoi=True)

sc("39-tat-tac-vu-theo-doi", "Tat tac vu theo doi", "Tat cac tac vu thu thap du lieu trong Task Scheduler (Compatibility Appraiser, CEIP...)",
r'''
$ds = @(
 @('\Microsoft\Windows\Application Experience\', 'Microsoft Compatibility Appraiser'),
 @('\Microsoft\Windows\Application Experience\', 'ProgramDataUpdater'),
 @('\Microsoft\Windows\Customer Experience Improvement Program\', 'Consolidator'),
 @('\Microsoft\Windows\Customer Experience Improvement Program\', 'UsbCeip'),
 @('\Microsoft\Windows\Customer Experience Improvement Program\', 'KernelCeipTask'))
$n = 0
foreach ($d in $ds) {
    $t = Get-ScheduledTask -TaskPath $d[0] -TaskName $d[1] -ErrorAction SilentlyContinue
    if ($t) {
        if ($t.State -ne 'Disabled') {
            Stop-ScheduledTask -TaskPath $d[0] -TaskName $d[1] -ErrorAction SilentlyContinue
            Disable-ScheduledTask -TaskPath $d[0] -TaskName $d[1] | Out-Null
            Start-Sleep 2
            if ((Get-ScheduledTask -TaskPath $d[0] -TaskName $d[1]).State -ne 'Disabled') { Start-Sleep 5; Disable-ScheduledTask -TaskPath $d[0] -TaskName $d[1] | Out-Null }
        }
        $n++
    }
}
Ghi "Da tat $n tac vu"
''', r'''$ds = @(@('\Microsoft\Windows\Application Experience\','Microsoft Compatibility Appraiser'),@('\Microsoft\Windows\Application Experience\','ProgramDataUpdater'),@('\Microsoft\Windows\Customer Experience Improvement Program\','Consolidator'),@('\Microsoft\Windows\Customer Experience Improvement Program\','UsbCeip'),@('\Microsoft\Windows\Customer Experience Improvement Program\','KernelCeipTask'))
$bad = 0; foreach ($d in $ds) { $t = Get-ScheduledTask -TaskPath $d[0] -TaskName $d[1]; if ($t -and $t.State -ne 'Disabled') { $bad++ } }; $bad -eq 0''',
undo="Enable-ScheduledTask cho tung tac vu")

sc("40-tat-consumer-features", "Tat Consumer Features", "Khong tu cai app/game goi y khi dang nhap tai khoan Microsoft (muc chinh sach may)",
r'''
Dat 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\CloudContent' 'DisableWindowsConsumerFeatures' 1
''', r'''(V 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\CloudContent' 'DisableWindowsConsumerFeatures') -eq 1''')

sc("41-tat-welcome-experience", "Tat man hinh chao mung sau cap nhat", "Khong hien 'Hoan tat thiet lap may' va trang chao mung sau moi ban cap nhat",
"", r'''(V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\UserProfileEngagement' 'ScoobeSystemSettingEnabled') -eq 0''',
user=[(r'Software\Microsoft\Windows\CurrentVersion\UserProfileEngagement', 'ScoobeSystemSettingEnabled', 0, 'DWord'),
      (r'Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager', 'SubscribedContent-310093Enabled', 0, 'DWord')])

sc("42-tat-hello-pin", "Tat yeu cau tao PIN Windows Hello", "Khong hien man hinh bat tao PIN/Windows Hello khi dang nhap lan dau",
r'''
Dat 'HKLM:\SOFTWARE\Policies\Microsoft\PassportForWork' 'Enabled' 0
Dat 'HKLM:\SOFTWARE\Policies\Microsoft\PassportForWork' 'DisablePostLogonProvisioning' 1
''', r'''(V 'HKLM:\SOFTWARE\Policies\Microsoft\PassportForWork' 'Enabled') -eq 0''',
undo="Xoa khoa chinh sach PassportForWork")

sc("43-tat-meetnow-people-ink", "Tat Meet Now, People, Ink tren taskbar", "An nut Meet Now, danh ba People va Windows Ink Workspace khoi thanh tac vu",
"", r'''(V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer' 'HideSCAMeetNow') -eq 1''',
user=[(POLEXP, 'HideSCAMeetNow', 1, 'DWord'), (ADV + r'\People', 'PeopleBand', 0, 'DWord'),
      (r'Software\Microsoft\Windows\CurrentVersion\PenWorkspace', 'PenWorkspaceButtonDesiredVisibility', 0, 'DWord')])

sc("44-dong-ho-hien-giay", "Dong ho hien giay", "Dong ho tren taskbar hien ca giay",
"", r'''(V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' 'ShowSecondsInSystemClock') -eq 1''',
user=[(ADV, 'ShowSecondsInSystemClock', 1, 'DWord')])

sc("45-control-panel-icon-nho", "Control Panel xem bieu tuong nho", "Control Panel mo san o dang All items + Small icons",
"", r'''(V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\ControlPanel' 'AllItemsIconView') -eq 1''',
user=[(EXP + r'\ControlPanel', 'AllItemsIconView', 1, 'DWord'), (EXP + r'\ControlPanel', 'StartupPage', 1, 'DWord')])

sc("46-explorer-duong-dan-checkbox", "Explorer hien duong dan day du va o chon file", "Thanh tieu de hien duong dan day du; hien o tick de chon nhieu file",
"", r'''(V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\CabinetState' 'FullPath') -eq 1 -and (V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' 'AutoCheckSelect') -eq 1''',
user=[(EXP + r'\CabinetState', 'FullPath', 1, 'DWord'), (ADV, 'AutoCheckSelect', 1, 'DWord')])

sc("47-tat-file-gan-day", "Tat 'file gan day' trong Quick Access", "Explorer khong hien file mo gan day va thu muc thuong dung (rieng tu hon)",
"", r'''(V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer' 'ShowRecent') -eq 0 -and (V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer' 'ShowFrequent') -eq 0''',
user=[(EXP, 'ShowRecent', 0, 'DWord'), (EXP, 'ShowFrequent', 0, 'DWord')])

sc("48-enable-linked-connections", "Bat EnableLinkedConnections", "O mang da map van hien khi chay chuong trinh bang quyen Administrator (co hieu luc sau khoi dong lai)",
r'''
Dat 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' 'EnableLinkedConnections' 1
''', r'''(V 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' 'EnableLinkedConnections') -eq 1''')

sc("49-hien-phien-ban-desktop", "Hien phien ban Windows tren Desktop", "Goc phai desktop hien ban Windows + build (de IT nhin la biet)",
"", r'''(V 'HKCU:\Control Panel\Desktop' 'PaintDesktopVersion') -eq 1''',
user=[(r'Control Panel\Desktop', 'PaintDesktopVersion', 1, 'DWord')])

sc("50-menu-mo-cmd-tai-day", "Them 'Mo CMD/PowerShell tai day' vao menu chuot phai", "Chuot phai vao nen thu muc: Open Command Prompt here / Open PowerShell here",
r'''
$goc = 'HKLM:\SOFTWARE\Classes\Directory\Background\shell'
Dat "$goc\ConsolePi_CMD" 'MUIVerb' 'Open Command Prompt here' 'String'
Dat "$goc\ConsolePi_CMD" 'Icon' 'cmd.exe' 'String'
Dat "$goc\ConsolePi_CMD\command" '(default)' 'cmd.exe /s /k pushd "%V"' 'String'
Dat "$goc\ConsolePi_PS" 'MUIVerb' 'Open PowerShell here' 'String'
Dat "$goc\ConsolePi_PS" 'Icon' 'powershell.exe' 'String'
Dat "$goc\ConsolePi_PS\command" '(default)' "powershell.exe -NoExit -Command Set-Location -LiteralPath '%V'" 'String'
''', r'''((Get-Item 'HKLM:\SOFTWARE\Classes\Directory\Background\shell\ConsolePi_CMD\command').GetValue('')) -match 'pushd' -and ((Get-Item 'HKLM:\SOFTWARE\Classes\Directory\Background\shell\ConsolePi_PS\command').GetValue('')) -match 'Set-Location' ''',
undo="Xoa khoa ConsolePi_CMD va ConsolePi_PS")
