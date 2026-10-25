# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Ket noi SQLite dung chung (B1b): MOT file `console.db` cho du lieu LON va TANG DAN (bao cao may, lich su tac vu, trang thai chay...).
WAL + synchronous=NORMAL (khong hong file khi mat dien; co the mat vai giao dich cuoi), busy_timeout dai (nhieu tien trinh).
Ket noi theo tung luong; `lam_moi()` buoc moi luong mo lai ket noi (dung sau khoi phuc sao luu / doi thu muc du lieu).
"""
import contextlib
import os
import sqlite3
import threading
import time

from . import nhatky
from .store import _them_canh_bao

_log = nhatky.lay("sqlite")
_local = threading.local()
_the_he = 0
_khoa = threading.Lock()
_da_kiem = set()


def lam_moi():
    """Dong moi ket noi cu (lan luong khac se tu mo lai khi dung toi)."""
    global _the_he
    with _khoa:
        _the_he += 1
        _da_kiem.clear()


def _mo(duong):
    os.makedirs(os.path.dirname(os.path.abspath(duong)), exist_ok=True)
    c = sqlite3.connect(duong, timeout=60, isolation_level=None)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA synchronous=NORMAL")
    c.execute("PRAGMA busy_timeout=60000")
    c.execute("PRAGMA foreign_keys=ON")
    return c


def _cach_ly_hong(duong, loi):
    hong = "%s.hong-%s" % (duong, time.strftime("%Y%m%d-%H%M%S"))
    for hau in ("", "-wal", "-shm"):
        with contextlib.suppress(OSError):
            os.replace(duong + hau, hong + hau)
    _them_canh_bao("CO SO DU LIEU HONG: %s (%s). Da giu lai o %s va tao co so moi (trong). Khoi phuc tu ban sao luu neu can." % (duong, loi, hong))


def ket_noi(duong):
    """Ket noi cua luong hien tai toi `duong`. File hong -> cach ly (giu lai), canh bao, tao moi."""
    kc = getattr(_local, "kc", None)
    if kc is None or kc.get("the_he") != _the_he:
        if kc:
            for c in kc.get("c", {}).values():
                with contextlib.suppress(sqlite3.Error):
                    c.close()
        kc = _local.kc = {"the_he": _the_he, "c": {}}
    c = kc["c"].get(duong)
    if c is None:
        try:
            c = _mo(duong)
            if duong not in _da_kiem:
                r = c.execute("PRAGMA quick_check").fetchone()
                if r and r[0] != "ok":
                    raise sqlite3.DatabaseError("quick_check: %s" % r[0])
                _da_kiem.add(duong)
        except sqlite3.DatabaseError as e:
            with contextlib.suppress(Exception):
                c.close()
            _cach_ly_hong(duong, e)
            c = _mo(duong)
        kc["c"][duong] = c
    return c


def snapshot(duong, dich):
    """Ban sao NHAT QUAN cua co so du lieu dang chay (API backup cua SQLite) -> file `dich`. Dung cho sao luu."""
    nguon = sqlite3.connect(duong, timeout=60)
    try:
        out = sqlite3.connect(dich)
        try:
            nguon.backup(out)
        finally:
            out.close()
    finally:
        nguon.close()
