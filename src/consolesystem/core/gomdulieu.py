# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Gom MOI du lieu cua nguoi dung ve MOT thu muc (/var/lib/console-system) de sao luu chi can chep thu muc do (ke hoach 2.0, phan A).

Chay moi lan cai / doi ban (console-system-apply) va sau khi khoi phuc sao luu. Lam lai bao nhieu lan cung an toan.
  1. deploy/, storage/ la LIEN KET sang bo cuc cu (/var/lib/console-pi/...) - may chuyen tu 1.9 giu nguyen cho cu vi nang
     (anh Windows hang chuc GB). Cung o dia thi DOI CHO bang rename (tuc thi, khong chep), de lai lien ket NGUOC o cho cu
     cho cau hinh cu (Samba, dnsmasq) van chay.
  2. File he thong chua du lieu nguoi dung ma chuong trinh khac bat buoc doc o /etc (WiFi da luu cua wpa_supplicant):
     chuyen vao secrets/he-thong/ va dat lien ket tu /etc. May moi khoi phuc sao luu: chi tao lai lien ket.
  3. Bi mat do chinh Console System doc (token Cloudflare, khoa Tailscale): chuong trinh doc thang trong secrets/
     (duongdan.FILE_CF_TOKEN / FILE_TS_AUTHKEY); o day chi chuyen file cu tu /etc sang (neu chua co).
Tra ve danh sach dong mo ta viec da lam (rong = da gon san).
"""
import glob
import os
import shutil

THU_MUC_NANG = ("deploy", "storage")


def _doi_cho_thu_muc(goc, ten, ra):
    lk = os.path.join(goc, ten)
    if not os.path.islink(lk):
        return
    dich = os.path.realpath(lk)
    if not os.path.isdir(dich) or dich.startswith(os.path.realpath(goc) + os.sep):
        return
    if os.stat(dich).st_dev != os.stat(goc).st_dev:
        ra.append(f"{ten}/: nằm ở ổ khác ({dich}) - giữ liên kết, khi sao lưu nhớ chép cả {dich}")
        return
    os.unlink(lk)
    try:
        os.rename(dich, lk)
    except OSError as e:
        os.symlink(dich, lk)
        ra.append(f"{ten}/: không chuyển được ({e}) - giữ liên kết như cũ")
        return
    os.symlink(lk, dich)
    ra.append(f"{ten}/: đã chuyển hẳn từ {dich} vào {lk} (để lại liên kết ngược ở chỗ cũ)")


def _chuyen_lien_ket(nguon, dich, ra):
    """nguon (o /etc) <-> dich (trong thu muc du lieu): dich la ban that, nguon la lien ket."""
    if os.path.islink(nguon):
        if os.path.realpath(nguon) == os.path.realpath(dich):
            return
        os.unlink(nguon)
    if os.path.exists(nguon):
        if os.path.exists(dich):                     # ca hai deu that: giu ban /etc (dang dung), cat ban kia sang .cu
            os.replace(dich, dich + ".cu")
        os.makedirs(os.path.dirname(dich), mode=0o700, exist_ok=True)
        shutil.move(nguon, dich)
        ra.append(f"đã chuyển {nguon} vào {dich}")
    if os.path.exists(dich) and not os.path.exists(nguon):
        os.makedirs(os.path.dirname(nguon), exist_ok=True)
        os.symlink(dich, nguon)


def _chuyen_neu_chua_co(cu, moi, ra):
    if os.path.isfile(cu) and not os.path.islink(cu) and not os.path.exists(moi):
        os.makedirs(os.path.dirname(moi), mode=0o700, exist_ok=True)
        shutil.copy2(cu, moi)
        os.chmod(moi, 0o600)
        os.remove(cu)
        ra.append(f"đã chuyển {cu} vào {moi}")


def gom(goc, etc="/etc"):
    ra = []
    if not os.path.isdir(goc):
        return ra
    for ten in THU_MUC_NANG:
        _doi_cho_thu_muc(goc, ten, ra)
    he_thong = os.path.join(goc, "secrets", "he-thong")
    for ten in sorted({os.path.basename(f) for f in glob.glob(os.path.join(etc, "wpa_supplicant", "wpa_supplicant-*.conf"))
                       + glob.glob(os.path.join(he_thong, "wifi", "wpa_supplicant-*.conf"))}):
        _chuyen_lien_ket(os.path.join(etc, "wpa_supplicant", ten), os.path.join(he_thong, "wifi", ten), ra)
    _chuyen_neu_chua_co(os.path.join(etc, "cloudflared", "console-pi-token"), os.path.join(goc, "secrets", "cloudflared-token"), ra)
    _chuyen_neu_chua_co(os.path.join(etc, "tailscale-console-pi-authkey"), os.path.join(goc, "secrets", "tailscale-authkey"), ra)
    return ra
