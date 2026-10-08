#!/bin/bash
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# Cap nhat Console Pi dang chay len ban moi nhat trong repo
# Chi thay ui/, nettools/, pxe-boot/, scripts/, VERSION - giong dung buoc copy cua install.sh.
# KHONG dung toi mang, dich vu systemd, cau hinh. Chay: sudo bash ~/cap-nhat-pi.sh
set -e
[ "$(id -u)" = 0 ] || { echo "Can chay bang sudo"; exit 1; }
SRC=/home/administrator/consolepi-toolkit
DST=/opt/console-pi
BK=/home/administrator/console-pi-truoc-moi-$(date +%Y%m%d-%H%M).tgz

tar czf "$BK" -C /opt console-pi/ui console-pi/nettools console-pi/scripts console-pi/VERSION \
    $(cd /opt && ls -d console-pi/pxe-boot 2>/dev/null)
echo "Da sao luu ban cu: $BK"

# ui + nettools: chep de (khong xoa file rieng cua Pi nhu ifthen-rules.json)
cp -r "$SRC/src/ui/." "$DST/ui/"
cp -r "$SRC/src/nettools/." "$DST/nettools/"
# File boot PXE ban ky kem san (tu 1.5.0)
rm -rf "$DST/pxe-boot" && cp -r "$SRC/src/pxe-boot" "$DST/pxe-boot"
for f in "$SRC"/src/scripts/*; do
    [ -f "$f" ] && install -m 755 "$f" "$DST/scripts/$(basename "$f")"
done
install -m 644 "$SRC/VERSION" "$DST/VERSION"
find "$DST" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
chown -R administrator:administrator "$DST/ui" "$DST/nettools"

# 1.7.7: da go tinh nang "Cho AI / may khac truy cap" (token + /ai + /api). cp -r khong xoa
# file da bi go khoi repo nen don tay: file code, khoa token trong config, nhat ky cu.
rm -f "$DST/ui/api.py"
if [ -f "$DST/config.json" ]; then
    python3 - "$DST/config.json" <<'PYEOF'
import json, os, sys
p = sys.argv[1]
c = json.load(open(p))
da = [k for k in list(c) if k.startswith("api_")]
for k in da:
    c.pop(k)
if da:
    json.dump(c, open(p + ".tmp", "w"), indent=2, ensure_ascii=False)
    os.chmod(p + ".tmp", 0o600)
    os.replace(p + ".tmp", p)
    print("Da xoa khoa token API cu khoi config:", ", ".join(da))
PYEOF
fi
rm -f /var/log/console-pi-api.log

# 1.8.0: share Samba [cs-o-dia] nhan bao cao "Do o dia". Chi cai smb.conf khi KHAC ban dang
# chay, kiem testparm truoc - loi thi tra ban cu (khong de Samba hong). smbd chi chay khi PXE bat.
mkdir -p /var/lib/console-pi/o-dia && chown nobody:nogroup /var/lib/console-pi/o-dia
if [ -f "$SRC/config/smb.conf" ] && ! cmp -s "$SRC/config/smb.conf" /etc/samba/smb.conf; then
    cp -a /etc/samba/smb.conf "/etc/samba/smb.conf.truoc-$(date +%Y%m%d-%H%M)"
    install -m 644 "$SRC/config/smb.conf" /etc/samba/smb.conf
    if testparm -s >/dev/null 2>&1; then
        echo "Da cap nhat smb.conf (them share cs-o-dia)"
        systemctl is-active --quiet smbd && smbcontrol smbd reload-config
    else
        echo "LOI smb.conf moi - tra ban cu"
        cp -a "$(ls -t /etc/samba/smb.conf.truoc-* | head -1)" /etc/samba/smb.conf
    fi
fi

# Kiem tra cu phap truoc khi khoi dong lai - loi thi tra ban cu, khong de web chet
if ! python3 -m py_compile "$DST"/ui/*.py "$DST"/nettools/*.py "$DST"/app.py; then
    echo "LOI cu phap - tra lai ban cu"
    tar xzf "$BK" -C /opt
    exit 1
fi
find "$DST" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true

systemctl restart console-pi-dashboard
sleep 6
systemctl is-active console-pi-dashboard
for p in / /deployos /deployos/kichban; do
    echo "$p -> $(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8880$p)"
done
echo "Phien ban: $(cat $DST/VERSION)"
echo "Neu co van de, tra lai ban cu: sudo tar xzf $BK -C /opt && sudo systemctl restart console-pi-dashboard"
