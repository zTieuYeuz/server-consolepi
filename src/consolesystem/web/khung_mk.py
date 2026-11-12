# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Khung nhap MAT KHAU dung chung (2.0.7 cum 3): truoc day moi trang tu viet o nhap mat khau (do rong, nhan, nut hien/an khac nhau; RustDesk chung de
dang chu). Thu tu cac o trong form remote: May -> Cong -> Tai khoan -> Mat khau. Gia tri DA LUU o may chu KHONG bao gio dua vao HTML (chi gioi thieu
'da dat' qua placeholder); nut Hien/An chi doi kieu o cho chu nguoi dung vua go. Khong tu ghi nho trong trinh duyet (autocomplete=new-password).
Ban va 05 (NV6): nhan GAN voi o (id/for; khong co nhan thay duoc thi aria-label), nut Hien/An la nut bieu tuong 44 px co ten doc man hinh doi theo trang thai
(khong dung aria-pressed), kich thuoc nam trong CSS: PC cao 42 px, cam ung (cd-cu hoac duoi 760 px) cao 50 px, o va nut cung chieu cao."""
from html import escape as _e

_CSS = ("<style>.mk-khung{max-width:100%;flex:1 1 240px}.mk-khung .mk-h{display:flex;gap:6px;align-items:stretch}"
        ".mk-khung input{flex:1 1 160px;min-width:0;height:42px;margin:0}"
        ".mk-khung .mk-hien{flex:none;width:44px;min-width:44px;height:42px;margin:0;padding:0;display:inline-grid;place-items:center}"
        ".mk-khung .mk-hien svg{width:20px;height:20px;pointer-events:none}.mk-khung .mk-hien [hidden]{display:none}"
        ".mk-khung input::placeholder{font-size:13px}body.cd-cu .mk-khung input,body.cd-cu .mk-khung .mk-hien{height:50px}body.cd-cu .mk-khung .mk-hien{width:50px;min-width:50px}"
        "@media(max-width:760px){.mk-khung input,.mk-khung .mk-hien{height:50px}.mk-khung .mk-hien{width:50px;min-width:50px}}</style>")
_MAT = ('<svg class="mk-m" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>')
_MAT_GACH = ('<svg class="mk-d" hidden viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
             '<path d="M3 3l18 18M10.6 5.1A10.7 10.7 0 0 1 12 5c6.4 0 10 7 10 7a17 17 0 0 1-3.2 4.2M6.6 6.6A17 17 0 0 0 2 12s3.6 7 10 7a10 10 0 0 0 4.4-1"/>'
             '<path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/></svg>')
_JS_HIEN = ("var i=this.parentNode.querySelector('input');var a=i.type==='password';i.type=a?'text':'password';"
            "this.setAttribute('aria-label',a?'Ẩn mật khẩu':'Hiện mật khẩu');this.title=a?'Ẩn mật khẩu':'Hiện mật khẩu';"
            "this.querySelector('.mk-m').hidden=a;this.querySelector('.mk-d').hidden=!a;")


def o_mat_khau(ten, nhan="Mật khẩu", placeholder="", bat_buoc=False, id_="", autocomplete="new-password", rong_toi_da=320, nhan_ben_ngoai=True, aria=""):
    """HTML khung mat khau: nhan phia tren (gan voi o bang for/id), o rong 100% (toi da `rong_toi_da` px) + nut con mat Hien/An ben phai.
    `id_` rong thi lay 'mk-<ten>'; hai khung cung ten tren MOT trang phai truyen id_ khac nhau. Khong co nhan thay duoc: truyen `aria` (ten doc man hinh cua o)."""
    id_ = id_ or "mk-" + ten
    co_nhan = bool(nhan and nhan_ben_ngoai)
    lab = f'<label for="{_e(id_)}" style="margin-top:0;">{_e(nhan)}</label>' if co_nhan else ""
    ten_dm = "" if co_nhan else f' aria-label="{_e(aria or nhan or "Mật khẩu")}"'
    return (f'{_CSS}<div class="mk-khung">{lab}<span class="mk-h" style="max-width:{int(rong_toi_da)}px;">'
            f'<input type="password" name="{_e(ten)}" id="{_e(id_)}" autocomplete="{_e(autocomplete)}" placeholder="{_e(placeholder)}"{ten_dm}{" required" if bat_buoc else ""}>'
            f'<button type="button" class="gray small mk-hien" aria-label="Hiện mật khẩu" title="Hiện mật khẩu" onclick="{_e(_JS_HIEN)}">{_MAT}{_MAT_GACH}</button></span></div>')
