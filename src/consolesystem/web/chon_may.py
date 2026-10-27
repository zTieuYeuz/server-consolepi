# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Khung chon may dung chung: o tim kiem, o "Chon tat ca" (chi tac dong len may dang hien), danh sach cuon.
Dung: dat KHUNG % {"id": "x"} vao trang, nap JS mot lan, roi goi ChonMay.ve('x', [{id, ten, ip, online}]) va ChonMay.chon('x') -> [id]."""

CSS = """<style>.cm-khung{border:1px solid var(--vien);border-radius:10px;padding:10px;background:var(--the)}
.cm-dau{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:8px}.cm-dau input[type=search]{flex:1;min-width:200px;margin:0;height:38px}
.cm-ds{max-height:260px;overflow:auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:6px}
.cm-ds label{display:flex;gap:8px;align-items:center;padding:6px 8px;border-radius:8px;cursor:pointer;margin:0}.cm-ds label:hover{background:rgba(127,127,127,.12)}
.cm-ds small{display:block;color:var(--chu-mo)}.cm-tat{font-size:11px;color:var(--vang)}
.nut-hang{display:flex;gap:10px;flex-wrap:wrap;align-items:center}</style>"""

KHUNG = """<div class="cm-khung" id="cm-%(id)s"><div class="cm-dau"><input type="search" placeholder="Tìm máy theo tên hoặc IP" data-cm-tim>
<label style="margin:0;display:flex;gap:6px;align-items:center;cursor:pointer;"><input type="checkbox" data-cm-tatca> Chọn tất cả</label><span class="tk-ghi" data-cm-dem></span></div>
<div class="cm-ds" data-cm-ds><span class="tk-ghi">Đang tải danh sách máy...</span></div></div>"""

JS = """<script>window.ChonMay=window.ChonMay||(function(){var ds={},chon={};
function e(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function bo(x){return (x||'').replace(/đ/g,'d').replace(/Đ/g,'D').normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();}
function hien(id){var k=document.getElementById('cm-'+id),q=bo(k.querySelector('[data-cm-tim]').value),h='',n=0;
 ds[id].forEach(function(m){if(q&&bo(m.ten+' '+m.ip).indexOf(q)<0)return;n++;
  h+='<label><input type="checkbox" value="'+e(m.id)+'"'+(chon[id][m.id]?' checked':'')+'><span><b>'+e(m.ten)+'</b><small>'+e(m.ip)+(m.online===false?' <span class="cm-tat">(offline)</span>':'')+'</small></span></label>';});
 k.querySelector('[data-cm-ds]').innerHTML=h||'<span class="tk-ghi">'+(ds[id].length?'Không có máy nào khớp.':'Chưa có máy nào có agent.')+'</span>';
 var c=Object.keys(chon[id]).filter(function(x){return chon[id][x];}).length;k.querySelector('[data-cm-dem]').textContent='Đã chọn '+c+' / '+ds[id].length+' máy';
 var hien_ra=[].slice.call(k.querySelectorAll('[data-cm-ds] input'));k.querySelector('[data-cm-tatca]').checked=hien_ra.length>0&&hien_ra.every(function(i){return i.checked;});}
function ve(id,may){var k=document.getElementById('cm-'+id);ds[id]=may||[];chon[id]=chon[id]||{};
 if(!k.dataset.ganxong){k.dataset.ganxong='1';
  k.querySelector('[data-cm-tim]').addEventListener('input',function(){hien(id);});
  k.querySelector('[data-cm-ds]').addEventListener('change',function(ev){if(ev.target.type==='checkbox'){chon[id][ev.target.value]=ev.target.checked;hien(id);}});
  k.querySelector('[data-cm-tatca]').addEventListener('change',function(ev){[].slice.call(k.querySelectorAll('[data-cm-ds] input')).forEach(function(i){chon[id][i.value]=ev.target.checked;});hien(id);});}
 hien(id);}
return {ve:ve,chon:function(id){return Object.keys(chon[id]||{}).filter(function(x){return chon[id][x]&&ds[id].some(function(m){return m.id===x;});});}};})();</script>"""


def khung(id_):
    return KHUNG % {"id": id_}


# Thanh tab dung chung cho cac trang gop tu 2 tinh nang khac nhau (moi tab la 1 trang rieng)
TAB_REMOTE = [("vnc", "Remote VNC", "/rustdesk/vnc"), ("rustdesk", "Remote RustDesk", "/rustdesk")]
TAB_TRIEN_KHAI = [("winget", "Triển khai từ WinGet", "/uem/trien-khai"), ("phanmem", "Triển khai phần mềm", "/deployos/trienkhai")]


def thanh_tab(ds, chinh):
    return ('<div class="dep-tabs" style="margin-bottom:14px;">' + "".join(
        f'<a href="{href}" class="dep-tab{" on" if ma == chinh else ""}">{nhan}</a>' for ma, nhan, href in ds) + "</div>")
