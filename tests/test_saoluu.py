"""A5: sao luu / khoi phuc. Thu muc tam, khong dung may that."""
import hashlib
import io
import json
import os
import sys
import tarfile

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))
from ui import dichuyen as DM  # noqa: E402
from ui import saoluu as S  # noqa: E402


def bam_cay(p, bo_qua=("backups", ".migrate.lock", "migrate.log")):
    ra = {}
    for d, ds, fs in os.walk(p):
        rel = os.path.relpath(d, p)
        ds[:] = [x for x in ds if not (rel == "." and (x in bo_qua or x.startswith(".")))]
        for f in fs:
            fp = os.path.join(d, f)
            if os.path.relpath(fp, p) in bo_qua:
                continue
            ra[os.path.relpath(fp, p)] = hashlib.sha256(open(fp, "rb").read()).hexdigest()
    return ra


@pytest.fixture
def may(tmp_path):
    goc = str(tmp_path / "cs")
    DM.tao_bo_cuc_moi(goc)
    w = lambda rel, nd, mode=0o644: (  # noqa: E731
        os.makedirs(os.path.dirname(os.path.join(goc, rel)), exist_ok=True),
        open(os.path.join(goc, rel), "w").write(nd), os.chmod(os.path.join(goc, rel), mode))
    w("config/config.json", '{"a": 1}', 0o600)
    w("secrets/flask-secret.key", "FLASK", 0o600)
    w("secrets/samba-deploy.key", "SMBKEY", 0o600)
    w("pki/ca.pem", "CA")
    w("pki/ca.key", "CAKEY", 0o600)
    w("data/trienkhai/may.json", '[{"ip":"1.2.3.4"}]')
    w("data/trienkhai/cache/x.zip", "TAM")                       # phai bi loai
    w("data/lich-su-cai.json", "[]")
    w("deploy/kichban/kb1.json", '{"ten":"kb1"}', 0o600)
    w("deploy/apps/_thongtin.json", "{}")
    w("deploy/apps/phanmem.msi", "NANG" * 100)
    w("deploy/os/install.wim", "RATNANG" * 100)
    w("storage/a.txt", "kho")
    return goc


def test_goi_cauhinh_co_dung_noi_dung_va_kiem_duoc(may, tmp_path):
    ra = str(tmp_path / "g.tar.gz")
    mf = S.tao_goi(may, "cauhinh", ra)
    ten = {t["duong"] for t in mf["tep"]}
    assert "secrets/samba-deploy.key" in ten and "deploy/kichban/kb1.json" in ten and "pki/ca.key" in ten
    assert "deploy/os/install.wim" not in ten and "storage/a.txt" not in ten and "data/trienkhai/cache/x.zip" not in ten
    assert S.kiem_goi(ra)["che_do"] == "cauhinh"


def test_goi_toanbo_co_ca_deploy_va_storage(may, tmp_path):
    ra = str(tmp_path / "t.tar.gz")
    ten = {t["duong"] for t in S.tao_goi(may, "toanbo", ra)["tep"]}
    assert {"deploy/os/install.wim", "storage/a.txt", "deploy/apps/phanmem.msi"} <= ten


def test_deploy_la_lien_ket_van_duoc_dua_vao(may, tmp_path):
    that = tmp_path / "deploy-that"
    os.rename(os.path.join(may, "deploy"), that)
    os.symlink(that, os.path.join(may, "deploy"))
    mf = S.tao_goi(may, "toanbo", str(tmp_path / "l.tar.gz"))
    assert "deploy/kichban/kb1.json" in {t["duong"] for t in mf["tep"]}


def test_luong_web_cho_cung_ket_qua_kiem_duoc(may, tmp_path):
    p = tmp_path / "luong.tar.gz"
    with open(p, "wb") as f:
        for kh in S.tao_luong(may, "toanbo", kich_thuoc_khoi=64):
            f.write(kh)
    assert S.kiem_goi(str(p))["che_do"] == "toanbo"


def test_file_bi_sua_mot_byte_thi_kiem_that_bai(may, tmp_path):
    ra = str(tmp_path / "g.tar.gz")
    S.tao_goi(may, "cauhinh", ra)
    # dung lai goi voi 1 file bi doi noi dung nhung giu nguyen manifest
    xay = str(tmp_path / "hong.tar.gz")
    with tarfile.open(ra) as a, tarfile.open(xay, "w:gz") as b:
        for tv in a:
            nd = a.extractfile(tv).read() if tv.isfile() else None
            if tv.name == "secrets/flask-secret.key":
                nd = b"FLASX"
            b.addfile(tv, io.BytesIO(nd) if nd is not None else None)
    with pytest.raises(S.LoiSaoLuu, match="sai ma bam"):
        S.kiem_goi(xay)


def _goi_tu_tao(duong, thanh_vien, manifest=True, **mf_kw):
    with tarfile.open(duong, "w:gz") as tf:
        for ten, nd, loai in thanh_vien:
            ti = tarfile.TarInfo(ten)
            if loai == "link":
                ti.type, ti.linkname = tarfile.SYMTYPE, "/etc/passwd"
                tf.addfile(ti)
            else:
                ti.size = len(nd)
                tf.addfile(ti, io.BytesIO(nd))
        if manifest:
            tep = [{"duong": n, "byte": len(d), "sha256": hashlib.sha256(d).hexdigest()} for n, d, l in thanh_vien if l == "file"]
            mf = dict({"dinh_dang": 1, "san_pham": "console-system", "che_do": "cauhinh", "schema": 1, "bo_cuc": "moi", "tep": tep}, **mf_kw)
            nd = json.dumps(mf).encode()
            ti = tarfile.TarInfo(S.TEN_MANIFEST)
            ti.size = len(nd)
            tf.addfile(ti, io.BytesIO(nd))


@pytest.mark.parametrize("ten", ["../etc/passwd", "/etc/passwd", "config/../../x", "lung-tung/a.txt", "config//x", "./config/a"])
def test_ten_nguy_hiem_bi_tu_choi(tmp_path, ten):
    p = str(tmp_path / "x.tar.gz")
    _goi_tu_tao(p, [(ten, b"x", "file")])
    with pytest.raises(S.LoiSaoLuu, match="khong an toan"):
        S.kiem_goi(p)


def test_link_trong_goi_bi_tu_choi(tmp_path):
    p = str(tmp_path / "x.tar.gz")
    _goi_tu_tao(p, [("config/lk", b"", "link")])
    with pytest.raises(S.LoiSaoLuu, match="link"):
        S.kiem_goi(p)


def test_thieu_manifest_hoac_sai_san_pham(tmp_path):
    p = str(tmp_path / "x.tar.gz")
    _goi_tu_tao(p, [("config/a", b"x", "file")], manifest=False)
    with pytest.raises(S.LoiSaoLuu, match="thieu manifest"):
        S.kiem_goi(p)
    _goi_tu_tao(p, [("config/a", b"x", "file")], san_pham="khac")
    with pytest.raises(S.LoiSaoLuu, match="khong cung"):
        S.kiem_goi(p)


def test_khoi_phuc_dua_ve_dung_trang_thai_cu_va_giu_quyen(may, tmp_path):
    ra = str(tmp_path / "g.tar.gz")
    S.tao_goi(may, "cauhinh", ra)
    chuan = bam_cay(may)
    # pha hong: sua, xoa, them
    open(os.path.join(may, "config/config.json"), "w").write("HONG")
    os.remove(os.path.join(may, "secrets/samba-deploy.key"))
    open(os.path.join(may, "data/file-la.json"), "w").write("thua")
    os.remove(os.path.join(may, "deploy/kichban/kb1.json"))
    open(os.path.join(may, "storage/a.txt"), "w").write("giu-nguyen-vi-chi-cauhinh")
    kq = S.khoi_phuc(ra, may)
    assert os.path.exists(kq["goi_truoc"]) and S.kiem_goi(kq["goi_truoc"])           # goi tu sao luu cung kiem duoc
    sau = bam_cay(may)
    assert not os.path.exists(os.path.join(may, "data/file-la.json"))                 # file thua bi go (thay ca cay)
    for k, v in chuan.items():
        if not k.startswith("storage/"):
            assert sau[k] == v, k
    assert open(os.path.join(may, "storage/a.txt")).read() == "giu-nguyen-vi-chi-cauhinh"
    assert os.stat(os.path.join(may, "secrets")).st_mode & 0o777 == 0o700
    assert os.stat(os.path.join(may, "secrets/samba-deploy.key")).st_mode & 0o777 == 0o600
    assert not [x for x in os.listdir(may) if x.startswith((".khoiphuc-", ".truoc-khoiphuc"))]


def test_khoi_phuc_toanbo_ghi_de_khong_xoa_file_thua(may, tmp_path):
    ra = str(tmp_path / "t.tar.gz")
    S.tao_goi(may, "toanbo", ra)
    open(os.path.join(may, "deploy/os/install.wim"), "w").write("SAI")
    open(os.path.join(may, "deploy/os/them.wim"), "w").write("MOI-HON")
    S.khoi_phuc(ra, may)
    assert open(os.path.join(may, "deploy/os/install.wim")).read() == "RATNANG" * 100
    assert open(os.path.join(may, "deploy/os/them.wim")).read() == "MOI-HON"


def test_khoi_phuc_loi_giua_chung_tra_ve_nhu_cu(may, tmp_path, monkeypatch):
    ra = str(tmp_path / "g.tar.gz")
    S.tao_goi(may, "cauhinh", ra)
    open(os.path.join(may, "config/config.json"), "w").write("HIEN-TAI")
    truoc = bam_cay(may)
    thuc = os.rename
    dem = []

    def hong(a, b):
        dem.append(1)
        if len(dem) == 4:                       # sau khi da doi vai thu muc
            raise OSError("het cho gia")
        return thuc(a, b)
    monkeypatch.setattr(os, "rename", hong)
    with pytest.raises(OSError):
        S.khoi_phuc(ra, may)
    monkeypatch.setattr(os, "rename", thuc)
    assert bam_cay(may) == truoc
    assert not [x for x in os.listdir(may) if x.startswith((".khoiphuc-", ".truoc-khoiphuc"))]


def test_tu_choi_goi_tu_du_lieu_moi_hon_ma(may, tmp_path):
    p = str(tmp_path / "x.tar.gz")
    _goi_tu_tao(p, [("config/a", b"x", "file")], schema=99)
    with pytest.raises(S.LoiSaoLuu, match="MOI hon"):
        S.khoi_phuc(p, may)


def test_tu_choi_khi_chua_o_bo_cuc_moi(tmp_path):
    (tmp_path / "cu").mkdir()
    with pytest.raises(S.LoiSaoLuu, match="chua o bo cuc moi"):
        S.khoi_phuc(str(tmp_path / "bat-ky"), str(tmp_path / "cu"))


def test_khoi_phuc_khi_mat_sach_du_lieu_va_ca_schema_version(may, tmp_path):
    """Tham hoa that (24/10 thu tren .30): dich vu bi bo trong, schema_version.json cung mat -> van khoi phuc duoc."""
    import shutil
    ra = str(tmp_path / "g.tar.gz")
    S.tao_goi(may, "cauhinh", ra)
    chuan = {k: v for k, v in bam_cay(may).items() if not k.startswith(("storage/", "deploy/os", "deploy/apps/phanmem"))}
    for d in ("config", "secrets", "pki", "data"):
        shutil.rmtree(os.path.join(may, d))
    shutil.rmtree(os.path.join(may, "deploy", "kichban"))
    os.remove(os.path.join(may, "schema_version.json"))
    S.khoi_phuc(ra, may)
    sau = bam_cay(may)
    assert all(sau.get(k) == v for k, v in chuan.items() if not k.startswith("data/trienkhai/cache"))
    assert DM.doc_phien_ban(may) == 1


def test_sao_luu_van_chay_khi_schema_version_hong(may, tmp_path):
    open(os.path.join(may, "schema_version.json"), "w").write("{hong")
    assert S.tao_goi(may, "cauhinh", str(tmp_path / "x.tar.gz"))["schema"] == 0
