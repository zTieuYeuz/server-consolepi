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
                                 "/deployos/pxeboot", "/api/tiendo/batdau", "/api/tiendo/buoc", "/api/tiendo/domain", "/api/tiendo/ketthuc", "/logout", "/tk/tai", "/uem/agent", "/uem/novnc"}, "them loi vao cong khai phai la quyet dinh co chu y"
    for p in ("/uem/agent/nhip", "/uem/agent/cai/abc.ps1", "/api/tiendo/domain", "/deployos/pxeboot/x"):
        assert RB.la_cong_khai(p)
    # lan can KHONG duoc ke thua: cac trang quan tri cung tien to gan giong phai van la dich vu co kiem quyen
    for p in ("/uem/quan-tri/agent", "/uem/may/x", "/uem/profiles", "/deployos/trienkhai/kichban", "/deployos/kichban", "/tk", "/apiX/tiendo", "/uem/agentx", "/api/tiendo/data", "/api/tiendo"):
        assert not RB.la_cong_khai(p), p
    assert RB.cho_phep(None, "POST", "/uem/quan-tri/agent/goi/1/passkey")[0] is False
    assert RB.cho_phep("chi_xem", "POST", "/uem/quan-tri/agent/goi/1/passkey")[0] is False


def test_ghi_nhan_tra_ket_qua_va_gioi_han_tan_suat(tmp_path, monkeypatch):
    RB = _rb(tmp_path, monkeypatch)
    RB._GHI_NHAN.update(sap_tu_choi=[], gan_nhat={})
    t = [1000.0]
    assert RB.ghi_nhan("POST", "/ssh/connect", "xem1", lambda u: False, lambda: t[0]) == (False, "khong-co-vai-tro")
    RB.ghi_nhan("POST", "/ssh/paste", "xem1", lambda u: False, lambda: t[0] + 5)               # cung nguoi+dich vu+ly do <10 phut: khong ghi lai
    assert len(RB.su_kien_gan_day()) == 1
    t[0] += 700
    RB.ghi_nhan("POST", "/ssh/paste", "xem1", lambda u: False, lambda: t[0])
    assert len(RB.su_kien_gan_day()) == 2


def test_moi_route_cua_app_da_khai_hoac_cong_khai_va_chan_theo_vai_tro(tmp_path):
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


def test_cong_vao_terminal_la_muc_ghi_ke_ca_get(tmp_path, monkeypatch):
    RB = _rb(tmp_path, monkeypatch)
    for p in ("/term-phien/x", "/uem-vnc-ws/a"):
        assert RB.dich_vu_cua(p) == "remote", p
        assert RB.muc_can("GET", p) == "ghi", p
        assert RB.cho_phep("van_hanh", "GET", p)[0] and RB.cho_phep("quan_tri", "GET", p)[0]
        assert not RB.cho_phep("chi_xem", "GET", p)[0] and not RB.cho_phep(None, "GET", p)[0]
    assert RB.dich_vu_cua("/term-khac/") is None                  # tien to la khong tu dong thuoc Remote


def test_moi_location_auth_request_cua_nginx_nam_trong_cong_vao():
    """Them location moi co auth_request ma quen khai vao CONG_VAO thi RBAC bi hong am tham."""
    import re
    from consolesystem.core import rbac as RB
    conf = open(os.path.join(GOC, "config", "nginx-console-pi.conf"), encoding="utf-8").read()
    khoi = re.findall(r"location\s+(?:~\s+)?(\S+)\s*\{[^}]*?auth_request\s+/_auth", conf)
    assert khoi
    for loc in khoi:
        goc = re.sub(r"^\^", "", loc)
        m = re.match(r"(/[A-Za-z0-9_-]+)", goc)
        assert m and m.group(1) in RB.CONG_VAO, (loc, "chua khai vao core.rbac.CONG_VAO")


def test_thao_tac_huy_diet_chi_quan_tri(tmp_path, monkeypatch):
    RB = _rb(tmp_path, monkeypatch)
    for p in ("/power/reboot", "/power/poweroff", "/rename", "/force-ap", "/deployos/pxe/tat", "/deployos/os/xoa", "/deployos/kichban/xoa",
              "/uem/may/m1/xoa", "/uem/profiles/p1/xoa", "/storage/xoa", "/wifi-delete", "/nettools/tftp/xoa", "/deployos/o-dia/xoa-het", "/phien/api/xoa"):
        assert RB.muc_can("POST", p) == "quan_tri", p
        assert not RB.cho_phep("van_hanh", "POST", p)[0], p
        assert not RB.cho_phep("chi_xem", "POST", p)[0], p
        assert RB.cho_phep("quan_tri", "POST", p)[0], p
    assert not RB.cho_phep("van_hanh", "GET", "/power")[0] and not RB.cho_phep(None, "GET", "/power")[0]   # ca trang /power cung chi Quan tri (LOI-011-A)
    assert RB.cho_phep("van_hanh", "POST", "/ssh/xin")[0]               # thao tac thuong van duoc


def test_chuan_may_khoa_dieu_khien():
    from consolesystem.features.terminal.ssh_phien import chuan_may as c
    assert c("localhost") == c("127.0.0.1") == c("root@LocalHost:22") == c("::1") == "127.0.0.1:22"
    assert c("10.0.0.1") == "10.0.0.1:22" and c("10.0.0.1:2222") == "10.0.0.1:2222" and c("10.0.0.1:22") != c("10.0.0.1:2222")


def test_shell_root_cua_pi_va_serial_chi_quan_tri(tmp_path, monkeypatch):
    """LOI-011-F (CEO chot): terminal tai cho + console/serial + gui phim/thu vien lenh vao terminal cua Pi + cai goi tren Pi chi Quan tri; SSH/RDP/VNC toi may dich van cho Van hanh."""
    RB = _rb(tmp_path, monkeypatch)
    for uri in ("/term-ssh/", "/term-ssh/ws?arg=x", "/term-local/", "/term-local/ws", "/term-console/ttyUSB0/x", "/term-phien/?arg=local", "/term-phien/ws?arg=serial-ttyUSB0"):
        assert RB.muc_cong_vao(uri) == "quan_tri", uri
        assert not RB.cho_phep("van_hanh", "GET", uri.split("?")[0], RB.muc_cong_vao(uri))[0], uri
        assert RB.cho_phep("quan_tri", "GET", uri.split("?")[0], RB.muc_cong_vao(uri))[0], uri
    for uri in ("/term-phien/?arg=abc123", "/uem-vnc-ws/x", "/term-phien/"):
        assert RB.muc_cong_vao(uri) is None, uri
        assert RB.cho_phep("van_hanh", "GET", uri.split("?")[0], RB.muc_cong_vao(uri))[0], uri
    for m, p in (("GET", "/terminal"), ("POST", "/terminal/paste"), ("POST", "/api/send-keys"), ("POST", "/commands/send"), ("POST", "/commands/add"),
                 ("POST", "/phien/api/local/dan"), ("POST", "/phien/api/serial-ttyUSB0/baud"), ("POST", "/remote/cai"), ("POST", "/remote/ts/cai"),
                 ("POST", "/rustdesk/api/cai"), ("POST", "/rustdesk/api/hanh-dong"), ("POST", "/nettools/pcap/start"), ("POST", "/settings/api/xem-mat-khau-terminal")):
        assert not RB.cho_phep("van_hanh", m, p)[0], (m, p)
        assert RB.cho_phep("quan_tri", m, p)[0], (m, p)
    for m, p in (("POST", "/phien/api/abc123/dan"), ("POST", "/ssh/connect"), ("POST", "/remote-desktop/ket-noi"), ("POST", "/rustdesk/api/ket-noi"), ("GET", "/phien"), ("GET", "/commands")):
        assert RB.cho_phep("van_hanh", m, p)[0], (m, p)


def test_danh_sach_route_ghi_da_duoc_duyet():
    """Moi route POST/PUT/DELETE o muc ghi (Van hanh dung duoc) nam trong tests/hop-dong/route-ghi.txt. Them route moi -> file doi -> phai co nguoi duyet muc quyen
    (NV4/CEO doc file nay), roi chay tools/xuat-route-ghi.py tests/hop-dong/route-ghi.txt de ghi nhan."""
    ra = subprocess.run([sys.executable, os.path.join(GOC, "tools", "xuat-route-ghi.py")], cwd=GOC, capture_output=True, text=True, timeout=300)
    assert ra.returncode == 0, ra.stderr[-500:]
    mau = open(os.path.join(GOC, "tests", "hop-dong", "route-ghi.txt"), encoding="utf-8").read()
    assert "(CHUA KHAI)" not in ra.stdout
    moi, cu = set(ra.stdout.splitlines()), set(mau.splitlines())
    assert moi == cu, ("them:", sorted(moi - cu)[:10], "bo:", sorted(cu - moi)[:10])


def test_lach_duong_dan_vao_cong_quan_tri_bi_chan(tmp_path, monkeypatch):
    """LOI-012: /term-phien/../term-local/ va bien the ma hoa phai bi coi la cong quan_tri; duong hop le khong bi nang muc oan."""
    RB = _rb(tmp_path, monkeypatch)
    for uri in ("/term-phien/../term-local/", "/term-phien/%2e%2e/term-local/", "/term-phien/./../term-local/", "/term-phien/..%2fterm-local/", "/term-phien/%252e%252e/term-local/",
                "/term-ssh/..\\term-local/", "/term-ssh//term-local/", "/term-ssh/../term-console/ttyUSB0/", "/term-phien/x/%2E%2E/%2e%2e/term-local", "/term-local/../term-local/"):
        d, q, lat = RB.chuan_uri(uri)
        assert RB.muc_cong_vao(uri) == "quan_tri", uri
        assert not RB.cho_phep("van_hanh", "GET", d, RB.muc_cong_vao(uri))[0], uri
    for uri in ("/term-phien/?arg=abc", "/term-phien/ws?arg=abc-123", "/term-phien/token", "/uem-vnc-ws/x"):
        assert RB.muc_cong_vao(uri) is None, uri


def test_get_nhay_cam_khong_phai_muc_xem(tmp_path, monkeypatch):
    """NV8-02: GET log terminal/serial, pcap, ban sao luu thiet bi, goi agent... = quan_tri; ghi hinh / tai tep tu may tram = it nhat van_hanh. Chi xem khong doc duoc."""
    RB = _rb(tmp_path, monkeypatch)
    qt = ("/phien/api/local/log", "/phien/api/serial-ttyUSB0/log", "/phien/api/abc123/log", "/nettools/pcap", "/nettools/pcap/download/a/b.pcap",
          "/nettools/console-backup", "/nettools/console-backup/tai/sw1/run.cfg", "/nettools/tftp/tai/x.cfg", "/logs/tai", "/uem/quan-tri/agent/goi/g1/tai",
          "/deployos/trienkhai/may/taikhoan")
    for p in qt:
        assert RB.muc_can("GET", p) == "quan_tri", p
        for vt in ("van_hanh", "chi_xem", None):
            assert not RB.cho_phep(vt, "GET", p)[0], (vt, p)
        assert RB.cho_phep("quan_tri", "GET", p)[0], p
    for p in ("/rustdesk/ghi-hinh/m1/a.mp4", "/uem/may/m1/duyet-file/tai"):
        assert RB.muc_can("GET", p) == "ghi", p
        assert RB.cho_phep("van_hanh", "GET", p)[0] and not RB.cho_phep("chi_xem", "GET", p)[0], p
    assert RB.cho_phep("chi_xem", "GET", "/logs")[0] and RB.cho_phep("chi_xem", "GET", "/uem/profiles")[0]   # trang xem thuong van mo


def test_nv8_phien_local_serial_moi_phuong_thuc_va_vnc_token(tmp_path, monkeypatch):
    RB = _rb(tmp_path, monkeypatch)
    for m in ("GET", "POST"):
        for p in ("/phien/api/local/log", "/phien/api/local/bat-ky", "/phien/api/serial-ttyUSB0/x", "/phien/api/serial-ttyACM1/log"):
            assert RB.muc_can(m, p) == "quan_tri", (m, p)
            assert not RB.cho_phep("van_hanh", m, p)[0] and not RB.cho_phep("chi_xem", m, p)[0]
    # NV8-06: trang VNC (chua token + PIN) it nhat Van hanh; Chi xem khong thay
    assert RB.cho_phep("van_hanh", "GET", "/uem/may/m1/tu-xa/vnc/abc123def")[0]
    assert not RB.cho_phep("chi_xem", "GET", "/uem/may/m1/tu-xa/vnc/abc123def")[0]
    # NV8-03: Chi xem khong mo VNC/CMD/PowerShell, khong lay mat khau RustDesk
    for p in ("/uem/may/m1/tu-xa/vnc/mo", "/rustdesk/api/xem-mat-khau", "/uem/may/m1/tu-xa/vnc/go"):
        assert not RB.cho_phep("chi_xem", "POST", p)[0], p


def test_nhat_ky_che_token_phien_vnc_va_ma_terminal():
    import logging
    import runpy
    import tempfile
    os.environ.setdefault("CONSOLE_PI_LOG", tempfile.mkdtemp(prefix="cs-test-log-"))
    ns = None
    src = open(os.path.join(GOC, "src", "app.py"), encoding="utf-8").read()
    i = src.index("class _LocTruyCap")
    j = src.index("_logging.getLogger(\"werkzeug\").addFilter")
    ns = {"_logging": logging, "_re": __import__("re")}
    exec(src[i:j], ns)                                                        # noqa: S102 - chi chay doan dinh nghia bo loc
    f = ns["_LocTruyCap"]()
    rec = logging.LogRecord("werkzeug", 20, "x", 1, '"GET /uem/may/m1/tu-xa/vnc/SECRETTOK123 HTTP/1.1" 200 -', None, None)
    f.filter(rec)
    assert "SECRETTOK123" not in rec.getMessage() and "/tu-xa/vnc/***" in rec.getMessage()
    rec = logging.LogRecord("werkzeug", 20, "x", 1, '"GET /ssh?xem=abcdef0123 HTTP/1.1" 500 -', None, None)
    f.filter(rec)
    assert "abcdef0123" not in rec.getMessage()
