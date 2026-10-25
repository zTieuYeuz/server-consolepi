# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Unattend - autounattend.xml: dia Windows (chia o), sinh_autounattend_xml.

(B4: tach nguyen van tu unattend.py; ten ham/hang giu nguyen, nguon van re-export.)"""
from consolesystem.core.esc import esc_xml as _esc
from consolesystem.features.deploy_os.un_hangso import (_khoi_credentials_samba, _khoi_dia_windows, _khoi_driverpaths)  # noqa: F401


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
