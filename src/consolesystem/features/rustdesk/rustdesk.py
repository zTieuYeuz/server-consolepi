# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Trang RustDesk (giao dien): cai/dieu khien may chu RustDesk tich hop. Logic o consolesystem/integrations/rustdesk_may_chu.py;
phan can du lieu may tram (cai client qua agent, danh sach may) o features/uem/uem_rustdesk.py."""
import secrets

from flask import Response, jsonify, request

from consolesystem.integrations import rustdesk_may_chu as RD

TRANG = """<style>.rd-2{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px}.rd-k{font-family:monospace;word-break:break-all;user-select:all;background:#111;padding:8px;border-radius:6px}
.rd-chip{display:inline-block;padding:2px 9px;border-radius:10px;background:#333;margin-right:6px}.rd-chip.ok{background:#1f6f2e}.rd-chip.loi{background:#8a2a2a}
.rd-tb{width:100%;border-collapse:collapse}.rd-tb td,.rd-tb th{padding:6px 8px;border-bottom:1px solid #333;text-align:left}</style>
<div class="card"><h3>RustDesk Server tích hợp</h3>
<p class="tk-ghi">Chạy máy chủ RustDesk (ID server + relay) ngay trên Console System để điều khiển máy từ xa không phụ thuộc máy chủ công cộng. Bản RustDesk Server miễn phí <b>không có trang quản trị web</b> (bản Pro mới có); trang này hiển thị đúng những gì máy chủ lưu: khóa, cổng, danh sách thiết bị đã đăng ký.</p>
<div id="rd-tt">Đang tải...</div><div class="tk-hang" style="margin-top:10px;" id="rd-nut"></div><div class="tk-ghi" id="rd-tb"></div></div>
<div class="rd-2"><div class="card"><h3>Cấu hình</h3><p class="tk-ghi">Địa chỉ để các máy RustDesk tìm tới máy chủ này: tên miền hoặc IP công cộng nếu có máy ở ngoài Internet; để trống = dùng IP LAN (chỉ trong mạng nội bộ).</p>
<input type="text" id="rd-host" placeholder="vd rd.ten-mien-cua-ban.com" style="width:100%;"><label class="tk-o" style="margin-top:8px;"><input type="checkbox" id="rd-ws"><span><b>Dùng đường Cloudflare (WebSocket)</b><small>Bật khi địa chỉ ở trên là tên miền qua Cloudflare Tunnel (đường /ws/id và /ws/relay). Áp dụng cho máy cài mới và script cài tay.</small></span></label>
<div class="tk-hang" style="margin-top:8px;"><button class="tk-nut chinh" id="rd-luu" type="button">Lưu</button><button class="tk-nut" id="rd-ap" type="button" title="Máy đã cài RustDesk từ trước chưa đổi địa chỉ: bấm để đẩy địa chỉ, khóa và WebSocket xuống các máy (cần agent)">Áp dụng xuống các máy đã cài</button></div><div class="tk-ghi" id="rd-ap-tb"></div>
<p class="tk-ghi" style="margin-top:12px;"><b>Để máy ngoài Internet remote được:</b> trên router chuyển tiếp (port forward) về máy này: <b>TCP 21115-21119</b> và <b>UDP 21116</b>. (Hoặc không cần mở cổng: đi qua Cloudflare Tunnel bằng chế độ WebSocket ở trên, với đường <code>/ws/id</code> và <code>/ws/relay</code> trỏ về cổng 21118 và 21119 của máy này.) Agent Console System vẫn chỉ hoạt động trong LAN, nên máy ở ngoài cài RustDesk bằng script thủ công bên dưới.</p></div>
<div class="card"><h3>Khóa và cấu hình cho client</h3><p class="tk-ghi">Dán vào RustDesk, Cài đặt, Mạng, Máy chủ ID/Relay:</p>
<div>ID server / Relay: <span class="rd-k" id="rd-h"></span></div><div style="margin-top:6px;">Key:</div><div class="rd-k" id="rd-key">(chưa có, cài máy chủ trước)</div>
<p class="tk-ghi" style="margin-top:10px;">Cài tay trên máy Windows bất kỳ (kể cả ngoài Internet): mở PowerShell quản trị và chạy file tải ở đây (đã nhúng máy chủ và khóa, tải bản chính thức có kiểm SHA-256):</p>
<a class="tk-nut" href="/rustdesk/client-cai.ps1">Tải script cài client (.ps1)</a>
<p class="tk-ghi" style="margin-top:10px;">Máy đã cài RustDesk từ trước (kể cả máy anh đang ngồi, không có agent) mà vẫn báo kết nối tới địa chỉ cũ: tải file này, bấm chuột phải chạy bằng PowerShell Administrator để đổi sang máy chủ hiện tại.</p>
<a class="tk-nut" href="/rustdesk/doi-may-chu.ps1">Tải script đổi máy chủ cho RustDesk đã cài (.ps1)</a></div></div>
<div class="card"><h3>Mật khẩu cố định chung cho mọi máy</h3><p class="tk-ghi">Đặt một mật khẩu, Console System đẩy xuống <b>tất cả máy đã cài RustDesk</b> qua agent. Đổi mật khẩu ở đây thì mọi máy đổi theo; máy đang tắt sẽ chờ, bấm <b>Đồng bộ lại</b> khi máy bật. Máy cài mới cũng dùng mật khẩu này.</p>
<div class="tk-hang"><input type="text" id="rd-mk" autocomplete="off" placeholder="8-64 ký tự: chữ, số, ! @ # % ^ * . _ -" style="max-width:340px;margin:0;"><button class="tk-nut chinh" id="rd-mk-luu" type="button">Lưu và áp dụng cho tất cả</button><button class="tk-nut" id="rd-mk-bo" type="button">Đồng bộ lại</button></div><div class="tk-ghi" id="rd-mk-tb" style="margin-top:6px;"></div></div>
<div class="card"><h3>Cài RustDesk lên máy Windows có agent</h3><p class="tk-ghi">Chọn máy rồi bấm Cài. Mỗi máy được đặt một mật khẩu cố định riêng, hiện ở bảng bên dưới.</p><div id="rd-may" class="tk-luoi"></div>
<div style="margin-top:8px;"><button class="tk-nut chinh" id="rd-cai-client" type="button">Cài lên máy đã chọn</button> <span class="tk-ghi" id="rd-ct"></span></div>
<table class="rd-tb" id="rd-bang-may" style="margin-top:10px;"></table></div>
<div class="card"><h3>Thiết bị đã đăng ký với máy chủ</h3><table class="rd-tb" id="rd-dev"></table></div>
<script>(function(){var $=function(i){return document.getElementById(i);};
function e(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function api(u,b){return fetch(u,b?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}:{}).then(function(r){return r.json();});}
function chip(t,ok){return '<span class="rd-chip '+(ok?'ok':'loi')+'">'+t+'</span>';}
function ve(d){
 var h='Phiên bản máy chủ: <b>'+e(d.ban)+'</b> ('+e(d.kien_truc||'chưa hỗ trợ')+')<br>';
 h+=d.da_cai?(chip('ID server (hbbs) '+(d.hbbs?'chạy':'dừng'),d.hbbs)+chip('Relay (hbbr) '+(d.hbbr?'chạy':'dừng'),d.hbbr)+chip('Cổng 21116 '+(d.cong['21116']?'mở':'đóng'),d.cong['21116'])):'<span class="rd-chip loi">Chưa cài</span>';
 $('rd-tt').innerHTML=h;
 var n='';
 if(!d.da_cai) n='<button class="tk-nut chinh" data-v="cai"'+(d.cai.dang?' disabled':'')+'>Cài máy chủ RustDesk</button>';
 else n='<button class="tk-nut xanh" data-v="start">Chạy</button><button class="tk-nut" data-v="restart">Khởi động lại</button><button class="tk-nut" data-v="stop">Dừng</button><button class="tk-nut do" data-v="go">Gỡ dịch vụ</button>';
 $('rd-nut').innerHTML=n; $('rd-tb').textContent=d.cai.tb||'';
 if(document.activeElement!==$('rd-host')) $('rd-host').value=d.host||''; $('rd-ws').checked=!!d.ws; $('rd-h').textContent=d.host_hieu_luc||'(chưa xác định)'; $('rd-key').textContent=d.khoa||'(chưa có, cài máy chủ trước)';
 if(d.cai.dang) setTimeout(tai,1500);}
function tai(){api('/rustdesk/api/trang-thai').then(ve);}
$('rd-nut').addEventListener('click',function(ev){var v=ev.target.dataset.v; if(!v)return; if(v==='go'&&!confirm('Gỡ dịch vụ RustDesk Server?'))return;
 api(v==='cai'?'/rustdesk/api/cai':'/rustdesk/api/hanh-dong',{viec:v}).then(function(d){$('rd-tb').textContent=d.tb||'';tai();});});
$('rd-luu').onclick=function(){api('/rustdesk/api/cau-hinh',{host:$('rd-host').value,ws:$('rd-ws').checked}).then(function(d){$('rd-tb').textContent=d.tb;tai();});};
function dev(){api('/rustdesk/api/thiet-bi').then(function(d){var h='<tr><th>ID</th><th>IP gần nhất</th><th>Đăng ký lúc</th><th>Ghi chú</th></tr>';
 (d.ds||[]).forEach(function(x){h+='<tr><td><b>'+e(x.id)+'</b></td><td>'+e(x.ip)+'</td><td>'+e(x.tao)+'</td><td>'+e(x.ghi_chu)+'</td></tr>';});
 if(!(d.ds||[]).length) h+='<tr><td colspan="4" class="tk-ghi">Chưa có thiết bị nào đăng ký.</td></tr>'; $('rd-dev').innerHTML=h;
 if(document.activeElement!==$('rd-mk')) $('rd-mk').value=d.mk_chung||''; $('rd-mk-tb').textContent=(d.dong_bo&&d.dong_bo.tb)||''; if(d.dong_bo&&d.dong_bo.dang) setTimeout(dev,2500);
 var m='<tr><th>Máy</th><th>ID RustDesk</th><th>Mật khẩu</th><th>Đồng bộ</th></tr>'; (d.may||[]).forEach(function(x){m+='<tr><td>'+e(x.ten)+'</td><td><b>'+e(x.id)+'</b></td><td><span class="rd-k">'+e(x.mk)+'</span></td><td>'+(x.dong_bo?'<span class="rd-chip ok">đã đồng bộ</span>':'<span class="rd-chip loi" title="'+e(x.loi)+'">chờ cập nhật</span>')+'</td></tr>';});
 $('rd-bang-may').innerHTML=(d.may||[]).length?m:''; var o=''; (d.agent||[]).forEach(function(x){o+='<label class="tk-o"><input type="checkbox" name="rdm" value="'+e(x.id)+'"><span><b>'+e(x.ten)+'</b><small>'+e(x.ip)+(x.online?'':' (offline)')+'</small></span></label>';});
 $('rd-may').innerHTML=o||'<span class="tk-ghi">Chưa có máy nào cài agent.</span>';});}
$('rd-cai-client').onclick=function(){var ids=[].slice.call(document.querySelectorAll('input[name=rdm]:checked')).map(function(i){return i.value;}); if(!ids.length){$('rd-ct').textContent='Chọn ít nhất một máy.';return;}
 $('rd-ct').textContent='Đang cài (có thể mất 1-2 phút mỗi máy)...'; api('/rustdesk/api/cai-client',{may:ids}).then(function(d){$('rd-ct').textContent=(d.kq||[]).map(function(x){return x.ten+': '+x.tb;}).join(' | ');dev();});};
$('rd-ap').onclick=function(){api('/rustdesk/api/ap-cau-hinh',{}).then(function(d){$('rd-ap-tb').textContent=d.ok?'Đang áp dụng, xem kết quả ở thẻ mật khẩu bên dưới...':'Đang có việc khác chạy.';setTimeout(dev,2500);});};
$('rd-mk-luu').onclick=function(){api('/rustdesk/api/mat-khau',{mk:$('rd-mk').value}).then(function(d){$('rd-mk-tb').textContent=d.tb;setTimeout(dev,1500);});};
$('rd-mk-bo').onclick=function(){api('/rustdesk/api/dong-bo',{}).then(function(d){$('rd-mk-tb').textContent=d.tb;setTimeout(dev,1500);});};
tai(); dev(); setInterval(function(){if(!document.hidden)tai();},8000);})();</script>"""


def register_rustdesk(app):
    from ui.layout import render_page

    @app.route("/rustdesk")
    def rustdesk_trang():
        return render_page(TRANG, active="/rustdesk", title="RustDesk", subtitle="Máy chủ RustDesk tích hợp và cài client lên máy Windows")

    @app.route("/rustdesk/api/trang-thai")
    def rustdesk_api_tt():
        return jsonify(RD.trang_thai())

    @app.route("/rustdesk/api/cai", methods=["POST"])
    def rustdesk_api_cai():
        ok = RD.bat_dau_cai()
        return jsonify({"ok": ok, "tb": "Đang cài, theo dõi ở trên..." if ok else "Đang có một lần cài chạy."})

    @app.route("/rustdesk/api/hanh-dong", methods=["POST"])
    def rustdesk_api_hd():
        ok, tb = RD.hanh_dong(str((request.get_json(silent=True) or {}).get("viec", "")))
        return jsonify({"ok": ok, "tb": tb})

    @app.route("/rustdesk/api/cau-hinh", methods=["POST"])
    def rustdesk_api_cfg():
        j = request.get_json(silent=True) or {}
        ok, tb = RD.dat_host(str(j.get("host", "")))
        if ok and "ws" in j:
            RD.dat_ws(j["ws"])
        return jsonify({"ok": ok, "tb": tb})

    @app.route("/rustdesk/doi-may-chu.ps1")
    def rustdesk_script_doi():
        try:
            sc = RD.script_cau_hinh_nguoi_dung()
        except RuntimeError as e:
            return Response(str(e), status=409, mimetype="text/plain; charset=utf-8")
        return Response("\ufeff" + sc.replace("\n", "\r\n"), mimetype="text/plain; charset=utf-8",
                        headers={"Content-Disposition": "attachment; filename=doi-may-chu-rustdesk.ps1"})

    @app.route("/rustdesk/client-cai.ps1")
    def rustdesk_script():
        try:
            sc = RD.script_client(secrets.token_hex(6))
        except RuntimeError as e:
            return Response(str(e), status=409, mimetype="text/plain; charset=utf-8")
        return Response("\ufeff" + sc.replace("\n", "\r\n") + "\r\n", mimetype="text/plain; charset=utf-8",
                        headers={"Content-Disposition": "attachment; filename=cai-rustdesk-client.ps1"})
