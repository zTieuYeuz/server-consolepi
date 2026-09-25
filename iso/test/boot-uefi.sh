#!/bin/bash
# CHI DE TEST: boot o ao da cai bang cai-uefi.sh (card man hinh std-VGA de
# kiosk ve bang CPU nhu may ao that), SSH qua cong 18022, man hinh qua
# monitor: echo "screendump /build/test/uefi/x.ppm" | socat - UNIX-CONNECT:/build/test/uefi/mon.sock
W=/build/test/uefi
cp /usr/share/OVMF/OVMF_VARS_4M.fd $W/vb.fd 2>/dev/null
[ -f $W/vars.fd ] && cp $W/vars.fd $W/vb.fd
systemd-run --unit=vmk --collect qemu-system-x86_64 -m 3072 -smp 2 -vga std \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
  -drive if=pflash,format=raw,file=$W/vb.fd \
  -drive file=$W/disk.qcow2,if=virtio,format=qcow2 -display none \
  -netdev user,id=n0,hostfwd=tcp::18022-:22,hostfwd=tcp::18080-:80 -device e1000,netdev=n0 \
  -monitor unix:$W/mon.sock,server,nowait
