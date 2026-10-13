# ConsolePi-Script: Suc khoe o cung ban dau
# Mo ta   : Ghi tinh trang o cung (SMART), RAM luc cai may vao C:\ConsolePi\reports. Phat hien o cung xau cua may cu
# Can mang: Khong | Can khoi dong lai: Khong | Hoan tac: Xoa file bao cao
# Hanh vi CO DINH - khong tham so. Chay duoc nhieu lan (lan sau khong doi gi them).
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Ten = '20-suc-khoe-o-cung'
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

    Ghi 'XONG'
    XongHoSo
    exit 0
} catch {
    Ghi ('LOI: ' + $_.Exception.Message + ' (dong ' + $_.InvocationInfo.ScriptLineNumber + ')')
    XongHoSo
    exit 1
}
