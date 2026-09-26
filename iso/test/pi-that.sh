#!/bin/bash
# ===================================================================
# CHI DE TEST: may ao tren MAY BUILD boot qua mang tu CONSOLE PI THAT (che
# do "mang co san DHCP") - may ao ra LAN that qua macvtap (khong doi cau
# hinh mang cua may build). Cai Windows TRON VEN len o ao 60 GB.
#
#   bash pi-that.sh <bios|uefi|sb> start    -> bat may (o moi), in IP/MAC
#   bash pi-that.sh <fw> key <phim...>        -> gui phim (sendkey cua QEMU)
#   bash pi-that.sh <fw> chup <ten>           -> chup man hinh ra PNG
#   bash pi-that.sh <fw> odia               -> bat lai CHI boot o cung (giu o + NVRAM)
#   bash pi-that.sh <fw> stop
# Nguoi dieu khien (Claude tren Pi) doc log HTTP cua Pi de biet luc nao may
# ao tai menu.ipxe roi moi gui phim chon kich ban.
# MAC co dinh theo kieu may -> router cong ty cap lai dung 1 IP moi lan.
# Bien moi truong: CARD=e1000-82545em (card cua VMware) | vmxnet3 | e1000e...,
# RAM=MB (mac dinh 4096), DISK=ahci (mac dinh) | pvscsi | virtio | nvme
# (bo dieu khien o dia WinPE khong co san driver -> test goi driver pho bien).
# ===================================================================
FW=$1; LENH=$2; shift 2
D=/build/test/pi-that/$FW; mkdir -p $D
IF=$(ip route show default | awk '{print $5; exit}')
case $FW in bios) M=02; ;; uefi) M=03; ;; sb) M=04; ;; *) echo "fw?"; exit 1;; esac
MAC0=52:54:00:c5:00:$M; MAC1=52:54:00:c5:01:$M
m(){ echo "$1" | socat - UNIX-CONNECT:$D/mon.sock >/dev/null; }

case $LENH in
start|odia)
  # Moi may cai xong chiem 7-22 GB; het cho thi QEMU tam dung (io-error) va
  # nhin nhu "treo" (lab 26/09/2026). Can it nhat 15 GB trong.
  CON=$(df -BG --output=avail /build | tail -1 | tr -dc 0-9)
  [ "$CON" -lt 15 ] && { echo "HET CHO: con ${CON}G tren /build - xoa o may test cu (pi-that/*/disk.qcow2)"; exit 1; }
  [ -f $D/q.pid ] && kill $(cat $D/q.pid) 2>/dev/null; sleep 1
  for n in 0 1; do ip link del mvt$M$n 2>/dev/null; done
  rm -f $D/mon.sock
  [ $LENH = start ] && { rm -f $D/disk.qcow2; qemu-img create -q -f qcow2 $D/disk.qcow2 60G; }
  ip link add link $IF name mvt${M}0 address $MAC0 type macvtap mode bridge
  ip link set mvt${M}0 up
  T0=/dev/tap$(cat /sys/class/net/mvt${M}0/ifindex)
  EXTRA=""; NIC="-netdev tap,id=n0,fd=3 -device ${CARD:-e1000},netdev=n0,mac=$MAC0,bootindex=1"
  FDS="3<>$T0"
  case $FW in
    uefi) [ $LENH = start ] && cp /usr/share/OVMF/OVMF_VARS_4M.fd $D/vars.fd
          EXTRA="-drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd -drive if=pflash,format=raw,file=$D/vars.fd" ;;
    sb)   # Secure Boot BAT that (khoa Microsoft). ROM iPXE cua e1000 khong ky
          # -> boot mang bang virtio-net (driver OVMF co ky); WinPE dung e1000.
          ip link add link $IF name mvt${M}1 address $MAC1 type macvtap mode bridge
          ip link set mvt${M}1 up
          T1=/dev/tap$(cat /sys/class/net/mvt${M}1/ifindex)
          [ $LENH = start ] && cp /usr/share/OVMF/OVMF_VARS_4M.ms.fd $D/vars.fd
          EXTRA="-machine q35,smm=on -global driver=cfi.pflash01,property=secure,value=on -drive if=pflash,format=raw,unit=0,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.secboot.fd -drive if=pflash,format=raw,unit=1,file=$D/vars.fd"
          NIC="-netdev tap,id=n0,fd=3 -device virtio-net-pci,netdev=n0,mac=$MAC0,bootindex=1 -netdev tap,id=n1,fd=4 -device e1000,netdev=n1,mac=$MAC1,romfile="
          FDS="3<>$T0 4<>$T1" ;;
  esac
  # odia: card mang van co (Windows can mang) nhung KHONG boot mang
  [ $LENH = odia ] && NIC=$(echo "$NIC" | sed 's/,bootindex=1/,romfile=/; s/romfile=,romfile=/romfile=/')
  case ${DISK:-ahci} in
    pvscsi) OD="-device pvscsi,id=s0 -device scsi-hd,drive=d0,bus=s0.0,bootindex=2" ;;
    virtio) OD="-device virtio-blk-pci,drive=d0,bootindex=2" ;;
    nvme)   OD="-device nvme,drive=d0,serial=cpi0001,bootindex=2" ;;
    *)      OD="-device ahci,id=ah -device ide-hd,drive=d0,bus=ah.0,bootindex=2" ;;
  esac
  eval "qemu-system-x86_64 -enable-kvm -cpu host -smp 4 -m ${RAM:-4096} -display none -vga std $EXTRA $NIC \
    -drive file=$D/disk.qcow2,if=none,id=d0 $OD \
    -monitor unix:$D/mon.sock,server,nowait -pidfile $D/q.pid -daemonize $FDS" || { echo QEMU_LOI; exit 1; }
  echo "BAT $FW mac=$MAC0 pid=$(cat $D/q.pid)" ;;
key)  for k in "$@"; do m "sendkey $k"; sleep 2; done ;;
chup) m "screendump $D/$1.ppm"; sleep 1
      python3 -c "from PIL import Image;Image.open('$D/$1.ppm').save('$D/$1.png')" && echo $D/$1.png ;;
stop) [ -f $D/q.pid ] && kill $(cat $D/q.pid) 2>/dev/null
      for n in 0 1; do ip link del mvt$M$n 2>/dev/null; done; echo DUNG ;;
esac
