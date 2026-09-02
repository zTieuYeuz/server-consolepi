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

exec /usr/local/bin/ttyd \
    -p "$PORT" \
    -i 127.0.0.1 \
    -b "$BASE" \
    -W \
    -t titleFixed="Console Pi - $KIND" \
    -t fontSize=15 \
    -t 'theme={"background":"#0f1114"}' \
    tmux new-session -A -s "$SESSION"
