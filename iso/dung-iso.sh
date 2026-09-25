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

# --- Chan truoc: danh sach goi khong duoc chua dau phan tram ---
# live-build cho file danh sach di qua printf. Mot dau phan tram dung truoc
# chu cai se bi hieu la ma dinh dang, printf bo ngang, va MOI DONG CON LAI
# trong danh sach bi nuot mat. `lb build` van bao thanh cong, van sinh ra
# ISO - chi la ISO thieu goi (lan dau gap: mat firmware, cage, chromium,
# user-setup, sudo -> khong dang nhap duoc). Chan o day cho no do som va noi
# ro ly do, thay vi de phat hien sau 20 phut build.
if grep -l "%" config/package-lists/*.list.chroot 2>/dev/null | grep -q .; then
    echo "DUNG LAI: co dau phan tram trong danh sach goi:"
    grep -n "%" config/package-lists/*.list.chroot
    echo "Xoa dau do di (viet chu 'phan tram') roi chay lai."
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
_fw=config/includes.installer/usr/lib/firmware
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

echo "[1/3] don ban build cu..."
lb clean >/dev/null 2>&1 || true

echo "[2/3] cau hinh..."
cau_hinh() {
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
}
cau_hinh

# --- CO Y KHONG chep anh nen sang thu muc grub-pc ---
# Neu co config/bootloaders/grub-pc/splash.svg thi live-build se sinh
# splash.png cho GRUB, va theme do hoa se tu bat len - ma theme do dang
# BI LOI: no ve mot o den dac che kin danh sach muc chon, nguoi dung
# khong bam duoc vao dau. Da kiem chung ca voi theme goc chua sua gi.
# Xem giai thich day du trong config/bootloaders/grub-pc/theme.cfg.
# Menu BIOS (isolinux) van co anh nen binh thuong - duong do khong dinh loi.

echo "[3/3] dung anh dia (20-40 phut)..."
# LOI THAT (25/09/2026, may build moi): debootstrap/apt thinh thoang bao
# "Couldn't download packages: <goi>" - moi lan 1 goi KHAC NHAU, goi do van
# tai duoc ngay sau do (mang toi mirror Debian chap chon). Mot goi loi la ca
# ban build hong. Chi voi DUNG loi tai goi thi build lai (toi da 3 lan,
# goi da tai nam trong cache/ nen lan sau nhanh); loi khac dung ngay.
for lan in 1 2 3; do
    lb build > build.log 2>&1 || true
    ls *.iso >/dev/null 2>&1 && break
    grep -qE "Couldn't download|Failed to fetch|Hash Sum mismatch" build.log || break
    echo "  lan $lan: loi tai goi ($(grep -oE "Couldn't download packages: .*|Failed to fetch [^ ]*" build.log | head -1)) - build lai"
    lb clean >/dev/null 2>&1 || true
    cau_hinh        # BAT BUOC sau lb clean (xem dau file) - khong thi lb build bo ngang
    sleep 30
done

# KHONG tin ma thoat cua lb build - no nuot loi o buoc don dep cuoi va van
# tra 0. Chi co FILE ISO THAT moi la bang chung.
if ls *.iso >/dev/null 2>&1; then
    echo "XONG: $(ls -la *.iso | awk "{printf \"%.0f MB\", \$5/1048576}")"
    exit 0
fi
echo "THAT BAI - khong sinh ra ISO. Loi trong log:"
grep -E "^E:" build.log | head -5
exit 1
