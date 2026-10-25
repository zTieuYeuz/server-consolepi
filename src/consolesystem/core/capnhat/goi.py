# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
GOI CAP NHAT .cspkg (C1).

  MAGIC "CSPKG\\x01\\n" | u32 do dai dau | DAU (JSON chuan) | chu ky Ed25519 (64 byte) | cac KHOI ma hoa: u32 do dai | AES-256-GCM(khoi)

DAU (da ky): manifest {phien ban, so phat hanh, kien truc, kenh, ban truoc bat buoc, ghi chu, can khoi dong lai, migration, ban toi thieu ha cap,
sha256 TUNG FILE}, khoa ky, tham so ma hoa, tai trong {kich thuoc, sha256 cua tar.gz, so khoi}.
TAI TRONG = tar.gz cua cay `releases/<ban>/` (tar xac dinh: mtime 0, uid 0) ma hoa theo KHOI 1 MiB, nonce = tien to(8) + chi so khoi(4),
AAD = sha256(DAU) + chi so + co "khoi cuoi" -> chong doi thu tu / cat cut / ghep khoi tu goi khac / sua dau.

THU TU KIEM bat buoc truoc khi tin bat ky byte nao: chu ky dau (khoa phat-hanh trong tai lieu tin cay) -> dieu kien cai (kien truc, kenh, so phat hanh
chi tang, ban truoc bat buoc = tuan tu, khong nhay cap) -> giai ma tung khoi (tag) -> sha256 tong -> giai nen an toan (ten, loai, quyen) -> sha256 TUNG FILE = manifest.
"""
import contextlib
import hashlib
import json
import os
import re
import struct
import tarfile
import tempfile
import time

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .. import phathanh as PH
from . import khoa as K

MAGIC = b"CSPKG\x01\n"
KICH_THUOC_KHOI = 1 << 20
TOI_DA_DAU = 4 << 20
TOI_DA_GIAI_NEN = 4 << 30                      # tong dung luong sau giai nen toi da
TOI_DA_SO_FILE = 200000
KIEN_TRUC_HOP_LE = ("amd64", "arm64", "armhf")
KENH_HOP_LE = ("on-dinh", "thu-nghiem")
BAT_BUOC = ("phien_ban", "so_phat_hanh", "kien_truc", "kenh")


class LoiGoi(Exception):
    pass


# ----------------------------------------------------------------------------------------------- phien ban
def khoa_phien_ban(v):
    """'2.0.1' -> (2,0,1,0); '2.0.1-3' -> (2,0,1,3). Khong hop le -> LoiGoi."""
    m = re.fullmatch(r"(\d+(?:\.\d+){0,3})(?:-(\d+))?", str(v or ""))
    if not m:
        raise LoiGoi("phien ban khong hop le: %r" % (v,))
    so = [int(x) for x in m.group(1).split(".")]
    return tuple(so + [0] * (4 - len(so))) + (int(m.group(2) or 0),)


# ----------------------------------------------------------------------------------------------- dong goi
def _tar_xac_dinh(thu_muc, dich_file):
    """tar.gz xac dinh (mtime 0, uid/gid 0, sap xep) -> (kich thuoc, sha256). Chi file thuong + thu muc (liên kết bi bo qua)."""
    h, n = hashlib.sha256(), 0

    class Ghi:
        def write(self, b):
            nonlocal n
            h.update(b)
            n += len(b)
            return dich_file.write(b)

        def flush(self):
            dich_file.flush()

    def loc(ti):
        ti.mtime, ti.uid, ti.gid, ti.uname, ti.gname = 0, 0, 0, "", ""
        ti.mode = 0o755 if (ti.isdir() or ti.mode & 0o111) else 0o644
        return ti

    import gzip
    gz = gzip.GzipFile(fileobj=Ghi(), mode="wb", mtime=0, compresslevel=6)
    with tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tf:
        for d, ds, fs in os.walk(thu_muc):
            ds[:] = sorted(x for x in ds if x != "__pycache__")
            rel = os.path.relpath(d, thu_muc)
            if rel != ".":
                tf.add(d, arcname=rel, recursive=False, filter=loc)
            for f in sorted(fs):
                p = os.path.join(d, f)
                if os.path.islink(p):
                    continue
                tf.add(p, arcname=os.path.normpath(os.path.join(rel, f)), recursive=False, filter=loc)
    gz.close()
    return n, h.hexdigest()


def dong_goi(thu_muc_ban, thong_tin, priv_phat_hanh, id_khoa, dich, dek=None, kich_thuoc_khoi=KICH_THUOC_KHOI):
    """Dong goi `thu_muc_ban` (cay releases/<ban>) thanh `dich` (.cspkg). Tra ve (manifest, dek 32 byte).
    thong_tin: phien_ban, so_phat_hanh, kien_truc, kenh (+ ban_truoc_bat_buoc, ghi_chu, can_khoi_dong_lai, migration, ban_toi_thieu_ha_cap)."""
    for k in BAT_BUOC:
        if k not in thong_tin:
            raise LoiGoi("thieu truong bat buoc: %s" % k)
    khoa_phien_ban(thong_tin["phien_ban"])
    if thong_tin["kien_truc"] not in KIEN_TRUC_HOP_LE or thong_tin["kenh"] not in KENH_HOP_LE:
        raise LoiGoi("kien truc/kenh khong hop le")
    if not isinstance(thong_tin["so_phat_hanh"], int) or thong_tin["so_phat_hanh"] < 1:
        raise LoiGoi("so_phat_hanh phai la so nguyen duong")
    tep = PH.bam_cay(thu_muc_ban)
    if os.path.exists(os.path.join(thu_muc_ban, PH.TEN_RELEASE)):
        tep[PH.TEN_RELEASE] = PH._bam_file(os.path.join(thu_muc_ban, PH.TEN_RELEASE))
    if not tep:
        raise LoiGoi("cay phat hanh rong")
    manifest = {"dinh_dang": 1, "ten": "console-system-%s-%s" % (thong_tin["phien_ban"], thong_tin["kien_truc"]),
                "ban_truoc_bat_buoc": None, "ghi_chu": "", "can_khoi_dong_lai": True, "migration": [], "ban_toi_thieu_ha_cap": None,
                "tao_luc": int(time.time())}
    manifest.update(thong_tin)
    manifest["tep"] = tep
    dek = dek or os.urandom(32)
    tam = dich + ".tar.tmp"
    out_tam = dich + ".tmp"
    try:
        with open(tam, "wb") as f:
            kich_thuoc, sha = _tar_xac_dinh(thu_muc_ban, f)
        so_khoi = max(1, -(-kich_thuoc // kich_thuoc_khoi))
        tien_to = os.urandom(8)
        dau = {"dinh_dang": 1, "manifest": manifest, "khoa_ky": id_khoa,
               "mat_ma": {"thuat_toan": "AES-256-GCM", "khoi": kich_thuoc_khoi, "tien_to": K.b64(tien_to)},
               "tai_trong": {"kich_thuoc": kich_thuoc, "sha256": sha, "so_khoi": so_khoi}}
        dau_b = K.chuan_json(dau)
        cs = K.ky(priv_phat_hanh, b"CSPKG-HEADER\0" + dau_b)
        h_dau = hashlib.sha256(dau_b).digest()
        aes = AESGCM(dek)
        with open(out_tam, "wb") as out, open(tam, "rb") as src:
            out.write(MAGIC + struct.pack(">I", len(dau_b)) + dau_b + cs)
            for i in range(so_khoi):
                kh = src.read(kich_thuoc_khoi)
                cuoi = i == so_khoi - 1
                ct = aes.encrypt(tien_to + struct.pack(">I", i), kh, _aad(h_dau, i, cuoi))
                out.write(struct.pack(">I", len(ct)) + ct)
            out.flush()
            os.fsync(out.fileno())
        os.replace(out_tam, dich)
    finally:
        for p in (tam, out_tam):
            with contextlib.suppress(OSError):
                os.remove(p)
    return manifest, dek


def _aad(h_dau, i, cuoi):
    return h_dau + struct.pack(">I", i) + (b"\x01" if cuoi else b"\x00")


# ----------------------------------------------------------------------------------------------- doc / kiem
def doc_dau(f):
    """(dau dict, dau bytes, chu ky) tu file mo; kiem MAGIC/do dai. CHUA tin gi."""
    if f.read(len(MAGIC)) != MAGIC:
        raise LoiGoi("khong phai goi .cspkg (sai MAGIC)")
    raw = f.read(4)
    if len(raw) != 4:
        raise LoiGoi("goi bi cat cut (dau)")
    (n,) = struct.unpack(">I", raw)
    if not 2 <= n <= TOI_DA_DAU:
        raise LoiGoi("do dai dau khong hop le")
    dau_b = f.read(n)
    cs = f.read(64)
    if len(dau_b) != n or len(cs) != 64:
        raise LoiGoi("goi bi cat cut (dau/chu ky)")
    try:
        dau = json.loads(dau_b.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise LoiGoi("dau goi khong phai JSON")
    if dau.get("dinh_dang") != 1 or not isinstance(dau.get("manifest"), dict):
        raise LoiGoi("dau goi sai dinh dang")
    if K.chuan_json(dau) != dau_b:
        raise LoiGoi("dau goi khong o dang chuan (nghi bi sua/ghep)")
    return dau, dau_b, cs


def kiem_chu_ky(dau, dau_b, cs, khoa_hop_le):
    """khoa_hop_le: [(id, pub_raw)] (tu tai lieu tin cay). Tra ve id khoa da ky."""
    for id_, pub in khoa_hop_le:
        if id_ == dau.get("khoa_ky"):
            if K.xac_minh(pub, b"CSPKG-HEADER\0" + dau_b, cs):
                return id_
            raise LoiGoi("CHU KY KHONG HOP LE (goi bi sua hoac gia mao)")
    raise LoiGoi("khoa ky %r khong nam trong danh sach khoa tin cay hien hanh" % dau.get("khoa_ky"))


def giai_ma_ra_tar(f, dau, dau_b, dek, dich_tar):
    """Doc cac khoi tu `f` (dang o sau chu ky), giai ma + kiem tag tung khoi, ghi `dich_tar`; kiem tong kich thuoc va sha256."""
    mm = dau["mat_ma"]
    if mm.get("thuat_toan") != "AES-256-GCM" or not 4096 <= mm.get("khoi", 0) <= (16 << 20):
        raise LoiGoi("tham so ma hoa khong ho tro")
    tien_to, tt = K.unb64(mm["tien_to"]), dau["tai_trong"]
    if len(tien_to) != 8 or len(dek) != 32:
        raise LoiGoi("tien to nonce/khoa goi sai do dai")
    h_dau, aes, h, tong = hashlib.sha256(dau_b).digest(), AESGCM(dek), hashlib.sha256(), 0
    with open(dich_tar, "wb") as out:
        for i in range(tt["so_khoi"]):
            raw = f.read(4)
            if len(raw) != 4:
                raise LoiGoi("goi bi cat cut (khoi %d)" % i)
            (n,) = struct.unpack(">I", raw)
            if not 16 <= n <= mm["khoi"] + 16:
                raise LoiGoi("do dai khoi %d khong hop le" % i)
            ct = f.read(n)
            if len(ct) != n:
                raise LoiGoi("goi bi cat cut (khoi %d)" % i)
            try:
                kh = aes.decrypt(tien_to + struct.pack(">I", i), ct, _aad(h_dau, i, i == tt["so_khoi"] - 1))
            except InvalidTag:
                raise LoiGoi("khoi %d sai tag (goi bi sua / sai khoa goi / sai thu tu)" % i)
            h.update(kh)
            tong += len(kh)
            out.write(kh)
        if f.read(1):
            raise LoiGoi("con du lieu thua sau khoi cuoi")
    if tong != tt["kich_thuoc"] or h.hexdigest() != tt["sha256"]:
        raise LoiGoi("kich thuoc/sha256 tai trong khong khop dau goi")


def _ten_an_toan(ten):
    if not ten or ten.startswith("/") or "\x00" in ten or "\\" in ten:
        return False
    p = ten.split("/")
    return ".." not in p and "." not in p and "" not in p


def giai_nen_an_toan(tar_gz, dich, manifest):
    """Giai nen tar.gz vao thu muc `dich` (chua ton tai): CHI file thuong + thu muc, ten an toan, khong link, quyen chuan hoa,
    tong dung luong/so file co tran, sha256 TUNG FILE = manifest, khong thieu/khong thua file."""
    khai, thay, tong = manifest["tep"], set(), 0
    os.makedirs(dich, mode=0o755)
    with tarfile.open(tar_gz, "r:gz") as tf:
        for dem, tv in enumerate(tf, 1):
            if dem > TOI_DA_SO_FILE:
                raise LoiGoi("qua nhieu muc trong goi")
            if not _ten_an_toan(tv.name):
                raise LoiGoi("ten khong an toan trong goi: %r" % tv.name)
            p = os.path.join(dich, tv.name)
            if tv.isdir():
                os.makedirs(p, mode=0o755, exist_ok=True)
                continue
            if not tv.isfile():
                raise LoiGoi("loai muc khong cho phep (link/thiet bi): %r" % tv.name)
            if tv.name not in khai:
                raise LoiGoi("file KHONG co trong manifest: %r" % tv.name)
            tong += tv.size
            if tong > TOI_DA_GIAI_NEN:
                raise LoiGoi("dung luong giai nen vuot tran")
            os.makedirs(os.path.dirname(p), mode=0o755, exist_ok=True)
            h = hashlib.sha256()
            fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o755 if tv.mode & 0o111 else 0o644)
            with os.fdopen(fd, "wb") as out:
                src = tf.extractfile(tv)
                for kh in iter(lambda: src.read(1 << 20), b""):
                    h.update(kh)
                    out.write(kh)
            if h.hexdigest() != khai[tv.name]:
                raise LoiGoi("file %r SAI sha256 so voi manifest" % tv.name)
            thay.add(tv.name)
    thieu = sorted(set(khai) - thay)
    if thieu:
        raise LoiGoi("thieu %d file so voi manifest: %s" % (len(thieu), thieu[:3]))


# ----------------------------------------------------------------------------------------------- dieu kien cai
def kiem_dieu_kien_cai(manifest, hien_tai, ha_cap=False):
    """Tra ve danh sach ly do KHONG cai duoc (rong = duoc). hien_tai: {phien_ban, so_phat_hanh, kien_truc, kenh, ban_toi_thieu_ha_cap}."""
    loi = []
    if manifest["kien_truc"] != hien_tai["kien_truc"]:
        loi.append("sai kien truc (goi %s, may %s)" % (manifest["kien_truc"], hien_tai["kien_truc"]))
    if manifest["kenh"] != hien_tai["kenh"]:
        loi.append("sai kenh (goi %s, may %s)" % (manifest["kenh"], hien_tai["kenh"]))
    try:
        if ha_cap:
            if manifest["so_phat_hanh"] >= hien_tai["so_phat_hanh"]:
                loi.append("ha cap phai ve ban CU hon (so phat hanh %s >= %s)" % (manifest["so_phat_hanh"], hien_tai["so_phat_hanh"]))
            toi_thieu = hien_tai.get("ban_toi_thieu_ha_cap")
            if toi_thieu is None or khoa_phien_ban(manifest["phien_ban"]) < khoa_phien_ban(toi_thieu):
                loi.append("khong cho phep ha cap ve %s (ban thap nhat duoc phep: %s)" % (manifest["phien_ban"], toi_thieu))
        else:
            if manifest["so_phat_hanh"] <= hien_tai["so_phat_hanh"]:
                loi.append("goi CU hon hoac bang ban dang chay (so phat hanh %s <= %s) - chong phat lai ban cu" % (manifest["so_phat_hanh"], hien_tai["so_phat_hanh"]))
            bat_buoc = manifest.get("ban_truoc_bat_buoc")
            if bat_buoc is not None and khoa_phien_ban(bat_buoc) != khoa_phien_ban(hien_tai["phien_ban"]):
                loi.append("phai len TUAN TU: goi nay yeu cau dang o %s, may dang o %s (khong nhay cap)" % (bat_buoc, hien_tai["phien_ban"]))
    except LoiGoi as e:
        loi.append(str(e))
    return loi


def cai_goi(duong, dek, khoa_hop_le, hien_tai, thu_muc_releases, ha_cap=False):
    """Kiem + giai ma + giai nen goi vao `thu_muc_releases/<phien_ban>` (chua dung toi `current`). Tra ve (ten ban, manifest).
    Moi buoc loi -> LoiGoi va KHONG de lai thu muc do dang."""
    with open(duong, "rb") as f:
        dau, dau_b, cs = doc_dau(f)
        kiem_chu_ky(dau, dau_b, cs, khoa_hop_le)               # 1. chu ky TRUOC moi viec khac
        manifest = dau["manifest"]
        loi = kiem_dieu_kien_cai(manifest, hien_tai, ha_cap)  # 2. dieu kien cai (tuan tu, khong lui, kien truc, kenh)
        if loi:
            raise LoiGoi("; ".join(loi))
        ten = manifest["phien_ban"]
        dich = os.path.join(thu_muc_releases, ten)
        if os.path.exists(dich):
            raise LoiGoi("da co ban %s trong %s" % (ten, thu_muc_releases))
        os.makedirs(thu_muc_releases, exist_ok=True)
        tam = tempfile.mkdtemp(prefix=".cai-", dir=thu_muc_releases)
        try:
            tar = os.path.join(tam, "tai-trong.tar.gz")
            giai_ma_ra_tar(f, dau, dau_b, dek, tar)             # 3. giai ma + tag tung khoi + sha256 tong
            cay = os.path.join(tam, "cay")
            giai_nen_an_toan(tar, cay, manifest)                # 4. giai nen an toan + sha256 tung file
            if not os.path.isfile(os.path.join(cay, PH.TEN_RELEASE)):
                raise LoiGoi("thieu RELEASE.json trong goi")
            PH._khoa_chi_doc(cay)
            os.rename(cay, dich)
        finally:
            PH.xoa_ban(tam)
    return ten, manifest
