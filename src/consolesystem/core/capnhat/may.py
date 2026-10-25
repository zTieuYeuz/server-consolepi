# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
PHIA MAY KHACH cua he thong cap nhat (C3): cau hinh, hoi kho moi 24 gio, kiem danh muc, nho trang thai, bao "co ban moi" cho chuong.

Khong phu thuoc flask. Moi thu co tac dong ben ngoai (hoi kho, doc dong ho, thu muc) di qua doi tuong `Moi` de test duoc.
Khoa GOC (cong khai) duoc NHUNG trong ma: file `khoa_goc.json` canh module nay. Chua co khoa goc that -> cap nhat bi TAT va hien ro ly do
(khong bao gio "tam tin" mot khoa nao khac).
"""
import json
import os
import random
import time

from .. import duongdan as DD
from ..store import KhoJson, LoiDuLieu
from . import danhmuc as DM
from . import goi as G
from . import khoa as K

FILE_KHOA_GOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "khoa_goc.json")
CHU_KY_HOI = 24 * 3600
LECH_NGAU_NHIEN = 3600
KENH = G.KENH_HOP_LE


class LoiCapNhat(Exception):
    pass


class LoiKho(LoiCapNhat):
    """Kho khong tra loi / tu choi (mang, 401, 403...). `ma` = ma HTTP neu co."""

    def __init__(self, msg, ma=None):
        super().__init__(msg)
        self.ma = ma


def kien_truc_may():
    import platform
    m = platform.machine().lower()
    return {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64", "armv7l": "armhf", "armv6l": "armhf"}.get(m, m)


class Moi:
    """Moi truong chay: noi dat file + dong ho + kho. Ban that: Moi(kho=KhoHttp...). Test: Moi(goc=tmp, opt=tmp, kho=Gia())."""

    def __init__(self, goc=None, opt=None, kho=None, gio=time.time, khoa_goc=None, kien_truc=None, chay=None):
        from .. import phathanh as PH
        self.goc = goc or DD.GOC
        self.opt = opt or PH.GOC_OPT
        self.kho = kho
        self.gio = gio
        self._khoa_goc = khoa_goc
        self.kien_truc = kien_truc or kien_truc_may()
        self.chay = chay

    @property
    def thu_muc(self):
        d = os.path.join(self.goc, "updates")
        os.makedirs(d, exist_ok=True)
        return d

    def tep(self, ten):
        return os.path.join(self.thu_muc, ten)

    def kho_json(self, ten, mac_dinh):
        return KhoJson(self.tep(ten), mac_dinh, mode=0o600, indent=1)

    def khoa_goc(self):
        """Khoa cong khai GOC (raw 32 byte). Chua cau hinh -> LoiCapNhat ro rang."""
        if self._khoa_goc is not None:
            return self._khoa_goc
        env = os.environ.get("CS_KHOA_GOC_FILE")                       # chi dung de thu nghiem/phat trien
        duong = env or FILE_KHOA_GOC
        try:
            d = json.load(open(duong, encoding="utf-8"))
            if d.get("khoa_cong_khai"):
                return K.unb64(d["khoa_cong_khai"])
        except (OSError, ValueError, K.LoiKhoa):
            pass
        raise LoiCapNhat("Chua cau hinh KHOA GOC cua nha phat hanh trong ban nay - cap nhat tu dong bi tat de an toan.")


# ----------------------------------------------------------------------------------------------- cau hinh / hien tai
def cau_hinh(moi):
    d = {"kenh": "on-dinh", "hoi_dinh_ky": True, "kho_url": None, "kho_token": None}      # kho_url/kho_token: kho RIENG cho cap nhat (kho LAN thu nghiem); mac dinh dung kho trung tam
    d.update(moi.kho_json("cau-hinh.json", {}).doc())
    if d["kenh"] not in KENH:
        d["kenh"] = "on-dinh"
    return d


def luu_cau_hinh(moi, **kw):
    if "kenh" in kw and kw["kenh"] not in KENH:
        raise LoiCapNhat("kenh khong hop le")
    moi.kho_json("cau-hinh.json", {}).sua(lambda d: d.update(kw))


def doc_da_cai(moi):
    """{phien_ban: {so_phat_hanh, kien_truc, kenh, ban_truoc, ban_toi_thieu_ha_cap, luc}} cac ban da cai bang bo nang cap."""
    return moi.kho_json("da-cai.json", {}).doc()


def hien_tai(moi):
    """Ban DANG CHAY: phien_ban (VERSION cua current), so_phat_hanh (RELEASE.json hoac ban ghi da-cai), kien truc, kenh, ban_toi_thieu_ha_cap."""
    from .. import phathanh as PH
    cur = PH.hien_tai(moi.opt)
    pb = None
    for p in (os.path.join(moi.opt, "current", "VERSION"), DD.FILE_VERSION):
        try:
            pb = open(p, encoding="utf-8").read().strip()
            break
        except OSError:
            continue
    if not pb:
        raise LoiCapNhat("khong doc duoc phien ban dang chay")
    so, rl = 1, {}
    try:
        rl = json.load(open(os.path.join(moi.opt, "releases", cur or pb, PH.TEN_RELEASE), encoding="utf-8")) if cur else {}
        so = int(rl.get("so_phat_hanh", 1))
    except (OSError, ValueError):
        pass
    bd = doc_da_cai(moi).get(cur or pb, {})
    so = max(so, int(bd.get("so_phat_hanh", 0)))
    return {"phien_ban": pb, "ten_ban": cur or pb, "so_phat_hanh": so, "kien_truc": moi.kien_truc, "kenh": cau_hinh(moi)["kenh"],
            "ban_toi_thieu_ha_cap": bd.get("ban_toi_thieu_ha_cap")}


# ----------------------------------------------------------------------------------------------- trang thai kiem tra
def trang_thai(moi):
    return moi.kho_json("trang-thai.json", {}).doc()


def _luu_trang_thai(moi, **kw):
    moi.kho_json("trang-thai.json", {}).sua(lambda d: d.update(kw))


def den_han_hoi(moi):
    ts = trang_thai(moi)
    if not cau_hinh(moi)["hoi_dinh_ky"]:
        return False
    return moi.gio() >= ts.get("hoi_lan_sau", 0)


def kiem_tra(moi, bat_buoc=False):
    """Hoi kho (neu den han hoac bat_buoc), kiem tai lieu tin cay + danh muc, ghi trang thai. Tra ve trang thai. Loi mang KHONG nem ra
    ngoai (ghi vao trang thai 'loi') de luong nen khong chet; loi AN NINH (chu ky, het han, lui so hieu) cung duoc ghi ro."""
    if not bat_buoc and not den_han_hoi(moi):
        return trang_thai(moi)
    ts = trang_thai(moi)
    now = moi.gio()
    kq = {"hoi_luc": now, "hoi_lan_sau": now + CHU_KY_HOI + random.randint(0, LECH_NGAU_NHIEN), "loi": "", "loai_loi": ""}
    cur, cfg = None, cau_hinh(moi)
    try:
        cur = hien_tai(moi)
        pub_goc = moi.khoa_goc()
        if moi.kho is None:
            raise LoiCapNhat("Chua ket noi kho trung tam (can token kho) - vao Kho trung tam de ghep.")
        tra = moi.kho.danh_muc(cfg["kenh"])
        try:
            khoa_hl, so_tin_cay = K.khoa_hop_le(tra["tin_cay"], pub_goc, "phat-hanh", bay_gio=now, so_hieu_da_thay=ts.get("tin_cay_so_hieu", 0))
            dm = DM.mo_danh_muc(tra["danh_muc"], khoa_hl, cfg["kenh"], bay_gio=now, so_hieu_da_thay=ts.get("danh_muc_so_hieu", 0))
        except (K.LoiKhoa, G.LoiGoi) as e:
            lech = (tra.get("gio_kho") or now) - now
            goi_y = " (Dong ho may lech %+.1f gio so voi kho - hay chinh gio roi thu lai.)" % (lech / 3600) if abs(lech) > 3600 else ""
            raise LoiCapNhat("AN NINH: %s%s" % (e, goi_y))
        moi.kho_json("tin-cay.json", {}).ghi(tra["tin_cay"])
        fn_lenh = getattr(moi, "xu_ly_lenh_fn", None)
        if tra.get("lenh") and fn_lenh:
            try:
                fn_lenh(tra["lenh"], K.khoa_hop_le(tra["tin_cay"], pub_goc, "lenh-khoa", bay_gio=now)[0])
            except Exception as e:                                 # lenh hong/khong kiem duoc khong duoc lam hong viec kiem cap nhat
                kq["canh_bao_lenh"] = "%s: %s" % (type(e).__name__, e)           # da kiem chu ky goc: giu de buoc `cai` kiem lai khong can mang
        ke = DM.ban_ke_tiep(dm, cur["phien_ban"], cur["kien_truc"])
        kq.update({"tin_cay_so_hieu": so_tin_cay, "danh_muc_so_hieu": dm["so_hieu"], "danh_muc_het_han": dm["het_han"], "kenh": cfg["kenh"],
                   "co_ban_moi": DM.con_ban_moi_hon(dm, cur["phien_ban"], cur["kien_truc"]), "ban_ke_tiep": ke,
                   "ban_moi_nhat": max([b for b in dm["ban"] if b["kien_truc"] == cur["kien_truc"]], key=lambda b: b["so_phat_hanh"], default=None),
                   "co_khoa_may": bool(tra.get("co_khoa_may")), "danh_muc": dm["ban"]})
    except LoiKho as e:
        kq.update({"loi": "Khong hoi duoc kho: %s" % e, "loai_loi": "kho", "hoi_lan_sau": now + 3600})        # loi mang: thu lai sau 1 gio
    except LoiCapNhat as e:
        kq.update({"loi": str(e), "loai_loi": "an-ninh" if str(e).startswith("AN NINH") else "cau-hinh"})
    except LoiDuLieu as e:
        kq.update({"loi": "Loi du lieu: %s" % e, "loai_loi": "kho"})
    moi.kho_json("trang-thai.json", {}).sua(lambda d: (d.update(kq), [d.pop(k) for k in ("ban_ke_tiep", "ban_moi_nhat") if kq.get(k) is None and k in d]))
    return trang_thai(moi)


_nho_chuong = {"luc": 0.0, "co": False}


def co_ban_moi_nhanh(hieu_luc=30):
    """Cho chuong tren thanh tren: doc trang thai da luu, nho `hieu_luc` giay de khong doc dia o MOI trang."""
    t = time.time()
    if t - _nho_chuong["luc"] > hieu_luc:
        try:
            _nho_chuong["co"] = co_ban_moi(Moi())
        except Exception:
            _nho_chuong["co"] = False
        _nho_chuong["luc"] = t
    return _nho_chuong["co"]


def co_ban_moi(moi):
    """Nhanh, khong mang - cho chuong tren thanh tren (doc trang thai da luu)."""
    try:
        ts = trang_thai(moi)
        return bool(ts.get("co_ban_moi")) and not ts.get("loi")
    except LoiDuLieu:
        return False


# ----------------------------------------------------------------------------------------------- khoa goi theo may
def luu_khoa_may(moi_hoac_duong, khoa_may_b64):
    from ..store import ghi_nguyen_tu
    duong = moi_hoac_duong if isinstance(moi_hoac_duong, str) else DD.FILE_KHOA_MAY
    if len(K.unb64(khoa_may_b64)) != 32:
        raise LoiCapNhat("khoa_may sai do dai")
    ghi_nguyen_tu(duong, khoa_may_b64.encode("ascii"), 0o600)


def doc_khoa_may(duong=None):
    try:
        return K.unb64(open(duong or DD.FILE_KHOA_MAY, encoding="ascii").read().strip())
    except (OSError, K.LoiKhoa):
        return None


def mo_khoa_goi(khoa_may, token, pb, kt, kenh, boc):
    """Giai khoa goi (DEK) kho boc cho RIENG may nay. Khop kho/src/capnhat.py::boc_khoa_goi."""
    import hashlib
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aad = ("cspkg-khoa-goi|%s|%s|%s|%s" % (pb, kt, kenh, hashlib.sha256(token.encode()).hexdigest()[:16])).encode()
    try:
        return AESGCM(khoa_may).decrypt(K.unb64(boc["nonce"]), K.unb64(boc["ct"]), aad)
    except (InvalidTag, KeyError, K.LoiKhoa):
        raise LoiCapNhat("khong giai duoc khoa goi (sai khoa may / kho tra sai)")
