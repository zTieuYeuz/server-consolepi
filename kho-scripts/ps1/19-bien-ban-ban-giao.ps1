# ConsolePi-Script: Bien ban ban giao may
# Mo ta   : Xuat serial, model, CPU, RAM, o cung, MAC, IP, ban Windows, phan mem va driver vao C:\ConsolePi\reports (HTML + CSV)
# Can mang: Khong | Can khoi dong lai: Khong | Hoan tac: Xoa file trong C:\ConsolePi\reports
# Hanh vi CO DINH - khong tham so. Chay duoc nhieu lan (lan sau khong doi gi them).
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Ten = '19-bien-ban-ban-giao'
$LogDir = 'C:\ConsolePi\logs'
New-Item $LogDir -ItemType Directory -Force | Out-Null
$Log = "$LogDir\$Ten.log"
$Build = [int](Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').CurrentBuild
function Ghi([string]$m) { ("{0:yyyy-MM-dd HH:mm:ss} {1}" -f (Get-Date), $m) | Out-File $Log -Append -Encoding UTF8; Write-Host $m }
function Lenh([string]$c) { cmd.exe /c "$c >nul 2>&1"; return $LASTEXITCODE }
function Chay([string]$c) {
    $t = [IO.Path]::GetTempFileName()
    cmd.exe /c "$c > `"$t`" 2>&1"; $script:Ma = $LASTEXITCODE
    $o = Get-Content -Raw -LiteralPath $t -ErrorAction SilentlyContinue
    Remove-Item $t -Force -ErrorAction SilentlyContinue
    if ($o) { return $o.Trim() } else { return '' }
}
function Dat([string]$Duong, [string]$Ten2, $Gia, [string]$Kieu = 'DWord') {
    if (-not (Test-Path -LiteralPath $Duong)) { New-Item -Path $Duong -Force | Out-Null }
    New-ItemProperty -LiteralPath $Duong -Name $Ten2 -Value $Gia -PropertyType $Kieu -Force | Out-Null
}
$script:DefDa = $false
function NapHoSoMacDinh {
    $f = 'C:\Users\Default\NTUSER.DAT'
    if (-not $script:DefDa -and (Test-Path -LiteralPath $f)) {
        if ((Lenh "reg load HKU\CS_Default `"$f`"") -eq 0) { $script:DefDa = $true } else { Ghi 'CANH BAO: khong nap duoc ho so mac dinh (Default User)' }
    }
    return $script:DefDa
}
# Ghi cho tai khoan dang chay VA ho so mac dinh (tai khoan tao sau cung huong)
function DatUser([string]$Duong, [string]$Ten2, $Gia, [string]$Kieu = 'DWord') {
    Dat "HKCU:\$Duong" $Ten2 $Gia $Kieu
    if (NapHoSoMacDinh) { Dat "Registry::HKEY_USERS\CS_Default\$Duong" $Ten2 $Gia $Kieu }
}
function XongHoSo {
    if ($script:DefDa) { [gc]::Collect(); [gc]::WaitForPendingFinalizers(); Start-Sleep 1; Lenh 'reg unload HKU\CS_Default' | Out-Null; $script:DefDa = $false }
}
function BoQua([string]$lydo) { Ghi "BO QUA: $lydo"; XongHoSo; exit 0 }
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Ghi 'LOI: can chay bang quyen Administrator'; exit 1
}
try {
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

    Ghi 'XONG'
    XongHoSo
    exit 0
} catch {
    Ghi ('LOI: ' + $_.Exception.Message + ' (dong ' + $_.InvocationInfo.ScriptLineNumber + ')')
    XongHoSo
    exit 1
}
