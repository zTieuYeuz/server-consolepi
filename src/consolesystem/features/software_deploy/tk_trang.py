# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Trien khai phan mem - GIAO DIEN. Cac tab: Tai nguyen | Kho trung tam (dung chung voi Deployment OS, chi bo He dieu hanh /
Driver / WinPE) | Lap lich | May - nhom may | Kich ban | Trien khai | Chuc nang khac.
Du lieu: tk_dulieu.py. Dong co chay (WinRM + lap lich): tk_dongco.py.
"""
from consolesystem.core import taisan as _taisan
import sys as _sys
_sys.modules["ui.tk_trang"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import json
import os
import re
import time

from flask import jsonify, redirect, request, send_file, session

from ui import tk_dongco as DC
from ui import tk_dulieu as DL
from ui.layout import render_page, svg_icon
from consolesystem.core.esc import esc_none as _esc
from consolesystem.web.css_tk import CSS  # noqa: F401  (B3)
from consolesystem.core import duongdan as _DD
from consolesystem.core import magic_packet as _MP
from consolesystem.core import token_tai as _TT






def _tb():
    return session.pop("tk_tb", None)


def _chuyen(url, tb, ok=True):
    session["tk_tb"] = [str(tb)[:600], bool(ok)]
    return redirect(url)


def _trang(body, chinh, phu="", tieu_de="Triển khai phần mềm", phu_de=""):
    from ui import deployos as D
    tb = _tb()
    thong = ""
    if tb:
        thong = f'<div class="msg {"ok" if tb[1] else "err"}">{_esc(tb[0])}</div>'
    kiem = ""
    if not DC.co_san():
        kiem = ('<div class="msg warn">Chưa cài thư viện WinRM: chạy <code>sudo bash /opt/console-pi/tools/cai-winrm.sh</code> '
                "trong Terminal của Console System rồi tải lại trang.</div>")
    return render_page(CSS + D.tabs_deployos(chinh, phu) + thong + kiem + body, active="/deployos/trienkhai",
                       title=tieu_de, subtitle=phu_de or "Cài phần mềm hàng loạt qua mạng (WinRM)")


def _nut(nhan, bieu_tuong="", cls="", **kw):
    ic = svg_icon(bieu_tuong) if bieu_tuong else ""
    th = "".join(f' {k.replace("_", "-")}="{_esc(v)}"' for k, v in kw.items())
    return f'<button type="submit" class="tk-nut {cls}"{th}>{ic}{_esc(nhan)}</button>'


def _xac_nhan(hoi):
    return f'onsubmit="return confirm(this.dataset.hoi);" data-hoi="{_esc(hoi)}"'


# ================================================================== tai nguyen
def _cac_tai_nguyen():
    from ui import deployos as D
    return {
        "phanmem": [{"ref": a["ten"], "ten": a["ten"], "mo_ta": (a.get("tham_so") or D.tham_so_mac_dinh_app(a["ten"]) or "chưa điền tham số cài im lặng")}
                    for a in D.danh_sach_app()],
        "ungdung": [{"ref": u["id"], "ten": u["ten_hien_thi"], "mo_ta": u.get("lenh_cai") or "chưa có dòng lệnh cài"}
                    for u in D.danh_sach_ungdung()],
        "script": [{"ref": s["ten"], "ten": s["ten"], "mo_ta": ""}
                   for s in D._liet_ke(_DD.SCRIPTS_DIR, _DD.EXT_SCRIPT)],
    }


def _trang_nhom_tn():
    tn = _cac_tai_nguyen()
    nhom = DL.NHOM_TN.doc()
    hang = ""
    for g in nhom:
        muc = "".join(f'<span class="tk-chip nhan" style="margin:2px;">{_esc(DC.TEN_LOAI_BUOC.get(m["loai"], m["loai"]))}: {_esc(m.get("ten"))}</span>'
                      for m in g.get("muc", []))
        hang += (f'<tr><td><b>{_esc(g["ten"])}</b></td><td>{muc or "(trống)"}</td><td style="white-space:nowrap;">'
                 f'<a class="tk-nut" href="/deployos/trienkhai/nhom-tn?sua={g["id"]}">Sửa</a> '
                 f'<form method="POST" action="/deployos/trienkhai/nhom-tn/xoa" style="display:inline;" {_xac_nhan("Xóa nhóm " + g["ten"] + "?")}>'
                 f'<input type="hidden" name="id" value="{g["id"]}">{_nut("Xóa", "", "do")}</form></td></tr>')
    bang = (f'<table class="tk-bang"><tr><th>Nhóm</th><th>Gồm</th><th></th></tr>{hang}</table>' if nhom
            else '<p class="tk-ghi">Chưa có nhóm nào. Nhóm giúp gom nhiều phần mềm/script thành một gói để thêm vào kịch bản bằng một lần chọn.</p>')
    sua = DL.tim(nhom, request.args.get("sua", ""))
    da = {(m["loai"], m["ref"]) for m in (sua or {}).get("muc", [])}
    khoi = ""
    for loai, ds in tn.items():
        if not ds:
            continue
        khoi += f'<h4 class="tk-tieude">{_esc(DC.TEN_LOAI_BUOC[loai])}</h4><div class="tk-luoi">'
        for t in ds:
            tick = " checked" if (loai, t["ref"]) in da else ""
            khoi += (f'<label class="tk-o"><input type="checkbox" name="muc" value="{loai}|{_esc(t["ref"])}"{tick}>'
                     f'<span><b>{_esc(t["ten"])}</b><small>{_esc(t["mo_ta"])}</small></span></label>')
        khoi += "</div>"
    if not khoi:
        khoi = ('<p class="tk-ghi">Chưa có tài nguyên nào. Thêm ở các mục Phần mềm, Ứng dụng, Script phía trên, '
                "hoặc tải từ tab <b>Kho trung tâm</b>.</p>")
    body = f"""
    <h2>Nhóm tài nguyên</h2>
    <div class="card">{bang}</div>
    <h2>{"Sửa nhóm" if sua else "Tạo nhóm mới"}</h2>
    <div class="card"><form method="POST" action="/deployos/trienkhai/nhom-tn/luu" class="tk-f">
      <input type="hidden" name="id" value="{_esc(sua["id"]) if sua else ""}">
      <label>Tên nhóm</label><input type="text" name="ten" required value="{_esc(sua["ten"]) if sua else ""}" placeholder="Ví dụ: Bộ phần mềm văn phòng">
      <label>Chọn các tài nguyên đưa vào nhóm (theo thứ tự cài: Phần mềm, Ứng dụng, rồi Script)</label>{khoi}
      {_nut("Lưu nhóm", "save", "chinh")}
    </form></div>"""
    return _trang(body, "tainguyen", "nhom")


# ================================================================== lich
def _trang_lich():
    lich = DL.LICH.doc()
    kb = DL.KICH_BAN.doc()
    hang = ""
    for l in lich:
        dung = [k["ten"] for k in kb if k.get("lich_id") == l["id"] and not k.get("tam")]
        tiep = DL.lan_hen_ke_tiep(l)
        hang += (f'<tr><td><b>{_esc(l["ten"])}</b></td><td>{_esc(DL.mo_ta_lich(l))}</td>'
                 f'<td>{_esc(tiep.strftime("%d/%m/%Y %H:%M")) if tiep else "—"}</td>'
                 f'<td>{_esc(", ".join(dung)) or "chưa dùng"}</td><td style="white-space:nowrap;">'
                 f'<a class="tk-nut" href="/deployos/trienkhai/lich?sua={l["id"]}">Sửa</a> '
                 f'<form method="POST" action="/deployos/trienkhai/lich/xoa" style="display:inline;" {_xac_nhan("Xóa lịch " + l["ten"] + "?")}>'
                 f'<input type="hidden" name="id" value="{l["id"]}">{_nut("Xóa", "", "do")}</form></td></tr>')
    bang = (f'<table class="tk-bang"><tr><th>Tên</th><th>Khi nào</th><th>Lần tới</th><th>Kịch bản dùng</th><th></th></tr>{hang}</table>'
            if lich else '<p class="tk-ghi">Chưa có lịch nào. Kịch bản không gắn lịch sẽ chạy ngay khi bấm Chạy.</p>')
    sua = DL.tim(lich, request.args.get("sua", "")) or {}
    kieu = sua.get("kieu", "hang_ngay")

    def chon(v, nhan):
        return f'<option value="{v}"{" selected" if kieu == v else ""}>{nhan}</option>'
    thu = "".join(f'<label><input type="checkbox" name="thu" value="{i}"{" checked" if i in sua.get("thu", []) else ""}>{t}</label>'
                  for i, t in enumerate(DL.THU))
    thang = "".join(f'<option value="{i}"{" selected" if sua.get("thang") == i else ""}>Tháng {i}</option>' for i in range(1, 13))
    body = f"""
    <h2>Lịch đã tạo</h2><div class="card">{bang}</div>
    <h2>{"Sửa lịch" if sua else "Tạo lịch mới"}</h2>
    <div class="card"><form method="POST" action="/deployos/trienkhai/lich/luu" class="tk-f" id="f-lich">
      <input type="hidden" name="id" value="{_esc(sua.get("id", ""))}">
      <label>Tên lịch (để dễ nhớ)</label><input type="text" name="ten" required value="{_esc(sua.get("ten", ""))}" placeholder="Ví dụ: 2 giờ sáng thứ 7 hằng tuần">
      <label>Lặp lại</label>
      <select name="kieu" id="lich-kieu">{chon("mot_lan", "Một lần duy nhất")}{chon("hang_ngay", "Hằng ngày")}{chon("hang_tuan", "Hằng tuần (chọn thứ)")}
        {chon("hang_thang", "Hằng tháng (chọn ngày trong tháng)")}{chon("hang_nam", "Hằng năm (chọn tháng và ngày)")}</select>
      <label>Giờ chạy</label><input type="time" name="gio" required value="{_esc(sua.get("gio", "02:00"))}">
      <div data-k="mot_lan"><label>Ngày chạy</label><input type="date" name="ngay" value="{_esc(sua.get("ngay", ""))}"></div>
      <div data-k="hang_tuan"><label>Những ngày trong tuần</label><div class="tk-thu">{thu}</div></div>
      <div data-k="hang_nam"><label>Tháng</label><select name="thang">{thang}</select></div>
      <div data-k="hang_thang hang_nam"><label>Ngày trong tháng (nếu tháng ngắn hơn thì chạy vào ngày cuối tháng)</label>
        <input type="number" name="ngay_thang" min="1" max="31" value="{_esc(sua.get("ngay_thang", 1))}"></div>
      <div data-k="hang_ngay hang_tuan hang_thang hang_nam"><label>Chỉ chạy trong khoảng (bỏ trống nếu không giới hạn)</label>
        <div class="tk-hang"><span>Từ ngày</span><input type="date" name="tu_ngay" value="{_esc(sua.get("tu_ngay", ""))}">
        <span>đến ngày</span><input type="date" name="den_ngay" value="{_esc(sua.get("den_ngay", ""))}"></div></div>
      <p class="tk-ghi">Sau khi tạo, vào tab <b>Kịch bản</b> để gắn lịch này cho kịch bản. Lỡ giờ hẹn (Console System tắt) mà chưa quá 6 giờ thì vẫn chạy bù.</p>
      <div class="tk-hang" style="margin-top:14px;">{_nut("Lưu lịch", "save", "chinh")}
        {'<a class="tk-nut" href="/deployos/trienkhai/lich">Hủy</a>' if sua else ""}</div>
    </form></div>
    <script>(function(){{var s=document.getElementById('lich-kieu');function d(){{document.querySelectorAll('#f-lich [data-k]').forEach(function(e){{
      e.style.display=e.getAttribute('data-k').split(' ').indexOf(s.value)>=0?'':'none';}});}}s.onchange=d;d();}})();</script>"""
    return _trang(body, "lich")


# ================================================================== may - nhom may - tai khoan
def _tom_tat_may(m):
    b = m.get("bao_mat") or {}
    if not b:
        return '<span class="tk-ghi">chưa kiểm tra</span>'
    return f'<span class="tk-ghi">{_esc(DC.tom_tat_bao_mat(b))}</span>'


def _trang_may():
    may = DL.MAY.doc()
    nhom = DL.NHOM_MAY.doc()
    hang = ""
    forms_sua = ""
    for m in may:
        trong = ", ".join(g["ten"] for g in nhom if m["id"] in g.get("may", []))
        fid = "fm-" + m["id"]
        forms_sua += (f'<form id="{fid}" method="POST" action="/deployos/trienkhai/may/sua"><input type="hidden" name="id" value="{m["id"]}"></form>')
        hang += (f'<tr><td><input type="text" form="{fid}" name="ten" value="{_esc(m.get("ten"))}" placeholder="Tên dễ nhớ"></td>'
                 f'<td><code>{_esc(m["ip"])}</code></td>'
                 f'<td><input type="text" form="{fid}" name="mac" value="{_esc(m.get("mac"))}" placeholder="AA:BB:CC:DD:EE:FF" style="width:150px;"></td>'
                 f'<td class="an-hep">{_esc(trong) or "—"}</td><td class="an-hep">{_tom_tat_may(m)}</td>'
                 f'<td><div class="tk-act"><button type="submit" form="{fid}" class="tk-nut">Lưu</button> '
                 + (f'<a class="tk-nut" href="/deployos/trienkhai/may/{m["id"]}/kiemke">Kiểm kê</a> ' if m.get("kiem_ke") else "") +
                 f'<form method="POST" action="/deployos/trienkhai/may/kiemtra"><input type="hidden" name="id" value="{m["id"]}">{_nut("Kiểm tra", "refresh", "")}</form> '
                 f'<form method="POST" action="/deployos/trienkhai/may/xoa" {_xac_nhan("Xóa máy " + (m.get("ten") or m["ip"]) + " khỏi danh sách?")}>'
                 f'<input type="hidden" name="id" value="{m["id"]}">{_nut("Xóa", "", "do")}</form></div></td></tr>')
    bang = (f'<table class="tk-bang"><tr><th>Tên dễ nhớ</th><th>IP</th><th>MAC (để bật máy từ xa)</th><th class="an-hep">Nhóm</th><th class="an-hep">Bảo mật lần cuối</th><th></th></tr>{hang}</table>{forms_sua}'
            if may else '<p class="tk-ghi">Chưa có máy nào. Thêm bên dưới hoặc dùng tab <b>Quét mạng</b>.</p>')
    body = f"""
    <h2>Danh sách máy ({len(may)})</h2><div class="card" style="overflow:auto;">{bang}</div>
    <h2>Thêm máy</h2>
    <div class="card"><form method="POST" action="/deployos/trienkhai/may/them" class="tk-f">
      <label>Địa chỉ IP (một máy, hoặc dải kiểu 192.168.1.10-30, hoặc nhiều IP cách nhau bằng dấu phẩy)</label>
      <input type="text" name="ip" required placeholder="192.168.1.21">
      <label>Tên dễ nhớ (nếu thêm nhiều máy một lúc sẽ thành Tên 1, Tên 2...)</label>
      <input type="text" name="ten" placeholder="Ví dụ: Phòng kế toán">
      <label>Địa chỉ MAC (tuỳ chọn, chỉ khi thêm một máy)</label>
      <input type="text" name="mac" placeholder="AA:BB:CC:DD:EE:FF">
      <div style="margin-top:14px;">{_nut("Thêm vào danh sách", "plus", "chinh")}</div>
    </form></div>"""
    return _trang(body, "may", "ds")


def _chuan_mac(m):
    return _MP.chuan_mac(m)         # "" neu rong / toan 0 / broadcast / multicast


def _giai_ip(s):
    """'1.2.3.4', '1.2.3.10-30', 'a,b' -> list IP (toi da 256)."""
    import ipaddress
    ra = []
    for p in re.split(r"[,\s;]+", (s or "").strip()):
        if not p:
            continue
        m = re.fullmatch(r"(\d+\.\d+\.\d+\.)(\d+)-(\d+)", p)
        if m:
            a, b = int(m.group(2)), int(m.group(3))
            ra += [f"{m.group(1)}{i}" for i in range(min(a, b), max(a, b) + 1)]
        else:
            ra.append(p)
    ok = []
    for x in ra:
        try:
            ok.append(str(ipaddress.ip_address(x)))
        except ValueError:
            raise ValueError(f'"{x}" không phải địa chỉ IP hợp lệ.')
    if len(ok) > 256:
        raise ValueError("Tối đa 256 máy mỗi lần thêm.")
    return ok


def _them_may(ds, ip, ten, mac=""):
    if any(m["ip"] == ip for m in ds):
        return False
    ds.append({"id": DL.moi_id(), "ten": ten, "ip": ip, "mac": mac or DC.mac_tu_arp(ip)})
    return True


def _trang_nhom_may():
    may = DL.MAY.doc()
    nhom = DL.NHOM_MAY.doc()
    hang = ""
    ten_may = {m["id"]: (m.get("ten") or m["ip"]) for m in may}
    for g in nhom:
        tv = ", ".join(ten_may.get(i, "?") for i in g.get("may", []))
        hang += (f'<tr><td><b>{_esc(g["ten"])}</b></td><td>{len(g.get("may", []))} máy: {_esc(tv)}</td><td style="white-space:nowrap;">'
                 f'<a class="tk-nut" href="/deployos/trienkhai/may/nhom?sua={g["id"]}">Sửa</a> '
                 f'<form method="POST" action="/deployos/trienkhai/may/nhom/xoa" style="display:inline;" {_xac_nhan("Xóa nhóm " + g["ten"] + "?")}>'
                 f'<input type="hidden" name="id" value="{g["id"]}">{_nut("Xóa", "", "do")}</form></td></tr>')
    bang = (f'<table class="tk-bang"><tr><th>Nhóm</th><th>Thành viên</th><th></th></tr>{hang}</table>' if nhom
            else '<p class="tk-ghi">Chưa có nhóm máy nào.</p>')
    sua = DL.tim(nhom, request.args.get("sua", ""))
    da = set((sua or {}).get("may", []))
    luoi = "".join(f'<label class="tk-o"><input type="checkbox" name="may" value="{m["id"]}"{" checked" if m["id"] in da else ""}>'
                   f'<span><b>{_esc(m.get("ten") or m["ip"])}</b><small>{_esc(m["ip"])}</small></span></label>' for m in may)
    body = f"""
    <h2>Nhóm máy</h2><div class="card">{bang}</div>
    <h2>{"Sửa nhóm" if sua else "Tạo nhóm máy"}</h2>
    <div class="card"><form method="POST" action="/deployos/trienkhai/may/nhom/luu" class="tk-f">
      <input type="hidden" name="id" value="{_esc(sua["id"]) if sua else ""}">
      <label>Tên nhóm</label><input type="text" name="ten" required value="{_esc(sua["ten"]) if sua else ""}" placeholder="Ví dụ: Phòng kế toán">
      <label>Chọn máy trong nhóm (máy chưa có trong danh sách thì thêm ở tab Danh sách máy hoặc Quét mạng)</label>
      <div class="tk-luoi">{luoi or '<p class="tk-ghi">Chưa có máy nào trong danh sách.</p>'}</div>
      {_nut("Lưu nhóm", "save", "chinh")}
    </form></div>"""
    return _trang(body, "may", "nhom")


def _ip_may_chu():
    """IP ma may Windows dung de toi Console System: IP trong URL dang mo neu la IPv4, khong thi IP LAN chinh cua may."""
    import socket
    h = (request.host or "").split(":")[0]
    if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", h) and not h.startswith("127."):
        return h
    try:
        so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        so.connect(("10.255.255.255", 1))
        ip = so.getsockname()[0]
        so.close()
        return ip
    except OSError:
        return "IP-MAY-CHU"


def _lenh_bat_winrm():
    return f"powershell -ExecutionPolicy Bypass -File .\\bat-winrm.ps1 -ChiChoIP {_ip_may_chu()}"


def _trang_quet():
    may = DL.MAY.doc()
    body = f"""
    <div class="tk-canhbao"><b>Quét mạng</b> tìm các máy đang mở cổng WinRM (5985), SMB (445) hoặc RDP (3389) trong mạng LAN,
      kèm tên và địa chỉ MAC. Chọn máy muốn quản lý, đặt tên dễ nhớ rồi thêm vào danh sách (có thể tạo luôn một nhóm máy).<br>
      Máy cần cài phần mềm phải <b>bật WinRM</b> (cách dễ nhất: <a href="/deployos/trienkhai/bat-winrm.ps1">tải script bat-winrm.ps1</a> rồi trong PowerShell Administrator chạy <code>{_lenh_bat_winrm()}</code> (chỉ cho phép đúng máy Console System này kết nối; bỏ <code>-ChiChoIP ...</code> để mở cho cả mạng LAN; nếu chạy thẳng <code>.\\bat-winrm.ps1</code> Windows sẽ báo "running scripts is disabled"); hoặc thủ công <code>Enable-PSRemoting -Force</code>; máy không vào domain thêm
      <code>LocalAccountTokenFilterPolicy=1</code> - xem tab Kiểm tra bảo mật). Console System không tự bật hộ.</div>
    <div class="card">
      <form method="POST" action="/deployos/trienkhai/may/quet" class="tk-hang">
        <input type="text" name="cidr" placeholder="Dải mạng thêm (tuỳ chọn), ví dụ 192.168.2.0/24" style="max-width:320px;margin:0;height:42px;">
        {_nut("Quét mạng LAN", "search", "chinh")}
      </form>
      <p class="tk-ghi" id="q-tt">Chưa quét.</p>
    </div>
    <form method="POST" action="/deployos/trienkhai/may/quet/them" class="card tk-f" id="q-form" style="display:none;">
      <table class="tk-bang" id="q-bang"><tr><th></th><th>IP</th><th>Tên dễ nhớ</th><th>MAC</th><th>Cổng mở</th></tr></table>
      <label>Tạo luôn nhóm máy (tuỳ chọn): tên nhóm</label><input type="text" name="nhom" placeholder="Ví dụ: Phòng kế toán">
      <div style="margin-top:14px;">{_nut("Thêm các máy đã chọn", "plus", "chinh")}</div>
    </form>
    <script>(function(){{
      var co={json.dumps([m["ip"] for m in may])};
      function hoi(){{ fetch('/deployos/trienkhai/may/quet/tt').then(function(r){{return r.json();}}).then(function(d){{
        var tt=document.getElementById('q-tt'); tt.textContent = d.dang ? ('Đang quét... '+d.xong+'/'+d.tong) : (d.tong ? ('Đã quét '+d.tong+' địa chỉ, thấy '+d.ket_qua.length+' máy.') : 'Chưa quét.');
        var f=document.getElementById('q-form'), b=document.getElementById('q-bang'); f.style.display = d.ket_qua.length ? '' : 'none';
        while(b.rows.length>1) b.deleteRow(1);
        d.ket_qua.forEach(function(m){{ var r=b.insertRow(); var da=co.indexOf(m.ip)>=0;
          var c0=r.insertCell(); if(!da){{ var cb=document.createElement('input'); cb.type='checkbox'; cb.name='ip'; cb.value=m.ip; cb.checked=m.cong.indexOf('WinRM')>=0; c0.appendChild(cb); }} else c0.textContent='✓';
          r.insertCell().textContent=m.ip;
          var c2=r.insertCell(); if(!da){{ var t=document.createElement('input'); t.type='text'; t.name='ten_'+m.ip; t.value=m.ten||''; t.placeholder='Tên dễ nhớ'; c2.appendChild(t);
            var h=document.createElement('input'); h.type='hidden'; h.name='mac_'+m.ip; h.value=m.mac||''; c2.appendChild(h); }} else c2.textContent='đã có trong danh sách';
          r.insertCell().textContent=m.mac||''; r.insertCell().textContent=m.cong.join(', '); }});
        if(d.dang) setTimeout(hoi,1000); }}).catch(function(){{}}); }}
      hoi(); }})();</script>"""
    return _trang(body, "may", "quet")


def _trang_tai_khoan():
    tk = DL.tai_khoan_cong_khai()
    may = DL.MAY.doc()
    hang = "".join(
        f'<tr><td><b>{_esc(t["ten"])}</b></td><td><code>{_esc(t["user"])}</code></td><td>•••••••• (mã hóa)</td><td style="white-space:nowrap;">'
        f'<form method="POST" action="/deployos/trienkhai/may/taikhoan/xoa" style="display:inline;" {_xac_nhan("Xóa tài khoản " + t["ten"] + "?")}>'
        f'<input type="hidden" name="id" value="{t["id"]}">{_nut("Xóa", "", "do")}</form></td></tr>' for t in tk)
    bang = (f'<table class="tk-bang"><tr><th>Tên gợi nhớ</th><th>Tài khoản</th><th>Mật khẩu</th><th></th></tr>{hang}</table>' if tk
            else '<p class="tk-ghi">Chưa có tài khoản nào.</p>')
    opt_tk = "".join(f'<option value="{t["id"]}">{_esc(t["ten"])} ({_esc(t["user"])})</option>' for t in tk)
    opt_may = "".join(f'<option value="{m["id"]}">{_esc(m.get("ten") or m["ip"])} ({_esc(m["ip"])})</option>' for m in may)
    body = f"""
    <div class="tk-canhbao"><b>Tài khoản quản trị</b> là tài khoản Administrator trên máy cần cài (cục bộ hoặc tài khoản domain).
      Mật khẩu được <b>mã hóa</b> bằng khóa riêng của thiết bị và <b>không bao giờ hiện lại</b>. Kịch bản chọn tài khoản theo tên.
      Cần lưu vì kịch bản đã Chạy và lịch hẹn phải tự đăng nhập khi không có ai ngồi trước máy. Khóa nằm cùng ổ đĩa với dữ liệu nên chỉ chặn
      được việc đọc lộ file hay bản sao lưu, không chặn được người có quyền root trên thiết bị.</div>
    <h2>Tài khoản đã lưu</h2><div class="card">{bang}</div>
    <h2>Thêm tài khoản</h2>
    <div class="card"><form method="POST" action="/deployos/trienkhai/may/taikhoan/them" class="tk-f" autocomplete="off">
      <label>Tên gợi nhớ</label><input type="text" name="ten" required placeholder="Ví dụ: Admin phòng kế toán">
      <label>Tài khoản (administrator, hoặc CONGTY\\\\it01 với domain)</label><input type="text" name="user" required>
      <label>Mật khẩu</label><input type="password" name="mk" required autocomplete="new-password">
      <div style="margin-top:14px;">{_nut("Lưu tài khoản", "save", "chinh")}</div>
    </form></div>
    <h2>Thử đăng nhập</h2>
    <div class="card"><form method="POST" action="/deployos/trienkhai/may/taikhoan/thu" class="tk-hang">
      <select name="tk" style="margin:0;height:42px;">{opt_tk}</select><select name="may" style="margin:0;height:42px;">{opt_may}</select>
      {_nut("Thử kết nối WinRM", "go", "")}</form>
      <p class="tk-ghi">Kiểm tra tài khoản có vào được máy qua WinRM không, trước khi dùng trong kịch bản.</p></div>"""
    return _trang(body, "may", "tk")


# ================================================================== kich ban
def _ten_buoc(b):
    if b.get("loai") == "nhom":
        return "Nhóm: " + (b.get("ten") or b.get("ref", ""))
    return DC.nhan_buoc(b)


def _ds_buoc_html(k):
    return "".join(f"<div>{i + 1}. {_esc(_ten_buoc(b))}</div>" for i, b in enumerate(k.get("buoc", [])))


def _trang_kichban():
    kb = [k for k in DL.KICH_BAN.doc() if not k.get("tam")]
    lich = DL.LICH.doc()
    hang = ""
    for k in kb:
        l = DL.tim(lich, k.get("lich_id"))
        so_may = len(DC.may_cua_kich_ban(k))
        hang += (f'<tr><td><b>{_esc(k["ten"])}</b><div class="tk-ghi">{_esc(k.get("ghi_chu", ""))}</div></td>'
                 f'<td>{_ds_buoc_html(k)}</td>'
                 f'<td>{so_may} máy</td><td>{_esc(DL.mo_ta_lich(l)) if l else "Chạy ngay"}</td><td style="white-space:nowrap;">'
                 f'<a class="tk-nut" href="/deployos/trienkhai/kichban?sua={k["id"]}">Sửa</a> '
                 f'<form method="POST" action="/deployos/trienkhai/kichban/xoa" style="display:inline;" {_xac_nhan("Xóa kịch bản " + k["ten"] + "?")}>'
                 f'<input type="hidden" name="id" value="{k["id"]}">{_nut("Xóa", "", "do")}</form></td></tr>')
    bang = (f'<table class="tk-bang"><tr><th>Kịch bản</th><th>Các bước</th><th>Máy</th><th>Lịch</th><th></th></tr>{hang}</table>' if kb
            else '<p class="tk-ghi">Chưa có kịch bản nào. Tạo ở dưới, rồi sang tab <b>Triển khai</b> để bấm Chạy.</p>')
    sua = DL.tim(kb, request.args.get("sua", "")) or {}
    tn = _cac_tai_nguyen()
    nhom_tn = DL.NHOM_TN.doc()
    may = DL.MAY.doc()
    nhom_may = DL.NHOM_MAY.doc()
    tk = DL.tai_khoan_cong_khai()
    da_nm, da_m = set(sua.get("nhom_may", [])), set(sua.get("may", []))
    luoi_nm = "".join(f'<label class="tk-o"><input type="checkbox" name="nhom_may" value="{g["id"]}"{" checked" if g["id"] in da_nm else ""}>'
                      f'<span><b>{_esc(g["ten"])}</b><small>{len(g.get("may", []))} máy</small></span></label>' for g in nhom_may)
    luoi_m = "".join(f'<label class="tk-o"><input type="checkbox" name="may" value="{m["id"]}"{" checked" if m["id"] in da_m else ""}>'
                     f'<span><b>{_esc(m.get("ten") or m["ip"])}</b><small>{_esc(m["ip"])}</small></span></label>' for m in may)
    opt_lich = '<option value="">Chạy ngay khi bấm Chạy (không hẹn giờ)</option>' + "".join(
        f'<option value="{l["id"]}"{" selected" if sua.get("lich_id") == l["id"] else ""}>{_esc(l["ten"])} - {_esc(DL.mo_ta_lich(l))}</option>' for l in lich)
    opt_tk = '<option value="">-- chọn tài khoản quản trị --</option>' + "".join(
        f'<option value="{t["id"]}"{" selected" if sua.get("tai_khoan_id") == t["id"] else ""}>{_esc(t["ten"])} ({_esc(t["user"])})</option>' for t in tk)
    du_lieu = json.dumps({"tn": tn, "nhom": [{"ref": g["id"], "ten": g["ten"], "mo_ta": f'{len(g.get("muc", []))} mục'} for g in nhom_tn],
                          "buoc": sua.get("buoc", []), "ten_loai": DC.TEN_LOAI_BUOC, "nguon": DC.TEN_NGUON},
                         ensure_ascii=False).replace("</", "<\\/")
    body = f"""
    <h2>Kịch bản đã tạo</h2><div class="card" style="overflow:auto;">{bang}</div>
    <h2>{"Sửa kịch bản" if sua else "Tạo kịch bản mới"}</h2>
    <form method="POST" action="/deployos/trienkhai/kichban/luu" class="card tk-f" id="f-kb">
      <input type="hidden" name="id" value="{_esc(sua.get("id", ""))}"><input type="hidden" name="buoc_json" id="buoc-json">
      <label>Tên kịch bản</label><input type="text" name="ten" required value="{_esc(sua.get("ten", ""))}" placeholder="Ví dụ: Cài Chrome + 7-Zip cho phòng kế toán">
      <label>Ghi chú (tuỳ chọn)</label><input type="text" name="ghi_chu" value="{_esc(sua.get("ghi_chu", ""))}">
      <h4 class="tk-tieude">1. Các bước (chạy lần lượt từ trên xuống)</h4>
      <div id="ds-buoc"></div>
      <div class="tk-hang" style="margin-top:8px;"><select id="b-loai" style="margin:0;height:42px;max-width:240px;"></select>
        <input type="search" id="b-tim" placeholder="Tìm trong danh sách (gõ không dấu cũng được)" autocomplete="off" style="margin:0;height:42px;max-width:300px;">
        <select id="b-ref" style="margin:0;height:42px;max-width:420px;"></select>
        <input type="text" id="b-text" placeholder="Mã WinGet, ví dụ Google.Chrome" style="margin:0;height:42px;max-width:320px;display:none;">
        <span class="tk-ghi" id="b-so"></span>
        <button type="button" class="tk-nut" id="b-them">{svg_icon("plus")}Thêm bước</button></div>
      <p class="tk-ghi" id="b-ghi"></p>
      <h4 class="tk-tieude">2. Máy chạy kịch bản</h4>
      <p class="tk-ghi">Chọn nhóm máy và/hoặc từng máy. Tạo nhóm ở tab Máy - nhóm máy.</p>
      <div class="tk-luoi">{luoi_nm}</div><div class="tk-luoi">{luoi_m}</div>
      {'' if (nhom_may or may) else '<p class="tk-ghi">Chưa có máy nào, thêm ở tab Máy - nhóm máy.</p>'}
      <h4 class="tk-tieude">3. Lịch chạy</h4><select name="lich_id">{opt_lich}</select>
      <h4 class="tk-tieude">4. Tài khoản quản trị</h4><select name="tai_khoan_id" required>{opt_tk}</select>
      <div class="tk-hang" style="margin-top:18px;">{_nut("Lưu kịch bản", "save", "chinh")}
        {'<a class="tk-nut" href="/deployos/trienkhai/kichban">Hủy</a>' if sua else ""}</div>
    </form>
    <script id="kb-du-lieu" type="application/json">{du_lieu}</script>
    <script>{JS_KICHBAN}</script>"""
    return _trang(body, "kichban")


JS_KICHBAN = _taisan.doc("features/software_deploy/tk_trang.JS_KICHBAN.js")


# ================================================================== trien khai (chay / dung / popup)
def _dem_may(st):
    """Dem may theo 4 nhom: thanh cong / dang chay / cho (thu lai) / khong thanh cong."""
    d = {"xong": 0, "dang": 0, "cho": 0, "loi": 0}
    for m in ((st or {}).get("may") or {}).values():
        t = m.get("tt")
        if t == "xong":
            d["xong"] += 1
        elif t == "loi":
            d["loi"] += 1
        elif t == "dang":
            d["dang"] += 1
        elif t in ("cho", "offline", "cho_thu_lai"):
            d["cho"] += 1
    return d


def _chip_dem(d):
    """Cac the 'Thanh cong N', 'Dang chay N', 'Cho thu lai N', 'Khong thanh cong N' - chi hien nhom co may."""
    ra = ""
    for k, nhan, mau in (("xong", "Thành công", "xanh"), ("dang", "Đang chạy", "nhan"),
                         ("cho", "Chờ thử lại", "vang"), ("loi", "Không thành công", "do")):
        if d[k]:
            ra += f'<span class="tk-chip {mau}">{nhan} {d[k]}</span> '
    return ra


def _tom_tat_kb(kb, st):
    may = (st or {}).get("may", {})
    tong = len(may)
    if not st or not st.get("bat"):
        if st and tong:
            xong = sum(1 for m in may.values() if m["tt"] == "xong")
            return ("Đã dừng", "", xong, tong)
        return ("Chưa chạy", "", 0, tong)
    xong = sum(1 for m in may.values() if m["tt"] == "xong")
    loi = sum(1 for m in may.values() if m["tt"] == "loi")
    cho = sum(1 for m in may.values() if m["tt"] in ("offline", "cho_thu_lai"))
    if not st.get("slot"):
        return ("Đang chờ đến giờ hẹn", "nhan", 0, tong)
    if st.get("xong_luc"):
        return ("Xong lượt này, chờ lịch kế tiếp" if kb.get("lich_id") else "Đã xong", "xanh" if not loi else "vang", xong, tong)
    if cho:
        return (f"Đang chạy (chờ {cho} máy thử lại)", "vang", xong, tong)
    return ("Đang chạy", "nhan", xong, tong)


def _trang_trienkhai():
    kb = [k for k in DL.KICH_BAN.doc() if not k.get("tam")]
    tt = DL.TRANG_THAI.doc()
    lich = DL.LICH.doc()
    hang = ""
    for k in kb:
        st = tt.get(k["id"], {})
        nhan, mau, xong, tong = _tom_tat_kb(k, st)
        l = DL.tim(lich, k.get("lich_id"))
        bat = bool(st.get("bat"))
        chay_lai = bat and not k.get("lich_id") and st.get("xong_luc")
        nut = (f'<form method="POST" action="/deployos/trienkhai/chay" style="display:inline;"><input type="hidden" name="id" value="{k["id"]}">'
               f'{_nut("Chạy lại", "refresh", "xanh")}</form> <form method="POST" action="/deployos/trienkhai/dung" style="display:inline;">'
               f'<input type="hidden" name="id" value="{k["id"]}">{_nut("Dừng", "x", "do")}</form>' if chay_lai else
               f'<form method="POST" action="/deployos/trienkhai/dung" style="display:inline;"><input type="hidden" name="id" value="{k["id"]}">'
               f'{_nut("Dừng", "x", "do")}</form>' if bat else
               f'<form method="POST" action="/deployos/trienkhai/chay" style="display:inline;"><input type="hidden" name="id" value="{k["id"]}">'
               f'{_nut("Chạy", "go", "xanh")}</form>')
        pt = int(xong * 100 / tong) if tong else 0
        hang += (f'<tr><td><a href="#" class="tk-xem" data-id="{k["id"]}" data-ten="{_esc(k["ten"])}"><b>{_esc(k["ten"])}</b></a>'
                 f'<div class="tk-ghi">{_esc(DL.mo_ta_lich(l))}</div></td>'
                 f'<td><span class="tk-chip {mau}">{_esc(nhan)}</span><div class="tk-dem">{_chip_dem(_dem_may(st))}</div></td>'
                 f'<td><div class="tk-vach"><i style="width:{pt}%"></i></div><div class="tk-ghi">{xong}/{tong} máy thành công</div></td>'
                 f'<td class="an-hep">{_esc(DL.dinh_dang_gio(st.get("bat_dau"))) or "—"}</td>'
                 f'<td><div class="tk-act">{nut} <button type="button" class="tk-nut tk-xem" data-id="{k["id"]}" data-ten="{_esc(k["ten"])}">Xem tiến độ</button></div></td></tr>')
    bang = (f'<table class="tk-bang"><tr><th>Kịch bản</th><th>Trạng thái</th><th>Tiến độ</th><th class="an-hep">Lượt chạy gần nhất</th><th></th></tr>{hang}</table>' if kb
            else '<p class="tk-ghi">Chưa có kịch bản nào. Tạo ở tab <b>Kịch bản</b>.</p>')
    body = f"""
    <div class="tk-ghi">Bấm <b>Chạy</b> để kích hoạt: kịch bản được ghi nhớ và tự chạy theo lịch cho đến khi bấm <b>Dừng</b> (kể cả khi Console System khởi động lại).
      Mỗi máy được thử tối đa 3 lần, cách nhau 5 phút (máy đang tắt, mất mạng hoặc cài lỗi); quá 3 lần sẽ báo <b>Không thành công</b>.
      Bấm tên kịch bản để xem đang làm tới đâu.</div>
    <div class="tk-act" style="margin:10px 0;"><button type="button" class="tk-nut" id="tk-lam-moi">&#8635; Làm mới</button>
      <span class="tk-ghi" id="tk-lm-gio"></span></div>
    <div class="card" style="overflow:auto;" id="tk-khung-bang">{bang}</div>
    <script>
    (function(){{
      var b=document.getElementById('tk-lam-moi'), g=document.getElementById('tk-lm-gio'), dang=false;
      function lam(){{
        if(dang) return; dang=true; b.disabled=true;
        fetch(location.pathname+'?_='+Date.now(), {{cache:'no-store'}}).then(function(r){{return r.text();}}).then(function(h){{
          var d=new DOMParser().parseFromString(h,'text/html'), n=d.getElementById('tk-khung-bang');
          if(n) {{
            document.getElementById('tk-khung-bang').innerHTML=n.innerHTML;
            document.querySelectorAll('.tk-xem').forEach(function(a){{ if(a.id==='tk-lam-moi') return;
              a.onclick=function(ev){{ ev.preventDefault(); window.tkMoModal&&window.tkMoModal(a.getAttribute('data-id'), a.getAttribute('data-ten')); }}; }});
          }}
          g.textContent='Cập nhật lúc '+new Date().toLocaleTimeString('vi-VN');
        }}).catch(function(){{ g.textContent='Không làm mới được, thử lại.'; }}).then(function(){{ dang=false; b.disabled=false; }});
      }}
      b.onclick=lam; setInterval(function(){{ if(!document.hidden) lam(); }}, 10000);
    }})();
    </script>
    {_MODAL}<script>{JS_MODAL}</script>"""
    return _trang(body, "chay")


_MODAL = """<div class="tk-modal" id="tk-modal" hidden><div class="tk-mbox"><div class="tk-mdau"><h3 id="tk-mten"></h3>
  <span class="tk-chip" id="tk-mchip"></span><button type="button" class="tk-nut" id="tk-xoa-xong" title="Xóa các dòng máy đã thành công">Xóa dòng thành công</button><button type="button" class="tk-nut" id="tk-xoa-loi" title="Xóa các dòng máy không thành công">Xóa dòng lỗi</button><button type="button" class="tk-nut" id="tk-dong">Đóng</button></div>
  <div class="tk-mthan" id="tk-mthan"></div></div></div>"""

JS_MODAL = """
(function(){
  var id=null, timer=null, mo={}; var $=function(i){return document.getElementById(i);};
  var TT={cho:'Chờ',dang:'Đang chạy',xong:'Thành công',loi:'Không thành công',offline:'Chờ máy lên',cho_thu_lai:'Chờ thử lại',dung:'Đã dừng'};
  var MAU={xong:'xanh',loi:'do',dang:'nhan',offline:'vang',cho_thu_lai:'vang',cho:'',dung:''};
  function e(t,c,x){var n=document.createElement(t); if(c)n.className=c; if(x!=null)n.textContent=x; return n;}
  function gio(t){ if(!t) return ''; var d=new Date(t*1000); return d.toLocaleTimeString('vi-VN'); }
  function ve(d){
    var tong=0,xong=0,loiN=0; Object.keys(d.may).forEach(function(ip){tong++; if(d.may[ip].tt==='xong')xong++; if(d.may[ip].tt==='loi')loiN++;});
    var c=$('tk-mchip'); c.textContent=d.nhan; c.className='tk-chip '+(d.mau||'');
    var b=$('tk-mthan'); var giu=b.scrollTop; b.textContent='';
    var t=e('div','tk-hang'); t.appendChild(e('b',null,xong+' / '+tong+' máy thành công'+(loiN?' · '+loiN+' không thành công':'')));
    var v=e('div','tk-vach'); v.style.flex='1'; var i=e('i'); i.style.width=(tong?Math.round(xong*100/tong):0)+'%'; v.appendChild(i); t.appendChild(v);
    t.appendChild(e('span','tk-ghi',d.lich)); b.appendChild(t);
    if (!Object.keys(d.may).length) b.appendChild(e('p','tk-ghi','Chưa có lượt chạy nào. Bấm Chạy ở trang Triển khai để bắt đầu.'));
    Object.keys(d.may).forEach(function(ip){
      var m=d.may[ip], de=e('details','tk-may'); if(mo[ip]) de.open=true; de.ontoggle=function(){mo[ip]=de.open;};
      var s=e('summary'); s.appendChild(e('b',null,m.ten)); s.appendChild(e('span','tk-ghi',ip)); var sp=e('span'); sp.style.flex='1'; s.appendChild(sp);
      var done=m.buoc.filter(function(x){return x.tt==='ok';}).length; s.appendChild(e('span','tk-ghi',done+'/'+m.buoc.length+' bước'));
      s.appendChild(e('span','tk-chip '+(MAU[m.tt]||''),TT[m.tt]||m.tt));
      if (m.tt==='xong'||m.tt==='loi'){ var xb=e('button','tk-nut','✕'); xb.type='button'; xb.title='Xóa dòng này'; xb.onclick=function(ev){ ev.preventDefault(); ev.stopPropagation(); xoa('ip',ip); }; s.appendChild(xb); }
      de.appendChild(s);
      m.buoc.forEach(function(x,k){
        var r=e('div','tk-b '+x.tt); r.appendChild(e('span','dau',x.tt==='ok'?'✓':x.tt==='loi'?'✗':x.tt==='dang'?'…':(k+1)+'.'));
        var n=e('div'); n.appendChild(document.createTextNode(x.ten)); if(x.tb){ n.appendChild(e('small',null,x.tb)); } r.appendChild(n); de.appendChild(r); });
      if (m.tt==='offline'||m.tt==='cho_thu_lai'){ var r=e('div','tk-b'); r.appendChild(e('span','dau','↻')); r.appendChild(e('div','tk-ghi','Lần thử '+(m.thu||0)+'/3 chưa được. Thử lại lúc '+gio(m.tiep))); de.appendChild(r); }
      b.appendChild(de);
    });
    b.appendChild(e('h4','tk-tieude','Nhật ký')); b.appendChild(e('div','tk-nk',(d.nhat_ky||[]).slice().reverse().join('\\n')||'(chưa có)'));
    b.scrollTop=giu;
  }
  function xoa(loai,ip){ if(!id) return; if(loai!=='ip' && !confirm('Xóa các dòng kết quả này khỏi bảng tiến độ?')) return;
    fetch('/deployos/trienkhai/tt/'+id+'/xoa',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({loai:loai,ip:ip||''})}).then(function(){ clearTimeout(timer); hoi(); }); }
  $('tk-xoa-xong').onclick=function(){ xoa('xong'); }; $('tk-xoa-loi').onclick=function(){ xoa('loi'); };
  function hoi(){ if(!id) return; fetch('/deployos/trienkhai/tt/'+id).then(function(r){return r.json();}).then(ve).catch(function(){}); timer=setTimeout(hoi,2000); }
  function mo_(i,t){ id=i; mo={}; $('tk-mten').textContent=t; $('tk-modal').hidden=false; clearTimeout(timer); hoi(); }
  function dong(){ id=null; clearTimeout(timer); $('tk-modal').hidden=true; }
  document.querySelectorAll('.tk-xem').forEach(function(a){ a.onclick=function(ev){ ev.preventDefault(); mo_(a.getAttribute('data-id'), a.getAttribute('data-ten')); }; });
  window.tkMoModal=mo_;
  $('tk-dong').onclick=dong; $('tk-modal').onclick=function(ev){ if(ev.target===this) dong(); };
  document.addEventListener('keydown',function(ev){ if(ev.key==='Escape') dong(); });
  var h=(location.hash||'').replace('#xem=',''); if(/^[a-z0-9-]+$/.test(h)&&h){ var a=document.querySelector('.tk-xem[data-id="'+h+'"]'); mo_(h, a ? a.getAttribute('data-ten') : 'Chạy nhanh'); }
})();
"""


# ================================================================== chuc nang khac
def _trang_khac():
    may = DL.MAY.doc()
    tk = DL.tai_khoan_cong_khai()
    opt_tk = "".join(f'<option value="{t["id"]}">{_esc(t["ten"])} ({_esc(t["user"])})</option>' for t in tk)
    luoi = "".join(f'<label class="tk-o"><input type="checkbox" name="may" value="{m["id"]}"><span><b>{_esc(m.get("ten") or m["ip"])}</b>'
                   f'<small>{_esc(m["ip"])}</small></span></label>' for m in may)
    hang_bm = ""
    for m in may:
        b = m.get("bao_mat") or {}
        if not b:
            hang_bm += f'<tr><td><b>{_esc(m.get("ten") or m["ip"])}</b><div class="tk-ghi">{_esc(m["ip"])}</div></td><td colspan="5" class="tk-ghi">Chưa kiểm tra</td></tr>'
            continue
        av = b.get("av")
        bl = b.get("bitlocker")

        def chip(ok, dung, sai, ko=""):
            if ok is None:
                return f'<span class="tk-chip">{ko or "không rõ"}</span>'
            return f'<span class="tk-chip {"xanh" if ok else "do"}">{dung if ok else sai}</span>'
        tl = b.get("tuong_lua") or []
        cn = b.get("cap_nhat_cho")
        o_nho = ", ".join(f'{x["o"]} trống {x["trong_gb"]}/{x["tong_gb"]} GB' for x in b.get("o_dia", []))
        hang_bm += (f'<tr><td><b>{_esc(m.get("ten") or m["ip"])}</b><div class="tk-ghi">{_esc(b.get("os", ""))}</div></td>'
                    f'<td>{chip(None if av is None else bool(av.get("bat") and av.get("realtime")), "Bật", "Tắt")}</td>'
                    f'<td>{chip(None if not tl else all(x.get("bat") for x in tl), "Bật", "Có profile tắt")}</td>'
                    f'<td>{chip(None if bl is None else all(x.get("bao_ve") in ("On", "1") for x in bl), "Đã mã hóa", "Chưa/không đủ")}</td>'
                    f'<td>{"không rõ" if cn is None else (str(cn) + " đang chờ")}</td>'
                    f'<td class="tk-ghi">{_esc(o_nho)}<br>{_esc(DL.dinh_dang_gio(b.get("luc")))}</td></tr>')
    bang_bm = (f'<table class="tk-bang"><tr><th>Máy</th><th>Diệt virus</th><th>Tường lửa</th><th>BitLocker</th><th>Cập nhật chờ</th><th>Ổ đĩa / lúc kiểm</th></tr>{hang_bm}</table>'
               if may else '<p class="tk-ghi">Chưa có máy nào trong danh sách.</p>')
    body = f"""
    <h2>Trạng thái bảo mật các máy</h2>
    <div class="card" style="overflow:auto;">{bang_bm}</div>
    <h2>Chạy nhanh trên các máy đã chọn</h2>
    <form method="POST" action="/deployos/trienkhai/nhanh" class="card tk-f">
      <label>Chọn máy</label><div class="tk-luoi">{luoi or '<p class="tk-ghi">Chưa có máy nào trong danh sách.</p>'}</div>
      <label>Việc cần làm</label>
      <select name="viec" id="n-viec"><option value="baomat">Kiểm tra bảo mật ngay</option><option value="kiemke">Kiểm kê phần cứng và phần mềm</option><option value="rustdesk">Cài RustDesk (kèm máy chủ ID / chuyển tiếp)</option><option value="khoi_dong_lai">Khởi động lại</option>
        <option value="tat">Tắt máy</option><option value="bat">Bật máy (Wake-on-LAN)</option><option value="winget">Cài từ WinGet</option></select>
      <div id="n-wg" style="display:none;"><label>Mã gói WinGet (vd Google.Chrome, 7zip.7zip, VideoLAN.VLC)</label>
        <input type="text" name="winget" placeholder="Google.Chrome"></div>
      <label>Tài khoản quản trị (không cần khi bật máy bằng Wake-on-LAN)</label><select name="tk">{opt_tk}</select>
      <div style="margin-top:14px;">{_nut("Chạy ngay", "go", "chinh")}</div>
    </form>
    <h2>Chuẩn bị máy đích</h2>
    <div class="tk-canhbao"><b>Cách nhanh:</b> <a href="/deployos/trienkhai/bat-winrm.ps1">tải bat-winrm.ps1</a> về máy Windows, mở PowerShell <b>Run as Administrator</b> tại thư mục chứa file rồi chạy: <code>{_lenh_bat_winrm()}</code><br>
      (script làm đủ các bước 1 và 2 bên dưới, chỉ cho phép máy Console System này kết nối; thêm <code>-Tat</code> thay cho <code>-ChiChoIP</code> để tắt WinRM lại.)<br><br>
      Hoặc làm tay trên <b>từng máy Windows</b> cần cài phần mềm (một lần, bằng PowerShell chạy <b>Run as Administrator</b>):<br>
      1. <code>Enable-PSRemoting -Force -SkipNetworkProfileCheck</code> (bật WinRM, mở tường lửa cổng 5985)<br>
      2. Nếu máy <b>không vào domain</b>: <code>New-ItemProperty -Path HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System -Name LocalAccountTokenFilterPolicy -Value 1 -PropertyType DWord -Force</code><br>
      Có domain thì đẩy bằng Group Policy cho cả phòng máy. Console System không tự bật hộ vì đó là thay đổi cấu hình bảo mật của máy khác.</div>
    <script>(function(){{var s=document.getElementById('n-viec');s.onchange=function(){{document.getElementById('n-wg').style.display=s.value==='winget'?'':'none';}};}})();</script>"""
    return _trang(body, "khac")


# ================================================================== dang ky route
def register_trienkhai(app):
    from flask import abort

    DC.khoi_dong_bo_lap_lich()

    @app.before_request
    def _dat_ngu_canh():
        p = request.path
        nc = request.args.get("nc")
        if nc in ("tk", "os"):
            session["nc"] = nc
        elif p.startswith("/deployos/trienkhai") or p.startswith("/tk/"):
            session["nc"] = "tk"
        elif p == "/deployos" or re.match(r"^/deployos/(kichban|tiendo|caidat|lichsu|os|drivers|o-dia|console$|console/file|pxe)", p):
            session["nc"] = "os"

    @app.route("/tk/tai/<tok>/<ten>")
    def tk_tai(tok, ten):
        if not DC._noi_bo(request.remote_addr or ""):
            abort(403)
        duong = _TT.tra_token(tok, ten)
        if not duong:
            abort(404)
        return send_file(duong, as_attachment=True, download_name=ten)

    # ---- Trien khai
    @app.route("/deployos/trienkhai")
    def tk_trienkhai():
        return _trang_trienkhai()

    @app.route("/deployos/trienkhai/chay", methods=["POST"])
    def tk_chay():
        ok, tb = DC.kich_hoat(request.form.get("id", ""))
        return _chuyen("/deployos/trienkhai", tb, ok)

    @app.route("/deployos/trienkhai/dung", methods=["POST"])
    def tk_dung():
        ok, tb = DC.dung(request.form.get("id", ""))
        return _chuyen("/deployos/trienkhai", tb, ok)

    @app.route("/deployos/trienkhai/tt/<kb_id>")
    def tk_tt(kb_id):
        kb = DL.tim(DL.KICH_BAN.doc(), kb_id) or {}
        st = DL.TRANG_THAI.doc().get(kb_id, {})
        nhan, mau, _x, _t = _tom_tat_kb(kb, st)
        return jsonify({"nhan": nhan, "mau": mau, "lich": DL.mo_ta_lich(DL.tim(DL.LICH.doc(), kb.get("lich_id"))),
                        "may": st.get("may", {}), "nhat_ky": st.get("nhat_ky", [])})

    @app.route("/deployos/trienkhai/tt/<kb_id>/xoa", methods=["POST"])
    def tk_tt_xoa(kb_id):
        """Xoa dong ket qua cua may DA XONG hoac LOI khoi bang tien do (khong dong vao may dang chay/cho thu lai)."""
        j = request.get_json(silent=True) or {}
        loai, ip = j.get("loai", ""), j.get("ip", "")
        if loai not in ("xong", "loi", "ca-hai", "ip"):
            return jsonify({"ok": False, "loi": "Yêu cầu không hợp lệ."}), 400
        dem = [0]

        def ghi(tt):
            st = tt.get(kb_id)
            if not st:
                return
            may = st.get("may") or {}
            for k in list(may):
                t = may[k].get("tt")
                if t not in ("xong", "loi"):
                    continue
                if (loai == "ip" and k == ip) or loai == "ca-hai" or t == loai:
                    del may[k]
                    dem[0] += 1
            if dem[0]:
                DC._nhat_ky(st, "-", f"Đã xóa {dem[0]} dòng kết quả khỏi bảng tiến độ.")
        DC._luu(ghi)
        return jsonify({"ok": True, "da_xoa": dem[0]})

    @app.route("/deployos/trienkhai/bat-winrm.ps1")
    def tk_script_winrm():
        """Tai script bat WinRM tren may Windows (chay bang PowerShell Administrator)."""
        from flask import Response
        return Response(_taisan.doc("windows/bat-winrm.ps1").replace("\r\n", "\n").replace("\n", "\r\n"), mimetype="text/plain; charset=utf-8",
                        headers={"Content-Disposition": "attachment; filename=bat-winrm.ps1"})

    # ---- Lap lich
    @app.route("/deployos/trienkhai/lich")
    def tk_lich():
        return _trang_lich()

    @app.route("/deployos/trienkhai/lich/luu", methods=["POST"])
    def tk_lich_luu():
        l, loi = DL.chuan_lich(request.form)
        ten = (request.form.get("ten") or "").strip()
        if not ten:
            loi = "Đặt tên cho lịch."
        if loi:
            return _chuyen("/deployos/trienkhai/lich", loi, False)
        l["ten"] = ten
        lid = request.form.get("id", "")

        def ghi(ds):
            c = DL.tim(ds, lid)
            if c:
                c.clear()
                c.update(l, id=lid)
            else:
                ds.append(dict(l, id=DL.moi_id()))
        DL.LICH.sua(ghi)
        return _chuyen("/deployos/trienkhai/lich", f'Đã lưu lịch "{ten}".')

    @app.route("/deployos/trienkhai/lich/xoa", methods=["POST"])
    def tk_lich_xoa():
        lid = request.form.get("id", "")
        DL.LICH.sua(lambda ds: ds.__setitem__(slice(None), [x for x in ds if x["id"] != lid]))

        def go(ds):
            for k in ds:
                if k.get("lich_id") == lid:
                    k["lich_id"] = ""
        DL.KICH_BAN.sua(go)
        return _chuyen("/deployos/trienkhai/lich", "Đã xóa lịch.")

    # ---- Tai nguyen: nhom
    @app.route("/deployos/trienkhai/nhom-tn")
    def tk_nhom_tn():
        return _trang_nhom_tn()

    @app.route("/deployos/trienkhai/nhom-tn/luu", methods=["POST"])
    def tk_nhom_tn_luu():
        ten = (request.form.get("ten") or "").strip()
        tn = _cac_tai_nguyen()
        muc = []
        for v in request.form.getlist("muc"):
            loai, _, ref = v.partition("|")
            t = next((x for x in tn.get(loai, []) if x["ref"] == ref), None)
            if t:
                muc.append({"loai": loai, "ref": ref, "ten": t["ten"]})
        if not ten or not muc:
            return _chuyen("/deployos/trienkhai/nhom-tn", "Cần có tên nhóm và ít nhất một tài nguyên.", False)
        gid = request.form.get("id", "")

        def ghi(ds):
            c = DL.tim(ds, gid)
            if c:
                c.update(ten=ten, muc=muc)
            else:
                ds.append({"id": DL.moi_id(), "ten": ten, "muc": muc})
        DL.NHOM_TN.sua(ghi)
        return _chuyen("/deployos/trienkhai/nhom-tn", f'Đã lưu nhóm "{ten}".')

    @app.route("/deployos/trienkhai/nhom-tn/xoa", methods=["POST"])
    def tk_nhom_tn_xoa():
        gid = request.form.get("id", "")
        DL.NHOM_TN.sua(lambda ds: ds.__setitem__(slice(None), [x for x in ds if x["id"] != gid]))
        return _chuyen("/deployos/trienkhai/nhom-tn", "Đã xóa nhóm.")

    # ---- May
    @app.route("/deployos/trienkhai/may")
    def tk_may():
        return _trang_may()

    @app.route("/deployos/trienkhai/may/them", methods=["POST"])
    def tk_may_them():
        try:
            ips = _giai_ip(request.form.get("ip", ""))
        except ValueError as e:
            return _chuyen("/deployos/trienkhai/may", str(e), False)
        ten, mac = (request.form.get("ten") or "").strip(), _chuan_mac(request.form.get("mac"))
        them = []

        def ghi(ds):
            for i, ip in enumerate(ips):
                t = ten if len(ips) == 1 else (f"{ten} {i + 1}" if ten else "")
                if _them_may(ds, ip, t, mac if len(ips) == 1 else ""):
                    them.append(ip)
        DL.MAY.sua(ghi)
        return _chuyen("/deployos/trienkhai/may", f"Đã thêm {len(them)} máy" + (f", bỏ qua {len(ips) - len(them)} máy đã có." if len(ips) > len(them) else "."))

    @app.route("/deployos/trienkhai/may/sua", methods=["POST"])
    def tk_may_sua():
        mid = request.form.get("id", "")

        def ghi(ds):
            m = DL.tim(ds, mid)
            if m:
                m["ten"] = (request.form.get("ten") or "").strip()
                m["mac"] = _chuan_mac(request.form.get("mac"))
        DL.MAY.sua(ghi)
        return _chuyen("/deployos/trienkhai/may", "Đã lưu.")

    @app.route("/deployos/trienkhai/may/xoa", methods=["POST"])
    def tk_may_xoa():
        mid = request.form.get("id", "")
        DL.MAY.sua(lambda ds: ds.__setitem__(slice(None), [x for x in ds if x["id"] != mid]))

        def go(ds):
            for g in ds:
                g["may"] = [i for i in g.get("may", []) if i != mid]
        DL.NHOM_MAY.sua(go)
        return _chuyen("/deployos/trienkhai/may", "Đã xóa máy khỏi danh sách.")

    @app.route("/deployos/trienkhai/may/kiemtra", methods=["POST"])
    def tk_may_kiemtra():
        m = DL.tim(DL.MAY.doc(), request.form.get("id", ""))
        if not m:
            return _chuyen("/deployos/trienkhai/may", "Không tìm thấy máy.", False)
        mo = [ten for cong, ten in DC.CONG_QUET if DC.cong_mo(m["ip"], cong, 1.0)]
        mac = DC.mac_tu_arp(m["ip"])
        if mac and not m.get("mac"):
            DL.MAY.sua(lambda ds: DL.tim(ds, m["id"]).__setitem__("mac", mac))
        if not mo:
            return _chuyen("/deployos/trienkhai/may", f'{m.get("ten") or m["ip"]}: không thấy cổng nào mở (máy tắt, tường lửa hoặc sai IP).', False)
        return _chuyen("/deployos/trienkhai/may", f'{m.get("ten") or m["ip"]}: cổng mở: {", ".join(mo)}.'
                       + ("" if "WinRM" in mo else " WinRM CHƯA bật nên chưa cài phần mềm được."), "WinRM" in mo)

    # ---- kiem ke
    @app.route("/deployos/trienkhai/may/<mid>/kiemke")
    def tk_kiem_ke(mid):
        m = DL.tim(DL.MAY.doc(), mid)
        k = (m or {}).get("kiem_ke")
        if not k:
            return _chuyen("/deployos/trienkhai/may", "Máy này chưa được kiểm kê. Chạy bước 'Kiểm kê' ở Kiểm tra bảo mật.", False)
        pm = k.get("phan_mem", [])
        hang = "".join(f'<tr data-t="{_esc((p.get("ten", "") + " " + p.get("nsx", "")).lower())}"><td>{_esc(p.get("ten"))}</td>'
                       f'<td>{_esc(p.get("pb"))}</td><td>{_esc(p.get("nsx"))}</td></tr>' for p in pm)
        o = ", ".join(f'{x["o"]} trống {x["trong_gb"]}/{x["tong_gb"]} GB' for x in k.get("o_dia", []))
        body = f"""
        <h2>Kiểm kê: {_esc(m.get("ten") or m["ip"])}</h2>
        <div class="card"><table class="tk-bang">
          <tr><th>Tên máy Windows</th><td>{_esc(k.get("ten_may"))}</td><th>Hãng / model</th><td>{_esc(k.get("hang"))} {_esc(k.get("model"))}</td></tr>
          <tr><th>Số serial</th><td>{_esc(k.get("serial"))}</td><th>Hệ điều hành</th><td>{_esc(k.get("os"))} (build {_esc(k.get("build"))})</td></tr>
          <tr><th>CPU</th><td>{_esc(k.get("cpu"))}</td><th>RAM</th><td>{_esc(k.get("ram_gb"))} GB</td></tr>
          <tr><th>Địa chỉ IP</th><td>{_esc(", ".join(k.get("ip", [])))}</td><th>Ổ đĩa</th><td>{_esc(o)}</td></tr>
          <tr><th>Kiểm kê lúc</th><td colspan="3">{_esc(DL.dinh_dang_gio(k.get("luc")))}</td></tr></table></div>
        <h2>Phần mềm đã cài ({len(pm)})</h2>
        <div class="card"><div class="tk-hang"><input type="text" id="pm-tim" placeholder="Tìm phần mềm" style="max-width:340px;margin:0;height:42px;">
          <a class="tk-nut" href="/deployos/trienkhai/may/{_esc(mid)}/kiemke.csv">Tải CSV</a>
          <a class="tk-nut" href="/deployos/trienkhai/may">Quay lại</a></div>
          <table class="tk-bang" id="pm-bang"><tr><th>Tên</th><th>Phiên bản</th><th>Nhà sản xuất</th></tr>{hang}</table></div>
        <script>(function(){{var i=document.getElementById('pm-tim');i.oninput=function(){{var q=i.value.toLowerCase();
          document.querySelectorAll('#pm-bang tr[data-t]').forEach(function(r){{r.style.display=r.getAttribute('data-t').indexOf(q)>=0?'':'none';}});}};}})();</script>"""
        return _trang(body, "may", "ds")

    @app.route("/deployos/trienkhai/may/<mid>/kiemke.csv")
    def tk_kiem_ke_csv(mid):
        import csv
        import io
        from flask import Response
        m = DL.tim(DL.MAY.doc(), mid)
        k = (m or {}).get("kiem_ke")
        if not k:
            abort(404)
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["phan_mem", "phien_ban", "nha_san_xuat"])
        for p in k.get("phan_mem", []):
            w.writerow([p.get("ten", ""), p.get("pb", ""), p.get("nsx", "")])
        return Response("\ufeff" + buf.getvalue(), mimetype="text/csv; charset=utf-8",
                        headers={"Content-Disposition": 'attachment; filename="phan-mem-' + re.sub(r"[^A-Za-z0-9_-]", "_", m.get("ten") or m["ip"]) + '.csv"'})

    # ---- nhom may
    @app.route("/deployos/trienkhai/may/nhom")
    def tk_nhom_may():
        return _trang_nhom_may()

    @app.route("/deployos/trienkhai/may/nhom/luu", methods=["POST"])
    def tk_nhom_may_luu():
        ten = (request.form.get("ten") or "").strip()
        ids = [i for i in request.form.getlist("may") if DL.tim(DL.MAY.doc(), i)]
        if not ten:
            return _chuyen("/deployos/trienkhai/may/nhom", "Đặt tên cho nhóm.", False)
        gid = request.form.get("id", "")

        def ghi(ds):
            c = DL.tim(ds, gid)
            if c:
                c.update(ten=ten, may=ids)
            else:
                ds.append({"id": DL.moi_id(), "ten": ten, "may": ids})
        DL.NHOM_MAY.sua(ghi)
        return _chuyen("/deployos/trienkhai/may/nhom", f'Đã lưu nhóm "{ten}" ({len(ids)} máy).')

    @app.route("/deployos/trienkhai/may/nhom/xoa", methods=["POST"])
    def tk_nhom_may_xoa():
        gid = request.form.get("id", "")
        DL.NHOM_MAY.sua(lambda ds: ds.__setitem__(slice(None), [x for x in ds if x["id"] != gid]))
        return _chuyen("/deployos/trienkhai/may/nhom", "Đã xóa nhóm máy.")

    # ---- quet
    @app.route("/deployos/trienkhai/may/quet")
    def tk_quet():
        return _trang_quet()

    @app.route("/deployos/trienkhai/may/quet", methods=["POST"])
    def tk_quet_bat():
        ok, tb = DC.bat_dau_quet((request.form.get("cidr") or "").strip())
        return _chuyen("/deployos/trienkhai/may/quet", tb, ok)

    @app.route("/deployos/trienkhai/may/quet/tt")
    def tk_quet_tt():
        return jsonify(DC.trang_thai_quet())

    @app.route("/deployos/trienkhai/may/quet/them", methods=["POST"])
    def tk_quet_them():
        ips = request.form.getlist("ip")
        them = []

        def ghi(ds):
            for ip in ips:
                try:
                    import ipaddress
                    ipaddress.ip_address(ip)
                except ValueError:
                    continue
                ten = (request.form.get("ten_" + ip) or "").strip()
                if _them_may(ds, ip, ten, _chuan_mac(request.form.get("mac_" + ip))):
                    them.append(next(m["id"] for m in ds if m["ip"] == ip))
        DL.MAY.sua(ghi)
        nhom = (request.form.get("nhom") or "").strip()
        if nhom and them:
            DL.NHOM_MAY.sua(lambda ds: ds.append({"id": DL.moi_id(), "ten": nhom, "may": them}))
        return _chuyen("/deployos/trienkhai/may", f"Đã thêm {len(them)} máy" + (f' và tạo nhóm "{nhom}".' if nhom and them else "."))

    # ---- tai khoan
    @app.route("/deployos/trienkhai/may/taikhoan")
    def tk_tai_khoan():
        return _trang_tai_khoan()

    @app.route("/deployos/trienkhai/may/taikhoan/them", methods=["POST"])
    def tk_tai_khoan_them():
        ten, user, mk = (request.form.get("ten") or "").strip(), (request.form.get("user") or "").strip(), request.form.get("mk") or ""
        if not (ten and user and mk):
            return _chuyen("/deployos/trienkhai/may/taikhoan", "Điền đủ tên gợi nhớ, tài khoản và mật khẩu.", False)
        DL.TAI_KHOAN.sua(lambda ds: ds.append({"id": DL.moi_id(), "ten": ten, "user": user, "mk": DL.ma_hoa(mk)}))
        return _chuyen("/deployos/trienkhai/may/taikhoan", f'Đã lưu tài khoản "{ten}" (mật khẩu đã mã hóa).')

    @app.route("/deployos/trienkhai/may/taikhoan/xoa", methods=["POST"])
    def tk_tai_khoan_xoa():
        tid = request.form.get("id", "")
        DL.TAI_KHOAN.sua(lambda ds: ds.__setitem__(slice(None), [x for x in ds if x["id"] != tid]))
        return _chuyen("/deployos/trienkhai/may/taikhoan", "Đã xóa tài khoản.")

    @app.route("/deployos/trienkhai/may/taikhoan/thu", methods=["POST"])
    def tk_tai_khoan_thu():
        user, mk = DL.lay_tai_khoan(request.form.get("tk", ""))
        m = DL.tim(DL.MAY.doc(), request.form.get("may", ""))
        if user is None or not m:
            return _chuyen("/deployos/trienkhai/may/taikhoan", "Chọn tài khoản và máy để thử.", False)
        try:
            if not DC.cong_mo(m["ip"], 5985, 3.0):
                raise DC.LoiKetNoi("Cổng WinRM 5985 đóng: máy tắt, chưa bật WinRM hoặc tường lửa chặn.")
            c = DC._ket_noi(m["ip"], user, mk)
            out, _e = DC._chay_ps(c, "$env:COMPUTERNAME + ' / ' + (whoami)")
            return _chuyen("/deployos/trienkhai/may/taikhoan", f"Đăng nhập được: {out.strip()}")
        except DC.LoiKetNoi as e:
            return _chuyen("/deployos/trienkhai/may/taikhoan", str(e), False)
        except Exception as e:
            return _chuyen("/deployos/trienkhai/may/taikhoan", DC._loi_dep(e, mk), False)

    # ---- kich ban
    @app.route("/deployos/trienkhai/kichban")
    def tk_kichban():
        return _trang_kichban()

    @app.route("/deployos/trienkhai/kichban/luu", methods=["POST"])
    def tk_kichban_luu():
        ten = (request.form.get("ten") or "").strip()
        try:
            buoc = json.loads(request.form.get("buoc_json") or "[]")
        except ValueError:
            buoc = []
        tn = _cac_tai_nguyen()
        sach = []
        for b in buoc if isinstance(buoc, list) else []:
            loai, ref = str(b.get("loai", "")), str(b.get("ref", ""))
            mot = bool(b.get("mot_lan")) and loai in ("phanmem", "ungdung", "winget", "nhom")
            n0 = len(sach)
            if loai not in DC.TEN_LOAI_BUOC:
                continue
            if loai in ("phanmem", "ungdung", "script"):
                t = next((x for x in tn[loai] if x["ref"] == ref), None)
                if not t:
                    continue
                sach.append({"loai": loai, "ref": ref, "ten": t["ten"]})
            elif loai == "winget":
                if re.fullmatch(r"[A-Za-z0-9._+-]{2,100}", ref):
                    sach.append({"loai": loai, "ref": ref, "ten": "WinGet: " + ref})
            elif loai == "nguon":
                if ref in DC.TEN_NGUON:
                    sach.append({"loai": loai, "ref": ref})
            elif loai == "nhom":
                g = DL.tim(DL.NHOM_TN.doc(), ref)
                if g:
                    sach.append({"loai": loai, "ref": ref, "ten": g["ten"]})
            elif loai == "kiemke":
                sach.append({"loai": "kiemke", "ref": ""})
            elif loai == "rustdesk":
                sach.append({"loai": "rustdesk", "ref": ""})
            else:
                sach.append({"loai": "baomat", "ref": ""})
            if len(sach) > n0 and mot:
                sach[-1]["mot_lan"] = True
        if not ten or not sach:
            return _chuyen("/deployos/trienkhai/kichban", "Cần có tên và ít nhất một bước hợp lệ.", False)
        dl = dict(ten=ten, ghi_chu=(request.form.get("ghi_chu") or "").strip(), buoc=sach,
                  nhom_may=[i for i in request.form.getlist("nhom_may") if DL.tim(DL.NHOM_MAY.doc(), i)],
                  may=[i for i in request.form.getlist("may") if DL.tim(DL.MAY.doc(), i)],
                  lich_id=request.form.get("lich_id", "") if DL.tim(DL.LICH.doc(), request.form.get("lich_id", "")) else "",
                  tai_khoan_id=request.form.get("tai_khoan_id", ""))
        kid = request.form.get("id", "")

        def ghi(ds):
            c = DL.tim(ds, kid)
            if c:
                c.update(dl)
            else:
                ds.append(dict(dl, id=DL.moi_id()))
        DL.KICH_BAN.sua(ghi)
        return _chuyen("/deployos/trienkhai/kichban", f'Đã lưu kịch bản "{ten}". Sang tab Triển khai để bấm Chạy.')

    @app.route("/deployos/trienkhai/kichban/xoa", methods=["POST"])
    def tk_kichban_xoa():
        kid = request.form.get("id", "")
        DC.dung(kid)
        DL.KICH_BAN.sua(lambda ds: ds.__setitem__(slice(None), [x for x in ds if x["id"] != kid]))
        DL.TRANG_THAI.sua(lambda t: t.pop(kid, None))
        return _chuyen("/deployos/trienkhai/kichban", "Đã xóa kịch bản.")

    # ---- chuc nang khac / chay nhanh
    @app.route("/deployos/trienkhai/khac")
    def tk_khac():
        return _trang_khac()

    @app.route("/deployos/trienkhai/nhanh", methods=["POST"])
    def tk_nhanh():
        ids = [i for i in request.form.getlist("may") if DL.tim(DL.MAY.doc(), i)]
        viec = request.form.get("viec", "")
        if not ids:
            return _chuyen("/deployos/trienkhai/khac", "Chọn ít nhất một máy.", False)
        if viec == "kiemke":
            buoc, ten = [{"loai": "kiemke", "ref": ""}], "Kiểm kê máy"
        elif viec == "baomat":
            buoc, ten = [{"loai": "baomat", "ref": ""}], "Kiểm tra bảo mật"
        elif viec == "rustdesk":
            buoc, ten = [{"loai": "rustdesk", "ref": ""}], "Cài RustDesk"
        elif viec in DC.TEN_NGUON:
            buoc, ten = [{"loai": "nguon", "ref": viec}], DC.TEN_NGUON[viec]
        elif viec == "winget":
            w = (request.form.get("winget") or "").strip()
            if not re.fullmatch(r"[A-Za-z0-9._+-]{2,100}", w):
                return _chuyen("/deployos/trienkhai/khac", "Mã WinGet không hợp lệ.", False)
            buoc, ten = [{"loai": "winget", "ref": w, "ten": "WinGet: " + w}], "WinGet " + w
        else:
            return _chuyen("/deployos/trienkhai/khac", "Chọn việc cần làm.", False)
        tk = request.form.get("tk", "")
        if not (viec == "bat") and DL.lay_tai_khoan(tk)[0] is None:
            return _chuyen("/deployos/trienkhai/khac", "Chọn tài khoản quản trị (tạo ở Máy - nhóm máy, Tài khoản quản trị).", False)
        kb_id, loi = DC.chay_nhanh("Chạy nhanh: " + ten, buoc, ids, tk)
        if not kb_id:
            return _chuyen("/deployos/trienkhai/khac", loi, False)
        return redirect(f"/deployos/trienkhai#xem={kb_id}")

    return app
