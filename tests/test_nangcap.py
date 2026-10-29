"""C3/C4/C5: kiem tra dinh ky, bo nang cap/ha cap - gom chen LOI o tung buoc va MAT DIEN o moi diem ghi."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from capnhat_gia import He, SupDo, kiem_nhat_quan, N, M, PH, K, DM, G, viet  # noqa: E402


@pytest.fixture
def he(tmp_path):
    return He(tmp_path)


def san_sang(he, **kw):
    moi = he.moi(**kw)
    ts = M.kiem_tra(moi, bat_buoc=True)
    assert not ts.get("loi"), ts
    return moi, ts


# ====================================================================================== C3: kiem tra dinh ky
def test_kiem_tra_thay_ban_ke_tiep_tuan_tu(he):
    moi, ts = san_sang(he)
    assert ts["co_ban_moi"] and ts["ban_ke_tiep"]["phien_ban"] == "2.0.1" and ts["ban_moi_nhat"]["phien_ban"] == "2.0.2"
    assert M.co_ban_moi(moi) and ts["hoi_lan_sau"] >= he.gio() + M.CHU_KY_HOI
    assert os.path.exists(os.path.join(he.goc, "updates", "tin-cay.json"))


def test_chua_den_han_thi_khong_hoi_lai(he):
    moi, ts = san_sang(he)
    he.kho.loi_danh_muc = M.LoiKho("khong toi duoc")
    again = M.kiem_tra(moi)                                   # chua den han -> dung ket qua cu, khong goi kho
    assert again["hoi_luc"] == ts["hoi_luc"] and not again["loi"]
    he.t[0] += M.CHU_KY_HOI + M.LECH_NGAU_NHIEN + 1
    assert M.den_han_hoi(moi)
    loi = M.kiem_tra(moi)
    assert loi["loai_loi"] == "kho" and not M.co_ban_moi(moi) and loi["hoi_lan_sau"] <= he.gio() + 3600 + 1       # loi mang: thu lai sau ~1 gio


def test_tat_hoi_dinh_ky(he):
    moi = he.moi()
    M.luu_cau_hinh(moi, hoi_dinh_ky=False)
    assert not M.den_han_hoi(moi)
    assert M.kiem_tra(moi, bat_buoc=True)["hoi_luc"]                  # bam 'Kiem tra ngay' van duoc


def test_chua_co_khoa_goc_thi_tat_cap_nhat(he):
    moi = he.moi(khoa_goc=None)
    os.environ["CS_KHOA_GOC_FILE"] = "/khong/ton/tai"
    try:
        ts = M.kiem_tra(moi, bat_buoc=True)
    finally:
        os.environ.pop("CS_KHOA_GOC_FILE")
    assert ts["loai_loi"] == "cau-hinh" and "KHÓA GỐC" in ts["loi"] and not M.co_ban_moi(moi)


def test_danh_muc_het_han_va_dong_ho_lech(he):
    moi = he.moi()
    he.t[0] += 8 * 86400                                      # qua han 7 ngay cua danh muc
    ts = M.kiem_tra(moi, bat_buoc=True)
    assert ts["loai_loi"] == "an-ninh" and "HẾT HẠN" in ts["loi"] and not ts.get("co_ban_moi")


def test_danh_muc_lui_so_hieu_bi_chan(he):
    moi, _ = san_sang(he)
    he.ghi_danh_muc(so_hieu=1)
    old = he.danh_muc_pb
    he.ghi_danh_muc(so_hieu=5)
    he.t[0] += 10
    M.kiem_tra(moi, bat_buoc=True)                                     # ghi nho so_hieu 5
    he.danh_muc_pb = old                                               # ke tan cong phat lai danh muc CU
    ts = M.kiem_tra(moi, bat_buoc=True)
    assert ts["loai_loi"] == "an-ninh" and "CŨ hơn" in ts["loi"]


def test_danh_muc_ky_boi_khoa_la_bi_chan(he):
    moi = he.moi()
    priv2, pub2 = K.tao_cap_khoa()
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    he.danh_muc_pb = DM.tao_danh_muc("on-dinh", 9, he.ban, Ed25519PrivateKey.from_private_bytes(priv2), he.ph_id, bay_gio=int(he.t[0]))
    ts = M.kiem_tra(moi, bat_buoc=True)
    assert ts["loai_loi"] == "an-ninh" and "chữ ký" in ts["loi"].lower()


# ====================================================================================== C4: nang cap thanh cong
def chay(moi):
    return N.chay_job(moi)


def test_nang_cap_thanh_cong_day_du(he):
    moi, _ = san_sang(he)
    job = N.bat_dau_nang_cap(moi)
    assert job["den"] == "2.0.1" and job["trang_thai"] == "dang-chay"
    j = chay(moi)
    assert j["trang_thai"] == "xong", j["nhat_ky"][-3:]
    assert PH.hien_tai(he.opt) == "2.0.1" and kiem_nhat_quan(he, moi) == "2.0.1"
    assert os.path.isdir(os.path.join(he.opt, "releases", "2.0.0"))                   # ban cu van con de ha cap
    assert he.nhat_ky == ["sao_luu", "migration", "ap_dung", "khoi_dong_lai", "suc_khoe"]
    d = M.doc_da_cai(moi)["2.0.1"]
    assert d["ban_truoc"] == "2.0.0" and d["so_phat_hanh"] == 2 and d["ban_toi_thieu_ha_cap"] == "2.0.0" and os.path.exists(d["sao_luu_truoc"])
    assert he.kho.bao_cao_ds[-1][:3] == ("nang-cap", "2.0.0", "2.0.1")
    assert N.lich_su(moi)[-1]["trang_thai"] == "xong"
    assert not os.path.exists(N._duong_goi(moi, j))                                   # don goi da tai
    h = M.hien_tai(moi)
    assert h["phien_ban"] == "2.0.1" and h["so_phat_hanh"] == 2


def test_nang_cap_tuan_tu_len_ban_ke_tiep(he):
    moi, ts = san_sang(he)
    chay_xong = (N.bat_dau_nang_cap(moi), chay(moi))[1]
    assert chay_xong["trang_thai"] == "xong"
    he.t[0] += 10
    ts2 = M.kiem_tra(moi, bat_buoc=True)
    assert ts2["ban_ke_tiep"]["phien_ban"] == "2.0.2"
    j2 = (N.bat_dau_nang_cap(moi), chay(moi))[1]
    assert j2["trang_thai"] == "xong" and PH.hien_tai(he.opt) == "2.0.2"


# ====================================================================================== dieu kien chan
def test_chan_khi_pxe_dang_chay_nhung_cho_phep_xac_nhan(he):
    moi, _ = san_sang(he, pxe_dang_bat_fn=lambda: True)
    with pytest.raises(N.LoiNangCap, match="PXE"):
        N.bat_dau_nang_cap(moi)
    job = N.bat_dau_nang_cap(moi, {"bo_qua_pxe": True})
    assert any("PXE" in c for c in job["canh_bao"])


def test_chan_khi_het_cho_hoac_thieu_khoa_may_hoac_khong_co_ban(he):
    moi, _ = san_sang(he, dung_luong_trong_fn=lambda d: 1 << 20)
    with pytest.raises(N.LoiNangCap, match="chỗ trống"):
        N.bat_dau_nang_cap(moi)
    moi2 = he.moi()
    M.kiem_tra(moi2, bat_buoc=True)
    M.kho = M.__dict__["kho"] if False else None
    ts = M.trang_thai(moi2)
    moi2.kho_json("trang-thai.json", {}).sua(lambda d: d.update(co_khoa_may=False))
    with pytest.raises(N.LoiNangCap, match="khóa riêng"):
        N.bat_dau_nang_cap(moi2)
    moi3 = he.moi()
    moi3.kho_json("trang-thai.json", {}).ghi({"hoi_luc": 1})
    with pytest.raises(N.LoiNangCap, match="Không có bản kế tiếp"):
        N.bat_dau_nang_cap(moi3)


def test_khong_bam_hai_lan(he):
    moi, _ = san_sang(he)
    N.bat_dau_nang_cap(moi)
    with pytest.raises(N.LoiNangCap, match="chưa kết thúc"):
        N.bat_dau_nang_cap(moi)
    with N.khoa_chay(moi):
        assert N.dang_chay(moi)
        with pytest.raises(N.LoiNangCap, match="khác chạy"):
            N.chay_job(moi)


# ====================================================================================== loi o tung buoc
def chay_loi(he, truoc_khi=None):
    moi, _ = san_sang(he)
    if truoc_khi:
        truoc_khi(moi)
    N.bat_dau_nang_cap(moi)
    return moi, chay(moi)


def test_goi_tai_ve_sai_sha_thi_that_bai_khong_dong_vao_he_thong(he):
    he.kho.tai_hong = True
    moi, j = chay_loi(he)
    assert j["trang_thai"] == "that-bai" and "SHA-256" in j["ly_do"]
    assert PH.hien_tai(he.opt) == "2.0.0" and kiem_nhat_quan(he, moi) == "2.0.0" and not os.path.isdir(os.path.join(he.opt, "releases", "2.0.1"))
    assert "migration" not in he.nhat_ky and "ap_dung" not in he.nhat_ky


def test_goi_bi_sua_trong_danh_muc_hop_le_van_bi_chan(he):
    """Danh muc (da ky) khai sha256 cua goi GOC; ke tan cong thay goi khac (cung kich thuoc) -> sai sha256 -> chan."""
    raw = bytearray(open(he.goi["2.0.1"], "rb").read())
    raw[len(raw) // 2] ^= 1
    open(he.goi["2.0.1"], "wb").write(bytes(raw))
    moi, j = chay_loi(he)
    assert j["trang_thai"] == "that-bai" and PH.hien_tai(he.opt) == "2.0.0"


def test_goi_dung_sha_nhung_ky_sai_thi_chan_o_buoc_cai(he, tmp_path):
    """Ke tan cong co the thay ca goi LAN danh muc? Khong (danh muc ky). Nhung neu goi KY BANG KHOA LA ma sha trong danh muc khop (lo khoa phat hanh?) -> van kiem chu ky."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    priv2, pub2 = K.tao_cap_khoa()
    PH.tao_ban(he.nguon["2.0.1"], str(tmp_path / "gia-opt"))
    rd = str(tmp_path / "gia-opt" / "releases" / "2.0.1")
    p = str(tmp_path / "gia.cspkg")
    _m, dek = G.dong_goi(rd, {"phien_ban": "2.0.1", "so_phat_hanh": 2, "kien_truc": "amd64", "kenh": "on-dinh", "ban_truoc_bat_buoc": "2.0.0"},
                         Ed25519PrivateKey.from_private_bytes(priv2), he.ph_id, p)
    he.goi["2.0.1"], he.dek["2.0.1"] = p, dek
    import hashlib
    he.ban[0]["sha256_goi"] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    he.ghi_danh_muc(so_hieu=2)
    moi, j = chay_loi(he)
    assert j["trang_thai"] == "that-bai" and "KHÔNG hợp lệ" in j["ly_do"] and PH.hien_tai(he.opt) == "2.0.0"


@pytest.mark.parametrize("hook", ["migration", "ap_dung", "khoi_dong_lai"])
def test_loi_sau_khi_bat_dau_doi_ban_thi_tu_hoan_tac(he, hook):
    def hong(moi):
        he.hong[hook] = 1
    moi, j = chay_loi(he, hong)
    assert j["trang_thai"] == "da-hoan-tac", j["nhat_ky"][-4:]
    assert PH.hien_tai(he.opt) == "2.0.0" and kiem_nhat_quan(he, moi) == "2.0.0"
    assert not os.path.isdir(os.path.join(he.opt, "releases", "2.0.1"))              # ban hong khong de lai
    assert he.kho.bao_cao_ds[-1][0] == "hoan-tac"
    if hook == "migration":
        assert he.khoi_phuc_goi                                                      # du lieu tra ve tu ban sao luu
    assert he.nhat_ky[-2:] == ["khoi_dong_lai", "suc_khoe"]                          # hoan tac xong con kiem lai suc khoe


def test_suc_khoe_that_bai_thi_hoan_tac_va_ban_cu_khoe_lai(he):
    n = [0]

    def suc_khoe(ten):
        n[0] += 1
        return (PH.hien_tai(he.opt) == ten and ten == "2.0.0"), "gia lap"          # ban moi khong bao gio khoe, ban cu khoe
    moi, _ = san_sang(he, suc_khoe_fn=suc_khoe)
    N.bat_dau_nang_cap(moi)
    j = chay(moi)
    assert j["trang_thai"] == "da-hoan-tac" and "sức khỏe" in j["ly_do"].lower() and PH.hien_tai(he.opt) == "2.0.0"


def test_hoan_tac_cung_that_bai_thi_bao_can_xu_ly_tay_co_huong_dan(he):
    he.suc_khoe_ok = False                                       # ca ban moi lan ban cu deu khong khoe
    moi, j = chay_loi(he)
    assert j["trang_thai"] == "can-xu-ly-tay" and "console-system-release.py lui" in j["ly_do"] and "saoluu.py khoi-phuc" in j["ly_do"]
    assert PH.hien_tai(he.opt) == "2.0.0"


def test_huy_truoc_khi_doi_ban(he):
    moi, _ = san_sang(he)
    N.bat_dau_nang_cap(moi)
    N.huy(moi)
    j = chay(moi)
    assert j["trang_thai"] == "da-huy" and PH.hien_tai(he.opt) == "2.0.0" and "ap_dung" not in he.nhat_ky


# ====================================================================================== MAT DIEN o moi diem ghi
def chay_den_khi_sup(he, n, **kw):
    """Chay bo nang cap, MAT DIEN o lan ghi job thu n. Tra ve (moi, da_xong_khong_sup)."""
    moi, _ = san_sang(he, **kw)
    N.bat_dau_nang_cap(moi)
    goc = N._luu_job
    dem = [0]

    def luu(m, job):
        dem[0] += 1
        if dem[0] == n:
            raise SupDo("mat dien")
        return goc(m, job)
    N._luu_job = luu
    try:
        try:
            chay(moi)
            return moi, True
        except SupDo:
            return moi, False
    finally:
        N._luu_job = goc


@pytest.mark.parametrize("n", list(range(1, 40)))
def test_mat_dien_o_bat_ky_diem_ghi_nao_cung_ve_trang_thai_an_toan(tmp_path, n):
    he = He(tmp_path)
    moi, xong = chay_den_khi_sup(he, n)
    if xong:
        pytest.skip("khong con diem ghi thu %d" % n)
    # khoi dong lai may: dich vu phuc hoi
    hanh_dong, j = N.phuc_hoi(he.moi())
    assert hanh_dong in ("huy", "hoan-tac", "tiep-tuc", "hoan-tac-lai"), hanh_dong
    assert j["trang_thai"] in ("xong", "da-hoan-tac", "da-huy"), (n, hanh_dong, j["trang_thai"], j.get("ly_do"))
    cur = kiem_nhat_quan(he, moi)
    if j["trang_thai"] == "xong":
        assert cur == "2.0.1"
    else:
        assert cur == "2.0.0"
    N.phuc_hoi(he.moi())                                      # chay lai lan nua: khong lam gi them (idempotent)
    assert N.doc_job(he.moi())["trang_thai"] == j["trang_thai"]


def test_mat_dien_giua_luc_tai_goi_thi_tiep_tuc_tai_tiep(he):
    he.kho.dung_giua_chung = 5000
    moi, _ = san_sang(he)
    N.bat_dau_nang_cap(moi)
    with pytest.raises(SupDo):
        chay(moi)
    part = os.path.join(he.goc, "updates", "tai", "2.0.1-amd64.cspkg.part")
    assert 0 < os.path.getsize(part) <= 5000
    he.kho.dung_giua_chung = None
    hd, j = N.phuc_hoi(he.moi())
    assert hd == "huy" and j["trang_thai"] == "da-huy"                  # chua dong vao he thong -> huy an toan
    assert PH.hien_tai(he.opt) == "2.0.0"
    N.bat_dau_nang_cap(moi.__class__(**{}) if False else he.moi())      # bam lai
    j2 = chay(he.moi())
    assert j2["trang_thai"] == "xong" and PH.hien_tai(he.opt) == "2.0.1"       # goi .part cu duoc dung tiep (Range)


# ====================================================================================== C5: ha cap
def nang_len(he):
    moi, _ = san_sang(he)
    N.bat_dau_nang_cap(moi)
    assert chay(moi)["trang_thai"] == "xong"
    return moi


def test_ha_cap_ve_ban_truoc_khoi_phuc_du_lieu(he):
    moi = nang_len(he)
    he.nhat_ky.clear()
    job = N.bat_dau_ha_cap(moi)
    assert job["den"] == "2.0.0" and any("MẤT" in c for c in job["canh_bao"])
    j = chay(moi)
    assert j["trang_thai"] == "xong", j["nhat_ky"][-3:]
    assert PH.hien_tai(he.opt) == "2.0.0" and kiem_nhat_quan(he, moi) == "2.0.0"
    assert he.nhat_ky == ["sao_luu", "ap_dung", "khoi_phuc", "khoi_dong_lai", "suc_khoe"]
    assert he.khoi_phuc_goi[-1].endswith(".tar.gz") and "truoc-nang-cap" in he.khoi_phuc_goi[-1]
    assert "2.0.1" not in M.doc_da_cai(moi)
    assert he.kho.bao_cao_ds[-1][0] == "ha-cap"


def test_ha_cap_bi_chan_khi_khong_duoc_phep_hoac_thieu_ban(he):
    moi = nang_len(he)
    moi.kho_json("da-cai.json", {}).sua(lambda d: d["2.0.1"].update(ban_toi_thieu_ha_cap="2.0.1"))
    with pytest.raises(N.LoiNangCap, match="Không được hạ cấp"):
        N.bat_dau_ha_cap(moi)
    moi.kho_json("da-cai.json", {}).sua(lambda d: d["2.0.1"].update(ban_toi_thieu_ha_cap=None))
    with pytest.raises(N.LoiNangCap, match="không cho phép hạ cấp"):
        N.bat_dau_ha_cap(moi)
    moi.kho_json("da-cai.json", {}).sua(lambda d: d["2.0.1"].update(ban_toi_thieu_ha_cap="2.0.0"))
    PH.xoa_ban(os.path.join(he.opt, "releases", "2.0.0"))
    with pytest.raises(N.LoiNangCap, match="dọn khỏi máy"):
        N.bat_dau_ha_cap(moi)


def test_ha_cap_bi_chan_khi_ban_cu_khong_con_nguyen_ven(he):
    moi = nang_len(he)
    p = os.path.join(he.opt, "releases", "2.0.0", "app.py")
    os.chmod(p, 0o644)
    open(p, "a").write("sua")
    with pytest.raises(N.LoiNangCap, match="nguyên vẹn"):
        N.bat_dau_ha_cap(moi)


def test_ha_cap_loi_thi_quay_lai_ban_dang_chay(he):
    moi = nang_len(he)
    he.hong["khoi_phuc"] = 1
    N.bat_dau_ha_cap(moi)
    j = chay(moi)
    assert j["trang_thai"] == "da-hoan-tac" and PH.hien_tai(he.opt) == "2.0.1" and kiem_nhat_quan(he, moi) == "2.0.1"
    assert len(he.khoi_phuc_goi) >= 1 and "truoc-ha-cap" in he.khoi_phuc_goi[-1]            # tra du lieu hien tai tu ban sao luu luc bat dau ha cap


@pytest.mark.parametrize("n", list(range(1, 30)))
def test_mat_dien_trong_luc_ha_cap(tmp_path, n):
    he = He(tmp_path)
    moi = nang_len(he)
    N.bat_dau_ha_cap(moi)
    goc = N._luu_job
    dem = [0]

    def luu(m, job):
        dem[0] += 1
        if dem[0] == n:
            raise SupDo("mat dien")
        return goc(m, job)
    N._luu_job = luu
    try:
        try:
            chay(moi)
            pytest.skip("khong con diem ghi thu %d" % n)
        except SupDo:
            pass
    finally:
        N._luu_job = goc
    hd, j = N.phuc_hoi(he.moi())
    assert j["trang_thai"] in ("xong", "da-hoan-tac", "da-huy"), (n, hd, j["trang_thai"], j.get("ly_do"))
    cur = kiem_nhat_quan(he, moi)
    assert cur == ("2.0.0" if j["trang_thai"] == "xong" else "2.0.1")


@pytest.mark.parametrize("n", list(range(1, 45)))
def test_mat_dien_ngay_trong_luc_dang_hoan_tac(tmp_path, n):
    """Loi migration -> hoan tac; MAT DIEN o bat ky lan ghi nao (ke ca trong luc hoan tac) -> khoi dong lai van ve ban cu an toan."""
    he = He(tmp_path)
    he.hong["migration"] = 1
    moi, xong = chay_den_khi_sup(he, n)
    if xong:
        pytest.skip("khong con diem ghi thu %d" % n)
    he.hong.clear()
    hd, j = N.phuc_hoi(he.moi())
    assert j["trang_thai"] in ("da-hoan-tac", "da-huy"), (n, hd, j["trang_thai"], j.get("ly_do"))
    assert kiem_nhat_quan(he, moi) == "2.0.0"
