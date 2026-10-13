# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# CHI DE TEST (chay TRONG may mau Windows qua thu-script-kho.sh): chay 50 script kho 2 luot,
# kiem sau moi script, khoi dong lai, kiem lai + kiem ho so Default User.
$ErrorActionPreference = 'Continue'
$d = 'C:\ConsolePi\ks'
$kq = "$d\ket-qua.json"
$man0 = Get-Content -Raw -Encoding UTF8 "$d\manifest.json" | ConvertFrom-Json
$man = @($man0)
if ($man.Count -eq 1 -and $man[0] -is [array]) { $man = $man[0] }
$thuTu = @($man | Where-Object { -not $_.cuoi }) + @($man | Where-Object { $_.cuoi })
$tt = if (Test-Path "$d\pha2") { 2 } else { 1 }
$out = [ordered]@{ pha = $tt }
if ($tt -eq 2 -and (Test-Path $kq)) { try { $out = [ordered]@{}; (Get-Content -Raw -Encoding UTF8 $kq | ConvertFrom-Json).PSObject.Properties | ForEach-Object { $out[$_.Name] = $_.Value } } catch { } }
function Luu { $out | ConvertTo-Json -Depth 8 | Out-File $kq -Encoding UTF8 }

function Kiem($id) {
    $o = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$d\c-$id.ps1" 2>&1 | Out-String
    return ($o -match '(?m)^DAT\s*$')
}
function ChayMot($id) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $p = Start-Process powershell.exe -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$d\$id.ps1`"" -PassThru -WindowStyle Hidden
    if (-not $p.WaitForExit(420000)) { try { $p.Kill() } catch { }; $ma = -999 } else { $ma = $p.ExitCode }
    return [ordered]@{ ma = $ma; giay = [int]$sw.Elapsed.TotalSeconds }
}

if ($tt -eq 1) {
    $os = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
    $adm = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    $out = [ordered]@{ pha = 1; may = [ordered]@{ ten = $os.ProductName; build = $os.CurrentBuild; ban = $os.DisplayVersion; user = $env:USERNAME; admin = $adm; ps = "$($PSVersionTable.PSVersion)" }; cu_phap = @(); lan = @() }
    Luu
    foreach ($m in $man) {
        $err = $null; $tok = $null
        [void][System.Management.Automation.Language.Parser]::ParseFile("$d\$($m.id).ps1", [ref]$tok, [ref]$err)
        $e2 = $null
        [void][System.Management.Automation.Language.Parser]::ParseFile("$d\c-$($m.id).ps1", [ref]$tok, [ref]$e2)
        $out.cu_phap += [ordered]@{ id = $m.id; loi = @($err | ForEach-Object { $_.Message }) + @($e2 | ForEach-Object { 'check: ' + $_.Message }) }
    }
    Luu
    foreach ($lan in 1, 2) {
        $lanKq = [ordered]@{ lan = $lan; kq = @() }
        $out.lan += $lanKq
        foreach ($m in $thuTu) {
            $r = ChayMot $m.id
            $r.id = $m.id
            $r.kiem = Kiem $m.id
            $lanKq.kq += $r
            Luu
        }
    }
    $out.xong_pha1 = $true
    Luu
    New-Item "$d\pha2" -ItemType File -Force | Out-Null
    shutdown /r /t 5 /f
    exit
}

# ---- Pha 2: sau khi khoi dong lai
$sau = @()
foreach ($m in $thuTu) { $sau += [ordered]@{ id = $m.id; kiem = (Kiem $m.id) } }
$out.sau_khoi_dong = $sau
$hs = @()
$f = 'C:\Users\Default\NTUSER.DAT'
$nap = $false
reg load HKU\CS_KT "$f" 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) { $nap = $true }
foreach ($m in $man) {
    foreach ($u in @($m.user)) {
        if (-not $u.path) { continue }
        $v = $null
        if ($nap) { $v = (Get-ItemProperty -LiteralPath "Registry::HKEY_USERS\CS_KT\$($u.path)" -Name $u.name -ErrorAction SilentlyContinue).($u.name) }
        $hs += [ordered]@{ id = $m.id; path = $u.path; name = $u.name; mong = "$($u.val)"; co = "$v"; dung = ("$v" -eq "$($u.val)") }
    }
}
if ($nap) { [gc]::Collect(); [gc]::WaitForPendingFinalizers(); Start-Sleep 1; reg unload HKU\CS_KT 2>&1 | Out-Null }
$out.ho_so_mac_dinh = [ordered]@{ nap_duoc = $nap; muc = $hs }
$out.hoan_tat = $true
Luu
shutdown /s /t 3 /f
