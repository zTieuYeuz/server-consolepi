# ============================================================
#  Console Pi - dieu phoi cai dat sau khi dang nhap
#  Tu sinh theo kich ban, KHONG sua bang tay (se bi ghi de lan cai sau).
# ============================================================
$ErrorActionPreference = 'Continue'
$Pi         = '192.168.98.1'
$TenMay     = $env:COMPUTERNAME
$KichBan    = '(khong ten)'
$HanGioGiay = 2700

$Buoc = @(
  @{ Ten='Đặt mạng ở chế độ riêng tư'; Lenh='powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetConnectionProfile | Where-Object { $_.NetworkCategory -ne ''DomainAuthenticated'' } | Set-NetConnectionProfile -NetworkCategory Private"'; HeThong=$true },
  @{ Ten='Bật .NET Framework 3.5 (tải qua mạng)'; Lenh='dism /online /enable-feature /featurename:NetFx3 /all /norestart'; HeThong=$false },
  @{ Ten='Xoá lối tắt Edge trên desktop'; Lenh='cmd /c del /q "%PUBLIC%\Desktop\Microsoft Edge.lnk" "%USERPROFILE%\Desktop\Microsoft Edge.lnk" 2>nul'; HeThong=$false },
  @{ Ten='Gỡ 3 ứng dụng kèm sẵn'; Lenh='powershell -NoProfile -ExecutionPolicy Bypass -Command "$ds=@(''Microsoft.BingNews'',''Microsoft.BingWeather'',''Microsoft.GetHelp'');foreach($t in $ds){Get-AppxPackage -Name $t -AllUsers -EA SilentlyContinue | Remove-AppxPackage -AllUsers -EA SilentlyContinue;Get-AppxProvisionedPackage -Online -EA SilentlyContinue | Where-Object {$_.DisplayName -eq $t} | Remove-AppxProvisionedPackage -Online -EA SilentlyContinue}"'; HeThong=$false },
  @{ Ten='Lệnh thêm'; Lenh='echo xin chao'; HeThong=$false },
  @{ Ten='Lệnh thêm'; Lenh='echo dong hai'; HeThong=$false }
)

$ThuMuc = 'C:\ConsolePi'
if (-not (Test-Path $ThuMuc)) { New-Item -ItemType Directory -Path $ThuMuc -Force | Out-Null }
$Log = Join-Path $ThuMuc 'tien-trinh.log'

function Ghi($t) {
    Add-Content -Path $Log -Value ((Get-Date -Format 'HH:mm:ss') + '  ' + $t) `
        -Encoding UTF8 -EA SilentlyContinue
}

# Bao ve Pi. TUYET DOI khong duoc lam dung qua trinh cai: loi thi bo qua,
# han gio ngan (4 giay) vi Pi co the da bi rut day mang tu luc nao.
# PHAI gui BYTE UTF-8: Windows PowerShell 5.1 ma hoa -Body kieu chuoi theo
# ISO-8859-1 -> ten buoc tieng Viet thanh byte khong hop le UTF-8, Pi khong
# doc duoc goi "batdau" (loi that 25/09/2026: trang Tien trinh hien ban ghi
# "?" 0/0 va cac buoc chi con ten "Buoc 1, Buoc 2...").
# Moi tien trinh con/chau cua 1 tien trinh (bo cai co the de ra nhieu tang)
function LayConChau($idCha) {
    $ra = @()
    foreach ($c in @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$idCha" -EA SilentlyContinue)) {
        $ra += $c; $ra += @(LayConChau $c.ProcessId)
    }
    return $ra
}

# Ma dong Lich su (deploy.cmd ghi luc con o WinPE) - gui kem moi goi de Pi noi dong lich su
# cua may nay voi ten may + ket qua cac buoc (ui/lichsu.py). Khong co file -> bo qua.
$LsId = (Get-Content (Join-Path $ThuMuc 'ls-id.txt') -EA SilentlyContinue | Select-Object -First 1)
function BaoPi($duong, $goi) {
    try {
        if ($LsId -and ($goi -is [hashtable])) { $goi['ls'] = "$LsId".Trim() }
        $byte = [System.Text.Encoding]::UTF8.GetBytes(($goi | ConvertTo-Json -Compress))
        Invoke-RestMethod -Uri "http://$Pi/api/tiendo/$duong" -Method Post `
            -Body $byte -ContentType 'application/json; charset=utf-8' `
            -TimeoutSec 4 | Out-Null
    } catch { }
}

# ------------------------------------------------------------ cua so
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

$frm = New-Object System.Windows.Forms.Form
$frm.Text = "Console System - Đang cài đặt phần mềm"
$frm.Size = New-Object System.Drawing.Size(720, 520)
$frm.StartPosition = 'CenterScreen'
$frm.BackColor = [System.Drawing.Color]::FromArgb(24, 26, 30)
$frm.TopMost = $true
# Khong cho dong giua chung: dong cua so KHONG dung duoc viec cai dang
# chay ngam, chi lam mat cho theo doi - de lai nguoi dung tuong da xong.
$frm.FormBorderStyle = 'FixedSingle'
$frm.MaximizeBox = $false
$frm.ControlBox = $false

$lblTo = New-Object System.Windows.Forms.Label
$lblTo.Text = "Đang cài đặt phần mềm cho máy này"
$lblTo.ForeColor = [System.Drawing.Color]::White
$lblTo.Font = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$lblTo.Location = New-Object System.Drawing.Point(18, 14)
$lblTo.Size = New-Object System.Drawing.Size(660, 30)
$frm.Controls.Add($lblTo)

$lblPhu = New-Object System.Windows.Forms.Label
$lblPhu.Text = "Kịch bản: $KichBan   —   Xin đừng tắt máy trong lúc đang cài."
$lblPhu.ForeColor = [System.Drawing.Color]::FromArgb(150, 158, 170)
$lblPhu.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$lblPhu.Location = New-Object System.Drawing.Point(20, 46)
$lblPhu.Size = New-Object System.Drawing.Size(660, 20)
$frm.Controls.Add($lblPhu)

$thanh = New-Object System.Windows.Forms.ProgressBar
$thanh.Location = New-Object System.Drawing.Point(20, 74)
$thanh.Size = New-Object System.Drawing.Size(660, 16)
$thanh.Minimum = 0
$thanh.Maximum = [Math]::Max(1, $Buoc.Count)
$frm.Controls.Add($thanh)

$lv = New-Object System.Windows.Forms.ListView
$lv.Location = New-Object System.Drawing.Point(20, 102)
$lv.Size = New-Object System.Drawing.Size(660, 330)
$lv.View = 'Details'
$lv.FullRowSelect = $true
$lv.GridLines = $false
$lv.BackColor = [System.Drawing.Color]::FromArgb(31, 34, 39)
$lv.ForeColor = [System.Drawing.Color]::White
$lv.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$lv.Columns.Add("", 40) | Out-Null
$lv.Columns.Add("Bước", 400) | Out-Null
$lv.Columns.Add("Trạng thái", 130) | Out-Null
$lv.Columns.Add("Giây", 70) | Out-Null
$frm.Controls.Add($lv)

foreach ($b in $Buoc) {
    $it = New-Object System.Windows.Forms.ListViewItem("")
    $it.SubItems.Add($b.Ten) | Out-Null
    $it.SubItems.Add("chờ...") | Out-Null
    $it.SubItems.Add("") | Out-Null
    $it.ForeColor = [System.Drawing.Color]::FromArgb(130, 138, 150)
    $lv.Items.Add($it) | Out-Null
}

$lblDay = New-Object System.Windows.Forms.Label
$lblDay.Text = ""
$lblDay.ForeColor = [System.Drawing.Color]::FromArgb(150, 158, 170)
$lblDay.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$lblDay.Location = New-Object System.Drawing.Point(20, 442)
$lblDay.Size = New-Object System.Drawing.Size(520, 22)
$frm.Controls.Add($lblDay)

$btnDong = New-Object System.Windows.Forms.Button
$btnDong.Text = "Đóng"
$btnDong.Location = New-Object System.Drawing.Point(580, 438)
$btnDong.Size = New-Object System.Drawing.Size(100, 32)
$btnDong.Enabled = $false          # chi bat khi da cai xong het
$btnDong.Add_Click({ $frm.Close() })
$frm.Controls.Add($btnDong)

$frm.Show()
[System.Windows.Forms.Application]::DoEvents()

function DatDong($i, $bieu, $tt, $giay, $mau) {
    $lv.Items[$i].Text = $bieu
    $lv.Items[$i].SubItems[2].Text = $tt
    $lv.Items[$i].SubItems[3].Text = $giay
    $lv.Items[$i].ForeColor = $mau
    $lv.EnsureVisible($i)
    [System.Windows.Forms.Application]::DoEvents()
}

$XANH  = [System.Drawing.Color]::FromArgb(110, 231, 160)
$VANG  = [System.Drawing.Color]::FromArgb(245, 158, 11)
$DO    = [System.Drawing.Color]::FromArgb(255, 107, 107)
$XAM   = [System.Drawing.Color]::FromArgb(130, 138, 150)

Ghi "===== Bat dau cai dat: $KichBan ====="
BaoPi 'batdau' @{ may = $TenMay; kichban = $KichBan;
                   buoc = @($Buoc | ForEach-Object { $_.Ten }) }

$i = 0
$soLoi = 0
# Ket qua tung buoc -> bao-cao.ps1 doc lai de BAO CAO co ca script, lenh
# them, cai/go phan mem (truoc day bao cao khong nhac toi cac viec nay).
$KetQuaBuoc = New-Object System.Collections.Generic.List[object]
foreach ($b in $Buoc) {
    $lblDay.Text = "Đang làm bước $($i + 1) / $($Buoc.Count)..."
    DatDong $i ">" "đang chạy..." "" $VANG
    Ghi ("[{0}/{1}] {2}" -f ($i + 1), $Buoc.Count, $b.Ten)
    BaoPi 'buoc' @{ may = $TenMay; chi_so = $i; trang_thai = 'dang';
                     ten = $b.Ten; kichban = $KichBan; tong = $Buoc.Count }

    $t0 = Get-Date
    $tt = 'xong'; $ghiChu = ''
    try {
      if ($b.HeThong) {
        # Buoc CAI phan mem: chay ngam bang SYSTEM qua tac vu hen gio, cho file ma
        # thoat (xem _danh_sach_buoc_nguoi_dung: bo cai tu mo app trong phien nguoi
        # dung thi khong bao gio thoat). ">file echo" (khong phai "echo 0>file": 0> la
        # chuyen huong luong 0 cua cmd).
        $fCmd = Join-Path $ThuMuc "buoc-$i.cmd"; $fMa = Join-Path $ThuMuc "buoc-$i.ma"
        Remove-Item $fMa -Force -EA SilentlyContinue
        Set-Content -Path $fCmd -Encoding Default -Value ("@echo off`r`n" + $b.Lenh +
            "`r`n>""$fMa"" echo %ERRORLEVEL%")
        $tn = "ConsolePi-Cai-$i"
        $act = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument ('/c "' + $fCmd + '"')
        $pri = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
        $set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
               -ExecutionTimeLimit (New-TimeSpan -Seconds ($HanGioGiay + 120))
        Register-ScheduledTask -TaskName $tn -Action $act -Principal $pri -Settings $set -Force | Out-Null
        # Danh sach phan mem da cai TRUOC buoc nay (de nhan ra phan mem moi)
        $kUn = @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
                 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall')
        $unTruoc = @($kUn | ForEach-Object { Get-ChildItem $_ -EA SilentlyContinue } | ForEach-Object { $_.PSChildName })
        Start-ScheduledTask -TaskName $tn
        $lan = 0; $sigCu = -1; $tDung = Get-Date; $daDong = $false
        while (-not (Test-Path $fMa)) {
            Start-Sleep -Milliseconds 300
            $gi = [int]((Get-Date) - $t0).TotalSeconds
            $lv.Items[$i].SubItems[3].Text = "$gi"
            [System.Windows.Forms.Application]::DoEvents()
            if ($gi -ge $HanGioGiay) {
                Stop-ScheduledTask -TaskName $tn -EA SilentlyContinue
                $tt = 'qua_gio'
                $ghiChu = "Quá $HanGioGiay giây — đã dừng bước này để đi tiếp"
                break
            }
            # BO CAI KHONG TU THOAT (lab 03/10/2026: TeamViewer_Setup /S khi da co nguoi
            # dang nhap cai xong, mo TeamViewer roi DUNG DO mai, ca khi chay bang SYSTEM).
            # Coi la XONG khi CA HAI: (1) Windows da ghi nhan phan mem MOI (khoa Uninstall
            # moi) va (2) chinh bo cai dung yen 60 giay (khong CPU, khong doc/ghi) - chi
            # xay ra khi da cai xong that, khong dong nham bo cai dang chay do.
            if ($lan % 15 -eq 0 -and $gi -ge 60) {
                $pCmd = @(Get-CimInstance Win32_Process -Filter "Name='cmd.exe'" -EA SilentlyContinue |
                          Where-Object { $_.CommandLine -like "*buoc-$i.cmd*" })
                $pCai = @()
                foreach ($c in $pCmd) { $pCai += @(LayConChau $c.ProcessId) }
                # Hieu hoat dong = bo cai + moi con chau + CA dich vu msiexec: bo cai kieu setup.exe goi
                # MSI thi tien trinh con dung yen cho msiexec lam viec -> neu khong tinh msiexec se
                # tuong nham "dung yen" roi giet bo cai giua chung (lab 04/10/2026: OpenOffice, Acrobat).
                $sig = 0
                foreach ($q in ($pCai + @(Get-CimInstance Win32_Process -Filter "Name='msiexec.exe'" -EA SilentlyContinue))) {
                    $sig += [double]$q.KernelModeTime + [double]$q.UserModeTime +
                            [double]$q.ReadTransferCount + [double]$q.WriteTransferCount + [double]$q.OtherTransferCount
                }
                if ($sig -ne $sigCu) { $sigCu = $sig; $tDung = Get-Date }
                elseif ($pCai.Count -gt 0 -and ((Get-Date) - $tDung).TotalSeconds -ge 60) {
                    # Bo qua WebView2/Edge: Windows tu cai chung ngam, khong phai phan mem cua buoc nay
                    $unMoi = @($kUn | ForEach-Object { Get-ChildItem $_ -EA SilentlyContinue } |
                               Where-Object { ($unTruoc -notcontains $_.PSChildName) -and
                                   ((Get-ItemProperty $_.PSPath -EA SilentlyContinue).DisplayName -notmatch 'WebView2|Microsoft Edge') })
                    if ($unMoi.Count -gt 0) {
                        # Dong cmd TRUOC (khong thi cmd kip ghi ma thoat cua bo cai bi dong
                        # = 1 -> bao nham "loi", lab 03/10/2026), roi moi dong bo cai
                        foreach ($c in $pCmd) { & taskkill /PID $c.ProcessId /F 2>&1 | Out-Null }
                        foreach ($q in $pCai) { & taskkill /PID $q.ProcessId /F 2>&1 | Out-Null }
                        $daDong = $true
                        Stop-ScheduledTask -TaskName $tn -EA SilentlyContinue
                        $ghiChu = 'Đã cài xong (bộ cài không tự thoát - đã đóng bộ cài)'
                        break
                    }
                }
            }
            # Tac vu ket thuc ma khong ghi ma (cmd bi giet...) -> loi, khong cho mai.
            # CHI tin trang thai DUNG RO RANG (Ready/Disabled), 2 lan cach nhau 2 giay. LOI THAT (thu
            # may mau 08/10/2026, buoc "Dat mang rieng tu"): luc Windows doi cau hinh mang, Get-ScheduledTask
            # tra ve RONG 1 lan -> ban cu coi rong la "khong chay" -> bao nham "Bo cai dung bat thuong" du
            # buoc chay xong, ma thoat 0. Rong / Queued = chua biet -> cho tiep (van con han gio o tren).
            $lan++
            if ($lan % 10 -eq 0 -and $gi -gt 5) {
                $st = [string](Get-ScheduledTask -TaskName $tn -EA SilentlyContinue).State
                if ($st -eq 'Ready' -or $st -eq 'Disabled') {
                    Start-Sleep -Milliseconds 2000
                    $st2 = [string](Get-ScheduledTask -TaskName $tn -EA SilentlyContinue).State
                    if (-not (Test-Path $fMa) -and ($st2 -eq 'Ready' -or $st2 -eq 'Disabled')) {
                        $tt = 'loi'; $ghiChu = 'Bộ cài dừng bất thường'; break
                    }
                }
            }
        }
        if ($tt -eq 'xong' -and -not $daDong -and (Test-Path $fMa)) {
            $ma = 0; [int]::TryParse(((Get-Content $fMa -Raw -EA SilentlyContinue) + '').Trim(), [ref]$ma) | Out-Null
            # 3010 = cai xong, can khoi dong lai (msiexec) - van tinh la xong
            if ($ma -ne 0 -and $ma -ne 3010) { $tt = 'loi'; $ghiChu = "Mã lỗi: $ma" }
        }
        Unregister-ScheduledTask -TaskName $tn -Confirm:$false -EA SilentlyContinue
        Remove-Item $fCmd, $fMa -Force -EA SilentlyContinue
      } else {
        $p = Start-Process -FilePath 'cmd.exe' `
             -ArgumentList '/c', $b.Lenh -PassThru -WindowStyle Hidden
        # Vong cho NGAN + DoEvents: giu cua so song va dem giay. Neu dung
        # WaitForExit() mot mach thi Windows bao "Not Responding" va lam
        # mo cua so - nhin y het treo may.
        while (-not $p.HasExited) {
            Start-Sleep -Milliseconds 300
            $gi = [int]((Get-Date) - $t0).TotalSeconds
            $lv.Items[$i].SubItems[3].Text = "$gi"
            [System.Windows.Forms.Application]::DoEvents()
            if ($gi -ge $HanGioGiay) {
                try { & taskkill /PID $p.Id /T /F 2>&1 | Out-Null } catch { }
                $tt = 'qua_gio'
                $ghiChu = "Quá $HanGioGiay giây — đã dừng bước này để đi tiếp"
                break
            }
        }
        if ($tt -eq 'xong' -and $p.ExitCode -ne 0) {
            $tt = 'loi'; $ghiChu = "Mã lỗi: $($p.ExitCode)"
        }
      }
    } catch {
        $tt = 'loi'; $ghiChu = $_.Exception.Message
    }

    $giay = [int]((Get-Date) - $t0).TotalSeconds
    if ($tt -eq 'xong') {
        DatDong $i ([char]0x2714) "xong" "$giay" $XANH
    } elseif ($tt -eq 'qua_gio') {
        $soLoi++
        DatDong $i ([char]0x2718) "quá giờ" "$giay" $DO
    } else {
        $soLoi++
        DatDong $i ([char]0x2718) "lỗi" "$giay" $DO
    }
    Ghi ("      -> {0} ({1}s) {2}" -f $tt, $giay, $ghiChu)
    $KetQuaBuoc.Add([PSCustomObject]@{ Ten = $b.Ten; TrangThai = $tt;
                                         Giay = $giay; GhiChu = $ghiChu })
    BaoPi 'buoc' @{ may = $TenMay; chi_so = $i; trang_thai = $tt;
                     giay = $giay; ghi_chu = $ghiChu;
                     ten = $b.Ten; kichban = $KichBan; tong = $Buoc.Count }

    $thanh.Value = [Math]::Min($thanh.Maximum, $i + 1)
    [System.Windows.Forms.Application]::DoEvents()
    $i++
}

Ghi "===== Xong ====="
# 'ketthuc' gui SAU khi bao cao da ghi ra dia (ben duoi) - lab 26/09/2026:
# Pi bao "da xong" truoc, tat may ngay luc do thi thu muc ConsolePi KHONG co
# bao cao (bao-cao.ps1 mat ~30s de kiem).
try {
    $KetQuaBuoc | ConvertTo-Json -Depth 3 |
        Out-File (Join-Path $ThuMuc 'ket-qua-tien-trinh.json') -Encoding UTF8
} catch { }

# ------------------------------------------------- bao cao tong ket
#
# 1 CUA SO DUY NHAT moi luc (anh Thoai 08/10/2026): dang cai -> cua so tien trinh; cai xong -> cua so
# tien trinh TU DONG, chi con POPUP tong ket. Bao cao chay o TIEN TRINH RIENG, KHONG CO console
# (conhost --headless), sau khi vong lap cac buoc da xong han.
#
# Vi sao van la tien trinh rieng ma khong goi ngay trong script nay: bao-cao.ps1 mat ~30 giay de kiem
# lai may; chay chung luong thi cua so tien trinh dung hinh ("Not Responding"). Trong luc cho, cua so
# tien trinh noi ro "dang kiem tra lai".
#
# LOI THAT DA GAP (13/09): bao-cao tung la 1 FirstLogonCommand rieng -> hien ra khi tien trinh moi
# toi buoc 6/11. Nen bao cao CHI duoc goi tu day, sau vong lap.
$lblTo.Text = "Đã cài xong - đang kiểm tra lại kết quả"
$lblDay.Text = "Đang kiểm tra lại toàn bộ máy (khoảng 30 giây). Bảng tổng kết sẽ hiện ngay sau đó..."
$lblDay.ForeColor = $XAM
$thanh.Value = $thanh.Maximum
[System.Windows.Forms.Application]::DoEvents()

# Chay 1 script PowerShell KHONG co cua so console nao (xem LENH_MO_TIEN_TRINH ben Python)
function ChayAn($ps1) {
    $ps = Join-Path $env:windir 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $ch = Join-Path $env:windir 'System32\conhost.exe'
    $tham = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', $ps1)
    if ([Environment]::OSVersion.Version.Build -ge 17763 -and (Test-Path $ch)) {
        return Start-Process -FilePath $ch -ArgumentList (@('--headless', $ps) + $tham) -PassThru
    }
    return Start-Process -FilePath $ps -ArgumentList $tham -PassThru -WindowStyle Hidden
}

$daBao = $false
$coPopup = $false
$baoCao = Join-Path $ThuMuc 'bao-cao.ps1'
if (Test-Path $baoCao) {
    $fBaoCao = Join-Path $ThuMuc 'bao-cao-day-du.json'
    Remove-Item $fBaoCao -ErrorAction SilentlyContinue
    try {
        $pBc = ChayAn $baoCao
        # bao-cao.ps1 GHI FILE KET QUA xong roi moi mo popup -> co file = popup sap hien
        for ($k = 0; $k -lt 600 -and -not (Test-Path $fBaoCao) -and -not $pBc.HasExited; $k++) {
            Start-Sleep -Milliseconds 300
            [System.Windows.Forms.Application]::DoEvents()
        }
        if ((Test-Path $fBaoCao) -and -not $pBc.HasExited) {
            $coPopup = $true
            Start-Sleep -Milliseconds 700          # de popup kip ve len truoc khi cua so nay dong
            $frm.Close(); $frm.Dispose()           # chi con popup tong ket
        }
        BaoPi 'ketthuc' @{ may = $TenMay }
        $daBao = $true
        if ($coPopup) { $pBc.WaitForExit() }
    } catch { Ghi "Khong mo duoc bao cao: $($_.Exception.Message)" }
}
if (-not $daBao) { BaoPi 'ketthuc' @{ may = $TenMay } }
if ($coPopup) { exit 0 }

# KHONG mo duoc popup tong ket (thieu bao-cao.ps1, bao cao loi...): GIU cua so tien trinh lam ket qua,
# co nut Dong - nguoi di cai may van phai doc duoc buoc nao hong (ly do cua ca cua so nay).
if ($soLoi -eq 0) {
    $lblDay.Text = "Xong tất cả $($Buoc.Count) bước. Không có lỗi."
    $lblDay.ForeColor = $XANH
} else {
    $lblDay.Text = "Xong, nhưng có $soLoi bước không đạt — xem dòng màu đỏ."
    $lblDay.ForeColor = $DO
}
$lblTo.Text = "Đã cài đặt xong"
$btnDong.Enabled = $true
$frm.ControlBox = $true
$frm.TopMost = $false
# KHONG dung ShowDialog() len form da Show() (.NET nem loi, script chet, cua so bien mat) - bom thong diep.
while (-not $frm.IsDisposed) {
    [System.Windows.Forms.Application]::DoEvents()
    Start-Sleep -Milliseconds 120
}
