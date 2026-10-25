# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
KhoSqlite: cung giao dien doc()/ghi()/sua() nhu KhoJson nhung luu trong SQLite, CHI GHI PHAN DOI (B1b).

Vi sao: file may.json voi 300 may ~ 20MB, moi lan agent bao cao phai doc-phan tich-ghi lai ca 20MB len the SD. O day moi ban ghi la 1 dong:
doi 1 may = ghi 1 dong. Quy tac luu (giu NGUYEN thu tu va noi dung nhu khi dung JSON):
  - list co moi phan tu la dict co "id" duy nhat -> khoa theo id (them cuoi = chi them dong; sua = chi sua dong do; xoa = xoa dong)
  - list khac (lich su khong co id) -> theo vi tri (them cuoi = chi them dong; bot cuoi = xoa dong cuoi)
  - dict -> moi khoa cap 1 la 1 dong
Lan dau dung: tu nhap file JSON cu (neu co), kiem lai, roi doi ten thanh `.da-chuyen-<gio>` (KHONG xoa). `xuat_json()` dua ve JSON de hoan tac.
"""
import contextlib
import json
import os
import re
import sqlite3
import threading
import time

from . import nhatky, sqlite as _sq
from .store import KhoJson, LoiDuLieu

_log = nhatky.lay("store_sqlite")


def _ten_bang(ten):
    return "k_" + re.sub(r"[^a-z0-9_]", "_", ten.lower())


def _dump(x):
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"))


class KhoSqlite:
    def __init__(self, duong_db, ten, mac_dinh, duong_json_cu=None, khoa=None):
        self._db = duong_db
        self.ten = ten
        self.mac_dinh = mac_dinh
        self.duong = duong_json_cu or duong_db            # tuong thich: noi cu tung luu (chi de hien thi/dem)
        self._json_cu = duong_json_cu
        self._khoa = khoa or threading.RLock()
        self._bang = _ten_bang(ten)
        self._la_list = isinstance(mac_dinh, list)
        self._san_sang_the_he = None

    # ------------------------------------------------------------------ nen
    def _c(self):
        c = _sq.ket_noi(self._db)
        if self._san_sang_the_he != _sq._the_he:
            self._khoi_tao(c)
            self._san_sang_the_he = _sq._the_he
        return c

    def _khoi_tao(self, c):
        c.execute("CREATE TABLE IF NOT EXISTS meta (ten TEXT PRIMARY KEY, nhap_luc TEXT, nguon TEXT, so_dong INTEGER)")
        c.execute("CREATE TABLE IF NOT EXISTS %s (pos INTEGER PRIMARY KEY, khoa TEXT, j TEXT NOT NULL)" % self._bang)
        c.execute("CREATE INDEX IF NOT EXISTS %s_khoa ON %s(khoa)" % (self._bang, self._bang))
        if c.execute("SELECT 1 FROM meta WHERE ten=?", (self.ten,)).fetchone():
            return
        nhap = None
        if self._json_cu and os.path.exists(self._json_cu) and not c.execute("SELECT 1 FROM %s LIMIT 1" % self._bang).fetchone():
            nhap = self._nhap_json_cu(c)
        else:
            c.execute("INSERT OR IGNORE INTO meta VALUES (?,?,?,?)", (self.ten, time.strftime("%Y-%m-%d %H:%M:%S"), "", 0))
        _log.info("kho %s san sang (%s)", self.ten, nhap or "trong")

    def _nhap_json_cu(self, c):
        d = KhoJson(self._json_cu, self.mac_dinh).doc()           # cung co che hong->.bak->giu .hong-*
        c.execute("BEGIN IMMEDIATE")
        try:
            self._ghi_trong_tx(c, d)
            ban_doc = self._doc_trong_tx(c)
            if _dump(ban_doc) != _dump(d):
                raise LoiDuLieu("nhap %s sang SQLite khong khop sau khi kiem" % self.ten)
            c.execute("INSERT OR REPLACE INTO meta VALUES (?,?,?,?)",
                      (self.ten, time.strftime("%Y-%m-%d %H:%M:%S"), os.path.basename(self._json_cu), len(d)))
            c.execute("COMMIT")
        except BaseException:
            with contextlib.suppress(Exception):
                c.execute("ROLLBACK")
            raise
        dich = "%s.da-chuyen-%s" % (self._json_cu, time.strftime("%Y%m%d-%H%M%S"))
        with contextlib.suppress(OSError):
            os.replace(self._json_cu, dich)
        with contextlib.suppress(OSError):
            os.remove(self._json_cu + ".bak")
        return "nhap %d muc tu %s" % (len(d), os.path.basename(self._json_cu))

    # ------------------------------------------------------------------ doc
    def _doc_trong_tx(self, c):
        if self._la_list:
            return [json.loads(j) for (j,) in c.execute("SELECT j FROM %s ORDER BY pos" % self._bang)]
        return {k: json.loads(j) for k, j in c.execute("SELECT khoa, j FROM %s ORDER BY pos" % self._bang)}

    def doc(self):
        with self._khoa:
            try:
                return self._doc_trong_tx(self._c())
            except (sqlite3.Error, ValueError) as e:
                raise LoiDuLieu("khong doc duoc kho %s: %s" % (self.ten, e))

    # ------------------------------------------------------------------ ghi
    def _ghi_trong_tx(self, c, d):
        cu = [(p, k, j) for p, k, j in c.execute("SELECT pos, khoa, j FROM %s ORDER BY pos" % self._bang)]
        if self._la_list:
            muc = [(None, _dump(x)) for x in d]
            khoas = [x.get("id") if isinstance(x, dict) else None for x in d]
            keyed = (bool(d) and all(isinstance(k, (str, int)) and not isinstance(k, bool) for k in khoas)
                     and len({str(k) for k in khoas}) == len(khoas))
            muc = [(str(k) if keyed else None, j) for k, (_n, j) in zip(khoas, muc)]
        else:
            keyed = True
            muc = [(str(k), _dump(v)) for k, v in d.items()]
        cu_keyed = bool(cu) and all(k is not None for _p, k, _j in cu)
        if keyed and (cu_keyed or not cu):
            self._ghi_theo_khoa(c, cu, muc)
        elif (not keyed) and (not cu_keyed or not cu):
            self._ghi_theo_vi_tri(c, cu, muc)
        else:
            self._ghi_toan_bo(c, muc)

    def _ghi_toan_bo(self, c, muc):
        c.execute("DELETE FROM %s" % self._bang)
        c.executemany("INSERT INTO %s(pos, khoa, j) VALUES (?,?,?)" % self._bang, [(i, k, j) for i, (k, j) in enumerate(muc)])

    def _ghi_theo_vi_tri(self, c, cu, muc):
        n_cu = len(cu)
        sua = [(j, i) for i, (_k, j) in enumerate(muc) if i < n_cu and cu[i][2] != j]
        them = [(i, None, j) for i, (_k, j) in enumerate(muc) if i >= n_cu]
        if len(muc) < n_cu:
            c.execute("DELETE FROM %s WHERE pos >= ?" % self._bang, (len(muc),))
        if sua:
            c.executemany("UPDATE %s SET j=? WHERE pos=?" % self._bang, sua)
        if them:
            c.executemany("INSERT INTO %s(pos, khoa, j) VALUES (?,?,?)" % self._bang, them)

    def _ghi_theo_khoa(self, c, cu, muc):
        cu_map = {k: (p, j) for p, k, j in cu}
        moi_khoa = [k for k, _j in muc]
        con_lai = [k for k in moi_khoa if k in cu_map]
        thu_tu_cu = [k for p, k, _j in cu if k in set(con_lai)]
        max_pos = max((p for p, _k, _j in cu), default=-1)
        moi = [k for k in moi_khoa if k not in cu_map]
        cuoi = moi_khoa[len(moi_khoa) - len(moi):] if moi else []
        giu_pos = (con_lai == thu_tu_cu) and (moi == cuoi)       # thu tu cu khong doi, phan tu moi chi o cuoi
        bo = [k for k in cu_map if k not in set(moi_khoa)]
        if bo:
            c.executemany("DELETE FROM %s WHERE khoa=?" % self._bang, [(k,) for k in bo])
        if not giu_pos:                                            # doi thu tu / chen giua (hiem) -> danh so lai ca bang
            self._ghi_toan_bo(c, muc)
            return
        sua, them, pos = [], [], max_pos
        for k, j in muc:
            if k in cu_map:
                if cu_map[k][1] != j:
                    sua.append((j, k))
            else:
                pos += 1
                them.append((pos, k, j))
        if sua:
            c.executemany("UPDATE %s SET j=? WHERE khoa=?" % self._bang, sua)
        if them:
            c.executemany("INSERT INTO %s(pos, khoa, j) VALUES (?,?,?)" % self._bang, them)

    def _giao_dich(self, ham):
        c = self._c()
        c.execute("BEGIN IMMEDIATE")
        try:
            kq = ham(c)
            c.execute("COMMIT")
            return kq
        except BaseException:
            with contextlib.suppress(Exception):
                c.execute("ROLLBACK")
            raise

    def ghi(self, d):
        if not isinstance(d, type(self.mac_dinh)):
            raise LoiDuLieu("ghi sai kieu cho kho %s: can %s" % (self.ten, type(self.mac_dinh).__name__))
        nd = _dump(d)                                   # loi tuan tu hoa (kieu khong json) nem TRUOC khi mo giao dich
        del nd
        with self._khoa:
            try:
                self._giao_dich(lambda c: self._ghi_trong_tx(c, d))
            except sqlite3.Error as e:
                raise LoiDuLieu("khong ghi duoc kho %s: %s" % (self.ten, e))

    def sua(self, ham):
        """doc -> ham(d) (sua tai cho) -> ghi, TRONG MOT giao dich (an toan ca khi nhieu tien trinh)."""
        with self._khoa:
            def lam(c):
                d = self._doc_trong_tx(c)
                kq = ham(d)
                _dump(d)
                self._ghi_trong_tx(c, d)
                return kq
            try:
                return self._giao_dich(lam)
            except sqlite3.Error as e:                    # loi cua ham nguoi dung (ke ca ngoai le tuy y) di thang len, giao dich da rollback
                raise LoiDuLieu("khong sua duoc kho %s: %s" % (self.ten, e))

    # ------------------------------------------------------------------ hoan tac
    def xuat_json(self, duong):
        """Ghi noi dung kho ra file JSON (cung dinh dang KhoJson) - dung de hoan tac sang JSON hoac kiem tra bang mat."""
        from .store import ghi_nguyen_tu
        ghi_nguyen_tu(duong, json.dumps(self.doc(), ensure_ascii=False, indent=1).encode("utf-8"))
