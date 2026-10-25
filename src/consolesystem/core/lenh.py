# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Chay lenh he thong AN TOAN: luon co timeout, khong bao gio nem ngoai le (tru khi check=True), tra ket qua co cau truc.
(Hon 80 cho `subprocess.run` rai rac, moi noi mot kieu xu ly loi - se chuyen dan sang day o B7.)
"""
import subprocess

from . import nhatky

_log = nhatky.lay("lenh")


class LoiLenh(Exception):
    pass


class Ket:
    """Ket qua mot lenh. rc: ma thoat; 124 = het gio; 127 = khong co lenh/khong chay duoc."""
    __slots__ = ("rc", "out", "err", "het_gio", "khong_chay_duoc")

    def __init__(self, rc, out="", err="", het_gio=False, khong_chay_duoc=False):
        self.rc, self.out, self.err, self.het_gio, self.khong_chay_duoc = rc, out, err, het_gio, khong_chay_duoc

    @property
    def ok(self):
        return self.rc == 0

    def __repr__(self):
        return "Ket(rc=%r, out=%r, err=%r)" % (self.rc, self.out[:60], self.err[:60])


def chay(lenh, timeout=30, input=None, cwd=None, env=None, check=False):
    """lenh: LIST (khong qua shell). Tra ve Ket. check=True: rc != 0 -> LoiLenh."""
    if isinstance(lenh, str):
        raise TypeError("lenh phai la list, khong dung chuoi (tranh shell injection)")
    try:
        r = subprocess.run(lenh, capture_output=True, text=True, timeout=timeout, input=input, cwd=cwd, env=env)
        ket = Ket(r.returncode, r.stdout or "", r.stderr or "")
    except subprocess.TimeoutExpired as e:
        _log.warning("het gio sau %ss: %s", timeout, lenh[:3])
        ket = Ket(124, _chuoi(e.stdout), _chuoi(e.stderr), het_gio=True)
    except (OSError, ValueError) as e:
        _log.warning("khong chay duoc %s: %s", lenh[:1], e)
        ket = Ket(127, "", str(e), khong_chay_duoc=True)
    if check and ket.rc != 0:
        raise LoiLenh("%s -> rc=%s %s" % (lenh[:3], ket.rc, (ket.err or ket.out)[-200:]))
    return ket


def _chuoi(b):
    if b is None:
        return ""
    return b.decode("utf-8", "replace") if isinstance(b, bytes) else b
