#!/usr/bin/env python3
"""B4 (giai doan 2): tach mot ham `register_xxx(app)` khong lo (hang tram route long) thanh nhieu module theo chuc nang.

  tach-register.py SPEC.json [--thu]

- Moi route (decorator `@app.route`) vao cum theo TIEN TO DUONG DAN (cum dau tien khop).
- Ham tro giup / hang long trong ham: neu chi MOT cum dung (ke ca gian tiep) -> nam o cum do; dung boi >=2 cum -> module `chung`.
- Ham tro giup duoc NANG len cap module (bo thut le 4 dau cach, KHONG dong vao noi dung chuoi nhieu dong).
- Moi cum co `register_<cum>(app)` chua cac route NGUYEN VAN; nguon giu `register_xxx(app)` goi lan luot cac register con.
Giu nguyen ten ham/endpoint. Doan khoi tao theo `app` (request_class...) nam trong `register_chung(app)`."""
import ast
import collections
import io
import json
import os
import re
import subprocess
import sys
import tokenize

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def khoang_chuoi_nhieu_dong(src):
    """Tap so dong (1-based) nam TRONG chuoi nhieu dong (khong tinh dong mo dau): khong duoc dedent."""
    ra = set()
    ngan_xep = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        ten = tokenize.tok_name[tok.type]
        if ten == "FSTRING_START":
            ngan_xep.append(tok.start[0])
        elif ten == "FSTRING_END":
            a = ngan_xep.pop()
            if not ngan_xep:                       # chi chuoi ngoai cung
                ra.update(range(a + 1, tok.end[0] + 1))
        elif ten == "STRING" and not ngan_xep and tok.end[0] > tok.start[0]:
            ra.update(range(tok.start[0] + 1, tok.end[0] + 1))
    return ra


def dedent(dong, a, z, trong_chuoi, n=4):
    ra = []
    for i in range(a, z + 1):
        l = dong[i - 1]
        if i in trong_chuoi or not l.startswith(" " * n):
            ra.append(l)
        else:
            ra.append(l[n:])
    return ra


def main(argv):
    spec = json.load(open(argv[0], encoding="utf-8"))
    thu = "--thu" in argv
    nguon = os.path.join(GOC, spec["nguon"])
    src = open(nguon, encoding="utf-8").read()
    dong = src.split("\n")
    cay = ast.parse(src)
    reg = [n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == spec["ham"]][0]
    trong_chuoi = khoang_chuoi_nhieu_dong(src)
    # ---- phan loai khoi trong than ham
    imports, units = [], []          # units: dict(ten, node, loai, d0, d1)
    for n in reg.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            imports.append("\n".join(l[4:] if l.startswith("    ") else l for l in dong[n.lineno - 1:n.end_lineno]))
            continue
        if isinstance(n, (ast.Expr, ast.Return, ast.Global)):
            continue
        if isinstance(n, ast.FunctionDef):
            route = [d for d in n.decorator_list if isinstance(d, ast.Call) and getattr(d.func, "attr", "") == "route"]
            if route:
                duong = route[0].args[0].value if route[0].args and isinstance(route[0].args[0], ast.Constant) else ""
                loai, ten = "route", [n.name]
            else:
                duong, loai, ten = "", "ham", [n.name]
        elif isinstance(n, ast.ClassDef):
            duong, loai, ten = "", "lop", [n.name]
        elif isinstance(n, ast.Assign):
            duong, loai = "", "gan"
            ten = [x.id for t in n.targets for x in ast.walk(t) if isinstance(x, ast.Name) and (isinstance(x.ctx, ast.Store) or isinstance(t, ast.Attribute))]
        else:
            continue
        bat_dau = min([n.lineno] + [d.lineno for d in getattr(n, "decorator_list", [])])
        b = bat_dau - 1                                  # keo chu thich dinh lien tren
        while b > reg.lineno and dong[b - 1].lstrip().startswith("#"):
            b -= 1
        d0 = b + 1 if b < bat_dau - 1 else bat_dau
        units.append({"ten": ten, "node": n, "loai": loai, "duong": duong, "d0": d0, "d1": n.end_lineno})
    ten_dn = {t: u for u in units for t in u["ten"]}
    # ---- khoi phai o trong register_chung(app) (dung bien app)
    khoi_app = set(spec.get("khoi_tao_app", []))
    # ---- phu thuoc
    def dung(u):
        return {x.id for x in ast.walk(u["node"]) if isinstance(x, ast.Name)} & set(ten_dn) - set(u["ten"])
    dep = {id(u): {id(ten_dn[t]) for t in dung(u)} for u in units}
    theo_id = {id(u): u for u in units}
    # ---- gan route vao cum
    cum_cua = {}
    for u in units:
        if u["loai"] == "route":
            for ten_cum, tien_to in spec["cum"].items():
                if any((u["duong"] == p[1:]) if p.startswith("=") else (u["duong"] == p or u["duong"].startswith(p.rstrip("/") + "/")) for p in tien_to):
                    cum_cua[id(u)] = ten_cum
                    break
            else:
                print("ROUTE KHONG THUOC CUM NAO:", u["duong"], u["ten"])
                return 1
    # ---- nguoi dung gian tiep cua moi khoi khong phai route
    nguoi_dung = collections.defaultdict(set)
    def lan(u_id, cum, thay):
        for d in dep[u_id]:
            if cum not in nguoi_dung[d]:
                nguoi_dung[d].add(cum)
                lan(d, cum, thay)
    for u in units:
        if id(u) in cum_cua:
            lan(id(u), cum_cua[id(u)], None)
    chung = spec["chung"]
    for u in units:
        if id(u) in cum_cua:
            continue
        us = nguoi_dung.get(id(u), set())
        cum_cua[id(u)] = list(us)[0] if len(us) == 1 else chung
    for t, c in spec.get("ep", {}).items():
        cum_cua[id(ten_dn[t])] = c
    # ---- kiem tra: khoi o cum X khong duoc phu thuoc khoi o cum Y (Y != chung, Y != X)
    xau = []
    for u in units:
        c = cum_cua[id(u)]
        for d in dep[id(u)]:
            c2 = cum_cua[d]
            if c2 not in (c, chung):
                xau.append((u["ten"][0], c, theo_id[d]["ten"][0], c2))
            if c == chung and c2 != chung:
                xau.append((u["ten"][0], c, theo_id[d]["ten"][0], c2))
    # ---- bao cao
    dem = collections.Counter(cum_cua.values())
    print("cum:", dict(dem))
    print("chung (ham/hang dung boi >=2 cum):", sorted(t for u in units if cum_cua[id(u)] == chung and u["loai"] != "route" for t in u["ten"]))
    dung_app = [t for u in units if u["loai"] in ("ham", "gan", "lop") and "app" in {x.id for x in ast.walk(u["node"]) if isinstance(x, ast.Name)} and not (set(u["ten"]) & khoi_app) for t in u["ten"]]
    if dung_app:
        print("CANH BAO - ham/hang cap module dung ten `app`:", dung_app)
    if xau:
        print("PHU THUOC XAU:", xau[:10])
        return 1
    if thu or dung_app:
        return 0 if thu else 1
    # ---- sinh module
    goi = spec["goi"]
    thu_muc = os.path.join(GOC, "src", *goi.split("."))
    # import dau than ham + import dau tep nguon (copy het, ruff go thua)
    imp_nguon = []
    for n in cay.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)) and "import sys as _sys" not in dong[n.lineno - 1]:
            imp_nguon.append("\n".join(dong[n.lineno - 1:n.end_lineno]))
    header = "\n".join(imp_nguon + imports)
    chung_mod = spec["chung"]
    # chung: module-level dinh nghia cua tung cum
    out = {}
    for ten_cum in list(spec["cum"]) + [chung_mod]:
        out[ten_cum] = {"muc": [], "route": [], "ten": []}
    for u in units:
        c = cum_cua[id(u)]
        if u["ten"][0] in khoi_app:
            out[chung_mod]["app"] = out[chung_mod].get("app", []) + [u]
        elif u["loai"] == "route":
            out[c]["route"].append(u)
        else:
            out[c]["muc"].append(u)
            out[c]["ten"] += u["ten"]
    for ten_cum, o in out.items():
        phan_muc = ["\n".join(dedent(dong, u["d0"], u["d1"], trong_chuoi)) for u in o["muc"]]
        nhap = []
        for c2, o2 in out.items():
            if c2 == ten_cum:
                continue
            can = sorted({t for u in o["muc"] + o["route"] for t in dung(u) if t in o2["ten"] and cum_cua[id(ten_dn[t])] == c2})
            if can:
                nhap.append("from %s.%s import (%s)  # noqa: F401" % (goi, c2, ", ".join(can)))
        fn_dk = spec["ham_dang_ky"][ten_cum] if ten_cum != chung_mod else "register_chung"
        phan_route = []
        if o["route"] or o.get("app"):
            than = []
            for u in o.get("app", []):
                than.append("\n".join(dong[u["d0"] - 1:u["d1"]]))
            for u in o["route"]:
                than.append("\n".join(dong[u["d0"] - 1:u["d1"]]))
            phan_route.append("def %s(app):\n%s\n" % (fn_dk, "\n\n".join(than)))
        mo_ta = spec["doc"].get(ten_cum, "Tach tu %s (B4)." % os.path.basename(spec["nguon"]))
        nd = ('# Console System - (c) 2026 zTieuYeuz. All rights reserved.\n"""%s\n\n(B4: tach nguyen van tu %s::%s; ten ham/route giu nguyen.)"""\n'
              % (mo_ta, os.path.basename(spec["nguon"]), spec["ham"]) + header + "\n" + "\n".join(nhap) + "\n\n\n" + "\n\n\n".join(phan_muc)
              + ("\n\n\n" if phan_muc and phan_route else "") + "\n".join(phan_route))
        open(os.path.join(thu_muc, ten_cum + ".py"), "w", encoding="utf-8").write(nd.rstrip("\n") + "\n")
    # ---- nguon: thay than register
    dang_ky = [("register_chung", chung_mod)] + [(spec["ham_dang_ky"][c], c) for c in spec["cum"] if out[c]["route"]]
    imp_dk = "\n".join("from %s.%s import %s" % (goi, m, f) for f, m in dang_ky)
    than_moi = ['def %s(app):' % spec["ham"]]
    doc = reg.body[0] if isinstance(reg.body[0], ast.Expr) and isinstance(getattr(reg.body[0], "value", None), ast.Constant) else None
    if doc:
        than_moi += dong[doc.lineno - 1:doc.end_lineno]
    for f, m in dang_ky:
        than_moi.append("    %s(app)" % f)
    moi = dong[:reg.lineno - 1] + imp_dk.split("\n") + ["", ""] + than_moi + dong[reg.end_lineno:]
    open(nguon, "w", encoding="utf-8").write("\n".join(moi))
    cac = [os.path.join(thu_muc, c + ".py") for c in out]
    subprocess.run(["/opt/devtools/bin/ruff", "check", "--select", "F401", "--fix", "-q"] + cac, cwd=GOC)
    print("xong: %s" % ", ".join(c for c in out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
