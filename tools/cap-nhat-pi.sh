#!/bin/bash
# Cap nhat Console Pi dang chay len ban moi nhat trong repo
# Chi thay ui/, nettools/, scripts/, VERSION - giong dung buoc copy cua install.sh.
# KHONG dung toi mang, dich vu systemd, cau hinh. Chay: sudo bash ~/cap-nhat-pi.sh
set -e
[ "$(id -u)" = 0 ] || { echo "Can chay bang sudo"; exit 1; }
SRC=/home/administrator/consolepi-toolkit
DST=/opt/console-pi
BK=/home/administrator/console-pi-truoc-moi-$(date +%Y%m%d-%H%M).tgz

tar czf "$BK" -C /opt console-pi/ui console-pi/nettools console-pi/scripts console-pi/VERSION
echo "Da sao luu ban cu: $BK"

# ui + nettools: chep de (khong xoa file rieng cua Pi nhu ifthen-rules.json)
cp -r "$SRC/src/ui/." "$DST/ui/"
cp -r "$SRC/src/nettools/." "$DST/nettools/"
for f in "$SRC"/src/scripts/*; do
    [ -f "$f" ] && install -m 755 "$f" "$DST/scripts/$(basename "$f")"
done
install -m 644 "$SRC/VERSION" "$DST/VERSION"
find "$DST" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
chown -R administrator:administrator "$DST/ui" "$DST/nettools"

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
