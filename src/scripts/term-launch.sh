#!/bin/bash
# Console Pi - Khoi dong 1 terminal web (ttyd gan vao phien tmux)
#
# BAO MAT: chi lang nghe tren 127.0.0.1, KHONG mo ra mang. Nguoi dung vao
# qua nginx o cong 80, va nginx da kiem tra phien dang nhap dashboard truoc
# (auth_request). Vi vay o day khong can mat khau rieng nua.
#
# Dung tmux vi 2 ly do:
#   1. Phien khong mat khi dong trinh duyet giua chung
#   2. Ban phim ao tren man hinh cam ung go duoc vao day qua `tmux send-keys`
#
# Tham so: local | ssh
set -e

KIND="${1:-local}"
case "$KIND" in
    local) PORT=8010; SESSION=consolepi-local; BASE=/term-local ;;
    ssh)   PORT=8011; SESSION=consolepi-ssh;   BASE=/term-ssh ;;
    *)     echo "Dung: $0 [local|ssh]"; exit 1 ;;
esac

# Bang mau: tuong phan cao, phan biet ro trang thai khi doc output thiet bi mang
THEME='{"background":"#0f1114","foreground":"#d5dae2","cursor":"#4CAF50","selectionBackground":"#2f4a5f","black":"#22262b","red":"#ff6b6b","green":"#7ddc7d","yellow":"#ffd166","blue":"#6cb6ff","magenta":"#d99bff","cyan":"#68d5d5","white":"#c8cdd4","brightBlack":"#5a6472","brightRed":"#ff8f8f","brightGreen":"#a2f0a2","brightYellow":"#ffe08a","brightBlue":"#9ccdff","brightMagenta":"#e6bcff","brightCyan":"#93e6e6","brightWhite":"#f0f3f7"}'

# Shell co mau san (dau nhac, ls, grep, va cac lenh mang qua grc).
# Dung --rcfile de KHONG dung vao .bashrc cua he thong.
exec /usr/local/bin/ttyd \
    -p "$PORT" \
    -i 127.0.0.1 \
    -b "$BASE" \
    -W \
    -t titleFixed="Console Pi - $KIND" \
    -t fontSize=15 \
    -t fontFamily="ui-monospace, Menlo, Consolas, monospace" \
    -t "theme=$THEME" \
    tmux new-session -A -s "$SESSION" \
        bash --rcfile /opt/console-pi/scripts/console-bashrc
