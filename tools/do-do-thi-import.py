#!/usr/bin/env python3
"""Do do thi import giua cac module cua consolesystem (+ nettools): canh TOP-LEVEL (chay luc import) va canh LAZY (trong ham).
Cau noi `ui/<ten>.py` duoc quy ve module that. Dung:  do-do-thi-import.py [--lazy] [--vong]   |   dung nhu thu vien: phan_tich()"""
import ast
import os
import sys

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(GOC, "src")


def liet_ke_module():
    ra = {}                                   # ten day du -> duong file
    for goc in ("consolesystem", "nettools"):
        for d, _ds, fs in os.walk(os.path.join(SRC, goc)):
            for f in fs:
                if f.endswith(".py"):
                    rel = os.path.relpath(os.path.join(d, f), SRC)[:-3].replace(os.sep, ".")
                    ra[rel[:-9] if rel.endswith(".__init__") else rel] = os.path.join(d, f)
    return ra


def cau_noi(modules):
    """ui.<ten> -> ten that (doc tu file cau noi)."""
    anh = {}
    for f in os.listdir(os.path.join(SRC, "ui")):
        if f.endswith(".py") and f != "__init__.py":
            nd = open(os.path.join(SRC, "ui", f), encoding="utf-8").read()
            if "import_module(" in nd:
                anh["ui." + f[:-3]] = nd.split('import_module("')[1].split('")')[0]
    return anh


def phan_tich():
    modules = liet_ke_module()
    anh = cau_noi(modules)
    top, lazy = {m: set() for m in modules}, {m: set() for m in modules}

    def giai(ten):
        ten = anh.get(ten, ten)
        return ten if ten in modules else None

    for m, p in modules.items():
        cay = ast.parse(open(p, encoding="utf-8").read())
        # xac dinh nut nao la top-level: khong nam trong def/class-method (class body van chay luc import)
        trong_ham = set()
        for n in ast.walk(cay):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                for c in ast.walk(n):
                    trong_ham.add(id(c))
        for n in ast.walk(cay):
            if not isinstance(n, (ast.Import, ast.ImportFrom)):
                continue
            ds = []
            if isinstance(n, ast.Import):
                ds = [a.name for a in n.names]
            elif n.level == 0 and n.module:
                ds = [n.module] + ["%s.%s" % (n.module, a.name) for a in n.names]
            elif n.level > 0:
                goc = m.rsplit(".", n.level)[0] if not p.endswith("__init__.py") else m.rsplit(".", n.level - 1)[0] if n.level > 1 else m
                base = goc + ("." + n.module if n.module else "")
                ds = [base] + ["%s.%s" % (base, a.name) for a in n.names]
            muc_tieu = {giai(x) for x in ds} - {None, m}
            # `from ui import ten` -> chi tinh module `ui.ten`, khong tinh goi ui
            for t in muc_tieu:
                (lazy if id(n) in trong_ham else top)[m].add(t)
    return modules, top, lazy


def scc(do_thi):
    chi_so, thap, stack, tren, ra, dem = {}, {}, [], set(), [], [0]
    sys.setrecursionlimit(10000)

    def duyet(v):
        chi_so[v] = thap[v] = dem[0]
        dem[0] += 1
        stack.append(v)
        tren.add(v)
        for w in do_thi.get(v, ()):
            if w not in chi_so:
                duyet(w)
                thap[v] = min(thap[v], thap[w])
            elif w in tren:
                thap[v] = min(thap[v], chi_so[w])
        if thap[v] == chi_so[v]:
            nhom = []
            while True:
                w = stack.pop()
                tren.discard(w)
                nhom.append(w)
                if w == v:
                    break
            if len(nhom) > 1:
                ra.append(sorted(nhom))
    for v in do_thi:
        if v not in chi_so:
            duyet(v)
    return ra


def main(argv):
    modules, top, lazy = phan_tich()
    tat = {m: top[m] | lazy[m] for m in modules} if "--lazy" in argv else top
    vong = scc(tat)
    print("module: %d | canh top-level: %d | canh lazy: %d | nhom vong (SCC>1): %d" % (
        len(modules), sum(len(v) for v in top.values()), sum(len(v) for v in lazy.values()), len(vong)))
    for g in vong:
        print("  VONG %d module: %s" % (len(g), ", ".join(x.replace("consolesystem.", "") for x in g)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
