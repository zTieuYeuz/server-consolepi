# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# Chay TRONG may Windows mau (xem thu-silent.sh), luc dang nhap Administrator.
# Lam y het cach Console System cai phan mem that: chay bo cai bang quyen SYSTEM
# (tac vu hen gio) qua 1 file .cmd roi ghi ma thoat o dong sau, dung ca cach nhan
# ra "bo cai khong tu thoat" (khoa Uninstall moi + bo cai dung yen 60 giay).
# Pha 1: cai. Pha 2 (neu cau-hinh co go_cai): go cai dat, kiem tra da sach chua.
#   go_cai = "auto"  -> doc UninstallString/QuietUninstallString cua cac muc moi roi suy ra lenh go im lang
#   go_cai = "<lenh>" -> chay dung lenh do ({BOCAI} = duong dan bo cai; bat dau bang / hoac - thi la
#                        tham so cua chinh bo cai)
# Ket qua ghi ra C:\ConsolePi\thu\ket-qua.json roi TU TAT MAY.
$ErrorActionPreference = 'Continue'
$D = 'C:\ConsolePi\thu'
$Out = "$D\ket-qua.json"
if (-not (Test-Path "$D\cau-hinh.json") -or (Test-Path $Out)) { exit }
$cfg = Get-Content "$D\cau-hinh.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$toiDa = [int]$cfg.toi_da
$tep = $cfg.tep

function Lay-Un-Chi-Tiet {
    foreach ($k in 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
                   'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall') {
        Get-ChildItem $k -EA SilentlyContinue | ForEach-Object {
            $p = Get-ItemProperty $_.PSPath -EA SilentlyContinue
            if ($p.DisplayName) {
                [pscustomobject]@{ khoa = $_.PSChildName; ten = $p.DisplayName; ban = $p.DisplayVersion
                                   go = $p.UninstallString; go_im = $p.QuietUninstallString
                                   msi = ($p.WindowsInstaller -eq 1) }
            }
        }
    }
}
function Lay-Thu-Muc { Get-ChildItem 'C:\Program Files', 'C:\Program Files (x86)' -Directory -EA SilentlyContinue | ForEach-Object { $_.FullName } }
function Lay-Lnk {
    Get-ChildItem 'C:\Users\Public\Desktop', 'C:\ProgramData\Microsoft\Windows\Start Menu\Programs' -Recurse -Filter *.lnk -EA SilentlyContinue |
        ForEach-Object { $_.FullName }
}

# Chay 1 lenh bang SYSTEM nhu Console System that. Tra ve {ket_luan, ma, giay, ghi_chu}
function Chay-Buoc($lenh, $gioiHan, $tenTac) {
    $fMa = "$D\ma-$tenTac.txt"; Remove-Item $fMa -EA SilentlyContinue
    $bat = "$D\chay-$tenTac.cmd"
    $noi = "@echo off`r`ncd /d `"" + (Split-Path $tep) + "`"`r`ncall " + $lenh + "`r`n>`"$fMa`" echo %ERRORLEVEL%`r`n"
    [System.IO.File]::WriteAllText($bat, $noi, [System.Text.Encoding]::ASCII)
    $tn = "CS_Thu_$tenTac"
    Unregister-ScheduledTask -TaskName $tn -Confirm:$false -EA SilentlyContinue
    $hd = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument "/c `"$bat`""
    $nd = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
    Register-ScheduledTask -TaskName $tn -Action $hd -Principal $nd -Force | Out-Null
    $unTruoc = @(Lay-Un-Chi-Tiet | ForEach-Object { $_.khoa })
    $t0 = Get-Date
    Start-ScheduledTask -TaskName $tn
    $kl = 'xong'; $gc = ''; $daDong = $false; $sigCu = -1; $tDung = Get-Date; $lan = 0
    while ($true) {
        Start-Sleep -Seconds 2; $lan++
        if (Test-Path $fMa) { break }
        $gi = ((Get-Date) - $t0).TotalSeconds
        $pCmd = @(Get-CimInstance Win32_Process -Filter "Name='cmd.exe'" -EA SilentlyContinue |
                  Where-Object { $_.CommandLine -like "*chay-$tenTac.cmd*" })
        $pCai = @(); foreach ($c in $pCmd) { $pCai += @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$($c.ProcessId)" -EA SilentlyContinue) }
        if ($gi -ge $gioiHan) {
            $cl = @($pCai | ForEach-Object { $_.Name })
            foreach ($c in $pCmd) { & taskkill /PID $c.ProcessId /F 2>&1 | Out-Null }
            foreach ($q in $pCai) { & taskkill /PID $q.ProcessId /F 2>&1 | Out-Null }
            $kl = 'qua_gio'
            $gc = "Van chay sau $gioiHan giay (thuong la dang cho nguoi bam nut vi tham so khong im lang): " + ($cl -join ', ')
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
                $moi = @(Lay-Un-Chi-Tiet | Where-Object { $unTruoc -notcontains $_.khoa })
                if ($moi.Count -gt 0 -or $tenTac -eq 'go') {
                    $cl = @($pCai | ForEach-Object { $_.Name })
                    foreach ($c in $pCmd) { & taskkill /PID $c.ProcessId /F 2>&1 | Out-Null }
                    foreach ($q in $pCai) { & taskkill /PID $q.ProcessId /F 2>&1 | Out-Null }
                    $daDong = $true; $kl = 'khong_tu_thoat'
                    $gc = 'Xong nhung bo cai khong tu thoat (Console System dong no sau 60 giay): ' + ($cl -join ', ')
                    break
                }
            }
        }
        if ($lan % 10 -eq 0 -and $gi -gt 5 -and (Get-ScheduledTask -TaskName $tn -EA SilentlyContinue).State -ne 'Running') {
            Start-Sleep -Milliseconds 800
            if (-not (Test-Path $fMa)) { $kl = 'dung_bat_thuong'; $gc = 'Tac vu ket thuc ma khong ghi ma thoat'; break }
        }
    }
    $giay = [int]((Get-Date) - $t0).TotalSeconds
    $ma = $null
    if ((Test-Path $fMa) -and -not $daDong) { $m = 0; if ([int]::TryParse(((Get-Content $fMa -Raw) + '').Trim(), [ref]$m)) { $ma = $m } }
    if ($kl -eq 'xong' -and $ma -ne $null -and $ma -ne 0 -and $ma -ne 3010 -and $ma -ne 1605) { $kl = 'loi'; $gc = "Ma thoat $ma" }
    Unregister-ScheduledTask -TaskName $tn -Confirm:$false -EA SilentlyContinue
    return [ordered]@{ lenh = $lenh; ket_luan = $kl; ma_thoat = $ma; giay = $giay; ghi_chu = $gc }
}

# ------------------------------------------------ pha 1: cai
$unTruocCT = @(Lay-Un-Chi-Tiet); $pfTruoc = @(Lay-Thu-Muc); $lnkTruoc = @(Lay-Lnk)
$khoaTruoc = @($unTruocCT | ForEach-Object { $_.khoa })
if ($tep -like '*.msi') { $lenhCai = 'msiexec /i "' + $tep + '" ' + $cfg.tham_so }
else { $lenhCai = '"' + $tep + '" ' + $cfg.tham_so }
$rCai = Chay-Buoc $lenhCai $toiDa 'cai'
Start-Sleep -Seconds 3
$unMoi = @(Lay-Un-Chi-Tiet | Where-Object { $khoaTruoc -notcontains $_.khoa })
$pfMoi = @(Lay-Thu-Muc | Where-Object { $pfTruoc -notcontains $_ })
$lnkMoi = @(Lay-Lnk | Where-Object { $lnkTruoc -notcontains $_ })

# lenh go im lang goi y (tu UninstallString cua cac muc moi) - luon tinh, de ghi vao kho
function Suy-Lenh-Go($e) {
    if ($e.go_im) { return $e.go_im }
    $u = $e.go
    if (-not $u) { return $null }
    if ($e.msi -or $u -match 'msiexec') {
        $g = [regex]::Match($u, '\{[0-9A-Fa-f-]{36}\}').Value
        if ($g) { return "msiexec /x $g /qn /norestart" }
    }
    if ($u -match 'unins\d*\.exe') { return "$u /VERYSILENT /NORESTART /SUPPRESSMSGBOXES" }
    if ($u -match 'uninst') { return "$u /S" }
    return $u
}
$goiY = @($unMoi | ForEach-Object { [ordered]@{ ten = $_.ten; ban = $_.ban; uninstall_string = $_.go; quiet_string = $_.go_im
                                                 goi_y_go_im_lang = (Suy-Lenh-Go $_) } })

# ------------------------------------------------ pha 2: go
$cacGo = @(); $sachKhong = $null; $conLaiSauGo = @()
$goCai = $cfg.go_cai
if ($goCai -and $rCai.ket_luan -in 'xong', 'khong_tu_thoat') {
    $lenhGo = @()
    if ($goCai -eq 'auto') {
        foreach ($e in $unMoi) {
            if ($e.ten -match 'WebView2|Visual C\+\+|\.NET|Windows Driver') { continue }
            $l = Suy-Lenh-Go $e; if ($l) { $lenhGo += $l }
        }
    } else {
        $l = $goCai.Replace('{BOCAI}', '"' + $tep + '"')
        if ($l.StartsWith('/') -or $l.StartsWith('-')) { $l = '"' + $tep + '" ' + $l }
        $lenhGo += $l
    }
    $n = 0
    foreach ($l in $lenhGo) { $n++; $cacGo += (Chay-Buoc $l ([Math]::Min($toiDa, 300)) "go$n") }
    Start-Sleep -Seconds 3
    $khoaMoi = @($unMoi | ForEach-Object { $_.khoa })
    $conLaiSauGo = @(Lay-Un-Chi-Tiet | Where-Object { $khoaMoi -contains $_.khoa } | ForEach-Object { $_.ten })
    $thuMucCon = @($pfMoi | Where-Object { Test-Path $_ })
    $sachKhong = [ordered]@{ muc_go_cai_con_lai = $conLaiSauGo; thu_muc_con_lai = $thuMucCon
                             sach = (($conLaiSauGo.Count -eq 0) -and ($thuMucCon.Count -eq 0)) }
}

$kq = [ordered]@{
    tep = (Split-Path $tep -Leaf); tham_so = $cfg.tham_so; ket_luan = $rCai.ket_luan; ma_thoat = $rCai.ma_thoat; giay = $rCai.giay
    ghi_chu = $rCai.ghi_chu
    muc_go_cai_moi = @($unMoi | ForEach-Object { $_.ten })
    thu_muc_moi = $pfMoi
    loi_tat_moi = $lnkMoi
    goi_y_go = $goiY
    go = $cacGo
    sau_go = $sachKhong
}
[System.IO.File]::WriteAllText($Out, ($kq | ConvertTo-Json -Depth 6), (New-Object System.Text.UTF8Encoding($false)))
Start-Sleep -Seconds 2
shutdown /s /t 3 /f
