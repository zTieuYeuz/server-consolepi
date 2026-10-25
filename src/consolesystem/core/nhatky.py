# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Nhat ky dung chung: ghi ra stderr de systemd/journald gom (`journalctl -u console-system-dashboard`). Dinh dang giu kieu '[ten] noi dung'."""
import logging
import sys

_GOC = "consolesystem"
_da_cau_hinh = False


def lay(ten):
    """Logger cua mot thanh phan, vd lay('store'). Cau hinh mot lan cho ca goi."""
    global _da_cau_hinh
    if not _da_cau_hinh:
        g = logging.getLogger(_GOC)
        if not g.handlers:
            h = logging.StreamHandler(sys.stderr)
            h.setFormatter(logging.Formatter("[%(name)s] %(levelname)s %(message)s"))
            g.addHandler(h)
        g.setLevel(logging.INFO)
        g.propagate = False
        _da_cau_hinh = True
    return logging.getLogger("%s.%s" % (_GOC, ten))


_lan_cuoi = {}


def bo_qua(loi, ghi_chu="", moi_giay=600):
    """Thay cho `except Exception: pass`: loi VAN duoc bo qua (hanh vi cu giu nguyen) nhung de lai dau vet trong journald.
    Moi diem goi chi ghi toi da 1 dong / `moi_giay` giay (khong lam ngap nhat ky khi nam trong vong lap). Vi tri lay tu khung goi."""
    import time
    f = sys._getframe(1)
    khoa = (f.f_code.co_filename, f.f_lineno)
    bay_gio = time.monotonic()
    if bay_gio - _lan_cuoi.get(khoa, -1e18) < moi_giay:
        return
    _lan_cuoi[khoa] = bay_gio
    ten = (f.f_globals.get("__name__") or "?").rsplit(".", 1)[-1]
    lay("bo-qua").warning("%s:%d (%s) bo qua loi %s: %s %s", ten, f.f_lineno, f.f_code.co_name, type(loi).__name__, loi, ghi_chu)
