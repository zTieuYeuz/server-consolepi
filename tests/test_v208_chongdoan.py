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


def _sai(CD, ten, ip, t, n=1):
    for _ in range(n):
        cho, the = CD.thu(ten, ip, t)
        assert not cho
        CD.xong(the, "sai", t)


def test_het_khoa_theo_thoi_gian_va_he_so_tang_dan():
    from consolesystem.core import chongdoan as CD
    t = 1000.0
    _sai(CD, "a", "203.0.113.1", t, 5)
    cho, _ = CD.thu("a", "203.0.113.1", t)
    assert cho in (CD.KHOA_DAU, CD.KHOA_DAU + 1)
    assert CD.thu("a", "203.0.113.1", t + CD.KHOA_DAU + 1)[0] == 0              # het han -> thu lai duoc
    cho2, _ = CD.thu("a", "203.0.113.1", t + 40)                                 # lan thu o t+31 da tinh 1 that bai -> khoa lau hon
    assert cho2 > CD.KHOA_DAU or cho2 == 0
    for i in range(30):
        CD.thu("a", "203.0.113.1", t + 400 + i)
    assert CD.thu("a", "203.0.113.1", t + 431)[0] <= CD.KHOA_TOI_DA + 1          # tran 5 phut, khong khoa vinh vien


def test_that_bai_cu_bi_quen():
    from consolesystem.core import chongdoan as CD
    _sai(CD, "b", "203.0.113.2", 0, 4)
    _sai(CD, "b", "203.0.113.2", CD.CUA_SO + 100)
    assert CD.thu("b", "203.0.113.2", CD.CUA_SO + 100)[0] == 0


def test_theo_ip_do_nhieu_ten_nhung_loopback_khong_dem():
    from consolesystem.core import chongdoan as CD
    for i in range(CD.NGUONG_IP):
        _sai(CD, "ten%d" % i, "203.0.113.9", 0)                                  # moi ten chi sai 1 lan nhung cung 1 IP
    assert CD.thu("tenmoi", "203.0.113.9", 0)[0] > 0
    assert CD.thu("tenmoi", "203.0.113.10", 0)[0] == 0
    for i in range(CD.NGUONG_IP * 2):
        CD.thu("lo%d" % i, "127.0.0.1", 0)                                       # loopback dung chung (cloudflared): khong khoa ca nhom
    assert CD.thu("lomoi", "127.0.0.1", 0)[0] == 0


def test_A1_ke_ngoai_biet_ten_khong_chan_duoc_nguoi_that_tu_ip_da_quen():
    from consolesystem.core import chongdoan as CD
    t = 5000.0
    cho, the = CD.thu("admin", "198.51.100.5", t)                                # nguoi that dang nhap dung 1 lan -> nho cap (admin, IP)
    CD.xong(the, "dung", t)
    # ke tan cong tu nhieu IP khac nhau gui sai de khoa theo TEN (vuot nguong ten)
    for i in range(CD.NGUONG_TEN + 5):
        CD.xong(CD.thu("admin", "192.0.2.%d" % (i + 1), t + 1)[1], "sai", t + 1)
    assert CD.thu("admin", "192.0.2.250", t + 2)[0] > 0                          # nguoi la (IP chua quen) bi khoa theo ten
    cho, the = CD.thu("admin", "198.51.100.5", t + 3)                            # nhung nguoi that tu IP QUEN van vao duoc
    assert cho == 0
    CD.xong(the, "dung", t + 3)
    # ke tan cong tu 1 IP: chi cap cua no bi khoa, khong anh huong nguoi that
    for _ in range(5):
        CD.xong(CD.thu("admin", "203.0.113.77", t + 10)[1], "sai", t + 10)
    assert CD.thu("admin", "203.0.113.77", t + 11)[0] > 0
    assert CD.thu("admin", "198.51.100.5", t + 11)[0] == 0


def test_A1_cap_chua_quen_chi_bi_khoa_khi_vuot_nguong_ten_cao():
    from consolesystem.core import chongdoan as CD
    _sai(CD, "pi", "192.0.2.1", 0, 5)                                            # 5 sai tu mot IP: chi khoa cap cua IP do
    assert CD.thu("pi", "192.0.2.2", 0)[0] == 0                                  # IP khac chua bi anh huong


def test_A2_song_song_khong_cung_qua_kiem_khoa():
    """40 luong cung xin thu luc dau: chi dung NGUONG_CAP luong duoc qua, so con lai bi tu choi (truoc day tat ca deu qua)."""
    import threading
    from consolesystem.core import chongdoan as CD
    qua, lock, rao = [], threading.Lock(), threading.Barrier(40)

    def chay():
        rao.wait()
        cho, the = CD.thu("song", "198.51.100.9", 100.0)
        if not cho:
            with lock:
                qua.append(the)
    ts = [threading.Thread(target=chay) for _ in range(40)]
    [x.start() for x in ts]
    [x.join() for x in ts]
    assert len(qua) == CD.NGUONG_CAP, len(qua)
    for the in qua:                                                              # PAM tra "sai" -> van la that bai
        CD.xong(the, "sai", 100.0)
    assert CD.thu("song", "198.51.100.9", 100.0)[0] > 0


def test_xong_dung_hoan_lai_cho_va_loi_he_thong_khong_tinh():
    from consolesystem.core import chongdoan as CD
    for i in range(10):
        cho, the = CD.thu("u", "198.51.100.3", 0)
        assert not cho
        CD.xong(the, "dung" if i % 2 else "loi", 0)                              # dung/loi he thong: khong tich luy
    assert CD.thu("u", "198.51.100.3", 0)[0] == 0
    assert CD._ds.get("p:u|198.51.100.3") is None or CD._ds["p:u|198.51.100.3"][0] <= 1


def test_ip_khach_chi_tin_cf_khi_ket_noi_tu_loopback():
    from consolesystem.core import chongdoan as CD
    assert CD.ip_khach("127.0.0.1", {"X-Real-IP": "127.0.0.1", "Cf-Connecting-Ip": "198.51.100.7"}) == "198.51.100.7"
    assert CD.ip_khach("192.168.1.5", {"X-Real-IP": "192.168.1.5", "Cf-Connecting-Ip": "198.51.100.7"}) == "192.168.1.5"   # gia mao tu LAN vo hieu
    assert CD.ip_khach("127.0.0.1", {"X-Real-IP": "127.0.0.1", "Cf-Connecting-Ip": "khong-phai-ip"}) == "127.0.0.1"


def test_bo_nho_co_tran():
    from consolesystem.core import chongdoan as CD
    for i in range(CD.TOI_DA_MUC + 500):
        CD.thu("rac%d" % i, "", 10.0 + i)
    assert len(CD._ds) <= CD.TOI_DA_MUC + 3


def test_thieu_thong_tin_khong_dem_va_loi_he_thong_khong_dem(monkeypatch):
    from consolesystem.core import chongdoan as CD
    from consolesystem.web import auth
    for _ in range(10):
        assert auth.check_login("", "x")[0] is False
        assert auth.check_login("u", "")[0] is False
    monkeypatch.setattr(auth, "_xac_thuc_pam", lambda u, p: (False, "Máy thiếu thư viện PAM cho Python."))
    for _ in range(10):
        auth.check_login("u", "x")
    assert CD.thu("u", "")[0] == 0


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


def test_B2_don_bo_nho_khong_xoa_muc_dang_khoa():
    from consolesystem.core import chongdoan as CD
    t = 1000.0
    for _ in range(5):
        CD.xong(CD.thu("nan", "198.51.100.1", t)[1], "sai", t)                       # khoa cap (nan, IP)
    assert CD.thu("nan", "198.51.100.1", t + 1)[0] > 0
    for i in range(CD.TOI_DA_MUC + 300):                                              # tran bo nho bang rac
        CD.thu("rac%d" % i, "", t + 2 + i * 0.001)
    assert CD.thu("nan", "198.51.100.1", t + 10)[0] > 0                               # muc dang khoa van con
