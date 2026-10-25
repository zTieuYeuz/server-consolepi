#!/usr/bin/env python3
"""B6: tach hang so chuoi LON (>= --toi-thieu dong) o cap module ra file trong src/consolesystem/assets/, thay bang taisan.doc(...).
Gia tri chuoi KHONG doi (kiem lai bang cach nap module truoc/sau). Dung: tach-tai-nguyen.py [--toi-thieu 60] [--lam] file.py ...
Khong co --lam: chi liet ke."""
import argparse
import ast
import os
import re
import sys

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(GOC, "src")
ASSETS = os.path.join(SRC, "consolesystem", "assets")


def doan_duoi(ten, nd):
    t = nd.lstrip()
    if re.search(r"(?m)^\s*(param\(|\$[A-Za-z_]+\s*=|Write-Host|function\s+\w+-?\w*\s*\{)", nd) and "<html" not in nd.lower():
        return ".ps1"
    if t.startswith("<!DOCTYPE") or t.startswith("<html") or re.match(r"^<\w+", t):
        return ".html"
    if re.search(r"(?m)^\s*(function\s+\w+\(|const\s+\w+\s*=|let\s+\w+\s*=|var\s+\w+\s*=|document\.|window\.)", nd):
        return ".js"
    if re.search(r"(?m)^\s*[.#:\w\s,>-]+\{\s*$", nd) and ";" in nd:
        return ".css"
    return ".txt"


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--toi-thieu", type=int, default=60)
    ap.add_argument("--lam", action="store_true")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args(argv)
    for rel in a.files:
        p = os.path.abspath(rel)
        nguon = open(p, encoding="utf-8").read()
        dong = nguon.split("\n")
        tree = ast.parse(nguon)
        viec = []
        for nd in tree.body:
            if (isinstance(nd, ast.Assign) and len(nd.targets) == 1 and isinstance(nd.targets[0], ast.Name)
                    and isinstance(nd.value, ast.Constant) and isinstance(nd.value.value, str)
                    and nd.end_lineno - nd.lineno + 1 >= a.toi_thieu):
                viec.append(nd)
        if not viec:
            continue
        mod = os.path.relpath(p, os.path.join(SRC, "consolesystem")) if p.startswith(os.path.join(SRC, "consolesystem")) else os.path.relpath(p, SRC)
        mod = os.path.splitext(mod)[0].replace(os.sep, "/")
        for nd in reversed(viec):
            ten, gt = nd.targets[0].id, nd.value.value
            duong = "%s.%s%s" % (mod, ten, doan_duoi(ten, gt))
            print("%s:%d %s -> assets/%s (%d dong)" % (rel, nd.lineno, ten, duong, nd.end_lineno - nd.lineno + 1))
            if a.lam:
                d = os.path.join(ASSETS, os.path.dirname(duong))
                os.makedirs(d, exist_ok=True)
                with open(os.path.join(ASSETS, duong), "wb") as f:
                    f.write(gt.encode("utf-8"))
                dong[nd.lineno - 1:nd.end_lineno] = ['%s = _taisan.doc("%s")' % (ten, duong)]
        if a.lam:
            s = "\n".join(dong)
            t2 = ast.parse(s)
            imp = [n for n in t2.body if isinstance(n, (ast.Import, ast.ImportFrom))]
            if "import taisan as _taisan" not in s:
                L = s.split("\n")
                k = imp[0].lineno - 1 if imp else (t2.body[0].end_lineno if isinstance(t2.body[0], ast.Expr) else 0)
                if imp and isinstance(imp[0], ast.ImportFrom) and imp[0].module == "__future__":
                    k = imp[0].end_lineno
                L.insert(k, "from consolesystem.core import taisan as _taisan")
                s = "\n".join(L)
            ast.parse(s)
            open(p, "w", encoding="utf-8").write(s)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
