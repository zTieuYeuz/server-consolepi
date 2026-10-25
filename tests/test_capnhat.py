"""C0/C1: khoa ky, goi .cspkg, danh muc phien ban - gom ca cac kieu TAN CONG (goi gia, sua byte, cat cut, doi thu tu, phat lai, nhay cap)."""
import hashlib
import io
import json
import os
import stat
import struct
import subprocess
import sys
import tarfile
import time

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))
from consolesystem.core.capnhat import danhmuc as DM  # noqa: E402
from consolesystem.core.capnhat import goi as G  # noqa: E402
from consolesystem.core.capnhat import khoa as K  # noqa: E402

N = 2 ** 14           # scrypt nhe cho test


def viet(p, nd, mode=0o644):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(nd if isinstance(nd, bytes) else nd.encode())
    os.chmod(p, mode)


@pytest.fixture
def cay(tmp_path):
    b = tmp_path / "ban"
    viet(str(b / "app.py"), "print('hi')\n" * 50)
    viet(str(b / "ui/a.py"), "A" * 5000)
    viet(str(b / "ui/b.py"), os.urandom(70000))
    viet(str(b / "scripts/chay.sh"), "#!/bin/sh\necho ok\n", 0o755)
    viet(str(b / "system/x.conf"), "conf")
    viet(str(b / "RELEASE.json"), json.dumps({"ten": "2.0.1"}))
    return str(b)


@pytest.fixture
def khoa(tmp_path):
    d = str(tmp_path / "khoa")
    for vt in K.VAI_TRO:
        K.luu_cap_khoa(d, vt, "mat-khau-thu-nghiem-%s" % vt, n=N)
    return d


def tai_khoa(d, vt):
    pub, _ = K.doc_khoa_cong_khai(os.path.join(d, vt + ".khoa-cong-khai.json"))
    priv = K.doc_khoa_rieng(os.path.join(d, vt + ".khoa-rieng.json"), "mat-khau-thu-nghiem-%s" % vt)
    return priv, pub, K.dau_van_tay(pub)


@pytest.fixture
def he(khoa):
    """(priv_ph, id_ph, tin_cay_phong_bi, pub_goc, khoa_hop_le)"""
    goc_priv, goc_pub, goc_id = tai_khoa(khoa, "goc")
    ph_priv, ph_pub, ph_id = tai_khoa(khoa, "phat-hanh")
    lk_priv, lk_pub, lk_id = tai_khoa(khoa, "lenh-khoa")
    het = int(time.time()) + 86400 * 365
    tc = K.tao_tai_lieu_tin_cay([{"vai_tro": "phat-hanh", "khoa_cong_khai": K.b64(ph_pub), "den": het},
                                 {"vai_tro": "lenh-khoa", "khoa_cong_khai": K.b64(lk_pub), "den": het}], 1, int(time.time()) + 86400 * 30, goc_priv, goc_id)
    hop_le, _ = K.khoa_hop_le(tc, goc_pub, "phat-hanh")
    return ph_priv, ph_id, tc, goc_pub, hop_le


def tt(**kw):
    d = {"phien_ban": "2.0.1", "so_phat_hanh": 2, "kien_truc": "amd64", "kenh": "on-dinh", "ban_truoc_bat_buoc": "2.0.0", "ghi_chu": "Ban thu"}
    d.update(kw)
    return d


HT = {"phien_ban": "2.0.0", "so_phat_hanh": 1, "kien_truc": "amd64", "kenh": "on-dinh", "ban_toi_thieu_ha_cap": "1.9.5"}


# ===================================================================================================== khoa
def test_khoa_rieng_ma_hoa_va_sai_mat_khau(tmp_path):
    d = str(tmp_path / "k")
    fp = K.luu_cap_khoa(d, "goc", "mat-khau-dai-12345", n=N)
    f = os.path.join(d, "goc.khoa-rieng.json")
    assert stat.S_IMODE(os.stat(f).st_mode) == 0o600
    priv_raw = K._raw_priv(K.doc_khoa_rieng(f, "mat-khau-dai-12345"))
    assert priv_raw.hex() not in open(f).read() and K.b64(priv_raw) not in open(f).read()        # khong lo khoa rieng ro
    with pytest.raises(K.LoiKhoa, match="sai mat khau"):
        K.doc_khoa_rieng(f, "sai-mat-khau-12345")
    with pytest.raises(K.LoiKhoa, match="DA CO"):
        K.luu_cap_khoa(d, "goc", "mat-khau-khac-12345", n=N)                                        # khong ghi de
    assert fp == K.dau_van_tay(K.doc_khoa_cong_khai(os.path.join(d, "goc.khoa-cong-khai.json"))[0])


def test_khoa_rieng_bi_sua_thi_tu_choi(tmp_path):
    d = str(tmp_path / "k")
    K.luu_cap_khoa(d, "phat-hanh", "mat-khau-dai-12345", n=N)
    f = os.path.join(d, "phat-hanh.khoa-rieng.json")
    doc = json.load(open(f))
    doc["vai_tro"] = "goc"                              # doi vai tro trong file -> AAD khac -> hong
    with pytest.raises(K.LoiKhoa):
        K.giai_ma_khoa_rieng(doc, "mat-khau-dai-12345")


def test_mat_khau_lay_tu_bien_moi_truong(monkeypatch):
    monkeypatch.setenv("CS_KHOA_MAT_KHAU", "chung-chung-12345")
    monkeypatch.setenv("CS_KHOA_MAT_KHAU_GOC", "rieng-goc-12345")
    assert K.lay_mat_khau(vai_tro="goc") == "rieng-goc-12345" and K.lay_mat_khau(vai_tro="phat-hanh") == "chung-chung-12345"


def test_tai_lieu_tin_cay_va_xoay_khoa(khoa):
    goc_priv, goc_pub, goc_id = tai_khoa(khoa, "goc")
    _, ph_pub, _ = tai_khoa(khoa, "phat-hanh")
    now = int(time.time())
    tc = K.tao_tai_lieu_tin_cay([{"vai_tro": "phat-hanh", "khoa_cong_khai": K.b64(ph_pub), "den": now + 1000}], 5, now + 1000, goc_priv, goc_id)
    ds, so = K.khoa_hop_le(tc, goc_pub, "phat-hanh")
    assert [x[1] for x in ds] == [ph_pub] and so == 5
    with pytest.raises(K.LoiKhoa, match="CU HON"):
        K.khoa_hop_le(tc, goc_pub, "phat-hanh", so_hieu_da_thay=6)                                  # lui so hieu
    with pytest.raises(K.LoiKhoa, match="HET HAN"):
        K.khoa_hop_le(tc, goc_pub, "phat-hanh", bay_gio=now + 5000)                                 # tan cong dong bang
    gia_priv, gia_pub = K.tao_cap_khoa()
    gia = K.tao_tai_lieu_tin_cay([{"vai_tro": "phat-hanh", "khoa_cong_khai": K.b64(gia_pub), "den": now + 1000}], 9, now + 1000,
                                 K.Ed25519PrivateKey.from_private_bytes(gia_priv), "x")
    with pytest.raises(K.LoiKhoa, match="chu ky tai lieu"):
        K.khoa_hop_le(gia, goc_pub, "phat-hanh")                                                    # khong phai khoa goc ky
    sua = dict(tc)
    sua["noi_dung"] = tc["noi_dung"].replace('"so_hieu":5', '"so_hieu":6')
    with pytest.raises(K.LoiKhoa, match="chu ky tai lieu"):
        K.khoa_hop_le(sua, goc_pub, "phat-hanh")
    # xoay khoa: tai lieu moi chi chua khoa moi -> khoa cu het hieu luc
    p2, pub2 = K.tao_cap_khoa()
    tc2 = K.tao_tai_lieu_tin_cay([{"vai_tro": "phat-hanh", "khoa_cong_khai": K.b64(pub2), "den": now + 1000}], 6, now + 1000, goc_priv, goc_id)
    ds2, _ = K.khoa_hop_le(tc2, goc_pub, "phat-hanh")
    assert [x[1] for x in ds2] == [pub2] and ph_pub not in [x[1] for x in ds2]


def test_tai_lieu_tin_cay_khong_chua_khoa_goc(khoa):
    goc_priv, goc_pub, goc_id = tai_khoa(khoa, "goc")
    with pytest.raises(K.LoiKhoa):
        K.tao_tai_lieu_tin_cay([{"vai_tro": "goc", "khoa_cong_khai": K.b64(goc_pub), "den": 1}], 1, 1, goc_priv, goc_id)


# ===================================================================================================== goi
def lam_goi(cay, he, tmp_path, ten="g.cspkg", khoi=4096, **kw):
    ph_priv, ph_id, *_ = he
    dich = str(tmp_path / ten)
    m, dek = G.dong_goi(cay, tt(**kw), ph_priv, ph_id, dich, kich_thuoc_khoi=khoi)
    return dich, m, dek


def cai(dich, dek, he, tmp_path, ht=HT, **kw):
    return G.cai_goi(dich, dek, he[4], ht, str(tmp_path / "releases"), **kw)


def so_cay(p):
    ra = {}
    for d, _ds, fs in os.walk(p):
        for f in fs:
            fp = os.path.join(d, f)
            ra[os.path.relpath(fp, p)] = hashlib.sha256(open(fp, "rb").read()).hexdigest()
    return ra


def test_dong_goi_va_cai_lai_giong_het(cay, he, tmp_path):
    dich, m, dek = lam_goi(cay, he, tmp_path)
    assert os.path.getsize(dich) > 1000 and len(dek) == 32
    ten, m2 = cai(dich, dek, he, tmp_path)
    assert ten == "2.0.1" and m2["phien_ban"] == "2.0.1"
    ra = str(tmp_path / "releases" / "2.0.1")
    assert so_cay(ra) == so_cay(cay)
    assert os.stat(os.path.join(ra, "scripts/chay.sh")).st_mode & 0o111 and not os.stat(os.path.join(ra, "app.py")).st_mode & 0o222
    assert not [x for x in os.listdir(tmp_path / "releases") if x.startswith(".cai-")]


def test_noi_dung_khong_lo_ro_trong_goi(cay, he, tmp_path):
    dich, _m, _d = lam_goi(cay, he, tmp_path)
    raw = open(dich, "rb").read()
    assert b"print('hi')" not in raw and b"AAAAAAAAAAAAAAAA" not in raw
    assert b"2.0.1" in raw                                   # chi manifest (da ky) o dang ro


def test_goi_xac_dinh_cung_payload_khac_ban_ma(cay, he, tmp_path):
    d1, m1, k1 = lam_goi(cay, he, tmp_path, "a.cspkg")
    d2, m2, k2 = lam_goi(cay, he, tmp_path, "b.cspkg")
    with open(d1, "rb") as f1, open(d2, "rb") as f2:
        h1, h2 = G.doc_dau(f1)[0], G.doc_dau(f2)[0]
    assert h1["tai_trong"]["sha256"] == h2["tai_trong"]["sha256"]          # tar xac dinh
    assert open(d1, "rb").read() != open(d2, "rb").read() and k1 != k2        # nhung nonce/khoa khac


def sua_byte(dich, vi_tri, ra):
    b = bytearray(open(dich, "rb").read())
    b[vi_tri] ^= 0x55
    open(ra, "wb").write(bytes(b))
    return ra


@pytest.mark.parametrize("phan", ["magic", "dau", "chu_ky", "khoi_dau", "khoi_giua", "khoi_cuoi"])
def test_sua_mot_byte_o_bat_ky_dau_deu_bi_chan(cay, he, tmp_path, phan):
    dich, m, dek = lam_goi(cay, he, tmp_path)
    raw = open(dich, "rb").read()
    n_dau = struct.unpack(">I", raw[7:11])[0]
    vi = {"magic": 3, "dau": 11 + n_dau // 2, "chu_ky": 11 + n_dau + 10, "khoi_dau": 11 + n_dau + 64 + 50,
          "khoi_giua": len(raw) // 2, "khoi_cuoi": len(raw) - 5}[phan]
    bad = sua_byte(dich, vi, str(tmp_path / "bad.cspkg"))
    with pytest.raises(G.LoiGoi):
        cai(bad, dek, he, tmp_path)
    assert not os.path.exists(tmp_path / "releases" / "2.0.1")


@pytest.mark.parametrize("cat", [10, 100, 400, -100, -1])
def test_cat_cut_goi_bi_chan(cay, he, tmp_path, cat):
    dich, m, dek = lam_goi(cay, he, tmp_path)
    raw = open(dich, "rb").read()
    bad = str(tmp_path / "cut.cspkg")
    open(bad, "wb").write(raw[:cat] if cat > 0 else raw[:cat])
    with pytest.raises(G.LoiGoi):
        cai(bad, dek, he, tmp_path)


def test_du_lieu_thua_sau_goi_bi_chan(cay, he, tmp_path):
    dich, m, dek = lam_goi(cay, he, tmp_path)
    bad = str(tmp_path / "thua.cspkg")
    open(bad, "wb").write(open(dich, "rb").read() + b"\0")
    with pytest.raises(G.LoiGoi, match="thua|cat cut|khoi"):
        cai(bad, dek, he, tmp_path)


def test_doi_thu_tu_khoi_bi_chan(cay, he, tmp_path):
    dich, m, dek = lam_goi(cay, he, tmp_path)
    raw = open(dich, "rb").read()
    with open(dich, "rb") as f:
        dau, dau_b, cs = G.doc_dau(f)
        vi_tri = f.tell()
        khoi = []
        while True:
            h = f.read(4)
            if not h:
                break
            n = struct.unpack(">I", h)[0]
            khoi.append(h + f.read(n))
    assert len(khoi) >= 4
    khoi[1], khoi[2] = khoi[2], khoi[1]
    bad = str(tmp_path / "doi.cspkg")
    open(bad, "wb").write(raw[:vi_tri] + b"".join(khoi))
    with pytest.raises(G.LoiGoi, match="tag|khoi"):
        cai(bad, dek, he, tmp_path)


def test_ghep_khoi_tu_goi_khac_bi_chan(cay, he, tmp_path):
    d1, _m1, k1 = lam_goi(cay, he, tmp_path, "a.cspkg")
    d2, _m2, _k2 = lam_goi(cay, he, tmp_path, "b.cspkg")
    r1, r2 = open(d1, "rb").read(), open(d2, "rb").read()
    with open(d1, "rb") as f:
        _d, db, _c = G.doc_dau(f)
        v = f.tell()
    # dau goi 1 + khoi cua goi 2 (cung khoa goi khong, nhung nonce/AAD khac)
    with open(d2, "rb") as f:
        G.doc_dau(f)
        v2 = f.tell()
    bad = str(tmp_path / "ghep.cspkg")
    open(bad, "wb").write(r1[:v] + r2[v2:])
    with pytest.raises(G.LoiGoi):
        cai(bad, k1, he, tmp_path)


def test_sai_khoa_goi_bi_chan(cay, he, tmp_path):
    dich, m, dek = lam_goi(cay, he, tmp_path)
    with pytest.raises(G.LoiGoi, match="tag"):
        cai(dich, os.urandom(32), he, tmp_path)


def test_chu_ky_cua_khoa_la_bi_chan(cay, he, tmp_path):
    priv2, pub2 = K.tao_cap_khoa()
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    ke_gia = Ed25519PrivateKey.from_private_bytes(priv2)
    dich = str(tmp_path / "gia.cspkg")
    _m, dek = G.dong_goi(cay, tt(), ke_gia, he[1], dich)                      # gia danh id khoa phat-hanh that, ky bang khoa la
    with pytest.raises(G.LoiGoi, match="CHU KY KHONG HOP LE"):
        cai(dich, dek, he, tmp_path)
    dich2 = str(tmp_path / "gia2.cspkg")
    _m, dek2 = G.dong_goi(cay, tt(), ke_gia, K.dau_van_tay(pub2), dich2)      # khai dung id khoa la -> khong nam trong tin cay
    with pytest.raises(G.LoiGoi, match="khong nam trong danh sach khoa tin cay"):
        cai(dich2, dek2, he, tmp_path)


def test_khoa_lenh_khoa_khong_ky_duoc_goi(cay, khoa, he, tmp_path):
    lk_priv, _lk_pub, lk_id = tai_khoa(khoa, "lenh-khoa")
    dich = str(tmp_path / "lk.cspkg")
    _m, dek = G.dong_goi(cay, tt(), lk_priv, lk_id, dich)
    with pytest.raises(G.LoiGoi, match="khong nam trong danh sach khoa tin cay"):
        cai(dich, dek, he, tmp_path)                                           # khoa lenh-khoa khong co quyen ky goi


def test_phat_lai_goi_cu_va_nhay_cap_bi_chan(cay, he, tmp_path):
    dich, m, dek = lam_goi(cay, he, tmp_path)                                  # so_phat_hanh 2, can o 2.0.0
    with pytest.raises(G.LoiGoi, match="CU hon hoac bang"):
        cai(dich, dek, he, tmp_path, ht=dict(HT, so_phat_hanh=2, phien_ban="2.0.0"))            # phat lai
    with pytest.raises(G.LoiGoi, match="TUAN TU"):
        cai(dich, dek, he, tmp_path, ht=dict(HT, phien_ban="1.9.5"))                            # nhay cap tu 1.9.5
    with pytest.raises(G.LoiGoi, match="kien truc"):
        cai(dich, dek, he, tmp_path, ht=dict(HT, kien_truc="arm64"))
    with pytest.raises(G.LoiGoi, match="kenh"):
        cai(dich, dek, he, tmp_path, ht=dict(HT, kenh="thu-nghiem"))
    assert not os.path.exists(tmp_path / "releases" / "2.0.1")
    cai(dich, dek, he, tmp_path)                                               # dung dieu kien: OK
    with pytest.raises(G.LoiGoi, match="da co ban"):
        cai(dich, dek, he, tmp_path)


def test_ha_cap_chi_khi_duoc_phep(cay, he, tmp_path):
    dich, m, dek = lam_goi(cay, he, tmp_path, phien_ban="2.0.0", so_phat_hanh=1, ban_truoc_bat_buoc=None)
    cur = {"phien_ban": "2.0.1", "so_phat_hanh": 2, "kien_truc": "amd64", "kenh": "on-dinh", "ban_toi_thieu_ha_cap": "2.0.0"}
    assert G.kiem_dieu_kien_cai(m, cur, ha_cap=True) == []
    assert "ha cap" in " ".join(G.kiem_dieu_kien_cai(m, dict(cur, ban_toi_thieu_ha_cap="2.0.1"), ha_cap=True))
    assert "ha cap" in " ".join(G.kiem_dieu_kien_cai(m, dict(cur, ban_toi_thieu_ha_cap=None), ha_cap=True))
    assert G.kiem_dieu_kien_cai(m, cur, ha_cap=False)                          # khong phai che do ha cap -> chan (so phat hanh thap)


def test_so_sanh_phien_ban():
    k = G.khoa_phien_ban
    assert k("2.0.1") > k("2.0.0") > k("1.9.5") and k("2.0.1-2") > k("2.0.1") and k("2.0") == k("2.0.0") and k("10.0.0") > k("9.9.9")
    for xau in ("", "x", "2..1", "2.0.1-", None):
        with pytest.raises(G.LoiGoi):
            k(xau)


def test_dong_goi_tu_choi_thong_tin_sai(cay, he):
    ph_priv, ph_id, *_ = he
    for sai in ({"phien_ban": "abc"}, {"kien_truc": "i386"}, {"kenh": "la"}, {"so_phat_hanh": 0}, {"so_phat_hanh": "2"}):
        with pytest.raises(G.LoiGoi):
            G.dong_goi(cay, tt(**sai), ph_priv, ph_id, "/tmp/khong-ghi.cspkg")
    with pytest.raises(G.LoiGoi, match="thieu truong"):
        G.dong_goi(cay, {"phien_ban": "1.0.0"}, ph_priv, ph_id, "/tmp/khong-ghi.cspkg")


# --------------------------------------- noi dung tar doc hai (tan cong o tang giai nen, sau khi chu ky/tag deu qua)
def tar_gz(thanh_vien, ra):
    with tarfile.open(ra, "w:gz") as tf:
        for ten, nd, loai in thanh_vien:
            ti = tarfile.TarInfo(ten)
            if loai == "sym":
                ti.type, ti.linkname = tarfile.SYMTYPE, "/etc/passwd"
                tf.addfile(ti)
            elif loai == "hard":
                ti.type, ti.linkname = tarfile.LNKTYPE, "app.py"
                tf.addfile(ti)
            elif loai == "dev":
                ti.type = tarfile.CHRTYPE
                tf.addfile(ti)
            else:
                ti.size = len(nd)
                tf.addfile(ti, io.BytesIO(nd))
    return ra


@pytest.mark.parametrize("ten", ["../x", "/etc/passwd", "a/../../x", "a//b", "./a", "a\\b"])
def test_giai_nen_chan_ten_nguy_hiem(tmp_path, ten):
    t = tar_gz([(ten, b"x", "file")], str(tmp_path / "t.tar.gz"))
    with pytest.raises(G.LoiGoi, match="khong an toan"):
        G.giai_nen_an_toan(t, str(tmp_path / "ra"), {"tep": {ten: "0"}})


@pytest.mark.parametrize("loai", ["sym", "hard", "dev"])
def test_giai_nen_chan_link_va_thiet_bi(tmp_path, loai):
    t = tar_gz([("l", b"", loai)], str(tmp_path / "t.tar.gz"))
    with pytest.raises(G.LoiGoi, match="loai muc"):
        G.giai_nen_an_toan(t, str(tmp_path / "ra"), {"tep": {"l": "0"}})


def test_giai_nen_chan_file_ngoai_manifest_thieu_file_va_sai_ma_bam(tmp_path):
    h = hashlib.sha256(b"x").hexdigest()
    t = tar_gz([("a", b"x", "file"), ("b", b"y", "file")], str(tmp_path / "t.tar.gz"))
    with pytest.raises(G.LoiGoi, match="KHONG co trong manifest"):
        G.giai_nen_an_toan(t, str(tmp_path / "r1"), {"tep": {"a": h}})
    t2 = tar_gz([("a", b"x", "file")], str(tmp_path / "t2.tar.gz"))
    with pytest.raises(G.LoiGoi, match="thieu 1 file"):
        G.giai_nen_an_toan(t2, str(tmp_path / "r2"), {"tep": {"a": h, "c": h}})
    with pytest.raises(G.LoiGoi, match="SAI sha256"):
        G.giai_nen_an_toan(t2, str(tmp_path / "r3"), {"tep": {"a": "0" * 64}})


def test_giai_nen_khong_ghi_de_va_bo_setuid(tmp_path):
    h = hashlib.sha256(b"x").hexdigest()
    with tarfile.open(str(tmp_path / "t.tar.gz"), "w:gz") as tf:
        ti = tarfile.TarInfo("s")
        ti.size, ti.mode = 1, 0o4777
        tf.addfile(ti, io.BytesIO(b"x"))
    G.giai_nen_an_toan(str(tmp_path / "t.tar.gz"), str(tmp_path / "ra"), {"tep": {"s": h}})
    m = os.stat(tmp_path / "ra" / "s").st_mode
    assert not m & stat.S_ISUID and m & 0o777 == 0o755


def test_goi_co_file_la_trong_tai_trong_bi_chan_du_chu_ky_dung(cay, he, tmp_path, monkeypatch):
    """Ke tan cong co khoa goi + khoa ky nhung manifest KHONG liet ke file la -> van bi chan o tang giai nen."""
    ph_priv, ph_id, *_ = he
    goc = G._tar_xac_dinh

    def them_file_la(thu_muc, dich_file):
        viet(os.path.join(thu_muc, "la.py"), "backdoor")
        try:
            return goc(thu_muc, dich_file)
        finally:
            os.remove(os.path.join(thu_muc, "la.py"))
    dich = str(tmp_path / "la.cspkg")
    monkeypatch.setattr(G, "_tar_xac_dinh", them_file_la)
    _m, dek = G.dong_goi(cay, tt(), ph_priv, ph_id, dich)
    monkeypatch.undo()
    with pytest.raises(G.LoiGoi, match="KHONG co trong manifest"):
        cai(dich, dek, he, tmp_path)
    assert not os.path.exists(tmp_path / "releases" / "2.0.1") and not [x for x in os.listdir(tmp_path / "releases") if x.startswith(".")]


# ===================================================================================================== danh muc
def lam_dm(he, **kw):
    ph_priv, ph_id, *_ = he
    ban = [{"phien_ban": "2.0.0", "so_phat_hanh": 1, "kien_truc": "amd64", "kich_thuoc": 1, "sha256_goi": "0" * 64, "ban_truoc_bat_buoc": "1.9.5"},
           {"phien_ban": "2.0.1", "so_phat_hanh": 2, "kien_truc": "amd64", "kich_thuoc": 1, "sha256_goi": "1" * 64, "ban_truoc_bat_buoc": "2.0.0"},
           {"phien_ban": "2.0.2", "so_phat_hanh": 3, "kien_truc": "amd64", "kich_thuoc": 1, "sha256_goi": "2" * 64, "ban_truoc_bat_buoc": "2.0.1"},
           {"phien_ban": "2.0.1", "so_phat_hanh": 2, "kien_truc": "arm64", "kich_thuoc": 1, "sha256_goi": "3" * 64, "ban_truoc_bat_buoc": "2.0.0"}]
    args = dict(kenh="on-dinh", so_hieu=10, cac_ban=ban, priv_phat_hanh=ph_priv, id_khoa=ph_id)
    args.update(kw)
    return DM.tao_danh_muc(**args)


def test_danh_muc_hop_le_va_ban_ke_tiep_tuan_tu(he):
    d = DM.mo_danh_muc(lam_dm(he), he[4], "on-dinh")
    b = DM.ban_ke_tiep(d, "2.0.0", "amd64")
    assert b["phien_ban"] == "2.0.1"                                                  # KHONG nhay thang 2.0.2
    assert DM.ban_ke_tiep(d, "2.0.1", "amd64")["phien_ban"] == "2.0.2"
    assert DM.ban_ke_tiep(d, "2.0.2", "amd64") is None
    assert DM.ban_ke_tiep(d, "2.0.1", "arm64") is None
    assert DM.ban_ke_tiep(d, "1.9.5", "amd64")["phien_ban"] == "2.0.0"
    assert DM.con_ban_moi_hon(d, "1.9.5", "amd64") and not DM.con_ban_moi_hon(d, "2.0.2", "amd64")


def test_danh_muc_het_han_tuong_lai_lui_so_hieu_sai_kenh_sai_khoa(he):
    now = time.time()
    pb = lam_dm(he, han=100, bay_gio=int(now) - 1000)
    with pytest.raises(G.LoiGoi, match="HET HAN"):
        DM.mo_danh_muc(pb, he[4], "on-dinh")
    with pytest.raises(G.LoiGoi, match="TUONG LAI"):
        DM.mo_danh_muc(lam_dm(he, bay_gio=int(now) + 3600), he[4], "on-dinh")
    with pytest.raises(G.LoiGoi, match="CU hon"):
        DM.mo_danh_muc(lam_dm(he), he[4], "on-dinh", so_hieu_da_thay=11)
    with pytest.raises(G.LoiGoi, match="sai loai/kenh"):
        DM.mo_danh_muc(lam_dm(he), he[4], "thu-nghiem")
    sua = lam_dm(he)
    sua["noi_dung"] = sua["noi_dung"].replace('"so_hieu":10', '"so_hieu":99')
    with pytest.raises(G.LoiGoi, match="chu ky"):
        DM.mo_danh_muc(sua, he[4], "on-dinh")
    with pytest.raises(G.LoiGoi, match="khong nam trong khoa tin cay"):
        DM.mo_danh_muc(lam_dm(he, id_khoa="khoa-la"), he[4], "on-dinh")


# ===================================================================================================== dong lenh dau cuoi
def chay_tool(ten, args, env_them=None):
    env = dict(os.environ, CS_KHOA_MAT_KHAU="mat-khau-cli-12345")
    env.update(env_them or {})
    return subprocess.run(["python3", os.path.join(GOC, "tools", ten)] + args, capture_output=True, text=True, env=env, timeout=180)


def test_dong_lenh_tu_dau_den_cuoi(cay, tmp_path):
    kd = str(tmp_path / "k")
    r = chay_tool("tao-khoa-ky.py", [kd, "--vai-tro", "goc", "--vai-tro", "phat-hanh", "--vai-tro", "lenh-khoa"])
    assert r.returncode == 0, r.stderr
    assert chay_tool("tao-khoa-ky.py", [kd, "--vai-tro", "goc"]).returncode == 1            # khong ghi de khoa rieng
    r = chay_tool("tao-khoa-ky.py", [kd, "--tin-cay", "--so-hieu", "1"])
    assert r.returncode == 0 and "2 khoa" in r.stdout, r.stdout + r.stderr
    goi = str(tmp_path / "console-system-2.0.1-amd64.cspkg")
    r = chay_tool("phat-hanh-ky.py", ["goi", "--khoa", kd, "--ban", cay, "--phien-ban", "2.0.1", "--so-phat-hanh", "2", "--kien-truc", "amd64", "--kenh", "on-dinh",
                                      "--ban-truoc", "2.0.0", "--ghi-chu", "thu", "--ra", goi])
    assert r.returncode == 0, r.stderr
    assert stat.S_IMODE(os.stat(goi + ".khoa-goi.json").st_mode) == 0o600
    r = chay_tool("phat-hanh-ky.py", ["danh-muc", "--khoa", kd, "--kenh", "on-dinh", "--so-hieu", "1", "--ra", str(tmp_path / "dm.json"), goi])
    assert r.returncode == 0, r.stderr
    cai_dir = str(tmp_path / "releases")
    r = chay_tool("kiem-goi.py", [goi, "--goc", kd + "/goc.khoa-cong-khai.json", "--tin-cay", kd + "/tin-cay.json", "--khoa-goi", goi + ".khoa-goi.json",
                                  "--thu-muc-cai", cai_dir, "--hien-tai-phien-ban", "2.0.0", "--hien-tai-so-phat-hanh", "1"])
    assert r.returncode == 0 and "CHU KY HOP LE" in r.stdout and "DA GIAI NEN" in r.stdout, r.stdout + r.stderr
    assert so_cay(os.path.join(cai_dir, "2.0.1")) == so_cay(cay)
    bad = sua_byte(goi, os.path.getsize(goi) // 2, str(tmp_path / "bad.cspkg"))
    r = chay_tool("kiem-goi.py", [bad, "--goc", kd + "/goc.khoa-cong-khai.json", "--tin-cay", kd + "/tin-cay.json", "--khoa-goi", goi + ".khoa-goi.json",
                                  "--thu-muc-cai", str(tmp_path / "r2"), "--hien-tai-phien-ban", "2.0.0", "--hien-tai-so-phat-hanh", "1"])
    assert r.returncode == 1 and "LOI" in r.stderr


def test_mat_khau_khong_hien_trong_tham_so_dong_lenh():
    src = open(os.path.join(GOC, "tools", "tao-khoa-ky.py")).read() + open(os.path.join(GOC, "tools", "phat-hanh-ky.py")).read()
    assert "--mat-khau" not in src and "add_argument(\"--password" not in src
