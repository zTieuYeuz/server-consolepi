#!/usr/bin/env bash
# Console Pi Toolkit - Go cai dat
#   sudo /opt/console-pi/uninstall.sh            (giu lai cau hinh)
#   sudo /opt/console-pi/uninstall.sh --purge    (xoa sach ca cau hinh)
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "Can quyen root"; exit 1; }

PURGE="no"
[[ "${1:-}" == "--purge" ]] && PURGE="yes"

SERVICES=( console-pi-dashboard console-pi-kiosk console-pi-term-local
           console-pi-term-ssh bt-pan0 bt-agent bt-nap dnsmasq-bt
           wifi-fallback.timer wifi-fallback )

echo "==> Dung va go cac dich vu"
for s in "${SERVICES[@]}"; do
    systemctl disable --now "$s" 2>/dev/null || true
    rm -f "/etc/systemd/system/$s.service" "/etc/systemd/system/$s.timer"
done
for u in /etc/systemd/system/console-pi-ttyd@*.service \
         /etc/systemd/system/multi-user.target.wants/console-pi-ttyd@* \
         /etc/systemd/system/dev-ttyUSB*.device.wants/console-pi-ttyd@*; do
    [[ -e "$u" ]] && rm -f "$u"
done
rm -f /etc/systemd/system/console-pi-ttyd@.service
systemctl daemon-reload
systemctl start getty@tty1 2>/dev/null || true

if [[ "$PURGE" == "yes" ]]; then
    echo "==> Xoa sach /opt/console-pi (ca cau hinh)"
    rm -rf /opt/console-pi
    rm -f /etc/dnsmasq-bt.conf
    echo "    Giu lai: /etc/hostapd/hostapd.conf, WiFi da luu (xoa tay neu muon)"
else
    echo "==> Xoa ma nguon, GIU LAI cau hinh"
    rm -rf /opt/console-pi/{ui,nettools,scripts,app.py,VERSION}
    echo "    Con lai: config.json, command-library.json, port-names.json"
fi
systemctl unmask wpa_supplicant 2>/dev/null || true
echo "==> Xong. Cac goi apt van giu nguyen (go tay neu can)."
