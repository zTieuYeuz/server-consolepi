# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Cai phan mem qua Agent - KICH BAN (mo phong Software Deployment configuration cua Endpoint Central):
  chon phan mem trong kho > chon may / group > chon tai khoan cai (Install As: System User / Run As User) > chon thoi gian
  (chay ngay khi bam Chay, hen gio rieng, hoac lich dung chung). Xem tien do tung may / tung buoc, Dung (Suspend),
  Tiep tuc (Resume), Xoa.

Dung chung dong co kich ban cua Cai phan mem qua LAN (tk_dongco: KICH_BAN + LICH + TRANG_THAI, vong 15 giay, luu dia)
voi kenh="agent": vao may bang agent thay vi WinRM, may tat thi "Cho may bat" va tu chay khi agent ket noi lai.
Kich ban Agent khong hien o trang LAN va nguoc lai.
"""
import json
import re
import time

from flask import jsonify, request

from ui import tk_dongco as DC
from ui import tk_dulieu as DL
from ui.uem_trang import _esc, chip, chuyen, gio, trang
from consolesystem.core import taisan as _taisan

URL = "/uem/trien-khai/kich-ban"
TT_MAY = {"cho": ("Chờ chạy", ""), "dang": ("Đang chạy", "nhan"), "xong": ("Thành công", "xanh"), "loi": ("Không thành công", "do"),
          "offline": ("Chờ máy bật", "vang"), "cho_thu_lai": ("Chờ thử lại", "vang"), "dung": ("Đã dừng", "")}
TT_BUOC = {"cho": ("Chờ", ""), "dang": ("Đang chạy", "nhan"), "ok": ("Xong", "xanh"), "loi": ("Lỗi", "do")}


# Cac loai buoc kich ban Agent cho phep (A5): cai app, script trong kho, khoi dong lai/tat may, WinGet, nhom phan mem.
NGUON_AGENT = {"khoi_dong_lai": "Khởi động lại máy (đợi máy bật lại rồi mới chạy bước sau)", "tat": "Tắt máy"}
LOAI_AGENT = ("phanmem", "ungdung", "script", "winget", "nguon", "nhom")


def _tai_nguyen():
    return {
        "phanmem": [{"ref": a["ten"], "ten": a["ten"], "mo_ta": a.get("tham_so") or "chưa điền tham số cài im lặng"} for a in DC.danh_sach_kho()],
        "ungdung": [{"ref": u["id"], "ten": u["ten_hien_thi"], "mo_ta": u.get("lenh_cai") or "chưa có dòng lệnh cài"} for u in DC.danh_sach_ungdung()],
        "script": [{"ref": x, "ten": x, "mo_ta": ""} for x in DC.danh_sach_script()],
    }


def chuan_buoc(buoc):
    """Danh sach buoc tu giao dien (buoc_json) -> danh sach sach, bo buoc khong hop le."""
    tn = _tai_nguyen()
    sach = []
    for b in buoc if isinstance(buoc, list) else []:
        if not isinstance(b, dict):
            continue
        loai, ref = str(b.get("loai", "")), str(b.get("ref", ""))
        if loai not in LOAI_AGENT:
            continue
        if loai in ("phanmem", "ungdung", "script"):
            t = next((x for x in tn[loai] if x["ref"] == ref), None)
            if not t:
                continue
            m = {"loai": loai, "ref": ref, "ten": t["ten"]}
        elif loai == "winget":
            if not re.fullmatch(r"[A-Za-z0-9._+-]{2,100}", ref):
                continue
            m = {"loai": loai, "ref": ref, "ten": "WinGet: " + ref}
        elif loai == "nguon":
            if ref not in NGUON_AGENT:
                continue
            m = {"loai": loai, "ref": ref}
        else:
            g = DL.tim(DL.NHOM_TN.doc(), ref)
            if not g:
                continue
            m = {"loai": loai, "ref": ref, "ten": g["ten"]}
        if b.get("mot_lan") and loai in ("phanmem", "ungdung", "winget", "nhom"):
            m["mot_lan"] = True
        sach.append(m)
    return sach


def _ds():
    return [k for k in DL.KICH_BAN.doc() if DC.la_agent(k)]


def _lich_rieng(kb):
    l = DL.tim(DL.LICH.doc(), kb.get("lich_id")) if kb.get("lich_id") else None
    return l if l and l.get("rieng") else None


def _mo_ta_thoi_gian(kb):
    l = DL.tim(DL.LICH.doc(), kb.get("lich_id")) if kb.get("lich_id") else None
    return DL.mo_ta_lich(l) if l else "Chạy ngay khi bấm Chạy"


def _dem(st):
    d = {}
    for m in ((st or {}).get("may") or {}).values():
        d[m.get("tt")] = d.get(m.get("tt"), 0) + 1
    return d


def _tom_tat(kb, st):
    """(nhan, mau) trang thai chung cua kich ban."""
    st = st or {}
    if not st.get("bat"):
        if st.get("slot") and not st.get("xong_luc") and st.get("may"):
            return "Đã dừng (bấm Tiếp tục để chạy tiếp)", "vang"
        return ("Đã xong" if st.get("xong_luc") else "Chưa chạy"), ""
    if not st.get("slot"):
        return "Chờ đến giờ hẹn", "nhan"
    if st.get("xong_luc"):
        return ("Xong lượt này, chờ lịch kế tiếp" if kb.get("lich_id") else "Đã xong"), ("vang" if _dem(st).get("loi") else "xanh")
    return "Đang chạy", "nhan"


def _chip_dem(st):
    d = _dem(st)
    return "".join(f'<span class="tk-chip {TT_MAY[k][1]}" style="margin:0 6px 4px 0;">{TT_MAY[k][0]}: {d[k]}</span>'
                   for k in ("xong", "dang", "cho", "offline", "cho_thu_lai", "dung", "loi") if d.get(k))


def _nut(action, nhan, cls="", hoi=""):
    xn = f' onsubmit="return confirm(this.dataset.hoi);" data-hoi="{_esc(hoi)}"' if hoi else ""
    return (f'<form method="POST" action="{action}" style="display:inline;"{xn}>'
            f'<button class="tk-nut {cls}" type="submit">{nhan}</button></form>')


def _nut_dieu_khien(kb, st):
    u = f'{URL}/{kb["id"]}'
    st = st or {}
    if st.get("bat"):
        if st.get("xong_luc") and not kb.get("lich_id"):     # chay ngay, da xong: khong con gi de dung
            return _nut(u + "/chay", "Chạy lại", "chinh")
        return _nut(u + "/dung", "Dừng", "do", "Dừng kịch bản? Máy đang chạy sẽ dừng sau bước đang làm; bấm Tiếp tục để chạy tiếp.")
    if st.get("slot") and not st.get("xong_luc") and st.get("may"):
        return _nut(u + "/tiep-tuc", "Tiếp tục", "chinh") + " " + _nut(u + "/chay", "Chạy lại từ đầu", "", "Chạy lại từ đầu? Tiến độ hiện tại sẽ bị thay bằng lượt mới.")
    return _nut(u + "/chay", "Chạy", "chinh")


# ------------------------------------------------------------------ danh sach
def trang_ds():
    from ui import uem_trang_b as TB
    tt = DL.TRANG_THAI.doc()
    hang = ""
    for k in _ds():
        st = tt.get(k["id"], {})
        nhan, mau = _tom_tat(k, st)
        tong = len(st.get("may", {}))
        xong = _dem(st).get("xong", 0)
        pt = int(xong * 100 / tong) if tong else 0
        hang += (f'<tr><td><a href="{URL}/{k["id"]}"><b>{_esc(k["ten"])}</b></a><div class="tk-ghi">{len(k.get("buoc", []))} phần mềm · '
                 f'{len(DC.may_cua_kich_ban(k))} máy · {_esc(_mo_ta_thoi_gian(k))}</div></td>'
                 f'<td>{chip(nhan, mau)}<div style="margin-top:6px;">{_chip_dem(st)}</div></td>'
                 f'<td style="min-width:140px;"><div class="tk-vach"><i style="width:{pt}%"></i></div><div class="tk-ghi">{xong}/{tong} máy thành công</div></td>'
                 f'<td><div class="tk-act">{_nut_dieu_khien(k, st)} <a class="tk-nut" href="{URL}/{k["id"]}">Tiến độ</a> '
                 f'<a class="tk-nut" href="{URL}/sua?id={k["id"]}">Sửa</a> '
                 f'{_nut(URL + "/" + k["id"] + "/xoa", "Xóa", "do", "Xóa kịch bản " + k["ten"] + " và tiến độ của nó?")}</div></td></tr>')
    bang = (f'<table class="tk-bang"><tr><th>Kịch bản</th><th>Trạng thái</th><th>Tiến độ</th><th></th></tr>{hang}</table>' if hang
            else '<p class="tk-ghi">Chưa có kịch bản nào.</p>')
    body = (TB._thanh_tab_cai("kb") + f'''<div class="card"><p class="tk-ghi" style="margin-top:0;">Kịch bản = chọn phần mềm trong kho, chọn máy hoặc group,
      chọn tài khoản cài và thời gian cài. Bấm <b>Chạy</b> để kích hoạt; kịch bản có hẹn giờ sẽ tự chạy theo lịch cho đến khi bấm <b>Dừng</b>.
      Máy đang tắt nằm ở <b>Chờ máy bật</b> và tự chạy khi agent kết nối lại; bước cài lỗi được thử lại tối đa 3 lần, cách nhau 5 phút.</p>
      <p><a class="tk-nut chinh" href="{URL}/sua">Tạo kịch bản mới</a></p></div>
      <div class="card" style="overflow:auto;" id="kb-khung">{bang}</div>''' + _JS_LAM_MOI)
    return trang(body, "td")


_JS_LAM_MOI = """<script>(function(){setInterval(function(){if(document.hidden)return;
fetch(location.pathname+'?_='+Date.now(),{cache:'no-store'}).then(function(r){return r.text();}).then(function(h){
var n=new DOMParser().parseFromString(h,'text/html').getElementById('kb-khung'),o=document.getElementById('kb-khung');if(n&&o)o.innerHTML=n.innerHTML;}).catch(function(){});},5000);})();</script>"""


# ------------------------------------------------------------------ tao / sua
def trang_sua():
    from ui import uem_trang_b as TB
    kb = DL.tim(_ds(), request.args.get("id", "")) or {}
    tn = _tai_nguyen()
    du_lieu = json.dumps({"tn": tn, "nhom": [{"ref": g["id"], "ten": g["ten"], "mo_ta": f'{len(g.get("muc", []))} mục'} for g in DL.NHOM_TN.doc()],
                          "buoc": kb.get("buoc", []), "ten_loai": DC.TEN_LOAI_BUOC, "nguon": NGUON_AGENT, "loai": list(LOAI_AGENT)},
                         ensure_ascii=False).replace("</", "<\\/")
    tk = DL.tai_khoan_cong_khai()
    o_tk = ('<option value="">Tài khoản hệ thống SYSTEM của agent (mặc định, quyền cao nhất)</option>'
            + "".join(f'<option value="{t["id"]}"{" selected" if kb.get("tai_khoan_id") == t["id"] else ""}>Chạy bằng tài khoản: {_esc(t["ten"])} ({_esc(t["user"])})</option>' for t in tk))
    rieng = _lich_rieng(kb) or {}
    chung = [l for l in DL.LICH.doc() if not l.get("rieng")]
    chon = "rieng" if rieng else (kb.get("lich_id") or "ngay")
    o_tg = (f'<option value="ngay"{" selected" if chon == "ngay" else ""}>Chạy ngay khi bấm Chạy</option>'
            f'<option value="rieng"{" selected" if chon == "rieng" else ""}>Hẹn giờ / lặp lại (đặt ngay bên dưới)</option>'
            + "".join(f'<option value="{l["id"]}"{" selected" if chon == l["id"] else ""}>Lịch dùng chung: {_esc(l["ten"])} - {_esc(DL.mo_ta_lich(l))}</option>' for l in chung))
    kieu = rieng.get("kieu", "hang_ngay")
    ok = lambda v, n: f'<option value="{v}"{" selected" if kieu == v else ""}>{n}</option>'  # noqa: E731
    thu = "".join(f'<label style="display:inline-flex;gap:4px;margin:0 10px 0 0;"><input type="checkbox" name="thu" value="{i}" style="width:auto;margin:0;"'
                  f'{" checked" if i in rieng.get("thu", []) else ""}>{t}</label>' for i, t in enumerate(DL.THU))
    thang = "".join(f'<option value="{i}"{" selected" if rieng.get("thang") == i else ""}>Tháng {i}</option>' for i in range(1, 13))
    body = (TB._thanh_tab_cai("kb") + f'''<p><a class="tk-nut" href="{URL}">Quay lại</a></p>
    <form method="POST" action="{URL}/luu" class="card tk-f" id="f-kb"><input type="hidden" name="id" value="{_esc(kb.get("id", ""))}"><input type="hidden" name="buoc_json" id="buoc-json">
      <h3 style="margin-top:0;">{"Sửa kịch bản" if kb else "Tạo kịch bản mới"}</h3>
      <label>Tên kịch bản</label><input type="text" name="ten" required value="{_esc(kb.get("ten", ""))}" placeholder="Ví dụ: Cài phần mềm văn phòng cho phòng kế toán">
      <h4 class="tk-tieude">1. Các bước (chạy lần lượt từ trên xuống)</h4>
      <div id="ds-buoc"></div>
      <div class="tk-hang" style="margin-top:8px;"><select id="b-loai" style="margin:0;height:42px;max-width:240px;"></select>
        <input type="search" id="b-tim" placeholder="Tìm trong danh sách (gõ không dấu cũng được)" autocomplete="off" style="margin:0;height:42px;max-width:300px;">
        <select id="b-ref" style="margin:0;height:42px;max-width:420px;"></select>
        <input type="text" id="b-text" placeholder="Mã WinGet, ví dụ Google.Chrome" style="margin:0;height:42px;max-width:320px;display:none;">
        <span class="tk-ghi" id="b-so"></span>
        <button type="button" class="tk-nut" id="b-them">Thêm bước</button></div>
      <p class="tk-ghi" id="b-ghi"></p>
      <p class="tk-ghi">Ví dụ: cài phần mềm → chạy Script → Khởi động lại máy → cài phần mềm tiếp theo. Sau bước khởi động lại, Console System đợi máy bật lại
        (agent trực tuyến, giờ khởi động đổi) rồi mới chạy bước kế tiếp; có thể tắt Console System giữa chừng, kịch bản vẫn tiếp tục.</p>
      <h4 class="tk-tieude">2. Chọn máy hoặc group</h4>
      <div class="tk-hang" style="gap:14px;"><div><label for="cg-loai">Áp dụng cho</label><select id="cg-loai" style="max-width:220px;margin:0;"><option value="may">Chọn máy</option><option value="nhom">Chọn group</option></select></div></div>
      {TB._chon_may_nhom_html(set(kb.get("may", [])), set(kb.get("nhom_may", [])))}
      <h4 class="tk-tieude">3. Cài bằng tài khoản</h4>
      <select name="tai_khoan_id">{o_tk}</select>
      <p class="tk-ghi">Mặc định agent cài bằng SYSTEM. Chọn tài khoản khi bộ cài phải chạy bằng một người dùng cụ thể (Run As User):
        Console System tạo tác vụ tạm trên máy, chạy bằng tài khoản đó rồi xóa. Tài khoản dùng chung với Cài phần mềm qua LAN (Máy - nhóm máy, Tài khoản quản trị).</p>
      <h4 class="tk-tieude">4. Thời gian cài</h4>
      <select name="thoi_gian" id="kb-tg">{o_tg}</select>
      <div id="kb-rieng" class="card" style="margin-top:10px;">
        <label>Lặp lại</label><select name="kieu" id="lich-kieu">{ok("mot_lan", "Một lần duy nhất")}{ok("hang_ngay", "Hằng ngày")}{ok("hang_tuan", "Hằng tuần (chọn thứ)")}
          {ok("hang_thang", "Hằng tháng (chọn ngày)")}{ok("hang_nam", "Hằng năm (chọn tháng và ngày)")}</select>
        <label>Giờ chạy</label><input type="time" name="gio" value="{_esc(rieng.get("gio", "02:00"))}">
        <div data-k="mot_lan"><label>Ngày chạy</label><input type="date" name="ngay" value="{_esc(rieng.get("ngay", ""))}"></div>
        <div data-k="hang_tuan"><label>Những ngày trong tuần</label><div>{thu}</div></div>
        <div data-k="hang_nam"><label>Tháng</label><select name="thang">{thang}</select></div>
        <div data-k="hang_thang hang_nam"><label>Ngày trong tháng</label><input type="number" name="ngay_thang" min="1" max="31" value="{_esc(rieng.get("ngay_thang", 1))}"></div>
        <p class="tk-ghi">Lỡ giờ hẹn (Console System tắt) mà chưa quá 6 giờ thì vẫn chạy bù. Máy tắt đúng giờ hẹn sẽ tự cài khi bật lên.</p></div>
      <div class="tk-hang" style="margin-top:16px;gap:10px;"><button class="tk-nut chinh" type="submit" name="sau" value="luu">Lưu kịch bản</button>
        <button class="tk-nut" type="submit" name="sau" value="chay">Lưu và chạy</button></div>
    </form>{TB.JS_CHON}
    <script id="kb-du-lieu" type="application/json">{du_lieu}</script>
    <script>{_taisan.doc("features/software_deploy/tk_trang.JS_KICHBAN.js")}</script>
    <script>(function(){{var t=document.getElementById('kb-tg'),r=document.getElementById('kb-rieng'),s=document.getElementById('lich-kieu');
    function d(){{r.style.display=t.value==='rieng'?'':'none';document.querySelectorAll('#kb-rieng [data-k]').forEach(function(e){{
      e.style.display=e.getAttribute('data-k').split(' ').indexOf(s.value)>=0?'':'none';}});}}t.onchange=d;s.onchange=d;d();}})();</script>''')
    return trang(body, "td")


def luu():
    f = request.form
    kid = f.get("id", "")
    cu = DL.tim(_ds(), kid) if kid else None
    if kid and not cu:
        return chuyen(URL, "Không còn kịch bản này.", False)
    ten = (f.get("ten") or "").strip()[:120]
    try:
        moi = json.loads(f.get("buoc_json") or "null")
    except ValueError:
        moi = None
    if isinstance(moi, list):                       # giao dien moi: danh sach buoc co thu tu (cai app, script, khoi dong lai...)
        buoc = chuan_buoc(moi)
    else:                                           # tuong thich: bieu mau cu chon phan mem bang o tick
        kho = [a["ten"] for a in DC.danh_sach_kho()]
        chon = set(f.getlist("pm"))
        mot_lan = bool(f.get("mot_lan"))
        buoc = [dict({"loai": "phanmem", "ref": t, "ten": t}, **({"mot_lan": True} if mot_lan else {})) for t in kho if t in chon]
        chon_ud = set(f.getlist("ud"))
        buoc += [dict({"loai": "ungdung", "ref": u["id"], "ten": u["ten_hien_thi"]}, **({"mot_lan": True} if mot_lan else {})) for u in DC.danh_sach_ungdung() if u["id"] in chon_ud]
    may = [i for i in dict.fromkeys(f.getlist("may")) if DL.tim(DL.MAY.doc(), i)]
    nhom = [i for i in dict.fromkeys(f.getlist("nhom")) if DL.tim(DL.NHOM_MAY.doc(), i)]
    tk = f.get("tai_khoan_id", "")
    if tk and DL.lay_tai_khoan(tk)[0] is None:
        tk = ""
    if not ten or not buoc:
        return chuyen(URL + "/sua" + (f"?id={kid}" if kid else ""), "Cần có tên và ít nhất một bước hợp lệ.", False)
    if not may and not nhom:
        return chuyen(URL + "/sua" + (f"?id={kid}" if kid else ""), "Chọn ít nhất một máy hoặc một group.", False)
    kb_id = kid or DL.moi_id()
    tg = f.get("thoi_gian", "ngay")
    rieng_cu = _lich_rieng(cu or {})
    lich_id = ""
    if tg == "rieng":
        l, loi = DL.chuan_lich(f)
        if loi:
            return chuyen(URL + "/sua" + (f"?id={kid}" if kid else ""), loi, False)
        l.update(ten="Riêng: " + ten, rieng=kb_id)
        lich_id = rieng_cu["id"] if rieng_cu else DL.moi_id()

        def ghi_lich(ds):
            c = DL.tim(ds, lich_id)
            if c:
                c.clear()
                c.update(l, id=lich_id)
            else:
                ds.append(dict(l, id=lich_id))
        DL.LICH.sua(ghi_lich)
    elif tg != "ngay" and DL.tim(DL.LICH.doc(), tg):
        lich_id = tg
    if rieng_cu and rieng_cu["id"] != lich_id:
        DL.LICH.sua(lambda ds: ds.__setitem__(slice(None), [x for x in ds if x["id"] != rieng_cu["id"]]))
    dl = dict(ten=ten, kenh="agent", buoc=buoc, may=may, nhom_may=nhom, tai_khoan_id=tk, lich_id=lich_id)

    def ghi(ds):
        c = DL.tim(ds, kb_id)
        if c:
            c.update(dl)
        else:
            ds.append(dict(dl, id=kb_id, tao=time.time()))
    DL.KICH_BAN.sua(ghi)
    if f.get("sau") == "chay":
        ok, tb = DC.kich_hoat(kb_id)
        return chuyen(f"{URL}/{kb_id}", f'Đã lưu kịch bản "{ten}". {tb}', ok)
    return chuyen(URL, f'Đã lưu kịch bản "{ten}". Bấm Chạy để kích hoạt.')


# ------------------------------------------------------------------ tien do
def trang_tien_do(kb_id):
    from ui import uem_trang_b as TB
    kb = DL.tim(_ds(), kb_id)
    if not kb:
        return chuyen(URL, "Không còn kịch bản này.", False)
    st = DL.TRANG_THAI.doc().get(kb_id, {})
    nhan, mau = _tom_tat(kb, st)
    tk = DL.tim(DL.tai_khoan_cong_khai(), kb.get("tai_khoan_id")) if kb.get("tai_khoan_id") else None
    hang = ""
    for m in sorted((st.get("may") or {}).values(), key=lambda x: x.get("ten", "")):
        n, mm = TT_MAY.get(m.get("tt"), (m.get("tt"), ""))
        buoc = "".join(f'<div style="margin:2px 0;">{chip(TT_BUOC.get(b["tt"], (b["tt"], ""))[0], TT_BUOC.get(b["tt"], ("", ""))[1])} {_esc(b["ten"])}'
                       f'{(" <span class=tk-ghi>" + _esc(b.get("tb", "")[:300]) + "</span>") if b.get("tb") else ""}</div>' for b in m.get("buoc", []))
        hang += (f'<tr><td><b>{_esc(m.get("ten", ""))}</b><div class="tk-ghi">lần thử {m.get("thu", 0)}</div></td><td>{chip(n, mm)}</td>'
                 f'<td>{buoc}</td><td class="tk-ghi">{_esc(gio(m.get("cap_nhat")))}</td></tr>')
    nk = "\n".join(reversed(st.get("nhat_ky", [])[-80:]))
    body = (TB._thanh_tab_cai("kb") + f'''<p><a class="tk-nut" href="{URL}">Quay lại</a></p>
    <div id="kb-khung"><div class="card"><h3 style="margin-top:0;">{_esc(kb["ten"])}</h3>
      <p class="tk-ghi">{len(kb.get("buoc", []))} phần mềm · {len(DC.may_cua_kich_ban(kb))} máy · {_esc(_mo_ta_thoi_gian(kb))} ·
        cài bằng {_esc(("tài khoản " + tk["user"]) if tk else "SYSTEM")}{" · lượt chạy bắt đầu " + _esc(gio(st.get("bat_dau"))) if st.get("bat_dau") else ""}</p>
      <p>{chip(nhan, mau)}</p><div style="margin:6px 0 12px;">{_chip_dem(st)}</div>
      <div class="tk-act">{_nut_dieu_khien(kb, st)} <a class="tk-nut" href="{URL}/sua?id={kb["id"]}">Sửa</a>
        {_nut(URL + "/" + kb["id"] + "/xoa", "Xóa", "do", "Xóa kịch bản " + kb["ten"] + " và tiến độ của nó?")}</div></div>
    <div class="card" style="overflow:auto;">{("<table class=tk-bang><tr><th>Máy</th><th>Trạng thái</th><th>Các bước</th><th>Cập nhật</th></tr>" + hang + "</table>") if hang
        else "<p class=tk-ghi>Chưa chạy lượt nào. Bấm Chạy để bắt đầu (kịch bản hẹn giờ sẽ chờ tới giờ hẹn).</p>"}</div>
    <div class="card"><h3 style="margin-top:0;">Nhật ký</h3><pre style="white-space:pre-wrap;max-height:320px;overflow:auto;margin:0;">{_esc(nk) or "Chưa có."}</pre></div></div>'''
            + _JS_LAM_MOI)
    return trang(body, "td")


def dang_ky(app):
    @app.route(URL)
    def uem_kb_ds():
        return trang_ds()

    @app.route(URL + "/sua")
    def uem_kb_sua():
        return trang_sua()

    @app.route(URL + "/luu", methods=["POST"])
    def uem_kb_luu():
        return luu()

    @app.route(URL + "/<kb_id>")
    def uem_kb_td(kb_id):
        return trang_tien_do(kb_id)

    @app.route(URL + "/<kb_id>/tt")
    def uem_kb_tt(kb_id):
        kb = DL.tim(_ds(), kb_id)
        if not kb:
            return jsonify({"loi": "Không còn kịch bản này."})
        st = DL.TRANG_THAI.doc().get(kb_id, {})
        return jsonify({"nhan": _tom_tat(kb, st)[0], "bat": bool(st.get("bat")), "dem": _dem(st), "may": st.get("may", {})})

    def _viec(kb_id, ham, ve=None):
        if not DL.tim(_ds(), kb_id):
            return chuyen(URL, "Không còn kịch bản này.", False)
        ok, tb = ham(kb_id)
        return chuyen(ve or f"{URL}/{kb_id}", tb, ok)

    @app.route(URL + "/<kb_id>/chay", methods=["POST"])
    def uem_kb_chay(kb_id):
        return _viec(kb_id, DC.kich_hoat)

    @app.route(URL + "/<kb_id>/dung", methods=["POST"])
    def uem_kb_dung(kb_id):
        return _viec(kb_id, DC.dung)

    @app.route(URL + "/<kb_id>/tiep-tuc", methods=["POST"])
    def uem_kb_tiep(kb_id):
        return _viec(kb_id, DC.tiep_tuc)

    @app.route(URL + "/<kb_id>/xoa", methods=["POST"])
    def uem_kb_xoa(kb_id):
        kb = DL.tim(_ds(), kb_id)
        if not kb:
            return chuyen(URL, "Không còn kịch bản này.", False)
        rieng = _lich_rieng(kb)
        DC.xoa_kich_ban(kb_id)
        if rieng:
            DL.LICH.sua(lambda ds: ds.__setitem__(slice(None), [x for x in ds if x["id"] != rieng["id"]]))
        return chuyen(URL, f'Đã xóa kịch bản "{kb["ten"]}".')
