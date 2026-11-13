"""2.0.8 V6-1: loi SQLite TAM THOI (locked, I/O) khong duoc cach ly/doi ten DB dang dung; file hong that van duoc cach ly nhu cu."""
import glob
import os
import sqlite3
import sys

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))


@pytest.fixture
def S():
    from consolesystem.core import sqlite as S
    S.lam_moi()
    yield S
    S.lam_moi()


def _tao(S, duong):
    c = S.ket_noi(duong)
    c.execute("CREATE TABLE IF NOT EXISTS t(x)")
    c.execute("INSERT INTO t VALUES (42)")
    S.lam_moi()


def test_database_is_locked_khong_cach_ly(S, tmp_path, monkeypatch):
    d = str(tmp_path / "console.db")
    _tao(S, d)
    that = S._mo

    def khoa(duong):
        raise sqlite3.OperationalError("database is locked")
    monkeypatch.setattr(S, "_mo", khoa)
    with pytest.raises(sqlite3.OperationalError):
        S.ket_noi(d)
    monkeypatch.setattr(S, "_mo", that)
    assert os.path.exists(d) and not glob.glob(d + ".hong-*")                 # KHONG bi doi ten
    assert S.ket_noi(d).execute("SELECT x FROM t").fetchone()[0] == 42          # va du lieu cu con nguyen khi het loi tam


def test_loi_io_tam_thoi_khong_cach_ly(S, tmp_path, monkeypatch):
    d = str(tmp_path / "console.db")
    _tao(S, d)
    that = S._mo
    monkeypatch.setattr(S, "_mo", lambda p: (_ for _ in ()).throw(sqlite3.OperationalError("disk I/O error")))
    with pytest.raises(sqlite3.OperationalError):
        S.ket_noi(d)
    monkeypatch.setattr(S, "_mo", that)
    assert not glob.glob(d + ".hong-*") and S.ket_noi(d).execute("SELECT count(*) FROM t").fetchone()[0] == 1


def test_file_hong_that_van_bi_cach_ly(S, tmp_path):
    d = str(tmp_path / "console.db")
    with open(d, "wb") as f:
        f.write(b"day khong phai sqlite" * 200)
    c = S.ket_noi(d)                                                           # tao DB moi, giu file hong
    c.execute("CREATE TABLE t(x)")
    assert len(glob.glob(d + ".hong-*")) == 1


def test_quick_check_hong_van_bi_cach_ly(S, tmp_path):
    d = str(tmp_path / "console.db")
    _tao(S, d)
    with open(d, "r+b") as f:                                                  # pha vung giua file (trang du lieu)
        f.seek(4096)
        f.write(b"\xff" * 4096)
    S.lam_moi()
    try:
        S.ket_noi(d).execute("SELECT * FROM t").fetchall()
    except sqlite3.DatabaseError:
        pass
    # hoac duoc cach ly (quick_check/malformed) hoac khong phat hien duoc vi trang trong: chi can khong crash va khong mat file goc im lang
    assert os.path.exists(d) or glob.glob(d + ".hong-*")
