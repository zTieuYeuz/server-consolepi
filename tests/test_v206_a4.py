"""A4 (2.0.6): tai khoan local them + muc quyen rieng tu trong unattend."""
import os
import sys
import xml.dom.minidom as md

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))


def _cauhinh(**kw):
    from consolesystem.features.deploy_os import dos_kichban as K
    d = K._cauhinh_mac_dinh("chay")
    d.update(os_ho="windows", os_id="w11", ten_may="PC-A4", mk_admin="Admin#Pass1", username="Administrator")
    d.update(kw)
    return d


def test_user_local_vao_unattend():
    from consolesystem.features.deploy_os.un_offline import sinh_unattend_offline_xml
    x = sinh_unattend_offline_xml(_cauhinh(ul_ten="nhanvien", ul_mk="Mk'1234", ul_quyen="Users"))
    md.parseString(x.encode("utf-8"))                      # XML hop le
    assert "New-LocalUser -Name 'nhanvien'" in x and "Mk''1234" in x       # nhay don nhan doi
    assert "S-1-5-32-545" in x and "S-1-5-32-544" not in x                 # nhom theo SID, khong theo ten
    x2 = sinh_unattend_offline_xml(_cauhinh(ul_ten="quantri", ul_mk="abc12345", ul_quyen="Administrators"))
    assert "S-1-5-32-544" in x2


def test_khong_dien_ten_thi_khong_tao():
    from consolesystem.features.deploy_os.un_offline import sinh_unattend_offline_xml
    assert "New-LocalUser" not in sinh_unattend_offline_xml(_cauhinh())


def test_kiem_tra_ten_va_mat_khau():
    from consolesystem.features.deploy_os.dos_kichban import loi_user_local as L
    assert L("", "") == ""
    assert L("nhanvien", "abc12345") == ""
    for ten, mk in [("a" * 21, "x"), ("a/b", "x"), ("Administrator", "x"), ("pc-a4", "x"), ("...", "x"), ("ok", ""),
                    ("ok", 'a"b'), ("ok", "a%b"), ("ok", "x" * 61)]:
        assert L(ten, mk, "PC-A4"), (ten, mk)


def test_lenh_du_ngan_cho_windows_setup():
    from consolesystem.features.deploy_os.un_offline import _lenh_tao_user_local
    for c in _lenh_tao_user_local(_cauhinh(ul_ten="u" * 20, ul_mk="p" * 60)):
        assert len("cmd /c " + c) <= 259


def test_muc_rieng_tu_co_trong_danh_sach():
    from consolesystem.features.deploy_os.un_tuychon import TUY_CHON_WINDOWS
    rt = [m for m in TUY_CHON_WINDOWS if m[0].startswith("rt_")]
    assert len(rt) == 6 and all(m[1].startswith("Quyền riêng tư") for m in rt)
    from consolesystem.features.deploy_os.un_offline import sinh_unattend_offline_xml
    x = sinh_unattend_offline_xml(_cauhinh(tuy_chon=[m[0] for m in rt]))
    md.parseString(x.encode("utf-8"))
    assert "AdvertisingInfo" in x and "ContentDeliveryManager" in x
