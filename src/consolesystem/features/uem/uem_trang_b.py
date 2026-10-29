# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Quan ly may tram (UEM) - GIAO DIEN PHAN 2: Phan mem, Bao mat, Trien khai (WinGet), Profiles, Bao cao, Quan tri, Chua ho tro,
cac tab con lai cua tung may (duyet file, ho tro tu xa, nguon dien, trien khai, tac vu) va TOAN BO route /uem/*.
"""
import sys as _sys
_sys.modules["ui.uem_trang_b"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import csv
import io
import os
import json
import re
import unicodedata
import tempfile
import time

from flask import Response, abort, jsonify, redirect, request, send_file

from ui import duongdan as _DD
from ui import tk_dongco as DC
from ui import tk_dulieu as DL
from ui import uem_baocao as UBC
from ui import uem_buoc as UB
from ui import uem_dulieu as UD
from ui import uem_profiles as UP
from ui import uem_trang as T
from ui import uem_ketnoi as UK
from ui import uem_trienkhai as UT
from consolesystem.features.uem import uem_kichban as UKB
from ui import uem_agent_trang as UAT
from ui import uem_agent as UA
from consolesystem.features.uem import uem_dieukhien as UDK
from consolesystem.features.uem import uem_sualoi as USL
from consolesystem.features.uem import uem_rustdesk as URD
from consolesystem.features.uem import uem_vnc_trang as UVT
from ui import uem_pki as PKI
from ui import uem_vnc as UV
from ui import uem_winget as UW
from ui.uem_trang import _esc, bc, bang, chip, chuyen, co_khong, gio, iso_gio, kv, may_theo_id, ten_may, the_html, trang
from consolesystem.core import magic_packet as _MP

CON_QT = [("may", "Máy được giám sát"), ("agent", "Agent"), ("the", "Thẻ"), ("dia-diem", "Địa điểm"), ("metadata", "Thông tin thêm"), ("cai-dat", "Cài đặt chung"), ("nhat-ky", "Nhật ký tác vụ")]
CON_BM = [("", "Tổng hợp"), ("cap-nhat", "Cập nhật Windows")]


# ----------------------------------------------------------------- phan mem toan he thong
def _phan_mem_tong():
    pm = {}
    for m in DL.MAY.doc():
        for a in bc(m).get("applications", []):
            e = pm.setdefault(a["name"], {"nsx": a.get("publisher", ""), "ban": {}, "may": set()})
            e["ban"][a.get("version", "")] = e["ban"].get(a.get("version", ""), 0) + 1
            e["may"].add(m["id"])
    return pm


def trang_phan_mem():
    pm = _phan_mem_tong()
    ten_chon = request.args.get("ten", "")
    if ten_chon and ten_chon in pm:
        e = pm[ten_chon]
        ds_may = [m for m in DL.MAY.doc() if m["id"] in e["may"]]
        hang = []
        for m in ds_may:
            a = next((x for x in bc(m).get("applications", []) if x["name"] == ten_chon), {})
            hang.append([f'<a href="/uem/may/{m["id"]}/phan-mem">{_esc(ten_may(m))}</a>', m["ip"], a.get("version", ""), a.get("install_date") or "—"])
        return trang(f'<p><a class="tk-nut" href="/uem/phan-mem">Tất cả phần mềm</a></p><div class="card"><h3>{_esc(ten_chon)}</h3>'
                     f'<p class="tk-ghi">Nhà sản xuất: {_esc(e["nsx"]) or "—"} · cài trên {len(ds_may)} máy</p>{bang(["Máy", "IP", "Phiên bản", "Ngày cài"], hang)}</div>', "pm")
    hang = "".join(f'<tr data-t="{_esc((k + " " + v["nsx"]).lower())}"><td><a href="/uem/phan-mem?ten={_esc(__import__("urllib.parse").parse.quote(k))}">{_esc(k)}</a></td>'
                   f'<td>{_esc(v["nsx"]) or "—"}</td><td>{len(v["ban"])}</td><td><b>{len(v["may"])}</b></td></tr>' for k, v in sorted(pm.items(), key=lambda kv: (-len(kv[1]["may"]), kv[0].lower())))
    if not pm:
        return trang('<div class="card"><p>Chưa có dữ liệu phần mềm. Gán tài khoản cho máy rồi bấm Lấy thông tin ở <a href="/uem/may">Máy tính</a>.</p></div>', "pm")
    return trang(f'<div class="card uem-ds" data-trang="20"><div class="uem-loc"><input type="text" class="uem-tim" placeholder="Tìm phần mềm hoặc nhà sản xuất">'
                 f'<span class="tk-ghi"><b class="uem-dem"></b> phần mềm khác nhau</span><a class="tk-nut" href="/uem/bao-cao/phan-mem.csv">Tải CSV</a></div>'
                 f'<div class="uem-bang-cuon"><table class="tk-bang"><thead><tr><th>Phần mềm</th><th>Nhà sản xuất</th><th>Số phiên bản</th><th>Số máy</th></tr></thead><tbody>{hang}</tbody></table></div></div>', "pm")


# ----------------------------------------------------------------- bao mat
def trang_bao_mat(muc=""):
    ds = [m for m in DL.MAY.doc() if m.get("giam_sat", True) and bc(m)]
    con = '<div class="uem-con">' + "".join(f'<a href="/uem/bao-mat{("/" + k) if k else ""}" class="{"on" if k == muc else ""}">{n}</a>' for k, n in CON_BM) + "</div>"
    if not ds:
        return trang(con + '<div class="card"><p>Chưa có báo cáo của máy nào.</p></div>', "bm")
    hang = ""
    for m in ds:
        r = bc(m)
        if muc == "cap-nhat":
            su = r.get("systemupdate") or {}
            cho = len(r.get("pending_updates", []))
            hang += (f'<tr data-t="{_esc((ten_may(m) + " " + m["ip"]).lower())}"><td><a href="/uem/may/{m["id"]}/cap-nhat">{_esc(ten_may(m))}</a></td><td>{_esc(UBC.ten_cap_nhat_tu_dong(su.get("status")))}</td>'
                     f'<td>{iso_gio(su.get("last_search"))}</td><td>{iso_gio(su.get("last_install"))}</td><td>{chip(str(cho) + " bản chờ", "vang") if cho else chip("Đã cập nhật", "xanh")}</td></tr>')
        else:
            av, fw = r.get("antivirus") or {}, r.get("firewall") or []
            c = next((d for d in r.get("logicaldisks", []) if d.get("label") == "C:"), {})
            hang += (f'<tr data-t="{_esc((ten_may(m) + " " + m["ip"] + " " + av.get("name", "")).lower())}"><td><a href="/uem/may/{m["id"]}">{_esc(ten_may(m))}</a></td>'
                     f'<td>{chip(av.get("name") or "Không có", "xanh" if av.get("is_active") else "do")}</td><td>{co_khong(av.get("is_updated"), "Mới", "Cũ")}</td>'
                     f'<td>{" ".join(chip(x["ten"], "xanh" if x["bat"] else "do") for x in fw) or "—"}</td>'
                     f'<td>{chip(c.get("bitlocker_status", "—"), "xanh" if c.get("bitlocker_status") == "Encrypted" else "vang")}</td>'
                     f'<td>{co_khong(str(r.get("smb1", "")).lower() != "enabled", "Tắt", "BẬT")}</td></tr>')
    cot = (["Máy", "Tự động cập nhật", "Tìm lần cuối", "Cài lần cuối", "Chờ cài"] if muc == "cap-nhat"
           else ["Máy", "Diệt virus", "CSDL", "Tường lửa (đang bật)", "BitLocker ổ C", "SMB1"])
    return trang(con + f'<div class="card uem-ds" data-trang="20"><div class="uem-loc"><input type="text" class="uem-tim" placeholder="Tìm máy"><span class="tk-ghi"><b class="uem-dem"></b> máy</span></div>'
                 f'<div class="uem-bang-cuon"><table class="tk-bang"><thead><tr>{"".join(f"<th>{c}</th>" for c in cot)}</tr></thead><tbody>{hang}</tbody></table></div></div>', "bm")


# ----------------------------------------------------------------- trien khai winget
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


# ----------------------------------------------------------------- profiles
def _o_nhap(f, gt=None):
    ten, nhan, kieu, bb, mac_dinh, ghi = f
    gt = mac_dinh if gt is None else gt
    h = f"<label>{_esc(nhan)}{' *' if bb else ''}</label>"
    if kieu == "checkbox":
        return f'<label class="tk-o"><input type="checkbox" name="{ten}" value="1"{" checked" if gt else ""}><span>{_esc(nhan)}</span></label>'
    if kieu == "textarea":
        h += f'<textarea name="{ten}" rows="7" style="width:100%;max-width:none;font-family:var(--mono);">{_esc(gt)}</textarea>'
    elif kieu.startswith("select:"):
        h += f'<select name="{ten}" style="max-width:320px;">' + "".join(f'<option value="{_esc(o)}"{" selected" if o == gt else ""}>{_esc(o) or "(không)"}</option>' for o in kieu[7:].split("|")) + "</select>"
    else:
        h += f'<input type="{"password" if kieu == "password" else "text"}" name="{ten}" value="{"" if kieu == "password" else _esc(gt)}"{" autocomplete=new-password" if kieu == "password" else ""}>'
    if ghi:
        h += f'<div class="tk-ghi">{_esc(ghi)}</div>'
    return h


GIAI_THICH_PROFILE = """<div class="card"><h3>Profile là gì?</h3>
<p><b>Profile là một "bộ cài đặt chuẩn" áp dụng cho nhiều máy cùng lúc.</b> Bạn khai báo <i>máy phải như thế nào</i> (ví dụ: có Chrome và 7-Zip, có tài khoản "ketoan", tắt Remote Desktop), Console System tự kiểm tra từng máy và chỉ làm phần chưa đúng. Cứ vài phút kiểm tra lại, máy nào bị đổi/hỏng sẽ được đưa về đúng, máy mới thêm vào cũng được cấu hình theo.</p>
<ol class="tk-ghi" style="margin:8px 0 0 18px;line-height:1.7;"><li><b>Tạo profile</b> và đặt tên, ví dụ "Máy văn phòng chuẩn".</li><li><b>Chọn áp dụng cho máy nào</b>: tất cả, một nhóm máy, hoặc máy có một thẻ.</li><li><b>Thêm các việc cần làm</b> (tác vụ): cài phần mềm, sửa registry, tạo người dùng, chạy PowerShell...</li><li><b>Bật profile</b>. Xem kết quả từng máy ở cuối trang, máy lỗi sẽ hiện trong mục Vấn đề.</li></ol>
<p class="tk-ghi">Khác với <b>Triển khai</b>: Triển khai chạy một lần cho các máy bạn chọn; Profile là cấu hình <b>duy trì liên tục</b>. Bấm "Áp dụng ngay" nếu không muốn chờ chu kỳ kiểm tra.</p></div>"""


def trang_profiles():
    ds = UD.PROFILES.doc()
    the_ds = UD.THE.doc()
    hang = ""
    for p in ds:
        may = UP.may_ap_dung(p)
        loi = len({m["id"] for m, _t, _tb in UP.van_de(p["id"])})
        ds_nhom = [g["ten"] + " (nhóm)" for g in DL.NHOM_MAY.doc() if g["id"] in p.get("nhom_may", [])]
        pham_vi = "Tất cả máy" if p.get("ap_dung_tat_ca") else (", ".join(ds_nhom + [t["ten"] for t in the_ds if t["id"] in p.get("the", [])]) or "Chưa chọn nhóm máy hoặc thẻ")
        hang += (f'<tr><td><a href="/uem/profiles/{p["id"]}"><b>{_esc(p["ten"])}</b></a><div class="tk-ghi">{_esc(p.get("mo_ta", ""))}</div></td><td>{_esc(pham_vi)}</td><td>{len(may)}</td>'
                 f'<td>{len(p.get("tasks", []))}</td><td>{chip("Bật", "xanh") if p.get("bat") else chip("Tắt")}</td><td>{chip(str(loi) + " máy lỗi", "do") if loi else chip("Không lỗi", "xanh")}</td></tr>')
    body = GIAI_THICH_PROFILE + f"""<h2>Các profile hiện có</h2><div class="card">{('<table class="tk-bang"><tr><th>Profile</th><th>Áp dụng cho</th><th>Số máy</th><th>Tác vụ</th><th>Trạng thái</th><th>Vấn đề</th></tr>' + hang + '</table>') if ds else '<p class="tk-ghi">Chưa có profile nào.</p>'}</div>
    <h2>Tạo profile mới</h2><div class="card"><form method="POST" action="/uem/profiles/tao" class="tk-f"><label>Tên profile</label><input type="text" name="ten" required placeholder="Ví dụ: Máy văn phòng chuẩn">
      <label>Mô tả</label><input type="text" name="mo_ta"><div style="margin-top:12px;"><button class="tk-nut chinh" type="submit">Tạo</button></div></form></div>
    <p class="tk-ghi">Profile là danh sách tác vụ khai báo trạng thái mong muốn (cài/gỡ phần mềm WinGet, registry, người dùng và nhóm cục bộ, MSI, PowerShell). Console System tự kiểm tra từng máy
      và chỉ làm những gì chưa đúng, lặp lại mỗi {int(UD.cai_dat().get("tan_suat_profile", 30))} phút.</p>"""
    return trang(body, "pf")


def trang_profile(pid):
    p = DL.tim(UD.PROFILES.doc(), pid)
    if not p:
        abort(404)
    the_ds = UD.THE.doc()
    tt = UD.TRANG_THAI_PROFILE.doc().get(pid, {})
    may = UP.may_ap_dung(p)
    o_nhom = "".join(f'<label class="tk-o"><input type="checkbox" name="nhom_may" value="{g["id"]}"{" checked" if g["id"] in p.get("nhom_may", []) else ""}><span><b>{_esc(g["ten"])}</b><small>{len(g.get("may", []))} máy</small></span></label>' for g in DL.NHOM_MAY.doc())
    o_the = "".join(f'<label class="tk-o"><input type="checkbox" name="the" value="{t["id"]}"{" checked" if t["id"] in p.get("the", []) else ""}><span><b>{_esc(t["ten"])}</b></span></label>' for t in the_ds)
    # tac vu
    ht = ""
    n = len(p.get("tasks", []))
    for i, t in enumerate(p.get("tasks", [])):
        n_ok = sum(1 for m in may if tt.get(m["id"], {}).get("tasks", {}).get(t["id"], {}).get("tt") in ("da_dat", "da_lam", "da_chay_truoc"))
        n_loi = sum(1 for m in may if tt.get(m["id"], {}).get("tasks", {}).get(t["id"], {}).get("tt") == "loi")
        ht += (f'<tr><td>{i + 1}</td><td>{_esc(UB.mo_ta(t["loai"], t["tham_so"]))}<div class="tk-ghi">{"Agent tự áp dụng · " if UP.tu_tri(t) else "Cần Console System (WinRM hoặc agent đang kết nối) · "}{"Bỏ qua lỗi, chạy tiếp · " if t.get("bo_qua_loi") else ""}{"" if t.get("bat", True) else "Đang tắt · "}đúng {n_ok}/{len(may)} máy{" · lỗi " + str(n_loi) if n_loi else ""}</div></td>'
               f'<td style="white-space:nowrap;"><form method="POST" action="/uem/profiles/{pid}/task/{t["id"]}/hanh-dong" style="display:inline;">'
               f'<button class="tk-nut" name="viec" value="len"{" disabled" if i == 0 else ""}>↑</button> <button class="tk-nut" name="viec" value="xuong"{" disabled" if i == n - 1 else ""}>↓</button> '
               f'<button class="tk-nut" name="viec" value="bat_tat">{"Tắt" if t.get("bat", True) else "Bật"}</button> <a class="tk-nut" href="/uem/profiles/{pid}?sua={t["id"]}#form-task">Sửa</a> '
               f'<button class="tk-nut do" name="viec" value="xoa" onclick="return confirm(\'Xóa tác vụ này?\');">Xóa</button></form></td></tr>')
    # form them/sua task
    sua = next((t for t in p.get("tasks", []) if t["id"] == request.args.get("sua")), None)
    loai = (sua or {}).get("loai") or request.args.get("loai", "")
    chon = '<option value="">(chọn loại tác vụ)</option>'
    nhom_cu = None
    for k, (ten, nhom, _f) in CAC_LOAI_SX().items():
        if nhom != nhom_cu:
            chon += ("</optgroup>" if nhom_cu else "") + f'<optgroup label="{_esc(UB.NHOM_LOAI[nhom])}">'
            nhom_cu = nhom
        chon += f'<option value="{k}"{" selected" if k == loai else ""}>{_esc(ten)}</option>'
    chon += "</optgroup>"
    form_task = ""
    if loai in UB.CAC_LOAI:
        gt = (sua or {}).get("tham_so", {})
        cac_o = "".join(_o_nhap(f, gt.get(f[0]) if sua else None) for f in UB.CAC_LOAI[loai][2])
        form_task = (f'<form method="POST" action="/uem/profiles/{pid}/task/luu" class="tk-f" style="margin-top:14px;"><input type="hidden" name="loai_tac_vu" value="{loai}"><input type="hidden" name="task_id" value="{(sua or {}).get("id", "")}">'
                     f'{cac_o}<label class="tk-o"><input type="checkbox" name="bo_qua_loi" value="1"{" checked" if (sua or {}).get("bo_qua_loi") else ""}><span>Nếu tác vụ lỗi, vẫn chạy các tác vụ sau</span></label>'
                     f'{"<p class=tk-ghi>Để trống ô mật khẩu = giữ mật khẩu cũ.</p>" if sua and loai == "user_them" else ""}'
                     f'<div style="margin-top:12px;"><button class="tk-nut chinh" type="submit">{"Lưu thay đổi" if sua else "Thêm tác vụ"}</button></div></form>')
    # bang may
    hm = ""
    for m in may:
        st = tt.get(m["id"], {})
        hm += (f'<tr><td><a href="/uem/may/{m["id"]}">{_esc(ten_may(m))}</a></td><td>{chip({"ok": "Đúng cấu hình", "loi": "Có lỗi", "offline": "Không kết nối", "dang": "Đang chạy"}.get(st.get("trang_thai"), "Chưa chạy"), {"ok": "xanh", "loi": "do", "offline": "vang"}.get(st.get("trang_thai"), ""))}</td>'
               f'<td>{_esc(gio(st.get("luc")) if st.get("luc") else "—")}</td><td>{_esc(st.get("tom_tat", ""))}</td></tr>')
    van = UP.van_de(pid)
    hv = "".join(f'<tr><td><a href="/uem/may/{m["id"]}">{_esc(ten_may(m))}</a></td><td>{_esc(tk)}</td><td>{_esc(tb)}</td></tr>' for m, tk, tb in van)
    body = f"""<p><a class="tk-nut" href="/uem/profiles">Danh sách profile</a></p>
    <p class="tk-ghi">Làm lần lượt 3 bước: <b>1</b> đặt tên và bật, <b>2</b> chọn áp dụng cho máy nào, <b>3</b> thêm các việc cần làm. Kết quả từng máy ở cuối trang.</p>
    <div class="card"><h3>Bước 1 và 2: Tên, trạng thái và phạm vi áp dụng</h3><form method="POST" action="/uem/profiles/{pid}/luu" class="tk-f"><label>Tên</label><input type="text" name="ten" value="{_esc(p["ten"])}" required>
      <label>Mô tả</label><input type="text" name="mo_ta" value="{_esc(p.get("mo_ta", ""))}">
      <label class="tk-o"><input type="checkbox" name="ap_dung_tat_ca" value="1"{" checked" if p.get("ap_dung_tat_ca") else ""}><span><b>Áp dụng cho tất cả máy</b><small>Bỏ chọn để chỉ áp dụng cho nhóm máy hoặc máy có thẻ bên dưới</small></span></label>
      <label>Bước 2: áp dụng cho nhóm máy nào</label><div class="tk-luoi">{o_nhom or '<span class="tk-ghi">Chưa có nhóm máy, tạo ở Máy tính (chọn máy, Thêm vào nhóm).</span>'}</div>
      <label>Hoặc áp dụng cho máy có thẻ</label><div class="tk-luoi">{o_the or '<span class="tk-ghi">Chưa có thẻ, tạo ở Quản trị, Thẻ.</span>'}</div>
      <label class="tk-o"><input type="checkbox" name="bat" value="1"{" checked" if p.get("bat") else ""}><span><b>Bật profile</b><small>Tắt = tạm dừng, không áp dụng nữa</small></span></label>
      <div class="tk-hang" style="margin-top:12px;"><button class="tk-nut chinh" type="submit">Lưu</button></div></form>
      <div class="tk-hang" style="margin-top:10px;"><form method="POST" action="/uem/profiles/{pid}/ap-dung"><button class="tk-nut xanh" type="submit">Áp dụng ngay lên {len(may)} máy</button></form>
      <form method="POST" action="/uem/profiles/{pid}/xoa" onsubmit="return confirm('Xóa profile này? Máy giữ nguyên cấu hình đã áp dụng.');"><button class="tk-nut do" type="submit">Xóa profile</button></form></div></div>
    <h2>Bước 3: Việc cần làm trên máy - tác vụ ({n})</h2><p class="tk-ghi">Các tác vụ chạy lần lượt từ trên xuống. Mỗi tác vụ khai báo trạng thái mong muốn; máy đã đúng thì tự bỏ qua.</p><div class="card">{('<table class="tk-bang"><tr><th>#</th><th>Tác vụ</th><th></th></tr>' + ht + '</table>') if ht else '<p class="tk-ghi">Chưa có tác vụ nào.</p>'}
      <h3 id="form-task" style="margin-top:18px;">{"Sửa tác vụ" if sua else "Thêm tác vụ"}</h3>
      <form method="GET" class="tk-f tk-hang"><select name="loai" style="margin:0;height:42px;max-width:420px;" onchange="this.form.submit()">{chon}</select>{f'<input type="hidden" name="sua" value="{_esc(sua["id"])}">' if sua else ""}<noscript><button class="tk-nut">Chọn</button></noscript></form>{form_task}</div>
    <h2>Kết quả trên từng máy ({len(may)})</h2><div class="card">{('<table class="tk-bang"><tr><th>Máy</th><th>Trạng thái</th><th>Lần cuối</th><th>Tóm tắt</th></tr>' + hm + '</table>') if hm else '<p class="tk-ghi">Chưa có máy nào thuộc phạm vi áp dụng (chọn nhóm máy hoặc gán thẻ cho máy).</p>'}</div>
    <h2>Vấn đề ({len(van)})</h2><div class="card">{('<table class="tk-bang"><tr><th>Máy</th><th>Tác vụ</th><th>Lỗi</th></tr>' + hv + '</table>') if hv else '<p class="tk-ghi">Không có vấn đề nào.</p>'}</div>"""
    return trang(body, "pf")


def CAC_LOAI_SX():
    return dict(sorted(UB.CAC_LOAI.items(), key=lambda kv: list(UB.NHOM_LOAI).index(kv[1][1])))


# ----------------------------------------------------------------- bao cao
def _csv(ten, cot, hang):
    s = io.StringIO()
    w = csv.writer(s)
    w.writerow(cot)
    w.writerows(hang)
    return Response("﻿" + s.getvalue(), mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{ten}"'})


BAO_CAO = {
    "may": ("Danh sách máy", "may.csv"), "phan-mem": ("Phần mềm trên tất cả máy", "phan-mem.csv"), "o-dia": ("Ổ đĩa và BitLocker", "o-dia.csv"),
    "bao-mat": ("Bảo mật", "bao-mat.csv"), "cap-nhat": ("Cập nhật Windows đang chờ", "cap-nhat.csv"), "may-in": ("Máy in", "may-in.csv"), "mang": ("Card mạng", "mang.csv")}


def csv_bao_cao(loai):
    ds = [m for m in DL.MAY.doc() if bc(m)]
    if loai == "may":
        return _csv("may.csv", ["Tên", "IP", "MAC", "Hệ điều hành", "Phiên bản", "Hãng", "Model", "Serial", "CPU", "RAM", "Người dùng", "Báo cáo lúc"],
                    [[ten_may(m), m["ip"], bc(m).get("mac", ""), (bc(m).get("operatingsystem") or {}).get("description", ""), (bc(m).get("operatingsystem") or {}).get("version", ""),
                      (bc(m).get("computer") or {}).get("manufacturer", ""), (bc(m).get("computer") or {}).get("model", ""), (bc(m).get("computer") or {}).get("serial", ""),
                      (bc(m).get("computer") or {}).get("processor", ""), (bc(m).get("computer") or {}).get("memory", ""), (bc(m).get("operatingsystem") or {}).get("username", ""), gio(m.get("bao_cao_luc"))] for m in ds])
    if loai == "phan-mem":
        return _csv("phan-mem.csv", ["Máy", "IP", "Phần mềm", "Phiên bản", "Nhà sản xuất", "Ngày cài"],
                    [[ten_may(m), m["ip"], a["name"], a.get("version", ""), a.get("publisher", ""), a.get("install_date", "")] for m in ds for a in bc(m).get("applications", [])])
    if loai == "o-dia":
        return _csv("o-dia.csv", ["Máy", "Ổ", "Hệ tập tin", "Dung lượng", "Còn trống", "Mức dùng %", "BitLocker"],
                    [[ten_may(m), d["label"], d["filesystem"], d["size_in_units"], d["remaining_space_in_units"], d["usage"], d["bitlocker_status"]] for m in ds for d in bc(m).get("logicaldisks", [])])
    if loai == "bao-mat":
        return _csv("bao-mat.csv", ["Máy", "Diệt virus", "Đang bật", "CSDL mới", "Tường lửa tắt", "SMB1", "Tự động cập nhật"],
                    [[ten_may(m), (bc(m).get("antivirus") or {}).get("name", ""), (bc(m).get("antivirus") or {}).get("is_active", ""), (bc(m).get("antivirus") or {}).get("is_updated", ""),
                      ", ".join(x["ten"] for x in bc(m).get("firewall", []) if not x["bat"]), bc(m).get("smb1", ""), UBC.ten_cap_nhat_tu_dong((bc(m).get("systemupdate") or {}).get("status"))] for m in ds])
    if loai == "cap-nhat":
        return _csv("cap-nhat.csv", ["Máy", "Tiêu đề", "KB"], [[ten_may(m), u["title"], u.get("kb", "")] for m in ds for u in bc(m).get("pending_updates", [])])
    if loai == "may-in":
        return _csv("may-in.csv", ["Máy", "Máy in", "Cổng", "Mặc định", "Mạng", "Chia sẻ"], [[ten_may(m), p["name"], p["port"], p["is_default"], p["is_network"], p["is_shared"]] for m in ds for p in bc(m).get("printers", [])])
    if loai == "mang":
        return _csv("mang.csv", ["Máy", "Card", "MAC", "IP", "Cổng mặc định", "DNS", "DHCP"], [[ten_may(m), n["name"], n["mac_address"], n["addresses"], n["default_gateway"], n["dns_servers"], n["dhcp_enabled"]] for m in ds for n in bc(m).get("networkadapters", [])])
    abort(404)


def trang_bao_cao():
    h = "".join(f'<tr><td><b>{n}</b></td><td><a class="tk-nut" href="/uem/bao-cao/{f}">Tải CSV</a></td></tr>' for k, (n, f) in BAO_CAO.items())
    return trang(f'<div class="card"><table class="tk-bang"><tr><th>Báo cáo</th><th></th></tr>{h}</table><p class="tk-ghi">Tệp CSV mở được bằng Excel (có dấu tiếng Việt). Số liệu lấy từ báo cáo gần nhất của từng máy.</p></div>', "bc")


# ----------------------------------------------------------------- quan tri
def trang_quan_tri(muc):
    con = '<div class="uem-con">' + "".join(f'<a href="/uem/quan-tri/{k}" class="{"on" if k == muc else ""}">{n}</a>' for k, n in CON_QT) + "</div>"
    if muc == "may":
        tk = DL.tai_khoan_cong_khai()
        opt = "".join(f'<option value="{t["id"]}">{_esc(t["ten"])} ({_esc(t["user"])})</option>' for t in tk)
        hang = ""
        for m in DL.MAY.doc():
            nhan, mau = T.trang_thai_may(m)
            hang += (f'<tr><td><a href="/uem/may/{m["id"]}"><b>{_esc(ten_may(m))}</b></a><div class="tk-ghi">{_esc(m["ip"])}</div></td><td><span class="uem-dot {mau}"></span>{_esc(nhan)}</td>'
                     f'<td>{_esc(next((t["ten"] for t in tk if t["id"] == m.get("tai_khoan_id")), "—"))}</td><td>{_esc(gio(m.get("bao_cao_luc")))}</td>'
                     f'<td style="white-space:nowrap;"><form method="POST" action="/uem/may/{m["id"]}/bao-cao-ngay" style="display:inline;"><button class="tk-nut">Lấy thông tin</button></form> '
                     f'<form method="POST" action="/uem/may/{m["id"]}/quan-ly" style="display:inline;"><input type="hidden" name="chi" value="giam_sat"><input type="hidden" name="giam_sat" value="{"" if m.get("giam_sat", True) else "1"}">'
                     f'<button class="tk-nut">{"Vô hiệu" if m.get("giam_sat", True) else "Bật lại"}</button></form></td></tr>')
        return trang(con + f'<div class="card">{("<table class=tk-bang><tr><th>Máy</th><th>Trạng thái</th><th>Tài khoản</th><th>Báo cáo lúc</th><th></th></tr>" + hang + "</table>") if hang else "<p class=tk-ghi>Chưa có máy nào.</p>"}'
                     f'<p class="tk-ghi">Danh sách máy dùng chung với <a href="/deployos/trienkhai/may">Triển khai phần mềm, Máy</a> và <a href="/deployos/trienkhai/may/quet">Quét mạng</a>. Máy chưa gán tài khoản quản trị thì chưa lấy được báo cáo: gán ở tab Quản lý của máy hoặc chọn nhiều máy ở trang Máy tính.</p></div>', "qt")
    if muc in ("the", "dia-diem", "metadata"):
        kho, ten = {"the": (UD.THE, "Thẻ"), "dia-diem": (UD.DIA_DIEM, "Địa điểm"), "metadata": (UD.METADATA, "Trường thông tin thêm")}[muc]
        ds = kho.doc()
        hang = ""
        for x in ds:
            dung = (sum(1 for m in DL.MAY.doc() if x["id"] in m.get("the", [])) if muc == "the" else
                    sum(1 for m in DL.MAY.doc() if m.get("dia_diem") == x["id"]) if muc == "dia-diem" else sum(1 for m in DL.MAY.doc() if (m.get("metadata") or {}).get(x["id"])))
            mau = f'<span class="uem-tag" style="background:{_esc(x.get("mau") or "#6366f1")}">{_esc(x["ten"])}</span>' if muc == "the" else f'<b>{_esc(x["ten"])}</b>'
            hang += (f'<tr><td>{mau}</td><td>{_esc(x.get("mo_ta", ""))}</td><td>{dung} máy</td><td style="white-space:nowrap;"><a class="tk-nut" href="/uem/quan-tri/{muc}?sua={x["id"]}">Sửa</a> '
                     f'<form method="POST" action="/uem/quan-tri/{muc}/xoa" style="display:inline;" onsubmit="return confirm(\'Xóa mục này?\');"><input type="hidden" name="id" value="{x["id"]}"><button class="tk-nut do">Xóa</button></form></td></tr>')
        sua = DL.tim(ds, request.args.get("sua", ""))
        mau_o = f'<label>Màu</label><input type="color" name="mau" value="{_esc((sua or {}).get("mau") or "#6366f1")}" style="height:42px;width:90px;padding:2px;">' if muc == "the" else ""
        return trang(con + f'<div class="card">{("<table class=tk-bang><tr><th>Tên</th><th>Mô tả</th><th>Đang dùng</th><th></th></tr>" + hang + "</table>") if hang else "<p class=tk-ghi>Chưa có mục nào.</p>"}</div>'
                     f'<h2>{"Sửa" if sua else "Thêm"} {ten.lower()}</h2><div class="card"><form method="POST" action="/uem/quan-tri/{muc}/luu" class="tk-f"><input type="hidden" name="id" value="{(sua or {}).get("id", "")}">'
                     f'<label>Tên</label><input type="text" name="ten" value="{_esc((sua or {}).get("ten", ""))}" required maxlength="60"><label>Mô tả</label><input type="text" name="mo_ta" value="{_esc((sua or {}).get("mo_ta", ""))}" maxlength="200">{mau_o}'
                     f'<div style="margin-top:12px;"><button class="tk-nut chinh" type="submit">Lưu</button></div></form></div>', "qt")
    if muc == "agent":
        return trang(con + UAT.trang_admin(), "qt")
    if muc == "cai-dat":
        cd = UD.cai_dat()
        return trang(con + f'''<div class="card"><form method="POST" action="/uem/quan-tri/cai-dat" class="tk-f">
          <label class="tk-o"><input type="checkbox" name="tu_dong_giam_sat" value="1"{" checked" if cd.get("tu_dong_giam_sat", True) else ""}><span><b>Tự động lấy báo cáo định kỳ</b><small>Tắt = chỉ lấy khi bấm Lấy thông tin</small></span></label>
          <label>Chu kỳ lấy báo cáo (phút, từ 5 đến 1440)</label><input type="text" name="tan_suat_bao_cao" value="{int(cd.get("tan_suat_bao_cao", 60))}" style="max-width:140px;">
          <label>Chu kỳ áp dụng profile (phút, từ 5 đến 1440)</label><input type="text" name="tan_suat_profile" value="{int(cd.get("tan_suat_profile", 30))}" style="max-width:140px;">
          <div style="margin-top:12px;"><button class="tk-nut chinh" type="submit">Lưu</button></div></form></div>
          <div class="card" style="margin-top:14px;"><h3>Danh mục WinGet</h3><p class="tk-ghi">{UW.so_goi():,} gói. Tự cập nhật mỗi 24 giờ khi có Internet.</p>
          <form method="POST" action="/uem/trien-khai/danh-muc"><button class="tk-nut">Cập nhật ngay</button></form></div>''', "qt")
    if muc == "nhat-ky":
        tong = []
        ten = {m["id"]: ten_may(m) for m in DL.MAY.doc()}
        for mid, ds in UD.BAO_CAO_TAC_VU.doc().items():
            for x in ds:
                tong.append((x["luc"], ten.get(mid, "(máy đã xóa)"), x))
        tong.sort(key=lambda t: -t[0])
        hang = [[gio(l), t, {"profile": "Profile", "trien_khai": "Triển khai", "tu_xa": "Điều khiển"}.get(x["nguon"], x["nguon"]), x["ten"], chip("Thành công" if x["ok"] else "Lỗi", "xanh" if x["ok"] else "do"), x["tb"]] for l, t, x in tong[:300]]
        return trang(con + f'<div class="card">{bang(["Lúc", "Máy", "Nguồn", "Tác vụ", "Kết quả", "Chi tiết"], hang, "Chưa có tác vụ nào.")}</div>', "qt")
    abort(404)


# ----------------------------------------------------------------- tab con lai cua may
def _ket_noi_may(m, bat_buoc_winrm=False):
    """(client, mat_khau) - qua agent neu dang song, khong thi WinRM. Loi -> UK.LoiMay (thong diep tieng Viet)."""
    c, mk, _loai = UK.ket_noi(m, bat_buoc_winrm=bat_buoc_winrm)
    return c, mk


def _duong_hop_le(p):
    return bool(p) and len(p) <= 400 and not re.search(r"[\x00-\x1f<>\"|?*]", p.replace("\\\\", "\\"))


def liet_ke_thu_muc(m, duong):
    c, mk = _ket_noi_may(m)
    if not duong:
        # Chi o co phuong tien (Size co gia tri): o DVD/USB rong khong co dia thi Windows van liet ke nhung bam vao se loi "khong ton tai"
        ps = ("$r = @(Get-CimInstance Win32_LogicalDisk | Where-Object { $_.Size } | ForEach-Object { [pscustomobject]@{Name=($_.DeviceID + '\\');Length=0;Dir=$true;Time=''} }); "
              "if ($r.Count -eq 0) { '[]' } else { ConvertTo-Json -InputObject $r -Compress }")
    else:
        ps = (f"$ErrorActionPreference='Stop'; $r = @(Get-ChildItem -LiteralPath {DC._q(duong)} -Force | Select-Object -First 1000 | ForEach-Object "
              "{ [pscustomobject]@{Name=$_.Name;Length=[int64]($(if($_.PSIsContainer){0}else{$_.Length}));Dir=[bool]$_.PSIsContainer;Time=$_.LastWriteTime.ToString('s')} }); "
              "if ($r.Count -eq 0) { '[]' } else { ConvertTo-Json -InputObject $r -Compress }")
    out, err = DC._chay_ps(c, ps)
    import json
    if err or not out.strip():
        raise RuntimeError(DC._loi_dep(err or "Không đọc được thư mục.", mk))
    d = json.loads(out)
    return [d] if isinstance(d, dict) else d


def _dung_luong(n):
    for d in ("B", "KB", "MB", "GB"):
        if n < 1024 or d == "GB":
            return f"{n:.0f} {d}" if d == "B" else f"{n:.1f} {d}"
        n /= 1024


def tab_duyet_file(m):
    duong = (request.args.get("p") or "").strip()
    if duong and not _duong_hop_le(duong):
        return T.khung_may(m, "duyet-file", '<div class="msg err">Đường dẫn không hợp lệ.</div>')
    if not UK.co_the_ket_noi(m):
        return T.khung_may(m, "duyet-file", T._chua_bao_cao(m))
    try:
        ds = liet_ke_thu_muc(m, duong)
    except Exception as e:
        return T.khung_may(m, "duyet-file", f'<div class="msg err">{_esc(DC._loi_dep(e))}</div>')
    import urllib.parse as up
    base = f"/uem/may/{m['id']}/duyet-file"
    lenh = ""
    if duong:
        cha = duong.rstrip("\\")
        cha = cha[:cha.rfind("\\")] if "\\" in cha else ""
        if len(cha) == 2 and cha[1] == ":":
            cha += "\\"
        lenh = f'<a class="tk-nut" href="{base}?p={up.quote(cha)}">Lên một cấp</a>'
    hang = ""
    for x in sorted(ds, key=lambda x: (not x["Dir"], x["Name"].lower())):
        day = (duong.rstrip("\\") + "\\" + x["Name"]) if duong else x["Name"]
        if x["Dir"]:
            ten = f'<a href="{base}?p={_esc(up.quote(day))}"><b>{_esc(x["Name"])}</b></a>'
            thao = (f'<form method="POST" action="{base}/xoa" style="display:inline;" onsubmit="return confirm(\'Xóa thư mục này và mọi thứ bên trong?\');">'
                    f'<input type="hidden" name="p" value="{_esc(day)}"><input type="hidden" name="cha" value="{_esc(duong)}"><button class="tk-nut do">Xóa</button></form>') if duong else ""
        else:
            ten = _esc(x["Name"])
            thao = (f'<a class="tk-nut" href="{base}/tai?p={_esc(up.quote(day))}">Tải về</a> '
                    f'<form method="POST" action="{base}/xoa" style="display:inline;" onsubmit="return confirm(\'Xóa file này?\');"><input type="hidden" name="p" value="{_esc(day)}"><input type="hidden" name="cha" value="{_esc(duong)}"><button class="tk-nut do">Xóa</button></form>')
        hang += f'<tr data-t="{_esc(x["Name"].lower())}"><td>{"📁" if x["Dir"] else "📄"} {ten}</td><td>{"" if x["Dir"] else _dung_luong(x["Length"])}</td><td>{_esc((x.get("Time") or "").replace("T", " "))}</td><td style="white-space:nowrap;">{thao}</td></tr>'
    tren = (f'<div class="card"><form method="POST" action="{base}/tao-thu-muc" class="tk-f tk-hang" style="margin-bottom:10px;"><input type="hidden" name="cha" value="{_esc(duong)}">'
            f'<input type="text" name="ten" placeholder="Tên thư mục mới" style="margin:0;height:40px;max-width:240px;" required><button class="tk-nut">Tạo thư mục</button></form>'
            f'<form method="POST" action="{base}/tai-len" enctype="multipart/form-data" class="tk-f tk-hang"><input type="hidden" name="cha" value="{_esc(duong)}">'
            f'<input type="file" name="tep" required style="margin:0;"><button class="tk-nut">Tải file lên (tối đa 200 MB)</button></form></div>') if duong else ""
    body = (f'<div class="uem-duong"><a href="{base}">Máy này</a>' + (f' <span>›</span> <b>{_esc(duong)}</b>' if duong else "") + f' {lenh}</div>{tren}'
            f'<div class="card uem-ds" data-trang="50"><div class="uem-loc"><input type="text" class="uem-tim" placeholder="Lọc trong thư mục này"><span class="tk-ghi"><b class="uem-dem"></b> mục</span></div>'
            f'<div class="uem-bang-cuon"><table class="tk-bang"><thead><tr><th>Tên</th><th>Dung lượng</th><th>Sửa lúc</th><th></th></tr></thead><tbody>{hang}</tbody></table></div></div>')
    return T.khung_may(m, "duyet-file", body)


def nginx_vnc_san_sang():
    """True neu nginx da co duong /uem-vnc-ws/ (hoac khong the kiem tra, vd may phat trien)."""
    try:
        with open("/etc/nginx/sites-available/console-pi.conf", encoding="utf-8") as f:
            return "uem-vnc-ws" in f.read()
    except OSError:
        return True


def tab_tu_xa(m):
    user, _ = DL.lay_tai_khoan(m.get("tai_khoan_id"))
    v = m.get("vnc") or {}
    ma = f"/uem/may/{m['id']}/tu-xa"
    canh = ("" if nginx_vnc_san_sang() else
            '<div class="msg warn">Chưa cấu hình nginx cho điều khiển từ xa. Chạy trong Terminal: <code>sudo bash /opt/console-pi/tools/cai-vnc.sh</code> rồi tải lại trang.</div>')
    trang_thai = (chip("Đã cài TightVNC " + _esc(v.get("ban", "")), "xanh") if v.get("da_cai") else chip("Chưa cài" if "da_cai" in v else "Chưa kiểm tra", "vang"))
    nut_tat = ("onsubmit=\"var b=this.querySelector('button');b.disabled=true;b.textContent='Đang xử lý, chờ khoảng 1 phút...';\"")
    return T.khung_may(m, "tu-xa", URD.khoi_tu_xa(m) + f'''{canh}<div class="card"><h3>Điều khiển màn hình ngay trong trình duyệt (VNC)</h3>
      <p>Thấy và điều khiển đúng màn hình đang hiện trên máy, kể cả màn hình đăng nhập. Mỗi phiên dùng mã PIN ngẫu nhiên, đóng tab là tự tắt. <b>Máy có agent</b>: kết nối đi ngược qua mTLS, TightVNC chỉ nghe 127.0.0.1 (không mở cổng ra mạng). <b>Máy chỉ có WinRM</b>: Console System kết nối thẳng tới cổng 5900, chỉ cho đúng IP Console System.</p>
      <p>Trạng thái: {trang_thai}</p>
      <p class="tk-ghi">Cài / kiểm tra / gỡ TightVNC: vào <a href="/rustdesk/vnc">Phần mềm remote, Remote VNC</a> (chọn được nhiều máy một lần).</p>
      <form method="POST" action="{ma}/vnc/mo" class="tk-f" style="margin-top:14px;" {nut_tat}>
        <label class="tk-o"><input type="checkbox" name="bao" value="1" checked><span><b>Hiện thông báo cho người đang dùng máy</b><small>Cửa sổ nhỏ trên màn hình máy đó trước khi kết nối</small></span></label>
        <label class="tk-o"><input type="checkbox" name="phep" value="1"><span><b>Xin phép người đang ngồi trước máy</b><small>Hiện hộp Có/Không trên màn hình máy đó (chỉ khi máy có agent); họ từ chối hoặc 40 giây không trả lời thì không kết nối</small></span></label>
        <div style="margin-top:10px;"><button class="tk-nut chinh" type="submit">Mở màn hình</button></div></form>
      <p class="tk-ghi">Cần cài TightVNC một lần ở trang <a href="/rustdesk/vnc">Remote VNC</a>: dịch vụ thủ công, luôn tắt khi không có phiên.</p></div>
      <div class="card" style="margin-top:14px;"><h3>Remote Desktop (RDP)</h3>
      <p>Tải tệp .rdp rồi mở bằng Remote Desktop Connection. Tệp không chứa mật khẩu. Máy đích cần bật Remote Desktop.</p>
      <p class="tk-ghi">Địa chỉ: {_esc(m["ip"])}{" · tài khoản " + _esc(user) if user else ""}</p>
      <a class="tk-nut" href="{ma}/rdp">Tải tệp RDP</a></div>
      <div class="card" style="margin-top:14px;"><h3>Chạy lệnh PowerShell</h3>
      <form method="POST" action="/uem/may/{m["id"]}/lenh" class="tk-f"><label>Lệnh chạy trên máy</label>
        <textarea name="lenh" rows="4" style="width:100%;max-width:none;font-family:var(--mono);" required placeholder="Get-Service | Where-Object Status -eq Running | Select-Object -First 5"></textarea>
        <div style="margin-top:10px;"><button class="tk-nut chinh" type="submit">Chạy lệnh</button></div></form>
      {('<pre style="white-space:pre-wrap;margin-top:14px;max-height:420px;overflow:auto;">' + _esc(KET_QUA_LENH.pop(m["id"], "")) + "</pre>") if m["id"] in KET_QUA_LENH else ""}</div>''')


KET_QUA_LENH = {}


def _loi_shutdown(out, err, mk):
    if "no shutdown was in progress" in out:
        return "Không có lệnh tắt/khởi động lại nào đang chờ để hủy."
    dong = re.sub(r"^shutdown\.exe\s*:\s*", "", out.split("At line:")[0].strip())
    return dong[:200] or DC._loi_dep(err, mk)


def tab_nguon(m):
    return T.khung_may(m, "nguon", f'''<div class="uem-2"><div class="card"><h3>Bật máy (Wake-on-LAN)</h3>
      <p class="tk-ghi">MAC: {_esc(m.get("mac") or "chưa có, nhập ở tab Quản lý")}. Máy phải bật Wake-on-LAN trong BIOS và cùng mạng LAN với Console System.</p>
      <form method="POST" action="/uem/may/{m["id"]}/nguon"><input type="hidden" name="viec" value="bat"><button class="tk-nut xanh" type="submit">Gửi gói đánh thức</button></form></div>
      <div class="card"><h3>Tắt / khởi động lại</h3><form method="POST" action="/uem/may/{m["id"]}/nguon" class="tk-f"><label>Hành động</label>
        <select name="viec" style="max-width:260px;"><option value="khoi_dong_lai">Khởi động lại</option><option value="tat">Tắt máy</option><option value="ngu_dong">Ngủ đông</option><option value="huy">Hủy lệnh tắt/khởi động lại đang chờ</option></select>
        <label>Sau bao nhiêu giây (0 đến 86400)</label><input type="text" name="sau" value="30" style="max-width:140px;">
        <label>Thông báo hiện trên màn hình máy đó</label><input type="text" name="tin" value="Quản trị viên yêu cầu khởi động lại/tắt máy." maxlength="200">
        <div style="margin-top:12px;"><button class="tk-nut do" type="submit" onclick="return confirm('Chắc chắn thực hiện trên máy này?');">Thực hiện</button></div></form></div></div>''')


def tab_trien_khai_may(m):
    ls = [x for x in reversed(UD.TRIEN_KHAI.doc()) if x.get("may_id") == m["id"]][:50]
    hang = [[gio(x["luc"]), UT.TEN_HANH_DONG.get(x.get("hanh_dong"), ""), x.get("ten_goi", ""), chip({"da_dat": "Đã đúng sẵn", "da_lam": "Hoàn tất"}.get(x.get("tt"), "Lỗi"), "do" if x.get("tt") == "loi" else "xanh"), x.get("tb", "")] for x in ls]
    return T.khung_may(m, "trien-khai", f'''<div class="card"><h3>Cài / gỡ phần mềm WinGet trên máy này</h3>
      <form method="GET" action="/uem/trien-khai" class="tk-f tk-hang"><input type="text" name="q" placeholder="Tìm phần mềm" style="margin:0;height:42px;max-width:300px;" required><button class="tk-nut chinh">Tìm trong danh mục</button></form>
      <p class="tk-ghi">Chọn gói rồi tick máy này ở bước chọn máy.</p></div><h2>Lịch sử triển khai của máy</h2><div class="card">{bang(["Lúc", "Hành động", "Phần mềm", "Kết quả", "Chi tiết"], hang, "Chưa có.")}</div>''')


def tab_tac_vu(m):
    ls = list(reversed(UD.BAO_CAO_TAC_VU.doc().get(m["id"], [])))[:100]
    hang = [[gio(x["luc"]), {"profile": "Profile", "trien_khai": "Triển khai", "tu_xa": "Điều khiển"}.get(x["nguon"], x["nguon"]), x["ten"], chip("Thành công" if x["ok"] else "Lỗi", "xanh" if x["ok"] else "do"), x["tb"]] for x in ls]
    return T.khung_may(m, "tac-vu", f'<p class="tk-ghi">Cài/gỡ phần mềm: dùng trang <a href="/uem/trien-khai">Triển khai phần mềm, Triển khai từ WinGet</a> rồi tick máy này; lịch sử cài của máy nằm ở bảng dưới (nguồn "Triển khai").</p><div class="card">{bang(["Lúc", "Nguồn", "Tác vụ", "Kết quả", "Chi tiết"], hang, "Chưa có tác vụ nào chạy trên máy này.")}</div>')


def tab_may_b(m, tab):
    return {"duyet-file": tab_duyet_file, "tu-xa": tab_tu_xa, "nguon": tab_nguon, "trien-khai": tab_trien_khai_may, "tac-vu": tab_tac_vu}[tab](m)


# ----------------------------------------------------------------- dang ky route
def _ips_tu_chuoi(s):
    """'192.168.1.5, 192.168.1.10-20' -> list ip (toi da 256)."""
    import ipaddress
    ra = []
    for p in re.split(r"[\s,;]+", s.strip()):
        if not p:
            continue
        try:
            m = re.fullmatch(r"(\d+\.\d+\.\d+\.)(\d+)-(\d+)", p)
            if m:
                a, b = int(m.group(2)), int(m.group(3))
                if a > b or b > 255:
                    return None
                ra += [m.group(1) + str(i) for i in range(a, b + 1)]
            else:
                ra.append(str(ipaddress.ip_address(p)))
        except ValueError:
            return None
    return ra[:256]


NOVNC_DIR = _DD.DIR_NOVNC


def trang_vnc(m, tok, pin):
    import json as _j
    ten = ten_may(m)
    cau_hinh = _j.dumps({"tok": tok, "pin": pin, "mid": m["id"]})
    html = ("""<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Điều khiển từ xa</title><style>
html,body{margin:0;height:100%;background:#0b0e14;color:#e3e8ef;font-family:system-ui,sans-serif}
body{display:flex;flex-direction:column;height:100dvh}
.bar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:8px 12px;background:#111826;border-bottom:1px solid #223049}
.bar b{font-size:15px}.bar .tt{color:#9aa8bd;font-size:13px}.sp{flex:1}
button,.nut{height:38px;padding:0 14px;border-radius:8px;border:1px solid #2f4a63;background:transparent;color:#e3e8ef;cursor:pointer;font:600 13.5px system-ui;display:inline-flex;align-items:center;text-decoration:none}
button:hover,.nut:hover{background:#18253a}button.do{border-color:#a33;color:#ff8a8a}
#man{flex:1;min-height:0;background:#000}
.loi{padding:12px 16px;background:#3a1b1b;color:#ffb4b4;display:none}
</style></head><body>
<div class="bar"><b>""" + _esc(ten) + """</b><span class="tt" id="tt">Đang kết nối...</span><span class="sp"></span>
<button id="cad" type="button">Ctrl+Alt+Del</button><button id="fs" type="button">Toàn màn hình</button><button id="kt" class="do" type="button">Kết thúc</button>
<a class="nut" href="/uem/may/""" + m["id"] + """/tu-xa">Quay lại</a></div>
<div class="loi" id="loi"></div><div id="man"></div>
<script type="module">
import RFB from '/uem/novnc/core/rfb.js';
const C = """ + cau_hinh + """;
const tt = document.getElementById('tt'), loi = document.getElementById('loi');
const dev = new URLSearchParams(location.search).get('ws');   // chi de thu tren may phat trien: noi thang cau noi 127.0.0.1:8895
const ws = (location.protocol === 'https:' ? 'wss://' : 'ws://') + (dev === '127.0.0.1:8895' ? dev : location.host) + '/uem-vnc-ws/' + C.tok;
let rfb, daNoi = false;
try {
  rfb = new RFB(document.getElementById('man'), ws, {credentials: {password: C.pin}, wsProtocols: ['binary']});
  rfb.scaleViewport = true; rfb.background = '#000'; rfb.focusOnClick = true;
  rfb.addEventListener('connect', () => { daNoi = true; tt.textContent = 'Đã kết nối'; });
  rfb.addEventListener('disconnect', e => { tt.textContent = e.detail.clean ? 'Đã ngắt kết nối' : 'Mất kết nối';
    if (!daNoi) { loi.style.display = 'block'; loi.textContent = 'Không kết nối được. Kiểm tra máy đang bật, TightVNC đã cài, và nginx đã có cấu hình /uem-vnc-ws/ (sudo bash /opt/console-pi/tools/cai-vnc.sh).'; } });
  rfb.addEventListener('securityfailure', e => { loi.style.display = 'block'; loi.textContent = 'Xác thực thất bại: ' + (e.detail.reason || ''); });
  rfb.addEventListener('credentialsrequired', () => rfb.sendCredentials({password: C.pin}));
} catch (e) { loi.style.display = 'block'; loi.textContent = 'Lỗi trình duyệt: ' + e; }
document.getElementById('cad').onclick = () => rfb && rfb.sendCtrlAltDel();
document.getElementById('fs').onclick = () => { const d = document.documentElement; if (document.fullscreenElement) document.exitFullscreen(); else if (d.requestFullscreen) d.requestFullscreen(); };
function xong() { try { navigator.sendBeacon('/uem/may/' + C.mid + '/tu-xa/vnc/' + C.tok + '/ket-thuc'); } catch (e) {} }
document.getElementById('kt').onclick = async () => {
  try { if (rfb) rfb.disconnect(); } catch (e) {}
  tt.textContent = 'Đang tắt dịch vụ trên máy...';
  try { await fetch('/uem/may/' + C.mid + '/tu-xa/vnc/' + C.tok + '/ket-thuc', {method: 'POST'}); } catch (e) {}
  location.href = '/uem/may/' + C.mid + '/tu-xa';
};
</script></body></html>""")
    return html


def register_uem(app):
    UBC.khoi_dong_bo_lap()
    UP.khoi_dong_bo_lap()
    UW.khoi_dong_bo_lap()
    UT.khoi_dong_bo_lap()
    DC.dat_kenh_agent(UA)                 # kich ban Agent (tk_dongco) vao may qua agent
    UKB.dang_ky(app)
    UV.khoi_dong_bridge()
    PKI.nap_lai_neu_doi()
    UAT.register_agent(app)
    UDK.register_dieukhien(app)
    USL.register_sualoi(app)
    URD.register_uem_rustdesk(app)
    UVT.register_vnc_trang(app)

    @app.route("/uem")
    def uem_tq():
        return T.trang_tong_quan()

    @app.route("/uem/may")
    def uem_may():
        return T.trang_may()

    @app.route("/uem/may/hang-loat", methods=["POST"])
    def uem_may_hl():
        ids = [i for i in request.form.getlist("may") if DL.tim(DL.MAY.doc(), i)]
        viec = request.form.get("viec", "")
        if not ids:
            return chuyen("/uem/may", "Chưa chọn máy nào.", False)
        tk, the, dd = request.form.get("tk"), request.form.get("the"), request.form.get("dd")
        if viec == "bao_cao":
            n = sum(1 for i in ids if UK.co_the_ket_noi(DL.tim(DL.MAY.doc(), i) or {}) and UBC.chay_nen(i))
            return chuyen("/uem/may", f"Đã xếp lịch lấy báo cáo cho {n} máy (máy chưa gán tài khoản bị bỏ qua). Tải lại trang sau ít giây.", n > 0)
        if viec == "gan_tk":
            if not DL.tim(DL.TAI_KHOAN.doc(), tk or ""):
                return chuyen("/uem/may", "Chọn tài khoản quản trị.", False)
            DL.MAY.sua(lambda ds: [x.update(tai_khoan_id=tk) for x in ds if x["id"] in ids])
            for i in ids:
                UBC.chay_nen(i)
            return chuyen("/uem/may", f"Đã gán tài khoản cho {len(ids)} máy và đang lấy báo cáo.")
        if viec in ("them_the", "bo_the"):
            if not DL.tim(UD.THE.doc(), the or ""):
                return chuyen("/uem/may", "Chọn thẻ.", False)

            def sua_the(ds):
                for x in ds:
                    if x["id"] in ids:
                        t = [k for k in x.get("the", []) if k != the]
                        x["the"] = t + [the] if viec == "them_the" else t
            DL.MAY.sua(sua_the)
            return chuyen("/uem/may", f"Đã {'thêm' if viec == 'them_the' else 'gỡ'} thẻ cho {len(ids)} máy.")
        if viec in ("them_nhom", "bo_nhom", "nhom_moi"):
            ten_moi = (request.form.get("nhom_moi") or "").strip()[:60]
            gid = request.form.get("nhom") or ""
            if viec == "nhom_moi":
                if not ten_moi:
                    return chuyen("/uem/may", "Nhập tên nhóm mới.", False)
                if any(g["ten"].lower() == ten_moi.lower() for g in DL.NHOM_MAY.doc()):
                    return chuyen("/uem/may", f"Đã có nhóm tên \"{ten_moi}\". Chọn nhóm đó rồi dùng Thêm vào nhóm.", False)
                DL.NHOM_MAY.sua(lambda ds: ds.append({"id": DL.moi_id(), "ten": ten_moi, "may": list(ids)}))
                return chuyen("/uem/may", f"Đã tạo nhóm \"{ten_moi}\" gồm {len(ids)} máy.")
            if not DL.tim(DL.NHOM_MAY.doc(), gid):
                return chuyen("/uem/may", "Chọn nhóm máy.", False)

            def sua_nhom(ds):
                g = DL.tim(ds, gid)
                cu = [i for i in g.get("may", []) if i not in ids]
                g["may"] = cu + list(ids) if viec == "them_nhom" else cu
            DL.NHOM_MAY.sua(sua_nhom)
            return chuyen("/uem/may", f"Đã {'thêm' if viec == 'them_nhom' else 'gỡ'} {len(ids)} máy {'vào' if viec == 'them_nhom' else 'khỏi'} nhóm.")
        if viec == "dia_diem":
            if dd and not DL.tim(UD.DIA_DIEM.doc(), dd):
                return chuyen("/uem/may", "Địa điểm không hợp lệ.", False)
            DL.MAY.sua(lambda ds: [x.update(dia_diem=dd or None) for x in ds if x["id"] in ids])
            return chuyen("/uem/may", f"Đã đặt địa điểm cho {len(ids)} máy.")
        if viec in ("bat", "tat"):
            DL.MAY.sua(lambda ds: [x.update(giam_sat=(viec == "bat")) for x in ds if x["id"] in ids])
            return chuyen("/uem/may", f"Đã {'bật' if viec == 'bat' else 'vô hiệu'} giám sát {len(ids)} máy.")
        if viec == "xoa":
            co_ag = {x["id"] for x in DL.MAY.doc() if x["id"] in ids and UA.co_agent(x)}
            DL.MAY.sua(lambda ds: [x.update(an=True) for x in ds if x["id"] in co_ag])
            ids = [i for i in ids if i not in co_ag] if not isinstance(ids, set) else ids - co_ag
            DL.MAY.sua(lambda ds: ds.__setitem__(slice(None), [x for x in ds if x["id"] not in ids]))
            DL.NHOM_MAY.sua(lambda gs: [g.update(may=[i for i in g.get("may", []) if i not in ids]) for g in gs])
            return chuyen("/uem/may", f"Đã xóa {len(ids)} máy khỏi danh sách.")
        return chuyen("/uem/may", "Hành động không hợp lệ.", False)

    @app.route("/uem/may/<mid>")
    @app.route("/uem/may/<mid>/")
    @app.route("/uem/may/<mid>/<tab>")
    def uem_may_ct(mid, tab=""):
        m = may_theo_id(mid)
        tab = tab or "tq"
        if tab == "trien-khai":                          # tab rieng tung may bi bo (5.3): cai/go phan mem lam o trang Trien khai WinGet chung
            return redirect("/uem/trien-khai")
        if tab not in {k for k, _ in T.TAB_MAY}:
            abort(404)
        if tab == "agent":
            return UAT.tab_agent(m)
        if tab in ("duyet-file", "tu-xa", "nguon", "trien-khai", "tac-vu"):
            return tab_may_b(m, tab)
        if tab in ("cli", "dich-vu", "tien-trinh", "sua-loi"):
            return {"cli": UDK.tab_cli, "dich-vu": UDK.tab_dich_vu, "tien-trinh": UDK.tab_tien_trinh, "sua-loi": USL.tab_sua_loi}[tab](m)
        return T.tab_may(m, tab)

    @app.route("/uem/may/<mid>/bao-cao-ngay", methods=["POST"])
    def uem_bao_cao_ngay(mid):
        m = may_theo_id(mid)
        if not UK.co_the_ket_noi(m):
            return chuyen(f"/uem/may/{mid}/quan-ly", "Gán tài khoản quản trị hoặc cài agent cho máy trước.", False)
        UBC.chay_nen(mid)
        return chuyen(request.referrer or f"/uem/may/{mid}", "Đang lấy báo cáo, mất khoảng 25 giây. Tải lại trang sau đó.")

    @app.route("/uem/may/<mid>/ghi-chu", methods=["POST"])
    def uem_ghi_chu(mid):
        may_theo_id(mid)
        UD.sua_may(mid, ghi_chu=(request.form.get("ghi_chu") or "")[:20000])
        return chuyen(f"/uem/may/{mid}/ghi-chu", "Đã lưu ghi chú.")

    @app.route("/uem/may/<mid>/metadata", methods=["POST"])
    def uem_metadata(mid):
        may_theo_id(mid)
        gt = {d["id"]: (request.form.get("md_" + d["id"]) or "").strip()[:300] for d in UD.METADATA.doc()}
        UD.sua_may(mid, metadata={k: v for k, v in gt.items() if v})
        return chuyen(f"/uem/may/{mid}/metadata", "Đã lưu.")

    @app.route("/uem/may/<mid>/quan-ly", methods=["POST"])
    def uem_quan_ly(mid):
        m = may_theo_id(mid)
        f = request.form
        if f.get("chi") == "giam_sat":
            UD.sua_may(mid, giam_sat=bool(f.get("giam_sat")))
            return chuyen(request.referrer or f"/uem/may/{mid}", "Đã đổi trạng thái giám sát.")
        ip = (f.get("ip") or "").strip()
        ips = _ips_tu_chuoi(ip)
        if not ips or len(ips) != 1:
            return chuyen(f"/uem/may/{mid}/quan-ly", "Địa chỉ IP không hợp lệ.", False)
        if any(x["ip"] == ips[0] and x["id"] != mid for x in DL.MAY.doc()):
            return chuyen(f"/uem/may/{mid}/quan-ly", "Đã có máy khác dùng IP này.", False)
        mac = (f.get("mac") or "").strip()
        mac_c = _MP.chuan_mac(mac) if mac else ""
        if mac and not mac_c:
            return chuyen(f"/uem/may/{mid}/quan-ly", "Địa chỉ MAC không hợp lệ.", False)
        tk = (f.get("tai_khoan_id") or None) if "tai_khoan_id" in f else m.get("tai_khoan_id")
        if tk and not DL.tim(DL.TAI_KHOAN.doc(), tk):
            tk = None
        the = [t for t in f.getlist("the") if DL.tim(UD.THE.doc(), t)]
        dd = f.get("dia_diem") or None
        if dd and not DL.tim(UD.DIA_DIEM.doc(), dd):
            dd = None
        UD.sua_may(mid, bi_danh=(f.get("bi_danh") or "").strip()[:60], ip=ips[0], mac=mac_c or "", loai=(f.get("loai") or "").strip()[:40], tai_khoan_id=tk, the=the, dia_diem=dd, giam_sat=bool(f.get("giam_sat")))
        if tk and tk != m.get("tai_khoan_id"):
            UBC.chay_nen(mid)
        return chuyen(f"/uem/may/{mid}/quan-ly", "Đã lưu.")

    @app.route("/uem/may/<mid>/xoa", methods=["POST"])
    def uem_may_xoa(mid):
        m = may_theo_id(mid)
        if UA.co_agent(m):
            # May da cai agent: chi AN khoi danh sach quan ly (giu chung chi). Khi agent bao nhip lai (may duoc bat len) se tu hien lai.
            UD.sua_may(mid, an=True)
            return chuyen("/uem/may", "Đã xóa máy khỏi quản lý. Khi máy được bật và agent kết nối lại, máy sẽ tự xuất hiện lại.")
        DL.MAY.sua(lambda ds: ds.__setitem__(slice(None), [x for x in ds if x["id"] != mid]))
        return chuyen("/uem/may", "Đã xóa máy khỏi danh sách.")

    @app.route("/uem/may/<mid>/phan-mem.csv")
    def uem_pm_csv(mid):
        m = may_theo_id(mid)
        return _csv("phan-mem-" + re.sub(r"[^A-Za-z0-9_.-]", "_", ten_may(m)) + ".csv", ["Tên", "Phiên bản", "Nhà sản xuất", "Ngày cài"],
                    [[a["name"], a.get("version", ""), a.get("publisher", ""), a.get("install_date", "")] for a in bc(m).get("applications", [])])

    @app.route("/uem/may/<mid>/may-in/xoa", methods=["POST"])
    def uem_xoa_may_in(mid):
        m = may_theo_id(mid)
        ten = (request.form.get("ten") or "").strip()
        if not any(p["name"] == ten for p in bc(m).get("printers", [])):
            return chuyen(f"/uem/may/{mid}/may-in", "Không thấy máy in này trong báo cáo.", False)
        try:
            c, mk = _ket_noi_may(m)
            out, err = DC._chay_ps(c, f"$ErrorActionPreference='Stop'; Remove-Printer -Name {DC._q(ten)}; 'OK'")
            ok = "OK" in out and not err
            tb = "Đã xóa máy in." if ok else DC._loi_dep(err or out, mk)
        except Exception as e:
            ok, tb = False, DC._loi_dep(e)
        UD.ghi_tac_vu(mid, "tu_xa", f"Xóa máy in {ten}", ok, tb)
        if ok:
            UBC.chay_nen(mid)
        return chuyen(f"/uem/may/{mid}/may-in", tb, ok)

    @app.route("/uem/may/<mid>/lenh", methods=["POST"])
    def uem_lenh(mid):
        m = may_theo_id(mid)
        lenh = (request.form.get("lenh") or "").strip()[:8000]
        if not lenh:
            return chuyen(f"/uem/may/{mid}/tu-xa", "Chưa nhập lệnh.", False)
        try:
            c, mk = _ket_noi_may(m)
            out, err = DC._chay_ps(c, lenh)
            KET_QUA_LENH[mid] = ((out or "") + ("\n[LỖI] " + err if err else ""))[:20000].replace(mk, "***") if mk else (out or "")[:20000]
            ok = not err
        except Exception as e:
            KET_QUA_LENH[mid] = DC._loi_dep(e)
            ok = False
        UD.ghi_tac_vu(mid, "tu_xa", "Chạy lệnh PowerShell: " + lenh.splitlines()[0][:60], ok, KET_QUA_LENH[mid][:300])
        return chuyen(f"/uem/may/{mid}/tu-xa", "Đã chạy lệnh." if ok else "Lệnh báo lỗi, xem kết quả bên dưới.", ok)

    @app.route("/uem/may/<mid>/tu-xa/rdp")
    def uem_rdp(mid):
        m = may_theo_id(mid)
        user, _ = DL.lay_tai_khoan(m.get("tai_khoan_id"))
        noi_dung = f"full address:s:{m['ip']}\r\nprompt for credentials:i:1\r\nauthentication level:i:2\r\n" + (f"username:s:{user}\r\n" if user and re.fullmatch(r"[\w .\\@-]{1,64}", user) else "")
        ten = re.sub(r"[^A-Za-z0-9_.-]", "_", ten_may(m)) or "may"
        return Response(noi_dung, mimetype="application/x-rdp", headers={"Content-Disposition": f'attachment; filename="{ten}.rdp"'})

    @app.route("/uem/may/<mid>/nguon", methods=["POST"])
    def uem_nguon(mid):
        m = may_theo_id(mid)
        viec = request.form.get("viec", "")
        if viec == "bat":
            mac = _MP.chuan_mac(m.get("mac", ""))
            if not mac:
                return chuyen(f"/uem/may/{mid}/nguon", "Máy chưa có địa chỉ MAC hợp lệ (nhập ở tab Quản lý).", False)
            n, _ct = _MP.gui([mac])
            UD.ghi_tac_vu(mid, "tu_xa", "Wake-on-LAN", True, mac)
            return chuyen(f"/uem/may/{mid}/nguon", f"Đã gửi gói đánh thức tới {mac}. Máy mất vài chục giây để khởi động.")
        if viec not in ("khoi_dong_lai", "tat", "ngu_dong", "huy"):
            return chuyen(f"/uem/may/{mid}/nguon", "Hành động không hợp lệ.", False)
        try:
            sau = max(0, min(86400, int(request.form.get("sau", "30"))))
        except ValueError:
            return chuyen(f"/uem/may/{mid}/nguon", "Số giây không hợp lệ.", False)
        tin = (request.form.get("tin") or "").replace('"', "'")[:200]
        lenh = {"khoi_dong_lai": f"shutdown.exe /r /f /t {sau} /c {DC._q(tin)}", "tat": f"shutdown.exe /s /f /t {sau} /c {DC._q(tin)}",
                "ngu_dong": "shutdown.exe /h", "huy": "shutdown.exe /a"}[viec]
        ten = {"khoi_dong_lai": "Khởi động lại", "tat": "Tắt máy", "ngu_dong": "Ngủ đông", "huy": "Hủy lệnh tắt máy"}[viec]
        try:
            c, mk = _ket_noi_may(m)
            out, err = DC._chay_ps(c, f"{lenh} 2>&1 | Out-String; 'RC=' + $LASTEXITCODE")
            ok = "RC=0" in out
            tb = (f"Đã gửi lệnh: {ten.lower()}" + (f" sau {sau} giây." if viec in ("khoi_dong_lai", "tat") else ".")) if ok else _loi_shutdown(out, err, mk)
        except Exception as e:
            ok, tb = False, DC._loi_dep(e)
        UD.ghi_tac_vu(mid, "tu_xa", ten, ok, tb)
        return chuyen(f"/uem/may/{mid}/nguon", tb, ok)

    # ---- duyet file
    @app.route("/uem/may/<mid>/duyet-file/tai")
    def uem_tai_file(mid):
        m = may_theo_id(mid)
        p = request.args.get("p", "")
        if not _duong_hop_le(p):
            abort(400)
        try:
            c, mk = _ket_noi_may(m)
            out, err = DC._chay_ps(c, f"$f = Get-Item -LiteralPath {DC._q(p)} -ErrorAction Stop; if ($f.PSIsContainer) {{ 'DIR' }} else {{ $f.Length }}")
            if out.strip() == "DIR" or not out.strip().isdigit():
                return chuyen(f"/uem/may/{mid}/duyet-file", "Không tải được (đây là thư mục hoặc không đọc được file).", False)
            if int(out.strip()) > 200 * 1024 * 1024:
                return chuyen(f"/uem/may/{mid}/duyet-file", "File lớn hơn 200 MB, không tải qua trang này.", False)
            tmp = tempfile.mkdtemp(prefix="uem-")
            dich = os.path.join(tmp, "f")
            c.fetch(p, dich)
        except Exception as e:
            return chuyen(f"/uem/may/{mid}/duyet-file", DC._loi_dep(e), False)
        UD.ghi_tac_vu(mid, "tu_xa", "Tải file " + p, True, "")
        resp = send_file(dich, as_attachment=True, download_name=p.rsplit("\\", 1)[-1] or "file")
        resp.call_on_close(lambda: (os.path.exists(dich) and os.remove(dich), os.path.isdir(tmp) and os.rmdir(tmp)))
        return resp

    @app.route("/uem/may/<mid>/duyet-file/tai-len", methods=["POST"])
    def uem_tai_len(mid):
        m = may_theo_id(mid)
        cha = (request.form.get("cha") or "").strip()
        f = request.files.get("tep")
        ten = os.path.basename((f.filename if f else "") or "").replace("\\", "_")
        if not cha or not _duong_hop_le(cha) or not f or not ten or re.search(r"[\x00-\x1f<>\"|?*:/]", ten):
            return chuyen(f"/uem/may/{mid}/duyet-file?p={cha}", "Tên file hoặc thư mục đích không hợp lệ.", False)
        tmp = tempfile.mkdtemp(prefix="uem-")
        nguon = os.path.join(tmp, "f")
        try:
            f.save(nguon)
            if os.path.getsize(nguon) > 200 * 1024 * 1024:
                raise RuntimeError("File lớn hơn 200 MB.")
            c, mk = _ket_noi_may(m)
            dich = cha.rstrip("\\") + "\\" + ten
            c.copy(nguon, dich)
            ok, tb = True, f"Đã tải lên {dich}"
        except Exception as e:
            ok, tb = False, DC._loi_dep(e)
        finally:
            try:
                os.remove(nguon)
                os.rmdir(tmp)
            except OSError:
                pass
        UD.ghi_tac_vu(mid, "tu_xa", "Tải file lên " + cha, ok, tb)
        return chuyen(f"/uem/may/{mid}/duyet-file?p={cha}", tb, ok)

    @app.route("/uem/may/<mid>/duyet-file/tao-thu-muc", methods=["POST"])
    def uem_tao_tm(mid):
        m = may_theo_id(mid)
        cha, ten = (request.form.get("cha") or "").strip(), (request.form.get("ten") or "").strip()
        if not cha or not _duong_hop_le(cha) or not ten or re.search(r"[\x00-\x1f<>\"|?*:/\\]", ten):
            return chuyen(f"/uem/may/{mid}/duyet-file?p={cha}", "Tên thư mục không hợp lệ.", False)
        try:
            c, mk = _ket_noi_may(m)
            out, err = DC._chay_ps(c, f"$ErrorActionPreference='Stop'; New-Item -ItemType Directory -Path {DC._q(cha.rstrip(chr(92)) + chr(92) + ten)} | Out-Null; 'OK'")
            ok = "OK" in out and not err
            tb = "Đã tạo thư mục." if ok else DC._loi_dep(err or out, mk)
        except Exception as e:
            ok, tb = False, DC._loi_dep(e)
        UD.ghi_tac_vu(mid, "tu_xa", f"Tạo thư mục {ten}", ok, tb)
        return chuyen(f"/uem/may/{mid}/duyet-file?p={cha}", tb, ok)

    @app.route("/uem/may/<mid>/duyet-file/xoa", methods=["POST"])
    def uem_xoa_file(mid):
        m = may_theo_id(mid)
        p, cha = (request.form.get("p") or "").strip(), (request.form.get("cha") or "").strip()
        if not _duong_hop_le(p) or len(p.rstrip("\\")) <= 3:
            return chuyen(f"/uem/may/{mid}/duyet-file", "Không được xóa đường dẫn này.", False)
        try:
            c, mk = _ket_noi_may(m)
            out, err = DC._chay_ps(c, f"$ErrorActionPreference='Stop'; Remove-Item -LiteralPath {DC._q(p)} -Recurse -Force; 'OK'")
            ok = "OK" in out and not err
            tb = "Đã xóa." if ok else DC._loi_dep(err or out, mk)
        except Exception as e:
            ok, tb = False, DC._loi_dep(e)
        UD.ghi_tac_vu(mid, "tu_xa", "Xóa " + p, ok, tb)
        return chuyen(f"/uem/may/{mid}/duyet-file?p={cha}", tb, ok)

    # ---- cac muc chinh
    @app.route("/uem/phan-mem")
    def uem_pm():
        return trang_phan_mem()

    @app.route("/uem/bao-mat")
    def uem_bm():
        return trang_bao_mat("")

    @app.route("/uem/bao-mat/cap-nhat")
    def uem_bm_cn():
        return trang_bao_mat("cap-nhat")

    @app.route("/uem/trien-khai")
    def uem_td():
        return trang_trien_khai()

    @app.route("/uem/trien-khai/dot")
    def uem_td_dot():
        return trang_dot()

    @app.route("/uem/trien-khai/dot/<dot>")
    def uem_td_dot_ct(dot):
        return trang_dot_ct(dot)

    @app.route("/uem/trien-khai/dot/<dot>/huy", methods=["POST"])
    def uem_td_dot_huy(dot):
        n = UT.huy_cho(dot)
        return chuyen(f"/uem/trien-khai/dot/{dot}", f"Đã hủy {n} máy đang chờ.", n > 0)

    @app.route("/uem/trien-khai/dot/<dot>/chay-lai", methods=["POST"])
    def uem_td_dot_lai(dot):
        n = UT.chay_lai_loi(dot)
        return chuyen(f"/uem/trien-khai/dot/{dot}", f"Đã đưa {n} máy vào hàng chờ chạy lại." if n else "Không có máy nào cần chạy lại.", n > 0)

    @app.route("/uem/trien-khai/kho")
    def uem_td_kho():
        return trang_kho()

    @app.route("/uem/trien-khai/goi")
    def uem_td_goi():
        return trang_goi()

    @app.route("/uem/trien-khai/lich-su")
    def uem_td_ls():
        return trang_lich_su()

    @app.route("/uem/trien-khai/danh-muc", methods=["POST"])
    def uem_td_dm():
        ok, tb = UW.cap_nhat(force=True)
        return chuyen("/uem/trien-khai", tb, ok)

    @app.route("/uem/trien-khai/chay", methods=["POST"])
    def uem_td_chay():
        f = request.form
        so = lambda k, md: int(f.get(k)) if (f.get(k) or "").isdigit() else md  # noqa: E731
        dot, loi = UT.bat_dau(f.get("hanh_dong", ""), (f.get("goi_id") or "").strip(), (f.get("ten_goi") or "").strip()[:120], may_tu_form(f),
                              thu_lai=so("thu_lai", 2), het_han_ngay=so("het_han_ngay", 7), wol=bool(f.get("wol")))
        if loi:
            return chuyen("/uem/trien-khai", loi, False)
        return redirect_dot(dot)

    @app.route("/uem/trien-khai/tt/<dot>")
    def uem_td_tt(dot):
        d = UT.trang_thai(dot)
        if d is None:
            return jsonify({"loi": "Không còn thông tin đợt này."})
        d["hanh_dong"] = UT.TEN_HANH_DONG.get(d["hanh_dong"], d["hanh_dong"])
        return jsonify(d)

    @app.route("/uem/profiles")
    def uem_pf():
        return trang_profiles()

    @app.route("/uem/profiles/tao", methods=["POST"])
    def uem_pf_tao():
        ten = (request.form.get("ten") or "").strip()[:80]
        if not ten:
            return chuyen("/uem/profiles", "Nhập tên profile.", False)
        pid = DL.moi_id()
        UD.PROFILES.sua(lambda ds: ds.append({"id": pid, "ten": ten, "mo_ta": (request.form.get("mo_ta") or "").strip()[:200], "bat": False, "ap_dung_tat_ca": False, "the": [], "tasks": []}))
        return chuyen(f"/uem/profiles/{pid}", "Đã tạo profile. Thêm tác vụ rồi bật profile.")

    @app.route("/uem/profiles/<pid>")
    def uem_pf_ct(pid):
        return trang_profile(pid)

    def _sua_pf(pid, ham):
        def ghi(ds):
            p = DL.tim(ds, pid)
            if p is None:
                return False
            ham(p)
            return True
        return UD.PROFILES.sua(ghi)

    @app.route("/uem/profiles/<pid>/luu", methods=["POST"])
    def uem_pf_luu(pid):
        f = request.form
        ten = (f.get("ten") or "").strip()[:80]
        if not ten:
            return chuyen(f"/uem/profiles/{pid}", "Nhập tên profile.", False)
        the = [t for t in f.getlist("the") if DL.tim(UD.THE.doc(), t)]
        nhom_may = [g for g in f.getlist("nhom_may") if DL.tim(DL.NHOM_MAY.doc(), g)]
        if not _sua_pf(pid, lambda p: p.update(ten=ten, mo_ta=(f.get("mo_ta") or "").strip()[:200], ap_dung_tat_ca=bool(f.get("ap_dung_tat_ca")), the=the, nhom_may=nhom_may, bat=bool(f.get("bat")))):
            abort(404)
        return chuyen(f"/uem/profiles/{pid}", "Đã lưu profile.")

    @app.route("/uem/profiles/<pid>/xoa", methods=["POST"])
    def uem_pf_xoa(pid):
        UD.PROFILES.sua(lambda ds: ds.__setitem__(slice(None), [p for p in ds if p["id"] != pid]))
        UD.TRANG_THAI_PROFILE.sua(lambda d: d.pop(pid, None))
        return chuyen("/uem/profiles", "Đã xóa profile.")

    @app.route("/uem/profiles/<pid>/ap-dung", methods=["POST"])
    def uem_pf_ap(pid):
        p = DL.tim(UD.PROFILES.doc(), pid)
        if not p:
            abort(404)
        if not p.get("tasks"):
            return chuyen(f"/uem/profiles/{pid}", "Profile chưa có tác vụ nào.", False)
        n = UP.ap_dung_ngay(pid)
        return chuyen(f"/uem/profiles/{pid}", f"Đang áp dụng lên {n} máy ở nền. Tải lại trang sau ít phút để xem kết quả." if n else "Không có máy nào thuộc phạm vi (hoặc máy chưa gán tài khoản).", n > 0)

    @app.route("/uem/profiles/<pid>/task/luu", methods=["POST"])
    def uem_pf_task_luu(pid):
        p = DL.tim(UD.PROFILES.doc(), pid)
        if not p:
            abort(404)
        loai, tid = request.form.get("loai_tac_vu", ""), request.form.get("task_id", "")
        ts, loi = UB.kiem_tra(loai, request.form)
        if loi:
            return chuyen(f"/uem/profiles/{pid}?loai={loai}" + (f"&sua={tid}" if tid else "") + "#form-task", loi, False)
        bo_qua = bool(request.form.get("bo_qua_loi"))

        def ghi(pp):
            if tid:
                t = DL.tim(pp["tasks"], tid)
                if t:
                    if loai == "user_them" and not ts.get("mat_khau"):
                        ts["mat_khau"] = t["tham_so"].get("mat_khau", "")
                    t.update(tham_so=ts, bo_qua_loi=bo_qua, ver=DL.moi_id())
                    return
            pp["tasks"].append({"id": DL.moi_id(), "loai": loai, "tham_so": ts, "bat": True, "bo_qua_loi": bo_qua, "ver": DL.moi_id()})
        _sua_pf(pid, ghi)
        return chuyen(f"/uem/profiles/{pid}", "Đã lưu tác vụ.")

    @app.route("/uem/profiles/<pid>/task/<tid>/hanh-dong", methods=["POST"])
    def uem_pf_task_hd(pid, tid):
        viec = request.form.get("viec", "")

        def ghi(p):
            ds = p["tasks"]
            i = next((k for k, t in enumerate(ds) if t["id"] == tid), None)
            if i is None:
                return
            if viec == "xoa":
                ds.pop(i)
            elif viec == "bat_tat":
                ds[i]["bat"] = not ds[i].get("bat", True)
            elif viec == "len" and i > 0:
                ds[i - 1], ds[i] = ds[i], ds[i - 1]
            elif viec == "xuong" and i < len(ds) - 1:
                ds[i + 1], ds[i] = ds[i], ds[i + 1]
        _sua_pf(pid, ghi)
        return chuyen(f"/uem/profiles/{pid}", "Đã cập nhật tác vụ.")

    @app.route("/uem/bao-cao")
    def uem_bc():
        return trang_bao_cao()

    @app.route("/uem/bao-cao/<ten>.csv")
    def uem_bc_csv(ten):
        return csv_bao_cao(ten)

    @app.route("/uem/quan-tri")
    def uem_qt():
        return trang_quan_tri("may")

    @app.route("/uem/quan-tri/<muc>")
    def uem_qt_muc(muc):
        return trang_quan_tri(muc)

    @app.route("/uem/quan-tri/<muc>/luu", methods=["POST"])
    def uem_qt_luu(muc):
        kho = {"the": UD.THE, "dia-diem": UD.DIA_DIEM, "metadata": UD.METADATA}.get(muc)
        if kho is None:
            abort(404)
        f = request.form
        ten = (f.get("ten") or "").strip()[:60]
        if not ten:
            return chuyen(f"/uem/quan-tri/{muc}", "Nhập tên.", False)
        mau = f.get("mau", "")
        mau = mau if re.fullmatch(r"#[0-9a-fA-F]{6}", mau) else "#6366f1"
        id_ = f.get("id", "")

        def ghi(ds):
            if any(x["ten"].lower() == ten.lower() and x["id"] != id_ for x in ds):
                return False
            x = DL.tim(ds, id_)
            if x is None:
                x = {"id": DL.moi_id()}
                ds.append(x)
            x.update(ten=ten, mo_ta=(f.get("mo_ta") or "").strip()[:200])
            if muc == "the":
                x["mau"] = mau
            return True
        if not kho.sua(ghi):
            return chuyen(f"/uem/quan-tri/{muc}", "Tên này đã có.", False)
        return chuyen(f"/uem/quan-tri/{muc}", "Đã lưu.")

    @app.route("/uem/quan-tri/<muc>/xoa", methods=["POST"])
    def uem_qt_xoa(muc):
        kho = {"the": UD.THE, "dia-diem": UD.DIA_DIEM, "metadata": UD.METADATA}.get(muc)
        if kho is None:
            abort(404)
        id_ = request.form.get("id", "")
        kho.sua(lambda ds: ds.__setitem__(slice(None), [x for x in ds if x["id"] != id_]))

        def don(ds):
            for m in ds:
                if muc == "the":
                    m["the"] = [t for t in m.get("the", []) if t != id_]
                elif muc == "dia-diem" and m.get("dia_diem") == id_:
                    m["dia_diem"] = None
                elif muc == "metadata":
                    (m.get("metadata") or {}).pop(id_, None)
        DL.MAY.sua(don)
        if muc == "the":
            UD.PROFILES.sua(lambda ds: [p.update(the=[t for t in p.get("the", []) if t != id_]) for p in ds])
        return chuyen(f"/uem/quan-tri/{muc}", "Đã xóa.")

    @app.route("/uem/quan-tri/cai-dat", methods=["POST"])
    def uem_qt_cai_dat():
        f = request.form
        try:
            a = max(5, min(1440, int(f.get("tan_suat_bao_cao", "60"))))
            b = max(5, min(1440, int(f.get("tan_suat_profile", "30"))))
        except ValueError:
            return chuyen("/uem/quan-tri/cai-dat", "Chu kỳ phải là số phút.", False)
        UD.luu_cai_dat(tan_suat_bao_cao=a, tan_suat_profile=b, tu_dong_giam_sat=bool(f.get("tu_dong_giam_sat")))
        return chuyen("/uem/quan-tri/cai-dat", "Đã lưu cài đặt.")

    # ---- dieu khien tu xa VNC (noVNC)
    @app.route("/uem/novnc/<path:p>")
    def uem_novnc(p):
        from flask import send_from_directory
        return send_from_directory(NOVNC_DIR, p, max_age=3600)

    @app.route("/uem/may/<mid>/tu-xa/vnc/cai", methods=["POST"])
    def uem_vnc_cai(mid):
        may_theo_id(mid)
        ok, tb = UV.cai(mid)
        return chuyen(f"/uem/may/{mid}/tu-xa", tb, ok)

    @app.route("/uem/may/<mid>/tu-xa/vnc/go", methods=["POST"])
    def uem_vnc_go(mid):
        may_theo_id(mid)
        ok, tb = UV.go(mid)
        return chuyen(f"/uem/may/{mid}/tu-xa", tb, ok)

    @app.route("/uem/may/<mid>/tu-xa/vnc/kiem-tra", methods=["POST"])
    def uem_vnc_kt(mid):
        may_theo_id(mid)
        ok, tb = UV.kiem_tra(mid)
        return chuyen(f"/uem/may/{mid}/tu-xa", tb, ok)

    @app.route("/uem/may/<mid>/tu-xa/vnc/mo", methods=["POST"])
    def uem_vnc_mo(mid):
        may_theo_id(mid)
        if not nginx_vnc_san_sang():
            return chuyen(f"/uem/may/{mid}/tu-xa", "Chưa cấu hình nginx cho điều khiển từ xa (chạy sudo bash /opt/console-pi/tools/cai-vnc.sh).", False)
        tok, tb = UV.mo_phien(mid, bool(request.form.get("bao")), bool(request.form.get("phep")))
        if not tok:
            return chuyen(f"/uem/may/{mid}/tu-xa", tb, False)
        from flask import redirect
        return redirect(f"/uem/may/{mid}/tu-xa/vnc/{tok}")

    @app.route("/uem/may/<mid>/tu-xa/vnc/<tok>")
    def uem_vnc_xem(mid, tok):
        m = may_theo_id(mid)
        p = UV.thong_tin_phien(tok)
        if not p or p["may_id"] != mid:
            return chuyen(f"/uem/may/{mid}/tu-xa", "Phiên điều khiển đã hết hạn hoặc đã kết thúc, hãy mở lại.", False)
        return trang_vnc(m, tok, p["pin"])

    @app.route("/uem/may/<mid>/tu-xa/vnc/<tok>/ket-thuc", methods=["POST"])
    def uem_vnc_ketthuc(mid, tok):
        p = UV.thong_tin_phien(tok)
        if p and p["may_id"] == mid:
            UV.ket_thuc(tok)
        return jsonify({"ok": True})


def redirect_dot(dot):
    from flask import redirect
    return redirect(f"/uem/trien-khai?dot={dot}")
