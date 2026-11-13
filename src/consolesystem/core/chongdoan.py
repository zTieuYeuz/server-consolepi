# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Chong doan mat khau dang nhap (2.0.8 V2-1): dem that bai theo TEN dang nhap va theo IP, khoa tam co he so tang dan.
Khong ngu (sleep) trong worker; tu choi ngay kem so giay cho. Khoa chi la TAM THOI (toi da 5 phut) de khong bien thanh tu choi dich vu vinh vien.
Luu trong bo nho: khoi dong lai dich vu la xoa (chap nhan duoc)."""
import ipaddress
import threading
import time

NGUONG_TEN = 5            # that bai lien tiep truoc khi khoa tam theo ten
NGUONG_IP = 15            # tuong tu theo IP (nhieu ten khac nhau tu mot may)
CUA_SO = 900              # giay: that bai cu hon thi bi quen
KHOA_DAU = 30             # giay khoa o lan vuot nguong dau, nhan doi moi lan tiep
KHOA_TOI_DA = 300
TOI_DA_MUC = 5000         # chan bo nho phinh khi bi do ten ngau nhien

_khoa_lock = threading.Lock()
_ds = {}                  # khoa -> [so_that_bai, lan_cuoi, den_luc_khoa]


def _bo_loopback(ip):
    try:
        return ipaddress.ip_address(ip).is_loopback
    except ValueError:
        return False


def ip_khach(remote_addr, headers):
    """IP that cua khach. Qua Cloudflare Tunnel nginx chi thay 127.0.0.1; khi do (va CHI khi do) tin Cf-Connecting-Ip
    (ket noi tu LAN vao nginx co remote_addr khong phai loopback nen khong gia mao duoc)."""
    ip = ((headers.get("X-Real-IP") or remote_addr or "").strip())
    if _bo_loopback(ip):
        cf = (headers.get("Cf-Connecting-Ip") or "").strip()
        try:
            ipaddress.ip_address(cf)
            return cf
        except ValueError:
            return ip
    return ip


def _khoa_ten(ten):
    return "t:" + (ten or "").strip().lower()[:64]


def _khoa_ip(ip):
    return "i:" + (ip or "-")


def _quet(bay_gio):
    if len(_ds) <= TOI_DA_MUC:
        return
    for k in [k for k, v in _ds.items() if bay_gio - v[1] > CUA_SO and v[2] <= bay_gio]:
        del _ds[k]
    while len(_ds) > TOI_DA_MUC:                          # van day: bo muc cu nhat
        del _ds[min(_ds, key=lambda k: _ds[k][1])]


def cho_bao_lau(ten, ip, bay_gio=None):
    """So giay con phai cho (0 = duoc thu)."""
    bay_gio = time.time() if bay_gio is None else bay_gio
    with _khoa_lock:
        cho = 0
        for k in (_khoa_ten(ten), _khoa_ip(ip)):
            v = _ds.get(k)
            if v and v[2] > bay_gio:
                cho = max(cho, int(v[2] - bay_gio) + 1)
        return cho


def ghi_that_bai(ten, ip, bay_gio=None):
    bay_gio = time.time() if bay_gio is None else bay_gio
    with _khoa_lock:
        _quet(bay_gio)
        cac = [(_khoa_ten(ten), NGUONG_TEN)]
        if ip and not _bo_loopback(ip):                   # loopback = cloudflared/man hinh cuc bo, dung chung: khong dem theo IP
            cac.append((_khoa_ip(ip), NGUONG_IP))
        for k, nguong in cac:
            v = _ds.get(k)
            if not v or bay_gio - v[1] > CUA_SO:
                v = [0, bay_gio, 0]
            v[0] += 1
            v[1] = bay_gio
            if v[0] >= nguong:
                bac = v[0] - nguong                       # lan vuot nguong thu may
                v[2] = bay_gio + min(KHOA_TOI_DA, KHOA_DAU * (2 ** min(bac, 10)))
            _ds[k] = v


def ghi_thanh_cong(ten, ip=None):
    with _khoa_lock:
        _ds.pop(_khoa_ten(ten), None)
        # KHONG xoa dem theo IP: ke tan cong co tai khoan hop le van khong the dung no de xoa dau vet do doan ten khac


def xoa_het():
    with _khoa_lock:
        _ds.clear()
