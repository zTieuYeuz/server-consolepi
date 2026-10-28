# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Quan ly may tram (UEM) - GIAO DIEN CHINH: khung, Tong quan (Dashboard), Danh sach may, Chi tiet may (cac tab).
Mo phong menu Dashboard / Computers cua OpenUEM; cac muc con lai o uem_trang_b.py. Du lieu: uem_dulieu.py, thu thap: uem_baocao.py.
"""
import sys as _sys
_sys.modules["ui.uem_trang"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import html
import json
import re
import time
from datetime import datetime

from flask import abort, jsonify, redirect, request, send_file, session

from ui import tk_dongco as DC
from ui import tk_dulieu as DL
from ui import uem_baocao as UBC
from ui import uem_buoc as UB
from ui import uem_agent as UA
from ui import uem_dulieu as UD
from ui import uem_trienkhai as UT
from ui import uem_winget as UW
from ui.layout import render_page, svg_icon
from consolesystem.core.esc import esc_html as _esc
from consolesystem.web.css_tk import CSS as _CSS_TK
from consolesystem.web import chon_may as _CM




TABS = [("tq", "Tổng quan", "/uem"), ("may", "Máy tính", "/uem/may"), ("pm", "Phần mềm đã cài", "/uem/phan-mem"), ("bm", "Bảo mật", "/uem/bao-mat"),
        ("td", "Cài phần mềm qua Agent", "/uem/trien-khai"), ("pf", "Cấu hình (Profiles)", "/uem/profiles"), ("bc", "Báo cáo", "/uem/bao-cao"),
        ("qt", "Quản trị", "/uem/quan-tri")]

CSS = """
<style>
.uem-luoi { display:grid; grid-template-columns:repeat(auto-fill,minmax(210px,1fr)); gap:12px; margin:8px 0 18px; }
.uem-the { border:1px solid var(--vien); background:var(--the); border-radius:14px; padding:16px 18px; display:block; color:var(--chu); transition:transform .5s var(--muot), border-color .3s var(--muot); }
a.uem-the:hover { border-color:var(--nhan); color:var(--chu); transform:translateY(-2px); }
.uem-the .so { font:600 30px var(--mono); letter-spacing:-.03em; display:block; line-height:1.1; }
.uem-the .nhan { color:var(--chu-mo); font-size:13.5px; margin-top:6px; display:block; }
.uem-the.do .so { color:var(--do); } .uem-the.vang .so { color:var(--vang); } .uem-the.xanh .so { color:var(--xanh); }
.uem-bieu { border:1px solid var(--vien); background:var(--the); border-radius:14px; padding:16px 18px; }
.uem-bieu h3 { margin:0 0 12px; font-size:15px; }
.uem-cot { display:grid; grid-template-columns:minmax(80px,200px) 1fr 40px; gap:10px; align-items:center; font-size:13px; margin:7px 0; }
.uem-cot span.t { color:var(--chu-mo); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.uem-cot .v { height:10px; background:var(--vien-ro); border-radius:6px; overflow:hidden; } .uem-cot .v i { display:block; height:100%; background:var(--nhan); border-radius:6px; }
.uem-cot b { text-align:right; font-family:var(--mono); }
.uem-2 { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr)); gap:14px; margin-bottom:18px; }
.uem-dau { display:flex; gap:16px; align-items:center; flex-wrap:wrap; margin:0 0 6px; }
.uem-dau h2 { margin:0; font-size:22px; }
.uem-con { display:flex; gap:4px; flex-wrap:wrap; margin:10px 0 16px; padding:4px; border:1px solid var(--vien); background:var(--the); border-radius:12px; }
.uem-con a { padding:0 12px; height:36px; line-height:36px; border-radius:8px; color:var(--chu-mo); font-weight:550; font-size:13.5px; white-space:nowrap; }
.uem-con a:hover { background:var(--hang-nen); color:var(--chu); } .uem-con a.on { background:var(--nhan-mo); color:var(--nhan); }
.uem-con.con2 { margin-top:-8px; border-top-left-radius:4px; border-top-right-radius:4px; background:transparent; }
.uem-con.con2 a { height:32px; line-height:32px; font-size:13px; }
.uem-kv { width:100%; border-collapse:collapse; } .uem-kv th { text-align:left; width:170px; color:var(--chu-mo2); font-weight:500; font-size:13.5px; padding:9px 12px 9px 0; vertical-align:top; }
.uem-kv td { padding:9px 0; font-size:14.5px; border-bottom:1px solid var(--vien); } .uem-kv tr:last-child td { border-bottom:0; }
.uem-loc { display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin:0 0 12px; }
.uem-loc input[type=text], .uem-loc select, .tk-hang select, .tk-hang input[type=text] { margin:0; height:40px; width:auto; min-width:170px; max-width:300px; }
.uem-trang { display:flex; gap:6px; align-items:center; justify-content:flex-end; margin:10px 0 0; font-size:13px; color:var(--chu-mo); flex-wrap:wrap; }
.uem-trang button { height:34px; min-height:34px; padding:0 12px; border-radius:8px; border:1px solid var(--vien-ro); background:transparent; color:var(--chu); cursor:pointer; font:550 13px var(--chu-font); }
.uem-trang button:disabled { opacity:.4; cursor:default; } .uem-trang button.on { background:var(--nhan-mo); border-color:var(--nhan); color:var(--nhan); }
.uem-dot { display:inline-block; width:9px; height:9px; border-radius:50%; background:var(--chu-mo2); margin-right:6px; }
.uem-dot.xanh { background:var(--xanh); } .uem-dot.do { background:var(--do); } .uem-dot.vang { background:var(--vang); }
.uem-tag { display:inline-block; padding:2px 9px; border-radius:99px; font-size:12px; font-weight:600; color:#fff; margin:1px 3px 1px 0; }
.uem-ghi { white-space:pre-wrap; line-height:1.6; }
.uem-bang-cuon { overflow:auto; }
.uem-duong { display:flex; gap:4px; flex-wrap:wrap; align-items:center; margin:0 0 12px; font-size:14px; }
.uem-duong a { padding:4px 8px; border-radius:6px; background:var(--hang-nen); }
@media (max-width:760px) { .uem-kv th { width:120px; } .uem-cot { grid-template-columns:90px 1fr 34px; } }
</style>
"""

JS_BANG = """
<script>
(function(){
  function khoi(b){
    var tr=Array.prototype.slice.call(b.querySelectorAll('tbody tr, table tr[data-t]')).filter(function(r){return r.hasAttribute('data-t');});
    var per=parseInt(b.getAttribute('data-trang')||'15',10), trang=1, tim=b.querySelector('.uem-tim'), sels=b.querySelectorAll('.uem-chon');
    var ctl=document.createElement('div'); ctl.className='uem-trang'; b.appendChild(ctl);
    var dem=b.querySelector('.uem-dem');
    function hien(){
      var q=(tim?tim.value:'').toLowerCase().trim(), ds=tr.filter(function(r){
        if(q && r.getAttribute('data-t').indexOf(q)<0) return false;
        for(var i=0;i<sels.length;i++){ var s=sels[i], v=s.value; if(v && (r.getAttribute('data-'+s.getAttribute('data-k'))||'').split('|').indexOf(v)<0) return false; }
        return true; });
      var tong=Math.max(1,Math.ceil(ds.length/per)); if(trang>tong) trang=tong;
      tr.forEach(function(r){r.style.display='none';}); ds.slice((trang-1)*per, trang*per).forEach(function(r){r.style.display='';});
      if(dem) dem.textContent=ds.length+' / '+tr.length;
      ctl.textContent=''; if(tong<=1) return;
      function nut(t,p,on,dis){ var x=document.createElement('button'); x.type='button'; x.textContent=t; if(on)x.className='on'; x.disabled=!!dis; x.onclick=function(){trang=p;hien();}; ctl.appendChild(x); }
      nut('‹ Trước',trang-1,false,trang<=1); var a=Math.max(1,trang-2), z=Math.min(tong,trang+2);
      if(a>1){nut('1',1,false);} for(var i=a;i<=z;i++) nut(String(i),i,i===trang); if(z<tong){nut(String(tong),tong,false);} nut('Sau ›',trang+1,false,trang>=tong);
    }
    if(tim) tim.addEventListener('input',function(){trang=1;hien();}); sels.forEach(function(s){s.addEventListener('change',function(){trang=1;hien();});}); hien();
  }
  document.querySelectorAll('.uem-ds').forEach(khoi);
})();
</script>
"""


def tabs_uem(chinh):
    return '<div class="dep-tabs">' + "".join(f'<a href="{h}" class="dep-tab{" on" if m == chinh else ""}">{n}</a>' for m, n, h in TABS) + "</div>"


def tb():
    return session.pop("uem_tb", None)


def chuyen(url, thong_bao, ok=True):
    session["uem_tb"] = [str(thong_bao)[:600], bool(ok)]
    return redirect(url)


def trang(body, chinh, tieu_de="Quản lý máy trạm", phu_de="Kiểm kê, bảo mật, triển khai và cấu hình máy Windows trong mạng (theo mô hình OpenUEM)"):
    t = tb()
    thong = f'<div class="msg {"ok" if t[1] else "err"}">{_esc(t[0])}</div>' if t else ""
    canh = ""
    if not DC.co_san():
        canh = ('<div class="msg warn">Chưa cài thư viện WinRM: chạy <code>sudo bash /opt/console-pi/tools/cai-winrm.sh</code> trong Terminal '
                "của Console System rồi tải lại trang.</div>")
    if chinh == "td":                       # menu "Trien khai phan mem": tab WinGet (trang nay) + tab Trien khai phan mem (WinRM)
        body = _CM.thanh_tab(_CM.TAB_TRIEN_KHAI, "winget") + body
    return render_page(_CSS_TK + CSS + thong + canh + body + JS_BANG, active=next((h for m_, _n, h in TABS if m_ == chinh), "/uem"), title=tieu_de, subtitle=phu_de)


# ----------------------------------------------------------------- tien ich du lieu
def iso_gio(s):
    if not s:
        return "—"
    try:
        return datetime.fromisoformat(str(s).replace("Z", "")).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return str(s)


def gio(ts):
    return DL.dinh_dang_gio(ts) or "—"


def bc(m):
    """Bao cao cua may, GOP them du lieu 'tro ly phien nguoi dung' cua agent (may in rieng, man hinh, nguoi dang nhap) neu co."""
    r = m.get("bao_cao") or {}
    nd = m.get("phien_nd")
    if not r or not nd:
        return r
    r = dict(r)
    ten = {p.get("name") for p in r.get("printers", [])}
    r["printers"] = list(r.get("printers", [])) + [p for p in nd.get("printers", []) if p.get("name") not in ten]
    if not r.get("monitors") and nd.get("monitors"):
        r["monitors"] = nd["monitors"]
    hdh = dict(r.get("operatingsystem") or {})
    if not hdh.get("username") and nd.get("user"):
        hdh["username"] = nd["user"]
        r["operatingsystem"] = hdh
    return r


def ten_may(m):
    return m.get("bi_danh") or (bc(m).get("hostname")) or m.get("ten") or m["ip"]


def trang_thai_may(m):
    """(nhan, mau) tong hop: vo hieu / chua gan tai khoan / khong ket noi / dang giam sat."""
    if not m.get("giam_sat", True):
        return "Vô hiệu", ""
    if not m.get("tai_khoan_id") and not (m.get("agent") or {}).get("khoa"):
        return "Chờ gán tài khoản", "vang"
    kn = m.get("ket_noi") or {}
    # Lan lay bao cao cuoi loi (vd may tat) nhung agent dang bao nhip -> may dang noi, khong bao "Khong ket noi"
    # (lab 28/10/2026: LaptopHome mo lai, remote binh thuong ma trang van do vai phut cho toi lan lay bao cao ke).
    if kn and not kn.get("ok") and not UA.con_song(m):
        return "Không kết nối", "do"
    if not m.get("bao_cao_luc"):
        return "Chưa có báo cáo", "vang"
    chu_ky = max(5, int(UD.cai_dat().get("tan_suat_bao_cao", 60))) * 60
    if time.time() - m["bao_cao_luc"] > chu_ky * 3 + 600:
        return "Quá hạn báo cáo", "vang"
    return "Đang giám sát", "xanh"


def the_html(m, ds_the=None):
    ds_the = ds_the if ds_the is not None else UD.THE.doc()
    return "".join(f'<span class="uem-tag" style="background:{_esc(t.get("mau") or "#6366f1")}">{_esc(t["ten"])}</span>'
                   for t in ds_the if t["id"] in m.get("the", []))


class Raw(str):
    """Chuoi HTML da tin cay (do code tao). bang()/kv() CHI khong escape khi la Raw - du lieu nguoi dung bat dau bang '<' van bi escape."""


def chip(txt, mau=""):
    return Raw(f'<span class="tk-chip {mau}">{_esc(txt)}</span>')


def co_khong(v, ok="Có", sai="Không"):
    return chip(ok, "xanh") if v else chip(sai, "do")


def don_vi_gb(s):
    """'237 GB' -> 237.0 (de sap xep / canh bao)."""
    m = re.match(r"([\d.]+)\s*(MB|GB|TB|PB)", str(s or ""))
    if not m:
        return 0.0
    return float(m.group(1)) * {"MB": 0.001, "GB": 1, "TB": 1000, "PB": 1000000}[m.group(2)]


def dem_theo(ds, khoa):
    d = {}
    for x in ds:
        k = khoa(x) or "(không rõ)"
        d[k] = d.get(k, 0) + 1
    return sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))


def bieu_cot(tieu_de, ds, tong=None):
    if not ds:
        return f'<div class="uem-bieu"><h3>{_esc(tieu_de)}</h3><p class="tk-ghi">Chưa có dữ liệu.</p></div>'
    tong = tong or max(1, max(v for _, v in ds))
    hang = "".join(f'<div class="uem-cot"><span class="t" title="{_esc(k)}">{_esc(k)}</span><div class="v"><i style="width:{int(v * 100 / tong)}%"></i></div><b>{v}</b></div>'
                   for k, v in ds[:8])
    return f'<div class="uem-bieu"><h3>{_esc(tieu_de)}</h3>{hang}</div>'


def may_theo_id(mid):
    m = DL.tim(DL.MAY.doc(), mid)
    if not m:
        abort(404)
    return m


# ----------------------------------------------------------------- tong quan
def _so_lieu():
    ds = DL.MAY.doc()
    gs = [m for m in ds if m.get("giam_sat", True)]
    cd = UD.cai_dat()
    now = time.time()
    r = {"tong": len(ds), "giam_sat": len(gs), "vo_hieu": len(ds) - len(gs)}
    r["cho_gan"] = sum(1 for m in gs if not m.get("tai_khoan_id"))
    r["online"] = sum(1 for m in gs if (m.get("ket_noi") or {}).get("ok") and now - (m.get("ket_noi") or {}).get("luc", 0) < 3 * max(5, int(cd.get("tan_suat_bao_cao", 60))) * 60 + 600)
    r["khong_bao_cao_24h"] = sum(1 for m in gs if m.get("tai_khoan_id") and now - m.get("bao_cao_luc", 0) > 86400)
    co = [m for m in gs if bc(m)]
    r["cap_nhat_cho"] = sum(1 for m in co if (bc(m).get("systemupdate") or {}).get("pending_updates"))
    r["av_tat"] = sum(1 for m in co if not (bc(m).get("antivirus") or {}).get("is_active"))
    r["av_cu"] = sum(1 for m in co if (bc(m).get("antivirus") or {}).get("is_active") and not (bc(m).get("antivirus") or {}).get("is_updated"))
    r["khong_tu_cap_nhat"] = sum(1 for m in co if str((bc(m).get("systemupdate") or {}).get("status", "")) in ("0", "1", ""))
    r["tuong_lua_tat"] = sum(1 for m in co if any(not x.get("bat") for x in (bc(m).get("firewall") or [])))
    r["bitlocker"] = sum(1 for m in co if any(d.get("bitlocker_status") == "Unencrypted" and d.get("label") == "C:" for d in bc(m).get("logicaldisks", [])))
    r["o_day"] = sum(1 for m in co if any(d.get("usage", 0) >= 90 for d in bc(m).get("logicaldisks", [])))
    r["smb1"] = sum(1 for m in co if str(bc(m).get("smb1", "")).lower() == "enabled")
    pm = {}
    for m in co:
        for a in bc(m).get("applications", []):
            pm.setdefault(a["name"], set()).add(m["id"])
    r["agent"] = sum(1 for m in ds if UA.con_song(m))
    r["so_phan_mem"] = len(pm)
    r["top_pm"] = sorted(((k, len(v)) for k, v in pm.items()), key=lambda kv: (-kv[1], kv[0]))[:10]
    r["may_in"] = len({p["name"] for m in co for p in bc(m).get("printers", [])})
    r["hang"] = len({(bc(m).get("computer") or {}).get("manufacturer") for m in co if (bc(m).get("computer") or {}).get("manufacturer")})
    r["nguoi_dung"] = len({(bc(m).get("operatingsystem") or {}).get("username") for m in co if (bc(m).get("operatingsystem") or {}).get("username")})
    r["the"] = len({t for m in gs for t in m.get("the", [])})
    r["trien_khai"] = len(UD.TRIEN_KHAI.doc())
    r["profile_loi"] = 0
    for p in UD.PROFILES.doc():
        from ui import uem_profiles as UP
        r["profile_loi"] += len({m["id"] for m, _t, _tb in UP.van_de(p["id"])})
    r["theo_os"] = dem_theo(co, lambda m: (bc(m).get("operatingsystem") or {}).get("description", "").replace("Microsoft ", ""))
    r["theo_build"] = dem_theo(co, lambda m: (bc(m).get("operatingsystem") or {}).get("version", ""))
    r["theo_hang"] = dem_theo(co, lambda m: (bc(m).get("computer") or {}).get("manufacturer", ""))
    r["theo_av"] = dem_theo(co, lambda m: (bc(m).get("antivirus") or {}).get("name", "") or "Không có")
    return r


def trang_tong_quan():
    r = _so_lieu()

    def the(so, nhan, mau="", href=None):
        tag = "a" if href else "div"
        h = f' href="{href}"' if href else ""
        return f'<{tag} class="uem-the {mau}"{h}><span class="so">{so}</span><span class="nhan">{_esc(nhan)}</span></{tag}>'
    canh = "".join([
        the(r["cap_nhat_cho"], "Máy có cập nhật Windows đang chờ", "vang" if r["cap_nhat_cho"] else "xanh", "/uem/bao-mat/cap-nhat"),
        the(r["av_tat"], "Máy diệt virus đang tắt", "do" if r["av_tat"] else "xanh", "/uem/bao-mat"),
        the(r["av_cu"], "Diệt virus cơ sở dữ liệu cũ", "vang" if r["av_cu"] else "xanh", "/uem/bao-mat"),
        the(r["khong_tu_cap_nhat"], "Máy không bật tự động cập nhật", "vang" if r["khong_tu_cap_nhat"] else "xanh", "/uem/bao-mat/cap-nhat"),
        the(r["tuong_lua_tat"], "Máy có tường lửa tắt (một profile)", "vang" if r["tuong_lua_tat"] else "xanh", "/uem/bao-mat"),
        the(r["bitlocker"], "Ổ C chưa mã hóa BitLocker", "vang" if r["bitlocker"] else "xanh", "/uem/bao-mat"),
        the(r["o_day"], "Máy có ổ đĩa đầy từ 90%", "do" if r["o_day"] else "xanh", "/uem/may"),
        the(r["smb1"], "Máy còn bật SMB1 (không an toàn)", "do" if r["smb1"] else "xanh", "/uem/bao-mat"),
        the(r["profile_loi"], "Máy có tác vụ profile lỗi", "do" if r["profile_loi"] else "xanh", "/uem/profiles"),
        the(r["khong_bao_cao_24h"], "Máy không báo cáo trong 24 giờ", "vang" if r["khong_bao_cao_24h"] else "xanh", "/uem/may")])
    tk = "".join([the(r["tong"], "Tổng số máy", "", "/uem/may"), the(r["giam_sat"], "Đang giám sát", "xanh", "/uem/quan-tri/may"),
                  the(r["online"], "Kết nối được gần đây", "xanh"), the(r["cho_gan"], "Chờ gán tài khoản", "vang" if r["cho_gan"] else "", "/uem/quan-tri/may"),
                  the(r["vo_hieu"], "Đã vô hiệu", "", "/uem/quan-tri/may"), the(r["so_phan_mem"], "Phần mềm khác nhau", "", "/uem/phan-mem"),
                  the(r["trien_khai"], "Lượt triển khai đã chạy", "", "/uem/trien-khai/lich-su"), the(r["may_in"], "Máy in khác nhau"),
                  the(r["agent"], "Máy có agent đang chạy", "xanh" if r["agent"] else "", "/uem/quan-tri/agent"), the(r["hang"], "Hãng máy khác nhau"), the(r["nguoi_dung"], "Người dùng Windows"), the(r["the"], "Thẻ đang dùng", "", "/uem/quan-tri/the")])
    top = bieu_cot("10 phần mềm cài trên nhiều máy nhất", r["top_pm"], max([v for _, v in r["top_pm"]] or [1]))
    body = f"""
    <h2>Cảnh báo</h2><div class="uem-luoi">{canh}</div>
    <h2>Thống kê</h2><div class="uem-luoi">{tk}</div>
    <div class="uem-2">{bieu_cot("Theo hệ điều hành", r["theo_os"], r["giam_sat"])}{bieu_cot("Theo phiên bản Windows", r["theo_build"], r["giam_sat"])}
      {bieu_cot("Theo hãng máy", r["theo_hang"], r["giam_sat"])}{bieu_cot("Theo phần mềm diệt virus", r["theo_av"], r["giam_sat"])}{top}</div>
    <p class="tk-ghi">Số liệu lấy từ báo cáo định kỳ của từng máy (mặc định {int(UD.cai_dat().get('tan_suat_bao_cao', 60))} phút một lần, đổi ở Quản trị, Cài đặt chung).
      Chưa có số liệu? Vào <a href="/uem/quan-tri/may">Quản trị, Máy được giám sát</a>, gán tài khoản cho máy rồi bấm Lấy thông tin.</p>"""
    return trang(body, "tq")


# ----------------------------------------------------------------- danh sach may
def trang_may():
    ds = [m for m in DL.MAY.doc() if UA.co_agent(m)]                # Console chi quan ly may DA CAI agent (may chua cai: chi Trien khai phan mem dung qua WinRM)
    the_ds = UD.THE.doc()
    dd = UD.DIA_DIEM.doc()
    tk = DL.tai_khoan_cong_khai()
    nhom_ds = DL.NHOM_MAY.doc()
    hang = ""
    for m in ds:
        if m.get("an"):
            continue                                     # da xoa khoi quan ly (may co agent), tu hien lai khi agent bao nhip
        r = bc(m)
        cs, os_, usr = r.get("computer") or {}, r.get("operatingsystem") or {}, (r.get("operatingsystem") or {}).get("username", "")
        nhan, mau = trang_thai_may(m)
        av = r.get("antivirus") or {}
        loc_t = "|".join(m.get("the", []))
        tim = " ".join([ten_may(m), m["ip"], os_.get("description", ""), cs.get("model", ""), cs.get("manufacturer", ""), usr, m.get("ghi_chu", "")]).lower()
        dia = DL.tim(dd, m.get("dia_diem"))
        ng = [g for g in nhom_ds if m["id"] in g.get("may", [])]
        nhom_chip = "".join(f'<span class="uem-tag" style="background:#475569">{_esc(g["ten"])}</span>' for g in ng)
        hang += (f'<tr data-nhom="{_esc("|".join(g["id"] for g in ng))}" data-t="{_esc(tim)}" data-os="{_esc(os_.get("description", ""))}" data-hang="{_esc(cs.get("manufacturer", ""))}" data-the="{_esc(loc_t)}" '
                 f'data-tt="{_esc(nhan)}" data-dd="{_esc(m.get("dia_diem", ""))}">'
                 f'<td><input type="checkbox" name="may" value="{m["id"]}" form="f-hd"></td>'
                 f'<td><a href="/uem/may/{m["id"]}"><b>{_esc(ten_may(m))}</b></a><div class="tk-ghi">{_esc(m["ip"])}{" · " + _esc(dia["ten"]) if dia else ""}</div>{nhom_chip}{the_html(m, the_ds)}</td>'
                 f'<td>{_esc(os_.get("description", "").replace("Microsoft ", "")) or "—"}<div class="tk-ghi">{_esc(os_.get("version", ""))}</div></td>'
                 f'<td>{_esc(cs.get("manufacturer", "")) or "—"}<div class="tk-ghi">{_esc(cs.get("model", ""))}</div></td>'
                 f'<td>{_esc(usr) or "—"}</td>'
                 f'<td>{chip(av.get("name") or "Không có", "xanh" if av.get("is_active") else "do") if r else "—"}</td>'
                 f'<td><span class="uem-dot {mau}"></span>{_esc(nhan)}<div class="tk-ghi">{_esc(gio(m.get("bao_cao_luc")))}</div></td></tr>')
    os_opt = "".join(f'<option value="{_esc(k)}">{_esc(k)}</option>' for k, _ in dem_theo([m for m in ds if bc(m)], lambda m: (bc(m).get("operatingsystem") or {}).get("description", "")))
    hang_opt = "".join(f'<option value="{_esc(k)}">{_esc(k)}</option>' for k, _ in dem_theo([m for m in ds if bc(m)], lambda m: (bc(m).get("computer") or {}).get("manufacturer", "")))
    nhom_opt = "".join(f'<option value="{g["id"]}">{_esc(g["ten"])} ({len(g.get("may", []))})</option>' for g in nhom_ds)
    the_opt = "".join(f'<option value="{t["id"]}">{_esc(t["ten"])}</option>' for t in the_ds)
    dd_opt = "".join(f'<option value="{d["id"]}">{_esc(d["ten"])}</option>' for d in dd)
    tt_opt = "".join(f'<option value="{x}">{x}</option>' for x in ("Đang giám sát", "Không kết nối", "Chờ gán tài khoản", "Chưa có báo cáo", "Quá hạn báo cáo", "Vô hiệu"))
    tk_opt = "".join(f'<option value="{t["id"]}">{_esc(t["ten"])} ({_esc(t["user"])})</option>' for t in tk)
    bang = (f'''<div class="uem-ds" data-trang="15"><div class="uem-loc"><input type="text" class="uem-tim" placeholder="Tìm tên, IP, người dùng, model...">
      <select class="uem-chon" data-k="nhom"><option value="">Mọi nhóm máy</option>{nhom_opt}</select>
      <select class="uem-chon" data-k="os"><option value="">Mọi hệ điều hành</option>{os_opt}</select>
      <select class="uem-chon" data-k="hang"><option value="">Mọi hãng</option>{hang_opt}</select>
      <select class="uem-chon" data-k="the"><option value="">Mọi thẻ</option>{the_opt}</select>
      <select class="uem-chon" data-k="dd"><option value="">Mọi địa điểm</option>{dd_opt}</select>
      <select class="uem-chon" data-k="tt"><option value="">Mọi trạng thái</option>{tt_opt}</select>
      <span class="tk-ghi"><b class="uem-dem"></b> máy</span></div>
      <div class="uem-bang-cuon"><table class="tk-bang"><thead><tr><th></th><th>Máy</th><th>Hệ điều hành</th><th>Hãng / model</th><th>Người dùng</th><th>Diệt virus</th><th>Trạng thái</th></tr></thead>
      <tbody>{hang}</tbody></table></div></div>''' if ds else '<p class="tk-ghi">Chưa có máy nào cài agent. Máy chỉ hiện ở đây sau khi cài agent: tạo gói cài ở <a href="/uem/quan-tri/agent">Quản trị, Agent</a> rồi chạy trên máy (hoặc triển khai bằng Triển khai phần mềm).</p>')
    body = f"""
    <div class="tk-ghi" style="margin-bottom:8px;">Chỉ máy <b>đã cài agent</b> mới hiện ở đây; máy tự lên danh sách khi agent báo về lần đầu. Muốn thêm máy: cài agent (gói cài ở <a href="/uem/quan-tri/agent">Quản trị, Agent</a>).</div>
    <div class="card">{bang}
    <form method="POST" action="/uem/may/hang-loat" id="f-hd" class="tk-f" style="margin-top:14px;border-top:1px solid var(--vien);padding-top:12px;">
      <div style="font-weight:700;margin-bottom:10px;">Với các máy đã chọn:</div>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;" class="hl-luoi">
        <select name="viec" style="margin:0;height:40px;"><option value="bao_cao">Lấy thông tin</option><option value="gan_tk">Gán tài khoản quản trị</option>
          <option value="them_nhom">Thêm vào nhóm máy</option><option value="bo_nhom">Gỡ khỏi nhóm máy</option><option value="nhom_moi">Tạo nhóm mới từ máy đã chọn</option>
          <option value="them_the">Thêm thẻ</option><option value="bo_the">Gỡ thẻ</option><option value="dia_diem">Đặt địa điểm</option>
          <option value="bat">Bật giám sát</option><option value="tat">Vô hiệu hóa giám sát</option><option value="xoa">Xóa khỏi danh sách</option></select>
        <select name="tk" style="margin:0;height:40px;"><option value="">(tài khoản)</option>{tk_opt}</select>
        <select name="nhom" style="margin:0;height:40px;"><option value="">(nhóm máy)</option>{nhom_opt}</select>
        <input type="text" name="nhom_moi" placeholder="Tên nhóm mới" style="margin:0;height:40px;">
        <select name="the" style="margin:0;height:40px;"><option value="">(thẻ)</option>{the_opt}</select>
        <select name="dd" style="margin:0;height:40px;"><option value="">(địa điểm)</option>{dd_opt}</select>
      </div>
      <style>@media(min-width:760px){{.hl-luoi{{grid-template-columns:repeat(3,1fr)!important;}}}}</style>
      <div style="display:flex;justify-content:flex-end;margin-top:12px;"><button type="submit" class="tk-nut chinh">Thực hiện</button></div></form></div>"""
    return trang(body, "may")


# ----------------------------------------------------------------- chi tiet may
TAB_MAY = [("tq", "Tổng quan"), ("phan-cung", "Phần cứng"), ("he-dieu-hanh", "Hệ điều hành"), ("o-dia", "Ổ đĩa"), ("man-hinh", "Màn hình"),
           ("mang", "Card mạng"), ("may-in", "Máy in"), ("chia-se", "Chia sẻ"), ("phan-mem", "Phần mềm"), ("cap-nhat", "Cập nhật"),
           ("duyet-file", "Duyệt file"), ("cli", "Dòng lệnh"), ("dich-vu", "Dịch vụ"), ("tien-trinh", "Tiến trình"), ("sua-loi", "Sửa lỗi in/chia sẻ"), ("tu-xa", "Hỗ trợ từ xa"), ("agent", "Agent"), ("nguon", "Nguồn điện"), ("tac-vu", "Tác vụ"),
           ("ghi-chu", "Ghi chú"), ("metadata", "Thông tin thêm"), ("quan-ly", "Quản lý")]


# Tab chi tiet may gom theo chuc nang (anh Thoai 28/10/2026: 22 tab tren 1 hang qua roi).
# Hang tren la nhom, bam nhom thi hien hang tab con cua nhom do.
NHOM_TAB_MAY = [
    ("Tổng quan", ["tq", "ghi-chu", "metadata"]),
    ("Phần cứng", ["phan-cung", "o-dia", "man-hinh", "mang", "may-in"]),
    ("Hệ điều hành & phần mềm", ["he-dieu-hanh", "phan-mem", "cap-nhat", "dich-vu", "tien-trinh"]),
    ("Điều khiển từ xa", ["cli", "duyet-file", "tu-xa", "nguon", "tac-vu"]),
    ("Chia sẻ & sửa lỗi", ["chia-se", "sua-loi"]),
    ("Quản lý", ["quan-ly", "agent"]),
]


def _tab_may_html(mid, tab):
    ten = dict(TAB_MAY)
    url = lambda k: f'/uem/may/{mid}/{k if k != "tq" else ""}'
    nhom_dang = next((ds for _n, ds in NHOM_TAB_MAY if tab in ds), NHOM_TAB_MAY[0][1])
    tren = "".join(f'<a href="{url(ds[0])}" class="{"on" if ds is nhom_dang else ""}">{n}</a>' for n, ds in NHOM_TAB_MAY)
    duoi = "".join(f'<a href="{url(k)}" class="{"on" if k == tab else ""}">{ten[k]}</a>' for k in nhom_dang)
    return f'<div class="uem-con">{tren}</div><div class="uem-con con2">{duoi}</div>'


def khung_may(m, tab, noi_dung):
    nhan, mau = trang_thai_may(m)
    os_ = bc(m).get("operatingsystem") or {}
    dau = (f'<div class="uem-dau"><h2>{_esc(ten_may(m))}</h2><span class="uem-dot {mau}"></span><span>{_esc(nhan)}</span>'
           f'<span class="tk-ghi">{_esc(m["ip"])} · {_esc((os_.get("description") or "").replace("Microsoft ", "")) or "chưa có báo cáo"} · báo cáo lúc {_esc(gio(m.get("bao_cao_luc")))}</span>'
           f'<form method="POST" action="/uem/may/{m["id"]}/bao-cao-ngay" style="margin:0;"><button type="submit" class="tk-nut">{svg_icon("refresh")}Lấy thông tin</button></form>'
           f'<a class="tk-nut" href="/uem/may">Danh sách máy</a></div><div>{the_html(m)}</div>')
    kn = m.get("ket_noi") or {}
    loi = f'<div class="msg err">Lần kết nối cuối thất bại: {_esc(kn.get("loi"))}</div>' if kn and not kn.get("ok") else ""
    cho = '<div class="msg info">Báo cáo đang được lấy ở nền, tải lại trang sau ít giây.</div>' if UBC.dang_chay(m["id"]) else ""
    return trang(f'{dau}{_tab_may_html(m["id"], tab)}{cho}{loi}{noi_dung}', "may", tieu_de=_esc(f"Máy: {ten_may(m)}"), phu_de="Chi tiết máy trạm")


def _chua_bao_cao(m):
    if not m.get("tai_khoan_id") and not (m.get("agent") or {}).get("khoa"):
        return '<div class="card"><p>Máy chưa gán tài khoản quản trị và chưa cài agent nên chưa lấy được báo cáo. Gán tài khoản ở tab <a href="/uem/may/' + m["id"] + '/quan-ly">Quản lý</a> hoặc cài agent ở tab <a href="/uem/may/' + m["id"] + '/agent">Agent</a>.</p></div>'
    return '<div class="card"><p>Chưa có báo cáo của máy này. Bấm <b>Lấy thông tin</b> ở phía trên (mất khoảng 25 giây).</p></div>'


def kv(*cap):
    return '<table class="uem-kv">' + "".join(f"<tr><th>{_esc(k)}</th><td>{v if isinstance(v, Raw) else _esc(v)}</td></tr>" for k, v in cap) + "</table>"


def bang(cot, hang, trong="Không có dữ liệu."):
    if not hang:
        return f'<p class="tk-ghi">{_esc(trong)}</p>'
    return '<div class="uem-bang-cuon"><table class="tk-bang"><tr>' + "".join(f"<th>{_esc(c)}</th>" for c in cot) + "</tr>" + "".join(
        "<tr>" + "".join(f"<td>{c if isinstance(c, Raw) else _esc(c)}</td>" for c in r) + "</tr>" for r in hang) + "</table></div>"


def tab_may(m, tab):
    r = bc(m)
    if tab not in ("ghi-chu", "metadata", "quan-ly", "tu-xa", "agent", "nguon", "trien-khai", "tac-vu", "duyet-file", "cli", "dich-vu", "tien-trinh", "sua-loi") and not r:
        return khung_may(m, tab, _chua_bao_cao(m))
    cs, os_ = r.get("computer") or {}, r.get("operatingsystem") or {}
    if tab == "tq":
        ao = r.get("antivirus") or {}
        su = r.get("systemupdate") or {}
        ds = r.get("logicaldisks", [])
        body = f"""<div class="uem-2"><div class="card"><h3>Máy</h3>{kv(("Tên máy Windows", r.get("hostname")), ("Hãng / model", f'{cs.get("manufacturer", "")} {cs.get("model", "")}'),
            ("Số serial", cs.get("serial")), ("Bộ xử lý", f'{cs.get("processor", "")} ({cs.get("processor_cores", "")} nhân, {cs.get("processor_arch", "")})'), ("Bộ nhớ", cs.get("memory")),
            ("Địa chỉ IP", r.get("ip") or m["ip"]), ("Địa chỉ MAC", r.get("mac")))}</div>
          <div class="card"><h3>Hệ điều hành</h3>{kv(("Hệ điều hành", os_.get("description")), ("Phiên bản", f'{os_.get("version", "")} ({os_.get("edition", "")}, {os_.get("arch", "")})'),
            ("Cài đặt lúc", iso_gio(os_.get("install_date"))), ("Khởi động gần nhất", iso_gio(os_.get("last_bootup_time"))), ("Người dùng đăng nhập", os_.get("username") or "—"),
            ("Miền / nhóm làm việc", os_.get("domain")))}</div>
          <div class="card"><h3>Bảo mật</h3>{kv(("Diệt virus", f'{ao.get("name") or "Không có"} - ' + ("đang bật" if ao.get("is_active") else "TẮT")),
            ("Cơ sở dữ liệu diệt virus", co_khong(ao.get("is_updated"), "Mới", "Cũ")),
            ("Cập nhật Windows chờ", f'{len(r.get("pending_updates", []))} bản'), ("Tự động cập nhật", ten_cap_nhat(su.get("status"))),
            ("Tường lửa", ", ".join(f'{x["ten"]}: {"bật" if x["bat"] else "tắt"}' for x in r.get("firewall", [])) or "—"),
            ("SMB1", r.get("smb1") or "—"))}</div>
          <div class="card"><h3>Ổ đĩa</h3>{bang(["Ổ", "Dùng", "Còn trống", "BitLocker"], [[d["label"], f'{d["usage"]}% của {d["size_in_units"]}', d["remaining_space_in_units"], d["bitlocker_status"]] for d in ds])}</div></div>"""
        return khung_may(m, tab, body)
    if tab == "phan-cung":
        slots = r.get("memoryslots", [])
        body = (f'<div class="card"><h3>Máy tính</h3>{kv(("Hãng", cs.get("manufacturer")), ("Model", cs.get("model")), ("Số serial", cs.get("serial")), ("Bộ xử lý", cs.get("processor")), ("Kiến trúc", cs.get("processor_arch")), ("Số nhân", cs.get("processor_cores")), ("Bộ nhớ", cs.get("memory")))}</div>'
                f'<h2>Khe RAM</h2><div class="card">{bang(["Khe", "Dung lượng", "Loại", "Tốc độ", "Hãng", "Part number", "Serial"], [[s["slot"], s["size"], s["type"], s["speed"], s["manufacturer"], s["part_number"], s["serial_number"]] for s in slots], "Không đọc được khe RAM.")}</div>')
        return khung_may(m, tab, body)
    if tab == "he-dieu-hanh":
        return khung_may(m, tab, f'<div class="card">{kv(("Mô tả", os_.get("description")), ("Phiên bản", os_.get("version")), ("Bản dựng", os_.get("build")), ("Edition", os_.get("edition")), ("Kiến trúc", os_.get("arch")), ("Ngày cài đặt", iso_gio(os_.get("install_date"))), ("Khởi động gần nhất", iso_gio(os_.get("last_bootup_time"))), ("Người dùng đăng nhập", os_.get("username") or "—"), ("Miền / nhóm làm việc", os_.get("domain")))}</div>')
    if tab == "o-dia":
        ld = [[d["label"], d.get("volume_name") or "—", d["filesystem"], d["size_in_units"], d["remaining_space_in_units"],
               Raw(f'<div class="tk-vach" style="min-width:110px"><i style="width:{d["usage"]}%;background:{"var(--do)" if d["usage"] >= 90 else "var(--xanh)"}"></i></div> {d["usage"]}%'),
               chip(d["bitlocker_status"], "xanh" if d["bitlocker_status"] == "Encrypted" else ("do" if d["bitlocker_status"] == "Unencrypted" else ""))] for d in r.get("logicaldisks", [])]
        pd = [[d["device_id"], d["model"], d["serial_number"], d["size_in_units"]] for d in r.get("physicaldisks", [])]
        return khung_may(m, tab, f'<h2>Ổ đĩa logic</h2><div class="card">{bang(["Ổ", "Tên", "Hệ tập tin", "Dung lượng", "Còn trống", "Mức dùng", "BitLocker"], ld)}</div>'
                                 f'<h2>Ổ đĩa vật lý</h2><div class="card">{bang(["Thiết bị", "Model", "Số serial", "Dung lượng"], pd)}</div>')
    if tab == "man-hinh":
        mn = [[x["manufacturer"], x["model"], x["serial"], x["week_of_manufacture"], x["year_of_manufacture"]] for x in r.get("monitors", [])]
        return khung_may(m, tab, f'<div class="card">{bang(["Hãng", "Model", "Serial", "Tuần sản xuất", "Năm sản xuất"], mn, "Không đọc được màn hình (Windows chỉ cung cấp thông tin này cho phiên đăng nhập có màn hình; qua WinRM thường để trống).")}</div>')
    if tab == "mang":
        na = [[x["name"], x["mac_address"], x["addresses"], x["subnet"], x["default_gateway"], x["dns_servers"], x["dns_domain"] or "—", "DHCP" if x["dhcp_enabled"] else "Tĩnh",
               iso_gio(x.get("dhcp_lease_obtained")) if x["dhcp_enabled"] else "—", iso_gio(x.get("dhcp_lease_expired")) if x["dhcp_enabled"] else "—", x["speed"]] for x in r.get("networkadapters", [])]
        return khung_may(m, tab, f'<div class="card">{bang(["Card", "MAC", "IP", "Mạng con", "Cổng mặc định", "DNS", "Miền DNS", "Kiểu", "Thuê DHCP từ", "Hết hạn", "Tốc độ"], na)}</div>')
    if tab == "may-in":
        pr = [[x["name"], x["port"], co_khong(x["is_default"], "Mặc định", "—"), co_khong(x["is_network"], "Mạng", "Cục bộ"), co_khong(x["is_shared"], "Chia sẻ", "—"),
               Raw(f'<form method="POST" action="/uem/may/{m["id"]}/may-in/xoa" onsubmit="return confirm(this.dataset.hoi);" data-hoi="Xóa máy in này khỏi máy Windows?" style="margin:0;"><input type="hidden" name="ten" value="{_esc(x["name"])}"><button class="tk-nut do" type="submit">Xóa</button></form>')] for x in r.get("printers", [])]
        return khung_may(m, tab, f'<div class="card">{bang(["Tên", "Cổng", "Mặc định", "Kiểu", "Chia sẻ", ""], pr, "Không có máy in.")}'
                                 '<p class="tk-ghi">Lưu ý: khác agent chạy trong phiên người dùng, Console System chỉ thấy máy in cấp hệ thống (máy in cài riêng cho từng người dùng và đặt máy in mặc định theo người dùng không làm được qua WinRM).</p></div>')
    if tab == "chia-se":
        sh = [[x["name"], x["path"], x["description"]] for x in r.get("shares", [])]
        return khung_may(m, tab, f'<div class="card">{bang(["Tên", "Đường dẫn", "Mô tả"], sh)}</div>')
    if tab == "phan-mem":
        return khung_may(m, tab, _tab_phan_mem(m))
    if tab == "cap-nhat":
        return khung_may(m, tab, _tab_cap_nhat(m))
    if tab == "ghi-chu":
        return khung_may(m, tab, f'<div class="card"><form method="POST" action="/uem/may/{m["id"]}/ghi-chu" class="tk-f"><label>Ghi chú về máy này</label>'
                                 f'<textarea name="ghi_chu" rows="10" style="width:100%;max-width:none;">{_esc(m.get("ghi_chu", ""))}</textarea><div style="margin-top:12px;">'
                                 f'<button class="tk-nut chinh" type="submit">Lưu ghi chú</button></div></form></div>' + (f'<h2>Xem trước</h2><div class="card uem-ghi">{_esc(m.get("ghi_chu"))}</div>' if m.get("ghi_chu") else ""))
    if tab == "metadata":
        dn = UD.METADATA.doc()
        if not dn:
            return khung_may(m, tab, '<div class="card"><p>Chưa định nghĩa trường thông tin nào. Tạo ở <a href="/uem/quan-tri/metadata">Quản trị, Thông tin thêm</a> (ví dụ: Vị trí đặt máy, Người phụ trách, Ngày hết bảo hành).</p></div>')
        o = "".join(f'<label>{_esc(d["ten"])}<span class="tk-ghi"> {_esc(d.get("mo_ta", ""))}</span></label><input type="text" name="md_{d["id"]}" value="{_esc((m.get("metadata") or {}).get(d["id"], ""))}">' for d in dn)
        return khung_may(m, tab, f'<div class="card"><form method="POST" action="/uem/may/{m["id"]}/metadata" class="tk-f">{o}<div style="margin-top:12px;"><button class="tk-nut chinh" type="submit">Lưu</button></div></form></div>')
    if tab == "quan-ly":
        tk = DL.tai_khoan_cong_khai()
        opt_tk = '<option value="">(chưa gán)</option>' + "".join(f'<option value="{t["id"]}"{" selected" if t["id"] == m.get("tai_khoan_id") else ""}>{_esc(t["ten"])} ({_esc(t["user"])})</option>' for t in tk)
        the_ds = UD.THE.doc()
        o_the = "".join(f'<label class="tk-o"><input type="checkbox" name="the" value="{t["id"]}"{" checked" if t["id"] in m.get("the", []) else ""}><span><b>{_esc(t["ten"])}</b><small>{_esc(t.get("mo_ta", ""))}</small></span></label>' for t in the_ds)
        dd = UD.DIA_DIEM.doc()
        opt_dd = '<option value="">(không)</option>' + "".join(f'<option value="{d["id"]}"{" selected" if d["id"] == m.get("dia_diem") else ""}>{_esc(d["ten"])}</option>' for d in dd)
        return khung_may(m, tab, f'''<div class="card"><form method="POST" action="/uem/may/{m["id"]}/quan-ly" class="tk-f">
          <label>Tên gọi (biệt danh)</label><input type="text" name="bi_danh" value="{_esc(m.get("bi_danh", ""))}" placeholder="Ví dụ: Máy kế toán 01">
          <label>Địa chỉ IP (Console System dùng để kết nối)</label><input type="text" name="ip" value="{_esc(m["ip"])}">
          <label>Địa chỉ MAC (để bật máy bằng Wake-on-LAN)</label><input type="text" name="mac" value="{_esc(m.get("mac", ""))}">
          <label>Loại thiết bị</label><input type="text" name="loai" value="{_esc(m.get("loai", ""))}" placeholder="Máy bàn, Laptop, Máy chủ...">
          <label>Tài khoản quản trị dùng cho máy này</label><select name="tai_khoan_id">{opt_tk}</select>
          <label>Địa điểm</label><select name="dia_diem">{opt_dd}</select>
          <label>Thẻ</label><div class="tk-luoi">{o_the or '<span class="tk-ghi">Chưa có thẻ, tạo ở Quản trị, Thẻ.</span>'}</div>
          <label><input type="checkbox" name="giam_sat" value="1"{" checked" if m.get("giam_sat", True) else ""} style="margin-right:8px;">Đang giám sát (tắt = vô hiệu, không lấy báo cáo, không áp profile)</label>
          <div style="margin-top:14px;"><button class="tk-nut chinh" type="submit">Lưu</button></div></form></div>
          <form method="POST" action="/uem/may/{m["id"]}/xoa" onsubmit="return confirm(this.dataset.hoi);" data-hoi="Xóa máy khỏi danh sách (không ảnh hưởng máy thật)?" style="margin-top:14px;"><button class="tk-nut do" type="submit">Xóa máy khỏi danh sách</button></form>''')
    return None


def ten_cap_nhat(s):
    return UBC.ten_cap_nhat_tu_dong(s)


def _tab_phan_mem(m):
    ap = bc(m).get("applications", [])
    hang = "".join(f'<tr data-t="{_esc((a["name"] + " " + a.get("publisher", "")).lower())}"><td>{_esc(a["name"])}</td><td>{_esc(a["version"])}</td><td>{_esc(a.get("publisher"))}</td><td>{_esc(a.get("install_date") or "—")}</td></tr>' for a in ap)
    return (f'<div class="card uem-ds" data-trang="20"><div class="uem-loc"><input type="text" class="uem-tim" placeholder="Tìm phần mềm hoặc nhà sản xuất"><span class="tk-ghi"><b class="uem-dem"></b> phần mềm</span>'
            f'<a class="tk-nut" href="/uem/may/{m["id"]}/phan-mem.csv">Tải CSV</a></div><div class="uem-bang-cuon"><table class="tk-bang"><thead><tr><th>Tên</th><th>Phiên bản</th><th>Nhà sản xuất</th><th>Ngày cài</th></tr></thead><tbody>{hang}</tbody></table></div></div>')


def _lk(u):
    u = str(u or "")
    if not u.startswith(("http://", "https://")):
        return "—"
    return Raw('<a href="' + _esc(u) + '" target="_blank" rel="noopener">Mở</a>')


def _tab_cap_nhat(m):
    r = bc(m)
    su = r.get("systemupdate") or {}
    pend = r.get("pending_updates", [])
    his = r.get("updates", [])
    return (f'<div class="card"><h3>Trạng thái Windows Update</h3>{kv(("Tự động cập nhật", ten_cap_nhat(su.get("status"))), ("Lần tìm kiếm gần nhất", iso_gio(su.get("last_search"))), ("Lần cài đặt gần nhất", iso_gio(su.get("last_install"))), ("Có bản cập nhật đang chờ", co_khong(su.get("pending_updates"), "Có", "Không")))}</div>'
            f'<h2>Đang chờ cài ({len(pend)})</h2><div class="card">{bang(["Tiêu đề", "KB", "Mức"], [[p["title"], p.get("kb") or "—", "Quan trọng" if p.get("critical") else "—"] for p in pend], "Không có bản cập nhật nào đang chờ.")}</div>'
            f'<h2>Lịch sử gần đây ({len(his)})</h2><div class="card">{bang(["Tiêu đề", "Ngày", "Liên kết hỗ trợ"], [[h["title"], iso_gio(h["date"]), _lk(h.get("support_url"))] for h in his], "Chưa có lịch sử.")}</div>')
