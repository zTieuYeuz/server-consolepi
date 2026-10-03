#!/bin/bash
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
#
# Dung ANH THE NHO cho Raspberry Pi (Pi 3/4/5, 64-bit): Raspberry Pi OS Lite 64-bit
# chinh thuc + Console Pi cai san. Chay tren may build (x86, Debian 13):
#     bash iso/pi/dung-anh-pi.sh            -> /build/pi/ConsoleSystem-<ban>-raspberrypi.img.xz
#
# VI SAO (anh Thoai 03/10/2026): khach muon "tai 1 file, ghi the, cam vao Pi la chay"
# nhu ban ISO. ISO x86 khong chay duoc tren Pi (chip ARM) nen can anh rieng.
#
# CACH LAM: mo anh Pi OS, chay install.sh TRONG chroot (qemu-user gia lap ARM) de cai
# san MOI goi; KHONG tao tai khoan (Raspberry Pi Imager tao khi ghi the). Lan khoi
# dong dau, console-system-pi-lan-dau doi tai khoan roi chay lai install.sh tren may.
# Bi mat rieng tung may (mat khau AP, khoa Samba, khoa SSH...) XOA khoi anh de moi
# the tu sinh moi - khong dung chung giua cac may da ban.
set -euo pipefail
REPO="${REPO:-/root/consolepi-toolkit}"
RA="${RA:-/build/pi}"
CACHE=/var/cache/zt-pi
URL="https://downloads.raspberrypi.com/raspios_lite_arm64_latest"
BAN="$(tr -d '[:space:]' < "$REPO/VERSION")"
M="$RA/mnt"

say() { echo "== $(date +%H:%M:%S) $*"; }
don_dep() {
    set +e
    for d in dev/pts dev proc sys boot/firmware ""; do
        mountpoint -q "$M/$d" && umount -l "$M/$d"
    done
    [ -n "${LOOP:-}" ] && losetup -d "$LOOP" 2>/dev/null
}
trap don_dep EXIT

say "Cong cu dung anh (qemu-user, parted...)"
apt-get install -y -q qemu-user-static binfmt-support parted e2fsprogs xz-utils curl rsync >/dev/null
[ -e /proc/sys/fs/binfmt_misc/qemu-aarch64 ] || systemctl restart systemd-binfmt

say "Tai Raspberry Pi OS Lite 64-bit (chinh thuc, kiem SHA256)"
mkdir -p "$CACHE" "$RA" "$M"
THAT="$(curl -sIL -o /dev/null -w '%{url_effective}' "$URL")"
TEN="$(basename "$THAT")"
if [ ! -s "$CACHE/$TEN" ]; then
    curl -fL --retry 3 -o "$CACHE/$TEN.tmp" "$THAT"
    mv "$CACHE/$TEN.tmp" "$CACHE/$TEN"
fi
curl -fsSL "$THAT.sha256" -o "$CACHE/$TEN.sha256"
(cd "$CACHE" && sha256sum -c "$TEN.sha256") || { echo "DUNG: sai SHA256 $TEN"; exit 1; }
echo "$TEN" > "$RA/goc-raspios.txt"

say "Giai nen + noi rong phan vung he thong (+3 GB cho goi cua Console System)"
IMG="$RA/console-system-pi.img"
xz -dc "$CACHE/$TEN" > "$IMG"
truncate -s +3G "$IMG"
parted -s "$IMG" resizepart 2 100%
LOOP="$(losetup -fP --show "$IMG")"
e2fsck -fy "${LOOP}p2" >/dev/null || true
resize2fs "${LOOP}p2" >/dev/null
mount "${LOOP}p2" "$M"
mount "${LOOP}p1" "$M/boot/firmware"
for d in dev dev/pts proc sys; do mount --bind "/$d" "$M/$d"; done
cp "$M/etc/resolv.conf" "$RA/resolv.conf.goc" 2>/dev/null || true
cp -L /etc/resolv.conf "$M/etc/resolv.conf"
printf '#!/bin/sh\nexit 101\n' > "$M/usr/sbin/policy-rc.d"; chmod 755 "$M/usr/sbin/policy-rc.d"

say "Chep ma nguon Console System vao anh"
rsync -a --delete --exclude=.git --exclude=__pycache__ "$REPO/" "$M/opt/console-system-src/"

say "Cai Console Pi trong chroot (gia lap ARM - cham, 20-60 phut)"
chroot "$M" /usr/bin/env -i HOME=/root PATH=/usr/sbin:/usr/bin:/sbin:/bin TERM=dumb \
    DEBIAN_FRONTEND=noninteractive \
    bash /opt/console-system-src/install.sh --local /opt/console-system-src --with-screen

say "Dich vu thiet lap lan dau"
install -m 755 "$REPO/iso/pi/console-system-pi-lan-dau" "$M/usr/local/sbin/console-system-pi-lan-dau"
install -m 644 "$REPO/iso/pi/console-system-pi-lan-dau.service" "$M/etc/systemd/system/"
chroot "$M" systemctl enable console-system-pi-lan-dau.service

say "Xoa bi mat rieng tung may + don dep"
rm -f "$M/etc/hostapd/hostapd.conf" "$M/var/lib/console-pi/samba-deploy.key" \
      "$M/opt/console-pi/flask-secret.key" "$M/var/lib/console-pi/kho-trungtam.json" \
      "$M"/etc/ssh/ssh_host_*
chroot "$M" sh -c 'pdbedit -x consolepi-deploy >/dev/null 2>&1 || true'
: > "$M/etc/machine-id"
rm -f "$M/var/lib/dbus/machine-id"
chroot "$M" apt-get clean
rm -rf "$M/var/lib/apt/lists/"* "$M/tmp/"* "$M/root/.cache"
rm -f "$M/usr/sbin/policy-rc.d"
if [ -f "$RA/resolv.conf.goc" ]; then cp "$RA/resolv.conf.goc" "$M/etc/resolv.conf"; fi
echo "Console System $BAN - anh the nho Raspberry Pi ($(date +%d/%m/%Y))" > "$M/etc/console-system-anh-pi"
df -h "$M" | tail -1
don_dep; trap - EXIT

say "Nen anh (xz)"
RA_FILE="$RA/ConsoleSystem-$BAN-raspberrypi.img.xz"
xz -T0 -6 -c "$IMG" > "$RA_FILE.tmp" && mv "$RA_FILE.tmp" "$RA_FILE"
rm -f "$IMG"
sha256sum "$RA_FILE" | tee "$RA_FILE.sha256"
ls -la "$RA_FILE"
say "XONG"
