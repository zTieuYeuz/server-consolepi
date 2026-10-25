# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Sao luu / Khoi phuc 2.0 (buoc A5) - chi cho BO CUC MOI (/var/lib/console-system, xem duongdan.py/dichuyen.py).

Hai che do:
  cauhinh : config/ secrets/ pki/ data/ + deploy/kichban + deploy/apps/_thongtin.json + schema_version.json  (nho, vai MB)
  toanbo  : cauhinh + toan bo deploy/ + storage/                                                            (co the nhieu GB)

Goi = 1 file .tar.gz; MUC CUOI la `_console-system-sao-luu.json` (manifest: phien ban ma, schema du lieu, tung file + byte + sha256).
Khoi phuc: (1) kiem CA GOI tu dau den cuoi (ma bam tung file, ten an toan, khong link, khong file la) -> (2) tu chan neu goi
tu du lieu MOI hon ma -> (3) tu sao luu trang thai hien tai thanh MOT GOI CUNG DINH DANG (backups/truoc-khoiphuc-*.tar.gz) ->
(4) giai ra thu muc tam -> (5) doi thu muc nguyen tu; loi giua chung thi tra ve nhu cu.
Phan tac dong ra ngoai (Samba, nginx, khoi dong lai dich vu) nam o hau_khoi_phuc(), khong nam trong loi.
"""
import sys as _sys
_sys.modules["ui.saoluu"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import contextlib
import hashlib
import io
import json
import os
import queue
import shutil
import socket
import tarfile
import tempfile
import threading
import time

from ui import dichuyen as DM
from ui import duongdan as DD
from consolesystem.core import sqlite as SQ

DINH_DANG = 1
SAN_PHAM = "console-system"
TEN_MANIFEST = "_console-system-sao-luu.json"
PHAM_VI_CAUHINH = ("schema_version.json", "config", "secrets", "pki", "data", "deploy/kichban", "deploy/apps/_thongtin.json")
PHAM_VI_TOANBO = PHAM_VI_CAUHINH + ("deploy", "storage")
GOC_CHO_PHEP = {"schema_version.json", "config", "secrets", "pki", "data", "deploy", "storage"}
LOAI_TRU = ("data/trienkhai/cache",)           # bo nho tam, tai lai duoc
TEN_DB = "data/console.db"                    # co so du lieu SQLite dang chay: KHONG chep file song (WAL) ma dung ban chup nhat quan
TEP_DB_PHU = (TEN_DB + "-wal", TEN_DB + "-shm", TEN_DB + "-journal")
THU_MUC_THAY_CA_CAY = ("config", "secrets", "pki", "data")     # khoi phuc: thay nguyen cay
THU_MUC_GHEP = ("deploy", "storage")                            # khoi phuc toan bo: ghi de tung file, khong xoa file thua


class LoiSaoLuu(Exception):
    pass


def phien_ban_ma():
    for p in (DD.FILE_VERSION, DD.FILE_VERSION_DEV):
        with contextlib.suppress(OSError):
            return open(p, encoding="utf-8").read().strip()
    return "?"


def _bi_loai(arc):
    return arc.endswith((".tmp", ".lock", ".bak")) or ".hong-" in arc or any(arc == t or arc.startswith(t + "/") for t in LOAI_TRU)


def liet_ke(goc, che_do):
    """{arcname: duong that} cho file va [(arcname, duong)] cho thu muc. deploy/storage co the la lien ket -> theo ban that."""
    pham_vi = PHAM_VI_TOANBO if che_do == "toanbo" else PHAM_VI_CAUHINH
    files, dirs = {}, {}
    for muc in pham_vi:
        p = os.path.join(goc, muc)
        if not os.path.lexists(p):
            continue
        real = os.path.realpath(p)
        if os.path.isfile(real):
            files[muc] = real
            continue
        dirs[muc] = real
        for d, ds, fs in os.walk(real):
            rel = os.path.relpath(d, real)
            base = muc if rel == "." else muc + "/" + rel.replace(os.sep, "/")
            ds[:] = sorted(x for x in ds if not _bi_loai(base + "/" + x))
            for x in ds:
                dirs[base + "/" + x] = os.path.join(d, x)
            for f in sorted(fs):
                fp = os.path.join(d, f)
                if os.path.islink(fp) or _bi_loai(base + "/" + f) or (base + "/" + f) in (TEN_DB,) + TEP_DB_PHU:
                    continue
                files[base + "/" + f] = fp
    return files, dirs


class _DocBam:
    """Boc file de tinh sha256 + dem byte trong luc tarfile doc."""

    def __init__(self, f):
        self.f, self.h, self.n = f, hashlib.sha256(), 0

    def read(self, n=-1):
        b = self.f.read(n)
        self.h.update(b)
        self.n += len(b)
        return b


def _schema_hien_tai(goc):
    """Phien ban du lieu hien tai; file mat/hong (dang cuu du lieu) thi coi la 0 chu khong lam hong viec sao luu."""
    try:
        return DM.doc_phien_ban(goc)
    except DM.LoiDichuyen:
        return 0


def _ghi_tar(goc, che_do, fileobj, mode="w:gz"):
    tam_db = None
    try:
        files, dirs = liet_ke(goc, che_do)
        db = os.path.join(goc, TEN_DB)
        if os.path.exists(db):                       # ban chup nhat quan cua co so du lieu dang chay (API backup cua SQLite)
            tam_db = tempfile.mkdtemp(prefix=".sao-luu-db-", dir=goc)
            SQ.snapshot(db, os.path.join(tam_db, "console.db"))
            files[TEN_DB] = os.path.join(tam_db, "console.db")
        return _ghi_tar_ds(goc, che_do, fileobj, mode, files, dirs)
    finally:
        if tam_db:
            shutil.rmtree(tam_db, ignore_errors=True)


def _ghi_tar_ds(goc, che_do, fileobj, mode, files, dirs):
    ds_tep = []
    with tarfile.open(fileobj=fileobj, mode=mode) as tf:
        for arc in sorted(dirs):
            ti = tf.gettarinfo(dirs[arc], arcname=arc)
            tf.addfile(ti)
        for arc in sorted(files):
            try:
                ti = tf.gettarinfo(files[arc], arcname=arc)
                f = open(files[arc], "rb")
            except FileNotFoundError:
                continue                                  # tep tam bien mat giua luc liet ke va luc doc (khong dua vao goi)
            with f:
                doc = _DocBam(f)
                tf.addfile(ti, doc)
            if doc.n != ti.size:
                raise LoiSaoLuu("file doi trong luc sao luu (dung dich vu hoac thu lai): " + arc)
            ds_tep.append({"duong": arc, "byte": doc.n, "sha256": doc.h.hexdigest()})
        mf = {"dinh_dang": DINH_DANG, "san_pham": SAN_PHAM, "che_do": che_do, "phien_ban_ma": phien_ban_ma(),
              "schema": _schema_hien_tai(goc), "bo_cuc": "moi", "tao_luc": time.strftime("%Y-%m-%d %H:%M:%S"),
              "may": socket.gethostname(), "tep": ds_tep}
        nd = json.dumps(mf, ensure_ascii=False, indent=1).encode("utf-8")
        ti = tarfile.TarInfo(TEN_MANIFEST)
        ti.size, ti.mtime, ti.mode = len(nd), int(time.time()), 0o600
        tf.addfile(ti, io.BytesIO(nd))
    return mf


def tao_goi(goc, che_do, duong_ra):
    """Ghi goi ra file (ghi tam roi doi ten). Tra manifest."""
    if che_do not in ("cauhinh", "toanbo"):
        raise LoiSaoLuu("che do khong hop le: %s" % che_do)
    os.makedirs(os.path.dirname(os.path.abspath(duong_ra)), exist_ok=True)
    tam = duong_ra + ".tmp"
    fd = os.open(tam, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "wb") as f:
            mf = _ghi_tar(goc, che_do, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tam, duong_ra)
    except BaseException:
        with contextlib.suppress(OSError):
            os.remove(tam)
        raise
    return mf


def tao_luong(goc, che_do, kich_thuoc_khoi=1 << 20):
    """Generator bytes cho tai ve qua web (bo nho gioi han, khong ghi file tam). Ngat ket noi -> dung."""
    q, dung = queue.Queue(maxsize=8), threading.Event()

    class Ghi:
        def __init__(self):
            self.buf = bytearray()

        def write(self, b):
            if dung.is_set():
                raise LoiSaoLuu("nguoi dung da huy")
            self.buf += b
            if len(self.buf) >= kich_thuoc_khoi:
                q.put(bytes(self.buf))
                self.buf.clear()
            return len(b)

        def flush(self):
            pass

    def chay():
        g = Ghi()
        try:
            _ghi_tar(goc, che_do, g, "w|gz")
            if g.buf:
                q.put(bytes(g.buf))
            q.put(None)
        except BaseException as e:           # noqa: BLE001
            q.put(e)

    threading.Thread(target=chay, daemon=True).start()
    try:
        while True:
            x = q.get()
            if x is None:
                return
            if isinstance(x, BaseException):
                raise x
            yield x
    finally:
        dung.set()
        with contextlib.suppress(queue.Empty):
            while True:
                q.get_nowait()


def ten_goi(che_do):
    return "console-system-%s-%s.tar.gz" % ("cauhinh" if che_do == "cauhinh" else "toanbo", time.strftime("%Y%m%d-%H%M"))


def _ten_hop_le(ten):
    if not ten or ten.startswith("/") or "\x00" in ten:
        return False
    p = ten.split("/")
    if ".." in p or "" in p[:-1] or "." in p:
        return False
    return p[0] in GOC_CHO_PHEP


def kiem_goi(duong):
    """Doc het goi, kiem moi thu. Tra manifest; sai bat ky diem nao -> LoiSaoLuu (khong giai ra dau ca)."""
    try:
        tf = tarfile.open(duong, "r:gz")
    except (tarfile.TarError, OSError, EOFError) as e:
        raise LoiSaoLuu("khong mo duoc file sao luu: %s" % e)
    bam, mf = {}, None
    try:
        for tv in tf:
            if tv.name == TEN_MANIFEST:
                if not tv.isfile() or tv.size > 64 << 20:
                    raise LoiSaoLuu("manifest bat thuong")
                try:
                    mf = json.loads(tf.extractfile(tv).read().decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    raise LoiSaoLuu("manifest hong")
                continue
            if not _ten_hop_le(tv.name):
                raise LoiSaoLuu("ten khong an toan hoac ngoai pham vi: %r" % tv.name)
            if tv.isdir():
                continue
            if not tv.isfile():
                raise LoiSaoLuu("khong cho phep link/thiet bi trong goi: %r" % tv.name)
            h, n, f = hashlib.sha256(), 0, tf.extractfile(tv)
            for kh in iter(lambda: f.read(1 << 20), b""):
                h.update(kh)
                n += len(kh)
            bam[tv.name] = (n, h.hexdigest())
    except (tarfile.TarError, OSError, EOFError) as e:
        raise LoiSaoLuu("goi bi cat/hong: %s" % e)
    finally:
        tf.close()
    if mf is None:
        raise LoiSaoLuu("khong phai goi sao luu Console System (thieu manifest)")
    if mf.get("san_pham") != SAN_PHAM or mf.get("dinh_dang") != DINH_DANG or mf.get("bo_cuc") != "moi":
        raise LoiSaoLuu("goi khong cung dinh dang/san pham/bo cuc")
    khai = {t["duong"]: (t["byte"], t["sha256"]) for t in mf.get("tep", [])}
    if set(khai) != set(bam):
        thieu, thua = sorted(set(khai) - set(bam)), sorted(set(bam) - set(khai))
        raise LoiSaoLuu("danh sach file khong khop manifest (thieu %s, thua %s)" % (thieu[:3], thua[:3]))
    sai = sorted(k for k in khai if khai[k] != bam[k])
    if sai:
        raise LoiSaoLuu("%d file sai ma bam (goi bi sua/hong): %s" % (len(sai), ", ".join(sai[:5])))
    return mf


def _giai_ra(duong, dich, mf):
    kw = {"filter": "tar"} if hasattr(tarfile, "tar_filter") else {}
    with tarfile.open(duong, "r:gz") as tf:
        for tv in tf:
            if tv.name == TEN_MANIFEST:
                continue
            tf.extract(tv, dich, **kw)


def _cho_trong(thu_muc, can):
    os.makedirs(thu_muc, exist_ok=True)
    trong = shutil.disk_usage(thu_muc).free
    if trong < can * 1.1 + (64 << 20):
        raise LoiSaoLuu("khong du cho trong: can ~%d MB, con %d MB" % (can >> 20, trong >> 20))


def khoi_phuc(duong, goc=None):
    """Khoi phuc tu goi. Tra dict ket qua (goi_truoc = goi tu sao luu trang thai cu). Can dung dich vu ghi du lieu truoc."""
    goc = goc or DD.GOC
    if not os.path.exists(os.path.join(goc, DM.DAU_BO_CUC_MOI)):
        raise LoiSaoLuu("may chua o bo cuc moi - chay dichuyen.py bo-cuc-moi truoc")
    mf = kiem_goi(duong)
    biet = len(DM.MIGRATIONS)          # phien ban du lieu MA NAY hieu duoc (schema_version.json hien tai co the da mat/hong)
    if mf.get("schema", 0) > biet:
        raise LoiSaoLuu("goi tu du lieu MOI hon (schema %s > %s) - cap nhat Console System truoc" % (mf.get("schema"), biet))
    tong = sum(t["byte"] for t in mf["tep"])
    with DM._khoa(goc):
        _cho_trong(goc, tong * 2)
        truoc = os.path.join(goc, "backups", "truoc-khoiphuc-%s.tar.gz" % time.strftime("%Y%m%d-%H%M%S"))
        tao_goi(goc, "cauhinh", truoc)
        tam = tempfile.mkdtemp(prefix=".khoiphuc-", dir=goc)
        ben_canh = os.path.join(goc, ".truoc-khoiphuc-%d" % os.getpid())
        da_doi = []
        try:
            _giai_ra(duong, tam, mf)
            os.makedirs(ben_canh)
            for ten in THU_MUC_THAY_CA_CAY:
                moi = os.path.join(tam, ten)
                if not os.path.isdir(moi):
                    continue
                cu = os.path.join(goc, ten)
                if os.path.lexists(cu):
                    os.rename(cu, os.path.join(ben_canh, ten))
                    da_doi.append(("cay", ten))
                    for t in LOAI_TRU:                  # thu muc tam khong nam trong goi: giu lai, dung xoa
                        if t.split("/")[0] == ten and os.path.exists(os.path.join(ben_canh, t)):
                            os.makedirs(os.path.dirname(os.path.join(tam, t)), exist_ok=True)
                            shutil.copytree(os.path.join(ben_canh, t), os.path.join(tam, t), symlinks=True, dirs_exist_ok=True)
                os.rename(moi, cu)
            sv = os.path.join(tam, "schema_version.json")
            if os.path.isfile(sv):
                cu = os.path.join(goc, "schema_version.json")
                if os.path.exists(cu):
                    shutil.copy2(cu, os.path.join(ben_canh, "schema_version.json"))
                    da_doi.append(("tep", "schema_version.json"))
                os.replace(sv, cu)
            # deploy/kichban (thay ca thu muc) + deploy/apps/_thongtin.json: di qua ban THAT cua deploy (co the la lien ket)
            real_deploy = os.path.realpath(os.path.join(goc, "deploy"))
            kb = os.path.join(tam, "deploy", "kichban")
            if os.path.isdir(kb):
                cu = os.path.join(real_deploy, "kichban")
                os.makedirs(real_deploy, exist_ok=True)
                if os.path.lexists(cu):
                    os.rename(cu, os.path.join(ben_canh, "deploy-kichban"))
                    da_doi.append(("kichban", cu))
                shutil.move(kb, cu)
            tt = os.path.join(tam, "deploy", "apps", "_thongtin.json")
            if os.path.isfile(tt):
                dich = os.path.join(real_deploy, "apps", "_thongtin.json")
                os.makedirs(os.path.dirname(dich), exist_ok=True)
                if os.path.exists(dich):
                    luu = os.path.join(ben_canh, "ghep-thongtin")
                    shutil.copy2(dich, luu)
                    da_doi.append(("ghep", dich, luu))
                else:
                    da_doi.append(("moi", dich))
                os.replace(tt, dich)
            if mf["che_do"] == "toanbo":              # ghi de tung file, khong xoa file thua
                if os.path.isdir(os.path.join(tam, "deploy")):
                    _ghep(os.path.join(tam, "deploy"), real_deploy, ben_canh, da_doi)
                if os.path.isdir(os.path.join(tam, "storage")):
                    _ghep(os.path.join(tam, "storage"), os.path.realpath(os.path.join(goc, "storage")), ben_canh, da_doi)
        except BaseException:
            _tra_lai(goc, ben_canh, da_doi)
            raise
        finally:
            shutil.rmtree(tam, ignore_errors=True)
        shutil.rmtree(ben_canh, ignore_errors=True)
        SQ.lam_moi()                         # co so du lieu da doi file: moi luong phai mo lai ket noi
        DM._nhat_ky(goc, viec="khoi-phuc", tu=os.path.basename(duong), phien_ban_ma=mf.get("phien_ban_ma"), goi_truoc=truoc)
    return {"manifest": mf, "goi_truoc": truoc, "so_tep": len(mf["tep"])}


def _ghep(nguon, dich, ben_canh, da_doi, thay=()):
    """Ghi de tung file tu nguon vao dich (khong xoa file thua); file bi ghi de duoc ghi nho de tra lai neu loi."""
    kho = os.path.join(ben_canh, "ghep")
    for d, _ds, fs in os.walk(nguon):
        rel = os.path.relpath(d, nguon)
        if rel.split(os.sep)[0] in thay:
            continue
        for f in fs:
            src = os.path.join(d, f)
            dst = os.path.normpath(os.path.join(dich, rel, f))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.exists(dst):
                luu = os.path.join(kho, str(len(da_doi)))
                os.makedirs(kho, exist_ok=True)
                shutil.copy2(dst, luu)
                da_doi.append(("ghep", dst, luu))
            else:
                da_doi.append(("moi", dst))
            os.replace(src, dst)


def _tra_lai(goc, ben_canh, da_doi):
    for muc in reversed(da_doi):
        with contextlib.suppress(OSError):
            if muc[0] == "cay":
                ten = muc[1]
                cu = os.path.join(goc, ten)
                shutil.rmtree(cu, ignore_errors=True)
                os.rename(os.path.join(ben_canh, ten), cu)
            elif muc[0] == "tep":
                shutil.copy2(os.path.join(ben_canh, "schema_version.json"), os.path.join(goc, "schema_version.json"))
            elif muc[0] == "kichban":
                shutil.rmtree(muc[1], ignore_errors=True)
                os.rename(os.path.join(ben_canh, "deploy-kichban"), muc[1])
            elif muc[0] == "ghep":
                shutil.copy2(muc[2], muc[1])
            elif muc[0] == "moi":
                os.remove(muc[1])
    shutil.rmtree(ben_canh, ignore_errors=True)


def hau_khoi_phuc(goc=None):
    """Tac dong ra ngoai sau khoi phuc (KHONG thu duoc trong test): dong bo mat khau Samba, nap lai nginx. Tra danh sach thong bao."""
    import subprocess
    goc = goc or DD.GOC
    tb = []
    khoa = os.path.join(goc, "secrets", "samba-deploy.key")
    if os.path.isfile(khoa) and shutil.which("smbpasswd"):
        try:
            mk = open(khoa, encoding="utf-8").read().strip()
            r = subprocess.run(["smbpasswd", "-s", "-a", "consolepi-deploy"], input=f"{mk}\n{mk}\n", text=True, capture_output=True, timeout=20)
            tb.append("Samba: " + ("đã đồng bộ mật khẩu kho" if r.returncode == 0 else "không đồng bộ được mật khẩu kho"))
        except (OSError, subprocess.SubprocessError) as e:
            tb.append(f"Samba: lỗi {e}")
    if shutil.which("nginx"):
        t = subprocess.run(["nginx", "-t"], capture_output=True, text=True, timeout=20)
        if t.returncode == 0:
            subprocess.run(["systemctl", "reload-or-restart", "nginx"], capture_output=True, timeout=30)
            tb.append("nginx: đã nạp lại chứng chỉ")
        else:
            tb.append("nginx: cấu hình lỗi, KHÔNG nạp lại - " + (t.stderr or t.stdout)[-200:])
    return tb
