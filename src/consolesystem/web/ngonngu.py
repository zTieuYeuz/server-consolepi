# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Ngon ngu giao dien: Tieng Viet (goc) / English. Chon o Cai dat chung, luu cookie `cs-lang` tren trinh duyet (moi nguoi xem
chon rieng, khong doi cua nguoi khac). Dich luc tra trang: thay nguyen van tung doan chu (ngoai <script>/<style>) va
placeholder/title/aria-label theo tu dien assets/i18n/en.json. Chuoi chua co trong tu dien thi giu tieng Viet.
"""
import json
import re

from consolesystem.core import taisan as _taisan

_TU_DIEN = {"en": json.loads(_taisan.doc("i18n/en.json"))}
NGON_NGU = (("vi", "Tiếng Việt"), ("en", "English"))
_KHOI = re.compile(r"(<script\b.*?</script>|<style\b.*?</style>|<textarea\b.*?</textarea>|<pre\b.*?</pre>)", re.S | re.I)
_CHU = re.compile(r">([^<]+)<")
_THUOC_TINH = re.compile(r'\b(placeholder|title|aria-label)="([^"]*)"')


def hien_tai():
    try:
        from flask import request
        l = request.cookies.get("cs-lang", "vi")
    except Exception:
        return "vi"
    return l if l in _TU_DIEN else "vi"


def _dich_doan(m, td):
    tho = m.group(1)
    goc = " ".join(tho.split())
    if not goc or goc not in td:
        return m.group(0)
    dau = tho[:len(tho) - len(tho.lstrip())]
    cuoi = tho[len(tho.rstrip()):]
    return ">" + dau + td[goc] + cuoi + "<"


def dich_html(html, ngon_ngu=None):
    l = ngon_ngu or hien_tai()
    td = _TU_DIEN.get(l)
    if not td:
        return html
    phan = _KHOI.split(html)
    for i in range(0, len(phan), 2):                    # phan le la <script>/<style>/... giu nguyen
        s = _CHU.sub(lambda m: _dich_doan(m, td), phan[i])
        phan[i] = _THUOC_TINH.sub(lambda m: f'{m.group(1)}="{td.get(" ".join(m.group(2).split()), m.group(2))}"', s)
    out = "".join(phan)
    return out.replace('<html lang="vi">', f'<html lang="{l}">', 1)
