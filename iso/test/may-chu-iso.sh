#!/bin/bash
# ===================================================================
# CHI DE TEST (may build): "Console System cai tu ISO" chay trong may ao,
# phuc vu PXE cho may khach trong 1 MANG LAB RIENG (bridge brlab, khong noi
# ra LAN that). Dung de test tron cac che do mang + kieu may + kich ban
# tren ban x86 truoc khi phat hanh.
#
#   bash may-chu-iso.sh cai [iso]            cai ISO len o 40G (cai-uefi.sh)
#   bash may-chu-iso.sh chuan-bi             gan khoa SSH + sudo khong mat khau
#                                            vao o DA CAI (chi may test)
#   bash may-chu-iso.sh mang <co_dhcp|khong> dung mang lab (+ router gia neu co_dhcp)
#   bash may-chu-iso.sh mang giu-cau       chi tat router gia, giu bridge (may dang chay)
#   bash may-chu-iso.sh bat | tat            may chu: card 1 = user-net (Internet,
#                                            SSH 127.0.0.1:18022, web :18080),
#                                            card 2 (enp0s4) = mang lab (PXE)
#   bash may-chu-iso.sh ssh '<lenh>'         chay lenh tren may chu (administrator)
#   bash may-chu-iso.sh khach <bios|uefi|sb> <start|odia|key ...|chup ten|stop>
#
# Mang lab: brlab. May build co 192.168.98.254 (che do Pi tu cap IP) va
# 10.77.0.254 (che do co DHCP) tren brlab de SSH/xem. Router gia (netns
# cty2) = 10.77.0.1, cap 10.77.0.100-150.
# ===================================================================
W=/build/test/srv
LENH=$1; shift
mkdir -p $W
SSHC="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=5 -p 18022 administrator@127.0.0.1"

case $LENH in
cai)
  bash /build/test/cai-uefi.sh "${1:-/build/console-system/live-image-amd64.hybrid.iso}" $W 40G ;;

chuan-bi)
  [ -f /root/.ssh/id_ed25519 ] || ssh-keygen -q -t ed25519 -N "" -f /root/.ssh/id_ed25519
  modprobe nbd max_part=16
  qemu-nbd -d /dev/nbd0 >/dev/null 2>&1
  qemu-nbd -c /dev/nbd0 $W/disk.qcow2 && sleep 2 && partprobe /dev/nbd0 2>/dev/null; sleep 1
  GOC=""
  for p in /dev/nbd0p*; do
    [ "$(blkid -o value -s TYPE $p)" = ext4 ] && GOC=$p
  done
  [ -n "$GOC" ] || { echo "KHONG THAY PHAN VUNG ext4"; qemu-nbd -d /dev/nbd0; exit 1; }
  mkdir -p /mnt/srv && mount $GOC /mnt/srv
  install -d -m 700 -o 1000 -g 1000 /mnt/srv/home/administrator/.ssh
  cat /root/.ssh/id_ed25519.pub > /mnt/srv/home/administrator/.ssh/authorized_keys
  chown 1000:1000 /mnt/srv/home/administrator/.ssh/authorized_keys
  chmod 600 /mnt/srv/home/administrator/.ssh/authorized_keys
  echo "administrator ALL=(ALL) NOPASSWD:ALL" > /mnt/srv/etc/sudoers.d/99-chi-may-test
  chmod 440 /mnt/srv/etc/sudoers.d/99-chi-may-test
  # Cong PXE = card thu 2 (card 1 la user-net de SSH/Internet)
  mkdir -p /mnt/srv/var/lib/console-pi
  echo '{"day": "enp0s4"}' > /mnt/srv/var/lib/console-pi/cong-mang.json
  umount /mnt/srv; qemu-nbd -d /dev/nbd0 >/dev/null; echo "CHUAN BI XONG ($GOC)" ;;

mang)
  # Tat router gia cu (xoa netns KHONG giet tien trinh ben trong - dnsmasq cu
  # van song va van noi vao brlab -> 2 DHCP trong lab, da gap 26/09/2026)
  [ -f $W/cty2.pid ] && kill $(cat $W/cty2.pid) 2>/dev/null
  pkill -F $W/cty2.pid 2>/dev/null; ip link del c2b 2>/dev/null
  ip netns del cty2 2>/dev/null
  [ "$1" = giu-cau ] && exit 0
  ip link del brlab 2>/dev/null
  ip link add brlab type bridge; ip link set brlab up
  ip addr add 192.168.98.254/24 dev brlab
  ip addr add 10.77.0.254/24 dev brlab
  if [ "$1" = co_dhcp ]; then
    ip netns add cty2
    ip link add c2 netns cty2 type veth peer name c2b
    ip link set c2b master brlab; ip link set c2b up
    ip -n cty2 link set c2 up; ip -n cty2 link set lo up
    ip -n cty2 addr add 10.77.0.1/24 dev c2
    printf '%s\n' interface=c2 bind-interfaces port=0 \
      dhcp-range=10.77.0.100,10.77.0.150,255.255.255.0,1h dhcp-option=3,10.77.0.1 \
      log-dhcp log-facility=$W/cty2.log > $W/cty2.conf
    ip netns exec cty2 dnsmasq -C $W/cty2.conf --pid-file=$W/cty2.pid && echo "ROUTER GIA 10.77.0.1 DA CHAY"
  fi
  echo "MANG LAB: $1" ;;

bat)
  [ -f $W/q.pid ] && kill $(cat $W/q.pid) 2>/dev/null; sleep 1
  ip tuntap add tsrv mode tap 2>/dev/null; ip link set tsrv master brlab; ip link set tsrv up
  cp -n /usr/share/OVMF/OVMF_VARS_4M.fd $W/vars.fd 2>/dev/null
  rm -f $W/mon.sock
  qemu-system-x86_64 -enable-kvm -cpu host -m 3072 -smp 2 -vga std -display none \
    -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
    -drive if=pflash,format=raw,file=$W/vars.fd \
    -drive file=$W/disk.qcow2,if=virtio,format=qcow2 \
    -netdev user,id=n0,hostfwd=tcp:127.0.0.1:18022-:22,hostfwd=tcp:127.0.0.1:18080-:80 \
    -device e1000,netdev=n0,addr=0x3 \
    -netdev tap,id=n1,ifname=tsrv,script=no,downscript=no -device e1000,netdev=n1,addr=0x4,mac=52:54:00:aa:00:01 \
    -monitor unix:$W/mon.sock,server,nowait -pidfile $W/q.pid -daemonize && echo "MAY CHU DA BAT"
  for i in $(seq 1 60); do $SSHC true 2>/dev/null && { echo "SSH OK sau $((i*5))s"; break; }; sleep 5; done ;;

tat)
  $SSHC 'sudo poweroff' 2>/dev/null; sleep 20
  [ -f $W/q.pid ] && kill $(cat $W/q.pid) 2>/dev/null; echo TAT ;;

ssh) $SSHC "$@" ;;

cap-nhat)
  # Day code MOI NHAT trong repo (/root/consolepi-toolkit tren may build) vao
  # may chu - giong cap-nhat-pi.sh (ui, nettools, pxe-boot, scripts, app.py,
  # VERSION) - de test ban sua ma khong phai build lai ISO.
  rsync -a --delete --exclude=__pycache__ -e "${SSHC% -p 18022*} -p 18022" \
    /root/consolepi-toolkit/src/ administrator@127.0.0.1:/tmp/src-moi/ || exit 1
  rsync -a -e "${SSHC% -p 18022*} -p 18022" /root/consolepi-toolkit/VERSION \
    administrator@127.0.0.1:/tmp/src-moi/VERSION
  $SSHC 'set -e; D=/opt/console-pi; S=/tmp/src-moi
    sudo cp -r $S/ui/. $D/ui/; sudo cp -r $S/nettools/. $D/nettools/
    sudo rm -rf $D/pxe-boot; sudo cp -r $S/pxe-boot $D/pxe-boot
    for f in $S/scripts/*; do [ -f "$f" ] && sudo install -m 755 "$f" $D/scripts/; done
    sudo install -m 644 $S/app.py $D/app.py
    sudo install -m 644 $S/VERSION $D/VERSION
    sudo find $D -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
    sudo python3 -m py_compile $D/ui/*.py $D/nettools/*.py $D/app.py
    sudo systemctl restart console-pi-dashboard; sleep 5
    systemctl is-active console-pi-dashboard' ;;

khach)
  FW=$1; L2=$2; shift 2
  K=$W/khach-$FW; mkdir -p $K
  case $FW in bios) M=12;; uefi) M=13;; sb) M=14;; *) echo "fw?"; exit 1;; esac
  m(){ echo "$1" | socat - UNIX-CONNECT:$K/mon.sock >/dev/null; }
  case $L2 in
  start|odia)
    [ -f $K/q.pid ] && kill $(cat $K/q.pid) 2>/dev/null; sleep 1
    rm -f $K/mon.sock
    [ $L2 = start ] && { rm -f $K/disk.qcow2; qemu-img create -q -f qcow2 $K/disk.qcow2 60G; }
    for t in 0 1; do ip tuntap add tk$M$t mode tap 2>/dev/null; ip link set tk$M$t master brlab; ip link set tk$M$t up; done
    EXTRA=""; BOOT=",bootindex=1"; [ $L2 = odia ] && BOOT=",romfile="
    NIC="-netdev tap,id=n0,ifname=tk${M}0,script=no,downscript=no -device e1000,netdev=n0,mac=52:54:00:bb:00:$M$BOOT"
    case $FW in
      uefi) [ $L2 = start ] && cp /usr/share/OVMF/OVMF_VARS_4M.fd $K/vars.fd
            EXTRA="-drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd -drive if=pflash,format=raw,file=$K/vars.fd" ;;
      sb)   [ $L2 = start ] && cp /usr/share/OVMF/OVMF_VARS_4M.ms.fd $K/vars.fd
            EXTRA="-machine q35,smm=on -global driver=cfi.pflash01,property=secure,value=on -drive if=pflash,format=raw,unit=0,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.secboot.fd -drive if=pflash,format=raw,unit=1,file=$K/vars.fd"
            NIC="-netdev tap,id=n0,ifname=tk${M}0,script=no,downscript=no -device virtio-net-pci,netdev=n0,mac=52:54:00:bb:00:$M$BOOT -netdev tap,id=n1,ifname=tk${M}1,script=no,downscript=no -device e1000,netdev=n1,mac=52:54:00:bb:01:$M,romfile=" ;;
    esac
    qemu-system-x86_64 -enable-kvm -cpu host -smp 2 -m 3072 -display none -vga std $EXTRA $NIC \
      -drive file=$K/disk.qcow2,if=none,id=d0 -device ahci,id=ah -device ide-hd,drive=d0,bus=ah.0,bootindex=2 \
      -monitor unix:$K/mon.sock,server,nowait -pidfile $K/q.pid -daemonize && echo "KHACH $FW BAT ($L2)" ;;
  key)  for k in "$@"; do m "sendkey $k"; sleep 2; done ;;
  chup) m "screendump $K/$1.ppm"; sleep 1
        python3 -c "from PIL import Image;Image.open('$K/$1.ppm').save('$K/$1.png')" && rm -f $K/$1.ppm && echo $K/$1.png ;;
  stop) [ -f $K/q.pid ] && kill $(cat $K/q.pid) 2>/dev/null; echo DUNG ;;
  # Tat DUNG CACH (nut nguon ACPI) truoc khi doc o dia: tat ngang may that,
  # file Windows vua ghi co the chua xuong dia (NTFS $LogFile - ntfs-3g
  # khong doc) -> tuong la mat file.
  tatdep) m "system_powerdown"
          for i in $(seq 1 60); do kill -0 $(cat $K/q.pid) 2>/dev/null || { echo "DA TAT sau $((i*5))s"; exit 0; }; sleep 5; done
          kill $(cat $K/q.pid) 2>/dev/null; echo "TAT CUONG BUC (qua 5 phut)" ;;
  xem)  # doc ket qua cai tren o Windows (sau khi tatdep)
        qemu-nbd -r -c /dev/nbd1 $K/disk.qcow2 && sleep 2 && partprobe /dev/nbd1; sleep 1
        P=$(lsblk -lnbo NAME,SIZE /dev/nbd1 | grep p | sort -k2 -n | tail -1 | cut -d" " -f1)
        # MBR (BIOS) co the co nhieu phan vung lon - lay phan vung co thu muc Windows
        for x in $(lsblk -lno NAME /dev/nbd1 | grep p); do
          mount -t ntfs-3g -o ro /dev/$x /mnt/w 2>/dev/null || continue
          [ -d /mnt/w/Windows ] && break; umount /mnt/w
        done
        cd /mnt/w/ConsolePi 2>/dev/null && {
          ls; for f in script-ps1.txt script-cmd.txt lenh-them.txt; do [ -f $f ] && echo "$f: $(tr -d "\r\0" < $f | head -c 100)"; done
          echo "=== BAO-CAO"; tr -d "\r" < BAO-CAO-TONG-KET.txt | sed "s/^\xef\xbb\xbf//"
          echo "=== CHUA DAT"; [ -f bao-cao-day-du.json ] && python3 -c "
import json,sys
d=json.load(open('bao-cao-day-du.json',encoding='utf-8-sig'))
d=d if isinstance(d,list) else [d]
for r in d:
    if r.get('Dat') is not True: print(' ', r.get('Nhom'), '|', r.get('Nhan'), '|', r.get('ChiTiet'))"
          echo "=== TIEN TRINH"; tr -d "\r" < tien-trinh.log | grep -E "\]|->" | tail -30; cd /; }
        umount /mnt/w 2>/dev/null; qemu-nbd -d /dev/nbd1 >/dev/null ;;
  esac ;;
*) echo "lenh?"; exit 1 ;;
esac
