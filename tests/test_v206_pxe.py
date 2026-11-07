"""2.0.6 (a): Tat PXE khong cat SMB 445 cua may dang cai Windows."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))


def test_tat_pxe_tu_choi_khi_may_dang_noi_smb(monkeypatch):
    from consolesystem.features.deploy_os import pxe
    goi = []
    monkeypatch.setattr(pxe, "dang_bat", lambda: True)
    monkeypatch.setattr(pxe, "may_dang_noi_smb", lambda: ["192.168.110.33"])
    monkeypatch.setattr(pxe, "_tat_pxe_that", lambda: goi.append(1) or (True, "da tat"))
    ok, tb = pxe.tat_pxe()
    assert not ok and "192.168.110.33" in tb and not goi            # khong dung toi dnsmasq/smbd/mang
    ok, tb = pxe.tat_pxe(ep=True)                                    # nguoi dung xac nhan 'Van tat'
    assert ok and goi == [1]


def test_tat_pxe_binh_thuong_khi_khong_ai_noi_smb(monkeypatch):
    from consolesystem.features.deploy_os import pxe
    monkeypatch.setattr(pxe, "dang_bat", lambda: True)
    monkeypatch.setattr(pxe, "may_dang_noi_smb", lambda: [])
    monkeypatch.setattr(pxe, "_tat_pxe_that", lambda: (True, "da tat"))
    assert pxe.tat_pxe() == (True, "da tat")


def test_may_dang_noi_smb_doc_ss(monkeypatch):
    from consolesystem.features.deploy_os import pxe
    ra = "0 0 192.168.110.14:445 192.168.110.33:49668\n0 0 [::ffff:192.168.110.40]:445 [::ffff:10.0.0.7]:50000\n"
    monkeypatch.setattr(pxe, "_sh", lambda cmd, timeout=20: (True, ra))
    assert pxe.may_dang_noi_smb() == ["10.0.0.7", "192.168.110.33"]
    monkeypatch.setattr(pxe, "_sh", lambda cmd, timeout=20: (False, "ss: not found"))
    assert pxe.may_dang_noi_smb() == []                              # khong doc duoc -> khong chan
