#!/bin/bash
# Console Pi - Khoi dong giao dien kiosk tren man hinh cam ung gan truc tiep
#
# Chay chromium toan man hinh (khong thanh dia chi, khong tab) tro vao
# dashboard localhost. Dung cage lam compositor Wayland toi gian - no chi
# chay dung 1 ung dung toan man hinh, khong desktop/taskbar gi ca.

# Cong 8880 chu KHONG phai 80. Day la cong rieng chi lang nghe tren loopback,
# va la CHO DUY NHAT duoc mien dang nhap. Cong 80 (LAN, WiFi, Cloudflare) luon
# phai dang nhap.
#
# Truoc day kiosk dung cong 80 va dieu kien mien dang nhap la "IP = 127.0.0.1".
# Nhung cloudflared cung chay tren Pi va cung goi vao 127.0.0.1:80, nen moi
# nguoi qua duong ham deu duoc mien dang nhap - lo hong nghiem trong da sua.
# Dia chi Flask that su - dung boi kiosk-loading.html (xem duoi), khong con
# dung truc tiep trong script nay nua.
LOADING_URL="file:///opt/console-pi/scripts/kiosk-loading.html"

# --- Xoay man hinh ------------------------------------------------------
# Huong lay tu config.json (tab Cai dat ghi vao day) - KHONG hardcode, de
# cai dat va giao dien luon dung 1 nguon su that.
#
# LUU Y: cage/wlroots khong tu xoay toa do cam ung theo man hinh, nen con
# can ma tran trong /etc/udev/rules.d/99-consolepi-touch.rules cho khop.
# Hai cho nay PHAI cung mot huong, lech la cham khong trung.
# Doc tu file rieng (khong doc config.json vi file do chmod 600 thuoc root
# de giau mat khau terminal - script nay chay quyen user nen khong doc duoc).
ROTATE="$(cat /opt/console-pi/screen-rotation 2>/dev/null || echo normal)"

if [ -n "$ROTATE" ] && [ "$ROTATE" != "normal" ]; then
    OUTPUT=$(wlr-randr 2>/dev/null | awk '/^[A-Za-z]/ {print $1; exit}')
    if [ -n "$OUTPUT" ]; then
        wlr-randr --output "$OUTPUT" --transform "$ROTATE" 2>/dev/null \
            && echo "Da xoay $OUTPUT sang $ROTATE"
    fi
fi
# -------------------------------------------------------------------------

# LOI THAT DA GAP (anh Thoai bao moi lan bat/khoi dong lai may deu thay
# trang "127.0.0.1 khong ket noi duoc", phai doi roi tu bam Reload): truoc
# day cho Chromium DUNG YEN trong shell (vong lap curl toi da 60 giay) roi
# moi mo trinh duyet vao dung dashboard. Nhung luc moi khoi dong dia rat
# ban (hang chuc dich vu cung chay, Flask phai nap scapy/cryptography/
# netmiko/tat ca module nettools), doi khi CAN HON 60 GIAY - luc do Chromium
# da mo va bao loi tu truoc khi kip xong. Va suot luc cho, man hinh khong co
# gi bao hieu dang chay hay da treo.
#
# Da doi cach: KHONG doi trong shell nua - mo NGAY trang tinh
# kiosk-loading.html (luon mo duoc, khong phu thuoc Flask/nginx da chay
# hay chua). Chinh trang do tu kiem tra dashboard bang JavaScript, hien
# thanh tien trinh %, va TU CHUYEN sang dashboard that ngay khi san sang -
# khong bao gio con thay trang loi nua. Da kiem chung that ca 2 chieu: goi
# fetch() tu file:// sang http://127.0.0.1:8880 thanh cong khong bi chan,
# va thanh tien trinh tang dan dung khi dashboard chua san sang.

# Thu muc profile rieng, tranh dinh trang thai cu / loi "profile in use"
PROFILE_DIR=/tmp/console-pi-kiosk-profile
rm -rf "$PROFILE_DIR"
mkdir -p "$PROFILE_DIR"

# --- Dieu chinh theo dung luong RAM cua may -----------------------------
# Pi 3 (1GB) va Pi Zero 2W (512MB) khong gong noi Chromium mac dinh:
# no de ra 1 tien trinh cho moi trang + GPU + zygote, de an het 1GB.
# Nhung may nay can gioi han so tien trinh va bo nho JS.
RAM_MB=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)

LOW_RAM_FLAGS=""
if [ "$RAM_MB" -lt 1500 ]; then
    LOW_RAM_FLAGS="--process-per-site         --renderer-process-limit=2         --js-flags=--max-old-space-size=96         --disable-gpu-rasterization         --disable-smooth-scrolling"
    echo "RAM ${RAM_MB}MB - bat che do tiet kiem bo nho"
elif [ "$RAM_MB" -lt 3000 ]; then
    LOW_RAM_FLAGS="--process-per-site --renderer-process-limit=3"
    echo "RAM ${RAM_MB}MB - gioi han vua phai"
else
    echo "RAM ${RAM_MB}MB - dung cau hinh day du"
fi

# LOI THAT DA GAP (khong phai doan): tung bat --overscroll-history-navigation=1
# de lam duong "vuot canh de quay ve dashboard" cho tab YouTube (nut dieu
# huong thang sang youtube.com). Da THAT BAI THAT SU: nguoi dung bam vao 1
# lien ket trong YouTube, bi dua sang mot website khac (datbike.vn) roi KET
# CUNG luon o do - vuot canh khong dua ve duoc, phai remote vao chay
# `systemctl restart console-pi-kiosk` moi cuu duoc man hinh. Nguyen nhan:
# co che nay cua Chromium chu yeu lam cho touchpad/chuot tren Windows/macOS,
# tren Linux voi man hinh cam ung thuan khong duoc trien khai day du/dang
# tin cay. Da TAT LAI ve mac dinh (=0) - khong dua vao cu chi nay nua.
#
# --remote-debugging-port=9222: CHI nghe tren 127.0.0.1 (mac dinh cua
# Chromium khi khong chi dia chi khac - da xac nhan bang `ss -tlnp`, khong
# lo ra mang ngoai). Dung boi scripts/kiosk-homebtn.py chay o service rieng
# (console-pi-kiosk-homebtn.service) de tiem 1 nut noi "Ve Dashboard" vao
# MOI trang duoc tai - day la duong quay ve THAT SU dang tin cay (khong phu
# thuoc cu chi cam ung nao), thay the cho --overscroll-history-navigation
# da that bai o tren. Xem chi tiet trong scripts/kiosk-homebtn.py.
#
# --allow-file-access-from-files: LOI THAT DA GAP khi lam man hinh cho
# co thanh tien trinh (scripts/kiosk-loading.html) - Chromium mac dinh
# CHAN trang file:// fetch() 1 file cuc bo KHAC (ke ca cung thu muc), da
# kiem chung that (fetch tra ve "Failed to fetch"). Co nay CHI noi long
# cho trang file:// tu doc file file:// khac - KHONG anh huong gi toi bao
# mat cua http/https (dashboard, YouTube, TikTok...), va trang file:// duy
# nhat tung mo trong kiosk nay la kiosk-loading.html do chinh du an tao ra.
exec chromium \
    --kiosk \
    --remote-debugging-port=9222 \
    --allow-file-access-from-files \
    --user-data-dir="$PROFILE_DIR" \
    --no-first-run \
    --no-default-browser-check \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-features=TranslateUI,Translate \
    --disable-pinch \
    --overscroll-history-navigation=0 \
    --noerrdialogs \
    --check-for-update-interval=31536000 \
    --touch-events=enabled \
    --enable-features=OverlayScrollbar \
    --autoplay-policy=user-gesture-required \
    --disable-background-networking \
    --disable-background-timer-throttling \
    --disable-component-update \
    --disable-domain-reliability \
    --disable-sync \
    --disable-extensions \
    --disable-breakpad \
    --no-pings \
    --metrics-recording-only \
    --disable-dev-shm-usage \
    $LOW_RAM_FLAGS \
    "$LOADING_URL"
