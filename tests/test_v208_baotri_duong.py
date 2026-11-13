"""2.0.8 V6-4: trang 'Du lieu cua anh'/don rac tinh dung muc NANG (deploy/*, storage) o bo cuc moi (GOC/data + GOC/deploy); bo cuc cu khong doi."""
import os
import sys

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))


def _dat(B, monkeypatch, goc, data):
    monkeypatch.setattr(B, "_GOC", str(goc))
    monkeypatch.setattr(B, "THU_MUC_DU_LIEU", str(data))


def _viet(p, n):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(b"x" * n)


def test_bo_cuc_moi_thay_anh_os_va_part_o_deploy(monkeypatch, tmp_path):
    from consolesystem.features.files import baotri as B
    _dat(B, monkeypatch, tmp_path, tmp_path / "data")
    (tmp_path / "data").mkdir()
    _viet(str(tmp_path / "deploy/os/win10/install.wim"), 5000)
    _viet(str(tmp_path / "storage/a.bin"), 700)
    _viet(str(tmp_path / "deploy/os/win10/up.wim.part"), 3000)
    _viet(str(tmp_path / "data/x.part"), 100)
    _viet(str(tmp_path / "secrets/k.part"), 9)                                  # secrets KHONG duoc quet/xoa
    dia, muc = B.tinh_dung_luong()
    nhan = {m["nhan"]: m["byte"] for m in muc}
    assert any("hệ điều hành" in k and v >= 8000 for k, v in nhan.items()), nhan      # muc NANG NHAT khong con bi bo qua
    assert any("Kho file" in k and v == 700 for k, v in nhan.items())
    rac = {r[0]: r for r in B.tim_rac()}
    assert rac["part"][2] == 3100                                                  # 3000 (deploy) + 100 (data)
    ok, _tb = B.don_rac("part")
    assert ok and not (tmp_path / "deploy/os/win10/up.wim.part").exists() and not (tmp_path / "data/x.part").exists()
    assert (tmp_path / "deploy/os/win10/install.wim").exists() and (tmp_path / "secrets/k.part").exists()    # khong xoa nham


def test_bo_cuc_cu_khong_doi(monkeypatch, tmp_path):
    from consolesystem.features.files import baotri as B
    _dat(B, monkeypatch, tmp_path, tmp_path)                                      # cu: GOC == du lieu
    _viet(str(tmp_path / "deploy/os/a/install.wim"), 4000)
    _viet(str(tmp_path / "deploy/os/a/u.part"), 50)
    dia, muc = B.tinh_dung_luong()
    assert any(m["byte"] >= 4000 for m in muc)
    assert {r[0]: r for r in B.tim_rac()}["part"][2] == 50                         # khong dem trung do quet 2 lan
