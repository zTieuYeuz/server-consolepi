# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# Chay TRONG may Windows mau (xem thu-silent.sh), luc dang nhap Administrator.
# Lam y het cach Console System cai phan mem that: chay bo cai bang quyen SYSTEM
# (tac vu hen gio) qua 1 file .cmd roi ghi ma thoat o dong sau, dung ca cach nhan
# ra "bo cai khong tu thoat" (khoa Uninstall moi + bo cai dung yen 60 giay).
# Ket qua ghi ra C:\ConsolePi\thu\ket-qua.json roi TU TAT MAY.
$ErrorActionPreference = 'Continue'
$D = 'C:\ConsolePi\thu'
$Out = "$D\ket-qua.json"
if (-not (Test-Path "$D\cau-hinh.json") -or (Test-Path $Out)) { exit }
$cfg = Get-Content "$D\cau-hinh.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$toiDa = [int]$cfg.toi_da

function Lay-Un {
    foreach ($k in 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
                   'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall') {
        Get-ChildItem $k -EA SilentlyContinue | ForEach-Object {
            $ten = (Get-ItemProperty $_.PSPath -EA SilentlyContinue).DisplayName
            if ($ten) { "$($_.PSChildName)|$ten" }
        }
    }
}
function Lay-Thu-Muc { Get-ChildItem 'C:\Program Files', 'C:\Program Files (x86)' -Directory -EA SilentlyContinue | ForEach-Object { $_.FullName } }
function Lay-Lnk {
    Get-ChildItem 'C:\Users\Public\Desktop', 'C:\ProgramData\Microsoft\Windows\Start Menu\Programs' -Recurse -Filter *.lnk -EA SilentlyContinue |
        ForEach-Object { $_.FullName }
}

$unTruoc = @(Lay-Un); $pfTruoc = @(Lay-Thu-Muc); $lnkTruoc = @(Lay-Lnk)

$tep = $cfg.tep
if ($tep -like '*.msi') { $lenh = 'msiexec /i "' + $tep + '" ' + $cfg.tham_so }
else { $lenh = '"' + $tep + '" ' + $cfg.tham_so }
$fMa = "$D\ma.txt"; Remove-Item $fMa -EA SilentlyContinue
$bat = "$D\chay.cmd"
$noi = "@echo off`r`ncd /d `"" + (Split-Path $tep) + "`"`r`ncall " + $lenh + "`r`n>`"$fMa`" echo %ERRORLEVEL%`r`n"
[System.IO.File]::WriteAllText($bat, $noi, [System.Text.Encoding]::ASCII)

$tn = 'CS_ThuSilent'
Unregister-ScheduledTask -TaskName $tn -Confirm:$false -EA SilentlyContinue
$hd = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument "/c `"$bat`""
$nd = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName $tn -Action $hd -Principal $nd -Force | Out-Null
$t0 = Get-Date
Start-ScheduledTask -TaskName $tn

$ketLuan = 'xong'; $ghiChu = ''; $daDong = $false
$sigCu = -1; $tDung = Get-Date; $lan = 0; $conLai = @()
while ($true) {
    Start-Sleep -Seconds 2; $lan++
    if (Test-Path $fMa) { break }
    $gi = ((Get-Date) - $t0).TotalSeconds
    $pCmd = @(Get-CimInstance Win32_Process -Filter "Name='cmd.exe'" -EA SilentlyContinue |
              Where-Object { $_.CommandLine -like '*chay.cmd*' })
    $pCai = @(); foreach ($c in $pCmd) { $pCai += @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$($c.ProcessId)" -EA SilentlyContinue) }
    if ($gi -ge $toiDa) {
        $conLai = @($pCai | ForEach-Object { $_.Name })
        foreach ($c in $pCmd) { & taskkill /PID $c.ProcessId /F 2>&1 | Out-Null }
        foreach ($q in $pCai) { & taskkill /PID $q.ProcessId /F 2>&1 | Out-Null }
        $ketLuan = 'qua_gio'
        $ghiChu = "Bo cai van chay sau $toiDa giay (thuong la dang cho nguoi bam nut vi tham so khong im lang): " + ($conLai -join ', ')
        break
    }
    if ($lan % 15 -eq 0 -and $gi -ge 60) {
        $sig = 0
        foreach ($q in $pCai) {
            $sig += [double]$q.KernelModeTime + [double]$q.UserModeTime + [double]$q.ReadTransferCount +
                    [double]$q.WriteTransferCount + [double]$q.OtherTransferCount
        }
        if ($sig -ne $sigCu) { $sigCu = $sig; $tDung = Get-Date }
        elseif ($pCai.Count -gt 0 -and ((Get-Date) - $tDung).TotalSeconds -ge 60) {
            $unMoi = @(Lay-Un | Where-Object { $unTruoc -notcontains $_ })
            if ($unMoi.Count -gt 0) {
                $conLai = @($pCai | ForEach-Object { $_.Name })
                foreach ($c in $pCmd) { & taskkill /PID $c.ProcessId /F 2>&1 | Out-Null }
                foreach ($q in $pCai) { & taskkill /PID $q.ProcessId /F 2>&1 | Out-Null }
                $daDong = $true
                $ketLuan = 'khong_tu_thoat'
                $ghiChu = 'Da cai xong nhung bo cai khong tu thoat (Console System dong no sau 60 giay): ' + ($conLai -join ', ')
                break
            }
        }
    }
    if ($lan % 10 -eq 0 -and $gi -gt 5 -and (Get-ScheduledTask -TaskName $tn -EA SilentlyContinue).State -ne 'Running') {
        Start-Sleep -Milliseconds 800
        if (-not (Test-Path $fMa)) { $ketLuan = 'dung_bat_thuong'; $ghiChu = 'Tac vu ket thuc ma khong ghi ma thoat'; break }
    }
}
$giay = [int]((Get-Date) - $t0).TotalSeconds
$ma = $null
if ((Test-Path $fMa) -and -not $daDong) { $m = 0; if ([int]::TryParse(((Get-Content $fMa -Raw) + '').Trim(), [ref]$m)) { $ma = $m } }
if ($ketLuan -eq 'xong' -and $ma -ne $null -and $ma -ne 0 -and $ma -ne 3010) { $ketLuan = 'loi'; $ghiChu = "Ma thoat $ma" }
Unregister-ScheduledTask -TaskName $tn -Confirm:$false -EA SilentlyContinue

Start-Sleep -Seconds 3
$kq = [ordered]@{
    tep = (Split-Path $tep -Leaf); tham_so = $cfg.tham_so; ket_luan = $ketLuan; ma_thoat = $ma; giay = $giay
    ghi_chu = $ghiChu
    muc_go_cai_moi = @(Lay-Un | Where-Object { $unTruoc -notcontains $_ } | ForEach-Object { ($_ -split '\|', 2)[1] })
    thu_muc_moi = @(Lay-Thu-Muc | Where-Object { $pfTruoc -notcontains $_ })
    loi_tat_moi = @(Lay-Lnk | Where-Object { $lnkTruoc -notcontains $_ })
}
[System.IO.File]::WriteAllText($Out, ($kq | ConvertTo-Json -Depth 4), (New-Object System.Text.UTF8Encoding($false)))
Start-Sleep -Seconds 2
shutdown /s /t 3 /f
