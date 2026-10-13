# ConsolePi-Script: Ghi danh sach tai khoan va quyen admin
# Mo ta   : Ghi tai khoan local va thanh vien nhom Administrators vao C:\ConsolePi\reports (de ra soat bao mat)
# Can mang: Khong | Can khoi dong lai: Khong | Hoan tac: Xoa file bao cao
# Hanh vi CO DINH - khong tham so. Chay duoc nhieu lan (lan sau khong doi gi them).
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Ten = '94-ghi-tai-khoan-admin'
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

    $o = New-Object System.Collections.Generic.List[string]
    $o.Add("May: $pc   Ngay: $(Get-Date -Format 'dd/MM/yyyy HH:mm')")
    $o.Add('--- Tai khoan local ---')
    foreach ($u in Get-LocalUser) { $o.Add(("{0} | bat={1} | can mat khau={2} | dang nhap cuoi={3}" -f $u.Name, $u.Enabled, $u.PasswordRequired, $u.LastLogon)) }
    $g = Get-LocalGroup -SID 'S-1-5-32-544'
    $o.Add("--- Thanh vien nhom $($g.Name) ---")
    try { foreach ($m in Get-LocalGroupMember -Group $g.Name -ErrorAction Stop) { $o.Add($m.Name) } }
    catch { $o.Add('(khong doc duoc bang Get-LocalGroupMember - dung net localgroup)'); (cmd /c "net localgroup `"$($g.Name)`"") | ForEach-Object { $o.Add($_) } }
    $o | Out-File "$dir\tai-khoan-$pc.txt" -Encoding UTF8

    Ghi 'XONG'
    XongHoSo
    exit 0
} catch {
    Ghi ('LOI: ' + $_.Exception.Message + ' (dong ' + $_.InvocationInfo.ScriptLineNumber + ')')
    XongHoSo
    exit 1
}
