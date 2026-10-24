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

tar czf "$BK" -C /opt console-pi/app.py console-pi/ui console-pi/nettools console-pi/branding console-pi/scripts console-pi/VERSION \
    $(cd /opt && ls -d console-pi/pxe-boot 2>/dev/null)
echo "Da sao luu ban cu: $BK"

# ui + nettools: chep de (khong xoa file rieng cua Pi nhu ifthen-rules.json)
cp -r "$SRC/src/ui/." "$DST/ui/"
cp -r "$SRC/src/nettools/." "$DST/nettools/"
# Logo + font Geist cua giao dien moi (18/10/2026)
mkdir -p "$DST/branding" && cp -r "$SRC/src/branding/." "$DST/branding/"
# File boot PXE ban ky kem san (tu 1.5.0)
rm -rf "$DST/pxe-boot" && cp -r "$SRC/src/pxe-boot" "$DST/pxe-boot"
for f in "$SRC"/src/scripts/*; do
    [ -f "$f" ] && install -m 755 "$f" "$DST/scripts/$(basename "$f")"
done
install -m 644 "$SRC/VERSION" "$DST/VERSION"
# app.py (19/10/2026): truoc day KHONG duoc chep nen sua trong app.py (vd bo loc nhat ky truy cap) khong len Pi
install -m 644 "$SRC/src/app.py" "$DST/app.py"
find "$DST" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
chown -R administrator:administrator "$DST/ui" "$DST/nettools" "$DST/branding"

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
mkdir -p /var/lib/console-pi/o-dia && chown consolepi-deploy:consolepi-deploy /var/lib/console-pi/o-dia 2>/dev/null || chown nobody:nogroup /var/lib/console-pi/o-dia
# 1.8.7: share [cs-lich-su] - WinPE bao ket qua cho trang Lich su cai dat
mkdir -p /var/lib/console-pi/lich-su-bao && chown consolepi-deploy:consolepi-deploy /var/lib/console-pi/lich-su-bao 2>/dev/null || chown nobody:nogroup /var/lib/console-pi/lich-su-bao
if [ -f "$SRC/config/smb.conf" ] && ! cmp -s "$SRC/config/smb.conf" /etc/samba/smb.conf; then
    cp -a /etc/samba/smb.conf "/etc/samba/smb.conf.truoc-$(date +%Y%m%d-%H%M)"
    install -m 644 "$SRC/config/smb.conf" /etc/samba/smb.conf
    if testparm -s >/dev/null 2>&1; then
        echo "Da cap nhat smb.conf"
        systemctl is-active --quiet smbd && smbcontrol smbd reload-config
    else
        echo "LOI smb.conf moi - tra ban cu"
        cp -a "$(ls -t /etc/samba/smb.conf.truoc-* | head -1)" /etc/samba/smb.conf
    fi
fi

# 1.9.5: cong cu .sh cua ui nam o /opt/console-pi/tools (ui nhac "sudo bash /opt/console-pi/tools/cai-winrm.sh")
mkdir -p "$DST/tools"
for f in "$SRC"/tools/cai-*.sh; do [ -f "$f" ] && install -m 755 "$f" "$DST/tools/$(basename "$f")"; done
# Dieu khien tu xa (VNC) cua Quan ly may tram can duong /uem-vnc-ws/ trong nginx (tu them neu thieu, loi thi tra ban cu)
[ -f "$DST/tools/cai-vnc.sh" ] && bash "$DST/tools/cai-vnc.sh" || echo "Canh bao: chua bat duoc nginx cho VNC (xem thong bao tren)"
# wixl de tao file MSI cai agent (Quan ly may tram, Agent); thieu mang/goi thi bo qua, script PowerShell van tao duoc
command -v wixl >/dev/null 2>&1 || apt-get install -y -qq wixl >/dev/null 2>&1 || echo "Canh bao: khong cai duoc wixl (khong tao duoc file MSI cai agent)"
# Cong mTLS 8443 cho agent (CA rieng + chung chi may chu + nginx), loi thi tra ban cu
[ -f "$DST/tools/cai-agent-tls.sh" ] && bash "$DST/tools/cai-agent-tls.sh" || echo "Canh bao: chua bat duoc cong mTLS 8443 cho agent (xem thong bao tren)"

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
