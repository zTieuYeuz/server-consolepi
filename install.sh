#!/usr/bin/env bash
#
# Console Pi Toolkit - Bo cai dat mot lenh
#
#   curl -fsSL https://raw.githubusercontent.com/USER/consolepi-toolkit/main/install.sh | sudo bash
#
# Tuy chon:
#   --no-screen    Khong cai giao dien kiosk (thiet bi khong gan man hinh)
#   --with-screen  Ep cai kiosk du khong phat hien duoc man hinh
#   --branch NAME  Cai tu nhanh khac (mac dinh: main)
#   --local DIR    Cai tu thu muc co san thay vi tai ve
#
# Chay lai duoc nhieu lan (idempotent). Cac file cau hinh cua ban KHONG bi ghi de.
#
set -euo pipefail

REPO_USER="${CONSOLEPI_REPO_USER:-USER}"
REPO_NAME="consolepi-toolkit"
BRANCH="main"
INSTALL_DIR="/opt/console-pi"
WANT_SCREEN="auto"
LOCAL_SRC=""

# ---------------------------------------------------------------- mau sac
R='\033[0;31m'; G='\033[0;32m'; Y='\033[1;33m'; B='\033[0;34m'; N='\033[0m'
say()  { echo -e "${B}==>${N} $*"; }
ok()   { echo -e "  ${G}✔${N} $*"; }
warn() { echo -e "  ${Y}!${N} $*"; }
die()  { echo -e "${R}✘ $*${N}" >&2; exit 1; }

# ------------------------------------------------------------ tham so
while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-screen)   WANT_SCREEN="no"; shift ;;
        --with-screen) WANT_SCREEN="yes"; shift ;;
        --branch)      BRANCH="$2"; shift 2 ;;
        --local)       LOCAL_SRC="$2"; shift 2 ;;
        -h|--help)     sed -n '2,20p' "$0"; exit 0 ;;
        *)             die "Tham so khong hieu: $1" ;;
    esac
done

[[ $EUID -eq 0 ]] || die "Can chay bang quyen root:  sudo bash install.sh"

echo
echo "╔══════════════════════════════════════════════╗"
echo "║   CONSOLE PI TOOLKIT - CAI DAT               ║"
echo "╚══════════════════════════════════════════════╝"
echo

# ------------------------------------------------- 1. Kiem tra he thong
say "Kiem tra he thong"

MODEL="$(tr -d '\0' < /proc/device-tree/model 2>/dev/null || echo 'khong ro')"
ok "Thiet bi: $MODEL"

if ! command -v apt-get >/dev/null; then
    die "Script nay chi chay tren Debian/Raspberry Pi OS (khong tim thay apt-get)."
fi
. /etc/os-release 2>/dev/null || true
ok "He dieu hanh: ${PRETTY_NAME:-khong ro}"

# Tai khoan se so huu file (thuong la user dau tien, uid 1000)
MAIN_USER="$(getent passwd 1000 | cut -d: -f1 || true)"
[[ -n "$MAIN_USER" ]] || MAIN_USER="root"
ok "Tai khoan chinh: $MAIN_USER"

# Phat hien man hinh HDMI
SCREEN_FOUND="no"
for s in /sys/class/drm/card*-HDMI*/status; do
    [[ -f "$s" ]] && [[ "$(cat "$s" 2>/dev/null)" == "connected" ]] && SCREEN_FOUND="yes"
done
if [[ "$WANT_SCREEN" == "auto" ]]; then
    WANT_SCREEN="$SCREEN_FOUND"
    ok "Man hinh HDMI: $([[ $SCREEN_FOUND == yes ]] && echo 'co - se cai giao dien kiosk' || echo 'khong co - bo qua kiosk')"
else
    ok "Man hinh: ep thanh '$WANT_SCREEN' theo tham so"
fi

# ------------------------------------------------- 2. Cai goi phu thuoc
say "Cai cac goi phu thuoc"

PKGS_CORE=(
    python3 python3-flask python3-pam python3-scapy python3-netmiko
    python3-cryptography
    tmux git curl nginx
    hostapd dnsmasq wpasupplicant iw wireless-tools
    bluez avahi-daemon
    lldpd arp-scan tcpdump tshark traceroute nmap eapoltest
    ethtool usbutils lsof
    tftpd-hpa
    grc
)
# fonts-noto-color-emoji: KHONG the thieu. Pi OS Lite khong co font emoji,
# thieu no thi moi icon tren giao dien hien thanh o vuong rong.
PKGS_SCREEN=( cage chromium wlr-randr fonts-noto-color-emoji )

export DEBIAN_FRONTEND=noninteractive

MISSING=()
for p in "${PKGS_CORE[@]}"; do
    dpkg -s "$p" >/dev/null 2>&1 || MISSING+=("$p")
done
if [[ "$WANT_SCREEN" == "yes" ]]; then
    for p in "${PKGS_SCREEN[@]}"; do
        dpkg -s "$p" >/dev/null 2>&1 || MISSING+=("$p")
    done
fi

if [[ ${#MISSING[@]} -gt 0 ]]; then
    ok "Can cai ${#MISSING[@]} goi: ${MISSING[*]}"
    apt-get update -qq
    apt-get install -y -qq "${MISSING[@]}" || die "Cai goi that bai"
    ok "Da cai xong"
else
    ok "Tat ca goi da co san"
fi

# Goi tftpd-hpa TU BAT SAN dich vu cua no ngay khi cai (postinst script) -
# di nguoc nguyen tac "khong tu bat dich vu mang khong xac thuc luc boot"
# cua du an nay. Console Pi dung unit rieng (console-pi-tftp.service, bat/
# tat qua tab May chu TFTP), nen phai tat han dich vu mac dinh cua goi o day.
if systemctl is-enabled --quiet tftpd-hpa 2>/dev/null || systemctl is-active --quiet tftpd-hpa 2>/dev/null; then
    systemctl disable --now tftpd-hpa 2>/dev/null || true
    ok "Da tat dich vu tftpd-hpa mac dinh (Console Pi tu quan ly rieng, mac dinh TAT)"
fi

# ttyd khong co trong repo Debian -> tai ban binary
if ! command -v ttyd >/dev/null 2>&1; then
    say "Cai ttyd (khong co trong repo Debian)"
    ARCH="$(uname -m)"
    case "$ARCH" in
        aarch64) TTYD_ARCH="aarch64" ;;
        armv7l)  TTYD_ARCH="armhf" ;;
        x86_64)  TTYD_ARCH="x86_64" ;;
        *)       die "Khong ho tro kien truc $ARCH cho ttyd" ;;
    esac
    TTYD_URL="https://github.com/tsl0922/ttyd/releases/latest/download/ttyd.${TTYD_ARCH}"
    curl -fsSL "$TTYD_URL" -o /usr/local/bin/ttyd || die "Tai ttyd that bai"
    chmod 755 /usr/local/bin/ttyd
    ok "Da cai ttyd: $(/usr/local/bin/ttyd --version 2>&1 | head -1)"
else
    ok "ttyd da co: $(command -v ttyd)"
fi

# microcom de noi vao cong serial
if ! command -v microcom >/dev/null 2>&1; then
    apt-get install -y -qq microcom 2>/dev/null || warn "Khong cai duoc microcom (console serial se khong chay)"
fi

# ------------------------------------------------- 3. Lay ma nguon
say "Chuan bi ma nguon"

if [[ -n "$LOCAL_SRC" ]]; then
    SRC_DIR="$LOCAL_SRC"
    ok "Dung thu muc co san: $SRC_DIR"
else
    SRC_DIR="$(mktemp -d)"
    trap 'rm -rf "$SRC_DIR"' EXIT
    TARBALL="https://github.com/${REPO_USER}/${REPO_NAME}/archive/refs/heads/${BRANCH}.tar.gz"
    ok "Tai tu: $TARBALL"
    curl -fsSL "$TARBALL" | tar xz -C "$SRC_DIR" --strip-components=1 \
        || die "Tai ma nguon that bai. Kiem tra REPO_USER/BRANCH hoac dung --local"
fi

[[ -d "$SRC_DIR/src" ]] || die "Thu muc ma nguon khong hop le (thieu src/)"

# ------------------------------------------------- 4. Trien khai file
say "Trien khai vao $INSTALL_DIR"

mkdir -p "$INSTALL_DIR"/{scripts,captures}

# Cac file cau hinh cua NGUOI DUNG - khong bao gio ghi de
PRESERVE=( config.json command-library.json port-names.json
           flask-secret.key force-ap.flag nettools/ifthen-rules.json )

copy_tree() {   # copy_tree <nguon> <dich>
    local src="$1" dst="$2"
    rm -rf "$dst"
    cp -r "$src" "$dst"
}

copy_tree "$SRC_DIR/src/ui"       "$INSTALL_DIR/ui"
copy_tree "$SRC_DIR/src/nettools" "$INSTALL_DIR/nettools.new"

# Giu lai rule IF/THEN cu neu co
if [[ -f "$INSTALL_DIR/nettools/ifthen-rules.json" ]]; then
    cp "$INSTALL_DIR/nettools/ifthen-rules.json" "$INSTALL_DIR/nettools.new/" 2>/dev/null || true
fi
rm -rf "$INSTALL_DIR/nettools"
mv "$INSTALL_DIR/nettools.new" "$INSTALL_DIR/nettools"

install -m 644 "$SRC_DIR/src/app.py" "$INSTALL_DIR/app.py"
install -m 644 "$SRC_DIR/VERSION"    "$INSTALL_DIR/VERSION"
# Chi chep FILE. Neu gap thu muc (vd __pycache__ do Python sinh ra khi
# chay thu script), `install` bao loi va `set -e` lam dung ca ban cai -
# da tung xay ra that.
for f in "$SRC_DIR"/src/scripts/*; do
    [[ -f "$f" ]] || continue
    install -m 755 "$f" "$INSTALL_DIR/scripts/$(basename "$f")"
done
[[ -f "$SRC_DIR/uninstall.sh" ]] && install -m 755 "$SRC_DIR/uninstall.sh" "$INSTALL_DIR/uninstall.sh"

find "$INSTALL_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Khong de file nao trong /opt/console-pi cho phep nguoi khac ghi - ai co
# shell tren may deu sua duoc noi dung dashboard hien ra.
find "$INSTALL_DIR" -perm -o+w -not -type l -exec chmod o-w {} + 2>/dev/null || true
chown -R "$MAIN_USER:$MAIN_USER" "$INSTALL_DIR/nettools" "$INSTALL_DIR/ui" "$INSTALL_DIR/captures" 2>/dev/null || true
ok "Da chep ma nguon"

# ------------------------------------------------- 5. File cau hinh he thong
say "Cau hinh he thong"

# --- systemd-networkd: giu IP tinh cua AP khong bi xoa ---
mkdir -p /etc/systemd/network
if [[ ! -f /etc/systemd/network/12-wlan0.network ]] || \
   ! grep -q "KeepConfiguration=static" /etc/systemd/network/12-wlan0.network 2>/dev/null; then
    cat > /etc/systemd/network/12-wlan0.network <<'EOF'
[Match]
Name=wlan0

[Network]
DHCP=ipv4
# KHONG xoa IP "la" (vd 192.168.50.1 cua AP do script tu gan) khi reconfigure.
# Thieu dong nay: bat AP xong bi systemd-networkd am tham xoa mat IP.
#
# Phai la 'static', KHONG duoc dung 'yes':
#   yes -> networkd coi lease DHCP la "critical". Sau khi IP wlan0 bi xoa
#          (nut Ngat WiFi, hoac wifi-fallback chuyen che do), networkd tu choi
#          xin lai IP: "DHCPv4 connection considered critical, ignoring request
#          to reconfigure it". WiFi ket noi duoc nhung KHONG BAO GIO co IP,
#          phai restart systemd-networkd moi song. Da gap that.
#   static -> van giu IP tinh cua AP, nhung lease DHCP thi khong bi khoa.
KeepConfiguration=static
EOF
    ok "Da tao 12-wlan0.network (KeepConfiguration=static)"
else
    ok "12-wlan0.network da dung"
fi

# --- hostapd (AP ConsolePi) ---
if [[ ! -f /etc/hostapd/hostapd.conf ]]; then
    mkdir -p /etc/hostapd
    AP_PASS="$(head -c 9 /dev/urandom | base64 | tr -d '/+=' | head -c 12)"
    cat > /etc/hostapd/hostapd.conf <<EOF
interface=wlan0
ssid=ConsolePi
hw_mode=g
channel=7
wpa=2
wpa_passphrase=${AP_PASS}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=CCMP
EOF
    chmod 600 /etc/hostapd/hostapd.conf
    ok "Da tao hostapd.conf - SSID: ConsolePi, mat khau: ${AP_PASS}"
    echo -e "  ${Y}>>> GHI LAI MAT KHAU AP NAY: ${AP_PASS}${N}"
else
    # Ban cu dung TKIP -> macOS/iOS bao "Weak Security", sua sang CCMP
    if grep -q "^wpa_pairwise=TKIP" /etc/hostapd/hostapd.conf; then
        sed -i 's/^wpa_pairwise=TKIP/wpa_pairwise=CCMP/' /etc/hostapd/hostapd.conf
        ok "Da doi hostapd tu TKIP sang CCMP (tuong thich macOS/iOS)"
    fi
    ok "Giu nguyen hostapd.conf hien co"
fi
systemctl unmask hostapd 2>/dev/null || true
systemctl disable hostapd 2>/dev/null || true   # script wifi-fallback tu bat khi can

# --- dnsmasq cho AP ---
if ! grep -q "192.168.50" /etc/dnsmasq.conf 2>/dev/null; then
    cat > /etc/dnsmasq.conf <<'EOF'
interface=wlan0
dhcp-range=192.168.50.10,192.168.50.50,255.255.255.0,24h
bind-interfaces
EOF
    ok "Da tao dnsmasq.conf cho AP"
else
    grep -q "^bind-interfaces" /etc/dnsmasq.conf || echo "bind-interfaces" >> /etc/dnsmasq.conf
    ok "Giu nguyen dnsmasq.conf"
fi
systemctl disable dnsmasq 2>/dev/null || true

# --- dnsmasq rieng cho Bluetooth PAN ---
cat > /etc/dnsmasq-bt.conf <<'EOF'
interface=pan0
bind-interfaces
except-interface=lo
dhcp-range=192.168.60.10,192.168.60.50,255.255.255.0,24h
dhcp-option=3,192.168.60.1
dhcp-option=6,192.168.60.1
pid-file=/run/dnsmasq-bt.pid
EOF
ok "Da cau hinh dnsmasq cho Bluetooth PAN"

# --- wpa_supplicant: file WiFi da luu ---
mkdir -p /etc/wpa_supplicant
if [[ ! -f /etc/wpa_supplicant/wpa_supplicant-wlan0.conf ]]; then
    cat > /etc/wpa_supplicant/wpa_supplicant-wlan0.conf <<'EOF'
ctrl_interface=/var/run/wpa_supplicant
update_config=1
country=VN
EOF
    ok "Da tao file WiFi rong"
else
    ok "GIU NGUYEN danh sach WiFi da luu"
fi

# Sua quyen o MOI lan cai, khong chi luc tao moi. Cac file nay chua mat khau
# WiFi va mat khau AP dang chu thuong; mac dinh cua he thong la 644 = bat ky
# tai khoan nao tren may cung doc duoc. Da gap tren chinh may nay.
chmod 600 /etc/wpa_supplicant/wpa_supplicant-wlan0.conf 2>/dev/null || true
chmod 600 /etc/hostapd/hostapd.conf 2>/dev/null || true
# Service wpa_supplicant he thong tranh quyen dieu khien wlan0 -> phai chan
# Mask ban wpa_supplicant "toan cuc" (dung chung cho moi interface, do
# NetworkManager dieu khien) de no khong tranh card WiFi voi hostapd.
systemctl mask wpa_supplicant 2>/dev/null || true

# ...nhung PHAI bat ban theo-interface thay the, neu khong sau khi reboot
# KHONG CO GI khoi dong wpa_supplicant va WiFi khong bao gio len.
# Truoc day may van chay duoc chi vi tien trinh tu lan boot cu con song;
# reboot mot phat la mat WiFi. Da kiem chung.
systemctl unmask wpa_supplicant@wlan0 2>/dev/null || true

# --- Bluetooth: ten thiet bi + tu bat ---
mkdir -p /etc/bluetooth
# Kiem tra TAT CA khoa can co, khong chi AutoEnable. Neu chi kiem tra 1 khoa
# thi ban nang cap them khoa moi se bi bo qua im lang (da gap voi ReconnectUUIDs).
if ! grep -q "^ReconnectUUIDs" /etc/bluetooth/main.conf 2>/dev/null \
   || ! grep -q "^AutoEnable" /etc/bluetooth/main.conf 2>/dev/null; then
    python3 - <<'PY'
import re
p = "/etc/bluetooth/main.conf"
try:
    s = open(p).read()
except FileNotFoundError:
    s = "[General]\n\n[Policy]\n"
def setkv(sec, key, val, s):
    m = re.search(rf"(\[{sec}\]\n)", s)
    if not m:
        return s + f"\n[{sec}]\n{key} = {val}\n"
    i = m.end()
    end = s.find("\n[", i)
    end = len(s) if end == -1 else end
    blk = s[i:end]
    kp = re.compile(rf"^{key}\s*=.*$", re.M)
    blk = kp.sub(f"{key} = {val}", blk) if kp.search(blk) else f"{key} = {val}\n" + blk
    return s[:i] + blk + s[end:]
for sec, k, v in [("General","DiscoverableTimeout","0"),
                  ("General","PairableTimeout","0"),
                  ("Policy","AutoEnable","true"),
                  # Kich ban 3: thiet bi DA ghep cap bat len la noi lai ngay,
                  # khong phai vao dashboard bam nut. BlueZ chi tu noi lai khi
                  # duoc liet ke o day: HID (ban phim/chuot) va PAN (mang).
                  ("Policy","ReconnectUUIDs",
                   "00001124-0000-1000-8000-00805f9b34fb,"
                   "00001116-0000-1000-8000-00805f9b34fb,"
                   "00001115-0000-1000-8000-00805f9b34fb"),
                  ("Policy","ReconnectAttempts","7"),
                  ("Policy","ReconnectIntervals","1,2,4,8,16,32,64")]:
    s = setkv(sec, k, v, s)
open(p, "w").write(s)
PY
    ok "Da cau hinh Bluetooth (luon ghep cap duoc)"
fi
grep -q "PRETTY_HOSTNAME=ConsolePi" /etc/machine-info 2>/dev/null || \
    echo "PRETTY_HOSTNAME=ConsolePi" > /etc/machine-info

# --- Tu nhan moi loai cap console + tat tiet kiem dien WiFi ---
for r in 99-consolepi-serial.rules 99-consolepi-wifi.rules; do
    if [[ -f "$SRC_DIR/config/$r" ]]; then
        install -m 644 "$SRC_DIR/config/$r" "/etc/udev/rules.d/$r"
    fi
done
udevadm control --reload-rules 2>/dev/null || true
ok "Da cai quy tac tu nhan cap console va tat tiet kiem dien WiFi"

# Tat tiet kiem dien ngay (khong doi cam lai card)
for w in /sys/class/net/wlan*; do
    [[ -e "$w" ]] && iw dev "$(basename "$w")" set power_save off 2>/dev/null || true
done

# --- Cam ung khi man hinh xoay ---
# cage/wlroots KHONG tu xoay toa do cam ung theo huong man hinh, nen phai
# hieu chinh o tang libinput cho khop. Neu lech: cham khong trung nut,
# vuot nguoc chieu.
#
# QUAN TRONG: chi ghi de file ma tran khi THAT SU biet huong man hinh.
# Ban truoc cua script nay doc config.json, thay trong thi mac dinh "normal"
# roi ghi de mat ma tran dang dung dung -> lam hong cam ung. Gio uu tien doc
# huong THUC TE tu man hinh dang chay, chi dung config lam phuong an du phong.
if [[ "$WANT_SCREEN" == "yes" ]]; then
    LIVE_ROT=""
    if command -v wlr-randr >/dev/null 2>&1; then
        LIVE_ROT="$(sudo -n -u "$MAIN_USER" env WAYLAND_DISPLAY=wayland-0 \
            XDG_RUNTIME_DIR="/run/user/$(id -u "$MAIN_USER")" wlr-randr 2>/dev/null \
            | awk '/[Tt]ransform:/ {print $2; exit}')"
    fi
    CFG_ROT="$(python3 -c "
import json
try: print(json.load(open('/opt/console-pi/config.json')).get('screen_rotation',''))
except Exception: print('')
" 2>/dev/null || echo '')"

    ROT="${LIVE_ROT:-$CFG_ROT}"

    if [[ -n "$ROT" ]]; then
        case "$ROT" in
            90)  MTX="0 -1 1 1 0 0" ;;
            180) MTX="-1 0 1 0 -1 1" ;;
            270) MTX="0 1 0 -1 0 1" ;;
            *)   MTX="1 0 0 0 1 0" ;;
        esac
        cat > /etc/udev/rules.d/99-consolepi-touch.rules <<EOF
# Console Pi - hieu chinh toa do cam ung cho huong man hinh: $ROT
# cage/wlroots khong tu xoay toa do cam ung nen phai chinh o day.
ENV{ID_INPUT_TOUCHSCREEN}=="1", ENV{LIBINPUT_CALIBRATION_MATRIX}="$MTX"
EOF
        udevadm control --reload-rules 2>/dev/null || true
        udevadm trigger --subsystem-match=input --action=change 2>/dev/null || true
        ok "Cam ung hieu chinh cho huong man hinh: $ROT"

        # File rieng cho kiosk-start.sh (chay quyen user, khong doc duoc
        # config.json vi file do chmod 600 thuoc root)
        echo "$ROT" > /opt/console-pi/screen-rotation
        chmod 644 /opt/console-pi/screen-rotation

        # Ghi them vao config de giao dien Cai dat hien dung trang thai
        python3 - "$ROT" <<'PY' 2>/dev/null || true
import json, os, sys
p = "/opt/console-pi/config.json"
try: cfg = json.load(open(p))
except Exception: cfg = {}
cfg["screen_rotation"] = sys.argv[1]
old = os.umask(0o077)
try: json.dump(cfg, open(p, "w"), indent=2)
finally: os.umask(old)
PY
    else
        ok "Chua ro huong man hinh - khong dung toi ma tran cam ung dang co"
    fi
fi

# --- nginx: cong trung gian cho tat ca ---
# Truoc day terminal chay o cong rieng va tu bao ve bang mat khau HTTP co ban,
# nhung trinh duyet CAM iframe khac origin hien hop thoai nhap mat khau nen
# khung terminal luon loi. Gio moi thu qua nginx cong 80: cung origin, va
# terminal dung luon phien dang nhap cua dashboard.
if [[ -f "$SRC_DIR/config/nginx-console-pi.conf" ]]; then
    install -m 644 "$SRC_DIR/config/nginx-console-pi.conf" \
            /etc/nginx/sites-available/console-pi.conf
    ln -sf /etc/nginx/sites-available/console-pi.conf \
           /etc/nginx/sites-enabled/console-pi.conf
    rm -f /etc/nginx/sites-enabled/default
    if nginx -t >/dev/null 2>&1; then
        ok "Cau hinh nginx hop le"
    else
        warn "Cau hinh nginx co loi - chay 'sudo nginx -t' de xem"
    fi
fi

# --- ssh client: cho phep ket noi toi thiet bi mang cu ---
# OpenSSH ban moi bo mac dinh KEX/host-key/cipher dua tren SHA-1 - hau het
# switch/router doi cu (chinh la thu Console Pi dung de chan doan) chi ho
# tro dung nhung thuat toan cu do. Khong co file nay thi SSH toi thiet bi
# cu bao thang "no matching key exchange method found", khong ket noi duoc
# gi ca - da gap that tren chinh thiet bi cua nguoi dung.
if [[ -f "$SRC_DIR/config/ssh_config-legacy-devices.conf" ]]; then
    install -m 644 "$SRC_DIR/config/ssh_config-legacy-devices.conf" \
            /etc/ssh/ssh_config.d/consolepi-legacy-devices.conf
    ok "Da cho phep SSH client ket noi thiet bi mang cu (KEX/cipher SHA-1)"
fi

# --- lldpd: bat tuong thich CDP (switch Cisco) ---
if [[ -f /etc/default/lldpd ]] && ! grep -q '^DAEMON_ARGS=".*-c' /etc/default/lldpd; then
    sed -i 's/^#*DAEMON_ARGS=.*/DAEMON_ARGS="-c"/' /etc/default/lldpd
    ok "Da bat CDP cho lldpd"
fi

# ------------------------------------------------- 6. Dich vu systemd
say "Cai dat dich vu"

for f in "$SRC_DIR"/systemd/*.service "$SRC_DIR"/systemd/*.timer; do
    [[ -e "$f" ]] || continue
    base="$(basename "$f")"
    # Kiosk chi cai khi co man hinh
    if [[ "$base" == "console-pi-kiosk.service" && "$WANT_SCREEN" != "yes" ]]; then
        continue
    fi
    install -m 644 "$f" "/etc/systemd/system/$base"
done

# Service kiosk chay duoi tai khoan chinh, khong hardcode "administrator"
if [[ "$WANT_SCREEN" == "yes" && -f /etc/systemd/system/console-pi-kiosk.service ]]; then
    UID_MAIN="$(id -u "$MAIN_USER")"
    sed -i "s/^User=.*/User=$MAIN_USER/; s/^Group=.*/Group=$MAIN_USER/; \
            s|XDG_RUNTIME_DIR=/run/user/[0-9]*|XDG_RUNTIME_DIR=/run/user/$UID_MAIN|" \
        /etc/systemd/system/console-pi-kiosk.service
fi

systemctl daemon-reload

# Thu tu quan trong: dashboard phai khoi dong lai TRUOC nginx.
# Ban cu cua dashboard lang nghe 0.0.0.0:80, ban moi chuyen sang
# 127.0.0.1:5000 - neu bat nginx truoc thi cong 80 con bi giu, nginx chet.
ENABLE_LIST=( console-pi-dashboard console-pi-term-local console-pi-term-ssh
              bt-pan0 dnsmasq-bt bt-agent bt-nap
              wifi-fallback.timer lldpd bluetooth avahi-daemon nginx
              wpa_supplicant@wlan0 console-pi-selftest )
[[ "$WANT_SCREEN" == "yes" ]] && ENABLE_LIST+=( console-pi-kiosk )

for s in "${ENABLE_LIST[@]}"; do
    systemctl enable "$s" >/dev/null 2>&1 || warn "Khong bat duoc $s"
done

# ttyd cho tung cong serial dang cam (template unit, tu bam theo udev)
# Ca hai ho thiet bi: ttyUSB (FTDI/Prolific/CH340) va ttyACM (cap Cisco USB
# console, cac thiet bi CDC-ACM). Chi quet ttyUSB* la bo sot dung cai cap
# micro-USB cua Cisco.
for dev in /dev/ttyUSB* /dev/ttyACM*; do
    [[ -e "$dev" ]] || continue
    systemctl enable "console-pi-ttyd@$(basename "$dev")" >/dev/null 2>&1 || true
done

ok "Da bat ${#ENABLE_LIST[@]} dich vu"

# ------------------------------------------------- 7. Khoi dong
say "Khoi dong dich vu"
for s in "${ENABLE_LIST[@]}"; do
    systemctl restart "$s" >/dev/null 2>&1 || warn "Khong khoi dong duoc $s"
done
for dev in /dev/ttyUSB*; do
    [[ -e "$dev" ]] || continue
    systemctl restart "console-pi-ttyd@$(basename "$dev")" >/dev/null 2>&1 || true
done
sleep 3

# ------------------------------------------------- 8. Kiem tra
# Cai dat co khoi dong lai wpa_supplicant@wlan0. Sau khi restart, card
# associate lai nhung systemd-networkd KHONG tu xin DHCP - phai goi
# `networkctl reconfigure` sau khi associate xong. Thieu buoc nay thi cai xong
# WiFi mat IP toi 2 phut (den luot wifi-fallback ke tiep) - rat de tuong la
# ban cai lam hong mang.
if ip link show wlan0 >/dev/null 2>&1 && ! systemctl is-active --quiet hostapd; then
    for _ in $(seq 1 20); do
        sleep 1
        wpa_cli -i wlan0 status 2>/dev/null | grep -q "wpa_state=COMPLETED" && break
    done
    networkctl reconfigure wlan0 2>/dev/null || true
    for _ in $(seq 1 10); do
        sleep 1
        WIP=$(ip -4 -o addr show wlan0 2>/dev/null | awk '{print $4}' | head -1)
        [[ -n "$WIP" ]] && break
    done
    [[ -n "${WIP:-}" ]] && ok "WiFi da co IP tro lai: $WIP" \
                        || warn "WiFi chua co IP - wifi-fallback se xu ly trong 2 phut"
fi

say "Kiem tra sau cai dat"
FAIL=0
for s in nginx console-pi-dashboard console-pi-term-local console-pi-term-ssh; do
    if systemctl is-active --quiet "$s"; then
        ok "$s: dang chay"
    else
        warn "$s: CHUA CHAY - xem 'journalctl -u $s -n 30'"
        FAIL=$((FAIL+1))
    fi
done

if curl -fsS --max-time 5 -o /dev/null http://127.0.0.1/healthz 2>/dev/null; then
    ok "Dashboard phan hoi tot"
else
    warn "Dashboard chua phan hoi - xem 'journalctl -u console-pi-dashboard -n 30'"
    FAIL=$((FAIL+1))
fi

# ------------------------------------------------- Ket thuc
IP_ETH="$(ip -4 -o addr show eth0 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | head -1)"
IP_WLAN="$(ip -4 -o addr show wlan0 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | head -1)"
HOSTN="$(hostname)"

echo
echo "╔══════════════════════════════════════════════╗"
if [[ $FAIL -eq 0 ]]; then
    echo -e "║   ${G}CAI DAT HOAN TAT${N}                           ║"
else
    echo -e "║   ${Y}CAI DAT XONG - CO $FAIL CANH BAO${N}              ║"
fi
echo "╚══════════════════════════════════════════════╝"
echo
echo "  Truy cap dashboard:"
[[ -n "$IP_ETH"  ]] && echo "    http://$IP_ETH        (day LAN)"
[[ -n "$IP_WLAN" ]] && echo "    http://$IP_WLAN        (WiFi)"
echo "    http://${HOSTN}.local"
[[ "$WANT_SCREEN" == "yes" ]] && echo "    Hoac xem truc tiep tren man hinh gan tren thiet bi"
echo
echo "  Dang nhap bang TAI KHOAN LINUX cua may nay (vi du: $MAIN_USER)"
echo
echo "  Tai lieu huong dan: mo dashboard -> tab 'Tai lieu'"
echo
