# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi Network Tools - Kiem tra DNS toan dien

Truy van MOT ten mien qua nhieu DNS server cung luc (DNS he thong hien tai +
3 DNS cong khai lon), do thoi gian phan hoi va doi chieu ket qua tra ve. Neu
DNS he thong tra ve dia chi KHAC HAN voi cac DNS cong khai, day la dau hieu
manh cua DNS bi can thiep - ISP chen quang cao, mang cong ty loc/chan domain,
hoac captive portal dang chuyen huong ngam.

KY THUAT: dung lop DNS/DNSQR cua scapy de DUNG GOI TIN (khong can quyen
root), nhung gui/nhan qua socket UDP THUONG (socket.SOCK_DGRAM) thay vi
scapy sr1()/send() - sr1() can raw socket (CAP_NET_RAW), trong khi mot truy
van UDP/53 binh thuong chi can socket UDP don gian. Cach nay nhanh hon va
khong phu thuoc quyen root, du dashboard nay dang chay duoi quyen root cho
cac cong cu khac (DHCP, ARP scan...) can raw socket that su.

DA KIEM CHUNG TREN MAY THAT: mot may co nhieu duong ra Internet (vi du eth0
+ wlan0) co the co tuyen duong dac biet cho MOT dia chi cu the (da gap that:
mot router WiFi cap rieng tuyen cho dung 8.8.8.8) khien truy van toi dia chi
do bi day nham cong va timeout, trong khi cac DNS server khac van binh
thuong. Vi vay ket qua LUON hien theo TUNG SERVER rieng le - mot server loi
khong duoc lam mat ket qua cua cac server con lai.
"""
from consolesystem.core import taisan as _taisan
from consolesystem.core.nhatky import bo_qua as _bo_qua
import re
import socket
import time

from flask import request, render_template_string

from . import nettools_bp

MAY_CHU_CO_DINH = [
    ("Google", "8.8.8.8"),
    ("Cloudflare", "1.1.1.1"),
    ("Quad9", "9.9.9.9"),
]


def _dns_he_thong():
    """Doc nameserver dau tien trong /etc/resolv.conf - DNS Pi dang dung that su."""
    try:
        with open("/etc/resolv.conf") as f:
            for line in f:
                line = line.strip()
                if line.startswith("nameserver"):
                    return line.split()[1]
    except Exception as _loi:
        _bo_qua(_loi)
    return None


def _truy_van_mot_server(server, domain, timeout):
    """
    Gui 1 truy van DNS type-A toi dung 1 server, tra ve
    (thoi_gian_ms, [dia_chi_ipv4], loi|None).
    """
    from scapy.all import DNS, DNSQR

    pkt = DNS(rd=1, qd=DNSQR(qname=domain, qtype="A"))
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    t0 = time.perf_counter()
    try:
        s.sendto(bytes(pkt), (server, 53))
        data, _ = s.recvfrom(4096)
    except socket.timeout:
        return None, [], f"Không phản hồi trong {timeout}s"
    except OSError as e:
        return None, [], str(e)
    finally:
        s.close()
    thoi_gian_ms = round((time.perf_counter() - t0) * 1000, 1)

    try:
        resp = DNS(data)
    except Exception as e:
        return thoi_gian_ms, [], f"Không đọc được phản hồi: {e}"

    if resp.rcode != 0:
        ten_loi = {1: "loi dinh dang", 2: "loi server", 3: "khong ton tai (NXDOMAIN)",
                  5: "bi tu choi (REFUSED)"}.get(int(resp.rcode), f"ma loi {resp.rcode}")
        return thoi_gian_ms, [], f"DNS server trả về: {ten_loi}"

    dia_chi = []
    for i in range(resp.ancount):
        rr = resp.an[i] if resp.ancount > 1 else resp.an
        if getattr(rr, "type", None) == 1:  # type 1 = A record
            dia_chi.append(rr.rdata)
    return thoi_gian_ms, dia_chi, None


def kiem_tra_dns(domain, timeout=3):
    """
    Tra ve {"ok", "error", "domain", "servers": [...], "co_mau_thuan": bool,
            "canh_bao": str|None}
    """
    domain = (domain or "").strip().rstrip(".")
    if not domain or not re.fullmatch(r"[A-Za-z0-9]([A-Za-z0-9\-.]{0,251}[A-Za-z0-9])?", domain):
        return {"ok": False, "error": "Tên miền không hợp lệ.", "domain": domain,
                "servers": [], "co_mau_thuan": False, "canh_bao": None}

    danh_sach = []
    dns_he_thong_ip = _dns_he_thong()
    if dns_he_thong_ip:
        danh_sach.append(("Hệ thống hiện tại", dns_he_thong_ip))
    danh_sach += MAY_CHU_CO_DINH

    ket_qua = []
    for ten, ip in danh_sach:
        thoi_gian, dia_chi, loi = _truy_van_mot_server(ip, domain, timeout)
        ket_qua.append({"ten": ten, "ip": ip, "thoi_gian_ms": thoi_gian,
                        "dia_chi": dia_chi, "loi": loi})

    # So sanh cac tap ket qua KHONG RONG voi nhau - mot server loi/timeout
    # khong tinh vao so sanh (khong the noi la "mau thuan" khi mot ben
    # khong tra loi gi ca).
    #
    # Chi coi la mau thuan khi co mot cap server tra ve hai tap IP KHONG CO
    # IP NAO CHUNG. LOI THAT (thu ban ISO 23/09/2026): debian.org - DNS he
    # thong tra 1 IP, Google/Cloudflare/Quad9 tra 4 IP trong do CO CHINH IP
    # do (resolver cat bot/xoay vong) -> cong cu van hien canh bao do "DNS
    # bi can thiep". DNS bi chen/chan that thi tra IP khac han, khong trung.
    cac_tap = [frozenset(r["dia_chi"]) for r in ket_qua if r["dia_chi"]]
    co_mau_thuan = any(not (a & b) for i, a in enumerate(cac_tap)
                       for b in cac_tap[i + 1:])

    canh_bao = None
    if co_mau_thuan:
        canh_bao = (
            "Co DNS server tra ve DIA CHI KHAC HAN (khong trung IP nao) cho cung 1 ten mien. Voi domain rieng/noi "
            "bo, day la dau hieu manh cua DNS bi can thiep (ISP chen quang cao, mang cong ty "
            "loc/chan, hoac captive portal). Luu y: voi cac trang lon dung CDN toan cau (Google, "
            "Facebook, Cloudflare...) thi lech ket qua theo VI TRI DIA LY la BINH THUONG, khong "
            "phai dau hieu xau - hay thu lai voi mot domain rieng/it dung CDN de ket luan chac chan hon."
        )

    return {"ok": True, "error": None, "domain": domain, "servers": ket_qua,
            "co_mau_thuan": co_mau_thuan, "canh_bao": canh_bao}


DNS_TEMPLATE = _taisan.doc("nettools/dns_check.DNS_TEMPLATE.html")


@nettools_bp.route("/nettools/dns-check", methods=["GET", "POST"])
def dns_check_route():
    domain = request.form.get("domain", "").strip()
    ran = request.method == "POST"
    result = kiem_tra_dns(domain) if ran else None
    return render_template_string(DNS_TEMPLATE, domain=domain, ran=ran, result=result)


if __name__ == "__main__":
    import sys
    import json
    domain = sys.argv[1] if len(sys.argv) > 1 else "google.com"
    print(json.dumps(kiem_tra_dns(domain), indent=2, ensure_ascii=False))
