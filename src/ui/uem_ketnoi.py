# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Quan ly may tram - DIEM KET NOI DUY NHAT toi 1 may Windows. Moi noi can chay PowerShell tren may goi ket_noi(m):
  1. May co AGENT dang song (vua bao nhip) -> chay qua hang doi viec cua agent (khong can mo WinRM, qua duoc mang con / duong ham)
  2. Khong thi WinRM bang tai khoan quan tri da gan (khoi tao 'tai_khoan_id').
Tra ve (client, mat_khau, loai). client co execute_ps(script) -> (out, streams, loi) giong pypsrp de cac ham cu dung duoc.
"""
from . import tk_dongco as DC
from . import tk_dulieu as DL


class LoiMay(Exception):
    """Khong vao duoc may - thong diep tieng Viet de hien thang cho nguoi dung."""


def co_agent(m):
    try:
        from . import uem_agent as UA
    except ImportError:
        return False
    return UA.con_song(m)


def co_the_ket_noi(m):
    """May co cach nao de vao khong (agent con song hoac da gan tai khoan)."""
    return bool(m.get("tai_khoan_id")) or co_agent(m)


def ket_noi(m, bat_buoc_winrm=False):
    """(client, mat_khau, loai) hoac raise LoiMay."""
    if not bat_buoc_winrm and co_agent(m):
        from . import uem_agent as UA
        return UA.Client(m["id"]), "", "agent"
    user, mk = DL.lay_tai_khoan(m.get("tai_khoan_id"))
    if user is None:
        raise LoiMay("Máy chưa gán tài khoản quản trị và chưa có agent đang chạy (tab Quản lý hoặc tab Agent).")
    if not DC.cong_mo(m["ip"], 5985, 3.0):
        raise LoiMay("Máy tắt, mất mạng hoặc chưa bật WinRM (cổng 5985 đóng).")
    try:
        return DC._ket_noi(m["ip"], user, mk), mk, "winrm"
    except DC.LoiKetNoi as e:
        raise LoiMay(str(e))
    except Exception as e:
        raise LoiMay(DC._loi_dep(e, mk))
