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


def test_rustdesk_che_mat_khau_trong_html(monkeypatch):
    from consolesystem.features.uem import uem_rustdesk as U
    monkeypatch.setattr(U.RD, "doc_cfg", lambda: {"may": {"m1": {"id": "123456789", "mk": "BiMat-xyz9"}}})
    monkeypatch.setattr(U.RD, "trang_thai", lambda: {"da_cai": True, "dia_chi": {"id": "10.0.0.1"}})
    h = U.khoi_tu_xa({"id": "m1", "ip": "10.0.0.5"})
    assert 'href="rustdesk://connection/new/123456789"' in h                    # href khong mang mat khau
    assert "?password=" not in h.split("onclick")[0]
    assert ">••••••••</span>" in h and 'data-mk="BiMat-xyz9"' in h              # che mac dinh, co nut hien/an
    assert h.count("BiMat-xyz9") == 2 and ">BiMat-xyz9<" not in h               # khong hien chu ro trong noi dung


def test_trang_rustdesk_script_che_mat_khau():
    from consolesystem.features.rustdesk import rustdesk as R
    assert "function mkO(mk)" in R.TRANG and "data-hien-mk" in R.TRANG
    assert "'+e(x.mk)+'</span>" not in R.TRANG and "e(x.mk||'chưa đặt')" not in R.TRANG


def test_tien_trinh_dich_vu_co_sap_xep_theo_cot():
    from consolesystem.features.uem import uem_dieukhien as K
    t = K.TRANG_DS
    assert "th('cpu','CPU (giây)')" in t and "th('mem','RAM (MB)')" in t and "th('state','Trạng thái')" in t
    assert "function sx(a)" in t and "t.dataset.s" in t
    assert t.count("{") == t.count("}") and t.count("(") == t.count(")") and t.count("[") == t.count("]")


def test_nhat_ky_thao_tac_khong_ghi_nhip_agent(tmp_path, monkeypatch):
    from consolesystem.core import errlog as EL

    class Req:
        method = "POST"
        form = {}

        def __init__(self, path):
            self.path = path

    class Resp:
        status_code = 200

    monkeypatch.setattr(EL, "LOG_THAO_TAC", str(tmp_path / "thao-tac.log"))
    monkeypatch.setattr(EL, "_NGU_CANH", lambda: ("admin", "10.0.0.1"))
    EL.ghi_thao_tac_tu_dong(Req("/uem/agent/nhip"), Resp())
    EL.ghi_thao_tac_tu_dong(Req("/uem/agent/ketqua"), Resp())
    assert not os.path.exists(EL.LOG_THAO_TAC)                       # nhip/ket qua dinh ky cua agent khong lam nhieu nhat ky
    EL.ghi_thao_tac_tu_dong(Req("/deployos/kichban/xoa"), Resp())
    assert "/deployos/kichban/xoa" in open(EL.LOG_THAO_TAC, encoding="utf-8").read()
    EL.ghi_thao_tac_tu_dong(Req("/uem/may/abc/dich-vu/api"), Resp())
    EL.ghi_thao_tac_tu_dong(Req("/uem/may/abc/duyet-file/xoa"), Resp())
    assert "dich-vu/api" not in open(EL.LOG_THAO_TAC, encoding="utf-8").read()        # da co cau dien giai tu ghi_tac_vu


def test_ram_gb_va_loai_o_dia():
    from consolesystem.features.uem import uem_trang as T
    assert T.ram_gb({"computer": {"memory": "16 GB"}}) == 16 and T.ram_gb({"computer": {"memory": "512 MB"}}) == 0.5
    assert T.ram_gb({"computer": {}}) is None and T.ram_gb({}) is None
    r = {"physicaldisks": [{"model": "WDC WD10", "media_type": "HDD"}, {"model": "Samsung SSD 860", "media_type": "Unknown"}, {"model": "VMware Virtual disk"}, {"model": "ABC"}]}
    assert T.loai_o_dia(r) == ["HDD", "SSD", "Chưa rõ", "Ổ ảo"] or set(T.loai_o_dia(r)) == {"HDD", "SSD", "Chưa rõ", "Ổ ảo"}
