"""2.0.8 V6-2: moi noi ghi JSON trang thai di qua core/store.ghi_json (tam + fsync + doi ten); khong con json.dump ra tep ngoai danh sach duoc duyet."""
import json
import os
import re
import stat
import sys

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(GOC, "src")
sys.path.insert(0, SRC)

# Noi con duoc json.dump truc tiep, KEM LY DO (khong phai trang thai ben vung cua may):
DUOC_PHEP = {
    "app.py": "tien do khoi dong trong /run (bay hoi khi khoi dong lai)",
    "nettools/tftp_server.py": "cau hinh chuyen cho tftp-chay trong /run",
    "consolesystem/features/terminal/ssh.py": "tep yeu cau giao cho launcher phien SSH (user khac, /var/lib/console-ssh/yeu-cau)",
    "consolesystem/core/capnhat/khoa.py": "cong cu tao khoa ky (O_EXCL, khong ghi de khoa rieng)",
    "consolesystem/core/phathanh.py": "RELEASE.json ghi TRONG thu muc tam, ca thu muc doi ten nguyen khoi",
    "scripts/tftp-chay.py": "tien trinh doc lap, trang thai trong /run",
    "scripts/bt-auto-agent.py": "tien trinh doc lap, trang thai trong /run",
}


def test_khong_con_json_dump_ngoai_danh_sach_duoc_duyet():
    bad = []
    for d, _ds, fs in os.walk(SRC):
        for f in fs:
            if not f.endswith(".py"):
                continue
            p = os.path.join(d, f)
            rel = os.path.relpath(p, SRC)
            if rel == os.path.join("consolesystem", "core", "store.py"):
                continue
            if re.search(r"\bjson\.dump\(", open(p, encoding="utf-8").read()) and rel not in DUOC_PHEP:
                bad.append(rel)
    assert not bad, "json.dump truc tiep (dung core.store.ghi_json): %s" % bad


def test_ghi_json_nguyen_tu_dung_quyen_va_khong_hong_file_khi_loi_kieu(tmp_path):
    from consolesystem.core.store import ghi_json
    f = tmp_path / "a" / "x.json"
    ghi_json(str(f), {"k": "ă"}, mode=0o600, ensure_ascii=False, indent=1)
    assert json.load(open(f, encoding="utf-8")) == {"k": "ă"} and stat.S_IMODE(os.stat(f).st_mode) == 0o600
    assert "ă" in open(f, encoding="utf-8").read()                                   # dung ensure_ascii=False
    with pytest.raises(TypeError):
        ghi_json(str(f), {"k": object()})                                              # khong tuan tu hoa duoc
    assert json.load(open(f, encoding="utf-8")) == {"k": "ă"}                         # file cu con nguyen
    assert not os.path.exists(str(f) + ".tmp")


def _mo(mod):
    import importlib
    return importlib.import_module(mod)


def test_cac_noi_ghi_da_chuyen_van_ghi_dung(tmp_path, monkeypatch):
    cases = []
    R = _mo("consolesystem.core.rbac")
    monkeypatch.setattr(R, "FILE", str(tmp_path / "r" / "rbac.json"))
    R._ghi({"nguoi_dung": {"a": {"vai_tro": "van_hanh"}}})
    cases.append((R.FILE, 0o600))
    assert json.load(open(R.FILE)) == {"nguoi_dung": {"a": {"vai_tro": "van_hanh"}}}

    P = _mo("consolesystem.features.terminal.phien")
    monkeypatch.setattr(P, "FILE_PHIEN", str(tmp_path / "p" / "phien.json"))
    monkeypatch.setattr(P, "THU_MUC_DU_LIEU", str(tmp_path / "p"))
    P._ghi({"phien": [{"ma": "x"}]})
    cases.append((P.FILE_PHIEN, 0o600))
    assert json.load(open(P.FILE_PHIEN)) == {"phien": [{"ma": "x"}]}

    S = _mo("consolesystem.features.terminal.ssh_phien")
    monkeypatch.setattr(S, "FILE", str(tmp_path / "s" / "sp.json"))
    S._ghi({"phien": {}, "khoa": {}})
    cases.append((S.FILE, 0o600))

    W = _mo("consolesystem.features.deploy_os.wol")
    monkeypatch.setattr(W, "FILE_MAY", str(tmp_path / "w" / "may.json"))
    monkeypatch.setattr(W, "THU_MUC_DU_LIEU", str(tmp_path / "w"))
    W._ghi_may([{"mac": "aa"}])
    cases.append((W.FILE_MAY, 0o644))

    L = _mo("consolesystem.features.deploy_os.lichsu")
    monkeypatch.setattr(L, "FILE_LUU", str(tmp_path / "l" / "ls.json"))
    L._ghi([{"id": 1}])
    cases.append((L.FILE_LUU, 0o644))
    assert json.load(open(L.FILE_LUU)) == [{"id": 1}]

    PM = _mo("consolesystem.features.deploy_os.dos_phanmem")
    monkeypatch.setattr(PM, "APPS_META", str(tmp_path / "pm" / "_thongtin.json"))
    monkeypatch.setattr(PM, "_bao_dam_thu_muc", lambda: os.makedirs(tmp_path / "pm", exist_ok=True))
    assert PM.ghi_thongtin_app({"a.exe": "/S"})
    cases.append((PM.APPS_META, 0o644))

    for duong, mode in cases:
        assert stat.S_IMODE(os.stat(duong).st_mode) == mode, duong
        assert not os.path.exists(duong + ".tmp")
