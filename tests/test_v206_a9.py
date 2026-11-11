"""2.0.6 A9: trang thai gia nhap domain o trang Tien trinh (tien trinh rieng, bo cuc moi tam)."""
import json
import os
import subprocess
import sys

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_trang_thai_domain_o_trang_tien_trinh(tmp_path):
    sys.path.insert(0, os.path.join(GOC, "src"))
    from ui import dichuyen as DM
    goc = str(tmp_path / "cs")
    DM.tao_bo_cuc_moi(goc)
    r = subprocess.run(["python3", os.path.join(GOC, "tests", "web_a9_domain.py")], capture_output=True, text=True,
                       env=dict(os.environ, CONSOLE_PI_DATA=goc), timeout=180)
    dong = [x for x in r.stdout.splitlines() if x.startswith("KETQUA ")]
    assert dong, r.stdout[-1500:] + r.stderr[-1500:]
    kq = json.loads(dong[0][7:])
    sai = [k for k, v in kq.items() if v is not True]
    assert not sai, (sai, r.stderr[-800:])


def test_script_tien_trinh_bao_domain_va_bao_cao_cuoi():
    sys.path.insert(0, os.path.join(GOC, "src"))
    from consolesystem.features.deploy_os.un_tientrinh import sinh_script_tien_trinh
    from consolesystem.features.deploy_os.un_kiemtra import _danh_sach_buoc_nguoi_dung  # noqa: F401
    ps = sinh_script_tien_trinh({"domain": "home.local"}, "10.0.0.1")
    assert "$DomainMuonVao = 'home.local'" in ps and "function KiemDomain" in ps
    assert ps.count("KiemDomain\n") == 2                                  # luc dau va truoc khi ket thuc
    assert "0x52e" in ps and "NetSetup.log" in ps and "'domain' @{" in ps
    assert ps.count("{") == ps.count("}") and ps.count("(") == ps.count(")")
    assert "KiemDomain" not in sinh_script_tien_trinh({}, "10.0.0.1")       # khong domain: khong them gi
    from consolesystem.features.deploy_os import un_kiemtra
    nguon = open(un_kiemtra.__file__, encoding="utf-8").read()
    assert "ĐÃ VÀO DOMAIN '" in nguon                                      # bao cao cuoi: nhan ro khi vao domain thanh cong
