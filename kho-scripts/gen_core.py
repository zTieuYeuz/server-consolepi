# Bo sinh script kho Console System - khung chung cho moi script
import os, json
OUT = "/build/kho-script/out"

PRELUDE = r'''# ConsolePi-Script: @@TITLE@@
# Mo ta   : @@DESC@@
# Can mang: @@NET@@ | Can khoi dong lai: @@REBOOT@@ | Hoan tac: @@UNDO@@
# Hanh vi CO DINH - khong tham so. Chay duoc nhieu lan (lan sau khong doi gi them).
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Ten = '@@ID@@'
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
'''
POSTLUDE = r'''
    Ghi 'XONG'
    XongHoSo
    exit 0
} catch {
    Ghi ('LOI: ' + $_.Exception.Message + ' (dong ' + $_.InvocationInfo.ScriptLineNumber + ')')
    XongHoSo
    exit 1
}
'''
CHECK_HEAD = r'''$ErrorActionPreference = 'SilentlyContinue'
$Build = [int](Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').CurrentBuild
function V($p, $n) { (Get-ItemProperty -LiteralPath $p -Name $n -ErrorAction SilentlyContinue).$n }
try { $r = & { '''
CHECK_TAIL = r''' } } catch { $r = $false }
if ($r) { 'DAT' } else { 'LOI' }
'''

S = []   # danh sach script

def sc(id, title, desc, body, check, user=(), net="Khong", reboot="Khong", undo="Doi gia tri ve mac dinh cua Windows", cuoi=False):
    S.append(dict(id=id, title=title, desc=desc, body=body.strip("\n"), check=check.strip(), user=list(user),
                  net=net, reboot=reboot, undo=undo, cuoi=cuoi))

def ps_val(v, kieu):
    return "'%s'" % v if kieu == "String" else str(v)

def build():
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT): os.remove(os.path.join(OUT, f))
    man = []
    for s in S:
        lines = []
        for (p, n, v, k) in s["user"]:
            lines.append("    DatUser '%s' '%s' %s '%s'" % (p, n, ps_val(v, k), k))
        corpo = "\n".join(lines + ["    " + l if l.strip() else l for l in s["body"].split("\n")])
        txt = PRELUDE
        for a, b in (("@@TITLE@@", s["title"]), ("@@DESC@@", s["desc"]), ("@@NET@@", s["net"]),
                     ("@@REBOOT@@", s["reboot"]), ("@@UNDO@@", s["undo"]), ("@@ID@@", s["id"])):
            txt = txt.replace(a, b)
        txt += corpo + "\n" + POSTLUDE
        open(os.path.join(OUT, s["id"] + ".ps1"), "w", encoding="utf-8-sig", newline="\r\n").write(txt)
        open(os.path.join(OUT, "c-" + s["id"] + ".ps1"), "w", encoding="utf-8-sig", newline="\r\n").write(
            CHECK_HEAD + s["check"] + CHECK_TAIL)
        man.append(dict(id=s["id"], title=s["title"], cuoi=s["cuoi"], reboot=s["reboot"] != "Khong",
                        user=[dict(path=p, name=n, val=str(v), kieu=k) for (p, n, v, k) in s["user"]]))
    json.dump(man, open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(S), "script ->", OUT)
