#!/bin/bash
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# Console System - mo 1 PHIEN KET NOI (kieu MobaXterm) trong tmux.
#
# ttyd (console-system-term-phien, cong 8012, chi 127.0.0.1) chay script nay voi
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

# Phien KHONG phai terminal that cua Pi (SSH rieng, phien da luu, serial): tuyet doi khong cho tmux tro thanh duong ra shell root (LOI-013 goc).
# Tat phim tien to (Ctrl+B ... `:` = chay lenh tmux), tat chuot (menu chuot co "split" mo shell), shell mac dinh cua cua so moi = /bin/false.
khoa_tmux() {
    tmux set-option -t "=$1:" prefix None 2>/dev/null
    tmux set-option -t "=$1:" prefix2 None 2>/dev/null
    tmux set-option -t "=$1:" mouse off 2>/dev/null
    tmux set-option -t "=$1:" default-command /bin/false 2>/dev/null
}

case "$MA" in
    local)
        # Terminal cua chinh may nay - dung chung phien voi trang Terminal cu
        exec tmux new-session -A -s consolepi-local \
            bash --rcfile /opt/console-pi/scripts/console-bashrc ;;
    ssh-*|xem-*)
        # Terminal SSH RIENG moi nguoi (2.0.7): ma ngau nhien tra ra ten phien tmux; xem-* = chi doc (tmux attach -r)
        KQ="$(/usr/bin/python3 /opt/console-pi/scripts/ssh-phien-tra.py "$MA")" || { echo "Phien khong hop le hoac da het han."; sleep 5; exit 1; }
        CHE="${KQ%% *}"; TEN="${KQ#* }"
        if [[ "$CHE" == "ro" ]]; then
            tmux has-session -t "=$TEN:" 2>/dev/null || { echo "Nguoi kia chua mo terminal."; sleep 5; exit 1; }
            exec tmux attach-session -r -t "=$TEN:"
        fi
        # Phien chay launcher phien-ssh.py (KHONG co shell) duoi user khong dac quyen console-ssh neu tao duoc. Phien cu dang la shell (ban truoc 2.0.8) thi bo di.
        id console-ssh >/dev/null 2>&1 || useradd --system --home-dir /var/lib/console-ssh --create-home --shell /usr/sbin/nologin console-ssh 2>/dev/null
        # FAIL CLOSED (NV8-12): khong co user khong dac quyen thi KHONG mo phien SSH (khong chay tiep bang root)
        id console-ssh >/dev/null 2>&1 || { echo "Khong tao duoc tai khoan console-ssh: tu choi mo terminal SSH (khong chay bang root). Bao quan tri."; sleep 8; exit 1; }
        mkdir -p /var/lib/console-ssh/yeu-cau
        if id console-ssh >/dev/null 2>&1; then
            chown console-ssh:console-ssh /var/lib/console-ssh /var/lib/console-ssh/yeu-cau; chmod 0700 /var/lib/console-ssh; chmod 0770 /var/lib/console-ssh/yeu-cau
            LAUNCH=(setpriv --reuid=console-ssh --regid=console-ssh --init-groups env HOME=/var/lib/console-ssh USER=console-ssh LOGNAME=console-ssh /usr/bin/python3 /opt/console-pi/scripts/phien-ssh.py "$TEN")
        else
            echo "Khong dung duoc tai khoan console-ssh."; sleep 8; exit 1
        fi
        if tmux has-session -t "=$TEN:" 2>/dev/null; then
            case "$(tmux display-message -p -t "=$TEN:" '#{pane_start_command}' 2>/dev/null)" in
                *phien-ssh.py*) ;;
                *) tmux kill-session -t "=$TEN:" 2>/dev/null ;;
            esac
        fi
        tmux has-session -t "=$TEN:" 2>/dev/null || tmux new-session -d -s "$TEN" "${LAUNCH[@]}"
        khoa_tmux "$TEN"
        exec tmux attach-session -t "=$TEN:" ;;
    serial-tty*)
        # Cong console: DUNG CHUNG phien voi dich vu console-system-ttyd@<cong>
        # (1 cong serial chi 1 chuong trinh giu duoc - mo 2 microcom se tranh
        # nhau ky tu). Doi toc do baud: phien-chay.py lo (respawn microcom).
        CONG="${MA#serial-}"
        [[ -e "/dev/$CONG" ]] || { echo "Khong thay /dev/$CONG - cap console da rut?"; sleep 8; exit 1; }
        tmux has-session -t "=console-$CONG:" 2>/dev/null || tmux new-session -d -s "console-$CONG" /usr/bin/python3 /opt/console-pi/scripts/phien-chay.py "$MA"
        khoa_tmux "console-$CONG"
        exec tmux attach-session -t "=console-$CONG:" ;;
    *)
        tmux has-session -t "=phien-$MA:" 2>/dev/null || tmux new-session -d -s "phien-$MA" /usr/bin/python3 /opt/console-pi/scripts/phien-chay.py "$MA"
        khoa_tmux "phien-$MA"
        exec tmux attach-session -t "=phien-$MA:" ;;
esac
