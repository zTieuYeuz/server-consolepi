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
<div class="rd-2"><div class="card"><h3>Máy chủ ID và máy chủ chuyển tiếp</h3><p class="tk-ghi">Địa chỉ các máy RustDesk dùng để tìm tới máy chủ này. Có máy ở ngoài Internet thì nhập <b>tên miền hoặc IP công cộng</b>; để trống = dùng IP LAN (chỉ trong mạng nội bộ). Máy chủ chuyển tiếp để trống = trùng máy chủ ID.</p>
<label>Máy chủ ID</label><input type="text" id="rd-host" placeholder="tên miền hoặc IP công cộng" style="width:100%;">
<label style="margin-top:8px;display:block;">Máy chủ chuyển tiếp (relay)</label><input type="text" id="rd-relay" placeholder="để trống = trùng máy chủ ID" style="width:100%;">
<div class="tk-hang" style="margin-top:8px;"><button class="tk-nut chinh" id="rd-luu" type="button">Lưu</button><button class="tk-nut" id="rd-ap" type="button" title="Đẩy máy chủ ID, chuyển tiếp và key xuống các máy đã cài RustDesk (cần agent)">Áp dụng xuống các máy đã cài</button></div><div class="tk-ghi" id="rd-ap-tb"></div>
<p class="tk-ghi" style="margin-top:12px;"><b>Cổng cần mở ra Internet</b> (chuyển tiếp về máy này, IP LAN <b id="rd-lan"></b>):</p>
<table class="rd-tb"><tr><th>Cổng</th><th>Giao thức</th><th>Dùng cho</th></tr><tr><td>21115</td><td>TCP</td><td>Kiểm tra NAT</td></tr><tr><td>21116</td><td>TCP và UDP</td><td>Máy chủ ID (đăng ký ID, gọi kết nối)</td></tr><tr><td>21117</td><td>TCP</td><td>Máy chủ chuyển tiếp</td></tr></table>
<p class="tk-ghi">Máy trong LAN cũng sẽ dùng địa chỉ này, nên router cần hỗ trợ NAT loopback (hairpin); nếu không, máy trong LAN báo lỗi kết nối.</p></div>
<div class="card"><h3>Khóa và cấu hình cho client</h3><p class="tk-ghi">Điền vào RustDesk, Cài đặt, Mạng (các cách cài bên dưới đều tự điền sẵn):</p>
<div>Máy chủ ID: <span class="rd-k" id="rd-h"></span></div><div style="margin-top:6px;">Máy chủ chuyển tiếp: <span class="rd-k" id="rd-r"></span></div><div style="margin-top:6px;">Key:</div><div class="rd-k" id="rd-key">(chưa có, cài máy chủ trước)</div>
<p class="tk-ghi" style="margin-top:10px;"><b>Cài tự động:</b> thẻ <b>Cài RustDesk lên máy Windows có agent</b> bên dưới, hoặc bước <b>RustDesk</b> trong <a href="/deployos/trienkhai/kichban">Triển khai phần mềm</a>. Bộ cài RustDesk tải lên Tài nguyên cũng được cài kèm cấu hình.</p>
<p class="tk-ghi"><b>Cài tay</b> (máy không có agent, kể cả ngoài Internet): tải file, chạy bằng PowerShell quản trị.</p>
<div class="tk-hang"><a class="tk-nut" href="/rustdesk/client-cai.ps1">Tải script cài client (.ps1)</a><a class="tk-nut" href="/rustdesk/doi-may-chu.ps1" title="Máy đã cài RustDesk từ trước, chỉ đổi máy chủ ID / chuyển tiếp / key">Script đổi máy chủ cho RustDesk đã cài</a></div></div></div>
<div class="card"><h3>Mật khẩu cố định chung cho mọi máy</h3><p class="tk-ghi">Đặt một mật khẩu, Console System đẩy xuống <b>tất cả máy đã cài RustDesk</b> qua agent. Đổi mật khẩu ở đây thì mọi máy đổi theo; máy đang tắt sẽ chờ, bấm <b>Đồng bộ lại</b> khi máy bật. Máy cài mới cũng dùng mật khẩu này.</p>
<div class="tk-hang"><input type="text" id="rd-mk" autocomplete="off" placeholder="8-64 ký tự: chữ, số, ! @ # % ^ * . _ -" style="max-width:340px;margin:0;"><button class="tk-nut chinh" id="rd-mk-luu" type="button">Lưu và áp dụng cho tất cả</button><button class="tk-nut" id="rd-mk-bo" type="button">Đồng bộ lại</button></div><div class="tk-ghi" id="rd-mk-tb" style="margin-top:6px;"></div></div>
<div class="card"><h3>Cài RustDesk lên máy Windows có agent</h3><p class="tk-ghi">Chọn máy rồi bấm Cài: tải bản chính thức, cài im lặng, điền sẵn máy chủ ID / chuyển tiếp / key và đặt mật khẩu chung (chưa đặt mật khẩu chung thì mỗi máy một mật khẩu riêng, hiện ở bảng bên dưới).</p><div id="rd-may" class="tk-luoi"></div>
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
 if(document.activeElement!==$('rd-host')) $('rd-host').value=d.host||''; if(document.activeElement!==$('rd-relay')) $('rd-relay').value=d.relay||'';
 $('rd-h').textContent=d.host_hieu_luc||'(chưa xác định)'; $('rd-r').textContent=d.relay_hieu_luc||'(chưa xác định)'; $('rd-lan').textContent=d.ip_lan||'?'; $('rd-key').textContent=d.khoa||'(chưa có, cài máy chủ trước)';
 if(d.cai.dang) setTimeout(tai,1500);}
function tai(){api('/rustdesk/api/trang-thai').then(ve);}
$('rd-nut').addEventListener('click',function(ev){var v=ev.target.dataset.v; if(!v)return; if(v==='go'&&!confirm('Gỡ dịch vụ RustDesk Server?'))return;
 api(v==='cai'?'/rustdesk/api/cai':'/rustdesk/api/hanh-dong',{viec:v}).then(function(d){$('rd-tb').textContent=d.tb||'';tai();});});
$('rd-luu').onclick=function(){api('/rustdesk/api/cau-hinh',{host:$('rd-host').value,relay:$('rd-relay').value}).then(function(d){$('rd-tb').textContent=d.tb;tai();});};
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
        ok, tb = RD.dat_may_chu(str(j.get("host", "")), str(j.get("relay", "")))
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
            sc = RD.script_client(RD.mk_chung() or secrets.token_hex(6))
        except RuntimeError as e:
            return Response(str(e), status=409, mimetype="text/plain; charset=utf-8")
        return Response("\ufeff" + sc.replace("\n", "\r\n") + "\r\n", mimetype="text/plain; charset=utf-8",
                        headers={"Content-Disposition": "attachment; filename=cai-rustdesk-client.ps1"})
