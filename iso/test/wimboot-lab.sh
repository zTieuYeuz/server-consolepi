#!/bin/bash
# ===================================================================
# CHI DE TEST: chung minh chuoi boot iPXE (ban ky) + wimboot chay tren ca
# 3 kieu may - BIOS, UEFI, UEFI + Secure Boot - trong phong thi nghiem
# network namespace TACH BIET (khong dung toi mang that).
#
#   bash wimboot-lab.sh <bios|uefi|sb> <thu_muc>
# thu_muc can co: boot.wim, wimboot, ipxeboot/ (giai nen ipxeboot.tar.gz
# ban release chinh thuc), va www/ (menu.ipxe + file nhung) neu muon dung
# menu that; khong co www/ thi tu sinh menu thu (deploy.cmd thu: len mang,
# net use vao Samba cua "Pi" lab, ghi file danh dau roi tat may).
# Ket qua: <thu_muc>/kq-<fw>/ (anh man hinh, log http/dnsmasq, file danh dau).
# ===================================================================
FW=$1; D=${2:-/build/test/wb}; R=$D/kq-$FW
for p in $D/kq-*/smbd.pid; do [ -f $p ] && kill $(cat $p) 2>/dev/null; done
rm -rf $R; mkdir -p $R/smb
PI=192.168.98.1
for f in boot.wim wimboot ipxeboot/x86_64/undionly.kpxe ipxeboot/x86_64-sb/snponly-shim.efi; do
  [ -e $D/$f ] || { echo "THIEU $D/$f"; exit 1; }; done
for f in pi.pid http.pid smb.pid q.pid; do [ -f $D/$f ] && kill $(cat $D/$f) 2>/dev/null; rm -f $D/$f; done
sleep 1
for n in lan pi; do ip netns del $n 2>/dev/null; done
ip netns add lan; ip netns add pi
ip -n lan link add br0 type bridge; ip -n lan link set br0 up
ip link add p0 netns pi type veth peer name p0b netns lan
ip -n lan link set p0b master br0; ip -n lan link set p0b up
ip -n pi link set p0 up; ip -n pi link set lo up; ip -n pi addr add $PI/24 dev p0

# --- TFTP: dung bo file ban release chinh thuc (BIOS + UEFI co ky)
rm -rf $D/tftp; mkdir -p $D/tftp
cp $D/ipxeboot/x86_64/undionly.kpxe $D/tftp/
cp -L $D/ipxeboot/x86_64-sb/snponly-shim.efi $D/ipxeboot/x86_64-sb/snponly.efi $D/tftp/
# shim nap tang 2 theo ten MAC DINH "ipxe.efi" (kiem chung: log TFTP xin
# ipxe.efi, khong xin snponly.efi) -> phat ban snponly DA KY duoi ten do.
cp $D/ipxeboot/x86_64-sb/snponly.efi $D/tftp/ipxe.efi
cat > $R/dnsmasq.conf <<EOF
interface=p0
bind-interfaces
port=0
dhcp-range=192.168.98.50,192.168.98.99,255.255.255.0,1h
dhcp-match=set:bios,option:client-arch,0
dhcp-match=set:efi-x64,option:client-arch,7
dhcp-match=set:efi-x64,option:client-arch,9
dhcp-userclass=set:ipxe,iPXE
tag-if=set:bios-that,tag:bios,tag:!ipxe
tag-if=set:efi-that,tag:efi-x64,tag:!ipxe
dhcp-boot=tag:bios-that,undionly.kpxe,,$PI
dhcp-boot=tag:efi-that,snponly-shim.efi,,$PI
dhcp-boot=tag:ipxe,http://$PI/menu.ipxe,,$PI
enable-tftp
tftp-root=$D/tftp
log-dhcp
log-facility=$R/dnsmasq.log
EOF
ip netns exec pi dnsmasq -C $R/dnsmasq.conf --pid-file=$D/pi.pid || { echo DNSMASQ_LOI; exit 1; }

# --- HTTP: menu + file nhung
if [ ! -d $D/www ]; then
  mkdir -p $D/www
  printf '[LaunchApps]\r\nX:\\sources\\setup.exe, /unattend:X:\\Windows\\System32\\autounattend.xml\r\n' > $D/www/winpeshl.ini
  cat > $D/www/autounattend.xml <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
  <settings pass="windowsPE">
    <component name="Microsoft-Windows-International-Core-WinPE" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <SetupUILanguage><UILanguage>en-US</UILanguage></SetupUILanguage>
      <InputLocale>en-US</InputLocale><SystemLocale>en-US</SystemLocale>
      <UILanguage>en-US</UILanguage><UserLocale>en-US</UserLocale>
    </component>
    <component name="Microsoft-Windows-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <RunSynchronous><RunSynchronousCommand wcm:action="add"><Order>1</Order>
        <Path>cmd /c X:\Windows\System32\deploy.cmd</Path></RunSynchronousCommand></RunSynchronous>
    </component>
  </settings>
</unattend>
EOF
  printf '%s\r\n' '@echo off' 'set LOG=X:\lab.txt' 'wpeinit >> %LOG% 2>&1' \
    'wpeutil UpdateBootInfo >> %LOG% 2>&1' \
    'reg query HKLM\System\CurrentControlSet\Control /v PEFirmwareType >> %LOG% 2>&1' \
    'reg query HKLM\System\CurrentControlSet\Control\SecureBoot\State /v UEFISecureBootEnabled >> %LOG% 2>&1' \
    ':cho' "ping -n 1 -w 1000 $PI >nul 2>&1" 'if errorlevel 1 goto cho' \
    "net use Z: \\\\$PI\\lab /user:lab lab123 >> %LOG% 2>&1" \
    'copy /y %LOG% Z:\ketqua.txt' 'wpeutil shutdown' > $D/www/deploy.cmd
  printf '%s\n' '#!ipxe' 'echo Lab wimboot - ${platform}' \
    "kernel http://$PI/wimboot" \
    "initrd http://$PI/winpeshl.ini winpeshl.ini" \
    "initrd http://$PI/autounattend.xml autounattend.xml" \
    "initrd http://$PI/deploy.cmd deploy.cmd" \
    "initrd http://$PI/boot.wim boot.wim" 'boot' > $D/www/menu.ipxe
fi
ln -sf $D/wimboot $D/www/wimboot; ln -sf $D/boot.wim $D/www/boot.wim
ip netns exec pi sh -c "cd $D/www && python3 -m http.server 80 > $R/http.log 2>&1 & echo \$! > $D/http.pid"

# --- Samba cua "Pi" lab (chi trong netns, user lab/lab123)
id lab >/dev/null 2>&1 || useradd -M -s /usr/sbin/nologin lab
printf 'lab123\nlab123\n' | smbpasswd -s -a lab >/dev/null
chmod 777 $R/smb
cat > $R/smb.conf <<EOF
[global]
interfaces = p0
bind interfaces only = yes
server min protocol = SMB2
map to guest = never
pid directory = $R
lock directory = $R
state directory = $R
cache directory = $R
log file = $R/smbd.log
[lab]
path = $R/smb
read only = no
valid users = lab
EOF
ip netns exec pi smbd -D -s $R/smb.conf

# --- May khach
ip netns exec lan ip tuntap add tap0 mode tap 2>/dev/null
ip netns exec lan ip tuntap add tap1 mode tap 2>/dev/null
for t in tap0 tap1; do ip -n lan link set $t master br0; ip -n lan link set $t up; done
NIC="-netdev tap,id=n0,ifname=tap0,script=no,downscript=no -device e1000,netdev=n0,mac=52:54:00:12:34:01,bootindex=1"
EXTRA=""
case $FW in
  uefi) cp /usr/share/OVMF/OVMF_VARS_4M.fd $R/vars.fd
        EXTRA="-drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd -drive if=pflash,format=raw,file=$R/vars.fd" ;;
  sb)   # Secure Boot BAT that (khoa Microsoft nap san). ROM iPXE cua e1000
        # khong ky -> bi chan; dung virtio-net (driver co san trong OVMF, co
        # ky) de boot mang, them e1000 KHONG ROM cho WinPE co driver.
        cp /usr/share/OVMF/OVMF_VARS_4M.ms.fd $R/vars.fd
        EXTRA="-machine q35,smm=on -global driver=cfi.pflash01,property=secure,value=on -drive if=pflash,format=raw,unit=0,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.secboot.fd -drive if=pflash,format=raw,unit=1,file=$R/vars.fd"
        NIC="-netdev tap,id=n0,ifname=tap0,script=no,downscript=no -device virtio-net-pci,netdev=n0,mac=52:54:00:12:34:01,bootindex=1 -netdev tap,id=n1,ifname=tap1,script=no,downscript=no -device e1000,netdev=n1,mac=52:54:00:12:34:02,romfile=" ;;
esac
rm -f $D/mon.sock
ip netns exec lan qemu-system-x86_64 -enable-kvm -cpu host -m 2048 -display none -vga std $EXTRA $NIC \
  -monitor unix:$D/mon.sock,server,nowait -pidfile $D/q.pid -daemonize || { echo QEMU_LOI; exit 1; }
m(){ echo "$1" | socat - UNIX-CONNECT:$D/mon.sock >/dev/null; }
chup(){ m "screendump $R/$1.ppm"; }
KQ=KHONG
for i in $(seq 1 90); do
  [ $i = 8 ] && chup 1-dau
  [ $i = 20 ] && chup 2-giua
  [ -s $R/smb/ketqua.txt ] && { KQ=DAT; break; }
  sleep 5
done
chup 3-cuoi
echo "== $FW: $KQ"
grep -o '"GET [^"]*" [0-9]*' $R/http.log | sort | uniq -c
grep -E "sent|PXE" $R/dnsmasq.log | grep -oE "(sent|file) [^ ]*" | sort | uniq -c | head
[ -s $R/smb/ketqua.txt ] && tr -d '\r' < $R/smb/ketqua.txt | grep -iE "PEFirmwareType|SecureBootEnabled|error"
kill $(cat $D/q.pid) 2>/dev/null
