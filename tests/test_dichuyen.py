"""Khung migration (A2): thu tren thu muc du lieu gia, khong dung du lieu that."""
import hashlib
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ui"))
import dichuyen as M  # noqa: E402


def bam(root):
    """{duong tuong doi: sha1} cua PHAN NHO (bo qua thu muc nang, backups, nhat ky, khoa, schema)."""
    ra = {}
    for d, ds, fs in os.walk(root):
        rel = os.path.relpath(d, root)
        ds[:] = [x for x in ds if not (rel == "." and x in M.THU_MUC_NANG)]
        for f in fs:
            if f in (".migrate.lock", M.TEN_NHAT_KY, M.TEN_FILE_PHIEN_BAN):
                continue
            p = os.path.join(d, f)
            ra[os.path.relpath(p, root)] = hashlib.sha1(open(p, "rb").read()).hexdigest()
    return ra


@pytest.fixture
def root(tmp_path):
    r = tmp_path / "du-lieu"
    (r / "data").mkdir(parents=True)
    (r / "data" / "may.json").write_text(json.dumps({"ds": [1, 2, 3]}, ensure_ascii=False, indent=2, sort_keys=True))
    (r / "secrets").mkdir()
    (r / "secrets" / "khoa").write_text("bi-mat")
    (r / "deploy").mkdir()
    (r / "deploy" / "anh.wim").write_text("NANG" * 10)
    return str(r)


def them_cot(ngu):
    d = ngu.doc_json("data", "may.json")
    d["cot"] = "moi"
    ngu.ghi_json("data", "may.json", data=d)


def bo_cot(ngu):
    d = ngu.doc_json("data", "may.json")
    d.pop("cot", None)
    ngu.ghi_json("data", "may.json", data=d)


def doi_ten(ngu):
    os.rename(ngu.duong("secrets", "khoa"), ngu.duong("secrets", "khoa.moi"))


def hoan_doi_ten(ngu):
    os.rename(ngu.duong("secrets", "khoa.moi"), ngu.duong("secrets", "khoa"))


def hong(ngu):
    raise RuntimeError("hong gia")


DS = [(1, "them-cot", them_cot, bo_cot), (2, "doi-ten", doi_ten, hoan_doi_ten)]


def test_chay_den_moi_nhat_va_ghi_phien_ban(root):
    assert M.chay(root, DS) == 2
    assert M.doc_phien_ban(root) == 2
    assert json.load(open(os.path.join(root, "data", "may.json")))["cot"] == "moi"
    assert os.path.exists(os.path.join(root, "secrets", "khoa.moi"))
    assert os.listdir(os.path.join(root, "backups"))           # co ban sao luu truoc khi chay
    assert open(os.path.join(root, "deploy", "anh.wim")).read() == "NANG" * 10


def test_chay_lai_khong_lam_gi(root):
    M.chay(root, DS)
    truoc = bam(root)
    n_bak = len(os.listdir(os.path.join(root, "backups")))
    assert M.chay(root, DS) == 2
    assert bam(root) == truoc and len(os.listdir(os.path.join(root, "backups"))) == n_bak


def test_loi_giua_chung_tra_du_lieu_ve_nhu_cu(root, monkeypatch):
    # buoc 1 thanh cong, buoc 2 hong CHI KHI chay that (chay thu tren ban sao cho qua) -> phai khoi phuc ca buoc 1
    that = []

    def hong_khi_that(ngu):
        if ngu.root == root:
            that.append(1)
            raise RuntimeError("mat dien gia")
        doi_ten(ngu)

    truoc = bam(root)
    with pytest.raises(M.LoiDichuyen):
        M.chay(root, [DS[0], (2, "hong-that", hong_khi_that, None)])
    assert that and bam(root) == truoc
    assert M.doc_phien_ban(root) == 0


def test_chay_thu_loi_thi_du_lieu_that_chua_dung_toi(root):
    truoc = bam(root)
    with pytest.raises(M.LoiDichuyen, match="chay thu"):
        M.chay(root, [DS[0], (2, "hong", hong, None)])
    assert bam(root) == truoc and M.doc_phien_ban(root) == 0


def test_hoan_tac_lui_mot_buoc_va_ve_0(root):
    truoc = bam(root)
    M.chay(root, DS)
    assert M.hoan_tac(root, DS) == 1
    assert os.path.exists(os.path.join(root, "secrets", "khoa"))
    assert M.hoan_tac(root, DS, ve=0) == 0
    assert bam(root) == truoc


def test_hoan_tac_tu_choi_neu_khong_co_down(root):
    M.chay(root, [(1, "mot-chieu", them_cot, None)])
    truoc = bam(root)
    with pytest.raises(M.LoiDichuyen):
        M.hoan_tac(root, [(1, "mot-chieu", them_cot, None)])
    assert bam(root) == truoc and M.doc_phien_ban(root) == 1


def test_khong_tu_ha_cap_khi_du_lieu_moi_hon_ma(root):
    M.chay(root, DS)
    with pytest.raises(M.LoiDichuyen, match="moi hon"):
        M.chay(root, DS[:1])


def test_phien_ban_phai_lien_tuc(root):
    with pytest.raises(M.LoiDichuyen):
        M.chay(root, [(1, "a", them_cot, None), (3, "c", them_cot, None)])


def test_schema_version_hong_thi_tu_choi(root):
    open(os.path.join(root, M.TEN_FILE_PHIEN_BAN), "w").write("{hong")
    with pytest.raises(M.LoiDichuyen, match="hong"):
        M.chay(root, DS)


def test_khoa_chay_dong_thoi(root):
    import fcntl
    fd = os.open(os.path.join(root, ".migrate.lock"), os.O_RDWR | os.O_CREAT)
    fcntl.flock(fd, fcntl.LOCK_EX)
    try:
        with pytest.raises(M.LoiDichuyen, match="khac chay"):
            M.chay(root, DS)
    finally:
        os.close(fd)


def test_nhat_ky_ghi_tung_dong_json(root):
    M.chay(root, DS)
    dong = [json.loads(x) for x in open(os.path.join(root, M.TEN_NHAT_KY))]
    assert dong[-1]["ket_qua"] == "xong" and dong[-1]["phien_ban"] == 2


def test_danh_sach_that_cua_san_pham_hop_le(root):
    assert M.chay(root, M.MIGRATIONS) == len(M.MIGRATIONS)
