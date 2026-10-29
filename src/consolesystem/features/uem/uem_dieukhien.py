# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Quan ly may tram - DIEU KHIEN TU XA: dong lenh (CMD/PowerShell), Dich vu (Services), Tien trinh (Task Manager).
Moi thao tac di qua UK.ket_noi: agent dang song (khong can WinRM) hoac WinRM neu da gan tai khoan. Moi lenh ghi vao tab "Tac vu" cua may.
AN TOAN: ten dich vu / PID duoc kiem chat theo mau; lenh nguoi dung go vao dong lenh duoc chuyen bang base64 (khong noi chuoi vao script).
"""
import base64
import json
import re

from flask import jsonify, request

from ui import uem_dulieu as UD
from ui import uem_ketnoi as UK
from ui import uem_trang as T
from ui.uem_trang import _esc, may_theo_id

MAU_DICH_VU = re.compile(r"[A-Za-z0-9_.$@ \-]{1,256}")
KIEU_KHOI_DONG = {"tu_dong": "Automatic", "thu_cong": "Manual", "tat": "Disabled"}


def _b64(s):
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def _chay(m, script):
    """(ok, out_hoac_loi). Khong nem ngoai le."""
    try:
        c, _mk, _loai = UK.ket_noi(m)
        out, luong, loi = c.execute_ps(script)
    except UK.LoiMay as e:
        return False, str(e)
    except Exception as e:      # agent mat lien lac, het gio...
        return False, str(e)
    if loi and not (out or "").strip():
        return False, "; ".join(str(x) for x in getattr(luong, "error", [])) or "Lệnh báo lỗi."
    return True, out or ""


def _ps_dong_lenh(loai, lenh):
    b = _b64(lenh)
    doc = f"$c=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{b}'))"
    if loai == "cmd":
        return doc + "\n[Console]::OutputEncoding=[Text.Encoding]::UTF8\ncmd.exe /d /c $c 2>&1 | Out-String"
    return doc + "\n$ErrorActionPreference='Continue'\n& ([scriptblock]::Create($c)) 2>&1 | Out-String"


PS_DICH_VU = ("Get-CimInstance Win32_Service | Select-Object Name,DisplayName,State,StartMode,"
              "@{n='Mota';e={([string]$_.Description)}} | ConvertTo-Json -Compress")
PS_TIEN_TRINH = ("Get-Process | Select-Object Id,ProcessName,@{n='cpu';e={[math]::Round([double]$_.CPU,1)}},"
                 "@{n='mem';e={[math]::Round($_.WorkingSet64/1MB,1)}},@{n='tieude';e={[string]$_.MainWindowTitle}} | ConvertTo-Json -Compress")


def _json_ds(out):
    d = json.loads(out)
    return d if isinstance(d, list) else [d]


def _khung(m, tab, noi_dung):
    return T.khung_may(m, tab, noi_dung)


TRANG_TERM = r"""<div class="card"><h3>Cửa sổ dòng lệnh trực tiếp</h3>
<p class="tk-ghi">Mở CMD hoặc PowerShell chạy liên tục trên máy (quyền SYSTEM, qua agent), gõ lệnh và thấy kết quả ngay như đang ngồi trước máy. Cần máy có agent đang chạy. Đóng cửa sổ hoặc rời trang là tiến trình trên máy tự tắt.</p>
<div class="tk-hang"><button class="tk-nut chinh" type="button" data-tm="cmd">Mở CMD</button><button class="tk-nut chinh" type="button" data-tm="powershell">Mở PowerShell</button>
<button class="tk-nut do" type="button" id="tm-dong" disabled>Đóng</button><button class="tk-nut" type="button" id="tm-xoa">Xóa màn hình</button>
<a class="tk-nut" id="tm-lon" href="__LON__" target="_blank" rel="noopener" title="Mở cửa sổ dòng lệnh toàn màn hình ở tab mới">⛶ Mở cửa sổ lớn</a><span class="tk-ghi" id="tm-tt"></span></div>
<div id="tm-khung" style="margin-top:12px;background:#0c0c0c;border-radius:8px;border:1px solid var(--vien);overflow:hidden;">
<pre id="tm-ra" tabindex="0" style="margin:0;padding:12px 14px 4px;height:__CAO__;overflow:auto;white-space:pre-wrap;word-break:break-all;color:#cccccc;font:13.5px/1.45 Consolas,'Cascadia Mono',ui-monospace,monospace;background:transparent;"></pre>
<div style="display:flex;align-items:center;gap:6px;padding:4px 14px 10px;"><span style="color:#16c60c;font:13.5px Consolas,ui-monospace,monospace;">&gt;</span>
<input id="tm-vao" autocomplete="off" spellcheck="false" disabled placeholder="Bấm Mở CMD hoặc Mở PowerShell" style="flex:1;margin:0;height:30px;background:transparent;border:0;outline:0;color:#f2f2f2;font:13.5px Consolas,ui-monospace,monospace;box-shadow:none;"></div></div>
<p class="tk-ghi" style="margin-top:6px;">Enter: chạy · ↑/↓: lệnh trước/sau · lệnh cần trả lời (Y/N...) thì gõ câu trả lời rồi Enter. Lệnh chạy mãi (ping -t) thì bấm Đóng rồi mở lại.</p></div>
<script>(function(){var $=function(i){return document.getElementById(i);}, U='__URL__', ws=null, ls=[], vt=0, dec=null, ra=$('tm-ra'), vao=$('tm-vao');
function viet(t){ra.textContent+=t; if(ra.textContent.length>400000)ra.textContent=ra.textContent.slice(-300000); ra.scrollTop=ra.scrollHeight;}
function trangThai(mo,t){vao.disabled=!mo; $('tm-dong').disabled=!mo; document.querySelectorAll('[data-tm]').forEach(function(b){b.disabled=mo;}); $('tm-tt').textContent=t||''; if(mo)vao.focus();}
function mo(loai){if(ws)return; trangThai(false,'Đang mở '+(loai==='cmd'?'CMD':'PowerShell')+' trên máy...'); document.querySelectorAll('[data-tm]').forEach(function(b){b.disabled=true;});
 fetch(U,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({loai:loai})}).then(function(r){return r.json();}).then(function(d){
  if(!d.tok){trangThai(false,d.tb||'Không mở được.');return;}
  dec=new TextDecoder('utf-8'); ws=new WebSocket((location.protocol==='https:'?'wss://':'ws://')+location.host+'/uem-vnc-ws/'+d.tok,['binary']); ws.binaryType='arraybuffer';
  var daNoi=false, cho=setTimeout(function(){if(!daNoi)viet('\n[Đang chờ agent kết nối...]\n');},4000);
  ws.onmessage=function(e){if(!daNoi){daNoi=true;trangThai(true,'Đã kết nối - '+(loai==='cmd'?'CMD':'PowerShell'));} viet(typeof e.data==='string'?e.data:dec.decode(e.data,{stream:true}));};
  ws.onopen=function(){viet('[Đang mở '+(loai==='cmd'?'CMD':'PowerShell')+'...]\n');};
  ws.onclose=function(){clearTimeout(cho); ws=null; viet('\n[Đã đóng phiên]\n'); trangThai(false,'');};
 }).catch(function(){trangThai(false,'Không gọi được máy chủ.');});}
document.querySelectorAll('[data-tm]').forEach(function(b){b.onclick=function(){mo(b.dataset.tm);};});
$('tm-dong').onclick=function(){if(ws)ws.close();};
$('tm-xoa').onclick=function(){ra.textContent=''; if(!vao.disabled)vao.focus();};
$('tm-khung').onclick=function(){if(!vao.disabled && !getSelection().toString())vao.focus();};
vao.addEventListener('keydown',function(e){
 if(e.key==='Enter'){var l=vao.value; if(ws&&ws.readyState===1){ws.send(l+'\r\n'); if(l.trim()){ls.push(l);} vt=ls.length; viet(l+'\n');} vao.value=''; e.preventDefault();}
 else if(e.key==='ArrowUp'){if(vt>0){vt--;vao.value=ls[vt];} e.preventDefault();}
 else if(e.key==='ArrowDown'){if(vt<ls.length-1){vt++;vao.value=ls[vt];}else{vt=ls.length;vao.value='';} e.preventDefault();}});
window.addEventListener('pagehide',function(){if(ws)ws.close();});
var tu=new URLSearchParams(location.search).get('mo'); if(tu==='cmd'||tu==='powershell')mo(tu);
var giu=setInterval(function(){if(ws&&!document.body.contains(ra)){ws.close();clearInterval(giu);}},2000);
})();</script>"""

TRANG_DS = """<div class="card"><h3>__TIEUDE__</h3><div class="tk-hang"><input type="search" id="ds-loc" placeholder="Lọc theo tên..." style="margin:0;height:42px;max-width:300px;"><button class="tk-nut" id="ds-tai" type="button">Tải lại</button><span class="tk-ghi" id="ds-tt"></span></div>
<div class="uem-bang-cuon"><table class="tk-bang" id="ds-bang"></table></div></div>
<script>(function(){var $=function(i){return document.getElementById(i);}, U='__URL__', LOAI='__LOAI__', DS=[];
function e(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function ve(){var q=($('ds-loc').value||'').toLowerCase(), h='';
 if(LOAI==='dv'){h='<tr><th>Tên</th><th>Mô tả</th><th>Trạng thái</th><th>Khởi động</th><th></th></tr>';
  DS.filter(function(x){return !q||(x.Name+' '+x.DisplayName).toLowerCase().indexOf(q)>=0;}).forEach(function(x){
   var chay=x.State==='Running';
   h+='<tr><td><b>'+e(x.DisplayName||x.Name)+'</b><div class="tk-ghi">'+e(x.Name)+'</div></td><td class="tk-ghi">'+e((x.Mota||'').slice(0,120))+'</td><td><span class="tk-chip '+(chay?'xanh':'')+'">'+e(x.State)+'</span></td><td>'+e(x.StartMode)+'</td><td>'
   +(chay?'<button class="tk-nut" data-v="dung" data-n="'+e(x.Name)+'">Dừng</button> <button class="tk-nut" data-v="khoi_dong_lai" data-n="'+e(x.Name)+'">Khởi động lại</button>':'<button class="tk-nut xanh" data-v="chay" data-n="'+e(x.Name)+'">Chạy</button>')
   +' <select data-kd="'+e(x.Name)+'"><option value="">Kiểu khởi động...</option><option value="tu_dong">Tự động</option><option value="thu_cong">Thủ công</option><option value="tat">Tắt (Disabled)</option></select></td></tr>';});}
 else{h='<tr><th>PID</th><th>Tên</th><th>CPU (giây)</th><th>RAM (MB)</th><th>Cửa sổ</th><th></th></tr>';
  DS.filter(function(x){return !q||(x.ProcessName+' '+x.tieude).toLowerCase().indexOf(q)>=0;}).sort(function(a,b){return (b.mem||0)-(a.mem||0);}).forEach(function(x){
   h+='<tr><td>'+x.Id+'</td><td><b>'+e(x.ProcessName)+'</b></td><td>'+e(x.cpu)+'</td><td>'+e(x.mem)+'</td><td class="tk-ghi">'+e(x.tieude)+'</td><td><button class="tk-nut do" data-kill="'+x.Id+'" data-n="'+e(x.ProcessName)+'">Kết thúc</button></td></tr>';});}
 $('ds-bang').innerHTML=h;}
function goi(body){return fetch(U,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(function(r){return r.json();});}
function tai(){$('ds-tt').textContent='Đang tải...'; goi({viec:'ds'}).then(function(d){if(!d.ok){$('ds-tt').textContent='Lỗi: '+d.loi;return;} DS=d.ds; $('ds-tt').textContent=DS.length+' mục, '+new Date().toLocaleTimeString('vi-VN'); ve();}).catch(function(){$('ds-tt').textContent='Không gọi được máy chủ.';});}
function lam(b){$('ds-tt').textContent='Đang thực hiện...'; goi(b).then(function(d){$('ds-tt').textContent=d.ok?(d.tb||'Xong.'):('Lỗi: '+d.loi); tai();});}
$('ds-tai').onclick=tai; $('ds-loc').oninput=ve;
$('ds-bang').addEventListener('click',function(ev){var t=ev.target; if(t.dataset.v){ if(t.dataset.v==='dung'&&!confirm('Dừng dịch vụ '+t.dataset.n+'?'))return; lam({viec:t.dataset.v,ten:t.dataset.n}); }
 else if(t.dataset.kill){ if(!confirm('Kết thúc tiến trình '+t.dataset.n+' (PID '+t.dataset.kill+')? Dữ liệu chưa lưu có thể mất.'))return; lam({viec:'kill',pid:+t.dataset.kill}); }});
$('ds-bang').addEventListener('change',function(ev){var t=ev.target; if(t.dataset.kd&&t.value){ if(t.value==='tat'&&!confirm('Tắt hẳn dịch vụ '+t.dataset.kd+'?')){t.value='';return;} lam({viec:'khoi_dong',ten:t.dataset.kd,kieu:t.value}); }});
tai();})();</script>"""


def _term(m, cao):
    return TRANG_TERM.replace("__URL__", f"/uem/may/{m['id']}/cli/mo").replace("__LON__", f"/uem/may/{m['id']}/cli/lon").replace("__CAO__", cao)


def tab_cli(m):
    return _khung(m, "cli", _term(m, "68vh"))


# Cua so dong lenh rieng (tab moi, toan man hinh, khong co menu)
TRANG_LON = """<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TEN__ - Dòng lệnh</title><style>
:root{--vien:#2b3240;--chu-mo:#9aa4b2}html,body{margin:0;background:#0b0d10;color:#e6e9ee;font:14px system-ui,sans-serif;height:100%}
.card{padding:10px 14px;height:100%;box-sizing:border-box;display:flex;flex-direction:column}.card h3{margin:0 0 6px;font-size:16px}
.card>p.tk-ghi:first-of-type{display:none}.tk-ghi{color:var(--chu-mo);font-size:12.5px;margin:4px 0}
.tk-hang{display:flex;gap:8px;align-items:center;flex-wrap:wrap}#tm-lon{display:none}
.tk-nut{background:#1c222c;color:#e6e9ee;border:1px solid #333c4a;border-radius:8px;padding:7px 14px;cursor:pointer;font:inherit;text-decoration:none}
.tk-nut:hover{background:#252d39}.tk-nut.chinh{background:#2f6fdb;border-color:#2f6fdb}.tk-nut.do{color:#ff8a8a}.tk-nut:disabled{opacity:.45;cursor:default}
#tm-khung{flex:1;display:flex;flex-direction:column}#tm-ra{flex:1}
</style></head><body>__TERM__</body></html>"""


def trang_lon(m):
    ten = m.get("bi_danh") or m.get("ten") or m.get("ip", "")
    return TRANG_LON.replace("__TEN__", _esc(ten)).replace("__TERM__", _term(m, "auto").replace(
        "<h3>Cửa sổ dòng lệnh trực tiếp</h3>", "<h3>Dòng lệnh: " + _esc(ten) + "</h3>"))


def tab_dich_vu(m):
    return _khung(m, "dich-vu", TRANG_DS.replace("__TIEUDE__", "Dịch vụ Windows (Services)").replace("__URL__", f"/uem/may/{m['id']}/dich-vu/api").replace("__LOAI__", "dv"))


def tab_tien_trinh(m):
    return _khung(m, "tien-trinh", TRANG_DS.replace("__TIEUDE__", "Tiến trình (Task Manager)").replace("__URL__", f"/uem/may/{m['id']}/tien-trinh/api").replace("__LOAI__", "tt"))


def chay_dong_lenh(m, loai, lenh):
    if loai not in ("ps", "cmd") or not lenh.strip() or len(lenh) > 8000:
        return False, "Lệnh trống hoặc quá dài (tối đa 8000 ký tự)."
    ok, out = _chay(m, _ps_dong_lenh(loai, lenh))
    UD.ghi_tac_vu(m["id"], "tu_xa", ("CMD: " if loai == "cmd" else "PowerShell: ") + lenh.strip().splitlines()[0][:80], ok, (out if ok else out)[:200])
    return ok, out[:200000]


def viec_dich_vu(m, j):
    viec = j.get("viec")
    if viec == "ds":
        ok, out = _chay(m, PS_DICH_VU)
        if not ok:
            return {"ok": False, "loi": out}
        try:
            return {"ok": True, "ds": _json_ds(out)}
        except ValueError:
            return {"ok": False, "loi": "Không đọc được danh sách dịch vụ từ máy."}
    ten = str(j.get("ten", ""))
    if not MAU_DICH_VU.fullmatch(ten):
        return {"ok": False, "loi": "Tên dịch vụ không hợp lệ."}
    q = "'" + ten.replace("'", "''") + "'"
    if viec == "chay":
        sc, nhan = f"Start-Service -Name {q} -ErrorAction Stop; 'OK'", "Chạy"
    elif viec == "dung":
        sc, nhan = f"Stop-Service -Name {q} -Force -ErrorAction Stop; 'OK'", "Dừng"
    elif viec == "khoi_dong_lai":
        sc, nhan = f"Restart-Service -Name {q} -Force -ErrorAction Stop; 'OK'", "Khởi động lại"
    elif viec == "khoi_dong" and j.get("kieu") in KIEU_KHOI_DONG:
        sc, nhan = f"Set-Service -Name {q} -StartupType {KIEU_KHOI_DONG[j['kieu']]} -ErrorAction Stop; 'OK'", "Đặt kiểu khởi động " + j["kieu"]
    else:
        return {"ok": False, "loi": "Yêu cầu không hợp lệ."}
    ok, out = _chay(m, sc)
    ok = ok and "OK" in out
    UD.ghi_tac_vu(m["id"], "tu_xa", f"Dịch vụ {ten}: {nhan}", ok, out[:200])
    return {"ok": ok, "tb": f"{nhan} {ten}: xong.", "loi": out[:300]}


def viec_tien_trinh(m, j):
    viec = j.get("viec")
    if viec == "ds":
        ok, out = _chay(m, PS_TIEN_TRINH)
        if not ok:
            return {"ok": False, "loi": out}
        try:
            return {"ok": True, "ds": _json_ds(out)}
        except ValueError:
            return {"ok": False, "loi": "Không đọc được danh sách tiến trình từ máy."}
    if viec == "kill":
        pid = j.get("pid")
        if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 4:
            return {"ok": False, "loi": "PID không hợp lệ."}
        ok, out = _chay(m, f"Stop-Process -Id {pid} -Force -ErrorAction Stop; 'OK'")
        ok = ok and "OK" in out
        UD.ghi_tac_vu(m["id"], "tu_xa", f"Kết thúc tiến trình PID {pid}", ok, out[:200])
        return {"ok": ok, "tb": f"Đã kết thúc PID {pid}.", "loi": out[:300]}
    return {"ok": False, "loi": "Yêu cầu không hợp lệ."}


def register_dieukhien(app):
    @app.route("/uem/may/<mid>/cli/chay", methods=["POST"])
    def uem_cli_chay(mid):
        m = may_theo_id(mid)
        j = request.get_json(silent=True) or {}
        ok, out = chay_dong_lenh(m, str(j.get("loai", "ps")), str(j.get("lenh", "")))
        return jsonify({"ok": ok, "out": out if ok else "", "loi": "" if ok else out})

    @app.route("/uem/may/<mid>/cli/lon")
    def uem_cli_lon(mid):
        return trang_lon(may_theo_id(mid))

    @app.route("/uem/may/<mid>/cli/mo", methods=["POST"])
    def uem_cli_mo(mid):
        from ui import uem_vnc as UV
        m = may_theo_id(mid)
        tok, tb = UV.mo_phien_shell(m["id"], str((request.get_json(silent=True) or {}).get("loai", "cmd")))
        return jsonify({"tok": tok, "tb": tb})

    @app.route("/uem/may/<mid>/dich-vu/api", methods=["POST"])
    def uem_dich_vu_api(mid):
        return jsonify(viec_dich_vu(may_theo_id(mid), request.get_json(silent=True) or {}))

    @app.route("/uem/may/<mid>/tien-trinh/api", methods=["POST"])
    def uem_tien_trinh_api(mid):
        return jsonify(viec_tien_trinh(may_theo_id(mid), request.get_json(silent=True) or {}))
