"""
Console Pi - GOI DRIVER PHO BIEN cho anh boot (WinPE).

VAN DE THAT (26/09/2026, may ao VMware cua anh Thoai + kiem tra boot.wim):
WinPE cua Windows 10/11 KHONG co san driver cho nhieu loai card mang / bo
dieu khien o dia pho bien - VMware VMXNET3/PVSCSI, Intel I225/I226 2.5G,
Intel I219 doi 2020+, Intel RST VMD (laptop doi moi), virtio (KVM/Proxmox).
May thieu driver -> khong co mang / khong thay o dia -> khong cai duoc.
Anh Thoai: "khong co driver thi them vao di, thieu cai gi thi them vao".

VI SAO KHONG NHET SAN VAO SAN PHAM: giay phep cua VMware/Intel khong cho
phan phoi lai driver kem theo 1 san pham ban ra. Nhung CHINH cac goi do co
tren Microsoft Update Catalog (noi Windows Update tai ve). Vi vay: nguoi
dung BAM NUT, may cua ho TU TAI tu Microsoft (giong Windows Update) - hop le.
virtio-win cua Red Hat co giay phep cho phep phan phoi.

Moi goi tai ve -> giai nen (.cab bang 7z) vao DRIVERS_DIR/goi-<ma>/, danh
dau "cho_boot" -> dung chung co che driver cho anh boot da co (drivers.wim +
drvload trong deploy.cmd) VA driver cho Windows sau khi cai (DriverPaths).
Danh sach goi: goi-driver.json canh file nay (url + sha256 da kiem chung).
"""
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time

from . import deployos as _d

FILE_DANH_SACH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "goi-driver.json")
TIEN_TO = "goi-"
_trang_thai = {}          # {ma: {"dang": bool, "thong_bao": str, "luc": ts}}
_khoa = threading.Lock()


def danh_sach_goi():
    """Cac goi trong goi-driver.json + trang thai da tai chua."""
    try:
        with open(FILE_DANH_SACH, encoding="utf-8") as f:
            ds = json.load(f)
    except (OSError, ValueError):
        ds = []
    ra = []
    for g in ds:
        thu_muc = os.path.join(_d.DRIVERS_DIR, TIEN_TO + g["ma"])
        with _khoa:
            tt = dict(_trang_thai.get(g["ma"], {}))
        ra.append(dict(g, da_tai=os.path.isfile(os.path.join(thu_muc, "_thongtin.json")),
                       dang_tai=tt.get("dang", False),
                       thong_bao=tt.get("thong_bao", "")))
    return ra


def _lenh_7z():
    return shutil.which("7z") or shutil.which("7zz")


def _dat(ma, dang, thong_bao):
    with _khoa:
        _trang_thai[ma] = {"dang": dang, "thong_bao": thong_bao, "luc": time.time()}


def _tai_mot(g):
    """Tai + kiem sha256 + giai nen 1 goi. Tra ve (ok, thong_bao)."""
    import requests
    ma = g["ma"]
    z = _lenh_7z()
    if not z:
        return False, "Thiếu lệnh 7z/7zz để giải nén (cài gói 7zip)."
    tam = tempfile.mkdtemp(prefix="goidrv-", dir=_d.DEPLOY_DIR)
    try:
        f_tai = os.path.join(tam, "goi" + os.path.splitext(g["url"])[1])
        h = hashlib.sha256()
        da = 0
        with requests.get(g["url"], stream=True, timeout=60) as r:
            if r.status_code != 200:
                return False, f"Tải lỗi (HTTP {r.status_code}) từ {g['url']}"
            with open(f_tai, "wb") as f:
                for khoi in r.iter_content(1 << 20):
                    f.write(khoi)
                    h.update(khoi)
                    da += len(khoi)
                    _dat(ma, True, f"Đang tải... {_d.co_kich_thuoc(da)}")
        if g.get("sha256") and h.hexdigest() != g["sha256"].lower():
            return False, "File tải về KHÔNG khớp mã kiểm tra (sha256) - đã bỏ, không dùng."
        _dat(ma, True, "Đang giải nén...")
        ra_dir = os.path.join(tam, "ra")
        os.makedirs(ra_dir)
        r = subprocess.run([z, "x", "-y", f"-o{ra_dir}", f_tai],
                           capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            return False, "Giải nén lỗi: " + (r.stdout + r.stderr)[-200:]
        # Goi lon (vd virtio-win ISO) chi giu dung thu muc can dung
        giu = g.get("chi_giu") or []
        if giu:
            loc = os.path.join(tam, "loc")
            for duong in giu:
                nguon = os.path.join(ra_dir, duong)
                if os.path.isdir(nguon):
                    shutil.copytree(nguon, os.path.join(loc, duong.replace("/", "_")))
            ra_dir = loc
        # File khong can cho boot (vd vioprot.inf cua netkvm - protocol tuy chon)
        bo = {x.lower() for x in g.get("bo_file") or []}
        if bo:
            for goc, _ds, fs in os.walk(ra_dir):
                for x in fs:
                    if x.lower() in bo:
                        os.remove(os.path.join(goc, x))
        so_inf = sum(1 for _g, _ds, fs in os.walk(ra_dir) for x in fs
                     if x.lower().endswith(".inf"))
        if not so_inf:
            return False, "Gói tải về không có file .inf nào - bỏ."
        with open(os.path.join(ra_dir, "_thongtin.json"), "w", encoding="utf-8") as f:
            json.dump({"ten_hien_thi": g["ten_hien_thi"], "cho_boot": True,
                       "nguon": g.get("nguon") or g["url"], "url": g["url"],
                       "tu_goi_pho_bien": ma},
                      f, ensure_ascii=False, indent=1)
        dich = os.path.join(_d.DRIVERS_DIR, TIEN_TO + ma)
        cu = dich + ".cu"
        shutil.rmtree(cu, ignore_errors=True)
        if os.path.isdir(dich):
            os.replace(dich, cu)
        shutil.move(ra_dir, dich)
        shutil.rmtree(cu, ignore_errors=True)
        return True, f"Đã tải ({_d.co_kich_thuoc(da)}, {so_inf} file .inf) - đã đánh dấu nạp vào ảnh boot."
    except Exception as e:  # mang dut, het cho...
        return False, f"Lỗi: {e}"
    finally:
        shutil.rmtree(tam, ignore_errors=True)


def tai_goi(cac_ma):
    """Tai o NEN (goi co the vai tram MB) - trang tu lam moi xem tien do."""
    ds = {g["ma"]: g for g in danh_sach_goi()}
    chon = [ds[m] for m in cac_ma if m in ds and not ds[m]["dang_tai"]]
    if not chon:
        return False, "Không có gói nào để tải (hoặc đang tải rồi)."

    def chay():
        for g in chon:
            _dat(g["ma"], True, "Đang bắt đầu...")
            ok, tb = _tai_mot(g)
            _dat(g["ma"], False, ("✔ " if ok else "✘ ") + tb)
        # PXE dang bat -> dong goi lai drivers.wim + menu ngay
        try:
            from . import pxe as _pxe
            _pxe.cap_nhat_menu()
        except Exception:
            pass

    threading.Thread(target=chay, daemon=True).start()
    return True, f"Đang tải {len(chon)} gói ở nền - trang tự cập nhật tiến độ."
