#!/bin/bash
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# ====================================================================
# CHI DE TEST (may build, can KVM + nbd + may mau thu-silent.sh tao-vang):
# THU GIA NHAP DOMAIN THAT bang CHINH khoi <UnattendedJoin> ma Console System sinh
# (ui/unattend.py: _khoi_gia_nhap_domain), tren o phu cua may Windows mau.
#   Cach: chep unattend.xml (specialize: ten may + UnattendedJoin; oobeSystem: tu dang nhap
#   + 1 lenh ghi ket qua) vao may mau -> sysprep /generalize /oobe /shutdown /unattend ->
#   bat may lan 2 (pass specialize chay UnattendedJoin) -> doc ket qua (PartOfDomain, Domain,
#   NetSetup.LOG). QEMU chay trong mount namespace rieng co /etc/resolv.conf tro ve DNS cua
#   domain => DHCP cua QEMU cap DNS = may chu domain (giong "mang co san DHCP").
#   bash thu-domain.sh <file thong tin>   (xem /build/.ad-test: dns/domain/user/netbios/password/ou)
# Khong dung toi may that nao ngoai may chu domain duoc chi dinh.
# ====================================================================
set -u
CFG=${1:?thieu file thong tin domain}
VANG=/build/test/vang; LAM=/build/test/thu-domain-tam; MAY=${2:-CSDOM01}
SRC=/root/consolepi-toolkit/src
[ -f $VANG/disk.qcow2 ] || { echo "chua co may mau"; exit 1; }
exec 9>/build/test/thu-silent.lock; flock 9      # chung khoa voi thu-silent (cung dung nbd0)
modprobe nbd max_part=8
mkdir -p $LAM /mnt/vang
umount /mnt/vang 2>/dev/null; qemu-nbd -d /dev/nbd0 >/dev/null 2>&1; sleep 1
rm -f $LAM/o.qcow2; qemu-img create -q -f qcow2 -b $VANG/disk.qcow2 -F qcow2 $LAM/o.qcow2
cp $VANG/vars.fd $LAM/vars.fd
dns=$(awk -F' *: *' '$1=="dns"{print $2}' $CFG); printf 'nameserver %s\n' "$dns" > $LAM/resolv.conf

montage_rw() { qemu-nbd -c /dev/nbd0 $LAM/o.qcow2; sleep 2
  local n=0; until mount -t ntfs-3g -o rw,remove_hiberfile /dev/nbd0p3 /mnt/vang 2>/dev/null; do
    n=$((n+1)); [ $n -ge 5 ] && { qemu-nbd -d /dev/nbd0 >/dev/null 2>&1; echo "mount loi"; exit 2; }; sleep 4; done; }
montage_rw
rm -rf /mnt/vang/ConsolePi/dom; mkdir -p /mnt/vang/ConsolePi/dom
CFG=$CFG SRC=$SRC MAY=$MAY python3 - <<'E'
import os, sys
sys.path.insert(0, os.environ["SRC"])
from ui import unattend as u
c = {}
for l in open(os.environ["CFG"], encoding="utf-8"):
    if ":" in l:
        k, v = l.split(":", 1); c[k.strip()] = v.strip()
user = c["user"]                       # cung cach cat nhu giao dien (ui/deployos.py)
if "\\" in user: user = user.split("\\", 1)[1]
elif "@" in user: user = user.split("@", 1)[0]
d = {"domain": c["domain"], "domain_ou": c.get("ou", ""), "domain_user": user, "domain_pass": c["password"]}
join = u._khoi_gia_nhap_domain(d)
mk = "Test12345!"
xml = f'''<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
  <settings pass="specialize">
    <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <ComputerName>{os.environ["MAY"]}</ComputerName>
    </component>{join}
  </settings>
  <settings pass="oobeSystem">
    <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <OOBE><HideEULAPage>true</HideEULAPage><HideLocalAccountScreen>true</HideLocalAccountScreen><HideOnlineAccountScreens>true</HideOnlineAccountScreens><HideWirelessSetupInOOBE>true</HideWirelessSetupInOOBE><ProtectYourPC>3</ProtectYourPC><SkipMachineOOBE>true</SkipMachineOOBE><SkipUserOOBE>true</SkipUserOOBE></OOBE>
      <UserAccounts><AdministratorPassword><Value>{mk}</Value><PlainText>true</PlainText></AdministratorPassword></UserAccounts>
      <AutoLogon><Password><Value>{mk}</Value><PlainText>true</PlainText></Password><Enabled>true</Enabled><LogonCount>1</LogonCount><Username>Administrator</Username></AutoLogon>
      <FirstLogonCommands><SynchronousCommand wcm:action="add"><Order>1</Order><CommandLine>powershell -NoProfile -ExecutionPolicy Bypass -File C:\\ConsolePi\\dom\\res.ps1</CommandLine></SynchronousCommand></FirstLogonCommands>
    </component>
  </settings>
</unattend>'''
open("/mnt/vang/ConsolePi/dom/unattend.xml", "w", encoding="utf-8").write(xml)
E
cat > /mnt/vang/ConsolePi/dom/run.ps1 <<'E'
if (Test-Path C:\ConsolePi\dom\da-sysprep.txt) { exit }
'1' | Out-File C:\ConsolePi\dom\da-sysprep.txt
Start-Sleep 20
$p = Start-Process -FilePath C:\Windows\System32\Sysprep\sysprep.exe -ArgumentList '/generalize','/oobe','/shutdown','/unattend:C:\ConsolePi\dom\unattend.xml' -PassThru -Wait
"sysprep ma thoat: $($p.ExitCode)" | Out-File C:\ConsolePi\dom\sysprep-kq.txt -Encoding ascii
if ($p.ExitCode -ne 0) { Copy-Item C:\Windows\System32\Sysprep\Panther\setupact.log C:\ConsolePi\dom\sysprep-setupact.log -EA SilentlyContinue; Copy-Item C:\Windows\System32\Sysprep\Panther\setuperr.log C:\ConsolePi\dom\sysprep-setuperr.log -EA SilentlyContinue; shutdown /s /t 3 }
E
cat > /mnt/vang/ConsolePi/dom/res.ps1 <<'E'
Start-Sleep 15
$cs = Get-CimInstance Win32_ComputerSystem
"PartOfDomain=$($cs.PartOfDomain)`r`nDomain=$($cs.Domain)`r`nName=$($cs.Name)" | Out-File C:\ConsolePi\dom\ket-qua.txt -Encoding ascii
Copy-Item C:\Windows\debug\NetSetup.LOG C:\ConsolePi\dom\NetSetup.LOG -EA SilentlyContinue
Copy-Item C:\Windows\Panther\setupact.log C:\ConsolePi\dom\setupact.log -EA SilentlyContinue
Copy-Item C:\Windows\Panther\UnattendGC\setupact.log C:\ConsolePi\dom\setupact-gc.log -EA SilentlyContinue
shutdown /s /t 5
E
sed -i 's/$/\r/' /mnt/vang/ConsolePi/dom/run.ps1 /mnt/vang/ConsolePi/dom/res.ps1
mkdir -p /mnt/vang/Windows/Setup/Scripts; printf '@echo off\r\npowershell -NoProfile -ExecutionPolicy Bypass -File C:\\ConsolePi\\dom\\res.ps1\r\n' > /mnt/vang/Windows/Setup/Scripts/SetupComplete.cmd
D="/mnt/vang/ProgramData/Microsoft/Windows/Start Menu/Programs/StartUp"; mkdir -p "$D"
printf '@echo off\r\npowershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\\ConsolePi\\dom\\run.ps1\r\n' > "$D/cs-dom.cmd"
sync; umount /mnt/vang; qemu-nbd -d /dev/nbd0 >/dev/null

chay_vm() {   # $1 = toi da (giay)
  rm -f $LAM/q.pid
  unshare -m bash -c "mount --bind $LAM/resolv.conf /etc/resolv.conf && exec qemu-system-x86_64 -enable-kvm -cpu host -smp 4 -m 3072 -display none -vga std \
    -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
    -drive if=pflash,format=raw,file=$LAM/vars.fd \
    -netdev user,id=n0 -device e1000,netdev=n0 \
    -drive file=$LAM/o.qcow2,if=none,id=d0 -device ahci,id=ah -device ide-hd,drive=d0,bus=ah.0 \
    -monitor unix:$LAM/mon.sock,server,nowait -pidfile $LAM/q.pid -daemonize" || { echo "QEMU loi"; return 2; }
  local pid; pid=$(cat $LAM/q.pid); local han=$(( $(date +%s) + $1 ))
  local n=0; mkdir -p /build/test/ket-qua-domain/anh
  while kill -0 "$pid" 2>/dev/null; do
    n=$((n+1)); if [ $((n%24)) -eq 0 ]; then echo "screendump /build/test/ket-qua-domain/anh/$(date +%H%M%S).ppm" | socat - UNIX-CONNECT:$LAM/mon.sock >/dev/null 2>&1; fi
    [ "$(date +%s)" -gt "$han" ] && { echo "(het gio - ep tat)"; kill "$pid"; sleep 3; return 1; }; sleep 5; done
}
echo "== Lan 1: sysprep /generalize + /unattend (co UnattendedJoin) =="; chay_vm 1200; echo "ket thuc lan 1 (rc=$?)"
qemu-nbd -r -c /dev/nbd0 $LAM/o.qcow2; sleep 2; mount -o ro /dev/nbd0p3 /mnt/vang 2>/dev/null
tr -d '\0\r' < /mnt/vang/ConsolePi/dom/sysprep-kq.txt 2>/dev/null; echo; ls /mnt/vang/ConsolePi/dom
if [ -f /mnt/vang/ConsolePi/dom/sysprep-setuperr.log ]; then echo "--- sysprep setuperr.log"; tail -15 /mnt/vang/ConsolePi/dom/sysprep-setuperr.log; fi
umount /mnt/vang; qemu-nbd -d /dev/nbd0 >/dev/null
grep -q "ma thoat: 0" <(qemu-nbd -r -c /dev/nbd0 $LAM/o.qcow2 >/dev/null; sleep 2; mount -o ro /dev/nbd0p3 /mnt/vang 2>/dev/null; tr -d '\0\r' < /mnt/vang/ConsolePi/dom/sysprep-kq.txt 2>/dev/null; umount /mnt/vang; qemu-nbd -d /dev/nbd0 >/dev/null) || { echo "SYSPREP KHONG THANH CONG - dung"; exit 3; }
echo "== Lan 2: specialize (gia nhap domain) -> OOBE -> ghi ket qua =="; chay_vm 1500; echo "ket thuc lan 2 (rc=$?)"
qemu-nbd -r -c /dev/nbd0 $LAM/o.qcow2; sleep 2; mount -o ro /dev/nbd0p3 /mnt/vang 2>/dev/null
mkdir -p /build/test/ket-qua-domain; cp -r /mnt/vang/ConsolePi/dom/. /build/test/ket-qua-domain/ 2>/dev/null
echo "--- ket-qua.txt"; cat /mnt/vang/ConsolePi/dom/ket-qua.txt 2>/dev/null || echo "(khong co ket qua)"
echo "--- NetSetup.LOG (cac dong chinh)"; grep -i "NetpDoDomainJoin\|NetpJoinDomain\|status\|error\|0x" /mnt/vang/ConsolePi/dom/NetSetup.LOG 2>/dev/null | tail -12
umount /mnt/vang; qemu-nbd -d /dev/nbd0 >/dev/null
[ "${GIU:-0}" = 1 ] || rm -f $LAM/o.qcow2
