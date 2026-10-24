# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Quan ly may tram (UEM) - lop du lieu. Mo phong cac chuc nang cua OpenUEM (open-uem, Apache 2.0): kiem ke, bao mat,
trien khai, profiles, the (tag), ghi chu, metadata, dia diem... Cach lam KHAC OpenUEM o diem co ban: khong cai agent,
Console System tu vao may qua WinRM va lay bao cao dinh ky (xem uem_baocao.py).

Dung CHUNG kho may + tai khoan quan tri voi muc "Trien khai phan mem" (tk_dulieu.MAY / TAI_KHOAN). Moi may co them:
  tai_khoan_id  tai khoan dung de lay bao cao + chay tac vu      the            [id the]
  giam_sat      True/False (tuong ung Enabled/Disabled cua agent)  dia_diem      id dia diem (Site)
  bi_danh       ten goi tuy y (nickname)      ghi_chu      ghi chu markdown       loai   loai thiet bi (may ban/laptop/may chu...)
  metadata      {id_dinh_nghia: gia_tri}      bao_cao      bao cao day du (cau truc nhu AgentReport cua OpenUEM)
  bao_cao_luc   thoi diem lay bao cao cuoi    ket_noi      {"ok": bool, "loi": str, "luc": ts}
"""
from . import tk_dulieu as DL
from .tk_dulieu import Kho, moi_id, tim

THE = Kho("uem_the.json", [])                # [{id, ten, mau, mo_ta}]
METADATA = Kho("uem_metadata.json", [])      # [{id, ten, mo_ta}]  (dinh nghia truong tuy chinh cap to chuc)
DIA_DIEM = Kho("uem_dia_diem.json", [])      # [{id, ten, mo_ta}]
PROFILES = Kho("uem_profiles.json", [])      # [{id, ten, mo_ta, bat, ap_dung_tat_ca, the:[id], tasks:[...]}]
BAO_CAO_TAC_VU = Kho("uem_tac_vu.json", {})  # {may_id: [{luc, nguon, ten, ok, tb}]}  (lich su tac vu / task reports)
TRIEN_KHAI = Kho("uem_trien_khai.json", [])  # lich su cai/go/cap nhat WinGet [{luc, may_id, goi_id, ten_goi, hanh_dong, ok, tb}]
TRANG_THAI_PROFILE = Kho("uem_profile_tt.json", {})  # {profile_id: {may_id: {task_id: {ok, tb, luc, lan}}}}
CAI_DAT = Kho("uem_cai_dat.json", {})

MAC_DINH = {"tan_suat_bao_cao": 60, "tan_suat_profile": 30, "so_dong_trang": 10, "tu_dong_giam_sat": True,
            "tu_dong_cap_nhat_winget": True}


def cai_dat():
    d = dict(MAC_DINH)
    d.update(CAI_DAT.doc())
    return d


def luu_cai_dat(**kw):
    CAI_DAT.sua(lambda d: d.update(kw))


def ghi_tac_vu(may_id, nguon, ten, ok, tb):
    """Ghi 1 dong lich su tac vu cua may (toi da 200 dong/may)."""
    import time

    def ghi(d):
        ds = d.setdefault(may_id, [])
        ds.append({"luc": time.time(), "nguon": nguon, "ten": ten, "ok": bool(ok), "tb": str(tb)[:500]})
        del ds[:-200]
    BAO_CAO_TAC_VU.sua(ghi)


def sua_may(may_id, **kw):
    def ghi(ds):
        m = tim(ds, may_id)
        if m is not None:
            m.update(kw)
    DL.MAY.sua(ghi)


def may_theo_the(the_ids, tat_ca=False, nhom_ids=None):
    """May dang giam sat thuoc 'tat ca', hoac co 1 trong cac the, hoac nam trong 1 trong cac nhom may (DL.NHOM_MAY)."""
    ds = DL.MAY.doc()
    if tat_ca:
        return [m for m in ds if m.get("giam_sat", True)]
    cap = set(the_ids or [])
    trong_nhom = set()
    for g in DL.NHOM_MAY.doc():
        if g["id"] in set(nhom_ids or []):
            trong_nhom |= set(g.get("may", []))
    return [m for m in ds if m.get("giam_sat", True) and (cap & set(m.get("the", [])) or m["id"] in trong_nhom)]
