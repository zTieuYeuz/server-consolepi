# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Kho du lieu JSON NGUYEN TU va KHONG BAO GIO am tham mat du lieu (B1; xem KE-HOACH-2.0 muc B2b).

LOI THAT da gap o tk_dulieu.Kho (23/10/2026): file JSON hong (mat dien luc ghi, the loi) -> doc() AM THAM tra danh sach rong ->
lan ghi ke tiep GHI DE mat sach du lieu. Nay:
  - ghi: file tam + fsync + doi ten + fsync thu muc (mat dien khong de file nua voi); giu ban truoc hop le thanh `.bak` bang
    LIEN KET CUNG (khong ton them chep/dung luong, file hang chuc MB van nhanh);
  - doc file hong: dung `.bak` neu hop le; khong thi doi ten file hong thanh `.hong-<gio>` (KHONG xoa, KHONG de lan ghi sau ghi de),
    ghi nhat ky + them vao canh_bao() de giao dien hien, roi moi dung gia tri mac dinh;
  - loi doc/ghi that (het cho, quyen) -> nem LoiDuLieu, khong tra rong.
"""
import contextlib
import json
import os
import threading
import time

from . import nhatky

_log = nhatky.lay("store")
_CANH_BAO = []
_khoa_canh_bao = threading.Lock()


class LoiDuLieu(Exception):
    pass


def canh_bao():
    """Danh sach cac su co du lieu da gap tu luc khoi dong (de giao dien hien cho nguoi dung)."""
    with _khoa_canh_bao:
        return list(_CANH_BAO)


def _them_canh_bao(nd):
    _log.error(nd)
    with _khoa_canh_bao:
        _CANH_BAO.append({"gio": time.strftime("%Y-%m-%d %H:%M:%S"), "noi_dung": nd})
        del _CANH_BAO[:-50]


def _fsync_thu_muc(duong):
    with contextlib.suppress(OSError):
        fd = os.open(duong, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def ghi_nguyen_tu(duong, noi_dung, mode=0o644):
    """Ghi bytes: tam + fsync + doi ten + fsync thu muc. Dung cho moi file can an toan khi mat dien."""
    thu_muc = os.path.dirname(os.path.abspath(duong))
    os.makedirs(thu_muc, exist_ok=True)
    tam = duong + ".tmp"
    fd = os.open(tam, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(noi_dung)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tam, duong)
    except BaseException:
        with contextlib.suppress(OSError):
            os.remove(tam)
        raise
    _fsync_thu_muc(thu_muc)


class KhoJson:
    """Mot danh sach (list) hoac tu dien (dict) luu o 1 file JSON."""

    def __init__(self, duong, mac_dinh, khoa=None, mode=0o644, indent=1):
        self.duong = duong
        self.mac_dinh = mac_dinh
        self._khoa = khoa or threading.RLock()
        self._mode = mode
        self._indent = indent
        self._bak = duong + ".bak"
        self._main_tot = False            # biet chac file chinh hien tai doc duoc (de moi dam lien ket thanh .bak)

    # ---- doc
    def _doc_file(self, duong):
        with open(duong, encoding="utf-8") as f:
            d = json.load(f)
        if not isinstance(d, type(self.mac_dinh)):
            raise ValueError("sai kieu: can %s, thay %s" % (type(self.mac_dinh).__name__, type(d).__name__))
        return d

    def _mac_dinh(self):
        return type(self.mac_dinh)()

    def doc(self):
        with self._khoa:
            try:
                d = self._doc_file(self.duong)
                self._main_tot = True
                return d
            except FileNotFoundError:
                self._main_tot = False
                return self._mac_dinh()
            except ValueError as e:                       # JSON hong / sai kieu (UnicodeDecodeError cung la ValueError)
                return self._xu_ly_hong(e)
            except OSError as e:
                raise LoiDuLieu("khong doc duoc %s: %s" % (self.duong, e))

    def _xu_ly_hong(self, loi):
        hong = "%s.hong-%s" % (self.duong, time.strftime("%Y%m%d-%H%M%S"))
        with contextlib.suppress(OSError):
            os.replace(self.duong, hong)               # giu lai de nguoi dung/chuyen gia cuu, khong de lan ghi sau de len
        try:
            d = self._doc_file(self._bak)
        except (OSError, ValueError):
            _them_canh_bao("File du lieu HONG va khong co ban du phong hop le: %s (%s). Da giu file hong o %s, dang dung gia tri trong."
                           % (self.duong, loi, hong))
            self._main_tot = False
            return self._mac_dinh()
        _them_canh_bao("File du lieu HONG: %s (%s). Da khoi phuc tu ban du phong .bak (file hong giu o %s)." % (self.duong, loi, hong))
        ghi_nguyen_tu(self.duong, self._tuan_tu(d), self._mode)
        self._main_tot = True
        return d

    # ---- ghi
    def _tuan_tu(self, d):
        return json.dumps(d, ensure_ascii=False, indent=self._indent).encode("utf-8")

    def ghi(self, d):
        if not isinstance(d, type(self.mac_dinh)):
            raise LoiDuLieu("ghi sai kieu cho %s: can %s" % (self.duong, type(self.mac_dinh).__name__))
        nd = self._tuan_tu(d)                           # tuan tu hoa TRUOC khi dung toi file (loi kieu khong lam hong file)
        with self._khoa:
            if self._main_tot is False and os.path.exists(self.duong):
                with contextlib.suppress(OSError, ValueError):
                    self._doc_file(self.duong)
                    self._main_tot = True
            if self._main_tot and os.path.exists(self.duong):
                with contextlib.suppress(OSError):         # ban hop le truoc do -> .bak (lien ket cung, khong ton dung luong)
                    with contextlib.suppress(FileNotFoundError):
                        os.remove(self._bak)
                    os.link(self.duong, self._bak)
            try:
                ghi_nguyen_tu(self.duong, nd, self._mode)
            except OSError as e:
                raise LoiDuLieu("khong ghi duoc %s: %s" % (self.duong, e))
            self._main_tot = True

    def sua(self, ham):
        """doc -> ham(d) (sua tai cho) -> ghi. Tra ve gia tri ham tra."""
        with self._khoa:
            d = self.doc()
            kq = ham(d)
            self.ghi(d)
            return kq
