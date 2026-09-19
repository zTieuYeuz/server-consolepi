#!/bin/bash
# ===================================================================
# Console System - test TU DONG anh dia ISO
# ===================================================================
# Boot ISO trong QEMU co CHUYEN TIEP CONG, roi goi thang vao dashboard
# dang chay BEN TRONG do. Day moi la bang chung that: khong chi "co file
# ISO" hay "boot len man hinh", ma la "dich vu ben trong that su phuc vu
# duoc". Khong can nguoi ngoi nhin.
ISO="${1:-/build/console-system/live-image-amd64.hybrid.iso}"
RAM="${2:-2048}"        # 2GB - mo phong may cu, kiem luon tieu chi may yeu
CHO="${3:-420}"         # giay cho toi da (khong co KVM nen gia lap cham)

[ -f "$ISO" ] || { echo "KHONG THAY ISO: $ISO"; exit 1; }
pkill -x qemu-system-x86_64 2>/dev/null; sleep 1
rm -f /tmp/qtest.log /tmp/qtest-mon.sock /tmp/qtest*.ppm

qemu-system-x86_64 \
  -m "$RAM" -smp 2 \
  -cdrom "$ISO" -boot d \
  -display none \
  -netdev user,id=n0,hostfwd=tcp::18080-:80,hostfwd=tcp::18022-:22 \
  -device e1000,netdev=n0 \
  -monitor unix:/tmp/qtest-mon.sock,server,nowait \
  > /tmp/qtest.log 2>&1 &
QPID=$!
echo "QEMU pid=$QPID, RAM=${RAM}MB, cho toi da ${CHO}s"

# Doi dashboard tra loi qua cong da chuyen tiep
t=0; ok=0
while [ $t -lt "$CHO" ]; do
    sleep 10; t=$((t+10))
    ma=$(curl -s -o /tmp/qtest-trang.html -w "%{http_code}" --max-time 5 http://127.0.0.1:18080/ 2>/dev/null)
    if [ "$ma" = "200" ] || [ "$ma" = "302" ]; then
        echo "  [${t}s] dashboard TRA LOI: HTTP $ma"
        ok=1; break
    fi
    kill -0 $QPID 2>/dev/null || { echo "  QEMU da chet o giay $t"; break; }
    [ $((t % 60)) -eq 0 ] && echo "  [${t}s] chua len, doi tiep..."
done
echo "screendump /tmp/qtest-manhinh.ppm" | timeout 15 socat - UNIX-CONNECT:/tmp/qtest-mon.sock >/dev/null 2>&1
echo "KETQUA_DASHBOARD=$ok"
exit 0
