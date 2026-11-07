"""2.0.6 (i): ket qua co dau tieng Viet, ma loi WinGet noi ro nguyen nhan; DNS/TLS co dau."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))


def test_viet_hoa_ket_qua_tightvnc_va_winget():
    from consolesystem.features.uem import uem_buoc as UB
    assert UB.viet_hoa("Da cai TightVNC (dich vu thu cong, dang tat)") == "Đã cài TightVNC (dịch vụ chạy thủ công, đang tắt)"
    assert UB.viet_hoa("Da cai san, da cau hinh lai") == "Đã cài sẵn, đã cấu hình lại"
    assert UB.viet_hoa("Chua cai TightVNC tren may nay") == "Chưa cài TightVNC trên máy này"
    assert UB.viet_hoa("Dich vu TightVNC khong mo duoc cong 5900") == "Dịch vụ TightVNC không mở được cổng 5900"
    tb = UB.viet_hoa("winget ma -1073741515 \r\nloi gi do")
    assert "WinGet không chạy được" in tb and "-1073741515" in tb
    assert UB.viet_hoa("winget ma 5 abc") == "winget mã 5 abc"                    # ma khac: giu nguyen, chi them dau
    assert UB.viet_hoa("Đã có dấu sẵn") == "Đã có dấu sẵn" and UB.viet_hoa(None) == ""


def test_ket_qua_vnc_va_buoc_chay_di_qua_viet_hoa():
    from consolesystem.features.uem import uem_vnc as V
    ok, tb = V._st("ST=DA_LAM Da go TightVNC", "")
    assert ok and tb == "Đã gỡ TightVNC"


def test_dns_tls_co_dau():
    import pathlib
    goc = pathlib.Path(__file__).resolve().parent.parent / "src"
    tls = (goc / "consolesystem/assets/nettools/tls_check.TLS_TEMPLATE.html").read_text(encoding="utf-8")
    assert '"Có" if result.tu_ky else "Không"' in tls and '"Co"' not in tls
    dns = (goc / "nettools/dns_check.py").read_text(encoding="utf-8")
    assert "ĐỊA CHỈ KHÁC HẲN" in dns and "DIA CHI KHAC" not in dns
