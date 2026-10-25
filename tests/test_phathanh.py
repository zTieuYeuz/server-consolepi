"""A6: releases/ + current + console-system-apply. Thu muc tam, lenh he thong gia."""
import json
import os
import stat
import sys

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))
from ui import phathanh as P  # noqa: E402


def viet(p, nd="x", mode=0o644):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(nd)
    os.chmod(p, mode)


@pytest.fixture
def nguon(tmp_path):
    s = tmp_path / "nguon"
    viet(str(s / "VERSION"), "2.0.0\n")
    viet(str(s / "src/app.py"), "print(1)")
    viet(str(s / "src/ui/a.py"), "A")
    viet(str(s / "src/ui/__pycache__/a.pyc"), "RAC")
    viet(str(s / "src/scripts/x.sh"), "#!/bin/sh", 0o755)
    viet(str(s / "src/static/s.css"), "css")
    viet(str(s / "tools/cai-vnc.sh"), "vnc", 0o755)
    viet(str(s / "tools/khac.sh"), "khong-duoc-mang-theo")
    viet(str(s / "uninstall.sh"), "un")
    viet(str(s / "systemd/console-pi-dashboard.service"), "[Service]\nExecStart=/usr/bin/python3 /opt/console-pi/app.py\n")
    viet(str(s / "systemd/console-pi-tftp.service"), "[Service]\nTFTP=/var/lib/console-system/data/tftp\n")
    viet(str(s / "config/nginx-console-pi.conf"), "nginx-v2")
    viet(str(s / "config/smb.conf"), "smb-v2")
    viet(str(s / "config/logrotate-console-pi"), "lr-v2")
    viet(str(s / "config/99-consolepi-serial.rules"), "udev-v2")
    viet(str(s / "config/ssh_config-legacy-devices.conf"), "khong-ap-dung")
    return str(s)


def test_ban_chua_dung_noi_dung_va_chi_doc(nguon, tmp_path):
    opt = str(tmp_path / "opt")
    ten = P.tao_ban(nguon, opt)
    assert ten == "2.0.0"
    b = os.path.join(opt, "releases", ten)
    for rel in ("app.py", "ui/a.py", "scripts/x.sh", "static/s.css", "VERSION", "tools/cai-vnc.sh", "uninstall.sh",
                "system/systemd/console-pi-tftp.service", "system/config/nginx-console-pi.conf", P.TEN_RELEASE):
        assert os.path.exists(os.path.join(b, rel)), rel
    assert not os.path.exists(os.path.join(b, "tools/khac.sh")) and not os.path.exists(os.path.join(b, "ui/__pycache__"))
    for d, ds, fs in os.walk(b):
        for x in ds + fs:
            assert os.lstat(os.path.join(d, x)).st_mode & 0o222 == 0, os.path.join(d, x)       # khong ai ghi duoc
    assert os.stat(os.path.join(b, "scripts/x.sh")).st_mode & 0o111                              # van chay duoc
    assert P.kiem_ban(opt, ten) == []


def test_cung_noi_dung_dung_lai_khac_noi_dung_ra_ban_moi(nguon, tmp_path):
    opt = str(tmp_path / "opt")
    assert P.tao_ban(nguon, opt) == P.tao_ban(nguon, opt) == "2.0.0"
    viet(os.path.join(nguon, "src/ui/a.py"), "A-SUA")
    assert P.tao_ban(nguon, opt) == "2.0.0-2"
    assert sorted(P.danh_sach(opt)) == ["2.0.0", "2.0.0-2"]


def test_kiem_ban_phat_hien_sua(nguon, tmp_path):
    opt = str(tmp_path / "opt")
    ten = P.tao_ban(nguon, opt)
    p = os.path.join(opt, "releases", ten, "ui/a.py")
    os.chmod(p, 0o644)
    open(p, "w").write("BI-SUA")
    viet(os.path.join(opt, "releases", ten, "ui/la.py"), "thua")
    assert P.kiem_ban(opt, ten) == ["ui/a.py", "ui/la.py"]


def test_chuyen_ban_lui_va_lich_su(nguon, tmp_path):
    opt = str(tmp_path / "opt")
    a = P.tao_ban(nguon, opt)
    assert P.chuyen_ban(opt, a) is None
    viet(os.path.join(nguon, "VERSION"), "2.0.1\n")
    b = P.tao_ban(nguon, opt)
    assert P.chuyen_ban(opt, b) == a and P.hien_tai(opt) == b
    assert os.readlink(os.path.join(opt, "current")) == os.path.join("releases", b)        # lien ket tuong doi
    assert P.ban_truoc(opt) == a
    P.chuyen_ban(opt, P.ban_truoc(opt))
    assert P.hien_tai(opt) == a
    with pytest.raises(P.LoiPhatHanh):
        P.chuyen_ban(opt, "khong-co")


def test_don_ban_cu_giu_dang_dung_va_ban_lui(nguon, tmp_path):
    opt = str(tmp_path / "opt")
    ten = []
    for v in ("1", "2", "3", "4", "5", "6"):
        viet(os.path.join(nguon, "VERSION"), v + "\n")
        ten.append(P.tao_ban(nguon, opt))
        os.utime(os.path.join(opt, "releases", ten[-1]), (len(ten), len(ten)))
        P.chuyen_ban(opt, ten[-1])
    P.chuyen_ban(opt, ten[0])            # dang dung ban 1 (cu nhat), lui duoc ve ban 6
    xoa = P.don_ban_cu(opt, giu=2)
    con = set(P.danh_sach(opt))
    assert {"1", "6"} <= con and "5" in con and not {"2", "3"} & con and set(xoa) == {"2", "3", "4"}


# ---------------------------------------------------------------- apply
class Gia:
    def __init__(self, loi=()):
        self.lenh, self.loi = [], set(loi)

    def __call__(self, cmd):
        self.lenh.append(cmd)
        return (1, "loi gia") if cmd[0] in self.loi else (0, "")


def etc_gia(tmp_path):
    e = tmp_path / "etc"
    viet(str(e / "etc/systemd/system/console-pi-dashboard.service"), "CU-dashboard")
    viet(str(e / "etc/systemd/system/console-pi-tftp.service"), "[Service]\nTFTP=/var/lib/console-system/data/tftp\n")   # da dung
    viet(str(e / "etc/nginx/sites-available/console-pi.conf"), "nginx-v1")
    viet(str(e / "etc/samba/smb.conf"), "smb-v1")
    # logrotate/udev/journald KHONG co tren may -> bo qua
    return str(e)


def test_apply_chi_doi_file_khac_va_bo_qua_file_may_khong_cai(nguon, tmp_path):
    opt, e = str(tmp_path / "opt"), etc_gia(tmp_path)
    ten = P.tao_ban(nguon, opt)
    gia = Gia()
    bc = P.ap_dung(os.path.join(opt, "releases", ten), str(tmp_path / "bk"), e, gia)
    assert sorted(bc["doi"]) == ["/etc/nginx/sites-available/console-pi.conf", "/etc/samba/smb.conf", "/etc/systemd/system/console-pi-dashboard.service"]
    assert bc["khong_doi"] == 1 and "/etc/logrotate.d/console-pi" in bc["bo_qua"] and "/etc/udev/rules.d/99-consolepi-serial.rules" in bc["bo_qua"]
    assert open(os.path.join(e, "etc/samba/smb.conf")).read() == "smb-v2"
    bk = [os.path.join(d, f) for d, _s, fs in os.walk(str(tmp_path / "bk")) for f in fs]
    assert len(bk) == 3 and any(open(x).read() == "smb-v1" for x in bk)                          # ban cu duoc sao luu
    cmds = [c[0] + " " + " ".join(c[1:]) for c in gia.lenh]
    assert "nginx -t" in cmds and "testparm -s" in cmds and "systemctl daemon-reload" in cmds
    assert bc["unit_doi"] == ["console-pi-dashboard.service"]


def test_apply_lan_hai_khong_lam_gi(nguon, tmp_path):
    opt, e = str(tmp_path / "opt"), etc_gia(tmp_path)
    ten = P.tao_ban(nguon, opt)
    ban = os.path.join(opt, "releases", ten)
    P.ap_dung(ban, str(tmp_path / "bk"), e, Gia())
    gia = Gia()
    bc = P.ap_dung(ban, str(tmp_path / "bk"), e, gia)
    assert bc["doi"] == [] and gia.lenh == []


def test_apply_nginx_loi_thi_tra_ban_cu(nguon, tmp_path):
    opt, e = str(tmp_path / "opt"), etc_gia(tmp_path)
    ten = P.tao_ban(nguon, opt)
    bc = P.ap_dung(os.path.join(opt, "releases", ten), str(tmp_path / "bk"), e, Gia(loi={"nginx"}))
    assert bc["loi"] and "nginx" in bc["loi"][0]
    assert open(os.path.join(e, "etc/nginx/sites-available/console-pi.conf")).read() == "nginx-v1"     # tra ve ban cu
    assert open(os.path.join(e, "etc/samba/smb.conf")).read() == "smb-v2"                                # cai khac van ap dung


def test_apply_thu_khong_ghi_gi(nguon, tmp_path):
    opt, e = str(tmp_path / "opt"), etc_gia(tmp_path)
    ten = P.tao_ban(nguon, opt)
    gia = Gia()
    bc = P.ap_dung(os.path.join(opt, "releases", ten), str(tmp_path / "bk"), e, gia, thu=True)
    assert len(bc["doi"]) == 3 and gia.lenh == [] and open(os.path.join(e, "etc/samba/smb.conf")).read() == "smb-v1"
    assert not os.path.exists(str(tmp_path / "bk"))


# ------------------------------------------------------- nhap khau thu muc cu
@pytest.fixture
def may_cu(tmp_path):
    cu = tmp_path / "opt-console-pi"
    for rel, nd in (("app.py", "CU"), ("ui/a.py", "CU"), (".dau-an", "DAU"), ("COPYRIGHT", "CR"), ("driver-san/v.inf", "DRV"),
                    ("captures/c.pcap", "PCAP"), ("tftp/running-config", "CFG"), ("nettools/ifthen-rules.json", "[]")):
        viet(str(cu / rel), nd)
    goc = tmp_path / "du-lieu"
    goc.mkdir()
    (goc / ".bo-cuc-moi").write_text("2")
    return str(cu), str(goc)


def test_nhap_khau_cu_thanh_lien_ket(nguon, may_cu, tmp_path):
    cu, goc = may_cu
    opt = str(tmp_path / "opt")
    ten, doi_ten = P.nhap_khau_cu(opt, cu, goc, nguon)
    assert os.path.islink(cu) and os.path.realpath(cu) == os.path.realpath(os.path.join(opt, "releases", ten))
    assert open(os.path.join(cu, ".dau-an")).read() == "DAU" and os.path.exists(os.path.join(cu, "driver-san/v.inf"))   # do ISO duoc mang theo
    assert open(os.path.join(goc, "data/captures/c.pcap")).read() == "PCAP"
    assert open(os.path.join(goc, "data/tftp/running-config")).read() == "CFG"
    assert os.path.exists(os.path.join(goc, "config/ifthen-rules.json"))
    assert os.path.isdir(doi_ten) and open(os.path.join(doi_ten, "app.py")).read() == "CU"              # thu muc cu con nguyen
    assert P.kiem_ban(opt, ten) == []


def test_tra_ve_thu_muc_cu(nguon, may_cu, tmp_path):
    cu, goc = may_cu
    opt = str(tmp_path / "opt")
    P.nhap_khau_cu(opt, cu, goc, nguon)
    P.tra_ve_thu_muc_cu(opt, cu)
    assert os.path.isdir(cu) and not os.path.islink(cu) and open(os.path.join(cu, "app.py")).read() == "CU"


def test_nhap_khau_tu_choi_khi_chua_o_bo_cuc_moi(nguon, may_cu, tmp_path):
    cu, goc = may_cu
    os.remove(os.path.join(goc, ".bo-cuc-moi"))
    with pytest.raises(P.LoiPhatHanh, match="bo cuc moi"):
        P.nhap_khau_cu(str(tmp_path / "opt"), cu, goc, nguon)
    assert os.path.isdir(cu) and not os.path.islink(cu)


def test_ban_that_cua_repo_dung_duoc():
    """Cay nguon THAT cua repo phai tao duoc ban va kiem nguyen ven."""
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        ten = P.tao_ban(GOC, t)
        assert P.kiem_ban(t, ten) == []
        b = os.path.join(t, "releases", ten)
        assert os.path.exists(os.path.join(b, "app.py")) and os.path.exists(os.path.join(b, "system/systemd/console-pi-dashboard.service"))
        P.xoa_ban(b)


def test_cli_bat_lai_dich_vu_da_dung_du_khi_loi(nguon, may_cu, tmp_path, monkeypatch):
    """Loi that 25/10 tren .30: dich vu bi dung de doi thu muc ma khong duoc bat lai (tftp con 'inactive')."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("csr", os.path.join(GOC, "src", "scripts", "console-system-release.py"))
    csr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(csr)
    cu, goc = may_cu
    lenh = []

    class R:
        def __init__(self, rc):
            self.returncode, self.stdout, self.stderr = rc, "", ""

    monkeypatch.setattr(csr, "_sc", lambda *a: lenh.append(a) or R(0))
    monkeypatch.setattr(csr.P, "TEN_CU", cu)
    monkeypatch.setattr(csr.DD, "BO_CUC_MOI", True)
    monkeypatch.setattr(csr.DD, "GOC", goc)

    def hong(*a, **k):
        raise csr.P.LoiPhatHanh("hong gia")
    monkeypatch.setattr(csr.P, "nhap_khau_cu", hong)
    assert csr.main(["cai", "--nguon", nguon, "--opt", str(tmp_path / "opt"), "--khong-khoi-dong-lai"]) == 1
    assert ("start", "console-pi-tftp") in lenh and ("start", "console-pi-dashboard") in lenh
