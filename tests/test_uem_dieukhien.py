"""Dong lenh / dich vu / tien trinh tu xa, xoa may khoi quan ly, xoa dong tien do (tien trinh rieng, bo cuc moi tam)."""
import json
import os
import subprocess
import sys

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_kich_ban_web_uem(tmp_path):
    sys.path.insert(0, os.path.join(GOC, "src"))
    from ui import dichuyen as DM
    goc = str(tmp_path / "cs")
    DM.tao_bo_cuc_moi(goc)
    r = subprocess.run(["python3", os.path.join(GOC, "tests", "web_uem_kichban.py")], capture_output=True, text=True,
                       env=dict(os.environ, CONSOLE_PI_DATA=goc), timeout=180)
    dong = [x for x in r.stdout.splitlines() if x.startswith("KETQUA ")]
    assert dong, r.stdout[-1500:] + r.stderr[-1500:]
    kq = json.loads(dong[0][7:])
    sai = [k for k, v in kq.items() if v is not True]
    assert not sai, (sai, r.stderr[-800:])


def test_file_cai_agent_bat_tu_nang_quyen_va_bo_qua_execution_policy():
    sys.path.insert(0, os.path.join(GOC, "src"))
    import base64
    import re
    from consolesystem.features.uem import uem_agent_goi as G
    ps1 = "# test\r\n$Servers = @('https://10.0.0.1:8443'); Write-Host 'xin chao'\r\n" * 40
    bat = G._bat(ps1)
    assert "-ExecutionPolicy Bypass" in bat and "-Verb RunAs" in bat
    b64 = "".join(re.findall(r"^::B64:(.*?)\r?$", bat, re.M))
    assert base64.b64decode(b64).decode("utf-8") == ps1
    assert all(len(l) < 300 for l in bat.splitlines())
