# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Quan ly may tram - AGENT: cac duong HTTPS (mTLS) cho agent, tab Agent cua may va muc Quan tri, Agent."""
import sys as _sys
_sys.modules["ui.uem_agent_trang"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import os
import re
import shutil
import time

from flask import Response, abort, jsonify, request, send_file

from ui import uem_agent as UA
from ui import uem_agent_goi as UG
from ui import uem_pki as PKI
from ui import uem_trang as T
from ui.uem_trang import _esc, chip, chuyen, gio, may_theo_id, ten_may
from consolesystem.core import duongdan as _DD

MAX_BODY = UA.TOI_DA_BODY


def _body():
    if (request.content_length or 0) > MAX_BODY:
        abort(413)
    d = request.get_json(silent=True)
    return d if isinstance(d, dict) else {}


def _ip_nguon():
    return (request.headers.get("X-Real-IP") or request.remote_addr or "").strip()


def _agent():
    m = UA.nhan_dien(request.headers, request.remote_addr)
    if not m:
        time.sleep(0.3)
        abort(403)
    return m


def lenh_cai(m, ma):
    """Dong lenh dan vao PowerShell (Administrator) tren may Windows - ghim dung CA cua Console System, nen khong the bi gia mao."""
    url = UA.url_may(m["ip"])
    return ("$h='" + PKI.ca_sha256() + "'; Add-Type '" + UA.PIN_CS + "'; [CsPin]::On($h); "
            "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; iex (irm '" + url + "/uem/agent/cai/" + ma + ".ps1')")


def _lenh_tu_phien(m):
    from flask import session
    v = session.pop("uem_ma_cai", None)
    if not v or v.get("may_id") != m["id"]:
        return ""
    try:
        return lenh_cai(m, v["ma"])
    except Exception:
        return ""


def khung_tls():
    ok = PKI.san_sang()
    if ok:
        return (f'<div class="card"><h3>Kết nối an toàn (mTLS) của agent</h3><p>{chip("Đã bật cổng " + str(PKI.cong()), "xanh")} Agent xác thực Console System bằng CA riêng và '
                f'Console System xác thực từng agent bằng chứng chỉ riêng.</p><div style="overflow-wrap:anywhere;word-break:break-all;">{T.kv(("Dấu vân tay CA (SHA-256, dùng để ghim khi cài)", PKI.ca_sha256()), ("Chứng chỉ máy chủ (SHA-256)", PKI.server_sha256()))}</div></div>')
    return ('<div class="card"><h3>Kết nối an toàn (mTLS) của agent</h3><p>' + chip("Chưa bật", "vang") + ' Cần bật một lần để agent có thể kết nối (Console System tạo CA riêng và mở cổng '
            f'{PKI.cong()} trong nginx; có kiểm tra và tự trả lại cấu hình cũ nếu lỗi).</p><form method="POST" action="/uem/quan-tri/agent/tls"><button class="tk-nut chinh" type="submit">Bật kết nối an toàn</button></form></div>')


def tab_agent(m):
    tt, mt = UA.trang_thai(m)
    a = UA.thong_tin(m)
    nd = m.get("phien_nd") or {}
    mau = {"online": "xanh", "offline": "vang", "chua_cai": ""}[tt]
    ma = f"/uem/may/{m['id']}/agent"
    co_tk = bool(m.get("tai_khoan_id"))
    san_sang = PKI.san_sang()
    lenh = ""
    if san_sang and (lc := _lenh_tu_phien(m)):
        lenh = (f'<div class="card" style="margin-top:14px;"><h3>Lệnh cài (dùng một lần, hết hạn sau 30 phút)</h3>'
                f'<p>Mở PowerShell bằng quyền Administrator trên máy rồi dán dòng này (đã ghim chứng chỉ của Console System):</p>'
                f'<pre style="white-space:pre-wrap;word-break:break-all;user-select:all;">{_esc(lc)}</pre></div>')
    han = gio(a.get("han")) if a.get("han") else "—"
    return T.khung_may(m, "agent", f"""{"" if san_sang else '<div class="msg warn">Cổng mTLS của Console System chưa bật nên chưa cài được agent. Vào <a href="/uem/quan-tri/agent">Quản trị, Agent</a> để bật.</div>'}
      <div class="card"><h3>Agent trên máy</h3>
      <p>Trạng thái: {chip(mt, mau)}</p>
      {T.kv(("Phiên bản agent", a.get("ban") or "—"), ("Báo nhịp lần cuối", gio(a.get("luc_cuoi")) if a.get("luc_cuoi") else "—"), ("Địa chỉ nguồn", a.get("ip_nguon") or "—"),
            ("Chứng chỉ agent hết hạn", han), ("Người dùng đang đăng nhập (trợ lý phiên)", nd.get("user") or "—"), ("Cập nhật trợ lý phiên", gio(nd.get("luc")) if nd.get("luc") else "—"))}
      <div class="tk-hang" style="margin-top:14px;">
        <form method="POST" action="{ma}/cai" onsubmit="var b=this.querySelector('button');b.disabled=true;b.textContent='Đang cài, chờ khoảng 1 phút...';"><button class="tk-nut chinh" type="submit"{"" if (co_tk and san_sang) else " disabled"}>{"Cài lại / cập nhật agent qua WinRM" if tt != "chua_cai" else "Cài agent qua WinRM"}</button></form>
        <form method="POST" action="{ma}/ma"><button class="tk-nut" type="submit"{"" if san_sang else " disabled"}>Tạo lệnh cài (máy chưa bật WinRM)</button></form>
        <form method="POST" action="{ma}/chungchi" onsubmit="return confirm('Cấp chứng chỉ mới cho agent này? Chứng chỉ cũ dùng tiếp đến khi agent đổi xong.');"><button class="tk-nut" type="submit"{"" if tt == "online" else " disabled"}>Cấp lại chứng chỉ</button></form>
        <form method="POST" action="{ma}/go" onsubmit="return confirm('Gỡ agent khỏi máy này?');"><button class="tk-nut do" type="submit">Gỡ agent</button></form>
        <form method="POST" action="/uem/may/{m['id']}/xoa" onsubmit="return confirm('Xóa máy này khỏi danh sách quản lý? Agent vẫn cài trên máy; khi máy được bật và agent kết nối lại, máy sẽ tự xuất hiện lại.');"><button class="tk-nut do" type="submit">Xóa máy khỏi quản lý</button></form></div>
      {"" if co_tk else '<p class="tk-ghi">Cài qua WinRM cần gán tài khoản quản trị ở tab Quản lý.</p>'}</div>{lenh}
    <div class="card" style="margin-top:14px;"><h3>Agent làm gì</h3>
      <p>Một dịch vụ Windows (ConsoleSystemAgent, chạy SYSTEM, tự khởi động, tự chạy lại khi lỗi) kết nối mTLS tới Console System. Báo cáo, profile, WinGet, điều khiển từ xa, duyệt file... đều chạy được qua agent
      <b>mà không cần bật WinRM</b>; máy ở mạng con khác vẫn quản lý được miễn là tới được cổng {PKI.cong()}. Profile được <b>lưu về máy và tự áp dụng</b> theo chu kỳ kể cả khi Console System tắt. Thêm "trợ lý phiên"
      (chạy khi người dùng đăng nhập) để lấy máy in riêng, màn hình, tên người đang dùng.</p>
      <p class="tk-ghi">Giới hạn: chỉ trong mạng nội bộ tới được cổng {PKI.cong()} (không qua đường hầm Cloudflare/Internet); Windows 10 / Server 2016 trở lên (cần .NET Framework 4 có sẵn để biên dịch agent tại chỗ).
      Việc mang mật khẩu (tạo người dùng có mật khẩu) luôn đi bằng WinRM. Nhật ký trên máy: C:\\ProgramData\\ConsoleSystem\\log\\agent.log.</p></div>""")


def _ips_lan():
    return [i for i in PKI.ips_pi() if not i.startswith("127.")]


def khung_ket_noi():
    """Thong tin ket noi cua server (IP LAN tu cap nhat, domain + cong) va bo tao file cai MSI / script."""
    cd = PKI.cai_dat()
    ok = PKI.san_sang()
    ips = " ".join(chip(i, "xanh") for i in _ips_lan()) or '<span class="tk-ghi">Không có địa chỉ mạng</span>'
    luachon = "".join(f'<label style="white-space:nowrap;"><input type="checkbox" value="{_esc(v)}"{" checked" if i < 2 and (cd["domain"] or i == 0) else ""}> {_esc(n)}</label>' for i, (n, v) in enumerate(UG.dia_chi_chon()))
    dis = "" if ok else " disabled"
    return f"""<div class="card" id="kn" style="margin-top:14px;"><h3>Kết nối của agent</h3>
      <div class="tk-hang" style="align-items:center;gap:10px;"><b style="min-width:150px;">IP LAN của server</b><span id="kn-ips">{ips}</span>
        <span class="tk-ghi" id="kn-doi"></span></div>
      <p class="tk-ghi" style="margin:4px 0 14px;">Tự cập nhật khi server đổi IP. File đã tạo bằng IP LAN sẽ không còn đúng sau khi IP đổi; dùng domain để không phụ thuộc IP.</p>
      <form method="POST" action="/uem/quan-tri/agent/cai-dat" class="tk-f tk-hang" style="align-items:center;gap:10px;" onsubmit="return confirm('Lưu địa chỉ và cổng? Nếu đổi cổng, các agent đã cài trước đó vẫn nối cổng cũ và cần cài lại bằng file mới.');">
        <b style="min-width:150px;">Domain và cổng</b>
        <input type="text" name="domain" value="{_esc(cd["domain"])}" placeholder="Domain hoặc IP công cộng (có thể bỏ trống)" style="margin:0;height:42px;min-width:260px;max-width:340px;">
        <span>cổng</span><input type="number" name="cong" value="{cd["cong"]}" min="1024" max="65535" title="Cổng mTLS của agent (1024 đến 65535). Đổi cổng khác mặc định {PKI.CONG_TLS} để giảm bị dò quét." style="margin:0;height:42px;width:110px;">
        <button type="submit" class="tk-nut">Lưu</button>
        <span class="tk-ghi">{"Đang nghe cổng " + str(cd["cong"]) if ok else "Chưa bật cổng mTLS"}</span></form>
      <div class="tk-hang" style="align-items:center;gap:10px;margin-top:14px;" id="kn-tao"><b style="min-width:150px;">Tạo file cài</b>
        <input type="text" id="kn-ten" placeholder="Tên file (ví dụ Agent-VanPhong)" style="margin:0;height:42px;min-width:200px;max-width:240px;">
        <span id="kn-dc" style="display:inline-flex;flex-wrap:wrap;gap:4px 14px;align-items:center;max-width:430px;" title="Tick nhiều địa chỉ: agent thử theo thứ tự này, địa chỉ nào không nối được thì chuyển sang địa chỉ kế tiếp">{luachon}</span>
        <input type="text" id="kn-pk" autocomplete="off" placeholder="Passkey (để trống = không đặt)" title="Passkey bắt buộc nhập khi cài và khi gỡ agent trên máy. Chỉ lưu dấu băm, không xem lại được." style="margin:0;height:42px;min-width:200px;max-width:240px;"></div>
      <div class="tk-hang" style="align-items:center;gap:10px;margin-top:8px;"><b style="min-width:150px;"></b>
        <label style="display:flex;gap:6px;align-items:center;margin:0;font-weight:500;font-size:13px;cursor:pointer;" title="Để dùng file MSI này trong Triển khai phần mềm (cài hàng loạt qua WinRM) mà không phải gõ passkey. Passkey được mã hóa bằng khóa riêng của Console System; file MSI vẫn chỉ chứa dấu băm.">
          <input type="checkbox" id="kn-tk" checked> Cho phép Triển khai phần mềm tự điền passkey (lưu mã hóa trên máy chủ)</label></div>
      <div class="tk-hang" style="align-items:center;gap:10px;margin-top:12px;"><b style="min-width:150px;"></b>
        <button type="button" class="tk-nut chinh" id="kn-msi"{dis}>Tạo file MSI</button>
        <button type="button" class="tk-nut chinh" id="kn-ps1"{dis}>Tạo script</button>
        <button type="button" class="tk-nut chinh" id="kn-bat"{dis}>Tạo file .bat (chuột đúp là cài)</button>
        <span class="tk-ghi">File chứa địa chỉ, dấu vân tay CA và một mã ghi danh; không chứa mật khẩu hay chứng chỉ.{"" if ok else " Bật kết nối an toàn ở khung trên trước."} Tick nhiều địa chỉ để agent tự chuyển sang địa chỉ dự phòng khi địa chỉ đầu không nối được (ví dụ domain khi ở ngoài, IP LAN khi ở công ty).</span></div>
      <div id="kn-tl" style="display:none;margin-top:12px;"></div></div>{_JS_KN}"""


_JS_KN = r"""<style>
.tl{position:relative;margin:6px 0 0 8px;padding-left:26px;border-left:2px solid var(--vien,#2a3550)}
.tl .b{position:relative;padding:5px 0 9px}.tl .b:before{content:"";position:absolute;left:-35px;top:9px;width:14px;height:14px;border-radius:50%;background:#2a3550;border:2px solid #0b1020}
.tl .b.xong:before{background:#38c172}.tl .b.loi:before{background:#e3342f}.tl .b.dang:before{background:#f6ad55;animation:tlp 1s infinite}
@keyframes tlp{50%{opacity:.35}}.tl .g{opacity:.65;font-size:.88em}.tl .s{float:right;opacity:.7;font-size:.88em}
</style>
<script>
(function(){
function E(s){return String(s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function ve(v,t){var h='<div class="tl">';v.buoc.forEach(function(b){h+='<div class="b '+b.tt+'"><b>'+E(b.ten)+'</b><span class="s">'+b.giay.toFixed(2)+' giây</span><div class="g">'+E(b.ghi_chu)+'</div></div>'});
 if(v.tt==='xong')h+='<div class="b xong"><b>Hoàn tất: '+E(v.ten)+'</b></div>';if(v.tt==='loi')h+='<div class="b loi"><b>Thất bại</b><div class="g">'+E(v.loi)+'</div></div>';
 t.style.display='block';t.innerHTML='<b>Tiến trình tạo file</b>'+h+'</div>'}
function tao(loai){var f=new FormData();f.append('loai',loai);f.append('ten',document.getElementById('kn-ten').value);f.append('dia_chi',Array.prototype.map.call(document.querySelectorAll('#kn-dc input:checked'),function(x){return x.value}).join(','));
 f.append('passkey',document.getElementById('kn-pk').value);f.append('trien_khai',document.getElementById('kn-tk').checked?'1':'0');
 var t=document.getElementById('kn-tl'),nm=document.getElementById('kn-msi'),np=document.getElementById('kn-ps1'),nb=document.getElementById('kn-bat');nm.disabled=np.disabled=nb.disabled=true;
 t.style.display='block';t.innerHTML='<span class="tk-ghi">Đang bắt đầu...</span>';
 fetch('/uem/quan-tri/agent/tao',{method:'POST',body:f,credentials:'same-origin'}).then(function(r){return r.json()}).then(function(j){
  if(!j.id){t.innerHTML='<div class="msg warn">'+E(j.loi||'Lỗi')+'</div>';nm.disabled=np.disabled=nb.disabled=false;return}
  (function poll(){fetch('/uem/quan-tri/agent/tao/'+j.id+'.json',{credentials:'same-origin'}).then(function(r){return r.json()}).then(function(v){ve(v,t);
   if(v.tt==='dang'){setTimeout(poll,350)}else{nm.disabled=np.disabled=nb.disabled=false;
    fetch(location.pathname,{credentials:'same-origin'}).then(function(r){return r.text()}).then(function(h){var d=new DOMParser().parseFromString(h,'text/html'),n=d.getElementById('goi-ds'),o=document.getElementById('goi-ds');if(n&&o)o.innerHTML=n.innerHTML})}
  }).catch(function(){setTimeout(poll,1000)})})()
 }).catch(function(e){t.innerHTML='<div class="msg warn">'+E(e)+'</div>';nm.disabled=np.disabled=nb.disabled=false})}
document.getElementById('kn-msi').onclick=function(){tao('msi')};document.getElementById('kn-ps1').onclick=function(){tao('ps1')};document.getElementById('kn-bat').onclick=function(){tao('bat')};
var cu=null;function ip(){fetch('/uem/quan-tri/agent/thongtin.json',{credentials:'same-origin'}).then(function(r){return r.json()}).then(function(j){
 var k=j.ips.join(',');if(cu!==null&&k!==cu){document.getElementById('kn-doi').textContent='IP vừa thay đổi'}cu=k;
 document.getElementById('kn-ips').innerHTML=j.ips.map(function(i){return '<span class="tk-chip xanh">'+E(i)+'</span>'}).join(' ')||'<span class="tk-ghi">Không có địa chỉ mạng</span>'}).catch(function(){})}
setInterval(ip,5000);ip();
})();
</script>"""


def khung_goi():
    hang = ""
    cac_ma = {x["id"]: x for x in UA.ds_ghi_danh()}
    for g in UG.ds_goi():
        tl = "".join(f'<div class="b xong"><b>{_esc(b["ten"])}</b><span class="s">{b["giay"]:.2f} giây</span><div class="g">{_esc(b["ghi_chu"])}</div></div>' for b in g.get("buoc", []))
        ma = cac_ma.get(g.get("ma_id"))
        if ma:
            dung = f'đã cài {ma["da_dung"]} máy' + (f' / tối đa {ma["toi_da"]}' if ma["toi_da"] else "") + (", không hết hạn" if ma["het_han"] > 4e9 else f', hết hạn {gio(ma["het_han"])}')
        else:
            dung = "mã đã hết hạn"
        loai = {"msi": "MSI", "bat": "File .bat"}.get(g["loai"], "Script PowerShell")
        kho = ""
        ghi_msi = ""
        if g["loai"] == "msi":
            kho = (f'<form method="POST" action="/uem/quan-tri/agent/goi/{g["id"]}/kho" style="display:inline;"><button class="tk-nut" type="submit" '
                   f'title="Đưa vào Tài nguyên, Phần mềm để dùng trong Triển khai phần mềm / hệ điều hành">Đưa vào kho phần mềm</button></form>')
            if g.get("co_passkey"):
                if g.get("pk_ma"):
                    ghi_msi += (f'<div class="tk-hang" style="gap:8px;margin-top:6px;align-items:center;">{chip("Triển khai phần mềm: đã lưu passkey", "xanh")}'
                                f'<form method="POST" action="/uem/quan-tri/agent/goi/{g["id"]}/passkey" style="display:inline;"><input type="hidden" name="bo" value="1">'
                                f'<button class="tk-nut" type="submit">Bỏ passkey đã lưu</button></form></div>')
                else:
                    ghi_msi += (f'<form method="POST" action="/uem/quan-tri/agent/goi/{g["id"]}/passkey" class="tk-hang" style="gap:8px;margin-top:6px;align-items:center;">'
                                f'{chip("Triển khai phần mềm: chưa lưu passkey", "vang")}<input type="password" name="passkey" placeholder="Nhập passkey của gói này" autocomplete="off" '
                                f'style="margin:0;height:38px;max-width:240px;" required><button class="tk-nut" type="submit">Lưu passkey cho triển khai</button></form>')
            ghi_msi += f'<p class="tk-ghi" style="margin:6px 0 0;">Mã sản phẩm MSI (để điền vào tác vụ MSI trong Triển khai phần mềm): {UG.MSI_PRODUCT_CODE}</p>'
        hang += (f'<div class="card" style="margin-top:10px;"><div class="tk-hang" style="justify-content:space-between;gap:10px;align-items:center;">'
                 f'<div><b>{_esc(g["ten_file"])}</b> {chip(loai, "xanh")} {chip("Có passkey", "xanh") if g.get("co_passkey") else chip("Không passkey", "vang")}<div class="tk-ghi">{_esc(gio(g["tao_luc"]))} · nối về {_esc(g["url"])} · agent {_esc(g["ban_agent"])} · {g["kich_thuoc"]} byte · {_esc(dung)}</div>'
                 f'<div class="tk-ghi">SHA-256: {_esc(g["sha256"])}</div></div>'
                 f'<div class="tk-hang"><a class="tk-nut chinh" href="/uem/quan-tri/agent/goi/{g["id"]}/tai">Tải xuống</a>{kho}'
                 f'<form method="POST" action="/uem/quan-tri/agent/goi/{g["id"]}/xoa" onsubmit="return confirm(\'Xoá file này? Mã ghi danh trong file cũng bị thu hồi (máy đã cài vẫn chạy).\');" style="display:inline;">'
                 f'<button class="tk-nut do" type="submit">Xoá</button></form></div></div>'
                 f'<details style="margin-top:6px;"><summary class="tk-ghi">Dòng thời gian khi tạo</summary><div class="tl">{tl}</div></details>{ghi_msi}</div>')
    return f'<h2 style="margin-top:22px;">File cài đã tạo</h2><div id="goi-ds">{hang or "<p class=tk-ghi>Chưa tạo file nào.</p>"}</div>'


def khung_internet():
    cong = PKI.cong()
    return (f"""<div class="card" style="margin-top:14px;"><h3>Máy ở ngoài Internet kết nối bằng gì?</h3>
      <p>Agent nối <b>ra</b> Console System bằng <b>HTTPS có xác thực hai chiều (mTLS) qua cổng {cong}</b>; Console System không cần nối vào máy trạm nên máy sau NAT hay tường lửa vẫn quản lý được.
      Agent chỉ tin CA riêng của Console System và Console System chỉ nhận agent có chứng chỉ đã cấp. Cần một trong hai cách để máy bên ngoài tới được cổng {cong}:</p>
      <ul><li><b>Chuyển cổng</b> TCP {cong} trên router về Console System, kèm tên miền hoặc DDNS, rồi điền domain ở trên.</li>
      <li><b>VPN</b> (WireGuard, Tailscale...): dùng IP trong VPN, không phải mở cổng ra Internet.</li></ul>
      <p class="tk-ghi">Không dùng được Cloudflare Tunnel hoặc proxy HTTP đứng giữa (chúng cắt TLS nên chứng chỉ máy trạm không tới được Console System). Địa chỉ nối về ghi cố định lúc cài.</p></div>""")


def khung_sac():
    return ("""<div class="card" style="margin-top:14px;"><h3>Máy Windows 11 báo Smart App Control chặn agent</h3>
      <p>Smart App Control (SAC) chỉ cho chạy file <b>đã ký số</b> bởi CA nằm trong danh sách tin cậy của Microsoft hoặc file Microsoft đánh giá là an toàn. <code>cs-agent.exe</code> hiện chưa ký số nên máy đang bật SAC sẽ chặn
      (MSI báo lỗi 1721 hoặc 1603). Không có cách thêm riêng một file vào danh sách cho phép của SAC. Có ba hướng:</p>
      <ul><li><b>Ký số agent (đúng nhất, lâu dài):</b> dùng chứng chỉ ký mã (OV/EV) của một CA thuộc chương trình Microsoft Trusted Root, hoặc dịch vụ Microsoft Artifact Signing (tên cũ Trusted Signing) nếu tổ chức đủ điều kiện đăng ký. Ký cả <code>cs-agent.exe</code> lẫn file MSI. Console System chưa có chứng chỉ nên bước này chưa làm được.</li>
      <li><b>Tắt SAC trên máy đích:</b> Cài đặt, Quyền riêng tư và bảo mật, Bảo mật Windows, Kiểm soát ứng dụng và trình duyệt, Smart App Control, chọn Tắt. Hoặc chạy bằng quyền quản trị rồi khởi động lại máy:
        <br><code>reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\CI\\Policy" /v VerifiedAndReputablePolicyState /t REG_DWORD /d 0 /f</code>
        <br>Xem trạng thái: <code>reg query "HKLM\\SYSTEM\\CurrentControlSet\\Control\\CI\\Policy" /v VerifiedAndReputablePolicyState</code> (0 = tắt, 1 = bật, 2 = đang đánh giá).
        Bản Windows 11 cũ tắt xong không bật lại được nếu không cài lại; từ bản cập nhật tháng 4/2026 (KB5083769) bật lại được.</li>
      <li><b>Máy do tổ chức quản lý:</b> SAC tự tắt khi máy có chính sách App Control for Business (WDAC) hoặc Intune; thêm chứng chỉ ký hoặc mã băm của agent vào chính sách đó.</li></ul>
      <p class="tk-ghi">Máy Windows 10, Windows Server và máy đã nâng cấp từ bản cũ thường không bật SAC nên cài bình thường.</p></div>""")


def trang_admin():
    ds = UA.danh_sach_trang_thai()
    hang = ""
    for m, tt, mt in ds:
        a = UA.thong_tin(m)
        mau = {"online": "xanh", "offline": "vang", "chua_cai": ""}[tt]
        hang += (f'<tr><td><a href="/uem/may/{m["id"]}/agent"><b>{_esc(ten_may(m))}</b></a><div class="tk-ghi">{_esc(m["ip"])}</div></td><td>{chip(mt, mau)}</td>'
                 f'<td>{_esc(a.get("ban") or "—")}</td><td>{_esc(gio(a.get("luc_cuoi")) if a.get("luc_cuoi") else "—")}</td></tr>')
    return (khung_tls() + khung_ket_noi() + khung_goi() + f'<div class="card" style="margin-top:14px;">{("<table class=tk-bang><tr><th>Máy</th><th>Agent</th><th>Phiên bản</th><th>Nhịp cuối</th></tr>" + hang + "</table>") if hang else "<p class=tk-ghi>Chưa có máy nào.</p>"}'
            f'<p class="tk-ghi">Phiên bản agent hiện hành: {UA.PHIEN_BAN}. Agent cũ tự cập nhật khi báo nhịp.</p></div>' + khung_huong_dan())


def khung_huong_dan():
    """Gom cac huong dan (ket noi qua Internet, Smart App Control) vao 1 khung thu gon o cuoi trang."""
    bo = lambda h: h.replace('<div class="card" style="margin-top:14px;">', '<div style="margin-top:12px;">').replace("<h3>", "<h4>").replace("</h3>", "</h4>")
    return ('<details class="card" style="margin-top:14px;"><summary style="cursor:pointer;"><b>Hướng dẫn</b> '
            '<span class="tk-ghi">máy ngoài Internet kết nối thế nào · Smart App Control chặn agent</span></summary>'
            + bo(khung_internet()) + bo(khung_sac()) + '</details>')


def register_agent(app):
    @app.route("/uem/agent/ping")
    def uem_ag_ping():
        m = _agent()                                   # can chung chi may hop le: dung de agent tu chan doan mTLS
        return jsonify({"ok": 1, "may": m["id"], "gio": int(time.time()), "ban": UA.PHIEN_BAN})

    @app.route("/uem/agent/nhip", methods=["POST"])
    def uem_ag_nhip():
        m = _agent()
        return jsonify(UA.xu_ly_nhip(m, _body(), _ip_nguon()))

    @app.route("/uem/agent/ketqua", methods=["POST"])
    def uem_ag_kq():
        m = _agent()
        return jsonify({"ok": UA.nhan_ket_qua(m, _body())})

    @app.route("/uem/agent/tep/<jid>", methods=["GET", "PUT"])
    def uem_ag_tep(jid):
        m = _agent()
        j = UA.viec_tep(jid, m)
        if not j:
            abort(404)
        if request.method == "GET" and j["kieu"] == "tep_xuong":
            return send_file(j["nguon_local"], as_attachment=True, download_name="tep")
        if request.method == "PUT" and j["kieu"] == "tep_len":
            dich = j["dich_local"]
            os.makedirs(os.path.dirname(dich) or ".", exist_ok=True)
            tam, n = dich + ".dang-tai", 0
            with open(tam, "wb") as f:
                while True:
                    b = request.stream.read(262144)
                    if not b:
                        break
                    n += len(b)
                    if n > UA.TOI_DA_TEP:
                        f.close()
                        os.remove(tam)
                        abort(413)
                    f.write(b)
            os.replace(tam, dich)
            return jsonify({"ok": True, "bytes": n})
        abort(405)

    @app.route("/uem/agent/cai/<ma>.ps1")
    def uem_ag_cai(ma):
        # Script cai chua KHOA RIENG cua agent: chi phuc vu qua cong mTLS 8443 (TLS), tuyet doi khong qua cong 80
        if not re.fullmatch(r"[A-Za-z0-9_-]{20,64}", ma) or not UA.qua_tls_nginx(request.headers, request.remote_addr):
            abort(404)
        s = UA.doi_ma_cai(ma, _ip_nguon(), request.args.get("h", ""))
        if not s:
            time.sleep(0.5)
            abort(404)
        return Response(s, mimetype="text/plain; charset=utf-8", headers={"Cache-Control": "no-store"})

    @app.route("/uem/quan-tri/agent/tls", methods=["POST"])
    def uem_ag_tls():
        ok, tb = PKI.bat_tls()
        return chuyen("/uem/quan-tri/agent", tb, ok)

    @app.route("/uem/quan-tri/agent/cai-dat", methods=["POST"])
    def uem_ag_cai_dat():
        dm = re.sub(r"^https?://", "", (request.form.get("domain") or "").strip()).rstrip("/")
        if dm and not re.fullmatch(r"[0-9A-Za-z.\-]{1,253}", dm):
            return chuyen("/uem/quan-tri/agent", "Domain không hợp lệ (chỉ chữ, số, dấu chấm, gạch ngang; không kèm cổng).", False)
        try:
            cong = int(request.form.get("cong") or PKI.cong())
        except ValueError:
            return chuyen("/uem/quan-tri/agent", "Cổng không hợp lệ.", False)
        ok, tb = PKI.doi_cong(cong, dm)
        return chuyen("/uem/quan-tri/agent", tb, ok)

    @app.route("/uem/quan-tri/agent/thongtin.json")
    def uem_ag_thongtin():
        return jsonify({"ips": _ips_lan(), "cong": PKI.cong(), "domain": PKI.cai_dat()["domain"]})

    @app.route("/uem/quan-tri/agent/tao", methods=["POST"])
    def uem_ag_tao():
        try:
            vid = UG.bat_dau(request.form.get("loai", ""), request.form.get("ten", ""), request.form.get("dia_chi", ""), request.form.get("ngay", "0"), request.form.get("toi_da", "0"), request.form.get("passkey", ""), request.form.get("trien_khai") == "1")
        except (ValueError, TypeError) as e:
            return jsonify({"loi": str(e) or "Dữ liệu không hợp lệ."}), 400
        return jsonify({"id": vid})

    @app.route("/uem/quan-tri/agent/tao/<vid>.json")
    def uem_ag_tao_tt(vid):
        v = UG.viec(vid) if re.fullmatch(r"[0-9a-f]{12}", vid) else None
        if not v:
            abort(404)
        return jsonify(v)

    @app.route("/uem/quan-tri/agent/goi/<gid>/tai")
    def uem_ag_goi_tai(gid):
        p, ten = UG.duong_file(gid) if re.fullmatch(r"[0-9a-f]{10}", gid) else (None, None)
        if not p:
            abort(404)
        return send_file(p, as_attachment=True, download_name=ten, mimetype="application/x-msi" if p.endswith(".msi") else "text/plain; charset=utf-8")

    @app.route("/uem/quan-tri/agent/goi/<gid>/xoa", methods=["POST"])
    def uem_ag_goi_xoa(gid):
        ok = bool(re.fullmatch(r"[0-9a-f]{10}", gid)) and UG.xoa_goi(gid)
        return chuyen("/uem/quan-tri/agent", "Đã xoá file và thu hồi mã ghi danh của nó." if ok else "Không tìm thấy file.", ok)

    @app.route("/uem/quan-tri/agent/goi/<gid>/kho", methods=["POST"])
    def uem_ag_goi_kho(gid):
        p, ten = UG.duong_file(gid) if re.fullmatch(r"[0-9a-f]{10}", gid) else (None, None)
        if not p or not ten.endswith(".msi"):
            return chuyen("/uem/quan-tri/agent", "Không tìm thấy file MSI.", False)
        os.makedirs(_DD.APPS_DIR, exist_ok=True)
        shutil.copyfile(p, os.path.join(_DD.APPS_DIR, ten))
        from consolesystem.integrations.tk_dongco import dien_tham_so_app_neu_trong
        dien_tham_so_app_neu_trong(ten, "/qn /norestart", f"msiexec /x {UG.MSI_PRODUCT_CODE} /qn /norestart")
        return chuyen("/uem/quan-tri/agent", f"Đã đưa {ten} vào kho phần mềm (Tài nguyên, Phần mềm). Khi triển khai, Console System tự điền passkey nếu đã lưu cho gói này. Mã sản phẩm: {UG.MSI_PRODUCT_CODE}")

    @app.route("/uem/quan-tri/agent/goi/<gid>/passkey", methods=["POST"])
    def uem_ag_goi_passkey(gid):
        if not re.fullmatch(r"[0-9a-f]{10}", gid) or not UG.tim_goi(gid):
            return chuyen("/uem/quan-tri/agent", "Không tìm thấy file.", False)
        if request.form.get("bo") == "1":
            UG.bo_passkey_trien_khai(gid)
            return chuyen("/uem/quan-tri/agent", "Đã bỏ passkey đã lưu. Triển khai phần mềm sẽ không cài được gói này cho đến khi lưu lại.")
        ok, tb = UG.luu_passkey_trien_khai(gid, request.form.get("passkey", ""))
        return chuyen("/uem/quan-tri/agent", tb, ok)

    @app.route("/uem/may/<mid>/agent/cai", methods=["POST"])
    def uem_ag_cai_winrm(mid):
        may_theo_id(mid)
        ok, tb = UA.cai_qua_winrm(mid)
        return chuyen(f"/uem/may/{mid}/agent", tb, ok)

    @app.route("/uem/may/<mid>/agent/ma", methods=["POST"])
    def uem_ag_ma(mid):
        from flask import session
        may_theo_id(mid)
        if not PKI.san_sang():
            return chuyen(f"/uem/may/{mid}/agent", "Chưa bật cổng mTLS (Quản trị, Agent).", False)
        session["uem_ma_cai"] = {"may_id": mid, "ma": UA.tao_ma_cai(mid)}
        return chuyen(f"/uem/may/{mid}/agent", "Đã tạo lệnh cài dùng một lần (hết hạn sau 30 phút).")

    @app.route("/uem/may/<mid>/agent/chungchi", methods=["POST"])
    def uem_ag_chungchi(mid):
        m = may_theo_id(mid)
        if not UA.con_song(m):
            return chuyen(f"/uem/may/{mid}/agent", "Agent đang không kết nối, chưa cấp lại được.", False)
        j = UA.cap_lai_chung_chi(mid)
        try:
            out, err = UA.cho_viec(j, 60)
        except RuntimeError as e:
            return chuyen(f"/uem/may/{mid}/agent", str(e), False)
        return chuyen(f"/uem/may/{mid}/agent", "Agent đã nhận chứng chỉ mới và đang khởi động lại." if not err else "Agent từ chối: " + err, not err)

    @app.route("/uem/may/<mid>/agent/go", methods=["POST"])
    def uem_ag_go(mid):
        may_theo_id(mid)
        ok, tb = UA.go_agent(mid)
        return chuyen(f"/uem/may/{mid}/agent", tb, ok)
