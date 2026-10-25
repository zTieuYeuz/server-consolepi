# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
KHOA / MO KHOA MAY BAN TU DONG (C6).

Luong: kho danh dau may nghi ngo (vd bao `lech-ma-bam`) -> CHU MAY duyet bang cach KY lenh voi khoa `lenh-khoa` (tren may build, mat khau rieng)
-> lenh nam trong phan hoi danh muc cua dung may do -> may kiem chu ky + han + so thu tu + dung may, roi:
  * ma hoa chi cac BI MAT NHO (khoa flask, token kho, khoa Samba, ...) bang khoa ngau nhien KS;
  * boc KS cho khoa cong khai P cua chu may (X25519, ma hoa kieu ECIES) roi QUEN KS; xoa ban ro cac bi mat do;
  * trang web chi con man hinh "May bi khoa" + o nhap ma mo khoa.
MA MO KHOA (160 bit) do chu may tinh LAI OFFLINE tu khoa `lenh-khoa` + id lenh; kho chi thay P (khong suy ra duoc ma). Moi lenh moi co P moi -> ma
dung MOT LAN. Ma sai khong giai duoc -> khong mo. Khong co kenh nao de kho mo khoa tu xa (chu y: tuc la mat ma + mat khoa lenh-khoa = mat bi mat da khoa).

GIOI HAN THANG THAN: khong khoa duoc o dia/du lieu lon (chi bi mat nho); ke co ROOT va dang giu may truoc khi lenh toi van lay duoc ban ro;
ke ngat mang khong bao gio nhan lenh. Day la lop lam kho cho viec dung tiep may bi mat/bi sao chep, khong phai hop dong bao mat tuyet doi.
"""
import base64
import hashlib
import json
import os
import time

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import serialization

from ..store import ghi_nguyen_tu
from . import khoa as K

TOI_DA_BI_MAT = 64 * 1024
HAN_TOI_DA = 14 * 86400
TEP_BLOB = "khoa-bi-mat.bin"
TEP_TRANG_THAI = "khoa-lenh.json"
DO_DAI_MA = 20                                                      # 160 bit


class LoiKhoaLenh(Exception):
    pass


def token_bam(token):
    """Dinh danh may trong lenh: khong lo token that, kho va may cung tinh duoc."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]


# ------------------------------------------------------------------------------------------------ ma mo khoa (phia chu may, offline)
def _master(priv_lenh_raw):
    return HKDF(hashes.SHA256(), 32, b"csmo-master", b"cs-mo-khoa-v1").derive(priv_lenh_raw)


def ma_mo_khoa(priv_lenh_raw, id_lenh):
    """20 byte xac dinh theo (khoa lenh-khoa, id lenh): chu may tinh lai bat cu luc nao, OFFLINE."""
    return HKDF(hashes.SHA256(), DO_DAI_MA, id_lenh.encode("ascii"), b"cs-mo-khoa-ma").derive(_master(priv_lenh_raw))


def hien_thi_ma(ma):
    s = base64.b32encode(ma).decode("ascii").rstrip("=")
    return "-".join(s[i:i + 4] for i in range(0, len(s), 4))


def doc_ma(chuoi):
    s = "".join(c for c in (chuoi or "").upper() if c.isalnum())
    try:
        ma = base64.b32decode(s + "=" * (-len(s) % 8))
    except (ValueError, TypeError):
        raise LoiKhoaLenh("ma mo khoa sai dinh dang")
    if len(ma) != DO_DAI_MA:
        raise LoiKhoaLenh("ma mo khoa sai do dai")
    return ma


def _khoa_x_tu_ma(ma):
    return X25519PrivateKey.from_private_bytes(HKDF(hashes.SHA256(), 32, b"cs-mo-khoa-x25519", b"v1").derive(ma))


def _raw(pub):
    return pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def tao_lenh_khoa(priv_lenh, id_khoa_ky, token_bam_hex, so_thu_tu, han_giay=7 * 86400, bay_gio=None):
    """(phong bi da ky, ma mo khoa dang chuoi). Chay tren may build (co khoa lenh-khoa)."""
    bay_gio = int(bay_gio or time.time())
    id_lenh = os.urandom(8).hex()
    ma = ma_mo_khoa(K._raw_priv(priv_lenh), id_lenh)
    p = _raw(_khoa_x_tu_ma(ma).public_key())
    doc = {"loai": "lenh-khoa", "hanh_dong": "khoa", "id_lenh": id_lenh, "token_bam": token_bam_hex, "so_thu_tu": int(so_thu_tu),
           "tao_luc": bay_gio, "het_han": bay_gio + min(han_giay, HAN_TOI_DA), "khoa_cong_khai_mo": K.b64(p)}
    return K.dong_goi_tai_lieu(doc, priv_lenh, id_khoa_ky), hien_thi_ma(ma)


# ------------------------------------------------------------------------------------------------ phia may
def _tep(moi, ten):
    return os.path.join(moi.thu_muc, ten)


def trang_thai(moi):
    return moi.kho_json(TEP_TRANG_THAI, {}).doc()


def dang_khoa(moi):
    return trang_thai(moi).get("trang_thai") in ("dang-khoa", "khoa")


def kiem_lenh(phong_bi, khoa_lenh_hop_le, token, bay_gio, so_da_thay=0, id_da_thay=()):
    """Tra ve dict lenh da kiem. Sai chu ky / het han / sai may / cu / lap -> LoiKhoaLenh."""
    id_ky = (phong_bi or {}).get("khoa")
    pub = dict(khoa_lenh_hop_le).get(id_ky)
    if pub is None:
        raise LoiKhoaLenh("lenh ky boi khoa %r khong phai khoa lenh-khoa tin cay" % id_ky)
    try:
        d = K.mo_tai_lieu(phong_bi, pub)
    except K.LoiKhoa as e:
        raise LoiKhoaLenh(str(e))
    if d.get("loai") != "lenh-khoa" or d.get("hanh_dong") != "khoa":
        raise LoiKhoaLenh("sai loai lenh")
    if d.get("token_bam") != token_bam(token):
        raise LoiKhoaLenh("lenh danh cho may khac")
    if not (d.get("tao_luc", 0) - 600 <= bay_gio <= d.get("het_han", 0)) or d["het_han"] - d["tao_luc"] > HAN_TOI_DA:
        raise LoiKhoaLenh("lenh het han hoac tao o tuong lai")
    if d.get("id_lenh") in id_da_thay or int(d.get("so_thu_tu", 0)) <= so_da_thay:
        raise LoiKhoaLenh("lenh cu/da dung (chong phat lai)")
    try:
        if len(K.unb64(d["khoa_cong_khai_mo"])) != 32:
            raise ValueError
    except (KeyError, ValueError, K.LoiKhoa):
        raise LoiKhoaLenh("lenh thieu khoa cong khai mo khoa")
    return d


def _doc_bi_mat(files):
    ra = {}
    for p in files:
        try:
            if os.path.isfile(p) and not os.path.islink(p) and os.path.getsize(p) <= TOI_DA_BI_MAT:
                ra[p] = K.b64(open(p, "rb").read())
        except OSError:
            continue
    return ra


def _xoa_an_toan(p):
    try:
        n = os.path.getsize(p)
        with open(p, "r+b") as f:                               # ghi de truoc khi xoa (tren SSD/FS co COW khong dam bao - da noi o gioi han)
            f.write(b"\0" * n)
            f.flush()
            os.fsync(f.fileno())
    except OSError:
        pass
    try:
        os.remove(p)
    except FileNotFoundError:
        pass


def khoa_may(moi, lenh, files):
    """Ap dung lenh KHOA da kiem. Co the chay lai an toan neu bi ngat giua chung (ghi truoc, xoa sau)."""
    st = moi.kho_json(TEP_TRANG_THAI, {})
    cu = st.doc()
    if cu.get("trang_thai") in ("dang-khoa", "khoa"):
        raise LoiKhoaLenh("may da o trang thai khoa")
    bi_mat = _doc_bi_mat(files)
    ks = os.urandom(32)
    nonce = os.urandom(12)
    blob = AESGCM(ks).encrypt(nonce, json.dumps(bi_mat).encode("utf-8"), lenh["id_lenh"].encode("ascii"))
    e = X25519PrivateKey.generate()
    kc = HKDF(hashes.SHA256(), 32, b"cs-khoa-boc", ("csmo|" + lenh["id_lenh"]).encode()).derive(e.exchange(X25519PublicKey.from_public_bytes(K.unb64(lenh["khoa_cong_khai_mo"]))))
    n2 = os.urandom(12)
    boc = AESGCM(kc).encrypt(n2, ks, lenh["id_lenh"].encode("ascii"))
    ghi_nguyen_tu(_tep(moi, TEP_BLOB), nonce + blob, 0o600)
    st.ghi({"trang_thai": "dang-khoa", "id_lenh": lenh["id_lenh"], "so_thu_tu": lenh["so_thu_tu"], "luc": int(moi.gio()), "files": sorted(bi_mat),
            "eph_pub": K.b64(_raw(e.public_key())), "nonce_boc": K.b64(n2), "boc": K.b64(boc),
            "so_lenh_da_thay": max(int(cu.get("so_lenh_da_thay", 0)), int(lenh["so_thu_tu"])), "id_da_thay": (cu.get("id_da_thay") or [])[-50:] + [lenh["id_lenh"]]})
    del ks, kc, e                                                # QUEN khoa: chi con ma mo khoa cua chu may giai duoc
    hoan_tat_khoa(moi)


def hoan_tat_khoa(moi):
    """Buoc 2: xoa ban ro cac bi mat da ma hoa. Chay lai khi khoi dong neu dang do (mat dien giua chung)."""
    st = moi.kho_json(TEP_TRANG_THAI, {})
    d = st.doc()
    if d.get("trang_thai") != "dang-khoa":
        return
    for p in d.get("files", []):
        _xoa_an_toan(p)
    st.sua(lambda x: x.update({"trang_thai": "khoa", "khoa_luc": int(moi.gio())}))


def mo_khoa(moi, ma_chuoi):
    """Nhap ma mo khoa -> giai ma, tra lai file bi mat, ket thuc trang thai khoa. Tra ve so file khoi phuc. Sai ma -> LoiKhoaLenh."""
    st = moi.kho_json(TEP_TRANG_THAI, {})
    d = st.doc()
    if d.get("trang_thai") not in ("khoa", "dang-khoa"):
        raise LoiKhoaLenh("may khong bi khoa")
    ma = doc_ma(ma_chuoi)
    try:
        kc = HKDF(hashes.SHA256(), 32, b"cs-khoa-boc", ("csmo|" + d["id_lenh"]).encode()).derive(
            _khoa_x_tu_ma(ma).exchange(X25519PublicKey.from_public_bytes(K.unb64(d["eph_pub"]))))
        ks = AESGCM(kc).decrypt(K.unb64(d["nonce_boc"]), K.unb64(d["boc"]), d["id_lenh"].encode("ascii"))
        raw = open(_tep(moi, TEP_BLOB), "rb").read()
        bi_mat = json.loads(AESGCM(ks).decrypt(raw[:12], raw[12:], d["id_lenh"].encode("ascii")))
    except (InvalidTag, ValueError, KeyError, OSError):
        raise LoiKhoaLenh("MA MO KHOA KHONG DUNG (hoac du lieu khoa bi hong)")
    for p, b in bi_mat.items():
        ghi_nguyen_tu(p, K.unb64(b), 0o600)
    st.sua(lambda x: x.update({"trang_thai": "mo", "mo_luc": int(moi.gio()), "boc": "", "eph_pub": "", "files": []}))
    try:
        os.remove(_tep(moi, TEP_BLOB))
    except FileNotFoundError:
        pass
    return len(bi_mat)


def xu_ly_lenh(moi, cac_lenh, khoa_lenh_hop_le, token, files, bao_cao_fn=None):
    """Goi tu luong kiem tra danh muc. Tra ve danh sach (id_lenh, ket_qua). Lenh hong bi bo qua + bao kho (neu co), KHONG nem ngoai le."""
    ra = []
    d = trang_thai(moi)
    for pb in cac_lenh or []:
        try:
            lenh = kiem_lenh(pb, khoa_lenh_hop_le, token, moi.gio(), d.get("so_lenh_da_thay", 0), d.get("id_da_thay") or [])
            if bao_cao_fn:
                bao_cao_fn("khoa", "", "", lenh["id_lenh"])      # bao TRUOC: sau khi khoa, token kho cung bi ma hoa nen khong bao duoc nua
            khoa_may(moi, lenh, files)
            ra.append((lenh["id_lenh"], "da-khoa"))
        except LoiKhoaLenh as e:
            ra.append(("?", "tu-choi: %s" % e))
    return ra
