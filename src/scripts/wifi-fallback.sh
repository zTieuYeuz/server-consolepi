#!/bin/bash
# Console Pi - WiFi fallback (AP <-> Client)
# Ban va: them 2 chot chan de KHONG pha ket noi dang chay tot.

WLAN_IFACE="wlan0"
WPA_CONF="/etc/wpa_supplicant/wpa_supplicant-wlan0.conf"
LOGFILE="/var/log/console-pi-fallback.log"
AP_IP="192.168.50.1"

FORCE_AP_FLAG="/opt/console-pi/force-ap.flag"
# Danh dau da mat ket noi 1 lan - can 2 lan lien tiep moi ket noi lai
LOST_FLAG="/run/console-pi-wifi-lost.flag"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOGFILE"; }

# Dung wpa_supplicant DUNG CACH.
#
# Truoc day script goi thang `wpa_supplicant -B`. Loi nghiem trong: unit nay la
# Type=oneshot, systemd giet toan bo cgroup khi service ket thuc - ke ca tien
# trinh vua duoc daemon hoa. Ket qua: moi lan fallback chuyen ve client mode,
# wpa_supplicant song vai giay roi bi giet, WiFi khong bao gio co IP lai.
# Nghich ly la loi nay chi lo ra dung luc CAN phuc hoi nhat.
# Dung unit wpa_supplicant@wlan0 thi tien trinh nam trong cgroup rieng, duoc
# systemd giam sat va tu khoi dong lai neu chet.
ngung_supplicant() {
    systemctl stop wpa_supplicant@"$WLAN_IFACE" 2>/dev/null
    pkill -f "wpa_supplicant -B -i $WLAN_IFACE" 2>/dev/null
    sleep 1
}

khoi_dong_supplicant() {
    systemctl restart wpa_supplicant@"$WLAN_IFACE"
}

bat_ap() {
    ngung_supplicant
    ip addr flush dev "$WLAN_IFACE"
    ip addr add "$AP_IP/24" dev "$WLAN_IFACE"
    ip link set "$WLAN_IFACE" up
    systemctl start hostapd
    systemctl start dnsmasq
    # Luoi an toan: systemd-networkd co the reconfigure va xoa mat IP AP
    # ngay sau khi carrier len (da tung xay ra). KeepConfiguration=static da
    # chan tu goc trong 12-wlan0.network, day chi la du phong.
    sleep 2
    ip -4 -o addr show "$WLAN_IFACE" | grep -q "$AP_IP" \
        || ip addr add "$AP_IP/24" dev "$WLAN_IFACE"
}

# ================================================================
# CHOT 0: User da KHOA che do AP tu dashboard -> LUON giu AP.
# Khong bao gio tu chuyen sang client du co thay WiFi quen.
# Neu AP bi chet vi ly do nao do thi tu bat lai o vong chay ke tiep.
# Go khoa: xoa file force-ap.flag (hoac bam nut tren dashboard).
# ================================================================
if [ -f "$FORCE_AP_FLAG" ]; then
    if ! systemctl is-active --quiet hostapd; then
        log "KHOA AP dang bat nhung hostapd chua chay -> bat lai AP"
        bat_ap
    fi
    exit 0
fi

# ================================================================
# CHOT 1: Dang o CLIENT MODE va chay tot -> KHONG DUNG TOI
# (day la bug cu: cu 2 phut lai flush IP + xin DHCP lai, lam mDNS
#  bi withdraw/re-register lien tuc, rot ca web lan console)
# ================================================================
CUR_SSID=$(iw dev "$WLAN_IFACE" link 2>/dev/null | sed -n 's/^\s*SSID: //p')
CUR_IP=$(ip -4 -o addr show "$WLAN_IFACE" 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | head -1)

if [ -n "$CUR_SSID" ] && [ -n "$CUR_IP" ] && [ "$CUR_IP" != "$AP_IP" ]; then
    # Dam bao tiet kiem dien luon TAT - day la nguyen nhan kinh dien gay rot
    # WiFi tren Pi: card ngu, router mat lien lac, nhung IP van con tren
    # interface nen nhin vao tuong mang van tot.
    iw dev "$WLAN_IFACE" set power_save off 2>/dev/null

    GW=$(ip route show dev "$WLAN_IFACE" 2>/dev/null | awk '/^default/{print $3; exit}')
    if [ -n "$GW" ]; then
        # Ping 3 lan (khong phai 1) truoc khi ket luan mat ket noi - tranh
        # bao dong gia khi router chi cham nhat thoi
        if ping -c 3 -W 2 -I "$WLAN_IFACE" "$GW" >/dev/null 2>&1; then
            rm -f "$LOST_FLAG"
            exit 0
        fi

        # Lan dau khong ping duoc: danh dau roi thoat, cho vong sau xac nhan.
        # Chi khi HAI vong lien tiep deu that bai moi ket noi lai - tranh viec
        # cu trac tro mang thoang qua la ngat ket noi cua nguoi dung.
        if [ ! -f "$LOST_FLAG" ]; then
            touch "$LOST_FLAG"
            log "Gateway $GW khong phan hoi (lan 1) - cho xac nhan vong sau"
            exit 0
        fi

        log "Gateway $GW khong phan hoi 2 vong lien tiep -> ket noi lai WiFi"
        rm -f "$LOST_FLAG"
        # Roi xuong duoi de quet va ket noi lai
    else
        log "Client mode '$CUR_SSID' ($CUR_IP) nhung khong co gateway -> danh gia lai"
    fi
fi

# ================================================================
# CHOT 2: Dang o AP MODE va CO CLIENT dang ket noi -> KHONG DUNG TOI
# (bug cu: stop hostapd de scan -> da van laptop cua user ra ngoai
#  dung luc dang nhap password WiFi tren dashboard)
# ================================================================
AP_HOLD="/run/console-pi-ap-hold.count"
if systemctl is-active --quiet hostapd; then
    N_STA=$(iw dev "$WLAN_IFACE" station dump 2>/dev/null | grep -c '^Station')
    if [ "$N_STA" -gt 0 ]; then
        HOLD=$(cat "$AP_HOLD" 2>/dev/null || echo 0)
        HOLD=$((HOLD + 1))
        echo "$HOLD" > "$AP_HOLD"

        # Giu AP khi co nguoi dang dung - NHUNG khong giu mai mai. Mot thiet bi
        # la (dien thoai hang xom, bo lap wifi) tu bam vao AP se ghim Pi o che
        # do AP vinh vien, va anh mat duong vao qua WiFi nha. Sau 5 vong (10
        # phut) thi van danh gia lai mot lan.
        if [ "$HOLD" -lt 5 ]; then
            log "AP mode dang co $N_STA client -> giu nguyen (vong $HOLD/5)"
            exit 0
        fi
        log "AP mode da giu $HOLD vong voi $N_STA client -> danh gia lai mot lan"
        echo 0 > "$AP_HOLD"
    else
        rm -f "$AP_HOLD"
    fi
else
    rm -f "$AP_HOLD"
fi

# Lay danh sach SSID da luu
KNOWN_SSIDS=$(sed -n 's/^\s*ssid="\(.*\)"\s*$/\1/p' "$WPA_CONF" 2>/dev/null)

# ================================================================
# CHOT 3: Chua luu WiFi nao + AP dang chay -> KHONG SCAN VO NGHIA
# (scan phai stop hostapd vai giay; neu khong co SSID nao de chuyen
#  sang thi viec do chi lam AP rot song dung luc user dang nham nối)
# ================================================================
if [ -z "$(printf '%s' "$KNOWN_SSIDS" | tr -d '[:space:]')" ] \
   && systemctl is-active --quiet hostapd; then
    exit 0
fi

# ================================================================
# Tu day tro xuong: that su can danh gia lai
# ================================================================

# Scan (phai tat hostapd tam thoi neu dang chay)
if systemctl is-active --quiet hostapd; then
    systemctl stop hostapd
    sleep 2
fi

# Quet toi 3 lan. Ly do: `iw scan` hay tra ve RONG khi wpa_supplicant vua
# khoi dong lai hoac card dang ban - va scan rong bi hieu nham thanh "khong co
# WiFi quen" -> Pi nhay sang AP, cat dut ket noi cua nguoi dung dang xai binh
# thuong. Da xay ra that luc 18:09.
SCAN_RESULT=""
for _try in 1 2 3; do
    SCAN_RESULT=$(iw dev "$WLAN_IFACE" scan 2>/dev/null | sed -n 's/^\s*SSID: //p')
    [ -n "$(printf '%s' "$SCAN_RESULT" | tr -d '[:space:]')" ] && break
    sleep 3
done

# Khong thay MOT SSID NAO ca (ke ca mang la) = viec quet that bai, khong phai
# "quanh day khong co WiFi quen". Truong hop nay tuyet doi khong duoc doi che
# do - cu giu nguyen hien trang va thu lai o vong sau.
if [ -z "$(printf '%s' "$SCAN_RESULT" | tr -d '[:space:]')" ]; then
    log "Quet WiFi that bai (khong thay SSID nao sau 3 lan) -> giu nguyen hien trang"
    if ! systemctl is-active --quiet hostapd \
       && ! systemctl is-active --quiet wpa_supplicant@"$WLAN_IFACE"; then
        log "Khong o che do nao ca -> bat lai supplicant"
        khoi_dong_supplicant
    fi
    exit 0
fi

# So khop CHINH XAC ca dong (bug cu dung grep -qF = khop chuoi con)
FOUND_KNOWN=""
while IFS= read -r ssid; do
    [ -z "$ssid" ] && continue
    if printf '%s\n' "$SCAN_RESULT" | grep -qxF "$ssid"; then
        FOUND_KNOWN="$ssid"
        break
    fi
done <<< "$KNOWN_SSIDS"

if [ -n "$FOUND_KNOWN" ]; then
    log "Tim thay WiFi quen thuoc: $FOUND_KNOWN -> chuyen sang client mode"
    systemctl stop hostapd
    systemctl stop dnsmasq
    ngung_supplicant
    ip addr flush dev "$WLAN_IFACE"
    khoi_dong_supplicant

    # PHAI cho ket noi xong ROI moi goi networkctl reconfigure.
    # Goi som (ngay sau khi bat supplicant) thi networkd chay khi card chua
    # associate, khong co gi de xin DHCP, va no KHONG tu thu lai khi carrier
    # len sau do - wlan0 associate thanh cong nhung vinh vien khong co IP.
    # Da do: goi lai reconfigure sau khi COMPLETED thi co IP trong 8 giay.
    for _ in $(seq 1 20); do
        sleep 1
        wpa_cli -i "$WLAN_IFACE" status 2>/dev/null | grep -q "wpa_state=COMPLETED" && break
    done
    networkctl reconfigure "$WLAN_IFACE"

    # Cho DHCP thuc su cap IP roi moi bao thanh cong - neu khong, lan chay sau
    # lai thay "co SSID nhung khong IP" va lam lai tu dau vo ich.
    for _ in $(seq 1 15); do
        sleep 2
        CHECK_IP=$(ip -4 -o addr show "$WLAN_IFACE" 2>/dev/null | awk '{print $4}' | head -1)
        [ -n "$CHECK_IP" ] && { log "Da co IP: $CHECK_IP"; break; }
    done
    if [ -z "$CHECK_IP" ]; then
        log "CANH BAO: da noi $FOUND_KNOWN nhung chua xin duoc IP sau 30s"
    fi
else
    log "Khong tim thay WiFi quen thuoc -> bat AP mode"
    bat_ap
fi

exit 0
