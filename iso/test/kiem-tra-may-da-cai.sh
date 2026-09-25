#!/bin/bash
# ===================================================================
# CHI DE TEST: chay BEN TRONG may vua cai tu ISO (bang sudo) - kiem tra
# "hang dem ban": moi dong la 1 dieu nguoi mua mong doi, in DAT / LOI.
# ===================================================================
#   sudo bash kiem-tra-may-da-cai.sh
dat=0; loi=0
kt() {  # kt "mo ta" lenh...
    local mo_ta="$1"; shift
    if "$@" >/dev/null 2>&1; then echo "DAT  $mo_ta"; dat=$((dat+1))
    else echo "LOI  $mo_ta"; loi=$((loi+1)); fi
}
khong() { ! "$@"; }
HTTP() { curl -s -o /dev/null -w '%{http_code}' --max-time 20 -H 'X-ConsolePi-Local: 1' "http://127.0.0.1:8880$1"; }

echo "== He thong"
kt "ten he thong la Console System"      grep -q '^PRETTY_NAME="Console System' /etc/os-release
kt "os-release con VERSION_CODENAME"      grep -q '^VERSION_CODENAME=[a-z]' /etc/os-release
kt "khong co dich vu nao loi"             test -z "$(systemctl --failed --no-legend)"
kt "da chay xong thiet lap lan dau"       test -f /var/lib/console-pi/.da-thiet-lap
kt "mat khau Samba rieng cho may nay"     test -s /var/lib/console-pi/samba-deploy.key
kt "tai khoan Samba consolepi-deploy (dung ten share/deploy.cmd)" sh -c "pdbedit -L | grep -q '^consolepi-deploy:'"
kt "khoa SSH may da sinh"                 test -s /etc/ssh/ssh_host_ed25519_key
kt "nguon apt khong con tro vao USB"      khong grep -qs '^deb cdrom' /etc/apt/sources.list
kt "da go file tang toc build dpkg"       test ! -e /etc/apt/apt.conf.d/00-toc-do-build

echo "== Dich vu chinh"
for s in console-pi-dashboard nginx ssh console-pi-term-local console-pi-term-ssh; do
    kt "$s dang chay" systemctl is-active --quiet $s
done
echo "== An toan mang: KHONG tu phat DHCP/WiFi/TFTP/Samba khi cam vao mang khach"
for s in dnsmasq dnsmasq-pxe dnsmasq-direct hostapd tftpd-hpa smbd; do
    kt "$s khong tu chay" khong systemctl is-active --quiet $s
done
kt "khong co gi nghe cong 67 (DHCP)"      khong sh -c "ss -ulpn | grep -q ':67 '"

echo "== Kiosk (man hinh)"
kt "kiosk dang chay"                      systemctl is-active --quiet console-pi-kiosk
kt "trinh duyet kiosk dang mo dashboard"  sh -c "curl -s http://127.0.0.1:9222/json | grep -q 8880"

echo "== Cong cu Deployment OS"
for c in parted wimlib-imagex 7z mkfs.vfat mcopy genisoimage; do
    kt "co lenh $c" sh -c "PATH=\$PATH:/usr/sbin command -v $c"
done
kt "co ttyd (terminal web)"               /usr/local/bin/ttyd --version

echo "== Trang web (qua cong kiosk 8880)"
# Do MOI link that tren cac trang chinh (khong doan ten trang) - moi link
# phai mo duoc (200/302), khong 404/500.
links=$(for p in / /deployos/kichban /deployos/caidat /docs /settings /nettools; do
          curl -s --max-time 20 -H 'X-ConsolePi-Local: 1' "http://127.0.0.1:8880$p"; done |
        grep -oE 'href="/[^"#?]*"' | sed 's/href="//;s/"$//' | sort -u |
        grep -vE '^/(static|logout)|\.(css|js|png|ico|svg)$')
so=0; hong=""
for p in $links; do
    ma=$(HTTP "$p"); so=$((so+1))
    case "$ma" in 200|302) ;; *) hong="$hong $p($ma)";; esac
done
kt "mo duoc ca $so trang co link (hong:${hong:- khong})" test -z "$hong"
kt "trang chu co nut Home/menu"           sh -c "curl -s -H 'X-ConsolePi-Local: 1' http://127.0.0.1:8880/deployos/caidat | grep -q 'href=\"/\"'"
kt "dashboard tra loi qua cong 80"        sh -c "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/ | grep -qE '200|302'"
kt "khong co traceback trong log web"     khong sh -c "journalctl -u console-pi-dashboard -b | grep -q Traceback"

echo
echo "TONG: $dat dat, $loi loi"
[ "$loi" = 0 ]
