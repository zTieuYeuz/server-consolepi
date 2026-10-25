"""B2: moi module da chuyen phai import duoc DOC LAP (tien trinh moi) bang ca ten moi lan ten cu, hai ten cung mot doi tuong,
va ui/ chi con cau noi + tai nguyen."""
import ast
import concurrent.futures as cf
import os
import subprocess
import sys

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(GOC, "src")
sys.path.insert(0, GOC + "/tools")


def _anh_xa():
    """(ten cu, ten moi) doc tu chinh cac file cau noi ui/*.py (nguon su that, khong phu thuoc bang cua cong cu di chuyen)."""
    import re
    ra = []
    for f in sorted(os.listdir(os.path.join(SRC, "ui"))):
        if f.endswith(".py") and f != "__init__.py":
            m = re.search(r'import_module\("([^"]+)"\)', open(os.path.join(SRC, "ui", f), encoding="utf-8").read())
            if m:
                ra.append((f[:-3], m.group(1)))
    return ra


MODULES = _anh_xa()


def _chay(code):
    r = subprocess.run([sys.executable if False else "python3", "-c", code], cwd=SRC, capture_output=True, text=True, timeout=120)
    return r.returncode, (r.stdout + r.stderr)[-600:]


def test_moi_module_import_doc_lap_bang_ten_cu_va_ten_moi():
    viec = []
    for ten, moi in MODULES:
        viec.append((ten, "import ui.%s as a, %s as b; assert a is b, 'hai ten khac doi tuong'" % (ten, moi)))
        viec.append((ten, "import %s as b, ui.%s as a; assert a is b" % (moi, ten)))        # thu tu nguoc: ten moi nap truoc
    hong = []
    with cf.ThreadPoolExecutor(8) as ex:
        for (ten, code), (rc, out) in zip(viec, ex.map(lambda v: _chay(v[1]), viec)):
            if rc != 0:
                hong.append((ten, code, out))
    assert not hong, hong[:3]


def test_ui_chi_con_cau_noi_va_tai_nguyen():
    ngoai_le = {"__init__.py"}
    for f in sorted(os.listdir(os.path.join(SRC, "ui"))):
        if not f.endswith(".py") or f in ngoai_le:
            continue
        nd = open(os.path.join(SRC, "ui", f), encoding="utf-8").read()
        assert "sys.modules[__name__] = _il.import_module" in nd, "ui/%s con ma that, chua la cau noi" % f
        assert len(nd.splitlines()) < 15
        assert not [n for n in ast.parse(nd).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]


def test_khong_con_import_tuong_doi_trong_goi_moi():
    sai = []
    for d, _ds, fs in os.walk(os.path.join(SRC, "consolesystem")):
        for f in fs:
            if f.endswith(".py"):
                for n in ast.walk(ast.parse(open(os.path.join(d, f), encoding="utf-8").read())):
                    if isinstance(n, ast.ImportFrom) and n.level > 0:
                        if not (n.level <= 2 and (d.endswith("core") or "/core/" in d + "/")):          # core/ dung import tuong doi trong chinh no (store, esc...)
                            sai.append((f, n.lineno))
    assert not sai, sai[:5]
