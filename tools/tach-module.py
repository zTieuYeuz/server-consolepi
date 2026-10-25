#!/usr/bin/env python3
"""B4: tach cac khoi cap cao cua mot module lon thanh nhieu module nho (DI CHUYEN THUAN TUY, nguyen van tung dong).

  tach-module.py SPEC.json [--thu]

SPEC: {"nguon": duong file, "goi": "ten.goi.python", "nhom": {"ten_module": [[dong_dau, dong_cuoi), ...], ...},
       "giu_o_nguon": [ten, ...], "bo_qua": [ten, ...], "doc": {"ten_module": "mo ta"}}
Moi khoi cap cao (def/gan) thuoc nhom theo DONG BAT DAU. Module moi nhan ban sao khoi import cua nguon (ruff go phan thua) + import ro rang
nhung ten no dung ma nhom khac dinh nghia. Nguon giu lai moi thu con lai + import lai MOI ten da chuyen (de `ui.<ten>.<ham>` van chay).
Dung --thu de chi in ke hoach / kiem vong phu thuoc."""
import ast
import collections
import json
import os
import re
import subprocess
import sys

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def doc_spec(p):
    return json.load(open(p, encoding="utf-8"))


def khoi_cap_cao(cay, dong):
    """[(ten_list, node, dong_dau_ke_ca_chu_thich, dong_cuoi)]"""
    ra = []
    truoc = 0
    for n in cay.body:
        if isinstance(n, ast.FunctionDef):
            ten = [n.name]
        elif isinstance(n, ast.ClassDef):
            ten = [n.name]
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            tg = n.targets if isinstance(n, ast.Assign) else [n.target]
            ten = [x.id for t in tg for x in ast.walk(t) if isinstance(x, ast.Name)]
        else:
            continue
        bat_dau = min([n.lineno] + [d.lineno for d in getattr(n, "decorator_list", [])])
        b = bat_dau - 1
        while b > 0 and (dong[b - 1].lstrip().startswith("#")) and b > truoc:
            b -= 1
        ra.append((ten, n, b + 1 if b < bat_dau - 1 else bat_dau, n.end_lineno))
        truoc = n.end_lineno
    return ra


def main(argv):
    spec = doc_spec(argv[0])
    thu = "--thu" in argv
    nguon = os.path.join(GOC, spec["nguon"])
    src = open(nguon, encoding="utf-8").read()
    dong = src.split("\n")
    cay = ast.parse(src)
    khoi = khoi_cap_cao(cay, dong)
    bo_qua, giu = set(spec.get("bo_qua", [])), set(spec.get("giu_o_nguon", []))
    nhom_cua = {}
    for ten_mod, dai in spec["nhom"].items():
        for a, b in dai:
            for ten, n, d0, d1 in khoi:
                if a <= n.lineno < b and not (set(ten) & (bo_qua | giu)):
                    nhom_cua[id(n)] = ten_mod
    for ten, n, d0, d1 in khoi:                                 # ep_nhom: ep mot ten sang nhom khac (de pha vong phu thuoc)
        for t in ten:
            if t in spec.get("ep_nhom", {}):
                nhom_cua[id(n)] = spec["ep_nhom"][t]
    dinh_nghia = {}                                    # ten -> nhom
    for ten, n, d0, d1 in khoi:
        g = nhom_cua.get(id(n))
        if g:
            for t in ten:
                dinh_nghia[t] = g
    # phu thuoc giua cac nhom + vao nguon
    ten_nguon = {t for ten, n, d0, d1 in khoi if id(n) not in nhom_cua for t in ten}
    dep = collections.defaultdict(set)
    vao_nguon = collections.defaultdict(set)
    can_nhap = collections.defaultdict(lambda: collections.defaultdict(set))   # nhom -> nhom_khac -> ten
    for ten, n, d0, d1 in khoi:
        g = nhom_cua.get(id(n))
        if not g:
            continue
        dung = {x.id for x in ast.walk(n) if isinstance(x, ast.Name)}
        for u in dung:
            if u in dinh_nghia and dinh_nghia[u] != g:
                dep[g].add(dinh_nghia[u])
                can_nhap[g][dinh_nghia[u]].add(u)
            elif u in ten_nguon and u not in set(ten):
                vao_nguon[g].add(u)
    print("nhom:", {g: sum(1 for ten, n, a, b in khoi if nhom_cua.get(id(n)) == g) for g in spec["nhom"]})
    print("phu thuoc nhom:", {g: sorted(v) for g, v in dep.items()})
    if any(vao_nguon.values()):
        print("CANH BAO - nhom dung ten con o nguon (se vong import):", {g: sorted(v) for g, v in vao_nguon.items() if v})
    # kiem vong
    def co_vong():
        trang = {}
        def dfs(u):
            trang[u] = 1
            for v in dep.get(u, ()):
                if trang.get(v) == 1 or (v not in trang and dfs(v)):
                    return True
            trang[u] = 2
            return False
        return any(dfs(g) for g in list(dep) if g not in trang)
    if co_vong():
        print("VONG phu thuoc giua cac nhom - dung")
        return 1
    if thu:
        return 0
    if any(vao_nguon.values()):
        return 1
    # ---- dau ra
    goi = spec["goi"]
    thu_muc = os.path.join(GOC, "src", *goi.split("."))
    # khoi import goc: moi import cap cao truoc khoi dau tien
    dau = min(d0 for ten, n, d0, d1 in khoi if id(n) in nhom_cua)     # chi tinh khoi SE CHUYEN
    import_goc = [l for l in dong[:dau - 1]]
    tiep_dau = "\n".join(import_goc)
    # bo docstring+alias cua nguon: chi giu cac dong import
    imps = []
    for n in cay.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)) and n.lineno < dau:
            imps.append("\n".join(dong[n.lineno - 1:n.end_lineno]))
    imps = [x for x in imps if "import sys as _sys" not in x]
    khoi_chuyen = collections.defaultdict(list)
    xoa = []
    for ten, n, d0, d1 in khoi:
        g = nhom_cua.get(id(n))
        if g:
            khoi_chuyen[g].append((d0, d1))
            xoa.append((d0, d1))
    for g, ds in khoi_chuyen.items():
        phan = []
        for d0, d1 in ds:
            phan.append("\n".join(dong[d0 - 1:d1]))
        nhap = []
        for g2, ten in sorted(can_nhap[g].items()):
            nhap.append("from %s.%s import (%s)  # noqa: F401" % (goi, g2, ", ".join(sorted(ten))))
        mo_ta = spec.get("doc", {}).get(g, "Tach tu %s (B4)." % os.path.basename(spec["nguon"]))
        nd = ('# Console System - (c) 2026 zTieuYeuz. All rights reserved.\n"""%s\n\n(B4: tach nguyen van tu %s; ten ham/hang giu nguyen, nguon van re-export.)"""\n'
              % (mo_ta, os.path.basename(spec["nguon"])) + "\n".join(imps) + "\n" + "\n".join(nhap) + "\n\n\n" + "\n\n".join(phan) + "\n")
        open(os.path.join(thu_muc, g + ".py"), "w", encoding="utf-8").write(nd)
    # nguon moi
    giu_dong = set()
    for d0, d1 in xoa:
        giu_dong.update(range(d0, d1 + 1))
    moi = [l for i, l in enumerate(dong, start=1) if i not in giu_dong]
    nhap_nguon = []
    for g in spec["nhom"]:
        ten = sorted({t for t, gg in dinh_nghia.items() if gg == g})
        if ten:
            nhap_nguon.append("from %s.%s import (%s)  # noqa: F401  (B4: nguyen van o module nay)" % (goi, g, ", ".join(ten)))
    # chen sau import cuoi cua nguon
    idx = max(n.end_lineno for n in cay.body if isinstance(n, (ast.Import, ast.ImportFrom)) and n.lineno < dau)
    # (alias `_sys.modules[...] = ...` nam giua cac import: chen SAU import cuoi truoc khoi dau tien)
    # idx tinh theo dong goc; chuyen sang chi so trong `moi` (cac dong < dau khong doi)
    moi[idx:idx] = nhap_nguon
    open(nguon, "w", encoding="utf-8").write("\n".join(moi))
    print("da tach %d khoi thanh %d module" % (len(xoa), len(khoi_chuyen)))
    # don import thua o module moi
    cac = [os.path.join(thu_muc, g + ".py") for g in khoi_chuyen]
    subprocess.run(["/opt/devtools/bin/ruff", "check", "--select", "F401", "--fix", "-q"] + cac, cwd=GOC)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
