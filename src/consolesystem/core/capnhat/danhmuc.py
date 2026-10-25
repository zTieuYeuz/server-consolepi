# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
DANH MUC PHIEN BAN (C1): kho ky danh sach cac ban dang phat hanh cua tung kenh; may khach hoi dinh ky va chi tin danh muc:
  - co chu ky hop le cua khoa PHAT-HANH (tu tai lieu tin cay do khoa GOC ky)
  - CON HAN (het_han ngan, vd 7 ngay): chong "tan cong dong bang" - ke xau giu mai mot danh muc cu de may khong bao gio thay ban moi
  - so_hieu KHONG LUI so voi danh muc da thay (chong phat lai danh muc cu)
Ban ke tiep = ban co ban_truoc_bat_buoc = ban may dang chay (len TUAN TU, khong nhay cap).
"""
import time

from . import khoa as K
from .goi import KENH_HOP_LE, LoiGoi, khoa_phien_ban

HAN_MAC_DINH = 7 * 86400
CAC_TRUONG_BAN = ("phien_ban", "so_phat_hanh", "kien_truc", "kich_thuoc", "sha256_goi")


def tao_danh_muc(kenh, so_hieu, cac_ban, priv_phat_hanh, id_khoa, han=HAN_MAC_DINH, bay_gio=None):
    if kenh not in KENH_HOP_LE:
        raise LoiGoi("kenh khong hop le")
    bay_gio = int(bay_gio or time.time())
    for b in cac_ban:
        for t in CAC_TRUONG_BAN:
            if t not in b:
                raise LoiGoi("muc ban thieu truong %s" % t)
        khoa_phien_ban(b["phien_ban"])
    doc = {"loai": "danh-muc", "kenh": kenh, "so_hieu": so_hieu, "tao_luc": bay_gio, "het_han": bay_gio + han, "ban": cac_ban}
    return K.dong_goi_tai_lieu(doc, priv_phat_hanh, id_khoa)


def mo_danh_muc(phong_bi, khoa_hop_le, kenh, bay_gio=None, so_hieu_da_thay=0):
    """Kiem + tra ve dict danh muc. khoa_hop_le: [(id, pub_raw)]. Loi -> LoiGoi."""
    bay_gio = bay_gio or time.time()
    id_ky = phong_bi.get("khoa")
    pub = dict(khoa_hop_le).get(id_ky)
    if pub is None:
        raise LoiGoi("danh muc ky boi khoa %r khong nam trong khoa tin cay" % id_ky)
    try:
        d = K.mo_tai_lieu(phong_bi, pub)
    except K.LoiKhoa as e:
        raise LoiGoi("danh muc: %s" % e)
    if d.get("loai") != "danh-muc" or d.get("kenh") != kenh:
        raise LoiGoi("danh muc sai loai/kenh (can %s)" % kenh)
    if d["het_han"] < bay_gio:
        raise LoiGoi("danh muc DA HET HAN (nghi bi giu lai ban cu hoac kho khong phat hanh nua) - khong dung")
    if d["tao_luc"] > bay_gio + 300:
        raise LoiGoi("danh muc tao o TUONG LAI (dong ho may lech?) - khong dung")
    if d["so_hieu"] < so_hieu_da_thay:
        raise LoiGoi("danh muc CU hon ban da thay (%s < %s) - tu choi (chong phat lai)" % (d["so_hieu"], so_hieu_da_thay))
    return d


def ban_ke_tiep(danh_muc, phien_ban_hien_tai, kien_truc):
    """Ban MOI HON duy nhat may duoc phep len ngay (tuan tu); None neu da moi nhat. Danh muc ghi `ban_truoc_bat_buoc` cho tung ban."""
    ung = [b for b in danh_muc["ban"] if b["kien_truc"] == kien_truc and b.get("ban_truoc_bat_buoc") is not None
           and khoa_phien_ban(b["ban_truoc_bat_buoc"]) == khoa_phien_ban(phien_ban_hien_tai)]
    return max(ung, key=lambda b: b["so_phat_hanh"]) if ung else None


def con_ban_moi_hon(danh_muc, phien_ban_hien_tai, kien_truc):
    """Co ban moi hon (de hien chuong) ke ca khi chua len ngay duoc (phai qua ban trung gian)."""
    cu = khoa_phien_ban(phien_ban_hien_tai)
    return any(b["kien_truc"] == kien_truc and khoa_phien_ban(b["phien_ban"]) > cu for b in danh_muc["ban"])
