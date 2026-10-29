# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Trang Cap nhat phai tim thay duoc: co trong menu Cai dat, co nut trong Cai dat chung (chi quan tri), giao dien khong con kenh Thu nghiem."""
import os
import sys

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))


def test_menu_cai_dat_co_cap_nhat_va_tim_kiem_khong_trung():
    from ui import layout as L
    nhom = next(m for m in L.NAV_ITEMS if m[0] == "nhom" and m[1] == "Cài đặt")
    assert any(h == "/cap-nhat" and ten == "Cập nhật" for h, ten, _i in nhom[3])
    assert L.ICON_MUC.get("/cap-nhat") == "refresh"
    assert sum(1 for x in L.TIM_THEM if x[1] == "/cap-nhat") == 0       # da len menu: khong lap trong o tim nhanh


def test_nut_cap_nhat_trong_cai_dat_chung_chi_cho_quan_tri(monkeypatch):
    from consolesystem.features.settings import settings as S
    from consolesystem.web import auth
    monkeypatch.setattr(auth, "la_quan_tri", lambda user=None: True)
    assert 'href="/cap-nhat"' in S._khoi_cap_nhat()
    monkeypatch.setattr(auth, "la_quan_tri", lambda user=None: False)
    assert S._khoi_cap_nhat() == ""


def test_giao_dien_khong_con_kenh_thu_nghiem():
    from consolesystem.features.updates import capnhat_ui as U
    h = U._khoi_cai_dat({"kenh": "on-dinh", "hoi_dinh_ky": True})
    assert "thu-nghiem" not in h and "Thử nghiệm" not in h and 'name="kenh"' not in h and "Ổn định" in h
