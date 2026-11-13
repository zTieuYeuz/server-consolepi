"""2.0.8: sao luu cau hinh (baotri) -> xoa -> khoi phuc DAY DU o CA HAI bo cuc (cu: moi thu duoi data/; moi: config/, secrets/, deploy/ tach rieng);
ban sao luu CU (ten trong goi nhu 2.0.7) van nap duoc; dinh dang goi khong doi."""
import io
import json
import os
import sys
import tarfile

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))


def _bo_cuc(B, monkeypatch, tmp_path, moi):
    DD = B._DD
    g = tmp_path / "goc"
    d = g / "data" if moi else g
    d.mkdir(parents=True)
    vt = (lambda cu, m: str(g / m)) if moi else (lambda cu, m: cu)
    monkeypatch.setattr(B, "THU_MUC_DU_LIEU", str(d))
    monkeypatch.setattr(B, "_GOC", str(g))
    monkeypatch.setattr(DD, "FILE_THU_VIEN_LENH", vt(str(d / "command-library.json"), "config/command-library.json"))
    monkeypatch.setattr(DD, "FILE_KHO_TRUNGTAM", vt(str(d / "kho-trungtam.json"), "secrets/kho-trungtam.json"))
    monkeypatch.setattr(DD, "KICHBAN_DIR", str(g / "deploy" / "kichban"))
    monkeypatch.setattr(DD, "APPS_DIR", str(g / "deploy" / "apps"))
    return g, d


def _ghi(p, nd):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(nd)


def _vi_tri(B):
    DD = B._DD
    return {"thu_vien": DD.FILE_THU_VIEN_LENH, "kho": DD.FILE_KHO_TRUNGTAM, "tt": os.path.join(B.THU_MUC_DU_LIEU, "tien-trinh.json"),
            "kb": os.path.join(DD.KICHBAN_DIR, "ky-ten-1", "kb.json"), "app": os.path.join(DD.APPS_DIR, "_thongtin.json")}


@pytest.mark.parametrize("moi", [False, True])
def test_vong_tron_day_du(monkeypatch, tmp_path, moi):
    from consolesystem.features.files import baotri as B
    g, d = _bo_cuc(B, monkeypatch, tmp_path, moi)
    vt = _vi_tri(B)
    nd = {k: json.dumps({"k": k}) for k in vt}
    for k, p in vt.items():
        _ghi(p, nd[k])
    du, ten = B.tao_ban_sao_luu()
    ten_trong_goi = {m.name for m in tarfile.open(fileobj=io.BytesIO(du), mode="r:gz").getmembers()}
    assert {"command-library.json", "kho-trungtam.json", "tien-trinh.json", "deploy/kichban", "deploy/apps/_thongtin.json"} <= ten_trong_goi    # dinh dang khong doi
    for p in vt.values():
        os.remove(p)
    ok, tb = B.nap_ban_sao_luu(du)
    assert ok, tb
    for k, p in vt.items():
        assert open(p).read() == nd[k], (moi, k)                                  # kich ban, ung dung, cau hinh, token kho deu ve du
    if moi:
        assert oct(os.stat(vt["kho"]).st_mode & 0o777) == "0o600"


@pytest.mark.parametrize("moi", [False, True])
def test_ban_sao_luu_cu_2_0_7_van_nap_duoc(monkeypatch, tmp_path, moi):
    """Ban sao luu cu = tar voi ten trong goi nhu code 2.0.7 (cung cac arcname) -> nap vao dung cho o ca hai bo cuc."""
    from consolesystem.features.files import baotri as B
    g, d = _bo_cuc(B, monkeypatch, tmp_path, moi)
    bo = io.BytesIO()
    with tarfile.open(fileobj=bo, mode="w:gz") as tf:
        for ten, nd in (("command-library.json", "{}"), ("kho-trungtam.json", '{"t": 1}'), ("deploy/kichban/a/kb.json", '{"a": 1}'),
                        ("deploy/apps/_thongtin.json", "{}"), ("_console-pi-sao-luu.json", '{"phien_ban": "1"}')):
            b = nd.encode()
            ti = tarfile.TarInfo(ten)
            ti.size = len(b)
            tf.addfile(ti, io.BytesIO(b))
    ok, tb = B.nap_ban_sao_luu(bo.getvalue())
    assert ok, tb
    vt = _vi_tri(B)
    assert open(vt["kho"]).read() == '{"t": 1}' and open(os.path.join(B._DD.KICHBAN_DIR, "a", "kb.json")).read() == '{"a": 1}'
    assert os.path.exists(vt["app"]) and os.path.exists(vt["thu_vien"])


def test_van_chan_zip_slip_va_muc_la(monkeypatch, tmp_path):
    from consolesystem.features.files import baotri as B
    g, d = _bo_cuc(B, monkeypatch, tmp_path, True)
    bo = io.BytesIO()
    with tarfile.open(fileobj=bo, mode="w:gz") as tf:
        for ten in ("deploy/kichban/../../../evil.txt", "/etc/evil", "deploy/os/windows.wim", "etc/passwd", "command-library.json"):
            b = b"x"
            ti = tarfile.TarInfo(ten)
            ti.size = 1
            tf.addfile(ti, io.BytesIO(b))
    ok, tb = B.nap_ban_sao_luu(bo.getvalue())
    assert ok and "Bỏ qua 4" in tb
    assert not (tmp_path / "evil.txt").exists() and not (g / "deploy" / "os").exists()


def test_B6_muc_tep_co_phan_con_khong_gay_500(monkeypatch, tmp_path):
    from consolesystem.features.files import baotri as B
    g, d = _bo_cuc(B, monkeypatch, tmp_path, True)
    bo = io.BytesIO()
    with tarfile.open(fileobj=bo, mode="w:gz") as tf:
        for ten in ("kho-trungtam.json/x", "command-library.json/y/z", "command-library.json"):
            ti = tarfile.TarInfo(ten)
            ti.size = 1
            tf.addfile(ti, io.BytesIO(b"x"))
    ok, tb = B.nap_ban_sao_luu(bo.getvalue())                                           # truoc day: NotADirectoryError/500
    assert ok and "Bỏ qua 2" in tb and os.path.exists(B._DD.FILE_THU_VIEN_LENH)
    # loi ghi giua chung (xung dot tep/thu muc) cung khong lam hong ca lan nap
    os.makedirs(os.path.join(B._DD.KICHBAN_DIR, "a", "kb.json"))
    bo2 = io.BytesIO()
    with tarfile.open(fileobj=bo2, mode="w:gz") as tf:
        for ten in ("deploy/kichban/a/kb.json", "deploy/kichban/b/kb.json"):
            ti = tarfile.TarInfo(ten)
            ti.size = 1
            tf.addfile(ti, io.BytesIO(b"x"))
    ok, tb = B.nap_ban_sao_luu(bo2.getvalue())
    assert ok and os.path.exists(os.path.join(B._DD.KICHBAN_DIR, "b", "kb.json"))
