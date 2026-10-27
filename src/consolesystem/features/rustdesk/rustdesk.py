# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Trang RustDesk (giao dien): cai/dieu khien may chu RustDesk tich hop. Logic o consolesystem/integrations/rustdesk_may_chu.py;
phan can du lieu may tram (cai client qua agent, danh sach may) o features/uem/uem_rustdesk.py."""
import json
import re

from flask import Response, jsonify, request

from consolesystem.integrations import rustdesk_may_chu as RD
from consolesystem.web import chon_may as CM

TRANG = """@CSS@<style>
.rd-k{font-family:var(--mono);font-size:13px;word-break:break-all;user-select:all;background:var(--pre-nen);color:var(--pre-chu);border:1px solid var(--vien);padding:5px 9px;border-radius:7px;font-variant-numeric:tabular-nums}
.rd-chep{margin-left:6px;padding:3px 9px;font-size:12px;border-radius:6px;border:1px solid var(--vien-ro);background:transparent;color:var(--chu-mo);cursor:pointer;min-height:0;font-weight:500;transition:color .18s,border-color .18s}
.rd-chep:hover{color:var(--chu);border-color:var(--nhan)}
.rd-chip{display:inline-flex;align-items:center;gap:6px;padding:3px 10px;border-radius:6px;background:var(--hang-nen);color:var(--chu-mo);font-size:12.5px;font-weight:500;margin:0 6px 4px 0;line-height:1.5}
.rd-chip::before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor;opacity:.9;flex:none}
.rd-chip.ok{background:var(--xanh-mo);color:var(--xanh)}.rd-chip.loi{background:var(--do-mo);color:var(--do)}.rd-chip.vang{background:var(--vang-mo);color:var(--vang)}
.rd-tb{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}.rd-tb td,.rd-tb th{padding:9px 10px;border-bottom:1px solid var(--vien);text-align:left;vertical-align:middle}
.rd-tb th{font-size:12px;font-weight:600;color:var(--chu-mo2);letter-spacing:.02em}.rd-tb tbody tr:hover,.rd-tb tr:hover td{background:var(--hang-hover)}
.rd-buoc{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:8px;background:var(--nhan-mo);color:var(--nhan-dam);font-weight:600;font-size:13px;margin-right:10px;flex:none}
.card[data-buoc]>h3{display:flex;align-items:center;font-size:18px;font-weight:600;letter-spacing:-.01em;margin:0 0 6px 0}
.card[data-buoc]>p.tk-ghi:first-of-type{max-width:78ch;line-height:1.6;margin-top:0}
.rd-o{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}.rd-o label{display:block;font-weight:500;margin-bottom:6px;font-size:13.5px;color:var(--chu-mo)}.rd-o input{width:100%;max-width:none;margin:0}
.rd-hd{margin-top:16px;padding:14px 16px;border:1px solid var(--vien);background:var(--the-noi);border-radius:10px;line-height:1.6}
.rd-chon{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
.rd-chon label{display:flex;gap:12px;align-items:flex-start;padding:16px;border:1px solid var(--vien-ro);border-radius:12px;cursor:pointer;margin:0;background:var(--the-noi);transition:border-color .2s,background .2s,transform .18s var(--muot)}
.rd-chon label:hover{border-color:var(--nhan)}.rd-chon label:active{transform:scale(.99)}
.rd-chon label.on{border-color:var(--nhan);background:var(--nhan-mo);box-shadow:inset 0 0 0 1px var(--nhan)}
.rd-chon input{margin:3px 0 0 0;flex:none;width:auto;accent-color:var(--nhan)}.rd-chon b{display:block;margin-bottom:6px;font-weight:600}.rd-chon small{display:block;color:var(--chu-mo);line-height:1.55;font-size:13px}
.rd-nen{position:fixed;inset:0;background:rgba(5,8,14,.62);backdrop-filter:blur(3px);display:flex;align-items:center;justify-content:center;z-index:1000;padding:16px;animation:rdHien .18s ease-out}
.rd-hop{background:var(--the);border:1px solid var(--vien-ro);border-radius:16px;max-width:460px;width:100%;padding:22px;box-shadow:0 24px 64px rgba(5,8,14,.55);animation:rdNoi .24s var(--muot)}
.rd-hop h3{margin:0 0 12px 0;font-weight:600}.rd-hop .nut-hang{justify-content:flex-end;margin-top:18px}
@keyframes rdHien{from{opacity:0}}@keyframes rdNoi{from{opacity:0;transform:translateY(8px) scale(.98)}}
#rd-ls{font-size:13px}#rd-ls td,#rd-ls th{padding:8px 7px}#rd-ls th{white-space:nowrap}
#rd-ls .rd-chip{font-size:12px;white-space:normal}.rd-nho{padding:4px 10px!important;font-size:12px!important;min-height:0!important;line-height:1.3!important;margin:0!important}
.rd-gh{display:flex;gap:6px;align-items:center;flex-wrap:nowrap;white-space:nowrap}.rd-video{width:100%;max-height:70vh;background:#05070a;border-radius:10px;margin-top:10px}
.rd-tong{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin-bottom:16px}
.rd-o-tt{display:block;text-decoration:none;color:inherit;background:var(--the);border:1px solid var(--vien);border-radius:12px;padding:12px 14px;transition:border-color .2s,transform .18s var(--muot)}
.rd-o-tt:hover{border-color:var(--vien-ro);transform:translateY(-1px)}.rd-o-tt small{display:block;font-size:12px;color:var(--chu-mo2);margin-bottom:4px}
.rd-o-tt b{display:flex;align-items:center;gap:8px;font-weight:600;font-size:15px;letter-spacing:-.01em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rd-cham{width:8px;height:8px;border-radius:50%;background:var(--chu-mo2);flex:none}.rd-cham.ok{background:var(--xanh);box-shadow:0 0 0 3px var(--xanh-mo)}.rd-cham.loi{background:var(--do);box-shadow:0 0 0 3px var(--do-mo)}.rd-cham.vang{background:var(--vang);box-shadow:0 0 0 3px var(--vang-mo)}
#rd-tabs{display:flex;flex-wrap:wrap;gap:14px 22px;align-items:flex-end;margin-bottom:16px}
.rd-nhom{display:flex;flex-direction:column;gap:6px}.rd-nhom>span{font-size:11.5px;font-weight:600;color:var(--chu-mo2);letter-spacing:.06em;text-transform:uppercase;padding-left:2px}
.rd-nhom>div{display:flex;flex-wrap:wrap;gap:6px}
#rd-tabs .dep-tab{gap:8px}#rd-tabs .dep-tab i{font-style:normal;display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:6px;background:var(--hang-nen);font-size:12px;font-weight:600;color:var(--chu-mo)}
#rd-tabs .dep-tab.xong i{background:var(--xanh-mo);color:var(--xanh)}#rd-tabs .dep-tab.on i{background:var(--nhan);color:var(--chu-tren-nhan)}
.rd-on{display:inline-flex;align-items:center;gap:7px;font-size:13px;color:var(--chu-mo)}
</style>
<div class="rd-tong" id="rd-tong" aria-live="polite">
<a class="rd-o-tt" href="#1"><small>Máy chủ RustDesk</small><b id="rd-t-mc"><span class="rd-cham"></span>Đang tải...</b></a>
<a class="rd-o-tt" href="#2"><small>Địa chỉ cho máy khách</small><b id="rd-t-dc"><span class="rd-cham"></span>...</b></a>
<a class="rd-o-tt" href="#5"><small>Máy đang báo về</small><b id="rd-t-nhip"><span class="rd-cham"></span>...</b></a>
<a class="rd-o-tt" href="#6"><small>Chế độ kết nối</small><b id="rd-t-cd"><span class="rd-cham"></span>...</b></a></div>
<nav id="rd-tabs" aria-label="Các bước RustDesk"><div class="rd-nhom"><span>Thiết lập (một lần)</span><div><a href="#1" class="dep-tab" data-b="1"><i>1</i>Máy chủ</a><a href="#2" class="dep-tab" data-b="2"><i>2</i>Kết nối Internet</a><a href="#3" class="dep-tab" data-b="3"><i>3</i>File cài đặt</a><a href="#4" class="dep-tab" data-b="4"><i>4</i>Triển khai</a></div></div>
<div class="rd-nhom"><span>Hằng ngày</span><div><a href="#5" class="dep-tab" data-b="5">Hỗ trợ từ xa</a><a href="#6" class="dep-tab" data-b="6">Cài đặt</a><a href="#7" class="dep-tab" data-b="7">Lịch sử kết nối</a></div></div></nav>
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
<div class="rd-o" style="margin-top:12px;"><div><label>Máy chủ ID</label><span class="rd-k" id="rd-h"></span><button class="rd-chep" type="button" data-chep="rd-h">Chép</button></div><div><label>Máy chủ chuyển tiếp</label><span class="rd-k" id="rd-r"></span><button class="rd-chep" type="button" data-chep="rd-r">Chép</button></div></div>
<div style="margin-top:12px;"><label style="display:block;font-size:13.5px;color:var(--chu-mo);margin-bottom:6px;font-weight:500;">Key</label><span class="rd-k" id="rd-key">(chưa có, cài máy chủ trước)</span><button class="rd-chep" type="button" data-chep="rd-key">Chép</button></div>
<div class="nut-hang" style="margin-top:16px;"><button class="tk-nut chinh" type="button" id="rd-tai-msi" onclick="location.href='/rustdesk/Cai-RustDesk-ConsoleSystem.msi'">Tải file cài RustDesk (.msi)</button><button class="tk-nut" id="rd-kho" type="button">Tạo lại file</button></div>
<div class="tk-ghi" id="rd-kho-tb" style="margin-top:6px;"></div>
<p class="tk-ghi" style="margin-top:8px;">Lưu ý: file chứa mật khẩu chung, chỉ đưa cho người được phép.</p></div>
<div class="card" data-buoc="4" hidden><h3><span class="rd-buoc">4</span>Triển khai xuống máy</h3>
<p class="tk-ghi"><b>Cách A - qua Triển khai phần mềm</b> (máy có WinRM): vào <a href="/deployos/trienkhai/kichban">Kịch bản</a>, thêm bước <b>Phần mềm</b> chọn <b>Cai-RustDesk-ConsoleSystem.msi</b>, chọn máy rồi Chạy. Xong là ID của máy tự ghi vào Console.<br>
<b>Cách B - máy có agent</b>: chọn máy bên dưới rồi bấm Cài.<br><b>Cách C - máy ở xa, không quản lý được</b>: gửi file .msi ở bước 3 cho người dùng bấm đúp; sau đó mở RustDesk trên máy đó xem ID, nhập ID vào tab Hỗ trợ từ xa của máy.</p>
@KHUNG@
<div class="nut-hang" style="margin-top:8px;"><button class="tk-nut chinh" id="rd-cai-client" type="button">Cài lên máy đã chọn</button><button class="tk-nut" id="rd-ap" type="button" title="Máy đã cài RustDesk từ trước: đẩy máy chủ ID, chuyển tiếp và key mới xuống (qua agent)">Áp dụng địa chỉ xuống máy đã cài</button><button class="tk-nut" id="rd-mk-bo" type="button">Đồng bộ lại mật khẩu</button></div>
<div class="tk-ghi" id="rd-ct"></div><div class="tk-ghi" id="rd-mk-tb"></div>
<table class="rd-tb" id="rd-bang-may" style="margin-top:10px;"></table></div>
<div class="card" data-buoc="5" hidden><h3>Kết nối hỗ trợ từ xa</h3>
<p class="tk-ghi">Bấm <b>Kết nối</b> trên dòng máy cần hỗ trợ để mở ứng dụng RustDesk trên máy anh đang ngồi và vào thẳng máy đó. Máy anh đang ngồi cũng cần RustDesk trỏ về máy chủ này (cài file .msi ở bước 3).</p>
<div class="rd-hd" style="margin:0 0 14px 0;display:flex;gap:10px;align-items:center;flex-wrap:wrap;">Chế độ đang áp dụng: <b id="rd-che-do">...</b> <a href="#6">Đổi ở Cài đặt</a></div>
<div class="nut-hang" style="margin-bottom:8px;"><input type="search" id="rd-tim" placeholder="Tìm theo tên máy, IP hoặc ID RustDesk" style="margin:0;max-width:380px;"><span class="tk-ghi" id="rd-kn-tb"></span></div>
<div style="overflow:auto;"><table class="rd-tb" id="rd-bang-kn"></table></div>
<div id="rd-kt" class="rd-hd" hidden></div>
<h4 style="margin:22px 0 8px 0;font-weight:600;">ID đã đăng ký nhưng chưa gắn vào máy nào</h4>
<div style="overflow:auto;"><table class="rd-tb" id="rd-chua"></table></div></div>
<div class="card" data-buoc="6" hidden><h3>Cài đặt kết nối</h3>
<p class="tk-ghi">Chế độ áp dụng cho <b>mọi</b> kết nối RustDesk vào các máy trỏ về máy chủ này, kể cả người tự mở RustDesk và gõ ID, mật khẩu (không chỉ nút Kết nối ở bước 5).</p>
<div class="rd-chon" id="rd-chon"><label data-cd="thong_bao"><input type="radio" name="rd-cd" value="thong_bao"><span><b>1. Thông báo</b><small>Kết nối vào được ngay. Màn hình máy được kết nối hiện thông báo đang có người kết nối vào (tên người dùng Console System nếu bấm từ Console, không thì tên máy kết nối tới).</small></span></label>
<label data-cd="xin_phep"><input type="radio" name="rd-cd" value="xin_phep"><span><b>2. Xin phép trước khi kết nối</b><small>Bấm Kết nối ở bước 5: giữa màn hình máy hiện hộp "<i>tên người dùng Console</i> xin quyền kết nối vào máy tính của bạn", chờ tối đa 5 phút. Người dùng bấm Có mới kết nối được; từ chối hoặc 5 phút không trả lời thì hủy. Mọi kết nối không qua bước xin phép này bị ngắt ngay. Máy cần có agent và có người đang đăng nhập. Console System khởi động lại (cập nhật, mất điện) thì phiên đang mở bị ngắt, cần xin phép lại.</small></span></label></div>
<h4 style="margin:22px 0 10px 0;font-weight:600;">Ghi hình phiên kết nối</h4>
<label class="tk-o" style="display:flex;gap:8px;align-items:center;"><input type="checkbox" id="rd-ghi" style="width:auto;margin:0;"> Tự động ghi hình mọi phiên điều khiển và lưu lên Console System</label>
<div class="nut-hang" style="margin-top:8px;"><label for="rd-gb" style="margin:0;">Dung lượng tối đa dành cho bản ghi</label><input type="number" id="rd-gb" min="1" max="10000" step="1" style="width:110px;margin:0;"> GB <span class="tk-ghi">vượt quá thì tự xóa bản ghi cũ nhất</span></div>
<p class="tk-ghi" style="margin-top:6px;">RustDesk trên máy được kết nối tự ghi màn hình (thư mục C:\\ProgramData\\RustDesk\\recording), Console lấy về qua agent sau khi phiên kết thúc (vài phút) rồi xóa trên máy. Xem lại ở tab Lịch sử kết nối. Chỉ máy có agent mới được lấy bản ghi về; máy không có agent (cài file .msi bằng tay) vẫn tự ghi và giữ bản ghi trên máy. Bản ghi lớn hơn 2 GB không lấy về được.</p>
<div class="nut-hang" style="margin-top:10px;"><button class="tk-nut chinh" id="rd-cd-luu" type="button">Lưu cài đặt</button><span class="tk-ghi" id="rd-cd-tb"></span></div>
<div class="rd-hd" id="rd-cd-tt"></div></div>
<div class="card" data-buoc="7" hidden><h3>Lịch sử kết nối</h3>
<p class="tk-ghi">Mọi kết nối RustDesk vào các máy (máy tự báo về Console System) và các lần xin phép từ Console. Giữ 90 ngày.</p>
<div class="nut-hang" style="margin-bottom:8px;"><input type="search" id="rd-ls-tim" placeholder="Tìm theo máy, người kết nối, IP" style="margin:0;max-width:380px;"><button class="tk-nut" id="rd-ls-tai" type="button">Tải lại</button><span class="tk-ghi" id="rd-ls-dem"></span></div>
<div id="rd-xem" hidden></div>
<div style="overflow:auto;"><table class="rd-tb" id="rd-ls"></table></div></div>
<div class="card" data-buoc="1"><h3 style="font-size:16px;font-weight:600;margin:0 0 8px 0;">Thiết bị đã đăng ký với máy chủ</h3><table class="rd-tb" id="rd-dev"></table></div>
<script>(function(){var $=function(i){return document.getElementById(i);};var D0={},MK0='';
function e(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function api(u,b){return fetch(u,b?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}:{}).then(function(r){return r.json();});}
function chip(t,ok){return '<span class="rd-chip '+(ok?'ok':'loi')+'">'+t+'</span>';}
function hd(){var v=function(i){return $(i).value.trim().toLowerCase();},h=v('rd-host'),lan=D0.ip_lan||'IP-Console',id=h||lan,nat=id,udp=id,rl=v('rd-relay')||id,x='';
 x+='<b>Hướng dẫn mở cổng (NAT / port forward) trên router</b>'+(h?'':' <span class="rd-chip loi">chưa nhập tên miền: chỉ dùng trong LAN</span>')+'<br>Cần mở <b>4 cổng</b> (5 dòng NAT vì cổng 21116 cần cả TCP và UDP), chuyển về máy Console System <b>'+e(lan)+'</b>:';
 x+='<table class="rd-tb" style="margin-top:6px;"><tr><th>Bên ngoài (Internet)</th><th>Giao thức</th><th>Chuyển về (trong LAN)</th><th>Dùng cho</th></tr>';
 [[nat,21115,'TCP','Kiểm tra NAT'],[id,21116,'TCP','Máy chủ ID: gọi kết nối'],[udp,21116,'UDP','Máy chủ ID: đăng ký ID (bắt buộc UDP)'],[rl,21117,'TCP','Máy chủ chuyển tiếp'],[id,21114,'TCP','Nhật ký kết nối, chế độ Thông báo / Xin phép (tab 6)']].forEach(function(a){
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
 hd(); if(d.cai.dang) setTimeout(tai,1500);
 var chay=d.da_cai&&d.hbbs&&d.hbbr;o('rd-t-mc',d.da_cai?(chay?'ok':'loi'):'vang',!d.da_cai?'Chưa cài':(chay?'Đang chạy':'Đã dừng'));
 o('rd-t-dc',d.host?'ok':'vang',d.dia_chi.id+(d.host?'':' (chỉ LAN)'));
 XONG[1]=!!chay;XONG[2]=!!(d.host&&d.mk_chung);XONG[3]=!!d.kho.co;danhBuoc();}
var XONG={1:false,2:false,3:false,4:false},DA_CHON=!!location.hash;
function o(id,mau,t){$(id).innerHTML='<span class="rd-cham '+mau+'"></span>'+e(t);}
function danhBuoc(){[].slice.call(document.querySelectorAll('#rd-tabs .dep-tab')).forEach(function(a){var b=a.dataset.b;a.classList.toggle('xong',!!XONG[b]);
  var i=a.querySelector('i');if(i)i.textContent=XONG[b]?'✓':b;});
 if(!DA_CHON&&XONG[1]&&XONG[2]&&XONG[3]&&XONG[4]){DA_CHON=true;location.hash='#5';}}
function tong(){api('/rustdesk/api/cai-dat').then(function(d){
  o('rd-t-nhip',d.nhip_gan>0?'ok':(d.tong_may?'vang':''),d.nhip_gan+' / '+d.tong_may+' máy');
  o('rd-t-cd',d.che_do==='xin_phep'?'vang':'ok',(d.che_do==='xin_phep'?'Xin phép':'Thông báo')+(d.ghi_hinh?' · ghi hình':''));});}
document.addEventListener('click',function(ev){var c=ev.target.dataset&&ev.target.dataset.chep;if(!c)return;var t=$(c).textContent,b=ev.target;
 var xong=function(){b.textContent='Đã chép';setTimeout(function(){b.textContent='Chép';},1500);};
 if(navigator.clipboard&&window.isSecureContext)navigator.clipboard.writeText(t).then(xong);else{var x=document.createElement('textarea');x.value=t;document.body.appendChild(x);x.select();try{document.execCommand('copy');}catch(_){}x.remove();xong();}});
function tai(){api('/rustdesk/api/trang-thai').then(ve);}
['rd-host','rd-relay','rd-mk'].forEach(function(i){$(i).addEventListener('input',function(){$(i).dataset.sua='1';hd();});});
$('rd-nut').addEventListener('click',function(ev){var v=ev.target.dataset.v; if(!v)return; var HOI={restart:'Khởi động lại máy chủ RustDesk? Các phiên điều khiển đang mở sẽ bị ngắt vài giây.',stop:'Dừng máy chủ RustDesk? Các máy sẽ không đăng ký ID và không điều khiển từ xa được cho tới khi chạy lại.',go:'Gỡ dịch vụ RustDesk Server? (Khóa và danh sách thiết bị vẫn được giữ.)'};
 if(HOI[v]&&!confirm(HOI[v]))return;
 api(v==='cai'?'/rustdesk/api/cai':'/rustdesk/api/hanh-dong',{viec:v}).then(function(d){$('rd-tb').textContent=d.tb||'';tai();});});
$('rd-luu').onclick=function(){var mk=$('rd-mk').value.trim();
 api('/rustdesk/api/cau-hinh',{host:$('rd-host').value,relay:$('rd-relay').value,ten_nat:'',ten_udp:''}).then(function(d){
  var t=d.tb; var xong=function(){['rd-host','rd-relay','rd-mk'].forEach(function(i){delete $(i).dataset.sua;});$('rd-luu-tb').textContent=t;tai();setTimeout(dev,1500);};
  if(d.ok&&mk!==MK0) api('/rustdesk/api/mat-khau',{mk:mk}).then(function(m){t+=' '+m.tb;xong();}); else xong();});};
$('rd-kho').onclick=function(){api('/rustdesk/api/kho',{}).then(function(d){$('rd-kho-tb').textContent=d.tb;tai();});};
function dev(){api('/rustdesk/api/thiet-bi').then(function(d){var h='<tr><th>ID</th><th>Tên máy</th><th>IP gần nhất</th><th>Đăng ký lúc</th></tr>';
 (d.ds||[]).forEach(function(x){h+='<tr><td><b>'+e(x.id)+'</b></td><td>'+(x.ten?e(x.ten):'<span class="tk-ghi">chưa rõ</span>')+'</td><td>'+e(x.ip)+'</td><td>'+e(x.tao)+'</td></tr>';});
 if(!(d.ds||[]).length) h+='<tr><td colspan="4" class="tk-ghi">Chưa có thiết bị nào đăng ký.</td></tr>'; $('rd-dev').innerHTML=h;
 $('rd-mk-tb').textContent=(d.dong_bo&&d.dong_bo.tb)||''; if(d.dong_bo&&d.dong_bo.dang) setTimeout(dev,2500);
 var m='<tr><th>Máy</th><th>ID RustDesk</th><th>Mật khẩu</th><th>Đồng bộ</th></tr>'; (d.may||[]).forEach(function(x){m+='<tr><td>'+e(x.ten)+'</td><td><b>'+e(x.id)+'</b></td><td><span class="rd-k">'+e(x.mk)+'</span></td><td>'+(x.dong_bo?'<span class="rd-chip ok">đã đồng bộ</span>':'<span class="rd-chip loi" title="'+e(x.loi)+'">chờ cập nhật</span>')+'</td></tr>';});
 $('rd-bang-may').innerHTML=(d.may||[]).length?m:''; ChonMay.ve('rd',d.agent||[]);});}
$('rd-cai-client').onclick=function(){var ids=ChonMay.chon('rd'); if(!ids.length){$('rd-ct').textContent='Chọn ít nhất một máy.';return;}
 $('rd-ct').textContent='Đang cài (có thể mất 1-2 phút mỗi máy)...'; api('/rustdesk/api/cai-client',{may:ids}).then(function(d){$('rd-ct').textContent=(d.kq||[]).map(function(x){return x.ten+': '+x.tb;}).join(' | ');dev();});};
$('rd-ap').onclick=function(){api('/rustdesk/api/ap-cau-hinh',{}).then(function(d){$('rd-ct').textContent=d.ok?'Đang áp dụng, xem kết quả bên dưới...':'Đang có việc khác chạy.';setTimeout(dev,2500);});};
$('rd-mk-bo').onclick=function(){api('/rustdesk/api/dong-bo',{}).then(function(d){$('rd-mk-tb').textContent=d.tb;setTimeout(dev,1500);});};
var BANG={may:[],chua_gan:[],tat_ca:[]},KN_OK=false;
function bo(x){return (x||'').replace(/đ/g,'d').replace(/Đ/g,'D').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();}
function veKn(){var q=bo($('rd-tim').value),h='<tr><th>Máy</th><th>IP</th><th>Trạng thái</th><th>ID RustDesk</th><th>Mật khẩu</th><th></th></tr>',n=0;
 BANG.may.forEach(function(x){if(q&&bo(x.ten+' '+x.ip+' '+x.id).indexOf(q)<0)return;n++;
  var tt=x.agent?'<span class="rd-on"><span class="rd-cham '+(x.online?'ok':'')+'"></span>'+(x.online?'Online':'Offline')+'</span>':'<span class="rd-on"><span class="rd-cham"></span>Không có agent</span>';
  h+='<tr><td><b>'+e(x.ten)+'</b></td><td>'+e(x.ip)+'</td><td>'+tt+'</td><td>'+(x.id?'<b>'+e(x.id)+'</b>':'<span class="tk-ghi">chưa có (cài ở bước 3-4)</span>')+'</td><td>'+(x.id?'<span class="rd-k">'+e(x.mk||'chưa đặt')+'</span>':'')+'</td><td style="white-space:nowrap;">'
   +(x.id?'<button class="tk-nut chinh" data-kn="'+e(x.mid)+'" type="button">Kết nối</button> ':'')+(x.agent?'<button class="tk-nut" data-kt="'+e(x.mid)+'" type="button">Kiểm tra máy</button>':'')+'</td></tr>';});
 $('rd-bang-kn').innerHTML=n?h:'<tr><td class="tk-ghi">'+(BANG.may.length?'Không có máy nào khớp.':'Chưa có máy nào có agent hoặc ID RustDesk.')+'</td></tr>';
 var c='<tr><th>ID</th><th>IP gần nhất</th><th>Đăng ký lúc</th><th>Gắn vào máy</th></tr>';
 BANG.chua_gan.forEach(function(x){var o='<option value="">-- chọn máy --</option>'+BANG.tat_ca.map(function(m){return '<option value="'+e(m.mid)+'"'+(m.ten===x.goi_y?' selected':'')+'>'+e(m.ten)+'</option>';}).join('');
  c+='<tr><td><b>'+e(x.id)+'</b></td><td>'+e(x.ip)+'</td><td>'+e(x.tao)+'</td><td><select data-gan="'+e(x.id)+'" style="margin:0;max-width:220px;">'+o+'</select> <button class="tk-nut" data-gan-nut="'+e(x.id)+'" type="button">Gắn</button></td></tr>';});
 $('rd-chua').innerHTML=BANG.chua_gan.length?c:'<tr><td class="tk-ghi">Mọi ID đã đăng ký đều đã gắn vào máy.</td></tr>';}
var TEN_CD={thong_bao:'Thông báo (vào được ngay, máy hiện thông báo)',xin_phep:'Xin phép trước khi kết nối (chờ người dùng đồng ý tối đa 5 phút)'};
function taiKn(){api('/rustdesk/api/bang').then(function(d){BANG=d;XONG[4]=d.may.some(function(x){return !!x.id;});danhBuoc();if(document.activeElement!==$('rd-tim')&&!document.querySelector('[data-gan]:focus'))veKn();$('rd-che-do').textContent=TEN_CD[d.che_do]||d.che_do;});}
$('rd-tim').addEventListener('input',veKn);
function moRd(mid,url){var m=BANG.may.filter(function(x){return x.mid===mid;})[0]||{},n=document.createElement('div');n.className='rd-nen';
 n.innerHTML='<div class="rd-hop" role="dialog" aria-modal="true"><h3>Mở RustDesk để kết nối?</h3><div>Máy: <b>'+e(m.ten||'')+'</b> ('+e(m.ip||'')+')</div><div style="margin-top:4px;">ID RustDesk: <span class="rd-k">'+e(m.id||'')+'</span></div>'
  +'<p class="tk-ghi" style="margin-top:10px;">Bấm Mở để chạy ứng dụng RustDesk trên máy anh đang ngồi. Trình duyệt có thể hỏi thêm một lần "mở ứng dụng RustDesk", muốn tắt hẳn câu hỏi đó: <a href="/rustdesk/cho-phep-trinh-duyet.reg">tải file cho phép (Chrome / Edge)</a>, chạy một lần trên máy này.</p>'
  +'<div class="nut-hang"><button class="tk-nut" type="button" data-v="huy">Hủy</button><button class="tk-nut chinh" type="button" data-v="mo">Mở RustDesk</button></div></div>';
 document.body.appendChild(n);var dong=function(){n.remove();document.removeEventListener('keydown',k);},k=function(ev){if(ev.key==='Escape')dong();};document.addEventListener('keydown',k);
 n.addEventListener('click',function(ev){var v=ev.target.dataset.v;if(ev.target===n||v==='huy'){dong();$('rd-kn-tb').textContent='Đã hủy mở RustDesk.';}else if(v==='mo'){dong();location.href=url;}});
 n.querySelector('[data-v=mo]').focus();}
function theoKn(ma,t,bd){api('/rustdesk/api/ket-noi/'+ma).then(function(d){if(!d.xong){$('rd-kn-tb').textContent=d.tb+' ('+Math.round((Date.now()-bd)/1000)+' giây)';setTimeout(function(){theoKn(ma,t,bd);},2000);return;}
 t.disabled=false;$('rd-kn-tb').textContent=d.tb;if(d.ok&&d.url)moRd(t.dataset.kn,d.url);});}
$('rd-bang-kn').addEventListener('click',function(ev){var t=ev.target,mid=t.dataset.kn||t.dataset.kt;if(!mid)return;
  if(t.dataset.kn){t.disabled=true;$('rd-kn-tb').textContent='Đang gửi yêu cầu...';
  api('/rustdesk/api/ket-noi',{mid:mid}).then(function(d){$('rd-kn-tb').textContent=d.tb;if(!d.xong&&d.ma){theoKn(d.ma,t,Date.now());return;}t.disabled=false;if(d.ok&&d.url)moRd(t.dataset.kn,d.url);});}
 else{t.disabled=true;$('rd-kt').hidden=false;$('rd-kt').textContent='Đang kiểm tra...';
  api('/rustdesk/api/kiem-tra',{mid:mid}).then(function(d){t.disabled=false;var k=d.kq;
   if(!d.ok){$('rd-kt').textContent='Lỗi: '+d.tb;return;} if(!k.cai){$('rd-kt').textContent='RustDesk chưa được cài trên máy này.';return;}
   $('rd-kt').innerHTML='<b>Kiểm tra máy</b><br>RustDesk '+e(k.ban)+', dịch vụ: <b>'+e(k.dich_vu)+'</b>, ID: <b>'+e(k.id)+'</b><br>Máy chủ ID: '+e(k.may_chu)+' · Chuyển tiếp: '+e(k.relay)+' · Tự ghi hình: '+(k.ghi_hinh?'bật':'tắt')+'<br>'+(k.dung_may_chu?'<span class="rd-chip ok">Đang trỏ đúng máy chủ này</span>':'<span class="rd-chip loi">Đang trỏ SAI máy chủ</span> bấm "Áp dụng địa chỉ xuống máy đã cài" ở bước 4');});}});
$('rd-chua').addEventListener('click',function(ev){var i=ev.target.dataset.ganNut;if(!i)return;var sel=document.querySelector('[data-gan="'+i+'"]');if(!sel.value){$('rd-kn-tb').textContent='Chọn máy cần gắn.';return;}
 api('/rustdesk/api/gan',{id:i,mid:sel.value}).then(function(d){$('rd-kn-tb').textContent=d.tb;taiKn();dev();});});
function gb(x){return (x/1073741824).toFixed(x>=1073741824*10?0:2)+' GB';}
var CD0={};function taiCd(){api('/rustdesk/api/cai-dat').then(function(d){CD0=d;if(!$('rd-chon').dataset.sua){[].slice.call(document.querySelectorAll('input[name=rd-cd]')).forEach(function(i){i.checked=i.value===d.che_do;});
  $('rd-ghi').checked=!!d.ghi_hinh;$('rd-gb').value=d.ghi_hinh_gb;danhDau();}
 var a=d.may_chu_api,x='<b>Tình trạng</b><br>';
 x+=a.chay?chip('Đang nhận nhật ký kết nối ở cổng '+a.cong,true):chip('Chưa nhận được nhật ký: '+(a.loi||'chưa chạy'),false);
 x+=chip(d.nhip_gan+' / '+d.tong_may+' máy đang báo về (2 phút gần nhất)',d.nhip_gan>0)+'<br>';
 x+='<div class="tk-ghi" style="margin-top:6px;">Máy chỉ báo về được khi tới được <b>'+e(d.host)+':'+d.cong_api_ngoai+'</b> (TCP). Router cần NAT cổng này về Console System cổng '+a.cong+' (xem bảng ở bước 2). Máy chưa báo về thì Console không áp được chế độ và không có lịch sử cho máy đó.</div>';
 x+='<div style="margin-top:8px;">Bản ghi hình đang lưu: <b>'+d.ghi_hinh_so+'</b> file, '+kt(d.ghi_hinh_dung)+' / '+d.ghi_hinh_gb+' GB · Ổ đĩa còn trống '+gb(d.dia_trong)+'</div>';
 if(d.thu_ghi&&d.thu_ghi.tb) x+='<div class="tk-ghi">'+e(d.thu_ghi.tb)+(d.thu_ghi.luc?' ('+new Date(d.thu_ghi.luc*1000).toLocaleString()+')':'')+'</div>';
 $('rd-cd-tt').innerHTML=x;});}
function danhDau(){[].slice.call(document.querySelectorAll('#rd-chon label')).forEach(function(l){l.classList.toggle('on',l.querySelector('input').checked);});}
$('rd-chon').addEventListener('change',function(){$('rd-chon').dataset.sua='1';danhDau();});
['rd-ghi','rd-gb'].forEach(function(i){$(i).addEventListener('input',function(){$('rd-chon').dataset.sua='1';});});
$('rd-cd-luu').onclick=function(){var c=document.querySelector('input[name=rd-cd]:checked');if(!c){$('rd-cd-tb').textContent='Chọn một chế độ.';return;}
 if($('rd-ghi').checked!==!!CD0.ghi_hinh&&!confirm(($('rd-ghi').checked?'Bật':'Tắt')+' ghi hình? Console sẽ cập nhật RustDesk trên mọi máy có agent và khởi động lại dịch vụ RustDesk ở đó: các phiên đang mở bị ngắt vài giây.'))return;
 if(c.value==='xin_phep'&&CD0.che_do!=='xin_phep'&&!confirm('Bật chế độ Xin phép? Mọi kết nối RustDesk không qua nút Kết nối của Console (và được người dùng bấm Có) sẽ bị ngắt. Máy không có ai đăng nhập sẽ không vào được.'))return;
 api('/rustdesk/api/cai-dat',{che_do:c.value,ghi_hinh:$('rd-ghi').checked,ghi_hinh_gb:$('rd-gb').value}).then(function(d){$('rd-cd-tb').textContent=d.tb;if(d.ok){delete $('rd-chon').dataset.sua;taiCd();taiKn();}});};
function kt(x){return x>=1073741824?(x/1073741824).toFixed(2)+' GB':x>=1048576?(x/1048576).toFixed(1)+' MB':Math.max(1,Math.round(x/1024))+' KB';}
var LS=[];function tg(t){return t?new Date(t*1000).toLocaleString():'';}
function dai(p){if(!p.ket_thuc)return p.loai==='Yêu cầu từ Console'?'':'<span class="rd-chip ok">đang mở</span>';var s=Math.round(p.ket_thuc-p.bat_dau);return s<60?s+' giây':Math.floor(s/60)+' phút '+(s%60)+' giây';}
function veLs(){var q=bo($('rd-ls-tim').value),h='<tr><th style="min-width:95px;">Bắt đầu</th><th style="min-width:120px;">Máy</th><th style="min-width:120px;">Người kết nối</th><th>Từ IP</th><th>Loại</th><th>Thời lượng</th><th style="min-width:120px;">Kết quả</th><th style="min-width:215px;">Ghi hình</th></tr>',n=0;
 LS.forEach(function(p,i){p.kq=String(p.kq||'').replace(' (chế độ Thông báo)','');var ai=(p.nguoi_console?p.nguoi_console+' (Console)':'')+(p.nguoi?(p.nguoi_console?' · ':'')+p.nguoi+(p.peer?' ['+p.peer+']':''):'');
  if(q&&bo([p.may,p.rid,ai,p.ip,p.kq].join(' ')).indexOf(q)<0)return;n++;
  var ok=/^Đã vào|^Đồng ý|^Mở kết nối/.test(p.kq),loi=/^Bị ngắt|từ chối|hủy|Không/.test(p.kq);
  h+='<tr><td>'+tg(p.bat_dau)+'</td><td><b>'+e(p.may||'?')+'</b><br><small class="tk-ghi">'+e(p.rid)+'</small></td><td>'+e(ai||'-')+'</td><td style="white-space:nowrap;">'+e(p.ip)+'</td><td>'+e(p.loai)+'</td><td style="white-space:nowrap;">'+dai(p)+'</td><td>'+(ok?chip(e(p.kq),true):loi?chip(e(p.kq),false):e(p.kq))+'</td><td>'
   +(p.ghi_hinh||[]).map(function(g,j){return '<div class="rd-gh"><button class="tk-nut chinh rd-nho" type="button" data-xem="'+i+':'+j+'">Xem</button><button class="tk-nut rd-nho" type="button" data-tai="/rustdesk/ghi-hinh/'+encodeURIComponent(g.mid)+'/'+encodeURIComponent(g.ten)+'?tai=1">Tải</button><button class="tk-nut do rd-nho" type="button" data-xoa="'+i+':'+j+'">Xóa</button><small class="tk-ghi">'+kt(g.kich_thuoc)+'</small></div>';}).join('')+'</td></tr>';});
 $('rd-ls').innerHTML=n?h:'<tr><td class="tk-ghi">'+(LS.length?'Không có dòng nào khớp.':'Chưa có kết nối nào được ghi lại.')+'</td></tr>';$('rd-ls-dem').textContent=n+' dòng';}
function taiLs(){api('/rustdesk/api/lich-su').then(function(d){LS=d.ds||[];veLs();});}
$('rd-ls-tim').addEventListener('input',veLs);$('rd-ls-tai').onclick=taiLs;
$('rd-ls').addEventListener('click',function(ev){if(ev.target.dataset.tai){location.href=ev.target.dataset.tai;return;}var z=ev.target.dataset.xoa;if(z){var b=z.split(':'),k=LS[+b[0]].ghi_hinh[+b[1]];
  if(confirm('Xóa bản ghi hình '+k.ten+'? Không khôi phục được.'))api('/rustdesk/api/ghi-hinh/xoa',{mid:k.mid,ten:k.ten}).then(function(d){$('rd-ls-dem').textContent=d.tb;taiLs();});return;}
 var x=ev.target.dataset.xem;if(!x)return;var a=x.split(':'),g=LS[+a[0]].ghi_hinh[+a[1]];
 $('rd-xem').hidden=false;$('rd-xem').innerHTML='<div class="nut-hang"><b>'+e(g.ten)+'</b><button class="tk-nut" type="button" id="rd-xem-dong">Đóng</button></div><video class="rd-video" controls autoplay src="/rustdesk/ghi-hinh/'+encodeURIComponent(g.mid)+'/'+encodeURIComponent(g.ten)+'"></video>';
 $('rd-xem-dong').onclick=function(){$('rd-xem').hidden=true;$('rd-xem').innerHTML='';};$('rd-xem').scrollIntoView({behavior:'smooth'});});
function buoc(){var b=(location.hash||'#1').slice(1); if(!/^[1-7]$/.test(b)) b='1'; if(b==='6')taiCd(); if(b==='7')taiLs();
 [].slice.call(document.querySelectorAll('[data-buoc]')).forEach(function(c){c.hidden=c.dataset.buoc!==b;});
 [].slice.call(document.querySelectorAll('#rd-tabs .dep-tab')).forEach(function(a){a.classList.toggle('on',a.dataset.b===b);});}
window.addEventListener('hashchange',buoc); buoc();
tai(); dev(); taiKn(); tong(); setInterval(function(){if(!document.hidden){tai();taiKn();tong();}},8000);})();</script>"""


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

    @app.route("/rustdesk/cho-phep-trinh-duyet.reg")
    def rustdesk_reg_trinh_duyet():
        """Chinh sach Chrome / Edge AutoLaunchProtocolsFromOrigins: trang Console nay mo rustdesk:// khong hoi lai."""
        goc = request.host_url.rstrip("/")
        if not re.fullmatch(r"https?://[A-Za-z0-9.\-]+(:\d+)?", goc):
            return Response("Địa chỉ không hợp lệ.", status=400, mimetype="text/plain; charset=utf-8")
        gt = json.dumps([{"protocol": "rustdesk", "allowed_origins": [goc]}]).replace('"', '\\"')      # goc da kiem: khong co dau \
        nd = "Windows Registry Editor Version 5.00\r\n"
        for k in ("Google\\Chrome", "Microsoft\\Edge"):
            nd += "\r\n[HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\%s]\r\n\"AutoLaunchProtocolsFromOrigins\"=\"%s\"\r\n" % (k, gt)
        return Response(("\ufeff" + nd).encode("utf-16-le"), mimetype="application/octet-stream",
                        headers={"Content-Disposition": "attachment; filename=cho-phep-mo-rustdesk.reg"})

    @app.route("/rustdesk/Cai-RustDesk-ConsoleSystem.msi")
    def rustdesk_msi():
        import os
        from flask import send_file
        if not RD.tep_kho_tt()["co"]:
            return Response("Chưa có file MSI: cài máy chủ và đặt mật khẩu chung ở bước 2.", status=409, mimetype="text/plain; charset=utf-8")
        return send_file(os.path.join(RD._DD.APPS_DIR, RD.TEN_MSI), as_attachment=True, download_name=RD.TEN_MSI, mimetype="application/x-msi")
