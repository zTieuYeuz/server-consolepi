"""B1b: KhoSqlite phai cho KET QUA GIONG HET KhoJson, nhung chi ghi phan doi. Thu muc tam."""
import copy
import json
import os
import random
import sqlite3
import sys
import time

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))
from consolesystem.core import sqlite as SQ  # noqa: E402
from consolesystem.core import store as S  # noqa: E402
from consolesystem.core.store_sqlite import KhoSqlite  # noqa: E402


@pytest.fixture
def db(tmp_path):
    SQ.lam_moi()
    return str(tmp_path / "console.db")


def so_dong_doi(db_path, bang, fn):
    """Chay fn() roi dem so dong trong `bang` bi doi (them/sua/xoa) bang total_changes."""
    c = SQ.ket_noi(db_path)
    truoc = c.total_changes
    fn()
    return c.total_changes - truoc


def tao_may(i):
    return {"id": "m%03d" % i, "ten": "May %d" % i, "bao_cao": {"pm": ["x"] * 20}, "ip": "10.0.0.%d" % (i % 250)}


def test_giong_het_khojson_tren_chuoi_thao_tac_ngau_nhien(tmp_path, db):
    rng = random.Random(42)
    a = S.KhoJson(str(tmp_path / "a.json"), [])
    b = KhoSqlite(db, "may", [])
    for buoc in range(120):
        k, r, n1, n2 = rng.choice(["them", "sua", "xoa", "doi_thu_tu", "chen"]), rng.random(), rng.randint(0, 40), rng.randint(0, 10 ** 6)

        def thao_tac(ds, k=k, r=r, n1=n1, n2=n2, buoc=buoc):          # tham so ngau nhien chot TRUOC de hai kho nhan cung thao tac
            if k == "them" or not ds:
                ds.append(tao_may(n1) | {"id": "n%d" % n2})
            elif k == "sua":
                ds[int(r * len(ds))]["ten"] = "doi-%d" % buoc
            elif k == "xoa":
                del ds[int(r * len(ds))]
            elif k == "doi_thu_tu":
                ds.reverse()
            else:
                ds.insert(int(r * len(ds)), {"id": "c%d" % buoc, "ten": "chen"})
        a.sua(thao_tac)
        b.sua(thao_tac)
        assert a.doc() == b.doc(), "lech o buoc %d" % buoc


def test_dict_giu_thu_tu_va_giong_json(tmp_path, db):
    a = S.KhoJson(str(tmp_path / "a.json"), {})
    b = KhoSqlite(db, "tt", {})
    for f in (lambda d: d.update({"z": 1, "a": {"x": [1, 2]}, "m": "tv"}), lambda d: d.pop("a"), lambda d: d.update({"a": 5}),
              lambda d: d["z"] and d.update({"z": 2})):
        a.sua(f)
        b.sua(f)
        assert a.doc() == b.doc() and list(a.doc()) == list(b.doc())


def test_lich_su_khong_co_id_them_cuoi_chi_ghi_dong_moi(tmp_path, db):
    k = KhoSqlite(db, "lichsu", [])
    k.ghi([{"luc": i, "ok": True} for i in range(500)])
    n = so_dong_doi(db, "k_lichsu", lambda: k.sua(lambda d: d.append({"luc": 999, "ok": False})))
    assert n == 1 and len(k.doc()) == 501
    n = so_dong_doi(db, "k_lichsu", lambda: k.sua(lambda d: d.__delitem__(slice(0, 0))))        # khong doi gi
    assert n == 0


def test_sua_mot_may_trong_300_chi_ghi_mot_dong(db):
    k = KhoSqlite(db, "may", [])
    k.ghi([tao_may(i) for i in range(300)])
    n = so_dong_doi(db, "k_may", lambda: k.sua(lambda d: d[150].update(ten="DA SUA")))
    assert n == 1 and k.doc()[150]["ten"] == "DA SUA"
    n = so_dong_doi(db, "k_may", lambda: k.sua(lambda d: d.append(tao_may(999))))
    assert n == 1
    n = so_dong_doi(db, "k_may", lambda: k.sua(lambda d: d.pop(10)))
    assert n == 1                                                              # xoa 1 may = xoa 1 dong, khong danh so lai ca bang


def test_nhap_json_cu_tu_dong_roi_giu_ban_goc(tmp_path, db):
    cu = tmp_path / "may.json"
    du_lieu = [tao_may(i) for i in range(5)]
    cu.write_text(json.dumps(du_lieu, ensure_ascii=False, indent=1))
    k = KhoSqlite(db, "may", [], duong_json_cu=str(cu))
    assert k.doc() == du_lieu
    assert not cu.exists() and [x for x in os.listdir(tmp_path) if x.startswith("may.json.da-chuyen-")]      # giu lai, khong xoa
    k2 = KhoSqlite(db, "may", [], duong_json_cu=str(cu))                      # lan sau khong nhap lai
    assert k2.doc() == du_lieu


def test_nhap_json_hong_giu_lai_va_dung_trong(tmp_path, db):
    cu = tmp_path / "may.json"
    cu.write_text("{hong")
    k = KhoSqlite(db, "may", [], duong_json_cu=str(cu))
    assert k.doc() == [] and [x for x in os.listdir(tmp_path) if ".hong-" in x]


def test_xuat_json_de_hoan_tac(tmp_path, db):
    k = KhoSqlite(db, "may", [])
    k.ghi([tao_may(1), tao_may(2)])
    k.xuat_json(str(tmp_path / "ra.json"))
    assert json.load(open(tmp_path / "ra.json")) == k.doc()


def test_sai_kieu_va_gia_tri_khong_json_khong_lam_hong_du_lieu(db):
    k = KhoSqlite(db, "may", [])
    k.ghi([tao_may(1)])
    with pytest.raises(S.LoiDuLieu):
        k.ghi({"a": 1})
    with pytest.raises((TypeError, ValueError)):
        k.sua(lambda d: d.append({"id": "x", "o": object()}))
    assert k.doc() == [tao_may(1)]


def test_loi_giua_sua_rollback(db):
    k = KhoSqlite(db, "may", [])
    k.ghi([tao_may(1)])

    def hong(d):
        d.append(tao_may(2))
        raise RuntimeError("giua chung")
    with pytest.raises(RuntimeError):
        k.sua(hong)
    assert k.doc() == [tao_may(1)]


def test_co_so_du_lieu_hong_duoc_cach_ly_va_canh_bao(tmp_path, db):
    SQ.lam_moi()
    open(db, "wb").write(b"khong phai sqlite" * 100)
    truoc = len(S.canh_bao())
    k = KhoSqlite(db, "may", [])
    assert k.doc() == [] and len(S.canh_bao()) == truoc + 1
    assert [x for x in os.listdir(tmp_path) if ".hong-" in x]
    k.ghi([tao_may(1)])
    assert k.doc() == [tao_may(1)]


def test_snapshot_nhat_quan_va_doc_duoc(tmp_path, db):
    k = KhoSqlite(db, "may", [])
    k.ghi([tao_may(i) for i in range(50)])
    SQ.snapshot(db, str(tmp_path / "ban-sao.db"))
    c = sqlite3.connect(str(tmp_path / "ban-sao.db"))
    assert c.execute("SELECT count(*) FROM k_may").fetchone()[0] == 50 and c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_lam_moi_buoc_mo_lai_ket_noi(tmp_path, db):
    k = KhoSqlite(db, "may", [])
    k.ghi([tao_may(1)])
    os.replace(db, str(tmp_path / "cu.db"))
    for h in ("-wal", "-shm"):
        if os.path.exists(db + h):
            os.replace(db + h, str(tmp_path / ("cu.db" + h)))
    SQ.lam_moi()                                              # nhu sau khoi phuc: doi file co so du lieu
    assert k.doc() == []


def test_500_may_hieu_nang(db):
    k = KhoSqlite(db, "may", [])
    k.ghi([tao_may(i) | {"bao_cao": {"pm": ["phan mem"] * 80}} for i in range(500)])
    t = time.time()
    for i in range(20):
        k.sua(lambda d, i=i: d[i].update(ghi_chu=str(i)))
    moi_lan = (time.time() - t) / 20
    assert moi_lan < 0.25, "moi lan sua %.3fs" % moi_lan


# ---------------------------------------------------------- tich hop voi sao luu (A5) va chuyen bo cuc (A3)
def _may_cs(tmp_path):
    from ui import dichuyen as DM
    goc = str(tmp_path / "cs")
    DM.tao_bo_cuc_moi(goc)
    return goc


def test_sao_luu_dung_ban_chup_db_khong_kem_wal_va_khoi_phuc_mo_lai_ket_noi(tmp_path):
    from ui import saoluu as SL
    goc = _may_cs(tmp_path)
    db_path = os.path.join(goc, "data", "console.db")
    SQ.lam_moi()
    k = KhoSqlite(db_path, "may", [])
    k.ghi([tao_may(i) for i in range(30)])                       # WAL con du lieu chua gop
    ra = str(tmp_path / "g.tar.gz")
    mf = SL.tao_goi(goc, "cauhinh", ra)
    ten = [t["duong"] for t in mf["tep"]]
    assert "data/console.db" in ten and not [x for x in ten if x.endswith(("-wal", "-shm"))]
    assert not [x for x in os.listdir(goc) if x.startswith(".sao-luu-db-")]                  # don tam
    SL.kiem_goi(ra)
    k.sua(lambda d: d.clear())                                   # pha hong sau khi sao luu
    assert k.doc() == []
    SL.khoi_phuc(ra, goc)
    assert len(k.doc()) == 30 and k.doc()[7]["id"] == "m007"       # cung doi tuong kho van doc duoc ban khoi phuc


def test_sao_luu_trong_luc_dang_ghi_van_nhat_quan(tmp_path):
    import threading
    from ui import saoluu as SL
    goc = _may_cs(tmp_path)
    SQ.lam_moi()
    k = KhoSqlite(os.path.join(goc, "data", "console.db"), "ls", [])
    dung = threading.Event()

    def ghi():
        i = 0
        while not dung.is_set():
            k.sua(lambda d, i=i: d.append({"luc": i}))
            i += 1
    t = threading.Thread(target=ghi)
    t.start()
    try:
        ra = str(tmp_path / "g.tar.gz")
        for _ in range(3):
            SL.tao_goi(goc, "cauhinh", ra)
            SL.kiem_goi(ra)
    finally:
        dung.set()
        t.join()
    import tarfile
    with tarfile.open(ra) as tf:
        tf.extract("data/console.db", str(tmp_path / "ra"))
    c = sqlite3.connect(str(tmp_path / "ra/data/console.db"))
    assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    n = c.execute("SELECT count(*) FROM k_ls").fetchone()[0]
    assert [r[0] for r in c.execute("SELECT json_extract(j,'$.luc') FROM k_ls ORDER BY pos")] == list(range(n))     # lien tuc, khong rach


def test_chuyen_bo_cuc_tu_choi_khi_wal_chua_gop(tmp_path):
    from ui import dichuyen as DM
    cu = tmp_path / "cu"
    cu.mkdir()
    (cu / "console.db-wal").write_bytes(b"x" * 100)
    with pytest.raises(DM.LoiDichuyen, match="WAL"):
        DM.dua_ve_bo_cuc_moi(str(cu), str(tmp_path / "opt"), str(tmp_path / "moi"))
    assert not (tmp_path / "moi").exists()
