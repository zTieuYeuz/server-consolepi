#!/bin/bash
# ===================================================================
# Console System - dung file ISO
# ===================================================================
# VI SAO CO SCRIPT NAY: da HAI LAN mat cong vi lam sai THU TU. `lb clean`
# xoa luon dau moc "da cau hinh" trong .build/, nen neu chay `lb build`
# ngay sau do thi no bo ngang voi loi kho hieu:
#     E: the following stage is required to be done first: config
# ma van tra ve ma thoat 0 - systemd bao "success" trong khi khong he co
# file ISO nao. Thu tu DUNG luon la: clean -> config -> build.
set -e
cd "$(dirname "$0")"

echo "[1/3] don ban build cu..."
lb clean >/dev/null 2>&1 || true

echo "[2/3] cau hinh..."
lb config \
  --distribution trixie --architectures amd64 \
  --archive-areas "main contrib non-free non-free-firmware" \
  --binary-images iso-hybrid --bootloaders "syslinux,grub-efi" \
  --uefi-secure-boot enable \
  --debian-installer live --debian-installer-gui false \
  --firmware-binary true --firmware-chroot false \
  --apt-recommends false \
  --memtest none \
  --iso-application "Console System" --iso-publisher "Console System" \
  --iso-volume "CONSOLE-SYSTEM" \
  --bootappend-live "boot=live components quiet splash hostname=console-system" \
  >/tmp/lb-config.log 2>&1

echo "[3/3] dung anh dia (20-40 phut)..."
lb build > build.log 2>&1 || true

# KHONG tin ma thoat cua lb build - no nuot loi o buoc don dep cuoi va van
# tra 0. Chi co FILE ISO THAT moi la bang chung.
if ls *.iso >/dev/null 2>&1; then
    echo "XONG: $(ls -la *.iso | awk "{printf \"%.0f MB\", \$5/1048576}")"
    exit 0
fi
echo "THAT BAI - khong sinh ra ISO. Loi trong log:"
grep -E "^E:" build.log | head -5
exit 1
