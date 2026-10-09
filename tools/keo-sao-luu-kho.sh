#!/bin/bash
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# Chay tren MAY BUILD (timer keo-sao-luu-kho.timer, moi ngay): keo ban sao luu kho moi nhat tu may
# kho (.34) ve may nay -> mat ca may kho van con khoa dang ky thiet bi + co so du lieu.
# Ban sao CHUA BI MAT (khoa, bam mat khau) -> thu muc 700, file 600, chi root.
set -euo pipefail
MAY="${KHO_MAY:-webserver-consolepi}"
DICH="${KHO_DICH:-/root/sao-luu/kho-auto}"
GIU="${KHO_GIU:-30}"
umask 077
mkdir -p "$DICH"; chmod 700 "$DICH"
T="$DICH/.dang-keo.$$"; trap 'rm -f "$T"' EXIT
ssh -o BatchMode=yes -o ConnectTimeout=15 "$MAY" 'sudo cat /var/backups/kho-console-pi/moi-nhat.tgz' > "$T"
# phai la tgz doc duoc, co co so du lieu, va khong qua cu (>3 ngay = timer o may kho dang hong)
tar tzf "$T" | grep -q '^kho/kho.db$' || { echo "Ban keo ve khong hop le"; exit 1; }
RA="$DICH/kho-$(date +%Y%m%d-%H%M%S).tgz"
cmp -s "$T" "$(ls -1t "$DICH"/kho-*.tgz 2>/dev/null | head -1)" 2>/dev/null && { echo "Chua co ban moi hon, giu nguyen"; exit 0; }
mv "$T" "$RA"; trap - EXIT
ls -1t "$DICH"/kho-*.tgz | tail -n +"$((GIU+1))" | xargs -r rm -f --
echo "Da keo ban sao luu kho ve: $RA ($(du -h "$RA" | cut -f1)); con $(ls -1 "$DICH"/kho-*.tgz | wc -l) ban"
if [ -n "$(find "$RA" -mtime +3 2>/dev/null)" ]; then echo "CANH BAO: ban nay cu hon 3 ngay"; fi
