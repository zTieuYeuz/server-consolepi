# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console System - BAT MAY TU XA (Wake-on-LAN) hang loat.

VI SAO (anh Thoai 14/10/2026, muc 9): cai lai ca phong may (phong lab, phong ke toan...)
thi phai di bat tung may. Nay chon may (lay san tu Lich su cai dat - MAC da biet) hoac dan
danh sach MAC, bam 1 nut -> Pi gui "goi tin danh thuc" (magic packet) cho tat ca.

GOI TIN (chuan AMD Magic Packet, NIC nao co WoL cung hieu): 6 byte FF + 16 lan MAC. Gui
3 kieu cung luc vi moi hang NIC/switch "nghe" khac nhau - ton vai tram byte, khong hai gi:
  - UDP broadcast 255.255.255.255 cong 9 va cong 7, ra TUNG card mang (SO_BINDTODEVICE)
  - UDP toi dia chi broadcast cua tung mang con (vd 192.168.110.255)
  - Khung Ethernet EtherType 0x0842 (kieu WoL "tran", khong can IP) ra tung card
Goi tin broadcast KHONG qua router: may o VLAN khac thi nhap them dia chi broadcast cua
VLAN do (router phai cho phep "directed broadcast").

GIOI HAN THAT (ghi ro tren trang): may phai bat Wake on LAN trong BIOS + tat ErP/Deep
Sleep, va con cam dien + day mang. Danh thuc xong may khoi dong theo thu tu boot cua BIOS -
muon may vao thang menu PXE thi dat "Network/PXE" len dau (menu PXE het gio tu vao o cung,
khong bao gio tu cai).
"""
import ipaddress
import json
import os
import re
import socket
import subprocess
import threading
import time

from .duongdan import THU_MUC_DU_LIEU
from consolesystem.core.esc import esc_html_rong as _esc

FILE_MAY = os.path.join(THU_MUC_DU_LIEU, "wol-may.json")   # may them tay (MAC + ten)
CONG = (9, 7)
_khoa = threading.Lock()


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


# ------------------------------------------------------------ danh sach may them tay
def doc_may():
    try:
        with open(FILE_MAY, encoding="utf-8") as f:
            d = json.load(f)
        return [x for x in d if isinstance(x, dict) and chuan_mac(x.get("mac"))] if isinstance(d, list) else []
    except (OSError, ValueError):
        return []


def _ghi_may(ds):
    os.makedirs(THU_MUC_DU_LIEU, exist_ok=True)
    tam = FILE_MAY + ".tmp"
    with open(tam, "w", encoding="utf-8") as f:
        json.dump(ds, f, ensure_ascii=False, indent=1)
    os.replace(tam, FILE_MAY)


def them_may(van_ban):
    """Moi dong: MAC [ten]. Tra ve (so them, so dong loi)."""
    with _khoa:
        ds = doc_may()
        co = {x["mac"] for x in ds}
        them = loi = 0
        for dong in (van_ban or "").splitlines():
            dong = dong.strip()
            if not dong:
                continue
            m = re.match(r"^([0-9A-Fa-f]{2}(?:[:-]?[0-9A-Fa-f]{2}){5})\s*[,;\t ]?\s*(.*)$", dong)
            mac = chuan_mac(m.group(1)) if m else ""
            if not mac:
                loi += 1
                continue
            ten = (m.group(2) or "").strip()[:64]
            if mac in co:
                for x in ds:
                    if x["mac"] == mac and ten:
                        x["ten"] = ten
                continue
            ds.append({"mac": mac, "ten": ten})
            co.add(mac)
            them += 1
        try:
            _ghi_may(ds[:1000])
        except OSError:
            return 0, loi
    return them, loi


def xoa_may(cac_mac):
    cac = {chuan_mac(m) for m in cac_mac or []}
    with _khoa:
        ds = doc_may()
        moi = [x for x in ds if x["mac"] not in cac]
        try:
            _ghi_may(moi)
        except OSError:
            return 0
    return len(ds) - len(moi)


def tat_ca_may():
    """May them tay + may trong Lich su cai dat (MAC moi nhat)."""
    from . import lichsu as _ls
    ra = {}
    for x in doc_may():
        ra[x["mac"]] = {"mac": x["mac"], "ten": x.get("ten", ""), "nguon": "tay",
                        "model": "", "luc": 0}
    for mac, b in _ls.may_da_biet().items():
        r = ra.setdefault(mac, {"mac": mac, "ten": "", "nguon": "lichsu"})
        r["ten"] = r.get("ten") or b.get("ten_may", "")
        r["model"] = " ".join(x for x in (b.get("hang"), b.get("model")) if x)
        r["luc"] = b.get("bat_dau", 0)
        if r["nguon"] == "tay":
            r["nguon"] = "ca_hai"
    return sorted(ra.values(), key=lambda x: (-(x.get("luc") or 0), x["ten"], x["mac"]))


# ---------------------------------------------------------------- giao dien
def register_wol(app):
    from flask import redirect, request, flash, get_flashed_messages
    from .layout import render_page
    from . import deployos as _d
    import html as _h


    @app.route("/deployos/caidat/wol")
    def deployos_wol():
        tin = "".join(
            f'<div class="msg {"ok" if cat == "ok" else "err"}">{nd}</div>'
            for cat, nd in get_flashed_messages(with_categories=True))
        ds = tat_ca_may()
        hang = ""
        for m in ds:
            nguon = {"tay": "thêm tay", "lichsu": "lịch sử cài", "ca_hai": "thêm tay + lịch sử"}[m["nguon"]]
            from .lichsu import gio
            hang += f"""<tr>
              <td><input type="checkbox" name="mac" value="{_esc(m['mac'])}" form="wol-gui"></td>
              <td><strong>{_esc(m['ten'] or '—')}</strong><br><small style="color:#8b93a1;">{_esc(m['model'])}</small></td>
              <td><code>{_esc(m['mac'])}</code></td>
              <td><small style="color:#8b93a1;">{_esc(nguon)}{('<br>cài lần cuối ' + _esc(gio(m['luc']))) if m.get('luc') else ''}</small></td>
            </tr>"""
        cards = card_mang()
        card_txt = ", ".join(f"{t} ({', '.join(b)})" for t, _m, b in cards) or "không có card nào có IP"
        bang = f"""
          <div class="tbl-scroll"><table data-pt="25" data-pt-tim="1">
            <tr><th style="width:28px;"><input type="checkbox" id="wol-tat-ca" title="Chọn cả trang"></th>
                <th>Máy</th><th>MAC</th><th>Nguồn</th></tr>
            {hang}
          </table></div>""" if ds else (
            '<p style="color:#8b93a1;">Chưa có máy nào. Máy cài qua PXE tự có ở đây '
            '(lấy MAC từ Lịch sử cài đặt), hoặc thêm tay ở khung bên dưới.</p>')
        body = _d.tabs_deployos("caidat", "wol") + tin + f"""
        <div class="card">
          <h3>Bật máy từ xa (Wake-on-LAN)</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 8px;">
            Chọn máy rồi bấm <strong>Bật các máy đã chọn</strong>: Console System gửi gói tin
            đánh thức qua mọi card mạng (hiện tại: {_esc(card_txt)}).
            Máy phải <strong>bật Wake on LAN trong BIOS</strong> (tắt ErP / Deep Sleep), còn cắm
            điện và dây mạng. Muốn máy tự vào menu cài đặt thì đặt <strong>Network/PXE boot
            lên đầu</strong> trong BIOS &mdash; menu PXE hết giờ tự vào ổ cứng nên không bao giờ
            tự cài.</p>
          {bang}
          <form id="wol-gui" method="POST" action="/deployos/caidat/wol/gui" style="margin-top:12px;">
            <label style="display:block;margin-bottom:8px;">Máy ở mạng/VLAN khác (không bắt buộc):
              địa chỉ broadcast của mạng đó, cách nhau dấu phẩy
              <input type="text" name="broadcast" placeholder="vd 192.168.20.255" style="max-width:320px;">
              <small style="color:#8b93a1;">(router phải cho phép "directed broadcast")</small></label>
            <button type="submit" {"" if ds else "disabled"}>Bật các máy đã chọn</button>
            <button type="submit" name="tat_ca" value="1" class="gray" {"" if ds else "disabled"}
              onclick="return confirm('Gửi tín hiệu bật tới TẤT CẢ {len(ds)} máy trong danh sách?');">Bật tất cả ({len(ds)})</button>
            <button type="submit" formaction="/deployos/caidat/wol/xoa" class="red small"
              onclick="return confirm('Bỏ các máy đã chọn khỏi danh sách thêm tay? (máy từ lịch sử cài vẫn còn)');">Bỏ máy thêm tay đã chọn</button>
          </form>
        </div>
        <div class="card">
          <h3>Thêm máy bằng tay</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 8px;">Mỗi dòng một máy: địa chỉ MAC,
            sau đó (không bắt buộc) tên máy. Ví dụ <code>00:1A:2B:3C:4D:5E Phong ke toan 01</code>.
            Dán được cả danh sách từ Excel.</p>
          <form method="POST" action="/deployos/caidat/wol/them">
            <textarea name="ds" rows="5" style="width:100%;" placeholder="00:1A:2B:3C:4D:5E  PC-KETOAN-01"></textarea>
            <button type="submit" style="margin-top:8px;">Thêm vào danh sách</button>
          </form>
        </div>
        <script>
        (function() {{
          var t = document.getElementById('wol-tat-ca');
          if (t) t.addEventListener('change', function() {{
            document.querySelectorAll('input[name=mac][form=wol-gui]').forEach(function(c) {{
              if (!c.closest('tr').classList.contains('pt-an')) c.checked = t.checked; }});
          }});
        }})();
        </script>"""
        if "data-pt=" in body:
            body += _d.JS_PHAN_TRANG_CHUNG
        return render_page(body, active="/deployos", title="Bật máy từ xa",
                           subtitle="Wake-on-LAN cho cả phòng máy", extra_css=_d.CSS_CHUNG)

    @app.route("/deployos/caidat/wol/gui", methods=["POST"])
    def deployos_wol_gui():
        if request.form.get("tat_ca"):
            macs = [m["mac"] for m in tat_ca_may()]
        else:
            macs = request.form.getlist("mac")
        bc = [x for x in re.split(r"[,\s]+", request.form.get("broadcast", "")) if x]
        if not macs:
            flash("Chưa chọn máy nào.", "err")
            return redirect("/deployos/caidat/wol")
        n, chi_tiet = gui(macs, 3, bc)
        nd = (f"Đã gửi tín hiệu bật tới <strong>{n}</strong> máy (3 lần, cách nhau 1 giây). "
              "Máy thường lên sau 5-30 giây.") if n else "Không gửi được tín hiệu."
        flash(nd + "<br><small>" + "<br>".join(_esc(x) for x in chi_tiet[:8]) + "</small>",
              "ok" if n else "err")
        return redirect("/deployos/caidat/wol")

    @app.route("/deployos/caidat/wol/them", methods=["POST"])
    def deployos_wol_them():
        them, loi = them_may(request.form.get("ds", ""))
        flash(f"Đã thêm {them} máy." + (f" {loi} dòng không có MAC hợp lệ - bỏ qua." if loi else ""),
              "ok" if them or not loi else "err")
        return redirect("/deployos/caidat/wol")

    @app.route("/deployos/caidat/wol/xoa", methods=["POST"])
    def deployos_wol_xoa():
        n = xoa_may(request.form.getlist("mac"))
        flash(f"Đã bỏ {n} máy thêm tay khỏi danh sách.", "ok")
        return redirect("/deployos/caidat/wol")
