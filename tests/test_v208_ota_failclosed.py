"""2.0.8 V1-11: bo nang cap OTA fail-closed - (b) schema khong doc duoc khong coi la 0, (c) nut Huy khong bi ghi de, (d) san chong ha cap khong rot ve 1."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from test_nangcap import he, san_sang, chay, nang_len  # noqa: E402,F401
from capnhat_gia import N, M, PH  # noqa: E402


def test_c_huy_giua_luc_chay_van_co_tac_dung(he, monkeypatch):
    """Nguoi dung bam Huy trong luc bo nang cap DANG chay (sau buoc 'kiem'): truoc day co 'huy' bi ban job trong bo nho ghi de -> van doi ban."""
    moi, _ = san_sang(he)
    N.bat_dau_nang_cap(moi)
    goc = N._BUOC_NC["kiem"]

    def kiem_roi_huy(m, job):
        goc(m, job)
        assert N.huy(m)                                           # giao dien ghi co huy vao tep job khi bo nang cap dang o giua
    monkeypatch.setitem(N._BUOC_NC, "kiem", kiem_roi_huy)
    j = chay(moi)
    assert j["trang_thai"] == "da-huy", j["nhat_ky"][-3:]
    assert PH.hien_tai(he.opt) == "2.0.0" and "ap_dung" not in he.nhat_ky


def test_c_khong_huy_thi_van_nang_cap_binh_thuong(he):
    moi, _ = san_sang(he)
    N.bat_dau_nang_cap(moi)
    assert chay(moi)["trang_thai"] == "xong" and PH.hien_tai(he.opt) == "2.0.1"


def test_b_khong_doc_duoc_schema_thi_chan_ha_cap_khong_phai_cho_qua(he, monkeypatch):
    moi = nang_len(he)
    from consolesystem.core import dichuyen as DMG

    def hong(goc):
        raise OSError("khong doc duoc")
    monkeypatch.setattr(DMG, "doc_phien_ban", hong)
    with pytest.raises(N.LoiNangCap, match="Không kiểm được tương thích dữ liệu"):
        N.bat_dau_ha_cap(moi, {"khoi_phuc_du_lieu": False})                  # truoc day _schema_hien_tai tra 0 -> kiem tra tuong thich bi mo
    # doc duoc binh thuong thi hanh vi cu giu nguyen
    monkeypatch.undo()
    assert N.bat_dau_ha_cap(moi, {"khoi_phuc_du_lieu": False})["den"] == "2.0.0"


def test_d_san_so_phat_hanh_khong_roi_ve_1_khi_mat_release_json(he):
    moi, _ = san_sang(he)
    cur = M.hien_tai(moi)
    assert cur["so_phat_hanh"] >= 1
    rj = os.path.join(he.opt, "releases", cur["ten_ban"], PH.TEN_RELEASE)
    os.chmod(os.path.dirname(rj), 0o755)
    os.chmod(rj, 0o644)
    os.remove(rj)
    # co ban ghi da-cai -> van lay san tu do (khong hong)
    moi.kho_json("da-cai.json", {}).sua(lambda d: d.setdefault(cur["ten_ban"], {}).update(so_phat_hanh=7))
    assert M.hien_tai(moi)["so_phat_hanh"] == 7
    # khong co ca ban ghi da-cai -> TU CHOI (khong ha san ve 1)
    moi.kho_json("da-cai.json", {}).sua(lambda d: d.pop(cur["ten_ban"], None))
    with pytest.raises(M.LoiCapNhat, match="chống hạ cấp"):
        M.hien_tai(moi)


def test_N_release_json_hop_le_nhung_thieu_so_phat_hanh_thi_tu_choi(he):
    import json
    moi, _ = san_sang(he)
    cur = M.hien_tai(moi)
    rj = os.path.join(he.opt, "releases", cur["ten_ban"], PH.TEN_RELEASE)
    os.chmod(os.path.dirname(rj), 0o755)
    os.chmod(rj, 0o644)
    d = json.load(open(rj))
    d.pop("so_phat_hanh")
    json.dump(d, open(rj, "w"))
    moi.kho_json("da-cai.json", {}).sua(lambda x: x.pop(cur["ten_ban"], None))
    with pytest.raises(M.LoiCapNhat, match="chống hạ cấp"):
        M.hien_tai(moi)                                                           # truoc day: rot ve 1
    d["so_phat_hanh"] = [1]                                                       # sai kieu -> TypeError -> LoiCapNhat, khong 500
    json.dump(d, open(rj, "w"))
    with pytest.raises(M.LoiCapNhat):
        M.hien_tai(moi)
    moi.kho_json("da-cai.json", {}).sua(lambda x: x.setdefault(cur["ten_ban"], {}).update(so_phat_hanh="abc"))
    d["so_phat_hanh"] = 3
    json.dump(d, open(rj, "w"))
    with pytest.raises(M.LoiCapNhat, match="không hợp lệ"):
        M.hien_tai(moi)
