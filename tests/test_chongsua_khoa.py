"""C6: chong chinh sua (bang bam da ky) + khoa/mo khoa may ban tu dong."""
import json
import os
import stat
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from capnhat_gia import He, N, M, PH, K, viet  # noqa: E402

from consolesystem.core.capnhat import khoa_lenh as KL  # noqa: E402
from consolesystem.core.capnhat import nguyenven as NV  # noqa: E402

MK = "mat-khau-test-12345"


@pytest.fixture
def he(tmp_path):
    return He(tmp_path)


def len_2_0_1(he):
    moi = he.moi()
    M.kiem_tra(moi, bat_buoc=True)
    N.bat_dau_nang_cap(moi, {})
    j = N.chay_job(moi)
    assert j["trang_thai"] == "xong", j
    return moi


def sua(p, noi_dung):
    os.chmod(os.path.dirname(p), 0o755)
    os.chmod(p, 0o644)
    open(p, "wb").write(noi_dung)


# ================================================================================================ chong chinh sua
def test_ban_cai_tay_chua_co_chu_ky_khong_phai_loi(he):
    kq = NV.kiem(he.moi())
    assert kq["trang_thai"] == "chua-ky" and not kq["lech"]


def test_ban_cai_bang_goi_nguyen_ven_la_ok(he):
    moi = len_2_0_1(he)
    kq = NV.kiem(moi)
    assert kq["trang_thai"] == "ok" and kq["so_file"] >= 3 and kq["ban"] == "2.0.1"


@pytest.mark.parametrize("kieu", ["sua", "xoa", "them"])
def test_phat_hien_sua_xoa_them_file(he, kieu):
    moi = len_2_0_1(he)
    r = os.path.join(he.opt, "releases", "2.0.1")
    if kieu == "sua":
        sua(r + "/app.py", b"print('backdoor')\n")
    elif kieu == "xoa":
        os.chmod(r, 0o755)
        os.remove(r + "/app.py")
    else:
        os.chmod(r, 0o755)
        open(r + "/them.py", "w").write("x=1\n")
    kq = NV.kiem(moi)
    assert kq["trang_thai"] == "lech" and kq["lech"], kq
    assert any("app.py" in x or "them.py" in x for x in kq["lech"])


def test_sua_ca_release_json_van_bi_bat(he):
    """Ke sua file VA sua luon RELEASE.json cho khop: bang bam da KY van la nguon su that."""
    moi = len_2_0_1(he)
    r = os.path.join(he.opt, "releases", "2.0.1")
    sua(r + "/app.py", b"print('x')\n")
    rl = json.load(open(r + "/RELEASE.json"))
    rl["tep"]["app.py"] = PH._bam_file(r + "/app.py")
    sua(r + "/RELEASE.json", json.dumps(rl).encode())
    assert PH.kiem_ban(he.opt, "2.0.1") == []                         # kiem cu bi lua
    assert NV.kiem(moi)["trang_thai"] == "lech"                       # kiem co chu ky thi khong


def test_chu_ky_luu_bi_sua_hoac_hong(he):
    moi = len_2_0_1(he)
    d = os.path.join(he.goc, "updates", "chu-ky", "2.0.1.json")
    luu = json.load(open(d))
    dau = json.loads(K.unb64(luu["dau"]))
    dau["manifest"]["tep"]["app.py"] = "0" * 64                    # ke sua bang bam trong manifest cho khop file da sua
    luu["dau"] = K.b64(K.chuan_json(dau))
    json.dump(luu, open(d, "w"))
    assert NV.kiem(moi)["trang_thai"] == "lech"
    open(d, "w").write("{hong")
    assert NV.kiem(moi)["trang_thai"] == "lech"


def test_khoa_tin_cay_het_han_thi_khong_ket_luan_bi_sua(he):
    moi = len_2_0_1(he)
    he.t[0] += 10 ** 8                                                 # tai lieu tin cay het han
    kq = NV.kiem(moi)
    assert kq["trang_thai"] == "khong-xac-minh" and not kq["lech"]


def test_nang_cap_bi_chan_khi_chuong_trinh_bi_sua_nhung_ha_cap_thi_khong(he):
    moi = len_2_0_1(he)
    he.ghi_danh_muc(so_hieu=2)
    sua(os.path.join(he.opt, "releases", "2.0.1", "app.py"), b"print('bi sua')\n")
    M.kiem_tra(moi, bat_buoc=True)
    chan, _cb, _ban = N.kiem_dieu_kien_nang_cap(moi, {})
    assert any("BỊ SỬA ĐỔI" in c for c in chan), chan
    chan2, _ = N.kiem_dieu_kien_ha_cap(moi, {})[:2]
    assert not any("BỊ SỬA ĐỔI" in c for c in chan2)


def test_bao_kho_dung_mot_lan(he):
    moi = len_2_0_1(he)
    sua(os.path.join(he.opt, "releases", "2.0.1", "app.py"), b"print('bi sua')\n")
    NV.kiem_va_ghi(moi, he.kho.bao_cao)
    NV.kiem_va_ghi(moi, he.kho.bao_cao)
    assert [x[0] for x in he.kho.bao_cao_ds].count("lech-ma-bam") == 1
    assert NV.doc_ket_qua(moi)["trang_thai"] == "lech"


# ================================================================================================ khoa / mo khoa
@pytest.fixture
def lenh_world(tmp_path):
    kd = str(tmp_path / "khoa-lenh")
    K.luu_cap_khoa(kd, "lenh-khoa", MK, n=2 ** 14)
    K.luu_cap_khoa(kd, "phat-hanh", MK, n=2 ** 14)
    priv = K.doc_khoa_rieng(kd + "/lenh-khoa.khoa-rieng.json", MK)
    pub, _ = K.doc_khoa_cong_khai(kd + "/lenh-khoa.khoa-cong-khai.json")
    ph = K.doc_khoa_rieng(kd + "/phat-hanh.khoa-rieng.json", MK)
    ph_pub, _ = K.doc_khoa_cong_khai(kd + "/phat-hanh.khoa-cong-khai.json")
    return {"priv": priv, "id": K.dau_van_tay(pub), "hl": [(K.dau_van_tay(pub), pub)], "ph": ph, "ph_id": K.dau_van_tay(ph_pub)}


class MoiGia:
    """Chi can thu_muc/kho_json/gio cho khoa_lenh."""

    def __init__(self, tmp, t=1_800_000_000.0):
        self.goc, self.t = str(tmp), [t]
        os.makedirs(self.goc + "/updates", exist_ok=True)

    thu_muc = property(lambda s: s.goc + "/updates")
    gio = lambda s: s.t[0]   # noqa: E731

    def kho_json(self, ten, mac_dinh):
        from consolesystem.core.store import KhoJson
        return KhoJson(os.path.join(self.thu_muc, ten), mac_dinh, mode=0o600, indent=1)


def bi_mat(tmp):
    d = tmp / "secrets"
    d.mkdir()
    ds = []
    for ten, nd in (("flask.key", b"khoa-flask-BI-MAT"), ("kho.json", b'{"token":"abc"}'), ("lon.bin", b"x" * 70000)):
        viet(str(d / ten), nd)
        ds.append(str(d / ten))
    return ds


def ky_lenh(w, token, so=1, **kw):
    return KL.tao_lenh_khoa(w["priv"], w["id"], KL.token_bam(token), so, bay_gio=1_800_000_000, **kw)


def test_khoa_roi_mo_bang_ma_chu_may(tmp_path, lenh_world):
    w, moi, files = lenh_world, MoiGia(tmp_path), bi_mat(tmp_path)
    pb, ma = ky_lenh(w, "TOK")
    lenh = KL.kiem_lenh(pb, w["hl"], "TOK", moi.gio())
    KL.khoa_may(moi, lenh, files)
    assert KL.dang_khoa(moi) and KL.trang_thai(moi)["trang_thai"] == "khoa"
    assert not os.path.exists(files[0]) and not os.path.exists(files[1])           # ban ro da xoa
    assert os.path.exists(files[2])                                                # file lon (>64KB) khong bi dung toi
    blob = open(moi.thu_muc + "/khoa-bi-mat.bin", "rb").read()
    assert b"khoa-flask-BI-MAT" not in blob and b"abc" not in blob
    assert ma.replace("-", "").encode() not in json.dumps(pb).encode()            # kho/lenh khong chua ma mo khoa
    with pytest.raises(KL.LoiKhoaLenh):
        KL.mo_khoa(moi, "AAAA-BBBB-CCCC-DDDD-EEEE-FFFF-GGGG-HHHH")                 # sai ma
    assert KL.dang_khoa(moi) and not os.path.exists(files[0])
    assert KL.mo_khoa(moi, ma.lower().replace("-", " ")) == 2                      # dung ma (chap nhan thuong/khoang trang)
    assert open(files[0], "rb").read() == b"khoa-flask-BI-MAT" and not KL.dang_khoa(moi)
    assert stat.S_IMODE(os.stat(files[0]).st_mode) == 0o600
    assert not os.path.exists(moi.thu_muc + "/khoa-bi-mat.bin")


def test_ma_tinh_lai_offline_va_moi_lenh_mot_ma(tmp_path, lenh_world):
    w = lenh_world
    pb, ma = ky_lenh(w, "TOK")
    id_lenh = json.loads(pb["noi_dung"])["id_lenh"]
    from consolesystem.core.capnhat import khoa as K2
    assert KL.hien_thi_ma(KL.ma_mo_khoa(K2._raw_priv(w["priv"]), id_lenh)) == ma
    pb2, ma2 = ky_lenh(w, "TOK", so=2)
    assert ma2 != ma
    moi = MoiGia(tmp_path)
    files = bi_mat(tmp_path)
    KL.khoa_may(moi, KL.kiem_lenh(pb2, w["hl"], "TOK", moi.gio()), files)
    with pytest.raises(KL.LoiKhoaLenh):
        KL.mo_khoa(moi, ma)                                                         # ma cua lenh KHAC khong mo duoc


@pytest.mark.parametrize("loi", ["may-khac", "het-han", "tuong-lai", "ky-sai-khoa", "cu"])
def test_lenh_gia_bi_tu_choi(tmp_path, lenh_world, loi):
    w = lenh_world
    t = 1_800_000_000.0
    if loi == "ky-sai-khoa":
        pb, _ = KL.tao_lenh_khoa(w["ph"], w["ph_id"], KL.token_bam("TOK"), 1, bay_gio=int(t))
    elif loi == "may-khac":
        pb, _ = ky_lenh(w, "TOK-KHAC")
    else:
        pb, _ = ky_lenh(w, "TOK")
    gio, so_da = {"het-han": t + 8 * 86400, "tuong-lai": t - 3600}.get(loi, t), (5 if loi == "cu" else 0)
    with pytest.raises(KL.LoiKhoaLenh):
        KL.kiem_lenh(pb, w["hl"], "TOK", gio, so_da)


def test_lenh_bi_sua_noi_dung_bi_tu_choi(lenh_world):
    w = lenh_world
    pb, _ = ky_lenh(w, "TOK")
    d = json.loads(pb["noi_dung"])
    d["token_bam"] = KL.token_bam("TOK-KHAC")
    pb["noi_dung"] = K.chuan_json(d).decode()
    with pytest.raises(KL.LoiKhoaLenh):
        KL.kiem_lenh(pb, w["hl"], "TOK-KHAC", 1_800_000_000.0)


def test_phat_lai_lenh_cu_sau_khi_mo_khoa_bi_chan(tmp_path, lenh_world):
    w, moi, files = lenh_world, MoiGia(tmp_path), bi_mat(tmp_path)
    pb, ma = ky_lenh(w, "TOK")
    kq = KL.xu_ly_lenh(moi, [pb], w["hl"], "TOK", files)
    assert kq[0][1] == "da-khoa"
    KL.mo_khoa(moi, ma)
    kq = KL.xu_ly_lenh(moi, [pb], w["hl"], "TOK", files)                         # ke chep lai dung lenh cu de khoa lai
    assert kq[0][1].startswith("tu-choi") and not KL.dang_khoa(moi)


def test_mat_dien_giua_luc_khoa_hoan_tat_khi_khoi_dong(tmp_path, lenh_world):
    w, moi, files = lenh_world, MoiGia(tmp_path), bi_mat(tmp_path)
    pb, ma = ky_lenh(w, "TOK")
    lenh = KL.kiem_lenh(pb, w["hl"], "TOK", moi.gio())
    goc = KL._xoa_an_toan
    KL._xoa_an_toan = lambda p: (_ for _ in ()).throw(KeyboardInterrupt("mat dien"))
    try:
        with pytest.raises(KeyboardInterrupt):
            KL.khoa_may(moi, lenh, files)
    finally:
        KL._xoa_an_toan = goc
    assert KL.trang_thai(moi)["trang_thai"] == "dang-khoa" and os.path.exists(files[0])       # blob + trang thai da ghi TRUOC khi xoa
    KL.hoan_tat_khoa(moi)                                                                    # luc khoi dong lai
    assert KL.trang_thai(moi)["trang_thai"] == "khoa" and not os.path.exists(files[0])
    assert KL.mo_khoa(moi, ma) == 2 and open(files[0], "rb").read() == b"khoa-flask-BI-MAT"


def test_blob_bi_hong_thi_mo_that_bai_khong_mat_them(tmp_path, lenh_world):
    w, moi, files = lenh_world, MoiGia(tmp_path), bi_mat(tmp_path)
    pb, ma = ky_lenh(w, "TOK")
    KL.khoa_may(moi, KL.kiem_lenh(pb, w["hl"], "TOK", moi.gio()), files)
    p = moi.thu_muc + "/khoa-bi-mat.bin"
    raw = bytearray(open(p, "rb").read())
    raw[40] ^= 1
    open(p, "wb").write(bytes(raw))
    with pytest.raises(KL.LoiKhoaLenh):
        KL.mo_khoa(moi, ma)
    assert KL.dang_khoa(moi)


def test_kiem_tra_danh_muc_nhan_lenh_khoa_that(he, lenh_world, tmp_path):
    """Luong day du: kho tra lenh trong phan hoi danh muc -> may kiem -> khoa."""
    w = lenh_world
    goc_priv = K.doc_khoa_rieng(str(he.tmp / "khoa") + "/goc.khoa-rieng.json", MK)
    ph_pub, _ = K.doc_khoa_cong_khai(str(he.tmp / "khoa") + "/phat-hanh.khoa-cong-khai.json")
    lenh_pub = dict(w["hl"])[w["id"]]
    he.tin_cay = K.tao_tai_lieu_tin_cay(
        [{"vai_tro": "phat-hanh", "khoa_cong_khai": K.b64(ph_pub), "den": int(he.t[0]) + 10 ** 8},
         {"vai_tro": "lenh-khoa", "khoa_cong_khai": K.b64(lenh_pub), "den": int(he.t[0]) + 10 ** 8}],
        1, int(he.t[0]) + 10 ** 7, goc_priv, K.dau_van_tay(he.goc_pub), tu=int(he.t[0]) - 100)
    pb, ma = KL.tao_lenh_khoa(w["priv"], w["id"], KL.token_bam(he.token), 1, bay_gio=int(he.t[0]))
    goc_dm = he.kho.danh_muc
    he.kho.danh_muc = lambda kenh: dict(goc_dm(kenh), lenh=[pb])
    files = bi_mat(tmp_path)
    moi = he.moi()
    moi.xu_ly_lenh_fn = lambda cac, hl: KL.xu_ly_lenh(moi, cac, hl, he.token, files, bao_cao_fn=he.kho.bao_cao)
    ts = M.kiem_tra(moi, bat_buoc=True)
    assert not ts.get("loi") and not ts.get("canh_bao_lenh"), ts
    assert KL.dang_khoa(moi) and not os.path.exists(files[0])
    assert he.kho.bao_cao_ds[0][0] == "khoa"
    KL.mo_khoa(moi, ma)
    assert os.path.exists(files[0])


def test_man_hinh_may_bi_khoa_qua_web(tmp_path):
    import subprocess
    GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, os.path.join(GOC, "src"))
    from ui import dichuyen as DM
    goc = str(tmp_path / "cs")
    DM.tao_bo_cuc_moi(goc)
    open(os.path.join(goc, "secrets", "flask-secret.key"), "w").write("BI-MAT-FLASK")
    r = subprocess.run(["python3", os.path.join(GOC, "tests", "web_khoa_kichban.py")], capture_output=True, text=True,
                       env=dict(os.environ, CONSOLE_PI_DATA=goc), timeout=180)
    dong = [x for x in r.stdout.splitlines() if x.startswith("KETQUA ")]
    assert dong, r.stdout[-800:] + r.stderr[-1500:]
    kq = json.loads(dong[0][7:])
    assert all(kq.values()), kq
