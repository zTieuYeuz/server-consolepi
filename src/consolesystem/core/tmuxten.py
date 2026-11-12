# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Dich cua lenh tmux khop CHINH XAC ten phien (NV8-11): `-t ssh-admin` mac dinh khop TIEN TO nen nguoi dung 'admin' chua co phien co the gui phim/xem man hinh cua
'ssh-administrator'. Dang '=ten:' (phien + cua so hien tai) dung duoc cho moi lenh (has-session, send-keys, capture-pane, kill-session, attach...). Ham thuan: khong
import gi ngoai thu vien chuan."""


def chinh_xac(ten):
    ten = str(ten)
    if ten.startswith("="):
        return ten
    return "=%s:" % ten
