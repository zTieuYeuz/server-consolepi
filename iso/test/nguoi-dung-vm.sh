#!/bin/bash
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# CHI DE TEST: may ao "nguoi dung moi" - cam ISO nhu USB, chup man hinh (screendump), gui phim; dung de lam theo
# docs tung buoc (boot menu -> Calamares -> web). Thu muc lam viec /build/test/nguoidung. Chuot ao khong on dinh -> dung phim tat (alt-t, alt-c).
# vm.sh start <iso> | shot <ten> | key <phim...> | stop     (may "nguoi dung" thu cai tu ISO nhu USB)
D=/build/test/nguoidung; cd $D
mon(){ echo "$1" | socat - UNIX-CONNECT:$D/mon.sock >/dev/null; }
case "$1" in
start)
  [ -f $D/q.pid ] && kill $(cat $D/q.pid) 2>/dev/null; rm -f $D/q.pid mon.sock
  [ -f disk.qcow2 ] || qemu-img create -q -f qcow2 disk.qcow2 20G
  [ -f vars.fd ] && [ "$3" = keepvars ] || cp /usr/share/OVMF/OVMF_VARS_4M.fd vars.fd
  USBARGS="-device qemu-xhci"; [ "$2" != none ] && USBARGS="-device qemu-xhci -drive if=none,id=usb,file=$2,format=raw,readonly=on -device usb-storage,drive=usb,bootindex=1"
  qemu-system-x86_64 -enable-kvm -cpu host -m 3072 -smp 2 -vga std -display none -pidfile $D/q.pid -daemonize \
    -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd -drive if=pflash,format=raw,file=$D/vars.fd \
    $USBARGS \
    -drive file=$D/disk.qcow2,if=virtio,format=qcow2 -device usb-tablet \
    -netdev user,id=n0,hostfwd=tcp::28080-:80,hostfwd=tcp::28022-:22 -device e1000,netdev=n0 \
    -monitor unix:$D/mon.sock,server,nowait ;;
shot) mon "screendump $D/$2.ppm"; sleep 1; python3 -c "
from PIL import Image; Image.open('$D/$2.ppm').save('$D/$2.png')"; rm -f $D/$2.ppm; ls $D/$2.png ;;
key) shift; for k in "$@"; do mon "sendkey $k"; sleep 0.4; done ;;
click) X=$2; Y=$3; mon "mouse_move $X $Y"; sleep 0.3; mon "mouse_button 1"; sleep 0.2; mon "mouse_button 0" ;;
type) shift; s="$1"; for ((n=0;n<${#s};n++)); do ch="${s:n:1}"; case "$ch" in [a-z0-9]) k=$ch;; [A-Z]) k="shift-$(echo $ch|tr A-Z a-z)";; @) k=shift-2;; .) k=dot;; -) k=minus;; ' ') k=spc;; :) k=shift-semicolon;; /) k=slash;; '\\') k=backslash;; _) k=shift-minus;; *) k=$ch;; esac; mon "sendkey $k"; sleep 0.15; done ;;
stop) [ -f $D/q.pid ] && kill $(cat $D/q.pid); rm -f $D/q.pid ;;
esac
