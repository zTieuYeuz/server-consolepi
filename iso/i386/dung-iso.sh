#!/bin/bash
# Console System - dung ISO ban 32-bit (Debian 12 / i386).
#
# Vi sao Debian 12 chu khong phai 13: Debian DA BO HAN kernel va trinh cai
# dat 32-bit tu ban 13 (da tra kho: 0 goi linux-image-686 trong trixie, 4
# goi trong bookworm). Muon chay duoc may 32-bit thi bat buoc dung ban 12.
set -e
cd "$(dirname "$0")"
# --- Chan truoc: danh sach goi khong duoc chua dau phan tram ---
# live-build cho file danh sach di qua printf. Mot dau phan tram dung truoc
# chu cai se bi hieu la ma dinh dang, printf bo ngang, va MOI DONG CON LAI
# trong danh sach bi nuot mat. `lb build` van bao thanh cong, van sinh ra
# ISO - chi la ISO thieu goi (lan dau gap tren ban amd64: mat firmware,
# cage, chromium, user-setup, sudo -> khong dang nhap duoc).
if grep -l "%" config/package-lists/*.list.chroot 2>/dev/null | grep -q .; then
    echo "DUNG LAI: co dau phan tram trong danh sach goi:"
    grep -n "%" config/package-lists/*.list.chroot
    exit 1
fi

# --- Nhung san firmware card mang Realtek vao BO CAI (initrd) ---
# LOI THAT (22/09/2026, anh Thoai cai len mini PC that bang USB Rufus):
# bo cai dung lai hoi "Load missing firmware from removable media?
# rtl_nic/rtl8168h-2.fw" - bat cam USB/dia mem chua firmware. File do CO
# SAN trong /firmware cua ISO, nhung bo cai chi tim o do dung MOT lan
# (va phai mount duoc dung o USB tai dung thoi diem); truot la hoi. Mini PC
# gia re gan nhu cai nao cung dung card Realtek (r8169/r8125), nen nhet
# thang cac file rtl_nic (~140KB) vao initrd cua bo cai: driver nap la
# thay firmware ngay, khong con gi de hoi. Card Intel (e1000e/igc) khong
# can firmware. May da cai xong van co du firmware tu goi firmware-realtek.
_fw=config/includes.installer/lib/firmware
# Ban 32-bit (Debian 12): initrd cua bo cai dung /lib/firmware that, chua
# gop vao /usr/lib nhu Debian 13 - dat sai cho la driver khong thay.
rm -rf "$_fw/rtl_nic"
_tmp="$(mktemp -d)"
( cd "$_tmp" && apt-get download firmware-realtek >/dev/null 2>&1 ) || true
_deb="$(ls cache/packages.chroot/firmware-realtek_*.deb "$_tmp"/firmware-realtek_*.deb 2>/dev/null | head -1)"
if [ -z "$_deb" ]; then
    echo "DUNG LAI: khong lay duoc goi firmware-realtek de nhung vao bo cai"
    rm -rf "$_tmp"; exit 1
fi
dpkg-deb -x "$_deb" "$_tmp/x"
mkdir -p "$_fw"
# Goi Debian 12 de o /lib/firmware, Debian 13 o /usr/lib/firmware
_src="$(find "$_tmp/x" -type d -name rtl_nic | head -1)"
[ -n "$_src" ] || { echo "DUNG LAI: goi firmware-realtek khong co rtl_nic"; exit 1; }
cp -a "$_src" "$_fw/"
rm -rf "$_tmp"
echo "[0/3] da nhung $(ls "$_fw/rtl_nic" | wc -l) file firmware Realtek vao bo cai"

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
