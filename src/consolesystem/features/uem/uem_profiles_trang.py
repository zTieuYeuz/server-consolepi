# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Quan ly may tram - trang CAU HINH (PROFILES): danh sach, chi tiet (tab Tac vu / Ap dung cho / Ket qua / Van de), the loai tac vu + mau.
Route dang ky o uem_trang_b.register_uem; du lieu + vong ap dung o uem_profiles.py; loai tac vu o uem_buoc.py."""
from flask import abort, request

from ui import tk_dulieu as DL
from ui import uem_buoc as UB
from ui import uem_dulieu as UD
from ui import uem_profiles as UP
from ui.uem_trang import _esc, chip, gio, ten_may, trang


_CSS_PF = """<style>
.pf-dau{display:flex;gap:16px;align-items:flex-start;justify-content:space-between;flex-wrap:wrap}.pf-dau h2{margin:0 0 4px}
.pf-chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.pf-act{display:flex;gap:8px;flex-wrap:wrap}
.pf-tabs{display:flex;gap:6px;flex-wrap:wrap;margin:16px 0 12px}.pf-tabs button{min-height:40px}.pf-tabs button.on{border-color:var(--nhan);background:var(--nhan-mo);color:var(--nhan-dam)}
.pf-luoi{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.pf-nhom{border:1px solid var(--vien);border-radius:12px;padding:12px 14px;background:var(--nen-phu,transparent)}
.pf-nhom h4{margin:0 0 2px;font-size:15px}.pf-nhom p{margin:0 0 8px;color:var(--chu-mo);font-size:12.5px}
.pf-nhom a{display:block;padding:7px 10px;margin:4px 0;border-radius:8px;border:1px solid var(--vien);text-decoration:none;color:inherit;font-size:13.5px}
.pf-nhom a:hover{border-color:var(--nhan);background:var(--nhan-mo)}
.pf-mau{display:flex;gap:8px;flex-wrap:wrap}.pf-mau a{font-size:13px}
.pf-task{display:flex;gap:12px;align-items:center;padding:10px 0;border-bottom:1px solid var(--vien)}.pf-task:last-child{border-bottom:0}
.pf-task .ic{font-size:20px;width:30px;text-align:center}.pf-task .nd{flex:1;min-width:0}.pf-task .nd b{display:block}
.pf-task.tat{opacity:.55}.pf-task form{display:flex;gap:4px;flex-wrap:wrap}
</style>"""


def _o_nhap(f, gt=None):
    ten, nhan, kieu, bb, mac_dinh, ghi = f
    gt = mac_dinh if gt is None else gt
    h = f"<label>{_esc(nhan)}{' *' if bb else ''}</label>"
    if kieu == "checkbox":
        return f'<label class="tk-o"><input type="checkbox" name="{ten}" value="1"{" checked" if gt else ""}><span>{_esc(nhan)}</span></label>'
    if kieu == "textarea":
        h += f'<textarea name="{ten}" rows="7" style="width:100%;max-width:none;font-family:var(--mono);">{_esc(gt)}</textarea>'
    elif kieu.startswith("select:"):
        h += f'<select name="{ten}" style="max-width:420px;">' + "".join(f'<option value="{_esc(v)}"{" selected" if v == gt else ""}>{_esc(n) or "(không)"}</option>' for v, n in UB.gia_tri_chon(kieu)) + "</select>"
    else:
        h += f'<input type="{"password" if kieu == "password" else "text"}" name="{ten}" value="{"" if kieu == "password" else _esc(gt)}"{" autocomplete=new-password" if kieu == "password" else ""}>'
    if ghi:
        h += f'<div class="tk-ghi">{_esc(ghi)}</div>'
    return h


GIAI_THICH_PROFILE = """<div class="card"><h3>Profile là gì?</h3>
<p><b>Profile là một "bộ cấu hình chuẩn" giữ cho nhiều máy luôn đúng.</b> Bạn khai báo máy phải như thế nào (có Chrome, bật tường lửa, mở Remote Desktop, tắt dịch vụ in...),
Console System kiểm tra từng máy và chỉ sửa phần chưa đúng. Cứ vài phút kiểm tra lại: máy bị đổi sẽ được đưa về đúng, máy mới cũng được cấu hình theo.</p>
<ol class="tk-ghi" style="margin:8px 0 0 18px;line-height:1.7;"><li><b>Tạo profile</b>, đặt tên.</li><li>Tab <b>Tác vụ</b>: bấm loại việc cần làm (hoặc một mẫu có sẵn), điền rồi lưu.</li>
<li>Tab <b>Áp dụng cho</b>: chọn tất cả máy, nhóm máy hoặc thẻ.</li><li>Bấm <b>Bật profile</b>. Kết quả từng máy ở tab <b>Kết quả</b>.</li></ol></div>"""


def trang_profiles():
    ds = UD.PROFILES.doc()
    the_ds = UD.THE.doc()
    hang = ""
    for p in ds:
        may = UP.may_ap_dung(p)
        loi = len({m["id"] for m, _t, _tb in UP.van_de(p["id"])})
        ds_nhom = [g["ten"] + " (nhóm)" for g in DL.NHOM_MAY.doc() if g["id"] in p.get("nhom_may", [])]
        pham_vi = "Tất cả máy" if p.get("ap_dung_tat_ca") else (", ".join(ds_nhom + [t["ten"] for t in the_ds if t["id"] in p.get("the", [])]) or "Chưa chọn máy")
        icon = "".join(dict.fromkeys(UB.NHOM_ICON.get(UB.CAC_LOAI.get(t["loai"], ("", ""))[1], "") for t in p.get("tasks", [])))
        hang += (f'<tr><td><a href="/uem/profiles/{p["id"]}"><b>{_esc(p["ten"])}</b></a><div class="tk-ghi">{_esc(p.get("mo_ta", ""))}</div></td><td>{_esc(pham_vi)}<div class="tk-ghi">{len(may)} máy</div></td>'
                 f'<td>{len(p.get("tasks", []))} <span title="Loại tác vụ">{icon}</span></td><td>{chip("Đang bật", "xanh") if p.get("bat") else chip("Tắt")}</td>'
                 f'<td>{chip(str(loi) + " máy lỗi", "do") if loi else chip("Không lỗi", "xanh")}</td><td><a class="tk-nut" href="/uem/profiles/{p["id"]}">Mở</a></td></tr>')
    body = GIAI_THICH_PROFILE + f"""<div class="card"><form method="POST" action="/uem/profiles/tao" class="tk-f tk-hang" style="gap:10px;align-items:flex-end;">
      <div style="flex:1;min-width:220px;"><label>Tạo profile mới</label><input type="text" name="ten" required placeholder="Ví dụ: Máy văn phòng chuẩn" style="margin:0;"></div>
      <div style="flex:1;min-width:220px;"><label>Mô tả (tuỳ chọn)</label><input type="text" name="mo_ta" style="margin:0;"></div>
      <button class="tk-nut chinh" type="submit" style="height:42px;">Tạo</button></form></div>
    <h2>Các profile ({len(ds)})</h2><div class="card">{('<table class="tk-bang"><tr><th>Profile</th><th>Áp dụng cho</th><th>Tác vụ</th><th>Trạng thái</th><th>Vấn đề</th><th></th></tr>' + hang + '</table>') if ds else '<p class="tk-ghi">Chưa có profile nào. Tạo ở ô phía trên.</p>'}</div>
    <p class="tk-ghi">Kiểm tra lại mỗi {int(UD.cai_dat().get("tan_suat_profile", 30))} phút (đổi ở Quản trị, Cài đặt).</p>"""
    return trang(body, "pf")


def _the_nhom_loai(pid):
    """Luoi the: moi nhom loai tac vu 1 the, bam ten tac vu de mo form."""
    nhom = {}
    for k, (ten, ng, _f) in UB.CAC_LOAI.items():
        nhom.setdefault(ng, []).append((k, ten.split(": ", 1)[-1]))
    o = "".join(f'<div class="pf-nhom"><h4>{UB.NHOM_ICON.get(ng, "")} {_esc(UB.NHOM_LOAI[ng])}</h4><p>{_esc(UB.NHOM_MO_TA.get(ng, ""))}</p>'
                + "".join(f'<a href="/uem/profiles/{pid}?loai={k}#tac-vu">{_esc(t[0].upper() + t[1:])}</a>' for k, t in nhom[ng]) + "</div>"
                for ng in UB.NHOM_LOAI if ng in nhom)
    mau = "".join(f'<a class="tk-nut" href="/uem/profiles/{pid}?loai={l}&mau={k}#tac-vu">{UB.NHOM_ICON.get(UB.CAC_LOAI[l][1], "")} {_esc(n)}</a>' for k, (n, l, _t) in UB.MAU.items())
    return (f'<h3 style="margin:18px 0 6px;">Thêm tác vụ</h3><p class="tk-ghi" style="margin-top:0;">Bấm một mẫu có sẵn, hoặc chọn loại việc cần làm bên dưới.</p>'
            f'<div class="pf-mau" style="margin-bottom:14px;">{mau}</div><div class="pf-luoi">{o}</div>')


def trang_profile(pid):
    p = DL.tim(UD.PROFILES.doc(), pid)
    if not p:
        abort(404)
    the_ds = UD.THE.doc()
    tt = UD.TRANG_THAI_PROFILE.doc().get(pid, {})
    may = UP.may_ap_dung(p)
    van = UP.van_de(pid)
    n_loi = len({m["id"] for m, _t, _tb in van})
    o_nhom = "".join(f'<label class="tk-o"><input type="checkbox" name="nhom_may" value="{g["id"]}"{" checked" if g["id"] in p.get("nhom_may", []) else ""}><span><b>{_esc(g["ten"])}</b><small>{len(g.get("may", []))} máy</small></span></label>' for g in DL.NHOM_MAY.doc())
    o_the = "".join(f'<label class="tk-o"><input type="checkbox" name="the" value="{t["id"]}"{" checked" if t["id"] in p.get("the", []) else ""}><span><b>{_esc(t["ten"])}</b></span></label>' for t in the_ds)
    # danh sach tac vu
    ht = ""
    tasks = p.get("tasks", [])
    for i, t in enumerate(tasks):
        n_ok = sum(1 for m in may if tt.get(m["id"], {}).get("tasks", {}).get(t["id"], {}).get("tt") in ("da_dat", "da_lam", "da_chay_truoc"))
        n_l = sum(1 for m in may if tt.get(m["id"], {}).get("tasks", {}).get(t["id"], {}).get("tt") == "loi")
        ng = UB.CAC_LOAI.get(t["loai"], ("", "powershell"))[1]
        ht += (f'<div class="pf-task{"" if t.get("bat", True) else " tat"}"><div class="ic">{UB.NHOM_ICON.get(ng, "")}</div><div class="nd"><b>{i + 1}. {_esc(UB.mo_ta(t["loai"], t["tham_so"]))}</b>'
               f'<span class="tk-ghi">{_esc(UB.NHOM_LOAI.get(ng, ""))} · {"agent tự áp dụng cả khi mất kết nối" if UP.tu_tri(t) else "cần Console System"}{" · lỗi thì vẫn chạy tiếp" if t.get("bo_qua_loi") else ""}'
               f'{"" if t.get("bat", True) else " · ĐANG TẮT"}</span><div style="margin-top:4px;">{chip(f"Đúng {n_ok}/{len(may)} máy", "xanh" if may and n_ok == len(may) else "")}{" " + str(chip(f"Lỗi {n_l} máy", "do")) if n_l else ""}</div></div>'
               f'<form method="POST" action="/uem/profiles/{pid}/task/{t["id"]}/hanh-dong">'
               f'<button class="tk-nut" name="viec" value="len" title="Lên"{" disabled" if i == 0 else ""}>↑</button><button class="tk-nut" name="viec" value="xuong" title="Xuống"{" disabled" if i == len(tasks) - 1 else ""}>↓</button>'
               f'<a class="tk-nut" href="/uem/profiles/{pid}?sua={t["id"]}#tac-vu">Sửa</a><button class="tk-nut" name="viec" value="bat_tat">{"Tắt" if t.get("bat", True) else "Bật"}</button>'
               f'<button class="tk-nut do" name="viec" value="xoa" onclick="return confirm(\'Xóa tác vụ này?\');">Xóa</button></form></div>')
    # form them / sua
    sua = next((t for t in tasks if t["id"] == request.args.get("sua")), None)
    loai = (sua or {}).get("loai") or request.args.get("loai", "")
    mau = UB.MAU.get(request.args.get("mau", ""))
    if loai in UB.CAC_LOAI:
        gt = (sua or {}).get("tham_so") or (mau[2] if mau and mau[1] == loai else {})
        cac_o = "".join(_o_nhap(f, gt.get(f[0]) if gt else None) for f in UB.CAC_LOAI[loai][2])
        ng = UB.CAC_LOAI[loai][1]
        phan_them = (f'<div class="card" id="form-task" style="margin-top:16px;border-color:var(--nhan);"><div class="tk-hang" style="justify-content:space-between;">'
                     f'<h3 style="margin:0;">{UB.NHOM_ICON.get(ng, "")} {"Sửa" if sua else "Thêm"}: {_esc(UB.CAC_LOAI[loai][0])}</h3>'
                     f'<a class="tk-nut" href="/uem/profiles/{pid}#tac-vu">← Chọn loại khác</a></div>'
                     f'<form method="POST" action="/uem/profiles/{pid}/task/luu" class="tk-f"><input type="hidden" name="loai_tac_vu" value="{loai}"><input type="hidden" name="task_id" value="{(sua or {}).get("id", "")}">'
                     f'{cac_o}<label class="tk-o"><input type="checkbox" name="bo_qua_loi" value="1"{" checked" if (sua or {}).get("bo_qua_loi") else ""}><span>Nếu tác vụ này lỗi, vẫn chạy các tác vụ sau</span></label>'
                     f'{"<p class=tk-ghi>Để trống ô mật khẩu = giữ mật khẩu cũ.</p>" if sua and loai == "user_them" else ""}'
                     f'<div class="tk-hang" style="margin-top:12px;gap:8px;"><button class="tk-nut chinh" type="submit">{"Lưu thay đổi" if sua else "Thêm vào profile"}</button>'
                     f'<a class="tk-nut" href="/uem/profiles/{pid}#tac-vu">Hủy</a></div></form></div>')
    else:
        phan_them = _the_nhom_loai(pid)
    # ket qua tung may
    hm = ""
    for m in may:
        st = tt.get(m["id"], {})
        hm += (f'<tr><td><a href="/uem/may/{m["id"]}">{_esc(ten_may(m))}</a></td><td>{chip({"ok": "Đúng cấu hình", "loi": "Có lỗi", "offline": "Không kết nối", "dang": "Đang chạy"}.get(st.get("trang_thai"), "Chưa chạy"), {"ok": "xanh", "loi": "do", "offline": "vang"}.get(st.get("trang_thai"), ""))}</td>'
               f'<td>{_esc(gio(st.get("luc")) if st.get("luc") else "—")}</td><td>{_esc(st.get("tom_tat", ""))}</td></tr>')
    hv = "".join(f'<tr><td><a href="/uem/may/{m["id"]}">{_esc(ten_may(m))}</a></td><td>{_esc(tk)}</td><td>{_esc(tb)}</td></tr>' for m, tk, tb in van)
    ds_nhom = [g["ten"] for g in DL.NHOM_MAY.doc() if g["id"] in p.get("nhom_may", [])] + [t["ten"] for t in the_ds if t["id"] in p.get("the", [])]
    pham_vi = "tất cả máy" if p.get("ap_dung_tat_ca") else (", ".join(ds_nhom) or "chưa chọn máy")
    body = _CSS_PF + f"""<p><a class="tk-nut" href="/uem/profiles">← Danh sách profile</a></p>
    <div class="card"><div class="pf-dau"><div><h2>{_esc(p["ten"])}</h2><div class="tk-ghi">{_esc(p.get("mo_ta", ""))}</div>
      <div class="pf-chips">{chip("Đang bật", "xanh") if p.get("bat") else chip("Đang tắt", "vang")}{chip(f"{len(tasks)} tác vụ")}{chip(f"Áp dụng cho {pham_vi} ({len(may)} máy)")}{chip(f"{n_loi} máy lỗi", "do") if n_loi else chip("Không lỗi", "xanh")}</div></div>
      <div class="pf-act"><form method="POST" action="/uem/profiles/{pid}/bat-tat"><button class="tk-nut {"do" if p.get("bat") else "chinh"}" type="submit">{"Tắt profile" if p.get("bat") else "Bật profile"}</button></form>
        <form method="POST" action="/uem/profiles/{pid}/ap-dung"><button class="tk-nut xanh" type="submit"{" disabled" if not tasks or not may else ""}>Áp dụng ngay ({len(may)} máy)</button></form>
        <form method="POST" action="/uem/profiles/{pid}/xoa" onsubmit="return confirm('Xóa profile này? Máy giữ nguyên cấu hình đã áp dụng.');"><button class="tk-nut do" type="submit">Xóa</button></form></div></div></div>
    <div class="pf-tabs"><button type="button" class="tk-nut" data-t="tac-vu">Tác vụ ({len(tasks)})</button><button type="button" class="tk-nut" data-t="ap-dung">Áp dụng cho ({len(may)} máy)</button>
      <button type="button" class="tk-nut" data-t="ket-qua">Kết quả từng máy</button><button type="button" class="tk-nut" data-t="van-de">Vấn đề ({len(van)})</button></div>
    <section data-pt="tac-vu"><div class="card"><p class="tk-ghi" style="margin-top:0;">Tác vụ chạy lần lượt từ trên xuống. Máy đã đúng thì tự bỏ qua.</p>
      {ht or '<p class="tk-ghi">Chưa có tác vụ nào.</p>'}{phan_them}</div></section>
    <section data-pt="ap-dung" hidden><div class="card"><form method="POST" action="/uem/profiles/{pid}/luu" class="tk-f">
      <label>Tên</label><input type="text" name="ten" value="{_esc(p["ten"])}" required><label>Mô tả</label><input type="text" name="mo_ta" value="{_esc(p.get("mo_ta", ""))}">
      <label class="tk-o"><input type="checkbox" name="ap_dung_tat_ca" value="1" id="pf-tatca"{" checked" if p.get("ap_dung_tat_ca") else ""}><span><b>Áp dụng cho tất cả máy</b><small>Bỏ chọn để chỉ áp dụng cho nhóm máy hoặc máy có thẻ bên dưới</small></span></label>
      <div id="pf-chon"><label>Nhóm máy</label><div class="tk-luoi">{o_nhom or '<span class="tk-ghi">Chưa có nhóm máy, tạo ở Máy tính (chọn máy, Tạo nhóm).</span>'}</div>
      <label>Hoặc máy có thẻ</label><div class="tk-luoi">{o_the or '<span class="tk-ghi">Chưa có thẻ, tạo ở Quản trị, Thẻ.</span>'}</div></div>
      <label class="tk-o"><input type="checkbox" name="bat" value="1"{" checked" if p.get("bat") else ""}><span><b>Bật profile</b><small>Tắt = tạm dừng, không áp dụng nữa</small></span></label>
      <div style="margin-top:12px;"><button class="tk-nut chinh" type="submit">Lưu</button></div></form></div></section>
    <section data-pt="ket-qua" hidden><div class="card">{('<table class="tk-bang"><tr><th>Máy</th><th>Trạng thái</th><th>Lần cuối</th><th>Tóm tắt</th></tr>' + hm + '</table>') if hm else '<p class="tk-ghi">Chưa có máy nào thuộc phạm vi áp dụng (tab Áp dụng cho).</p>'}</div></section>
    <section data-pt="van-de" hidden><div class="card">{('<table class="tk-bang"><tr><th>Máy</th><th>Tác vụ</th><th>Lỗi</th></tr>' + hv + '</table>') if hv else '<p class="tk-ghi">Không có vấn đề nào.</p>'}</div></section>
    <script>(function(){{var bs=document.querySelectorAll('.pf-tabs [data-t]'),ss=document.querySelectorAll('[data-pt]');
    function hien(t){{if(!document.querySelector('[data-pt="'+t+'"]'))t='tac-vu';ss.forEach(function(s){{s.hidden=s.dataset.pt!==t;}});bs.forEach(function(b){{b.classList.toggle('on',b.dataset.t===t);}});}}
    bs.forEach(function(b){{b.onclick=function(){{hien(b.dataset.t);history.replaceState(null,'','#'+b.dataset.t);}};}});
    hien((location.hash||'#tac-vu').slice(1)); var f=document.getElementById('form-task'); if(f)f.scrollIntoView({{block:'start'}});
    var c=document.getElementById('pf-tatca'),k=document.getElementById('pf-chon');function d(){{k.style.opacity=c.checked?.45:1;}}c.onchange=d;d();}})();</script>"""
    return trang(body, "pf")
