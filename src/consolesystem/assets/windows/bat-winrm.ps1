<#
 Console System - Bat WinRM tren may Windows de Console System trien khai phan mem / quan ly tu xa.
 Chay bang PowerShell "Run as administrator":
     powershell -ExecutionPolicy Bypass -File .\bat-winrm.ps1
     powershell -ExecutionPolicy Bypass -File .\bat-winrm.ps1 -ChiChoIP 192.168.110.37      (khuyen nghi: chi cho 1 may Console System)
     powershell -ExecutionPolicy Bypass -File .\bat-winrm.ps1 -Tat                            (tat lai WinRM va go mo tuong lua)
 Khong bat Basic, khong bat truyen khong ma hoa: Console System dung NTLM (du lieu van duoc ma hoa o tang tin nhan).
#>
param(
    [string]$ChiChoIP = "",     # trong = mo cho mang LAN (LocalSubnet); dien IP may Console System de chat hon
    [switch]$Tat
)
$ErrorActionPreference = "Stop"
$ten = "Console System - WinRM (5985)"

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "LOI: hay chay PowerShell bang 'Run as administrator'." -ForegroundColor Red; exit 1
}

# Nhieu IP: cach nhau dau phay/cham phay/khoang trang (vd "192.168.110.30,192.168.110.31")
$nguon = @($ChiChoIP -split '[,; ]+' | Where-Object { $_ })
foreach ($ip in $nguon) {
    $o = $null
    if (-not [Net.IPAddress]::TryParse(($ip -split '/')[0], [ref]$o)) {
        Write-Host "LOI: '$ip' khong phai dia chi IP hop le." -ForegroundColor Red; exit 2
    }
}
if (-not $nguon) { $nguon = @("LocalSubnet") }

if ($Tat) {
    Get-NetFirewallRule -DisplayName $ten -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    Stop-Service WinRM -Force -ErrorAction SilentlyContinue
    Set-Service WinRM -StartupType Manual
    Disable-PSRemoting -Force -ErrorAction SilentlyContinue
    Stop-Service WinRM -Force -ErrorAction SilentlyContinue      # Disable-PSRemoting co the bat lai dich vu
    Write-Host "Da tat WinRM va go quy tac tuong lua '$ten'." -ForegroundColor Yellow; exit 0
}

# Mang dang o che do Public thi WinRM khong cho mo -> chuyen sang Private
Get-NetConnectionProfile | Where-Object { $_.NetworkCategory -eq "Public" } | ForEach-Object {
    Set-NetConnectionProfile -InterfaceIndex $_.InterfaceIndex -NetworkCategory Private
    Write-Host "Da chuyen mang '$($_.Name)' tu Public sang Private."
}

Set-Service WinRM -StartupType Automatic
Enable-PSRemoting -Force -SkipNetworkProfileCheck | Out-Null

# Tai khoan quan tri CUC BO (khong vao domain) can khoa nay moi chay duoc lenh quan tri qua mang
New-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name LocalAccountTokenFilterPolicy -Value 1 -PropertyType DWord -Force | Out-Null

# Quy tac tuong lua rieng, gioi han dia chi nguon
Get-NetFirewallRule -DisplayName $ten -ErrorAction SilentlyContinue | Remove-NetFirewallRule
New-NetFirewallRule -DisplayName $ten -Direction Inbound -Protocol TCP -LocalPort 5985 -Action Allow `
    -Profile Any -RemoteAddress $nguon | Out-Null

# Enable-PSRemoting bat quy tac co san cua Windows "Windows Remote Management (HTTP-In)" (Private/Domain: moi IP)
# -> quy tac gioi han IP o tren khong con tac dung. Tat cac quy tac co san, chi giu quy tac cua Console System.
# (lab 28/10/2026: cai CHICHOIP=192.168.110.30 ma may .37 van vao duoc cong 5985)
Get-NetFirewallRule -Name "WINRM-HTTP-In-TCP*" -ErrorAction SilentlyContinue | Disable-NetFirewallRule

Test-WSMan -ComputerName localhost | Out-Null
Write-Host "XONG: WinRM da bat (cong 5985), cho phep tu: $($nguon -join ', ')" -ForegroundColor Green
Write-Host "Luu y: day la kenh quan tri tu xa, chi dung trong mang noi bo, dat mat khau Administrator manh."
