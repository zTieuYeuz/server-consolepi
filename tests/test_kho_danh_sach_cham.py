# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Kho qua Internet luc cham: danh sach phai doi toi 30 giay va thu lai 1 lan (do 29/10/2026: 0,5-21 giay)."""
import os
import sys

import requests

sys.path.insert(0, os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "src"))


class _Tra:
    status_code = 200

    def json(self):
        return {"ok": True, "muc": [{"k": "a"}]}


def test_danh_sach_thu_lai_khi_het_gio(monkeypatch):
    from ui import khotrungtam as K
    lan = []

    def get(url, headers=None, timeout=None):
        lan.append(timeout)
        if len(lan) == 1:
            raise requests.Timeout("cham")
        return _Tra()
    monkeypatch.setattr(K.requests, "get", get)
    assert K.danh_sach({"url": "https://x", "token": "t"}) == (True, [{"k": "a"}])
    assert lan == [30, 30]


def test_danh_sach_het_gio_hai_lan_bao_loi(monkeypatch):
    from ui import khotrungtam as K

    def get(url, headers=None, timeout=None):
        raise requests.Timeout("cham")
    monkeypatch.setattr(K.requests, "get", get)
    ok, tb = K.danh_sach({"url": "https://x", "token": "t"})
    assert not ok and "Không kết nối được tới kho" in tb
