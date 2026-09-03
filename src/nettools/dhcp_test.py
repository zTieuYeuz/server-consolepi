"""
Console Pi Network Tools - DHCP Testing (netool.io Phan 2)

Gui DHCPDISCOVER bang Scapy, bat DHCPOFFER de xem thong tin DHCP server
tra ve. Mac dinh CHI DUNG O OFFER, KHONG gui DHCPREQUEST - khong tieu ton
lease thuc su, an toan de chay nhieu lan lien tuc.

TUY CHON "kiem tra ra Internet": neu nguoi dung chu dong tick chon, cong cu
se di THEM mot buoc nua - hoan tat bat tay DHCP that su (REQUEST/ACK), tam
gan IP do vao cong mang, roi ping 8.8.8.8 / ping google.com / mo thu web
(port 80 va 443) DUNG QUA CHINH DUONG MANG DO. Xong viec thi TRA LAI moi
thu ve nguyen trang - khong dung IP quan ly hien co cua Pi tren cong nay.

Day la buoc "tieu ton mot lease that" nen luon la TUY CHON, khong tu dong -
giu dung tinh than "an toan chay nhieu lan" cua ban DISCOVER-only ban dau,
chi ai chu dong can moi bat.

Can quyen root (raw socket, sua bang dinh tuyen) - hoat dong binh thuong khi
chay qua web vi console-pi-dashboard.service chay duoi quyen root.
"""
import random
import re
import subprocess
import time

from flask import request, render_template_string

from . import nettools_bp

# Bang dinh tuyen + do uu tien rule rieng cho buoc test Internet, khong dung
# chung voi bat ky gi khac tren may (da kiem tra: may nay chi co 3 rule mac
# dinh cua kernel - 0/32766/32767). Chon so xa cac gia tri do de khong dam.
_TEST_TABLE = 199
_TEST_RULE_PRIO = 199

# Hai trang dung de kiem tra web that su (khong chi ping):
#   - example.com (port 80, HTTP thuan)  : do IANA duy tri, khong quang cao,
#     khong redirect, rat on dinh lau dai - hop de phat hien captive portal
#     (mang chan bang trang dang nhap se tra ve noi dung/redirect khac hoan
#     toan noi dung mong doi)
#   - www.google.com (port 443, HTTPS)   : kiem tra ca TLS handshake, uptime
#     toan cau rat cao
WEB_CHECKS = [("http://example.com", 80), ("https://www.google.com", 443)]


def run_dhcp_test(iface="eth0", timeout=5, test_internet=False):
    """
    Tra ve {"ok": bool, "error": str|None, "offers": [...], "internet": {...}|None}

    LUU Y KY THUAT: dung sniff() + sendp() rieng biet thay vi srp(), vi
    srp() tu ghep cap request/response bang IP.answers() - co logic khong
    phu hop voi DHCP (goi OFFER tra tu server IP khac, dia chi broadcast,
    khien srp() bo sot OFFER that du no da toi noi). sniff() bat moi goi
    UDP port 68 trong khoang thoi gian cho, khong phu thuoc logic ghep cap.

    TU GUI LAI DISCOVER NHIEU LAN (quan trong voi wlan0): da kiem chung
    thuc te tren chinh may nay - DHCPDISCOVER va DHCPOFFER deu la goi tin
    BROADCAST, va broadcast tren 802.11 KHONG co ACK/retry o tang lien ket
    (khac han unicast). Mot lan gui duy nhat co the mat hoan toan du router
    hoan toan khoe manh - da kiem chung bang doi chieu voi `nmap
    --script broadcast-dhcp-discover` va tcpdump doc lap: cung mot noi dung
    goi tin, cung mot router, co lan nhan duoc OFFER co lan khong, hoan toan
    ngau nhien - khong phai do sai dinh dang goi tin (da thu doi MAC that/
    gia, doi TTL, them Parameter-Request-List, dem toi 300+ byte deu khong
    lam thay doi ket qua mot cach on dinh). Day chinh la ly do RFC 2131 quy
    dinh client PHAI tu gui lai DISCOVER neu chua thay OFFER - khong phai
    tra loi mot lan la xong. Tren eth0 hau nhu luon thanh cong tu lan dau vi
    Ethernet co dinh khong co van de mat goi broadcast nay.
    """
    try:
        from scapy.all import (
            Ether, IP, UDP, BOOTP, DHCP, sendp, AsyncSniffer,
            get_if_hwaddr, mac2str, conf,
        )
    except ImportError as e:
        return {"ok": False, "error": f"Loi import scapy: {e}", "offers": [], "internet": None}

    conf.verb = 0

    try:
        hw_str = get_if_hwaddr(iface)
        hw = mac2str(hw_str)
    except Exception as e:
        return {"ok": False, "error": f"Khong lay duoc MAC cua {iface}: {e}", "offers": [], "internet": None}

    xid = random.randint(1, 0xFFFFFFFF)
    pkt = (
        # BAT BUOC ghi ro src=hw_str: neu bo trong, scapy tu dien MAC theo
        # conf.iface (interface MAC DINH cua scapy, thuong la interface dau
        # tien no thay - KHONG chac chan la cung `iface` dang test). Da gap
        # loi that: tren wlan0, Ethernet src tu dien lai la MAC cua eth0,
        # trong khi BOOTP chaddr van dung la MAC cua wlan0 - hai dia chi mau
        # thuan nhau trong cung mot goi. Router (dac biet AP WiFi co kiem
        # tra chat) coi day la dau hieu gia mao va IM LANG khong tra loi,
        # du goi tin van roi khoi day binh thuong (khong bao loi gi ca, nen
        # rat kho phat hien neu khong doi chieu tung byte tren day).
        Ether(src=hw_str, dst="ff:ff:ff:ff:ff:ff") /
        IP(src="0.0.0.0", dst="255.255.255.255") /
        UDP(sport=68, dport=67) /
        BOOTP(chaddr=hw, xid=xid, flags=0x8000) /
        DHCP(options=[("message-type", "discover"), "end"])
    )

    # So lan gui lai va khoang cach giua cac lan - du de "trung" duoc it
    # nhat mot cua so khong bi mat goi tren broadcast WiFi, ma van tra loi
    # trong thoi gian hop ly cho nguoi dung bam nut cho.
    SO_LAN_GUI = 3
    KHOANG_CACH = max(1.0, timeout / SO_LAN_GUI)

    captured = []
    sniffer = AsyncSniffer(
        iface=iface, filter="udp and port 68", store=True,
        prn=lambda p: captured.append(p),
    )
    try:
        sniffer.start()
        time.sleep(0.3)  # dam bao sniffer da san sang truoc khi gui
        # Gui du ca 3 lan va doi du thoi gian, KHONG dung som khi thay 1
        # OFFER: co nhieu DHCP server tra loi la dau hieu huu ich (nghi ngo
        # rogue DHCP), dung som se bo lo cac OFFER den tre hon.
        for _ in range(SO_LAN_GUI):
            sendp(pkt, iface=iface, verbose=0)
            time.sleep(KHOANG_CACH)
    except PermissionError:
        sniffer.stop()
        return {"ok": False, "error": "Khong du quyen mo raw socket (can chay duoi quyen root).",
                "offers": [], "internet": None}
    except OSError as e:
        sniffer.stop()
        return {"ok": False, "error": f"Loi khi gui goi tin: {e}", "offers": [], "internet": None}
    else:
        sniffer.stop()

    # Gui lai toi 3 lan (o tren) co nghia la MOT server that su co the tra
    # loi nhieu lan - phai gop trung theo (server_id, offered_ip) truoc khi
    # hien, neu khong se bao nham "nhieu DHCP server" (canh bao rogue DHCP
    # gia) chi vi chinh server do da tra loi hon 1 lan cho cac lan gui lai.
    offers = []
    da_thay = set()
    for recv in captured:
        if not recv.haslayer(DHCP) or not recv.haslayer(BOOTP):
            continue
        if recv[BOOTP].xid != xid:
            continue  # bo qua goi cua phien DHCP khac dang chay tren cung day
        opts = {k: v for k, v in
                ((o[0], o[1]) for o in recv[DHCP].options if isinstance(o, tuple))}
        if opts.get("message-type") != 2:  # 2 = DHCPOFFER
            continue
        khoa = (opts.get("server_id", "?"), recv[BOOTP].yiaddr)
        if khoa in da_thay:
            continue
        da_thay.add(khoa)
        offers.append({
            "offered_ip": recv[BOOTP].yiaddr,
            "server_id": opts.get("server_id", "?"),
            "subnet_mask": opts.get("subnet_mask", "?"),
            "router": opts.get("router", "?"),
            "name_server": opts.get("name_server", "?"),
            "lease_time": opts.get("lease_time", "?"),
        })

    internet_result = None
    if test_internet and offers:
        internet_result = _test_internet_qua_dhcp(iface, xid, offers[0], hw)

    return {"ok": True, "error": None, "offers": offers, "internet": internet_result}


def _mask_to_prefixlen(mask):
    """'255.255.255.0' -> 24. Tra ve None neu khong hop le."""
    try:
        parts = [int(x) for x in str(mask).split(".")]
        if len(parts) != 4:
            return None
        bits = "".join(f"{p:08b}" for p in parts)
        if "01" in bits:  # mask khong hop le (co lo hong bit 0 xen giua)
            return None
        return bits.count("1")
    except Exception:
        return None


def _dhcp_request_ack(iface, xid, offer, hw, timeout=5):
    """
    Hoan tat buoc REQUEST/ACK - CHI goi khi nguoi dung chu dong muon test
    Internet. Day la buoc THAT SU xin lease, khac voi DISCOVER/OFFER o tren.

    Tra ve (ok, ip, mask, gw, dns, loi).
    """
    from scapy.all import Ether, IP, UDP, BOOTP, DHCP, sendp, AsyncSniffer, conf
    conf.verb = 0

    # hw la bytes (tu mac2str) - doi nguoc lai thanh chuoi "aa:bb:.." de dat
    # cho Ether src. Phai KHOP voi chaddr, cung ly do da giai thich trong
    # run_dhcp_test() o tren: lech nhau la bi router im lang tu choi.
    hw_str_lai = ":".join(f"{b:02x}" for b in hw)

    pkt = (
        Ether(src=hw_str_lai, dst="ff:ff:ff:ff:ff:ff") /
        IP(src="0.0.0.0", dst="255.255.255.255") /
        UDP(sport=68, dport=67) /
        BOOTP(chaddr=hw, xid=xid, flags=0x8000) /
        DHCP(options=[
            ("message-type", "request"),
            ("requested_addr", offer["offered_ip"]),
            ("server_id", offer["server_id"]),
            "end",
        ])
    )

    captured = []
    sniffer = AsyncSniffer(iface=iface, filter="udp and port 68", store=True,
                           prn=lambda p: captured.append(p))
    try:
        sniffer.start()
        time.sleep(0.3)
        sendp(pkt, iface=iface, verbose=0)
        time.sleep(timeout)
    finally:
        sniffer.stop()

    for recv in captured:
        if not recv.haslayer(DHCP) or not recv.haslayer(BOOTP):
            continue
        if recv[BOOTP].xid != xid:
            continue
        opts = {k: v for k, v in
                ((o[0], o[1]) for o in recv[DHCP].options if isinstance(o, tuple))}
        mtype = opts.get("message-type")
        if mtype == 6:  # DHCPNAK
            return False, None, None, None, None, "DHCP server tu choi (NAK) - offer co the da het han."
        if mtype != 5:  # 5 = DHCPACK
            continue
        ip = recv[BOOTP].yiaddr
        mask = opts.get("subnet_mask", offer.get("subnet_mask"))
        gw = opts.get("router", offer.get("router"))
        dns = opts.get("name_server", offer.get("name_server"))
        return True, ip, mask, gw, dns, None

    return False, None, None, None, None, "Khong nhan duoc DHCPACK trong thoi gian cho."


def _dia_chi_hien_co_tren_cong(iface):
    """Danh sach dia chi IPv4 dang co san tren cong (khong tinh IP ta sap tu them)."""
    try:
        out = subprocess.run(["ip", "-4", "-o", "addr", "show", "dev", iface],
                             capture_output=True, text=True, timeout=6).stdout
    except Exception:
        return set()
    return set(re.findall(r"inet (\d+\.\d+\.\d+\.\d+)/", out))


def _test_internet_qua_dhcp(iface, xid, offer, hw):
    """
    Xin that mot lease (REQUEST/ACK), gan tam vao cong (KHONG dung/xoa IP
    quan ly hien co - chi them dia chi PHU), dinh tuyen rieng theo dia chi
    nguon bang policy routing (bang/ip-rule rieng), roi kiem tra Internet
    DUNG QUA DUONG MANG DO. Don sach toan bo trong finally, du thanh cong
    hay loi giua chung.

    TRUONG HOP HAY GAP (khong phai loi): neu cong dang test la CHINH cong
    Pi da co IP tu truoc (vi du eth0 dang la duong quan tri), DHCP server
    thuong tra lai DUNG dia chi hien tai cho cung MAC do (RFC 2131 muc 4.3.1
    - server uu tien cap lai lease cu neu con hop le cho client da biet).
    Luc do KHONG can `ip addr add` gi ca (IP da co san tren cong).

    NHUNG VAN PHAI thiet lap dinh tuyen rieng (policy routing) CA TRONG
    TRUONG HOP NAY. Da gap loi that: may co nhieu cong ra Internet (vi du
    eth0 la LAN chinh, wlan0 la WiFi), va router WiFi cap mot tuyen duong
    RIENG cho dung 8.8.8.8 di qua wlan0 (kieu "classless static route" hoc
    tuong tu). Tuyen duong danh rieng cho MOT dia chi luon duoc uu tien hon
    default route bat ke metric, nen `ping -I <ip_eth0> 8.8.8.8` bi kernel
    day nham qua wlan0 - goi tin mang dia chi nguon cua eth0 nhung lai di ra
    tu cong wlan0, bi loai bo giua duong (sai subnet nguon). Ket qua: ping
    8.8.8.8 bao mat 100% goi tin, trong khi ping google.com (IP khac, khong
    dinh tuyen dac biet) van thanh cong binh thuong - de gay hieu lam la loi
    mang that, trong khi mang hoan toan on.

    Dinh tuyen rieng (ip rule uu tien theo dia chi NGUON, danh gia truoc ca
    bang main) giai quyet dut diem: moi goi tin nguon tu {ip} deu bi ep di
    dung qua {iface}/{gw}, bo qua hoan toan moi tuyen duong dac biet nam
    trong bang main - bat ke dich la 8.8.8.8 hay bat ky dia chi nao khac.
    """
    ket_qua = {"lease_ok": False, "loi": None, "ip": None, "gw": None,
              "ping_8888": None, "ping_google": None, "web": []}

    ok, ip, mask, gw, dns, loi = _dhcp_request_ack(iface, xid, offer, hw)
    if not ok:
        ket_qua["loi"] = loi
        return ket_qua

    prefix = _mask_to_prefixlen(mask)
    if prefix is None or not gw or gw == "?":
        ket_qua["loi"] = (f"Nhan duoc IP {ip} nhung thieu subnet mask hoac gateway hop le "
                          f"(mask={mask}, gateway={gw}) - khong the dinh tuyen de test.")
        return ket_qua

    da_co_san = ip in _dia_chi_hien_co_tren_cong(iface)
    da_them_ip = False
    da_them_dinh_tuyen = False

    try:
        if not da_co_san:
            # 1) Them IP nay nhu dia chi PHU tren cong - KHONG dong cham gi
            # den dia chi/duong dan hien co cua Pi.
            r = subprocess.run(["ip", "addr", "add", f"{ip}/{prefix}", "dev", iface],
                               capture_output=True, text=True, timeout=8)
            # Cac ban iproute2 khac nhau bao loi trung dia chi bang chu khac
            # nhau ("File exists" hoac "Address already assigned") - da gap
            # ca hai tren thuc te, nen kiem tra ca hai truoc khi coi la loi that.
            trung_dia_chi = ("File exists" in r.stderr or "already assigned" in r.stderr)
            if r.returncode != 0 and not trung_dia_chi:
                ket_qua["loi"] = f"Khong gan duoc IP tam: {r.stderr.strip()[:150]}"
                return ket_qua
            da_them_ip = not trung_dia_chi

        # 2) LUON LUON thiet lap dinh tuyen rieng theo dia chi NGUON, ke ca
        # khi IP da co san tren cong (xem giai thich dai o docstring: neu
        # khong co buoc nay, mot tuyen duong dac biet nam san trong bang
        # main - vi du router WiFi cap rieng cho 8.8.8.8 - co the danh cuop
        # goi tin sang cong khac va lam sai lech ket qua test mot cach kho
        # hieu). ip rule uu tien 199 duoc kiem truoc ca bang main (32766)
        # nen chan dut moi tuyen duong dac biet do truoc khi no kip anh huong.
        subprocess.run(["ip", "route", "flush", "table", str(_TEST_TABLE)],
                       capture_output=True, timeout=8)
        subprocess.run(["ip", "route", "add", f"{ip}/{prefix}", "dev", iface,
                        "src", ip, "table", str(_TEST_TABLE)],
                       capture_output=True, timeout=8)
        subprocess.run(["ip", "route", "add", "default", "via", gw, "dev", iface,
                        "src", ip, "table", str(_TEST_TABLE)],
                       capture_output=True, timeout=8)
        subprocess.run(["ip", "rule", "del", "priority", str(_TEST_RULE_PRIO)],
                       capture_output=True, timeout=8)  # xoa rule cu neu con sot
        r = subprocess.run(["ip", "rule", "add", "from", ip, "table", str(_TEST_TABLE),
                            "priority", str(_TEST_RULE_PRIO)],
                           capture_output=True, text=True, timeout=8)
        da_them_dinh_tuyen = (r.returncode == 0)

        # Chi bay gio moi coi la "san sang de kiem tra that su".
        ket_qua.update(lease_ok=True, ip=ip, gw=gw)

        # 3) Ping thang IP 8.8.8.8 - kiem tra Internet o muc co ban nhat,
        # khong phu thuoc DNS.
        r = subprocess.run(["ping", "-I", ip, "-c", "3", "-W", "2", "8.8.8.8"],
                           capture_output=True, text=True, timeout=12)
        m = re.search(r"(\d+)% packet loss", r.stdout)
        mat = int(m.group(1)) if m else 100
        ket_qua["ping_8888"] = {"ok": mat < 100, "mat_goi_pct": mat,
                                "chi_tiet": r.stdout.strip().splitlines()[-2:]}

        # 4) Ping ten mien - kiem tra ca phan giai DNS (dung DNS hien tai cua
        # Pi de phan giai ten, roi di ra qua duong mang moi test).
        r = subprocess.run(["ping", "-I", ip, "-c", "3", "-W", "2", "google.com"],
                           capture_output=True, text=True, timeout=12)
        m = re.search(r"(\d+)% packet loss", r.stdout)
        mat = int(m.group(1)) if m is not None else 100
        ip_phan_giai = ""
        m2 = re.search(r"PING \S+ \(([\d.]+)\)", r.stdout)
        if m2:
            ip_phan_giai = m2.group(1)
        loi_dns = "Khong phan giai duoc ten mien (loi DNS)" if "Name or service not known" in r.stderr else None
        ket_qua["ping_google"] = {"ok": mat < 100 and not loi_dns, "mat_goi_pct": mat,
                                  "ip_phan_giai": ip_phan_giai, "loi": loi_dns}

        # 5) Mo web that su tren 2 cong - kiem tra TCP connect + HTTP(S)
        # thuc su tra ve noi dung, khong chi ping duoc.
        for url, port in WEB_CHECKS:
            r = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-m", "6", "--interface", ip,
                 "-w", "%{http_code} %{time_total} %{scheme}", url],
                capture_output=True, text=True, timeout=8)
            parts = (r.stdout or "").split()
            code = parts[0] if len(parts) > 0 else "000"
            giay = parts[1] if len(parts) > 1 else "?"
            ket_qua["web"].append({
                "url": url, "port": port, "http_code": code,
                "ok": code not in ("000", ""), "thoi_gian_s": giay,
            })

    except Exception as e:
        # That bai giua luc kiem tra (khac voi that bai luc CHUAN BI o tren):
        # da co lease that su nen van giu lease_ok=True, chi bao them loi.
        ket_qua["loi"] = (ket_qua.get("loi") or "") + f" Loi khong luong truoc: {e}"
    finally:
        # DON SACH - luon chay du thanh cong hay that bai giua chung. Rule
        # va bang dinh tuyen thi luon don (vi luon la thu ta them, bat ke
        # IP co san hay khong); dia chi IP CHI xoa neu chinh ta la nguoi
        # them no (khong dong vao IP von da co san tren cong).
        if da_them_dinh_tuyen:
            subprocess.run(["ip", "rule", "del", "priority", str(_TEST_RULE_PRIO)],
                           capture_output=True, timeout=8)
        subprocess.run(["ip", "route", "flush", "table", str(_TEST_TABLE)],
                       capture_output=True, timeout=8)
        if da_them_ip:
            subprocess.run(["ip", "addr", "del", f"{ip}/{prefix}", "dev", iface],
                           capture_output=True, timeout=8)

    return ket_qua

DHCP_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>DHCP Testing - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: #eee; padding: 20px; }
        h1 { color: #4CAF50; }
        h3 { color: #4CAF50; margin-top: 22px; }
        a { color: #4CAF50; }
        select { padding: 8px; background: #333; color: #eee; border: 1px solid #555; }
        button { padding: 9px 18px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
        table { width: 100%; border-collapse: collapse; margin-top: 16px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #444; }
        th { background: #2d2d2d; }
        .err { background: #4a2d2d; border-left: 4px solid #f44336; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .hint { color: #999; font-size: 13px; }
        .card { background:#262626; border:1px solid #3a3a3a; border-left:4px solid #4CAF50;
                border-radius:6px; padding:14px 16px; margin-top:14px; }
        .ok-badge { color:#8fd99a; }
        .bad-badge { color:#ff8a8a; }
        label.chk { display:flex; align-items:center; gap:8px; margin-top:12px; color:#ccc; font-size:14px; }
        code.small { font-size:12px; color:#aaa; }
    </style>
</head>
<body>
    <h1>🌐 DHCP Testing</h1>
    <p><a href="/nettools">← Network Tools</a></p>
    <p class="hint">Khuyen nghi dung <strong>eth0</strong> (day mang) - da xac nhan hoat dong dung.
    Tren <strong>wlan0</strong>, nhieu driver WiFi khong the "tiem" (inject) goi tin da tao san
    qua interface dang ket noi WPA2, nen co the KHONG thay OFFER du mang van binh thuong
    (khong phai loi cong cu).</p>
    <p class="hint">Gui 1 goi DHCPDISCOVER va cho DHCPOFFER tra ve. Mac dinh KHONG hoan tat
    handshake (khong gui REQUEST) nen khong chiem lease that - an toan chay lai nhieu lan.</p>

    <form method="POST" style="margin-top:16px;">
        <label>Interface:</label>
        <select name="iface">
            <option value="eth0" {{ 'selected' if iface=='eth0' else '' }}>eth0</option>
            <option value="wlan0" {{ 'selected' if iface=='wlan0' else '' }}>wlan0</option>
        </select>
        <button type="submit" style="margin-left:10px;">Gui DHCPDISCOVER</button>

        <label class="chk">
            <input type="checkbox" name="test_internet" value="1" {{ 'checked' if test_internet else '' }}>
            Cung kiem tra ra duoc Internet khong (ping 8.8.8.8, ping google.com, mo thu web)
        </label>
        <p class="hint" style="margin:4px 0 0 26px;">Muc nay se <strong>tam thoi xin that mot IP</strong>
        (hoan tat DHCPREQUEST/ACK) de test qua dung duong mang do, roi <strong>tra lai ngay sau khi
        xong</strong> - khong dung den IP quan ly hien co cua Pi tren cong nay. Vi co chiem mot lease
        that (khac voi phan quet OFFER o tren), chi bat khi that su can.</p>
    </form>

    {% if ran %}
        {% if result.error %}
        <div class="err">Loi: {{ result.error }}</div>
        {% else %}
        <p style="margin-top:16px;">Nhan duoc <strong>{{ result.offers|length }}</strong> OFFER:</p>
        <table>
            <tr><th>IP cap</th><th>DHCP Server</th><th>Subnet</th><th>Gateway</th><th>DNS</th><th>Lease (s)</th></tr>
            {% for o in result.offers %}
            <tr>
                <td>{{ o.offered_ip }}</td><td>{{ o.server_id }}</td><td>{{ o.subnet_mask }}</td>
                <td>{{ o.router }}</td><td>{{ o.name_server }}</td><td>{{ o.lease_time }}</td>
            </tr>
            {% endfor %}
        </table>
        {% if result.offers|length > 1 %}
        <p class="hint">⚠️ Co <strong>{{ result.offers|length }}</strong> DHCP server tra loi tren cung 1
        day - co the la dau hieu DHCP server gia mao (rogue) neu ban chi mong doi 1 server.</p>
        {% endif %}
        {% if not result.offers %}<p>Khong co OFFER nao tra ve trong thoi gian cho (co the khong co DHCP server tren day nay).</p>{% endif %}

        {% if result.internet %}
        <h3>🌍 Ket qua kiem tra Internet (qua IP {{ result.internet.ip or '?' }})</h3>
        {% if not result.internet.lease_ok %}
        <div class="err">Khong xin duoc lease that de test: {{ result.internet.loi }}</div>
        {% else %}
        <div class="card">
            <table style="margin:0;">
                <tr><th style="width:220px;">Kiem tra</th><th>Ket qua</th></tr>
                <tr>
                    <td>Ping 8.8.8.8 (Google DNS)</td>
                    <td>
                        {% if result.internet.ping_8888.ok %}
                        <span class="ok-badge">✔ Thanh cong</span> - mat {{ result.internet.ping_8888.mat_goi_pct }}% goi tin
                        {% else %}
                        <span class="bad-badge">✘ That bai</span> - mat {{ result.internet.ping_8888.mat_goi_pct }}% goi tin
                        {% endif %}
                    </td>
                </tr>
                <tr>
                    <td>Ping google.com</td>
                    <td>
                        {% if result.internet.ping_google.ok %}
                        <span class="ok-badge">✔ Thanh cong</span>
                        {% if result.internet.ping_google.ip_phan_giai %} - phan giai ra <code class="small">{{ result.internet.ping_google.ip_phan_giai }}</code>{% endif %}
                        {% else %}
                        <span class="bad-badge">✘ That bai</span>
                        {% if result.internet.ping_google.loi %} - {{ result.internet.ping_google.loi }}{% endif %}
                        {% endif %}
                    </td>
                </tr>
                {% for w in result.internet.web %}
                <tr>
                    <td>Mo web {{ w.url }} (port {{ w.port }})</td>
                    <td>
                        {% if w.ok %}
                        <span class="ok-badge">✔ HTTP {{ w.http_code }}</span> - {{ w.thoi_gian_s }}s
                        {% else %}
                        <span class="bad-badge">✘ Khong ket noi duoc</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
        {% if result.internet.loi %}<div class="err">{{ result.internet.loi }}</div>{% endif %}
        <p class="hint">Da tra lai IP tam va bang dinh tuyen - khong con anh huong gi den cong {{ iface }} nua.</p>
        {% endif %}
        {% endif %}
        {% endif %}
    {% endif %}
</body>
</html>
"""


@nettools_bp.route("/nettools/dhcp-test", methods=["GET", "POST"])
def dhcp_test_route():
    iface = request.form.get("iface", "eth0")
    test_internet = request.form.get("test_internet") == "1"
    ran = request.method == "POST"
    result = run_dhcp_test(iface=iface, test_internet=test_internet) if ran else None
    return render_template_string(DHCP_TEMPLATE, iface=iface, ran=ran, result=result,
                                  test_internet=test_internet)


if __name__ == "__main__":
    import sys
    import json
    iface = sys.argv[1] if len(sys.argv) > 1 else "eth0"
    ti = len(sys.argv) > 2 and sys.argv[2] == "internet"
    print(json.dumps(run_dhcp_test(iface=iface, test_internet=ti), indent=2, ensure_ascii=False))
