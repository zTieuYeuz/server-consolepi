#!/bin/bash
# Console System - mo 1 PHIEN KET NOI (kieu MobaXterm) trong tmux.
#
# ttyd (console-pi-term-phien, cong 8012, chi 127.0.0.1) chay script nay voi
# doi so lay tu URL: /term-phien/?arg=<ma_phien>. Moi phien la 1 phien tmux
# rieng "phien-<ma>" -> dong tab / tai lai trang KHONG mat phien, mo lai la
# thay dung man hinh cu; mo cung phien tren 2 may thi thay cung 1 man hinh.
#
# AN TOAN: <ma_phien> la chuoi nguoi dung dieu khien (qua URL) -> chi nhan
# chu, so va dau "-" (chu hoa cho ten cong ttyUSB0), toi da 48 ky tu. Lenh that su (ssh/telnet/cong serial) KHONG
# bao gio lay tu URL ma do phien-chay.py doc tu file phien da luu, va chay
# bang danh sach doi so (khong qua shell) - khong the chen lenh.
set -u
MA="${1:-}"
if ! [[ "$MA" =~ ^[a-z0-9][a-zA-Z0-9-]{0,47}$ ]]; then
    echo "Ma phien khong hop le."; sleep 5; exit 1
fi

# Nhieu cua so cung xem 1 phien voi kich thuoc khac nhau (man hinh cam ung
# cua may + laptop): mac dinh tmux thu cua so theo man NHO NHAT -> phan con
# lai hien du lieu cu, thanh trang thai nam giua khung (loi that 27/09/2026).
# "latest" = theo cua so vua go phim gan nhat.
tmux set-option -g window-size latest 2>/dev/null || true
# Tat thanh trang thai cua tmux: nguoi dung khong can "[console-t0:microcom*]",
# va khi 2 man hinh khac co xem cung phien no nam lo lung giua khung.
tmux set-option -g status off 2>/dev/null || true
tmux set-option -g mouse on 2>/dev/null || true

case "$MA" in
    local)
        # Terminal cua chinh may nay - dung chung phien voi trang Terminal cu
        exec tmux new-session -A -s consolepi-local \
            bash --rcfile /opt/console-pi/scripts/console-bashrc ;;
    serial-tty*)
        # Cong console: DUNG CHUNG phien voi dich vu console-pi-ttyd@<cong>
        # (1 cong serial chi 1 chuong trinh giu duoc - mo 2 microcom se tranh
        # nhau ky tu). Doi toc do baud: phien-chay.py lo (respawn microcom).
        CONG="${MA#serial-}"
        [[ -e "/dev/$CONG" ]] || { echo "Khong thay /dev/$CONG - cap console da rut?"; sleep 8; exit 1; }
        exec tmux new-session -A -s "console-$CONG" \
            /usr/bin/python3 /opt/console-pi/scripts/phien-chay.py "$MA" ;;
    *)
        exec tmux new-session -A -s "phien-$MA" \
            /usr/bin/python3 /opt/console-pi/scripts/phien-chay.py "$MA" ;;
esac
