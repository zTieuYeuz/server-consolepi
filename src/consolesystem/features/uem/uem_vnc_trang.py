# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Trang "Phan mem remote" > tab Remote VNC: tai bo cai TightVNC (khi can cai tay / offline) va Cai / Kiem tra / Go TightVNC
hang loat tren cac may co agent. Thao tac tung may van la uem_vnc.cai / kiem_tra / go (giong tab Ho tro tu xa cua may)."""
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from flask import Response, jsonify, request, send_file

from consolesystem.web import chon_may as CM
from ui import tk_dulieu as DL
from ui import uem_agent as UA
from ui import uem_vnc as UV

_EX = ThreadPoolExecutor(max_workers=4)
_VIEC = {}                       # ma -> {viec, tong, xong, kq: {may_id: {ten, ok, tb}}, luc}
_KHOA = threading.Lock()
TEN_VIEC = {"cai": "Cài TightVNC", "kiem": "Kiểm tra", "go": "Gỡ TightVNC"}

TRANG = """<style>.vn-tb{width:100%;border-collapse:collapse;margin-top:10px}.vn-tb td,.vn-tb th{padding:6px 8px;border-bottom:1px solid var(--vien);text-align:left}
.vn-ok{color:var(--xanh)}.vn-loi{color:var(--do)}</style>
<div class="card"><h3>Tải phần mềm VNC</h3>
<p class="tk-ghi">Bộ cài TightVNC 2.8.85 bản GPL chính thức (đã kiểm SHA-256), dùng khi cần cài tay trên máy không có agent hoặc máy không ra được Internet. Cài tay thì nhớ đặt mật khẩu VNC; cài tự động ở dưới thì Console System tự cấu hình (dịch vụ thủ công, chỉ bật khi có phiên, mã PIN mới mỗi phiên).</p>
<div class="nut-hang"><button class="tk-nut chinh" type="button" onclick="location.href='/rustdesk/vnc/tai/64'">Tải TightVNC 64-bit (.msi)</button>
<button class="tk-nut" type="button" onclick="location.href='/rustdesk/vnc/tai/32'">Tải TightVNC 32-bit (.msi)</button></div></div>
<div class="card"><h3>Tự động trên các máy có agent</h3>
<div class="dep-tabs sub" id="vn-viec" style="margin-bottom:10px;"><a href="#" class="dep-tab on" data-v="cai">Cài TightVNC</a><a href="#" class="dep-tab" data-v="kiem">Kiểm tra</a><a href="#" class="dep-tab" data-v="go">Gỡ</a></div>
<p class="tk-ghi" id="vn-ghi"></p>
@KHUNG@
<div class="nut-hang" style="margin-top:10px;"><button class="tk-nut chinh" type="button" id="vn-chay">Thực hiện</button><span class="tk-ghi" id="vn-tb"></span></div>
<table class="vn-tb" id="vn-kq"></table></div>
<script>(function(){var $=function(i){return document.getElementById(i);},viec='cai';
var GHI={cai:'Cài TightVNC (bản GPL chính thức) dạng dịch vụ thủ công, luôn tắt khi không có phiên. Máy đã cài thì cấu hình lại. Mỗi máy khoảng 1 phút.',
 kiem:'Xem máy đã cài TightVNC chưa, bản nào, dịch vụ đang chạy hay tắt.',go:'Gỡ TightVNC và xóa cấu hình khỏi máy.'};
function e(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function chon(v){viec=v;[].slice.call(document.querySelectorAll('#vn-viec .dep-tab')).forEach(function(b){b.classList.toggle('on',b.dataset.v===v);});
 $('vn-ghi').textContent=GHI[v];$('vn-chay').textContent='Thực hiện: '+{cai:'Cài TightVNC',kiem:'Kiểm tra',go:'Gỡ TightVNC'}[v];}
$('vn-viec').addEventListener('click',function(ev){if(ev.target.dataset.v){ev.preventDefault();chon(ev.target.dataset.v);}});
function tai(){fetch('/rustdesk/vnc/api/may').then(function(r){return r.json();}).then(function(d){ChonMay.ve('vn',d.may);});}
function ve(d){var h='<tr><th>Máy</th><th>Kết quả</th></tr>';Object.keys(d.kq).forEach(function(k){var x=d.kq[k];
 h+='<tr><td>'+e(x.ten)+'</td><td class="'+(x.ok===null?'':(x.ok?'vn-ok':'vn-loi'))+'">'+e(x.ok===null?'Đang chạy...':x.tb)+'</td></tr>';});$('vn-kq').innerHTML=h;
 $('vn-tb').textContent=d.ten+': xong '+d.xong+' / '+d.tong+' máy';}
function theo(ma){fetch('/rustdesk/vnc/api/tt/'+ma).then(function(r){return r.json();}).then(function(d){ve(d);if(d.xong<d.tong)setTimeout(function(){theo(ma);},2000);else{$('vn-chay').disabled=false;tai();}});}
$('vn-chay').onclick=function(){var ids=ChonMay.chon('vn');if(!ids.length){$('vn-tb').textContent='Chọn ít nhất một máy.';return;}
 if(viec==='go'&&!confirm('Gỡ TightVNC khỏi '+ids.length+' máy?'))return;$('vn-chay').disabled=true;
 fetch('/rustdesk/vnc/api/chay',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({viec:viec,may:ids})}).then(function(r){return r.json();}).then(function(d){
  if(!d.ok){$('vn-tb').textContent=d.tb;$('vn-chay').disabled=false;return;}theo(d.ma);});};
chon('cai');tai();})();</script>"""


def _ds_may():
    ra = []
    for m in DL.MAY.doc():
        if m.get("an") or not UA.co_agent(m):
            continue
        v = m.get("vnc") or {}
        trang = (" · TightVNC " + v.get("ban", "")) if v.get("da_cai") else (" · chưa cài VNC" if "da_cai" in v else "")
        ra.append({"id": m["id"], "ten": m.get("ten") or m["ip"], "ip": m["ip"] + trang, "online": UA.con_song(m)})
    return ra


def _chay_mot(ma, mid):
    v = _VIEC[ma]
    try:
        ok, tb = {"cai": UV.cai, "kiem": UV.kiem_tra, "go": UV.go}[v["viec"]](mid)
    except Exception as e:                     # moi loi cua 1 may chi ghi vao ket qua may do
        ok, tb = False, str(e)[:300]
    with _KHOA:
        v["kq"][mid].update(ok=ok, tb=tb)
        v["xong"] += 1


def bat_dau(viec, ids):
    if viec not in TEN_VIEC:
        return None, "Việc không hợp lệ."
    ds = {m["id"]: m for m in _ds_may()}
    ids = [i for i in dict.fromkeys(ids or []) if i in ds]
    if not ids:
        return None, "Chưa chọn máy nào (chỉ máy có agent)."
    ma = uuid.uuid4().hex[:10]
    with _KHOA:
        for k in [k for k, x in _VIEC.items() if time.time() - x["luc"] > 6 * 3600]:
            _VIEC.pop(k, None)
        _VIEC[ma] = {"viec": viec, "ten": TEN_VIEC[viec], "tong": len(ids), "xong": 0, "luc": time.time(),
                     "kq": {i: {"ten": ds[i]["ten"], "ok": None, "tb": ""} for i in ids}}
    for i in ids:
        _EX.submit(_chay_mot, ma, i)
    return ma, ""


def register_vnc_trang(app):
    from ui.layout import render_page

    @app.route("/rustdesk/vnc")
    def remote_vnc():
        body = CM.JS + CM.CSS + CM.thanh_tab(CM.TAB_REMOTE, "vnc") + TRANG.replace("@KHUNG@", CM.khung("vn"))
        return render_page(body, active="/rustdesk", title="Hỗ trợ từ xa", subtitle="Remote VNC: tải TightVNC, cài / kiểm tra / gỡ trên nhiều máy")

    @app.route("/rustdesk/vnc/tai/<bits>")
    def remote_vnc_tai(bits):
        if bits not in ("64", "32"):
            return Response("Không có bản này.", status=404, mimetype="text/plain; charset=utf-8")
        try:
            duong = UV.lay_msi(bits)
        except RuntimeError as e:
            return Response(str(e), status=409, mimetype="text/plain; charset=utf-8")
        return send_file(duong, as_attachment=True, download_name=UV.MSI[bits][0], mimetype="application/x-msi")

    @app.route("/rustdesk/vnc/api/may")
    def remote_vnc_may():
        return jsonify({"may": _ds_may()})

    @app.route("/rustdesk/vnc/api/chay", methods=["POST"])
    def remote_vnc_chay():
        j = request.get_json(silent=True) or {}
        ma, loi = bat_dau(str(j.get("viec", "")), [str(x) for x in (j.get("may") or [])])
        return jsonify({"ok": bool(ma), "ma": ma, "tb": loi})

    @app.route("/rustdesk/vnc/api/tt/<ma>")
    def remote_vnc_tt(ma):
        with _KHOA:
            v = _VIEC.get(ma)
            if not v:
                return jsonify({"ten": "", "tong": 0, "xong": 0, "kq": {}}), 404
            return jsonify({"ten": v["ten"], "tong": v["tong"], "xong": v["xong"], "kq": {k: dict(x) for k, x in v["kq"].items()}})
