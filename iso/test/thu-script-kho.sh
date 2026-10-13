#!/bin/bash
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# THU THAT bo script kho (50 file .ps1) tren may mau Windows 10 (/build/test/vang - xem thu-silent.sh).
#   thu-script-kho.sh [thu_muc_script = /build/kho-script/out]
# Chep script + check vao o phu qcow2, bat may, runner chay 2 luot (kiem sau moi script), khoi dong
# lai, kiem lai + kiem ho so Default User. Chi 1 lan thu tai 1 thoi diem (chung khoa voi thu-silent.sh).
set -u
VANG=/build/test/vang; LAM=/build/test/thu-script-tam; HERE=$(cd "$(dirname "$0")" && pwd)
NGUON=${1:-/build/kho-script/out}
[ -f $VANG/disk.qcow2 ] || { echo "Chua co may mau $VANG"; exit 1; }
[ -f $NGUON/manifest.json ] || { echo "Thieu $NGUON/manifest.json"; exit 1; }
exec 9>/build/test/thu-silent.lock; flock 9
modprobe nbd max_part=8
umount /mnt/vang 2>/dev/null; qemu-nbd -d /dev/nbd0 >/dev/null 2>&1; sleep 1
rm -rf $LAM; mkdir -p $LAM
qemu-img create -q -f qcow2 -b $VANG/disk.qcow2 -F qcow2 $LAM/o.qcow2
cp $VANG/vars.fd $LAM/vars.fd
qemu-nbd -c /dev/nbd0 $LAM/o.qcow2; sleep 2
mkdir -p /mnt/vang
try=0; until mount -t ntfs-3g -o rw,remove_hiberfile /dev/nbd0p3 /mnt/vang 2>/dev/null; do try=$((try+1)); [ $try -ge 5 ] && { qemu-nbd -d /dev/nbd0; echo "mount loi"; exit 2; }; sleep 4; done
rm -rf /mnt/vang/ConsolePi/ks /mnt/vang/ConsolePi/logs
mkdir -p /mnt/vang/ConsolePi/ks
if [ -n "${SOLO:-}" ]; then   # chi thu vai script: SOLO="39-tat-tac-vu-theo-doi 07-dinh-dang-viet-nam"
  python3 - "$NGUON" /mnt/vang/ConsolePi/ks $SOLO <<'XONGPY'
import json, shutil, sys
src, dst, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
m = [x for x in json.load(open(src + "/manifest.json", encoding="utf-8")) if x["id"] in ids]
for x in m:
    for f in (x["id"] + ".ps1", "c-" + x["id"] + ".ps1"): shutil.copy(src + "/" + f, dst)
json.dump(m, open(dst + "/manifest.json", "w", encoding="utf-8"), ensure_ascii=False)
XONGPY
else
  cp $NGUON/*.ps1 $NGUON/manifest.json /mnt/vang/ConsolePi/ks/
fi
cp "$HERE/thu-script-kho-guest.ps1" /mnt/vang/ConsolePi/ks/cs-runner.ps1
mkdir -p "/mnt/vang/ProgramData/Microsoft/Windows/Start Menu/Programs/StartUp"
printf '@echo off\r\npowershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\\ConsolePi\\ks\\cs-runner.ps1\r\n' \
  > "/mnt/vang/ProgramData/Microsoft/Windows/Start Menu/Programs/StartUp/cs-ks.cmd"
sync; umount /mnt/vang; qemu-nbd -d /dev/nbd0 >/dev/null
rm -f $LAM/q.pid $LAM/mon.sock
qemu-system-x86_64 -enable-kvm -cpu host -smp 4 -m 4096 -display none -vga std \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
  -drive if=pflash,format=raw,file=$LAM/vars.fd \
  -netdev user,id=n0 -device e1000,netdev=n0 \
  -drive file=$LAM/o.qcow2,if=none,id=d0 -device ahci,id=ah -device ide-hd,drive=d0,bus=ah.0 \
  -monitor unix:$LAM/mon.sock,server,nowait -pidfile $LAM/q.pid -daemonize || { echo "QEMU loi"; exit 2; }
pid=$(cat $LAM/q.pid); han=$(( $(date +%s) + ${HAN_PHUT:-120} * 60 ))
echo "may mau dang chay (2 luot -> khoi dong lai -> kiem lai -> tat), toi da ${HAN_PHUT:-120} phut..."
while kill -0 "$pid" 2>/dev/null; do
  [ "$(date +%s)" -gt "$han" ] && { echo "(het gio - ep tat)"; kill "$pid"; sleep 3; break; }
  sleep 10
done
qemu-nbd -r -c /dev/nbd0 $LAM/o.qcow2; sleep 2
mount -o ro /dev/nbd0p3 /mnt/vang 2>/dev/null
rm -rf $LAM/logs; mkdir -p $LAM/logs
cp /mnt/vang/ConsolePi/logs/* $LAM/logs/ 2>/dev/null
cp /mnt/vang/ConsolePi/ks/ket-qua.json $LAM/ 2>/dev/null
cp -r /mnt/vang/ConsolePi/reports $LAM/ 2>/dev/null
umount /mnt/vang 2>/dev/null; qemu-nbd -d /dev/nbd0 >/dev/null
[ "${GIU:-0}" = 1 ] || rm -f $LAM/o.qcow2
[ -f $LAM/ket-qua.json ] || { echo "(khong co ket qua - runner khong chay duoc)"; exit 1; }
python3 "$HERE/thu-script-kho-bao-cao.py" $LAM/ket-qua.json
