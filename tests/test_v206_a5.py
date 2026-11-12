"""2.0.6 A5: kich ban Agent co buoc script + khoi dong lai (tien trinh rieng, bo cuc moi tam)."""
import json
import os
import subprocess
import sys

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_kich_ban_agent_script_khoi_dong_lai(tmp_path):
    sys.path.insert(0, os.path.join(GOC, "src"))
    from ui import dichuyen as DM
    goc = str(tmp_path / "cs")
    DM.tao_bo_cuc_moi(goc)
    r = subprocess.run(["python3", os.path.join(GOC, "tests", "web_kichban_khoidonglai.py")], capture_output=True, text=True,
                       env=dict(os.environ, CONSOLE_PI_DATA=goc), timeout=180)
    dong = [x for x in r.stdout.splitlines() if x.startswith("KETQUA ")]
    assert dong, r.stdout[-1500:] + r.stderr[-1500:]
    kq = json.loads(dong[0][7:])
    sai = [k for k, v in kq.items() if v is not True]
    assert not sai, (sai, r.stderr[-800:])


def test_canh_bao_ha_cap_noi_ro_agent_ghi_danh_sau_nang_cap_phai_cai_lai():
    src = open(os.path.join(GOC, "src", "consolesystem", "core", "capnhat", "nangcap.py"), encoding="utf-8").read()
    assert "cài agent SAU" in src and "403" in src and "cài lại agent" in src
