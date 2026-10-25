#!/usr/bin/env python3
"""B8: sinh docs/MODULES.md (muc luc module + mo ta dong dau docstring) tu ma nguon. Chay lai moi khi them/doi module:
    tools/tao-tai-lieu-module.py          (ghi docs/MODULES.md)       tools/tao-tai-lieu-module.py --kiem   (loi neu file cu hon ma nguon)"""
import ast
import os
import sys

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(GOC, "src")
DICH = os.path.join(GOC, "docs", "MODULES.md")


def dong_dau(doc):
    for d in (doc or "").strip().split("\n"):
        d = d.strip().strip('"').strip()
        if d and not d.startswith(("Console System - (c)", "=", "-")):
            return d[:160].replace("|", "/")
    return ""


def sinh():
    ra = ["# Muc luc module (TU DONG SINH - khong sua tay)", "",
          "Sinh boi `tools/tao-tai-lieu-module.py` tu docstring dau moi file. Kien truc va quy tac: xem `KIEN-TRUC.md`; thuat ngu: `TU-DIEN.md`.", ""]
    nhom = {}
    for d, ds, fs in os.walk(os.path.join(SRC, "consolesystem")):
        ds[:] = sorted(x for x in ds if x != "__pycache__")
        for f in sorted(fs):
            if f.endswith(".py") and f != "__init__.py":
                p = os.path.join(d, f)
                rel = os.path.relpath(p, SRC)
                k = os.path.dirname(rel)
                nhom.setdefault(k, []).append((f, dong_dau(ast.get_docstring(ast.parse(open(p, encoding="utf-8").read()))), sum(1 for _ in open(p, encoding="utf-8"))))
    for k in sorted(nhom):
        ra += ["## `%s`" % k, "", "| File | Dong | Vai tro |", "|---|---:|---|"]
        ra += ["| `%s` | %d | %s |" % (f, n, mo) for f, mo, n in nhom[k]]
        ra.append("")
    return "\n".join(ra)


if __name__ == "__main__":
    nd = sinh()
    if "--kiem" in sys.argv:
        cu = open(DICH, encoding="utf-8").read() if os.path.exists(DICH) else ""
        if cu != nd:
            print("docs/MODULES.md da cu - chay tools/tao-tai-lieu-module.py")
            sys.exit(1)
        print("MODULES.md moi")
    else:
        open(DICH, "w", encoding="utf-8").write(nd)
        print("da ghi", DICH, len(nd.split("\n")), "dong")
