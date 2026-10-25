
# Console System - cai 1 bo font cho TOAN MAY (chay bang quyen SYSTEM, sau khi dang nhap lan dau).
# Cach Windows cai font: chep file vao %windir%\Fonts + ghi 1 gia tri vao HKLM\...\Fonts.
param([Parameter(Mandatory=$true)][string]$Bo)
$ErrorActionPreference = 'Continue'
$goc    = 'C:\ConsolePi\fonts'
$nguon  = Join-Path $goc $Bo
$dsFile = Join-Path $nguon '_fonts.json'
$dichF  = Join-Path $env:windir 'Fonts'
$reg    = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'
$kqFile = Join-Path $goc ('ket-qua-' + $Bo + '.json')

$daCai = New-Object System.Collections.Generic.List[string]
$loi   = New-Object System.Collections.Generic.List[string]
$canh  = New-Object System.Collections.Generic.List[string]
$tong  = 0
function Ghi-KetQua {
    $o = [ordered]@{ bo = $Bo; tong = $tong; da_cai = @($daCai); loi = @($loi); canh_bao = @($canh) }
    try { $o | ConvertTo-Json -Depth 3 | Out-File $kqFile -Encoding UTF8 } catch { }
}

try {
    Add-Type -Namespace CS -Name FontApi -MemberDefinition @'
[DllImport("gdi32.dll", CharSet=CharSet.Unicode)] public static extern int AddFontResourceW(string f);
[DllImport("user32.dll", CharSet=CharSet.Auto)] public static extern IntPtr SendMessageTimeout(IntPtr h, uint m, UIntPtr w, IntPtr l, uint f, uint t, out UIntPtr r);
'@ -ErrorAction Stop
    $coApi = $true
} catch { $coApi = $false }

if (-not (Test-Path -LiteralPath $dsFile)) {
    $loi.Add("Khong thay danh sach font: $dsFile (chep bo font sang may that bai?)")
    Ghi-KetQua; Write-Output $loi[0]; exit 2
}
$ds = @((Get-Content -Raw -Encoding UTF8 -LiteralPath $dsFile | ConvertFrom-Json).fonts)
$tong = $ds.Count
foreach ($m in $ds) {
    $src = Join-Path $nguon $m.file
    $dst = Join-Path $dichF $m.file
    try {
        if (-not (Test-Path -LiteralPath $src)) { throw 'thieu file nguon' }
        if (Test-Path -LiteralPath $dst) {
            $a = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash
            $b = (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash
            if ($a -ne $b) {
                # Trung TEN FILE voi 1 font KHAC dang co tren may (thuong la font he thong,
                # dang bi khoa nen cung khong ghi de duoc): giu nguyen, chi canh bao.
                $canh.Add($m.file + ': trung ten file voi font khac da co tren may - giu nguyen font cua may')
                continue
            }
        } else {
            Copy-Item -LiteralPath $src -Destination $dst -Force -ErrorAction Stop
        }
        New-ItemProperty -Path $reg -Name $m.reg -Value $m.file -PropertyType String -Force -ErrorAction Stop | Out-Null
        if ($coApi) { [void][CS.FontApi]::AddFontResourceW($dst) }
        $daCai.Add($m.file)
    } catch {
        $loi.Add($m.file + ': ' + $_.Exception.Message)
    }
}
if ($coApi) {
    try { $r = [UIntPtr]::Zero; [void][CS.FontApi]::SendMessageTimeout([IntPtr]0xffff, 0x1D, [UIntPtr]::Zero, [IntPtr]::Zero, 2, 1000, [ref]$r) } catch { }
}
Ghi-KetQua
Write-Output ("Bo font {0}: {1}/{2} font da cai, {3} canh bao, {4} loi" -f $Bo, $daCai.Count, $tong, $canh.Count, $loi.Count)
foreach ($x in $canh) { Write-Output ('CANH BAO ' + $x) }
foreach ($x in $loi)  { Write-Output ('LOI ' + $x) }
if ($loi.Count -gt 0) { exit 1 }
exit 0
