#!/usr/bin/env python3
"""V1-4/V6-6 (2.0.8): liet ke route POST co doc `request.files` (truc tiep hoac qua ham tro giup cung module, toi da 3 tang) -> tests/hop-dong/route-tai-len.txt.
Dung de (1) sinh/kiem regex nginx 'duoc phep body lon', (2) test bat buoc nginx va danh sach nay khop nhau.
    xuat-route-upload.py [dau-ra]    (mac dinh in ra stdout)"""
import ast
import inspect
import os
import runpy
import sys
import tempfile
import textwrap
import threading

GOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(GOC, "src")


def _doc_request_files(ham, goc, depth=3, thay=None):
    thay = thay if thay is not None else set()
    try:
        nguon = textwrap.dedent(inspect.getsource(ham))
    except (OSError, TypeError):
        return False
    if "request.files" in nguon or ".files.get(" in nguon:
        return True
    if depth == 0:
        return False
    mod = inspect.getmodule(ham)
    try:
        cay = ast.parse(nguon)
    except SyntaxError:
        return False
    for n in ast.walk(cay):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            f = getattr(mod, n.func.id, None) if mod else None
            if inspect.isfunction(f) and f not in thay:
                thay.add(f)
                if _doc_request_files(f, goc, depth - 1, thay):
                    return True
    return False


def main():
    os.environ.setdefault("CONSOLE_PI_LOG", tempfile.mkdtemp(prefix="cs-xuat-log-"))
    sys.path.insert(0, SRC)
    os.chdir(SRC)
    goc = threading.Thread.start
    threading.Thread.start = lambda self: None
    app = runpy.run_path(os.path.join(SRC, "app.py"), run_name="dev")["app"]
    threading.Thread.start = goc
    ra = set()
    for rule in app.url_map.iter_rules():
        if "POST" not in rule.methods:
            continue
        ham = app.view_functions.get(rule.endpoint)
        if ham and _doc_request_files(inspect.unwrap(ham), GOC):
            ra.add(str(rule))
    out = "\n".join(sorted(ra)) + "\n"
    if len(sys.argv) > 1:
        open(sys.argv[1], "w", encoding="utf-8").write(out)
    else:
        sys.stdout.write(out)


if __name__ == "__main__":
    main()
