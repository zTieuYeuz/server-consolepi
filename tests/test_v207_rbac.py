"""2.0.7 RBAC buoc 1: registry, vai tro, tai khoan cuu ho, cong khai khong leo thang, che do ghi nhan (CHUA chan)."""
import json
import os
import subprocess
import sys

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))


def _rb(tmp_path, monkeypatch):
    from consolesystem.core import rbac as RB
    monkeypatch.setattr(RB, "FILE", str(tmp_path / "rbac.json"))
    return RB


def test_ma_tran_vai_tro():
    from consolesystem.core import rbac as RB
    ok = lambda v, m, p: RB.cho_phep(v, m, p)[0]  # noqa: E731
    # Quan tri: moi thu
    assert ok("quan_tri", "POST", "/cap-nhat/bat-dau") and ok("quan_tri", "POST", "/nguoi-dung/luu")
    # Van hanh: xem + ghi dich vu van hanh, KHONG dich vu quan tri (ke ca xem)
    assert ok("van_hanh", "POST", "/uem/may/x/rustdesk/luu") and ok("van_hanh", "GET", "/ssh") and ok("van_hanh", "POST", "/ssh/connect")
    assert not ok("van_hanh", "GET", "/cap-nhat") and not ok("van_hanh", "POST", "/settings/sao-luu") and not ok("van_hanh", "GET", "/nguoi-dung")
    # Chi xem: chi GET
    assert ok("chi_xem", "GET", "/uem/may") and ok("chi_xem", "GET", "/logs")
    assert not ok("chi_xem", "POST", "/uem/may/x/rustdesk/luu") and not ok("chi_xem", "POST", "/ssh/connect") and not ok("chi_xem", "GET", "/cap-nhat")
    # Chua co vai tro / route chua khai: tu choi
    assert not ok(None, "GET", "/uem/may") and not ok("quan_tri", "GET", "/duong-chua-khai/x")
    assert RB.cho_phep("quan_tri", "GET", "/duong-chua-khai/x")[1] == "route-chua-khai"


def test_tai_khoan_cuu_ho_va_man_hinh_cuc_bo(tmp_path, monkeypatch):
    RB = _rb(tmp_path, monkeypatch)
    RB.dat_vai_tro("sudoer", "chi_xem")                                   # co bang vai tro ha xuong cung KHONG co tac dung voi sudo
    assert RB.vai_tro_cua("sudoer", lambda u: u == "sudoer") == "quan_tri"
    assert RB.vai_tro_cua("root", lambda u: False) == "quan_tri"
    RB.dat_vai_tro("thuong", "van_hanh")
    assert RB.vai_tro_cua("thuong", lambda u: False) == "van_hanh" and RB.vai_tro_cua("la", lambda u: False) is None
    assert RB.vai_tro_cua(None, lambda u: False) == RB.LOCAL_MAC_DINH != "quan_tri"      # man hinh cuc bo KHONG phai quan tri
    assert (tmp_path / "rbac.json").stat().st_mode & 0o777 == 0o600
    assert RB.reset() is True and RB.danh_sach() == {} and RB.reset() is False        # rbac-reset


def test_cong_khai_khong_leo_thang():
    from consolesystem.core import rbac as RB
    assert set(RB.CONG_KHAI) == {"/login", "/healthz", "/_auth", "/vkeyboard.js", "/dashboard.js", "/favicon.ico", "/static", "/thuong-hieu",
                                 "/deployos/pxeboot", "/api/tiendo", "/tk/tai", "/uem/agent", "/uem/novnc"}, "them loi vao cong khai phai la quyet dinh co chu y"
    for p in ("/uem/agent/nhip", "/uem/agent/cai/abc.ps1", "/api/tiendo/domain", "/deployos/pxeboot/x"):
        assert RB.la_cong_khai(p)
    # lan can KHONG duoc ke thua: cac trang quan tri cung tien to gan giong phai van la dich vu co kiem quyen
    for p in ("/uem/quan-tri/agent", "/uem/may/x", "/uem/profiles", "/deployos/trienkhai/kichban", "/deployos/kichban", "/tk", "/apiX/tiendo", "/uem/agentx"):
        assert not RB.la_cong_khai(p), p
    assert RB.cho_phep(None, "POST", "/uem/quan-tri/agent/goi/1/passkey")[0] is False
    assert RB.cho_phep("chi_xem", "POST", "/uem/quan-tri/agent/goi/1/passkey")[0] is False


def test_ghi_nhan_khong_chan_va_gioi_han_tan_suat(tmp_path, monkeypatch):
    RB = _rb(tmp_path, monkeypatch)
    RB._GHI_NHAN.update(sap_tu_choi=[], gan_nhat={})
    t = [1000.0]
    assert RB.ghi_nhan("POST", "/ssh/connect", "xem1", lambda u: False, lambda: t[0]) == (False, "khong-co-vai-tro")
    RB.ghi_nhan("POST", "/ssh/paste", "xem1", lambda u: False, lambda: t[0] + 5)               # cung nguoi+dich vu+ly do <10 phut: khong ghi lai
    assert len(RB.su_kien_gan_day()) == 1
    t[0] += 700
    RB.ghi_nhan("POST", "/ssh/paste", "xem1", lambda u: False, lambda: t[0])
    assert len(RB.su_kien_gan_day()) == 2


def test_moi_route_cua_app_da_khai_hoac_cong_khai_va_ghi_nhan_khong_chan(tmp_path):
    sys.path.insert(0, os.path.join(GOC, "src"))
    from ui import dichuyen as DM
    goc = str(tmp_path / "cs")
    DM.tao_bo_cuc_moi(goc)
    r = subprocess.run([sys.executable, os.path.join(GOC, "tests", "web_v207_rbac.py")], capture_output=True, text=True,
                       env=dict(os.environ, CONSOLE_PI_DATA=goc), timeout=240)
    dong = [x for x in r.stdout.splitlines() if x.startswith("KETQUA ")]
    assert dong, r.stdout[-1500:] + r.stderr[-1500:]
    kq = json.loads(dong[0][7:])
    sai = {k: v for k, v in kq.items() if v is not True}
    assert not sai, (sai, r.stderr[-600:])
