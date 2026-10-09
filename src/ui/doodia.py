# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi - DO O DIA cua may khach qua PXE (CHI DOC, KHONG xoa gi).

VI SAO (anh Thoai 08/10/2026): kich ban cai Windows chon o dia theo SO (0, 1, 2...) ma
ky su IT khong biet may do co may o, o nao la o nao -> chon nham o = mat du lieu khach.
Menu PXE co muc "Do o dia": may boot WinPE, doc TAT CA o dia + phan vung, hien ngay
tren man hinh may do VA gui ve Console System (trang Deployment OS -> O dia da do) de
ky su xem roi chon dung so o khi tao kich ban.

Cach lam (giu y het chuoi da kiem chung cua deploy.cmd - xem unattend.py):
  - wimboot nap boot.wim GOC cua 1 he dieu hanh + file nhung rieng (thu muc
    BOOT_DIR/_pxe/do-o-dia/): winpeshl.ini -> setup.exe -> autounattend.xml ->
    RunSynchronous `do-o-dia.cmd` (setup.exe moi bat duoc bo SMB client cua WinPE).
  - Nap driver "cho anh boot" (cpi-drivers.bin) bang drvload TRUOC khi doc o: may dung
    Intel VMD/RST hoac NVMe doi moi khong co driver san thi diskpart khong thay o.
  - diskpart CHI dung lenh doc: list disk / select disk / detail disk / list partition.
  - Gui file ket qua qua share Samba RIENG [cs-o-dia] (ghi duoc, chi cho tai khoan
    consolepi-deploy, chi chap nhan file .txt nho) - share [deploy] van CHI DOC.
    Samba chi chay khi PXE bat (quy tac 7), nen share nay cung chi mo khi PXE bat.
"""
import os
import re
import time

from .duongdan import THU_MUC_DU_LIEU

THU_MUC_O_DIA = os.path.join(THU_MUC_DU_LIEU, "o-dia")
TEN_SHARE = "cs-o-dia"
THU_MUC_NHUNG_PXE = "do-o-dia"          # BOOT_DIR/_pxe/do-o-dia/
MAX_BYTE_BAO_CAO = 512 * 1024           # bao cao that chi vai KB
GIU_TOI_DA = 100                        # giu 100 bao cao moi nhat
MO_DAU = "===CONSOLE-SYSTEM-O-DIA 1==="


# ------------------------------------------------------------ file nhung cho WinPE
def sinh_do_o_dia_cmd(dia_chi_pi, tai_khoan, mat_khau, share=TEN_SHARE):
    r"""Script chay trong WinPE (X:\Windows\System32\do-o-dia.cmd). CHI DOC o dia."""
    from . import unattend as _u
    pi = dia_chi_pi
    d = [
        "@echo off",
        "setlocal EnableExtensions",
        "title Console System - Do o dia (CHI DOC, KHONG XOA GI)",
        "color 1F",
        f"set NHUNG={_u.THU_MUC_NHUNG}",
        "set OUT=X:\\o-dia.txt",
        "set DP=X:\\dp-o-dia.txt",
        "set LOG=X:\\do-o-dia.log",
        "cls",
        "echo.",
        "echo  =====================================================================",
        "echo    CONSOLE SYSTEM - DO O DIA CUA MAY NAY",
        "echo    CHI DOC thong tin o dia - KHONG xoa, KHONG chia, KHONG ghi gi vao o.",
        "echo  =====================================================================",
        "echo.",
        # Mang len o NEN ngay tu dau (song song voi viec doc o) - xem deploy.cmd
        f"ping -n 1 -w 1000 {pi} >nul 2>&1",
        'if errorlevel 1 start "khoi tao mang" /min cmd /c "wpeinit >> X:\\wpeinit_log.txt 2>&1 '
        '& wpeutil InitializeNetwork >> X:\\wpeinit_log.txt 2>&1"',
        "echo  [1/3] Nap driver o cung / card mang (neu co)...",
        f"if exist %NHUNG%\\{_u.TEN_NHUNG_DRIVER} copy /y %NHUNG%\\{_u.TEN_NHUNG_DRIVER} "
        "X:\\cpi-drivers.wim >> %LOG% 2>&1",
        "if exist X:\\cpi-drivers.wim mkdir X:\\ConsolePiDrivers >nul 2>&1",
        "if exist X:\\cpi-drivers.wim dism /apply-image /imagefile:X:\\cpi-drivers.wim /index:1 "
        "/applydir:X:\\ConsolePiDrivers >> %LOG% 2>&1",
        'if exist X:\\ConsolePiDrivers (for /r X:\\ConsolePiDrivers %%i in (*.inf) do drvload "%%i" >> %LOG% 2>&1)',
        "",
        "echo  [2/3] Doc danh sach o dia va phan vung...",
        f"echo {MO_DAU}> %OUT%",
        "set FW=UEFI",
        'for /f "tokens=3" %%a in (\'reg query HKLM\\System\\CurrentControlSet\\Control /v '
        'PEFirmwareType 2^>nul ^| find "PEFirmwareType"\') do if "%%a"=="0x1" set FW=BIOS',
        "echo ===firmware=== >> %OUT%",
        "echo %FW% >> %OUT%",
        "echo ===may=== >> %OUT%",
        "reg query HKLM\\HARDWARE\\DESCRIPTION\\System\\BIOS >> %OUT% 2>&1",
        "echo list disk> %DP%",
        "diskpart /s %DP% > X:\\list-disk.txt 2>&1",
        "echo ===list-disk=== >> %OUT%",
        "type X:\\list-disk.txt >> %OUT%",
        # Dong "  Disk 0    Online ..." -> tokens=2 = so o; dong tieu de "Disk ###" bo qua
        'for /f "tokens=2" %%n in (\'type X:\\list-disk.txt ^| find "Disk "\') do call :mot_o %%n',
        "echo ===ipconfig=== >> %OUT%",
        "",
        # ---- hien tren man hinh: chi tiet tung o (gon), roi BANG TOM TAT o cuoi de luon thay
        "mode con: cols=100 lines=55 >nul 2>&1",
        "cls",
        "echo  ======================= CHI TIET TUNG O (%FW%) =======================",
        'for /f "tokens=2" %%n in (\'type X:\\list-disk.txt ^| find "Disk "\') do call :hien_o %%n',
        "echo.",
        "echo  =========================== TOM TAT O DIA ===========================",
        "type X:\\list-disk.txt | find \"Disk \"",
        "echo  (Gpt = * la o GPT. So o = so can nhap vao kich ban. Free = cho trong chua chia.)",
        "echo.",
        "",
        "echo  [3/3] Gui ket qua ve Console System de chon o khi tao kich ban...",
        "set CHO=0",
        ":cho_mang",
        "set /a CHO+=1",
        f"ping -n 1 -w 1000 {pi} >nul 2>&1",
        "if not errorlevel 1 goto mang_thong",
        "if %CHO% GEQ 60 goto khong_gui_duoc",
        "if %CHO% EQU 20 start \"khoi tao mang\" /min cmd /c \"wpeutil InitializeNetwork >> X:\\wpeinit_log.txt 2>&1\"",
        "ping -n 2 127.0.0.1 >nul",
        "goto cho_mang",
        ":mang_thong",
        "ipconfig /all >> %OUT% 2>&1",
        "echo ===het=== >> %OUT%",
        "net start workstation >> %LOG% 2>&1",
        "set THU=0",
        ":thu_gui",
        "set /a THU+=1",
        "net use Y: /delete /y >nul 2>&1",
        f"net use Y: \\\\{pi}\\{share} /user:{tai_khoan} {mat_khau} >> %LOG% 2>&1",
        "if not errorlevel 1 goto da_noi",
        "if %THU% GEQ 6 goto khong_gui_duoc",
        "ping -n 4 127.0.0.1 >nul",
        "goto thu_gui",
        ":da_noi",
        "copy /y %OUT% Y:\\o-dia-%RANDOM%%RANDOM%.txt >> %LOG% 2>&1",
        "if errorlevel 1 goto khong_gui_duoc",
        "net use Y: /delete /y >nul 2>&1",
        "echo.",
        "echo  DA GUI ve Console System. Tren trang web: Deployment OS - O dia da do.",
        "echo  Ghi nho SO O (Disk 0, 1, 2...) dung de nhap vao kich ban cai dat.",
        "goto ket_thuc",
        ":khong_gui_duoc",
        "echo.",
        "echo  KHONG gui duoc ve Console System (mang chua thong / PXE da tat?).",
        "echo  Hay ghi lai SO O tren man hinh nay de nhap vao kich ban.",
        ":ket_thuc",
        "echo.",
        "echo  Khong co gi bi thay doi tren may nay. Bam phim bat ky de TAT MAY...",
        "pause >nul",
        "wpeutil shutdown",
        "exit /b 0",
        "",
        ":mot_o",
        'if "%~1"=="###" exit /b 0',
        "echo ===o %~1=== >> %OUT%",
        "(echo select disk %~1& echo detail disk& echo list partition)> %DP%",
        "diskpart /s %DP% >> %OUT% 2>&1",
        "exit /b 0",
        "",
        ":hien_o",
        'if "%~1"=="###" exit /b 0',
        "echo  -------------------------------- Disk %~1 --------------------------------",
        "(echo select disk %~1& echo detail disk)> %DP%",
        "diskpart /s %DP% > X:\\hien.txt 2>&1",
        # Chi giu dong co ich: ten o (model), Type, bang volume. Bo dong le cua diskpart.
        # `for /f` tu bo dong trong (diskpart in rat nhieu dong trong -> tran man hinh)
        'for /f "delims=" %%l in (\'type X:\\hien.txt ^| find /v "Microsoft" ^| find /v "Copyright" ^| find /v "On computer" '
        '^| find /v "is now the selected" ^| find /v "Disk ID" ^| find /v "Path" ^| find /v "Target" '
        '^| find /v "LUN ID" ^| find /v "Read-only" ^| find /v "Boot Disk" ^| find /v "Pagefile" '
        '^| find /v "Hibernation" ^| find /v "Crashdump" ^| find /v "Clustered" ^| find /v "Status :" '
        '^| find /v "-----"\') do echo   %%l',
        "exit /b 0",
    ]
    return "\r\n".join(d) + "\r\n"


def sinh_file_nhung(dia_chi_pi):
    """{ten file: noi dung} cho muc PXE "Do o dia"."""
    from . import unattend as _u
    return {
        "winpeshl.ini": _u.sinh_winpeshl_ini(),
        "autounattend.xml": _u.sinh_autounattend_goi_script("do-o-dia.cmd",
                                                            "Console System - do o dia (chi doc)"),
        "do-o-dia.cmd": sinh_do_o_dia_cmd(dia_chi_pi, _u.TEN_TAI_KHOAN_SAMBA,
                                          _u._doc_mat_khau_samba()),
    }


def bao_dam_thu_muc():
    """Thu muc nhan bao cao: Samba ghi bang user `nobody` (force user) -> phai ghi duoc."""
    try:
        os.makedirs(THU_MUC_O_DIA, exist_ok=True)
        import pwd
        nb = pwd.getpwnam("nobody")
        st = os.stat(THU_MUC_O_DIA)
        if st.st_uid != nb.pw_uid:
            os.chown(THU_MUC_O_DIA, nb.pw_uid, nb.pw_gid)
        os.chmod(THU_MUC_O_DIA, 0o755)
    except (OSError, KeyError):
        pass


# ------------------------------------------------------------ doc bao cao
def _doc_bang(dong, i, chu_dau):
    """
    Doc bang co dinh cua diskpart bat dau o dong i (dong tieu de). Cot lay theo DONG GACH
    "----  ---" ngay duoi tieu de (gia tri so nhu "233 GB" can PHAI, co the lan sang trai
    chu tieu de - cat theo tieu de se sai). Tra (danh sach dict {ten cot: gia tri}, i ket thuc).
    """
    if i + 1 >= len(dong) or not re.match(r"^[\s-]+$", dong[i + 1]) or "-" not in dong[i + 1]:
        return [], i + 1
    gach = dong[i + 1]
    khoang = [(m.start(), m.end()) for m in re.finditer(r"-+", gach)]
    ten = [dong[i][bd:kt + 2].strip() for bd, kt in khoang]

    def cat(h):
        ra = []
        for k, (bd, _kt) in enumerate(khoang):
            kt = khoang[k + 1][0] if k + 1 < len(khoang) else len(h) + 1
            ra.append(h[bd:kt].strip())
        return ra

    hang = []
    j = i + 2
    while j < len(dong) and dong[j].strip().lstrip("*").strip().startswith(chu_dau):
        h = dong[j]
        if h.lstrip().startswith("*"):            # dong dang duoc chon: "*" thay bang khoang trang
            vt = h.index("*")
            h = h[:vt] + " " + h[vt + 1:]
        hang.append(dict(zip(ten, cat(h))))
        j += 1
    return hang, j


def phan_tich(noi_dung):
    """
    Doc 1 bao cao do-o-dia.cmd (dau ra diskpart tieng Anh) -> dict:
      {"firmware", "hang", "model", "mac": [], "ip": [], "o": [{so, model, loai, trang_thai,
       dung_luong, trong, gpt, phan_vung: [...], volume: [...]}]}
    Khong doc duoc phan nao thi de trong - trang web van hien nguyen van ban goc.
    """
    noi_dung = noi_dung.replace("\r", "")
    kq = {"firmware": "", "hang": "", "model": "", "mac": [], "ip": [], "o": []}
    phan = {}
    ten, buf = None, []
    for d in noi_dung.split("\n"):
        m = re.match(r"^===(.+?)===\s*$", d.strip())
        if m:
            if ten is not None:
                phan.setdefault(ten, []).append(buf)
            ten, buf = m.group(1).strip(), []
        else:
            buf.append(d)
    if ten is not None:
        phan.setdefault(ten, []).append(buf)

    kq["firmware"] = " ".join("".join(" ".join(b) for b in phan.get("firmware", [])).split())[:10]
    for b in phan.get("may", []):
        for d in b:
            m = re.match(r"\s*(SystemManufacturer|SystemProductName)\s+REG_SZ\s+(.*)$", d)
            if m:
                kq["hang" if m.group(1) == "SystemManufacturer" else "model"] = m.group(2).strip()[:80]
    for b in phan.get("ipconfig", []):
        for d in b:
            m = re.search(r"Physical Address[ .]*:\s*([0-9A-F]{2}(?:-[0-9A-F]{2}){5})", d)
            if m:
                kq["mac"].append(m.group(1))
            m = re.search(r"IPv4 Address[ .]*:\s*([\d.]+)", d)
            if m:
                kq["ip"].append(m.group(1))

    # list disk -> dung luong, trong, GPT
    tom = {}
    for b in phan.get("list-disk", []):
        for i, d in enumerate(b):
            if re.match(r"^\s*Disk ###", d):
                hang, _ = _doc_bang(b, i, "Disk")
                for r in hang:
                    so = (r.get("Disk ###") or "").replace("Disk", "").strip()
                    if so.isdigit():
                        tom[int(so)] = {"trang_thai": r.get("Status", ""), "dung_luong": r.get("Size", ""),
                                        "trong": r.get("Free", ""), "gpt": "*" in (r.get("Gpt") or "")}
                break

    for khoa, cac in phan.items():
        m = re.match(r"^o (\d+)$", khoa)
        if not m:
            continue
        so = int(m.group(1))
        b = cac[-1]
        o = {"so": so, "model": "", "loai": "", "phan_vung": [], "volume": []}
        o.update(tom.get(so, {"trang_thai": "", "dung_luong": "", "trong": "", "gpt": False}))
        for i, d in enumerate(b):
            if d.startswith("Disk ID:") and i > 0:
                k = i - 1
                while k >= 0 and not b[k].strip():
                    k -= 1
                if k >= 0:
                    o["model"] = b[k].strip()[:80]
            m2 = re.match(r"^Type\s*:\s*(.+)$", d.strip())
            if m2 and not o["loai"]:
                o["loai"] = m2.group(1).strip()[:20]
            if re.match(r"^\s*Volume ###", d):
                hang, _ = _doc_bang(b, i, "Volume")
                for r in hang:
                    o["volume"].append({"so": r.get("Volume ###", "").replace("Volume", "").strip(),
                                        "chu": r.get("Ltr", ""), "nhan": r.get("Label", ""),
                                        "fs": r.get("Fs", ""), "kieu": r.get("Type", ""),
                                        "dung_luong": r.get("Size", ""), "trang_thai": r.get("Status", ""),
                                        "info": r.get("Info", "")})
            if re.match(r"^\s*Partition ###", d):
                hang, _ = _doc_bang(b, i, "Partition")
                for r in hang:
                    o["phan_vung"].append({"so": r.get("Partition ###", "").replace("Partition", "").strip(),
                                           "kieu": r.get("Type", ""), "dung_luong": r.get("Size", ""),
                                           "offset": r.get("Offset", "")})
        kq["o"].append(o)
    kq["o"].sort(key=lambda x: x["so"])
    return kq


def canh_bao_may(kq):
    """
    Phan tich ket qua `phan_tich` -> danh sach canh bao cho ky su IT: [(muc, noi_dung)], muc la
    "do" (nguy co mat du lieu / khong cai duoc), "cam" (can luu y). Khong doan bua: chi nhan xet khi
    bao cao co dau hieu ro rang. Dung chung cho trang "O dia da do" va buoc chia o cua kich ban.
    """
    ra = []
    o_ds = kq.get("o") or []
    trong = [o for o in o_ds if (o.get("loai") or "").upper() not in ("USB", "SD", "MMC")]
    if not o_ds:
        ra.append(("do", "Không thấy ổ đĩa nào. Thường do máy dùng Intel RST/VMD hoặc RAID mà WinPE chưa có "
                         "driver: vào BIOS đổi chế độ SATA/NVMe sang AHCI, hoặc nạp driver Intel RST/VMD vào ảnh "
                         "boot (Tài nguyên → Driver → bật \"Nạp vào ảnh boot\"), rồi dò lại."))
    elif not trong:
        ra.append(("do", "Chỉ thấy ổ USB/thẻ nhớ, KHÔNG thấy ổ cứng bên trong. Có thể máy dùng Intel RST/VMD hoặc RAID "
                         "chưa có driver (xem hướng dẫn ở trên: đổi AHCI hoặc nạp driver vào ảnh boot)."))
    if len(trong) > 1:
        ra.append(("cam", f"Máy có {len(trong)} ổ cứng bên trong. Đối chiếu kỹ model và dung lượng để chọn đúng ổ cài "
                          "Windows; ổ còn lại sẽ giữ nguyên."))
    if any((o.get("loai") or "").upper() in ("USB", "SD", "MMC") for o in o_ds) and trong:
        ra.append(("cam", "Có ổ USB đang cắm: SỐ Ổ có thể đổi khi rút/cắm USB (ví dụ ổ cứng từ 0 thành 1). "
                          "Dò lại lúc cài thật, hoặc rút USB khỏi máy trước khi cài."))
    nghi_bl = []
    for o in o_ds:
        for v in o.get("volume") or []:
            fs = (v.get("fs") or "").strip().upper()
            if fs in ("", "RAW") and not (v.get("info") or "").strip():
                nghi_bl.append(f"ổ {o['so']}")
                break
        else:
            if o.get("phan_vung") and not o.get("volume") and (o.get("loai") or "").upper() not in ("USB", "SD", "MMC"):
                nghi_bl.append(f"ổ {o['so']}")
    if nghi_bl:
        ra.append(("do", f"Phân vùng không đọc được hệ thống file ({', '.join(nghi_bl)}): có thể đã mã hóa BITLOCKER "
                         "(hoặc Linux / chưa định dạng). Nếu là BitLocker: cài lại sẽ XÓA SẠCH dữ liệu, không khôi phục "
                         "được nếu không có khóa — lưu khóa khôi phục và/hoặc giải mã ổ trong Windows cũ trước khi cài."))
    return ra


def danh_sach_bao_cao(gioi_han=GIU_TOI_DA):
    """Cac bao cao da nhan, MOI NHAT truoc: [{"ten", "luc", "noi_dung", ...phan_tich}]."""
    ra = []
    try:
        cac = [f for f in os.listdir(THU_MUC_O_DIA) if f.lower().endswith(".txt")]
    except OSError:
        return ra
    cac.sort(key=lambda f: os.path.getmtime(os.path.join(THU_MUC_O_DIA, f)), reverse=True)
    for i, f in enumerate(cac):
        p = os.path.join(THU_MUC_O_DIA, f)
        try:
            if i >= gioi_han or os.path.getsize(p) > MAX_BYTE_BAO_CAO:
                os.remove(p)                # don bao cao cu / file la qua lon
                continue
            with open(p, encoding="utf-8", errors="replace") as fh:
                nd = fh.read()
        except OSError:
            continue
        if MO_DAU not in nd:
            continue                         # khong phai bao cao cua do-o-dia.cmd
        kq = phan_tich(nd)
        kq.update({"ten": f, "luc": os.path.getmtime(p), "noi_dung": nd})
        ra.append(kq)
    return ra


def xoa_bao_cao(ten):
    ten = os.path.basename(ten or "")
    p = os.path.join(THU_MUC_O_DIA, ten)
    if not ten.lower().endswith(".txt") or not os.path.isfile(p):
        return False, "Không tìm thấy báo cáo."
    try:
        os.remove(p)
    except OSError as e:
        return False, f"Không xóa được: {e}"
    return True, "Đã xóa báo cáo."


def xoa_het():
    n = 0
    try:
        for f in os.listdir(THU_MUC_O_DIA):
            if f.lower().endswith(".txt"):
                os.remove(os.path.join(THU_MUC_O_DIA, f))
                n += 1
    except OSError:
        pass
    return True, f"Đã xóa {n} báo cáo."


def gio(t):
    return time.strftime("%d/%m/%Y %H:%M", time.localtime(t))
