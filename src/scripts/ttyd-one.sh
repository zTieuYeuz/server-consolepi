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

IDX="${DEV#ttyUSB}"
case "$IDX" in ''|*[!0-9]*) IDX=0 ;; esac
PORT=$((8001 + IDX))
SESSION="console-$DEV"
BAUD="${CONSOLE_BAUD:-9600}"

exec /usr/local/bin/ttyd \
    -p "$PORT" \
    -i 127.0.0.1 \
    -b "/term-console/$DEV" \
    -W \
    -t titleFixed="$DEV" \
    -t fontSize=15 \
    tmux new-session -A -s "$SESSION" \
    /usr/bin/microcom -s "$BAUD" -p "/dev/$DEV"
