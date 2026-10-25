# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Gui goi tin danh thuc (Wake-on-LAN magic packet) - dich vu dung chung (tach tu wol.py o B3): chuan hoa MAC, liet ke card, gui 3 kieu."""
import ipaddress
import json
import re
import socket
import subprocess
import time


CONG = (9, 7)


def chuan_mac(s):
    h = re.sub(r"[^0-9a-f]", "", (s or "").lower())
    if len(h) != 12:
        return ""
    if h in ("000000000000", "ffffffffffff") or int(h[1], 16) & 1:
        return ""          # MAC rong / broadcast / multicast - khong phai card that
    return ":".join(h[i:i + 2] for i in range(0, 12, 2))


def goi_tin(mac):
    """Magic packet 102 byte."""
    return b"\xff" * 6 + bytes.fromhex(mac.replace(":", "")) * 16


def card_mang():
    """[(ten card, mac card, [dia chi broadcast IPv4])] cac card dang UP, bo lo/ao."""
    ra = []
    try:
        r = subprocess.run(["ip", "-j", "addr"], capture_output=True, text=True, timeout=5)
        ds = json.loads(r.stdout or "[]")
    except (OSError, ValueError, subprocess.SubprocessError):
        return ra
    for c in ds:
        ten = c.get("ifname", "")
        if (ten == "lo" or ten.startswith(("docker", "veth", "virbr", "br-", "tailscale", "tun", "wg"))
                or "UP" not in (c.get("flags") or [])):
            continue
        bc = []
        for a in c.get("addr_info") or []:
            if a.get("family") != "inet":
                continue
            b = a.get("broadcast")
            if not b:
                try:
                    b = str(ipaddress.ip_interface(f"{a['local']}/{a['prefixlen']}").network.broadcast_address)
                except (KeyError, ValueError):
                    b = ""
            if b and b not in bc:
                bc.append(b)
        if bc:
            ra.append((ten, c.get("address", ""), bc))
    return ra


def gui(cac_mac, so_lan=3, them_broadcast=()):
    """
    Gui magic packet cho moi MAC. Tra ve (so_may, chi_tiet[]). Lap so_lan lan cach nhau 1
    giay (goi UDP co the rot; NIC dang chuyen trang thai ngu co the bo lo goi dau).
    """
    macs = []
    for m in cac_mac or []:
        m = chuan_mac(m)
        if m and m not in macs:
            macs.append(m)
    if not macs:
        return 0, ["Không có địa chỉ MAC hợp lệ nào."]
    cards = card_mang()
    ngoai = []
    for b in them_broadcast or []:
        try:
            ngoai.append(str(ipaddress.IPv4Address(b.strip())))
        except ValueError:
            pass
    loi = []
    da_gui = 0
    for lan in range(max(1, min(int(so_lan or 1), 5))):
        for mac in macs:
            p = goi_tin(mac)
            for ten, mac_card, bcs in cards:
                # 1. UDP 255.255.255.255 ra dung card nay
                for cong in CONG:
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                            s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, ten.encode())
                            s.sendto(p, ("255.255.255.255", cong))
                            da_gui += 1
                    except OSError as e:
                        loi.append(f"{ten} 255.255.255.255:{cong}: {e}")
                # 2. UDP broadcast mang con
                for b in bcs:
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                            s.sendto(p, (b, 9))
                            da_gui += 1
                    except OSError as e:
                        loi.append(f"{ten} {b}:9: {e}")
                # 3. Khung Ethernet 0x0842
                try:
                    nguon = bytes.fromhex(mac_card.replace(":", "")) if mac_card else b"\0" * 6
                    with socket.socket(socket.AF_PACKET, socket.SOCK_RAW) as s:
                        s.bind((ten, 0))
                        s.send(b"\xff" * 6 + nguon + b"\x08\x42" + p)
                        da_gui += 1
                except OSError as e:
                    loi.append(f"{ten} ethertype 0x0842: {e}")
            for b in ngoai:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                        s.sendto(p, (b, 9))
                        da_gui += 1
                except OSError as e:
                    loi.append(f"{b}:9: {e}")
        if lan + 1 < so_lan:
            time.sleep(1)
    chi_tiet = [f"Qua card: " + ", ".join(f"{t} ({', '.join(b)})" for t, _m, b in cards)
                if cards else "KHÔNG có card mạng nào đang có IP - không gửi được."]
    if ngoai:
        chi_tiet.append("Thêm broadcast: " + ", ".join(ngoai))
    chi_tiet.append(f"Đã gửi {da_gui} gói tin.")
    # Loi lap lai giong nhau qua cac lan -> chi giu khac nhau
    for x in dict.fromkeys(loi):
        chi_tiet.append("Lỗi: " + x)
    return (len(macs) if da_gui else 0), chi_tiet
