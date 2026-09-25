#!/bin/bash
# ===================================================================
# CHI DUNG DE TEST TREN MAY AO BO DI - KHONG PHAI PRESEED PHAT HANH.
# ===================================================================
# Cai TU DONG ban ISO len 1 o ao TRANG trong QEMU (UEFI, ISO cam nhu USB).
# Tham so chia o/mat khau nam o dong lenh kernel cua may ao nay, KHONG nam
# trong ISO (quy tac: ISO phat hanh khong bao gio dien san o dia/chia o).
# Mat khau thu: administrator / Test12345 - chi ton tai trong may ao test.
#
#   bash iso/test/cai-uefi.sh [iso] [thu_muc] [dung_luong]
# Ket qua: <thu_muc>/disk.qcow2 (+ vars.fd) - boot bang boot-uefi.sh
ISO="${1:-/build/console-system/live-image-amd64.hybrid.iso}"
W="${2:-/build/test/uefi}"; CO="${3:-12G}"
# Chi tat may ao CUA CHINH thu muc nay (co the dang co may ao test khac
# chay song song). Khong dung pkill -f (tu giet phien SSH - da bi 2 lan).
[ -f $W/q.pid ] && kill -9 $(cat $W/q.pid) 2>/dev/null; sleep 1
mkdir -p $W && cd $W && rm -rf ./*
mkdir -p mnt; umount mnt 2>/dev/null; mount -o loop,ro "$ISO" mnt
cp mnt/install/vmlinuz mnt/install/initrd.gz .; umount mnt
cp /usr/share/OVMF/OVMF_VARS_4M.fd vars.fd
qemu-img create -f qcow2 disk.qcow2 $CO >/dev/null
CMD="auto=true priority=critical console=ttyS0,115200n8 \
partman-auto/method=regular partman-auto/disk=/dev/vda partman-auto/choose_recipe=atomic \
partman-lvm/device_remove_lvm=true partman-lvm/confirm=true partman-lvm/confirm_nooverwrite=true \
partman-md/confirm=true partman-partitioning/confirm_write_new_label=true \
partman/choose_partition=finish partman/confirm=true partman/confirm_nooverwrite=true \
partman-efi/non_efi_system=true \
passwd/user-fullname=Administrator passwd/username=administrator \
passwd/user-password=Test12345 passwd/user-password-again=Test12345 passwd/root-login=false \
cdrom-detect/eject=false finish-install/reboot_in_progress=note"
timeout 3600 qemu-system-x86_64 -enable-kvm -cpu host -m 3072 -smp 2 -no-reboot -pidfile $W/q.pid \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
  -drive if=pflash,format=raw,file=$W/vars.fd \
  -kernel vmlinuz -initrd initrd.gz -append "$CMD" \
  -device qemu-xhci -drive if=none,id=usbstick,file="$ISO",format=raw,readonly=on \
  -device usb-storage,drive=usbstick \
  -drive file=disk.qcow2,if=virtio,format=qcow2 \
  -display none -serial file:$W/serial.log \
  -netdev user,id=n0 -device e1000,netdev=n0
echo "QEMU thoat, ma=$?"
tr -d '\033' < serial.log | grep -aoE "(Installing GRUB[^.]*|Finishing the installation|Installation complete|failed[^\r]{0,80})" | sort -u | tail -8
