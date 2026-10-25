# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Deploy OS - kho FONT (bo font): tao/xoa/them font, giai nen zip.

(B4: tach nguyen van tu deployos.py; ten ham/hang giu nguyen, nguon van re-export.)"""
import json
import os
import re
import secrets
import shutil
import time
import unicodedata
from ui.duongdan import DEPLOY_DIR, BOOT_DIR, APPS_DIR, SCRIPTS_DIR, KICHBAN_DIR, OS_DIR, DRIVERS_DIR, UNGDUNG_DIR, FONTS_DIR, EXT_SCRIPT  # noqa: F401  (B3: khai bao o core/duongdan.py)
from consolesystem.features.deploy_os.dos_chung import (_bao_dam_thu_muc, _con_trong_gb, co_kich_thuoc, ten_an_toan)  # noqa: F401
from consolesystem.features.deploy_os.dos_hangso import (MIN_FREE_GB)  # noqa: F401


# ------------------------------------------------ BO FONT (font chu cai cho may Windows)
# Cong ty co nhieu font rieng (thuong hang tram file) can co san tren moi may. 1 "bo font"
# la 1 thu muc trong FONTS_DIR chua cac file .ttf/.otf/.ttc/.otc (+ _thongtin.json ten
# hien thi, + _fonts.json do ui/fontinfo.py sinh ra: ten that cua tung font va ten gia tri
# registry). Kich ban chon cac bo can cai; luc trien khai Windows, deploy.cmd chep ca
# thu muc sang may dich va 1 buoc sau dang nhap (cai-font.ps1, quyen SYSTEM) cai tung font.
# Moi file tai len deu duoc DOC THAT bang fontinfo: file doi duoi (vd .txt thanh .ttf), file
# hong, web font .woff khong cai duoc vao Windows -> bi tu choi ngay, noi ro ly do, khong
# de den luc cai may moi phat hien.
MAX_FONT_BYTE = 300 * 1024 * 1024        # 1 font that khong bao gio lon the

MAX_ZIP_FONT_BYTE = 1024 * 1024 * 1024        # tong font giai nen tu 1 zip (the nho Pi chi vai chuc GB)

def _id_bo_font_tu_ten(ten):
    """Ten hien thi (co dau) -> id ASCII: 'Phông công ty' -> 'phong_cong_ty'."""
    t = unicodedata.normalize("NFKD", (ten or "").replace("đ", "d").replace("Đ", "D"))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return ten_an_toan(re.sub(r"\s+", "_", t.strip())).lower()

def duong_bo_font(bo_id):
    """Duong dan that cua 1 bo font neu id hop le va thu muc ton tai, nguoc lai None."""
    bo_id = ten_an_toan(bo_id or "").lower()
    if not bo_id:
        return None
    p = os.path.join(FONTS_DIR, bo_id)
    return p if os.path.isdir(p) else None

def _doc_meta_bo_font(p):
    try:
        with open(os.path.join(p, "_thongtin.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def danh_sach_bo_font():
    from ui import fontinfo as _fi
    _bao_dam_thu_muc()
    ra = []
    try:
        for bo_id in sorted(os.listdir(FONTS_DIR)):
            p = os.path.join(FONTS_DIR, bo_id)
            if not os.path.isdir(p):
                continue
            ds = _fi.lam_moi_danh_sach(p)
            ra.append({
                "id": bo_id,
                "ten_hien_thi": _doc_meta_bo_font(p).get("ten_hien_thi") or bo_id,
                "so_font": len(ds),
                "kich_thuoc": co_kich_thuoc(sum(m["byte"] for m in ds)) if ds else "0 B",
                "fonts": ds,
            })
    except OSError:
        pass
    return ra

def lay_bo_font(bo_id):
    for b in danh_sach_bo_font():
        if b["id"] == bo_id:
            return b
    return None

def tao_bo_font(ten_hien_thi):
    _bao_dam_thu_muc()
    ten_hien_thi = (ten_hien_thi or "").strip()[:80]
    if not ten_hien_thi:
        return False, "Chưa đặt tên bộ font.", None
    bo_id = _id_bo_font_tu_ten(ten_hien_thi)
    if not bo_id:
        return False, "Tên không hợp lệ.", None
    p = os.path.join(FONTS_DIR, bo_id)
    if os.path.isdir(p):
        return False, "Đã có bộ font cùng tên.", None
    try:
        os.makedirs(p)
        with open(os.path.join(p, "_thongtin.json"), "w", encoding="utf-8") as f:
            json.dump({"ten_hien_thi": ten_hien_thi}, f, ensure_ascii=False, indent=1)
    except OSError as e:
        return False, f"Không tạo được: {e}", None
    return True, f'Đã tạo bộ font "{ten_hien_thi}".', bo_id

def xoa_bo_font(bo_id):
    p = duong_bo_font(bo_id)
    if not p:
        return False, "Không tìm thấy bộ font."
    try:
        shutil.rmtree(p)
    except OSError as e:
        return False, f"Không xóa được: {e}"
    return True, "Đã xóa bộ font."

def xoa_font_trong_bo(bo_id, ten):
    from ui import fontinfo as _fi
    p = duong_bo_font(bo_id)
    ten = _fi.ten_file_an_toan(ten)
    if not p or not ten or not _fi.la_duoi_font(ten):
        return False, "Không tìm thấy font cần xóa."
    fp = os.path.join(p, ten)
    if not os.path.isfile(fp):
        return False, "Không tìm thấy font cần xóa."
    try:
        os.remove(fp)
    except OSError as e:
        return False, f"Không xóa được: {e}"
    _fi.lam_moi_danh_sach(p)
    return True, "Đã xóa font."

def _xoa_tam(tam):
    try:
        os.remove(tam)
    except OSError:
        pass

def _don_tam_cu(p, tuoi_giay=3600):
    """Xoa file .tam-* bi bo lai (tai len loi giua chung, mat dien...) cu hon 1 gio."""
    try:
        for n in os.listdir(p):
            if n.startswith(".tam-"):
                f = os.path.join(p, n)
                if time.time() - os.path.getmtime(f) > tuoi_giay:
                    _xoa_tam(f)
    except OSError:
        pass

def _luu_font_hop_le(p, tam, ten):
    """Kiem tra file tam la font that roi dat vao bo. Tra (ok, thong_bao)."""
    from ui import fontinfo as _fi
    if not _fi.la_font_hop_le(tam):
        try:
            os.remove(tam)
        except OSError:
            pass
        return False, f'"{ten}": không phải font thật (file hỏng, sai định dạng hoặc chỉ đổi đuôi).'
    os.replace(tam, os.path.join(p, ten))
    return True, ""

def them_font_vao_bo(bo_id, fileobj):
    """
    Nhan 1 file tai len vao bo font. Chap nhan font (.ttf/.otf/.ttc/.otc) HOAC .zip
    chua font (giai nen PHANG - bo qua thu muc, chi lay file font, bo qua rac nhu
    __MACOSX). Tra (ok, thong_bao, so_font_them, [ly_do_bo_qua...]).
    """
    from ui import fontinfo as _fi
    p = duong_bo_font(bo_id)
    if not p:
        return False, "Không tìm thấy bộ font.", 0, []
    if _con_trong_gb() < MIN_FREE_GB:
        return False, (f"Chỉ còn {_con_trong_gb()} GB trống - cần ít nhất {MIN_FREE_GB} GB. "
                       "Xóa bớt file trước khi tải thêm."), 0, []
    ten = _fi.ten_file_an_toan(getattr(fileobj, "filename", ""))
    duoi = os.path.splitext(ten)[1].lower()
    if not ten:
        return False, "Chưa chọn file.", 0, []
    if duoi in (".woff", ".woff2"):
        return False, (f'"{ten}" là web font (dùng cho trang web), Windows không cài được. '
                       "Cần bản .ttf hoặc .otf."), 0, []
    _don_tam_cu(p)
    tam = os.path.join(p, ".tam-" + secrets.token_hex(4))
    if duoi == ".zip":
        try:
            fileobj.save(tam)
        except OSError as e:
            _xoa_tam(tam)
            return False, f"Không lưu được: {e}", 0, []
        return _giai_nen_font_zip(p, tam, ten)
    if duoi not in _fi.DUOI_FONT:
        return False, (f'"{ten}": không nhận đuôi này. Chỉ nhận font .ttf, .otf, .ttc, .otc '
                       "hoặc .zip chứa font."), 0, []
    try:
        fileobj.save(tam)
    except OSError as e:
        _xoa_tam(tam)
        return False, f"Không lưu được: {e}", 0, []
    ok, lydo = _luu_font_hop_le(p, tam, ten)
    if not ok:
        return False, lydo, 0, []
    _fi.lam_moi_danh_sach(p)
    return True, f'Đã thêm "{ten}".', 1, []

def _giai_nen_font_zip(p, tam_zip, ten_zip):
    import zipfile
    from ui import fontinfo as _fi
    them, bo_qua, tong = 0, [], 0
    try:
        with zipfile.ZipFile(tam_zip) as z:
            for info in z.infolist():
                goc = info.filename.replace("\\", "/")
                if info.is_dir() or "__MACOSX/" in goc or goc.rsplit("/", 1)[-1].startswith("._"):
                    continue
                ten = _fi.ten_file_an_toan(goc)
                if not ten or not _fi.la_duoi_font(ten):
                    if goc.lower().endswith((".woff", ".woff2")):
                        bo_qua.append(f'"{ten}": web font, Windows không cài được')
                    continue
                if info.file_size > MAX_FONT_BYTE:
                    bo_qua.append(f'"{ten}": lớn bất thường ({co_kich_thuoc(info.file_size)})')
                    continue
                tong += info.file_size
                if tong > MAX_ZIP_FONT_BYTE:
                    bo_qua.append("Dừng giải nén: tổng dung lượng font trong zip quá lớn (> 1 GB). Chia nhỏ file zip rồi tải lại.")
                    break
                if _con_trong_gb() < 1:
                    bo_qua.append("Dừng giải nén: ổ đĩa sắp đầy")
                    break
                tam = os.path.join(p, ".tam-" + secrets.token_hex(4))
                da_ghi, vuot = 0, False
                try:
                    with z.open(info) as src, open(tam, "wb") as dst:
                        while True:
                            khoi = src.read(1024 * 1024)
                            if not khoi:
                                break
                            da_ghi += len(khoi)
                            if da_ghi > MAX_FONT_BYTE:
                                vuot = True
                                break
                            dst.write(khoi)
                except BaseException:
                    _xoa_tam(tam)          # loi giua chung (day o, mat dien...): khong de file do dang
                    raise
                if vuot:
                    os.remove(tam)
                    bo_qua.append(f'"{ten}": lớn bất thường')
                    continue
                ok, lydo = _luu_font_hop_le(p, tam, ten)
                if ok:
                    them += 1
                else:
                    bo_qua.append(lydo)
    except zipfile.BadZipFile:
        return False, f'"{ten_zip}" không phải file .zip hợp lệ (hoặc bị hỏng khi tải lên).', 0, []
    except OSError as e:
        return False, f"Lỗi khi giải nén: {e}", them, bo_qua
    finally:
        try:
            os.remove(tam_zip)
        except OSError:
            pass
    _fi.lam_moi_danh_sach(p)
    if not them:
        return False, f'Trong "{ten_zip}" không có font nào cài được.', 0, bo_qua
    return True, f'Đã thêm {them} font từ "{ten_zip}".', them, bo_qua

def chuan_hoa_fonts(ds):
    """Danh sach id bo font cua kich ban -> list id (chuoi, khong trung, giu thu tu).
    KHONG loc bo font da bi xoa: kich ban phai bao ro "bo font X khong con" thay vi
    am tham bo qua (xem unattend va man hinh tong ket)."""
    ra = []
    for x in ds or []:
        x = x.get("id") if isinstance(x, dict) else x
        if isinstance(x, str) and x and x not in ra:
            ra.append(ten_an_toan(x).lower())
    return ra
