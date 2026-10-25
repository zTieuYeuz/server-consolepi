# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Khung MIGRATION co so phien ban cho thu muc du lieu (2.0, buoc A2).

Chi dung thu vien chuan, KHONG import flask/ui -> chay duoc khi dich vu web chua len (dung luc nang cap).

Quy trinh cho MOI lan chay (run/undo):
  1. khoa chay (flock) - khong chay hai lan cung luc
  2. sao luu phan "nho" cua thu muc du lieu (bo qua deploy/, storage/, backups/, updates/ - nang, khong sua) -> backups/
  3. CHAY THU tren mot ban sao tam; loi la dung ngay, du lieu that chua bi dung toi
  4. chay that, TUNG buoc mot; sau moi buoc thanh cong ghi schema_version.json (ghi nguyen tu + fsync)
  5. loi giua chung -> tra du lieu ve dung nhu truoc khi chay (tu ban sao luu o buoc 2), phien ban khong doi
  6. moi viec ghi vao migrate.log (JSON moi dong)

Moi migration: (so_phien_ban, ten, up(ctx), down(ctx)); down co the la None (khong hoan tac duoc -> undo tu choi).
ctx.root = thu muc du lieu dang thao tac (ban sao khi chay thu); hay dung ctx.duong(...), ctx.doc_json/ghi_json.
"""
import contextlib
import fcntl
import json
import os
import shutil
import tarfile
import tempfile
import time

TEN_FILE_PHIEN_BAN = "schema_version.json"
TEN_NHAT_KY = "migrate.log"
THU_MUC_NANG = ("deploy", "storage", "backups", "updates")      # khong sao luu/khong chep thu
THU_MUC_SAO_LUU = "backups"


class LoiDichuyen(Exception):
    pass


class Ngu:
    """Ngu canh dua cho up()/down()."""

    def __init__(self, root):
        self.root = root

    def duong(self, *phan):
        return os.path.join(self.root, *phan)

    def doc_json(self, *phan, mac_dinh=None):
        try:
            with open(self.duong(*phan), encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return mac_dinh

    def ghi_json(self, *phan, data):
        ghi_nguyen_tu(self.duong(*phan), json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8"))


def ghi_nguyen_tu(duong, data, mode=0o600):
    """Ghi vao file tam, fsync, doi ten (mat dien giua chung khong de lai file nua voi)."""
    os.makedirs(os.path.dirname(duong) or ".", exist_ok=True)
    tam = duong + ".tmp"
    fd = os.open(tam, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tam, duong)
    with contextlib.suppress(OSError):
        dfd = os.open(os.path.dirname(duong) or ".", os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)


def doc_phien_ban(root):
    try:
        with open(os.path.join(root, TEN_FILE_PHIEN_BAN), encoding="utf-8") as f:
            return int(json.load(f).get("version", 0))
    except FileNotFoundError:
        return 0
    except (ValueError, OSError, AttributeError) as e:
        raise LoiDichuyen("schema_version.json hong, tu choi chay de khong lam hong them: %s" % e)


def _ghi_phien_ban(root, v):
    ghi_nguyen_tu(os.path.join(root, TEN_FILE_PHIEN_BAN),
                  json.dumps({"version": v, "cap_nhat": time.strftime("%Y-%m-%d %H:%M:%S")}).encode("utf-8"))


def _nhat_ky(root, **kv):
    kv["gio"] = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(os.path.join(root, TEN_NHAT_KY), "a", encoding="utf-8") as f:
            f.write(json.dumps(kv, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    except OSError:
        pass


@contextlib.contextmanager
def _khoa(root):
    os.makedirs(root, exist_ok=True)
    fd = os.open(os.path.join(root, ".migrate.lock"), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise LoiDichuyen("dang co mot lan migrate khac chay")
        yield
    finally:
        os.close(fd)


def _muc_nho(root):
    """Cac muc cap 1 cua thu muc du lieu se sao luu/khoi phuc (bo qua thu muc nang + khoa + file tam)."""
    for ten in sorted(os.listdir(root)):
        if ten in THU_MUC_NANG or ten == ".migrate.lock" or ten.endswith(".tmp"):
            continue
        yield ten


def sao_luu(root):
    os.makedirs(os.path.join(root, THU_MUC_SAO_LUU), exist_ok=True)
    duong = os.path.join(root, THU_MUC_SAO_LUU, "truoc-migrate-%s-%d.tgz" % (time.strftime("%Y%m%d-%H%M%S"), os.getpid()))
    with tarfile.open(duong, "w:gz") as t:
        for ten in _muc_nho(root):
            t.add(os.path.join(root, ten), arcname=ten)
    return duong


def khoi_phuc(root, tgz):
    """Dua phan nho cua thu muc du lieu ve DUNG nhu trong ban sao luu (xoa file moi sinh them)."""
    with tempfile.TemporaryDirectory(dir=root, prefix=".khoiphuc-") as tam:
        with tarfile.open(tgz) as t:
            t.extractall(tam, filter="tar") if hasattr(tarfile, "data_filter") else t.extractall(tam)
        for ten in list(_muc_nho(root)):
            if ten.startswith(".khoiphuc-"):
                continue
            p = os.path.join(root, ten)
            shutil.rmtree(p) if os.path.isdir(p) and not os.path.islink(p) else os.remove(p)
        for ten in os.listdir(tam):
            os.replace(os.path.join(tam, ten), os.path.join(root, ten))


def _ban_sao_thu(root):
    tam = tempfile.mkdtemp(prefix="migrate-thu-")
    for ten in _muc_nho(root):
        nguon, dich = os.path.join(root, ten), os.path.join(tam, ten)
        if os.path.isdir(nguon):
            shutil.copytree(nguon, dich, symlinks=True)
        else:
            shutil.copy2(nguon, dich)
    return tam


def _ds_hop_le(migrations):
    ds = sorted(migrations, key=lambda m: m[0])
    so = [m[0] for m in ds]
    if so != list(range(1, len(ds) + 1)):
        raise LoiDichuyen("so phien ban phai lien tuc 1..N, dang co: %s" % so)
    return ds


def _chay_chuoi(root, buoc, huong):
    """buoc: list (v, ten, ham). Chay lan luot; tra ve phien ban cuoi (huong 'len' = v, 'xuong' = v-1)."""
    ngu = Ngu(root)
    ket = None
    for v, ten, ham in buoc:
        if ham is None:
            raise LoiDichuyen("migration %d (%s) khong hoan tac duoc" % (v, ten))
        ham(ngu)
        ket = v if huong == "len" else v - 1
        _ghi_phien_ban(root, ket)
    return ket


def _thuc_hien(root, buoc, huong):
    with _khoa(root):
        tgz = sao_luu(root)
        _nhat_ky(root, viec=huong, buoc=[b[0] for b in buoc], sao_luu=tgz)
        tam = _ban_sao_thu(root)
        try:
            try:
                _chay_chuoi(tam, buoc, huong)
            except Exception as e:
                _nhat_ky(root, viec=huong, ket_qua="chay thu loi, du lieu that chua bi dung toi", loi=repr(e))
                raise LoiDichuyen("chay thu tren ban sao bi loi (du lieu that nguyen ven): %r" % (e,))
        finally:
            shutil.rmtree(tam, ignore_errors=True)
        try:
            ket = _chay_chuoi(root, buoc, huong)
        except Exception as e:
            khoi_phuc(root, tgz)
            _nhat_ky(root, viec=huong, ket_qua="loi giua chung, da khoi phuc", loi=repr(e))
            raise LoiDichuyen("loi giua chung, da tra du lieu ve nhu cu: %r" % (e,))
        _nhat_ky(root, viec=huong, ket_qua="xong", phien_ban=ket)
        return ket


def chay(root, migrations, den=None):
    """Len phien ban `den` (mac dinh: moi nhat). Khong con gi de lam -> tra phien ban hien tai, khong sao luu."""
    ds = _ds_hop_le(migrations)
    hien = doc_phien_ban(root) if os.path.isdir(root) else 0
    cuoi = den if den is not None else len(ds)
    if cuoi > len(ds) or cuoi < 0:
        raise LoiDichuyen("khong co phien ban %s" % cuoi)
    if hien > len(ds):
        raise LoiDichuyen("du lieu o phien ban %d moi hon ma (%d) - khong tu ha cap" % (hien, len(ds)))
    buoc = [(v, ten, up) for v, ten, up, _down in ds if hien < v <= cuoi]
    if not buoc:
        return hien
    return _thuc_hien(root, buoc, "len")


def hoan_tac(root, migrations, ve=None):
    """Lui ve phien ban `ve` (mac dinh: lui 1 buoc)."""
    ds = _ds_hop_le(migrations)
    hien = doc_phien_ban(root)
    dich = ve if ve is not None else max(hien - 1, 0)
    if dich >= hien:
        return hien
    buoc = [(v, ten, down) for v, ten, _up, down in reversed(ds) if dich < v <= hien]
    return _thuc_hien(root, buoc, "xuong")


# ------------------------------------------------------------- danh sach migration that cua san pham
def _m1_up(ngu):
    """Phien ban 1 = moc xuat phat (bo cuc du lieu cua 1.9.5). Khong doi gi, chi dong dau schema_version."""


MIGRATIONS = [
    (1, "moc-xuat-phat-1.9.5", _m1_up, lambda ngu: None),
]
