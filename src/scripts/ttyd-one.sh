#!/bin/bash
# Console Pi - Chay 1 ttyd cho 1 cong serial
#
# Port = 8001 + so thu tu cua ttyUSB (ttyUSB0 -> 8001, ttyUSB1 -> 8002)
# Chi lang nghe 127.0.0.1 - nguoi dung vao qua nginx cong 80 (da kiem tra
# dang nhap), khong the vao thang tu mang.
#
# Chay microcom BEN TRONG tmux vi:
#   1. Phien console khong mat khi dong trinh duyet
#   2. Ban phim ao go duoc vao console qua `tmux send-keys` (xterm.js khong
#      phai o nhap lieu nen khong go thang vao duoc)
DEV="$1"
[ -z "$DEV" ] && { echo "Dung: $0 ttyUSB0"; exit 1; }

# Hai ho thiet bi dung dai cong rieng de khong dam nhau:
#   ttyUSB0..3 -> 8001..8004  (cap FTDI / Prolific / CH340)
#   ttyACM0..3 -> 8005..8008  (cap Cisco USB Console va thiet bi CDC-ACM khac)
# Cong thuc PHAI khop voi console_port_for() trong ui/home.py va bang map
# trong config/nginx-console-pi.conf.
case "$DEV" in
    ttyACM*) BASE=8005; IDX="${DEV#ttyACM}" ;;
    ttyUSB*) BASE=8001; IDX="${DEV#ttyUSB}" ;;
    *)       echo "Khong ho tro thiet bi: $DEV"; exit 1 ;;
esac
case "$IDX" in ''|*[!0-9]*) IDX=0 ;; esac
PORT=$((BASE + IDX))
SESSION="console-$DEV"
BAUD="${CONSOLE_BAUD:-9600}"

# Thiet bi phai ton tai (co the vua bi rut ra)
[ -e "/dev/$DEV" ] || { echo "Khong thay /dev/$DEV"; exit 1; }

# Cung bang mau voi cac terminal khac. Thiet bi Cisco thuong khong tu gui
# ma mau, nhung nhung thiet bi co gui (NX-OS, IOS-XE, thiet bi nen Linux)
# se hien dung mau va de doc.
THEME='{"background":"#0f1114","foreground":"#d5dae2","cursor":"#4CAF50","selectionBackground":"#2f4a5f","black":"#22262b","red":"#ff6b6b","green":"#7ddc7d","yellow":"#ffd166","blue":"#6cb6ff","magenta":"#d99bff","cyan":"#68d5d5","white":"#c8cdd4","brightBlack":"#5a6472","brightRed":"#ff8f8f","brightGreen":"#a2f0a2","brightYellow":"#ffe08a","brightBlue":"#9ccdff","brightMagenta":"#e6bcff","brightCyan":"#93e6e6","brightWhite":"#f0f3f7"}'

# Bat chuot cho tmux (giong term-launch.sh): khong bat thi banh xe chuot bi
# dich thanh phim Mui ten -> lan chuot de xem lai man hinh lai hoa ra goi lai
# cac lenh cu. Bat roi thi banh xe cuon dung lich su man hinh.
tmux new-session -A -d -s "$SESSION" \
    /usr/bin/microcom -s "$BAUD" -p "/dev/$DEV" 2>/dev/null || true
tmux set-option -g mouse on 2>/dev/null || true

# disableLeaveAlert=true: bo hop thoai "Leave site?" moi khi roi trang.
exec /usr/local/bin/ttyd \
    -p "$PORT" \
    -i 127.0.0.1 \
    -b "/term-console/$DEV" \
    -W \
    -t titleFixed="$DEV" \
    -t fontSize=15 \
    -t fontFamily="ui-monospace, Menlo, Consolas, monospace" \
    -t disableLeaveAlert=true \
    -t disableResizeOverlay=true \
    -t "theme=$THEME" \
    tmux new-session -A -s "$SESSION" \
    /usr/bin/microcom -s "$BAUD" -p "/dev/$DEV"
