# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Quan ly may tram - trang CAI PHAN MEM QUA AGENT: WinGet, cai tu kho, trang thai dot cai, lich su; bo chon may/group dung chung
(kich ban Agent o uem_kichban.py). Route dang ky o uem_trang_b.register_uem."""
import json
import re
import unicodedata

from flask import request

from ui import tk_dongco as DC
from ui import tk_dulieu as DL
from ui import uem_agent as UA
from ui import uem_dulieu as UD
from ui import uem_trienkhai as UT
from ui import uem_winget as UW
from ui.uem_trang import _esc, bang, chip, chuyen, gio, ten_may, trang


JS_TIEN_DO = """
<div id="tk-popup" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:60;align-items:center;justify-content:center;padding:16px;">
 <div style="background:var(--the);border:1px solid var(--vien-ro);border-radius:16px;max-width:640px;width:100%;max-height:86vh;overflow:auto;padding:20px;">
  <h3 id="tk-pt" style="margin:0 0 4px;">Đang triển khai</h3><p class="tk-ghi" id="tk-ps"></p><div id="tk-pb"></div>
  <div style="margin-top:14px;text-align:right;"><button type="button" class="tk-nut" id="tk-pd">Đóng</button></div></div></div>
<script>
(function(){
  var po=document.getElementById('tk-popup'); if(!po) return;
  var MAU={da_dat:'xanh',da_lam:'xanh',loi:'do',het_han:'do',cho_online:'vang',thu_lai:'vang'};
  function hien(id){
    po.style.display='flex'; var dung=false; document.getElementById('tk-pd').onclick=function(){po.style.display='none';dung=true;};
    (function lap(){ if(dung) return;
      fetch('/uem/trien-khai/tt/'+id).then(function(r){return r.json();}).then(function(d){
        if(!d||d.loi){return;} document.getElementById('tk-pt').textContent=d.hanh_dong+' '+d.ten_goi;
        document.getElementById('tk-ps').innerHTML=esc(d.xong+' / '+d.tong+' máy đã xong')+(d.cho?'. <b>'+d.cho+' máy đang chờ</b> (máy tắt hoặc chờ thử lại), sẽ tự chạy khi máy bật, có thể đóng cửa sổ này. Xem ở <a href="/uem/trien-khai/dot/'+id+'">Trạng thái triển khai</a>.':'');
        var h=''; Object.keys(d.may).forEach(function(k){var m=d.may[k];
          h+='<div style="padding:8px 0;border-bottom:1px solid var(--vien);"><b>'+esc(m.ten)+'</b> <span class="tk-chip '+(MAU[m.tt]||'')+'">'+esc(m.nhan||m.tt)+'</span><div class="tk-ghi">'+esc(m.tb||'')+'</div></div>';});
        document.getElementById('tk-pb').innerHTML=h;
        if(d.dang>0) setTimeout(lap,2000);
      }).catch(function(){setTimeout(lap,4000);});
    })();
  }
  function esc(s){var e=document.createElement('div');e.textContent=s==null?'':String(s);return e.innerHTML;}
  window.uemTienDo=hien; var u=new URLSearchParams(location.search).get('dot'); if(u) hien(u);
})();
</script>"""


CSS_CHON = """<style>.cg-dau{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:6px 0 10px}.cg-dau input[type=search]{flex:1;min-width:220px;max-width:420px;margin:0;height:42px}
.cg-ds{gap:8px;margin:0}.cg-ds[hidden]{display:none!important}.cg-ds label.tk-o{display:flex;flex-direction:row;align-items:flex-start;gap:10px;margin:0}.cg-ds label[hidden]{display:none!important}
.cg-ds .tk-o input{width:auto;max-width:none;flex:none;margin:3px 0 0 0}.cg-ds .tk-o b{display:block}.cg-ds .tk-o small{display:block;color:var(--chu-mo)}.cg-trang{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-top:10px}
.cg-trang button{min-height:34px;padding:4px 12px}.cg-trang button.on{border-color:var(--nhan);background:var(--nhan-mo);color:var(--nhan-dam)}</style>"""

JS_CHON = """<script>(function(){var MOI_TRANG=25,TRANG={may:0,nhom:0};
function bo(x){return (x||'').replace(/đ/g,'d').replace(/Đ/g,'D').normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();}
function $(i){return document.getElementById(i);}
function ve(loai){var k=$('cg-'+loai),q=bo($('cg-tim').value),o=[].slice.call(k.querySelectorAll('label[data-cg-tim]')),khop=o.filter(function(l){return !q||l.dataset.cgTim.indexOf(q)>=0;});
 var so=Math.max(1,Math.ceil(khop.length/MOI_TRANG));if(TRANG[loai]>=so)TRANG[loai]=so-1;var bd=TRANG[loai]*MOI_TRANG;
 o.forEach(function(l){l.hidden=true;});khop.slice(bd,bd+MOI_TRANG).forEach(function(l){l.hidden=false;});
 var h='';if(so>1){h+='<button type="button" class="tk-nut" data-t="'+(TRANG[loai]-1)+'"'+(TRANG[loai]?'':' disabled')+'>‹</button>';
  for(var i=0;i<so;i++)h+='<button type="button" class="tk-nut'+(i===TRANG[loai]?' on':'')+'" data-t="'+i+'">'+(i+1)+'</button>';
  h+='<button type="button" class="tk-nut" data-t="'+(TRANG[loai]+1)+'"'+(TRANG[loai]<so-1?'':' disabled')+'>›</button>';}
 h+='<span class="tk-ghi">'+(khop.length?(bd+1)+'-'+Math.min(bd+MOI_TRANG,khop.length)+' / '+khop.length:'0')+(loai==='may'?' máy':' group')+'</span>';
 $('cg-trang').innerHTML=h;var hien=khop.slice(bd,bd+MOI_TRANG).map(function(l){return l.querySelector('input');});
 $('cg-tatca').checked=hien.length>0&&hien.every(function(i){return i.checked;});dem();}
function loai(){return $('cg-loai').value;}
function dem(){var m=document.querySelectorAll('#cg-may input:checked').length,n=[].slice.call(document.querySelectorAll('#cg-nhom input:checked')),them={};
 n.forEach(function(i){JSON.parse(i.dataset.may||'[]').forEach(function(x){them[x]=1;});});
 [].slice.call(document.querySelectorAll('#cg-may input:checked')).forEach(function(i){them[i.value]=1;});
 $('cg-dem').textContent='Đã chọn '+m+' máy, '+n.length+' group, tổng '+Object.keys(them).length+' máy sẽ chạy';}
$('cg-loai').addEventListener('change',function(){var v=loai();$('cg-may').hidden=v!=='may';$('cg-nhom').hidden=v!=='nhom';$('cg-tim').placeholder=v==='may'?'Tìm máy theo tên hoặc IP':'Tìm group theo tên';ve(v);});
$('cg-tim').addEventListener('input',function(){TRANG[loai()]=0;ve(loai());});
$('cg-trang').addEventListener('click',function(ev){var t=ev.target.dataset.t;if(t==null||ev.target.disabled)return;TRANG[loai()]=+t;ve(loai());});
$('cg-tatca').addEventListener('change',function(ev){[].slice.call(document.querySelectorAll('#cg-'+loai()+' label:not([hidden]) input')).forEach(function(i){i.checked=ev.target.checked;});dem();});
['cg-may','cg-nhom'].forEach(function(x){$(x).addEventListener('change',function(){ve(loai());});});
ve('may');})();</script>"""


def _chon_may_nhom_html(chon_may=(), chon_nhom=()):
    """Chon may HOAC chon group (nhom may), tim kiem, 25 dong / trang. Gui len: may=<id> va nhom=<id>. chon_*: danh dau san (sua kich ban)."""
    ds = [m for m in DL.MAY.doc() if m.get("giam_sat", True) and not m.get("an") and UA.co_agent(m)]
    nhom = [g for g in DL.NHOM_MAY.doc() if g.get("may")]
    co = {m["id"] for m in ds}
    tim = lambda x: _esc(re.sub(r"[\u0300-\u036f]", "", unicodedata.normalize("NFD", x.replace("đ", "d").replace("Đ", "D"))).lower())  # noqa: E731
    o_may = "".join(f'<label class="tk-o" data-cg-tim="{tim(ten_may(m) + " " + m["ip"])}"><input type="checkbox" name="may" value="{_esc(m["id"])}"{" checked" if m["id"] in chon_may else ""}><span><b>{_esc(ten_may(m))}</b>'
                    f'<small>{_esc(m["ip"])}</small></span></label>' for m in ds)
    o_nhom = "".join(f'<label class="tk-o" data-cg-tim="{tim(g["ten"])}"><input type="checkbox" name="nhom" value="{_esc(g["id"])}"{" checked" if g["id"] in chon_nhom else ""} data-may="{_esc(json.dumps([i for i in g["may"] if i in co]))}"><span><b>{_esc(g["ten"])}</b>'
                     f'<small>{sum(1 for i in g["may"] if i in co)} máy</small></span></label>' for g in nhom)
    return (CSS_CHON + f"""<div class="cg-dau"><input type="search" id="cg-tim" placeholder="Tìm máy theo tên hoặc IP">
      <label style="margin:0;display:flex;gap:6px;align-items:center;cursor:pointer;"><input type="checkbox" id="cg-tatca" style="width:auto;margin:0;"> Chọn tất cả trang này</label></div>
      <div class="tk-luoi cg-ds" id="cg-may">{o_may or '<p class="tk-ghi">Chưa có máy nào. Máy hiện ở đây sau khi cài agent (xem Máy tính).</p>'}</div>
      <div class="tk-luoi cg-ds" id="cg-nhom" hidden>{o_nhom or '<p class="tk-ghi">Chưa có group nào. Tạo ở Triển khai phần mềm, Máy - nhóm máy, Nhóm máy.</p>'}</div>
      <div class="cg-trang" id="cg-trang"></div><p class="tk-ghi" id="cg-dem" style="margin-top:8px;"></p>""")


def may_tu_form(form):
    """Gop may tick truc tiep + may cua cac group da tick (bo trung, giu thu tu)."""
    ids = list(form.getlist("may"))
    nhom = {g["id"]: g for g in DL.NHOM_MAY.doc()}
    for gid in form.getlist("nhom"):
        ids += (nhom.get(gid) or {}).get("may", [])
    return list(dict.fromkeys(ids))


_TAB_CAI = [("winget", "Cài bằng WinGet", "/uem/trien-khai"), ("kho", "Cài từ kho phần mềm", "/uem/trien-khai/kho"),
            ("kb", "Kịch bản", "/uem/trien-khai/kich-ban"),
            ("dot", "Trạng thái triển khai", "/uem/trien-khai/dot"), ("ls", "Lịch sử", "/uem/trien-khai/lich-su")]


def _thanh_tab_cai(chinh):
    return ('<div class="dep-tabs" style="margin-bottom:14px;">' + "".join(
        f'<a href="{h}" class="dep-tab{" on" if m == chinh else ""}">{n}</a>' for m, n, h in _TAB_CAI) + "</div>")


_MAU_TT = {"da_lam": "xanh", "da_dat": "xanh", "loi": "do", "het_han": "do", "cho_online": "vang", "thu_lai": "vang", "dang_chay": "", "cho": "", "huy": ""}


def _o_thu_lai():
    return "".join(f'<option value="{i}"{" selected" if i == 2 else ""}>{"Không thử lại" if i == 0 else f"{i} lần"}</option>' for i in range(6))


def _o_het_han():
    return "".join(f'<option value="{i}"{" selected" if i == 7 else ""}>{i} ngày</option>' for i in (1, 3, 7, 14, 30))


def _o_dem(t, n, mau=""):
    return f'<span class="tk-chip {mau}" style="margin-right:6px;">{_esc(t)}: {n}</span>' if n else ""


def _dem_html(s):
    dm = s["dem"]
    return (_o_dem("Hoàn tất", dm.get("da_lam", 0) + dm.get("da_dat", 0), "xanh") + _o_dem("Đang chạy", s["dang"])
            + _o_dem("Chờ máy bật", dm.get("cho_online", 0), "vang") + _o_dem("Chờ thử lại", dm.get("thu_lai", 0), "vang")
            + _o_dem("Lỗi", dm.get("loi", 0), "do") + _o_dem("Hết hạn", dm.get("het_han", 0), "do") + _o_dem("Đã hủy", dm.get("huy", 0)))


def trang_dot():
    hang = ""
    for k, s in UT.danh_sach_dot()[:200]:
        hang += (f'<tr><td>{_esc(gio(s["bat_dau"]))}</td><td><b>{_esc(UT.TEN_HANH_DONG.get(s["hanh_dong"], s["hanh_dong"]))}</b> {_esc(s["ten_goi"])}</td>'
                 f'<td>{s["tong"]}</td><td>{_dem_html(s)}</td><td><a class="tk-nut" href="/uem/trien-khai/dot/{_esc(k)}">Chi tiết</a></td></tr>')
    body = (_thanh_tab_cai("dot") + '<div class="card"><p class="tk-ghi" style="margin-top:0;">Mỗi lần bấm Bắt đầu là một đợt. Máy đang tắt nằm ở <b>Chờ máy bật</b> '
            'và tự chạy khi agent kết nối lại, không cần làm lại. Đợt đã xong được giữ 30 ngày.</p>'
            + ('<table class=tk-bang><tr><th>Bắt đầu</th><th>Việc</th><th>Số máy</th><th>Tình trạng</th><th></th></tr>' + hang + '</table>' if hang
               else '<p class=tk-ghi>Chưa có đợt triển khai nào.</p>') + '</div>')
    return trang(body, "td")


def trang_dot_ct(dot):
    s = UT.trang_thai(dot)
    if s is None:
        return chuyen("/uem/trien-khai/dot", "Không còn đợt này.", False)
    hang = "".join(f'<tr><td><b>{_esc(x["ten"])}</b></td><td>{chip(x["nhan"], _MAU_TT.get(x["tt"], ""))}</td><td>{x.get("lan", 0)}</td>'
                   f'<td>{_esc(gio(x.get("luc")))}</td><td class="tk-ghi">{_esc(x.get("tb", ""))}</td></tr>'
                   for x in sorted(s["may"].values(), key=lambda v: (v["xong"], v["ten"])))
    nut = ""
    if s["cho"]:
        nut += (f'<form method="POST" action="/uem/trien-khai/dot/{_esc(dot)}/huy" style="display:inline;" onsubmit="return confirm(this.dataset.hoi);" '
                f'data-hoi="Hủy {s["cho"]} máy đang chờ? Các máy này sẽ không được chạy nữa."><button class="tk-nut do" type="submit">Hủy máy đang chờ</button></form> ')
    n_loi = sum(s["dem"].get(k, 0) for k in ("loi", "het_han", "huy"))
    if n_loi:
        nut += (f'<form method="POST" action="/uem/trien-khai/dot/{_esc(dot)}/chay-lai" style="display:inline;"><button class="tk-nut chinh" type="submit">'
                f'Chạy lại {n_loi} máy lỗi / hết hạn / đã hủy</button></form>')
    wol = " · có Wake-on-LAN" if s["wol"] else ""
    body = (_thanh_tab_cai("dot") + '<p><a class="tk-nut" href="/uem/trien-khai/dot">Quay lại</a></p>'
            + f'<div class="card"><h3 style="margin-top:0;">{_esc(UT.TEN_HANH_DONG.get(s["hanh_dong"], s["hanh_dong"]))} {_esc(s["ten_goi"])}</h3>'
            + f'<p class="tk-ghi">Bắt đầu {_esc(gio(s["bat_dau"]))} · chờ máy bật tới {_esc(gio(s["het_han"]))} · thử lại tối đa {s["thu_lai"]} lần{wol}</p>'
            + f'<p>{_dem_html(s)}</p><div style="margin:10px 0;">{nut}</div>'
            + f'<table class=tk-bang><tr><th>Máy</th><th>Trạng thái</th><th>Lần chạy</th><th>Cập nhật</th><th>Chi tiết</th></tr>{hang}</table></div>'
            + ('<script>setTimeout(function(){location.reload();},10000);</script>' if (s["dang"] or s["cho"]) else ""))
    return trang(body, "td")


def trang_kho():
    ds = DC.danh_sach_kho()
    hang = "".join(f'<tr><td><b>{_esc(a["ten"])}</b></td><td class="tk-ghi">{_esc(a["tham_so"] or "chưa điền tham số cài im lặng")}</td>'
                   f'<td><a class="tk-nut" href="/uem/trien-khai/goi?kho=1&id={_esc(a["ten"])}">Chọn máy</a></td></tr>' for a in ds)
    body = (_thanh_tab_cai("kho") + '<div class="card"><p class="tk-ghi" style="margin-top:0;">Cài file .exe / .msi trong <a href="/tai-nguyen">Tài nguyên máy</a> lên máy đã có agent. '
            'Console System đẩy file qua agent rồi chạy cài im lặng với tham số đã điền.</p>'
            + ('<table class=tk-bang><tr><th>Phần mềm</th><th>Tham số cài im lặng</th><th></th></tr>' + hang + '</table>' if hang else '<p class=tk-ghi>Kho chưa có phần mềm nào.</p>')
            + '</div>' + JS_TIEN_DO)
    return trang(body, "td")


def trang_trien_khai():
    q = (request.args.get("q") or "").strip()
    kq = UW.tim(q) if q else []
    co = UW.co_danh_muc()
    gui = ""
    if not co:
        gui = ('<div class="msg warn">Danh mục WinGet chưa được tải về. Bấm <b>Cập nhật danh mục</b> (cần Internet, tải khoảng 200 MB lần đầu) hoặc nhập thẳng mã gói '
               '(ví dụ <code>Google.Chrome</code>) ở ô bên dưới.</div>')
    ham = ""
    for g in kq:
        ham += (f'<tr><td><b>{_esc(g["ten"])}</b><div class="tk-ghi">{_esc(g["id"])}</div></td><td>{_esc(g["ban"])}</td>'
                f'<td><a class="tk-nut" href="/uem/trien-khai/goi?id={_esc(g["id"])}">Chọn máy</a></td></tr>')
    ket_qua = f'<div class="card">{"<table class=tk-bang><tr><th>Phần mềm</th><th>Bản mới nhất</th><th></th></tr>" + ham + "</table>" if ham else "<p class=tk-ghi>Không tìm thấy gói nào khớp.</p>"}</div>' if q else ""
    body = f"""{_thanh_tab_cai("winget")}{gui}
    <div class="card"><form method="GET" class="tk-f tk-hang"><input type="text" name="q" value="{_esc(q)}" placeholder="Tìm phần mềm trong danh mục WinGet (Chrome, 7-Zip, VLC...)" style="margin:0;height:42px;min-width:280px;flex:1;">
      <button class="tk-nut chinh" type="submit">Tìm</button>
      <span class="tk-ghi">{UW.so_goi():,} gói trong danh mục</span></form>
      <form method="POST" action="/uem/trien-khai/danh-muc" style="margin-top:10px;"><button class="tk-nut" type="submit">Cập nhật danh mục WinGet</button></form></div>
    {ket_qua}
    <h2>Nhập thẳng mã gói</h2><div class="card"><form method="GET" action="/uem/trien-khai/goi" class="tk-f tk-hang">
      <input type="text" name="id" placeholder="Mã gói, ví dụ Mozilla.Firefox" style="margin:0;height:42px;max-width:340px;" required><button class="tk-nut" type="submit">Chọn máy</button></form></div>
    <h2>Nâng cấp tất cả phần mềm trên các máy</h2><div class="card"><form method="GET" action="/uem/trien-khai/goi" class="tk-f tk-hang">
      <input type="hidden" name="id" value="*"><button class="tk-nut" type="submit">Chọn máy để nâng cấp tất cả</button></form></div>
    {JS_TIEN_DO}"""
    return trang(body, "td")


def trang_goi():
    gid = (request.args.get("id") or "").strip()
    kho = bool(request.args.get("kho"))
    if kho:
        if gid not in [a["ten"] for a in DC.danh_sach_kho()]:
            return chuyen("/uem/trien-khai/kho", "Không có phần mềm này trong kho.", False)
    elif gid != "*" and not re.fullmatch(r"[A-Za-z0-9._+-]{2,100}", gid):
        return chuyen("/uem/trien-khai", "Mã gói không hợp lệ.", False)
    g = ({"id": gid, "ten": gid, "ban": ""} if kho else UW.lay(gid) if gid != "*" else {"id": "*", "ten": "Tất cả phần mềm có bản mới", "ban": ""})
    ten = g["ten"] if g else gid
    hd = ('<option value="kho">Cài đặt từ kho</option>' if kho else '<option value="nang">Nâng cấp tất cả</option>' if gid == "*"
          else '<option value="cai">Cài đặt</option><option value="nang">Nâng cấp (nếu đã cài)</option><option value="go">Gỡ cài đặt</option>')
    body = f"""<p><a class="tk-nut" href="{"/uem/trien-khai/kho" if kho else "/uem/trien-khai"}">Quay lại</a></p>
    <div class="card"><h3>{_esc(ten)}</h3><p class="tk-ghi">{_esc(gid)}{" · bản mới nhất " + _esc(g["ban"]) if g and g.get("ban") else ""}</p>
    <form method="POST" action="/uem/trien-khai/chay" class="tk-f"><input type="hidden" name="goi_id" value="{_esc(gid)}"><input type="hidden" name="ten_goi" value="{_esc(ten)}">
      <div class="tk-hang" style="gap:14px;flex-wrap:wrap;align-items:flex-end;"><div><label>Hành động</label><select name="hanh_dong" style="max-width:260px;margin:0;">{hd}</select></div>
      <div><label for="cg-loai">Áp dụng cho</label><select id="cg-loai" style="max-width:220px;margin:0;"><option value="may">Chọn máy</option><option value="nhom">Chọn group</option></select></div></div>
      {_chon_may_nhom_html()}
      <h3 style="margin:16px 0 6px;">Chính sách triển khai</h3>
      <div class="tk-hang" style="gap:14px;flex-wrap:wrap;align-items:flex-end;">
        <div><label>Thử lại khi lỗi</label><select name="thu_lai" style="max-width:200px;margin:0;">{_o_thu_lai()}</select></div>
        <div><label>Máy đang tắt: chờ tối đa</label><select name="het_han_ngay" style="max-width:200px;margin:0;">{_o_het_han()}</select></div>
        <label style="display:flex;gap:8px;align-items:center;margin:0 0 10px;"><input type="checkbox" name="wol" value="1" style="width:auto;margin:0;"> Bật máy đang tắt bằng Wake-on-LAN</label></div>
      <p class="tk-ghi">Máy đang bật chạy ngay. Máy đang tắt hoặc mất mạng sẽ ở trạng thái <b>Chờ máy bật</b> và tự chạy khi agent kết nối lại.
        Máy lỗi được thử lại sau 5, 10, 15... phút. Máy đã đúng trạng thái sẽ được bỏ qua. Theo dõi ở tab <a href="/uem/trien-khai/dot">Trạng thái triển khai</a>.</p>
      <div style="margin-top:12px;"><button class="tk-nut chinh" type="submit">Bắt đầu</button></div></form></div>{JS_CHON}"""
    return trang(body, "td")


def trang_lich_su():
    ds = list(reversed(UD.TRIEN_KHAI.doc()))[:300]
    hang = [[gio(x["luc"]), x.get("may", ""), UT.TEN_HANH_DONG.get(x.get("hanh_dong"), x.get("hanh_dong")), x.get("ten_goi", ""),
             chip({"da_dat": "Đã đúng sẵn", "da_lam": "Hoàn tất", "loi": "Lỗi", "het_han": "Hết hạn"}.get(x.get("tt"), "Lỗi"), "do" if x.get("tt") in ("loi", "het_han") else "xanh"), x.get("tb", "")] for x in ds]
    return trang(_thanh_tab_cai("ls") + f'<div class="card">{bang(["Lúc", "Máy", "Hành động", "Phần mềm", "Kết quả", "Chi tiết"], hang, "Chưa triển khai lần nào.")}</div>', "td")
