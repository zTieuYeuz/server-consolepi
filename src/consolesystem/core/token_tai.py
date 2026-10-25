# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Token tai file 1 lan cho may dich (Trien khai phan mem / Quan ly may tram) - tach tu tk_dongco.py o B3 de web.auth khong phai import tk_dongco. Trang thai nam trong RAM tien trinh dashboard."""
import os
import threading
import time
import uuid

_KHOA = threading.RLock()


_TOKEN = {}                                               # token -> {duong, ten, het}


def tao_token(duong, giay=7200):
    tok = uuid.uuid4().hex
    with _KHOA:
        for k in [k for k, v in _TOKEN.items() if v["het"] < time.time()]:
            _TOKEN.pop(k, None)
        _TOKEN[tok] = {"duong": duong, "ten": os.path.basename(duong), "het": time.time() + giay}
    return tok


def tra_token(tok, ten):
    with _KHOA:
        v = _TOKEN.get(tok)
    if v and v["het"] > time.time() and v["ten"] == ten and os.path.isfile(v["duong"]):
        return v["duong"]
    return None
