# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Chong doan mat khau dang nhap (2.0.8 V2-1): dem that bai theo TEN dang nhap va theo IP, khoa tam co he so tang dan.
Khoa theo CAP (ten, IP) va theo IP; khoa theo TEN chi la lop phu (nguong cao) va KHONG chan cap (ten, IP) da tung dang nhap thanh cong, de ke ngoai biet ten khong khoa duoc nguoi that.
Giu cho (thu/xong) trong cung khoa de N yeu cau song song khong cung qua kiem tra. Khong ngu (sleep) trong worker; tu choi ngay kem so giay cho. Khoa chi la TAM THOI (toi da 5 phut) de khong bien thanh tu choi dich vu vinh vien.
Luu trong bo nho: khoi dong lai dich vu la xoa (chap nhan duoc)."""
import ipaddress
import threading
import time

NGUONG_CAP = 5            # that bai truoc khi khoa tam theo cap (ten, IP)
NGUONG_IP = 15            # theo IP (nhieu ten tu mot may)
NGUONG_TEN = 20           # theo ten tren moi IP (ke tan cong phan tan); cao hon, va cap da quen bo qua
CUA_SO = 900              # giay: that bai cu hon thi bi quen
KHOA_DAU = 30             # giay khoa o lan vuot nguong dau, nhan doi moi lan tiep
KHOA_TOI_DA = 300
HAN_QUEN = 30 * 86400     # cap (ten, IP) da dang nhap dung duoc nho chung nay
TOI_DA_MUC = 5000

_khoa_lock = threading.Lock()
_ds = {}                  # khoa -> [so_that_bai (ke ca dang thu), lan_cuoi, den_luc_khoa]
_quen = {}                # (ten, ip) -> luc dang nhap dung gan nhat


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


def _n(ten):
    return (ten or "").strip().lower()[:64]


def _cac_khoa(ten, ip):
    """[(khoa, nguong)] ap dung. Cap (ten, IP) luon co; IP chi khi la IP that (loopback dung chung -> bo); ten la lop phu."""
    ks = [("p:%s|%s" % (_n(ten), ip or "-"), NGUONG_CAP), ("t:" + _n(ten), NGUONG_TEN)]
    if ip and not _bo_loopback(ip):
        ks.append(("i:" + ip, NGUONG_IP))
    return ks


def _tin(ten, ip, bay_gio):
    """Cap (ten, IP) da dang nhap dung gan day (chi IP that moi duoc nho)."""
    if not ip or _bo_loopback(ip):
        return False
    t = _quen.get((_n(ten), ip))
    return bool(t and bay_gio - t < HAN_QUEN)


def _quet(bay_gio):
    if len(_ds) > TOI_DA_MUC:
        for k in [k for k, v in _ds.items() if bay_gio - v[1] > CUA_SO and v[2] <= bay_gio]:
            del _ds[k]
        while len(_ds) > TOI_DA_MUC:
            del _ds[min(_ds, key=lambda k: _ds[k][1])]
    if len(_quen) > TOI_DA_MUC:
        for k in sorted(_quen, key=_quen.get)[:len(_quen) - TOI_DA_MUC]:
            del _quen[k]


def thu(ten, ip, bay_gio=None):
    """Xin phep thu mot mat khau. Tra (so_giay_cho, the). cho > 0: bi khoa, KHONG duoc goi PAM. Neu duoc phep, lan thu da duoc TINH la mot that bai
    (giu cho nguyen tu trong cung khoa) -> N yeu cau song song khong cung qua; goi xong(the, ...) de hoan lai khi dung/loi he thong."""
    bay_gio = time.time() if bay_gio is None else bay_gio
    tin = None
    with _khoa_lock:
        tin = _tin(ten, ip, bay_gio)
        _quet(bay_gio)
        cho = 0
        ks = _cac_khoa(ten, ip)
        for k, _ng in ks:
            if tin and k.startswith("t:"):
                continue                                       # cap da quen: khong bi khoa vi ke khac do ten
            v = _ds.get(k)
            if v and v[2] > bay_gio:
                cho = max(cho, int(v[2] - bay_gio) + 1)
        if cho:
            return cho, None
        da = []
        for k, ng in ks:
            v = _ds.get(k)
            if not v or bay_gio - v[1] > CUA_SO:
                v = [0, bay_gio, 0]
            v[0] += 1
            v[1] = bay_gio
            if v[0] >= ng:
                v[2] = bay_gio + min(KHOA_TOI_DA, KHOA_DAU * (2 ** min(v[0] - ng, 10)))
            _ds[k] = v
            da.append((k, ng))
        return 0, (ten, ip, da)


def xong(the, ket_qua, bay_gio=None):
    """ket_qua: 'dung' (hoan lai cho + nho cap (ten, IP)), 'loi' (loi he thong, khong tinh la doan: hoan lai), 'sai' (giu la that bai)."""
    if not the or ket_qua == "sai":
        return
    bay_gio = time.time() if bay_gio is None else bay_gio
    ten, ip, da = the
    with _khoa_lock:
        for k, ng in da:
            v = _ds.get(k)
            if not v:
                continue
            if ket_qua == "dung" and k.startswith("p:"):
                del _ds[k]                                     # dang nhap dung: xoa bo dem cua cap
                continue
            v[0] = max(0, v[0] - 1)
            if v[0] < ng:
                v[2] = 0
        if ket_qua == "dung" and ip and not _bo_loopback(ip):
            _quen[(_n(ten), ip)] = bay_gio


def xoa_het():
    with _khoa_lock:
        _ds.clear()
        _quen.clear()
