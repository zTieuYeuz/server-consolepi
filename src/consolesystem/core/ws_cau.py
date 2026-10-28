# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
[core] Dang ky "phien WebSocket" dung chung cau WebSocket 127.0.0.1:8895 (nginx /uem-vnc-ws/<ma>, da dang nhap moi vao duoc).
Tinh nang khac (vd Remote Desktop qua guacd) dang ky ma phien + ham xu ly o day; cau noi (features/uem/uem_vnc) tra cuu
ma phien truoc khi xu ly kieu VNC. Nho vay khong phai them duong nginx moi tren may da cai.
"""
import threading
import time

_KHOA = threading.Lock()
_XU_LY = {}            # ma phien -> (ham(cs, hdr, khoa_ws, doc_khung, khung), het_han)
_KHOI_DONG = []        # ham bat cau noi (uem_vnc dang ky luc nap module)


def dang_ky(tok, ham, giay=600):
    """Ma phien chi dung de MO ket noi trong `giay` giay; ket noi da mo thi khong bi cat."""
    with _KHOA:
        now = time.time()
        for k in [k for k, (_h, h) in _XU_LY.items() if h < now]:
            _XU_LY.pop(k, None)
        _XU_LY[tok] = (ham, now + giay)


def lay(tok):
    with _KHOA:
        v = _XU_LY.get(tok)
    return v[0] if v and v[1] >= time.time() else None


def bo(tok):
    with _KHOA:
        _XU_LY.pop(tok, None)


def dat_khoi_dong(ham):
    _KHOI_DONG[:] = [ham]


def dam_bao_chay():
    """Bat cau noi WebSocket neu chua chay. Tra False neu chua co cau noi nao dang ky."""
    return bool(_KHOI_DONG) and bool(_KHOI_DONG[0]())
