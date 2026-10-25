# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Unattend - unattend.xml offline (specialize/firstlogon), ho so mac dinh, tat hoi mang.

(B4: tach nguyen van tu unattend.py; ten ham/hang giu nguyen, nguon van re-export.)"""
from consolesystem.core.esc import esc_xml as _esc
from consolesystem.features.deploy_os.un_goapp_font import (DUONG_PS_GO_APP, THU_MUC_TREN_MAY, _ds_go_app, _lenh_theo_pha)  # noqa: F401
from consolesystem.features.deploy_os.un_tuychon import (_khoi_gia_nhap_domain)  # noqa: F401


def _lenh_bat_administrator(d):
    r"""
    Mo khoa tai khoan Administrator co san.

    VI SAO CAN LENH NAY: dat <AdministratorPassword> trong unattend.xml
    CHI dat mat khau, KHONG mo khoa tai khoan - Windows van de no o trang
    thai disabled va no khong hien ra man hinh dang nhap. Rat nhieu nguoi
    tuong dat mat khau la xong roi khong hieu sao khong thay tai khoan dau.

    TIM THEO SID CHU KHONG THEO TEN: tai khoan Administrator co ten KHAC
    NHAU theo ngon ngu Windows (Administrateur o ban Phap, Administrador
    o ban Tay Ban Nha...), nen `net user Administrator /active:yes` se hong
    tren cac ban do. SID thi luon ket thuc bang -500 o MOI ngon ngu - day
    la cach duy nhat dung chac. Vi buoc 3 cho chon ngon ngu Windows nen
    truong hop nay la co that, khong phai lo xa.
    """
    if not d.get("mk_admin"):
        return []
    # Doi ten ve "Administrator" neu image ngon ngu khac (AutoLogon goi theo ten).
    return ["powershell -NoProfile -ExecutionPolicy Bypass -Command "
            "\"$a = Get-LocalUser | Where-Object { $_.SID.Value -like '*-500' }; "
            "$a | Enable-LocalUser; "
            "if ($a.Name -ne 'Administrator') { Rename-LocalUser $a -NewName Administrator }\""]

# Ho so mac dinh: moi tai khoan moi duoc tao bang cach chep C:\Users\Default.
# HKCU\Software\Classes KHONG nam trong NTUSER.DAT ma trong UsrClass.dat (vd
# menu chuot phai kieu cu cua Windows 11) - phai nap rieng file do.
_HIVE_HS = r"HKU\CPI_MACDINH"

_HIVE_HS_CLASS = r"HKU\CPI_MACDINH_CLASSES"

def _lenh_ho_so_mac_dinh(d):
    """Lenh cac tuy chon pha "ho_so", ghi vao ho so mac dinh (chay o specialize,
    quyen SYSTEM, chua co tai khoan nao) -> ap dung cho MOI tai khoan."""
    goc = _lenh_theo_pha(d, "ho_so")
    if not goc:
        return []
    doi = []
    for c in goc:
        c = c.replace("HKCU\\Software\\Classes\\", _HIVE_HS_CLASS + "\\")
        c = c.replace("HKCU\\", _HIVE_HS + "\\")
        doi.append(c)
    # Giao dien Toi: Windows tu ap chu de SANG o lan dang nhap dau cua moi tai
    # khoan, de len gia tri trong ho so mac dinh (lab 03/10/2026: Default = 0
    # nhung tai khoan moi = 1). Them 1 lenh RunOnce vao ho so mac dinh -> MOI tai
    # khoan moi tu dat lai ngay sau khi Windows ap chu de xong.
    if "giao_dien_toi" in set(d.get("tuy_chon") or []):
        # 2 muc RunOnce rieng, lenh reg ngan: <Path> cua RunSynchronousCommand
        # toi da 259 ky tu (lab 04/10/2026: ban dau 1 lenh powershell 423 ky tu
        # -> "unattend answer file is invalid" o pass specialize).
        for i, ten in enumerate(("AppsUseLightTheme", "SystemUsesLightTheme"), 1):
            doi.append(rf'reg add "{_HIVE_HS}\Software\Microsoft\Windows\CurrentVersion\RunOnce"'
                       rf' /v CPI_Toi{i} /t REG_SZ /d "reg add HKCU\Software\Microsoft\Windows'
                       rf'\CurrentVersion\Themes\Personalize /v {ten} /t REG_DWORD /d 0 /f" /f')
    return ([rf'reg load {_HIVE_HS} "C:\Users\Default\NTUSER.DAT"',
             rf'reg load {_HIVE_HS_CLASS} '
             r'"C:\Users\Default\AppData\Local\Microsoft\Windows\UsrClass.dat"']
            + doi
            + [f"reg unload {_HIVE_HS_CLASS}", f"reg unload {_HIVE_HS}"])

def _lenh_tat_hoi_mang():
    """
    Tat bang hoi "Do you want to allow your PC to be discoverable by other PCs and
    devices on this network? Yes/No" (Network Location Wizard) hien o goc phai man hinh
    lan dang nhap dau. Anh Thoai 04/10/2026: "van hien bang hoi yes no, dau phai silent".
    <NetworkLocation>Work</NetworkLocation> trong unattend khong chan duoc bang nay
    (SkipMachineOOBE). Khoa NewNetworkWindowOff la cach chinh thuc de tat no; mang se
    duoc dat sang Private bang buoc dau o phien dang nhap (xem _danh_sach_buoc_nguoi_dung).
    """
    return [r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Network\NewNetworkWindowOff" /f']

def _khoi_runsync_specialize(d):
    """
    Component Microsoft-Windows-Deployment chay cac lenh cap MAY: tuy chon Windows
    (quyen he thong, TRUOC khi co ai dang nhap). Phan mem KHONG cai o day nua - tu
    02/10/2026 moi phan mem cai o phien dang nhap dau (co bang tien trinh).
    """
    lenh = (_lenh_tat_hoi_mang()
            + _lenh_bat_administrator(d)
            + ([f"powershell -NoProfile -ExecutionPolicy Bypass -File {DUONG_PS_GO_APP}"]
               if _ds_go_app(d) else [])
            + _lenh_theo_pha(d, "may")
            + _lenh_ho_so_mac_dinh(d))
    if not lenh:
        return ""
    qua_dai = [c for c in lenh if len("cmd /c " + c) > 259]
    if qua_dai:
        raise ValueError("Lenh qua 259 ky tu (Windows Setup se bao unattend loi): "
                         + qua_dai[0][:80])
    muc = "".join(f"""
        <RunSynchronousCommand wcm:action="add">
          <Order>{i}</Order>
          <Path>cmd /c {_esc(c)}</Path>
        </RunSynchronousCommand>""" for i, c in enumerate(lenh, start=1))
    return f"""
    <component name="Microsoft-Windows-Deployment" processorArchitecture="amd64"
        publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS"
        xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <RunSynchronous>{muc}
      </RunSynchronous>
    </component>"""

# Lenh mo tien-trinh.ps1 o lan dang nhap dau. KHONG qua `cmd /c` va KHONG de lo cua so console:
# anh Thoai 08/10/2026 "chi hien bang popup, khong hien bang powershell dang sau". `-WindowStyle
# Hidden` khong du: Windows 11 (Windows Terminal la terminal mac dinh) van mo 1 cua so Terminal rong,
# Windows 10 thi chop console. `conhost.exe --headless` chay powershell KHONG co cua so console nao
# (co tu Windows 10 1809 / build 17763). Windows cu hon (deu het ho tro) khong hieu --headless ->
# deploy.cmd doc build cua anh vua bung va chep unattend-cu.xml (kieu cu) thay vao - xem _lenh_chon_unattend.
BUILD_TOI_THIEU_HEADLESS = 17763

_LENH_PS_TIEN_TRINH = ("powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "
                       f"{THU_MUC_TREN_MAY}\\tien-trinh.ps1")

LENH_MO_TIEN_TRINH = ("C:\\Windows\\System32\\conhost.exe --headless "
                      "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\" + _LENH_PS_TIEN_TRINH)

LENH_MO_TIEN_TRINH_CU = "cmd /c " + _LENH_PS_TIEN_TRINH

def _khoi_firstlogon(d, kieu_cu=False):
    """
    FirstLogonCommands - chay trong phien dang nhap DAU TIEN, theo thu tu:
      1. Tuy chon Windows cap nguoi dung
      2. Phan mem chon "cai cho Nguoi dung"
      3. Script sau khi cai
      4. "Lenh them" anh Thoai tu go o buoc 6
    (Truoc day ca 4 nhom nay deu duoc LUU nhung KHONG he duoc dung -
    day la lan dau chung thuc su chay.)
    """
    # TOAN BO cac buoc tren gio chay trong MOT script dieu phoi
    # (tien-trinh.ps1) thay vi tung SynchronousCommand rieng le.
    #
    # LY DO THAT (2 thu Windows khong lam duoc, xem sinh_script_tien_trinh):
    #   - Khong co GIOI HAN THOI GIAN cho tung lenh: Office 365 tung treo
    #     45 phut ma man hinh khong khac gi luc chay binh thuong, khong
    #     cach nao biet ngoai viec mo Task Manager doan.
    #   - Khong bao duoc tien do ra ngoai: nguoi dung khong biet dang cai
    #     toi cai nao trong so 10 cai.
    # Script dieu phoi lo ca hai, va van chay dung nhung dong lenh cu
    # (qua cmd /c) nen khong phai viet lai cu phap cai dat nao.
    lenh = [LENH_MO_TIEN_TRINH_CU if kieu_cu else LENH_MO_TIEN_TRINH]

    # BAO CAO TONG KET: KHONG dat o day nua.
    #
    # LOI THAT DA GAP (anh Thoai chup man hinh 13/09): bao-cao.ps1 tung la
    # mot SynchronousCommand RIENG dat ngay sau tien-trinh.ps1. Tren ly
    # thuyet Windows chay lan luot va cho tung cai xong han, nhung THUC TE
    # bang bao cao hien ra khi tien trinh moi chay toi buoc 6/11 - hai cua
    # so cmd cung song mot luc, bao cao doc trang thai may LUC PHAN MEM CON
    # DANG CAI DO nen bao sai hang loat.
    #
    # Khong kiem chung duoc ben trong Windows vi sao lai vay, nen cach chac
    # chan la khong phu thuoc vao no nua: chinh tien-trinh.ps1 tu goi bao
    # cao o cuoi, sau khi vong lap cac buoc da xong han (xem
    # sinh_script_tien_trinh). Thu tu do script cua minh quyet dinh.
    if not lenh:
        return ""
    muc = "".join(f"""
        <SynchronousCommand wcm:action="add">
          <Order>{i}</Order>
          <CommandLine>{_esc(c)}</CommandLine>
        </SynchronousCommand>""" for i, c in enumerate(lenh, start=1))
    return f"""
      <FirstLogonCommands>{muc}
      </FirstLogonCommands>"""

def sinh_unattend_offline_xml(d, kieu_cu=False, ten_override=None):
    """
    Sinh unattend.xml dat vao W:\\Windows\\Panther sau khi dism apply -
    CHI con pass specialize + oobeSystem (dat ten may, mui gio, tai
    khoan, bo qua OOBE, gia nhap domain, cac tuy chon Windows).

    KHAC voi sinh_autounattend_xml(): KHONG con pass windowsPE
    (DiskConfiguration/ImageInstall) vi phan do da duoc chinh WinPE lam
    bang diskpart + dism (xem sinh_deploy_cmd) - Windows chi con viec
    cau hinh no luc boot lan dau.
    """
    ten_may = (d.get("ten_may") or "PC-CONSOLEPI")[:15]
    if ten_override:
        # 1.9.4: ten may dong (serial/CSV/ngau nhien/hoi) - deploy.cmd ghep ten that vao giua 2 nua file.
        ten_may = ten_override
    # Khong tao user rieng: chi dung Administrator co san (anh Thoai 04/10/2026).
    # Mat khau o mk_admin (bat buoc, xem thieu_gi); AutoLogon vao Administrator.
    username = "Administrator"
    password = d.get("mk_admin") or ""
    mui_gio = d.get("mui_gio") or "SE Asia Standard Time"
    BANG_TIMEZONE_WINDOWS = {
        "Asia/Ho_Chi_Minh": "SE Asia Standard Time",
        "Asia/Bangkok": "SE Asia Standard Time",
        "Asia/Singapore": "Singapore Standard Time",
        "Asia/Tokyo": "Tokyo Standard Time",
        "Asia/Seoul": "Korea Standard Time",
        "Asia/Shanghai": "China Standard Time",
        "UTC": "UTC",
    }
    tz_windows = BANG_TIMEZONE_WINDOWS.get(mui_gio, "SE Asia Standard Time")

    # Key Windows anh Thoai tu nhap o buoc 3. De trong thi dung key KMS
    # client CONG KHAI chinh thuc cua Microsoft cho Windows 10/11 Pro
    # (khong phai key lau/crack) - cong khai tai learn.microsoft.com
    # "KMS client setup keys". May cai duoc nhung o trang thai CHUA kich
    # hoat cho toi khi gap may chu KMS hoac duoc nhap key that.
    product_key = (d.get("product_key") or "").strip() or "VK7JG-NPHTM-C97JM-9MPGT-3V66T"

    # Ngon ngu hien thi + kieu ban phim (truoc day ghi cung en-US).
    ngon_ngu = d.get("ngon_ngu") or "en-US"
    ban_phim = d.get("ban_phim") or "0409:00000409"
    # Tai khoan Administrator co san: Windows luon KHOA no lai. Dat
    # <AdministratorPassword> chi dat mat khau CHU KHONG mo khoa - phai
    # co them 1 lenh bat len (xem _lenh_bat_administrator).
    khoi_mk_admin = ""
    if d.get("mk_admin"):
        khoi_mk_admin = f"""
        <AdministratorPassword>
          <Value>{_esc(d['mk_admin'])}</Value>
          <PlainText>true</PlainText>
        </AdministratorPassword>"""

    # Tu dong dang nhap: dung <AutoLogon> chinh chu cua Windows (khong
    # phai thu thuat registry). Tien khi cai may kiosk / may trung bay /
    # may thu nghiem - bat may la vao thang desktop.
    #
    # KHONG dat <LogonCount>: co LogonCount thi Windows chi tu dang nhap
    # dung so lan do roi thoi, rat de gay hieu nham "sao dung may hom nay
    # lai bat nhap mat khau". Khong co thi tu dang nhap mai cho toi khi
    # tat di.
    # ---- Tu dong dang nhap ----
    #
    # LUON tu dang nhap LAN DAU, giong het cach MDT lam. LY DO THAT: moi
    # thu chay sau khi cai xong (phan mem "cai cho Nguoi dung", script,
    # go app rac, bang bao cao cuoi) deu nam trong FirstLogonCommands -
    # ma FirstLogonCommands CHI chay khi that su co nguoi dang nhap. Neu
    # may dung o man hinh nhap mat khau cho nguoi den go tay thi khong co
    # gi chay ca, va nguoi di cai may cung khong bao gio thay duoc bang
    # bao cao ket qua. Khong tu dang nhap = mat nua chuoi trien khai.
    #
    # KHAC NHAU giua 2 truong hop:
    #   - Khong tich "tu dang nhap": <LogonCount>1</LogonCount> - Windows
    #     tu dang nhap DUNG 1 LAN de chay cho xong, cac lan bat may sau
    #     deu hoi mat khau binh thuong (may van an toan khi giao cho
    #     nguoi dung).
    #   - Co tich: bo <LogonCount> - tu dang nhap mai mai (may kiosk,
    #     may trung bay).
    lan_dang_nhap = "" if d.get("tu_dang_nhap") else """
        <LogonCount>1</LogonCount>"""
    khoi_autologon = f"""
      <AutoLogon>
        <Username>{_esc(username)}</Username>
        <Password>
          <Value>{_esc(password)}</Value>
          <PlainText>true</PlainText>
        </Password>
        <Enabled>true</Enabled>{lan_dang_nhap}
      </AutoLogon>"""

    khoi_ngon_ngu = f"""
    <component name="Microsoft-Windows-International-Core" processorArchitecture="amd64"
        publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS"
        xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <InputLocale>{_esc(ban_phim)}</InputLocale>
      <SystemLocale>{_esc(ngon_ngu)}</SystemLocale>
      <UILanguage>{_esc(ngon_ngu)}</UILanguage>
      <UserLocale>{_esc(ngon_ngu)}</UserLocale>
    </component>"""

    return f"""<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
  <settings pass="specialize">
    <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64"
        publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS"
        xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <ComputerName>{_esc(ten_may)}</ComputerName>
      <TimeZone>{_esc(tz_windows)}</TimeZone>
      <ProductKey>{_esc(product_key)}</ProductKey>
    </component>{khoi_ngon_ngu}{_khoi_gia_nhap_domain(d)}{_khoi_runsync_specialize(d)}
  </settings>

  <settings pass="oobeSystem">
    <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64"
        publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS"
        xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <UserAccounts>{khoi_mk_admin}
      </UserAccounts>{khoi_autologon}
      <OOBE>
        <HideEULAPage>true</HideEULAPage>
        <HideOEMRegistrationScreen>true</HideOEMRegistrationScreen>
        <HideOnlineAccountScreens>true</HideOnlineAccountScreens>
        <HideWirelessSetupInOOBE>true</HideWirelessSetupInOOBE>
        <NetworkLocation>Work</NetworkLocation>
        <ProtectYourPC>3</ProtectYourPC>
        <SkipMachineOOBE>true</SkipMachineOOBE>
        <SkipUserOOBE>true</SkipUserOOBE>
      </OOBE>{_khoi_firstlogon(d, kieu_cu)}
      <TimeZone>{_esc(tz_windows)}</TimeZone>
    </component>
  </settings>
</unattend>
"""
