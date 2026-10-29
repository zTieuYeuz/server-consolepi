# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Go agent tu console phai go ca dang ky MSI (loi that 29/10: file mat nhung Windows van coi la da cai -> cai lai bi tu choi)."""
import os
import sys

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))
WXS = os.path.join(GOC, "src", "ui", "agent_bin", "ConsoleSystemAgent.wxs.tpl")


def _nap():
    from ui import uem_agent as UA
    from ui import uem_agent_goi as UG
    return UA, UG


def test_ma_nen_dung_dinh_dang_windows_installer():
    UA, _ = _nap()
    assert UA.ma_msi_nen("6B1F2C9E-4D7A-4E58-9C31-0A5D8E7F4B21") == "E9C2F1B6A7D485E4C913A0D5E8F7B412"
    assert UA.ma_msi_nen("{6B1F2C9E-4D7A-4E58-9C31-0A5D8E7F4B21}") == "E9C2F1B6A7D485E4C913A0D5E8F7B412"


def test_ma_san_pham_khop_wxs_va_goi():
    UA, UG = _nap()
    with open(WXS, encoding="utf-8") as f:
        assert 'Product Id="%s"' % UA.MA_SAN_PHAM_MSI in f.read()
    assert UG.MSI_PRODUCT_CODE == "{%s}" % UA.MA_SAN_PHAM_MSI


def test_ps_go_xoa_dang_ky_msi():
    UA, _ = _nap()
    assert "__NEN__" not in UA.PS_GO and "__MA__" not in UA.PS_GO
    for khoa in ("Installer\\Products\\E9C2F1B6A7D485E4C913A0D5E8F7B412", "Installer\\Features\\E9C2F1B6A7D485E4C913A0D5E8F7B412",
                 "UserData\\S-1-5-18\\Products\\E9C2F1B6A7D485E4C913A0D5E8F7B412", "Uninstall\\{6B1F2C9E-4D7A-4E58-9C31-0A5D8E7F4B21}"):
        assert khoa in UA.PS_GO
    assert UA.PS_GO.index("Installer\\Products") < UA.PS_GO.index("Remove-Item -LiteralPath (Join-Path $env:ProgramFiles")
