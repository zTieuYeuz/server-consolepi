# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Trang RustDesk (giao dien): cai/dieu khien may chu RustDesk tich hop. Logic o consolesystem/integrations/rustdesk_may_chu.py;
phan can du lieu may tram (cai client qua agent, danh sach may) o features/uem/uem_rustdesk.py."""
from flask import Response, jsonify, request

from consolesystem.integrations import rustdesk_may_chu as RD
from consolesystem.web import chon_may as CM

TRANG = """@CSS@<style>.rd-k{font-family:monospace;word-break:break-all;user-select:all;background:#111;padding:6px 8px;border-radius:6px}
.rd-chip{display:inline-block;padding:2px 9px;border-radius:10px;background:#333;margin-right:6px}.rd-chip.ok{background:#1f6f2e}.rd-chip.loi{background:#8a2a2a}
.rd-tb{width:100%;border-collapse:collapse}.rd-tb td,.rd-tb th{padding:6px 8px;border-bottom:1px solid #333;text-align:left}
.rd-buoc{display:inline-block;min-width:26px;height:26px;line-height:26px;text-align:center;border-radius:50%;background:#2d6cdf;color:#fff;font-weight:700;margin-right:8px}
.rd-o{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px}.rd-o label{display:block;font-weight:600;margin-bottom:4px}.rd-o input{width:100%;margin:0}
.rd-hd{margin-top:14px;padding:12px;border-left:3px solid #2d6cdf;background:rgba(45,108,223,.08);border-radius:6px}</style>
<div class="dep-tabs" id="rd-tabs" style="margin-bottom:14px;"><a href="#1" class="dep-tab" data-b="1">1. Máy chủ</a><a href="#2" class="dep-tab" data-b="2">2. Kết nối Internet</a><a href="#3" class="dep-tab" data-b="3">3. File cài đặt</a><a href="#4" class="dep-tab" data-b="4">4. Triển khai</a><a href="#5" class="dep-tab" data-b="5">5. Hỗ trợ từ xa</a></div>
<div class="card" data-buoc="1"><h3><span class="rd-buoc">1</span>Cài máy chủ RustDesk</h3>
<p class="tk-ghi">Máy chủ RustDesk (ID server hbbs + relay hbbr) chạy ngay trên Console System. Bấm cài một lần, Console tự tải bản chính thức (kiểm SHA-256) và tạo khóa.</p>
<div id="rd-tt">Đang tải...</div><div class="nut-hang" style="margin-top:10px;" id="rd-nut"></div><div class="tk-ghi" id="rd-tb"></div></div>
<div class="card" data-buoc="2" hidden><h3><span class="rd-buoc">2</span>Thông tin kết nối ra Internet</h3>
<p class="tk-ghi">Nhập tên miền (trỏ về IP WAN của router) hoặc IP WAN, và mật khẩu chung. Cổng cố định 21115, 21116, 21117. Để trống tên miền = chỉ dùng trong LAN.</p>
<div class="rd-o"><div><label for="rd-host">Tên miền hoặc IP WAN</label><input type="text" id="rd-host" placeholder="vd rustdesk.congty.com"></div>
<div><label for="rd-mk">Mật khẩu cố định chung cho các máy</label><input type="text" id="rd-mk" autocomplete="off" placeholder="8-64 ký tự: chữ, số, ! @ # % ^ * . _ -"></div></div>
<details style="margin-top:8px;"><summary class="tk-ghi">Nâng cao: máy chủ chuyển tiếp ở địa chỉ khác</summary><div class="rd-o" style="margin-top:6px;"><div><label for="rd-relay">Tên miền máy chủ chuyển tiếp (TCP 21117)</label><input type="text" id="rd-relay" placeholder="để trống = trùng tên miền ở trên"></div></div></details>
<div class="nut-hang" style="margin-top:10px;"><button class="tk-nut chinh" id="rd-luu" type="button">Lưu</button></div><div class="tk-ghi" id="rd-luu-tb" style="margin-top:6px;"></div>
<div class="rd-hd" id="rd-hd"></div></div>
<div class="card" data-buoc="3" hidden><h3><span class="rd-buoc">3</span>File cài đặt RustDesk</h3>
<p class="tk-ghi">Một file <b>.msi</b> duy nhất, chứa sẵn bộ cài RustDesk chính thức và đã điền máy chủ ID, máy chủ chuyển tiếp, key, mật khẩu chung ở bước 2. Máy nào (trong LAN hay ngoài Internet, không cần mạng để tải thêm) bấm đúp hoặc chạy <code>msiexec /i Cai-RustDesk-ConsoleSystem.msi /qn</code> là cài xong và kết nối về máy chủ này. File nằm sẵn trong kho Triển khai phần mềm và tự tạo lại khi đổi thông tin ở bước 2.</p>
<div>Máy chủ ID: <span class="rd-k" id="rd-h"></span> &nbsp; Máy chủ chuyển tiếp: <span class="rd-k" id="rd-r"></span></div><div style="margin-top:6px;">Key: <span class="rd-k" id="rd-key">(chưa có, cài máy chủ trước)</span></div>
<div class="nut-hang" style="margin-top:10px;"><button class="tk-nut chinh" type="button" id="rd-tai-msi" onclick="location.href='/rustdesk/Cai-RustDesk-ConsoleSystem.msi'">Tải file cài RustDesk (.msi)</button><button class="tk-nut" id="rd-kho" type="button">Tạo lại file</button></div>
<div class="tk-ghi" id="rd-kho-tb" style="margin-top:6px;"></div>
<p class="tk-ghi" style="margin-top:8px;">Lưu ý: file chứa mật khẩu chung, chỉ đưa cho người được phép.</p></div>
<div class="card" data-buoc="4" hidden><h3><span class="rd-buoc">4</span>Triển khai xuống máy</h3>
<p class="tk-ghi"><b>Cách A - qua Triển khai phần mềm</b> (máy có WinRM): vào <a href="/deployos/trienkhai/kichban">Kịch bản</a>, thêm bước <b>Phần mềm</b> chọn <b>Cai-RustDesk-ConsoleSystem.msi</b>, chọn máy rồi Chạy. Xong là ID của máy tự ghi vào Console.<br>
<b>Cách B - máy có agent</b>: chọn máy bên dưới rồi bấm Cài.<br><b>Cách C - máy ở xa, không quản lý được</b>: gửi file .msi ở bước 3 cho người dùng bấm đúp; sau đó mở RustDesk trên máy đó xem ID, nhập ID vào tab Hỗ trợ từ xa của máy.</p>
@KHUNG@
<div class="nut-hang" style="margin-top:8px;"><button class="tk-nut chinh" id="rd-cai-client" type="button">Cài lên máy đã chọn</button><button class="tk-nut" id="rd-ap" type="button" title="Máy đã cài RustDesk từ trước: đẩy máy chủ ID, chuyển tiếp và key mới xuống (qua agent)">Áp dụng địa chỉ xuống máy đã cài</button><button class="tk-nut" id="rd-mk-bo" type="button">Đồng bộ lại mật khẩu</button></div>
<div class="tk-ghi" id="rd-ct"></div><div class="tk-ghi" id="rd-mk-tb"></div>
<table class="rd-tb" id="rd-bang-may" style="margin-top:10px;"></table></div>
<div class="card" data-buoc="5" hidden><h3><span class="rd-buoc">5</span>Kết nối hỗ trợ từ xa</h3>
<p class="tk-ghi">Vào <a href="/uem">Quản lý máy trạm</a>, mở máy cần hỗ trợ, tab <b>Hỗ trợ từ xa</b>, bấm <b>Mở RustDesk và kết nối</b>. Máy anh đang ngồi cũng cần RustDesk trỏ về máy chủ này: cài luôn file .msi ở bước 3 trên máy của anh là xong.</p></div>
<div class="card" data-buoc="1"><h3>Thiết bị đã đăng ký với máy chủ</h3><table class="rd-tb" id="rd-dev"></table></div>
<script>(function(){var $=function(i){return document.getElementById(i);};var D0={},MK0='';
function e(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function api(u,b){return fetch(u,b?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}:{}).then(function(r){return r.json();});}
function chip(t,ok){return '<span class="rd-chip '+(ok?'ok':'loi')+'">'+t+'</span>';}
function hd(){var v=function(i){return $(i).value.trim().toLowerCase();},h=v('rd-host'),lan=D0.ip_lan||'IP-Console',id=h||lan,nat=id,udp=id,rl=v('rd-relay')||id,x='';
 x+='<b>Hướng dẫn mở cổng (NAT / port forward) trên router</b>'+(h?'':' <span class="rd-chip loi">chưa nhập tên miền: chỉ dùng trong LAN</span>')+'<br>Cần mở <b>3 cổng</b> (4 dòng NAT vì cổng 21116 cần cả TCP và UDP), chuyển về máy Console System <b>'+e(lan)+'</b>:';
 x+='<table class="rd-tb" style="margin-top:6px;"><tr><th>Bên ngoài (Internet)</th><th>Giao thức</th><th>Chuyển về (trong LAN)</th><th>Dùng cho</th></tr>';
 [[nat,21115,'TCP','Kiểm tra NAT'],[id,21116,'TCP','Máy chủ ID: gọi kết nối'],[udp,21116,'UDP','Máy chủ ID: đăng ký ID (bắt buộc UDP)'],[rl,21117,'TCP','Máy chủ chuyển tiếp']].forEach(function(a){
  x+='<tr><td><b>'+e(a[0])+':'+a[1]+'</b></td><td>'+a[2]+'</td><td>'+e(lan)+':'+a[1]+'</td><td>'+a[3]+'</td></tr>';});
 x+='</table><div style="margin-top:8px;">Client RustDesk sẽ dùng: Máy chủ ID <span class="rd-k">'+e(id)+'</span>, Máy chủ chuyển tiếp <span class="rd-k">'+e(rl)+'</span>, Key ở bước 3 (file cài tự điền).</div>';
 if(h&&!/^[0-9.]+$/.test(h)) x+='<div class="tk-ghi" style="margin-top:6px;">Các tên miền phải trỏ (bản ghi A hoặc DDNS) về IP công cộng của router. Nếu quản lý DNS trên Cloudflare thì để <b>DNS only</b> (đám mây xám).</div>';
 x+='<div class="tk-ghi" style="margin-top:6px;">Máy trong LAN cũng dùng các địa chỉ này, nên router cần hỗ trợ NAT loopback (hairpin).</div>';
 $('rd-hd').innerHTML=x;}
function ve(d){D0=d;
 var h='Phiên bản máy chủ: <b>'+e(d.ban)+'</b> ('+e(d.kien_truc||'chưa hỗ trợ')+')<br>';
 h+=d.da_cai?(chip('ID server (hbbs) '+(d.hbbs?'chạy':'dừng'),d.hbbs)+chip('Relay (hbbr) '+(d.hbbr?'chạy':'dừng'),d.hbbr)+chip('Cổng 21116 '+(d.cong['21116']?'mở':'đóng'),d.cong['21116'])):'<span class="rd-chip loi">Chưa cài</span>';
 $('rd-tt').innerHTML=h;
 $('rd-nut').innerHTML=!d.da_cai?'<button class="tk-nut chinh" data-v="cai"'+(d.cai.dang?' disabled':'')+'>Cài máy chủ RustDesk</button>':'<button class="tk-nut xanh" data-v="start">Chạy</button><button class="tk-nut" data-v="restart">Khởi động lại</button><button class="tk-nut" data-v="stop">Dừng</button><button class="tk-nut do" data-v="go">Gỡ dịch vụ</button>';
 $('rd-tb').textContent=d.cai.tb||'';
 [['rd-host',d.host],['rd-relay',d.relay],['rd-mk',d.mk_chung]].forEach(function(a){if(document.activeElement!==$(a[0])&&!$(a[0]).dataset.sua) $(a[0]).value=a[1]||'';});
 if(d.relay) $('rd-relay').closest('details').open=true; MK0=d.mk_chung||''; $('rd-h').textContent=d.dia_chi.id; $('rd-r').textContent=d.dia_chi.relay; $('rd-key').textContent=d.khoa||'(chưa có, cài máy chủ trước)';
 $('rd-kho-tb').textContent=d.kho.dang?d.kho.tb:(d.kho.co?('Đã có trong kho Triển khai phần mềm (Tài nguyên, Phần mềm): '+d.kho.ten+', tạo lúc '+new Date(d.kho.luc*1000).toLocaleString()):(d.kho.tb||'Chưa có (cần cài máy chủ và đặt mật khẩu chung ở bước 2).'));
 $('rd-tai-msi').disabled=!d.kho.co||d.kho.dang; if(d.kho.dang) setTimeout(tai,2000);
 hd(); if(d.cai.dang) setTimeout(tai,1500);}
function tai(){api('/rustdesk/api/trang-thai').then(ve);}
['rd-host','rd-relay','rd-mk'].forEach(function(i){$(i).addEventListener('input',function(){$(i).dataset.sua='1';hd();});});
$('rd-nut').addEventListener('click',function(ev){var v=ev.target.dataset.v; if(!v)return; if(v==='go'&&!confirm('Gỡ dịch vụ RustDesk Server?'))return;
 api(v==='cai'?'/rustdesk/api/cai':'/rustdesk/api/hanh-dong',{viec:v}).then(function(d){$('rd-tb').textContent=d.tb||'';tai();});});
$('rd-luu').onclick=function(){var mk=$('rd-mk').value.trim();
 api('/rustdesk/api/cau-hinh',{host:$('rd-host').value,relay:$('rd-relay').value,ten_nat:'',ten_udp:''}).then(function(d){
  var t=d.tb; var xong=function(){['rd-host','rd-relay','rd-mk'].forEach(function(i){delete $(i).dataset.sua;});$('rd-luu-tb').textContent=t;tai();setTimeout(dev,1500);};
  if(d.ok&&mk!==MK0) api('/rustdesk/api/mat-khau',{mk:mk}).then(function(m){t+=' '+m.tb;xong();}); else xong();});};
$('rd-kho').onclick=function(){api('/rustdesk/api/kho',{}).then(function(d){$('rd-kho-tb').textContent=d.tb;tai();});};
function dev(){api('/rustdesk/api/thiet-bi').then(function(d){var h='<tr><th>ID</th><th>IP gần nhất</th><th>Đăng ký lúc</th><th>Ghi chú</th></tr>';
 (d.ds||[]).forEach(function(x){h+='<tr><td><b>'+e(x.id)+'</b></td><td>'+e(x.ip)+'</td><td>'+e(x.tao)+'</td><td>'+e(x.ghi_chu)+'</td></tr>';});
 if(!(d.ds||[]).length) h+='<tr><td colspan="4" class="tk-ghi">Chưa có thiết bị nào đăng ký.</td></tr>'; $('rd-dev').innerHTML=h;
 $('rd-mk-tb').textContent=(d.dong_bo&&d.dong_bo.tb)||''; if(d.dong_bo&&d.dong_bo.dang) setTimeout(dev,2500);
 var m='<tr><th>Máy</th><th>ID RustDesk</th><th>Mật khẩu</th><th>Đồng bộ</th></tr>'; (d.may||[]).forEach(function(x){m+='<tr><td>'+e(x.ten)+'</td><td><b>'+e(x.id)+'</b></td><td><span class="rd-k">'+e(x.mk)+'</span></td><td>'+(x.dong_bo?'<span class="rd-chip ok">đã đồng bộ</span>':'<span class="rd-chip loi" title="'+e(x.loi)+'">chờ cập nhật</span>')+'</td></tr>';});
 $('rd-bang-may').innerHTML=(d.may||[]).length?m:''; ChonMay.ve('rd',d.agent||[]);});}
$('rd-cai-client').onclick=function(){var ids=ChonMay.chon('rd'); if(!ids.length){$('rd-ct').textContent='Chọn ít nhất một máy.';return;}
 $('rd-ct').textContent='Đang cài (có thể mất 1-2 phút mỗi máy)...'; api('/rustdesk/api/cai-client',{may:ids}).then(function(d){$('rd-ct').textContent=(d.kq||[]).map(function(x){return x.ten+': '+x.tb;}).join(' | ');dev();});};
$('rd-ap').onclick=function(){api('/rustdesk/api/ap-cau-hinh',{}).then(function(d){$('rd-ct').textContent=d.ok?'Đang áp dụng, xem kết quả bên dưới...':'Đang có việc khác chạy.';setTimeout(dev,2500);});};
$('rd-mk-bo').onclick=function(){api('/rustdesk/api/dong-bo',{}).then(function(d){$('rd-mk-tb').textContent=d.tb;setTimeout(dev,1500);});};
function buoc(){var b=(location.hash||'#1').slice(1); if(!/^[1-5]$/.test(b)) b='1';
 [].slice.call(document.querySelectorAll('[data-buoc]')).forEach(function(c){c.hidden=c.dataset.buoc!==b;});
 [].slice.call(document.querySelectorAll('#rd-tabs .dep-tab')).forEach(function(a){a.classList.toggle('on',a.dataset.b===b);});}
window.addEventListener('hashchange',buoc); buoc();
tai(); dev(); setInterval(function(){if(!document.hidden)tai();},8000);})();</script>"""


def register_rustdesk(app):
    from ui.layout import render_page

    @app.route("/rustdesk")
    def rustdesk_trang():
        body = TRANG.replace("@CSS@", CM.JS + CM.CSS + CM.thanh_tab(CM.TAB_REMOTE, "rustdesk")).replace("@KHUNG@", CM.khung("rd"))
        return render_page(body, active="/rustdesk", title="Phần mềm remote", subtitle="Remote RustDesk: máy chủ RustDesk tích hợp, file cài và triển khai")

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
        ok, tb = RD.dat_may_chu(str(j.get("host", "")), str(j.get("relay", "")), j.get("cong_id"), j.get("cong_relay"),
                                 str(j.get("ten_nat", "")), str(j.get("ten_udp", "")))
        return jsonify({"ok": ok, "tb": tb})

    @app.route("/rustdesk/doi-may-chu.ps1")
    def rustdesk_script_doi():
        try:
            sc = RD.script_cau_hinh_nguoi_dung()
        except RuntimeError as e:
            return Response(str(e), status=409, mimetype="text/plain; charset=utf-8")
        return Response("\ufeff" + sc.replace("\n", "\r\n"), mimetype="text/plain; charset=utf-8",
                        headers={"Content-Disposition": "attachment; filename=doi-may-chu-rustdesk.ps1"})

    @app.route("/rustdesk/api/kho", methods=["POST"])
    def rustdesk_api_kho():
        ok, tb = RD.cap_nhat_kho()
        return jsonify({"ok": ok, "tb": tb})

    @app.route("/rustdesk/Cai-RustDesk-ConsoleSystem.msi")
    def rustdesk_msi():
        import os
        from flask import send_file
        if not RD.tep_kho_tt()["co"]:
            return Response("Chưa có file MSI: cài máy chủ và đặt mật khẩu chung ở bước 2.", status=409, mimetype="text/plain; charset=utf-8")
        return send_file(os.path.join(RD._DD.APPS_DIR, RD.TEN_MSI), as_attachment=True, download_name=RD.TEN_MSI, mimetype="application/x-msi")
