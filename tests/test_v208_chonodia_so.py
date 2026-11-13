"""2.0.8 V3-2: che do chon o theo SO (mac dinh) phai qua loc an toan o USB/the nho truoc `diskpart ... clean`; cac che do khac khong doi."""
import importlib.util
import os
import sys

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))


def _golden_unused():
    sp = importlib.util.spec_from_file_location("golden", os.path.join(GOC, "tools", "golden.py"))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def _deploy_cmd(**sua):
    from ui import unattend as u
    co_ban = {"os_id": "windows_10_pro", "ten_may": "T1", "username": "nhanvien", "password": "Mau@1234", "mui_gio": "Asia/Ho_Chi_Minh",
              "o_dia_che_do": "tu_dong", "o_dia_so": "1"}
    co_ban.update(sua)
    return u.sinh_file_nhung(co_ban, "192.168.98.1")["deploy.cmd"].replace("\r\n", "\n")


def test_che_do_so_kiem_usb_truoc_khi_clean():
    t = _deploy_cmd()
    dong = t.splitlines()
    i_kiem = next(i for i, x in enumerate(dong) if "select disk 1& echo detail disk" in x)
    i_clean = next(i for i, x in enumerate(dong) if x.strip().startswith("diskpart /s %DPT%"))
    assert i_kiem < i_clean                                                        # kiem tra TRUOC khi chay script co `clean`
    for bus in ("USB", "SD", "MMC"):
        assert 'if /i "%%BUS%%"=="%s" goto loi_o_usb' % bus in t
    assert t.count("\n:loi_o_usb\n") == 1 and "goto bao_loi" in t.split(":loi_o_usb")[1].split("\n\n")[0]
    assert "O so 1 la o USB" in t                                                  # dung so o cua kich ban


def test_kich_ban_cho_phep_usb_thi_bo_loc():
    t = _deploy_cmd(o_dia_cho_usb="1")
    assert "loi_o_usb" not in t and "diskpart /s %DPT%" in t


def test_che_do_khac_khong_doi():
    for ch in ("model", "nho_nhat", "co_windows"):
        t = _deploy_cmd(o_dia_chon=ch, o_dia_model="Samsung")
        assert "loi_o_usb" not in t, ch                                           # duong cu (da loc USB trong _ham_chon_o) giu nguyen
        assert 'if /i "%BUS%"=="USB" exit /b 0' in t
