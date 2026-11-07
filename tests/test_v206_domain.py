"""2.0.6 (b): bao cao sau cai phai noi ro khi gia nhap domain that bai."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))


def _kich_ban(**kw):
    from consolesystem.features.deploy_os.dos_kichban import _cauhinh_mac_dinh
    d = _cauhinh_mac_dinh("windows") if _cauhinh_mac_dinh.__code__.co_argcount else _cauhinh_mac_dinh()
    d.update(kw)
    return d


def test_bao_cao_co_nhom_can_xem_lai_khi_vao_domain_that_bai():
    from consolesystem.features.deploy_os.un_baocao import sinh_script_bao_cao
    ps = sinh_script_bao_cao(_kich_ban(domain="home.local", domain_user="svc", domain_pass="x"))
    assert "Gia nhập domain" in ps                                   # muc kiem tra van co
    assert "NetSetup.log" in ps and "0x52e" in ps                    # doc ma loi that
    assert "CHƯA VÀO DOMAIN" in ps and "CẦN XEM LẠI" in ps            # noi ro tren cua so
    assert "!!! " in ps                                              # va trong file .txt
    assert ps.count("{") == ps.count("}") and ps.count("(") == ps.count(")")


def test_bao_cao_khong_domain_khong_them_kiem_tra_domain():
    from consolesystem.features.deploy_os.un_baocao import sinh_script_bao_cao
    ps = sinh_script_bao_cao(_kich_ban(domain=""))
    assert "Nhan = 'Gia nhập domain'" not in ps and "Nhan=''Gia" not in ps
    assert "Gia nhập domain'; Loai" not in ps
