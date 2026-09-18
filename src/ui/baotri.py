"""
Console Pi - Bao tri: don dung luong va sao luu cau hinh.

VI SAO CO MUC NAY (anh Thoai yeu cau 19/09/2026 "them cong cu giup console
pi ngay cang tot hon" - hai cong cu duoi day chon theo dung nhung gi da that
su xay ra trong luc dung, khong phai doan):

1. DON DUNG LUONG. The nho 29GB ma rieng anh Windows da chiem 10GB, bo Office
   3.6GB, phan mem 800MB. Da co lan tai install.wim len giua chung thi het
   cho (con 5.3GB luc dang tai file 5GB). Truoc day muon biet cai gi an dia
   thi phai SSH vao go `du -sh` tung thu muc - ngoai hien truong khong tien.
   Nay nhin mot cai la thay, va don duoc ba thu rac AN TOAN ngay tren giao
   dien.

2. SAO LUU CAU HINH. Toan bo cong suc cau hinh cua anh Thoai (kich ban cai
   dat, bang tra tham so, thu vien lenh thiet bi mang, ket noi kho trung
   tam) chi nam trong vai file JSON ~20KB tren MOT the nho - the nho la
   thu hong vat trong may Pi. Mat the la mat sach, phai dung lai tu dau.
   Nay tai ve duoc 1 file nen nho xiu, cat o may khac; luc can thi nap lai.

   CO Y KHONG sao luu anh Windows / bo cai phan mem (15GB): chung tai lai
   duoc tu nguon goc bat cu luc nao, con kich ban thi khong. Nhet chung
   vao ban sao luu chi lam file to den muc khong ai tai ve noi.
"""

import io
import json
import os
import shutil
import subprocess
import tarfile
import time

from .duongdan import THU_MUC_DU_LIEU, DEPLOY_DIR

# Cac duong DUOI THU MUC DU LIEU duoc dua vao ban sao luu. Deu la file cau
# hinh nho; moi thu khac (anh OS, bo cai) co the tai lai tu nguon goc.
CAC_MUC_SAO_LUU = [
    "tham-so-cai-dat.json",      # bang tra tham so cai im lang
    "command-library.json",      # thu vien lenh thiet bi mang
    "kho-trungtam.json",         # ket noi kho luu tru trung tam (co token)
    "tien-trinh.json",           # lich su tien trinh cai dat
    "deploy/kichban",            # CAC KICH BAN - thu quy nhat
    "deploy/apps/_thongtin.json",  # tham so cai im lang cua tung phan mem
]

# Cac thu muc "nang" - chi DEM dung luong de hien, khong bao gio tu dong xoa
THU_MUC_NANG = [
    ("deploy/os", "Ảnh hệ điều hành (boot.wim / install.wim)",
     "/deployos/os"),
    ("deploy/ungdung", "Ứng dụng nhiều file (Office...)", "/deployos/ungdung"),
    ("deploy/apps", "Phần mềm (.exe/.msi)", "/deployos/console/apps"),
    ("deploy/boot", "File boot PXE + ảnh đĩa cài", "/deployos/console"),
    ("deploy/drivers", "Driver", "/deployos/drivers"),
    ("storage", "Kho file dùng chung", "/storage"),
]


def _chay(cmd, timeout=120):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return False, "qua-thoi-gian-cho"
    except OSError as e:
        return False, str(e)


def co_kich_thuoc(n):
    for don_vi, chia in (("GB", 1024 ** 3), ("MB", 1024 ** 2), ("KB", 1024)):
        if n >= chia:
            return f"{n / chia:.1f} {don_vi}"
    return f"{int(n)} B"


def _do_thu_muc(duong):
    """Tong dung luong 1 thu muc (byte). Tu di bo thay vi goi `du` - tranh
    spawn tien trinh, va khong chet khi gap file bi xoa giua chung."""
    if os.path.isfile(duong):
        try:
            return os.path.getsize(duong)
        except OSError:
            return 0
    tong = 0
    for goc, _thu_muc, files in os.walk(duong, onerror=lambda e: None):
        for f in files:
            try:
                tong += os.path.getsize(os.path.join(goc, f))
            except OSError:
                pass
    return tong


# ------------------------------------------------------------ dung luong
def tinh_dung_luong():
    """Bang dung luong: dia tong the + tung muc nang + rac don duoc."""
    try:
        du = shutil.disk_usage(THU_MUC_DU_LIEU)
        dia = {"tong": du.total, "dung": du.used, "trong": du.free,
               "phan_tram": int(du.used * 100 / du.total) if du.total else 0}
    except OSError:
        dia = {"tong": 0, "dung": 0, "trong": 0, "phan_tram": 0}

    muc = []
    for duong, nhan, lien_ket in THU_MUC_NANG:
        d = os.path.join(THU_MUC_DU_LIEU, duong)
        if os.path.exists(d):
            muc.append({"nhan": nhan, "byte": _do_thu_muc(d), "lien_ket": lien_ket})
    muc.sort(key=lambda x: -x["byte"])
    return dia, muc


def tim_rac():
    """
    Ba thu rac AN TOAN de don - tra ve [(ma, nhan, byte, giai_thich)].

    "An toan" o day nghia la: xoa di khong mat bat ky du lieu nao cua nguoi
    dung, va he thong tu tao lai duoc khi can.
    """
    ra = []

    # 1. Goi cai dat .deb da tai ve (apt tu tai lai khi can)
    ra.append(("apt", "Gói cài đặt hệ thống đã tải về (apt)",
               _do_thu_muc("/var/cache/apt/archives"),
               "apt tự tải lại khi cần - xoá không ảnh hưởng gì."))

    # 2. Nhat ky he thong cu
    ok, out = _chay(["journalctl", "--disk-usage"], timeout=20)
    cd = 0
    if ok:
        import re
        m = re.search(r"([\d.]+)([KMG])", out)
        if m:
            cd = int(float(m.group(1)) * {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3}[m.group(2)])
    ra.append(("journal", "Nhật ký hệ thống cũ (journald)", cd,
               "Giữ lại 50 MB gần nhất, cắt phần cũ hơn."))

    # 3. File tai len bo do
    #
    # Sinh ra khi dang tai 1 file lon thi mat mang/dong trinh duyet giua
    # chung. Chung vo dung 100% (khong bao gio duoc dung toi nua) nhung co
    # the nang vai GB - dung loai rac dang don nhat ma khong ai nghi toi.
    tong_part, so_part = 0, 0
    for goc, _t, files in os.walk(THU_MUC_DU_LIEU, onerror=lambda e: None):
        for f in files:
            if f.endswith(".part"):
                try:
                    tong_part += os.path.getsize(os.path.join(goc, f))
                    so_part += 1
                except OSError:
                    pass
    ra.append(("part", f"File tải lên dở dang ({so_part} file)", tong_part,
               "Sinh ra khi tải file bị đứt giữa chừng - không bao giờ dùng tới nữa."))
    return ra


def don_rac(ma):
    """Don 1 loai rac. Tra (ok, thong_bao)."""
    if ma == "apt":
        ok, out = _chay(["apt-get", "clean"], timeout=120)
        return ok, ("Đã xoá gói cài đặt đã tải về." if ok else f"Không xoá được: {out[:150]}")
    if ma == "journal":
        ok, out = _chay(["journalctl", "--vacuum-size=50M"], timeout=120)
        return ok, ("Đã cắt nhật ký cũ, giữ lại 50 MB gần nhất."
                    if ok else f"Không cắt được: {out[:150]}")
    if ma == "part":
        so, byte = 0, 0
        for goc, _t, files in os.walk(THU_MUC_DU_LIEU, onerror=lambda e: None):
            for f in files:
                if f.endswith(".part"):
                    p = os.path.join(goc, f)
                    try:
                        byte += os.path.getsize(p)
                        os.remove(p)
                        so += 1
                    except OSError:
                        pass
        return True, (f"Đã xoá {so} file dở dang, lấy lại {co_kich_thuoc(byte)}."
                      if so else "Không có file dở dang nào.")
    return False, "Không rõ cần dọn gì."


# ------------------------------------------------------- sao luu cau hinh
def tao_ban_sao_luu():
    """
    Dong goi cau hinh thanh .tar.gz TRONG BO NHO (khong ghi file tam ra the
    nho - tong cong chi vai chuc KB nen khong dang, va the nho co the dang
    day). Tra (bytes, ten_file).
    """
    bo_nho = io.BytesIO()
    nhat_ky = {"tao_luc": time.strftime("%Y-%m-%d %H:%M:%S"),
               "phien_ban": "1", "muc": []}
    with tarfile.open(fileobj=bo_nho, mode="w:gz") as tf:
        for muc in CAC_MUC_SAO_LUU:
            duong = os.path.join(THU_MUC_DU_LIEU, muc)
            if not os.path.exists(duong):
                continue
            tf.add(duong, arcname=muc)
            nhat_ky["muc"].append({"duong": muc, "byte": _do_thu_muc(duong)})
        # Kem 1 file mo ta de sau nay mo ra con biet day la ban sao luu gi
        mo_ta = json.dumps(nhat_ky, ensure_ascii=False, indent=1).encode()
        ti = tarfile.TarInfo("_console-pi-sao-luu.json")
        ti.size = len(mo_ta)
        ti.mtime = int(time.time())
        tf.addfile(ti, io.BytesIO(mo_ta))
    bo_nho.seek(0)
    ten = f"console-pi-cauhinh-{time.strftime('%Y%m%d-%H%M')}.tar.gz"
    return bo_nho.read(), ten


def _duong_an_toan(ten_trong_goi):
    """
    Chi cho phep giai nen dung cac muc minh da khai bao, va TUYET DOI khong
    cho thoat ra ngoai thu muc du lieu.

    Day la cho de dinh loi "zip slip": mot file .tar.gz doc hai co the chua
    duong dan kieu "../../etc/passwd" hoac duong dan tuyet doi, giai nen
    thang la ghi de file he thong. Ban sao luu co the den tu bat ky dau
    (anh Thoai cat o USB, gui qua mang...) nen phai coi nhu khong tin duoc.
    """
    if ten_trong_goi.startswith("/") or ".." in ten_trong_goi.split("/"):
        return None
    if ten_trong_goi == "_console-pi-sao-luu.json":
        return None                      # file mo ta, khong can giai ra
    goc = ten_trong_goi.split("/")[0]
    cho_phep = {m.split("/")[0] for m in CAC_MUC_SAO_LUU}
    if goc not in cho_phep:
        return None
    dich = os.path.realpath(os.path.join(THU_MUC_DU_LIEU, ten_trong_goi))
    if not dich.startswith(os.path.realpath(THU_MUC_DU_LIEU) + os.sep):
        return None
    return dich


def nap_ban_sao_luu(du_lieu):
    """Nap lai cau hinh tu file .tar.gz. Tra (ok, thong_bao)."""
    try:
        tf = tarfile.open(fileobj=io.BytesIO(du_lieu), mode="r:gz")
    except (tarfile.TarError, OSError) as e:
        return False, f"Không mở được file sao lưu: {e}"

    da_nap, bo_qua = [], []
    try:
        for tv in tf.getmembers():
            if not (tv.isfile() or tv.isdir()):
                bo_qua.append(tv.name)          # bo qua symlink/thiet bi
                continue
            dich = _duong_an_toan(tv.name)
            if dich is None:
                if tv.name != "_console-pi-sao-luu.json":
                    bo_qua.append(tv.name)
                continue
            if tv.isdir():
                os.makedirs(dich, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(dich), exist_ok=True)
            f = tf.extractfile(tv)
            if f is None:
                continue
            with open(dich, "wb") as ra:
                shutil.copyfileobj(f, ra)
            # Kich ban co the chua mat khau may dich -> quyen 600 nhu ban goc
            if "/kichban/" in dich or dich.endswith(".key"):
                try:
                    os.chmod(dich, 0o600)
                except OSError:
                    pass
            da_nap.append(tv.name)
    finally:
        tf.close()

    if not da_nap:
        return False, "File này không chứa mục cấu hình nào của Console Pi."
    tb = f"Đã nạp lại {len(da_nap)} mục cấu hình."
    if bo_qua:
        tb += f" Bỏ qua {len(bo_qua)} mục lạ không thuộc Console Pi."
    return True, tb
