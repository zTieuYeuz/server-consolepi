# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Ban phat hanh (releases/) + `current` + console-system-apply (2.0, buoc A6).

  /opt/console-system/releases/<phien ban>/   MA cua MOT ban, chi doc (khong sua tai cho), kem RELEASE.json (ma bam tung file)
                                             va system/ (don vi systemd, nginx, smb.conf, logrotate, udev... cua ban nay)
  /opt/console-system/current  ->  releases/<phien ban>    (doi ban = doi lien ket, nguyen tu)
  /opt/console-pi              ->  /opt/console-system/current   (TEN CU giu lai lam lien ket: don vi systemd, script, nginx... khong phai sua)

Du lieu cua nguoi dung KHONG nam o day (xem duongdan.py/dichuyen.py: /var/lib/console-system). Chi dung thu vien chuan.
`ap_dung()` (console-system-apply) dua file he thong cua mot ban ra /etc, so ma bam, sao luu ban cu, kiem cu phap (nginx -t, testparm)
truoc khi nap, loi thi tra ve.
"""
import sys as _sys
_sys.modules["ui.phathanh"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import contextlib
import hashlib
import json
import os
import shutil
import stat
import subprocess
import time

GOC_OPT = "/opt/console-system"
TEN_CU = "/opt/console-pi"
MUC_MA = ("app.py", "ui", "nettools", "consolesystem", "scripts", "static", "branding", "pxe-boot")
MUC_MANG_THEO = (".dau-an", "COPYRIGHT", "driver-san")      # do ISO/Pi them, khong co trong cay nguon
GIU_BAN = 3
TEN_RELEASE = "RELEASE.json"


class LoiPhatHanh(Exception):
    pass


# ----------------------------------------------------------------------------------------- bam
def _bam_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for kh in iter(lambda: f.read(1 << 20), b""):
            h.update(kh)
    return h.hexdigest()


def bam_cay(goc):
    """{duong tuong doi: sha256} cho moi file thuong (bo qua __pycache__, RELEASE.json)."""
    ra = {}
    for d, ds, fs in os.walk(goc):
        ds[:] = sorted(x for x in ds if x != "__pycache__")
        for f in sorted(fs):
            p = os.path.join(d, f)
            rel = os.path.relpath(p, goc)
            if rel == TEN_RELEASE or os.path.islink(p):
                continue
            ra[rel] = _bam_file(p)
    return ra


def doc_phien_ban(src):
    return open(os.path.join(src, "VERSION"), encoding="utf-8").read().strip()


# ------------------------------------------------------------------------------------- tao ban
def _chep(nguon, dich):
    if os.path.isdir(nguon):
        shutil.copytree(nguon, dich, symlinks=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".ruff_cache"))
    else:
        os.makedirs(os.path.dirname(dich), exist_ok=True)
        shutil.copy2(nguon, dich)


def dung_cay(src, dich, mang_theo=None):
    """Dung cay MA cua mot ban tu cay nguon `src` (repo) vao thu muc `dich` (chua ton tai)."""
    os.makedirs(dich)
    for m in MUC_MA:
        if os.path.exists(os.path.join(src, "src", m)):
            _chep(os.path.join(src, "src", m), os.path.join(dich, m))
    _chep(os.path.join(src, "VERSION"), os.path.join(dich, "VERSION"))
    for f in ("uninstall.sh",):
        if os.path.exists(os.path.join(src, f)):
            _chep(os.path.join(src, f), os.path.join(dich, f))
    os.makedirs(os.path.join(dich, "tools"), exist_ok=True)
    for f in sorted(os.listdir(os.path.join(src, "tools"))) if os.path.isdir(os.path.join(src, "tools")) else []:
        if f.startswith("cai-") and f.endswith(".sh"):
            _chep(os.path.join(src, "tools", f), os.path.join(dich, "tools", f))
    he = os.path.join(dich, "system")
    for thu_muc in ("systemd", "config"):
        if os.path.isdir(os.path.join(src, thu_muc)):
            _chep(os.path.join(src, thu_muc), os.path.join(he, thu_muc))
    for m in MUC_MANG_THEO:
        if mang_theo and os.path.exists(os.path.join(mang_theo, m)) and not os.path.exists(os.path.join(dich, m)):
            _chep(os.path.join(mang_theo, m), os.path.join(dich, m))


def _khoa_chi_doc(goc):
    for d, ds, fs in os.walk(goc):
        for f in fs:
            p = os.path.join(d, f)
            if not os.path.islink(p):
                os.chmod(p, os.stat(p).st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
    for d, ds, fs in os.walk(goc, topdown=False):
        os.chmod(d, os.stat(d).st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def _mo_khoa(goc):
    for d, ds, fs in os.walk(goc):
        os.chmod(d, os.stat(d).st_mode | stat.S_IWUSR)
        for f in fs:
            p = os.path.join(d, f)
            if not os.path.islink(p):
                os.chmod(p, os.stat(p).st_mode | stat.S_IWUSR)


def xoa_ban(goc):
    if os.path.lexists(goc):
        _mo_khoa(goc)
        shutil.rmtree(goc)


def tao_ban(src, opt=GOC_OPT, mang_theo=None):
    """Tao releases/<phien ban> tu cay nguon. Cung noi dung da co -> dung lai ban cu. Khac noi dung -> hau to -2, -3...
    Tra ve ten ban."""
    ver = doc_phien_ban(src)
    thu = os.path.join(opt, "releases")
    os.makedirs(thu, exist_ok=True)
    tam = os.path.join(thu, ".dang-dung-%d" % os.getpid())
    xoa_ban(tam)
    try:
        dung_cay(src, tam, mang_theo)
        bam = bam_cay(tam)
        n, ten = 1, ver
        while os.path.exists(os.path.join(thu, ten)):
            if bam_cay(os.path.join(thu, ten)) == bam:
                return ten                                     # y het ban da co
            n += 1
            ten = "%s-%d" % (ver, n)
        rl = {"ten": ten, "phien_ban": ver, "so_phat_hanh": _so_phat_hanh(src), "tao_luc": time.strftime("%Y-%m-%d %H:%M:%S"),
              "nguon_git": _git(src), "so_tep": len(bam)}
        with open(os.path.join(tam, TEN_RELEASE), "w", encoding="utf-8") as f:
            json.dump(dict(rl, tep=bam), f, indent=1, sort_keys=True)
        _khoa_chi_doc(tam)
        os.rename(tam, os.path.join(thu, ten))
        return ten
    except BaseException:
        xoa_ban(tam)
        raise


def _so_phat_hanh(src):
    """So phat hanh (chi TANG, dung de chong phat lai ban cu - xem capnhat/goi.py). Doc tu file SO_PHAT_HANH o goc cay nguon; mac dinh 1."""
    try:
        return max(1, int(open(os.path.join(src, "SO_PHAT_HANH"), encoding="utf-8").read().strip()))
    except (OSError, ValueError):
        return 1


def _git(src):
    with contextlib.suppress(OSError, subprocess.SubprocessError):
        r = subprocess.run(["git", "-C", src, "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return r.stdout.strip()
    return ""


# -------------------------------------------------------------------- danh sach / doi / lui ban
def danh_sach(opt=GOC_OPT):
    thu = os.path.join(opt, "releases")
    if not os.path.isdir(thu):
        return []
    ds = [x for x in os.listdir(thu) if not x.startswith(".") and os.path.isdir(os.path.join(thu, x))]
    return sorted(ds, key=lambda x: os.path.getmtime(os.path.join(thu, x)))


def hien_tai(opt=GOC_OPT):
    p = os.path.join(opt, "current")
    if not os.path.islink(p):
        return None
    return os.path.basename(os.path.realpath(p))


def _lich_su(opt):
    try:
        return json.load(open(os.path.join(opt, "lich-su.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return []


def _ghi_lich_su(opt, ds):
    tam = os.path.join(opt, "lich-su.json.tmp")
    with open(tam, "w", encoding="utf-8") as f:
        json.dump(ds[-50:], f, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tam, os.path.join(opt, "lich-su.json"))


def chuyen_ban(opt, ten):
    """Doi `current` sang ban `ten` (nguyen tu: tao lien ket tam roi doi ten de len)."""
    if not os.path.isdir(os.path.join(opt, "releases", ten)):
        raise LoiPhatHanh("khong co ban %s" % ten)
    cu = hien_tai(opt)
    tam = os.path.join(opt, ".current.%d" % os.getpid())
    with contextlib.suppress(OSError):
        os.remove(tam)
    os.symlink(os.path.join("releases", ten), tam)
    os.replace(tam, os.path.join(opt, "current"))
    ds = _lich_su(opt)
    ds.append({"gio": time.strftime("%Y-%m-%d %H:%M:%S"), "tu": cu, "sang": ten})
    _ghi_lich_su(opt, ds)
    return cu


def ban_truoc(opt):
    """Ban `current` da thay the gan nhat (de lui), con ton tai tren dia."""
    cu = hien_tai(opt)
    for m in reversed(_lich_su(opt)):
        if m.get("sang") == cu and m.get("tu") and os.path.isdir(os.path.join(opt, "releases", m["tu"])):
            return m["tu"]
    return None


def don_ban_cu(opt, giu=GIU_BAN):
    """Giu `giu` ban moi nhat + ban dang dung + ban lui duoc; xoa phan con lai. Tra ve cac ban da xoa."""
    ds = danh_sach(opt)
    giu_lai = set(ds[-giu:]) | {hien_tai(opt), ban_truoc(opt)}
    xoa = [x for x in ds if x not in giu_lai]
    for x in xoa:
        xoa_ban(os.path.join(opt, "releases", x))
    return xoa


def kiem_ban(opt, ten):
    """So ma bam tung file voi RELEASE.json. Tra ve danh sach file sai/thieu/thua (rong = nguyen ven)."""
    goc = os.path.join(opt, "releases", ten)
    rl = json.load(open(os.path.join(goc, TEN_RELEASE), encoding="utf-8"))
    that = bam_cay(goc)
    khai = rl["tep"]
    return sorted([k for k in khai if that.get(k) != khai[k]] + [k for k in that if k not in khai])


# ================================================================================ console-system-apply
def _chay_that(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr)
    except (OSError, subprocess.SubprocessError) as e:
        return 127, str(e)


def muc_he_thong(ban):
    """Danh sach file he thong cua mot ban: (nguon tuyet doi, dich tuyet doi, kieu). Dich chi duoc cap nhat khi DA TON TAI tren may
    (may nao cai gi thi giu nhu vay - viec cai lan dau la cua install.sh)."""
    he = os.path.join(ban, "system")
    ra = []
    sd = os.path.join(he, "systemd")
    for f in sorted(os.listdir(sd)) if os.path.isdir(sd) else []:
        if f.endswith((".service", ".timer")):
            ra.append((os.path.join(sd, f), "/etc/systemd/system/" + f, "unit"))
    cf = os.path.join(he, "config")
    anh_xa = {"nginx-console-pi.conf": ("/etc/nginx/sites-available/console-pi.conf", "nginx"),
              "smb.conf": ("/etc/samba/smb.conf", "smb"),
              "logrotate-console-pi": ("/etc/logrotate.d/console-pi", "tho"),
              "journald-console-pi.conf": ("/etc/systemd/journald.conf.d/60-console-pi.conf", "tho")}
    for f in sorted(os.listdir(cf)) if os.path.isdir(cf) else []:
        if f in anh_xa:
            ra.append((os.path.join(cf, f), anh_xa[f][0], anh_xa[f][1]))
        elif f.startswith("99-") and f.endswith(".rules"):
            ra.append((os.path.join(cf, f), "/etc/udev/rules.d/" + f, "udev"))
    return ra


TEN_DV_DOI = ("dashboard", "kiosk-helper", "kiosk", "selftest", "term-local", "term-phien", "term-ssh", "tftp", "tunnel", "ttyd@")


def _dich_vu_cua(x, tien_to, dev_glob=("/dev/ttyUSB*", "/dev/ttyACM*")):
    """Ten dich vu thuc de goi systemctl: don vi thuong -> [ten]; mau ttyd@ -> mot ten cho moi cong serial dang cam."""
    if not x.endswith("@"):
        return [tien_to + x]
    import glob
    return ["%s%s%s" % (tien_to, x, os.path.basename(d)) for g in dev_glob for d in sorted(glob.glob(g))]


def chuyen_ten_dich_vu(ban, etc_goc="/", chay=_chay_that, thu=False):
    """2.0: dich vu console-pi-X -> console-system-X. May con unit ten cu (file that) thi: dung + go (disable --now), chuyen thu muc .d, de unit ten moi
    (co `Alias=` ten cu) duoc cai o ap_dung. Tra ve danh sach ten da chuyen. Unit moi chua co thi KHONG go unit cu (tranh mat dich vu)."""
    sd = os.path.join(ban, "system", "systemd")
    ra = []
    for x in TEN_DV_DOI:
        cu = os.path.join(etc_goc, "etc/systemd/system/console-pi-%s.service" % x)
        moi_nguon = os.path.join(sd, "console-system-%s.service" % x)
        if not (os.path.isfile(cu) and not os.path.islink(cu) and os.path.isfile(moi_nguon)):
            continue
        ra.append(x)
        if thu:
            continue
        for ten_cu in _dich_vu_cua(x, "console-pi-"):
            chay(["systemctl", "disable", "--now", ten_cu])
        d_cu, d_moi = cu[:-len(".service")] + ".service.d", os.path.join(etc_goc, "etc/systemd/system/console-system-%s.service.d" % x)
        if os.path.isdir(d_cu) and not os.path.exists(d_moi):
            os.rename(d_cu, d_moi)
        moi = os.path.join(etc_goc, "etc/systemd/system/console-system-%s.service" % x)
        shutil.copyfile(cu, moi)                    # tao san de ap_dung thay noi dung (ap_dung chi cap nhat file DA TON TAI)
        os.remove(cu)
    if ra and not thu:
        chay(["systemctl", "daemon-reload"])
        for x in ra:
            for ten_moi in _dich_vu_cua(x, "console-system-"):
                chay(["systemctl", "enable", ten_moi])
    return ra


def ap_dung(ban, sao_luu_vao, etc_goc="/", chay=_chay_that, thu=False):
    """Dua file he thong cua `ban` ra /etc (etc_goc="/" ; thu muc tam khi test). Tra ve bao cao dict. Khong nap lai dich vu khi thu=True."""
    bc = {"doi": [], "khong_doi": 0, "bo_qua": [], "loi": [], "unit_doi": [], "da_tra_lai": [], "chuyen_ten": []}
    bc["chuyen_ten"] = chuyen_ten_dich_vu(ban, etc_goc, chay, thu)
    ts = time.strftime("%Y%m%d-%H%M%S")
    kho = os.path.join(sao_luu_vao, "etc-" + ts)
    da_ghi = []      # (dich, duong ban sao luu hoac None, kieu)
    for nguon, dich_abs, kieu in muc_he_thong(ban):
        dich = os.path.join(etc_goc, dich_abs.lstrip("/"))
        if not os.path.exists(dich):
            bc["bo_qua"].append(dich_abs)
            continue
        if _bam_file(nguon) == _bam_file(dich):
            bc["khong_doi"] += 1
            continue
        bc["doi"].append(dich_abs)
        if thu:
            continue
        bk = os.path.join(kho, dich_abs.lstrip("/"))
        os.makedirs(os.path.dirname(bk), exist_ok=True)
        shutil.copy2(dich, bk)
        tam = dich + ".cs-moi"
        shutil.copyfile(nguon, tam)
        os.chmod(tam, 0o644)
        os.replace(tam, dich)
        da_ghi.append((dich, bk, kieu, dich_abs))
    if thu or not da_ghi:
        return bc

    def tra_lai(kieu_can):
        for dich, bk, kieu, ten in da_ghi:
            if kieu in kieu_can:
                shutil.copy2(bk, dich)
                bc["da_tra_lai"].append(ten)

    kieus = {k for _d, _b, k, _t in da_ghi}
    if "nginx" in kieus:
        rc, out = chay(["nginx", "-t"])
        if rc != 0:
            bc["loi"].append("nginx -t loi, da tra ban cu: " + out[-200:])
            tra_lai({"nginx"})
    if "smb" in kieus:
        rc, out = chay(["testparm", "-s"])
        if rc != 0:
            bc["loi"].append("testparm loi, da tra ban cu: " + out[-200:])
            tra_lai({"smb"})
    if "unit" in kieus:
        chay(["systemctl", "daemon-reload"])
        bc["unit_doi"] = [os.path.basename(t) for _d, _b, k, t in da_ghi if k == "unit" and t not in bc["da_tra_lai"]]
    if "nginx" in kieus and "nginx" not in {k for _d, _b, k, t in da_ghi if t in bc["da_tra_lai"]}:
        if chay(["systemctl", "is-active", "--quiet", "nginx"])[0] == 0:
            chay(["systemctl", "reload", "nginx"])
    if "smb" in kieus and chay(["systemctl", "is-active", "--quiet", "smbd"])[0] == 0:
        chay(["smbcontrol", "smbd", "reload-config"])
    if "udev" in kieus:
        chay(["udevadm", "control", "--reload-rules"])
    return bc


# ================================================================== chuyen /opt/console-pi (thu muc that) thanh lien ket
def _chep_neu_chua_co(nguon, dich):
    if not os.path.exists(nguon) or os.path.lexists(dich):
        return False
    os.makedirs(os.path.dirname(dich), exist_ok=True)
    if os.path.isdir(nguon):
        shutil.copytree(nguon, dich, symlinks=True)
    else:
        shutil.copy2(nguon, dich)
    return True


TRANG_THAI_TRONG_OPT = (("captures", "data/captures"), ("backups", "data/thiet-bi-backups"), ("tftp", "data/tftp"),
                        ("nettools/ifthen-rules.json", "config/ifthen-rules.json"))


def nhap_khau_cu(opt, cu_dir, goc_du_lieu, src):
    """Chuyen `cu_dir` (thuong /opt/console-pi, THU MUC THAT chua ma + vai file trang thai) thanh lien ket toi `opt/current`.
    1) dung ban tu cay nguon, mang theo .dau-an/COPYRIGHT/driver-san  2) chep trang thai (captures, tftp...) sang du lieu neu chua co
    3) chuyen current  4) doi ten thu muc cu thanh <cu>.cu-<gio> va tao lien ket. Thu muc cu GIU NGUYEN (khong xoa).
    Goi khi da dung dich vu. Loi o buoc 4 thi tra thu muc cu ve cho. Tra (ten ban, thu muc cu da doi ten)."""
    if os.path.islink(cu_dir) or not os.path.isdir(cu_dir):
        raise LoiPhatHanh("%s khong phai thu muc that" % cu_dir)
    if not os.path.exists(os.path.join(goc_du_lieu, ".bo-cuc-moi")):
        raise LoiPhatHanh("du lieu chua o bo cuc moi - chay dichuyen.py bo-cuc-moi truoc")
    ten = tao_ban(src, opt, mang_theo=cu_dir)
    for rel, dich in TRANG_THAI_TRONG_OPT:
        _chep_neu_chua_co(os.path.join(cu_dir, rel), os.path.join(goc_du_lieu, dich))
    truoc = chuyen_ban(opt, ten)
    doi_ten = "%s.cu-%s" % (cu_dir, time.strftime("%Y%m%d-%H%M%S"))
    os.rename(cu_dir, doi_ten)
    try:
        os.symlink(os.path.join(opt, "current"), cu_dir)
    except OSError:
        os.rename(doi_ten, cu_dir)
        if truoc:
            chuyen_ban(opt, truoc)
        raise
    return ten, doi_ten


def tra_ve_thu_muc_cu(opt, cu_dir):
    """Hoan tac nhap_khau_cu: bo lien ket, dua thu muc .cu-* moi nhat ve cho cu. Tra ve ten thu muc da dua ve."""
    if not os.path.islink(cu_dir):
        raise LoiPhatHanh("%s khong phai lien ket" % cu_dir)
    cac = sorted(x for x in os.listdir(os.path.dirname(cu_dir)) if x.startswith(os.path.basename(cu_dir) + ".cu-"))
    if not cac:
        raise LoiPhatHanh("khong con thu muc cu de tra ve")
    os.remove(cu_dir)
    os.rename(os.path.join(os.path.dirname(cu_dir), cac[-1]), cu_dir)
    return cac[-1]
