"""
Console Pi - MENU PXE: may khach boot qua mang thay menu de TU CHON kich ban.

VI SAO (anh Thoai 24/09/2026, "Buoc A"): truoc day PXE chi phuc vu DUNG 1
kich ban - kich ban vua bam "Dung" tren web. Muon cai may khac bang kich
ban khac thi phai quay lai web bam "Dung" kich ban do (dung lai anh dia
~1 phut). Kieu MDT thi nguoc lai: ky thuat vien dung TAI MAY chon.

MENU 2 TANG (anh Thoai 24/09/2026: "neu nhu la kich ban de lua chon thi co
1 cai a lua chon lam gi" - ban dau phai tick tung kich ban vao menu, tick
1 cai thi menu chi co 1 muc, vo nghia):
  Menu chinh:  1. Win PE - cuu ho may > (moi bo Windows co boot.wim 1 muc)
               2. Install Windows  >  TAT CA kich ban Windows dang co
               Khoi dong o cung / Khoi dong lai

CACH LAM (tu 1.5.0 - wimboot, xem unattend: FILE NHUNG QUA WIMBOOT):
  - Moi kich ban Windows (du thong tin) co 1 thu muc BOOT_DIR/_pxe/<ten>/
    chua cac file nho (winpeshl.ini, autounattend.xml, deploy.cmd,
    diskpart*.txt, unattend.xml, *.ps1) sinh bang CHINH cau hinh cua kich ban
    (deployos.cauhinh_tu_kichban). Vai chuc KB, ghi lai MOI lan bat PXE /
    luu kich ban - duoi 1 giay, khong can "dau van tay" nhu thoi anh dia.
  - Muc menu = `kernel wimboot` + `initrd` tung file + boot.wim GOC cua he
    dieu hanh. Chay tren BIOS, UEFI, UEFI + Secure Boot.
  - Truoc 1.5.0: moi kich ban 1 anh dia GPT+FAT32 ~500 MB (dung ~1 phut) +
    `sanboot` - chi chay UEFI tat Secure Boot (BIOS dung im o "Booting from
    SAN device 0x80", loi that anh Thoai 25/09/2026). Anh cu tu xoa.

CHI CON MENU (anh Thoai 25/09/2026: "co menu va khi nao client chon kich
ban thi moi bat dau boot, con phan 'dung' kia thi thoi"): bo nut "Dung"
va anh dia chung windows-autounattend.img. Bat PXE = LUON la menu; che do
mang (truc tiep / khong DHCP / co DHCP) chon 1 lan khi bat PXE, luu o
menu-pxe.json - khong con phu thuoc kich ban nao.

GIOI HAN THAT:
  - Menu chu (iPXE chay TRUOC Windows, chi co man hinh chu, khong co dau
    tieng Viet, chon bang phim mui ten + Enter).
  - Moi muc dung CHE DO MANG da chon khi bat PXE (dnsmasq chi chay 1 che
    do mot luc) - dia chi Pi ghi trong deploy.cmd la dia chi cua che do do.
  - Chi kich ban Windows (Linux van dung duong cu, chua co menu).
"""
import json
import os
import re
import unicodedata

from . import deployos as _d

FILE_CAUHINH = os.path.join(_d.DEPLOY_DIR, "menu-pxe.json")
TIEN_TO_ANH = "_menu-"      # anh dia GPT cu (< 1.5.0) - chi con de don rac
THU_MUC_PXE = "_pxe"        # BOOT_DIR/_pxe/<kich ban>/ = file wimboot chen vao
THU_MUC_WINPE = "_winpe"    # BOOT_DIR/_pxe/_winpe/startnet.cmd cho WinPE cuu ho
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
    """Nhung gi kich ban con thieu de vao duoc menu (rong = du)."""
    d = _d.cauhinh_tu_kichban(kb)
    if kieu_boot:
        d["kieu_boot"] = kieu_boot
    return _d.thieu_gi(d)


# ------------------------------------------------- file nhung rieng (wimboot)
def ten_thu_muc(ten_file_kichban):
    """Thu muc file nhung cua 1 kich ban: BOOT_DIR/_pxe/<ten nay>/.
    Nam trong URL cua lenh initrd - chi giu ky tu an toan cho URL."""
    goc = ten_file_kichban[:-5] if ten_file_kichban.endswith(".json") else ten_file_kichban
    return re.sub(r"[^A-Za-z0-9._-]", "_", goc)[:120].lstrip(".") or "_"


def _duong_pxe(*phan):
    return os.path.join(_d.BOOT_DIR, THU_MUC_PXE, *phan)


def _don_anh_cu():
    """Anh dia GPT cua ban < 1.5.0 (moi cai ~500 MB) - khong con dung nua."""
    from . import unattend as _u
    try:
        for n in os.listdir(_d.BOOT_DIR):
            if ((n.startswith(TIEN_TO_ANH) and (n.endswith(".img") or n.endswith(".img.json")))
                    or n in (_u.TEN_DIA_GPT_TU_DONG, _u.TEN_DIA_GPT_TU_DONG + ".json")):
                try:
                    os.remove(os.path.join(_d.BOOT_DIR, n))
                except OSError:
                    pass
    except OSError:
        pass


def sinh_startnet_winpe():
    r"""
    startnet.cmd cho muc "Win PE - cuu ho": chay tren boot.wim image 2 (moi
    truong Setup) + man hinh huong dan. KHONG dung image 1: trong boot.wim cua
    bo cai, image 1 cau hinh SYSTEMROOT = X:\$windows.~bt (danh rieng cho
    Setup) - boot rieng bao "Windows PE cannot start" (lab 26/09/2026).
    winpeshl.ini (sinh_winpeshl_cuu_ho) mo cmd chay file nay thay cho Setup. Nap driver card mang "cho anh boot" (neu
    co) truoc wpeinit - cung cach deploy.cmd lam.

    KHONG nhet mat khau Samba cua kho vao day: ai dung truoc may cung chon
    duoc muc nay (khong phai kich ban da duyet), lo mat khau la lo kho.
    """
    from . import unattend as _u
    return "\r\n".join([
        "@echo off",
        "title Console System - WinPE cuu ho",
        # Tung dong + goto (khong gop vao khoi ngoac: "(*.inf)" ben trong
        # de lam vo ngoac cua khoi if).
        f"if not exist X:\\Windows\\System32\\{_u.TEN_WIM_DRIVER} goto het_driver",
        f"dism /apply-image /imagefile:X:\\Windows\\System32\\{_u.TEN_WIM_DRIVER} "
        "/index:1 /applydir:X:\\ConsolePiDrivers >nul 2>&1",
        'for /r X:\\ConsolePiDrivers %%i in (*.inf) do drvload "%%i" >nul 2>&1',
        ":het_driver",
        "wpeinit",
        "cls",
        "echo ==============================================================",
        "echo   CONSOLE SYSTEM - WinPE CUU HO MAY",
        "echo ==============================================================",
        "echo   diskpart            - xem / chia lai o dia (list disk, list vol)",
        "echo   notepad             - mo hop thoai File-Open de duyet va CHEP file",
        "echo   bcdboot C:\\Windows  - tao lai boot loader khi Windows khong boot",
        "echo   chkdsk C: /f        - sua loi o dia",
        "echo   net use Z: \\\\may\\thu-muc /user:ten  - noi thu muc chia se",
        "echo   wpeutil reboot      - khoi dong lai may",
        "echo ==============================================================",
        "ipconfig | find \"IPv4\"",
        "echo.",
    ]) + "\r\n"


def sinh_winpeshl_cuu_ho():
    """Thay Setup bang cua so lenh chay startnet.cmd cuu ho."""
    return ("[LaunchApps]\r\n"
            "%SYSTEMROOT%\\System32\\cmd.exe, /k %SYSTEMROOT%\\System32\\startnet.cmd\r\n")


def muc_winpe():
    """(ten hien thi, os_id) cua moi bo Windows CO boot.wim - moi bo 1 muc
    WinPE (boot.wim cua ban nao thi co driver cua ban do)."""
    return [(o["ten_hien_thi"], o["id"]) for o in _d.danh_sach_os()
            if o.get("os_ho") == "windows" and o.get("co_boot_wim")]


def chuan_bi_menu(dia_chi_pi, kieu_boot):
    """
    Ghi bo file nhung cho MOI kich ban Windows du thong tin (vai chuc KB moi
    kich ban, duoi 1 giay - khong con dung anh dia 500 MB/1 phut nhu truoc
    1.5.0) + dong goi driver cho anh boot. Xoa thu muc cua kich ban da xoa va
    anh dia GPT cu. Tra ve danh sach dong ket qua de hien cho nguoi dung.
    """
    import shutil
    from . import unattend as _u
    ket_qua = []
    can_giu = set()
    os.makedirs(_duong_pxe(), exist_ok=True)
    for kb in kichban_windows():
        ten = kb.get("ten_kichban", kb["_file"])
        d = _d.cauhinh_tu_kichban(kb)
        d["kieu_boot"] = kieu_boot
        thieu = _d.thieu_gi(d)
        if not thieu and not os.path.isfile(_d.duong_boot_wim(kb.get("os_id", ""))):
            thieu = ["boot.wim của hệ điều hành"]
        if thieu:
            ket_qua.append(f'"{ten}": bỏ qua - ' + ", ".join(thieu) + ".")
            continue
        thu_muc = ten_thu_muc(kb["_file"])
        ok, loi = _u.ghi_file_nhung(d, dia_chi_pi, _duong_pxe(thu_muc))
        if ok:
            can_giu.add(thu_muc)
        else:
            ket_qua.append(f'"{ten}": LỖI - {loi}')
    ok, loi = _u.dung_wim_driver(_duong_pxe(_u.TEN_WIM_DRIVER))
    if not ok:
        ket_qua.append(loi)
    try:
        os.makedirs(_duong_pxe(THU_MUC_WINPE), exist_ok=True)
        for ten, nd in (("startnet.cmd", sinh_startnet_winpe()),
                        ("winpeshl.ini", sinh_winpeshl_cuu_ho())):
            with open(_duong_pxe(THU_MUC_WINPE, ten), "w",
                      encoding="utf-8", newline="") as f:
                f.write(nd)
        can_giu.add(THU_MUC_WINPE)
    except OSError as e:
        ket_qua.append(f"Không ghi được file WinPE cứu hộ: {e}")
    try:
        for n in os.listdir(_duong_pxe()):
            p = _duong_pxe(n)
            if os.path.isdir(p) and n not in can_giu:
                shutil.rmtree(p, ignore_errors=True)
    except OSError:
        pass
    _don_anh_cu()
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
    Danh sach (nhan, thu muc file nhung, os_id) theo DUNG thu tu hien trong
    menu - dung cho ca script iPXE lan phan xem truoc tren web. Chi kich ban
    DA CO file nhung va boot.wim cua he dieu hanh.
    """
    muc = []
    for kb in kichban_windows():
        thu_muc = ten_thu_muc(kb["_file"])
        os_id = kb.get("os_id", "")
        if (os.path.isfile(_duong_pxe(thu_muc, "deploy.cmd"))
                and os.path.isfile(_d.duong_boot_wim(os_id))):
            muc.append((kb.get("ten_kichban", kb["_file"]), thu_muc, os_id))
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
    pe = muc_winpe()
    # --timeout tinh bang mili giay; 0 giay = cho mai den khi co nguoi bam.
    cho = f"--timeout {c['cho_giay'] * 1000} " if c["cho_giay"] > 0 else ""
    dong = ["#!ipxe", ":menu",
            "menu Console System - Cai dat qua mang",
            "item --gap -- Chon bang phim mui ten + Enter:",
            "item --gap -- ",
            ("item pe 1. Win PE - cuu ho may >" if pe else
             "item --gap -- 1. Win PE (chua co boot.wim nao)"),
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
    for i, (nhan, *_r) in enumerate(muc):
        dong.append(f"item kb{i} {_chu_ipxe(nhan)}")
    dong += ["item --gap -- ",
             "item menu < Quay lai menu chinh"]
    # Menu con: KHONG dem nguoc - chi cai khi co nguoi chon.
    dong += [f"choose --default {'kb0' if muc else 'menu'} chon || goto menu",
             "goto ${chon}", ""]
    from . import unattend as _u
    co_driver = os.path.isfile(_duong_pxe(_u.TEN_WIM_DRIVER))
    # ---- Menu con WinPE cuu ho: boot.wim image 2 + winpeshl.ini mo cmd chay
    # startnet.cmd cuu ho thay cho Setup (xem sinh_startnet_winpe).
    dong += [":pe", "menu Win PE - cuu ho may (khong cai gi, khong xoa gi)"]
    for i, (nhan, _o) in enumerate(pe):
        dong.append(f"item pe{i} Win PE cua {_chu_ipxe(nhan)}")
    dong += ["item --gap -- ", "item menu < Quay lai menu chinh",
             f"choose --default {'pe0' if pe else 'menu'} chon || goto menu",
             "goto ${chon}", ""]
    for i, (nhan, os_id) in enumerate(pe):
        dong += [f":pe{i}", f"echo Dang nap Win PE: {_chu_ipxe(nhan)}",
                 f"kernel {goc}/wimboot || goto loi",
                 f"initrd {goc}/{THU_MUC_PXE}/{THU_MUC_WINPE}/winpeshl.ini winpeshl.ini || goto loi",
                 f"initrd {goc}/{THU_MUC_PXE}/{THU_MUC_WINPE}/startnet.cmd startnet.cmd || goto loi"]
        if co_driver:
            dong.append(f"initrd {goc}/{THU_MUC_PXE}/{_u.TEN_WIM_DRIVER} "
                        f"{_u.TEN_WIM_DRIVER} || goto loi")
        dong += [f"initrd {goc}/os/{os_id}/boot.wim boot.wim || goto loi",
                 "boot || goto loi", ""]
    for i, (nhan, thu_muc, os_id) in enumerate(muc):
        # wimboot (Microsoft ky) nap boot.wim GOC + file nhung - chay tren
        # BIOS, UEFI va UEFI + Secure Boot (xem unattend: FILE NHUNG QUA
        # WIMBOOT). Ten thu 2 cua initrd = ten file hien trong X:\System32.
        dong += [f":kb{i}", f"echo Dang nap: {_chu_ipxe(nhan)}",
                 f"kernel {goc}/wimboot || goto loi"]
        try:
            cac_file = sorted(os.listdir(_duong_pxe(thu_muc)))
        except OSError:
            cac_file = []
        for f in cac_file:
            dong.append(f"initrd {goc}/{THU_MUC_PXE}/{thu_muc}/{f} {f} || goto loi")
        if co_driver:
            dong.append(f"initrd {goc}/{THU_MUC_PXE}/{_u.TEN_WIM_DRIVER} "
                        f"{_u.TEN_WIM_DRIVER} || goto loi")
        dong += [f"initrd {goc}/os/{os_id}/boot.wim boot.wim || goto loi",
                 "boot || goto loi", ""]
    dong += [":odia",
             "echo Khoi dong tu o cung...",
             # UEFI: `exit` (ma 0) = firmware coi muc boot mang "chay xong" va
             # nhieu firmware (OVMF, kiem chung that 25/09/2026 bang may ao cai
             # tu Pi) DUNG o man hinh Setup thay vi sang o cung. `exit 1` = bao
             # "boot mang khong thanh" -> firmware thu muc boot KE TIEP (o cung).
             # BIOS: quay ve ROM PXE -> BIOS tu sang thiet bi ke tiep (da chay).
             "iseq ${platform} efi && echo (May UEFI: dong Could not boot image ngay sau day la BINH THUONG - firmware se tu sang o cung)",
             "iseq ${platform} efi && exit 1 || exit", "",
             ":lai",
             "reboot", "",
             ":loi",
             "echo LOI: khong nap duoc file cai dat tu Console System.",
             "prompt Bam phim bat ky de quay lai menu...",
             "goto win", ""]
    return "\n".join(dong)


# ------------------------------------------------------------------- web
def _xem_truoc(c, muc):
    """Ve lai 2 man hinh menu may khach se thay (cung chu voi sinh_script)."""
    # iPXE gop nhieu dau cach thanh 1 -> xem truoc cung khong can can cot.
    chinh = ["  Console System - Cai dat qua mang", "",
             "    Chon bang phim mui ten + Enter:", "",
             ("    1. Win PE - cuu ho may >" if muc_winpe() else
              "    1. Win PE (chua co boot.wim nao)"),
             f"    2. Install Windows > ({len(muc)} kich ban)", "",
             "  > Khoi dong o cung (KHONG cai gi)",
             "    Khoi dong lai may"]
    con = ["  Install Windows - chon kich ban cai dat", ""]
    if not muc:
        con.append("    (Chua co kich ban Windows nao dung duoc)")
    for i, (nhan, *_r) in enumerate(muc):
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
