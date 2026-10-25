"""B3: luat kien truc cho consolesystem (do bang tools/do-do-thi-import.py, tinh ca import trong ham).

  R1  core/ va integrations/ KHONG import web, features, nettools hay ui; core/ khong import flask
  R2  khong co vong import luc nap (top-level), tru mau blueprint cua nettools
  R3  web/ chi import core/ (+ web/); features/ chi import core, integrations, web va CHINH NO;
      nettools chi import core, web. Ngoai le co ten:
        - 'goc lap rap' (composition root): features.settings va web.home gom nhieu tinh nang len MOT trang -> duoc import tinh nang khac
        - NO KY THUAT da biet (ben duoi): chi duoc GIAM, khong duoc them; muc nao het ton tai phai go khoi danh sach
"""
import importlib.util
import os

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
spec = importlib.util.spec_from_file_location("dothi", os.path.join(GOC, "tools", "do-do-thi-import.py"))
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)

GOC_LAP_RAP = {"consolesystem.features.settings.settings", "consolesystem.web.home", "consolesystem.features.updates.thuc_te"}   # thuc_te noi bo nang cap voi sao luu/kho/he thong
NO_KY_THUAT = {                     # (tu, den): ly do / buoc go
    ("consolesystem.features.software_deploy.tk_trang", "consolesystem.features.deploy_os.deployos"): "B4: danh muc phan mem/ung dung (app catalog) con nam trong deployos",
    ("consolesystem.integrations.tk_dongco", "consolesystem.features.deploy_os.deployos"): "B4: nhu tren (doc_thongtin_app, lay_ungdung, tham_so_mac_dinh_app)",
    ("consolesystem.integrations.tk_dongco", "consolesystem.features.uem.uem_agent_goi"): "B4: kho goi MSI agent (passkey_trien_khai, tim_theo_file)",
}


def _goi(m):
    p = m.split(".")
    if p[0] == "nettools":
        return "nettools"
    if len(p) == 1:
        return "goc"                  # chinh goi `consolesystem` (khong phai tinh nang)
    if p[1] == "features" and len(p) > 2:
        return "features." + p[2]
    return p[1]


def _vi_pham(top, lazy):
    ra = set()
    for g in (top, lazy):
        for m, ts in g.items():
            if m in GOC_LAP_RAP:
                continue
            a = _goi(m)
            for t in ts:
                b = _goi(t)
                if a == b or "goc" in (a, b):
                    continue
                ok = (b in ("core", "integrations")
                      or (a.startswith("features") and b == "web")
                      or (a in ("nettools", "integrations") and b in ("core", "web"))
                      or (a == "web" and b == "core"))
                if a in ("core", "integrations") and b not in ("core", "integrations"):
                    ok = False if a == "core" else ok
                if not ok:
                    ra.add((m, t))
    return ra


def test_core_khong_phu_thuoc_ngoai_va_khong_flask():
    modules, top, lazy = D.phan_tich()
    sai = [(m, t) for g in (top, lazy) for m, ts in g.items() if _goi(m) == "core" for t in ts if _goi(t) not in ("core", "goc")]
    assert not sai, sai
    import ast
    for m, p in modules.items():
        if _goi(m) == "core":
            for n in ast.walk(ast.parse(open(p, encoding="utf-8").read())):
                ten = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module or ""] if isinstance(n, ast.ImportFrom) and n.level == 0 else []
                assert not [x for x in ten if x == "flask" or x.startswith(("flask.", "ui", "ui."))], (m, ten)


def test_khong_vong_import_luc_nap_ngoai_mau_blueprint_nettools():
    modules, top, lazy = D.phan_tich()
    vong = D.scc(top)
    assert len(vong) <= 1 and all(x.startswith("nettools") for g in vong for x in g), vong


def test_phu_thuoc_giua_cac_goi_dung_luat_va_no_ky_thuat_chi_giam():
    modules, top, lazy = D.phan_tich()
    vp = _vi_pham(top, lazy)
    moi = sorted(vp - set(NO_KY_THUAT))
    assert not moi, "phu thuoc moi vi pham luat kien truc (tach dich vu dung chung ra core/integrations): %s" % moi
    het = sorted(set(NO_KY_THUAT) - vp)
    assert not het, "no ky thuat da duoc go - xoa khoi NO_KY_THUAT: %s" % het
