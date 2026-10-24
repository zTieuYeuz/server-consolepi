#!/bin/bash
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# Bat "Dieu khien tu xa (VNC)" cua Quan ly may tram tren may DA CAI: them duong /uem-vnc-ws/ vao nginx (neu chua co).
# An toan: sao luu truoc, nginx -t, loi thi tra ban cu. Khong dung toi dich vu khac. Chay: sudo bash cai-vnc.sh
set -e
[ "$(id -u)" = 0 ] || { echo "Chay bang sudo."; exit 1; }
CONF=/etc/nginx/sites-available/console-pi.conf
[ -f "$CONF" ] || { echo "Khong thay $CONF (nginx chua duoc cai boi Console System)."; exit 1; }
if grep -q "location /uem-vnc-ws/" "$CONF"; then echo "nginx da co duong /uem-vnc-ws/."; exit 0; fi
grep -q "# ---- Phien ket noi kieu MobaXterm" "$CONF" || { echo "Cau hinh nginx khac thuong, khong tu them duoc."; exit 1; }
BK="$CONF.truoc-vnc-$(date +%Y%m%d-%H%M)"
cp -a "$CONF" "$BK"
python3 - "$CONF" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
blk = '''    # ---- Dieu khien tu xa VNC (noVNC) - Quan ly may tram ----
    location /uem-vnc-ws/ {
        auth_request /_auth;
        proxy_pass       http://127.0.0.1:8895;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_read_timeout 7200;
        proxy_send_timeout 7200;
        proxy_buffering off;
    }

'''
m = "    # ---- Phien ket noi kieu MobaXterm"
open(p, "w", encoding="utf-8").write(s.replace(m, blk + m, 1))
PYEOF
if nginx -t >/dev/null 2>&1; then
    systemctl reload nginx
    echo "Da them /uem-vnc-ws/ vao nginx va nap lai."
else
    cp -a "$BK" "$CONF"
    echo "LOI cau hinh nginx moi - da tra ban cu."
    exit 1
fi
