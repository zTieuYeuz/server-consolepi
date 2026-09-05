#!/bin/bash
# Console Pi - Tu kiem tra toan bo he thong.
#
# Muc dich: tra loi duoc cau hoi "sau khi khoi dong lai, moi thu con chay dung
# khong?" ma khong phai nho lai tung thu bang tay. Chay:
#     sudo /opt/console-pi/scripts/selftest.sh
#
# Ma thoat 0 = tat ca dat, 1 = co muc that bai.

RED=$'\033[0;31m'; GRN=$'\033[0;32m'; YEL=$'\033[0;33m'; BLU=$'\033[0;34m'; NC=$'\033[0m'
PASS=0; FAIL=0; WARN=0

muc()  { printf "\n${BLU}==> %s${NC}\n" "$1"; }
dat()  { printf "  ${GRN}✔${NC} %s\n" "$1"; PASS=$((PASS+1)); }
tach() { printf "  ${RED}✘${NC} %s\n" "$1"; FAIL=$((FAIL+1)); }
luu()  { printf "  ${YEL}!${NC} %s\n" "$1"; WARN=$((WARN+1)); }

kiem_dich_vu() {
    if systemctl is-active --quiet "$1"; then dat "$2 ($1)"
    else tach "$2 ($1) KHONG chay"; fi
}

kiem_trang() {
    # Dung cong 8880 (danh rieng cho man hinh kiosk tai cho, duoc mien dang
    # nhap) chu KHONG phai cong 80. Sau ban va lo hong Cloudflare, cong 80
    # LUON doi dang nhap (dung, xem muc Bao mat duong vao o tren) - dung no
    # o day se bao 302 va bi hieu nham la loi.
    local code
    code=$(curl -s -o /dev/null -m 8 -w "%{http_code}" "http://127.0.0.1:8880$1")
    if [ "$code" = "200" ]; then dat "Trang $1"
    else tach "Trang $1 tra ve $code"; fi
}

printf "\n${BLU}Console Pi - tu kiem tra${NC}  (%s, da chay %s)\n" \
    "$(date '+%Y-%m-%d %H:%M')" "$(uptime -p 2>/dev/null | sed 's/^up //')"

# ---------------------------------------------------------------- dich vu
muc "Dich vu"
kiem_dich_vu nginx                    "Web server"
kiem_dich_vu console-pi-dashboard     "Dashboard"
kiem_dich_vu console-pi-term-local    "Terminal cuc bo"
kiem_dich_vu console-pi-term-ssh      "Terminal SSH"
kiem_dich_vu bluetooth                "Bluetooth"
kiem_dich_vu avahi-daemon             "mDNS (.local)"
kiem_dich_vu lldpd                    "LLDP/CDP"
systemctl is-active --quiet wifi-fallback.timer \
    && dat "Bo dinh gio WiFi fallback" || tach "wifi-fallback.timer khong chay"

# ---------------------------------------------------------------- web
muc "Cac trang web"
for p in / /wifi /bluetooth /nettools /terminal /ssh /commands /docs /settings; do
    kiem_trang "$p"
done

# ---------------------------------------------------------------- bao mat
muc "Bao mat duong vao"

# Chot chan cho mot lo hong da tung co that: cloudflared chay ngay tren Pi va
# goi vao 127.0.0.1:80, nen khi dieu kien mien dang nhap con dua vao dia chi
# IP thi MOI NGUOI qua duong ham Cloudflare deu vao thang dashboard va
# terminal quyen root khong can mat khau. Phep thu nay mo phong dung cach do.
MA=$(curl -s -o /dev/null -m 8 -w "%{http_code}" \
     -H "X-Forwarded-For: 203.0.113.55" http://127.0.0.1/)
if [ "$MA" = "302" ] || [ "$MA" = "401" ]; then
    dat "Duong cong cong (cong 80) doi dang nhap - dung"
else
    tach "NGUY HIEM: cong 80 tra ve $MA thay vi 302. Nguoi tu Internet qua"
    tach "  Cloudflare co the vao thang dashboard va terminal root khong can mat khau!"
fi

# Cong kiosk phai chi lang nghe tren loopback, khong duoc ra mang
if ss -tlnH 2>/dev/null | grep -q "127.0.0.1:8880"; then
    dat "Cong kiosk 8880 chi lang nghe tren loopback"
elif ss -tlnH 2>/dev/null | grep -q ":8880"; then
    tach "NGUY HIEM: cong 8880 dang lang nghe ra mang - ai cung vao duoc khong can mat khau"
else
    luu "Chua thay cong kiosk 8880 (binh thuong neu may khong gan man hinh)"
fi

for f in /etc/wpa_supplicant/wpa_supplicant-wlan0.conf /etc/hostapd/hostapd.conf; do
    if [ -f "$f" ]; then
        Q=$(stat -c "%a" "$f" 2>/dev/null)
        [ "$Q" = "600" ] && dat "$(basename "$f") quyen 600" \
                         || tach "$(basename "$f") quyen $Q - chua mat khau ma ai cung doc duoc"
    fi
done

if grep -q '"api_enabled": *true' /opt/console-pi/config.json 2>/dev/null; then
    QUYEN=$(grep -o '"api_token_scope": *"[a-z]*"' /opt/console-pi/config.json 2>/dev/null | grep -o '[a-z]*"$' | tr -d '"')
    luu "API cho may/AI dang BAT (quyen: ${QUYEN:-?}). Thu hoi token khi xong viec."
else
    dat "API cho may/AI dang tat"
fi

# ---------------------------------------------------------------- console
muc "Cong console"
PORTS=$(ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null)
if [ -z "$PORTS" ]; then
    luu "Khong co cap console nao dang cam (khong phai loi neu chua cam)"
else
    for dev in $PORTS; do
        d=$(basename "$dev")
        if systemctl is-active --quiet "console-pi-ttyd@$d"; then
            # LOI THAT DA GAP (ngu yen tu truoc gio vi chua bao gio co cap
            # console that de kich hoat nhanh nay): dung cong 80 (duong cong
            # cong) thay vi 8880 (kiosk, duoc mien dang nhap) - giong dung
            # bai hoc da ghi o kiem_trang() phia tren nhung QUEN AP DUNG o
            # day, vi day la 1 khoi kiem tra rieng tu viet tay chu khong goi
            # qua ham kiem_trang(). Cong 80 LUON doi dang nhap (dung, xem
            # muc Bao mat) nen se bao 302 va bi hieu nham la loi that.
            code=$(curl -s -o /dev/null -m 8 -w "%{http_code}" "http://127.0.0.1:8880/term-console/$d/")
            [ "$code" = "200" ] && dat "$d mo duoc console" \
                                || tach "$d: ttyd chay nhung nginx tra ve $code"
        else
            tach "$d: dich vu console-pi-ttyd@$d khong chay"
        fi
    done
fi

# ---------------------------------------------------------------- kich ban 1
muc "Kich ban 1 - cam day LAN thang sang laptop"
if ip link show eth0 >/dev/null 2>&1; then
    ETH_IP=$(ip -4 -o addr show eth0 2>/dev/null | awk '{print $4}' | head -1)
    if [ -n "$ETH_IP" ]; then
        dat "eth0 co IP: $ETH_IP"
    else
        # Khong co IP la BINH THUONG neu chua cam day. Chi bao loi khi co
        # carrier (da cam day that) ma van khong lay duoc dia chi.
        if [ "$(cat /sys/class/net/eth0/carrier 2>/dev/null)" = "1" ]; then
            tach "eth0 da cam day nhung khong co IP sau khi cho"
        else
            luu "eth0 chua cam day - bo qua"
        fi
    fi
    # eth0 do NetworkManager (netplan) quan ly tren may nay, khong phai
    # systemd-networkd - phai hoi dung nguon thi moi ra ket qua that.
    LL=$(nmcli -t -f ipv4.link-local connection show netplan-eth0 2>/dev/null | cut -d: -f2)
    if [ -z "$LL" ]; then
        LL=$(grep -h "LinkLocalAddressing" /etc/systemd/network/*eth0*.network 2>/dev/null | head -1)
    fi
    # `nmcli -t` tra ve so, khong phai chu: 0=default 1=auto 2=disabled
    # 3=enabled 4=fallback. Can 3 hoac 4 thi cam thang sang laptop moi ra
    # 169.254.x.x khi khong ai cap DHCP.
    case "$LL" in
        3|4|*fallback*|*ipv4*|*yes*)
            dat "eth0 co link-local du phong (169.254.x.x khi khong co DHCP)" ;;
        "")   luu "Khong xac dinh duoc cau hinh link-local cua eth0" ;;
        *)    tach "eth0 link-local = '$LL' - cam thang sang laptop se khong ra IP" ;;
    esac
else
    tach "Khong thay giao dien eth0"
fi

# ------------------------------------------------- DNS du phong (mang la)
# LOI THAT DA GAP (fail o cong ty): may chu DNS do DHCP cap chi ton tai
# TRONG MANG DO. Mang Pi sang noi khac (hotspot 4G/5G tu dien thoai) thi DNS
# cu chet -> khong phan giai duoc ten mien -> cloudflared khong tim duoc
# argotunnel.com -> DUONG HAM TU XA CHET. Kiem tra o day de neu cau hinh du
# phong bi mat (vd cai lai he dieu hanh, doi cau hinh mang) thi biet ngay.
muc "DNS du phong (de chay duoc o mang la)"
if grep -qE "^nameserver (1\.1\.1\.1|8\.8\.8\.8)" /etc/resolv.conf 2>/dev/null; then
    dat "Co DNS cong cong du phong trong resolv.conf"
else
    tach "THIEU DNS du phong - o mang la (hotspot dien thoai) co the khong phan giai duoc ten mien, tunnel se chet"
fi
if timeout 6 python3 -c "import socket; socket.gethostbyname('region1.v2.argotunnel.com')" 2>/dev/null; then
    dat "Phan giai duoc ten mien cua Cloudflare Tunnel"
else
    tach "KHONG phan giai duoc region1.v2.argotunnel.com - duong ham tu xa se khong ket noi duoc"
fi

# ---------------------------------------------------------------- kich ban 2
muc "Kich ban 2 - tu phat AP khi khong co WiFi quen"
[ -x /opt/console-pi/scripts/wifi-fallback.sh ] \
    && dat "Script fallback ton tai va chay duoc" \
    || tach "Thieu /opt/console-pi/scripts/wifi-fallback.sh"

systemctl is-enabled --quiet wpa_supplicant@wlan0 \
    && dat "wpa_supplicant@wlan0 duoc bat luc khoi dong" \
    || tach "wpa_supplicant@wlan0 CHUA duoc bat - reboot xong se mat WiFi"

grep -q "KeepConfiguration=static" /etc/systemd/network/12-wlan0.network 2>/dev/null \
    && dat "12-wlan0.network dung KeepConfiguration=static" \
    || tach "12-wlan0.network sai KeepConfiguration - WiFi se khong xin lai duoc IP"

if [ -f /opt/console-pi/force-ap.flag ]; then
    luu "Dang KHOA che do AP - Pi se khong tu chuyen sang WiFi"
fi
systemctl is-active --quiet hostapd && dat "Dang phat AP ConsolePi" \
    || luu "Khong phat AP (dung neu dang ket noi WiFi)"

WIFI_IP=$(ip -4 -o addr show wlan0 2>/dev/null | awk '{print $4}' | head -1)
[ -n "$WIFI_IP" ] && dat "wlan0 co IP: $WIFI_IP" || tach "wlan0 khong co IP"

PS=$(iw dev wlan0 get power_save 2>/dev/null | awk '{print $3}')
[ "$PS" = "off" ] && dat "Tiet kiem dien WiFi da tat (chong rot mang)" \
                  || tach "Tiet kiem dien WiFi dang '$PS' - se rot mang sau mot luc"

# ---------------------------------------------------------------- kich ban 3
muc "Kich ban 3 - thiet bi Bluetooth da ghep tu noi lai"
grep -q "^ReconnectUUIDs" /etc/bluetooth/main.conf 2>/dev/null \
    && dat "ReconnectUUIDs da bat (HID + PAN tu noi lai)" \
    || tach "Thieu ReconnectUUIDs - thiet bi da ghep se khong tu noi lai"

N_PAIR=$(bluetoothctl devices Paired 2>/dev/null | grep -c '^Device')
if [ "$N_PAIR" -gt 0 ]; then
    dat "$N_PAIR thiet bi da ghep cap"
    N_TRUST=$(bluetoothctl devices Paired 2>/dev/null | awk '{print $2}' | while read -r m; do
        bluetoothctl info "$m" 2>/dev/null | grep -q "Trusted: yes" && echo x
    done | grep -c x)
    [ "$N_TRUST" -eq "$N_PAIR" ] && dat "Tat ca deu duoc tin cay (tu noi lai duoc)" \
        || luu "$((N_PAIR-N_TRUST)) thiet bi chua 'trusted' - se khong tu noi lai"

    # Bat trang thai ghep cap hong mot nua: Paired=yes nhung Bonded=no.
    # BlueZ se tu choi gan ho so HID ("Rejected connection from !bonded
    # device") nen ban phim/chuot bao la dang ket noi ma go khong an gi -
    # rat kho doan neu khong kiem tra dung truong Bonded. Da gap that.
    HONG=$(bluetoothctl devices Paired 2>/dev/null | awk '{print $2}' | while read -r m; do
        I=$(bluetoothctl info "$m" 2>/dev/null)
        echo "$I" | grep -q "Bonded: no" && echo "$m"
    done)
    if [ -n "$HONG" ]; then
        for m in $HONG; do
            tach "Thiet bi $m: Paired nhung Bonded=no - se KHONG dung duoc."
            tach "  Vao tab Bluetooth bam 'Ghep cap lai' de xoa ban ghi va ghep lai tu dau."
        done
    else
        dat "Khong co thiet bi nao bi ghep cap hong (Bonded=no)"
    fi
else
    luu "Chua ghep cap thiet bi Bluetooth nao"
fi

# ---------------------------------------------------------------- suc khoe
muc "Suc khoe phan cung"
TH=$(vcgencmd get_throttled 2>/dev/null | cut -d= -f2)
case "$TH" in
    0x0) dat "Nguon on dinh, chua tung sut ap" ;;
    "")  luu "Khong doc duoc trang thai nguon (khong phai Raspberry Pi?)" ;;
    *)   luu "get_throttled=$TH - da tung sut ap hoac qua nhiet, xem tab Tong quan" ;;
esac
TEMP=$(awk '{printf "%.1f", $1/1000}' /sys/class/thermal/thermal_zone0/temp 2>/dev/null)
if [ -n "$TEMP" ]; then
    awk -v t="$TEMP" 'BEGIN{exit !(t<80)}' && dat "Nhiet do CPU ${TEMP}°C" \
                                           || luu "Nhiet do CPU ${TEMP}°C - hoi cao"
fi
DISK=$(df --output=pcent / 2>/dev/null | tail -1 | tr -dc '0-9')
[ -n "$DISK" ] && { [ "$DISK" -lt 90 ] && dat "Dia da dung ${DISK}%" \
                                       || tach "Dia da dung ${DISK}% - sap day"; }

# ---------------------------------------------------------------- tong ket
printf "\n${BLU}Ket qua:${NC} ${GRN}%d dat${NC}"  "$PASS"
[ "$WARN" -gt 0 ] && printf ", ${YEL}%d luu y${NC}" "$WARN"
[ "$FAIL" -gt 0 ] && printf ", ${RED}%d that bai${NC}" "$FAIL"
printf "\n\n"

[ "$FAIL" -eq 0 ]
