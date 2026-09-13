"""
Console Pi - Tu dong hoa Windows Setup (autounattend.xml) cho Deployment OS

Tiep noi ui/pxe.py: sau khi boot qua PXE vao duoc man hinh "Windows Setup"
that (da kiem chung that - anh Thoai xac nhan bang anh chup man hinh), muc
nay lam cho Windows Setup TU CHAY het cac buoc (chon ngon ngu, chia o dia,
dat ten may, tao tai khoan, mui gio, bo qua OOBE) THEO DUNG cac lua chon
anh Thoai da chon o 7 buoc cua wizard - khong con phai bam Next thu cong.

CO CHE (dung tai lieu unattend.xml chinh thuc cua Microsoft, khong doan):
Windows Setup tu dong quet moi O DIA RIENG (kho ca dia cung/USB/dia mem ao)
tim file ten dung `autounattend.xml` o thu muc goc ngay tu buoc dau tien
(windowsPE pass) - khong can chi duong dan gi ca, chi can file co mat va
dung ten.

wimboot (dang dung de nap WinPE qua mang - xem ui/pxe.py) ho tro nap them
1 "dia mem ao" (floppy image) cung luc voi boot.wim: Windows Setup nhin
thay dia mem ao nay y het 1 o dia that, tu tim thay autounattend.xml
trong do. Day la cach lam CHINH THUC cua chinh du an wimboot cho truong
hop nay (khong phai tu nghi ra).

GIOI HAN THAT (khong bia): phan tu dong CAI PHAN MEM (FirstLogonCommands)
CAN duong mang toi noi luu file .msi/.exe (Samba hoac HTTP tu chinh Pi) -
HA TANG NAY CHUA DUNG (xem docs/ke-hoach-pxe-winpe-tu-dong-cai-windows.md,
muc "Samba"). File autounattend.xml o day moi lam duoc phan CAI DAT HE
DIEU HANH tu dong hoan toan (dia, ten may, tai khoan, mui gio, OOBE) -
CHUA tu dong cai phan mem sau do. Se bao ro trong ket qua kiem tra san
sang, khong gia vo da lam xong.
"""
import os
import re
import subprocess
import xml.sax.saxutils as _x

from . import deployos as _d



def _esc(s):
    return _x.escape(str(s or ""))


# Tai khoan Samba RIENG (user he thong "nologin", khong the dang nhap
# SSH/local - xem install.sh/README) chi de Windows Setup tu xac thuc khi
# no tu mo phien SMB rieng doc InstallFrom/Path - xem ly do that (guest
# bi Windows hien dai chan) trong sinh_autounattend_xml() ben duoi.
TEN_TAI_KHOAN_SAMBA = "consolepi-deploy"

# Duong dan file khoa Samba - xem install.sh (khoi "Samba: kho trien khai
# Windows qua PXE"): tu sinh ngau nhien 1 lan duy nhat luc cai, quyen 600.
#
# TUYET DOI KHONG viet mat khau thang vao code: repo nay la PUBLIC tren
# GitHub, code se bi doc boi bat ky ai - hang chuc nghin nguoi. Mat khau
# tung bi viet cung o day (da phat hien va sua truoc khi commit lan dau,
# chua tung bi day len GitHub).
from .duongdan import FILE_KHOA_SAMBA as _FILE_KHOA_SAMBA


def _doc_mat_khau_samba():
    """Doc mat khau Samba tu file khoa install.sh da tao. Rong neu chua cai."""
    try:
        with open(_FILE_KHOA_SAMBA, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""
# LOI THAT DA GAP (kiem chung qua chinh setupact.log cua Windows Setup,
# ma loi that su [gle=0x00000035] ERROR_BAD_NETPATH): de <Domain> RONG
# khien Windows dung dinh dang credential "\consolepi-deploy" (backslash
# + username, KHONG co ten may) - Windows tu choi ket noi voi dinh dang
# nay (that bai NGAY, khong he thu ket noi mang - Samba server KHONG ghi
# nhan bat ky ket noi nao trong log, du `net use` thu cong voi CUNG dia
# chi/tai khoan tu 1 Command Prompt khac trong CUNG WinPE session lai
# THANH CONG binh thuong). SUA DUNG: dien Domain = ten may Samba (hostname
# that cua Pi, xem "hostname" tren Pi) - dung quy uoc DOMAIN\Username cho
# tai khoan local (khong phai domain AD) khi xac thuc tu xa.
TEN_MAY_SAMBA = "Server-console"


def _khoi_driverpaths(d, dia_chi_pi):
    """
    Sinh component Microsoft-Windows-PnpCustomizationsWinPE (pass
    windowsPE) - tiem driver "Out-of-Box" (mo hinh MDT) qua Samba, dung
    <Credentials> giong het InstallFrom (ly do that: xem
    sinh_autounattend_xml). Rong neu khong chon driver nao - KHONG in ra
    component thua (Windows kho chiu voi component rong trong 1 so
    truong hop).
    """
    driver_ids = d.get("driver_ids") or []
    if not driver_ids:
        return ""
    muc = ""
    for i, driver_id in enumerate(driver_ids, start=1):
        muc += f"""
      <PathAndCredentials wcm:action="add" wcm:keyValue="{i}">
        <Path>\\\\{_esc(dia_chi_pi)}\\deploy\\drivers\\{_esc(driver_id)}</Path>
        <Credentials>
          <Domain>{_esc(TEN_MAY_SAMBA)}</Domain>
          <Username>{_esc(TEN_TAI_KHOAN_SAMBA)}</Username>
          <Password>{_esc(_doc_mat_khau_samba())}</Password>
        </Credentials>
      </PathAndCredentials>"""
    return f"""
    <component name="Microsoft-Windows-PnpCustomizationsWinPE"
        processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35"
        language="neutral" versionScope="nonSxS"
        xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <DriverPaths>{muc}
      </DriverPaths>
    </component>"""


def _khoi_credentials_samba():
    return f"""
            <Credentials>
              <Domain>{_esc(TEN_MAY_SAMBA)}</Domain>
              <Username>{_esc(TEN_TAI_KHOAN_SAMBA)}</Username>
              <Password>{_esc(_doc_mat_khau_samba())}</Password>
            </Credentials>"""


def _sh(cmd, timeout=20):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, str(e)


def _khoi_dia_windows(d):
    """
    Doan XML DiskConfiguration - chia o dia theo dung lua chon cua wizard
    (buoc 4). Theo dung chuan GPT/UEFI: EFI (fat32) + MSR (khong dinh dang,
    Windows yeu cau tren GPT) + o he thong (ntfs).
    """
    o_dia_so = d.get("o_dia_so", "0")

    if d.get("o_dia_che_do") != "chia_tay":
        # Tu dong: dung dung bo mac dinh da hien trong buoc 4 cua wizard
        # LOI THAT DA GAP (anh Thoai kiem chung that: boot that bai rat
        # nhanh - duoi 2 phut tu luc tai xong boot.wim toi luc quay lai loi
        # 0xc000000f, qua nhanh de la mot lan ap anh Windows that su (4.4GB
        # thuong mat vai phut), va Samba khong he ghi nhan bat ky ket noi
        # nao trong TAT CA cac lan thu - chung to Setup chua bao gio thuc
        # su cham toi buoc ImageInstall/lay install.wim ca 3 lan thu khac
        # nhau (dia mem ao, RunSynchronousCommand net use, UNC truc tiep)):
        # <ModifyPartitions> vo tinh duoc dat TRUOC <CreatePartitions> -
        # nguoc thu tu logic bat buoc (khong the SUA dinh dang 1 phan vung
        # CHUA duoc TAO ra). Windows Setup co le tu choi/bo qua toan bo
        # DiskConfiguration ngay tu dau vi vay, dan toi mot trang thai dia
        # mac dinh/rong, boot that bai rat nhanh - khong lien quan gi den
        # cach lay install.wim ca (do la huong dieu tra sai truoc do).
        return f"""
            <CreatePartitions>
                <CreatePartition wcm:action="add">
                    <Order>1</Order>
                    <Type>EFI</Type>
                    <Size>260</Size>
                </CreatePartition>
                <CreatePartition wcm:action="add">
                    <Order>2</Order>
                    <Type>MSR</Type>
                    <Size>16</Size>
                </CreatePartition>
                <CreatePartition wcm:action="add">
                    <Order>3</Order>
                    <Type>Primary</Type>
                    <Extend>true</Extend>
                </CreatePartition>
            </CreatePartitions>
            <ModifyPartitions>
                <ModifyPartition wcm:action="add">
                    <Order>1</Order>
                    <PartitionID>1</PartitionID>
                    <Label>EFI</Label>
                    <Format>FAT32</Format>
                </ModifyPartition>
                <ModifyPartition wcm:action="add">
                    <Order>2</Order>
                    <PartitionID>2</PartitionID>
                </ModifyPartition>
                <ModifyPartition wcm:action="add">
                    <Order>3</Order>
                    <PartitionID>3</PartitionID>
                    <Label>Windows</Label>
                    <Format>NTFS</Format>
                    <Letter>C</Letter>
                </ModifyPartition>
            </ModifyPartitions>
            <DiskID>{_esc(o_dia_so)}</DiskID>
            <WillWipeDisk>true</WillWipeDisk>"""

    # Chia tay: dung dung danh sach phan vung tu buoc 4
    tao, sua = [], []
    for i, p in enumerate(d.get("phan_vung") or [], start=1):
        fs = (p.get("fs") or "ntfs").lower()
        if fs == "msr":
            tao.append(f"""
                <CreatePartition wcm:action="add">
                    <Order>{i}</Order>
                    <Type>MSR</Type>
                    <Size>{_esc(p.get('cd', '16'))}</Size>
                </CreatePartition>""")
            continue
        loai = "EFI" if fs == "fat32" and i == 1 else "Primary"
        if p.get("cd") == "con_lai":
            tao.append(f"""
                <CreatePartition wcm:action="add">
                    <Order>{i}</Order>
                    <Type>{loai}</Type>
                    <Extend>true</Extend>
                </CreatePartition>""")
        else:
            tao.append(f"""
                <CreatePartition wcm:action="add">
                    <Order>{i}</Order>
                    <Type>{loai}</Type>
                    <Size>{_esc(p.get('cd', '1024'))}</Size>
                </CreatePartition>""")
        dinh_dang = "FAT32" if fs == "fat32" else ("NTFS" if fs == "ntfs" else fs.upper())
        gan = p.get("gan", "")
        chu_o = f"<Letter>{_esc(gan.rstrip(':'))}</Letter>" if gan and gan not in ("-", "EFI") else ""
        sua.append(f"""
                <ModifyPartition wcm:action="add">
                    <Order>{i}</Order>
                    <PartitionID>{i}</PartitionID>
                    <Label>{_esc(p.get('nhan', ''))}</Label>
                    <Format>{dinh_dang}</Format>
                    {chu_o}
                </ModifyPartition>""")

    return f"""
            <CreatePartitions>{''.join(tao)}
            </CreatePartitions>
            <ModifyPartitions>{''.join(sua)}
            </ModifyPartitions>
            <DiskID>{_esc(o_dia_so)}</DiskID>
            <WillWipeDisk>true</WillWipeDisk>"""


def sinh_autounattend_xml(d, dia_chi_pi="192.168.98.1", duong_install=None):
    """
    Sinh noi dung autounattend.xml THAT tu cau hinh wizard/kich ban (dict
    `d` - cung cau truc voi trang thai wizard trong deployos.py).

    `dia_chi_pi`: dia chi IP THAT cua Pi luc PXE dang chay (xem
    ui/pxe.py: _dia_chi_pi_that()) - CHI dung khi duong_install=None (mac
    dinh, tro qua Samba - xem chi tiet lich su trong XML ben duoi).

    `duong_install`: neu co, dung THANG duong nay lam <InstallFrom><Path>
    thay vi UNC qua Samba. KHONG con dung duoc trong thuc te cho dia GPT+
    FAT32 (xem dung_dia_gpt_tu_dong(): da kiem chung that qua `wmic
    logicaldisk` ngay trong WinPE dang chay - dia SAN cua sanboot BIEN MAT
    truoc ca luc Setup xu ly ImageInstall, nen install.wim/install.swm
    dat tren dia do KHONG the doc lai duoc) - giu tham so nay lai phong
    khi co co che boot khac trong tuong lai co the dung duoc (vd USB that).

    Chi lam phan CAI DAT HE DIEU HANH tu dong (chua cai phan mem - xem
    gioi han o dau file).
    """
    ten_may = (d.get("ten_may") or "PC-CONSOLEPI")[:15]
    username = d.get("username") or "admin"
    password = d.get("password") or ""
    mui_gio = d.get("mui_gio") or "SE Asia Standard Time"
    # Windows dung ten mui gio rieng (khong phai IANA nhu Asia/Ho_Chi_Minh).
    # Bang tra ngan, chi cac mui gio da liet ke trong deployos.MUI_GIO.
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

    khoi_dia = _khoi_dia_windows(d)

    # Duong install.wim mac dinh: lay THANG tu thu muc rieng cua os_id da
    # chon (xem ui/deployos.py: OS_DIR) - KHONG con file "install.wim" o
    # goc chia se "deploy" nua tu khi tach thanh nhieu he dieu hanh.
    if duong_install is None:
        os_id = d.get("os_id", "")
        duong_install_mac_dinh = f"\\\\{dia_chi_pi}\\deploy\\os\\{os_id}\\install.wim"
    else:
        duong_install_mac_dinh = duong_install

    khoi_driver = _khoi_driverpaths(d, dia_chi_pi)

    return f"""<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
  <settings pass="windowsPE">
    <component name="Microsoft-Windows-International-Core-WinPE"
        processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35"
        language="neutral" versionScope="nonSxS"
        xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <SetupUILanguage><UILanguage>en-US</UILanguage></SetupUILanguage>
      <InputLocale>en-US</InputLocale>
      <SystemLocale>en-US</SystemLocale>
      <UILanguage>en-US</UILanguage>
      <UserLocale>en-US</UserLocale>
    </component>{khoi_driver}
    <component name="Microsoft-Windows-Setup" processorArchitecture="amd64"
        publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS"
        xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <!-- LOI THAT DA GAP: wimboot chi dua may vao duoc moi truong WinPE/
           Setup (boot.wim) - BAN THAN Windows Setup van can 1 nguon ANH
           CAI DAT THAT (install.wim, 4.4GB) giong het khi cai tu USB/DVD
           that (X:/sources/install.wim nam CUNG dia voi WinPE). Qua mang
           thi khong co "cung 1 dia" nhu vay - dung 1 chia se Samba
           (xem smb.conf cua Console Pi, share "deploy") va tro thang
           InstallFrom/Path toi duong dan UNC.

           LOI KY THUAT DA GAP - vong 1 (kiem chung that bang smbstatus):
           ban dau dinh dung 1 lenh `net use` rieng (RunSynchronousCommand)
           de anh xa o mang TRUOC. Ket qua: `smbstatus` tren Pi khong ghi
           nhan BAT KY ket noi nao - bo huong nay, quay ve InstallFrom/Path
           TU KET NOI UNC truc tiep (dung guest, khong mat khau).

           LOI KY THUAT DA GAP - vong 2 (kiem chung that bang cach go tay
           qua Command Prompt that trong WinPE, anh Thoai truc tiep thu):
           `net use //<pi>/deploy /user:guest ""` bao "completed
           successfully", nhung ngay sau do goi thang
           `setup.exe /unattend://<pi>/deploy/autounattend.xml` van bao
           "The specified file does not exist" - CHUNG TO Windows Setup
           TU MO 1 phien SMB RIENG cua chinh no (system context) khi doc
           InstallFrom/Path, KHONG dung chung phien voi bat ky `net use`
           thu cong nao da chay truoc do trong cung WinPE (context khac
           nhau) - VA rat co the Windows hien dai (tu 1709+) chan dang
           nhap khach an danh (chinh sach "insecure guest logon") ngay ca
           khi server cho phep guest.

           SUA DUNG (dang dung): dung <Credentials> CHINH THUC ngay trong
           <InstallFrom> (tai lieu Microsoft, xem
           learn.microsoft.com ".../microsoft-windows-setup-imageinstall-
           osimage-installfrom") - Windows Setup TU xac thuc bang tai
           khoan nay khi no tu mo phien SMB, khong can `net use`/
           RunSynchronousCommand gi ca. Samba tren Pi dung 1 user he thong
           RIENG "consolepi-deploy" (khong the dang nhap SSH/local,
           nologin) - chi de xac thuc doc chia se "deploy". -->
      <!-- LOI THAT DA THU VA BO (kiem chung that bang log Samba
           /var/log/samba/: HOAN TOAN khong co ket noi nao duoc ghi nhan,
           ke ca sau khi xac nhan mang DA len that su qua 1 file log
           chuan doan rieng): tung thu dung RunSynchronousCommand o day de
           chay `net start workstation` + `wpeinit` truoc DiskConfiguration/
           ImageInstall, theo dung tai lieu Microsoft mo ta - NHUNG Windows
           Setup xu ly ImageInstall SOM HON ca RunSynchronousCommand cua
           CHINH pass windowsPE nay (khong dam bao thu tu nhu tai lieu ngu
           y). SUA DUNG THAT SU: chuyen sang nhung 1 file winpeshl.ini rieng
           vao boot.wim (xem dung_dia_gpt_tu_dong() - chay wpeinit truoc
           ca khi setup.exe duoc khoi dong, som hon nhieu so voi bat ky
           cai gi trong chinh autounattend.xml nay). -->
      <DiskConfiguration>
        <Disk wcm:action="add">
          {khoi_dia}
        </Disk>
      </DiskConfiguration>
      <ImageInstall>
        <OSImage>
          <InstallFrom>{_khoi_credentials_samba() if duong_install is None else ""}
            <Path>{_esc(duong_install_mac_dinh)}</Path>
            <MetaData wcm:action="add">
              <Key>/IMAGE/INDEX</Key><Value>1</Value>
            </MetaData>
          </InstallFrom>
          <InstallTo>
            <DiskID>{_esc(d.get('o_dia_so', '0'))}</DiskID>
            <PartitionID>3</PartitionID>
          </InstallTo>
        </OSImage>
      </ImageInstall>
      <UserData>
        <AcceptEula>true</AcceptEula>
        <!-- Key KMS client CONG KHAI chinh thuc cua Microsoft cho Windows
             10/11 Pro (khong phai key lau/crack) - dung de Setup chay
             tiep khong can nhap key that luc cai, kich hoat that su lam
             sau (KMS/MAK cua to chuc). Cong khai tai learn.microsoft.com
             "KMS client setup keys". -->
        <ProductKey>
          <Key>VK7JG-NPHTM-C97JM-9MPGT-3V66T</Key>
        </ProductKey>
      </UserData>
    </component>
  </settings>

  <settings pass="specialize">
    <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64"
        publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS"
        xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <ComputerName>{_esc(ten_may)}</ComputerName>
      <TimeZone>{_esc(tz_windows)}</TimeZone>
    </component>
  </settings>

  <settings pass="oobeSystem">
    <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64"
        publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS"
        xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <UserAccounts>
        <LocalAccounts>
          <LocalAccount wcm:action="add">
            <Name>{_esc(username)}</Name>
            <Group>Administrators</Group>
            <Password>
              <Value>{_esc(password)}</Value>
              <PlainText>true</PlainText>
            </Password>
          </LocalAccount>
        </LocalAccounts>
      </UserAccounts>
      <OOBE>
        <HideEULAPage>true</HideEULAPage>
        <HideOEMRegistrationScreen>true</HideOEMRegistrationScreen>
        <HideOnlineAccountScreens>true</HideOnlineAccountScreens>
        <HideWirelessSetupInOOBE>true</HideWirelessSetupInOOBE>
        <NetworkLocation>Work</NetworkLocation>
        <ProtectYourPC>3</ProtectYourPC>
        <SkipMachineOOBE>true</SkipMachineOOBE>
        <SkipUserOOBE>true</SkipUserOOBE>
      </OOBE>
      <TimeZone>{_esc(tz_windows)}</TimeZone>
    </component>
  </settings>
</unattend>
"""


def _phan_tich_lenh_reg(lenh):
    r"""
    Doc 1 lenh `reg add` roi suy ra CACH KIEM TRA lai chinh no.

    VI SAO LAM VAY thay vi viet san 1 bang "tuy chon -> cach kiem tra":
    hai danh sach song song nhu vay chac chan se lech nhau theo thoi gian
    (sua lenh o TUY_CHON_WINDOWS ma quen sua bang kiem tra -> bao cao noi
    doi ma khong ai biet). Suy thang tu chinh lenh se chay thi khong bao
    gio lech duoc.

    Tra ve None neu khong phai `reg add` (powercfg, dism, powershell... -
    nhung cai do nam trong KIEM_TRA_DAC_BIET).
    """
    m = re.match(r'^\s*reg add\s+"([^"]+)"(.*)$', lenh, re.I | re.S)
    if not m:
        return None
    duong, con_lai = m.group(1), m.group(2)
    # HKLM\... -> HKLM:\...  (dang PowerShell dung)
    duong_ps = re.sub(r"^(HKLM|HKCU|HKCR|HKU)\\", r"\1:\\", duong, flags=re.I)

    m_ten = re.search(r'/v\s+("[^"]+"|\S+)', con_lai)
    m_gt = re.search(r'/d\s+("[^"]+"|\S+)', con_lai)
    if not m_ten:
        # `/ve` = dat gia tri mac dinh cua khoa (vd menu chuot phai kieu
        # cu) - chi kiem duoc la KHOA CO TON TAI hay khong.
        if re.search(r"/ve\b", con_lai, re.I):
            return {"loai": "khoa", "duong": duong_ps}
        return None
    if not m_gt:
        return None
    return {"loai": "reg", "duong": duong_ps,
            "ten": m_ten.group(1).strip('"'), "gt": m_gt.group(1).strip('"')}


# Cach kiem tra cho cac tuy chon KHONG phai `reg add` (khong suy tu lenh
# duoc). Moi muc la 1 doan PowerShell tra ve mot hashtable @{Dat=...;
# ChiTiet='...'}. Muc nao khong co o day va cung khong phai reg add thi
# bao cao ghi ro "khong tu kiem duoc" - KHONG bao bua la DAT.
KIEM_TRA_DAC_BIET = {
    "ping": """
        $r = (netsh advfirewall firewall show rule name="ICMPv4 vao" 2>&1 | Out-String)
        @{ Dat = ($r -notmatch 'No rules match'); ChiTiet = 'luat tuong lua ICMPv4' }
    """,
    "khong_ngu": """
        $r = (powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE 2>&1 | Out-String)
        if ($r -match 'Current AC Power Setting Index:\\s*0x0*([0-9a-f]+)') {
            $giay = [Convert]::ToInt32($matches[1], 16)
            @{ Dat = ($giay -eq 0); ChiTiet = "thoi gian cho = $giay giay" }
        } else { @{ Dat = $false; ChiTiet = 'khong doc duoc powercfg' } }
    """,
    "hieu_suat_cao": """
        $r = (powercfg /getactivescheme 2>&1 | Out-String)
        $ten = if ($r -match '\\(([^)]+)\\)') { $matches[1] } else { '?' }
        @{ Dat = ($r -match '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'); ChiTiet = $ten }
    """,
    "ps_chay_script": """
        $p = Get-ExecutionPolicy -Scope LocalMachine
        @{ Dat = ($p -eq 'RemoteSigned'); ChiTiet = "ExecutionPolicy = $p" }
    """,
    "tat_system_restore": """
        $c = Get-CimInstance -Namespace root\\default -ClassName SystemRestoreConfig -EA SilentlyContinue
        if ($c) { @{ Dat = ($c.RPSessionInterval -eq 0); ChiTiet = "RPSessionInterval = $($c.RPSessionInterval)" } }
        else { @{ Dat = $null; ChiTiet = 'khong doc duoc cau hinh System Restore' } }
    """,
    "bat_net_framework35": """
        $f = Get-WindowsOptionalFeature -Online -FeatureName NetFx3 -EA SilentlyContinue
        if ($f) { @{ Dat = ($f.State -eq 'Enabled'); ChiTiet = "State = $($f.State) (can bo nguon sxs)" } }
        else { @{ Dat = $null; ChiTiet = 'khong doc duoc trang thai tinh nang' } }
    """,
}


def _ps_chuoi(s):
    """Boc 1 chuoi Python thanh chuoi PowerShell nháy don an toan."""
    return "'" + str(s).replace("'", "''") + "'"


# Han gio cho MOI buoc cai dat sau khi dang nhap (giay).
#
# VI SAO 45 PHUT: phai du rong cho thu cai lau THAT SU - Office 365 tu
# nguon cuc bo mat 15-25 phut tren may cau hinh thap. Nhung phai co GIOI
# HAN, vi khong co thi mot buoc hong se treo vinh vien: Office tung dung
# im 45 phut (goi may chu Microsoft that bai roi tu thu lai voi khoang
# cho tang gap doi: 3 -> 7 -> 14 -> 28 phut...) ma khong cach nao biet.
# Tha dung 1 buoc, ghi ro "Qua gio" roi cai tiep nhung thu con lai.
GIAY_TOI_DA_MOI_BUOC = 2700


def _muc_kiem_tra(d):
    """
    Dung danh sach cac muc CAN KIEM TRA cho dung kich ban nay.

    DIEM MAU CHOT: chi kiem nhung gi kich ban THUC SU YEU CAU. Bao cao cu
    quet het 28 tuy chon roi bao "HONG" cho nhung muc anh Thoai khong he
    chon la bao cao vo dung - nguoi doc phai tu nho minh da chon gi de
    biet dong nao dang thuc su la loi.
    """
    muc = []

    def them(nhom, nhan, **kw):
        muc.append(dict(nhom=nhom, nhan=nhan, **kw))

    # --- Danh tinh may
    them("May", "Tên máy", loai="ps", ma=f"""
        $t = (Get-CimInstance Win32_ComputerSystem).Name
        @{{ Dat = ($t -eq {_ps_chuoi((d.get('ten_may') or '')[:15])}); ChiTiet = $t }}
    """)
    if d.get("username"):
        them("May", "Tài khoản chính", loai="ps", ma=f"""
            $u = Get-LocalUser -Name {_ps_chuoi(d['username'])} -EA SilentlyContinue
            @{{ Dat = ($u -ne $null); ChiTiet = $(if ($u) {{ 'da tao, Enabled=' + $u.Enabled }} else {{ 'KHONG thay tai khoan' }}) }}
        """)

    # Tai khoan Administrator: tim theo SID -500 (ten doi theo ngon ngu)
    if d.get("bat_admin"):
        them("May", "Tài khoản Administrator đã mở", loai="ps", ma="""
            $a = Get-LocalUser -EA SilentlyContinue | Where-Object { $_.SID.Value -like '*-500' }
            if ($a) { @{ Dat = $a.Enabled; ChiTiet = "$($a.Name) - Enabled=$($a.Enabled)" } }
            else { @{ Dat = $false; ChiTiet = 'khong tim thay tai khoan SID -500' } }
        """)
    if d.get("tu_dang_nhap"):
        them("May", "Tự động đăng nhập", loai="reg",
             duong=r"HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon",
             ten="AutoAdminLogon", gt="1")

    if d.get("domain"):
        them("May", "Gia nhập domain", loai="ps", ma=f"""
            $c = Get-CimInstance Win32_ComputerSystem
            @{{ Dat = ($c.PartOfDomain -and $c.Domain -eq {_ps_chuoi(d['domain'])});
                ChiTiet = $(if ($c.PartOfDomain) {{ $c.Domain }} else {{ 'chua vao domain' }}) }}
        """)

    # --- Tuy chon Windows da tich: suy cach kiem tu CHINH lenh se chay
    da_chon = set(d.get("tuy_chon") or [])
    for ma, nhan, _mo_ta, pha, cac_lenh in TUY_CHON_WINDOWS:
        if ma not in da_chon:
            continue
        nhom = "Tùy chọn máy" if pha == "may" else "Tùy chọn người dùng"
        if ma in KIEM_TRA_DAC_BIET:
            them(nhom, nhan, loai="ps", ma=KIEM_TRA_DAC_BIET[ma])
            continue
        # Lay lenh reg DAU TIEN phan tich duoc lam dai dien cho tuy chon
        # (cac tuy chon nhieu lenh deu la nhieu khoa cua CUNG 1 viec).
        kt = next((k for k in (_phan_tich_lenh_reg(l) for l in cac_lenh) if k), None)
        if kt:
            them(nhom, nhan, **kt)
        else:
            them(nhom, nhan, loai="khong_kiem")

    # --- Go app kem san
    for ma_app in (d.get("go_app") or []):
        ten_app = next((t for m, t, _n in APP_RAC if m == ma_app), ma_app)
        them("Gỡ ứng dụng", ten_app, loai="ps", ma=f"""
            $g = Get-AppxPackage -Name {_ps_chuoi(ma_app)} -EA SilentlyContinue
            @{{ Dat = ($g -eq $null); ChiTiet = $(if ($g) {{ 'VAN CON tren may' }} else {{ 'da go' }}) }}
        """)

    # --- Nhung app PHAI GIU LAI: go nham chung la loi nghiem trong, phai
    #     bao cao du anh Thoai khong he yeu cau kiem.
    for ma_app, ten_app in (("Microsoft.WindowsStore", "Microsoft Store"),
                            ("Microsoft.WindowsCalculator", "Máy tính (Calculator)")):
        them("Phải giữ lại", ten_app, loai="ps", ma=f"""
            $g = Get-AppxPackage -Name {_ps_chuoi(ma_app)} -EA SilentlyContinue
            @{{ Dat = ($g -ne $null); ChiTiet = $(if ($g) {{ 'con nguyen' }} else {{ 'DA BI GO NHAM' }}) }}
        """)

    # --- Phan mem da chon
    for a in _d.chuan_hoa_apps(d.get("apps")):
        them("Phần mềm", a["ten"], loai="ps", ma=f"""
            $f = {_ps_chuoi(THU_MUC_TREN_MAY + chr(92) + 'apps' + chr(92) + a['ten'])}
            @{{ Dat = (Test-Path $f); ChiTiet = $(if (Test-Path $f) {{ 'da chep sang may' }} else {{ 'KHONG thay file' }}) }}
        """)

    # --- Ung dung nhieu file
    for u in _d.chuan_hoa_ungdung(d.get("ungdung")):
        them("Ứng dụng", u["id"], loai="ps", ma=f"""
            $t = {_ps_chuoi(THU_MUC_UNGDUNG_TREN_MAY + chr(92) + u['id'])}
            $n = if (Test-Path $t) {{ (Get-ChildItem $t -Recurse -EA SilentlyContinue).Count }} else {{ 0 }}
            @{{ Dat = (Test-Path $t); ChiTiet = "$n muc trong thu muc" }}
        """)
        if u["id"].lower().startswith("office"):
            them("Ứng dụng", "Office đã cài xong", loai="ps", ma="""
                $k = 'HKLM:\\SOFTWARE\\Microsoft\\Office\\ClickToRun\\Configuration'
                if (Test-Path $k) {
                    $v = (Get-ItemProperty $k -EA SilentlyContinue).VersionToReport
                    @{ Dat = ($v -ne $null); ChiTiet = "phien ban $v" }
                } else { @{ Dat = $false; ChiTiet = 'chua cai (khong co khoa ClickToRun)' } }
            """)

    # --- File noi bo cua Console Pi khong duoc lot sang may khach
    them("Vệ sinh", "File nội bộ _thongtin.json không lọt sang", loai="ps", ma=f"""
        $l = @(Get-ChildItem {_ps_chuoi(THU_MUC_UNGDUNG_TREN_MAY)} -Recurse -Filter '_thongtin.json' -EA SilentlyContinue)
        @{{ Dat = ($l.Count -eq 0); ChiTiet = "$($l.Count) file" }}
    """)

    return muc


def _danh_sach_buoc_nguoi_dung(d):
    """
    Danh sach cac buoc se chay SAU KHI dang nhap, dang (ten_hien_thi, lenh).

    Ten hien thi la thu nguoi dung doc tren bang tien trinh, nen phai la
    tieng Viet de hieu ("Cài Google Chrome") chu khong phai dong lenh tho.
    """
    ra = []

    for nhan, lenh in zip(_nhan_tuy_chon(d, "nguoi_dung"),
                          _lenh_theo_pha(d, "nguoi_dung")):
        ra.append((nhan, lenh))

    if d.get("go_app"):
        for lenh in _lenh_go_app(d):
            ra.append((f"Gỡ {len(d['go_app'])} ứng dụng kèm sẵn", lenh))

    for a in _d.chuan_hoa_apps(d.get("apps")):
        if a.get("dich") == "nguoi_dung":
            ra.append((f"Cài {a['ten']}", _lenh_cai_app(a)))

    for u in _d.chuan_hoa_ungdung(d.get("ungdung")):
        if u.get("dich") != "nguoi_dung":
            continue
        lenh = _lenh_cai_ungdung(u)
        if lenh:
            o = _d.lay_ungdung(u["id"]) or {}
            ra.append((f"Cài {o.get('ten_hien_thi') or u['id']}", lenh))

    for ten in (d.get("scripts") or []):
        ra.append((f"Chạy script {ten}",
                   f'"{THU_MUC_TREN_MAY}\\scripts\\{ten}"'))

    for dong in (d.get("lenh_them") or "").splitlines():
        dong = dong.strip()
        if dong and not dong.startswith("#"):
            ra.append(("Lệnh thêm", dong))

    return ra


def _nhan_tuy_chon(d, pha):
    """Ten de hieu cua tung LENH trong cac tuy chon da tich, dung pha.

    1 tuy chon co the sinh ra NHIEU lenh (vd "Bat Remote Desktop" = 1 lenh
    reg + 1 lenh mo tuong lua), nen phai tra ve 1 nhan cho MOI lenh thi
    moi ghep 1-1 voi _lenh_theo_pha() duoc.
    """
    da_chon = set(d.get("tuy_chon") or [])
    ra = []
    for ma, nhan, _mo, pha_muc, cac_lenh in TUY_CHON_WINDOWS:
        if ma in da_chon and pha_muc == pha:
            ra.extend([nhan] * len(cac_lenh))
    return ra


def sinh_script_tien_trinh(d, dia_chi_pi):
    r"""
    Sinh script PowerShell DIEU PHOI toan bo viec cai dat sau khi dang nhap,
    kem CUA SO TIEN TRINH hien ngay tren man hinh may dich.

    VI SAO GOP LAI MOT SCRIPT thay vi de Windows chay tung
    FirstLogonCommand rieng le nhu truoc:

    1. HIEN TIEN TRINH NGAY TREN MAY DICH. Nguoi dung dung ngay truoc may
       phai nhin thay dang cai cai gi, con bao nhieu cai nua. Cua so cmd
       cua FirstLogonCommand thi chu chay vut qua roi TU DONG DONG, khong
       ai kip doc (anh Thoai da gap dung viec nay voi ca bao cao cuoi).

    2. BAO NGUOC VE PI de xem tu xa - xem ui/tiendo.py.

    3. CO GIOI HAN THOI GIAN CHO TUNG BUOC. Day la thu quan trong nhat.
       LOI THAT DA GAP: Office 365 goi ra may chu Microsoft xin token,
       khong duoc, roi TU THU LAI voi khoang cho tang gap doi moi lan
       (3 -> 7 -> 14 -> 28 phut...). Windows khong co timeout nao cho
       FirstLogonCommand, nen ca qua trinh cai dung im 45 phut ma man
       hinh khong khac gi luc chay binh thuong. Nay moi buoc co han gio
       rieng, qua han thi GIET tien trinh do, ghi "Qua gio" va DI TIEP.

    4. MOT BUOC HONG KHONG KEO SAP CA CHUOI.

    KY THUAT GIU CUA SO SONG: PowerShell chi co 1 luong. Trong luc cho
    mot buoc cai xong (co the ca chuc phut) ma khong lam gi thi Windows
    danh dau cua so la "Not Responding" va lam mo di - nhin nhu treo may.
    Nen thay vi WaitForExit() mot mach, phai vong lap ngan: cu 300ms lai
    goi DoEvents() de cua so ve lai, cap nhat dong ho dem giay, roi kiem
    tra tien trinh xong chua.
    """
    buoc = _danh_sach_buoc_nguoi_dung(d)
    dong = []
    for ten, lenh in buoc:
        dong.append(f"  @{{ Ten={_ps_chuoi(ten)}; Lenh={_ps_chuoi(lenh)} }}")
    mang_buoc = ",\n".join(dong) if dong else ""

    ten_kb = d.get("tu_kichban") or d.get("ten_kichban") or "(khong ten)"

    return f"""# ============================================================
#  Console Pi - dieu phoi cai dat sau khi dang nhap
#  Tu sinh theo kich ban, KHONG sua bang tay (se bi ghi de lan cai sau).
# ============================================================
$ErrorActionPreference = 'Continue'
$Pi         = '{dia_chi_pi}'
$TenMay     = $env:COMPUTERNAME
$KichBan    = {_ps_chuoi(ten_kb)}
$HanGioGiay = {GIAY_TOI_DA_MOI_BUOC}

$Buoc = @(
{mang_buoc}
)

$ThuMuc = 'C:\\ConsolePi'
if (-not (Test-Path $ThuMuc)) {{ New-Item -ItemType Directory -Path $ThuMuc -Force | Out-Null }}
$Log = Join-Path $ThuMuc 'tien-trinh.log'

function Ghi($t) {{
    Add-Content -Path $Log -Value ((Get-Date -Format 'HH:mm:ss') + '  ' + $t) `
        -Encoding UTF8 -EA SilentlyContinue
}}

# Bao ve Pi. TUYET DOI khong duoc lam dung qua trinh cai: loi thi bo qua,
# han gio ngan (4 giay) vi Pi co the da bi rut day mang tu luc nao.
function BaoPi($duong, $goi) {{
    try {{
        Invoke-RestMethod -Uri "http://$Pi/api/tiendo/$duong" -Method Post `
            -Body ($goi | ConvertTo-Json -Compress) -ContentType 'application/json' `
            -TimeoutSec 4 | Out-Null
    }} catch {{ }}
}}

# ------------------------------------------------------------ cua so
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

$frm = New-Object System.Windows.Forms.Form
$frm.Text = "Console Pi - Đang cài đặt phần mềm"
$frm.Size = New-Object System.Drawing.Size(720, 520)
$frm.StartPosition = 'CenterScreen'
$frm.BackColor = [System.Drawing.Color]::FromArgb(24, 26, 30)
$frm.TopMost = $true
# Khong cho dong giua chung: dong cua so KHONG dung duoc viec cai dang
# chay ngam, chi lam mat cho theo doi - de lai nguoi dung tuong da xong.
$frm.FormBorderStyle = 'FixedSingle'
$frm.MaximizeBox = $false
$frm.ControlBox = $false

$lblTo = New-Object System.Windows.Forms.Label
$lblTo.Text = "Đang cài đặt phần mềm cho máy này"
$lblTo.ForeColor = [System.Drawing.Color]::White
$lblTo.Font = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$lblTo.Location = New-Object System.Drawing.Point(18, 14)
$lblTo.Size = New-Object System.Drawing.Size(660, 30)
$frm.Controls.Add($lblTo)

$lblPhu = New-Object System.Windows.Forms.Label
$lblPhu.Text = "Kịch bản: $KichBan   —   Xin đừng tắt máy trong lúc đang cài."
$lblPhu.ForeColor = [System.Drawing.Color]::FromArgb(150, 158, 170)
$lblPhu.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$lblPhu.Location = New-Object System.Drawing.Point(20, 46)
$lblPhu.Size = New-Object System.Drawing.Size(660, 20)
$frm.Controls.Add($lblPhu)

$thanh = New-Object System.Windows.Forms.ProgressBar
$thanh.Location = New-Object System.Drawing.Point(20, 74)
$thanh.Size = New-Object System.Drawing.Size(660, 16)
$thanh.Minimum = 0
$thanh.Maximum = [Math]::Max(1, $Buoc.Count)
$frm.Controls.Add($thanh)

$lv = New-Object System.Windows.Forms.ListView
$lv.Location = New-Object System.Drawing.Point(20, 102)
$lv.Size = New-Object System.Drawing.Size(660, 330)
$lv.View = 'Details'
$lv.FullRowSelect = $true
$lv.GridLines = $false
$lv.BackColor = [System.Drawing.Color]::FromArgb(31, 34, 39)
$lv.ForeColor = [System.Drawing.Color]::White
$lv.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$lv.Columns.Add("", 40) | Out-Null
$lv.Columns.Add("Bước", 400) | Out-Null
$lv.Columns.Add("Trạng thái", 130) | Out-Null
$lv.Columns.Add("Giây", 70) | Out-Null
$frm.Controls.Add($lv)

foreach ($b in $Buoc) {{
    $it = New-Object System.Windows.Forms.ListViewItem("")
    $it.SubItems.Add($b.Ten) | Out-Null
    $it.SubItems.Add("chờ...") | Out-Null
    $it.SubItems.Add("") | Out-Null
    $it.ForeColor = [System.Drawing.Color]::FromArgb(130, 138, 150)
    $lv.Items.Add($it) | Out-Null
}}

$lblDay = New-Object System.Windows.Forms.Label
$lblDay.Text = ""
$lblDay.ForeColor = [System.Drawing.Color]::FromArgb(150, 158, 170)
$lblDay.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$lblDay.Location = New-Object System.Drawing.Point(20, 442)
$lblDay.Size = New-Object System.Drawing.Size(520, 22)
$frm.Controls.Add($lblDay)

$btnDong = New-Object System.Windows.Forms.Button
$btnDong.Text = "Đóng"
$btnDong.Location = New-Object System.Drawing.Point(580, 438)
$btnDong.Size = New-Object System.Drawing.Size(100, 32)
$btnDong.Enabled = $false          # chi bat khi da cai xong het
$btnDong.Add_Click({{ $frm.Close() }})
$frm.Controls.Add($btnDong)

$frm.Show()
[System.Windows.Forms.Application]::DoEvents()

function DatDong($i, $bieu, $tt, $giay, $mau) {{
    $lv.Items[$i].Text = $bieu
    $lv.Items[$i].SubItems[2].Text = $tt
    $lv.Items[$i].SubItems[3].Text = $giay
    $lv.Items[$i].ForeColor = $mau
    $lv.EnsureVisible($i)
    [System.Windows.Forms.Application]::DoEvents()
}}

$XANH  = [System.Drawing.Color]::FromArgb(110, 231, 160)
$VANG  = [System.Drawing.Color]::FromArgb(245, 158, 11)
$DO    = [System.Drawing.Color]::FromArgb(255, 107, 107)
$XAM   = [System.Drawing.Color]::FromArgb(130, 138, 150)

Ghi "===== Bat dau cai dat: $KichBan ====="
BaoPi 'batdau' @{{ may = $TenMay; kichban = $KichBan;
                   buoc = @($Buoc | ForEach-Object {{ $_.Ten }}) }}

$i = 0
$soLoi = 0
foreach ($b in $Buoc) {{
    $lblDay.Text = "Đang làm bước $($i + 1) / $($Buoc.Count)..."
    DatDong $i ">" "đang chạy..." "" $VANG
    Ghi ("[{{0}}/{{1}}] {{2}}" -f ($i + 1), $Buoc.Count, $b.Ten)
    BaoPi 'buoc' @{{ may = $TenMay; chi_so = $i; trang_thai = 'dang' }}

    $t0 = Get-Date
    $tt = 'xong'; $ghiChu = ''
    try {{
        $p = Start-Process -FilePath 'cmd.exe' `
             -ArgumentList '/c', $b.Lenh -PassThru -WindowStyle Hidden
        # Vong cho NGAN + DoEvents: giu cua so song va dem giay. Neu dung
        # WaitForExit() mot mach thi Windows bao "Not Responding" va lam
        # mo cua so - nhin y het treo may.
        while (-not $p.HasExited) {{
            Start-Sleep -Milliseconds 300
            $gi = [int]((Get-Date) - $t0).TotalSeconds
            $lv.Items[$i].SubItems[3].Text = "$gi"
            [System.Windows.Forms.Application]::DoEvents()
            if ($gi -ge $HanGioGiay) {{
                try {{ & taskkill /PID $p.Id /T /F 2>&1 | Out-Null }} catch {{ }}
                $tt = 'qua_gio'
                $ghiChu = "Quá $HanGioGiay giây — đã dừng bước này để đi tiếp"
                break
            }}
        }}
        if ($tt -eq 'xong' -and $p.ExitCode -ne 0) {{
            $tt = 'loi'; $ghiChu = "Mã lỗi: $($p.ExitCode)"
        }}
    }} catch {{
        $tt = 'loi'; $ghiChu = $_.Exception.Message
    }}

    $giay = [int]((Get-Date) - $t0).TotalSeconds
    if ($tt -eq 'xong') {{
        DatDong $i ([char]0x2714) "xong" "$giay" $XANH
    }} elseif ($tt -eq 'qua_gio') {{
        $soLoi++
        DatDong $i ([char]0x2718) "quá giờ" "$giay" $DO
    }} else {{
        $soLoi++
        DatDong $i ([char]0x2718) "lỗi" "$giay" $DO
    }}
    Ghi ("      -> {{0}} ({{1}}s) {{2}}" -f $tt, $giay, $ghiChu)
    BaoPi 'buoc' @{{ may = $TenMay; chi_so = $i; trang_thai = $tt;
                     giay = $giay; ghi_chu = $ghiChu }}

    $thanh.Value = [Math]::Min($thanh.Maximum, $i + 1)
    [System.Windows.Forms.Application]::DoEvents()
    $i++
}}

Ghi "===== Xong ====="
BaoPi 'ketthuc' @{{ may = $TenMay }}

if ($soLoi -eq 0) {{
    $lblDay.Text = "Xong tất cả $($Buoc.Count) bước. Không có lỗi."
    $lblDay.ForeColor = $XANH
}} else {{
    $lblDay.Text = "Xong, nhưng có $soLoi bước không đạt — xem dòng màu đỏ."
    $lblDay.ForeColor = $DO
}}
$lblTo.Text = "Đã cài đặt xong"
$btnDong.Enabled = $true
$frm.ControlBox = $true
[System.Windows.Forms.Application]::DoEvents()

# Dung yen cho toi khi bam Dong. Khong tu dong dong: nguoi di cai may
# phai co co hoi doc xem buoc nao hong - day la ly do cua ca cua so nay.
$frm.TopMost = $false
[void]$frm.ShowDialog()
"""


def sinh_script_bao_cao(d):
    """
    Sinh script PowerShell hien BAO CAO TONG KET cuoi cung.

    Chay LUON LUON o buoc cuoi cua moi lan cai (khong phai tuy chon) -
    xem _khoi_firstlogon(). Nhung thu no doi chieu duoc suy ra tu CHINH
    kich ban dang chay (xem _muc_kiem_tra), nen doc bao cao la biet ngay
    may co dung y muon hay khong, khong phai tu nho minh da chon gi.

    Hien bang cua so do hoa (WinForms) chu khong phai cua so cmd: cua so
    cmd cua FirstLogonCommands TU DONG DONG ngay khi lenh chay xong,
    khong kip doc (anh Thoai da gap dung viec nay). Cua so nay dung yen
    cho toi khi bam Dong.
    """
    muc = _muc_kiem_tra(d)

    dong_muc = []
    for m in muc:
        nhom = _ps_chuoi(m["nhom"])
        nhan = _ps_chuoi(m["nhan"])
        if m["loai"] == "reg":
            dong_muc.append(
                f"  @{{ Nhom={nhom}; Nhan={nhan}; Loai='reg'; "
                f"Duong={_ps_chuoi(m['duong'])}; Ten={_ps_chuoi(m['ten'])}; "
                f"Gt={_ps_chuoi(m['gt'])} }}")
        elif m["loai"] == "khoa":
            dong_muc.append(
                f"  @{{ Nhom={nhom}; Nhan={nhan}; Loai='khoa'; "
                f"Duong={_ps_chuoi(m['duong'])} }}")
        elif m["loai"] == "ps":
            # Doan kiem tra rieng - boc vao scriptblock
            dong_muc.append(
                f"  @{{ Nhom={nhom}; Nhan={nhan}; Loai='ps'; "
                f"Ma={{{m['ma']}}} }}")
        else:
            dong_muc.append(
                f"  @{{ Nhom={nhom}; Nhan={nhan}; Loai='khong_kiem' }}")

    bang = "$MUC = @(\n" + ",\n".join(dong_muc) + "\n)\n"

    # "tu_kichban" co khi bam Dung tu trang kich ban; "ten_kichban" la ten
    # nam trong chinh file kich ban da luu. Lay ca hai de bao cao luon noi
    # duoc no dang doi chieu theo kich ban nao.
    ten_kb = (d.get("tu_kichban") or d.get("ten_kichban")
              or "(chạy trực tiếp, chưa lưu thành kịch bản)")

    # Phan than script la template TINH - khong dung f-string de khoi
    # phai escape hang tram dau { } cua PowerShell.
    than = r"""
# ============================================================
#  Console Pi - BAO CAO TONG KET SAU KHI CAI
#  (sinh tu dong theo dung kich ban da chay - khong sua tay)
# ============================================================
$ErrorActionPreference = 'SilentlyContinue'

$OutDir  = 'C:\ConsolePi'
$OutFile = Join-Path $OutDir 'BAO-CAO-TONG-KET.txt'
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }

function Doc-Reg($duong, $ten) {
    try { return (Get-ItemProperty -Path $duong -Name $ten -EA Stop).$ten } catch { return $null }
}

$ketQua = @()
foreach ($m in $MUC) {
    $dat = $null; $ct = ''
    switch ($m.Loai) {
        'reg' {
            $that = Doc-Reg $m.Duong $m.Ten
            if ($null -eq $that) { $dat = $false; $ct = 'khong tim thay gia tri' }
            else { $dat = ("$that" -eq "$($m.Gt)"); $ct = "= $that" + $(if (-not $dat) { " (can $($m.Gt))" } else { '' }) }
        }
        'khoa' {
            $dat = Test-Path $m.Duong
            $ct = $(if ($dat) { 'khoa da duoc tao' } else { 'khong thay khoa' })
        }
        'ps' {
            try { $r = & $m.Ma; $dat = $r.Dat; $ct = [string]$r.ChiTiet }
            catch { $dat = $false; $ct = 'loi khi kiem: ' + $_.Exception.Message }
        }
        default { $dat = $null; $ct = 'muc nay khong tu kiem duoc' }
    }
    $ketQua += [PSCustomObject]@{
        Nhom = $m.Nhom; Nhan = $m.Nhan
        Dat = $dat
        ChiTiet = $ct
        TrangThai = $(if ($dat -eq $true) { 'DAT' } elseif ($dat -eq $false) { 'CHUA DAT' } else { 'khong ro' })
    }
}

$soDat   = @($ketQua | Where-Object { $_.Dat -eq $true }).Count
$soHong  = @($ketQua | Where-Object { $_.Dat -eq $false }).Count
$soKhong = @($ketQua | Where-Object { $_.Dat -eq $null }).Count

# ---------- Ghi ra file (luon ghi, du co ai doc popup hay khong) ----------
$txt = New-Object System.Collections.Generic.List[string]
$txt.Add('================================================================')
$txt.Add('   CONSOLE PI - BAO CAO TONG KET SAU KHI CAI')
$txt.Add('   Kich ban : ' + $TEN_KICHBAN)
$txt.Add('   May      : ' + $env:COMPUTERNAME + '   |   Nguoi dung: ' + $env:USERNAME)
$txt.Add('   Thoi diem: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
$txt.Add('================================================================')
$txt.Add('')
$txt.Add("   DAT: $soDat     CHUA DAT: $soHong     khong ro: $soKhong")
$txt.Add('')
foreach ($nhom in ($ketQua | Select-Object -ExpandProperty Nhom -Unique)) {
    $txt.Add('--- ' + $nhom + ' ' + ('-' * [Math]::Max(0, 50 - $nhom.Length)))
    foreach ($r in ($ketQua | Where-Object { $_.Nhom -eq $nhom })) {
        $txt.Add(('  [{0,-9}] {1,-44} {2}' -f $r.TrangThai, $r.Nhan, $r.ChiTiet))
    }
    $txt.Add('')
}
$txt.Add('--- Thong tin them -------------------------------------')
$os = Get-CimInstance Win32_OperatingSystem
$txt.Add('  Windows : ' + $os.Caption + ' (build ' + $os.BuildNumber + ')')
foreach ($c in (Get-NetAdapter -Physical | Where-Object Status -eq 'Up')) {
    $ip = Get-NetIPAddress -InterfaceIndex $c.InterfaceIndex -AddressFamily IPv4 |
          Where-Object { $_.IPAddress -notlike '169.254.*' } | Select-Object -First 1
    $txt.Add('  Mang    : ' + $c.Name + ' - ' + $(if ($ip) { $ip.IPAddress } else { 'chua co IP' }))
}
$thieu = @(Get-CimInstance Win32_PnPEntity | Where-Object { $_.ConfigManagerErrorCode -ne 0 })
$txt.Add('  Thiet bi thieu driver: ' + $thieu.Count)
foreach ($t in $thieu) { $txt.Add('      - ' + $t.Name) }
$txt -join "`r`n" | Out-File -FilePath $OutFile -Encoding UTF8

# ---------- Cua so bao cao ----------
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

# Ten bien la $frm chu khong phai $f: cac doan kiem tra rieng o tren co
# dung bien $f (vd Get-WindowsOptionalFeature), de trung ten thi rat kho
# lan ra khi hong.
$frm = New-Object System.Windows.Forms.Form
$frm.Text = 'Console Pi - Bao cao tong ket sau khi cai'
$frm.Size = New-Object System.Drawing.Size(940, 720)
$frm.StartPosition = 'CenterScreen'
$frm.BackColor = [System.Drawing.Color]::FromArgb(248, 249, 251)
$frm.TopMost = $true
$frm.MinimumSize = New-Object System.Drawing.Size(700, 480)

# --- Dai mau tren cung: xanh neu khong con muc nao chua dat
$mauNen = if ($soHong -eq 0) { [System.Drawing.Color]::FromArgb(22, 128, 70) } else { [System.Drawing.Color]::FromArgb(180, 45, 45) }
$head = New-Object System.Windows.Forms.Panel
$head.Dock = 'Top'; $head.Height = 96; $head.BackColor = $mauNen
$frm.Controls.Add($head)

$lblTo = New-Object System.Windows.Forms.Label
$lblTo.Text = if ($soHong -eq 0) { "HOAN TAT - tat ca $soDat muc deu DAT" } else { "HOAN TAT - co $soHong muc CHUA DAT" }
$lblTo.Font = New-Object System.Drawing.Font('Segoe UI', 19, [System.Drawing.FontStyle]::Bold)
$lblTo.ForeColor = [System.Drawing.Color]::White
$lblTo.AutoSize = $true; $lblTo.Location = New-Object System.Drawing.Point(22, 16)
$head.Controls.Add($lblTo)

$lblPhu = New-Object System.Windows.Forms.Label
$lblPhu.Text = "May: $env:COMPUTERNAME     Kich ban: $TEN_KICHBAN     " + (Get-Date -Format 'yyyy-MM-dd HH:mm')
$lblPhu.Font = New-Object System.Drawing.Font('Segoe UI', 10)
$lblPhu.ForeColor = [System.Drawing.Color]::FromArgb(232, 240, 236)
$lblPhu.AutoSize = $true; $lblPhu.Location = New-Object System.Drawing.Point(24, 58)
$head.Controls.Add($lblPhu)

# --- Thanh nut duoi cung (phai them TRUOC bang ket qua)
# THU TU THEM QUAN TRONG: WinForms dock theo z-order, control them SAU
# nam duoi cung z-order va duoc dock SAU CUNG. Control Dock='Fill' phai
# la cai them SAU CUNG thi no moi chiem dung phan con lai; them no o
# giua thi hai thanh Top/Bottom se de len no.
$foot = New-Object System.Windows.Forms.Panel
$foot.Dock = 'Bottom'; $foot.Height = 58
$foot.BackColor = [System.Drawing.Color]::FromArgb(238, 240, 244)
$frm.Controls.Add($foot)

$lblFile = New-Object System.Windows.Forms.Label
$lblFile.Text = 'Da luu ban day du vao: ' + $OutFile
$lblFile.Font = New-Object System.Drawing.Font('Segoe UI', 9)
$lblFile.ForeColor = [System.Drawing.Color]::FromArgb(90, 95, 105)
$lblFile.AutoSize = $true; $lblFile.Location = New-Object System.Drawing.Point(18, 20)
$foot.Controls.Add($lblFile)

$btnMo = New-Object System.Windows.Forms.Button
$btnMo.Text = 'Mo file bao cao'; $btnMo.Size = New-Object System.Drawing.Size(140, 34)
$btnMo.Font = New-Object System.Drawing.Font('Segoe UI', 10)
$btnMo.Anchor = 'Top,Right'
$btnMo.Location = New-Object System.Drawing.Point(($foot.Width - 300), 12)
$btnMo.Add_Click({ Start-Process notepad.exe $OutFile })
$foot.Controls.Add($btnMo)

$btnDong = New-Object System.Windows.Forms.Button
$btnDong.Text = 'Dong'; $btnDong.Size = New-Object System.Drawing.Size(130, 34)
$btnDong.Font = New-Object System.Drawing.Font('Segoe UI', 10, [System.Drawing.FontStyle]::Bold)
$btnDong.Anchor = 'Top,Right'
$btnDong.Location = New-Object System.Drawing.Point(($foot.Width - 150), 12)
$btnDong.Add_Click({ $frm.Close() })
$foot.Controls.Add($btnDong)

# --- Bang ket qua (them SAU CUNG vi Dock='Fill')
$lv = New-Object System.Windows.Forms.ListView
$lv.View = 'Details'; $lv.FullRowSelect = $true; $lv.GridLines = $false
$lv.Dock = 'Fill'; $lv.Font = New-Object System.Drawing.Font('Segoe UI', 10)
$lv.BorderStyle = 'None'
$lv.Columns.Add('Trang thai', 110) | Out-Null
$lv.Columns.Add('Hang muc', 400) | Out-Null
$lv.Columns.Add('Thuc te tren may', 380) | Out-Null

$xanh = [System.Drawing.Color]::FromArgb(20, 115, 62)
$do   = [System.Drawing.Color]::FromArgb(178, 40, 40)
$xam  = [System.Drawing.Color]::FromArgb(130, 130, 140)

foreach ($nhom in ($ketQua | Select-Object -ExpandProperty Nhom -Unique)) {
    $g = New-Object System.Windows.Forms.ListViewItem('')
    $g.SubItems.Add($nhom) | Out-Null
    $g.SubItems.Add('') | Out-Null
    $g.Font = New-Object System.Drawing.Font('Segoe UI', 10, [System.Drawing.FontStyle]::Bold)
    $g.BackColor = [System.Drawing.Color]::FromArgb(238, 240, 244)
    $lv.Items.Add($g) | Out-Null
    foreach ($r in ($ketQua | Where-Object { $_.Nhom -eq $nhom })) {
        $it = New-Object System.Windows.Forms.ListViewItem($r.TrangThai)
        $it.SubItems.Add('     ' + $r.Nhan) | Out-Null
        $it.SubItems.Add($r.ChiTiet) | Out-Null
        if ($r.Dat -eq $true) { $it.ForeColor = $xanh }
        elseif ($r.Dat -eq $false) { $it.ForeColor = $do }
        else { $it.ForeColor = $xam }
        $lv.Items.Add($it) | Out-Null
    }
}
$frm.Controls.Add($lv)

$frm.AcceptButton = $btnDong
[void]$frm.ShowDialog()
"""
    return (f"$TEN_KICHBAN = {_ps_chuoi(ten_kb)}\n\n" + bang + than)


def sinh_diskpart_txt(d):
    """
    Script cho `diskpart /s` - chia o dia theo dung lua chon wizard.

    Kieu MDT: TU chia o dia trong WinPE (thay vi giao cho Windows Setup
    qua DiskConfiguration cua autounattend.xml) - xem ly do that trong
    docstring cua sinh_deploy_cmd().

    Quy uoc chu o (giong het MDT):
      S: = phan vung EFI (System)
      W: = phan vung se chua Windows (luc boot that no se thanh C:)
    Khong dung C: trong WinPE vi chu o do co the da bi chiem san.
    """
    o_dia_so = d.get("o_dia_so", "0")
    dong = [f"select disk {o_dia_so}", "clean", "convert gpt"]

    if d.get("o_dia_che_do") != "chia_tay":
        dong += [
            "create partition efi size=260",
            'format quick fs=fat32 label="System"',
            "assign letter=S",
            "create partition msr size=16",
            "create partition primary",
            'format quick fs=ntfs label="Windows"',
            "assign letter=W",
        ]
    else:
        da_gan_windows = False
        for i, p in enumerate(d.get("phan_vung") or [], start=1):
            fs = (p.get("fs") or "ntfs").lower()
            nhan = p.get("nhan") or ""
            if fs == "msr":
                dong.append(f"create partition msr size={p.get('cd', '16')}")
                continue
            if fs == "fat32" and i == 1:
                dong.append(f"create partition efi size={p.get('cd', '260')}")
                dong.append(f'format quick fs=fat32 label="{nhan or "System"}"')
                dong.append("assign letter=S")
                continue
            if p.get("cd") == "con_lai":
                dong.append("create partition primary")
            else:
                dong.append(f"create partition primary size={p.get('cd', '1024')}")
            dinh_dang = "fat32" if fs == "fat32" else "ntfs"
            dong.append(f'format quick fs={dinh_dang} label="{nhan}"')
            # Phan vung dau tien khong phai EFI/MSR chinh la o he dieu hanh
            if not da_gan_windows:
                dong.append("assign letter=W")
                da_gan_windows = True
            else:
                gan = (p.get("gan") or "").rstrip(":")
                if gan and gan not in ("-", "EFI", "C"):
                    dong.append(f"assign letter={gan}")
                else:
                    dong.append("assign")

    dong.append("exit")
    return "\r\n".join(dong) + "\r\n"


def _lenh_chep_app_script(d):
    """
    Cac dong batch chep phan mem + script tu kho tren Pi (o mang Z: dang
    map trong WinPE) sang thang o dia may dich, vao C:\\ConsolePi\\.

    Chep TUNG FILE DA CHON chu khong chep ca thu muc - kho phan mem tren
    Pi co the rat nang, kich ban nay chi can vai file.
    """
    apps = _d.chuan_hoa_apps(d.get("apps"))
    scripts = d.get("scripts") or []
    ungdung = [u for u in _d.chuan_hoa_ungdung(d.get("ungdung"))
               if _lenh_cai_ungdung(u)]  # bo qua ung dung chua dat lenh cai
    if not apps and not scripts and not ungdung:
        return []

    dong = ["echo     ... chep them phan mem va script sang may dich..."]
    if apps:
        dong.append("if not exist W:\\ConsolePi\\apps mkdir W:\\ConsolePi\\apps")
        for a in apps:
            dong.append(
                f'copy /y "Z:\\apps\\{a["ten"]}" W:\\ConsolePi\\apps\\ '
                ">> %LOG% 2>&1")
            dong.append("if errorlevel 1 goto loi_chep_app")
    if scripts:
        dong.append("if not exist W:\\ConsolePi\\scripts mkdir W:\\ConsolePi\\scripts")
        for ten in scripts:
            dong.append(
                f'copy /y "Z:\\scripts\\{ten}" W:\\ConsolePi\\scripts\\ '
                ">> %LOG% 2>&1")
            dong.append("if errorlevel 1 goto loi_chep_app")
    if ungdung:
        # Ung dung kieu thu muc (mo hinh MDT) - CA THU MUC, khong phai 1
        # file, nen dung `robocopy /E` (chep het thu muc con) thay vi
        # `copy`. LUU Y THAT VE MA LOI ROBOCOPY (khac han cac lenh khac):
        # robocopy tra ve 0-7 la THANH CONG (1 = "co file duoc chep" - VAN
        # la thanh cong, khong phai loi!), CHI >=8 moi la that bai that su.
        # Neu dung `if errorlevel 1` nhu cac lenh copy khac o tren se BAO
        # LOI SAI ngay ca khi chep thanh cong.
        for u in ungdung:
            # LUU Y: dang o giai doan WinPE, o dich la W: (chua boot vao
            # Windows that su) - KHONG dung THU_MUC_UNGDUNG_TREN_MAY (C:,
            # chi dung cho lenh chay SAU khi da boot vao Windows).
            dich = f"W:\\ConsolePi\\ungdung\\{u['id']}"
            # Bao tien trinh RO RANG truoc moi ung dung: ung dung kieu thu
            # muc co the nang vai GB (Office 365 ~3.5GB), robocopy day het
            # dau ra vao %LOG% nen man hinh dung im nhieu phut. Khong co
            # dong nay thi nguoi dung tuong may treo (da xay ra that).
            dong.append(
                f'echo     ... dang chep ung dung "{u["id"]}" - co the mat '
                "vai phut, xin doi...")
            # /XF _thongtin.json: day la file cau hinh NOI BO cua Console Pi
            # (ten hien thi + dong lenh cai), khong phai file cua ung dung -
            # khong duoc chep sang may khach.
            dong.append(
                f'robocopy "Z:\\ungdung\\{u["id"]}" "{dich}" /E /R:2 /W:2 '
                "/XF _thongtin.json >> %LOG% 2>&1")
            dong.append("if errorlevel 8 goto loi_chep_app")
    dong.append("")
    return dong


def sinh_deploy_cmd(d, dia_chi_pi="192.168.98.1"):
    r"""
    Sinh script trien khai chay NGAY TRONG WinPE - mo phong dung cach
    MDT (LiteTouch) lam viec.

    LY DO THAT SU PHAI LAM NHU VAY (ca 1 chuoi kiem chung that, khong
    doan - xem lich su chi tiet trong sinh_autounattend_xml va
    dung_dia_gpt_tu_dong):

      Moi huong "nho Windows Setup tu lay install.wim qua mang" DEU that
      bai, ly do cuoi cung tim ra tu CHINH setupact.log cua Windows Setup:
        "Failed to access network share '\\<pi>\deploy' with credentials
         \consolepi-deploy (status 0x80070035)" (ERROR_BAD_NETPATH)
      - va Samba tren Pi KHONG HE ghi nhan bat ky ket noi nao trong TAT
      CA cac lan thu, trong khi `net use` GO TAY voi CUNG dia chi + CUNG
      tai khoan, trong CUNG phien WinPE do, lai THANH CONG ngay lap tuc
      (anh Thoai da kiem chung truc tiep). Nghia la co che tu ket noi SMB
      cua rieng Windows Setup (InstallFrom/Credentials) khong lam viec
      duoc voi Samba o day - va no nam trong ruot setup.exe, khong sua
      duoc tu ben ngoai.

    CACH MDT LAM (va gio Console Pi lam theo): KHONG CHAY setup.exe CHUT
    NAO. Thay vao do WinPE tu lam tung buoc bang cong cu co san (da kiem
    tra that: dism.exe, diskpart.exe, bcdboot.exe, wpeutil.exe deu CO SAN
    trong boot.wim, ke ca bo provider DISM day du):
        1. wpeinit               -> len mang
        2. net use               -> map kho trien khai (lenh DA CHUNG MINH
                                    chay duoc bang tay)
        3. diskpart /s           -> chia o dia
        4. dism /apply-image     -> bung install.wim ra o W:
        5. copy unattend.xml     -> W:\Windows\Panther (pass specialize +
                                    oobeSystem se chay luc boot lan dau)
        6. bcdboot               -> tao boot loader UEFI tren o S:
        7. wpeutil reboot        -> khoi dong vao Windows vua bung

    Neu bat ky buoc nao loi: KHONG tu khoi dong lai (tranh vong lap vo
    han), ma hien loi ro rang roi mo Command Prompt de xem log that.
    """
    os_id = d.get("os_id", "")
    duong_wim = f"Z:\\os\\{os_id}\\install.wim"

    return "\r\n".join([
        "@echo off",
        "title Console Pi - Trien khai he dieu hanh",
        "set LOG=X:\\deploy_log.txt",
        "echo === Console Pi - bat dau trien khai === > %LOG%",
        "",
        "echo.",
        "echo  ================================================",
        "echo    CONSOLE PI - TRIEN KHAI HE DIEU HANH TU DONG",
        "echo  ================================================",
        "echo.",
        "",
        # ================================================================
        # KHOI TAO MANG - phan mong manh nhat, da phai sua nhieu vong.
        #
        # DU LIEU THAT thu duoc tu chinh X:\deploy_log.txt qua cac lan
        # chay (khong doan):
        #   - Lan A: ngay tu dau `ipconfig` DA co IP hop le -> mang san
        #     sang truoc khi script chay.
        #   - Lan B: `ipconfig` bao "Unable to contact IP driver. General
        #     failure", `ping` bao "The network is not present or not
        #     started" (loi 1222), `net use` bao loi 2138 (Workstation
        #     service chua chay) -> mang CHUA duoc khoi tao gi ca.
        # => setup.exe khoi tao mang BAT DONG BO; script nay (chay qua
        #    RunSynchronousCommand ben trong setup.exe) co the roi vao
        #    BAT KY thoi diem nao trong qua trinh do. Day chinh la ly do
        #    "luc duoc luc khong" - khong phai loi ngau nhien.
        #
        # CACH LAM DUNG (giong LiteTouch cua MDT): khoi tao mang MOT LAN
        # ngay tu dau, roi DOI cho toi khi mang THAT SU thong (ping duoc
        # Pi) - lay ping lam moc kiem chung khach quan, khong tin vao
        # viec "lenh da chay xong". Chi khi L3 da thong moi dung toi SMB.
        # NAP DRIVER CARD MANG TRUOC KHI KHOI TAO MANG.
        # LY DO THAT (kiem chung bang cach trich .inf trong chinh
        # boot.wim ra doc ma phan cung): anh WinPE nay CHI co driver
        # Intel I219 doi 2016-2019; TU doi 2020 tro di (Comet Lake,
        # Tiger Lake, Alder Lake, Raptor Lake, Meteor Lake) va toan bo
        # Intel I225/I226 2.5G thi KHONG CO. May HP/Dell/Lenovo doi moi
        # dung LAN Intel se khong co mang trong WinPE -> khong tai duoc
        # install.wim -> dung hinh (dung hien tuong anh Thoai gap voi
        # MDT). `drvload` la cong cu chinh chu cua WinPE de nap driver
        # luc dang chay - da kiem tra CO SAN trong boot.wim nay.
        # Neu khong danh dau goi driver nao "cho anh boot" thi thu muc
        # nay khong ton tai va vong lap chay qua, khong anh huong gi.
        "echo  [1/6] Nap driver card mang (neu co)...",
        "echo === nap driver cho WinPE === >> %LOG%",
        'if exist X:\\ConsolePiDrivers (for /r X:\\ConsolePiDrivers %%i in '
        '(*.inf) do drvload "%%i" >> %LOG% 2>&1)',
        "",
        "echo  [1/6] Khoi tao mang va doi mang san sang...",
        "echo === khoi tao mang === >> %LOG%",
        "wpeinit >> %LOG% 2>&1",
        "wpeutil InitializeNetwork >> %LOG% 2>&1",
        "set CHO=0",
        "",
        ":cho_mang",
        "set /a CHO+=1",
        f"ping -n 1 -w 1000 {dia_chi_pi} >nul 2>&1",
        "if not errorlevel 1 goto mang_thong",
        "if %CHO% GEQ 40 goto loi_mang_khong_thong",
        # Cu 5 lan doi khong duoc thi khoi tao lai 1 lan (phong truong hop
        # lan khoi tao dau roi vao luc setup.exe dang doi lai card mang).
        "set /a NHAC=%CHO% %% 5",
        "if %NHAC% NEQ 0 goto cho_tiep",
        "echo === khoi tao lai mang lan %CHO% === >> %LOG%",
        "wpeinit >> %LOG% 2>&1",
        "wpeutil InitializeNetwork >> %LOG% 2>&1",
        "",
        ":cho_tiep",
        "echo     dang doi mang san sang... (%CHO%)",
        "ping -n 3 127.0.0.1 >nul",
        "goto cho_mang",
        "",
        ":mang_thong",
        "echo === mang da thong === >> %LOG%",
        "ipconfig >> %LOG% 2>&1",
        "",
        "echo  [2/6] Ket noi kho trien khai tren Console Pi...",
        # TUYET DOI KHONG `net stop workstation` o day.
        #
        # LOI THAT DA GAP khi tung lam vay (log: "=== khoi dong lai dich vu
        # SMB client ===" -> "The Workstation service was stopped/started
        # successfully" -> `net use` bao "System error 1312 - A specified
        # logon session does not exist"): dung dich vu Workstation huy toan
        # bo logon session ma SMB redirector dang giu. Tien trinh cmd dang
        # chay deploy.cmd van giu token cua session DA BI HUY do, nen moi
        # `net use ... /user:...` sau do deu that bai 1312 - du mang va
        # Samba deu hoan toan binh thuong. Day chinh la hien tuong "luc
        # duoc luc khong".
        #
        # Gia thuyet cu (dich vu bind truoc khi co IP nen phai restart) la
        # SAI: nguyen nhan that cua loi 53 truoc day la ket noi SMB cu con
        # ESTABLISHED tren Pi, da duoc xu ly o phia Pi bang
        # `smbcontrol smbd kill-client-ip` luc nap menu.ipxe.
        # O day chi CAN dam bao dich vu dang chay - start khong bao gio
        # huy session, stop thi co.
        "echo === bao dam dich vu SMB client dang chay === >> %LOG%",
        "net start workstation >> %LOG% 2>&1",
        "net config workstation >> %LOG% 2>&1",
        "set THU=0",
        "",
        ":thu_ket_noi",
        "set /a THU+=1",
        "echo --- ket noi lan thu %THU% --- >> %LOG%",
        # Xoa phien cu (neu co) truoc moi lan thu - phien hong nua chung
        # se lam lan thu sau bao loi y het du van de goc da het.
        "net use Z: /delete /y >nul 2>&1",
        f"net use Z: \\\\{dia_chi_pi}\\deploy /user:{TEN_TAI_KHOAN_SAMBA} "
        f"{_doc_mat_khau_samba()} >> %LOG% 2>&1",
        "if not errorlevel 1 goto ket_noi_xong",
        "if %THU% GEQ 10 goto loi_mang",
        # KHONG dung `sc` o day - WinPE nay KHONG co sc.exe (da kiem chung
        # that: log bao "'sc' is not recognized as an internal or external
        # command"). Dung `net` (luon co san) de chan doan.
        "net start workstation >> %LOG% 2>&1",
        "net view \\\\" + dia_chi_pi + " >> %LOG% 2>&1",
        "echo     chua ket noi duoc, thu lai lan %THU% ...",
        "ping -n 4 127.0.0.1 >nul",
        "goto thu_ket_noi",
        "",
        ":ket_noi_xong",
        "echo  [2/6] Da ket noi kho trien khai.",
        # LUU Y CU PHAP BATCH (loi that da tranh duoc): KHONG duoc viet
        # `if errorlevel 1 set X=...& goto nhan` - cmd.exe tach thanh
        # `(if errorlevel 1 set X=...) & (goto nhan)`, tuc la LUON LUON
        # nhay bat ke dieu kien. Cung KHONG dung block `( )` vi thong bao
        # co the chua dau ngoac lam vo parse. Dung nhan rieng cho tung loi
        # la cach chac chan dung nhat.
        f"if not exist {duong_wim} goto loi_thieu_wim",
        "",
        "echo  [3/6] Chia lai o dia - toan bo du lieu cu se mat...",
        "diskpart /s X:\\diskpart.txt >> %LOG% 2>&1",
        "if errorlevel 1 goto loi_dia",
        "",
        "echo  [4/6] Bung anh he dieu hanh - buoc nay lau nhat, xin doi...",
        "echo.",
        f"dism /apply-image /imagefile:{duong_wim} /index:1 /applydir:W:\\ "
        "/logpath:X:\\dism_log.txt",
        "if errorlevel 1 goto loi_bung",
        "",
        "echo.",
        "echo  [5/6] Chep cau hinh tu dong - ten may, tai khoan, mui gio...",
        "if not exist W:\\Windows\\Panther mkdir W:\\Windows\\Panther",
        "copy /y X:\\unattend.xml W:\\Windows\\Panther\\unattend.xml >> %LOG% 2>&1",
        "if errorlevel 1 goto loi_chep",
        "",
        # Chep phan mem + script sang THANG o dia may dich NGAY BAY GIO,
        # trong khi con o WinPE va o mang Z: dang chac chan hoat dong.
        # LY DO: luc Windows chay lan dau va cai cac phan mem nay, no se
        # doc file tu o C: cua chinh no - KHONG can mang, khong can tai
        # khoan Samba. Dung cai cho da gay ra rat nhieu rac roi truoc day
        # (loi 53, phien SMB ket...) nen khong lap lai o giai doan do.
    ] + _lenh_chep_app_script(d) + [
        # BAO CAO TONG KET - chep LUON LUON, khong phu thuoc lua chon nao.
        # Lay tu X:\ (da nhung san trong boot.wim) chu KHONG qua Samba:
        # bao cao la thu cuoi cung con lai de biet ca ca lan cai co dung
        # y hay khong, khong duoc phep phu thuoc vao mang con song hay
        # kho Samba con ket noi duoc hay khong.
        "if not exist W:\\ConsolePi mkdir W:\\ConsolePi",
        "copy /y X:\\bao-cao.ps1 W:\\ConsolePi\\bao-cao.ps1 >> %LOG% 2>&1",
        "copy /y X:\\tien-trinh.ps1 W:\\ConsolePi\\tien-trinh.ps1 >> %LOG% 2>&1",
        "",
        "echo  [6/6] Tao boot loader UEFI...",
        "bcdboot W:\\Windows /s S: /f UEFI >> %LOG% 2>&1",
        "if errorlevel 1 goto loi_boot",
        "",
        "echo XONG >> %LOG%",
        "echo.",
        "echo  ================================================",
        "echo    HOAN TAT - khoi dong lai sau 10 giay",
        "echo  ================================================",
        "ping -n 11 127.0.0.1 >nul",
        "wpeutil reboot",
        "exit",
        "",
        ":loi_mang_khong_thong",
        f"set BUOC=Mang khong thong toi Console Pi ({dia_chi_pi}) - kiem tra "
        "day mang da cam dung chua",
        "goto bao_loi",
        "",
        ":loi_mang",
        "set BUOC=Mang thong nhung khong ket noi duoc kho trien khai - kiem "
        "tra dich vu Samba tren Pi",
        "goto bao_loi",
        "",
        ":loi_thieu_wim",
        f"set BUOC=Khong tim thay {duong_wim}",
        "goto bao_loi",
        "",
        ":loi_dia",
        "set BUOC=Chia o dia that bai",
        "goto bao_loi",
        "",
        ":loi_bung",
        "set BUOC=Bung anh he dieu hanh that bai - xem X:\\dism_log.txt",
        "goto bao_loi",
        "",
        ":loi_chep",
        "set BUOC=Chep unattend.xml that bai",
        "goto bao_loi",
        "",
        ":loi_chep_app",
        "set BUOC=Chep phan mem/script sang may dich that bai",
        "goto bao_loi",
        "",
        ":loi_boot",
        "set BUOC=Tao boot loader that bai",
        "goto bao_loi",
        "",
        ":bao_loi",
        "echo LOI: %BUOC% >> %LOG%",
        "echo.",
        "echo  ================================================",
        "echo    LOI: %BUOC%",
        "echo.",
        "echo    Xem chi tiet:  type %LOG%",
        "echo  ================================================",
        "echo.",
        # Script co the chay AN (khong hien cua so) khi duoc goi tu
        # RunSynchronousCommand cua Windows Setup - nen mo Notepad hien
        # log ra man hinh de nguoi dung doc duoc ngay, khong phai tu di
        # tim file. Notepad co san trong WinPE (da kiem chung that).
        "start notepad %LOG%",
        "cmd",
        "",
    ]) + "\r\n"


def sinh_autounattend_goi_script():
    r"""
    autounattend.xml TOI GIAN - chi lam DUNG 1 viec: goi script trien khai
    cua Console Pi (X:\deploy.cmd), khong khai bao DiskConfiguration hay
    ImageInstall gi ca (script tu lam het bang diskpart + dism).

    LY DO THAT SU PHAI LAM KIEU NAY (chuoi kiem chung that, khong doan):

      1. Thay setup.exe bang script rieng qua winpeshl.ini: script CHAY
         DUOC (da thay man hinh Console Pi that), nhung `net use` bao
         "System error 53 - network path not found", va tcpdump tren Pi
         cho thay client KHONG GUI BAT KY GOI NAO toi cong 445 - tuc bo
         SMB client phia Windows chua hoat dong, du:
           - ping tu may do sang Pi THONG hoan toan (4/4 reply)
           - `net start workstation/mup/rdbss/mrxsmb/mrxsmb20` deu bao
             "already been started"
           - wpeinit + wpeutil InitializeNetwork da chay xong, da co IP
      2. NHUNG khi de setup.exe chay binh thuong roi bam Shift+F10 mo
         Command Prompt, thi CUNG lenh `net use` do lai THANH CONG ngay
         (anh Thoai da lam that nhieu lan). Khac biet DUY NHAT giua 2
         truong hop la: co setup.exe chay hay khong.
      => Ket luan: chinh setup.exe (moi truong Windows Setup) moi kich
         hoat day du bo SMB client trong anh boot.wim nay. Vay ta KHONG
         thay the setup.exe nua, ma de no chay binh thuong, roi nho no
         goi script cua minh qua RunSynchronousCommand (co che nay DA
         duoc kiem chung la chay that - lan truoc no da ghi duoc file
         netinit_log.txt).

    Script se tu reboot khi xong nen Setup khong bao gio kip hien giao
    dien hoi gi - nguoi dung chi thay man hinh tien trinh cua Console Pi.
    """
    return """<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
  <settings pass="windowsPE">
    <component name="Microsoft-Windows-International-Core-WinPE"
        processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35"
        language="neutral" versionScope="nonSxS"
        xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <SetupUILanguage><UILanguage>en-US</UILanguage></SetupUILanguage>
      <InputLocale>en-US</InputLocale>
      <SystemLocale>en-US</SystemLocale>
      <UILanguage>en-US</UILanguage>
      <UserLocale>en-US</UserLocale>
    </component>
    <component name="Microsoft-Windows-Setup" processorArchitecture="amd64"
        publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS"
        xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <RunSynchronous>
        <RunSynchronousCommand wcm:action="add">
          <Order>1</Order>
          <Path>cmd /c X:\\deploy.cmd</Path>
          <Description>Console Pi - trien khai he dieu hanh</Description>
        </RunSynchronousCommand>
      </RunSynchronous>
    </component>
  </settings>
</unattend>
"""


# =====================================================================
# TUY CHON WINDOWS SAU KHI CAI (mo hinh MDT: "Task Sequence" co san cac
# buoc thiet lap thay vi bat nguoi dung tu viet script)
#
# MOT NGUON SU THAT DUY NHAT: giao dien (ui/deployos.py buoc 6) doc
# chinh bang nay de ve o tich, va sinh_unattend_offline_xml() cung doc
# chinh bang nay de sinh lenh - khong the lech nhau.
#
# Moi muc: (ma, nhan hien thi, mo ta, pha, [cac lenh])
#   pha = "may"       -> chay o pass specialize, quyen SYSTEM, TRUOC khi
#                        co nguoi dang nhap (thiet lap cap may)
#   pha = "nguoi_dung"-> chay o FirstLogonCommands, trong phien cua
#                        nguoi dung dau tien (thiet lap cap nguoi dung,
#                        vi ghi vao HKCU)
# =====================================================================
TUY_CHON_WINDOWS = [
    ("rdp", "Bật Remote Desktop",
     "Cho phép nối từ xa qua RDP và mở sẵn cổng trên tường lửa", "may", [
         r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server"'
         r' /v fDenyTSConnections /t REG_DWORD /d 0 /f',
         'netsh advfirewall firewall set rule group="remote desktop"'
         ' new enable=Yes',
     ]),
    ("ping", "Cho phép ping tới máy này",
     "Mở ICMP vào - rất cần khi đi kiểm tra mạng", "may", [
         'netsh advfirewall firewall add rule name="ICMPv4 vao"'
         ' protocol=icmpv4:8,any dir=in action=allow',
     ]),
    ("khong_ngu", "Không tự động ngủ / tắt màn hình",
     "Đặt thời gian chờ về 0 khi cắm điện - hợp cho máy để bàn làm việc lâu", "may", [
         "powercfg /change standby-timeout-ac 0",
         "powercfg /change monitor-timeout-ac 0",
         "powercfg /change hibernate-timeout-ac 0",
     ]),
    ("tat_fast_startup", "Tắt Fast Startup",
     "Để lệnh Shut down tắt máy THẬT SỰ - tránh lỗi thiết bị cắm ngoài",
     "may", [
         r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Power"'
         r' /v HiberbootEnabled /t REG_DWORD /d 0 /f',
     ]),
    ("tat_uac", "Tắt UAC (hộp hỏi quyền)",
     "GIẢM AN TOÀN - chỉ dùng cho máy thử nghiệm / phòng lab", "may", [
         r'reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"'
         r' /v EnableLUA /t REG_DWORD /d 0 /f',
     ]),
    ("tat_telemetry", "Giảm thu thập dữ liệu (telemetry)",
     "Đặt mức thấp nhất mà bản Windows đó cho phép", "may", [
         r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection"'
         r' /v AllowTelemetry /t REG_DWORD /d 0 /f',
     ]),
    ("hien_duoi_file", "Hiện phần mở rộng tập tin",
     "Thấy .exe .bat .pdf... thay vì giấu đi", "nguoi_dung", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"'
         r' /v HideFileExt /t REG_DWORD /d 0 /f',
     ]),
    ("hien_file_an", "Hiện tập tin ẩn",
     "Hiện cả file/thư mục bị đánh dấu ẩn", "nguoi_dung", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"'
         r' /v Hidden /t REG_DWORD /d 1 /f',
     ]),

    # ---- Bo sung dot 2 (tham khao schneegans.de/windows/unattend-generator)
    # Chi lay nhung muc THUC SU huu ich cho may cai tai hien truong, bo qua
    # cac muc trang tri (mau sac, hinh nen, hieu ung) va cac muc nguy hiem
    # (tat hoan toan Defender, tat SmartScreen o muc he thong).

    ("tat_bitlocker", "Không tự mã hoá ổ đĩa (BitLocker)",
     "RẤT NÊN BẬT khi cài máy cho người khác: Windows 11 tự bật mã hoá ổ và "
     "gắn khoá vào tài khoản Microsoft - máy hỏng mà không có khoá là mất "
     "sạch dữ liệu, cứu cũng không được", "may", [
         r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\BitLocker"'
         r' /v PreventDeviceEncryption /t REG_DWORD /d 1 /f',
     ]),
    ("tat_windows_update", "Tắt Windows Update tự động",
     "Máy không tự tải bản cập nhật và tự khởi động lại giữa giờ làm. "
     "Đổi lại phải tự cập nhật định kỳ, nếu không sẽ thiếu vá lỗi bảo mật",
     "may", [
         r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"'
         r' /v NoAutoUpdate /t REG_DWORD /d 1 /f',
     ]),
    ("bat_duong_dan_dai", "Cho phép đường dẫn dài hơn 260 ký tự",
     "Hết lỗi copy báo \"tên file quá dài\" khi thư mục lồng nhau nhiều tầng",
     "may", [
         r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem"'
         r' /v LongPathsEnabled /t REG_DWORD /d 1 /f',
     ]),
    ("tat_system_restore", "Tắt System Restore",
     "Không giữ điểm khôi phục - tiết kiệm vài GB ổ đĩa. Chỉ nên dùng cho "
     "máy đã có cách sao lưu khác", "may", [
         'powershell -NoProfile -ExecutionPolicy Bypass -Command '
         '"Disable-ComputerRestore -Drive C:\\"',
     ]),
    ("hieu_suat_cao", "Đặt nguồn điện ở mức Hiệu suất cao",
     "CPU không hạ xung để tiết kiệm điện - máy phản hồi nhanh hơn, tốn "
     "điện hơn. Hợp cho máy bàn cắm điện liên tục", "may", [
         "powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
     ]),
    ("tat_bing_start", "Tắt tìm kiếm Bing trong menu Start",
     "Gõ tìm chương trình thì chỉ tìm trong máy, không lẫn kết quả web",
     "nguoi_dung", [
         r'reg add "HKCU\Software\Policies\Microsoft\Windows\Explorer"'
         r' /v DisableSearchBoxSuggestions /t REG_DWORD /d 1 /f',
     ]),
    ("mo_this_pc", "Mở Explorer vào This PC thay vì Quick Access",
     "Bấm vào Explorer là thấy ngay danh sách ổ đĩa", "nguoi_dung", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"'
         r' /v LaunchTo /t REG_DWORD /d 1 /f',
     ]),
    ("menu_chuot_cu", "Menu chuột phải kiểu cũ (Windows 11)",
     "Bỏ menu rút gọn của Windows 11, hiện thẳng menu đầy đủ như Windows 10 - "
     "không phải bấm thêm \"Show more options\". Không ảnh hưởng Windows 10",
     "nguoi_dung", [
         r'reg add "HKCU\Software\Classes\CLSID'
         r'\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}'
         r'\InprocServer32" /f /ve',
     ]),
    ("taskbar_trai", "Thanh tác vụ căn trái (Windows 11)",
     "Nút Start về góc trái như Windows 10. Không ảnh hưởng Windows 10",
     "nguoi_dung", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"'
         r' /v TaskbarAl /t REG_DWORD /d 0 /f',
     ]),
    ("tat_widgets", "Tắt Widgets / bảng tin thời tiết",
     "Bỏ ô thời tiết - tin tức trên thanh tác vụ", "nguoi_dung", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"'
         r' /v TaskbarDa /t REG_DWORD /d 0 /f',
     ]),
    ("tat_goi_y_app", "Tắt gợi ý ứng dụng và quảng cáo",
     "Windows không tự cài app gợi ý, không hiện quảng cáo trong Start và "
     "màn hình khoá", "nguoi_dung", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion'
         r'\ContentDeliveryManager" /v SilentInstalledAppsEnabled'
         r' /t REG_DWORD /d 0 /f',
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion'
         r'\ContentDeliveryManager" /v SubscribedContent-338388Enabled'
         r' /t REG_DWORD /d 0 /f',
     ]),

    # ---- Bo sung dot 3
    ("hien_icon_desktop", "Hiện This PC và Network ngoài desktop",
     "Bỏ desktop trống trơn - có sẵn biểu tượng máy tính và mạng để bấm vào",
     "nguoi_dung", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer'
         r'\HideDesktopIcons\NewStartPanel"'
         r' /v {20D04FE0-3AEA-1069-A2D8-08002B30309D} /t REG_DWORD /d 0 /f',
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer'
         r'\HideDesktopIcons\NewStartPanel"'
         r' /v {F02C1A0D-BE21-4350-88B0-7367FC96EF3C} /t REG_DWORD /d 0 /f',
     ]),
    ("uu_tien_hieu_nang", "Ưu tiên hiệu năng thay vì giao diện đẹp",
     "Tắt hiệu ứng mờ, đổ bóng, cửa sổ bay - máy cũ / máy yếu chạy mượt hơn "
     "rõ rệt", "nguoi_dung", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer'
         r'\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 2 /f',
     ]),
    ("tat_tu_khoi_dong_lai", "Không tự khởi động lại khi có người đang dùng",
     "Windows Update không được tự khởi động lại máy khi còn người đăng "
     "nhập - tránh mất việc đang làm dở", "may", [
         r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"'
         r' /v NoAutoRebootWithLoggedOnUsers /t REG_DWORD /d 1 /f',
     ]),
    ("bat_net_framework35", "Bật .NET Framework 3.5",
     "Nhiều phần mềm kế toán, phần mềm quản lý cũ bắt buộc phải có. "
     "CHỈ bật được nếu máy có sẵn bộ nguồn ở C:\\ConsolePi\\sxs "
     "(tải thư mục sources\\sxs của đĩa Windows lên mục Ứng dụng, đặt tên "
     "\"sxs\"). Không có nguồn thì bước này báo lỗi rồi đi tiếp, không "
     "làm dừng quá trình cài", "may", [
         # BAT BUOC co /limitaccess - DAY LA CHO DA GAY LOI THAT.
         #
         # LOI THAT DA GAP (12/09/2026, anh Thoai chup man hinh): lenh nay
         # luc dau viet KHONG co /limitaccess. Khi do neu may khong co
         # nguon cai san, DISM tu dong di hoi Windows Update qua mang de
         # tai goi ve. Mang hien truong cham/chap chon -> DISM dung im o
         # "Enabling feature(s) 5.9%" HANG GIO (CPU 2%, dia 0%, mang 0
         # Kbps - khong lam gi ca). Vi lenh nay chay o pha specialize
         # (RunSynchronousCommand chay DONG BO) nen ca qua trinh cai
         # Windows treo cung luon o man hinh "Getting ready".
         #
         # /limitaccess = CAM DISM ra Windows Update. Khong co nguon thi
         # no bao loi 0x800f081f trong vai giay roi thoi - Windows di tiep
         # binh thuong. Tha bao loi nhanh con hon treo im lang.
         "dism /online /enable-feature /featurename:NetFx3 /all /norestart"
         " /limitaccess /source:C:\\ConsolePi\\ungdung\\sxs",
     ]),
    ("tat_ipv6", "Tắt IPv6 trên mọi card mạng",
     "CHỈ dùng khi hệ thống mạng của anh chưa chạy IPv6 và IPv6 gây chậm "
     "phân giải tên. Mạng có IPv6 thật thì đừng bật mục này", "may", [
         r'reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters"'
         r' /v DisabledComponents /t REG_DWORD /d 255 /f',
     ]),
    ("bat_admin_shares", "Mở chia sẻ quản trị qua mạng (C$, ADMIN$)",
     "Cho phép vào ổ đĩa máy này từ xa bằng \\\\tên-máy\\c$ - tiện khi đi "
     "hỗ trợ từ xa. GIẢM AN TOÀN nếu máy nằm ở mạng không tin cậy", "may", [
         r'reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies'
         r'\System" /v LocalAccountTokenFilterPolicy /t REG_DWORD /d 1 /f',
     ]),
    ("tat_man_hinh_khoa", "Bỏ màn hình khoá, vào thẳng ô đăng nhập",
     "Không phải bấm/vuốt một lần thừa trước khi nhập mật khẩu", "may", [
         r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Personalization"'
         r' /v NoLockScreen /t REG_DWORD /d 1 /f',
     ]),
    ("tat_cortana", "Tắt Cortana",
     "Tắt trợ lý ảo - đỡ tốn tài nguyên và không gửi nội dung tìm kiếm ra "
     "ngoài", "may", [
         r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search"'
         r' /v AllowCortana /t REG_DWORD /d 0 /f',
     ]),
    ("ps_chay_script", "Cho phép chạy script PowerShell",
     "Đặt ExecutionPolicy về RemoteSigned - chạy được script .ps1 tự viết "
     "mà không phải gõ lệnh mở khoá mỗi lần", "may", [
         "powershell -NoProfile -Command "
         "\"Set-ExecutionPolicy RemoteSigned -Scope LocalMachine -Force\"",
     ]),
]


def _khoi_gia_nhap_domain(d):
    """
    Component Microsoft-Windows-UnattendedJoin (pass specialize) - TINH
    NANG CHINH THUC cua Windows de tu gia nhap domain, dung dung co che
    MDT dung. Rong neu khong khai bao domain.

    Tai khoan dung de gia nhap PHAI co quyen them may vao domain (thuong
    la 1 tai khoan rieng cho viec nay, khong nhat thiet la Domain Admin).
    """
    domain = (d.get("domain") or "").strip()
    if not domain:
        return ""
    ou = (d.get("domain_ou") or "").strip()
    khoi_ou = f"\n        <MachineObjectOU>{_esc(ou)}</MachineObjectOU>" if ou else ""
    return f"""
    <component name="Microsoft-Windows-UnattendedJoin" processorArchitecture="amd64"
        publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS"
        xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <Identification>
        <Credentials>
          <Domain>{_esc(domain)}</Domain>
          <Username>{_esc(d.get('domain_user') or '')}</Username>
          <Password>{_esc(d.get('domain_pass') or '')}</Password>
        </Credentials>
        <JoinDomain>{_esc(domain)}</JoinDomain>{khoi_ou}
      </Identification>
    </component>"""


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


def _lenh_app_theo_dich(d, dich):
    """Lenh cai cac phan mem da chon co dung dich (may / nguoi_dung)."""
    return [_lenh_cai_app(a) for a in _d.chuan_hoa_apps(d.get("apps"))
            if a["dich"] == dich]


THU_MUC_UNGDUNG_TREN_MAY = f"{THU_MUC_TREN_MAY}\\ungdung"


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


def _lenh_ungdung_theo_dich(d, dich):
    """Lenh cai cac ung dung (thu muc) da chon co dung dich (may/nguoi_dung).
    Bo qua am tham ung dung nao chua dat lenh cai - da canh bao ngay tren
    giao dien buoc 5, khong lam vo ca chuoi trien khai vi 1 muc thieu."""
    ra = []
    for u in _d.chuan_hoa_ungdung(d.get("ungdung")):
        if u["dich"] != dich:
            continue
        lenh = _lenh_cai_ungdung(u)
        if lenh:
            ra.append(lenh)
    return ra


def _lenh_script(d):
    """Lenh chay cac script da chon (luon chay o phien nguoi dung dau)."""
    return [f'"{THU_MUC_TREN_MAY}\\scripts\\{ten}"'
            for ten in (d.get("scripts") or [])]


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
    if not (d.get("bat_admin") and d.get("mk_admin")):
        return []
    return ["powershell -NoProfile -ExecutionPolicy Bypass -Command "
            "\"Get-LocalUser | Where-Object { $_.SID.Value -like '*-500' } "
            "| Enable-LocalUser\""]


def _khoi_runsync_specialize(d):
    """
    Component Microsoft-Windows-Deployment chay cac lenh cap MAY:
    tuy chon Windows + cai cac phan mem chon "cai cho May" (chay voi
    quyen he thong, TRUOC khi co ai dang nhap).
    """
    lenh = (_lenh_bat_administrator(d)
            + _lenh_theo_pha(d, "may") + _lenh_app_theo_dich(d, "may")
            + _lenh_ungdung_theo_dich(d, "may"))
    if not lenh:
        return ""
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


def _khoi_firstlogon(d):
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
    lenh = ["powershell -NoProfile -ExecutionPolicy Bypass -File "
            f"{THU_MUC_TREN_MAY}\\tien-trinh.ps1"]

    # BAO CAO TONG KET - LUON LUON la lenh CUOI CUNG, khong phai tuy chon,
    # khong phu thuoc kich ban / he dieu hanh / phan mem da chon.
    #
    # Vi sao cho vao day thay vi de anh Thoai tu them vao o "Lenh them":
    # thu gi phai nho lam bang tay thi som muon cung co lan quen, dung
    # luc can doi chieu nhat lai khong co. Day la bao cao cuoi cung cua
    # ca qua trinh cai - phai co mat vo dieu kien.
    #
    # Hien bang cua so do hoa va DUNG YEN cho toi khi bam Dong: cua so
    # cmd cua FirstLogonCommands tu dong dong ngay khi chay xong, khong
    # ai kip doc (anh Thoai da gap dung viec nay).
    lenh.append("powershell -NoProfile -ExecutionPolicy Bypass -File "
                f"{THU_MUC_TREN_MAY}\\bao-cao.ps1")

    if not lenh:
        return ""
    muc = "".join(f"""
        <SynchronousCommand wcm:action="add">
          <Order>{i}</Order>
          <CommandLine>cmd /c {_esc(c)}</CommandLine>
        </SynchronousCommand>""" for i, c in enumerate(lenh, start=1))
    return f"""
      <FirstLogonCommands>{muc}
      </FirstLogonCommands>"""


def sinh_unattend_offline_xml(d):
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
    username = d.get("username") or "admin"
    password = d.get("password") or ""
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
    if d.get("bat_admin") and d.get("mk_admin"):
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
      <UserAccounts>
        <LocalAccounts>
          <LocalAccount wcm:action="add">
            <Name>{_esc(username)}</Name>
            <Group>Administrators</Group>
            <Password>
              <Value>{_esc(password)}</Value>
              <PlainText>true</PlainText>
            </Password>
          </LocalAccount>
        </LocalAccounts>{khoi_mk_admin}
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
      </OOBE>{_khoi_firstlogon(d)}
      <TimeZone>{_esc(tz_windows)}</TimeZone>
    </component>
  </settings>
</unattend>
"""


TEN_AUTOUNATTEND = "autounattend.xml"
TEN_FLOPPY = "autounattend.img"
DUNG_LUONG_FLOPPY_KB = 1440


def tao_dia_mem_ao(noi_dung_xml, duong_dia):
    """
    Dong goi autounattend.xml vao 1 anh dia mem ao FAT12 1.44MB that su
    (dung mtools: mformat + mcopy), KHONG dung wimlib, KHONG dung boot.wim.

    LICH SU CAC CACH DA THU (khong doan, da kiem chung that qua nhieu vong
    boot may ao that):
    1. Nhung XML vao BEN TRONG boot.wim (`wimlib-imagex update`, hoac mount
       FUSE + commit) - lam boot.wim MAT KHA NANG BOOT (loi firmware
       "0xc000000f"), du noi dung XML don gian toi dau. boot.wim GOC
       (khong qua wimlib sua gi) luon boot binh thuong - da doi chieu
       truc tiep. KET LUAN: khong dung wimlib de sua boot.wim nua.
    2. Nap autounattend.xml nhu 1 FILE RIENG (khong nen trong dia mem) qua
       1 dong `initrd` phu cua wimboot - file NAY CO toi noi that su qua
       mang (xac nhan qua log HTTP that: 200, dung kich thuoc), nhung
       Windows Setup VAN KHONG tu ap dung (van dung o man hinh "Language
       to install"). Wimboot phoi file nay ra nhu 1 file DOC o goc o dia
       X: (chinh o dia WinPE dang chay) - nhung Setup chi tu quet
       autounattend.xml o cac O DIA RIENG (USB/dia mem/DVD gan vao may),
       KHONG quet chinh o dia X: no dang chay tren do (hop ly theo thiet
       ke cua Microsoft, khong phai loi).
    3. (Ham nay) Dong autounattend.xml vao 1 ANH DIA MEM AO that (FAT12)
       - muc tieu la de no duoc trinh dien nhu 1 O DIA RIENG thuc su
       (không phai file roi tren X:) de roi vao dung nhanh quet cua Setup.
       DA KIEM CHUNG THAT (boot that qua VM, autounattend.img toi noi day
       du qua HTTP - xac nhan qua log nginx: 200, dung 1474560 byte) -
       KET QUA: VAN KHONG duoc Setup nhan dien (van dung man hinh
       "Language to install" y het cach 2). Ket luan: wimboot KHONG gan
       file .img thanh 1 o dia rieng duoc BIOS/UEFI/Setup nhan dien - no
       chi phoi ra nhu 1 file thuong tren X: giong het moi file khac,
       khong co "gia lap dia mem" thuc su. Ca 3 cach (nhung vao boot.wim,
       file roi, dia mem ao) DEU KHONG dung duoc theo huong nay.

       DA KIEM TRA (khong doan): startnet.cmd trong CA 2 image (1 va 2)
       CHI co `wpeinit` - khong phai noi goi setup.exe (co che that nam o
       dau khac, nhieu kha nang la registry hive SYSTEM nhung san, kho sua
       an toan bang van ban thuong).

       DA THU dung chinh dism.exe co san trong X:/sources (WinPE dang
       chay) de mount boot.wim qua Samba (//<ip>/deploy) va copy
       autounattend.xml vao bang DISM that (khong phai wimlib) - day la
       cong cu CHINH CHU cua Microsoft, tranh duoc loi wimlib da gap. Bi
       CHAN boi 1 gioi han moi, khac hoan toan: phim Shift KHONG hoat dong
       qua duong ket noi console tu xa (browser -> ESXi HTML5 console) -
       da kiem chung that (`shift+a` cho ra "a" thuong, khong phai "A";
       ky tu ":" luon thanh ";" du dung `type` hay `key`). Khong lien quan
       gi den DISM/wimlib/boot.wim - la gioi han cua chinh duong truyen
       ban phim ao. KHONG the go duoc lenh DISM (can `/Flag:value` va ky
       tu hoa) qua duong nay. Neu co nguoi ngoi truc tiep tai ban phim that
       cua may (khong qua console tu xa), huong DISM nay RAT co trien
       vong (dung dung DISM chinh chu, khong con gioi han cua wimlib nua).
    """
    tam_xml = duong_dia + ".xml.tmp"
    try:
        with open(tam_xml, "w", encoding="utf-8") as f:
            f.write(noi_dung_xml)
        try:
            os.remove(duong_dia)
        except OSError:
            pass
        ok, out = _sh(["mformat", "-C", "-f", str(DUNG_LUONG_FLOPPY_KB),
                       "-i", duong_dia, "::"], timeout=20)
        if not ok:
            return False, f"Khong tao duoc anh dia mem (mformat): {out[-300:]}"
        ok, out = _sh(["mcopy", "-i", duong_dia, tam_xml,
                       "::AUTOUNATTEND.XML"], timeout=20)
        if not ok:
            return False, f"Khong chep duoc XML vao dia mem (mcopy): {out[-300:]}"
        return True, f"Da tao anh dia mem ao {os.path.basename(duong_dia)}."
    finally:
        try:
            os.remove(tam_xml)
        except OSError:
            pass


def chuan_bi_autounattend(d, dia_chi_pi="192.168.98.1"):
    """
    Sinh XML, ghi THANH 1 FILE RIENG (autounattend.xml) va DONG THEM 1 anh
    dia mem ao (autounattend.img) trong BOOT_DIR - hoan toan KHONG dung
    den boot.wim (xem ly do that trong docstring cua tao_dia_mem_ao()).
    ui/pxe.py se nap CA HAI qua wimboot bang initrd rieng - dang thu
    nghiem xem cach nao (file roi hay dia mem ao) duoc Windows Setup nhan
    dien, chua ket luan chac chan.
    """
    xml_noi_dung = sinh_autounattend_xml(d, dia_chi_pi)
    duong_xml = os.path.join(_d.BOOT_DIR, TEN_AUTOUNATTEND)
    try:
        with open(duong_xml, "w", encoding="utf-8") as f:
            f.write(xml_noi_dung)
    except OSError as e:
        return False, f"Khong ghi duoc {TEN_AUTOUNATTEND}: {e}"

    duong_floppy = os.path.join(_d.BOOT_DIR, TEN_FLOPPY)
    ok, msg = tao_dia_mem_ao(xml_noi_dung, duong_floppy)
    if not ok:
        return False, msg
    return True, f"Da ghi {TEN_AUTOUNATTEND} va {TEN_FLOPPY}."


def co_san_autounattend():
    return os.path.isfile(os.path.join(_d.BOOT_DIR, TEN_AUTOUNATTEND))


def co_san_dia_mem_autounattend():
    return os.path.isfile(os.path.join(_d.BOOT_DIR, TEN_FLOPPY))


TEN_ISO_TU_DONG = "windows-autounattend.iso"


def co_san_iso_tu_dong():
    """True neu da dung xong ISO tu dong (xem dung_iso_tu_dong)."""
    return os.path.isfile(os.path.join(_d.BOOT_DIR, TEN_ISO_TU_DONG))


# Cac file boot BIOS+UEFI can de dung 1 ISO Windows that boot duoc, TAT CA
# da co san BEN TRONG chinh boot.wim (image 2 "Microsoft Windows Setup")
# - khong can tai ISO goc tu Microsoft. (duong trong wim, duong dich
# tuong doi tren ISO). Da kiem chung that qua `wimlib-imagex dir`.
_CAC_FILE_BOOT_ISO = [
    (r"\Windows\Boot\PCAT\bootmgr", "bootmgr"),
    (r"\Windows\Boot\DVD\PCAT\etfsboot.com", "boot/etfsboot.com"),
    (r"\Windows\Boot\DVD\PCAT\BCD", "boot/BCD"),
    (r"\Windows\Boot\DVD\PCAT\boot.sdi", "boot/boot.sdi"),
    (r"\Windows\Boot\EFI\bootmgfw.efi", "efi/boot/bootx64.efi"),
    (r"\Windows\Boot\DVD\EFI\BCD", "efi/microsoft/boot/BCD"),
    (r"\Windows\Boot\DVD\EFI\boot.sdi", "efi/microsoft/boot/boot.sdi"),
    (r"\Windows\Boot\DVD\EFI\en-US\efisys_noprompt.bin",
     "efi/microsoft/boot/efisys_noprompt.bin"),
    (r"\setup.exe", "setup.exe"),
]

_GIOI_HAN_ISO9660 = 4 * 1024 * 1024 * 1024 - 1  # 4GB - 1, gioi han 1 file


def dung_iso_tu_dong(d, dia_chi_pi="192.168.98.1"):
    """
    Dung 1 ISO Windows co the boot that (BIOS+UEFI, dung `sanboot` cua
    iPXE - xem ly do that trong ui/pxe.py) hoan toan bang cong cu Linux
    tren chinh Console Pi - KHONG can Windows/ADK, KHONG sua boot.wim.

    Cac file boot (bootmgr, etfsboot.com, efisys_noprompt.bin, BCD,
    bootmgfw.efi, setup.exe) duoc trich THANG tu chinh boot.wim GOC (an
    toan tuyet doi, khong dung wimlib de GHI lai boot.wim - chi doc/trich
    xuat). autounattend.xml dat o GOC ISO - day la vi tri Windows Setup
    THAT SU quet khi boot tu 1 o dia rieng that (khong phai o dia ao rieng
    cua wimboot ma Setup khong nhin thay).

    install.wim (~4.4GB) vuot gioi han 1 file cua ISO9660 chuan (4GB) -
    chi dua vao qua UDF, giong cach cac ISO Windows that lam.
    """
    try:
        import pycdlib
    except ImportError:
        return False, ("Chua co pycdlib - chay: sudo apt-get install "
                        "python3-pycdlib")

    goc_wim = os.path.join(_d.BOOT_DIR, "boot.wim")
    duong_install = os.path.join(_d.BOOT_DIR, "install.wim")
    if not os.path.isfile(goc_wim):
        return False, "Chua co boot.wim."
    if not os.path.isfile(duong_install):
        return False, "Chua co install.wim."

    import shutil
    import tempfile
    tam = tempfile.mkdtemp(prefix="iso-src-", dir=_d.BOOT_DIR)
    try:
        for duong_wim, duong_dich in _CAC_FILE_BOOT_ISO:
            dich_day_du = os.path.join(tam, duong_dich)
            os.makedirs(os.path.dirname(dich_day_du), exist_ok=True)
            ok, out = _sh(["wimlib-imagex", "extract", goc_wim, "2",
                           duong_wim, f"--dest-dir={os.path.dirname(dich_day_du)}"],
                          timeout=60)
            if not ok:
                return False, f"Không trích xuất được {duong_wim}: {out[-300:]}"
            # os.path.basename tren Linux KHONG hieu dau \ cua duong dan
            # Windows (chi hieu /) - phai tu tach thu cong.
            ten_goc = duong_wim.rsplit("\\", 1)[-1]
            trich_ra = os.path.join(os.path.dirname(dich_day_du), ten_goc)
            if trich_ra != dich_day_du and os.path.isfile(trich_ra):
                os.replace(trich_ra, dich_day_du)

        xml_noi_dung = sinh_autounattend_xml(d, dia_chi_pi)
        with open(os.path.join(tam, "autounattend.xml"), "w",
                  encoding="utf-8") as f:
            f.write(xml_noi_dung)

        os.makedirs(os.path.join(tam, "sources"), exist_ok=True)
        os.symlink(goc_wim, os.path.join(tam, "sources", "boot.wim"))
        os.symlink(duong_install, os.path.join(tam, "sources", "install.wim"))

        iso = pycdlib.PyCdlib()
        iso.new(interchange_level=3, vol_ident="CONSOLEPI_WIN",
                joliet=3, udf="2.60")

        thu_muc_can = ["boot", "efi", "efi/boot", "efi/microsoft",
                       "efi/microsoft/boot", "sources"]
        cong_don = ""
        for ten_dir in thu_muc_can:
            cong_don = ten_dir
            duong_tren_dia = "/" + ten_dir
            iso.add_directory(iso_path=f"/{ten_dir.upper()}",
                               joliet_path=duong_tren_dia,
                               udf_path=duong_tren_dia)

        for goc, _dirs, files in os.walk(tam):
            for ten in files:
                duong_that = os.path.join(goc, ten)
                duong_tuong_doi = os.path.relpath(duong_that, tam).replace(
                    os.sep, "/")
                kich_thuoc = os.path.getsize(duong_that)
                chi_udf = kich_thuoc > _GIOI_HAN_ISO9660
                iso_path = (None if chi_udf
                            else f"/{duong_tuong_doi.upper()};1")
                joliet_path = None if chi_udf else f"/{duong_tuong_doi}"
                iso.add_file(duong_that, iso_path=iso_path,
                             joliet_path=joliet_path,
                             udf_path=f"/{duong_tuong_doi}")

        iso.add_eltorito(
            "/BOOT/ETFSBOOT.COM;1", bootcatfile="/BOOT.CAT;1",
            joliet_bootcatfile="/boot.cat", udf_bootcatfile="/boot.cat",
            platform_id=0, media_name="noemul", boot_load_size=4)
        # LOI THAT DA GAP (anh Thoai kiem chung that qua sanboot va tra
        # ma loi iPXE 0x7f22208e tai ipxe.org/7f22208e): ban dau tro
        # entry El Torito UEFI THANG vao bootx64.efi - SAI. Firmware UEFI
        # khi boot tu quang dia (El Torito) mount ANH FAT nho
        # (efisys_noprompt.bin) nhu 1 o dia rieng va tim
        # \EFI\BOOT\BOOTX64.EFI BEN TRONG anh FAT do - khong doc truc
        # tiep tu cay ISO9660/UDF. Phai tro vao chinh efisys_noprompt.bin
        # (giong dung cach Microsoft tu lam voi ISO that), khong phai
        # bootx64.efi.
        iso.add_eltorito("/EFI/MICROSOFT/BOOT/EFISYS_NOPROMPT.BIN;1",
                          platform_id=0xef, efi=True, media_name="noemul")

        duong_iso = os.path.join(_d.BOOT_DIR, TEN_ISO_TU_DONG)
        duong_iso_tam = duong_iso + ".dang-dung"
        iso.write(duong_iso_tam)
        iso.close()
        os.replace(duong_iso_tam, duong_iso)
        return True, f"Da dung {TEN_ISO_TU_DONG} ({os.path.getsize(duong_iso):,} bytes)."
    except Exception as e:
        return False, f"Loi khi dung ISO: {e}"
    finally:
        shutil.rmtree(tam, ignore_errors=True)


TEN_DIA_GPT_TU_DONG = "windows-autounattend.img"


def co_san_dia_gpt_tu_dong():
    """True neu da dung xong anh dia GPT+FAT32 (xem dung_dia_gpt_tu_dong)."""
    return os.path.isfile(os.path.join(_d.BOOT_DIR, TEN_DIA_GPT_TU_DONG))


TEN_DAU_KICHBAN = TEN_DIA_GPT_TU_DONG + ".json"


def _ghi_dau_kichban(d):
    """
    Ghi lai CHINH XAC kich ban nao da dung nen anh dia dang phuc vu.

    LY DO THAT (loi that da xay ra, tra gia bang 1 lan cai lai may): anh
    dia la MOT file duy nhat dung chung (windows-autounattend.img) - ai
    dung lai sau se de len nguoi truoc ma khong de lai dau vet gi. Da co
    lan anh Thoai bam "Bat PXE" tu kich ban cua anh (dung mat khau cua
    anh), sau do 1 lan dung anh dia de kiem thu (mat khau test khac) da
    ghi de len - may cai xong thi mat khau khong phai cua anh, va KHONG
    CO CACH NAO nhin ra dieu do tu giao dien. Tu gio moi lan dung anh
    dia deu ghi kem file dau nay de man hinh Deployment OS noi ro dang
    phuc vu kich ban nao (xem deployos.kichban_dang_phuc_vu()).
    """
    import json
    import datetime
    dau = {
        "ten_kichban": d.get("tu_kichban") or "",
        "os_id": d.get("os_id") or "",
        "ten_may": d.get("ten_may") or "",
        "username": d.get("username") or "",
        "kieu_boot": d.get("kieu_boot") or "",
        "dung_luc": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        with open(os.path.join(_d.BOOT_DIR, TEN_DAU_KICHBAN), "w",
                  encoding="utf-8") as f:
            json.dump(dau, f, ensure_ascii=False, indent=1)
    except OSError:
        pass  # khong ghi duoc dau thi van coi nhu dung anh dia thanh cong


def doc_dau_kichban():
    """Dict mo ta kich ban da dung nen anh dia hien tai, None neu khong co."""
    import json
    try:
        with open(os.path.join(_d.BOOT_DIR, TEN_DAU_KICHBAN),
                  encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def dung_dia_gpt_tu_dong(d, dia_chi_pi="192.168.98.1"):
    """
    Dung 1 ANH DIA GPT + 1 phan vung FAT32 (kieu USB cai Windows that,
    KHONG phai ISO9660) - thay the hoan toan cho dung_iso_tu_dong().

    LOI THAT DA GAP (anh Thoai kiem chung that qua sanboot, tra ve 2 ma
    loi iPXE khac nhau 0x7f22208e roi 0x7f222091, da tra cuu tai
    ipxe.org): sau khi sua dung entry El Torito UEFI (tro efisys_noprompt.bin
    thay vi bootx64.efi), VAN loi - vi day la 1 LOI THAT DA BIET cua chinh
    iPXE (mailing list ipxe-devel, thang 12/2016, "Bug in UEFI Sanboot with
    iso9660"): code `efi_block.c` cua iPXE tu dong nhan dien chu ky ISO9660
    tren dia va ap dat sai `blksize_shift`, khien no doc sai du lieu FAT
    nam trong anh El Torito - xay ra VOI BAT KY dia nao vua co ISO9660 vua
    co cau truc UEFI phuc tap (dung y het truong hop cua minh). Fix that
    su can sua lai chinh ma nguon C cua iPXE (bien dich lai iPXE tu dau -
    ngoai pham vi hop ly cua Console Pi).

    SUA DUNG: bo ISO9660 hoan toan, dung dinh dang GPT+FAT32 (kieu USB cai
    Windows that) - KHONG co chu ky ISO9660 nao ca nen khong bao gio cham
    vao doan code loi do cua iPXE.

    GIOI HAN THAT cua FAT32 (da kiem chung, khong doan): 1 file khong duoc
    vuot 4GB (truong kich thuoc 32-bit) - install.wim (~4.4GB) VUOT gioi
    han nay. Giai phap CHINH THUC cua Microsoft (khop voi cach lam USB cai
    Windows that su khi install.wim qua lon): `wimlib-imagex split` chia
    thanh install.swm + install2.swm (< 4GB moi phan), autounattend.xml
    tro InstallFrom/Path toi install.swm - Windows Setup TU tim cac phan
    tiep theo (install2.swm...) theo dung quy uoc dat ten, khong can khai
    bao gi them.

    KHONG dung NTFS (co the chua ca install.wim khong can chia) vi
    firmware UEFI dùng chung (nhu cua VMware/QEMU, dua tren EDK2) KHONG co
    san driver doc NTFS - day la ly do cong cu Rufus phai tu nhung 1
    driver UEFI:NTFS rieng. FAT32 la dinh dang UEFI DOC DUOC SAN, an toan
    nhat.

    Can chay voi quyen root (losetup/mount/mkfs.vfat) - dashboard da chay
    duoi quyen root nen khong can sudo rieng trong subprocess.

    QUAN TRONG - PHAT HIEN THAT lam DON GIAN HOA lon (kiem chung that qua
    `diskpart list disk` + `wmic diskdrive` NGAY TRONG WinPE dang chay tu
    dia nay): ket noi SAN cua sanboot CHI ton tai trong luc firmware dang
    boot (de nap boot.wim vao RAM) - MOT KHI WinPE da chay xong (X: la RAM
    disk, KHONG con lien quan gi den dia SAN nua) thi dia do BIEN MAT hoan
    toan, khong con thay duoc boi Windows/diskpart. Vi vay: KHONG con ly
    do gi de nhet install.wim/install.swm VAO dia nay nua - se KHONG THE
    nao doc lai duoc sau khi boot xong (kiem chung that: Windows Setup bao
    "specified file does not exist" khi tu no doc mot duong UNC bat ky
    tro ve dia nay sau khi WinPE da boot xong). install.wim VAN phai lay
    qua Samba (xem sinh_autounattend_xml: InstallFrom co <Credentials>,
    DriverPaths cung vay). Nho vay khong can wimlib-imagex split nua (tiet
    kiem rat nhieu thoi gian + dung luong dia tam).

    RIENG autounattend.xml thi KHAC: no duoc NHUNG THANG vao ben trong
    ban sao boot.wim cua chinh dia nay (xem doan wimlib-imagex update ben
    duoi) - vi no la 1 phan cua chinh anh WinPE dang chay (X:), KHONG phai
    thu Windows can "doc lai tu ben ngoai" sau khi boot, nen khong bi anh
    huong boi viec dia SAN bien mat. Windows Setup tu quet duoc no ngay
    tren X: - khong can lenh `setup.exe /unattend:` thu cong nua.
    """
    os_id = d.get("os_id", "")
    goc_wim = _d.duong_boot_wim(os_id)
    if not os.path.isfile(goc_wim):
        return False, f'Không tìm thấy boot.wim cho hệ điều hành "{os_id}".'

    import tempfile
    tam = tempfile.mkdtemp(prefix="gpt-src-", dir=_d.BOOT_DIR)
    duong_dia = os.path.join(_d.BOOT_DIR, TEN_DIA_GPT_TU_DONG)
    duong_mnt = None
    loop_dev = None
    try:
        # 1. Trich xuat cac file boot BIOS+UEFI tu chinh boot.wim cua os_id
        #    da chon (tai su dung danh sach _CAC_FILE_BOOT_ISO).
        for duong_wim, duong_dich in _CAC_FILE_BOOT_ISO:
            dich_day_du = os.path.join(tam, duong_dich)
            os.makedirs(os.path.dirname(dich_day_du), exist_ok=True)
            ok, out = _sh(["wimlib-imagex", "extract", goc_wim, "2",
                           duong_wim,
                           f"--dest-dir={os.path.dirname(dich_day_du)}"],
                          timeout=60)
            if not ok:
                return False, f"Không trích xuất được {duong_wim}: {out[-300:]}"
            ten_goc = duong_wim.rsplit("\\", 1)[-1]
            trich_ra = os.path.join(os.path.dirname(dich_day_du), ten_goc)
            if trich_ra != dich_day_du and os.path.isfile(trich_ra):
                os.replace(trich_ra, dich_day_du)

        import shutil
        os.makedirs(os.path.join(tam, "sources"), exist_ok=True)
        duong_boot_wim_tam = os.path.join(tam, "sources", "boot.wim")
        shutil.copyfile(goc_wim, duong_boot_wim_tam)
        os.chmod(duong_boot_wim_tam, 0o644)

        # 1b. THU that: nhet install.wim (tach nho .swm) NGAY TREN dia GPT
        #     nay, hy vong Setup doc duoc no y het luc doc boot.wim. KET
        #     QUA THAT (kiem chung bang `wmic logicaldisk get caption,
        #     volumename,filesystem` ngay trong WinPE dang chay): dia
        #     WININSTALL KHONG XUAT HIEN o bat ky o dia nao (C: la Windows
        #     cai lan truoc, D: rong, X: la RAM cua boot.wim) - CHUNG TO dia
        #     SAN da bien mat TU RAT SOM, som hon ca luc Setup xu ly
        #     ImageInstall. Vay khong con cach nao khac: install.wim BAT
        #     BUOC phai lay qua Samba (UNC), quay lai dung Credentials.
        #
        #     NHUNG loi THAT SU (kiem chung bang log Samba /var/log/samba/:
        #     HOAN TOAN khong co ket noi nao duoc ghi nhan trong MOI lan
        #     thu, ke ca lan RunSynchronousCommand da xac nhan mang len
        #     duoc that su qua netinit_log.txt) la: Windows Setup xu ly
        #     ImageInstall/InstallFrom SOM HON ca RunSynchronousCommand cua
        #     CHINH pass windowsPE (dat Order=1 cung khong giup - Setup
        #     KHONG dam bao chay RunSynchronousCommand truoc DiskConfig/
        #     ImageInstall, khac voi tai lieu Microsoft ngu y). Vi vay
        #     RunSynchronousCommand la SAI CHO cho viec nay.
        #
        #     SUA DUNG THAT SU (mo hinh MDT): WinPE luon uu tien chay
        #     winpeshl.ini (neu co) TRUOC khi lam bat ky viec gi khac luc
        #     khoi dong shell - da KIEM CHUNG THAT bang file log X:\diag.txt
        #     (thu tu chay dung 100%: bat_dau -> wpeinit_xong -> goi_setup).
        #     Nhung ngay ca khi mang DA len HAN truoc khi goi setup.exe,
        #     Setup VAN bao loi credentials va Samba VAN khong ghi nhan ket
        #     noi nao - ly do cuoi cung tim ra o setupact.log:
        #     ERROR_BAD_NETPATH tu chinh ruot setup.exe (khong sua duoc).
        #
        #     => BO HAN setup.exe. Dung winpeshl.ini de chay 1 SCRIPT
        #     TRIEN KHAI cua rieng minh (deploy.cmd), tu lam tung buoc
        #     bang diskpart + dism + bcdboot - dung y het cach MDT
        #     (LiteTouch) lam. Xem chi tiet trong sinh_deploy_cmd().
        goc_install = _d.duong_install_wim(os_id)
        if not os.path.isfile(goc_install):
            return False, f'Không tìm thấy install.wim cho hệ điều hành "{os_id}".'

        # 4 file nhung vao goc image 2 cua boot.wim (deu doc duoc tu X:\)
        #   autounattend.xml : Setup tu quet thay o goc X:, chi de GOI
        #                      deploy.cmd (xem sinh_autounattend_goi_script)
        #   deploy.cmd       : script trien khai kieu MDT (lam het moi viec)
        #   diskpart.txt     : script chia o dia cho deploy.cmd
        #   unattend.xml     : cau hinh cho Windows sau khi bung xong,
        #                      deploy.cmd chep vao W:\Windows\Panther
        # KHONG con nhung winpeshl.ini nua - de setup.exe chay binh thuong
        # (chinh no moi kich hoat duoc bo SMB client - xem ly do that trong
        # docstring cua sinh_autounattend_goi_script).
        cac_file_nhung = {
            "autounattend.xml": sinh_autounattend_goi_script(),
            "deploy.cmd": sinh_deploy_cmd(d, dia_chi_pi),
            "diskpart.txt": sinh_diskpart_txt(d),
            "unattend.xml": sinh_unattend_offline_xml(d),
            # Bao cao tong ket - LUON nhung, khong phai tuy chon. Nam
            # trong chinh anh boot nen co mat o MOI lan cai, khong phu
            # thuoc Samba hay viec anh Thoai co chon gi hay khong.
            "bao-cao.ps1": sinh_script_bao_cao(d),
            # Script dieu phoi cai dat + bao tien trinh ve Pi. Nhung vao
            # anh boot (khong qua Samba) de no co mat ke ca khi mang chap
            # chon - day la thu duy nhat biet dang cai toi dau.
            "tien-trinh.ps1": sinh_script_tien_trinh(d, dia_chi_pi),
        }
        lenh_update = []
        duong_tam_da_tao = []
        for ten, noi_dung in cac_file_nhung.items():
            duong = os.path.join(tam, f"_nhung_{ten}")
            # File .ps1 PHAI co BOM. Windows PowerShell 5.1 (ban co san
            # trong Windows 10/11) doc file .ps1 KHONG co BOM theo bang ma
            # ANSI cua he thong, nen moi chu tieng Viet co dau trong bao
            # cao se thanh ky tu rac. Co BOM thi no doc dung UTF-8.
            ma_hoa = "utf-8-sig" if ten.lower().endswith(".ps1") else "utf-8"
            with open(duong, "w", encoding=ma_hoa, newline="") as f:
                f.write(noi_dung)
            duong_tam_da_tao.append(duong)
            lenh_update.append(f"add {duong} /{ten}")

        # Driver CHO ANH BOOT: chep ca thu muc goi driver vao trong
        # boot.wim tai /ConsolePiDrivers/<id>/. deploy.cmd se `drvload`
        # chung NGAY TRUOC khi khoi tao mang - xem ly do that (do chinh
        # boot.wim thieu driver LAN Intel doi moi) trong docstring cua
        # deployos.dat_driver_cho_boot().
        for dr in _d.danh_sach_driver():
            if not dr.get("cho_boot"):
                continue
            thu_muc_dr = os.path.join(_d.DRIVERS_DIR, dr["id"])
            if os.path.isdir(thu_muc_dr):
                lenh_update.append(
                    f"add {thu_muc_dr} /ConsolePiDrivers/{dr['id']}")

        # LUU Y: wimlib-imagex chi nhan 1 tham so --command duy nhat (khong
        #     lap lai duoc) - phai gop nhieu lenh vao CHUNG 1 chuoi, moi
        #     lenh 1 dong (kiem chung that qua CLI, ERROR "--command may
        #     only be specified one time" khi truyen 2 lan rieng).
        ok, out = _sh(["wimlib-imagex", "update", duong_boot_wim_tam, "2",
                       "--command", "\n".join(lenh_update)],
                      timeout=120)
        for duong in duong_tam_da_tao:
            os.remove(duong)
        if not ok:
            return False, f"Không nhúng được script triển khai vào boot.wim: {out[-300:]}"

        # 2. Tinh dung luong can - cong tat ca file that su se nam tren
        #    dia, cong them 10% du phong cho cau truc FAT32 + GPT (dia
        #    nho hon nhieu lan so voi truoc vi khong con install.wim).
        tong_byte = sum(
            os.path.getsize(os.path.join(goc, f))
            for goc, _dirs, files in os.walk(tam) for f in files)
        dung_luong_mb = int(tong_byte / 1024 / 1024 * 1.05) + 16

        # 5. Tao anh dia GPT + 1 phan vung FAT32 (kieu ESP), format, gan
        #    qua loop device, chep file vao, thao ra.
        duong_dia_tam = duong_dia + ".dang-dung"
        ok, out = _sh(["truncate", "-s", f"{dung_luong_mb}M", duong_dia_tam],
                      timeout=30)
        if not ok:
            return False, f"Không tạo được file ảnh đĩa: {out[-300:]}"
        ok, out = _sh(["parted", "--script", duong_dia_tam,
                       "mklabel", "gpt",
                       "mkpart", "ESP", "fat32", "1MiB", "100%",
                       "set", "1", "esp", "on"], timeout=30)
        if not ok:
            return False, f"Không phân vùng được ảnh đĩa: {out[-300:]}"

        ok, out = _sh(["losetup", "--find", "--partscan", "--show",
                       duong_dia_tam], timeout=15)
        if not ok:
            return False, f"Không gắn được loop device: {out[-300:]}"
        loop_dev = out.strip().splitlines()[-1].strip()
        duong_phan_vung = f"{loop_dev}p1"

        ok, out = _sh(["mkfs.vfat", "-F", "32", "-n", "WININSTALL",
                       duong_phan_vung], timeout=60)
        if not ok:
            return False, f"Không định dạng FAT32 được: {out[-300:]}"

        duong_mnt = tempfile.mkdtemp(prefix="gpt-mnt-", dir=_d.BOOT_DIR)
        ok, out = _sh(["mount", duong_phan_vung, duong_mnt], timeout=15)
        if not ok:
            return False, f"Không mount được phân vùng: {out[-300:]}"

        ok, out = _sh(["cp", "-a", f"{tam}/.", duong_mnt], timeout=600)
        if not ok:
            return False, f"Không chép file vào ảnh đĩa được: {out[-300:]}"

        _sh(["sync"], timeout=30)
        _sh(["umount", duong_mnt], timeout=15)
        _sh(["losetup", "--detach", loop_dev], timeout=15)
        loop_dev = None

        os.replace(duong_dia_tam, duong_dia)
        _ghi_dau_kichban(d)
        return True, f"Đã dựng {TEN_DIA_GPT_TU_DONG} ({os.path.getsize(duong_dia):,} bytes)."
    except Exception as e:
        return False, f"Lỗi khi dựng ảnh đĩa GPT: {e}"
    finally:
        if loop_dev:
            if duong_mnt:
                _sh(["umount", duong_mnt], timeout=15)
            _sh(["losetup", "--detach", loop_dev], timeout=15)
        if duong_mnt:
            try:
                os.rmdir(duong_mnt)
            except OSError:
                pass
        shutil.rmtree(tam, ignore_errors=True)
        try:
            os.remove(duong_dia + ".dang-dung")
        except OSError:
            pass
