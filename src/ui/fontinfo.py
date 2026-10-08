# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi - Doc thong tin font (.ttf / .otf / .ttc / .otc) de quan ly "bo font"
trong Deployment OS va sinh danh sach cai cho may Windows.

VI SAO TU VIET BO DOC NAY (khong dung fontTools): Pi/ISO khong co san thu vien do
va quy tac 11 la khong them goi he thong neu khong that su can. Doc bang `name`
cua sfnt chi can ~80 dong struct, khong phu thuoc gi.

Windows cai font cho TOAN MAY bang 2 viec:
  1. chep file vao C:\\Windows\\Fonts
  2. ghi 1 gia tri vao HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts:
         "<Ten day du> (TrueType)" = "<ten file>"        (OpenType cho .otf dang CFF)
     Ten gia tri la nhan hien thi; tep that moi la thu Windows nap. Font .ttc (nhieu
     kieu chu trong 1 file) ghi ten cac kieu noi bang " & ".
Ket qua doc duoc luu o `_fonts.json` trong thu muc bo font de script cai tren may
Windows (cai-font.ps1) doc thang, khong phai tu phan tich font.
"""
import json
import os
import re
import struct

DUOI_FONT = {".ttf", ".otf", ".ttc", ".otc"}
TEN_DANH_SACH = "_fonts.json"
TEN_THONGTIN = "_thongtin.json"
_NOI_BO = {TEN_DANH_SACH, TEN_THONGTIN}

# 4 byte dau cua file sfnt hop le: TrueType 1.0, 'true' (Apple), 'OTTO' (CFF), 'ttcf' (bo)
_MA_SFNT = {b"\x00\x01\x00\x00", b"true", b"OTTO"}
_MA_BO = b"ttcf"
_GIOI_HAN_BANG_NAME = 2 * 1024 * 1024     # bang `name` that khong bao gio lon the


def ten_file_an_toan(ten):
    """Giu chu cai (ke ca co dau), so, dau cham, gach, khoang trang, ngoac.
    Bo moi thanh phan duong dan. Ten font that thuong la ASCII nhung co font
    dat ten tieng Viet - khong doi chu co dau thanh '_' de khoi trung ten."""
    ten = os.path.basename((ten or "").replace("\\", "/")).strip()
    ten = re.sub(r"[^\w.+() \-]", "_", ten, flags=re.UNICODE)
    ten = ten.lstrip(".").strip()
    return ten[:120]


def la_duoi_font(ten):
    return os.path.splitext(ten or "")[1].lower() in DUOI_FONT


def _giai_ma(raw, nen, ma_hoa, ngon):
    try:
        if nen in (0, 3):
            return raw.decode("utf-16-be")
        if nen == 1:
            return raw.decode("mac_roman" if ma_hoa == 0 else "latin-1")
    except UnicodeDecodeError:
        return ""
    return ""


def _chon_chuoi(bang, ma):
    """Chon chuoi `name` ID `ma` theo thu tu uu tien: Windows tieng Anh (0x409) ->
    Windows bat ky -> Unicode -> Macintosh. Tra "" neu khong co."""
    tot = ("", 99)
    for (nen, ma_hoa, ngon, nid, chuoi) in bang:
        if nid != ma or not chuoi.strip():
            continue
        if nen == 3 and ngon == 0x409:
            diem = 0
        elif nen == 3:
            diem = 1
        elif nen == 0:
            diem = 2
        else:
            diem = 3
        if diem < tot[1]:
            tot = (chuoi.strip(), diem)
    return tot[0]


def _doc_mot_font(f, goc, kich_thuoc_file):
    """Doc 1 font sfnt bat dau o `goc`. Tra dict hoac None neu khong hop le."""
    f.seek(goc)
    dau = f.read(12)
    if len(dau) < 12 or dau[:4] not in _MA_SFNT:
        return None
    so_bang = struct.unpack(">H", dau[4:6])[0]
    if not 1 <= so_bang <= 200:
        return None
    thu_muc = f.read(16 * so_bang)
    if len(thu_muc) < 16 * so_bang:
        return None
    bang = {}
    for i in range(so_bang):
        tag, _ck, vt, dai = struct.unpack(">4sIII", thu_muc[i * 16:i * 16 + 16])
        bang[tag] = (vt, dai)
    if b"name" not in bang or b"head" not in bang or b"cmap" not in bang:
        return None          # thieu bang bat buoc cua font -> khong phai font dung duoc
    vt, dai = bang[b"name"]
    if dai < 6 or dai > _GIOI_HAN_BANG_NAME or vt + dai > kich_thuoc_file:
        return None
    f.seek(vt)
    nd = f.read(dai)
    if len(nd) < dai:
        return None
    _fmt, so_ban_ghi, off_chuoi = struct.unpack(">HHH", nd[:6])
    chuoi = []
    for i in range(min(so_ban_ghi, 2000)):
        o = 6 + i * 12
        if o + 12 > len(nd):
            break
        nen, ma_hoa, ngon, nid, dl, vo = struct.unpack(">HHHHHH", nd[o:o + 12])
        if nid not in (1, 2, 4, 16, 17):
            continue
        raw = nd[off_chuoi + vo:off_chuoi + vo + dl]
        chuoi.append((nen, ma_hoa, ngon, nid, _giai_ma(raw, nen, ma_hoa, ngon)))
    ho = _chon_chuoi(chuoi, 16) or _chon_chuoi(chuoi, 1)
    kieu = _chon_chuoi(chuoi, 17) or _chon_chuoi(chuoi, 2)
    day_du = _chon_chuoi(chuoi, 4) or (f"{ho} {kieu}".strip() if ho else "")
    return {"ho": ho, "kieu": kieu, "ten": day_du,
            "cff": b"CFF " in bang or b"CFF2" in bang}


def doc_font(duong):
    """
    Doc 1 file font. Tra dict {"ten", "ho", "kieu", "loai"} hoac None neu file
    KHONG phai font hop le (sai dinh dang, hong, hoac chi la web font .woff).
    """
    try:
        kich = os.path.getsize(duong)
        with open(duong, "rb") as f:
            ma = f.read(4)
            if ma == _MA_BO:
                f.seek(8)
                so = struct.unpack(">I", f.read(4))[0]
                if not 1 <= so <= 64:
                    return None
                vi_tri = list(struct.unpack(f">{so}I", f.read(4 * so)))
                cac = [_doc_mot_font(f, v, kich) for v in vi_tri]
                cac = [c for c in cac if c]
                if not cac:
                    return None
                ten = " & ".join(dict.fromkeys(c["ten"] for c in cac if c["ten"]))
                ho = ", ".join(dict.fromkeys(c["ho"] for c in cac if c["ho"]))
                return {"ten": ten, "ho": ho, "kieu": f"{len(cac)} kiểu trong 1 file",
                        "loai": "TrueType"}
            if ma not in _MA_SFNT:
                return None
            c = _doc_mot_font(f, 0, kich)
            if not c:
                return None
            return {"ten": c["ten"], "ho": c["ho"], "kieu": c["kieu"],
                    "loai": "OpenType" if c["cff"] else "TrueType"}
    except (OSError, struct.error):
        return None


def la_font_hop_le(duong):
    return doc_font(duong) is not None


def lam_moi_danh_sach(thu_muc):
    """
    Quet thu muc bo font, doc ten tung font (dung lai ket qua cu neu file khong doi:
    ten + kich thuoc + mtime) roi ghi `_fonts.json`. Tra ve danh sach:
        [{"file", "ten", "ho", "kieu", "loai", "reg", "byte"}, ...]
    "reg" la ten gia tri ghi vao registry Windows - DUY NHAT trong bo.
    File trong thu muc ma khong phai font hop le thi BO QUA (khong dua vao danh sach).
    """
    cu = {}
    try:
        with open(os.path.join(thu_muc, TEN_DANH_SACH), encoding="utf-8") as f:
            for m in json.load(f).get("fonts", []):
                cu[m["file"]] = m
    except (OSError, ValueError, KeyError, TypeError):
        pass

    ra = []
    try:
        ten_ds = sorted(os.listdir(thu_muc), key=str.lower)
    except OSError:
        return ra
    for ten in ten_ds:
        if ten in _NOI_BO or not la_duoi_font(ten):
            continue
        fp = os.path.join(thu_muc, ten)
        try:
            st = os.stat(fp)
        except OSError:
            continue
        if not os.path.isfile(fp):
            continue
        c = cu.get(ten)
        if c and c.get("byte") == st.st_size and c.get("mtime") == int(st.st_mtime):
            ra.append(c)
            continue
        tt = doc_font(fp)
        if not tt:
            continue
        ra.append({"file": ten, "ten": tt["ten"] or os.path.splitext(ten)[0],
                   "ho": tt["ho"], "kieu": tt["kieu"], "loai": tt["loai"],
                   "byte": st.st_size, "mtime": int(st.st_mtime)})

    # Ten gia tri registry duy nhat trong bo: trung ten day du (2 file cung 1 font)
    # thi them ten file de ca 2 deu duoc dang ky
    da = {}
    for m in ra:
        goc = f'{m["ten"]} ({m["loai"]})'
        if goc.lower() in da:
            goc = f'{m["ten"]} [{os.path.splitext(m["file"])[0]}] ({m["loai"]})'
        da[goc.lower()] = True
        m["reg"] = goc
    try:
        moi = json.dumps({"fonts": ra}, ensure_ascii=False, indent=1)
        dich = os.path.join(thu_muc, TEN_DANH_SACH)
        try:
            with open(dich, encoding="utf-8") as f:
                if f.read() == moi:
                    return ra          # khong doi: khong ghi lai (trang danh sach goi ham nay moi lan mo)
        except OSError:
            pass
        tam = dich + ".tmp"
        with open(tam, "w", encoding="utf-8") as f:
            f.write(moi)
        os.replace(tam, dich)
    except OSError:
        pass
    return ra
