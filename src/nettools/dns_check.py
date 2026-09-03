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
    except Exception:
        pass
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
        return None, [], f"Khong phan hoi trong {timeout}s"
    except OSError as e:
        return None, [], str(e)
    finally:
        s.close()
    thoi_gian_ms = round((time.perf_counter() - t0) * 1000, 1)

    try:
        resp = DNS(data)
    except Exception as e:
        return thoi_gian_ms, [], f"Khong doc duoc phan hoi: {e}"

    if resp.rcode != 0:
        ten_loi = {1: "loi dinh dang", 2: "loi server", 3: "khong ton tai (NXDOMAIN)",
                  5: "bi tu choi (REFUSED)"}.get(int(resp.rcode), f"ma loi {resp.rcode}")
        return thoi_gian_ms, [], f"DNS server tra ve: {ten_loi}"

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
        return {"ok": False, "error": "Ten mien khong hop le.", "domain": domain,
                "servers": [], "co_mau_thuan": False, "canh_bao": None}

    danh_sach = []
    dns_he_thong_ip = _dns_he_thong()
    if dns_he_thong_ip:
        danh_sach.append((f"He thong hien tai", dns_he_thong_ip))
    danh_sach += MAY_CHU_CO_DINH

    ket_qua = []
    for ten, ip in danh_sach:
        thoi_gian, dia_chi, loi = _truy_van_mot_server(ip, domain, timeout)
        ket_qua.append({"ten": ten, "ip": ip, "thoi_gian_ms": thoi_gian,
                        "dia_chi": dia_chi, "loi": loi})

    # So sanh cac tap ket qua KHONG RONG voi nhau - mot server loi/timeout
    # khong tinh vao so sanh (khong the noi la "mau thuan" khi mot ben
    # khong tra loi gi ca).
    cac_tap = {frozenset(r["dia_chi"]) for r in ket_qua if r["dia_chi"]}
    co_mau_thuan = len(cac_tap) > 1

    canh_bao = None
    if co_mau_thuan:
        canh_bao = (
            "Cac DNS server tra ve DIA CHI KHAC NHAU cho cung 1 ten mien. Voi domain rieng/noi "
            "bo, day la dau hieu manh cua DNS bi can thiep (ISP chen quang cao, mang cong ty "
            "loc/chan, hoac captive portal). Luu y: voi cac trang lon dung CDN toan cau (Google, "
            "Facebook, Cloudflare...) thi lech ket qua theo VI TRI DIA LY la BINH THUONG, khong "
            "phai dau hieu xau - hay thu lai voi mot domain rieng/it dung CDN de ket luan chac chan hon."
        )

    return {"ok": True, "error": None, "domain": domain, "servers": ket_qua,
            "co_mau_thuan": co_mau_thuan, "canh_bao": canh_bao}


DNS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Kiem tra DNS - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: #eee; padding: 20px; }
        h1 { color: #4CAF50; } h3 { color: #4CAF50; margin-top: 22px; }
        a { color: #4CAF50; }
        input[type=text] { padding: 8px; background: #333; color: #eee; border: 1px solid #555; }
        button { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 12px; }
        th, td { padding: 9px 10px; text-align: left; border-bottom: 1px solid #444; vertical-align: top; }
        th { background: #2d2d2d; }
        .card { background:#262626; border:1px solid #3a3a3a; border-left:4px solid #4CAF50;
                border-radius:6px; padding:14px 16px; margin-top:16px; }
        .err { background: #4a2d2d; border-left: 4px solid #f44336; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .warn { background: #4a3d1a; border-left: 4px solid #ffb74d; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .ok-txt { color: #8fd99a; } .bad-txt { color: #ff8a8a; }
        .hint { color: #999; font-size: 13px; }
        code.small { font-size:12px; color:#aaa; }
    </style>
</head>
<body>
    <h1>🌐 Kiem tra DNS</h1>
    <p><a href="/nettools">← Network Tools</a></p>
    <p class="hint">Truy van cung 1 ten mien toi DNS he thong hien tai va 3 DNS cong khai lon,
    doi chieu ket qua. DNS he thong tra ve khac han cac DNS cong khai la dau hieu bi can thiep
    (ISP chen quang cao, mang cong ty loc, captive portal).</p>

    <form method="POST" style="margin-top:16px;">
        <label>Ten mien:</label>
        <input type="text" name="domain" value="{{ domain or '' }}" placeholder="vd google.com" required>
        <button type="submit" style="margin-left:10px;" data-busy="Dang truy van...">Kiem tra</button>
    </form>

    {% if ran %}
        {% if not result.ok %}
        <div class="err">{{ result.error }}</div>
        {% else %}
        {% if result.canh_bao %}<div class="warn">⚠️ {{ result.canh_bao }}</div>{% endif %}
        <div class="card">
            <table style="margin:0;">
                <tr><th>DNS Server</th><th>Thoi gian</th><th>Dia chi tra ve</th></tr>
                {% for s in result.servers %}
                <tr>
                    <td>{{ s.ten }}<br><code class="small">{{ s.ip }}</code></td>
                    <td>{% if s.thoi_gian_ms %}{{ s.thoi_gian_ms }} ms{% else %}—{% endif %}</td>
                    <td>
                        {% if s.dia_chi %}
                            {% for ip in s.dia_chi %}<code>{{ ip }}</code><br>{% endfor %}
                        {% elif s.loi %}
                            <span class="bad-txt">✘ {{ s.loi }}</span>
                        {% else %}—{% endif %}
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
        {% if not result.co_mau_thuan %}
        <p class="ok-txt" style="margin-top:11px;">✔ Tat ca DNS server co ket qua tra ve deu khop nhau (hoac khong du du lieu de so sanh).</p>
        {% endif %}
        {% endif %}
    {% endif %}
</body>
</html>
"""


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
