# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Khoi "Nhom phan mem" dung chung cho cac man hinh chon phan mem de cai (Cai Windows qua mang, Cai phan mem qua Agent):
tick 1 nhom -> tu tick san cac phan mem trong nhom (van bo tick tung cai ben duoi duoc). Nhom tao o Tai nguyen may > Nhom phan mem.
"""
import html
import json

from consolesystem.core import tk_dulieu as DL

LINK_NHOM = "/deployos/trienkhai/nhom-tn"
_JS = """<script>(function(){document.querySelectorAll('input.cs-nhom-pm').forEach(function(c){c.addEventListener('change',function(){
  var m=JSON.parse(c.getAttribute('data-m'));Object.keys(m).forEach(function(n){m[n].forEach(function(v){
    document.querySelectorAll('input[name="'+n+'"]').forEach(function(i){if(i.value===v)i.checked=c.checked;});});});});});})();</script>"""


def khoi_nhom(o_phanmem, o_ungdung=None, ten_o_nhom=None, kieu="tk-o", the=True):
    """HTML the "Nhom phan mem". o_phanmem/o_ungdung = name cua o tick phan mem / ung dung tren trang (None = trang khong co).
    ten_o_nhom: neu co thi o tick nhom cung duoc gui len (de may chu xu ly phan khong nam tren trang, vd script).
    the=False: khong boc the (dung ben trong form da la the, tieu de nho)."""
    bao = (lambda t: f'<div class="card"><h3>Nhóm phần mềm</h3>{t}</div>') if the else (lambda t: f'<h4 class="tk-tieude">Nhóm phần mềm (chọn nhanh)</h4>{t}')
    ds = DL.nhom_phan_mem()
    if not ds:
        return bao(f'<p style="color:#8b93a1;font-size:13px;margin:0;">Chưa có nhóm nào. Nhóm gom nhiều phần mềm '
                   f'thành một gói để chọn một lần. Tạo ở <a href="{LINK_NHOM}">Tài nguyên máy › Nhóm phần mềm</a>.</p>')
    o = ""
    for g in ds:
        m = {o_phanmem: g["phanmem"]}
        if o_ungdung:
            m[o_ungdung] = g["ungdung"]
        n = len(g["phanmem"]) + (len(g["ungdung"]) if o_ungdung else 0) + len(g["script"])
        ten_o = f' name="{html.escape(ten_o_nhom)}" value="{html.escape(g["id"])}"' if ten_o_nhom else ""
        o += (f'<label class="{kieu}"><input type="checkbox" class="cs-nhom-pm"{ten_o} data-m="{html.escape(json.dumps(m), quote=True)}">'
              f'<span class="t"><b>{html.escape(g["ten"])}</b> <small class="d">{n} mục</small></span></label>')
    return bao(f'<p style="color:#8b93a1;font-size:13px;margin:0 0 8px;">Tick một nhóm để chọn sẵn tất cả phần mềm trong nhóm '
               f'(vẫn bỏ tick từng phần mềm bên dưới được). Tạo hoặc sửa nhóm ở <a href="{LINK_NHOM}">Tài nguyên máy › Nhóm phần mềm</a>.</p>'
               f'<div class="tk-luoi">{o}</div>') + _JS
