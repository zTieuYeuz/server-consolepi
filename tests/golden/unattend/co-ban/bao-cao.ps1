$TEN_KICHBAN = '(chạy trực tiếp, chưa lưu thành kịch bản)'

$MUC = @(
  @{ Nhom='May'; Nhan='Tên máy'; Loai='ps'; Ma={
        $t = (Get-CimInstance Win32_ComputerSystem).Name
        @{ Dat = ($t -eq 'T1-COBAN'); ChiTiet = $t }
    } },
  @{ Nhom='Phải giữ lại'; Nhan='Microsoft Store'; Loai='ps'; Ma={
            $g = Get-AppxPackage -Name 'Microsoft.WindowsStore' -EA SilentlyContinue
            @{ Dat = ($g -ne $null); ChiTiet = $(if ($g) { 'con nguyen' } else { 'DA BI GO NHAM' }) }
        } },
  @{ Nhom='Phải giữ lại'; Nhan='Máy tính (Calculator)'; Loai='ps'; Ma={
            $g = Get-AppxPackage -Name 'Microsoft.WindowsCalculator' -EA SilentlyContinue
            @{ Dat = ($g -ne $null); ChiTiet = $(if ($g) { 'con nguyen' } else { 'DA BI GO NHAM' }) }
        } },
  @{ Nhom='Vệ sinh'; Nhan='File nội bộ _thongtin.json không lọt sang'; Loai='ps'; Ma={
        $l = @(Get-ChildItem 'C:\ConsolePi\ungdung' -Recurse -Filter '_thongtin.json' -EA SilentlyContinue)
        @{ Dat = ($l.Count -eq 0); ChiTiet = "$($l.Count) file" }
    } }
)

# ============================================================
#  Console Pi - BAO CAO TONG KET SAU KHI CAI
#  (sinh tu dong theo dung kich ban da chay - khong sua tay)
# ============================================================
$ErrorActionPreference = 'SilentlyContinue'

$OutDir  = 'C:\ConsolePi'
$OutFile = Join-Path $OutDir 'BAO-CAO-TONG-KET.txt'
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }

function Doc-Reg($duong, $ten) {
    try { return (Get-ItemProperty -Path $duong -Name $ten -EA Stop).$ten } catch { return $null }
}

$ketQua = @()
foreach ($m in $MUC) {
    $dat = $null; $ct = ''
    switch ($m.Loai) {
        'reg' {
            $that = Doc-Reg $m.Duong $m.Ten
            if ($null -eq $that) { $dat = $false; $ct = 'khong tim thay gia tri' }
            else { $dat = ("$that" -eq "$($m.Gt)"); $ct = "= $that" + $(if (-not $dat) { " (can $($m.Gt))" } else { '' }) }
        }
        'khoa' {
            $dat = Test-Path $m.Duong
            $ct = $(if ($dat) { 'khoa da duoc tao' } else { 'khong thay khoa' })
        }
        'ps' {
            try { $r = & $m.Ma; $dat = $r.Dat; $ct = [string]$r.ChiTiet }
            catch { $dat = $false; $ct = 'loi khi kiem: ' + $_.Exception.Message }
        }
        default { $dat = $null; $ct = 'muc nay khong tu kiem duoc' }
    }
    $ketQua += [PSCustomObject]@{
        Nhom = $m.Nhom; Nhan = $m.Nhan
        Dat = $dat
        ChiTiet = $ct
        TrangThai = $(if ($dat -eq $true) { 'ĐÃ LÀM' } elseif ($dat -eq $false) { 'chưa được' } else { 'không rõ' })
    }
}

# Cac buoc chay SAU KHI dang nhap (tien-trinh.ps1 ghi lai): script, lenh
# them, cai/go phan mem - bao cao ghi ca nhung viec nay. Tuy chon Windows
# thi da doi chieu registry o tren nen khong lap lai.
$fKq = Join-Path $OutDir 'ket-qua-tien-trinh.json'
if (Test-Path $fKq) {
    try {
        # PHAI gan vao bien truoc: PowerShell 5.1 `ConvertFrom-Json` tra CA
        # MANG thanh 1 doi tuong - boc @(...) quanh ong dan thi foreach chi
        # chay 1 lan voi ca mang (loi that lab 26/09/2026: bao cao Win11 khong
        # hien dong "Sau dang nhap" nao du script da chay).
        $dsBuoc = Get-Content $fKq -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($b in $dsBuoc) {
            if ("$($b.Ten)" -notmatch '^(Chạy script|Lệnh thêm|Cài |Gỡ )') { continue }
            $ok = ($b.TrangThai -eq 'xong')
            $ketQua += [PSCustomObject]@{
                Nhom = 'Sau đăng nhập'; Nhan = "$($b.Ten)"
                Dat = $ok
                ChiTiet = $(if ($ok) { "xong ($($b.Giay)s)" } else { "$($b.TrangThai) $($b.GhiChu)" })
                TrangThai = $(if ($ok) { 'ĐÃ LÀM' } else { 'chưa được' })
            }
        }
    } catch { }
}

$soDat   = @($ketQua | Where-Object { $_.Dat -eq $true }).Count
$soHong  = @($ketQua | Where-Object { $_.Dat -eq $false }).Count
$soKhong = @($ketQua | Where-Object { $_.Dat -eq $null }).Count

# ---------- Ghi ra file (luon ghi, du co ai doc popup hay khong) ----------
$txt = New-Object System.Collections.Generic.List[string]
$txt.Add('================================================================')
$txt.Add('   CONSOLE SYSTEM - BÁO CÁO NHỮNG VIỆC ĐÃ LÀM TRÊN MÁY NÀY')
$txt.Add('   Kich ban : ' + $TEN_KICHBAN)
$txt.Add('   May      : ' + $env:COMPUTERNAME + '   |   Nguoi dung: ' + $env:USERNAME)
$txt.Add('   Thoi diem: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
$txt.Add('================================================================')
$txt.Add('')
$txt.Add("   ĐÃ LÀM XONG: $soDat việc")
$txt.Add('')
# File van ban: CHI ghi viec DA LAM XONG, dung y het khoi hien tren cua so.
$cac = @($ketQua | Where-Object { $_.Dat -eq $true })
if ($cac.Count -gt 0) {
    $td = "ĐÃ LÀM XONG ($($cac.Count))"
    $txt.Add('--- ' + $td + ' ' + ('-' * [Math]::Max(0, 50 - $td.Length)))
    foreach ($r in $cac) {
        $txt.Add(('  [{0}] {1,-42} {2}' -f $r.Nhom, $r.Nhan, $r.ChiTiet))
    }
    $txt.Add('')
}
$txt.Add('--- Thong tin them -------------------------------------')
$os = Get-CimInstance Win32_OperatingSystem
$txt.Add('  Windows : ' + $os.Caption + ' (build ' + $os.BuildNumber + ')')
foreach ($c in (Get-NetAdapter -Physical | Where-Object Status -eq 'Up')) {
    $ip = Get-NetIPAddress -InterfaceIndex $c.InterfaceIndex -AddressFamily IPv4 |
          Where-Object { $_.IPAddress -notlike '169.254.*' } | Select-Object -First 1
    $txt.Add('  Mang    : ' + $c.Name + ' - ' + $(if ($ip) { $ip.IPAddress } else { 'chua co IP' }))
}
$thieu = @(Get-CimInstance Win32_PnPEntity | Where-Object { $_.ConfigManagerErrorCode -ne 0 })
$txt.Add('  Thiet bi thieu driver: ' + $thieu.Count)
# Thiet bi chua co driver thuong KHONG co Name (lab 26/09/2026: dong "- "
# trong) -> ghi ma phan cung de biet can tai driver gi.
foreach ($t in $thieu) {
    $ten = if ($t.Name) { $t.Name } else { '(chua co ten)' }
    $txt.Add('      - ' + $ten + '  [' + $t.PNPDeviceID + '] ma loi ' + $t.ConfigManagerErrorCode)
}
$txt -join "`r`n" | Out-File -FilePath $OutFile -Encoding UTF8
# Ban DAY DU (ca muc chua dat) cho ky thuat tra loi - cua so va file .txt chi
# hien viec da xong theo yeu cau anh Thoai, nen muc hong khong duoc mat dau vet.
try { $ketQua | ConvertTo-Json -Depth 3 |
      Out-File -FilePath (Join-Path $OutDir 'bao-cao-day-du.json') -Encoding UTF8 } catch { }

# ---------- Cua so bao cao ----------
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

# Ten bien la $frm chu khong phai $f: cac doan kiem tra rieng o tren co
# dung bien $f (vd Get-WindowsOptionalFeature), de trung ten thi rat kho
# lan ra khi hong.
$frm = New-Object System.Windows.Forms.Form
$frm.Text = 'Console System - Những việc đã làm trên máy này'
$frm.Size = New-Object System.Drawing.Size(940, 720)
$frm.StartPosition = 'CenterScreen'
$frm.BackColor = [System.Drawing.Color]::FromArgb(248, 249, 251)
$frm.TopMost = $true
$frm.MinimumSize = New-Object System.Drawing.Size(700, 480)

# --- Dai mau tren cung: LUON XANH - bao cao gio chi liet ke viec DA LAM,
# khong con danh sach "chua dat" de doi mau canh bao theo nua (xem ly do
# that o cho DoNhom ben duoi).
$mauNen = [System.Drawing.Color]::FromArgb(22, 128, 70)
$head = New-Object System.Windows.Forms.Panel
$head.Dock = 'Top'; $head.Height = 96; $head.BackColor = $mauNen
$frm.Controls.Add($head)

$lblTo = New-Object System.Windows.Forms.Label
$lblTo.Text = "Đã làm xong $soDat việc"
$lblTo.Font = New-Object System.Drawing.Font('Segoe UI', 19, [System.Drawing.FontStyle]::Bold)
$lblTo.ForeColor = [System.Drawing.Color]::White
$lblTo.AutoSize = $true; $lblTo.Location = New-Object System.Drawing.Point(22, 16)
$head.Controls.Add($lblTo)

$lblPhu = New-Object System.Windows.Forms.Label
$lblPhu.Text = "May: $env:COMPUTERNAME     Kich ban: $TEN_KICHBAN     " + (Get-Date -Format 'yyyy-MM-dd HH:mm')
$lblPhu.Font = New-Object System.Drawing.Font('Segoe UI', 10)
$lblPhu.ForeColor = [System.Drawing.Color]::FromArgb(232, 240, 236)
$lblPhu.AutoSize = $true; $lblPhu.Location = New-Object System.Drawing.Point(24, 58)
$head.Controls.Add($lblPhu)

# --- Thanh nut duoi cung (phai them TRUOC bang ket qua)
# THU TU THEM QUAN TRONG: WinForms dock theo z-order, control them SAU
# nam duoi cung z-order va duoc dock SAU CUNG. Control Dock='Fill' phai
# la cai them SAU CUNG thi no moi chiem dung phan con lai; them no o
# giua thi hai thanh Top/Bottom se de len no.
$foot = New-Object System.Windows.Forms.Panel
$foot.Dock = 'Bottom'; $foot.Height = 58
$foot.BackColor = [System.Drawing.Color]::FromArgb(238, 240, 244)
$frm.Controls.Add($foot)

$lblFile = New-Object System.Windows.Forms.Label
$lblFile.Text = 'Da luu ban day du vao: ' + $OutFile
$lblFile.Font = New-Object System.Drawing.Font('Segoe UI', 9)
$lblFile.ForeColor = [System.Drawing.Color]::FromArgb(90, 95, 105)
$lblFile.AutoSize = $true; $lblFile.Location = New-Object System.Drawing.Point(18, 20)
$foot.Controls.Add($lblFile)

$btnMo = New-Object System.Windows.Forms.Button
$btnMo.Text = 'Mo file bao cao'; $btnMo.Size = New-Object System.Drawing.Size(140, 34)
$btnMo.Font = New-Object System.Drawing.Font('Segoe UI', 10)
$btnMo.Anchor = 'Top,Right'
$btnMo.Location = New-Object System.Drawing.Point(($foot.Width - 300), 12)
$btnMo.Add_Click({ Start-Process notepad.exe $OutFile })
$foot.Controls.Add($btnMo)

$btnDong = New-Object System.Windows.Forms.Button
$btnDong.Text = 'Dong'; $btnDong.Size = New-Object System.Drawing.Size(130, 34)
$btnDong.Font = New-Object System.Drawing.Font('Segoe UI', 10, [System.Drawing.FontStyle]::Bold)
$btnDong.Anchor = 'Top,Right'
$btnDong.Location = New-Object System.Drawing.Point(($foot.Width - 150), 12)
$btnDong.Add_Click({ $frm.Close() })
$foot.Controls.Add($btnDong)

# --- Bang ket qua (them SAU CUNG vi Dock='Fill')
$lv = New-Object System.Windows.Forms.ListView
$lv.View = 'Details'; $lv.FullRowSelect = $true; $lv.GridLines = $false
$lv.Dock = 'Fill'; $lv.Font = New-Object System.Drawing.Font('Segoe UI', 10)
$lv.BorderStyle = 'None'
# WinForms dock control CUOI danh sach truoc -> Fill them sau cung lai bi dock
# truoc va chiem ca form, dai tren/duoi de len chu. BringToFront dua no len
# dau danh sach = dock SAU CUNG, chi chiem phan con lai (xem duoi).
$lv.Columns.Add('Trang thai', 110) | Out-Null
$lv.Columns.Add('Hang muc', 400) | Out-Null
$lv.Columns.Add('Thuc te tren may', 380) | Out-Null

$xanh = [System.Drawing.Color]::FromArgb(20, 115, 62)
$do   = [System.Drawing.Color]::FromArgb(178, 40, 40)
$xam  = [System.Drawing.Color]::FromArgb(130, 130, 140)

# DO THEO 3 PHAN, PHAN "DA LAM" LEN DAU TIEN.
#
# LY DO THAT (anh Thoai: "anh muon bao cao la nhung gi no DA LAM chu
# khong phai show nhung cai con lai"): truoc day cac muc do theo NHOM
# chuc nang, ma nhom dau tien lai la danh sach app go bo - neu go khong
# duoc thi mo bao cao ra la thay kin mot man hinh chu do "chua dat",
# phai keo mai moi thay nhung viec da lam duoc. Nhin vao tuong ca buoi
# cai hong, trong khi thuc te phan lon deu xong.
function DoNhom($tieuDe, $mau, $cacMuc) {
    if ($cacMuc.Count -eq 0) { return }
    $g = New-Object System.Windows.Forms.ListViewItem('')
    $g.SubItems.Add($tieuDe + "  ($($cacMuc.Count))") | Out-Null
    $g.SubItems.Add('') | Out-Null
    $g.Font = New-Object System.Drawing.Font('Segoe UI', 11, [System.Drawing.FontStyle]::Bold)
    $g.BackColor = $mau
    $lv.Items.Add($g) | Out-Null
    foreach ($r in $cacMuc) {
        $it = New-Object System.Windows.Forms.ListViewItem($r.TrangThai)
        $it.SubItems.Add('     ' + $r.Nhan) | Out-Null
        $it.SubItems.Add($r.ChiTiet) | Out-Null
        if ($r.Dat -eq $true) { $it.ForeColor = $xanh }
        elseif ($r.Dat -eq $false) { $it.ForeColor = $do }
        else { $it.ForeColor = $xam }
        $lv.Items.Add($it) | Out-Null
    }
}

# CHI HIEN VIEC DA LAM XONG.
#
# LY DO THAT (anh Thoai: "anh chi can no xuat ra nhung gi no da lam
# thoi"): ban truoc do van con hien them nhom "CAN XEM LAI" va "KHONG
# TU KIEM DUOC" ben duoi - dai va roi mat, trong khi dieu anh Thoai can
# chi la xac nhan may da lam xong nhung gi. Bo han 2 nhom kia khoi cua
# so va khoi file .txt (van con dem so trong dong tieu de neu co viec
# chua xong, khong giau hoan toan - xem $lblTo.Text ben duoi).
DoNhom 'ĐÃ LÀM XONG' ([System.Drawing.Color]::FromArgb(214, 240, 222)) `
       @($ketQua | Where-Object { $_.Dat -eq $true })
$frm.Controls.Add($lv)
$lv.BringToFront()

$frm.AcceptButton = $btnDong
[void]$frm.ShowDialog()
