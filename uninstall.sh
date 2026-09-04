#!/usr/bin/env bash
# Console Pi Toolkit - Go cai dat
#   sudo /opt/console-pi/uninstall.sh            (giu lai cau hinh)
#   sudo /opt/console-pi/uninstall.sh --purge    (xoa sach ca cau hinh)
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "Can quyen root"; exit 1; }

PURGE="no"
[[ "${1:-}" == "--purge" ]] && PURGE="yes"

# LOI THAT DA TIM RA (ra soat lai code, khong phai da gap that): danh sach
# nay truoc day THIEU console-pi-tftp, console-pi-tunnel, console-pi-selftest,
# dnsmasq-direct. Neu nguoi dung tung bat TFTP hoac Truy cap tu xa (Cloudflare
# Tunnel) qua giao dien web roi sau do go cai dat, cac dich vu do se BI BO
# LAI CHAY NGAM tren may - rieng console-pi-tunnel la nghiem trong nhat vi no
# tiep tuc PHOI PI RA INTERNET du nguoi dung tuong da go sach roi.
SERVICES=( console-pi-dashboard console-pi-kiosk console-pi-term-local
           console-pi-term-ssh console-pi-selftest console-pi-tftp
           console-pi-tunnel bt-pan0 bt-agent bt-nap dnsmasq-bt
           dnsmasq-direct wifi-fallback.timer wifi-fallback )

echo "==> Dung va go cac dich vu"
for s in "${SERVICES[@]}"; do
    systemctl disable --now "$s" 2>/dev/null || true
    rm -f "/etc/systemd/system/$s.service" "/etc/systemd/system/$s.timer"
done

# Nginx: chi go RIENG site config cua Console Pi (khong tat han nginx - co
# the may co dung cho viec khac). Khong lam viec nay thi nginx van chay va
# proxy toi mot backend Flask GIO DA BI XOA, hien loi 502 kho hieu thay vi
# don gian la khong con Console Pi nua.
if [[ -f /etc/nginx/sites-enabled/console-pi.conf || -f /etc/nginx/sites-available/console-pi.conf ]]; then
    rm -f /etc/nginx/sites-enabled/console-pi.conf /etc/nginx/sites-available/console-pi.conf
    systemctl reload nginx 2>/dev/null || true
    echo "    Da go site nginx cua Console Pi (nginx van chay, khong con site nao duoc bat)"
fi
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
    rm -f /etc/dnsmasq-bt.conf /etc/dnsmasq-direct.conf

    # Token Cloudflare Tunnel: PHAI xoa khi purge - de lai la de lo mot token
    # con hieu luc co the dung lai duong ham cu tu xa, du dich vu da tat.
    rm -rf /etc/cloudflared

    # Cau hinh SSH client cho thiet bi mang cu (v0.4.8) - chi anh huong lenh
    # ssh tren chinh may nay, an toan de xoa khi purge.
    rm -f /etc/ssh/ssh_config.d/consolepi-legacy-devices.conf

    # Cau hinh xoay vong nhat ky + cac file nhat ky do Console Pi tao ra
    rm -f /etc/logrotate.d/console-pi
    rm -f /var/log/console-pi-*.log /var/log/console-pi-*.log.*

    # udev rules rieng cua Console Pi (dat ten cong serial, xoay man hinh
    # cham, doi ten WiFi). Chi xoa khi purge - ban cai lai thong thuong
    # (khong purge) van can giu de "cai lai nhieu lan khong mat gi".
    rm -f /etc/udev/rules.d/99-consolepi-*.rules
    udevadm control --reload-rules 2>/dev/null || true

    echo "    Giu lai: /etc/hostapd/hostapd.conf, WiFi da luu, cau hinh mang"
    echo "    (wlan0/dnsmasq/wpa_supplicant) - xoa tay neu muon ve trang thai goc"
else
    echo "==> Xoa ma nguon, GIU LAI cau hinh"
    rm -rf /opt/console-pi/{ui,nettools,scripts,app.py,VERSION}
    echo "    Con lai: config.json, command-library.json, port-names.json"
fi
systemctl unmask wpa_supplicant 2>/dev/null || true
echo "==> Xong. Cac goi apt van giu nguyen (go tay neu can)."
