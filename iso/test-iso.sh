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
# Don may ao cu. KHONG dung `pkill -x qemu-system-x86_64`: nhan tien trinh
# (comm) bi kernel cat con 15 ky tu -> that ra la "qemu-system-x86", con -x
# doi khop CHINH XAC nen khong bao gio trung, pkill im lang khong giet gi.
# Hau qua that: may ao cu van song va giu cong 18080/18022, may ao moi bat
# len bi QEMU tu choi ("Could not set up host forwarding rule") roi chet
# ngay, con vong kiem tra thi cu goi vao may ao CU suot 10 phut roi ket
# luan "ISO khong boot duoc" - oan cho ban ISO.
# Cung KHONG dung `pkill -f qemu-system...`: -f khop ca dong lenh nen no
# giet luon chinh phien SSH dang chay lenh nay (da bi hai lan).
ps -eo pid,comm | awk '/qemu-system/{print $1}' | xargs -r kill -9 2>/dev/null
sleep 2
if ss -lnt 2>/dev/null | grep -qE ":18080|:18022"; then
    echo "DUNG LAI: cong 18080/18022 van con bi giu, khong the test sach"
    exit 1
fi
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
