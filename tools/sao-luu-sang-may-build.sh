#!/bin/bash
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
#
# Sao luu nhung thu KHONG nam tren GitHub (du lieu + bi mat rieng cua Console
# Pi dang dung, va du lieu cua kho) sang may build, de lo the nho / o cung Pi
# hong thi dung lai duoc may y het. Ma nguon thi da o GitHub - xem
# docs/KHOI-PHUC-TU-DAU.md.
#
# Chay tren Console Pi (user thuong, co sudo):  bash tools/sao-luu-sang-may-build.sh
# (can SSH key toi may build + may kho trong ~/.ssh/config)
#
# KHONG dua cac file nay len GitHub: chua mat khau, token tunnel, khoa ky.
# Anh anh / file ISO Windows (vai chuc GB trong deploy/os, deploy/ungdung,
# deploy/apps) KHONG nam trong goi nay - xem muc "Du lieu nang" trong tai lieu.
set -euo pipefail

[ "$(id -u)" = 0 ] && { echo "Chay bang user thuong (script tu goi sudo khi can)"; exit 1; }
NHA=$HOME
SSH="ssh -o BatchMode=yes"
MAY_BUILD=build-consolepi
MAY_KHO=webserver-consolepi
DICH=/root/sao-luu
NGAY=$(date +%Y%m%d-%H%M)
TAM=$(mktemp -d)
trap 'rm -rf "$TAM"' EXIT

echo "== 1. Du lieu + cau hinh Console Pi"
DS=(
  /var/lib/console-pi
  /opt/console-pi/config.json
  /opt/console-pi/port-names.json
  /opt/console-pi/flask-secret.key
  /opt/console-pi/screen-rotation
  /opt/console-pi/nettools/ifthen-rules.json
  /opt/console-pi/backups
  /opt/console-pi/tftp
  /etc/cloudflared
  /etc/NetworkManager/system-connections
  /etc/udev/rules.d/99-consolepi-touch.rules
  /etc/hostname
  /etc/hosts
  "$NHA/.config/zt"
  "$NHA/.ssh"
)
CO=()
for p in "${DS[@]}"; do [ -e "$p" ] && CO+=("$p"); done
sudo tar -czf "$TAM/pi-$NGAY.tar.gz" \
  --exclude=/var/lib/console-pi/deploy/os \
  --exclude=/var/lib/console-pi/deploy/ungdung \
  --exclude=/var/lib/console-pi/deploy/fonts \
  --exclude='/var/lib/console-pi/deploy/apps/*.exe' \
  --exclude='/var/lib/console-pi/deploy/apps/*.msi' \
  --exclude='/var/lib/console-pi/deploy/apps/*.zip' \
  "${CO[@]}" 2>/dev/null || [ $? = 1 ]
sudo chown "$(id -u)" "$TAM/pi-$NGAY.tar.gz"
du -h "$TAM/pi-$NGAY.tar.gz"

echo "== 2. Du lieu kho (tu may kho)"
$SSH $MAY_KHO "tar -czf - -C / var/lib/kho-console-pi etc/systemd/system/kho-console-pi.service \
  \$(ls -d etc/nginx/sites-enabled etc/cloudflared 2>/dev/null)" > "$TAM/kho-$NGAY.tar.gz"
du -h "$TAM/kho-$NGAY.tar.gz"

echo "== 3. Chep sang may build: $MAY_BUILD:$DICH"
$SSH $MAY_BUILD "mkdir -p $DICH && chmod 700 $DICH"
for f in "$TAM"/*.tar.gz; do
  $SSH $MAY_BUILD "cat > $DICH/$(basename "$f")" < "$f"
done
# Giu 10 ban moi nhat moi loai
$SSH $MAY_BUILD "cd $DICH && chmod 600 *.tar.gz && for l in pi kho; do ls -1t \$l-*.tar.gz | tail -n +11 | xargs -r rm -f; done; ls -lh $DICH"
echo "XONG"
