#!/bin/bash
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# Thu NHANH 1 phan mem cai im lang (~3-5 phut, khong cai lai Windows) - chay tren Console Pi.
# Chep bo cai sang may build roi chay iso/test/thu-silent.sh o do (may mau Windows 10 Pro).
#   bash tools/thu-phan-mem.sh <bo cai | ten file trong deploy/apps> "<tham so>"
#   bash tools/thu-phan-mem.sh <bo cai | ten file trong deploy/apps> --tu-do   # tu doan, thu lan luot
set -e
F=${1:?thieu bo cai}; TS=${2:?thieu tham so hoac --tu-do}
[ -f "$F" ] || F=/var/lib/console-pi/deploy/apps/$F
sudo test -f "$F" || { echo "Khong thay $1"; exit 1; }
TEN=$(basename "$F")
sudo cat "$F" | ssh build-consolepi "cat > /tmp/thu-$TEN"
ssh build-consolepi "bash /build/test/thu-silent.sh '/tmp/thu-$TEN' '$TS' ${3:-}; rc=\$?; rm -f '/tmp/thu-$TEN'; exit \$rc"
