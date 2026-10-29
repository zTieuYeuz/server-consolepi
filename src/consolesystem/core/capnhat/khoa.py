# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
KHOA KY (C0). Ed25519; khoa RIENG duoc ma hoa bang mat khau (scrypt + AES-256-GCM) khi cat xuong dia; may khach chi giu khoa CONG KHAI.

VAI TRO (tach rieng de lo mot khoa khong mat het - hoc tu khung TUF):
  goc        : cat NGOAI TUYEN, hiem dung; chi de ky "tai lieu tin cay" liet ke/thay cac khoa khac. Khoa cong khai cua no nam trong ma may khach.
  phat-hanh  : ky goi .cspkg va danh muc phien ban (dung thuong xuyen tren may build).
  lenh-khoa  : ky lenh khoa/mo khoa may (C6).
Mat khau khoa KHONG BAO GIO di qua tham so dong lenh (lo trong `ps`): doc tu bien moi truong CS_KHOA_MAT_KHAU hoac o nhap an (getpass).
"""
import base64
import hashlib
import json
import os
import time

from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

VAI_TRO = ("goc", "phat-hanh", "lenh-khoa")
BIEN_MAT_KHAU = "CS_KHOA_MAT_KHAU"
SCRYPT_N = 2 ** 15


class LoiKhoa(Exception):
    pass


def b64(b):
    return base64.b64encode(b).decode("ascii")


def unb64(s):
    try:
        return base64.b64decode(s.encode("ascii"), validate=True)
    except (ValueError, AttributeError) as e:
        raise LoiKhoa("chuoi base64 khong hop le: %s" % e)


def chuan_json(x):
    """Dang JSON CHUAN (khoa sap xep, khong khoang trang) - de ky va so sanh khong phu thuoc cach in."""
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def dau_van_tay(pub_raw):
    return hashlib.sha256(pub_raw).hexdigest()[:16]


def _raw_pub(pub):
    return pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def _raw_priv(priv):
    return priv.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())


def tao_cap_khoa():
    """(khoa rieng 32 byte, khoa cong khai 32 byte)."""
    k = Ed25519PrivateKey.generate()
    return _raw_priv(k), _raw_pub(k.public_key())


def lay_mat_khau(mat_khau=None, xac_nhan=False, vai_tro=None):
    """Mat khau tu tham so (chi cho test), bien moi truong CS_KHOA_MAT_KHAU_<VAI_TRO> hoac CS_KHOA_MAT_KHAU, hoac o nhap an.
    KHONG tu tham so dong lenh."""
    if mat_khau:
        return mat_khau
    v = (vai_tro and os.environ.get("%s_%s" % (BIEN_MAT_KHAU, vai_tro.upper().replace("-", "_")))) or os.environ.get(BIEN_MAT_KHAU)
    if v:
        return v
    import getpass
    v = getpass.getpass("Mat khau khoa ky: ")
    if xac_nhan and getpass.getpass("Nhap lai: ") != v:
        raise LoiKhoa("hai lan nhap mat khau khac nhau")
    if len(v) < 12:
        raise LoiKhoa("mat khau qua ngan (can tu 12 ky tu)")
    return v


def _khoa_tu_mat_khau(mat_khau, muoi, n):
    return Scrypt(salt=muoi, length=32, n=n, r=8, p=1).derive(mat_khau.encode("utf-8"))


def ma_hoa_khoa_rieng(priv_raw, mat_khau, vai_tro, n=SCRYPT_N):
    muoi, nonce = os.urandom(16), os.urandom(12)
    ct = AESGCM(_khoa_tu_mat_khau(mat_khau, muoi, n)).encrypt(nonce, priv_raw, b"cspkg-khoa-rieng-v1:" + vai_tro.encode())
    return {"dinh_dang": "cspkg-khoa-rieng", "v": 1, "vai_tro": vai_tro, "kdf": "scrypt", "n": n, "r": 8, "p": 1,
            "muoi": b64(muoi), "nonce": b64(nonce), "ct": b64(ct)}


def giai_ma_khoa_rieng(doc, mat_khau):
    if doc.get("dinh_dang") != "cspkg-khoa-rieng" or doc.get("v") != 1:
        raise LoiKhoa("khong phai file khoa rieng dung dinh dang")
    if not (2 ** 14 <= doc.get("n", 0) <= 2 ** 22):
        raise LoiKhoa("tham so scrypt khong hop le")
    try:
        raw = AESGCM(_khoa_tu_mat_khau(mat_khau, unb64(doc["muoi"]), doc["n"])).decrypt(
            unb64(doc["nonce"]), unb64(doc["ct"]), b"cspkg-khoa-rieng-v1:" + doc["vai_tro"].encode())
    except InvalidTag:
        raise LoiKhoa("sai mat khau hoac file khoa bi sua")
    return Ed25519PrivateKey.from_private_bytes(raw)


def luu_cap_khoa(thu_muc, vai_tro, mat_khau, n=SCRYPT_N):
    """Tao cap khoa cho `vai_tro`, ghi <vai_tro>.khoa-rieng.json (0600) va <vai_tro>.khoa-cong-khai.json. Tra ve dau van tay."""
    if vai_tro not in VAI_TRO:
        raise LoiKhoa("vai tro khong hop le: %s" % vai_tro)
    os.makedirs(thu_muc, mode=0o700, exist_ok=True)
    rieng, cong = os.path.join(thu_muc, vai_tro + ".khoa-rieng.json"), os.path.join(thu_muc, vai_tro + ".khoa-cong-khai.json")
    if os.path.exists(rieng):
        raise LoiKhoa("DA CO %s - khong ghi de khoa rieng (xoa tay neu that su muon tao lai)" % rieng)
    priv, pub = tao_cap_khoa()
    fd = os.open(rieng, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(ma_hoa_khoa_rieng(priv, mat_khau, vai_tro, n), f, indent=1)
        f.flush()
        os.fsync(f.fileno())
    with open(cong, "w", encoding="utf-8") as f:
        json.dump({"dinh_dang": "cspkg-khoa-cong-khai", "v": 1, "vai_tro": vai_tro, "khoa_cong_khai": b64(pub), "id": dau_van_tay(pub)}, f, indent=1)
    return dau_van_tay(pub)


def doc_khoa_rieng(duong, mat_khau):
    with open(duong, encoding="utf-8") as f:
        return giai_ma_khoa_rieng(json.load(f), mat_khau)


def doc_khoa_cong_khai(duong):
    with open(duong, encoding="utf-8") as f:
        d = json.load(f)
    return unb64(d["khoa_cong_khai"]), d.get("vai_tro")


def ky(priv, data):
    return priv.sign(data)


def xac_minh(pub_raw, data, chu_ky):
    try:
        Ed25519PublicKey.from_public_bytes(pub_raw).verify(chu_ky, data)
        return True
    except (InvalidSignature, ValueError):
        return False


# ------------------------------------------------------------------------------- tai lieu da ky
def dong_goi_tai_lieu(doc, priv, id_khoa):
    """Phong bi {noi_dung: <json chuan>, chu_ky, khoa}. Ky tren CHINH chuoi noi_dung (khong phu thuoc cach in lai)."""
    nd = chuan_json(doc)
    return {"noi_dung": nd.decode("utf-8"), "chu_ky": b64(ky(priv, b"CSDOC\0" + nd)), "khoa": id_khoa}


def mo_tai_lieu(phong_bi, pub_raw):
    """Kiem chu ky bang `pub_raw` roi tra ve dict. Sai -> LoiKhoa."""
    try:
        nd = phong_bi["noi_dung"].encode("utf-8")
        cs = unb64(phong_bi["chu_ky"])
    except (KeyError, AttributeError, TypeError):
        raise LoiKhoa("phong bì tài liệu thiếu trường")
    if not xac_minh(pub_raw, b"CSDOC\0" + nd, cs):
        raise LoiKhoa("chữ ký tài liệu KHÔNG hợp lệ")
    return json.loads(nd.decode("utf-8"))


def tao_tai_lieu_tin_cay(khoa_cong_khai, so_hieu, het_han, priv_goc, id_goc, tu=None):
    """Tai lieu tin cay do khoa GOC ky: liet ke cac khoa cong khai dang duoc phep theo vai tro (thay khoa khong phai cai lai may).
    khoa_cong_khai: [{"vai_tro", "khoa_cong_khai": b64, "den": ts}, ...]"""
    muc = []
    for k in khoa_cong_khai:
        if k["vai_tro"] not in VAI_TRO or k["vai_tro"] == "goc":
            raise LoiKhoa("tai lieu tin cay chi chua khoa phat-hanh/lenh-khoa")
        muc.append({"vai_tro": k["vai_tro"], "khoa_cong_khai": k["khoa_cong_khai"], "id": dau_van_tay(unb64(k["khoa_cong_khai"])),
                    "tu": k.get("tu", tu or int(time.time())), "den": k["den"]})
    return dong_goi_tai_lieu({"loai": "tin-cay", "so_hieu": so_hieu, "het_han": het_han, "khoa": muc}, priv_goc, id_goc)


def khoa_hop_le(tai_lieu_tin_cay, pub_goc, vai_tro, bay_gio=None, so_hieu_da_thay=0):
    """[(id, pub_raw)] cac khoa `vai_tro` con hieu luc theo tai lieu tin cay (da kiem chu ky goc, het han, so hieu khong lui)."""
    bay_gio = bay_gio or time.time()
    d = mo_tai_lieu(tai_lieu_tin_cay, pub_goc)
    if d.get("loai") != "tin-cay":
        raise LoiKhoa("không phải tài liệu tin cậy")
    if d["het_han"] < bay_gio:
        raise LoiKhoa("tài liệu tin cậy ĐÃ HẾT HẠN (nghi bị giữ lại tài liệu cũ) - cần làm mới từ kho")
    if d["so_hieu"] < so_hieu_da_thay:
        raise LoiKhoa("tài liệu tin cậy CŨ HƠN bản đã thấy (%s < %s) - từ chối" % (d["so_hieu"], so_hieu_da_thay))
    return [(k["id"], unb64(k["khoa_cong_khai"])) for k in d["khoa"] if k["vai_tro"] == vai_tro and k["tu"] <= bay_gio <= k["den"]], d["so_hieu"]
