# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# CHI DE TEST (chay TRONG may mau Windows qua thu-font.sh): thu cai-font.ps1 that.
#  Pha 1: chay cai-font.ps1 bang quyen SYSTEM (tac vu hen gio) 2 LAN - lan 2 phai on dinh (da co thi bo qua)
#  Pha 2 (sau khi khoi dong lai): font co that su hien cho ung dung khong (GDI+ InstalledFontCollection),
#         file + registry du khong
$ErrorActionPreference = 'Continue'
$d  = 'C:\ConsolePi\thuf'
$cfg = Get-Content -Raw -Encoding UTF8 "$d\cau-hinh.json" | ConvertFrom-Json
$kq = "$d\ket-qua.json"
$tt = if (Test-Path "$d\pha2") { 2 } else { 1 }
$out = [ordered]@{ pha = $tt }
if ($tt -eq 2 -and (Test-Path $kq)) { try { $cu = Get-Content -Raw -Encoding UTF8 $kq | ConvertFrom-Json; $out = [ordered]@{ pha = 2; lan = @($cu.lan) } } catch { } }

function Luu { $out | ConvertTo-Json -Depth 6 | Out-File $kq -Encoding UTF8 }

if ($tt -eq 1) {
    $out = [ordered]@{ pha = 1; lan = @() }
    foreach ($lan in 1, 2) {
        $tn = "cstf$lan"
        Remove-Item 'C:\ConsolePi\fonts\ket-qua-thuf.json' -EA SilentlyContinue
        schtasks /create /tn $tn /tr 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\ConsolePi\cai-font.ps1 -Bo thuf' /sc once /st 00:00 /ru SYSTEM /rl HIGHEST /f | Out-Null
        schtasks /run /tn $tn | Out-Null
        $han = (Get-Date).AddSeconds(240)
        do { Start-Sleep 2; $tr = (schtasks /query /tn $tn /fo list /v) -join "`n" } while (($tr -match 'Status:\s+Running') -and (Get-Date) -lt $han)
        $ma = if ($tr -match 'Last Result:\s+(-?\d+)') { [int]$Matches[1] } else { -1 }
        $k = $null
        if (Test-Path 'C:\ConsolePi\fonts\ket-qua-thuf.json') { $k = Get-Content -Raw -Encoding UTF8 'C:\ConsolePi\fonts\ket-qua-thuf.json' | ConvertFrom-Json }
        $out.lan += [ordered]@{ lan = $lan; ma_thoat = $ma; tong = $k.tong; da_cai = @($k.da_cai).Count; loi = @($k.loi); canh_bao = @($k.canh_bao) }
        schtasks /delete /tn $tn /f | Out-Null
    }
    Luu
    New-Item "$d\pha2" -ItemType File -Force | Out-Null
    shutdown /r /t 5 /f
    exit
}

# ---- Pha 2: sau khi khoi dong lai
Add-Type -AssemblyName System.Drawing
$ho = @((New-Object System.Drawing.Text.InstalledFontCollection).Families | ForEach-Object { $_.Name })
$man = @((Get-Content -Raw -Encoding UTF8 'C:\ConsolePi\fonts\thuf\_fonts.json' | ConvertFrom-Json).fonts)
$reg = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'
$rs = @()
foreach ($m in $man) {
    $f = Test-Path -LiteralPath (Join-Path $env:windir ('Fonts\' + $m.file))
    $r = ($reg.PSObject.Properties[$m.reg] -ne $null) -and ($reg.PSObject.Properties[$m.reg].Value -eq $m.file)
    $rs += [ordered]@{ file = $m.file; reg = $m.reg; file_co = $f; reg_co = $r }
}
$out.pha2_font = $rs
$out.ho_mong_doi = @($cfg.ho_mong_doi)
$out.ho_thieu = @($cfg.ho_mong_doi | Where-Object { $ho -notcontains $_ })
$out.so_ho_he_thong = $ho.Count
$out.arial_con_nguyen = ((Get-FileHash 'C:\Windows\Fonts\arial.ttf').Hash -eq $cfg.arial_hash)
$out.hoan_tat = $true
Luu
shutdown /s /t 3 /f
