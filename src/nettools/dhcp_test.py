"""
Console Pi Network Tools - Kiem tra toan dien cong mang day (gop DHCP
Testing + Kiem tra cong vat ly + Bang thong, theo yeu cau gop lam mot trang
bam MOT NUT la test het).

Mot lan bam "Kiem tra toan dien" se lam:
  1. Doc thong tin cong vat ly (ethtool) - toc do/duplex that, loi duong
     truyen, PoE. KHONG can DHCP, luon hien duoc ngay ca khi cong chua
     co IP nao ca.
  2. Gui DHCPDISCOVER, cho DHCPOFFER (khong tieu ton lease - an toan).
  3. Neu co OFFER: tu dong xin that mot lease (REQUEST/ACK), kiem tra ra
     Internet (ping 8.8.8.8, ping google.com, mo web that), VA do luon
     bang thong qua Cloudflare - tat ca dung CHUNG mot ha tang dinh tuyen
     tam thoi da dung cho phan ping/web, xong thi tra lai nguyen trang.

KHONG dung iperf3 (theo yeu cau) - chi dung Cloudflare Speed Test, khong
can chuan bi may thu hai.
"""
import random
import re
import subprocess
import time

from flask import request, render_template_string

from . import nettools_bp

_TEST_TABLE = 199
_TEST_RULE_PRIO = 199
WEB_CHECKS = [("http://example.com", 80), ("https://www.google.com", 443)]
CLOUDFLARE_BYTES = 25_000_000


def _chay(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return -1, "", "khong-cai-dat"
    except subprocess.TimeoutExpired:
        return -1, "", "qua-thoi-gian-cho"
    except Exception as e:
        return -1, "", str(e)


# =========================================================== CONG VAT LY
def doc_thong_tin_cong(iface):
    """Toc do/duplex thuong luong that, nang luc hai ben, trang thai lien ket."""
    rc, out, err = _chay(["ethtool", iface])
    if rc != 0:
        if "khong-cai-dat" in err:
            return {"ok": False, "loi": "Chua cai ethtool tren may."}
        return {"ok": False, "loi": f"Khong doc duoc thong tin cong: {err.strip()[:150]}"}

    def _lay(nhan, van_ban):
        m = re.search(rf"{nhan}:\s*(.+)", van_ban)
        return m.group(1).strip() if m else ""

    def _lay_khoi(nhan, van_ban):
        """
        Cac muc 'Advertised link modes' / 'Link partner advertised link
        modes' trai dai nhieu dong noi tiep, thut le sau nhan dau tien.
        Khong the dung "dong khong thut le la het khoi" - TOAN BO output
        cua ethtool deu thut le bang 1 tab. Cach dung: dong noi tiep cua
        danh sach mode la chuoi thuan (khong co dau ':'), con moi truong
        moi luon co dau ':' o dau dong.
        """
        dong = van_ban.splitlines()
        ket_qua = []
        dang_doc = False
        for d in dong:
            if not dang_doc:
                m = re.match(rf"\s*{nhan}:\s*(.*)$", d)
                if m:
                    dang_doc = True
                    ket_qua += m.group(1).split()
                continue
            if re.match(r"\s*[A-Za-z][^:]*:", d):
                break
            ket_qua += d.split()
        return ket_qua

    ket_qua = {
        "ok": True, "loi": None,
        "toc_do": _lay("Speed", out) or "?",
        "duplex": _lay("Duplex", out) or "?",
        "auto_neg": _lay("Auto-negotiation", out) or "?",
        "lien_ket": _lay("Link detected", out) or "?",
        "nang_luc_minh": _lay_khoi("Advertised link modes", out),
        "nang_luc_doi_phuong": _lay_khoi(r"Link partner advertised link modes", out),
    }

    rc2, out2, _ = _chay(["ethtool", "-i", iface])
    if rc2 == 0:
        ket_qua["driver"] = _lay("driver", out2) or "?"

    if "1000baseT" in " ".join(ket_qua["nang_luc_minh"]) and \
       "1000baseT" in " ".join(ket_qua["nang_luc_doi_phuong"]) and \
       ket_qua["toc_do"] not in ("1000Mb/s", "?"):
        ket_qua["canh_bao"] = (f"Ca hai ben deu ho tro Gigabit nhung chi thuong luong duoc "
                               f"{ket_qua['toc_do']} - kiem tra lai chat luong day cap hoac "
                               f"cai dat toc do co dinh (fixed speed) tren switch.")
    elif ket_qua["duplex"] == "Half":
        ket_qua["canh_bao"] = ("Dang chay Half Duplex - hau nhu chac chan la loi cau hinh "
                              "(duplex mismatch), gay mat goi va cham ro ret. Kiem tra cai dat "
                              "tren cong switch phia ben kia.")
    else:
        ket_qua["canh_bao"] = None

    return ket_qua


def doc_thong_ke_loi(iface):
    rc, out, err = _chay(["ethtool", "-S", iface])
    if rc != 0:
        return {"ok": False, "loi": "Card mang nay khong ho tro doc thong ke chi tiet."}

    muon_biet = ["rx_errors", "tx_errors", "rx_dropped", "tx_dropped",
                "rx_crc_errors", "rx_length_errors", "rx_over_errors",
                "rx_missed_errors", "collisions", "tx_aborted_errors"]
    so_lieu = {}
    for dong in out.splitlines():
        if ":" not in dong:
            continue
        khoa, _, gia_tri = dong.strip().partition(":")
        khoa = khoa.strip()
        if khoa in muon_biet:
            try:
                so_lieu[khoa] = int(gia_tri.strip())
            except ValueError:
                pass
    return {"ok": True, "so_lieu": so_lieu, "tong_loi": sum(so_lieu.values())}


def doc_poe(iface):
    """Chi hien khi phan cung THAT SU co mach do - khong bia du lieu."""
    for duong in (f"/sys/class/net/{iface}/device/poe_power", "/sys/class/hwmon/hwmon0/poe_watts"):
        try:
            with open(duong) as f:
                return {"phat_hien": True, "gia_tri": f.read().strip()}
        except OSError:
            continue
    return {"phat_hien": False}


# =========================================================== DHCP DISCOVER
def run_dhcp_test(iface="eth0", timeout=5, test_internet=True):
    """
    Tra ve {"ok", "error", "offers": [...], "internet": {...}|None,
            "cong": {...}, "loi_truyen": {...}, "poe": {...}}

    LUU Y KY THUAT: dung sniff() + sendp() rieng biet thay vi srp(), vi
    srp() tu ghep cap request/response bang IP.answers() - co logic khong
    phu hop voi DHCP. sniff() bat moi goi UDP port 68 trong khoang thoi
    gian cho, khong phu thuoc logic ghep cap.

    TU GUI LAI DISCOVER NHIEU LAN: DHCPDISCOVER/OFFER la goi tin BROADCAST,
    khong co ACK/retry o tang lien ket 802.11 (khac unicast) nen tren WiFi
    co the mat hoan toan mot lan gui du moi thu deu dung - dung RFC 2131
    khuyen nghi client tu gui lai.
    """
    cong = doc_thong_tin_cong(iface)
    loi_truyen = doc_thong_ke_loi(iface)
    poe = doc_poe(iface)

    try:
        from scapy.all import (
            Ether, IP, UDP, BOOTP, DHCP, sendp, AsyncSniffer,
            get_if_hwaddr, mac2str, conf,
        )
    except ImportError as e:
        return {"ok": False, "error": f"Loi import scapy: {e}", "offers": [], "internet": None,
                "cong": cong, "loi_truyen": loi_truyen, "poe": poe}

    conf.verb = 0

    try:
        hw_str = get_if_hwaddr(iface)
        hw = mac2str(hw_str)
    except Exception as e:
        return {"ok": False, "error": f"Khong lay duoc MAC cua {iface}: {e}", "offers": [], "internet": None,
                "cong": cong, "loi_truyen": loi_truyen, "poe": poe}

    xid = random.randint(1, 0xFFFFFFFF)
    pkt = (
        # BAT BUOC ghi ro src=hw_str: neu bo trong, scapy tu dien MAC theo
        # conf.iface (interface MAC DINH noi bo cua scapy - KHONG chac la
        # cung iface dang test). Da gap loi that: tren wlan0, Ethernet src
        # tu dien lai la MAC cua eth0 trong khi BOOTP chaddr dung la MAC
        # cua wlan0 - hai dia chi mau thuan trong cung 1 goi khien AP WiFi
        # (kiem tra chat hon router co day) im lang khong tra loi, khong
        # bao loi gi, rat kho phat hien neu khong doi chieu tung byte.
        Ether(src=hw_str, dst="ff:ff:ff:ff:ff:ff") /
        IP(src="0.0.0.0", dst="255.255.255.255") /
        UDP(sport=68, dport=67) /
        BOOTP(chaddr=hw, xid=xid, flags=0x8000) /
        DHCP(options=[("message-type", "discover"), "end"])
    )

    SO_LAN_GUI = 3
    KHOANG_CACH = max(1.0, timeout / SO_LAN_GUI)

    captured = []
    sniffer = AsyncSniffer(
        iface=iface, filter="udp and port 68", store=True,
        prn=lambda p: captured.append(p),
    )
    try:
        sniffer.start()
        time.sleep(0.3)
        for _ in range(SO_LAN_GUI):
            sendp(pkt, iface=iface, verbose=0)
            time.sleep(KHOANG_CACH)
    except PermissionError:
        sniffer.stop()
        return {"ok": False, "error": "Khong du quyen mo raw socket (can chay duoi quyen root).",
                "offers": [], "internet": None, "cong": cong, "loi_truyen": loi_truyen, "poe": poe}
    except OSError as e:
        sniffer.stop()
        return {"ok": False, "error": f"Loi khi gui goi tin: {e}", "offers": [], "internet": None,
                "cong": cong, "loi_truyen": loi_truyen, "poe": poe}
    else:
        sniffer.stop()

    # Gui lai 3 lan co the khien mot server that tra loi ca 3 lan - gop
    # trung theo (server_id, offered_ip) truoc khi hien, neu khong se bao
    # nham "nhieu DHCP server" (canh bao rogue DHCP gia).
    offers = []
    da_thay = set()
    for recv in captured:
        if not recv.haslayer(DHCP) or not recv.haslayer(BOOTP):
            continue
        if recv[BOOTP].xid != xid:
            continue
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

    return {"ok": True, "error": None, "offers": offers, "internet": internet_result,
            "cong": cong, "loi_truyen": loi_truyen, "poe": poe}


def _mask_to_prefixlen(mask):
    """'255.255.255.0' -> 24. Tra ve None neu khong hop le."""
    try:
        parts = [int(x) for x in str(mask).split(".")]
        if len(parts) != 4:
            return None
        bits = "".join(f"{p:08b}" for p in parts)
        if "01" in bits:
            return None
        return bits.count("1")
    except Exception:
        return None


def _dhcp_request_ack(iface, xid, offer, hw, timeout=5):
    """Hoan tat REQUEST/ACK - buoc THAT SU xin lease. Tra ve (ok, ip, mask, gw, dns, loi)."""
    from scapy.all import Ether, IP, UDP, BOOTP, DHCP, sendp, AsyncSniffer, conf
    conf.verb = 0

    # hw la bytes (tu mac2str) - doi nguoc lai chuoi "aa:bb:.." cho Ether
    # src, PHAI KHOP voi chaddr, cung ly do da giai thich o run_dhcp_test().
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
        if mtype == 6:
            return False, None, None, None, None, "DHCP server tu choi (NAK) - offer co the da het han."
        if mtype != 5:
            continue
        ip = recv[BOOTP].yiaddr
        mask = opts.get("subnet_mask", offer.get("subnet_mask"))
        gw = opts.get("router", offer.get("router"))
        dns = opts.get("name_server", offer.get("name_server"))
        return True, ip, mask, gw, dns, None

    return False, None, None, None, None, "Khong nhan duoc DHCPACK trong thoi gian cho."


def _dia_chi_hien_co_tren_cong(iface):
    try:
        out = subprocess.run(["ip", "-4", "-o", "addr", "show", "dev", iface],
                             capture_output=True, text=True, timeout=6).stdout
    except Exception:
        return set()
    return set(re.findall(r"inet (\d+\.\d+\.\d+\.\d+)/", out))


def cloudflare_speedtest(so_byte, ip_nguon=None):
    """Tai du lieu tu speed.cloudflare.com - dich vu speedtest cong khai
    chinh chu, khong can chuan bi gi o dau kia."""
    url = f"https://speed.cloudflare.com/__down?bytes={so_byte}"
    cmd = ["curl", "-s", "-o", "/dev/null", "-m", "20"]
    if ip_nguon:
        cmd += ["--interface", ip_nguon]
    cmd += ["-w", "%{speed_download} %{http_code} %{time_total}", url]
    rc, out, err = _chay(cmd, timeout=25)
    if rc != 0:
        return {"ok": False, "loi": f"Khong tai duoc: {err.strip()[:150]}"}
    phan = out.split()
    if len(phan) < 2 or phan[1] != "200":
        return {"ok": False, "loi": f"Cloudflare tra ve loi (HTTP {phan[1] if len(phan)>1 else '?'})."}
    mbps = float(phan[0]) * 8 / 1_000_000
    return {"ok": True, "mbps": round(mbps, 1), "thoi_gian_s": phan[2], "so_mb": so_byte // 1_000_000}


def _test_internet_qua_dhcp(iface, xid, offer, hw):
    """
    Xin that mot lease (REQUEST/ACK), gan tam vao cong (KHONG dung/xoa IP
    quan ly hien co - chi them dia chi PHU), dinh tuyen rieng theo dia chi
    nguon bang policy routing, roi kiem tra Internet + do bang thong DUNG
    QUA DUONG MANG DO. Don sach toan bo trong finally.

    TRUONG HOP HAY GAP: neu cong dang test la CHINH cong Pi da co IP tu
    truoc, DHCP server thuong tra lai DUNG dia chi hien tai cho cung MAC
    (RFC 2131 4.3.1). Luc do KHONG can `ip addr add` (da co san), NHUNG VAN
    PHAI thiet lap dinh tuyen rieng: da gap that mot router WiFi cap tuyen
    duong RIENG cho dung 8.8.8.8 di qua interface khac, khien ping bi day
    nham cong du dia chi nguon dung - dinh tuyen rieng (danh gia truoc ca
    bang main) chan dut moi tuyen duong dac biet kieu do.
    """
    ket_qua = {"lease_ok": False, "loi": None, "ip": None, "gw": None,
              "ping_8888": None, "ping_google": None, "web": [], "bang_thong": None}

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
            r = subprocess.run(["ip", "addr", "add", f"{ip}/{prefix}", "dev", iface],
                               capture_output=True, text=True, timeout=8)
            trung_dia_chi = ("File exists" in r.stderr or "already assigned" in r.stderr)
            if r.returncode != 0 and not trung_dia_chi:
                ket_qua["loi"] = f"Khong gan duoc IP tam: {r.stderr.strip()[:150]}"
                return ket_qua
            da_them_ip = not trung_dia_chi

        # LUON LUON thiet lap dinh tuyen rieng theo dia chi NGUON, ke ca khi
        # IP da co san - xem docstring o tren cho ly do (router WiFi voi
        # tuyen duong dac biet cho 8.8.8.8 la vi du that da gap).
        subprocess.run(["ip", "route", "flush", "table", str(_TEST_TABLE)],
                       capture_output=True, timeout=8)
        subprocess.run(["ip", "route", "add", f"{ip}/{prefix}", "dev", iface,
                        "src", ip, "table", str(_TEST_TABLE)],
                       capture_output=True, timeout=8)
        subprocess.run(["ip", "route", "add", "default", "via", gw, "dev", iface,
                        "src", ip, "table", str(_TEST_TABLE)],
                       capture_output=True, timeout=8)
        subprocess.run(["ip", "rule", "del", "priority", str(_TEST_RULE_PRIO)],
                       capture_output=True, timeout=8)
        r = subprocess.run(["ip", "rule", "add", "from", ip, "table", str(_TEST_TABLE),
                            "priority", str(_TEST_RULE_PRIO)],
                           capture_output=True, text=True, timeout=8)
        da_them_dinh_tuyen = (r.returncode == 0)

        ket_qua.update(lease_ok=True, ip=ip, gw=gw)

        r = subprocess.run(["ping", "-I", ip, "-c", "3", "-W", "2", "8.8.8.8"],
                           capture_output=True, text=True, timeout=12)
        m = re.search(r"(\d+)% packet loss", r.stdout)
        mat = int(m.group(1)) if m else 100
        ket_qua["ping_8888"] = {"ok": mat < 100, "mat_goi_pct": mat,
                                "chi_tiet": r.stdout.strip().splitlines()[-2:]}

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

        # Bam MOT nut la test het - do luon bang thong qua duong mang vua
        # xac nhan la thong (tai su dung dung dinh tuyen tam thoi da lap o
        # tren, khong can them thiet lap gi khac).
        ket_qua["bang_thong"] = cloudflare_speedtest(CLOUDFLARE_BYTES, ip_nguon=ip)

    except Exception as e:
        ket_qua["loi"] = (ket_qua.get("loi") or "") + f" Loi khong luong truoc: {e}"
    finally:
        if da_them_dinh_tuyen:
            subprocess.run(["ip", "rule", "del", "priority", str(_TEST_RULE_PRIO)],
                           capture_output=True, timeout=8)
        subprocess.run(["ip", "route", "flush", "table", str(_TEST_TABLE)],
                       capture_output=True, timeout=8)
        if da_them_ip:
            subprocess.run(["ip", "addr", "del", f"{ip}/{prefix}", "dev", iface],
                           capture_output=True, timeout=8)

    return ket_qua


# =========================================================== GIAO DIEN
DHCP_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Kiem tra cong mang - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: #eee; padding: 20px; }
        h1 { color: #4CAF50; } h3 { color: #4CAF50; margin-top: 22px; }
        a { color: #4CAF50; }
        select { padding: 8px; background: #333; color: #eee; border: 1px solid #555; }
        button { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 12px; }
        th, td { padding: 9px 10px; text-align: left; border-bottom: 1px solid #444; vertical-align: top; }
        th { background: #2d2d2d; width: 220px; }
        .card { background:#262626; border:1px solid #3a3a3a; border-left:4px solid #4CAF50;
                border-radius:6px; padding:14px 16px; margin-top:16px; }
        .err { background: #4a2d2d; border-left: 4px solid #f44336; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .warn { background: #4a3d1a; border-left: 4px solid #ffb74d; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .ok-txt { color: #8fd99a; } .bad-txt { color: #ff8a8a; }
        .hint { color: #999; font-size: 13px; }
        .modes { display:flex; gap:6px; flex-wrap:wrap; }
        .mode-chip { background:#1f1f1f; border:1px solid #444; border-radius:10px; padding:2px 9px; font-size:12px; }
        .big { font-size:26px; font-weight:700; }
    </style>
</head>
<body>
    <h1>🔌🌐 Kiem tra toan dien cong mang</h1>
    <p><a href="/nettools">← Network Tools</a></p>
    <p class="hint">Mot nut bam duy nhat: doc toc do/duplex/loi duong truyen/PoE cua cong,
    gui DHCPDISCOVER, va neu co IP thi kiem tra luon ra Internet + do bang thong that
    (Cloudflare Speed Test) - tat ca trong 1 lan.</p>
    <p class="hint">Khuyen nghi dung <strong>eth0</strong>. Tren <strong>wlan0</strong> cong cu van
    hoat dong (tu dong gui lai 3 lan de vuot qua mat goi broadcast dac trung cua WiFi).</p>

    <form method="POST" style="margin-top:16px;">
        <label>Interface:</label>
        <select name="iface">
            <option value="eth0" {{ 'selected' if iface=='eth0' else '' }}>eth0</option>
            <option value="wlan0" {{ 'selected' if iface=='wlan0' else '' }}>wlan0</option>
        </select>
        <button type="submit" style="margin-left:10px;" data-busy="Dang kiem tra toan dien...">🔎 Kiem tra toan dien</button>
    </form>

    {% if ran %}
    <div class="card">
        <h3 style="margin-top:0;">🔌 Cong vat ly</h3>
        {% if result.cong.ok %}
        <table>
            <tr><th>Toc do thuong luong</th><td class="big">{{ result.cong.toc_do }}</td></tr>
            <tr><th>Duplex</th><td>{{ result.cong.duplex }}</td></tr>
            <tr><th>Auto-negotiation</th><td>{{ result.cong.auto_neg }}</td></tr>
            <tr><th>Lien ket (link)</th><td>{{ result.cong.lien_ket }}</td></tr>
            <tr><th>Driver</th><td><code>{{ result.cong.driver }}</code></td></tr>
            <tr><th>Nang luc cua Pi</th><td><div class="modes">{% for m in result.cong.nang_luc_minh %}<span class="mode-chip">{{ m }}</span>{% endfor %}</div></td></tr>
            <tr><th>Nang luc phia ben kia</th><td><div class="modes">{% for m in result.cong.nang_luc_doi_phuong %}<span class="mode-chip">{{ m }}</span>{% endfor %}
                {% if not result.cong.nang_luc_doi_phuong %}<span class="hint">Khong doc duoc (cong co the dang down)</span>{% endif %}</div></td></tr>
        </table>
        {% if result.cong.canh_bao %}<div class="warn" style="margin-top:11px;">⚠️ {{ result.cong.canh_bao }}</div>{% endif %}
        {% else %}<div class="err">{{ result.cong.loi }}</div>{% endif %}

        <h3>Thong ke loi duong truyen</h3>
        {% if result.loi_truyen.ok %}
        <table>
            {% for khoa, gt in result.loi_truyen.so_lieu.items() %}
            <tr><th>{{ khoa }}</th><td class="{{ 'bad-txt' if gt > 0 else 'ok-txt' }}">{{ gt }}</td></tr>
            {% endfor %}
        </table>
        <p style="margin-top:9px;" class="{{ 'bad-txt' if result.loi_truyen.tong_loi > 0 else 'ok-txt' }}">
            {% if result.loi_truyen.tong_loi == 0 %}🟢 Khong co loi nao duoc ghi nhan{% else %}
            🔴 Tong {{ result.loi_truyen.tong_loi }} loi - day cap co the kem chat luong hoac bi nhieu{% endif %}</p>
        {% else %}<p class="hint">{{ result.loi_truyen.loi }}</p>{% endif %}

        <h3>PoE (nguon qua cap mang)</h3>
        {% if result.poe.phat_hien %}<p>🟢 Phat hien PoE: {{ result.poe.gia_tri }}</p>
        {% else %}<p class="hint">Khong phat hien mach do PoE tren phan cung nay.</p>{% endif %}
    </div>

    {% if result.error %}
    <div class="err">Loi: {{ result.error }}</div>
    {% else %}
        <div class="card">
        <h3 style="margin-top:0;">📡 DHCP</h3>
        <p>Nhan duoc <strong>{{ result.offers|length }}</strong> OFFER:</p>
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
        </div>

        {% if result.internet %}
        <div class="card">
        <h3 style="margin-top:0;">🌍 Internet + Bang thong (qua IP {{ result.internet.ip or '?' }})</h3>
        {% if not result.internet.lease_ok %}
        <div class="err">Khong xin duoc lease that de test: {{ result.internet.loi }}</div>
        {% else %}
        <table style="margin:0;">
            <tr><th style="width:220px;">Ping 8.8.8.8 (Google DNS)</th>
                <td>{% if result.internet.ping_8888.ok %}<span class="ok-txt">✔ Thanh cong</span> - mat {{ result.internet.ping_8888.mat_goi_pct }}% goi tin
                    {% else %}<span class="bad-txt">✘ That bai</span> - mat {{ result.internet.ping_8888.mat_goi_pct }}% goi tin{% endif %}</td></tr>
            <tr><th>Ping google.com</th>
                <td>{% if result.internet.ping_google.ok %}<span class="ok-txt">✔ Thanh cong</span>
                    {% if result.internet.ping_google.ip_phan_giai %} - phan giai ra <code>{{ result.internet.ping_google.ip_phan_giai }}</code>{% endif %}
                    {% else %}<span class="bad-txt">✘ That bai</span>{% if result.internet.ping_google.loi %} - {{ result.internet.ping_google.loi }}{% endif %}{% endif %}</td></tr>
            {% for w in result.internet.web %}
            <tr><th>Mo web {{ w.url }} (port {{ w.port }})</th>
                <td>{% if w.ok %}<span class="ok-txt">✔ HTTP {{ w.http_code }}</span> - {{ w.thoi_gian_s }}s
                    {% else %}<span class="bad-txt">✘ Khong ket noi duoc</span>{% endif %}</td></tr>
            {% endfor %}
            <tr><th>📶 Bang thong (Cloudflare)</th>
                <td>{% if result.internet.bang_thong and result.internet.bang_thong.ok %}
                    <span class="big ok-txt">⬇ {{ result.internet.bang_thong.mbps }} Mbps</span>
                    <span class="hint"> - tai {{ result.internet.bang_thong.so_mb }}MB trong {{ result.internet.bang_thong.thoi_gian_s }}s</span>
                    {% else %}<span class="bad-txt">✘ {{ (result.internet.bang_thong or {}).get('loi', 'Khong do duoc') }}</span>{% endif %}</td></tr>
        </table>
        {% if result.internet.loi %}<div class="err" style="margin-top:11px;">{{ result.internet.loi }}</div>{% endif %}
        <p class="hint" style="margin-top:9px;">Da tra lai IP tam va bang dinh tuyen - khong con anh huong gi den cong {{ iface }} nua.</p>
        {% endif %}
        </div>
        {% endif %}
    {% endif %}
    {% endif %}
</body>
</html>
"""


@nettools_bp.route("/nettools/dhcp-test", methods=["GET", "POST"])
def dhcp_test_route():
    iface = request.form.get("iface", "eth0")
    ran = request.method == "POST"
    result = run_dhcp_test(iface=iface, test_internet=True) if ran else None
    return render_template_string(DHCP_TEMPLATE, iface=iface, ran=ran, result=result)


if __name__ == "__main__":
    import sys
    import json
    iface = sys.argv[1] if len(sys.argv) > 1 else "eth0"
    print(json.dumps(run_dhcp_test(iface=iface), indent=2, ensure_ascii=False))
