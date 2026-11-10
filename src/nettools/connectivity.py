# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi Network Tools - Ping / Traceroute (netool.io: Connectivity Test)
"""
from consolesystem.core import taisan as _taisan
import re
import subprocess

from flask import request, render_template_string

from . import nettools_bp


def _cong_mac_dinh():
    """Cong mac dinh cho o chon - cong co day that cua may nay (xem
    ui/phancung.py). Truoc day viet cung "eth0" nen chi dung tren Pi."""
    from ui.phancung import cong_mac_dinh
    return cong_mac_dinh()


def _o_chon_cong(dang_chon=""):
    """Cac the <option> liet ke dung cac cong THAT dang co tren may."""
    from ui.phancung import o_chon_cong
    return o_chon_cong(dang_chon)

# LO HONG DA VA (ra soat lai code, khong phai da gap that): truoc day
# khong kiem tra gi ca truoc khi dua "host" thang vao subprocess.run(). Vi
# goi dang list (khong shell=True) nen KHONG the chen lenh shell duoc, NHUNG
# neu "host" bat dau bang dau "-" (vd "--flood" hoac "-f") thi ping/
# traceroute co the hieu nham do la MOT CO LENH thay vi ten may - va "ping
# --flood" can quyen root de chay (ma tien trinh Flask nay CHINH LA root).
# Rui ro thuc te thap (chi admin da dang nhap moi goi duoc, va ho da co
# quyen root qua Terminal roi) nhung van nen chan cho chac, phong truong hop
# co lo hong CSRF khac khien trinh duyet cua admin tu dong gui form nay ma
# ho khong hay biet.
_MAU_HOST_HOP_LE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-:]{0,253}$")


def _host_hop_le(host):
    return bool(host) and bool(_MAU_HOST_HOP_LE.fullmatch(host))


def run_ping(host, iface=None, count=4, timeout=2):
    cmd = ["ping", "-c", str(count), "-W", str(timeout), "-I", iface, host]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=count * timeout + 10)
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "(quá thời gian chờ)"
    except Exception as e:
        return f"(lỗi: {e})"


def run_traceroute(host, iface=None, max_hops=20, timeout=2):
    cmd = ["traceroute", "-n", "-w", str(timeout), "-m", str(max_hops), "-i", iface, host]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=max_hops * timeout + 15)
        return result.stdout + result.stderr
    except FileNotFoundError:
        return "(chưa cài traceroute)"
    except subprocess.TimeoutExpired:
        return "(quá thời gian chờ)"
    except Exception as e:
        return f"(lỗi: {e})"


TOI_DA_DICH = 8


def tach_dich_day_du(chuoi):
    """'a.com, 1.1.1.1 8.8.8.8' -> (['a.com','1.1.1.1','8.8.8.8'], []) : (cac dich se chay - toi da TOI_DA_DICH, cac dich bi bo qua vi vuot gioi han). Bo dich trung."""
    tat_ca = list(dict.fromkeys(h for h in re.split(r"[\s,;]+", chuoi or "") if h))
    return tat_ca[:TOI_DA_DICH], tat_ca[TOI_DA_DICH:]


def tach_dich(chuoi):
    """Nhu tach_dich_day_du nhung chi tra cac dich se chay."""
    return tach_dich_day_du(chuoi)[0]


def ping_nhieu(dich, iface=None):
    """Ping dong thoi nhieu dich; tra ve chuoi: moi dich 1 khoi '=== host ===' kem dong tom tat mat goi (hoac lap lai ket qua day du khi chi co 1 dich)."""
    from concurrent.futures import ThreadPoolExecutor
    if len(dich) == 1:
        return run_ping(dich[0], iface=iface)
    with ThreadPoolExecutor(max_workers=len(dich)) as ex:
        kq = list(ex.map(lambda h: run_ping(h, iface=iface), dich))
    ra = []
    for h, out in zip(dich, kq):
        loss = next((d.strip() for d in out.splitlines() if "packet loss" in d), "")
        ra.append(f"=== {h} ===\n{loss}\n{out.strip()}\n" if loss else f"=== {h} ===\n{out.strip()}\n")
    return "\n".join(ra)


PING_TEMPLATE = _taisan.doc("nettools/connectivity.PING_TEMPLATE.html")


@nettools_bp.route("/nettools/ping", methods=["GET", "POST"])
def ping_route():
    host = (request.form.get("host") or "").strip()
    iface = request.form.get("iface") or _cong_mac_dinh()
    ran = request.method == "POST" and bool(host)

    che_do = request.form.get("che_do") if request.form.get("che_do") in ("ping", "traceroute") else "ca-hai"
    ping_out = trace_out = ""
    if ran:
        dich, bo_qua = tach_dich_day_du(host)
        if not dich or not all(_host_hop_le(h) for h in dich + bo_qua):
            ping_out = trace_out = ("(địa chỉ không hợp lệ - chỉ cho chữ, số và "
                                    "các dấu . - : , không được bắt đầu bằng dấu -)")
        else:
            if che_do in ("ping", "ca-hai"):
                ping_out = ping_nhieu(dich, iface=iface)
            if che_do in ("traceroute", "ca-hai"):
                trace_out = (run_traceroute(dich[0], iface=iface) if len(dich) == 1
                             else "(Traceroute chỉ chạy cho 1 đích mỗi lần - hãy nhập 1 đích, hoặc dùng Ping khi nhập nhiều đích.)")
            if bo_qua:                       # khong bo lang le: noi ro dich nao khong duoc chay
                tb = "(Chỉ chạy tối đa %d đích mỗi lần. Đã bỏ qua %d đích: %s. Hãy chạy lại với các đích này.)\n\n" % (TOI_DA_DICH, len(bo_qua), ", ".join(bo_qua))
                ping_out = tb + ping_out if ping_out else ping_out
                trace_out = tb + trace_out if trace_out else trace_out

    return render_template_string(
        PING_TEMPLATE, o_chon_cong=_o_chon_cong(iface), host=host, iface=iface, ran=ran,
        ping_out=ping_out, trace_out=trace_out, che_do=che_do,
    )


if __name__ == "__main__":
    import sys
    host = sys.argv[1] if len(sys.argv) > 1 else "8.8.8.8"
    iface = sys.argv[2] if len(sys.argv) > 2 else "eth0"
    print("=== PING ===")
    print(run_ping(host, iface=iface))
    print("=== TRACEROUTE ===")
    print(run_traceroute(host, iface=iface))
