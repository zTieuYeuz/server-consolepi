"""2.0.8 R1: cong RBAC FAIL-CLOSED. Loi trong luc kiem quyen -> 403 (khong cho qua); che do cuu ho CONSOLE_RBAC_GHI_NHAN=1 thi cho qua; hoat dong binh thuong khong doi."""
import os
import runpy
import sys
import tempfile
import threading

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))


@pytest.fixture(scope="module")
def app():
    os.environ.setdefault("CONSOLE_PI_LOG", tempfile.mkdtemp(prefix="cs-test-log-"))
    cu = os.getcwd()
    os.chdir(os.path.join(GOC, "src"))
    goc = threading.Thread.start
    threading.Thread.start = lambda self: None
    try:
        return runpy.run_path(os.path.join(GOC, "src", "app.py"), run_name="dev")["app"]
    finally:
        threading.Thread.start = goc
        os.chdir(cu)


def _client(app, user):
    c = app.test_client()
    with c.session_transaction() as s:
        s["user"] = user
    return c


ENV = {"REMOTE_ADDR": "192.168.1.50"}


def _hong(*a, **k):
    raise RuntimeError("loi gia lap")


def test_binh_thuong_khong_doi(app):
    from consolesystem.core import rbac
    # root: trang xem vao duoc; nguoi thuong chua gan vai tro: van bi chan nhu 2.0.7 (hoi quy)
    assert _client(app, "root").get("/ssh", environ_overrides=ENV).status_code == 200
    assert _client(app, "nguoi-la-khong-vai-tro").get("/ssh", environ_overrides=ENV).status_code == 403
    assert _client(app, "nguoi-la-khong-vai-tro").get("/healthz", environ_overrides=ENV).status_code == 200      # cong khai van mo


def test_loi_kiem_quyen_thi_chan(app, monkeypatch):
    from consolesystem.core import rbac
    monkeypatch.setattr(rbac, "ghi_nhan", _hong)
    r = _client(app, "root").get("/ssh", environ_overrides=ENV)
    assert r.status_code == 403 and "an toàn" in r.get_data(as_text=True)
    r = _client(app, "root").post("/api/tiendo/data", environ_overrides=ENV)                                   # API -> JSON
    assert r.status_code == 403 and r.is_json and r.get_json()["ok"] is False
    assert app.test_client().get("/ssh", environ_overrides=ENV).status_code == 302                              # chua dang nhap van ve /login
    assert app.test_client().get("/healthz", environ_overrides=ENV).status_code == 200                           # duong cong khai khong phu thuoc RBAC


def test_loi_o_cong_vao_terminal_thi_chan(app, monkeypatch):
    from consolesystem.core import rbac
    h = {"X-Original-URI": "/term-phien/ssh-a/"}
    c = _client(app, "root")
    assert c.get("/_auth", headers=h, environ_overrides=ENV).status_code == 200
    monkeypatch.setattr(rbac, "ghi_nhan", _hong)
    assert c.get("/_auth", headers=h, environ_overrides=ENV).status_code == 403


def test_che_do_cuu_ho_ghi_nhan_thi_cho_qua(app, monkeypatch):
    from consolesystem.core import rbac
    monkeypatch.setattr(rbac, "ghi_nhan", _hong)
    monkeypatch.setenv("CONSOLE_RBAC_GHI_NHAN", "1")
    assert _client(app, "root").get("/ssh", environ_overrides=ENV).status_code == 200
    assert _client(app, "root").get("/_auth", headers={"X-Original-URI": "/term-phien/ssh-a/"}, environ_overrides=ENV).status_code == 200
