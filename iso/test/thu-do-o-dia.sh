#!/bin/bash
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# CHI DE TEST: chay do-o-dia.cmd (ui/doodia.py) trong WinPE THAT qua iPXE + wimboot (lab netns
# tach biet, giong wimboot-lab.sh), may khach co 3 o: SATA GPT (EFI + NTFS "Windows" + NTFS
# "DuLieu"), USB MBR FAT32, SATA trong. Kiem: man hinh may khach, bao cao gui ve Samba lab,
# Console System doc dung bao cao, KHONG o nao bi thay doi (so sanh sha256 truoc/sau).
#   bash thu-do-o-dia.sh <bios|uefi>
FW=${1:-uefi}; WB=/build/test/wb; D=/build/test/odia-lab; R=$D/kq-$FW
REPO=$(cd "$(dirname "$0")/../.." && pwd); PI=192.168.98.1
for f in pi.pid http.pid q.pid; do [ -f $D/$f ] && kill $(cat $D/$f) 2>/dev/null; rm -f $D/$f; done
[ -f $R/smbd.pid ] && kill $(cat $R/smbd.pid) 2>/dev/null
sleep 1; rm -rf $R; mkdir -p $R/smb $D/www $D/tftp
for n in lan pi; do ip netns del $n 2>/dev/null; done
# --- 3 o dia thu
if [ ! -f $D/o-sata.qcow2 ]; then
  modprobe nbd max_part=8
  qemu-img create -q -f qcow2 $D/o-sata.qcow2 3G; qemu-img create -q -f qcow2 $D/o-usb.qcow2 1G
  qemu-img create -q -f qcow2 $D/o-trong.qcow2 2G
  qemu-nbd -c /dev/nbd2 $D/o-sata.qcow2; sleep 1
  parted -s /dev/nbd2 mklabel gpt mkpart EFI fat32 1MiB 101MiB set 1 esp on mkpart Win ntfs 101MiB 2101MiB mkpart Data ntfs 2101MiB 100%
  sleep 1; mkfs.vfat -n SYSTEM /dev/nbd2p1 >/dev/null; mkfs.ntfs -Q -L Windows /dev/nbd2p2 >/dev/null; mkfs.ntfs -Q -L DuLieu /dev/nbd2p3 >/dev/null
  qemu-nbd -d /dev/nbd2 >/dev/null; sleep 1
  qemu-nbd -c /dev/nbd2 $D/o-usb.qcow2; sleep 1
  parted -s /dev/nbd2 mklabel msdos mkpart primary fat32 1MiB 100%; sleep 1; mkfs.vfat -n USBKEY /dev/nbd2p1 >/dev/null
  qemu-nbd -d /dev/nbd2 >/dev/null
fi
# Chay tren BAN SAO cho phep GHI THAT (khong snapshot) -> so bang phan vung + danh sach file truoc/sau
anh_o() {   # $1 = file qcow2 -> in bang phan vung + danh sach file moi phan vung
  qemu-nbd -r -c /dev/nbd2 "$1"; sleep 1
  sfdisk -d /dev/nbd2 2>/dev/null | grep -v "^device\|^last-lba"
  for pp in /dev/nbd2p*; do [ -b "$pp" ] || continue; mkdir -p /mnt/odia; mount -o ro "$pp" /mnt/odia 2>/dev/null && { echo "== $pp"; (cd /mnt/odia && find . | sort); umount /mnt/odia; }; done
  qemu-nbd -d /dev/nbd2 >/dev/null; sleep 1
}
for o in sata usb trong; do cp $D/o-$o.qcow2 $R/chay-$o.qcow2; done
TRUOC=$(for o in sata usb trong; do anh_o $D/o-$o.qcow2; done)
# --- file nhung that do code sinh (tai khoan lab/lab123, share "lab")
CONSOLE_PI_DATA=$(mktemp -d) python3 - "$REPO" "$D/www" "$PI" <<'E'
import sys; sys.path.insert(0, sys.argv[1] + "/src")
from ui import doodia as O, unattend as U
w, pi = sys.argv[2], sys.argv[3]
f = {"winpeshl.ini": U.sinh_winpeshl_ini(),
     "autounattend.xml": U.sinh_autounattend_goi_script("do-o-dia.cmd", "do o dia"),
     "do-o-dia.cmd": O.sinh_do_o_dia_cmd(pi, "lab", "lab123", share="lab")}
for k, v in f.items(): open(f"{w}/{k}", "w", newline="").write(v)
open(f"{w}/menu.ipxe", "w").write("#!ipxe\nkernel http://%s/wimboot\n" % pi + "".join(
    f"initrd http://{pi}/{k} {k}\n" for k in f) + f"initrd http://{pi}/boot.wim boot.wim\nboot\n")
E
ln -sf $WB/wimboot $D/www/wimboot; ln -sf $WB/boot.wim $D/www/boot.wim
cp $WB/ipxeboot/x86_64/undionly.kpxe $D/tftp/; cp -L $WB/ipxeboot/x86_64-sb/snponly.efi $D/tftp/ipxe.efi
cp -L $WB/ipxeboot/x86_64-sb/snponly-shim.efi $D/tftp/
ip netns add lan; ip netns add pi
ip -n lan link add br0 type bridge; ip -n lan link set br0 up
ip link add p0 netns pi type veth peer name p0b netns lan
ip -n lan link set p0b master br0; ip -n lan link set p0b up
ip -n pi link set p0 up; ip -n pi link set lo up; ip -n pi addr add $PI/24 dev p0
cat > $R/dnsmasq.conf <<C
interface=p0
bind-interfaces
port=0
dhcp-range=192.168.98.50,192.168.98.99,255.255.255.0,1h
dhcp-match=set:bios,option:client-arch,0
dhcp-match=set:efi,option:client-arch,7
dhcp-userclass=set:ipxe,iPXE
tag-if=set:b,tag:bios,tag:!ipxe
tag-if=set:e,tag:efi,tag:!ipxe
dhcp-boot=tag:b,undionly.kpxe,,$PI
dhcp-boot=tag:e,snponly-shim.efi,,$PI
dhcp-boot=tag:ipxe,http://$PI/menu.ipxe,,$PI
enable-tftp
tftp-root=$D/tftp
log-facility=$R/dnsmasq.log
C
ip netns exec pi dnsmasq -C $R/dnsmasq.conf --pid-file=$D/pi.pid
ip netns exec pi sh -c "cd $D/www && python3 -m http.server 80 > $R/http.log 2>&1 & echo \$! > $D/http.pid"
id lab >/dev/null 2>&1 || useradd -M -s /usr/sbin/nologin lab
printf 'lab123\nlab123\n' | smbpasswd -s -a lab >/dev/null; chmod 777 $R/smb
cat > $R/smb.conf <<C
[global]
interfaces = p0
bind interfaces only = yes
server min protocol = SMB2
pid directory = $R
lock directory = $R
state directory = $R
cache directory = $R
log file = $R/smbd.log
[lab]
path = $R/smb
read only = no
valid users = lab
C
ip netns exec pi smbd -D -s $R/smb.conf
ip netns exec lan ip tuntap add tap0 mode tap 2>/dev/null
ip -n lan link set tap0 master br0; ip -n lan link set tap0 up
EXTRA=""
[ "$FW" = uefi ] && { cp /usr/share/OVMF/OVMF_VARS_4M.fd $R/vars.fd
  EXTRA="-drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd -drive if=pflash,format=raw,file=$R/vars.fd"; }
ip netns exec lan qemu-system-x86_64 -enable-kvm -cpu host -m 2048 -display none -vga std $EXTRA \
  -netdev tap,id=n0,ifname=tap0,script=no,downscript=no -device e1000,netdev=n0,mac=52:54:00:12:34:01,bootindex=1 \
  -device ahci,id=ah \
  -drive file=$R/chay-sata.qcow2,if=none,id=d0 -device ide-hd,drive=d0,bus=ah.0 \
  -drive file=$R/chay-trong.qcow2,if=none,id=d2 -device ide-hd,drive=d2,bus=ah.1 \
  -device qemu-xhci -drive file=$R/chay-usb.qcow2,if=none,id=d1 -device usb-storage,drive=d1 \
  -monitor unix:$D/mon.sock,server,nowait -pidfile $D/q.pid -daemonize || { echo QEMU_LOI; exit 1; }
m(){ echo "$1" | socat - UNIX-CONNECT:$D/mon.sock >/dev/null; }
KQ=KHONG
for i in $(seq 1 100); do
  ls $R/smb/o-dia-*.txt >/dev/null 2>&1 && { KQ=DAT; break; }
  sleep 5
done
sleep 4; m "screendump $R/man-hinh.ppm"
m "sendkey ret"; sleep 25
python3 -c "from PIL import Image; Image.open('$R/man-hinh.ppm').save('$R/man-hinh.png')"
echo "== $FW: nhan bao cao: $KQ"
kill $(cat $D/q.pid) 2>/dev/null; sleep 2
SAU=$(for o in sata usb trong; do anh_o $R/chay-$o.qcow2; done)
if [ "$TRUOC" = "$SAU" ]; then echo "DAT  3 o: bang phan vung + danh sach file KHONG doi sau khi do"
else echo "LOI  o dia bi thay doi:"; diff <(echo "$TRUOC") <(echo "$SAU") | head -20; fi
rm -f $R/chay-*.qcow2
for p in $D/pi.pid $D/http.pid $R/smbd.pid; do [ -f $p ] && kill $(cat $p) 2>/dev/null; done
f=$(ls $R/smb/o-dia-*.txt 2>/dev/null | head -1); [ -n "$f" ] && cp "$f" $R/bao-cao.txt
for n in lan pi; do ip netns del $n 2>/dev/null; done
