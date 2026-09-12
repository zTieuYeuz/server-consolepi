"""
Console Pi - Tra cuu THAM SO CAI DAT IM LANG cua phan mem.

VI SAO CO MUC NAY: moi bo cai lai co mot kieu tham so cai im lang rieng
(/S, /VERYSILENT, /qn, -s, --silent...) - khong the doan, chi co the tra.
Truoc day anh Thoai giu bang nay trong 1 file Excel roi mo tren may tinh,
nhung luc di hien truong thi trong tay chi co Console Pi. Dua han vao day
de tra ngay tren thiet bi, va sua duoc ngay khi tim ra tham so moi.

DU LIEU goc lay tu chinh file MDT.xlsx cua anh Thoai (giu nguyen tung
chu, khong "lam sach" gi ca - vi do la ghi chep that da dung duoc viec).
"""

import json
import os
import time
import unicodedata

from .duongdan import FILE_THAM_SO as FILE_DU_LIEU

# Ten cot - dung chung giua du lieu, giao dien va tim kiem
CAC_COT = [
    ("phan_mem", "Phần mềm"),
    ("cai_dat", "Tham số CÀI ĐẶT"),
    ("go_cai", "Tham số GỠ CÀI"),
    ("kem_cmd", "Kèm CMD"),
    ("ghi_chu", "Ghi chú"),
]


def bo_dau(s):
    """
    Bo dau tieng Viet + ha chu thuong, de tim kiem khong phu thuoc dau.

    LY DO THAT: tren man hinh cam ung cua Console Pi, go tieng Viet co dau
    rat cham (phai bat bo go, phai go dau). Nguoi dung se go "thoi gian",
    "may in", "chung chi" - phai tim ra duoc "thời gian", "máy in",
    "chứng chỉ". Bo dau CA HAI PHIA khi so sanh thi moi lam duoc.

    Dac biet phai xu ly rieng chu 'đ'/'Đ': unicodedata KHONG tach duoc
    (no la 1 ky tu doc lap, khong phai 'd' + dau), nen neu khong thay tay
    thi go "dia" se khong ra "đĩa".
    """
    if not s:
        return ""
    s = str(s).replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower().strip()


def _bao_dam_file():
    thu_muc = os.path.dirname(FILE_DU_LIEU)
    if thu_muc and not os.path.isdir(thu_muc):
        os.makedirs(thu_muc, exist_ok=True)


def danh_sach():
    """Doc toan bo bang. Tra ve [] neu chua co file (lan dau chay)."""
    try:
        with open(FILE_DU_LIEU, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else []
    except (OSError, ValueError):
        return []


def _ghi(ds):
    _bao_dam_file()
    tam = FILE_DU_LIEU + ".tmp"
    try:
        with open(tam, "w", encoding="utf-8") as f:
            json.dump(ds, f, ensure_ascii=False, indent=1)
        # Ghi ra file tam roi doi ten: neu mat dien giua chung thi file cu
        # van con nguyen ven, khong bi cut mat nua chung.
        os.replace(tam, FILE_DU_LIEU)
        return True, ""
    except OSError as e:
        return False, str(e)


def _ma_moi(ds):
    """Sinh ma khong trung - dung thoi diem nen khong bao gio quay vong."""
    ma = f"ts{int(time.time() * 1000)}"
    dang_co = {x.get("id") for x in ds}
    i = 0
    while ma in dang_co:
        i += 1
        ma = f"ts{int(time.time() * 1000)}_{i}"
    return ma


def them(muc):
    """Them 1 dong moi. Bat buoc co ten phan mem."""
    ds = danh_sach()
    ten = (muc.get("phan_mem") or "").strip()
    if not ten:
        return False, "Chưa điền tên phần mềm."
    moi = {"id": _ma_moi(ds)}
    for khoa, _nhan in CAC_COT:
        moi[khoa] = (muc.get(khoa) or "").strip()
    ds.append(moi)
    ok, err = _ghi(ds)
    if not ok:
        return False, f"Không lưu được: {err}"
    return True, f'Đã thêm "{ten}".'


def sua(ma, muc):
    ds = danh_sach()
    for x in ds:
        if x.get("id") == ma:
            ten = (muc.get("phan_mem") or "").strip()
            if not ten:
                return False, "Chưa điền tên phần mềm."
            for khoa, _nhan in CAC_COT:
                x[khoa] = (muc.get(khoa) or "").strip()
            ok, err = _ghi(ds)
            if not ok:
                return False, f"Không lưu được: {err}"
            return True, f'Đã sửa "{ten}".'
    return False, "Không tìm thấy dòng cần sửa."


def xoa(ma):
    ds = danh_sach()
    con = [x for x in ds if x.get("id") != ma]
    if len(con) == len(ds):
        return False, "Không tìm thấy dòng cần xoá."
    ten = next((x.get("phan_mem", "") for x in ds if x.get("id") == ma), "")
    ok, err = _ghi(con)
    if not ok:
        return False, f"Không xoá được: {err}"
    return True, f'Đã xoá "{ten}".'


def nap_lan_dau(cac_dong):
    """
    Nap du lieu ban dau (tu file Excel cua anh Thoai) - CHI khi bang con
    trong. Khong bao gio ghi de du lieu dang co: anh Thoai co the da them
    tham so moi tim ra duoc, ghi de la mat het.
    """
    if danh_sach():
        return False, "Bảng đã có dữ liệu - không nạp đè."
    ds = []
    for i, dong in enumerate(cac_dong):
        muc = {"id": f"ts{i:04d}"}
        for khoa, _nhan in CAC_COT:
            muc[khoa] = (dong.get(khoa) or "").strip()
        if muc["phan_mem"]:
            ds.append(muc)
    ok, err = _ghi(ds)
    if not ok:
        return False, err
    return True, f"Đã nạp {len(ds)} dòng."
