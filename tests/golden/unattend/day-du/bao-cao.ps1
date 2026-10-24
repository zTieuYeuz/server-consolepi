$TEN_KICHBAN = '(chạy trực tiếp, chưa lưu thành kịch bản)'

$MUC = @(
  @{ Nhom='May'; Nhan='Tên máy'; Loai='ps'; Ma={
        $t = (Get-CimInstance Win32_ComputerSystem).Name
        @{ Dat = ($t -eq 'T2-DAYDU'); ChiTiet = $t }
    } },
  @{ Nhom='May'; Nhan='Tài khoản Administrator đã mở'; Loai='ps'; Ma={
            $a = Get-LocalUser -EA SilentlyContinue | Where-Object { $_.SID.Value -like '*-500' }
            if ($a) { @{ Dat = $a.Enabled; ChiTiet = "$($a.Name) - Enabled=$($a.Enabled)" } }
            else { @{ Dat = $false; ChiTiet = 'khong tim thay tai khoan SID -500' } }
        } },
  @{ Nhom='May'; Nhan='Tự động đăng nhập'; Loai='reg'; Duong='HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon'; Ten='AutoAdminLogon'; Gt='1' },
  @{ Nhom='Tùy chọn máy'; Nhan='Bật Remote Desktop'; Loai='reg'; Duong='HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server'; Ten='fDenyTSConnections'; Gt='0' },
  @{ Nhom='Tùy chọn máy'; Nhan='Cho phép ping tới máy này'; Loai='ps'; Ma={
        $r = (netsh advfirewall firewall show rule name="ICMPv4 vao" 2>&1 | Out-String)
        @{ Dat = ($r -notmatch 'No rules match'); ChiTiet = 'luat tuong lua ICMPv4' }
    } },
  @{ Nhom='Tùy chọn máy'; Nhan='Không tự động ngủ / tắt màn hình'; Loai='ps'; Ma={
        $r = (powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE 2>&1 | Out-String)
        if ($r -match 'Current AC Power Setting Index:\s*0x0*([0-9a-f]+)') {
            $giay = [Convert]::ToInt32($matches[1], 16)
            @{ Dat = ($giay -eq 0); ChiTiet = "thoi gian cho = $giay giay" }
        } else { @{ Dat = $false; ChiTiet = 'khong doc duoc powercfg' } }
    } },
  @{ Nhom='Tùy chọn máy'; Nhan='Tắt Fast Startup'; Loai='reg'; Duong='HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Power'; Ten='HiberbootEnabled'; Gt='0' },
  @{ Nhom='Tùy chọn máy'; Nhan='Tắt UAC (hộp hỏi quyền)'; Loai='reg'; Duong='HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System'; Ten='EnableLUA'; Gt='0' },
  @{ Nhom='Tùy chọn máy'; Nhan='Giảm thu thập dữ liệu (telemetry)'; Loai='reg'; Duong='HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection'; Ten='AllowTelemetry'; Gt='0' },
  @{ Nhom='Tùy chọn giao diện (mọi tài khoản)'; Nhan='Hiện phần mở rộng tập tin'; Loai='reg'; Duong='HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced'; Ten='HideFileExt'; Gt='0' },
  @{ Nhom='Tùy chọn giao diện (mọi tài khoản)'; Nhan='Hiện tập tin ẩn'; Loai='reg'; Duong='HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced'; Ten='Hidden'; Gt='1' },
  @{ Nhom='Tùy chọn máy'; Nhan='Không tự mã hoá ổ đĩa (BitLocker)'; Loai='reg'; Duong='HKLM:\SYSTEM\CurrentControlSet\Control\BitLocker'; Ten='PreventDeviceEncryption'; Gt='1' },
  @{ Nhom='Tùy chọn máy'; Nhan='Tắt Windows Update tự động'; Loai='reg'; Duong='HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU'; Ten='NoAutoUpdate'; Gt='1' },
  @{ Nhom='Tùy chọn máy'; Nhan='Cho phép đường dẫn dài hơn 260 ký tự'; Loai='reg'; Duong='HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem'; Ten='LongPathsEnabled'; Gt='1' },
  @{ Nhom='Tùy chọn máy'; Nhan='Tắt System Restore'; Loai='ps'; Ma={
        $c = Get-CimInstance -Namespace root\default -ClassName SystemRestoreConfig -EA SilentlyContinue
        if ($c) { @{ Dat = ($c.RPSessionInterval -eq 0); ChiTiet = "RPSessionInterval = $($c.RPSessionInterval)" } }
        else { @{ Dat = $null; ChiTiet = 'khong doc duoc cau hinh System Restore' } }
    } },
  @{ Nhom='Tùy chọn máy'; Nhan='Đặt nguồn điện ở mức Hiệu suất cao'; Loai='ps'; Ma={
        $r = (powercfg /getactivescheme 2>&1 | Out-String)
        $ten = if ($r -match '\(([^)]+)\)') { $matches[1] } else { '?' }
        @{ Dat = ($r -match '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'); ChiTiet = $ten }
    } },
  @{ Nhom='Tùy chọn giao diện (mọi tài khoản)'; Nhan='Tắt tìm kiếm Bing trong menu Start'; Loai='reg'; Duong='HKCU:\Software\Policies\Microsoft\Windows\Explorer'; Ten='DisableSearchBoxSuggestions'; Gt='1' },
  @{ Nhom='Tùy chọn giao diện (mọi tài khoản)'; Nhan='Mở Explorer vào This PC thay vì Quick Access'; Loai='reg'; Duong='HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced'; Ten='LaunchTo'; Gt='1' },
  @{ Nhom='Tùy chọn giao diện (mọi tài khoản)'; Nhan='Menu chuột phải kiểu cũ (Windows 11)'; Loai='khoa'; Duong='HKCU:\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32' },
  @{ Nhom='Tùy chọn giao diện (mọi tài khoản)'; Nhan='Thanh tác vụ căn trái (Windows 11)'; Loai='reg'; Duong='HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced'; Ten='TaskbarAl'; Gt='0' },
  @{ Nhom='Tùy chọn máy'; Nhan='Tắt Widgets / bảng tin thời tiết'; Loai='reg'; Duong='HKLM:\SOFTWARE\Policies\Microsoft\Dsh'; Ten='AllowNewsAndInterests'; Gt='0' },
  @{ Nhom='Tùy chọn giao diện (mọi tài khoản)'; Nhan='Tắt gợi ý ứng dụng và quảng cáo'; Loai='reg'; Duong='HKCU:\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager'; Ten='SilentInstalledAppsEnabled'; Gt='0' },
  @{ Nhom='Tùy chọn giao diện (mọi tài khoản)'; Nhan='Hiện This PC và Network ngoài desktop'; Loai='reg'; Duong='HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel'; Ten='{20D04FE0-3AEA-1069-A2D8-08002B30309D}'; Gt='0' },
  @{ Nhom='Tùy chọn giao diện (mọi tài khoản)'; Nhan='Ưu tiên hiệu năng thay vì giao diện đẹp'; Loai='reg'; Duong='HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects'; Ten='VisualFXSetting'; Gt='2' },
  @{ Nhom='Tùy chọn máy'; Nhan='Không tự khởi động lại khi có người đang dùng'; Loai='reg'; Duong='HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU'; Ten='NoAutoRebootWithLoggedOnUsers'; Gt='1' },
  @{ Nhom='Tùy chọn máy'; Nhan='Bật .NET Framework 3.5 (tải qua mạng)'; Loai='ps'; Ma={
        $f = Get-WindowsOptionalFeature -Online -FeatureName NetFx3 -EA SilentlyContinue
        if ($f) { @{ Dat = ($f.State -eq 'Enabled'); ChiTiet = "State = $($f.State) (can bo nguon sxs)" } }
        else { @{ Dat = $null; ChiTiet = 'khong doc duoc trang thai tinh nang' } }
    } },
  @{ Nhom='Tùy chọn máy'; Nhan='Tắt IPv6 trên mọi card mạng'; Loai='reg'; Duong='HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters'; Ten='DisabledComponents'; Gt='255' },
  @{ Nhom='Tùy chọn máy'; Nhan='Mở chia sẻ quản trị qua mạng (C$, ADMIN$)'; Loai='reg'; Duong='HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System'; Ten='LocalAccountTokenFilterPolicy'; Gt='1' },
  @{ Nhom='Tùy chọn máy'; Nhan='Bỏ màn hình khoá, vào thẳng ô đăng nhập'; Loai='reg'; Duong='HKLM:\SOFTWARE\Policies\Microsoft\Windows\Personalization'; Ten='NoLockScreen'; Gt='1' },
  @{ Nhom='Tùy chọn máy'; Nhan='Tắt Cortana'; Loai='reg'; Duong='HKLM:\SOFTWARE\Policies\Microsoft\Windows\Windows Search'; Ten='AllowCortana'; Gt='0' },
  @{ Nhom='Tùy chọn máy'; Nhan='Cho phép chạy script PowerShell'; Loai='ps'; Ma={
        $p = Get-ExecutionPolicy -Scope LocalMachine
        @{ Dat = ($p -eq 'RemoteSigned'); ChiTiet = "ExecutionPolicy = $p" }
    } },
  @{ Nhom='Tùy chọn giao diện (mọi tài khoản)'; Nhan='Bật sẵn Num Lock khi khởi động'; Loai='reg'; Duong='Registry::HKEY_USERS\.DEFAULT\Control Panel\Keyboard'; Ten='InitialKeyboardIndicators'; Gt='2' },
  @{ Nhom='Tùy chọn máy'; Nhan='Bỏ màn hình chào của Edge lần đầu mở'; Loai='reg'; Duong='HKLM:\SOFTWARE\Policies\Microsoft\Edge'; Ten='HideFirstRunExperience'; Gt='1' },
  @{ Nhom='Tùy chọn máy'; Nhan='Không cho Edge chạy ngầm khi đã đóng'; Loai='reg'; Duong='HKLM:\SOFTWARE\Policies\Microsoft\Edge'; Ten='StartupBoostEnabled'; Gt='0' },
  @{ Nhom='Tùy chọn máy'; Nhan='Xoá lối tắt Edge trên desktop'; Loai='ps'; Ma={
        $con = @("$env:PUBLIC\Desktop\Microsoft Edge.lnk", "$env:USERPROFILE\Desktop\Microsoft Edge.lnk") |
               Where-Object { Test-Path $_ }
        @{ Dat = (-not $con); ChiTiet = $(if ($con) { 'VAN CON: ' + ($con -join ', ') } else { 'khong con loi tat Edge' }) }
    } },
  @{ Nhom='Tùy chọn máy'; Nhan='Tắt SmartScreen'; Loai='reg'; Duong='HKLM:\SOFTWARE\Policies\Microsoft\Windows\System'; Ten='EnableSmartScreen'; Gt='0' },
  @{ Nhom='Tùy chọn giao diện (mọi tài khoản)'; Nhan='Tắt âm thanh hệ thống'; Loai='khoa'; Duong='HKCU:\AppEvents\Schemes' },
  @{ Nhom='Tùy chọn giao diện (mọi tài khoản)'; Nhan='Luôn hiện mọi biểu tượng khay hệ thống'; Loai='reg'; Duong='HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer'; Ten='EnableAutoTray'; Gt='0' },
  @{ Nhom='Tùy chọn giao diện (mọi tài khoản)'; Nhan='Ẩn nút Task View trên thanh tác vụ'; Loai='reg'; Duong='HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced'; Ten='ShowTaskViewButton'; Gt='0' },
  @{ Nhom='Tùy chọn giao diện (mọi tài khoản)'; Nhan='Thu nhỏ ô tìm kiếm thành biểu tượng'; Loai='reg'; Duong='HKCU:\Software\Microsoft\Windows\CurrentVersion\Search'; Ten='SearchboxTaskbarMode'; Gt='1' },
  @{ Nhom='Tùy chọn giao diện (mọi tài khoản)'; Nhan='Tắt bảng chú thích khi rê chuột vào thư mục'; Loai='reg'; Duong='HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced'; Ten='ShowInfoTip'; Gt='0' },
  @{ Nhom='Tùy chọn máy'; Nhan='Không ghi thời điểm mở file lần cuối'; Loai='ps'; Ma={
        $r = (fsutil behavior query disableLastAccess 2>&1 | Out-String)
        @{ Dat = ($r -match '=\s*(1|3)\b'); ChiTiet = $r.Trim() }
    } },
  @{ Nhom='Tùy chọn máy'; Nhan='Không tự cài app kèm theo thiết bị'; Loai='reg'; Duong='HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Device Metadata'; Ten='PreventDeviceMetadataFromNetwork'; Gt='1' },
  @{ Nhom='Tùy chọn máy'; Nhan='Chặn hãng máy tự nhét phần mềm qua BIOS (WPBT)'; Loai='reg'; Duong='HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager'; Ten='DisableWpbtExecution'; Gt='1' },
  @{ Nhom='Tùy chọn giao diện (mọi tài khoản)'; Nhan='Tắt tăng tốc con trỏ chuột'; Loai='reg'; Duong='HKCU:\Control Panel\Mouse'; Ten='MouseSpeed'; Gt='0' },
  @{ Nhom='Tùy chọn giao diện (mọi tài khoản)'; Nhan='Dùng giao diện Tối (Dark mode)'; Loai='reg'; Duong='HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'; Ten='AppsUseLightTheme'; Gt='0' },
  @{ Nhom='Tùy chọn máy'; Nhan='Cho phép nâng cấp Windows 11 trên máy không đủ chuẩn'; Loai='reg'; Duong='HKLM:\SYSTEM\Setup\MoSetup'; Ten='AllowUpgradesWithUnsupportedTPMOrCPU'; Gt='1' },
  @{ Nhom='Tùy chọn máy'; Nhan='Xoá thư mục Windows.old nếu còn sót'; Loai='ps'; Ma={
        @{ Dat = (-not (Test-Path 'C:\Windows.old')); ChiTiet = $(if (Test-Path 'C:\Windows.old') { 'VAN CON C:\Windows.old' } else { 'khong co Windows.old' }) }
    } },
  @{ Nhom='Gỡ ứng dụng'; Nhan='Tin tức (News)'; Loai='ps'; Ma={
            $g = Get-AppxPackage -Name 'Microsoft.BingNews' -EA SilentlyContinue
            @{ Dat = ($g -eq $null); ChiTiet = $(if ($g) { 'VAN CON tren may' } else { 'da go' }) }
        } },
  @{ Nhom='Gỡ ứng dụng'; Nhan='Thời tiết (Weather)'; Loai='ps'; Ma={
            $g = Get-AppxPackage -Name 'Microsoft.BingWeather' -EA SilentlyContinue
            @{ Dat = ($g -eq $null); ChiTiet = $(if ($g) { 'VAN CON tren may' } else { 'da go' }) }
        } },
  @{ Nhom='Gỡ ứng dụng'; Nhan='Trợ giúp (Get Help)'; Loai='ps'; Ma={
            $g = Get-AppxPackage -Name 'Microsoft.GetHelp' -EA SilentlyContinue
            @{ Dat = ($g -eq $null); ChiTiet = $(if ($g) { 'VAN CON tren may' } else { 'da go' }) }
        } },
  @{ Nhom='Phải giữ lại'; Nhan='Microsoft Store'; Loai='ps'; Ma={
            $g = Get-AppxPackage -Name 'Microsoft.WindowsStore' -EA SilentlyContinue
            @{ Dat = ($g -ne $null); ChiTiet = $(if ($g) { 'con nguyen' } else { 'DA BI GO NHAM' }) }
        } },
  @{ Nhom='Phải giữ lại'; Nhan='Máy tính (Calculator)'; Loai='ps'; Ma={
            $g = Get-AppxPackage -Name 'Microsoft.WindowsCalculator' -EA SilentlyContinue
            @{ Dat = ($g -ne $null); ChiTiet = $(if ($g) { 'con nguyen' } else { 'DA BI GO NHAM' }) }
        } },
  @{ Nhom='Vệ sinh'; Nhan='File nội bộ _thongtin.json không lọt sang'; Loai='ps'; Ma={
        $l = @(Get-ChildItem 'C:\ConsolePi\ungdung' -Recurse -Filter '_thongtin.json' -EA SilentlyContinue)
        @{ Dat = ($l.Count -eq 0); ChiTiet = "$($l.Count) file" }
    } }
)

# ============================================================
#  Console Pi - BAO CAO TONG KET SAU KHI CAI
#  (sinh tu dong theo dung kich ban da chay - khong sua tay)
# ============================================================
$ErrorActionPreference = 'SilentlyContinue'

$OutDir  = 'C:\ConsolePi'
$OutFile = Join-Path $OutDir 'BAO-CAO-TONG-KET.txt'
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }

function Doc-Reg($duong, $ten) {
    try { return (Get-ItemProperty -Path $duong -Name $ten -EA Stop).$ten } catch { return $null }
}

$ketQua = @()
foreach ($m in $MUC) {
    $dat = $null; $ct = ''
    switch ($m.Loai) {
        'reg' {
            $that = Doc-Reg $m.Duong $m.Ten
            if ($null -eq $that) { $dat = $false; $ct = 'khong tim thay gia tri' }
            else { $dat = ("$that" -eq "$($m.Gt)"); $ct = "= $that" + $(if (-not $dat) { " (can $($m.Gt))" } else { '' }) }
        }
        'khoa' {
            $dat = Test-Path $m.Duong
            $ct = $(if ($dat) { 'khoa da duoc tao' } else { 'khong thay khoa' })
        }
        'ps' {
            try { $r = & $m.Ma; $dat = $r.Dat; $ct = [string]$r.ChiTiet }
            catch { $dat = $false; $ct = 'loi khi kiem: ' + $_.Exception.Message }
        }
        default { $dat = $null; $ct = 'muc nay khong tu kiem duoc' }
    }
    $ketQua += [PSCustomObject]@{
        Nhom = $m.Nhom; Nhan = $m.Nhan
        Dat = $dat
        ChiTiet = $ct
        TrangThai = $(if ($dat -eq $true) { 'ĐÃ LÀM' } elseif ($dat -eq $false) { 'chưa được' } else { 'không rõ' })
    }
}

# Cac buoc chay SAU KHI dang nhap (tien-trinh.ps1 ghi lai): script, lenh
# them, cai/go phan mem - bao cao ghi ca nhung viec nay. Tuy chon Windows
# thi da doi chieu registry o tren nen khong lap lai.
$fKq = Join-Path $OutDir 'ket-qua-tien-trinh.json'
if (Test-Path $fKq) {
    try {
        # PHAI gan vao bien truoc: PowerShell 5.1 `ConvertFrom-Json` tra CA
        # MANG thanh 1 doi tuong - boc @(...) quanh ong dan thi foreach chi
        # chay 1 lan voi ca mang (loi that lab 26/09/2026: bao cao Win11 khong
        # hien dong "Sau dang nhap" nao du script da chay).
        $dsBuoc = Get-Content $fKq -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($b in $dsBuoc) {
            if ("$($b.Ten)" -notmatch '^(Chạy script|Lệnh thêm|Cài |Gỡ )') { continue }
            $ok = ($b.TrangThai -eq 'xong')
            $ketQua += [PSCustomObject]@{
                Nhom = 'Sau đăng nhập'; Nhan = "$($b.Ten)"
                Dat = $ok
                ChiTiet = $(if ($ok) { "xong ($($b.Giay)s)" } else { "$($b.TrangThai) $($b.GhiChu)" })
                TrangThai = $(if ($ok) { 'ĐÃ LÀM' } else { 'chưa được' })
            }
        }
    } catch { }
}

$soDat   = @($ketQua | Where-Object { $_.Dat -eq $true }).Count
$soHong  = @($ketQua | Where-Object { $_.Dat -eq $false }).Count
$soKhong = @($ketQua | Where-Object { $_.Dat -eq $null }).Count

# ---------- Ghi ra file (luon ghi, du co ai doc popup hay khong) ----------
$txt = New-Object System.Collections.Generic.List[string]
$txt.Add('================================================================')
$txt.Add('   CONSOLE SYSTEM - BÁO CÁO NHỮNG VIỆC ĐÃ LÀM TRÊN MÁY NÀY')
$txt.Add('   Kich ban : ' + $TEN_KICHBAN)
$txt.Add('   May      : ' + $env:COMPUTERNAME + '   |   Nguoi dung: ' + $env:USERNAME)
$txt.Add('   Thoi diem: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
$txt.Add('================================================================')
$txt.Add('')
$txt.Add("   ĐÃ LÀM XONG: $soDat việc")
$txt.Add('')
# File van ban: CHI ghi viec DA LAM XONG, dung y het khoi hien tren cua so.
$cac = @($ketQua | Where-Object { $_.Dat -eq $true })
if ($cac.Count -gt 0) {
    $td = "ĐÃ LÀM XONG ($($cac.Count))"
    $txt.Add('--- ' + $td + ' ' + ('-' * [Math]::Max(0, 50 - $td.Length)))
    foreach ($r in $cac) {
        $txt.Add(('  [{0}] {1,-42} {2}' -f $r.Nhom, $r.Nhan, $r.ChiTiet))
    }
    $txt.Add('')
}
$txt.Add('--- Thong tin them -------------------------------------')
$os = Get-CimInstance Win32_OperatingSystem
$txt.Add('  Windows : ' + $os.Caption + ' (build ' + $os.BuildNumber + ')')
foreach ($c in (Get-NetAdapter -Physical | Where-Object Status -eq 'Up')) {
    $ip = Get-NetIPAddress -InterfaceIndex $c.InterfaceIndex -AddressFamily IPv4 |
          Where-Object { $_.IPAddress -notlike '169.254.*' } | Select-Object -First 1
    $txt.Add('  Mang    : ' + $c.Name + ' - ' + $(if ($ip) { $ip.IPAddress } else { 'chua co IP' }))
}
$thieu = @(Get-CimInstance Win32_PnPEntity | Where-Object { $_.ConfigManagerErrorCode -ne 0 })
$txt.Add('  Thiet bi thieu driver: ' + $thieu.Count)
# Thiet bi chua co driver thuong KHONG co Name (lab 26/09/2026: dong "- "
# trong) -> ghi ma phan cung de biet can tai driver gi.
foreach ($t in $thieu) {
    $ten = if ($t.Name) { $t.Name } else { '(chua co ten)' }
    $txt.Add('      - ' + $ten + '  [' + $t.PNPDeviceID + '] ma loi ' + $t.ConfigManagerErrorCode)
}
$txt -join "`r`n" | Out-File -FilePath $OutFile -Encoding UTF8
# Ban DAY DU (ca muc chua dat) cho ky thuat tra loi - cua so va file .txt chi
# hien viec da xong theo yeu cau anh Thoai, nen muc hong khong duoc mat dau vet.
try { $ketQua | ConvertTo-Json -Depth 3 |
      Out-File -FilePath (Join-Path $OutDir 'bao-cao-day-du.json') -Encoding UTF8 } catch { }

# ---------- Cua so bao cao ----------
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

# Ten bien la $frm chu khong phai $f: cac doan kiem tra rieng o tren co
# dung bien $f (vd Get-WindowsOptionalFeature), de trung ten thi rat kho
# lan ra khi hong.
$frm = New-Object System.Windows.Forms.Form
$frm.Text = 'Console System - Những việc đã làm trên máy này'
$frm.Size = New-Object System.Drawing.Size(940, 720)
$frm.StartPosition = 'CenterScreen'
$frm.BackColor = [System.Drawing.Color]::FromArgb(248, 249, 251)
$frm.TopMost = $true
$frm.MinimumSize = New-Object System.Drawing.Size(700, 480)

# --- Dai mau tren cung: LUON XANH - bao cao gio chi liet ke viec DA LAM,
# khong con danh sach "chua dat" de doi mau canh bao theo nua (xem ly do
# that o cho DoNhom ben duoi).
$mauNen = [System.Drawing.Color]::FromArgb(22, 128, 70)
$head = New-Object System.Windows.Forms.Panel
$head.Dock = 'Top'; $head.Height = 96; $head.BackColor = $mauNen
$frm.Controls.Add($head)

$lblTo = New-Object System.Windows.Forms.Label
$lblTo.Text = "Đã làm xong $soDat việc"
$lblTo.Font = New-Object System.Drawing.Font('Segoe UI', 19, [System.Drawing.FontStyle]::Bold)
$lblTo.ForeColor = [System.Drawing.Color]::White
$lblTo.AutoSize = $true; $lblTo.Location = New-Object System.Drawing.Point(22, 16)
$head.Controls.Add($lblTo)

$lblPhu = New-Object System.Windows.Forms.Label
$lblPhu.Text = "May: $env:COMPUTERNAME     Kich ban: $TEN_KICHBAN     " + (Get-Date -Format 'yyyy-MM-dd HH:mm')
$lblPhu.Font = New-Object System.Drawing.Font('Segoe UI', 10)
$lblPhu.ForeColor = [System.Drawing.Color]::FromArgb(232, 240, 236)
$lblPhu.AutoSize = $true; $lblPhu.Location = New-Object System.Drawing.Point(24, 58)
$head.Controls.Add($lblPhu)

# --- Thanh nut duoi cung (phai them TRUOC bang ket qua)
# THU TU THEM QUAN TRONG: WinForms dock theo z-order, control them SAU
# nam duoi cung z-order va duoc dock SAU CUNG. Control Dock='Fill' phai
# la cai them SAU CUNG thi no moi chiem dung phan con lai; them no o
# giua thi hai thanh Top/Bottom se de len no.
$foot = New-Object System.Windows.Forms.Panel
$foot.Dock = 'Bottom'; $foot.Height = 58
$foot.BackColor = [System.Drawing.Color]::FromArgb(238, 240, 244)
$frm.Controls.Add($foot)

$lblFile = New-Object System.Windows.Forms.Label
$lblFile.Text = 'Da luu ban day du vao: ' + $OutFile
$lblFile.Font = New-Object System.Drawing.Font('Segoe UI', 9)
$lblFile.ForeColor = [System.Drawing.Color]::FromArgb(90, 95, 105)
$lblFile.AutoSize = $true; $lblFile.Location = New-Object System.Drawing.Point(18, 20)
$foot.Controls.Add($lblFile)

$btnMo = New-Object System.Windows.Forms.Button
$btnMo.Text = 'Mo file bao cao'; $btnMo.Size = New-Object System.Drawing.Size(140, 34)
$btnMo.Font = New-Object System.Drawing.Font('Segoe UI', 10)
$btnMo.Anchor = 'Top,Right'
$btnMo.Location = New-Object System.Drawing.Point(($foot.Width - 300), 12)
$btnMo.Add_Click({ Start-Process notepad.exe $OutFile })
$foot.Controls.Add($btnMo)

$btnDong = New-Object System.Windows.Forms.Button
$btnDong.Text = 'Dong'; $btnDong.Size = New-Object System.Drawing.Size(130, 34)
$btnDong.Font = New-Object System.Drawing.Font('Segoe UI', 10, [System.Drawing.FontStyle]::Bold)
$btnDong.Anchor = 'Top,Right'
$btnDong.Location = New-Object System.Drawing.Point(($foot.Width - 150), 12)
$btnDong.Add_Click({ $frm.Close() })
$foot.Controls.Add($btnDong)

# --- Bang ket qua (them SAU CUNG vi Dock='Fill')
$lv = New-Object System.Windows.Forms.ListView
$lv.View = 'Details'; $lv.FullRowSelect = $true; $lv.GridLines = $false
$lv.Dock = 'Fill'; $lv.Font = New-Object System.Drawing.Font('Segoe UI', 10)
$lv.BorderStyle = 'None'
# WinForms dock control CUOI danh sach truoc -> Fill them sau cung lai bi dock
# truoc va chiem ca form, dai tren/duoi de len chu. BringToFront dua no len
# dau danh sach = dock SAU CUNG, chi chiem phan con lai (xem duoi).
$lv.Columns.Add('Trang thai', 110) | Out-Null
$lv.Columns.Add('Hang muc', 400) | Out-Null
$lv.Columns.Add('Thuc te tren may', 380) | Out-Null

$xanh = [System.Drawing.Color]::FromArgb(20, 115, 62)
$do   = [System.Drawing.Color]::FromArgb(178, 40, 40)
$xam  = [System.Drawing.Color]::FromArgb(130, 130, 140)

# DO THEO 3 PHAN, PHAN "DA LAM" LEN DAU TIEN.
#
# LY DO THAT (anh Thoai: "anh muon bao cao la nhung gi no DA LAM chu
# khong phai show nhung cai con lai"): truoc day cac muc do theo NHOM
# chuc nang, ma nhom dau tien lai la danh sach app go bo - neu go khong
# duoc thi mo bao cao ra la thay kin mot man hinh chu do "chua dat",
# phai keo mai moi thay nhung viec da lam duoc. Nhin vao tuong ca buoi
# cai hong, trong khi thuc te phan lon deu xong.
function DoNhom($tieuDe, $mau, $cacMuc) {
    if ($cacMuc.Count -eq 0) { return }
    $g = New-Object System.Windows.Forms.ListViewItem('')
    $g.SubItems.Add($tieuDe + "  ($($cacMuc.Count))") | Out-Null
    $g.SubItems.Add('') | Out-Null
    $g.Font = New-Object System.Drawing.Font('Segoe UI', 11, [System.Drawing.FontStyle]::Bold)
    $g.BackColor = $mau
    $lv.Items.Add($g) | Out-Null
    foreach ($r in $cacMuc) {
        $it = New-Object System.Windows.Forms.ListViewItem($r.TrangThai)
        $it.SubItems.Add('     ' + $r.Nhan) | Out-Null
        $it.SubItems.Add($r.ChiTiet) | Out-Null
        if ($r.Dat -eq $true) { $it.ForeColor = $xanh }
        elseif ($r.Dat -eq $false) { $it.ForeColor = $do }
        else { $it.ForeColor = $xam }
        $lv.Items.Add($it) | Out-Null
    }
}

# CHI HIEN VIEC DA LAM XONG.
#
# LY DO THAT (anh Thoai: "anh chi can no xuat ra nhung gi no da lam
# thoi"): ban truoc do van con hien them nhom "CAN XEM LAI" va "KHONG
# TU KIEM DUOC" ben duoi - dai va roi mat, trong khi dieu anh Thoai can
# chi la xac nhan may da lam xong nhung gi. Bo han 2 nhom kia khoi cua
# so va khoi file .txt (van con dem so trong dong tieu de neu co viec
# chua xong, khong giau hoan toan - xem $lblTo.Text ben duoi).
DoNhom 'ĐÃ LÀM XONG' ([System.Drawing.Color]::FromArgb(214, 240, 222)) `
       @($ketQua | Where-Object { $_.Dat -eq $true })
$frm.Controls.Add($lv)
$lv.BringToFront()

$frm.AcceptButton = $btnDong
[void]$frm.ShowDialog()
