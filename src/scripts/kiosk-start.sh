#!/bin/bash
# Console Pi - Khoi dong giao dien kiosk tren man hinh cam ung gan truc tiep
#
# Chay chromium toan man hinh (khong thanh dia chi, khong tab) tro vao
# dashboard localhost. Dung cage lam compositor Wayland toi gian - no chi
# chay dung 1 ung dung toan man hinh, khong desktop/taskbar gi ca.

DASH_URL="http://127.0.0.1/"

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

# Doi dashboard san sang truoc khi mo trinh duyet (tranh man hinh loi
# "khong ket noi duoc" luc moi boot khi Flask chua kip khoi dong)
for i in $(seq 1 30); do
    if curl -s -o /dev/null --max-time 2 "$DASH_URL"; then
        break
    fi
    sleep 2
done

# Thu muc profile rieng, tranh dinh trang thai cu / loi "profile in use"
PROFILE_DIR=/tmp/console-pi-kiosk-profile
rm -rf "$PROFILE_DIR"
mkdir -p "$PROFILE_DIR"

exec chromium \
    --kiosk \
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
    "$DASH_URL"
