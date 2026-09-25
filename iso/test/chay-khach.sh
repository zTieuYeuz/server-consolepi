#!/bin/bash
# chay-khach.sh <fw> <so lan bam down trong danh sach kich ban>  (chay tren may build)
FW=$1; XUONG=$2; cd /build/test
bash may-chu-iso.sh khach $FW start >/dev/null
for i in $(seq 1 60); do bash may-chu-iso.sh ssh "sudo journalctl -u console-pi-dashboard --since -30s --no-pager | grep -q menu.ipxe" && break; sleep 3; done
echo "menu sau $((i*3))s"; sleep 3
bash may-chu-iso.sh khach $FW key up ret; sleep 3
K=""; for n in $(seq 1 $XUONG); do K="$K down"; done
bash may-chu-iso.sh khach $FW key $K ret; sleep 25
bash may-chu-iso.sh ssh "sudo journalctl -u console-pi-dashboard --since -90s --no-pager | grep pxeboot | awk '{print \$12}' | uniq -c"
systemctl stop chup-lab-$FW 2>/dev/null
systemd-run --unit=chup-lab-$FW --collect bash -c "cd /build/test; for i in \$(seq -w 1 200); do kill -0 \$(cat srv/khach-$FW/q.pid) 2>/dev/null || break; bash may-chu-iso.sh khach $FW chup t\$i >/dev/null; sleep 60; done"
