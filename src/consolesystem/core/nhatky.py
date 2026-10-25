# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Nhat ky dung chung: ghi ra stderr de systemd/journald gom (`journalctl -u console-pi-dashboard`). Dinh dang giu kieu '[ten] noi dung'."""
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
