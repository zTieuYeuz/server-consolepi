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


def test_rustdesk_mat_khau_khong_nam_trong_html(monkeypatch):
    """LOI-003 (Cao): trang tu xa cua may KHONG chua mat khau (khong value=, khong data-mk, khong ?password=); chi lay qua API khi bam."""
    from consolesystem.features.uem import uem_rustdesk as U
    monkeypatch.setattr(U.RD, "doc_cfg", lambda: {"may": {"m1": {"id": "123456789", "mk": "BiMat-xyz9"}}, "mk_chung": "Chung-abc1"})
    monkeypatch.setattr(U.RD, "trang_thai", lambda: {"da_cai": True, "dia_chi": {"id": "10.0.0.1"}})
    h = U.khoi_tu_xa({"id": "m1", "ip": "10.0.0.5"})
    assert "BiMat-xyz9" not in h and "Chung-abc1" not in h and "?password=" not in h and "data-mk" not in h
    assert ">••••••••</span>" in h and "/rustdesk/api/xem-mat-khau" in h and "/rustdesk/api/ket-noi" in h
    h2 = U.khoi_tu_xa({"id": "m2", "ip": "10.0.0.6"})                          # may chua co ID: form Luu khong dien san mat khau chung
    assert "Chung-abc1" not in h2 and "Để trống = dùng mật khẩu chung" in h2


def test_trang_rustdesk_script_che_mat_khau():
    from consolesystem.features.rustdesk import rustdesk as R
    assert "function mkO(co,mid)" in R.TRANG and "data-hien-mk" in R.TRANG and "/rustdesk/api/xem-mat-khau" in R.TRANG
    assert "data-mk" not in R.TRANG and "d.mk_chung" not in R.TRANG and "x.mk)" not in R.TRANG


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


def test_ping_nhieu_dich(monkeypatch):
    from nettools import connectivity as CN
    assert CN.tach_dich("a.com, 1.1.1.1  8.8.8.8;a.com") == ["a.com", "1.1.1.1", "8.8.8.8"]
    assert len(CN.tach_dich(",".join(f"h{i}.com" for i in range(20)))) == CN.TOI_DA_DICH and CN.tach_dich(" , ") == []
    monkeypatch.setattr(CN, "run_ping", lambda h, iface=None, **k: f"PING {h}\n4 packets transmitted, 4 received, {'0' if h == 'ok.com' else '100'}% packet loss, time 3ms\n")
    ra = CN.ping_nhieu(["ok.com", "chet.com"], iface="eth0")
    assert "=== ok.com ===\n4 packets transmitted, 4 received, 0% packet loss" in ra and "=== chet.com ===" in ra and "100% packet loss" in ra
    assert CN.ping_nhieu(["ok.com"]).startswith("PING ok.com")                  # 1 dich: giu nguyen ket qua day du nhu cu


def test_ping_qua_8_dich_bao_ro_dich_bi_bo_va_cau_loi_co_dau(monkeypatch):
    """LOI-001: nhap 9 dich thi khong bo lang le dich thu 9; dich sai bao co dau."""
    from flask import Flask
    from nettools import connectivity as CN, nettools_bp
    assert CN.tach_dich_day_du(",".join(f"h{i}.com" for i in range(1, 10))) == ([f"h{i}.com" for i in range(1, 9)], ["h9.com"])
    monkeypatch.setattr(CN, "run_ping", lambda h, iface=None, **k: f"PING {h}\n4 packets transmitted, 4 received, 0% packet loss\n")
    monkeypatch.setattr(CN, "_o_chon_cong", lambda *a, **k: "")
    monkeypatch.setattr(CN, "_cong_mac_dinh", lambda: "eth0")
    app = Flask(__name__)
    app.register_blueprint(nettools_bp)
    c = app.test_client()
    t = c.post("/nettools/ping", data={"host": " ".join(f"127.0.0.{i}" for i in range(1, 10)), "che_do": "ping"}).get_data(as_text=True)
    assert "tối đa 8 đích" in t and "Đã bỏ qua 1 đích: 127.0.0.9" in t and "=== 127.0.0.8 ===" in t and "=== 127.0.0.9 ===" not in t
    t = c.post("/nettools/ping", data={"host": "-rf", "che_do": "ping"}).get_data(as_text=True)
    assert "địa chỉ không hợp lệ" in t and "dia chi khong hop le" not in t
    t = c.post("/nettools/ping", data={"host": "1.1.1.1 2.2.2.2 3.3.3.3 4.4.4.4 5.5.5.5 6.6.6.6 7.7.7.7 8.8.8.8 -rf", "che_do": "ping"}).get_data(as_text=True)
    assert "địa chỉ không hợp lệ" in t                      # dich sai nam o vi tri thu 9 van bi chan


def test_ram_gb_theo_thanh_ram_khong_bi_lech_do_bo_nho_giu():
    from consolesystem.features.uem import uem_trang as T
    r = {"computer": {"memory": "7 GB"}, "memoryslots": [{"size": "8 GB"}]}              # may 8 GB: TotalPhysicalMemory chi bao 7 GB
    assert T.ram_gb(r) == 8
    assert T.ram_gb({"computer": {"memory": "7 GB"}, "memoryslots": [{"size": "4 GB"}, {"size": "4096 MB"}]}) == 8
    assert T.ram_gb({"computer": {"memory": "3 GB"}, "memoryslots": []}) == 3            # khong co thanh RAM (may ao): dung memory


def test_profile_ket_qua_agent_tu_ap_dung_duoc_viet_hoa():
    import inspect
    from consolesystem.features.uem import uem_profiles as P, uem_profiles_trang as PT
    assert "UB.viet_hoa(str(r.get(\"tb\", \"\")))" in inspect.getsource(P)
    assert "UB.viet_hoa(tb)" in inspect.getsource(PT)


def test_pxe_van_tat_la_form_rieng_co_input_an():
    from consolesystem.features.deploy_os import dosui_caidat as C
    ma = open(C.__file__, encoding="utf-8").read()
    assert 'name="ep" value="1"' in ma and 'name="ep" value="1" class' not in ma        # input an trong form rieng, khong dua vao nut submit
