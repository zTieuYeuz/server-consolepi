#!/bin/bash
# ===================================================================
# Console System - dung lai CAY BUILD (live-build) tu repo
# ===================================================================
# VI SAO CO SCRIPT NAY (25/09/2026): may build cu (192.168.110.19) bi xoa
# mat. Cay /build/console-system* tren do tung duoc dung dan bang tay qua
# hang tram lenh scp - khong co cach nao dung lai ngoai viec do lai nhat ky.
# Tu nay REPO la nguon duy nhat: chay script nay tren may build (Debian 13
# x86_64) la co lai dung 2 cay nhu cu, roi chay dung-iso.sh trong tung cay.
#
#   sudo ./iso/dung-cay-build.sh            # dung ca 2 cay (amd64 + i386)
#   sudo ./iso/dung-cay-build.sh amd64      # chi ban 64-bit
#   sudo ./iso/dung-cay-build.sh i386       # chi ban 32-bit
#
# Chay lai bao nhieu lan cung duoc: moi lan XOA config/ cu va dung lai tu
# repo (giu cache/ de lan build sau khong phai tai lai goi).
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
I="$REPO/iso"
CHON="${1:-ca-hai}"

[ "$(id -u)" = 0 ] || { echo "Can chay bang root/sudo"; exit 1; }
[ -f "$REPO/src/app.py" ] || { echo "Khong thay repo o $REPO"; exit 1; }

dung_cay() {   # $1 = amd64 | i386
    local ARCH="$1" T C
    if [ "$ARCH" = amd64 ]; then T=/build/console-system; else T=/build/console-system-i386; fi
    C="$T/config"
    echo "=== dung $T ==="
    mkdir -p "$T"
    rm -rf "$C"
    mkdir -p "$C"/{hooks/live,package-lists,includes.installer,bootloaders/isolinux,bootloaders/syslinux_common}
    local R="$C/includes.chroot"

    # --- 1. Ma nguon ung dung -> /opt/console-pi (giong install.sh tren Pi)
    mkdir -p "$R/opt/console-pi"
    rsync -a --exclude='__pycache__' --exclude='*.pyc' "$REPO/src/" "$R/opt/console-pi/"
    install -m 644 "$REPO/VERSION" "$R/opt/console-pi/VERSION"
    chmod 755 "$R/opt/console-pi/scripts/"*.sh "$R/opt/console-pi/scripts/"*.py 2>/dev/null || true

    # --- 2. Don vi systemd + cau hinh: hook 0100 cai tu day vao he thong
    local S="$R/usr/local/share/console-system"
    mkdir -p "$S/systemd" "$S/config"
    cp "$REPO"/systemd/* "$S/systemd/"
    cp "$REPO"/config/* "$S/config/"

    # --- 3. File rieng cua ban ISO (xem bang trong iso/README.md)
    mkdir -p "$R/etc/update-motd.d" "$R/usr/local/sbin" "$R/etc/systemd/system" \
             "$R/etc/ssh/sshd_config.d" "$R/etc/chromium/policies/managed" \
             "$R/etc/apt/apt.conf.d"
    echo "console-system" > "$R/etc/hostname"
    printf "127.0.0.1\tlocalhost\n127.0.1.1\tconsole-system\n" > "$R/etc/hosts"
    install -m 755 "$I/includes/update-motd.d/10-console-system" "$R/etc/update-motd.d/"
    install -m 755 "$I/includes/console-system-lan-dau"  "$R/usr/local/sbin/"
    install -m 755 "$I/includes/console-system-kiosk-ve" "$R/usr/local/sbin/"
    install -m 644 "$I/includes/console-system-lan-dau.service" "$R/etc/systemd/system/"
    install -m 644 "$I/includes/10-console-system.conf" "$R/etc/ssh/sshd_config.d/"
    install -m 644 "$I/includes/chromium-policies/console-system.json" "$R/etc/chromium/policies/managed/"
    install -m 644 "$I/includes/apt.conf.d/00-toc-do-build" "$R/etc/apt/apt.conf.d/"

    # --- 4. Bo cai chu (d-i): preseed + script nguon apt vao goc initrd
    install -m 644 "$I/preseed.cfg" "$C/includes.installer/preseed.cfg"
    install -m 755 "$I/includes-installer/console-system-nguon-apt.sh" "$C/includes.installer/"

    # --- 5. Menu boot BIOS (isolinux) - live-build CHEP DE len mac dinh
    install -m 644 "$I/bootloader/isolinux.cfg" "$I/bootloader/splash.svg" "$C/bootloaders/isolinux/"
    install -m 644 "$I/bootloader/menu.cfg" "$I/bootloader/live.cfg.in" \
                   "$I/bootloader/install_text.cfg" "$C/bootloaders/syslinux_common/"

    # --- 6. Hook thu gon (dung chung)
    install -m 755 "$I/hooks/0200-thu-gon.hook.chroot" "$C/hooks/live/"

    if [ "$ARCH" = amd64 ]; then
        install -m 755 "$I/hooks/0100-console-system.hook.chroot" "$C/hooks/live/"
        install -m 644 "$I/danh-sach-goi.txt" "$C/package-lists/console-pi.list.chroot"
        install -m 755 "$I/dung-iso.sh" "$T/dung-iso.sh"
        # Menu boot UEFI (GRUB). CO Y khong chep splash.svg sang grub-pc:
        # theme do hoa cua GRUB ve o den che menu (xem dung-iso.sh).
        mkdir -p "$C/bootloaders/grub-pc"
        install -m 644 "$I"/bootloader-grub/*.cfg "$C/bootloaders/grub-pc/"
        # Trinh cai do hoa Calamares (chi ban 64-bit)
        mkdir -p "$R/etc/calamares" "$R/usr/share/calamares/lang" \
                 "$R/etc/systemd/system/console-pi-kiosk.service.d" \
                 "$R/etc/systemd/system/console-pi-kiosk-helper.service.d"
        cp -r "$I/calamares/settings.conf" "$I/calamares/modules" "$I/calamares/branding" "$R/etc/calamares/"
        install -m 644 "$I/calamares/lang/calamares_vi.qm" "$R/usr/share/calamares/lang/"
        install -m 755 "$I/calamares/he-thong/console-system-grub-install" "$R/usr/local/sbin/"
        install -m 644 "$I/calamares/he-thong/console-system-cai.service" "$R/etc/systemd/system/"
        install -m 644 "$I/calamares/he-thong/05-khi-cai-dat.conf" "$R/etc/systemd/system/console-pi-kiosk.service.d/"
        install -m 644 "$I/calamares/he-thong/05-khi-cai-dat.conf" "$R/etc/systemd/system/console-pi-kiosk-helper.service.d/"
    else
        install -m 755 "$I/i386/hook-console-system.chroot" "$C/hooks/live/0100-console-system.hook.chroot"
        install -m 644 "$I/i386/danh-sach-goi.txt" "$C/package-lists/console-pi.list.chroot"
        install -m 755 "$I/i386/dung-iso.sh" "$T/dung-iso.sh"
        install -m 644 "$I/i386/os-release" "$R/etc/os-release"
    fi

    # Chan som loi da gap: dau phan tram trong danh sach goi (xem dung-iso.sh)
    if grep -q "%" "$C/package-lists/console-pi.list.chroot"; then
        echo "DUNG LAI: dau phan tram trong danh sach goi $ARCH"; exit 1
    fi
    echo "  $(find "$C" -type f | wc -l) file cau hinh, $(find "$R/opt/console-pi" -name '*.py' | wc -l) file python"
}

case "$CHON" in
    amd64|i386) dung_cay "$CHON" ;;
    ca-hai) dung_cay amd64; dung_cay i386 ;;
    *) echo "dung: $0 [amd64|i386|ca-hai]"; exit 2 ;;
esac
echo "XONG. Build: /build/console-system/dung-iso.sh ; /build/console-system-i386/dung-iso.sh"
