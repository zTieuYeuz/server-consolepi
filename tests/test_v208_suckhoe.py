"""2.0.8 V1-2: kiem tra suc khoe sau nang cap di QUA nginx va kiem don vi da bat; khong doi hoi don vi chua bat (tranh hoan tac nham)."""
import os
import sys

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))


class _Ket:
    def __init__(self, ok):
        self.ok = ok


class _Resp:
    def __init__(self, code, js=None):
        self.status_code = code
        self._js = js or {}

    def json(self):
        return self._js


@pytest.fixture
def T(tmp_path, monkeypatch):
    from consolesystem.features.updates import thuc_te as T
    (tmp_path / "releases" / "2.0.8").mkdir(parents=True)
    (tmp_path / "releases" / "2.0.8" / "VERSION").write_text("2.0.8\n")
    monkeypatch.setattr(T.PH, "GOC_OPT", str(tmp_path))
    st = {"enabled": {"nginx", "console-system-term-local"}, "active": {"nginx", "console-system-term-local"}, "nginx_status": 200}

    def get(url, timeout=0):
        if ":5000/" in url:
            return _Resp(200, {"phien_ban": "2.0.8"})
        if st["nginx_status"] is None:
            import requests
            raise requests.ConnectionError("x")
        return _Resp(st["nginx_status"])

    def lenh(cmd, timeout=0):
        if cmd[:2] == ["nginx", "-t"]:
            return _Ket(True)
        if cmd[:2] == ["systemctl", "is-enabled"]:
            return _Ket(cmd[-1] in st["enabled"])
        if cmd[:2] == ["systemctl", "is-active"]:
            return _Ket(cmd[-1] in st["active"])
        return _Ket(True)
    monkeypatch.setattr(T.requests, "get", get)
    monkeypatch.setattr(T, "chay_lenh", lenh)
    return T, st


def test_tat_ca_tot_thi_dat(T):
    t, st = T
    assert t.suc_khoe("2.0.8") == (True, "ok")


def test_nginx_khong_proxy_duoc_thi_that_bai(T):
    t, st = T
    st["nginx_status"] = 502
    ok, ly = t.suc_khoe("2.0.8")
    assert not ok and "nginx" in ly
    st["nginx_status"] = None
    assert not t.suc_khoe("2.0.8")[0]


def test_don_vi_da_bat_ma_khong_chay_thi_that_bai(T):
    t, st = T
    st["active"].discard("console-system-term-local")
    ok, ly = t.suc_khoe("2.0.8")
    assert not ok and "console-system-term-local" in ly


def test_don_vi_chua_bat_thi_khong_doi_hoi(T):
    t, st = T                                                                   # term-phien chua bat (khong trong enabled) va khong chay -> van dat
    assert "console-system-term-phien" not in st["enabled"] and t.suc_khoe("2.0.8")[0]


def test_C4_don_vi_phai_go_ma_van_chay_thi_that_bai(T, tmp_path):
    import json
    t, st = T
    mf = tmp_path / "releases" / "2.0.8" / "system" / "config"
    mf.mkdir(parents=True)
    (mf / "hethong.json").write_text(json.dumps({"don_vi": {"bat": [], "go": ["console-system-term-ssh"]}}))
    assert t.suc_khoe("2.0.8") == (True, "ok")                                      # da go va khong chay -> dat
    st["active"].add("console-system-term-ssh")
    ok, ly = t.suc_khoe("2.0.8")
    assert not ok and "console-system-term-ssh" in ly and "go" in ly                 # go loi (con chay) khong duoc bao thanh cong
