# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Thoat ky tu dac biet khi nhung chuoi vao HTML/XML. Truoc day co 12 ban `_esc` rai trong ui/ voi 4 HANH VI KHAC NHAU nhe
(khac o cho xu ly gia tri 0/False/None va o dau nhay); gom thanh 4 ham co ten ro rang, giu NGUYEN hanh vi tung noi
(doi hanh vi lam lech giao dien/XML da kiem bang hop dong trang + golden).
"""
import html as _html
from xml.sax.saxutils import escape as _xml_escape


def esc(s):
    """HTML: gia tri 'rong' (None, 0, False, '') -> ''. Thoat & < > "  (ban cu o home, logs, commands, ssh, network, soanlenh...)"""
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def esc_none(s):
    """HTML: chi None -> '' (0 va False van hien '0'/'False'). Thoat & < > "  (ban cu o tk_trang)."""
    return (str(s if s is not None else "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def esc_html(s):
    """HTML day du: chi None -> ''; thoat ca dau nhay don (&#x27;) - dung cho thuoc tinh bao dau nhay don (ban cu o uem_trang)."""
    return _html.escape(str(s if s is not None else ""), quote=True)


def esc_xml(s):
    """XML: gia tri rong -> ''; chi thoat & < > (KHONG thoat dau nhay) - dung trong noi dung phan tu XML (ban cu o unattend)."""
    return _xml_escape(str(s or ""))


def esc_html_rong(s):
    """HTML: gia tri 'rong' (None, 0, False, '') -> ''; html.escape day du (thoat ca dau nhay don) - ban cu o lichsu, tiendo, wol."""
    return _html.escape(str(s or ""))
