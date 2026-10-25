#!/usr/bin/env python3
"""B2: chuyen module tu src/ui/ vao cau truc goi moi (consolesystem/...), THUAN TUY di chuyen:
  - git mv (giu lich su); viet lai import tuong doi (`from . import x` -> `from ui import x`) de khong phu thuoc vi tri
  - dong dau tien truoc import dau: dang ky ten cu `ui.<ten>` tro toi chinh module nay (chong vong import)
  - de lai CAU NOI o ui/<ten>.py: sys.modules[ten cu] = module moi (CUNG DOI TUONG: patch/state nhu cu)
Dung:  chuyen-b2.py NHOM [NHOM...]   (xem ANH_XA)   |   chuyen-b2.py --ds"""
import ast
import os
import re
import subprocess
import sys

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(GOC, "src")

ANH_XA = {
    "core": ("consolesystem/core", ["duongdan", "dichuyen", "phathanh"]),
    "core2": ("consolesystem/core", ["errlog", "phancung", "tk_dulieu"]),         # B3: dich vu dung chung keo ra khoi tinh nang
    "web": ("consolesystem/web", ["layout", "auth", "gioithieu", "docs", "ph_icons", "home", "health"]),
    "deploy_os": ("consolesystem/features/deploy_os", ["deployos", "unattend", "pxe", "pxemenu", "isotach", "goidriver", "doodia", "lichsu",
                                                        "tiendo", "datten", "tenmay", "khotrungtam", "winperieng", "wol", "sansang", "gopy", "fontinfo"]),
    "software_deploy": ("consolesystem/features/software_deploy", ["tk_dulieu", "tk_dongco", "tk_trang"]),
    "uem": ("consolesystem/features/uem", ["uem_agent", "uem_agent_cs", "uem_agent_goi", "uem_agent_trang", "uem_baocao", "uem_buoc", "uem_dulieu",
                                           "uem_ketnoi", "uem_pki", "uem_profiles", "uem_trang", "uem_trang_b", "uem_trienkhai", "uem_vnc", "uem_winget"]),
    "network": ("consolesystem/features/network", ["network", "phancung", "direct", "remote"]),
    "terminal": ("consolesystem/features/terminal", ["terminal", "ssh", "commands", "soanlenh", "phien"]),
    "power": ("consolesystem/features/power", ["power", "entertainment"]),
    "files": ("consolesystem/features/files", ["storage", "baotri"]),
    "logs": ("consolesystem/features/logs", ["logs", "errlog"]),
    "settings": ("consolesystem/features/settings", ["settings"]),
    "backup": ("consolesystem/features/backup", ["saoluu"]),
}

RE_TUONG_DOI_1 = re.compile(r"^(\s*)from \. import ", re.M)
RE_TUONG_DOI_2 = re.compile(r"^(\s*)from \.(\w+) import ", re.M)
CAU_NOI = '''# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Cau noi tuong thich (B2): `ui.{ten}` da chuyen sang `{moi}`. Hai ten tro toi CUNG MOT module (sys.modules), nen
patch/trang thai/`from ui import {ten}` van nhu truoc. Se go cau noi khi moi noi goi da dung ten moi."""
import importlib as _il
import sys as _sys

_sys.modules[__name__] = _il.import_module("{moi}")
'''


def sh(*a):
    subprocess.run(a, cwd=GOC, check=True)


def vi_tri_import_dau(nguon):
    for n in ast.parse(nguon).body:
        if isinstance(n, (ast.Import, ast.ImportFrom)) and not (isinstance(n, ast.ImportFrom) and n.module == "__future__"):
            return n.lineno
    return None


def chuyen(nhom, ten):
    thu_muc, _ = ANH_XA[nhom]
    cu = os.path.join(SRC, "ui", ten + ".py")
    moi_rel = "%s/%s.py" % (thu_muc, ten)
    moi = os.path.join(SRC, moi_rel)
    ten_moi = moi_rel[:-3].replace("/", ".")
    nguon = open(cu, encoding="utf-8").read()
    if "sys.modules[__name__] = _il.import_module" in nguon:
        return False                                   # da la cau noi
    os.makedirs(os.path.dirname(moi), exist_ok=True)
    for p in {os.path.dirname(moi), os.path.dirname(os.path.dirname(moi))}:
        if p.startswith(os.path.join(SRC, "consolesystem")) and not os.path.exists(os.path.join(p, "__init__.py")):
            open(os.path.join(p, "__init__.py"), "w").write("# Console System - (c) 2026 zTieuYeuz. All rights reserved.\n")
    sh("git", "mv", os.path.relpath(cu, GOC), os.path.relpath(moi, GOC))
    nguon = RE_TUONG_DOI_1.sub(r"\1from ui import ", nguon)
    nguon = RE_TUONG_DOI_2.sub(r"\1from ui.\2 import ", nguon)
    dong = nguon.split("\n")
    vt = vi_tri_import_dau(nguon)
    alias = ['import sys as _sys', '_sys.modules["ui.%s"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)' % ten]
    if vt is None:
        dong += alias
    else:
        dong[vt - 1:vt - 1] = alias
    open(moi, "w", encoding="utf-8").write("\n".join(dong))
    open(cu, "w", encoding="utf-8").write(CAU_NOI.format(ten=ten, moi=ten_moi))
    return True


def main(argv):
    if not argv or argv == ["--ds"]:
        for n, (d, ds) in ANH_XA.items():
            print("%-16s -> %-40s %d module" % (n, d, len(ds)))
        return 0
    for nhom in argv:
        for ten in ANH_XA[nhom][1]:
            print(("da chuyen " if chuyen(nhom, ten) else "bo qua   ") + ten)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
