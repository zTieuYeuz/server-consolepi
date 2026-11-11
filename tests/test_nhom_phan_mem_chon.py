# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Nhom phan mem phai chon duoc o Cai Windows qua mang va Cai phan mem qua Agent (anh Thoai 29/10/2026: 'chua thay nhom phan mem')."""
import json
import os
import re
import sys

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))

NHOM = [{"id": "g1", "ten": "Bộ văn phòng", "muc": [{"loai": "phanmem", "ref": "7z.exe", "ten": "7z"}, {"loai": "phanmem", "ref": "vlc.exe"},
                                                      {"loai": "ungdung", "ref": "ud1"}, {"loai": "script", "ref": "don-dep.ps1"}]}]


def _nap(monkeypatch, nhom):
    from consolesystem.core import tk_dulieu as DL
    monkeypatch.setattr(DL.NHOM_TN, "doc", lambda: nhom)
    return DL


def test_thanh_vien_nhom_theo_loai(monkeypatch):
    DL = _nap(monkeypatch, NHOM)
    g = DL.nhom_phan_mem()[0]
    assert g["phanmem"] == ["7z.exe", "vlc.exe"] and g["ungdung"] == ["ud1"] and g["script"] == ["don-dep.ps1"]


def test_khoi_nhom_co_o_tick_va_du_lieu(monkeypatch):
    _nap(monkeypatch, NHOM)
    from consolesystem.web.chon_nhom_pm import khoi_nhom
    h = khoi_nhom("app", "ungdung", "nhom", "chon")
    assert "Bộ văn phòng" in h and 'class="chon"' in h and 'name="nhom" value="g1"' in h
    m = json.loads(re.search(r'data-m="([^"]*)"', h).group(1).replace("&quot;", '"'))
    assert m == {"app": ["7z.exe", "vlc.exe"], "ungdung": ["ud1"]}
    h2 = khoi_nhom("pm", the=False)
    assert "<h4" in h2 and 'class="card"' not in h2 and "name=\"nhom\"" not in h2
    assert json.loads(re.search(r'data-m="([^"]*)"', h2).group(1).replace("&quot;", '"')) == {"pm": ["7z.exe", "vlc.exe"]}


def test_khoi_nhom_trong_chi_cach_tao(monkeypatch):
    _nap(monkeypatch, [])
    from consolesystem.web.chon_nhom_pm import khoi_nhom
    h = khoi_nhom("app")
    assert "Chưa có nhóm" in h and "/deployos/trienkhai/nhom-tn" in h and "cs-nhom-pm" not in h


def test_agent_luu_buoc_ung_dung_nhieu_file():
    """Kich ban Agent: buoc 'Ung dung nhieu file' va 'Nhom phan mem' chon duoc trong trinh dung buoc co thu tu (buoc_json, A5 2.0.6); bieu mau cu (pm/ud) van duoc nhan."""
    src = open(os.path.join(GOC, "src", "consolesystem", "features", "uem", "uem_kichban.py"), encoding="utf-8").read()
    assert 'getlist("ud")' in src and '"loai": "ungdung"' in src
    assert 'LOAI_AGENT = ("phanmem", "ungdung", "script", "winget", "nguon", "nhom")' in src and 'name="buoc_json"' in src
