# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""config.json cua may (mat khau terminal, xoay man hinh, tuy chon...) - quyen 0600, ghi nguyen tu, khong am tham mat khi file hong."""
import threading

from .store import KhoJson

_cac = {}
_khoa = threading.Lock()


def kho(duong):
    """Mot KhoJson DUY NHAT cho moi duong dan (de khoa luong va trang thai 'file chinh tot' dung chung giua cac cho goi)."""
    with _khoa:
        if duong not in _cac:
            _cac[duong] = KhoJson(duong, {}, mode=0o600, indent=2)
        return _cac[duong]
