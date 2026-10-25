#!/bin/bash
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
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
kt "dich vu phuc hoi cap nhat luc khoi dong da bat (mat dien giua luc nang cap)" sh -c "systemctl is-enabled console-system-nang-cap-phuc-hoi"
kt "da chay xong thiet lap lan dau"       test -f /var/lib/console-system/data/.da-thiet-lap
kt "mat khau Samba rieng cho may nay"     test -s /var/lib/console-system/secrets/samba-deploy.key
kt "tai khoan Samba consolepi-deploy (dung ten share/deploy.cmd)" sh -c "pdbedit -L | grep -q '^consolepi-deploy:'"
kt "khoa SSH may da sinh"                 test -s /etc/ssh/ssh_host_ed25519_key
kt "nguon apt khong con tro vao USB"      khong grep -qs '^deb cdrom' /etc/apt/sources.list
kt "da go file tang toc build dpkg"       test ! -e /etc/apt/apt.conf.d/00-toc-do-build

echo "== Dich vu chinh"
for s in console-system-dashboard nginx ssh console-system-term-local console-system-term-ssh console-system-term-phien; do
    kt "$s dang chay" systemctl is-active --quiet $s
done
echo "== An toan mang: KHONG tu phat DHCP/WiFi/TFTP/Samba khi cam vao mang khach"
# Nguoi dung CHU DONG bat PXE (co /run/console-pi-pxe.flag) thi dnsmasq-pxe,
# smbd, cong 67 chay la DUNG - chi kiem khi PXE dang tat.
PXE_BAT=""; [ -f /run/console-pi-pxe.flag ] && PXE_BAT=1
for s in dnsmasq dnsmasq-pxe dnsmasq-direct hostapd tftpd-hpa smbd; do
    case "$PXE_BAT:$s" in
        1:dnsmasq-pxe|1:smbd) echo "BO QUA $s (nguoi dung dang bat PXE)"; continue;;
    esac
    kt "$s khong tu chay" khong systemctl is-active --quiet $s
done
if [ -n "$PXE_BAT" ]; then echo "BO QUA cong 67 (nguoi dung dang bat PXE)"
else kt "khong co gi nghe cong 67 (DHCP)"  khong sh -c "ss -ulpn | grep -q ':67 '"; fi

echo "== Kiosk (man hinh)"
kt "kiosk dang chay"                      systemctl is-active --quiet console-system-kiosk
kt "trinh duyet kiosk dang mo dashboard"  sh -c "curl -s http://127.0.0.1:9222/json | grep -q 8880"

echo "== Driver VirtIO nhung san trong ISO (khong can mang)"
kt "co 3 file .cab VirtIO trong /opt/console-pi/driver-san"  test "$(ls /opt/console-pi/driver-san/virtio_*.cab 2>/dev/null | wc -l)" = 3
kt "3 goi VirtIO da duoc nap san vao thu muc driver"          test -s /var/lib/console-system/deploy/drivers/goi-virtio_netkvm/_thongtin.json -a -s /var/lib/console-system/deploy/drivers/goi-virtio_viostor/_thongtin.json -a -s /var/lib/console-system/deploy/drivers/goi-virtio_vioscsi/_thongtin.json

# May co Internet -> tu tai not cac goi con thieu (toi da ~3 phut)
for _i in $(seq 36); do
    [ "$(ls /var/lib/console-system/deploy/drivers/goi-*/_thongtin.json 2>/dev/null | wc -l)" -ge 15 ] && break
    sleep 5
done
kt "du 15 goi driver pho bien (3 VirtIO nhung san + 12 tu tai khi co Internet)" \
   test "$(ls /var/lib/console-system/deploy/drivers/goi-*/_thongtin.json 2>/dev/null | wc -l)" -ge 15

echo "== Cong cu Deployment OS"
for c in parted wimlib-imagex mkfs.vfat mcopy genisoimage; do
    kt "co lenh $c" sh -c "PATH=\$PATH:/usr/sbin command -v $c"
done
# bookworm (ISO 32-bit) chi co 7zz, trixie co 7z - ui/isotach.py dung ca hai
kt "co lenh 7z hoac 7zz"                  sh -c "command -v 7z || command -v 7zz"
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
kt "1.7.5: trang File boot co khung Boot WinPE"  sh -c "curl -s -H 'X-ConsolePi-Local: 1' http://127.0.0.1:8880/deployos/console | grep -q 'Boot WinPE (menu PXE)'"
kt "1.7.5: o buoc kich ban bam duoc (data-den)"    sh -c "L=\$(curl -s -i -H 'X-ConsolePi-Local: 1' 'http://127.0.0.1:8880/deployos/wizard/bat-dau?che_do=luu' | sed -n 's/^[Ll]ocation: *//p' | tr -d '\r'); curl -s -H 'X-ConsolePi-Local: 1' \"http://127.0.0.1:8880\${L#http://127.0.0.1:8880}\" | grep -c 'data-den=' | grep -q '^[1-9]'"
kt "dashboard tra loi qua cong 80"        sh -c "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/ | grep -qE '200|302'"
kt "khong co traceback trong log web"     khong sh -c "journalctl -u console-system-dashboard -b | grep -q Traceback"

echo "== Quan ly may tram + Agent (1.9.5)"
kt "co wixl (tao file MSI agent)"          sh -c "command -v wixl"
kt "venv WinRM nap duoc pypsrp"            /opt/console-pi-venv/winrm/bin/python3 -c "from pypsrp.client import Client"
kt "co cong cu cai them (tools/cai-*.sh)"  sh -c "test -x /opt/console-pi/tools/cai-agent-tls.sh && test -x /opt/console-pi/tools/cai-winrm.sh && test -x /opt/console-pi/tools/cai-vnc.sh"
kt "co file agent dung san (cs-agent.exe, mau MSI)" sh -c "test -s /opt/console-pi/ui/agent_bin/cs-agent.exe && test -s /opt/console-pi/ui/agent_bin/ConsoleSystemAgent.wxs.tpl"
kt "PKI rieng da tao (CA + chung chi may chu)" sh -c "test -s /var/lib/console-system/pki/ca.pem && test -s /var/lib/console-system/pki/server.pem"
kt "cong mTLS agent 8443 dang nghe"        sh -c "ss -ltn | grep -q ':8443 '"
kt "cong 8443 khong co chung chi khach -> 403/404 (khong mo)" sh -c "c=\$(curl -sk -o /dev/null -w '%{http_code}' --max-time 10 https://127.0.0.1:8443/uem/agent/ping); [ \"\$c\" = 403 ] || [ \"\$c\" = 404 ]"
kt "khong co CA/khoa nao trong ISO goc (tao luc khoi dong dau)" sh -c "test \$(stat -c %Y /var/lib/console-system/pki/ca.pem) -gt \$(stat -c %Y /opt/console-pi/VERSION)"
for p in /uem /uem/may /uem/phan-mem /uem/bao-mat /uem/trien-khai /uem/profiles /uem/bao-cao /uem/quan-tri /uem/quan-tri/agent /uem/chua-ho-tro /deployos/trienkhai; do
    kt "trang $p mo duoc" sh -c "c=\$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 -H 'X-ConsolePi-Local: 1' http://127.0.0.1:8880$p); [ \"\$c\" = 200 ] || [ \"\$c\" = 302 ]"
done
kt "tao duoc file script agent (khong can wixl)" sh -c "cd /opt/console-pi && PYTHONPATH=/opt/console-pi python3 -c \"
import time
from ui import uem_agent_goi as UG
v=UG.bat_dau('ps1','kiem-tra','127.0.0.1:8443',0,0,'')
for _ in range(100):
    r=UG.viec(v)
    if r['tt']!='dang': break
    time.sleep(0.2)
import sys; sys.exit(0 if r['tt']=='xong' else 1)
\""
kt "tao duoc file MSI agent (wixl)"        sh -c "cd /opt/console-pi && PYTHONPATH=/opt/console-pi python3 -c \"
import time
from ui import uem_agent_goi as UG
v=UG.bat_dau('msi','kiem-tra-msi','127.0.0.1:8443',0,0,'')
for _ in range(100):
    r=UG.viec(v)
    if r['tt']!='dang': break
    time.sleep(0.2)
import sys; sys.exit(0 if r['tt']=='xong' else 1)
\""

echo
echo "TONG: $dat dat, $loi loi"
[ "$loi" = 0 ]
