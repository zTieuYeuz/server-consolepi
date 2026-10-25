# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""config.json cua may (mat khau terminal, xoay man hinh, tuy chon...) - quyen 0600, ghi nguyen tu, khong am tham mat khi file hong."""
import secrets
import threading

from . import duongdan as _DD
from .store import KhoJson, LoiDuLieu

_cac = {}
_khoa = threading.Lock()


def kho(duong):
    """Mot KhoJson DUY NHAT cho moi duong dan (de khoa luong va trang thai 'file chinh tot' dung chung giua cac cho goi)."""
    with _khoa:
        if duong not in _cac:
            _cac[duong] = KhoJson(duong, {}, mode=0o600, indent=2)
        return _cac[duong]


def load_config():
    """config.json cua may. File hong -> khoi phuc tu .bak hoac giu lai .hong-* (xem store.py), khong am tham tra {} roi ghi de."""
    try:
        return kho(_DD.FILE_CONFIG).doc()
    except LoiDuLieu:
        return {}


def save_config(cfg):
    kho(_DD.FILE_CONFIG).ghi(cfg)           # quyen 0600, ghi nguyen tu (tam + fsync + doi ten)


def get_term_credential():
    """Lay (user, pass) cho ttyd. Tu sinh lan dau neu chua co."""
    cfg = load_config()
    cred = cfg.get("terminal_auth")
    if not cred or ":" not in cred:
        cred = "console:" + secrets.token_urlsafe(12)
        cfg["terminal_auth"] = cred
        save_config(cfg)
    user, _, pw = cred.partition(":")
    return user, pw
