"""A5: trang Cai dat > Sao luu/Khoi phuc qua Flask test client (tien trinh rieng, bo cuc moi tam)."""
import json
import os
import subprocess
import sys

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_luong_web_sao_luu_khoi_phuc(tmp_path):
    sys.path.insert(0, os.path.join(GOC, "src"))
    from ui import dichuyen as DM
    goc = str(tmp_path / "cs")
    DM.tao_bo_cuc_moi(goc)
    os.makedirs(os.path.join(goc, "deploy", "kichban"))
    for rel, nd in (("config/config.json", '{"x":1}'), ("secrets/flask-secret.key", "K"), ("data/may.json", "[]"),
                    ("deploy/kichban/a.json", "{}")):
        open(os.path.join(goc, rel), "w").write(nd)
    r = subprocess.run(["python3", os.path.join(GOC, "tests", "web_saoluu_kichban.py")], capture_output=True, text=True,
                       env=dict(os.environ, CONSOLE_PI_DATA=goc), timeout=120)
    dong = [x for x in r.stdout.splitlines() if x.startswith("KETQUA ")]
    assert dong, r.stdout[-800:] + r.stderr[-800:]
    kq = json.loads(dong[0][7:])
    assert all(v is True or v == "cauhinh" for v in kq.values()), kq
