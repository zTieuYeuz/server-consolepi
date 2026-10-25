# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
BO NANG CAP / HA CAP (C4, C5): may trang thai BEN VUNG chay TACH KHOI giao dien (don vi systemd rieng), moi buoc ghi ra dia TRUOC khi lam
(write-ahead) nen khoi dong lai dich vu hay MAT DIEN giua chung van tiep tuc hoac tu hoan tac duoc.

NANG CAP (tuan tu, tung ban):
  kiem -> sao-luu (cau hinh, kiem lai) -> tai (tiep tuc duoc, kiem sha256) -> cai (chu ky + giai ma + giai nen + kiem tung file; CHUA dung toi ban dang chay)
  -> migration (du lieu da sao luu) -> doi-ban (current + console-system-apply) -> khoi-dong-lai -> suc-khoe -> hoan-tat
  Loi o bat ky buoc nao SAU khi bat dau doi ban/migration -> TU HOAN TAC: tra current ve ban cu, khoi phuc du lieu tu ban sao luu, khoi dong lai, kiem lai.
HA CAP 1 BAN: kiem (con ban cu nguyen ven, duoc phep, du lieu tuong thich) -> sao-luu -> doi-ban -> khoi-phuc-du-lieu -> khoi-dong-lai -> suc-khoe -> hoan-tat.
Moi viec co tac dong he thong di qua `MoiNangCap` (hook) de thu duoc bang gia lap ca ngat dien/hong o tung buoc.
"""
import contextlib
import fcntl
import hashlib
import json
import os
import shutil
import time

from .. import phathanh as PH
from ..store import ghi_nguyen_tu
from . import danhmuc as DM  # noqa: F401
from . import goi as G
from . import khoa as K
from . import may as M
from . import nguyenven as NV

BUOC_NANG_CAP = ("kiem", "sao-luu", "tai", "cai", "migration", "doi-ban", "khoi-dong-lai", "suc-khoe", "hoan-tat")
BUOC_HA_CAP = ("kiem", "sao-luu", "doi-ban", "khoi-phuc-du-lieu", "khoi-dong-lai", "suc-khoe", "hoan-tat")
KET_THUC = ("xong", "da-hoan-tac", "da-huy", "that-bai", "can-xu-ly-tay")
DUNG_LUONG_DU = 500 << 20
CHO_SUC_KHOE = 90


class LoiNangCap(M.LoiCapNhat):
    """Loi buoc nang cap. `hoan_tac`=True: nen tra ve ban cu (da dong vao he thong); False: huy sach se, khong co gi thay doi."""

    def __init__(self, msg, hoan_tac=False):
        super().__init__(msg)
        self.hoan_tac = hoan_tac


class MoiNangCap(M.Moi):
    """Moi + cac HOOK he thong. Mac dinh None -> phai gan (ban that: features/updates/thuc_te.py; test: gia lap)."""

    def __init__(self, *a, **kw):
        hooks = {k: kw.pop(k, None) for k in ("sao_luu_fn", "khoi_phuc_fn", "pxe_dang_bat_fn", "suc_khoe_fn", "khoi_dong_lai_fn", "ap_dung_fn",
                                              "migration_fn", "schema_fn", "token_fn", "dung_luong_trong_fn", "ngu")}
        khoa_may_duong = kw.pop("khoa_may_duong", None)
        super().__init__(*a, **kw)
        self.khoa_may_duong = khoa_may_duong or M.DD.FILE_KHOA_MAY
        self.__dict__.update({k: v for k, v in hooks.items() if v is not None})
        self.ngu = hooks["ngu"] or time.sleep
        self.dung_luong_trong_fn = hooks["dung_luong_trong_fn"] or (lambda d: shutil.disk_usage(d).free)
        self.pxe_dang_bat_fn = hooks["pxe_dang_bat_fn"] or (lambda: False)
        self.cho_suc_khoe = CHO_SUC_KHOE

    def hook(self, ten):
        f = getattr(self, ten, None)
        if f is None:
            raise LoiNangCap("thieu hook he thong: %s" % ten)
        return f


# ----------------------------------------------------------------------------------------------- job
def _tep_job(moi):
    return moi.tep("job.json")


def doc_job(moi):
    try:
        return json.load(open(_tep_job(moi), encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _luu_job(moi, job):
    ghi_nguyen_tu(_tep_job(moi), json.dumps(job, ensure_ascii=False, indent=1).encode("utf-8"), 0o600)


def _nhat_ky(moi, job, msg):
    job.setdefault("nhat_ky", []).append({"luc": int(moi.gio()), "buoc": job.get("buoc"), "noi_dung": msg})
    del job["nhat_ky"][:-200]
    _luu_job(moi, job)


def lich_su(moi):
    return moi.kho_json("lich-su.json", []).doc()


def _ghi_lich_su(moi, job):
    tom = {k: job.get(k) for k in ("loai", "tu", "den", "trang_thai", "bat_dau", "ket_thuc", "ly_do")}
    moi.kho_json("lich-su.json", []).sua(lambda d: (d.append(tom), d.__delitem__(slice(0, max(0, len(d) - 50)))))


@contextlib.contextmanager
def khoa_chay(moi, cho=False):
    fd = os.open(moi.tep(".nang-cap.lock"), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | (0 if cho else fcntl.LOCK_NB))
        except OSError:
            raise LoiNangCap("dang co mot lan nang cap/ha cap khac chay")
        yield
    finally:
        os.close(fd)


def dang_chay(moi):
    """Co tien trinh bo nang cap dang giu khoa? (UI hien thanh tien do; khong cho bam 2 lan)"""
    fd = os.open(moi.tep(".nang-cap.lock"), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    except OSError:
        return True
    finally:
        os.close(fd)


# ----------------------------------------------------------------------------------------------- kiem dieu kien
def _ban_ke_tiep(moi):
    ts = M.trang_thai(moi)
    return ts.get("ban_ke_tiep"), ts


def kiem_dieu_kien_nang_cap(moi, tuy_chon=None):
    """(chan: [str], canh_bao: [str], ban: dict|None) - cac ly do KHONG nen/khong the nang cap luc nay."""
    tuy_chon = tuy_chon or {}
    chan, canh_bao = [], []
    ban, ts = _ban_ke_tiep(moi)
    cur = None
    try:
        cur = M.hien_tai(moi)
    except M.LoiCapNhat as e:
        chan.append(str(e))
    if ts.get("loi"):
        chan.append("Lan kiem tra gan nhat bi loi: %s" % ts["loi"])
    if not ban:
        chan.append("Khong co ban ke tiep de nang cap (da moi nhat, hoac phai qua ban trung gian).")
    if dang_chay(moi):
        chan.append("Dang co mot lan nang cap/ha cap chay.")
    nv = NV.kiem(moi)
    if nv["trang_thai"] == "lech":
        chan.append("CHUONG TRINH DANG CHAY BI SUA DOI so voi ban da ky (%s). Cap nhat tu dong bi chan de khong de len mot he thong khong tin cay. "
                    "Cach xu ly: tim nguyen nhan, roi cai lai ban hien tai tu nguon tin cay (console-system-release.py cai) truoc khi cap nhat." % nv["ly_do"])
    j = doc_job(moi)
    if j and j.get("trang_thai") == "dang-chay":
        chan.append("Con mot cong viec cap nhat chua ket thuc.")
    if not ts.get("co_khoa_may"):
        chan.append("May chua co khoa rieng tu kho (chua tu dang ky voi kho) - mo trang Kho trung tam de dang ky.")
    if moi.pxe_dang_bat_fn():
        if tuy_chon.get("bo_qua_pxe"):
            canh_bao.append("PXE dang chay - may khach dang cai Windows co the BI LOI neu dich vu khoi dong lai giua chung.")
        else:
            chan.append("PXE dang chay (co the dang cai Windows qua mang). Tat PXE hoac xac nhan chap nhan nguy co.")
    if ban and cur:
        try:
            moi.khoa_goc()
        except M.LoiCapNhat as e:
            chan.append(str(e))
        can = ban.get("kich_thuoc", 0) * 3 + DUNG_LUONG_DU
        try:
            if moi.dung_luong_trong_fn(moi.thu_muc) < can:
                chan.append("Khong du cho trong (can ~%d MB)." % (can >> 20))
        except OSError:
            pass
        if ban.get("ban_truoc_bat_buoc") and G.khoa_phien_ban(ban["ban_truoc_bat_buoc"]) != G.khoa_phien_ban(cur["phien_ban"]):
            chan.append("Phai len tuan tu: ban %s yeu cau dang o %s." % (ban["phien_ban"], ban["ban_truoc_bat_buoc"]))
    return chan, canh_bao, ban


def bat_dau_nang_cap(moi, tuy_chon=None):
    """Kiem + tao job (CHUA chay). Loi -> LoiNangCap voi ly do day du."""
    tuy_chon = tuy_chon or {}
    chan, canh_bao, ban = kiem_dieu_kien_nang_cap(moi, tuy_chon)
    if chan:
        raise LoiNangCap(" | ".join(chan))
    cur = M.hien_tai(moi)
    job = {"id": hashlib.sha256(("%s%s" % (moi.gio(), os.urandom(4).hex())).encode()).hexdigest()[:12], "loai": "nang-cap", "tu": cur["phien_ban"],
           "den": ban["phien_ban"], "ten_ban_truoc": cur["ten_ban"], "kien_truc": cur["kien_truc"], "kenh": cur["kenh"], "ban": ban,
           "so_phat_hanh_den": ban["so_phat_hanh"], "buoc": "kiem", "trang_thai": "dang-chay", "bat_dau": int(moi.gio()), "tuy_chon": tuy_chon,
           "canh_bao": canh_bao, "nhat_ky": []}
    _luu_job(moi, job)
    _nhat_ky(moi, job, "Bat dau nang cap %s -> %s" % (job["tu"], job["den"]))
    return job


# ----------------------------------------------------------------------------------------------- cac buoc nang cap
def _b_kiem(moi, job):
    chan, _cb, ban = kiem_dieu_kien_nang_cap(moi, job.get("tuy_chon"))
    chan = [c for c in chan if "Dang co mot lan" not in c and "Con mot cong viec" not in c]         # chinh minh dang chay
    if chan:
        raise LoiNangCap(" | ".join(chan))
    if ban and ban["phien_ban"] != job["den"]:
        raise LoiNangCap("ban ke tiep da doi (%s -> %s) tu luc bam; kiem tra lai" % (job["den"], ban["phien_ban"]))
    _nhat_ky(moi, job, "Dieu kien nang cap dat")


def _b_sao_luu(moi, job):
    thu = os.path.join(moi.thu_muc, "sao-luu")
    os.makedirs(thu, exist_ok=True)
    duong = os.path.join(thu, "truoc-nang-cap-%s-%s-%s.tar.gz" % (job["tu"], job["den"], job["id"]))
    if not (job.get("sao_luu") and os.path.exists(job["sao_luu"])):
        moi.hook("sao_luu_fn")(duong)
        job["sao_luu"] = duong
        _nhat_ky(moi, job, "Da sao luu cau hinh: %s (%d byte)" % (os.path.basename(duong), os.path.getsize(duong)))


def _duong_goi(moi, job):
    return os.path.join(moi.thu_muc, "tai", "%s-%s.cspkg" % (job["den"], job["kien_truc"]))


def _b_tai(moi, job):
    ban = job["ban"]
    dich = _duong_goi(moi, job)
    os.makedirs(os.path.dirname(dich), exist_ok=True)
    if not os.path.exists(dich) or hashlib.sha256(open(dich, "rb").read()).hexdigest() != ban["sha256_goi"]:
        part = dich + ".part"

        def dung():
            return bool((doc_job(moi) or {}).get("huy"))
        moi.kho.tai_goi(job["den"], job["kien_truc"], job["kenh"], part, bao_tien_do=lambda d, t: None, dung=dung)
        if hashlib.sha256(open(part, "rb").read()).hexdigest() != ban["sha256_goi"]:
            with contextlib.suppress(OSError):
                os.remove(part)
            raise LoiNangCap("goi tai ve SAI sha256 so voi danh muc da ky (tai lai)")
        os.replace(part, dich)
    _nhat_ky(moi, job, "Da tai goi %s (%d byte, sha256 dung)" % (os.path.basename(dich), os.path.getsize(dich)))


def _tin_cay_va_khoa(moi, job):
    ts = M.trang_thai(moi)
    try:
        tin_cay = moi.kho_json("tin-cay.json", {}).doc()
        khoa_hl, _so = K.khoa_hop_le(tin_cay, moi.khoa_goc(), "phat-hanh", bay_gio=moi.gio(), so_hieu_da_thay=ts.get("tin_cay_so_hieu", 0))
    except K.LoiKhoa as e:
        raise LoiNangCap("tai lieu tin cay: %s" % e)
    return khoa_hl


def _b_cai(moi, job):
    thu_releases = os.path.join(moi.opt, "releases")
    dich = os.path.join(thu_releases, job["den"])
    if os.path.isdir(dich) and PH.kiem_ban(moi.opt, job["den"]) == [] and job.get("da_cai_ban"):
        _nhat_ky(moi, job, "Ban %s da giai nen va kiem tung file truoc do" % job["den"])
        return
    if os.path.isdir(dich):
        PH.xoa_ban(dich)                                                # ban do dang (chua tung duoc doi) -> lam lai tu goi da kiem
    boc = moi.kho.khoa_goi(job["den"], job["kien_truc"], job["kenh"])
    khoa_may = M.doc_khoa_may(moi.khoa_may_duong)
    if khoa_may is None:
        raise LoiNangCap("khong doc duoc khoa may")
    dek = M.mo_khoa_goi(khoa_may, moi.hook("token_fn")(), job["den"], job["kien_truc"], job["kenh"], boc)
    cur = M.hien_tai(moi)
    try:
        ten, manifest = G.cai_goi(_duong_goi(moi, job), dek, _tin_cay_va_khoa(moi, job), cur, thu_releases,
                                luu_chu_ky=lambda t, db, cs: NV.luu_chu_ky(moi, t, db, cs))
    except G.LoiGoi as e:
        raise LoiNangCap("goi KHONG hop le: %s" % e)
    if manifest["so_phat_hanh"] != job["so_phat_hanh_den"] or ten != job["den"]:
        PH.xoa_ban(os.path.join(thu_releases, ten))
        raise LoiNangCap("manifest trong goi khong khop danh muc da ky (phien ban/so phat hanh)")
    job["manifest"] = {k: manifest.get(k) for k in ("phien_ban", "so_phat_hanh", "ban_truoc_bat_buoc", "ban_toi_thieu_ha_cap", "can_khoi_dong_lai", "migration", "ghi_chu")}
    job["da_cai_ban"] = True
    _nhat_ky(moi, job, "Da kiem chu ky, giai ma, giai nen va doi chieu TUNG FILE: ban %s san sang (chua kich hoat)" % ten)


def _b_migration(moi, job):
    job["migration_bat_dau"] = True                                    # ghi truoc khi lam: mat dien giua chung -> phuc_hoi biet phai tra du lieu
    _luu_job(moi, job)
    moi.hook("migration_fn")(os.path.join(moi.opt, "releases", job["den"]))
    _nhat_ky(moi, job, "Da chay migration du lieu cho ban %s" % job["den"])


def _b_doi_ban(moi, job):
    job["doi_ban_bat_dau"] = True
    _luu_job(moi, job)
    ban_dir = os.path.join(moi.opt, "releases", job["den"])
    if PH.hien_tai(moi.opt) != job["den"]:
        PH.chuyen_ban(moi.opt, job["den"])
    moi.hook("ap_dung_fn")(ban_dir)
    job["doi_ban_xong"] = True
    _nhat_ky(moi, job, "Da doi current sang %s va ap dung cau hinh he thong" % job["den"])


def _b_khoi_dong_lai(moi, job):
    moi.hook("khoi_dong_lai_fn")()
    job["da_khoi_dong_lai"] = True
    _nhat_ky(moi, job, "Da khoi dong lai dich vu")


def _b_suc_khoe(moi, job):
    ten = job["den"]
    han = moi.gio() + moi.cho_suc_khoe
    cuoi = ""
    while True:
        ok, msg = moi.hook("suc_khoe_fn")(ten)
        if ok:
            sai = PH.kiem_ban(moi.opt, ten)
            if not sai:
                _nhat_ky(moi, job, "Kiem suc khoe dat; moi file chuong trinh khop ban %s" % ten)
                return
            ok, msg = False, "%d file chuong trinh lech so voi ban phat hanh: %s" % (len(sai), ", ".join(sai[:3]))
        cuoi = msg
        if moi.gio() >= han:
            raise LoiNangCap("Kiem suc khoe THAT BAI sau %ds: %s" % (moi.cho_suc_khoe, cuoi), hoan_tac=True)
        moi.ngu(2)


def _b_hoan_tat(moi, job):
    m = job.get("manifest", {})
    d = {"so_phat_hanh": job["so_phat_hanh_den"], "kien_truc": job["kien_truc"], "kenh": job["kenh"], "ban_truoc": job["tu"], "ten_ban_truoc": job["ten_ban_truoc"],
         "ban_toi_thieu_ha_cap": m.get("ban_toi_thieu_ha_cap"), "sao_luu_truoc": job.get("sao_luu"), "luc": int(moi.gio())}
    moi.kho_json("da-cai.json", {}).sua(lambda x: x.__setitem__(job["den"], d))
    xoa = PH.don_ban_cu(moi.opt)
    with contextlib.suppress(OSError):
        os.remove(_duong_goi(moi, job))
    _nhat_ky(moi, job, "Hoan tat. Don ban cu: %s" % (xoa or "khong"))


_BUOC_NC = {"kiem": _b_kiem, "sao-luu": _b_sao_luu, "tai": _b_tai, "cai": _b_cai, "migration": _b_migration, "doi-ban": _b_doi_ban,
            "khoi-dong-lai": _b_khoi_dong_lai, "suc-khoe": _b_suc_khoe, "hoan-tat": _b_hoan_tat}


# ----------------------------------------------------------------------------------------------- ha cap
def kiem_dieu_kien_ha_cap(moi, tuy_chon=None):
    """(chan, canh_bao, ban_dich dict|None)"""
    tuy_chon = tuy_chon or {}
    chan, canh_bao, dich = [], [], None
    try:
        cur = M.hien_tai(moi)
    except M.LoiCapNhat as e:
        return [str(e)], [], None
    bd = M.doc_da_cai(moi).get(cur["ten_ban"]) or M.doc_da_cai(moi).get(cur["phien_ban"])
    if dang_chay(moi):
        chan.append("Dang co mot lan nang cap/ha cap chay.")
    if not bd or not bd.get("ban_truoc"):
        chan.append("Khong co ban truoc de ha cap (ban nay khong duoc cai bang bo nang cap).")
        return chan, canh_bao, None
    ten = bd.get("ten_ban_truoc") or bd["ban_truoc"]
    thu = os.path.join(moi.opt, "releases", ten)
    if not os.path.isdir(thu):
        chan.append("Ban %s da bi don khoi may - khong ha cap duoc." % bd["ban_truoc"])
    elif PH.kiem_ban(moi.opt, ten):
        chan.append("Ban %s tren dia khong con nguyen ven." % bd["ban_truoc"])
    toi_thieu = bd.get("ban_toi_thieu_ha_cap")
    if toi_thieu is None:
        chan.append("Ban hien tai khong cho phep ha cap (manifest khong khai ban toi thieu).")
    elif G.khoa_phien_ban(bd["ban_truoc"]) < G.khoa_phien_ban(toi_thieu):
        chan.append("Khong duoc ha cap ve %s (ban thap nhat duoc phep: %s)." % (bd["ban_truoc"], toi_thieu))
    sao = bd.get("sao_luu_truoc")
    if tuy_chon.get("khoi_phuc_du_lieu", True):
        if not (sao and os.path.exists(sao)):
            chan.append("Khong con ban sao luu luc nang cap de khoi phuc du lieu.")
        else:
            canh_bao.append("Du lieu se tro ve luc TRUOC khi nang cap: moi thay doi tu do den gio se MAT (trang thai hien tai van duoc sao luu truoc).")
    else:
        try:
            ho_tro = moi.hook("schema_fn")(thu)
            hien = _schema_hien_tai(moi)
            if hien > ho_tro:
                chan.append("Du lieu hien tai (schema %d) moi hon ban %s hieu duoc (%d) - phai khoi phuc du lieu cu." % (hien, bd["ban_truoc"], ho_tro))
        except (LoiNangCap, OSError, ValueError) as e:
            chan.append("Khong kiem duoc tuong thich du lieu: %s" % e)
    if moi.pxe_dang_bat_fn() and not tuy_chon.get("bo_qua_pxe"):
        chan.append("PXE dang chay (co the dang cai Windows qua mang).")
    dich = {"phien_ban": bd["ban_truoc"], "ten_ban": ten, "sao_luu": sao}
    return chan, canh_bao, dich


def _schema_hien_tai(moi):
    from .. import dichuyen as DMG
    try:
        return DMG.doc_phien_ban(moi.goc)
    except Exception:
        return 0


def bat_dau_ha_cap(moi, tuy_chon=None):
    tuy_chon = tuy_chon or {}
    chan, canh_bao, dich = kiem_dieu_kien_ha_cap(moi, tuy_chon)
    if chan:
        raise LoiNangCap(" | ".join(chan))
    cur = M.hien_tai(moi)
    job = {"id": hashlib.sha256(("%s%s" % (moi.gio(), os.urandom(4).hex())).encode()).hexdigest()[:12], "loai": "ha-cap", "tu": cur["phien_ban"], "den": dich["phien_ban"],
           "ten_ban_truoc": cur["ten_ban"], "ten_ban_dich": dich["ten_ban"], "pre_sao_luu": dich["sao_luu"], "kien_truc": cur["kien_truc"], "kenh": cur["kenh"],
           "buoc": "kiem", "trang_thai": "dang-chay", "bat_dau": int(moi.gio()), "tuy_chon": tuy_chon, "canh_bao": canh_bao, "nhat_ky": []}
    _luu_job(moi, job)
    _nhat_ky(moi, job, "Bat dau ha cap %s -> %s" % (job["tu"], job["den"]))
    return job


def _h_kiem(moi, job):
    chan, _cb, _d = kiem_dieu_kien_ha_cap(moi, job.get("tuy_chon"))
    chan = [c for c in chan if "Dang co mot lan" not in c]
    if chan:
        raise LoiNangCap(" | ".join(chan))
    _nhat_ky(moi, job, "Dieu kien ha cap dat")


def _h_sao_luu(moi, job):
    thu = os.path.join(moi.thu_muc, "sao-luu")
    os.makedirs(thu, exist_ok=True)
    duong = os.path.join(thu, "truoc-ha-cap-%s-%s.tar.gz" % (job["tu"], job["id"]))
    if not (job.get("sao_luu") and os.path.exists(job["sao_luu"])):
        moi.hook("sao_luu_fn")(duong)
        job["sao_luu"] = duong
        _nhat_ky(moi, job, "Da sao luu trang thai HIEN TAI (de quay lai neu can): %s" % os.path.basename(duong))


def _h_doi_ban(moi, job):
    job["doi_ban_bat_dau"] = True
    _luu_job(moi, job)
    if PH.hien_tai(moi.opt) != job["ten_ban_dich"]:
        PH.chuyen_ban(moi.opt, job["ten_ban_dich"])
    moi.hook("ap_dung_fn")(os.path.join(moi.opt, "releases", job["ten_ban_dich"]))
    job["doi_ban_xong"] = True
    _nhat_ky(moi, job, "Da doi current ve %s" % job["den"])


def _h_khoi_phuc(moi, job):
    if job.get("tuy_chon", {}).get("khoi_phuc_du_lieu", True):
        job["du_lieu_bat_dau"] = True
        _luu_job(moi, job)
        moi.hook("khoi_phuc_fn")(job["pre_sao_luu"])
        _nhat_ky(moi, job, "Da khoi phuc du lieu tu ban sao luu luc nang cap")
    else:
        _nhat_ky(moi, job, "Giu nguyen du lieu hien tai (khong khoi phuc)")


def _h_suc_khoe(moi, job):
    j2 = dict(job, den=job["ten_ban_dich"])
    _b_suc_khoe(moi, j2)
    job.update({k: v for k, v in j2.items() if k in ("nhat_ky",)})


def _h_hoan_tat(moi, job):
    da = moi.kho_json("da-cai.json", {})
    da.sua(lambda x: x.pop(job["ten_ban_truoc"], None))                 # ban vua roi khong con la "ban hien tai co ban truoc"
    _nhat_ky(moi, job, "Hoan tat ha cap ve %s" % job["den"])


_BUOC_HC = {"kiem": _h_kiem, "sao-luu": _h_sao_luu, "doi-ban": _h_doi_ban, "khoi-phuc-du-lieu": _h_khoi_phuc,
            "khoi-dong-lai": _b_khoi_dong_lai, "suc-khoe": _h_suc_khoe, "hoan-tat": _h_hoan_tat}


# ----------------------------------------------------------------------------------------------- chay / hoan tac / phuc hoi
def _ds_buoc(job):
    return BUOC_NANG_CAP if job["loai"] == "nang-cap" else BUOC_HA_CAP


def _ham_buoc(job):
    return _BUOC_NC if job["loai"] == "nang-cap" else _BUOC_HC


def chay_job(moi):
    """Chay (hoac TIEP TUC) job tu buoc da ghi. Giu khoa. Tra ve job cuoi cung."""
    with khoa_chay(moi):
        job = doc_job(moi)
        if not job or job.get("trang_thai") != "dang-chay":
            return job
        ds, ham = _ds_buoc(job), _ham_buoc(job)
        i = ds.index(job["buoc"])
        try:
            while i < len(ds):
                job["buoc"] = ds[i]
                _luu_job(moi, job)                                     # WRITE-AHEAD: ghi truoc khi lam
                if job.get("huy") and job["loai"] == "nang-cap" and ds[i] in ("tai", "cai"):
                    raise LoiNangCap("nguoi dung huy truoc khi doi ban")
                ham[ds[i]](moi, job)
                i += 1
            _ket_thuc(moi, job, "xong", "")
            _bao_cao_kho(moi, job, "nang-cap" if job["loai"] == "nang-cap" else "ha-cap", "ok")
        except LoiNangCap as e:
            if job.get("doi_ban_bat_dau") or job.get("migration_bat_dau") or job.get("du_lieu_bat_dau") or e.hoan_tac:
                hoan_tac(moi, job, str(e))
            else:
                _ket_thuc(moi, job, "da-huy" if job.get("huy") else "that-bai", str(e))
                _bao_cao_kho(moi, job, "loi", str(e)[:400])
        except Exception as e:                                          # NGOAI DU KIEN: coi nhu loi, tra ve an toan
            if job.get("doi_ban_bat_dau") or job.get("migration_bat_dau") or job.get("du_lieu_bat_dau"):
                hoan_tac(moi, job, "%s: %s" % (type(e).__name__, e))
            else:
                _ket_thuc(moi, job, "that-bai", "%s: %s" % (type(e).__name__, e))
                _bao_cao_kho(moi, job, "loi", "%s: %s" % (type(e).__name__, e))
        return doc_job(moi)


def _ket_thuc(moi, job, trang_thai, ly_do):
    job["trang_thai"], job["ly_do"], job["ket_thuc"] = trang_thai, ly_do, int(moi.gio())
    _nhat_ky(moi, job, {"xong": "XONG", "that-bai": "THAT BAI: " + ly_do, "da-huy": "DA HUY: " + ly_do, "da-hoan-tac": "DA HOAN TAC: " + ly_do,
                        "can-xu-ly-tay": "CAN XU LY TAY: " + ly_do}.get(trang_thai, trang_thai))
    _ghi_lich_su(moi, job)


def _bao_cao_kho(moi, job, hanh_dong, ket_qua):
    with contextlib.suppress(Exception):
        if moi.kho is not None:
            moi.kho.bao_cao(hanh_dong, job.get("tu", ""), job.get("den", ""), ket_qua)


def hoan_tac(moi, job, ly_do):
    """Tra he thong ve nhu truoc khi bat dau: current -> ban cu, apply, du lieu tu ban sao luu (neu da dung toi), khoi dong lai, kiem lai."""
    job["buoc"], job["dang_hoan_tac"] = "hoan-tac", True
    _nhat_ky(moi, job, "Dang HOAN TAC do: %s" % ly_do)
    truoc = job["ten_ban_truoc"]
    loi = []
    try:
        if os.path.isdir(os.path.join(moi.opt, "releases", truoc)):
            if PH.hien_tai(moi.opt) != truoc:
                PH.chuyen_ban(moi.opt, truoc)
            moi.hook("ap_dung_fn")(os.path.join(moi.opt, "releases", truoc))
        else:
            loi.append("ban cu %s khong con tren dia" % truoc)
    except Exception as e:
        loi.append("khong tra current ve ban cu: %s" % e)
    if job.get("migration_bat_dau") or job.get("du_lieu_bat_dau"):
        sao = job.get("sao_luu")
        try:
            if sao and os.path.exists(sao):
                moi.hook("khoi_phuc_fn")(sao)
                _nhat_ky(moi, job, "Da khoi phuc du lieu tu ban sao luu truoc khi nang cap")
            else:
                loi.append("khong co ban sao luu de khoi phuc du lieu")
        except Exception as e:
            loi.append("khoi phuc du lieu loi: %s" % e)
    try:
        moi.hook("khoi_dong_lai_fn")()
        ok, msg = False, ""
        han = moi.gio() + moi.cho_suc_khoe
        while True:
            ok, msg = moi.hook("suc_khoe_fn")(truoc)
            if ok or moi.gio() >= han:
                break
            moi.ngu(2)
        if not ok:
            loi.append("sau hoan tac he thong chua khoe: %s" % msg)
    except Exception as e:
        loi.append("khoi dong lai/kiem sau hoan tac loi: %s" % e)
    if loi:
        _ket_thuc(moi, job, "can-xu-ly-tay", "%s. Hoan tac gap van de: %s. Huong dan: sudo python3 /opt/console-pi/scripts/console-system-release.py lui; "
                  "khoi phuc cau hinh: saoluu.py khoi-phuc %s" % (ly_do, "; ".join(loi), job.get("sao_luu", "<file sao luu>")))
        _bao_cao_kho(moi, job, "loi", "hoan tac that bai: " + "; ".join(loi)[:300])
        return
    if job["loai"] == "nang-cap" and os.path.isdir(os.path.join(moi.opt, "releases", job["den"])) and PH.hien_tai(moi.opt) != job["den"]:
        PH.xoa_ban(os.path.join(moi.opt, "releases", job["den"]))        # ban hong khong de lai
    _ket_thuc(moi, job, "da-hoan-tac", ly_do)
    _bao_cao_kho(moi, job, "hoan-tac", ly_do[:400])


def phuc_hoi(moi):
    """Goi luc KHOI DONG MAY (don vi systemd rieng): job dang do (mat dien/khoi dong lai giua chung) -> tiep tuc hoac hoan tac cho an toan.
    Tra ve (hanh_dong, job|None)."""
    job = doc_job(moi)
    if not job or job.get("trang_thai") != "dang-chay":
        return "khong-co-viec", job
    if dang_chay(moi):
        return "dang-chay-binh-thuong", job
    with khoa_chay(moi):
        job = doc_job(moi)
        buoc = job.get("buoc")
        if buoc == "hoan-tac":                                                   # dang hoan tac thi mat dien: lam lai hoan tac (idempotent)
            hoan_tac(moi, job, job.get("ly_do") or "bi gian doan luc dang hoan tac")
            return "hoan-tac-lai", doc_job(moi)
        den_migration = job.get("migration_bat_dau") or job.get("doi_ban_bat_dau") or job.get("du_lieu_bat_dau")
        if buoc == "migration" or (den_migration and not job.get("doi_ban_xong") and job["loai"] == "nang-cap" and buoc != "doi-ban") \
                or (job["loai"] == "ha-cap" and buoc == "khoi-phuc-du-lieu"):
            hoan_tac(moi, job, "Bi gian doan (mat dien/khoi dong lai) o buoc %s - tra ve trang thai an toan" % buoc)
            return "hoan-tac", doc_job(moi)
        if not den_migration and buoc in ("kiem", "sao-luu", "tai", "cai"):
            _ket_thuc(moi, job, "da-huy", "Bi gian doan o buoc %s truoc khi dong vao he thong - khong co gi thay doi, co the thu lai" % buoc)
            return "huy", doc_job(moi)
    chay_job(moi)                                                                # buoc sau doi-ban: tiep tuc (cac buoc deu idempotent)
    return "tiep-tuc", doc_job(moi)


def huy(moi):
    """Yeu cau huy (chi co tac dung truoc buoc cai/doi ban)."""
    j = doc_job(moi)
    if j and j.get("trang_thai") == "dang-chay":
        j["huy"] = True
        _luu_job(moi, j)
        return True
    return False
