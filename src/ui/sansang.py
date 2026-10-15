# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console System - KIEM TRA SAN SANG truoc khi cai qua mang (~5 giay).

VI SAO (anh Thoai 14/10/2026, muc 5): ngoai doi phan lon lan cai hong la do MANG CUA KHACH
hoac thieu file, khong phai do Console System: day mang 100 Mbps, router khach cung phat
DHCP khi Pi dang "tu cap IP", may domain ma DNS khong tro ve AD, dong ho Pi lech (Kerberos
tu choi gia nhap domain), file Windows chep do dang... Moi loi do chi lo ra sau 10-30 phut
cho. Bam 1 nut, biet ngay - kem CACH SUA cu the cho tung muc.

Moi muc: {"muc", "muc_do" (ok|canh|loi|info), "noi_dung", "sua"}. "loi" = chac chan hong
neu cai bay gio; "canh" = van cai duoc nhung de cham/hong mot phan; "info" = de biet.
"""
import os
import random
import socket
import struct
import subprocess
import threading
import time

from . import deployos as _d


def _m(muc, muc_do, noi_dung, sua=""):
    return {"muc": muc, "muc_do": muc_do, "noi_dung": noi_dung, "sua": sua}


def _sh(cmd, timeout=5):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "").strip()
    except (OSError, subprocess.SubprocessError):
        return -1, ""


def _doc(p):
    try:
        with open(p) as f:
            return f.read().strip()
    except OSError:
        return ""


# --------------------------------------------------------------------- DHCP
def _tong_kiem(b):
    if len(b) % 2:
        b += b"\0"
    s = sum(struct.unpack(f"!{len(b) // 2}H", b))
    s = (s >> 16) + (s & 0xFFFF)
    s += s >> 16
    return (~s) & 0xFFFF


def do_dhcp(iface, cho=3.0):
    """
    Gui 1 goi DHCPDISCOVER ra `iface` va nghe DHCPOFFER trong `cho` giay. Tra ve danh sach
    {"may_chu", "cap_ip"} (moi may chu 1 lan) hoac None neu khong do duoc.

    Dung socket AF_PACKET (tu dung khung Ethernet/IP/UDP) - KHONG bind cong 68, nen khong
    dung do voi trinh DHCP cua NetworkManager dang giu IP cho Pi. DISCOVER chi la HOI:
    router khong cap IP that su cho toi khi co REQUEST, nen khong de lai dau vet gi.
    """
    try:
        mac = bytes.fromhex(_doc(f"/sys/class/net/{iface}/address").replace(":", ""))
        if len(mac) != 6:
            return None
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0800))
        s.bind((iface, 0))
    except (OSError, ValueError):
        return None
    xid = random.getrandbits(32)
    bootp = struct.pack("!BBBBIHH4s4s4s4s16s64s128s", 1, 1, 6, 0, xid, 0, 0x8000,
                        b"\0" * 4, b"\0" * 4, b"\0" * 4, b"\0" * 4, mac + b"\0" * 10,
                        b"\0" * 64, b"\0" * 128)
    tuy_chon = (b"\x63\x82\x53\x63" + b"\x35\x01\x01" + b"\x37\x03\x01\x03\x06"
                + b"\x3d\x07\x01" + mac + b"\xff")
    du_lieu = bootp + tuy_chon
    udp = struct.pack("!HHHH", 68, 67, 8 + len(du_lieu), 0)
    nguon, dich = b"\0" * 4, b"\xff" * 4
    gia = nguon + dich + struct.pack("!BBH", 0, 17, len(udp) + len(du_lieu))
    udp = udp[:6] + struct.pack("!H", _tong_kiem(gia + udp + du_lieu) or 0xFFFF)
    ip = struct.pack("!BBHHHBBH4s4s", 0x45, 0, 20 + len(udp) + len(du_lieu), 0, 0, 64, 17, 0,
                     nguon, dich)
    ip = ip[:10] + struct.pack("!H", _tong_kiem(ip)) + ip[12:]
    khung = b"\xff" * 6 + mac + b"\x08\x00" + ip + udp + du_lieu
    ra = {}
    try:
        s.send(khung)
        het = time.time() + cho
        s.settimeout(0.3)
        while time.time() < het:
            try:
                g = s.recv(2048)
            except socket.timeout:
                continue
            if len(g) < 14 + 20 + 8 + 240 or g[23] != 17:
                continue
            ihl = (g[14] & 0x0F) * 4
            u = 14 + ihl
            if struct.unpack("!H", g[u + 2:u + 4])[0] != 68:
                continue
            b = g[u + 8:]
            if b[0] != 2 or struct.unpack("!I", b[4:8])[0] != xid:
                continue
            cap = socket.inet_ntoa(b[16:20])
            may_chu = socket.inet_ntoa(g[26:30])
            # Option 54 (server identifier) chinh xac hon IP nguon (relay)
            i = 240
            while i < len(b) and b[i] != 255:
                if b[i] == 0:
                    i += 1
                    continue
                if i + 1 >= len(b):
                    break
                ma, dai = b[i], b[i + 1]
                if ma == 54 and dai == 4:
                    may_chu = socket.inet_ntoa(b[i + 2:i + 6])
                i += 2 + dai
            ra.setdefault(may_chu, {"may_chu": may_chu, "cap_ip": cap})
    except OSError:
        return None
    finally:
        s.close()
    return list(ra.values())


def _ip_cua_pi():
    rc, out = _sh(["ip", "-o", "-4", "addr"])
    return {t.split("/")[0] for t in out.split() if "/" in t and t[0].isdigit()}


# --------------------------------------------------------------------- tung muc
def _muc_mang(iface, kieu, pxe_bat):
    ra = []
    if not iface or not os.path.isdir(f"/sys/class/net/{iface}"):
        return [_m("Cổng mạng có dây", "loi", "Không tìm thấy cổng mạng có dây nào.",
                   "Cắm dây mạng / USB-LAN, chọn cổng ở Cài đặt → Mạng.")]
    if _doc(f"/sys/class/net/{iface}/carrier") != "1":
        return [_m(f"Dây mạng ({iface})", "loi", "Chưa cắm dây hoặc đầu bên kia chưa bật.",
                   "Kiểm tra dây, cổng switch / máy cần cài đã bật chưa.")]
    toc_do = _doc(f"/sys/class/net/{iface}/speed")
    try:
        td = int(toc_do)
    except ValueError:
        td = 0
    if td <= 0:
        ra.append(_m(f"Dây mạng ({iface})", "ok", "Đã cắm (không đọc được tốc độ)."))
    elif td < 1000:
        ra.append(_m(f"Tốc độ mạng ({iface})", "canh",
                     f"Chỉ {td} Mbps - bộ cài Windows ~5 GB mất khoảng "
                     f"{int(5 * 8192 / max(td * 0.9, 1) / 60) + 1} phút mỗi máy.",
                     "Dây mạng loại cũ/đứt 1 cặp sợi, hoặc cổng switch 100 Mbps: thay dây Cat5e/Cat6, "
                     "cắm sang cổng Gigabit."))
    else:
        ra.append(_m(f"Tốc độ mạng ({iface})", "ok", f"{td} Mbps."))
    co_ip = _sh(["ip", "-o", "-4", "addr", "show", iface])[1]
    if pxe_bat and kieu in ("truc_tiep", "mang_khong_dhcp"):
        from . import pxe as _pxe
        if _pxe.PI_IP not in co_ip:
            ra.append(_m("Địa chỉ của Pi", "loi", f"PXE đang bật nhưng {iface} không có {_pxe.PI_IP}.",
                         "Tắt PXE rồi bật lại."))
    elif not co_ip:
        ra.append(_m("Địa chỉ của Pi", "canh" if kieu == "mang_co_dhcp" else "info",
                     f"{iface} chưa có địa chỉ IP.",
                     "Chế độ \"mạng có sẵn DHCP\" cần Pi nhận IP từ router: kiểm tra dây vào đúng mạng."))
    return ra


def _muc_dhcp(iface, kieu, pxe_bat):
    ds = do_dhcp(iface) if iface else None
    if ds is None:
        return [_m("Máy chủ DHCP trên mạng", "info", "Không dò được (cổng mạng chưa sẵn sàng).")]
    cua_pi = _ip_cua_pi()
    la = [x for x in ds if x["may_chu"] not in cua_pi]
    ten = ", ".join(f'{x["may_chu"]} (cấp {x["cap_ip"]})' for x in la)
    if kieu == "mang_co_dhcp":
        if la:
            return [_m("Máy chủ DHCP trên mạng", "ok", f"Có: {ten}. Đúng với chế độ \"mạng có sẵn DHCP\".")]
        return [_m("Máy chủ DHCP trên mạng", "loi",
                   "KHÔNG thấy máy chủ DHCP nào - chế độ \"mạng có sẵn DHCP\" sẽ không ai cấp IP cho máy cài.",
                   "Đổi sang chế độ \"mạng không có DHCP\" (Pi tự cấp IP) hoặc \"trực tiếp\".")]
    if la:
        return [_m("Máy chủ DHCP lạ", "loi",
                   f"Có DHCP khác trên dây mạng: {ten}. Máy cài sẽ nhận IP lộn xộn giữa 2 bên, "
                   "boot lúc được lúc không.",
                   "Dùng chế độ \"mạng có sẵn DHCP\" (Pi chỉ chỉ đường boot, không cấp IP), hoặc rút "
                   "dây khỏi mạng của khách và cắm thẳng/switch riêng.")]
    return [_m("Máy chủ DHCP lạ", "ok", "Không có DHCP nào khác - Pi tự cấp IP an toàn." if pxe_bat
               else "Không có DHCP nào trên dây mạng này - dùng chế độ \"trực tiếp\" hoặc \"mạng không có DHCP\".")]


def _muc_dich_vu(pxe_bat):
    if not pxe_bat:
        return [_m("PXE", "canh", "PXE đang TẮT - máy khách boot qua mạng chưa thấy menu.",
                   "Bật ở tab Bật / Tắt PXE.")]
    ra = []
    from . import pxe as _pxe
    for don_vi, ten in ((_pxe.DON_VI_SYSTEMD, "DHCP/TFTP (dnsmasq)"), ("smbd", "Chia sẻ file (Samba)"),
                        ("nginx", "Máy chủ web (HTTP)")):
        rc, out = _sh(["systemctl", "is-active", don_vi])
        if out == "active":
            ra.append(_m(ten, "ok", "Đang chạy."))
        else:
            ra.append(_m(ten, "loi", f"Không chạy ({out or 'không rõ'}).", "Tắt PXE rồi bật lại; vẫn lỗi thì "
                         f"xem nhật ký: journalctl -u {don_vi}"))
    from . import pxemenu as _pm
    n = len(_pm.muc_menu())
    ra.append(_m("Menu PXE", "ok" if n else "loi", f"{n} kịch bản trong menu." if n else
                 "Menu chưa có kịch bản nào.", "" if n else "Tạo kịch bản Windows rồi bấm \"Cập nhật menu\"."))
    return ra


def _muc_luu_tru():
    ra = []
    try:
        st = os.statvfs(_d.DEPLOY_DIR)
        con = st.f_bavail * st.f_frsize / 1024 ** 3
    except OSError:
        con = -1
    if 0 <= con < 3:
        ra.append(_m("Chỗ trống", "loi", f"Chỉ còn {con:.1f} GB.", "Xóa bớt hệ điều hành / phần mềm không dùng."))
    elif con >= 0:
        ra.append(_m("Chỗ trống", "ok" if con >= 10 else "canh", f"Còn {con:.1f} GB."))
    rc, nguon = _sh(["findmnt", "-n", "-o", "SOURCE", "--target", _d.DEPLOY_DIR])
    if "mmcblk" in nguon:
        ra.append(_m("Nơi chứa bộ cài", "info",
                     "Bộ cài nằm trên thẻ SD (đọc ~40 MB/s): cài 1-2 máy một lúc thì ổn, nhiều máy cùng "
                     "lúc sẽ chậm vì thẻ đọc không kịp mạng.",
                     "Cài nhiều máy cùng lúc: dùng SSD cắm cổng USB 3 (cổng xanh) cho dữ liệu."))
    return ra


def _muc_dong_ho(co_domain):
    rc, out = _sh(["timedatectl", "show", "-p", "NTPSynchronized", "--value"])
    if out == "yes":
        return [_m("Đồng hồ", "ok", "Đã đồng bộ giờ qua mạng.")]
    return [_m("Đồng hồ", "canh" if co_domain else "info",
               "Đồng hồ Pi chưa đồng bộ giờ qua mạng (Pi không có pin giữ giờ)."
               + (" Gia nhập domain cần giờ máy cài lệch AD dưới 5 phút." if co_domain else ""),
               "Cho Pi ra Internet một lúc, hoặc chỉnh giờ ở Cài đặt.")]


def _phan_giai(ten, cho=3.0):
    kq = {}

    def chay():
        try:
            kq["ip"] = sorted({a[4][0] for a in socket.getaddrinfo(ten, 389, socket.AF_INET)})
        except OSError as e:
            kq["loi"] = str(e)
    t = threading.Thread(target=chay, daemon=True)
    t.start()
    t.join(cho)
    return kq.get("ip"), kq.get("loi", "quá giờ")


def _muc_kichban(kieu):
    from . import pxemenu as _pm
    ra = []
    ds = _pm.kichban_windows()
    if not ds:
        return [_m("Kịch bản Windows", "loi", "Chưa có kịch bản Windows nào.", "Tạo ở tab Kịch bản.")]
    co_domain = False
    wim_da_xem = {}
    co_driver = {x["id"]: x for x in _d.danh_sach_driver()}
    for kb in ds:
        ten = kb.get("ten_kichban", kb["_file"])
        d = _d.cauhinh_tu_kichban(kb)
        van_de, muc_do = [], "ok"
        thieu = _d.thieu_gi(d)
        if thieu:
            van_de.append("thiếu: " + ", ".join(thieu))
            muc_do = "loi"
        os_id = d.get("os_id") or ""
        if os_id:
            for loai, p in (("boot.wim", _d.duong_boot_wim(os_id)), ("install.wim", _d.duong_install_wim(os_id))):
                if p not in wim_da_xem:
                    wim_da_xem[p] = _kiem_wim(p)
                if wim_da_xem[p]:
                    van_de.append(f"{loai}: {wim_da_xem[p]}")
                    muc_do = "loi"
        for di in d.get("driver_ids") or []:
            dr = co_driver.get(di)
            if not dr:
                van_de.append(f"gói driver \"{di}\" không còn")
                muc_do = "loi" if muc_do == "loi" else "canh"
            elif not dr["so_inf"]:
                van_de.append(f"gói driver \"{dr['ten_hien_thi']}\" chưa có file .inf")
                muc_do = "loi" if muc_do == "loi" else "canh"
        dom = (d.get("domain") or "").strip()
        sua = ""
        if dom:
            co_domain = True
            if kieu in ("truc_tiep", "mang_khong_dhcp"):
                van_de.append(f"gia nhập domain {dom} nhưng chế độ PXE đang là mạng riêng của Pi - máy cài "
                              "không thấy máy chủ AD, sẽ cài xong mà KHÔNG vào domain")
                muc_do = "loi" if muc_do == "loi" else "canh"
                sua = "Kịch bản có domain: dùng chế độ \"mạng có sẵn DHCP\" trên mạng có AD."
            else:
                ips, loi = _phan_giai(dom)
                if ips:
                    van_de.append(f"domain {dom} → {', '.join(ips[:3])} (DNS mạng này thấy AD)")
                else:
                    van_de.append(f"KHÔNG tra được domain {dom} qua DNS mạng này ({loi}) - máy cài sẽ "
                                  "không vào được domain")
                    muc_do = "loi" if muc_do == "loi" else "canh"
                    sua = "DHCP của mạng phải cấp DNS là máy chủ AD (không phải 8.8.8.8 / DNS nhà mạng)."
        if not van_de:
            van_de.append(f"đủ file, cài phiên bản Pro (chỉ số {_d.chi_so_anh_pro(os_id)})")
        ra.append(_m(f"Kịch bản: {ten}", muc_do, "; ".join(van_de), sua))
    return ra, co_domain


def _kiem_wim(p):
    """'' = tot; nguoc lai mo ta loi. Doc header + bang XML cuoi file (wiminfo, ~1 giay)
    -> bat duoc file chep do dang / hong ma khong phai doc het 5 GB."""
    if not os.path.isfile(p):
        return "không có file"
    try:
        with open(p, "rb") as f:
            if f.read(8) != b"MSWIM\0\0\0":
                return "không phải file WIM hợp lệ"
    except OSError as e:
        return f"không đọc được ({e})"
    rc, out = _sh(["wiminfo", p], timeout=60)
    if rc == -1:
        return ""                       # khong co wimlib - bo qua buoc nay
    if rc != 0:
        return "file hỏng hoặc chép dở dang (wiminfo báo lỗi) - tải lại hệ điều hành"
    return ""


def kiem_tra():
    from . import pxe as _pxe
    from . import pxemenu as _pm
    pxe_bat = _pxe.dang_bat()
    kieu = _pxe.kieu_dang_bat() or _pm.doc_cauhinh()["kieu_boot"]
    iface = _pxe.cong()
    ra = []
    for dat, nhan, chi_tiet in _pxe.trang_thai_chuan_bi():
        ra.append(_m(nhan, "ok" if dat else "loi", chi_tiet))
    ra += _muc_dich_vu(pxe_bat)
    ra += _muc_mang(iface, kieu, pxe_bat)
    ra += _muc_dhcp(iface, kieu, pxe_bat)
    ra += _muc_luu_tru()
    kb, co_domain = _muc_kichban(kieu) if _pm.kichban_windows() else (
        [_m("Kịch bản Windows", "loi", "Chưa có kịch bản Windows nào.", "Tạo ở tab Kịch bản.")], False)
    ra += _muc_dong_ho(co_domain)
    ra += kb
    from .duongdan import FILE_KHOA_SAMBA
    if not os.path.isfile(FILE_KHOA_SAMBA):
        ra.append(_m("Tài khoản chia sẻ file", "loi", "Thiếu mật khẩu tài khoản Samba của Console System.",
                     "Chạy lại cập nhật Console System."))
    return {"kieu": kieu, "pxe_bat": pxe_bat, "cong": iface, "muc": ra,
            "so_loi": sum(1 for x in ra if x["muc_do"] == "loi"),
            "so_canh": sum(1 for x in ra if x["muc_do"] == "canh")}
