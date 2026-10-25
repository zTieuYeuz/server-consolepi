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
import sys as _sys
from consolesystem.core.magic_packet import CONG, chuan_mac, goi_tin, card_mang, gui  # noqa: F401  (B3: dich vu dung chung o core)
_sys.modules["ui.wol"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import ipaddress
import json
import os
import re
import socket
import subprocess
import threading
import time

from ui.duongdan import THU_MUC_DU_LIEU
from consolesystem.core.esc import esc_html_rong as _esc

FILE_MAY = os.path.join(THU_MUC_DU_LIEU, "wol-may.json")   # may them tay (MAC + ten)
_khoa = threading.Lock()










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
    from ui import lichsu as _ls
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
    from ui.layout import render_page
    from ui import deployos as _d
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
            from ui.lichsu import gio
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
