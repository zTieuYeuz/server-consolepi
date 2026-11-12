# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Khung nhap MAT KHAU dung chung (2.0.7 cum 3): truoc day moi trang tu viet o nhap mat khau (do rong, nhan, nut hien/an khac nhau; RustDesk chung de
dang chu). Thu tu cac o trong form remote: May -> Cong -> Tai khoan -> Mat khau. Gia tri DA LUU o may chu KHONG bao gio dua vao HTML (chi gioi thieu
'da dat' qua placeholder); nut Hien/An chi doi kieu o cho chu nguoi dung vua go. Khong tu ghi nho trong trinh duyet (autocomplete=new-password)."""
from html import escape as _e

_JS_HIEN = ("var i=this.previousElementSibling;var a=i.type==='password';i.type=a?'text':'password';"
            "this.textContent=a?'Ẩn':'Hiện';this.setAttribute('aria-pressed',a?'true':'false');")


def o_mat_khau(ten, nhan="Mật khẩu", placeholder="", bat_buoc=False, id_="", autocomplete="new-password", rong_toi_da=320, nhan_ben_ngoai=True):
    """HTML khung mat khau: nhan phia tren, o rong 100% (toi da `rong_toi_da` px, cao 42 px) + nut con mat Hien/An ben phai."""
    idh = f' id="{_e(id_)}"' if id_ else ""
    lab = f'<label{(" for=%s" % chr(34) + _e(id_) + chr(34)) if id_ else ""} style="margin-top:0;">{_e(nhan)}</label>' if (nhan and nhan_ben_ngoai) else ""
    return (f'<div class="mk-khung">{lab}<span style="display:flex;gap:6px;align-items:center;">'
            f'<input type="password" name="{_e(ten)}"{idh} autocomplete="{_e(autocomplete)}" placeholder="{_e(placeholder)}"{" required" if bat_buoc else ""} '
            f'style="flex:1 1 220px;min-width:200px;max-width:{int(rong_toi_da)}px;height:42px;margin:0;">'
            f'<button type="button" class="gray small" aria-pressed="false" style="height:42px;margin:0;" onclick="{_e(_JS_HIEN)}">Hiện</button></span></div>')
