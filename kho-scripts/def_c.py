from gen_core import sc
EXP = r'Software\Microsoft\Windows\CurrentVersion\Explorer'
ADV = EXP + r'\Advanced'
SVC_DIS = r'''
$n = 0
foreach ($ten in @(%s)) {
    if (Get-Service $ten -ErrorAction SilentlyContinue) {
        Stop-Service $ten -Force -ErrorAction SilentlyContinue
        Set-Service $ten -StartupType Disabled
        $n++
    }
}
Ghi "Da tat $n dich vu"
'''
SVC_CHK = r'''-not (@(%s | ForEach-Object { Get-Service $_ } | Where-Object { $_.StartType -ne 'Disabled' }))'''
DEF_MP = r'''
try { $st = Get-MpComputerStatus -ErrorAction Stop } catch { BoQua 'Defender khong chay (co the dang dung phan mem diet virus khac)' }
if (-not $st.AMServiceEnabled) { BoQua 'Defender khong bat (phan mem diet virus khac dang quan ly)' }
'''
def svc(lst): return ", ".join("'%s'" % x for x in lst)

# ---------------- Rieng tu (51-58)
sc("51-tat-copilot", "Tat Copilot", "Tat Windows Copilot (chinh sach may + nguoi dung) va an nut Copilot tren taskbar",
r'''
Dat 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot' 'TurnOffWindowsCopilot' 1
''', r'''(V 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot' 'TurnOffWindowsCopilot') -eq 1 -and (V 'HKCU:\Software\Policies\Microsoft\Windows\WindowsCopilot' 'TurnOffWindowsCopilot') -eq 1''',
user=[(r'Software\Policies\Microsoft\Windows\WindowsCopilot', 'TurnOffWindowsCopilot', 1, 'DWord'), (ADV, 'ShowCopilotButton', 0, 'DWord')])

sc("52-tat-recall-ai", "Tat Recall va phan tich du lieu AI", "Tat tinh nang chup/phan tich hoat dong bang AI (Windows Recall, ban Windows 11 moi) bang chinh sach",
r'''
Dat 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsAI' 'DisableAIDataAnalysis' 1
''', r'''(V 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsAI' 'DisableAIDataAnalysis') -eq 1 -and (V 'HKCU:\Software\Policies\Microsoft\Windows\WindowsAI' 'DisableAIDataAnalysis') -eq 1''',
user=[(r'Software\Policies\Microsoft\Windows\WindowsAI', 'DisableAIDataAnalysis', 1, 'DWord')])

sc("53-tat-advertising-id", "Tat Advertising ID", "Ung dung khong dung ma quang cao rieng cua nguoi dung de nham muc tieu",
r'''
Dat 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\AdvertisingInfo' 'DisabledByGroupPolicy' 1
''', r'''(V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo' 'Enabled') -eq 0 -and (V 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\AdvertisingInfo' 'DisabledByGroupPolicy') -eq 1''',
user=[(r'Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo', 'Enabled', 0, 'DWord')])

sc("54-tat-activity-history", "Tat Activity History", "Tat lich su hoat dong (Timeline) - khong ghi va khong tai len Microsoft",
r'''
$k = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\System'
Dat $k 'EnableActivityFeed' 0
Dat $k 'PublishUserActivities' 0
Dat $k 'UploadUserActivities' 0
''', r'''$k = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\System'; (V $k 'EnableActivityFeed') -eq 0 -and (V $k 'UploadUserActivities') -eq 0''')

sc("55-tat-input-personalization", "Tat thu thap du lieu go phim va viet tay", "Windows khong thu thap thong tin go phim, viet tay, danh ba de ca nhan hoa",
"", r'''(V 'HKCU:\Software\Microsoft\InputPersonalization' 'RestrictImplicitTextCollection') -eq 1 -and (V 'HKCU:\Software\Microsoft\Personalization\Settings' 'AcceptedPrivacyPolicy') -eq 0''',
user=[(r'Software\Microsoft\InputPersonalization', 'RestrictImplicitTextCollection', 1, 'DWord'),
      (r'Software\Microsoft\InputPersonalization', 'RestrictImplicitInkCollection', 1, 'DWord'),
      (r'Software\Microsoft\InputPersonalization\TrainedDataStore', 'HarvestContacts', 0, 'DWord'),
      (r'Software\Microsoft\Personalization\Settings', 'AcceptedPrivacyPolicy', 0, 'DWord')])

sc("56-tat-feedback-prompts", "Tat hoi y kien Windows", "Windows khong hien thong bao xin y kien/khao sat nguoi dung",
r'''
Dat 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection' 'DoNotShowFeedbackNotifications' 1
''', r'''(V 'HKCU:\Software\Microsoft\Siuf\Rules' 'NumberOfSIUFInPeriod') -eq 0 -and (V 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection' 'DoNotShowFeedbackNotifications') -eq 1''',
user=[(r'Software\Microsoft\Siuf\Rules', 'NumberOfSIUFInPeriod', 0, 'DWord')])

sc("57-tat-tailored-experiences", "Tat trai nghiem ca nhan hoa theo du lieu chan doan", "Khong de Microsoft dung du lieu chan doan de goi y; tat nhan dien giong noi truc tuyen",
"", r'''(V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Privacy' 'TailoredExperiencesWithDiagnosticDataEnabled') -eq 0 -and (V 'HKCU:\Software\Microsoft\Speech_OneCore\Settings\OnlineSpeechPrivacy' 'HasAccepted') -eq 0''',
user=[(r'Software\Microsoft\Windows\CurrentVersion\Privacy', 'TailoredExperiencesWithDiagnosticDataEnabled', 0, 'DWord'),
      (r'Software\Microsoft\Speech_OneCore\Settings\OnlineSpeechPrivacy', 'HasAccepted', 0, 'DWord')])

sc("58-tat-dich-vu-diagtrack", "Tat dich vu DiagTrack va dmwappushservice", "Tat han dich vu thu thap du lieu chan doan (bo sung cho tuy chon giam telemetry)",
SVC_DIS % svc(['DiagTrack', 'dmwappushservice']), SVC_CHK % "@('DiagTrack','dmwappushservice')",
undo="Set-Service DiagTrack -StartupType Automatic")

# ---------------- Giao dien / Start / Explorer (59-67)
sc("59-tat-chat-teams-taskbar", "An nut Chat/Teams tren taskbar", "An bieu tuong Chat (Teams ca nhan) khoi thanh tac vu Windows 11",
"", r'''(V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' 'TaskbarMn') -eq 0''',
user=[(ADV, 'TaskbarMn', 0, 'DWord')])

sc("60-tat-theo-doi-start", "Tat theo doi app va file gan day trong Start", "Start khong hien app/tai lieu moi dung va phan Recommended",
"", r'''(V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' 'Start_TrackDocs') -eq 0 -and (V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' 'Start_TrackProgs') -eq 0''',
user=[(ADV, 'Start_TrackDocs', 0, 'DWord'), (ADV, 'Start_TrackProgs', 0, 'DWord'), (ADV, 'Start_IrisRecommendations', 0, 'DWord')])

sc("61-tat-search-highlights", "Tat Search Highlights", "O tim kiem khong hien hinh/su kien trong ngay (search highlights)",
"", r'''(V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\SearchSettings' 'IsDynamicSearchBoxEnabled') -eq 0''',
user=[(r'Software\Microsoft\Windows\CurrentVersion\SearchSettings', 'IsDynamicSearchBoxEnabled', 0, 'DWord')])

sc("62-tat-aero-shake", "Tat Aero Shake", "Lac cua so khong lam thu nho cac cua so khac (tranh bam nham)",
"", r'''(V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' 'DisallowShaking') -eq 1''',
user=[(ADV, 'DisallowShaking', 1, 'DWord')])

sc("63-explorer-tien-trinh-rieng", "Explorer mo cua so trong tien trinh rieng", "Moi cua so thu muc chay tien trinh rieng - mot cua so treo khong keo ca desktop treo theo",
"", r'''(V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' 'SeparateProcess') -eq 1''',
user=[(ADV, 'SeparateProcess', 1, 'DWord')])

sc("64-tat-thong-bao-sync-explorer", "Tat quang cao dong bo trong Explorer", "Explorer khong hien thong bao/goi y cua dich vu dong bo (OneDrive...)",
"", r'''(V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' 'ShowSyncProviderNotifications') -eq 0''',
user=[(ADV, 'ShowSyncProviderNotifications', 0, 'DWord')])

sc("65-khong-thumbsdb-mang", "Khong tao Thumbs.db tren o mang", "Explorer khong rai file Thumbs.db len thu muc mang chia se",
r'''
Dat 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Explorer' 'DisableThumbsDBOnNetworkFolders' 1
''', r'''(V 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Explorer' 'DisableThumbsDBOnNetworkFolders') -eq 1''')

sc("66-giam-tre-khoi-dong-app", "Giam tre khoi dong chuong trinh", "Bo do tre mac dinh truoc khi chay cac chuong trinh khoi dong cung Windows - vao desktop nhanh hon",
"", r'''(V 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Serialize' 'StartupDelayInMSec') -eq 0''',
user=[(EXP + r'\Serialize', 'StartupDelayInMSec', 0, 'DWord')])

sc("67-tat-may-nhanh", "Tat may nhanh hon", "Giam thoi gian cho dich vu/ung dung treo luc tat may (5 giay thay vi 20 giay)",
r'''
Dat 'HKLM:\SYSTEM\CurrentControlSet\Control' 'WaitToKillServiceTimeout' '5000' 'String'
''', r'''(V 'HKLM:\SYSTEM\CurrentControlSet\Control' 'WaitToKillServiceTimeout') -eq '5000' -and (V 'HKCU:\Control Panel\Desktop' 'WaitToKillAppTimeout') -eq '5000' ''',
user=[(r'Control Panel\Desktop', 'WaitToKillAppTimeout', '5000', 'String'), (r'Control Panel\Desktop', 'HungAppTimeout', '3000', 'String')])

# ---------------- Edge / Office (68-72)
sc("68-edge-khong-hoi-mac-dinh", "Edge khong hoi lam trinh duyet mac dinh", "Edge khong nhac dat lam mac dinh, khong nhap du lieu tu trinh duyet khac, khong hien tab quang cao",
r'''
$k = 'HKLM:\SOFTWARE\Policies\Microsoft\Edge'
Dat $k 'DefaultBrowserSettingEnabled' 0
Dat $k 'AutoImportAtFirstRun' 4
Dat $k 'PromotionalTabsEnabled' 0
Dat $k 'ShowRecommendationsEnabled' 0
''', r'''$k = 'HKLM:\SOFTWARE\Policies\Microsoft\Edge'; (V $k 'DefaultBrowserSettingEnabled') -eq 0 -and (V $k 'PromotionalTabsEnabled') -eq 0''')

sc("69-edge-tat-sidebar-shopping", "Edge tat sidebar, shopping, rewards", "Edge khong hien thanh ben (sidebar), tro ly mua sam, Microsoft Rewards",
r'''
$k = 'HKLM:\SOFTWARE\Policies\Microsoft\Edge'
Dat $k 'HubsSidebarEnabled' 0
Dat $k 'EdgeShoppingAssistantEnabled' 0
Dat $k 'ShowMicrosoftRewards' 0
Dat $k 'SpotlightExperiencesAndRecommendationsEnabled' 0
''', r'''$k = 'HKLM:\SOFTWARE\Policies\Microsoft\Edge'; (V $k 'HubsSidebarEnabled') -eq 0 -and (V $k 'EdgeShoppingAssistantEnabled') -eq 0''')

sc("70-office-tat-first-run", "Office bo man hinh chao lan dau", "Word/Excel/PowerPoint mo la vao thang: tu chap nhan EULA, bo video gioi thieu va cua so tuy chon lan dau. Khong kich hoat ban quyen",
"", r'''(V 'HKCU:\Software\Microsoft\Office\16.0\Registration' 'AcceptAllEulas') -eq 1 -and (V 'HKCU:\Software\Microsoft\Office\16.0\FirstRun' 'BootedRTM') -eq 1''',
user=[(r'Software\Microsoft\Office\16.0\Registration', 'AcceptAllEulas', 1, 'DWord'),
      (r'Software\Microsoft\Office\16.0\Common\General', 'ShownFirstRunOptin', 1, 'DWord'),
      (r'Software\Microsoft\Office\16.0\FirstRun', 'BootedRTM', 1, 'DWord'),
      (r'Software\Microsoft\Office\16.0\FirstRun', 'disablemovie', 1, 'DWord')])

sc("71-office-tat-telemetry", "Office tat telemetry", "Tat gui du lieu su dung/CEIP cua Office ve Microsoft",
"", r'''(V 'HKCU:\Software\Policies\Microsoft\Office\16.0\Common\ClientTelemetry' 'SendTelemetry') -eq 3 -and (V 'HKCU:\Software\Microsoft\Office\Common\ClientTelemetry' 'DisableTelemetry') -eq 1''',
user=[(r'Software\Policies\Microsoft\Office\16.0\Common\ClientTelemetry', 'SendTelemetry', 3, 'DWord'),
      (r'Software\Microsoft\Office\Common\ClientTelemetry', 'DisableTelemetry', 1, 'DWord'),
      (r'Software\Microsoft\Office\16.0\Common', 'QMEnable', 0, 'DWord')])

sc("72-office-luu-may-mac-dinh", "Office luu tren may mac dinh", "Hop thoai Save cua Office mac dinh luu tren may thay vi OneDrive, bo nhac dang nhap OneDrive",
"", r'''(V 'HKCU:\Software\Microsoft\Office\16.0\Common\General' 'PreferCloudSaveLocations') -eq 0 -and (V 'HKCU:\Software\Microsoft\Office\16.0\Common\General' 'SkyDriveSignInOption') -eq 0''',
user=[(r'Software\Microsoft\Office\16.0\Common\General', 'PreferCloudSaveLocations', 0, 'DWord'),
      (r'Software\Microsoft\Office\16.0\Common\General', 'SkyDriveSignInOption', 0, 'DWord')])

# ---------------- Dich vu (73-75)
sc("73-tat-dich-vu-xbox", "Tat dich vu Xbox", "Tat han 4 dich vu Xbox (Auth, GameSave, NetApi, Gip) chay nen khong dung toi",
SVC_DIS % svc(['XblAuthManager', 'XblGameSave', 'XboxNetApiSvc', 'XboxGipSvc']), SVC_CHK % "@('XblAuthManager','XblGameSave','XboxNetApiSvc','XboxGipSvc')",
undo="Set-Service <ten> -StartupType Manual")

sc("74-tat-dich-vu-it-dung", "Tat dich vu it dung", "Tat Fax, Retail Demo, Maps Downloader, Media Player Network Sharing, Windows Insider",
SVC_DIS % svc(['Fax', 'RetailDemo', 'MapsBroker', 'WMPNetworkSvc', 'wisvc']), SVC_CHK % "@('Fax','RetailDemo','MapsBroker','WMPNetworkSvc','wisvc')",
undo="Set-Service <ten> -StartupType Manual")

sc("75-tat-sysmain-neu-ssd", "Tat SysMain (Superfetch) neu o he thong la SSD", "Tren SSD thi Superfetch khong con huu ich; tren o HDD giu nguyen. Tu nhan biet loai o",
r'''
if (-not (Get-Service SysMain -ErrorAction SilentlyContinue)) { BoQua 'Khong co dich vu SysMain' }
$ssd = $false
try {
    $part = Get-Partition -DriveLetter ($env:SystemDrive.Substring(0, 1))
    $dk = Get-PhysicalDisk | Where-Object { $_.DeviceId -eq [string]$part.DiskNumber }
    if ($dk.MediaType -eq 'SSD') { $ssd = $true }
} catch { }
if (-not $ssd) { BoQua 'O he thong khong phai SSD (hoac khong xac dinh duoc) - giu SysMain' }
Stop-Service SysMain -Force -ErrorAction SilentlyContinue
Set-Service SysMain -StartupType Disabled
''', r'''$ssd = $false
try { $part = Get-Partition -DriveLetter ($env:SystemDrive.Substring(0,1)); $dk = Get-PhysicalDisk | Where-Object { $_.DeviceId -eq [string]$part.DiskNumber }; if ($dk.MediaType -eq 'SSD') { $ssd = $true } } catch { }
if ($ssd) { (Get-Service SysMain).StartType -eq 'Disabled' } else { $true }''',
undo="Set-Service SysMain -StartupType Automatic")

# ---------------- Mang (76-82)
sc("76-tat-llmnr", "Tat LLMNR", "Tat phan giai ten da phat (LLMNR) - dong lo hong gia mao ten tren mang noi bo; DNS van hoat dong binh thuong",
r'''
Dat 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient' 'EnableMulticast' 0
''', r'''(V 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient' 'EnableMulticast') -eq 0''')

sc("77-tat-teredo", "Tat Teredo", "Tat duong ham IPv6-qua-IPv4 Teredo (it dung, de lam lo may sau NAT)",
r'''
$r = Lenh 'netsh interface teredo set state disabled'
if ($r -ne 0) { throw "netsh teredo loi ma $r" }
''', r'''(cmd /c 'netsh interface teredo show state' | Out-String) -match 'disabled' ''',
undo="netsh interface teredo set state default")

sc("78-uu-tien-ipv4", "Uu tien IPv4 hon IPv6", "Dat uu tien IPv4 (giu IPv6 hoat dong). Neu da co cau hinh IPv6 san (vd tuy chon Tat IPv6) thi khong ghi de",
r'''
$k = 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters'
$cur = (Get-ItemProperty $k -Name DisabledComponents -ErrorAction SilentlyContinue).DisabledComponents
if ($null -ne $cur) {
    if (($cur -band 0x20) -ne 0) { Ghi 'Da uu tien IPv4 san' } else { BoQua "DisabledComponents da duoc cau hinh ($cur) - khong ghi de" }
} else { Dat $k 'DisabledComponents' 32 }
''', r'''$c = V 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters' 'DisabledComponents'; $null -ne $c''',
reboot="Co hieu luc sau khoi dong lai", undo="Xoa gia tri DisabledComponents")

sc("79-tat-tu-ket-noi-hotspot", "Tat tu ket noi Wi-Fi mo", "Windows khong tu ket noi vao hotspot Wi-Fi mo/chia se (Wi-Fi Sense)",
r'''
Dat 'HKLM:\SOFTWARE\Microsoft\WcmSvc\wifinetworkmanager\config' 'AutoConnectAllowedOEM' 0
''', r'''(V 'HKLM:\SOFTWARE\Microsoft\WcmSvc\wifinetworkmanager\config' 'AutoConnectAllowedOEM') -eq 0''')

sc("80-bat-nla-rdp", "Bat NLA cho Remote Desktop", "Yeu cau xac thuc truoc khi vao Remote Desktop (Network Level Authentication) - an toan hon. Khong tu bat RDP",
r'''
Dat 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' 'UserAuthentication' 1
''', r'''(V 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' 'UserAuthentication') -eq 1''',
undo="UserAuthentication = 0")

sc("81-dam-bao-dong-bo-gio", "Dam bao dong bo gio tu dong", "Dich vu Windows Time chay tu dong cung Windows va dong bo ngay",
r'''
Set-Service w32time -StartupType Automatic
if ((Get-Service w32time).Status -ne 'Running') { Start-Service w32time }
Lenh 'w32tm /resync /nowait' | Out-Null
''', r'''(Get-Service w32time).StartType -eq 'Automatic' -and (Get-Service w32time).Status -eq 'Running' ''')

sc("82-tat-remote-registry", "Tat Remote Registry", "Tat dich vu cho phep sua registry tu xa (rui ro bao mat, hiem khi can)",
SVC_DIS % svc(['RemoteRegistry']), SVC_CHK % "@('RemoteRegistry')", undo="Set-Service RemoteRegistry -StartupType Manual")

# ---------------- Bao mat chinh sach (83-89)
sc("83-khoa-tai-khoan-sai-mat-khau", "Khoa tai khoan khi nhap sai mat khau", "Sai 10 lan thi khoa 15 phut (chong do mat khau). Ap dung cho tai khoan local",
r'''
$r = Lenh 'net accounts /lockoutthreshold:10 /lockoutduration:15 /lockoutwindow:15'
if ($r -ne 0) { throw "net accounts loi ma $r" }
''', r'''(cmd /c 'net accounts' | Out-String) -match '(?m)threshold:\s+10\s*$' ''',
undo="net accounts /lockoutthreshold:0")

sc("84-tat-tai-khoan-guest", "Tat tai khoan Guest", "Dam bao tai khoan Guest (khach) bi tat",
r'''
foreach ($u in Get-LocalUser | Where-Object { $_.SID.Value -like '*-501' -and $_.Enabled }) { Disable-LocalUser -Name $u.Name; Ghi "Da tat $($u.Name)" }
''', r'''-not (@(Get-LocalUser | Where-Object { $_.SID.Value -like '*-501' -and $_.Enabled }))''',
undo="Enable-LocalUser Guest")

sc("85-bat-audit-dang-nhap", "Bat ghi nhat ky dang nhap", "Ghi vao Security log: dang nhap thanh cong/that bai, khoa tai khoan, quan ly tai khoan",
r'''
foreach ($g in '{0CCE9215-69AE-11D9-BED3-505054503030}', '{0CCE9217-69AE-11D9-BED3-505054503030}', '{0CCE9235-69AE-11D9-BED3-505054503030}') {
    $o = Chay "auditpol /set /subcategory:`"$g`" /success:enable /failure:enable"
    if ($script:Ma -ne 0) { throw "auditpol loi ma $($script:Ma): $o" }
}
''', r'''$ok = $true; foreach ($g in '{0CCE9215-69AE-11D9-BED3-505054503030}','{0CCE9217-69AE-11D9-BED3-505054503030}','{0CCE9235-69AE-11D9-BED3-505054503030}') { $o = (auditpol /get /subcategory:"$g" /r | Out-String); if ($o -notmatch 'Success and Failure') { $ok = $false } }; $ok''',
undo="auditpol /set ... /success:disable /failure:disable")

sc("86-tang-event-log", "Tang dung luong Event Log", "Security 128 MB, System va Application 64 MB (mac dinh chi 20 MB - nhat ky bi ghi de qua nhanh)",
r'''
foreach ($kv in @(@('Security', 134217728), @('System', 67108864), @('Application', 67108864))) {
    $r = Lenh "wevtutil sl $($kv[0]) /ms:$($kv[1])"
    if ($r -ne 0) { throw "wevtutil $($kv[0]) loi ma $r" }
}
''', r'''(cmd /c 'wevtutil gl Security' | Out-String) -match 'maxSize: 134217728' -and (cmd /c 'wevtutil gl System' | Out-String) -match 'maxSize: 67108864' ''',
undo="wevtutil sl <log> /ms:20971520")

sc("87-tat-powershell-v2", "Tat PowerShell 2.0", "Go tinh nang PowerShell 2.0 cu (khong co log/bao ve hien dai, hay bi lam dung de ne tranh). PowerShell 5.1 khong bi anh huong",
r'''
$ft = Get-WindowsOptionalFeature -Online -FeatureName MicrosoftWindowsPowerShellV2Root -ErrorAction SilentlyContinue
if (-not $ft) { BoQua 'Ban Windows nay khong co PowerShell 2.0' }
if ($ft.State -notin 'Disabled', 'DisablePending') { Disable-WindowsOptionalFeature -Online -FeatureName MicrosoftWindowsPowerShellV2Root -NoRestart | Out-Null; Ghi 'Da tat PowerShell 2.0' }
''', r'''$ft = Get-WindowsOptionalFeature -Online -FeatureName MicrosoftWindowsPowerShellV2Root; (-not $ft) -or $ft.State -in 'Disabled', 'DisablePending' ''',
undo="Enable-WindowsOptionalFeature -Online -FeatureName MicrosoftWindowsPowerShellV2Root")

sc("88-defender-bat-pua", "Defender bat chan phan mem rac (PUA)", "Defender chan phan mem co the khong mong muon (adware, bundle). May dung phan mem diet virus khac thi bo qua",
DEF_MP + "Set-MpPreference -PUAProtection Enabled\n",
r'''try { $s = Get-MpComputerStatus -ErrorAction Stop; if (-not $s.AMServiceEnabled) { $true } else { (Get-MpPreference).PUAProtection -eq 1 } } catch { $true }''',
undo="Set-MpPreference -PUAProtection Disabled")

sc("89-defender-bat-network-protection", "Defender bat Network Protection", "Chan ket noi toi trang/may chu doc hai. May dung phan mem diet virus khac thi bo qua",
DEF_MP + "Set-MpPreference -EnableNetworkProtection Enabled\n",
r'''try { $s = Get-MpComputerStatus -ErrorAction Stop; if (-not $s.AMServiceEnabled) { $true } else { (Get-MpPreference).EnableNetworkProtection -eq 1 } } catch { $true }''',
undo="Set-MpPreference -EnableNetworkProtection Disabled")

# ---------------- Menu chuot phai (90-91)
CHIAKHOA = r'''
function ChiaKhoa([string]$duong, [string]$ten, [string]$gia) {
    $k = [Microsoft.Win32.Registry]::LocalMachine.CreateSubKey($duong)
    $k.SetValue($ten, $gia)
    $k.Close()
}
'''
sc("90-menu-take-ownership", "Menu chuot phai: Take ownership", "Chuot phai file/thu muc: Take ownership (chiem quyen so huu + cap Full cho Administrators, chay voi quyen admin)",
CHIAKHOA + r'''
foreach ($goc in 'SOFTWARE\Classes\*\shell\runas', 'SOFTWARE\Classes\Directory\shell\runas') {
    ChiaKhoa $goc 'MUIVerb' 'Take ownership'
    ChiaKhoa $goc 'HasLUAShield' ''
    ChiaKhoa $goc 'NoWorkingDirectory' ''
}
ChiaKhoa 'SOFTWARE\Classes\*\shell\runas\command' '' 'cmd.exe /c takeown /f "%1" && icacls "%1" /grant *S-1-5-32-544:F'
ChiaKhoa 'SOFTWARE\Classes\Directory\shell\runas\command' '' 'cmd.exe /c takeown /f "%1" /r /d y && icacls "%1" /grant *S-1-5-32-544:F /t'
''', r'''([Microsoft.Win32.Registry]::LocalMachine.OpenSubKey('SOFTWARE\Classes\*\shell\runas\command').GetValue('')) -match 'takeown' -and ([Microsoft.Win32.Registry]::LocalMachine.OpenSubKey('SOFTWARE\Classes\Directory\shell\runas\command').GetValue('')) -match 'takeown' ''',
undo="Xoa khoa shell\\runas duoi *\\ va Directory\\")

sc("91-menu-mo-bang-notepad", "Menu chuot phai: Open with Notepad", "Chuot phai moi file: Open with Notepad (mo nhanh file khong ro dinh dang)",
CHIAKHOA + r'''
ChiaKhoa 'SOFTWARE\Classes\*\shell\ConsolePi_Notepad' 'MUIVerb' 'Open with Notepad'
ChiaKhoa 'SOFTWARE\Classes\*\shell\ConsolePi_Notepad\command' '' 'notepad.exe "%1"'
''', r'''([Microsoft.Win32.Registry]::LocalMachine.OpenSubKey('SOFTWARE\Classes\*\shell\ConsolePi_Notepad\command').GetValue('')) -match 'notepad' ''',
undo="Xoa khoa ConsolePi_Notepad")

# ---------------- Bao cao / kiem ke (92-99)
REP = r'''
$dir = 'C:\ConsolePi\reports'; New-Item $dir -ItemType Directory -Force | Out-Null
$pc = $env:COMPUTERNAME
'''
sc("92-dong-dau-may", "Dong dau may cai boi Console System", "Ghi dau vet vao registry HKLM\\SOFTWARE\\ConsolePi va file: ngay cai Windows, build, lan dau dong dau (IT/GPO/Intune doc duoc)",
r'''
$k = 'HKLM:\SOFTWARE\ConsolePi'
if (-not (Test-Path $k)) { New-Item $k -Force | Out-Null }
$os = Get-CimInstance Win32_OperatingSystem
Dat $k 'InstalledBy' 'Console System' 'String'
Dat $k 'WindowsInstallDate' $os.InstallDate.ToString('yyyy-MM-dd') 'String'
Dat $k 'WindowsBuild' "$($os.Version)" 'String'
if (-not (Get-ItemProperty $k -Name FirstStamp -ErrorAction SilentlyContinue)) { Dat $k 'FirstStamp' (Get-Date -Format 'yyyy-MM-dd HH:mm') 'String' }
$first = (Get-ItemProperty $k).FirstStamp
"May cai boi Console System`r`nNgay cai Windows: $($os.InstallDate.ToString('dd/MM/yyyy HH:mm'))`r`nBuild: $($os.Version)`r`nDong dau lan dau: $first" |
    Out-File 'C:\ConsolePi\may-cai-boi-console-system.txt' -Encoding UTF8
''', r'''(V 'HKLM:\SOFTWARE\ConsolePi' 'InstalledBy') -eq 'Console System' -and (V 'HKLM:\SOFTWARE\ConsolePi' 'FirstStamp') -and (Test-Path 'C:\ConsolePi\may-cai-boi-console-system.txt')''',
undo="Xoa khoa HKLM\\SOFTWARE\\ConsolePi")

sc("93-ghi-cap-nhat-da-cai", "Ghi danh sach ban cap nhat Windows da cai", "Ghi cac ban cap nhat (KB) da co tren may vao C:\\ConsolePi\\reports\\cap-nhat-<may>.csv",
REP + r'''
$h = @(Get-HotFix -ErrorAction SilentlyContinue | Select-Object HotFixID, Description, InstalledOn, InstalledBy | Sort-Object InstalledOn)
$h | Export-Csv "$dir\cap-nhat-$pc.csv" -NoTypeInformation -Encoding UTF8
Ghi "Ghi $($h.Count) ban cap nhat"
''', r'''Test-Path "C:\ConsolePi\reports\cap-nhat-$env:COMPUTERNAME.csv"''', undo="Xoa file bao cao")

sc("94-ghi-tai-khoan-admin", "Ghi danh sach tai khoan va quyen admin", "Ghi tai khoan local va thanh vien nhom Administrators vao C:\\ConsolePi\\reports (de ra soat bao mat)",
REP + r'''
$o = New-Object System.Collections.Generic.List[string]
$o.Add("May: $pc   Ngay: $(Get-Date -Format 'dd/MM/yyyy HH:mm')")
$o.Add('--- Tai khoan local ---')
foreach ($u in Get-LocalUser) { $o.Add(("{0} | bat={1} | can mat khau={2} | dang nhap cuoi={3}" -f $u.Name, $u.Enabled, $u.PasswordRequired, $u.LastLogon)) }
$g = Get-LocalGroup -SID 'S-1-5-32-544'
$o.Add("--- Thanh vien nhom $($g.Name) ---")
try { foreach ($m in Get-LocalGroupMember -Group $g.Name -ErrorAction Stop) { $o.Add($m.Name) } }
catch { $o.Add('(khong doc duoc bang Get-LocalGroupMember - dung net localgroup)'); (cmd /c "net localgroup `"$($g.Name)`"") | ForEach-Object { $o.Add($_) } }
$o | Out-File "$dir\tai-khoan-$pc.txt" -Encoding UTF8
''', r'''(Get-Content -Raw "C:\ConsolePi\reports\tai-khoan-$env:COMPUTERNAME.txt") -match 'Tai khoan local' ''', undo="Xoa file bao cao")

sc("95-ghi-chuong-trinh-khoi-dong", "Ghi chuong trinh khoi dong cung Windows", "Liet ke muc Run (may + nguoi dung) va thu muc Startup vao C:\\ConsolePi\\reports",
REP + r'''
$o = New-Object System.Collections.Generic.List[string]
foreach ($k in 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run', 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run', 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run') {
    $o.Add("--- $k ---")
    $p = Get-ItemProperty $k -ErrorAction SilentlyContinue
    if ($p) { foreach ($n in $p.PSObject.Properties | Where-Object { $_.Name -notmatch '^PS' }) { $o.Add(("{0} = {1}" -f $n.Name, $n.Value)) } }
}
foreach ($d in "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp", "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup") {
    $o.Add("--- $d ---")
    Get-ChildItem $d -ErrorAction SilentlyContinue | ForEach-Object { $o.Add($_.Name) }
}
$o | Out-File "$dir\khoi-dong-$pc.txt" -Encoding UTF8
''', r'''(Get-Content -Raw "C:\ConsolePi\reports\khoi-dong-$env:COMPUTERNAME.txt") -match 'CurrentVersion.Run' ''', undo="Xoa file bao cao")

sc("96-bao-cao-pin-laptop", "Bao cao pin laptop", "Laptop: tao bao cao pin (dung luong thiet ke so voi hien tai) - bat may cu pin chai. May ban/may ao tu bo qua",
REP + r'''
if (-not (Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue)) { BoQua 'May khong co pin (may ban/may ao)' }
$f = "$dir\bao-cao-pin-$pc.html"
[void](Lenh "powercfg /batteryreport /output `"$f`"")
if (-not (Test-Path $f)) { throw 'powercfg /batteryreport khong tao duoc file' }
''', r'''if (-not (Get-CimInstance Win32_Battery)) { $true } else { Test-Path "C:\ConsolePi\reports\bao-cao-pin-$env:COMPUTERNAME.html" }''', undo="Xoa file bao cao")

sc("97-ghi-ban-quyen-windows", "Ghi trang thai ban quyen Windows", "Ghi trang thai kich hoat Windows (chi doc, KHONG kich hoat gi) vao C:\\ConsolePi\\reports",
REP + r'''
$o = New-Object System.Collections.Generic.List[string]
$o.Add("May: $pc   Ngay: $(Get-Date -Format 'dd/MM/yyyy HH:mm')")
$ten = @{ 0 = 'Unlicensed'; 1 = 'Licensed (da kich hoat)'; 2 = 'OOBGrace'; 3 = 'OOTGrace'; 4 = 'NonGenuineGrace'; 5 = 'Notification'; 6 = 'ExtendedGrace' }
$ds = Get-CimInstance SoftwareLicensingProduct -Filter "ApplicationId='55c92734-d682-4d71-983e-d6ec3f16059f' AND PartialProductKey IS NOT NULL" -ErrorAction SilentlyContinue
if (-not $ds) { $o.Add('LicenseStatus: khong co khoa san pham (chua cai khoa/chua kich hoat)') }
foreach ($l in $ds) { $o.Add(("{0} | {1} | LicenseStatus={2} {3}" -f $l.Name, $l.Description, $l.LicenseStatus, $ten[[int]$l.LicenseStatus])) }
$o | Out-File "$dir\ban-quyen-$pc.txt" -Encoding UTF8
''', r'''(Get-Content -Raw "C:\ConsolePi\reports\ban-quyen-$env:COMPUTERNAME.txt") -match 'LicenseStatus' ''', undo="Xoa file bao cao")

sc("98-ghi-tpm-secureboot-bitlocker", "Ghi TPM, Secure Boot, BitLocker", "Ghi tinh trang TPM, Secure Boot, BitLocker, kieu BIOS/UEFI (de biet may co len duoc Windows 11/ma hoa o khong) vao C:\\ConsolePi\\reports",
REP + r'''
$o = New-Object System.Collections.Generic.List[string]
$o.Add("May: $pc   Ngay: $(Get-Date -Format 'dd/MM/yyyy HH:mm')")
$bcd = (cmd /c 'bcdedit /enum {current}' | Out-String)
$o.Add("Firmware: " + $(if ($bcd -match 'winload\.efi') { 'UEFI' } elseif ($bcd -match 'winload\.exe') { 'BIOS Legacy' } else { 'khong ro' }))
try { $t = Get-Tpm -ErrorAction Stop; $o.Add("TPM: Present=$($t.TpmPresent) Ready=$($t.TpmReady) Enabled=$($t.TpmEnabled)") } catch { $o.Add('TPM: khong doc duoc (khong co TPM hoac khong ho tro)') }
try { $o.Add("SecureBoot: $(Confirm-SecureBootUEFI -ErrorAction Stop)") } catch { $o.Add('SecureBoot: khong ho tro (BIOS Legacy) hoac khong doc duoc') }
try { foreach ($v in Get-BitLockerVolume -ErrorAction Stop) { $o.Add("BitLocker $($v.MountPoint): bao ve=$($v.ProtectionStatus) trang thai=$($v.VolumeStatus)") } } catch { $o.Add('BitLocker: khong doc duoc') }
$o | Out-File "$dir\tpm-secureboot-$pc.txt" -Encoding UTF8
''', r'''(Get-Content -Raw "C:\ConsolePi\reports\tpm-secureboot-$env:COMPUTERNAME.txt") -match 'SecureBoot' ''', undo="Xoa file bao cao")

sc("99-thiet-bi-thieu-driver", "Liet ke thiet bi loi/thieu driver", "Ghi cac thiet bi trong Device Manager dang loi hoac thieu driver vao C:\\ConsolePi\\reports (sau cai may biet ngay thieu gi)",
REP + r'''
$bad = @(Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue | Where-Object { $_.ConfigManagerErrorCode -ne 0 })
$o = New-Object System.Collections.Generic.List[string]
$o.Add("May: $pc   Ngay: $(Get-Date -Format 'dd/MM/yyyy HH:mm')")
if ($bad.Count -eq 0) { $o.Add('Khong co thiet bi nao bao loi.') }
else {
    $o.Add("CANH BAO: $($bad.Count) thiet bi loi/thieu driver:")
    foreach ($d in $bad) { $o.Add(("  {0} | ma loi {1} | {2}" -f $d.Name, $d.ConfigManagerErrorCode, $d.PNPDeviceID)) }
    Ghi "CANH BAO: $($bad.Count) thiet bi loi/thieu driver"
}
$o | Out-File "$dir\thiet-bi-loi-$pc.txt" -Encoding UTF8
''', r'''(Get-Content -Raw "C:\ConsolePi\reports\thiet-bi-loi-$env:COMPUTERNAME.txt") -match 'May:' ''', undo="Xoa file bao cao")

# ---------------- Tinh nang Windows (100)
sc("100-bat-wsl", "Bat tinh nang WSL", "Bat Windows Subsystem for Linux va Virtual Machine Platform (chua cai ban Linux). Can khoi dong lai - dat CUOI kich ban",
r'''
$bat = 0
foreach ($f in 'Microsoft-Windows-Subsystem-Linux', 'VirtualMachinePlatform') {
    $ft = Get-WindowsOptionalFeature -Online -FeatureName $f -ErrorAction SilentlyContinue
    if (-not $ft) { Ghi "Khong co tinh nang $f tren ban Windows nay"; continue }
    if ($ft.State -notin 'Enabled', 'EnablePending') { Enable-WindowsOptionalFeature -Online -FeatureName $f -All -NoRestart | Out-Null; Ghi "Da bat $f (can khoi dong lai)"; $bat++ }
}
''', r'''$bad = 0; foreach ($f in 'Microsoft-Windows-Subsystem-Linux','VirtualMachinePlatform') { $ft = Get-WindowsOptionalFeature -Online -FeatureName $f; if ($ft -and $ft.State -notin 'Enabled','EnablePending') { $bad++ } }; $bad -eq 0''',
reboot="Co", undo="Disable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux", cuoi=True)
