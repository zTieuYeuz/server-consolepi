#!/bin/sh
# Console System - ghi nguon goi Debian cho may cai bang TRINH CAI CHU (d-i).
# Chay TRONG he thong vua cai (in-target) o cuoi qua trinh cai, qua
# preseed/late_command.
#
# LOI THAT (23/09/2026, cai tu ISO roi bam "Cai Tailscale"): may cai bang
# trinh cai chu co /etc/apt/sources.list TRONG TRON - chi co dong cdrom da
# bi comment. `apt install` BAT KY goi nao cung bao "not installable" (vd
# tailscale can iptables -> "Unable to satisfy dependencies"). Nguyen nhan:
# trinh cai chi hoi "dung may chu mang?" o muc uu tien cao; khong duoc hoi
# thi no bo trong. May cai bang trinh cai do hoa KHONG bi (nguon lay tu anh
# dia live, da co san deb.debian.org).
#
# VI SAO KHONG DIEN SAN mirror trong preseed: cai KHONG CO MANG (thiet ke
# cua san pham - cai tu chinh anh dia) thi trinh cai se dung o hop thoai
# "khong ket noi duoc mirror". Ghi file o day chay duoc ca khi offline; may
# co mang luc nao thi apt dung duoc luc do.
#
# CHI ghi khi chua co dong "deb" nao dang bat - khong de len nguon nguoi cai
# da chon (vd mirror noi bo cong ty).
set -e
. /etc/os-release
[ -n "$VERSION_CODENAME" ] || { echo "[console-system] thieu VERSION_CODENAME"; exit 1; }

# Chi xet NGUON CHINH cua he thong (sources.list va debian.sources) - nguon
# cua ben thu ba trong sources.list.d (tailscale.list...) chi chua goi cua ho,
# khong thay duoc kho Debian (tailscale can iptables tu kho Debian).
#
# BO QUA dong "deb cdrom:" - LOI THAT (23/09/2026, cai thu ban da sua lan 1):
# luc late_command chay, dong cdrom VAN DANG BAT (trinh cai chi comment no
# o buoc sau cung, sau late_command) -> script tuong "da co nguon" va bo
# qua, may cai xong van trong tron nhu cu.
if grep -s '^[[:space:]]*deb[[:space:]]' /etc/apt/sources.list | grep -qv 'cdrom:'; then
    echo "[console-system] da co nguon apt - giu nguyen"
    exit 0
fi
if grep -qs '^Types:.*deb' /etc/apt/sources.list.d/debian.sources; then
    echo "[console-system] da co nguon apt (debian.sources) - giu nguyen"
    exit 0
fi

C=main
C="$C contrib non-free non-free-firmware"
cat > /etc/apt/sources.list <<EOF
# Nguon goi Debian - do Console System ghi luc cai dat.
deb http://deb.debian.org/debian $VERSION_CODENAME $C
deb http://deb.debian.org/debian $VERSION_CODENAME-updates $C
deb http://security.debian.org/debian-security $VERSION_CODENAME-security $C
EOF
echo "[console-system] da ghi nguon apt cho $VERSION_CODENAME"
