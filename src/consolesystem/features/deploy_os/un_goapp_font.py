# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Unattend - go app rac, cai font/ung dung/script/driver offline, .NET 3.5.

(B4: tach nguyen van tu unattend.py; ten ham/hang giu nguyen, nguon van re-export.)"""
from consolesystem.core import taisan as _taisan
import re
from ui import deployos as _d
from consolesystem.features.deploy_os.un_tuychon import (TUY_CHON_WINDOWS)  # noqa: F401


# Cac ung dung kem san cua Windows co the go bo an toan.
#
# CACH CHON DANH SACH NAY (khong bia, khong "go tat ca"): chi liet ke
# nhung goi go di ma KHONG lam hong chuc nang he thong. Co y KHONG dua
# vao day: Microsoft Store, May tinh (Calculator), Anh (Photos), Paint,
# Notepad, Snipping Tool, Terminal, .NET/VCLibs runtime - go nhung cai
# do se lam hong may hoac lam nguoi dung kho chiu ma khong loi gi.
#
# (ma_goi, ten_de_hieu, co_nen_go_mac_dinh)
APP_RAC = [
    ("Microsoft.BingNews", "Tin tức (News)", True),
    ("Microsoft.BingWeather", "Thời tiết (Weather)", True),
    ("Microsoft.GetHelp", "Trợ giúp (Get Help)", True),
    ("Microsoft.Getstarted", "Mẹo dùng Windows (Tips)", True),
    ("Microsoft.MicrosoftSolitaireCollection", "Game bài Solitaire", True),
    ("Microsoft.MixedReality.Portal", "Mixed Reality Portal", True),
    ("Microsoft.People", "Danh bạ (People)", True),
    ("Microsoft.SkypeApp", "Skype", True),
    ("Microsoft.WindowsFeedbackHub", "Gửi phản hồi (Feedback Hub)", True),
    ("Microsoft.WindowsMaps", "Bản đồ (Maps)", True),
    ("Microsoft.YourPhone", "Điện thoại của bạn (Phone Link)", True),
    ("Microsoft.ZuneMusic", "Groove Music / Media Player", True),
    ("Microsoft.ZuneVideo", "Phim & TV (Movies & TV)", True),
    ("Microsoft.Xbox.TCUI", "Xbox - giao diện", True),
    ("Microsoft.XboxGameOverlay", "Xbox - lớp phủ game", True),
    ("Microsoft.XboxGamingOverlay", "Xbox - Game Bar", True),
    ("Microsoft.XboxSpeechToTextOverlay", "Xbox - phụ đề giọng nói", True),
    ("Microsoft.XboxIdentityProvider", "Xbox - đăng nhập", False),
    ("Microsoft.MicrosoftOfficeHub", "Office Hub (quảng cáo Office)", True),
    ("Microsoft.Office.OneNote", "OneNote bản Store", False),
    ("Microsoft.Todos", "Microsoft To Do", False),
    ("Microsoft.PowerAutomateDesktop", "Power Automate", True),
    ("Clipchamp.Clipchamp", "Clipchamp (dựng video)", True),
    ("MicrosoftTeams", "Teams bản cá nhân (Chat)", True),
    ("Microsoft.WindowsCommunicationsApps", "Mail và Lịch", False),
    ("Microsoft.Microsoft3DViewer", "3D Viewer", True),
    ("Microsoft.MicrosoftStickyNotes", "Ghi chú dán (Sticky Notes)", False),
    ("Microsoft.WindowsAlarms", "Đồng hồ báo thức", False),
    ("Microsoft.WindowsSoundRecorder", "Ghi âm", False),
    ("Microsoft.WindowsCamera", "Máy ảnh (Camera)", False),
]

TEN_PS_GO_APP = "go-app.ps1"

DUONG_PS_GO_APP = "C:\\Windows\\Setup\\Scripts\\" + TEN_PS_GO_APP

def _ds_go_app(d):
    return [m for m in (d.get("go_app") or [])
            if re.fullmatch(r"[A-Za-z0-9._-]{1,64}", m or "")]

def sinh_ps_go_app(d):
    r"""
    Script go BO CAI (provisioned) cua app kem san - chay o pha specialize
    (quyen SYSTEM, TRUOC khi co tai khoan nao) nen tai khoan tao sau KHONG
    BAO GIO nhan app do. Cach nay dung y trinh tao unattend schneegans.de.

    LOI THAT (lab 26/09/2026): (1) chi go o phien nguoi dung dau thi app
    VAN CON (can quyen quan tri, loi bi nuot, buoc van bao "xong");
    (2) go offline trong WinPE (dism /Image) cung khong an - bo cai
    "neutral_~" van nam trong WindowsApps. Ca 2 lo ra nho bao-cao-day-du.json.
    Ghi ra file rieng (khong nhet vao <Path> cua RunSynchronousCommand - gioi
    han 259 ky tu, danh sach app dai se vuot).
    """
    ds = _ds_go_app(d)
    if not ds:
        return ""
    mang = ",".join("'" + m + "'" for m in ds)
    return f"""# Console Pi - go app kem san (pha specialize, SYSTEM). Tu sinh, khong sua tay.
$ds = @({mang})
$log = 'C:\\Windows\\Setup\\Scripts\\go-app.log'
foreach ($p in (Get-AppxProvisionedPackage -Online)) {{
    if ($ds -contains $p.DisplayName) {{
        try {{
            Remove-AppxProvisionedPackage -Online -AllUsers -PackageName $p.PackageName -ErrorAction Stop | Out-Null
            Add-Content $log "da go: $($p.DisplayName)"
        }} catch {{ Add-Content $log "LOI go $($p.DisplayName): $($_.Exception.Message)" }}
    }}
}}
"""

def _lenh_tiem_driver_offline(d):
    r"""
    Tiem driver vao anh Windows VUA BUNG (dism /image:W:\ /add-driver).

    LY DO THAT (26/09/2026, goi driver pho bien): deploy.cmd tu bung
    install.wim bang dism nen setup.exe KHONG BAO GIO chay buoc cai - khoi
    DriverPaths (PnpCustomizationsWinPE) trong unattend cua WinPE vi vay
    khong co tac dung. Driver chi nap trong WinPE (drvload) KHONG theo sang
    Windows: may o dia PVSCSI / VMD / virtio se man hinh xanh
    INACCESSIBLE_BOOT_DEVICE ngay lan khoi dong dau, may card VMXNET3 /
    I226... vao Windows khong co mang de lam cac buoc sau dang nhap.
      - driver "cho anh boot": da bung o X:\ConsolePiDrivers
      - driver thuong cua kich ban: lay tu o mang Z:\drivers\<id>
    Loi o day KHONG dung cai dat (driver hong/khong ky chi bi bo qua) - ghi log.
    """
    dong = [
        "echo === tiem driver vao Windows vua bung === >> %LOG%",
        "if exist X:\\ConsolePiDrivers dism /image:W:\\ /add-driver "
        "/driver:X:\\ConsolePiDrivers /recurse >> %LOG% 2>&1",
    ]
    for driver_id in d.get("driver_ids") or []:
        dong.append(f'if exist "Z:\\drivers\\{driver_id}" dism /image:W:\\ /add-driver '
                    f'/driver:"Z:\\drivers\\{driver_id}" /recurse >> %LOG% 2>&1')
    # Goi driver gan DONG MAY (deployos.dat_model_driver): Pi chon theo hang/model trong
    # BIOS, dua ten thu muc qua CS_DRV (cs-may.cmd). Goi trung voi kich ban thi dism tu
    # bo qua driver da co.
    dong += [
        'if defined CS_DRV echo  Nap driver rieng cho dong may nay: %CS_DRV%',
        'if defined CS_DRV for %%i in (%CS_DRV%) do if exist "Z:\\drivers\\%%i" '
        'dism /image:W:\\ /add-driver /driver:"Z:\\drivers\\%%i" /recurse >> %LOG% 2>&1',
    ]
    return dong

def _lenh_net35_offline(d):
    r"""
    Bat .NET Framework 3.5 OFFLINE ngay luc bung anh (dism /image:W:\ /enable-feature NetFx3
    /source:...\sxs /limitaccess) neu he dieu hanh co goi sxs\*.cab. ~1 phut, thay cho tai qua
    mang ~9 phut o buoc sau dang nhap (lab 04/10/2026: 523 giay). Cach MDT lam.
    Loi (goi sai ban Windows...) KHONG dung cai dat: ghi log roi buoc sau dang nhap van tu tai
    qua mang nhu cu (lenh `dism /online` o do la no-op neu da bat san).
    Thu muc tam o o W: vi X: (RAM cua WinPE) rat nho.
    """
    if "bat_net_framework35" not in (d.get("tuy_chon") or []):
        return []
    os_id = d.get("os_id", "")
    if not os_id or not _d.co_sxs(os_id):
        return []
    nguon = f"Z:\\os\\{os_id}\\sxs"
    return [
        "echo === bat .NET Framework 3.5 offline === >> %LOG%",
        "echo  Bat .NET Framework 3.5 tu goi offline - khoang 1-2 phut...",
        f'if exist "{nguon}" mkdir W:\\cs-scratch',
        f'if exist "{nguon}" dism /image:W:\\ /enable-feature /featurename:NetFx3 /all '
        f'/source:"{nguon}" /limitaccess /scratchdir:W:\\cs-scratch /logpath:X:\\dism_net35.txt >> %LOG% 2>&1',
        "if exist W:\\cs-scratch rd /s /q W:\\cs-scratch",
        "echo.",
    ]

def _lenh_chep_go_app(d):
    """Dong deploy.cmd: chep go-app.ps1 vao anh Windows vua bung."""
    if not _ds_go_app(d):
        return []
    return [
        "if not exist W:\\Windows\\Setup\\Scripts mkdir W:\\Windows\\Setup\\Scripts",
        f"copy /y %NHUNG%\\{TEN_PS_GO_APP} W:\\Windows\\Setup\\Scripts\\{TEN_PS_GO_APP} >> %LOG% 2>&1",
    ]

def _lenh_go_app(d):
    r"""
    Go cac ung dung kem san da chon.

    GOM TAT CA VAO 1 LENH POWERSHELL DUY NHAT thay vi moi app 1 lenh:
    moi RunSynchronousCommand/SynchronousCommand deu phai khoi dong mot
    tien trinh PowerShell rieng (moi lan ~2-4 giay chi de nap PowerShell),
    30 app se thanh hon 1 phut chi de nap lai PowerShell 30 lan.

    GO CA HAI TANG - thieu 1 trong 2 la khong sach:
      - Remove-AppxPackage -AllUsers : go cho cac tai khoan DANG co
      - Remove-AppxProvisionedPackage: go "mam" trong anh he dieu hanh,
        neu khong thi tai khoan nao TAO MOI sau nay se bi cai lai het.

    Chay o pha nguoi_dung (FirstLogonCommands) chu khong phai specialize:
    cac lenh Appx can mot phien nguoi dung thuc su de lam viec dung.
    """
    ds = [m for m in (d.get("go_app") or [])
          if re.fullmatch(r"[A-Za-z0-9._-]{1,64}", m or "")]
    if not ds:
        return []
    mang = ",".join("'" + m + "'" for m in ds)
    ps = (
        "$ds=@(" + mang + ");"
        "foreach($t in $ds){"
        "Get-AppxPackage -Name $t -AllUsers -EA SilentlyContinue"
        " | Remove-AppxPackage -AllUsers -EA SilentlyContinue;"
        "Get-AppxProvisionedPackage -Online -EA SilentlyContinue"
        " | Where-Object {$_.DisplayName -eq $t}"
        " | Remove-AppxProvisionedPackage -Online -EA SilentlyContinue"
        "}"
    )
    return ['powershell -NoProfile -ExecutionPolicy Bypass -Command "' + ps + '"']

def _lenh_theo_pha(d, pha):
    """Danh sach lenh THAT cua cac tuy chon da tich, theo pha yeu cau."""
    da_chon = set(d.get("tuy_chon") or [])
    ra = []
    for ma, _nhan, _mo_ta, pha_muc, cac_lenh in TUY_CHON_WINDOWS:
        if ma in da_chon and pha_muc == pha:
            ra.extend(cac_lenh)
    return ra

# Noi cac file phan mem/script duoc chep sang tren chinh may dich (do
# deploy.cmd chep tu Z:\ luc con trong WinPE - xem sinh_deploy_cmd).
# Chep san ra dia roi moi cai la co y: luc Windows chay lan dau KHONG
# can mang, khong can tai khoan Samba gi ca - tranh dung lai dung cai
# cho da tung gay bao nhieu rac roi o giai doan WinPE.
THU_MUC_TREN_MAY = "C:\\ConsolePi"

def _lenh_cai_app(a):
    """
    Lenh cai 1 phan mem tu file da duoc chep san sang may dich.

    .msi  -> msiexec /i "duong dan" <tham so>
    .exe  -> "duong dan" <tham so>
    Tham so lay theo TUNG FILE o tab "Phan mem" (apps/_thongtin.json) -
    vi tham so cai im lang la thuoc tinh cua BO CAI, khong phai cua kich
    ban: cung 1 file thi moi kich ban deu dung tham so do.
    """
    ten = a["ten"]
    duong = f"{THU_MUC_TREN_MAY}\\apps\\{ten}"
    tham_so = (_d.doc_thongtin_app().get(ten)
               or _d.tham_so_mac_dinh_app(ten)).strip()
    if ten.lower().endswith(".msi"):
        return f'msiexec /i "{duong}" {tham_so}'.strip()
    return f'"{duong}" {tham_so}'.strip()

THU_MUC_UNGDUNG_TREN_MAY = f"{THU_MUC_TREN_MAY}\\ungdung"

# ----------------------------------------------------------------- BO FONT
# Kich ban chon cac "bo font" (xem deployos: muc BO FONT). Deploy.cmd chep thu muc bo font
# sang C:\ConsolePi\fonts\<id> (con o WinPE), con cai-font.ps1 chay bang quyen SYSTEM o 1 buoc
# sau khi dang nhap: chep tung font vao C:\Windows\Fonts + ghi registry HKLM (cho MOI tai
# khoan) + AddFontResource. Danh sach + ten registry nam trong _fonts.json (ui/fontinfo.py).
TEN_PS_CAI_FONT = "cai-font.ps1"

def _bo_font_cai_duoc(d):
    """(cai_duoc, mat): cai_duoc = [{"id","ten_hien_thi","so_font"}] cua cac bo font da chon
    VA con ton tai VA co font; mat = id da chon nhung bo font khong con / dang trong - de bao
    cao RO thay vi am tham bo qua."""
    cai_duoc, mat = [], []
    for bo_id in _d.chuan_hoa_fonts(d.get("fonts")):
        b = _d.lay_bo_font(bo_id)
        if b and b["so_font"]:
            cai_duoc.append({"id": b["id"], "ten_hien_thi": b["ten_hien_thi"],
                             "so_font": b["so_font"]})
        else:
            mat.append(bo_id)
    return cai_duoc, mat

_PS_CAI_FONT = _taisan.doc("features/deploy_os/un_goapp_font._PS_CAI_FONT.ps1")

def sinh_ps_cai_font():
    return _PS_CAI_FONT.lstrip("\n")

def _lenh_cai_bo_font(b):
    return ('powershell.exe -NoProfile -ExecutionPolicy Bypass -File '
            f'"{THU_MUC_TREN_MAY}\\{TEN_PS_CAI_FONT}" -Bo "{b["id"]}"')

def _lenh_cai_ungdung(u):
    r"""
    Lenh cai 1 UNG DUNG kieu thu muc (mo hinh MDT "Application with source
    files" - xem deployos.danh_sach_ungdung()). Khac voi _lenh_cai_app():
    o day KHONG doan tham so tu duoi file - dong lenh la TU DO, nguoi dung
    tu go nguyen (vd "setup.exe /configure configuration.xml" cho Office
    365). Vi lenh co the tham chieu file TUONG DOI trong chinh thu muc do
    (nhu configuration.xml canh setup.exe), phai `cd /d` vao dung thu muc
    ung dung TRUOC khi chay - MDT cung lam dung nhu vay (tu cd vao thu muc
    da copy roi moi goi lenh).
    """
    o = _d.lay_ungdung(u["id"])
    lenh_cai = (o or {}).get("lenh_cai", "").strip()
    if not lenh_cai:
        return None
    thu_muc = f"{THU_MUC_UNGDUNG_TREN_MAY}\\{u['id']}"
    return f'cd /d "{thu_muc}" && {lenh_cai}'

def _lenh_mot_script(ten):
    """
    Lenh chay 1 script theo DUNG loai file (cmd.exe /c <lenh>).

    LOI THAT (lab 26/09/2026, kich ban co script .ps1): truoc day chi goi
    duong dan file -> Windows mo .ps1 bang Notepad (lien ket mac dinh cua
    .ps1 la "Edit"), script KHONG chay, buoc tien trinh dung cho toi khi qua
    gio. .ps1 phai chay qua powershell -ExecutionPolicy Bypass -File.
    """
    duong = f"{THU_MUC_TREN_MAY}\\scripts\\{ten}"
    if ten.lower().endswith(".ps1"):
        return ('powershell.exe -NoProfile -ExecutionPolicy Bypass '
                f'-File "{duong}"')
    return f'"{duong}"'

def _lenh_script(d):
    """Lenh chay cac script da chon (luon chay o phien nguoi dung dau)."""
    return [_lenh_mot_script(ten) for ten in (d.get("scripts") or [])]
