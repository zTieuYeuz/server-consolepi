"""C7: tinh huong doi thuc con thieu - day o dia, bam dup, kho tat, dong ho lech, khong dang nhap."""
import errno
import json
import os
import subprocess
import sys
import threading

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from capnhat_gia import He, N, M, PH, G, kiem_nhat_quan  # noqa: E402


@pytest.fixture
def he(tmp_path):
    return He(tmp_path)


def san_sang(he, **kw):
    moi = he.moi(**kw)
    assert not M.kiem_tra(moi, bat_buoc=True).get("loi")
    return moi


def chay_job_moi(moi):
    N.bat_dau_nang_cap(moi)
    return N.chay_job(moi)


def test_day_o_dia_luc_tai_goi_that_bai_gon_va_thu_lai_duoc(he):
    moi = san_sang(he)
    goc = he.kho.tai_goi

    def day(*a, **k):
        raise OSError(errno.ENOSPC, "No space left on device")
    he.kho.tai_goi = day
    j = chay_job_moi(moi)
    assert j["trang_thai"] == "that-bai" and "space" in j["ly_do"].lower() or "dia" in j["ly_do"].lower() or "OSError" in j["ly_do"], j["ly_do"]
    assert PH.hien_tai(he.opt) == "2.0.0" and kiem_nhat_quan(he, moi) == "2.0.0"
    he.kho.tai_goi = goc                                                # giai phong cho -> thu lai thanh cong
    M.kiem_tra(moi, bat_buoc=True)
    assert chay_job_moi(moi)["trang_thai"] == "xong" and PH.hien_tai(he.opt) == "2.0.1"


def test_day_o_dia_luc_giai_nen_khong_de_lai_thu_muc_do(he):
    moi = san_sang(he)
    goc = G.giai_nen_an_toan

    def day(*a, **k):
        raise OSError(errno.ENOSPC, "No space left on device")
    G.giai_nen_an_toan = day
    try:
        j = chay_job_moi(moi)
    finally:
        G.giai_nen_an_toan = goc
    assert j["trang_thai"] in ("that-bai", "da-hoan-tac")
    assert PH.hien_tai(he.opt) == "2.0.0" and kiem_nhat_quan(he, moi) == "2.0.0"      # kiem_nhat_quan: khong con thu muc tam, ban chay con nguyen ven
    assert not os.path.isdir(os.path.join(he.opt, "releases", "2.0.1"))


def test_day_o_dia_luc_sao_luu_thi_dung_truoc_khi_doi_ban(he):
    def day(duong):
        raise OSError(errno.ENOSPC, "No space left on device")
    moi = san_sang(he, sao_luu_fn=day)
    j = chay_job_moi(moi)
    assert j["trang_thai"] in ("that-bai", "da-hoan-tac") and PH.hien_tai(he.opt) == "2.0.0"
    assert "ap_dung" not in he.nhat_ky and "migration" not in he.nhat_ky


def test_bam_dup_khong_tao_hai_job(he):
    moi = san_sang(he)
    N.bat_dau_nang_cap(moi)
    with pytest.raises(N.LoiNangCap):
        N.bat_dau_nang_cap(moi)                                           # bam lan 2 khi job dang cho
    j = N.chay_job(moi)
    assert j["trang_thai"] == "xong"
    assert N.chay_job(moi)["trang_thai"] == "xong"                        # chay lai job da xong: khong lam gi them
    assert he.nhat_ky.count("migration") == 1 and he.nhat_ky.count("khoi_dong_lai") == 1


def test_hai_bo_nang_cap_chay_cung_luc_chi_mot_duoc_lam(he):
    moi = san_sang(he)
    N.bat_dau_nang_cap(moi)
    vao, tiep = threading.Event(), threading.Event()

    def cham(duong):
        from capnhat_gia import viet
        viet(duong, b"SAO-LUU-GIA")
        vao.set()
        tiep.wait(10)
    moi2 = he.moi(sao_luu_fn=cham)
    kq = {}
    t = threading.Thread(target=lambda: kq.setdefault("a", N.chay_job(moi2)))
    t.start()
    assert vao.wait(10)
    try:
        N.chay_job(moi)                                                   # nguoi thu hai khi bo thu nhat dang giu khoa
        bi_chan = False
    except N.LoiNangCap as e:
        bi_chan = "khac chay" in str(e)
    finally:
        tiep.set()
        t.join(30)
    assert bi_chan
    assert kq["a"]["trang_thai"] == "xong" and he.nhat_ky.count("migration") == 1, (kq, he.nhat_ky)


def test_kho_tat_luc_kiem_tra_va_luc_tai(he):
    moi = he.moi()
    he.kho.loi_danh_muc = M.LoiKho("khong toi duoc kho (ConnectionError)")
    ts = M.kiem_tra(moi, bat_buoc=True)
    assert ts["loai_loi"] == "kho" and not M.co_ban_moi(moi)
    with pytest.raises(N.LoiNangCap):
        N.bat_dau_nang_cap(moi)                                           # khong co danh muc hop le -> khong cho nang cap
    he.kho.loi_danh_muc = None
    moi = san_sang(he)
    he.kho.tai_goi = lambda *a, **k: (_ for _ in ()).throw(M.LoiKho("kho tat giua chung"))
    j = chay_job_moi(moi)
    assert j["trang_thai"] == "that-bai" and "kho" in j["ly_do"].lower() and PH.hien_tai(he.opt) == "2.0.0"


@pytest.mark.parametrize("lech", [-3 * 86400, 3 * 86400, 8 * 86400])
def test_dong_ho_may_lech_nhieu(he, lech):
    moi = he.moi()
    gio_kho = int(he.t[0])                                                   # dong ho kho dung, dong ho MAY lech
    goc_dm = he.kho.danh_muc
    he.kho.danh_muc = lambda kenh: dict(goc_dm(kenh), gio_kho=gio_kho)
    he.t[0] += lech
    ts = M.kiem_tra(moi, bat_buoc=True)
    if abs(lech) >= 8 * 86400:
        assert ts["loai_loi"] == "an-ninh"                                   # danh muc het han / tuong lai
    elif lech < 0:
        assert ts["loai_loi"] == "an-ninh" or ts.get("co_ban_moi")           # lui it ngay: danh muc hoi tuong lai -> chan hoac chap nhan trong dung sai
    else:
        assert ts.get("co_ban_moi") and not ts.get("loi")                    # nhanh 3 ngay van trong han 7 ngay
    if ts.get("loi"):
        assert "Dong ho may lech" in ts["loi"], ts["loi"]                      # nguoi dung duoc chi ro nguyen nhan, khong chi 'khoa khong tin cay'


def test_bo_qua_phien_ban_phai_len_tuan_tu_khong_nhay_coc(he):
    moi = san_sang(he)
    he.ban[:] = [b for b in he.ban if b["phien_ban"] == "2.0.2"]            # kho chi quang cao 2.0.2 (yeu cau dang o 2.0.1)
    he.ghi_danh_muc(so_hieu=7)
    he.t[0] += 5
    ts = M.kiem_tra(moi, bat_buoc=True)
    assert ts["co_ban_moi"] and not ts.get("ban_ke_tiep")                    # co ban moi nhung KHONG cho nhay coc
    with pytest.raises(N.LoiNangCap):
        N.bat_dau_nang_cap(moi)
    assert PH.hien_tai(he.opt) == "2.0.0"


def test_ban_khong_dang_nhap_khong_vao_duoc_tab_cap_nhat(tmp_path):
    GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, os.path.join(GOC, "src"))
    from ui import dichuyen as DM
    goc = str(tmp_path / "cs")
    DM.tao_bo_cuc_moi(goc)
    r = subprocess.run(["python3", os.path.join(GOC, "tests", "web_quyen_kichban.py")], capture_output=True, text=True,
                       env=dict(os.environ, CONSOLE_PI_DATA=goc), timeout=180)
    dong = [x for x in r.stdout.splitlines() if x.startswith("KETQUA ")]
    assert dong, r.stdout[-800:] + r.stderr[-1500:]
    kq = json.loads(dong[0][7:])
    assert all(kq.values()), kq
