# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Deploy OS - danh muc PHAN MEM (.exe/.msi) va UNG DUNG nhieu file: doc/ghi thong tin, tham so cai im lang, giai nen, xoa.

(B4: tach nguyen van tu deployos.py; ten ham/hang giu nguyen, nguon van re-export.)"""
from consolesystem.core.nhatky import bo_qua as _bo_qua
import json
import os
from ui.duongdan import DEPLOY_DIR, BOOT_DIR, APPS_DIR, SCRIPTS_DIR, KICHBAN_DIR, OS_DIR, DRIVERS_DIR, UNGDUNG_DIR, FONTS_DIR, EXT_SCRIPT  # noqa: F401  (B3: khai bao o core/duongdan.py)
from consolesystem.features.deploy_os.dos_chung import (_bao_dam_thu_muc, _duong_dan_trong, _liet_ke, co_kich_thuoc, ten_an_toan)  # noqa: F401
from consolesystem.features.deploy_os.dos_hangso import (APPS_META, EXT_APP)  # noqa: F401


# ------------------------------------------------- thong tin phan mem (2.2)
def doc_thongtin_app():
    """
    Tham so cai dat im lang cua tung phan mem, vd {"teamviewer.exe": "/S"}.
    Moi hang dat 1 kieu cho rieng (/S, /silent, /quiet, /verysilent...) nen
    phai cho nguoi dung tu dien, khong doan gium.
    """
    try:
        with open(APPS_META) as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        return {}

def ghi_thongtin_app(d):
    _bao_dam_thu_muc()
    try:
        tam = APPS_META + ".tmp"
        with open(tam, "w") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.replace(tam, APPS_META)
        return True
    except OSError:
        return False

# Tham so GO CAI DAT luu cung file voi tham so cai, khoa "<ten file>::go" (04/10/2026).
HAU_TO_GO = "::go"

def danh_sach_app():
    meta = doc_thongtin_app()
    ra = _liet_ke(APPS_DIR, EXT_APP)
    for a in ra:
        a["tham_so"] = meta.get(a["ten"], "")
        a["go_cai"] = meta.get(a["ten"] + HAU_TO_GO, "")
        a["la_msi"] = a["ten"].lower().endswith(".msi")
    return ra

# Goi y tham so cai im lang theo tung ho trinh cai dat - de nguoi dung
# chon thay vi phai tu tra cuu tieng Anh. Dung chung cho tab "Phan mem"
# va buoc 5 cua kich ban.
GOI_Y_THAM_SO = [
    ("/qn /norestart", "MSI chuẩn - im lặng hoàn toàn"),
    ("/qn /norestart ALLUSERS=1", "MSI - cài cho MỌI người dùng trên máy"),
    ("/S", "NSIS (7-Zip, Notepad++, VLC...) - chữ S HOA"),
    ("/VERYSILENT /SUPPRESSMSGBOXES /NORESTART", "Inno Setup"),
    ("/quiet /norestart", "WiX Burn (.NET, Visual C++ Redist...)"),
    ('/s /v"/qn"', "InstallShield"),
    ("-ms", "Firefox"),
    ("--silent", "Squirrel (một số app kiểu Electron)"),
]

def tham_so_mac_dinh_app(ten):
    """Tham so hop ly nhat khi chua ai dien gi - .msi thi chac chan dung."""
    return "/qn /norestart" if (ten or "").lower().endswith(".msi") else ""

def chuan_hoa_apps(apps):
    """
    Dua danh sach phan mem cua kich ban ve dang chuan:
        [{"ten": "chrome.msi", "dich": "nguoi_dung"}, ...]

    02/10/2026 anh Thoai: "tat ca phan mem khi dang nhap lan dau moi bat dau cai, bo
    che do cai theo may" - MOI phan mem cai o phien dang nhap dau (co bang tien trinh
    tren may + trang Tien trinh cua Console System, xem unattend.sinh_script_tien_trinh).
    Kich ban CU luu "may" (hoac dang chuoi ten file) van doc duoc, tu chuyen sang
    "nguoi_dung" - khong lam hong kich ban da luu.
    """
    ra = []
    for a in apps or []:
        ten = a if isinstance(a, str) else (a.get("ten") if isinstance(a, dict) else None)
        if ten:
            ra.append({"ten": ten, "dich": "nguoi_dung"})
    return ra

def danh_sach_ungdung():
    """Danh sach ung dung kieu thu muc - moi ung dung la 1 thu muc rieng
    trong UNGDUNG_DIR, co the chua bao nhieu file/thu muc con cung duoc."""
    _bao_dam_thu_muc()
    ra = []
    try:
        for ung_id in sorted(os.listdir(UNGDUNG_DIR)):
            p = os.path.join(UNGDUNG_DIR, ung_id)
            if not os.path.isdir(p):
                continue
            meta = {}
            try:
                with open(os.path.join(p, "_thongtin.json")) as f:
                    meta = json.load(f)
            except Exception as _loi:
                _bo_qua(_loi)
            so_file = 0
            tong_byte = 0
            for goc, _dirs, files in os.walk(p):
                for ten in files:
                    if goc == p and ten == "_thongtin.json":
                        continue
                    so_file += 1
                    try:
                        tong_byte += os.path.getsize(os.path.join(goc, ten))
                    except OSError:
                        pass
            ra.append({
                "id": ung_id,
                "ten_hien_thi": meta.get("ten_hien_thi") or ung_id,
                "lenh_cai": meta.get("lenh_cai") or "",
                "so_file": so_file,
                "kich_thuoc": co_kich_thuoc(tong_byte) if tong_byte else "0 B",
            })
    except OSError:
        pass
    return ra

def lay_ungdung(ung_id):
    for u in danh_sach_ungdung():
        if u["id"] == ung_id:
            return u
    return None

def _doc_meta_ungdung(ung_id):
    p = os.path.join(UNGDUNG_DIR, ten_an_toan(ung_id), "_thongtin.json")
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return {}

def _ghi_meta_ungdung(ung_id, meta):
    p = os.path.join(UNGDUNG_DIR, ten_an_toan(ung_id), "_thongtin.json")
    try:
        with open(p, "w") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
        return True
    except OSError:
        return False

def tao_ungdung_moi(ten_hien_thi):
    _bao_dam_thu_muc()
    ten_hien_thi = (ten_hien_thi or "").strip()
    if not ten_hien_thi:
        return False, "Chưa đặt tên ứng dụng.", None
    ung_id = ten_an_toan(ten_hien_thi.replace(" ", "_")).lower()
    if not ung_id:
        return False, "Tên không hợp lệ.", None
    p = os.path.join(UNGDUNG_DIR, ung_id)
    if os.path.isdir(p):
        return False, "Đã có ứng dụng cùng tên.", None
    try:
        os.makedirs(p)
        _ghi_meta_ungdung(ung_id, {"ten_hien_thi": ten_hien_thi, "lenh_cai": ""})
    except OSError as e:
        return False, f"Không tạo được: {e}", None
    return True, f'Đã tạo "{ten_hien_thi}".', ung_id

def xoa_ungdung(ung_id):
    import shutil
    p = _duong_dan_trong(UNGDUNG_DIR, ung_id)
    if not p or not os.path.isdir(p):
        return False, "Không tìm thấy ứng dụng."
    try:
        shutil.rmtree(p)
    except OSError as e:
        return False, f"Không xóa được: {e}"
    return True, "Đã xóa ứng dụng."

def dat_lenh_cai_ungdung(ung_id, lenh_cai):
    """
    Luu dong lenh cai TU DO - dung y het "Command line" cua MDT. Nguoi dung
    tu go nguyen dong (vd "setup.exe /configure configuration.xml" cho
    Office 365, hoac "msiexec /i goi.msi /qn" cho MSI thuong). Deploy.cmd se
    tu `cd` vao dung thu muc ung dung nay TRUOC khi chay dong lenh, nen chi
    can go ten file, khong can duong dan day du.
    """
    p = os.path.join(UNGDUNG_DIR, ten_an_toan(ung_id))
    if not os.path.isdir(p):
        return False, "Không tìm thấy ứng dụng."
    lenh_cai = (lenh_cai or "").strip()[:500]
    meta = _doc_meta_ungdung(ung_id)
    meta["lenh_cai"] = lenh_cai
    if not _ghi_meta_ungdung(ung_id, meta):
        return False, "Không ghi được lệnh cài."
    return True, "Đã lưu dòng lệnh cài."

def _an_toan_trong_zip(ten_muc):
    """Chan zip-slip (../../etc/passwd) khi giai nen - kiem tra THAT bang
    os.path.normpath, khong tin vao chinh chuoi trong file zip."""
    chuan = os.path.normpath(ten_muc)
    return not (chuan.startswith("..") or os.path.isabs(chuan))

def giai_nen_ungdung(ung_id, duong_zip):
    """
    Giai nen 1 file .zip da tai len THANG vao thu muc ung dung (giu nguyen
    cau truc thu muc con ben trong zip - dung cho bo cai nhieu file/thu muc
    long nhau nhu Office 365: thu muc Office\\Data\\..., setup.exe,
    configuration.xml). Xoa file .zip sau khi giai nen xong.
    """
    import zipfile
    p = os.path.join(UNGDUNG_DIR, ten_an_toan(ung_id))
    if not os.path.isdir(p):
        return False, "Không tìm thấy ứng dụng."
    try:
        import shutil
        with zipfile.ZipFile(duong_zip) as z:
            hop_le = [i for i in z.infolist() if _an_toan_trong_zip(i.filename)]
            # Kiem tra CHO TRUOC: giai nen ra se chiem bao nhieu, o con du khong (chua tru file
            # .zip dang nam tren o). Tranh giai nen nua chung roi day o lam hong ca may.
            can = sum(i.file_size for i in hop_le)
            con = shutil.disk_usage(UNGDUNG_DIR).free
            if can > con - 1024 ** 3:
                return False, (f"Không đủ chỗ trống để giải nén: cần {co_kich_thuoc(can)}, "
                               f"ổ còn {co_kich_thuoc(con)} (phải chừa lại ít nhất 1 GB).")
            for info in hop_le:
                z.extract(info, p)
    except zipfile.BadZipFile:
        return False, "File không phải .zip hợp lệ (hoặc bị hỏng khi tải lên)."
    except OSError as e:
        return False, f"Lỗi khi giải nén: {e}"
    finally:
        try:
            os.remove(duong_zip)
        except OSError:
            pass
    return True, "Đã giải nén xong vào ứng dụng."

def liet_ke_muc_ungdung(ung_id):
    """Liet ke CAP 1 (file/thu muc con ngay duoi goc) de hien tren giao
    dien - khong liet ke sau hon vi Office co the co hang ngan file con."""
    p = os.path.join(UNGDUNG_DIR, ten_an_toan(ung_id))
    ra = []
    try:
        for ten in sorted(os.listdir(p)):
            if ten == "_thongtin.json":
                continue
            fp = os.path.join(p, ten)
            if os.path.isdir(fp):
                so_con = sum(len(files) for _g, _d, files in os.walk(fp))
                ra.append({"ten": ten, "la_thu_muc": True, "so_file": so_con,
                          "kich_thuoc": ""})
            else:
                ra.append({"ten": ten, "la_thu_muc": False, "so_file": 0,
                          "kich_thuoc": co_kich_thuoc(os.path.getsize(fp))})
    except OSError:
        pass
    return ra

def xoa_muc_trong_ungdung(ung_id, ten_muc):
    """Xoa 1 file HOAC 1 thu muc con o CAP 1 (khong cho xoa xuyen thu muc
    cha bang duong dan co '/' hay '..')."""
    p = _duong_dan_trong(UNGDUNG_DIR, ung_id)
    if not p or not os.path.isdir(p):
        return False, "Không tìm thấy ứng dụng."
    ten_muc = ten_an_toan(ten_muc)
    if not ten_muc or ten_muc == "_thongtin.json":
        return False, "Không tìm thấy mục cần xóa."
    fp = os.path.join(p, ten_muc)
    if not os.path.exists(fp):
        return False, "Không tìm thấy mục cần xóa."
    import shutil
    try:
        if os.path.isdir(fp):
            shutil.rmtree(fp)
        else:
            os.remove(fp)
    except OSError as e:
        return False, f"Không xóa được: {e}"
    return True, "Đã xóa."

def chuan_hoa_ungdung(ds):
    """Dua danh sach ung dung (thu muc) cua kich ban ve dang chuan:
        [{"id": "office365", "dich": "nguoi_dung"}, ...] - luon cai o phien dang nhap
        dau, giong chuan_hoa_apps (bo che do cai theo may 02/10/2026)."""
    return [{"id": a["id"], "dich": "nguoi_dung"}
            for a in ds or [] if isinstance(a, dict) and a.get("id")]
