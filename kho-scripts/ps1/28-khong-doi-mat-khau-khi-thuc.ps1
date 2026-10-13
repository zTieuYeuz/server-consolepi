# ConsolePi-Script: Khong doi mat khau khi thuc may
# Mo ta   : Khong yeu cau nhap lai mat khau khi may thuc day tu ngu/tat man hinh (ha thap bao mat: chi dung cho may de ban/van phong)
# Can mang: Khong | Can khoi dong lai: Khong | Hoan tac: Xoa khoa chinh sach Power\PowerSettings\0e796bdb-...
# Hanh vi CO DINH - khong tham so. Chay duoc nhieu lan (lan sau khong doi gi them).
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Ten = '28-khong-doi-mat-khau-khi-thuc'
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
    $pol = 'HKLM:\SOFTWARE\Policies\Microsoft\Power\PowerSettings\0e796bdb-100d-47d6-a2d5-f7d2daa51f51'
    Dat $pol 'ACSettingIndex' 0
    Dat $pol 'DCSettingIndex' 0
    foreach ($m in 'setacvalueindex', 'setdcvalueindex') { Lenh "powercfg /$m SCHEME_CURRENT SUB_NONE 0e796bdb-100d-47d6-a2d5-f7d2daa51f51 0" | Out-Null }
    Lenh 'powercfg /setactive SCHEME_CURRENT' | Out-Null

    Ghi 'XONG'
    XongHoSo
    exit 0
} catch {
    Ghi ('LOI: ' + $_.Exception.Message + ' (dong ' + $_.InvocationInfo.ScriptLineNumber + ')')
    XongHoSo
    exit 1
}
