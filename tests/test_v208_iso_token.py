"""2.0.8 V7-2: build ISO that bai neu co cf-access.json tren may build (tru khi chu build cho phep ro rang cho ISO noi bo)."""
import os
import re
import subprocess

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _khoi():
    s = open(os.path.join(GOC, "iso", "dung-cay-build.sh"), encoding="utf-8").read()
    m = re.search(r"    if \[ -s /root/\.config/zt/cf-access\.json \]; then\n(.*?)\n    fi\n", s, re.S)
    assert m, "khong thay khoi cf-access"
    return m.group(0)


def _chay(tmp_path, co_tep, env_them=None):
    tep = tmp_path / "cf-access.json"
    if co_tep:
        tep.write_text('{"id": "x"}')
    R = tmp_path / "R"
    khoi = _khoi().replace("/root/.config/zt/cf-access.json", str(tep))
    kb = 'R="%s"\n%s\necho TIEP_TUC\n' % (R, khoi)
    env = dict(os.environ, **(env_them or {}))
    env.pop("CS_CHO_PHEP_NHUNG_TOKEN_CF", None)
    env.update(env_them or {})
    r = subprocess.run(["bash", "-c", kb], capture_output=True, text=True, env=env, timeout=20)
    return r, R


def test_co_tep_token_thi_dung_build_va_khong_nhung(tmp_path):
    r, R = _chay(tmp_path, True)
    assert r.returncode == 1 and "TIEP_TUC" not in r.stdout and "DUNG BUILD" in r.stderr
    assert not (R / "var/lib/console-system/secrets/cf-access.json").exists()


def test_khong_co_tep_thi_di_tiep(tmp_path):
    r, R = _chay(tmp_path, False)
    assert r.returncode == 0 and "TIEP_TUC" in r.stdout


def test_chu_build_cho_phep_ro_rang_cho_iso_noi_bo(tmp_path):
    r, R = _chay(tmp_path, True, {"CS_CHO_PHEP_NHUNG_TOKEN_CF": "1"})
    assert r.returncode == 0 and "TIEP_TUC" in r.stdout and "CANH BAO" in r.stderr
    assert (R / "var/lib/console-system/secrets/cf-access.json").exists()
