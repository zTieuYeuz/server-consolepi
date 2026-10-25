"""B1: consolesystem.core - esc (giu nguyen hanh vi cu), store (khong am tham mat du lieu), lenh, cauhinh."""
import json
import os
import sys
import threading

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))
from consolesystem.core import esc as E  # noqa: E402
from consolesystem.core import lenh as L  # noqa: E402
from consolesystem.core import store as S  # noqa: E402
from consolesystem.core.cauhinh import kho as kho_cauhinh  # noqa: E402


# ------------------------------------------------------------------ esc: moi bien the = dung hanh vi ban cu
CU_ESC = lambda s: (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))  # noqa: E731
CU_NONE = lambda s: (str(s if s is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))  # noqa: E731
GIA_TRI = [None, 0, 1, False, True, "", "a&b<c>d\"e'f", "Tiếng Việt <b>", 3.5, [1], "&amp;"]


@pytest.mark.parametrize("v", GIA_TRI)
def test_esc_bien_the_khop_ban_cu(v):
    import html
    from xml.sax.saxutils import escape
    assert E.esc(v) == CU_ESC(v)
    assert E.esc_none(v) == CU_NONE(v)
    assert E.esc_html(v) == html.escape(str(v if v is not None else ""), quote=True)
    assert E.esc_xml(v) == escape(str(v or ""))
    assert E.esc_html_rong(v) == html.escape(str(v or ""))


def test_esc_khac_nhau_dung_cho_can():
    assert E.esc(0) == "" and E.esc_none(0) == "0"
    assert "'" in E.esc("'") and "&#x27;" in E.esc_html("'") and E.esc_xml('"') == '"'


# ------------------------------------------------------------------ store
def test_ghi_doc_va_ban_du_phong(tmp_path):
    k = S.KhoJson(str(tmp_path / "d.json"), [])
    k.ghi([1])
    k.ghi([1, 2])
    assert k.doc() == [1, 2] and json.load(open(k.duong + ".bak")) == [1]
    assert not [x for x in os.listdir(tmp_path) if x.endswith(".tmp")]


def test_file_hong_co_bak_thi_khoi_phuc_va_giu_file_hong(tmp_path):
    k = S.KhoJson(str(tmp_path / "d.json"), [])
    k.ghi(["tot"])
    k.ghi(["tot", "moi"])
    open(k.duong, "w").write("{hong giua chung")
    truoc = len(S.canh_bao())
    assert k.doc() == ["tot"]                                                   # bak = ban hop le truoc do
    assert json.load(open(k.duong)) == ["tot"]
    hong = [x for x in os.listdir(tmp_path) if ".hong-" in x]
    assert len(hong) == 1 and open(tmp_path / hong[0]).read() == "{hong giua chung"      # khong mat bang chung
    assert len(S.canh_bao()) == truoc + 1


def test_file_hong_khong_bak_giu_lai_hong_va_khong_ghi_de(tmp_path):
    p = str(tmp_path / "d.json")
    open(p, "w").write("")                     # file rong: mat dien luc ghi
    k = S.KhoJson(p, [])
    assert k.doc() == []
    hong = [x for x in os.listdir(tmp_path) if ".hong-" in x]
    assert len(hong) == 1                                                         # file hong con do
    k.ghi([5])
    assert json.load(open(p)) == [5] and os.path.exists(tmp_path / hong[0])


def test_sai_kieu_bi_xem_la_hong(tmp_path):
    p = str(tmp_path / "d.json")
    open(p, "w").write('{"a": 1}')
    k = S.KhoJson(p, [])
    assert k.doc() == [] and [x for x in os.listdir(tmp_path) if ".hong-" in x]
    with pytest.raises(S.LoiDuLieu):
        k.ghi({"a": 1})


def test_loi_doc_that_khong_tra_rong(tmp_path, monkeypatch):
    p = str(tmp_path / "d.json")
    S.KhoJson(p, []).ghi([1])
    k = S.KhoJson(p, [])
    real_open = open

    def hong(f, *a, **kw):
        if f == p:
            raise PermissionError("khong co quyen")
        return real_open(f, *a, **kw)
    monkeypatch.setattr("builtins.open", hong)
    with pytest.raises(S.LoiDuLieu):
        k.doc()


def test_khong_co_file_thi_tra_mac_dinh_moi_lan_khac_nhau(tmp_path):
    k = S.KhoJson(str(tmp_path / "x.json"), {})
    a = k.doc()
    a["x"] = 1
    assert k.doc() == {}                       # khong dung chung doi tuong mac dinh


def test_sua_va_nhieu_luong(tmp_path):
    k = S.KhoJson(str(tmp_path / "d.json"), [])
    ts = [threading.Thread(target=lambda: [k.sua(lambda d: d.append(1)) for _ in range(30)]) for _ in range(5)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(k.doc()) == 150


def test_ghi_nguyen_tu_quyen_va_dir(tmp_path):
    p = str(tmp_path / "con" / "s.key")
    S.ghi_nguyen_tu(p, b"bi-mat", 0o600)
    assert open(p, "rb").read() == b"bi-mat" and os.stat(p).st_mode & 0o777 == 0o600


def test_bak_la_lien_ket_cung_khong_ton_them_dung_luong(tmp_path):
    k = S.KhoJson(str(tmp_path / "d.json"), [])
    k.ghi(list(range(1000)))
    k.ghi(list(range(1001)))
    assert os.stat(k.duong + ".bak").st_nlink == 1 and os.stat(k.duong).st_nlink == 1      # sau ghi thu hai bak giu inode cu rieng


def test_goi_sao_luu_khong_dua_bak_va_hong_vao(tmp_path):
    from ui import dichuyen as DM, saoluu as SL
    goc = str(tmp_path / "cs")
    DM.tao_bo_cuc_moi(goc)
    k = S.KhoJson(os.path.join(goc, "data", "may.json"), [])
    k.ghi([1])
    k.ghi([1, 2])
    open(os.path.join(goc, "data", "may.json.hong-20260101-000000"), "w").write("x")
    mf = SL.tao_goi(goc, "cauhinh", str(tmp_path / "g.tar.gz"))
    ten = [t["duong"] for t in mf["tep"]]
    assert "data/may.json" in ten and not [x for x in ten if ".bak" in x or ".hong-" in x] and SL.kiem_goi(str(tmp_path / "g.tar.gz"))


# ------------------------------------------------------------------ lenh
def test_lenh_chay_binh_thuong_va_ma_loi():
    r = L.chay(["sh", "-c", "echo xin; echo loi >&2; exit 3"])
    assert (r.rc, r.out.strip(), r.err.strip(), r.ok) == (3, "xin", "loi", False)


def test_lenh_het_gio_khong_nem_ngoai_le():
    r = L.chay(["sleep", "5"], timeout=0.3)
    assert r.rc == 124 and r.het_gio


def test_lenh_khong_ton_tai():
    r = L.chay(["lenh-khong-ton-tai-xyz"])
    assert r.rc == 127 and r.khong_chay_duoc


def test_lenh_check_va_chuoi_bi_cam():
    with pytest.raises(L.LoiLenh):
        L.chay(["false"], check=True)
    with pytest.raises(TypeError):
        L.chay("ls -l")


# ------------------------------------------------------------------ cau hinh
def test_cauhinh_quyen_0600_va_mot_doi_tuong_moi_duong_dan(tmp_path):
    p = str(tmp_path / "config.json")
    assert kho_cauhinh(p) is kho_cauhinh(p)
    kho_cauhinh(p).ghi({"terminal_auth": "u:p"})
    assert os.stat(p).st_mode & 0o777 == 0o600 and kho_cauhinh(p).doc() == {"terminal_auth": "u:p"}


def test_errlog_thao_tac_dung_ngu_canh_do_tang_web_dang_ky(tmp_path, monkeypatch):
    from consolesystem.core import errlog as EL
    monkeypatch.setattr(EL, "LOG_THAO_TAC", str(tmp_path / "tt.log"))
    monkeypatch.setattr(EL, "_NGU_CANH", None)
    EL.ghi_thao_tac("Hanh dong A")                                   # chua dang ky -> '-@-'
    EL.dat_ngu_canh(lambda: ("anh.thoai", "10.0.0.7"))
    EL.ghi_thao_tac("Hanh dong B", "chi tiet")
    EL.ghi_thao_tac("Hanh dong C", nguoi="khac")                      # truyen tay thang
    dong = open(tmp_path / "tt.log").read().splitlines()
    assert "| -@- | Hanh dong A" in dong[0] and "| anh.thoai@10.0.0.7 | Hanh dong B | chi tiet" in dong[1] and "| khac@10.0.0.7 | Hanh dong C" in dong[2]


def test_core_dich_vu_moi_khong_keo_flask():
    import subprocess
    r = subprocess.run(["python3", "-c", "import sys;sys.path.insert(0,'src');import consolesystem.core.errlog, consolesystem.core.tk_dulieu, consolesystem.core.phancung, consolesystem.core.magic_packet, consolesystem.core.token_tai, consolesystem.core.cauhinh;print('flask' in sys.modules)"],
                       cwd=GOC, capture_output=True, text=True)
    assert r.stdout.strip() == "False", r.stdout + r.stderr[-300:]
