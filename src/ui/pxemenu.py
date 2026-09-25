"""
Console Pi - MENU PXE: may khach boot qua mang thay menu de TU CHON kich ban.

VI SAO (anh Thoai 24/09/2026, "Buoc A"): truoc day PXE chi phuc vu DUNG 1
kich ban - kich ban vua bam "Dung" tren web. Muon cai may khac bang kich
ban khac thi phai quay lai web bam "Dung" kich ban do (dung lai anh dia
~1 phut). Kieu MDT thi nguoc lai: ky thuat vien dung TAI MAY chon.

MENU 2 TANG (anh Thoai 24/09/2026: "neu nhu la kich ban de lua chon thi co
1 cai a lua chon lam gi" - ban dau phai tick tung kich ban vao menu, tick
1 cai thi menu chi co 1 muc, vo nghia):
  Menu chinh:  1. Win PE (chua co - lam sau, hien san cho biet)
               2. Install Windows  >  TAT CA kich ban Windows dang co
               Khoi dong o cung / Khoi dong lai

CACH LAM - dung lai nguyen duong da kiem chung, khong viet lai:
  - Moi kich ban Windows (du thong tin) duoc dung 1 ANH DIA RIENG bang
    CHINH ham cua nut "Dung" (unattend.dung_dia_gpt_tu_dong) voi cau hinh
    nap Y HET nut "Dung" (deployos.cauhinh_tu_kichban). Ten file
    "_menu-<ten kich ban>.img": dau "_" de trang "Tai nguyen > File boot"
    khong liet ke (xem deployos._liet_ke), duoi .img nam trong danh sach
    route /deployos/pxeboot/ duoc phep phuc vu.
  - menu.ipxe (file iPXE tai DUNG 1 lan dau moi lan boot, xem pxe.py) doi
    tu 1 dong `sanboot` thanh 1 MENU cua chinh iPXE (lenh menu/item/choose).
    Muc mac dinh chay sau N giay neu khong ai bam - giu duoc che do "cam
    vao la tu cai" cho phong may.
  - Anh dia chi dung lai khi THAT SU can: "dau van tay" (noi dung kich ban
    + dia chi Pi + boot.wim + phien ban ma sinh script) khop thi dung lai
    anh cu. Moi anh vai tram MB, dung mat ~1 phut - dung lai het moi lan
    bat PXE thi rat cham.

CHI CON MENU (anh Thoai 25/09/2026: "co menu va khi nao client chon kich
ban thi moi bat dau boot, con phan 'dung' kia thi thoi"): bo nut "Dung"
va anh dia chung windows-autounattend.img. Bat PXE = LUON la menu; che do
mang (truc tiep / khong DHCP / co DHCP) chon 1 lan khi bat PXE, luu o
menu-pxe.json - khong con phu thuoc kich ban nao.

GIOI HAN THAT:
  - Menu chu (iPXE chay TRUOC Windows, chi co man hinh chu, khong co dau
    tieng Viet, chon bang phim mui ten + Enter).
  - Moi muc dung CHE DO MANG da chon khi bat PXE (dnsmasq chi chay 1 che
    do mot luc) - dia chi Pi nhet vao anh dia la dia chi cua che do do.
  - Chi kich ban Windows (Linux van dung duong cu, chua co menu).
"""
import hashlib
import json
import os
import re
import unicodedata

from . import deployos as _d

FILE_CAUHINH = os.path.join(_d.DEPLOY_DIR, "menu-pxe.json")
TIEN_TO_ANH = "_menu-"
CHO_TOI_DA = 300          # giay
KIEU_HOP_LE = [k for k, _t, _m in _d.KIEU_BOOT]
# Mac dinh "mang co DHCP" (proxyDHCP): khong bao gio tranh cap IP voi router
# cua khach - kieu an toan nhat khi cam vao mang co san (loi that 25/09:
# "mang khong DHCP" tren mang cong ty -> may khach nghe nham router).
MAC_DINH = {"kieu_boot": "mang_co_dhcp", "cho_giay": 30}


# ---------------------------------------------------------------- cau hinh
def doc_cauhinh():
    c = dict(MAC_DINH)
    try:
        with open(FILE_CAUHINH, encoding="utf-8") as f:
            c.update({k: v for k, v in json.load(f).items() if k in MAC_DINH})
    except (OSError, ValueError):
        pass
    try:
        c["cho_giay"] = max(0, min(CHO_TOI_DA, int(c["cho_giay"])))
    except (TypeError, ValueError):
        c["cho_giay"] = MAC_DINH["cho_giay"]
    if c["kieu_boot"] not in KIEU_HOP_LE:
        c["kieu_boot"] = MAC_DINH["kieu_boot"]
    return c


def luu_cauhinh(kieu_boot=None, cho_giay=None):
    """Luu che do mang va/hoac so giay cho (None = giu nguyen gia tri cu)."""
    c = doc_cauhinh()
    if kieu_boot is not None:
        if kieu_boot not in KIEU_HOP_LE:
            return False, "Chế độ mạng không hợp lệ."
        c["kieu_boot"] = kieu_boot
    if cho_giay is not None:
        try:
            c["cho_giay"] = max(0, min(CHO_TOI_DA, int(cho_giay)))
        except (TypeError, ValueError):
            return False, "Số giây chờ không hợp lệ."
    try:
        os.makedirs(os.path.dirname(FILE_CAUHINH), exist_ok=True)
        with open(FILE_CAUHINH, "w", encoding="utf-8") as f:
            json.dump(c, f, ensure_ascii=False, indent=1)
    except OSError as e:
        return False, f"Không lưu được: {e}"
    return True, "Đã lưu cài đặt menu PXE."


def kichban_windows():
    """TAT CA kich ban Windows (khong can tick nua), theo thu tu ten."""
    return [k for k in _d.danh_sach_kichban() if k.get("os_ho") == "windows"]


def thieu_cua(kb, kieu_boot=None):
    """Nhung gi kich ban con thieu de dung duoc anh dia (rong = du)."""
    d = _d.cauhinh_tu_kichban(kb)
    if kieu_boot:
        d["kieu_boot"] = kieu_boot
    return _d.thieu_gi(d)


# ------------------------------------------------------------ anh dia rieng
def ten_anh(ten_file_kichban):
    goc = ten_file_kichban[:-5] if ten_file_kichban.endswith(".json") else ten_file_kichban
    # Ten nay nam trong URL cua lenh sanboot - chi giu ky tu an toan cho URL
    # (ten_an_toan con cho phep dau cach, dau cach se lam gay lenh iPXE).
    return TIEN_TO_ANH + re.sub(r"[^A-Za-z0-9._-]", "_", goc)[:120] + ".img"


def _dau_van_tay(kb, dia_chi_pi):
    """
    Thay doi BAT KY thu gi lam anh dia khac di thi dau van tay phai khac:
    noi dung kich ban, dia chi Pi nhet vao anh, boot.wim cua OS do, va ma
    nguon sinh noi dung anh (unattend.py, deployos.py).

    Ma nguon bam theo NOI DUNG, khong theo ngay gio: cap-nhat-pi.sh chep lai
    moi file nen ngay gio luon doi - bam theo ngay gio thi lan bat PXE dau
    sau MOI lan cap nhat deu dung lai het anh (~1 phut/kich ban, anh Thoai
    cho 3 phut ngay 25/09/2026) du code tao anh khong doi 1 chu.
    """
    from . import unattend as _u
    h = hashlib.sha256()
    kb_sach = {k: v for k, v in kb.items() if not k.startswith("_")}
    h.update(json.dumps(kb_sach, sort_keys=True, ensure_ascii=False).encode())
    h.update(dia_chi_pi.encode())
    wim = _d.duong_boot_wim(kb.get("os_id", ""))
    try:  # boot.wim vai tram MB - bam ca file thi cham, kich thuoc+gio la du
        st = os.stat(wim)
        h.update(f"{wim}:{st.st_size}:{int(st.st_mtime)}".encode())
    except OSError:
        h.update(f"{wim}:khong-co".encode())
    for p in (_u.__file__, _d.__file__):
        try:
            with open(p, "rb") as f:
                h.update(hashlib.sha256(f.read()).digest())
        except OSError:
            h.update(f"{p}:khong-co".encode())
    return h.hexdigest()[:16]


def _con_trong_mb():
    try:
        st = os.statvfs(_d.BOOT_DIR)
        return st.f_bavail * st.f_frsize // (1024 * 1024)
    except OSError:
        return 0


def dung_anh_menu(dia_chi_pi, kieu_boot):
    """
    Dung (hoac dung lai neu da cu) anh dia cho MOI kich ban Windows. Xoa
    anh cua kich ban da xoa va anh chung cu (windows-autounattend.img). Tra ve danh sach dong ket qua de hien cho nguoi dung.
    """
    from . import unattend as _u
    ket_qua = []
    can_giu = set()
    for kb in kichban_windows():
        ten = kb.get("ten_kichban", kb["_file"])
        d = _d.cauhinh_tu_kichban(kb)
        # Moi muc dung che do mang cua kich ban dang Dung - xem GIOI HAN.
        d["kieu_boot"] = kieu_boot
        thieu = _d.thieu_gi(d)
        if thieu:
            ket_qua.append(f'"{ten}": bỏ qua - ' + ", ".join(thieu) + ".")
            continue
        anh = ten_anh(kb["_file"])
        can_giu.add(anh)
        dau = _dau_van_tay(kb, dia_chi_pi)
        cu = _u.doc_dau_kichban(anh)
        if (cu and cu.get("dau_van_tay") == dau
                and os.path.isfile(os.path.join(_d.BOOT_DIR, anh))):
            ket_qua.append(f'"{ten}": ảnh đĩa vẫn đúng, dùng lại.')
            continue
        # Moi anh ~ kich thuoc boot.wim + file boot. Doi 1.5 lan + 300MB
        # cho chac (co ca file tam trong luc dung).
        try:
            can_mb = os.path.getsize(_d.duong_boot_wim(kb.get("os_id", ""))) * 3 // 2 // (1024 * 1024) + 300
        except OSError:
            can_mb = 1200
        if _con_trong_mb() < can_mb:
            ket_qua.append(f'"{ten}": KHÔNG dựng được - ổ đĩa còn {_con_trong_mb()} MB, '
                           f'cần khoảng {can_mb} MB.')
            can_giu.discard(anh)
            continue
        ok, msg = _u.dung_dia_gpt_tu_dong(d, dia_chi_pi, ten_dia=anh,
                                          dau_them={"dau_van_tay": dau})
        ket_qua.append(f'"{ten}": ' + ("đã dựng ảnh đĩa." if ok else f"LỖI - {msg}"))
        if not ok:
            can_giu.discard(anh)
    # Anh chung cu cua nut "Dung" (da bo) - khong con muc nao tro toi, ~500 MB.
    for x in (_u.TEN_DIA_GPT_TU_DONG, _u.TEN_DIA_GPT_TU_DONG + ".json"):
        try:
            os.remove(os.path.join(_d.BOOT_DIR, x))
        except OSError:
            pass
    # Don anh cua kich ban da xoa / khong con la Windows - moi anh vai tram MB.
    try:
        for n in os.listdir(_d.BOOT_DIR):
            if n.startswith(TIEN_TO_ANH) and n.endswith(".img") and n not in can_giu:
                for x in (n, n + ".json"):
                    try:
                        os.remove(os.path.join(_d.BOOT_DIR, x))
                    except OSError:
                        pass
    except OSError:
        pass
    return ket_qua


# ---------------------------------------------------------------- menu iPXE
def _chu_ipxe(s, dai=60):
    """
    Chu cho menu iPXE: iPXE chi ve duoc ASCII -> bo dau tieng Viet; bo ky
    tu dac biet cua iPXE ($ { } ...) de ten kich ban khong the chen lenh.
    """
    s = (s or "").replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^A-Za-z0-9 .,_()+:/-]", " ", s)
    s = re.sub(r" +", " ", s).strip()
    return s[:dai] or "(khong ten)"


def muc_menu():
    """
    Danh sach (nhan, file anh) theo DUNG thu tu hien trong menu - dung cho
    ca script iPXE lan phan xem truoc tren web. Chi kich ban DA CO anh dia.
    """
    muc = []
    for kb in kichban_windows():
        anh = ten_anh(kb["_file"])
        if os.path.isfile(os.path.join(_d.BOOT_DIR, anh)):
            muc.append((kb.get("ten_kichban", kb["_file"]), anh))
    return muc


def sinh_script(goc):
    """
    Script iPXE menu 2 tang. goc = http://<dia chi Pi>/deployos/pxeboot

    Menu chinh -> "Install Windows" -> menu con liet ke kich ban. Menu
    chinh het gio -> khoi dong o cung (may lo boot qua mang KHONG bao gio
    tu cai); menu con cho nguoi bam, KHONG tu chon. Esc o menu con = quay
    lai menu chinh, o menu chinh = o cung.
    """
    c = doc_cauhinh()
    muc = muc_menu()
    # --timeout tinh bang mili giay; 0 giay = cho mai den khi co nguoi bam.
    cho = f"--timeout {c['cho_giay'] * 1000} " if c["cho_giay"] > 0 else ""
    dong = ["#!ipxe", ":menu",
            "menu Console System - Cai dat qua mang",
            "item --gap -- Chon bang phim mui ten + Enter:",
            "item --gap -- ",
            # iPXE "gap" = dong chu KHONG chon duoc - WinPE chua co (lam sau).
            "item --gap -- 1. Win PE (chua co - sap ra mat)",
            f"item win 2. Install Windows > ({len(muc)} kich ban)",
            "item --gap -- ",
            "item odia Khoi dong o cung (KHONG cai gi)",
            "item lai Khoi dong lai may",
            f"choose {cho}--default odia chon || goto odia",
            "goto ${chon}", "",
            ":win",
            "menu Install Windows - chon kich ban cai dat"]
    if not muc:
        dong.append("item --gap -- (Chua co kich ban Windows nao dung duoc)")
    for i, (nhan, _anh) in enumerate(muc):
        dong.append(f"item kb{i} {_chu_ipxe(nhan)}")
    dong += ["item --gap -- ",
             "item menu < Quay lai menu chinh"]
    # Menu con: KHONG dem nguoc - chi cai khi co nguoi chon.
    dong += [f"choose --default {'kb0' if muc else 'menu'} chon || goto menu",
             "goto ${chon}", ""]
    for i, (nhan, anh) in enumerate(muc):
        dong += [f":kb{i}",
                 # Anh GPT+FAT32 chi boot duoc bang UEFI (MBR khong co ma
                 # boot) - may BIOS/Legacy se DUNG IM sau "Booting from SAN
                 # device 0x80". Chan truoc, noi ro cach sua.
                 "iseq ${platform} efi || goto bios",
                 f"echo Dang nap: {_chu_ipxe(nhan)}",
                 f"sanboot --no-describe {goc}/{anh} || goto loi", ""]
    dong += [":odia",
             "echo Khoi dong tu o cung...",
             "exit", "",
             ":lai",
             "reboot", "",
             ":bios",
             "echo",
             "echo LOI: may nay dang khoi dong kieu BIOS / Legacy.",
             "echo Anh cai Windows cua Console System CHI chay tren UEFI.",
             "echo Vao BIOS/Setup cua may (hoac Firmware cua may ao) chon UEFI,",
             "echo tat Secure Boot, roi boot qua mang lai.",
             "prompt Bam phim bat ky de quay lai menu...",
             "goto win", "",
             ":loi",
             "echo LOI: khong nap duoc anh dia cai dat tu Console System.",
             "prompt Bam phim bat ky de quay lai menu...",
             "goto win", ""]
    return "\n".join(dong)


# ------------------------------------------------------------------- web
def _xem_truoc(c, muc):
    """Ve lai 2 man hinh menu may khach se thay (cung chu voi sinh_script)."""
    # iPXE gop nhieu dau cach thanh 1 -> xem truoc cung khong can can cot.
    chinh = ["  Console System - Cai dat qua mang", "",
             "    Chon bang phim mui ten + Enter:", "",
             "    1. Win PE (chua co - sap ra mat)",
             f"    2. Install Windows > ({len(muc)} kich ban)", "",
             "  > Khoi dong o cung (KHONG cai gi)",
             "    Khoi dong lai may"]
    con = ["  Install Windows - chon kich ban cai dat", ""]
    if not muc:
        con.append("    (Chua co kich ban Windows nao dung duoc)")
    for i, (nhan, _a) in enumerate(muc):
        con.append(("  > " if i == 0 else "    ") + _chu_ipxe(nhan))
    con += ["", ("  > " if not muc else "    ") + "< Quay lai menu chinh"]
    if c["cho_giay"]:
        chinh += ["", f"  (khong ai bam: tu khoi dong o cung sau {c['cho_giay']} giay)"]
    con += ["", "  (cho den khi co nguoi chon - khong tu cai)"]
    return "\n".join(chinh), "\n".join(con)


def trang_thai_html(k, esc):
    """Cot "Menu PXE" cua bang kich ban: kich ban nay co hien trong menu khong."""
    if k.get("os_ho") != "windows":
        return '<small style="color:#8b93a1;">chỉ Windows</small>'
    thieu = thieu_cua(k)
    if thieu:
        return (f'<small style="color:#f59e0b;">thiếu: '
                f'{esc(", ".join(thieu))}</small>')
    return '<small style="color:#4CAF50;">&#10003; Có trong menu</small>'
