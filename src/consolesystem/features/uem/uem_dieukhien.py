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


TRANG_CLI = """<div class="card"><h3>Dòng lệnh từ xa</h3>
<p class="tk-ghi">Chạy lệnh CMD hoặc PowerShell trên máy với quyền hệ thống (SYSTEM qua agent). Kết quả trả về sau khi lệnh chạy xong (tối đa 60 giây). Lệnh nào cũng được ghi vào tab Tác vụ.</p>
<div class="tk-f"><label>Kiểu</label><select id="cli-loai" style="max-width:200px;"><option value="ps">PowerShell</option><option value="cmd">CMD</option></select>
<label>Lệnh</label><textarea id="cli-lenh" rows="4" style="width:100%;font-family:monospace;" placeholder="ví dụ: Get-Service | Where Status -eq Running   hoặc   ipconfig /all"></textarea>
<div class="tk-hang" style="margin-top:10px;"><button class="tk-nut chinh" id="cli-chay" type="button">Chạy lệnh</button><button class="tk-nut" id="cli-xoa" type="button">Xóa kết quả</button><span class="tk-ghi" id="cli-tt"></span></div></div>
<pre id="cli-kq" style="background:#0f1114;color:#d5dae2;padding:12px;border-radius:6px;min-height:120px;max-height:60vh;overflow:auto;white-space:pre-wrap;word-break:break-all;margin-top:12px;"></pre></div>
<script>(function(){var $=function(i){return document.getElementById(i);}, U='__URL__';
$('cli-xoa').onclick=function(){$('cli-kq').textContent='';};
$('cli-lenh').addEventListener('keydown',function(e){if(e.ctrlKey&&e.key==='Enter'){$('cli-chay').click();}});
$('cli-chay').onclick=function(){var l=$('cli-lenh').value; if(!l.trim())return; var b=$('cli-chay'); b.disabled=true; $('cli-tt').textContent='Đang chạy...';
 fetch(U,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({loai:$('cli-loai').value,lenh:l})}).then(function(r){return r.json();}).then(function(d){
  $('cli-kq').textContent+=(d.ok?'':'[LỖI] ')+(d.out||d.loi||'(không có kết quả)')+'\\n'; $('cli-tt').textContent=''; $('cli-kq').scrollTop=1e9;}).catch(function(){$('cli-tt').textContent='Không gọi được máy chủ.';}).then(function(){b.disabled=false;});};})();</script>"""

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


def tab_cli(m):
    return _khung(m, "cli", TRANG_CLI.replace("__URL__", f"/uem/may/{m['id']}/cli/chay"))


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

    @app.route("/uem/may/<mid>/dich-vu/api", methods=["POST"])
    def uem_dich_vu_api(mid):
        return jsonify(viec_dich_vu(may_theo_id(mid), request.get_json(silent=True) or {}))

    @app.route("/uem/may/<mid>/tien-trinh/api", methods=["POST"])
    def uem_tien_trinh_api(mid):
        return jsonify(viec_tien_trinh(may_theo_id(mid), request.get_json(silent=True) or {}))
