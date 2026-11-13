"""2.0.8 V2-1: chong doan mat khau dang nhap. Dang nhap dung van vao duoc (hoi quy); sai nhieu lan thi khoa TAM, khi khoa khong goi PAM."""
import os
import sys

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))


@pytest.fixture(autouse=True)
def sach():
    from consolesystem.core import chongdoan as CD
    CD.xoa_het()
    yield
    CD.xoa_het()


@pytest.fixture
def pam(monkeypatch):
    """PAM gia: mat khau dung la 'dung'. Dem so lan duoc goi."""
    from consolesystem.web import auth
    goi = []

    def gia(u, p):
        goi.append(u)
        return (True, "") if p == "dung" else (False, "Sai tài khoản hoặc mật khẩu.")
    monkeypatch.setattr(auth, "_xac_thuc_pam", gia)
    return auth, goi


def test_dang_nhap_dung_van_vao_duoc_va_it_lan_sai_khong_bi_khoa(pam):
    auth, goi = pam
    assert auth.check_login("thuong", "dung") == (True, "")                  # hoi quy: tai khoan thuong (khong admin)
    for _ in range(4):                                                         # < nguong
        assert auth.check_login("thuong", "sai")[0] is False
    assert auth.check_login("thuong", "dung") == (True, "")                  # van vao duoc, dem ve 0
    for _ in range(4):
        assert auth.check_login("thuong", "sai")[0] is False
    assert auth.check_login("thuong", "dung")[0] is True


def test_sai_nhieu_lan_bi_khoa_tam_va_khong_goi_pam(pam):
    auth, goi = pam
    for _ in range(5):
        auth.check_login("nan", "sai")
    n = len(goi)
    ok, msg = auth.check_login("nan", "dung")                                  # ke ca mat khau DUNG cung bi tu choi trong luc khoa
    assert not ok and "đợi" in msg and len(goi) == n                          # PAM khong duoc goi
    assert auth.check_login("nguoikhac", "dung")[0] is True                    # tai khoan khac khong bi anh huong


def test_het_khoa_theo_thoi_gian_va_he_so_tang_dan():
    from consolesystem.core import chongdoan as CD
    t = 1000.0
    for _ in range(5):
        CD.ghi_that_bai("a", "", t)
    assert CD.cho_bao_lau("a", "", t) in (CD.KHOA_DAU, CD.KHOA_DAU + 1)
    assert CD.cho_bao_lau("a", "", t + CD.KHOA_DAU + 1) == 0                   # het han -> thu lai duoc
    CD.ghi_that_bai("a", "", t + 40)                                           # sai tiep -> khoa lau hon
    assert CD.cho_bao_lau("a", "", t + 40) > CD.KHOA_DAU
    for i in range(30):
        CD.ghi_that_bai("a", "", t + 41 + i)
    assert CD.cho_bao_lau("a", "", t + 71) <= CD.KHOA_TOI_DA + 1               # tran 5 phut, khong khoa vinh vien


def test_that_bai_cu_bi_quen():
    from consolesystem.core import chongdoan as CD
    for _ in range(4):
        CD.ghi_that_bai("b", "", 0)
    CD.ghi_that_bai("b", "", CD.CUA_SO + 100)                                  # lan thu 5 nhung 4 lan truoc da qua cua so
    assert CD.cho_bao_lau("b", "", CD.CUA_SO + 100) == 0


def test_theo_ip_do_nhieu_ten_nhung_loopback_khong_dem():
    from consolesystem.core import chongdoan as CD
    for i in range(CD.NGUONG_IP):
        CD.ghi_that_bai("ten%d" % i, "203.0.113.9", 0)                         # moi ten chi sai 1 lan nhung cung 1 IP
    assert CD.cho_bao_lau("tenmoi", "203.0.113.9", 0) > 0
    assert CD.cho_bao_lau("tenmoi", "203.0.113.10", 0) == 0
    for i in range(CD.NGUONG_IP * 2):
        CD.ghi_that_bai("lo%d" % i, "127.0.0.1", 0)                            # loopback dung chung (cloudflared): khong khoa ca nhom
    assert CD.cho_bao_lau("lomoi", "127.0.0.1", 0) == 0


def test_ip_khach_chi_tin_cf_khi_ket_noi_tu_loopback():
    from consolesystem.core import chongdoan as CD
    assert CD.ip_khach("127.0.0.1", {"X-Real-IP": "127.0.0.1", "Cf-Connecting-Ip": "198.51.100.7"}) == "198.51.100.7"
    assert CD.ip_khach("192.168.1.5", {"X-Real-IP": "192.168.1.5", "Cf-Connecting-Ip": "198.51.100.7"}) == "192.168.1.5"   # gia mao tu LAN vo hieu
    assert CD.ip_khach("127.0.0.1", {"X-Real-IP": "127.0.0.1", "Cf-Connecting-Ip": "khong-phai-ip"}) == "127.0.0.1"


def test_bo_nho_co_tran():
    from consolesystem.core import chongdoan as CD
    for i in range(CD.TOI_DA_MUC + 500):
        CD.ghi_that_bai("rac%d" % i, "", 10.0 + i)
    assert len(CD._ds) <= CD.TOI_DA_MUC + 1


def test_thieu_thong_tin_khong_dem_va_loi_he_thong_khong_dem(monkeypatch):
    from consolesystem.core import chongdoan as CD
    from consolesystem.web import auth
    for _ in range(10):
        assert auth.check_login("", "x")[0] is False
        assert auth.check_login("u", "")[0] is False
    monkeypatch.setattr(auth, "_xac_thuc_pam", lambda u, p: (False, "Máy thiếu thư viện PAM cho Python."))
    for _ in range(10):
        auth.check_login("u", "x")
    assert CD.cho_bao_lau("u", "") == 0


def test_route_login_qua_flask_khoa_sau_5_lan(monkeypatch):
    """Di qua route /login that: lan thu 6 thay thong bao khoa, HTTP van 200 (trang dang nhap), khong dang nhap duoc."""
    import runpy
    import threading
    os.environ.setdefault("CONSOLE_PI_LOG", __import__("tempfile").mkdtemp(prefix="cs-test-log-"))
    old = os.getcwd()
    os.chdir(os.path.join(GOC, "src"))
    goc = threading.Thread.start
    threading.Thread.start = lambda self: None
    try:
        app = runpy.run_path(os.path.join(GOC, "src", "app.py"), run_name="dev")["app"]
    finally:
        threading.Thread.start = goc
        os.chdir(old)
    from consolesystem.web import auth
    monkeypatch.setattr(auth, "_xac_thuc_pam", lambda u, p: (True, "") if p == "dung" else (False, "Sai tài khoản hoặc mật khẩu."))
    c = app.test_client()
    env = {"REMOTE_ADDR": "192.168.1.50"}
    for _ in range(5):
        r = c.post("/login", data={"username": "ai-do", "password": "sai"}, environ_overrides=env)
        assert "Sai tài khoản" in r.get_data(as_text=True)
    r = c.post("/login", data={"username": "ai-do", "password": "dung"}, environ_overrides=env)
    assert r.status_code == 200 and "đợi" in r.get_data(as_text=True)
    with c.session_transaction() as s:
        assert not s.get("user")
    r = c.post("/login", data={"username": "khac", "password": "dung"}, environ_overrides=env)       # nguoi khac van vao duoc
    assert r.status_code == 302
