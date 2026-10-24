"""Bo test nen B0: gom moi kiem tra chay OFFLINE ve mot lenh `pytest tests/`.
Cac bo can trinh duyet/may that (thu-banphim-ao, thu-chuot-terminal, ...) chua gom
o day - chay rieng theo buoc kiem tra trinh duyet."""
import os
import subprocess

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEST = os.path.join(GOC, "iso", "test")


def chay(lenh, timeout=900):
    return subprocess.run(lenh, cwd=GOC, capture_output=True, text=True, timeout=timeout)


def test_hop_dong_route(tmp_path):
    ra = tmp_path / "routes.txt"
    r = chay(["python3", "tools/xuat-route.py", str(ra)])
    assert r.returncode == 0, r.stderr
    mau = open(os.path.join(GOC, "tests", "hop-dong", "routes.txt"), encoding="utf-8").read()
    assert ra.read_text(encoding="utf-8") == mau


def test_golden_khop_tung_byte():
    r = chay(["python3", "tools/golden.py", "kiem"])
    assert r.returncode == 0, r.stdout + r.stderr


def test_python311_khong_loi():
    r = chay(["bash", "iso/test/kiem-python311.sh"])
    assert "loi 3.11: 0" in r.stdout, r.stdout + r.stderr


@pytest.mark.parametrize("tep,dau", [
    ("thu-uem.py", "HONG 0"),
    pytest.param("thu-trienkhai.py", "0 hong", marks=pytest.mark.xfail(strict=False, reason="1 kiem tra Kho trung tam phu thuoc kho-console.home-server.id.vn (24/10: tra 302, trang khong co nut loc) - khong do ma")),
    ("thu-nhat-ky.py", "0 hong"),
])
def test_bo_cu(tep, dau):
    r = chay(["python3", os.path.join(TEST, tep)])
    assert r.returncode == 0 and dau in r.stdout, r.stdout[-800:] + r.stderr[-400:]
