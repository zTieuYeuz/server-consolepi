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

# Windows tu cai nen "Microsoft Edge WebView2 Runtime" (va cap nhat Edge) vao luc nao do sau khi
# bat may -> lan vao ket qua cua moi phan mem (lab 04/10/2026: bao "cai duoc" chi vi WebView2 moi
# xuat hien, bo cai that bi giet nham o giay thu 60). Loai han ra khoi moi phep so sanh.
$LoaiTru = 'WebView2|Microsoft Edge'
function Lay-Un-Chi-Tiet {
    foreach ($k in 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
                   'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall') {
        Get-ChildItem $k -EA SilentlyContinue | ForEach-Object {
            $p = Get-ItemProperty $_.PSPath -EA SilentlyContinue
            if ($p.DisplayName -and $p.DisplayName -notmatch $LoaiTru) {
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

# Tat ca tien trinh con/chau cua 1 tien trinh (bo cai co the de ra nhieu tang: setup.exe -> msiexec...)
function Lay-Con-Chau($idCha) {
    $ra = @()
    foreach ($c in @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$idCha" -EA SilentlyContinue)) {
        $ra += $c; $ra += @(Lay-Con-Chau $c.ProcessId)
    }
    return $ra
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
        $pCai = @(); foreach ($c in $pCmd) { $pCai += @(Lay-Con-Chau $c.ProcessId) }
        if ($gi -ge $gioiHan) {
            $cl = @($pCai | ForEach-Object { $_.Name })
            foreach ($c in $pCmd) { & taskkill /PID $c.ProcessId /F 2>&1 | Out-Null }
            foreach ($q in $pCai) { & taskkill /PID $q.ProcessId /F 2>&1 | Out-Null }
            $kl = 'qua_gio'
            $gc = "Van chay sau $gioiHan giay (thuong la dang cho nguoi bam nut vi tham so khong im lang): " + ($cl -join ', ')
            break
        }
        if ($lan % 15 -eq 0 -and $gi -ge 60) {
            # Hieu hoat dong = bo cai + moi con chau + CA dich vu msiexec (bo cai kieu setup.exe goi MSI:
            # tien trinh con dung yen cho msiexec lam viec -> neu khong tinh msiexec se tuong nham
            # "dung yen" va giet bo cai giua chung, lab 04/10/2026: OpenOffice/Acrobat bi giet, msiexec
            # sau do bao 1618 "dang co cai dat khac")
            $sig = 0
            foreach ($q in ($pCai + @(Get-CimInstance Win32_Process -Filter "Name='msiexec.exe'" -EA SilentlyContinue))) {
                $sig += [double]$q.KernelModeTime + [double]$q.UserModeTime + [double]$q.ReadTransferCount +
                        [double]$q.WriteTransferCount + [double]$q.OtherTransferCount
            }
            if ($sig -ne $sigCu) { $sigCu = $sig; $tDung = Get-Date }
            elseif ($pCai.Count -gt 0 -and ((Get-Date) - $tDung).TotalSeconds -ge 60) {
                $moi = @(Lay-Un-Chi-Tiet | Where-Object { $unTruoc -notcontains $_.khoa })
                if ($moi.Count -gt 0 -or $tenTac -like 'go*') {
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
Start-Sleep -Seconds 45     # cho Windows xong cac viec nen luc moi bat may roi moi chup "truoc"
if ($tep -like '*.msi') { $lenhCai = 'msiexec /i "' + $tep + '" ' + $cfg.tham_so }
else { $lenhCai = '"' + $tep + '" ' + $cfg.tham_so }
# Lenh chuan bi truoc khi cai (vd tin cay chung chi nha phat hanh driver): cfg.truoc_cai, ngan cach " ;; "
$truoc = @()
if ($cfg.truoc_cai) {
    $n0 = 0
    foreach ($l in @($cfg.truoc_cai -split ' ;; ' | ForEach-Object { $_.Trim() } | Where-Object { $_ })) {
        $n0++; $truoc += (Chay-Buoc $l 120 "truoc$n0")
    }
}
# chup "truoc" SAU cac lenh chuan bi (vd go ban co san trong may vang) de bang chung chi tinh phan bo cai them vao
$unTruocCT = @(Lay-Un-Chi-Tiet); $pfTruoc = @(Lay-Thu-Muc); $lnkTruoc = @(Lay-Lnk)
$khoaTruoc = @($unTruocCT | ForEach-Object { $_.khoa })
$rCai = Chay-Buoc $lenhCai $toiDa 'cai'
Start-Sleep -Seconds 3
$unMoi = @(Lay-Un-Chi-Tiet | Where-Object { $khoaTruoc -notcontains $_.khoa })
$pfMoi = @(Lay-Thu-Muc | Where-Object { $pfTruoc -notcontains $_ })
$lnkMoi = @(Lay-Lnk | Where-Object { $lnkTruoc -notcontains $_ })

# BANG CHUNG DA CAI THAT - chup NGAY SAU KHI CAI, TRUOC khi go (go xong thi file/loi tat deu mat)
$bangChung = @()
foreach ($m in $unMoi) { $bangChung += "muc go cai dat: $($m.ten)" }
foreach ($f in $pfMoi) {
    $tep0 = @(Get-ChildItem $f -Recurse -File -EA SilentlyContinue)
    $ct = @($tep0 | Where-Object { ($_.Extension -eq '.exe' -or $_.Extension -eq '.dll') -and $_.Name -notlike 'unins*' })
    if ($ct.Count -gt 0) { $bangChung += "thu muc ${f}: $($tep0.Count) file, $($ct.Count) exe/dll" }
}
foreach ($l in $lnkMoi) { if (Test-Path $l) { $bangChung += "loi tat: $l" } }

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
# Thu lan luot cac ung vien lenh go IM LANG cho tung muc moi, dung o ung vien lam khoa Uninstall
# bien mat. go_cai: "auto" = suy tu UninstallString; "<lenh>" = chay dung lenh do ({BOCAI} = bo cai;
# bat dau bang / hoac - thi la tham so cua chinh bo cai); nhieu muc ngan cach bang " ;; ".
function Ung-Vien-Go($e) {
    $c = @()
    if ($e.go_im) { $c += $e.go_im }
    $u = $e.go
    if ($u) {
        if ($e.msi -or $u -match 'msiexec') {
            $g = [regex]::Match($u, '\{[0-9A-Fa-f-]{36}\}').Value
            if ($g) { $c += "msiexec /x $g /qn /norestart" }
        } elseif ($u -match 'unins\d*\.exe') {
            $c += "$u /VERYSILENT /NORESTART /SUPPRESSMSGBOXES"; $c += "$u /SILENT /NORESTART"
        } else {
            $duong = [regex]::Match($u, '^"?([^"]+?\.exe)"?').Groups[1].Value
            $thuMuc = if ($duong) { Split-Path $duong } else { '' }
            if ($u -match '/uninstall|--uninstall') { $c += "$u /quiet /norestart"; $c += "$u /S" }
            $c += "$u /S"
            if ($thuMuc) { $c += "$u /S _?=$thuMuc" }
            $c += "$u /quiet /norestart"; $c += "$u /silent"; $c += "$u /VERYSILENT /NORESTART"; $c += "$u /qn"
        }
    }
    return ($c | Select-Object -Unique)
}
$cacGo = @(); $sachKhong = $null
$goCai = $cfg.go_cai
if ($goCai -and $rCai.ket_luan -in 'xong', 'khong_tu_thoat') {
    $phan = @($goCai -split ' ;; ' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    $tuDong = ($phan -contains 'auto'); $rieng = @($phan | Where-Object { $_ -ne 'auto' })
    $gioiHanGo = [Math]::Min($toiDa, 900)
    $n = 0
    # muc "goi lon" (bundle/uninstall) go truoc; bo qua runtime dung chung cua he thong
    $ds = @($unMoi | Where-Object { $_.ten -notmatch 'WebView2|\.NET|Windows Driver' } |
            Sort-Object { if (($_.go -match '/uninstall|Package Cache') -or $_.go_im) { 0 } else { 1 } })
    $dsRieng = @($rieng | ForEach-Object { $_.Replace('{BOCAI}', '"' + $tep + '"') } |
                 ForEach-Object { if ($_.StartsWith('/') -or $_.StartsWith('-')) { '"' + $tep + '" ' + $_ } else { $_ } })
    $thuLenh = {
        param($lenh, $khoa)
        $script:n++
        $r = Chay-Buoc $lenh $gioiHanGo ("go" + $script:n)
        Start-Sleep -Seconds 2
        $con = @(Lay-Un-Chi-Tiet | Where-Object { $khoa -contains $_.khoa })
        $r['con_lai'] = $con.Count
        $script:cacGo += $r
        return ($con.Count -eq 0)
    }
    $khoaMoi = @($unMoi | ForEach-Object { $_.khoa })
    foreach ($l in $dsRieng) { if (& $thuLenh $l $khoaMoi) { break } }       # lenh anh dat truoc
    if ($tuDong) {
        foreach ($e in $ds) {
            if (-not (Lay-Un-Chi-Tiet | Where-Object { $_.khoa -eq $e.khoa })) { continue }   # da bi go cung muc khac
            foreach ($l in (Ung-Vien-Go $e)) { if (& $thuLenh $l @($e.khoa)) { break } }
        }
    }
    Start-Sleep -Seconds 3
    $conLaiSauGo = @(Lay-Un-Chi-Tiet | Where-Object { $khoaMoi -contains $_.khoa } | ForEach-Object { $_.ten })
    # thu muc con lai chi tinh khi con FILE ben trong (thu muc hang rong khong tinh)
    $thuMucCon = @($pfMoi | Where-Object { (Test-Path $_) -and (@(Get-ChildItem $_ -Recurse -File -EA SilentlyContinue).Count -gt 0) })
    $sachKhong = [ordered]@{ muc_go_cai_con_lai = $conLaiSauGo; thu_muc_con_lai = $thuMucCon
                             sach = (($conLaiSauGo.Count -eq 0) -and ($thuMucCon.Count -eq 0)) }
}

$kq = [ordered]@{
    tep = (Split-Path $tep -Leaf); tham_so = $cfg.tham_so; ket_luan = $rCai.ket_luan; ma_thoat = $rCai.ma_thoat; giay = $rCai.giay
    ghi_chu = $rCai.ghi_chu
    muc_go_cai_moi = @($unMoi | ForEach-Object { $_.ten })
    thu_muc_moi = $pfMoi
    loi_tat_moi = $lnkMoi
    bang_chung = $bangChung
    truoc_cai = $truoc
    goi_y_go = $goiY
    go = $cacGo
    sau_go = $sachKhong
}
[System.IO.File]::WriteAllText($Out, ($kq | ConvertTo-Json -Depth 6), (New-Object System.Text.UTF8Encoding($false)))
Start-Sleep -Seconds 2
shutdown /s /t 3 /f
