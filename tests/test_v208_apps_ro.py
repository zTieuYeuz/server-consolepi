"""2.0.8 V3-3: cs-apps.cmd dung tai khoan Samba CHI DOC cs-apps-ro (mat khau ngau nhien doi khi bat PXE), lui ve consolepi-deploy khi loi;
chi phat cho may cung mang voi cong PXE. Khong in/ghi mat khau o dau ngoai tep khoa 0600."""
import os
import stat
import sys

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))

SMB_MOI = "[global]\n  x = 1\n[winpe-apps]\n   path = /p\n   valid users = consolepi-deploy cs-apps-ro\n[deploy]\n   valid users = consolepi-deploy\n"
SMB_CU = "[winpe-apps]\n   valid users = consolepi-deploy\n[deploy]\n   valid users = consolepi-deploy cs-apps-ro\n"


@pytest.fixture
def R(tmp_path, monkeypatch):
    from consolesystem.features.deploy_os import apps_ro as R
    monkeypatch.setattr(R._DD, "FILE_KHOA_APPS_RO", str(tmp_path / "apps-ro.key"))
    monkeypatch.setattr(R._DD, "FILE_KHOA_SAMBA", str(tmp_path / "samba.key"))
    (tmp_path / "samba.key").write_text("MK-CU\n")
    return R, tmp_path


def _smb(tmp, nd):
    p = tmp / "smb.conf"
    p.write_text(nd)
    return str(p)


class Sh:
    def __init__(self, loi=None, co_tai_khoan=False):
        self.goi, self.loi, self.co = [], loi, co_tai_khoan
        self.nhap = []

    def __call__(self, cmd, input=None, timeout=20):
        self.goi.append(cmd[0] if cmd[0] != "smbpasswd" else "smbpasswd " + cmd[1])
        if input:
            self.nhap.append(input)
        if cmd[0] == "id":
            return (self.co, "")
        if self.loi and cmd[0] == self.loi:
            return False, "hong"
        return True, ""


def test_smb_conf_repo_co_cs_apps_ro_dung_muc():
    from consolesystem.features.deploy_os import apps_ro as R
    assert R.smb_conf_co_tai_khoan(os.path.join(GOC, "config", "smb.conf"))
    # cs-apps-ro KHONG duoc co o share nao khac (chi winpe-apps)
    nd = open(os.path.join(GOC, "config", "smb.conf"), encoding="utf-8").read()
    for dong in nd.splitlines():
        if "cs-apps-ro" in dong and not dong.strip().startswith("#"):
            assert dong.strip() == "valid users = consolepi-deploy cs-apps-ro"


def test_nhan_dien_muc_dung(R):
    r, tmp = R
    assert r.smb_conf_co_tai_khoan(_smb(tmp, SMB_MOI)) and not r.smb_conf_co_tai_khoan(_smb(tmp, SMB_CU))         # chi tinh dung muc [winpe-apps]
    assert not r.smb_conf_co_tai_khoan(str(tmp / "khong-co"))


def test_xoay_tao_tai_khoan_mat_khau_ngau_nhien_khoa_600(R):
    r, tmp = R
    sh = Sh()
    ok, tb = r.xoay_mat_khau(sh, _smb(tmp, SMB_MOI))
    assert ok and "useradd" in sh.goi and "smbpasswd -s" in sh.goi and "smbpasswd -e" in sh.goi
    mk = (tmp / "apps-ro.key").read_text()
    assert len(mk) >= 20 and stat.S_IMODE(os.stat(tmp / "apps-ro.key").st_mode) == 0o600
    assert sh.nhap == ["%s\n%s\n" % (mk, mk)]                                  # mat khau chi di qua stdin cua smbpasswd
    sh2 = Sh(co_tai_khoan=True)
    r.xoay_mat_khau(sh2, _smb(tmp, SMB_MOI))
    assert "useradd" not in sh2.goi and (tmp / "apps-ro.key").read_text() != mk        # doi moi lan bat PXE
    assert mk not in tb


def test_loi_thi_lui_ve_tai_khoan_cu_khong_hong_trien_khai(R):
    r, tmp = R
    smb = _smb(tmp, SMB_MOI)
    assert r.xoay_mat_khau(Sh(), smb)[0] and r.thong_tin_apps(smb)[0] == "cs-apps-ro"
    for loi in ("useradd", "smbpasswd"):
        ok, tb = r.xoay_mat_khau(Sh(loi=loi), smb)
        assert not ok and "tài khoản cũ" in tb and not (tmp / "apps-ro.key").exists()
        assert r.thong_tin_apps(smb) == ("consolepi-deploy", "MK-CU")           # cs-apps.cmd van dung duoc
    ok, tb = r.xoay_mat_khau(Sh(), _smb(tmp, SMB_CU))                            # may OTA chua co cau hinh moi
    assert not ok and r.thong_tin_apps(_smb(tmp, SMB_CU)) == ("consolepi-deploy", "MK-CU")


def test_cs_apps_cmd_dung_tai_khoan_moi_hoac_cu(R, monkeypatch):
    r, tmp = R
    from consolesystem.features.deploy_os import winperieng as W
    monkeypatch.setattr(W, "danh_sach", lambda: [{"file": "w.wim", "apps_mang": "Boot1"}])
    monkeypatch.setattr(r, "SMB_CONF", _smb(tmp, SMB_MOI))
    r.xoay_mat_khau(Sh(), str(tmp / "smb.conf"))
    mk = (tmp / "apps-ro.key").read_text()
    nd = W.noi_dung_cs_apps("w.wim", "192.168.98.1")
    assert "/user:cs-apps-ro %s" % mk in nd and "consolepi-deploy" not in nd and "MK-CU" not in nd
    os.remove(tmp / "apps-ro.key")
    assert "/user:consolepi-deploy MK-CU" in W.noi_dung_cs_apps("w.wim", "192.168.98.1")


def test_chi_phat_cho_cung_mang_voi_cong_pxe(R):
    r, tmp = R
    sh = lambda cmd, input=None, timeout=20: (True, "2: eth0    inet 192.168.98.1/24 brd 192.168.98.255 scope global eth0")   # noqa: E731
    assert r.khach_trong_mang_trien_khai("192.168.98.50", "eth0", sh)
    assert not r.khach_trong_mang_trien_khai("10.0.0.5", "eth0", sh) and not r.khach_trong_mang_trien_khai("khong-phai-ip", "eth0", sh)
    assert r.khach_trong_mang_trien_khai("10.0.0.5", "eth0", lambda c, input=None, timeout=20: (False, ""))        # khong xac dinh duoc mang -> khong lam hong


def test_uninstall_don_tai_khoan():
    s = open(os.path.join(GOC, "uninstall.sh"), encoding="utf-8").read()
    assert "smbpasswd -x cs-apps-ro" in s and "userdel cs-apps-ro" in s
