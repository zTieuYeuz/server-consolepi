# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
CHONG CHINH SUA (C6): doi chieu TUNG FILE chuong trinh dang chay voi bang bam DA KY cua nha phat hanh.

Khi cai mot goi, ta giu lai phan dau goi (manifest + chu ky Ed25519) trong `updates/chu-ky/<ban>.json`. Moi lan kiem:
  1. xac minh lai chu ky bang khoa tin cay (khoa goc nhung trong ma -> tai lieu tin cay -> khoa phat hanh);
  2. bam lai cay `releases/<ban>` va so voi `manifest["tep"]` (thieu / sai / thua file).
Ket qua: ok | chua-ky (ban cai tay/dev, khong co chu ky de doi chieu - KHONG phai loi) | lech (bi sua) | khong-xac-minh (khong kiem duoc chu ky
vi tai lieu tin cay het han/thieu, nhung bam van khop ban da luu).

GIOI HAN THANG THAN: ke co quyen ROOT tren may co the sua luon ma kiem tra nay hoac xoa chu ky. Day la lop phat hien thay doi vo tinh/than thiet
(sua tay, ban sao la, o dia hong) va chan CAP NHAT TU DONG len mot he thong da bi sua - khong phai ranh gioi an ninh chong root.
"""
from consolesystem.core.nhatky import bo_qua as _bo_qua
import json
import os

from .. import phathanh as PH
from . import goi as G
from . import khoa as K

TRANG_THAI = ("ok", "chua-ky", "lech", "khong-xac-minh")


def _duong(moi, ten):
    return os.path.join(moi.thu_muc, "chu-ky", ten + ".json")


def luu_chu_ky(moi, ten, dau_b, cs):
    """Goi tu buoc `cai` ngay sau khi giai nen xong."""
    from ..store import ghi_nguyen_tu
    d = os.path.join(moi.thu_muc, "chu-ky")
    os.makedirs(d, mode=0o700, exist_ok=True)
    ghi_nguyen_tu(_duong(moi, ten), json.dumps({"dau": K.b64(dau_b), "chu_ky": K.b64(cs)}).encode("ascii"), 0o600)


def _khoa_phat_hanh(moi):
    tin_cay = moi.kho_json("tin-cay.json", {}).doc()
    ts = moi.kho_json("trang-thai.json", {}).doc()
    khoa_hl, _ = K.khoa_hop_le(tin_cay, moi.khoa_goc(), "phat-hanh", bay_gio=moi.gio(), so_hieu_da_thay=ts.get("tin_cay_so_hieu", 0))
    return khoa_hl


def kiem(moi, ten=None):
    """Tra ve {"trang_thai", "ban", "lech": [...], "so_file", "ly_do"}. Khong nem ngoai le."""
    kq = {"trang_thai": "chua-ky", "ban": ten, "lech": [], "so_file": 0, "ly_do": "", "luc": int(moi.gio())}
    try:
        ten = ten or PH.hien_tai(moi.opt)
        kq["ban"] = ten
        if not ten:
            kq["ly_do"] = "không xác định được bản đang chạy"
            return kq
        luu = json.load(open(_duong(moi, ten), encoding="utf-8"))
        dau_b, cs = K.unb64(luu["dau"]), K.unb64(luu["chu_ky"])
        dau = json.loads(dau_b.decode("utf-8"))
        if K.chuan_json(dau) != dau_b:
            raise G.LoiGoi("chữ ký lưu không ở dạng chuẩn")
    except FileNotFoundError:
        kq["ly_do"] = "bản này không cài bằng gói đã ký (cài tay/phát triển) - không có bảng băm đã ký để đối chiếu"
        return kq
    except (OSError, ValueError, KeyError, K.LoiKhoa, G.LoiGoi) as e:
        kq.update({"trang_thai": "lech", "ly_do": "chữ ký đã lưu bị hỏng/bị sửa: %s" % e})
        return kq
    ky_ok, ly_do_ky = False, ""
    try:
        G.kiem_chu_ky(dau, dau_b, cs, _khoa_phat_hanh(moi))
        ky_ok = True
    except G.LoiGoi as e:
        if "nằm trong" in str(e) or "nam trong" in str(e):
            ly_do_ky = str(e)
        else:
            kq.update({"trang_thai": "lech", "ly_do": str(e)})
            return kq
    except (K.LoiKhoa, Exception) as e:                     # tai lieu tin cay het han/thieu/khoa goc chua cau hinh: khong ket luan "bi sua"
        ly_do_ky = str(e)
    man = dau.get("manifest") or {}
    khai = man.get("tep") or {}
    goc = os.path.join(moi.opt, "releases", ten)
    try:
        that = PH.bam_cay(goc)
        rl = os.path.join(goc, PH.TEN_RELEASE)
        if os.path.exists(rl):
            that[PH.TEN_RELEASE] = PH._bam_file(rl)
    except OSError as e:
        kq.update({"trang_thai": "lech", "ly_do": "không đọc được cây chương trình: %s" % e})
        return kq
    lech = sorted([k for k in khai if that.get(k) != khai[k]] + [k for k in that if k not in khai])
    kq["so_file"] = len(khai)
    kq["lech"] = lech[:200]
    if lech:
        kq.update({"trang_thai": "lech", "ly_do": "%d file không khớp bảng băm đã ký (ví dụ: %s)" % (len(lech), ", ".join(lech[:3]))})
    elif ky_ok:
        kq["trang_thai"] = "ok"
    else:
        kq.update({"trang_thai": "khong-xac-minh", "ly_do": "băm khớp bản đã lưu nhưng không xác minh lại được chữ ký: " + ly_do_ky})
    return kq


def kiem_va_ghi(moi, bao_cao_fn=None):
    """Kiem + ghi `updates/nguyen-ven.json`. Neu moi chuyen sang 'lech' (hoac doi tap file lech) thi bao kho DUNG MOT LAN (bao_cao_fn)."""
    kq = kiem(moi)
    tep = moi.kho_json("nguyen-ven.json", {})
    cu = tep.doc()
    moi_lech = kq["trang_thai"] == "lech" and (cu.get("trang_thai") != "lech" or cu.get("lech") != kq["lech"] or cu.get("ban") != kq["ban"])
    tep.ghi(kq)
    if moi_lech and bao_cao_fn:
        try:
            bao_cao_fn("lech-ma-bam", kq["ban"], kq["ban"], kq["ly_do"][:400])
        except Exception as _loi:                                    # bao cao la phu
            _bo_qua(_loi)
    return kq


def doc_ket_qua(moi):
    return moi.kho_json("nguyen-ven.json", {}).doc()
