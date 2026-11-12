"""2.0.7 cum 3: khung mat khau dung chung (tien trinh rieng, bo cuc moi tam)."""
import json
import os
import subprocess
import sys

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_khung_mat_khau_dung_chung(tmp_path):
    sys.path.insert(0, os.path.join(GOC, "src"))
    from ui import dichuyen as DM
    goc = str(tmp_path / "cs")
    DM.tao_bo_cuc_moi(goc)
    r = subprocess.run(["python3", os.path.join(GOC, "tests", "web_v207_khung_mk.py")], capture_output=True, text=True,
                       env=dict(os.environ, CONSOLE_PI_DATA=goc), timeout=180)
    dong = [x for x in r.stdout.splitlines() if x.startswith("KETQUA ")]
    assert dong, r.stdout[-1500:] + r.stderr[-1500:]
    kq = json.loads(dong[0][7:])
    sai = [k for k, v in kq.items() if v is not True]


def test_ham_khung_mat_khau():
    sys.path.insert(0, os.path.join(GOC, "src"))
    from consolesystem.web.khung_mk import o_mat_khau
    h = o_mat_khau("mk", "Mật khẩu", "gợi ý <x>", True, "o1")
    assert 'type="password"' in h and 'name="mk"' in h and "required" in h and 'autocomplete="new-password"' in h
    assert "&lt;x&gt;" in h and ">Hiện</button>" in h and "height:42px" in h and 'value=' not in h     # khong bao gio co value (mat khau da luu)
