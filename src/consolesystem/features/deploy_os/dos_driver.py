# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Deploy OS - DRIVER: goi driver, chon cho boot, khop model, giai nen.

(B4: tach nguyen van tu deployos.py; ten ham/hang giu nguyen, nguon van re-export.)"""
from consolesystem.core.nhatky import bo_qua as _bo_qua
import json
import os
import re
import shutil
import time
from ui.duongdan import DEPLOY_DIR, BOOT_DIR, APPS_DIR, SCRIPTS_DIR, KICHBAN_DIR, OS_DIR, DRIVERS_DIR, UNGDUNG_DIR, FONTS_DIR, EXT_SCRIPT  # noqa: F401  (B3: khai bao o core/duongdan.py)
from consolesystem.features.deploy_os.dos_chung import (_bao_dam_thu_muc, _duong_dan_trong, co_kich_thuoc, ten_an_toan)  # noqa: F401


# ---------------------------- driver (mo hinh MDT: "Out-of-Box Drivers")
def danh_sach_driver():
    """Danh sach cac goi driver da tai len - moi goi la 1 thu muc rieng
    (co the chua nhieu file .inf/.sys/.cat cho 1 thiet bi/dong may)."""
    _bao_dam_thu_muc()
    ra = []
    try:
        for driver_id in sorted(os.listdir(DRIVERS_DIR)):
            p = os.path.join(DRIVERS_DIR, driver_id)
            if not os.path.isdir(p):
                continue
            meta = {}
            try:
                with open(os.path.join(p, "_thongtin.json")) as f:
                    meta = json.load(f)
            except Exception as _loi:
                _bo_qua(_loi)
            so_file = sum(
                1 for n in os.listdir(p)
                if n != "_thongtin.json" and os.path.isfile(os.path.join(p, n)))
            # Goi cua hang (Dell .cab, zip...) giai nen ra NHIEU thu muc con - dem .inf
            # trong ca cay moi biet goi co dung duoc khong (dism /add-driver /recurse).
            so_inf = sum(1 for _g, _d2, fs in os.walk(p) for n in fs
                         if n.lower().endswith(".inf"))
            ra.append({
                "id": driver_id,
                "ten_hien_thi": meta.get("ten_hien_thi") or driver_id,
                "so_file": so_file,
                "so_inf": so_inf,
                # Driver CHO ANH BOOT (WinPE) - xem giai thich trong
                # docstring cua dat_driver_cho_boot().
                "cho_boot": bool(meta.get("cho_boot")),
                # Dong may tu nap goi nay (xem dat_model_driver)
                "model": [str(m) for m in (meta.get("model") or []) if str(m).strip()],
            })
    except OSError:
        pass
    return ra

def dat_driver_cho_boot(driver_id, bat):
    r"""
    Danh dau 1 goi driver la "nap vao anh boot (WinPE)" hay khong.

    VAN DE THAT (anh Thoai da gap voi MDT: "boot vao may nhung no
    khong nhan vi file boot MDT khong co driver card mang cua may
    do") - va da KIEM CHUNG lai tren chinh boot.wim cua Console Pi
    bang cach trich cac file .inf trong DriverStore ra doc ma phan
    cung that:

        CO   : Intel I219 doi 2016-2019 (DEV_15B7/15B8/15BB/15BE,
               15D6/15D7/15D8/15E3), Realtek RTL8111/8168, RTL8125,
               Broadcom NetXtreme, USB-LAN ASIX AX88179 + RTL8153
        THIEU: Intel I219 tu doi Comet Lake 2020 tro di (0D4E/0D4F,
               15FB/15FC, 1A1C-1A1F, 550A-550D, 0DC5-0DC7) va toan bo
               Intel I225/I226 2.5G (15F2/15F3, 125B/125C/125D)

    Nghia la may HP/Dell/Lenovo doi 2020 tro lai day dung LAN Intel
    se KHONG CO MANG trong WinPE -> khong tai duoc install.wim ->
    dung hinh, dung y het hien tuong anh gap voi MDT.

    Driver danh dau "cho_boot" se duoc CHEP THANG vao trong boot.wim
    luc dung anh dia (xem ui/unattend.py), va script trien khai chay
    `drvload` nap chung NGAY TRUOC khi khoi tao mang - nho vay card
    mang doi moi hoat dong duoc. Khac han voi driver thuong (chi
    tiem cho Windows SAU khi da cai xong, luc do da co mang roi).
    """
    p = os.path.join(DRIVERS_DIR, ten_an_toan(driver_id))
    if not os.path.isdir(p):
        return False, "Không tìm thấy gói driver."
    f_meta = os.path.join(p, "_thongtin.json")
    meta = {}
    try:
        with open(f_meta) as f:
            meta = json.load(f)
    except Exception as _loi:
        _bo_qua(_loi)
    meta["cho_boot"] = bool(bat)
    try:
        with open(f_meta, "w") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
    except OSError as e:
        return False, f"Không ghi được: {e}"
    return True, ("Đã đánh dấu nạp vào ảnh boot." if bat
                  else "Đã bỏ đánh dấu nạp vào ảnh boot.")

def dat_model_driver(driver_id, chuoi):
    """
    Gan goi driver voi DONG MAY (anh Thoai 14/10/2026, muc 8 "goi driver theo hang may").

    Di cai cho cong ty thi moi dong may (Dell Latitude 5420, HP EliteBook 840 G8...) can 1
    bo driver rieng cua hang. Truoc day phai tick goi driver vao TUNG kich ban - 1 kich ban
    dung cho nhieu dong may thi hoac thieu driver, hoac nhoi ca driver may khac vao. Nay goi
    driver ghi san "dung cho dong may nao"; luc may chon kich ban trong menu PXE, iPXE doc
    hang/model trong BIOS (SMBIOS) gui ve Pi, Pi chon dung goi -> deploy.cmd chi tiem goi do
    vao Windows vua bung (xem lichsu.py + unattend._lenh_tiem_driver_offline).

    Moi dong = 1 mau, cach nhau dau phay hoac xuong dong. Mau khop khi MOI TU trong mau la
    dau cua 1 tu trong "hang + model + dong may" cua may (khong phan biet hoa thuong) - vd
    "Latitude 5420" khop "Dell Inc. Latitude 5420"; "20W0" khop ThinkPad co model 20W0003XUS.
    """
    p = os.path.join(DRIVERS_DIR, ten_an_toan(driver_id))
    if not os.path.isdir(p):
        return False, "Không tìm thấy gói driver."
    f_meta = os.path.join(p, "_thongtin.json")
    meta = {}
    try:
        with open(f_meta) as f:
            meta = json.load(f)
    except Exception as _loi:
        _bo_qua(_loi)
    mau = []
    for m in re.split(r"[,;\n\r]+", chuoi or ""):
        m = " ".join(m.split())[:80]
        if m and m.lower() not in (x.lower() for x in mau):
            mau.append(m)
    meta["model"] = mau[:30]
    try:
        with open(f_meta, "w") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
    except OSError as e:
        return False, f"Không ghi được: {e}"
    return True, (f"Đã lưu {len(mau)} dòng máy cho gói driver." if mau
                  else "Đã bỏ gán dòng máy - gói chỉ dùng khi chọn trong kịch bản.")

def _tu_may(chuoi):
    return [t for t in re.split(r"[^0-9a-z]+", (chuoi or "").lower()) if t]

def khop_model(mau, hang="", model="", phien_ban=""):
    """True neu MOI tu cua mau la dau cua 1 tu cua thong tin may (xem dat_model_driver)."""
    tu_may = _tu_may(" ".join((hang or "", model or "", phien_ban or "")))
    tu_mau = _tu_may(mau)
    return bool(tu_mau and tu_may) and all(
        any(t.startswith(w) for t in tu_may) for w in tu_mau)

def driver_hop_model(hang="", model="", phien_ban=""):
    """Cac goi driver (khong phai goi "cho anh boot" - goi do da luon duoc tiem) co mau
    dong may khop voi may nay."""
    ra = []
    for dr in danh_sach_driver():
        if dr["cho_boot"] or not dr["so_inf"]:
            continue
        if any(khop_model(m, hang, model, phien_ban) for m in dr["model"]):
            ra.append(dr["id"])
    return ra

EXT_GOI_NEN_DRIVER = {".zip", ".cab", ".7z", ".exe"}

def giai_nen_goi_driver(driver_id, duong):
    """
    Giai nen goi driver cua hang (Dell Driver Pack .cab, HP SoftPaq .exe, .zip/.7z) vao thu
    muc con cung ten trong goi, roi xoa file nen. LOI CU (truoc 1.8.7): .zip tai len DE
    NGUYEN - dism /add-driver khong doc ben trong zip nen driver khong bao gio duoc tiem.
    Bo cai .exe kieu Inno Setup (Lenovo SCCM) 7z khong mo duoc -> bao ro cach lam.
    """
    import shutil as _sh
    import subprocess as _sp
    z = _sh.which("7z") or _sh.which("7zz")
    thu_muc = os.path.join(DRIVERS_DIR, ten_an_toan(driver_id))
    goc = os.path.splitext(os.path.basename(duong))[0]
    ra = os.path.join(thu_muc, ten_an_toan(goc) or "goi")
    if os.path.exists(ra):
        ra += time.strftime("_%H%M%S")
    try:
        if not z:
            return False, "Thiếu lệnh 7z để giải nén (cài gói 7zip)."
        can = os.path.getsize(duong) * 4
        if _sh.disk_usage(thu_muc).free < can + 1024 ** 3:
            return False, ("Không đủ chỗ trống để giải nén gói này (cần khoảng "
                           f"{co_kich_thuoc(can)}).")
        r = _sp.run([z, "x", "-y", f"-o{ra}", duong], capture_output=True, text=True,
                    timeout=1800)
        so_inf = sum(1 for _g, _d2, fs in os.walk(ra) for n in fs
                     if n.lower().endswith(".inf")) if os.path.isdir(ra) else 0
        if r.returncode != 0 or not so_inf:
            _sh.rmtree(ra, ignore_errors=True)
            if duong.lower().endswith(".exe"):
                return False, ("Không lấy được driver từ file .exe này (bộ cài kiểu Inno/"
                               "InstallShield). Chạy file đó trên máy Windows, chọn "
                               "giải nén (Extract) ra thư mục, nén thư mục thành .zip rồi "
                               "tải .zip lên.")
            if r.returncode != 0:
                return False, ("File nén hỏng hoặc không đúng định dạng (tải lại file từ trang "
                               "của hãng).")
            return False, "Gói này không có file .inf nào - không phải gói driver."
        return True, f"Đã giải nén {os.path.basename(duong)}: {so_inf} file .inf."
    except (OSError, _sp.TimeoutExpired) as e:
        _sh.rmtree(ra, ignore_errors=True)
        return False, f"Lỗi khi giải nén: {e}"
    finally:
        try:
            os.remove(duong)
        except OSError:
            pass

def tao_driver_moi(ten_hien_thi):
    _bao_dam_thu_muc()
    ten_hien_thi = (ten_hien_thi or "").strip()
    if not ten_hien_thi:
        return False, "Chưa đặt tên gói driver.", None
    driver_id = ten_an_toan(ten_hien_thi.replace(" ", "_")).lower()
    if not driver_id:
        return False, "Tên không hợp lệ.", None
    p = os.path.join(DRIVERS_DIR, driver_id)
    if os.path.isdir(p):
        return False, f'Da co goi driver "{driver_id}" roi.', None
    try:
        os.makedirs(p, exist_ok=True)
        with open(os.path.join(p, "_thongtin.json"), "w") as f:
            json.dump({"ten_hien_thi": ten_hien_thi}, f, ensure_ascii=False)
    except OSError as e:
        return False, f"Không tạo được: {e}", None
    return True, f'Đã tạo "{ten_hien_thi}".', driver_id

def xoa_driver(driver_id):
    p = _duong_dan_trong(DRIVERS_DIR, driver_id)
    if not p or not os.path.isdir(p):
        return False, "Không tìm thấy gói driver."
    try:
        import shutil
        shutil.rmtree(p)
    except OSError as e:
        return False, f"Không xóa được: {e}"
    return True, "Đã xóa."

def xoa_file_trong_driver(driver_id, ten_file):
    p = _duong_dan_trong(DRIVERS_DIR, driver_id)
    if not p or not os.path.isdir(p):
        return False, "Không tìm thấy gói driver."
    fp = _duong_dan_trong(p, ten_file)
    if fp and os.path.isdir(fp) and os.path.dirname(fp) == p:
        # Thu muc giai nen tu goi cua hang (giai_nen_goi_driver)
        shutil.rmtree(fp, ignore_errors=True)
        return (not os.path.exists(fp)), "Đã xóa thư mục."
    if not fp or not os.path.isfile(fp) or os.path.basename(fp) == "_thongtin.json":
        return False, "Không tìm thấy file."
    try:
        os.remove(fp)
    except OSError as e:
        return False, f"Không xóa được: {e}"
    return True, "Đã xóa."
