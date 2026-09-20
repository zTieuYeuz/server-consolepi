#!/bin/bash
# Console System - dung ISO ban 32-bit (Debian 12 / i386).
#
# Vi sao Debian 12 chu khong phai 13: Debian DA BO HAN kernel va trinh cai
# dat 32-bit tu ban 13 (da tra kho: 0 goi linux-image-686 trong trixie, 4
# goi trong bookworm). Muon chay duoc may 32-bit thi bat buoc dung ban 12.
set -e
cd "$(dirname "$0")"
echo "[1/3] don..."; lb clean >/dev/null 2>&1 || true
echo "[2/3] cau hinh..."
lb config \
  --distribution bookworm --architectures i386 \
  --archive-areas "main contrib non-free non-free-firmware" \
  --binary-images iso-hybrid --bootloaders syslinux \
  --debian-installer live --debian-installer-gui false \
  --firmware-binary true --firmware-chroot false \
  --apt-recommends false \
  --memtest none \
  --linux-flavours 686-pae \
  --iso-application "Console System (32-bit)" --iso-publisher "Console System" \
  --iso-volume "CONSOLE-SYS-32" \
  --bootappend-live "boot=live components quiet splash hostname=console-system" \
  >/tmp/lb-config-i386.log 2>&1
echo "[3/3] dung anh dia..."
lb build > build.log 2>&1 || true
if ls *.iso >/dev/null 2>&1; then
    echo "XONG: $(ls -la *.iso | awk '{printf "%.0f MB", $5/1048576}')"; exit 0
fi
echo "THAT BAI:"; grep -E "^E:" build.log | head -5; exit 1
