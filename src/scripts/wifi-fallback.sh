#!/bin/bash
# Console Pi - WiFi fallback (AP <-> Client)
# Ban va: them 2 chot chan de KHONG pha ket noi dang chay tot.

WLAN_IFACE="wlan0"
WPA_CONF="/etc/wpa_supplicant/wpa_supplicant-wlan0.conf"
LOGFILE="/var/log/console-pi-fallback.log"
AP_IP="192.168.50.1"

FORCE_AP_FLAG="/opt/console-pi/force-ap.flag"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOGFILE"; }

bat_ap() {
    pkill wpa_supplicant 2>/dev/null
    ip addr flush dev "$WLAN_IFACE"
    ip addr add "$AP_IP/24" dev "$WLAN_IFACE"
    ip link set "$WLAN_IFACE" up
    systemctl start hostapd
    systemctl start dnsmasq
    # Luoi an toan: systemd-networkd co the reconfigure va xoa mat IP AP
    # ngay sau khi carrier len (da tung xay ra). KeepConfiguration=yes da
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
    GW=$(ip route show dev "$WLAN_IFACE" 2>/dev/null | awk '/^default/{print $3; exit}')
    if [ -n "$GW" ] && ping -c 1 -W 2 -I "$WLAN_IFACE" "$GW" >/dev/null 2>&1; then
        # Ket noi lanh manh: co SSID, co IP, gateway ping duoc -> thoat im lang
        exit 0
    fi
    log "Client mode '$CUR_SSID' ($CUR_IP) nhung gateway khong phan hoi -> danh gia lai"
fi

# ================================================================
# CHOT 2: Dang o AP MODE va CO CLIENT dang ket noi -> KHONG DUNG TOI
# (bug cu: stop hostapd de scan -> da van laptop cua user ra ngoai
#  dung luc dang nhap password WiFi tren dashboard)
# ================================================================
if systemctl is-active --quiet hostapd; then
    N_STA=$(iw dev "$WLAN_IFACE" station dump 2>/dev/null | grep -c '^Station')
    if [ "$N_STA" -gt 0 ]; then
        log "AP mode dang co $N_STA client -> giu nguyen, khong scan"
        exit 0
    fi
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

SCAN_RESULT=$(iw dev "$WLAN_IFACE" scan 2>/dev/null | sed -n 's/^\s*SSID: //p')

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
    pkill -f "wpa_supplicant -B -i $WLAN_IFACE" 2>/dev/null
    sleep 1
    ip addr flush dev "$WLAN_IFACE"
    wpa_supplicant -B -i "$WLAN_IFACE" -c "$WPA_CONF"
    networkctl reconfigure "$WLAN_IFACE"
else
    log "Khong tim thay WiFi quen thuoc -> bat AP mode"
    bat_ap
fi
