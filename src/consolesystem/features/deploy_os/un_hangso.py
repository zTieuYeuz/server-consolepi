# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Unattend - hang so Samba va ham dung chung nho (mat khau kho, driverpaths, credentials).

(B4: tach nguyen van tu unattend.py; ten ham/hang giu nguyen, nguon van re-export.)"""
import subprocess
from ui.duongdan import FILE_KHOA_SAMBA as _FILE_KHOA_SAMBA
from consolesystem.core.esc import esc_xml as _esc



# Tai khoan Samba RIENG (user he thong "nologin", khong the dang nhap
# SSH/local - xem install.sh/README) chi de Windows Setup tu xac thuc khi
# no tu mo phien SMB rieng doc InstallFrom/Path - xem ly do that (guest
# bi Windows hien dai chan) trong sinh_autounattend_xml() ben duoi.
TEN_TAI_KHOAN_SAMBA = "consolepi-deploy"

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

# =====================================================================
# FILE NHUNG QUA WIMBOOT (1.5.0) - thay cho anh dia GPT+FAT32 + sanboot
# =====================================================================
# Anh dia GPT+FAT32 cu (1 file ~500 MB moi kich ban, dung ~1 phut) chi boot
# duoc tren UEFI TAT Secure Boot: may BIOS dung im o "Booting from SAN
# device 0x80" (440 byte ma boot MBR toan 0 - loi that anh Thoai 25/09/2026),
# may bat Secure Boot tu choi iPXE khong ky. Nay: iPXE ban KY chinh thuc +
# wimboot (Microsoft ky) nap boot.wim GOC (khong sua 1 byte) + cac file
# nhung duoi day. Chay duoc BIOS, UEFI, UEFI + Secure Boot (kiem chung that
# trong lab QEMU/OVMF khoa Microsoft - iso/test/wimboot-lab.sh).
#
# wimboot dat file chen vao X:\Windows\System32 (tai lieu wimboot). Setup
# KHONG tu quet autounattend.xml o do (da thu 2024: dung o "Language to
# install") -> chen them winpeshl.ini goi CHINH setup.exe kem
# /unattend:<duong dan ro>. Van la setup.exe chay (khong thay no bang script
# rieng - thay bang script thi bo SMB client khong len, xem
# sinh_autounattend_goi_script), nen RunSynchronous -> deploy.cmd nhu cu.
# Lab: may BIOS chay het chuoi, net use vao Samba thanh cong.
TEN_DIA_GPT_TU_DONG = "windows-autounattend.img"   # anh cu - chi con de don rac

THU_MUC_NHUNG = "X:\\Windows\\System32"

DAU_TEN_MAY = "@@CSTEN@@"      # cho dat ten may trong unattend (xem sinh_file_nhung)

TEN_WIM_DRIVER = "drivers.wim"

# TEN FILE KHI CHEN QUA wimboot. wimboot KHONG chen file duoi ".wim" vao
# System32 (coi la anh boot) - lab 26/09/2026 may VMXNET3: drivers.wim da
# tai ve nhung khong co trong X:\Windows\System32 -> driver cho anh boot
# chua bao gio duoc nap qua PXE. Chen duoi ten khac, deploy.cmd chep lai.
TEN_NHUNG_DRIVER = "cpi-drivers.bin"

DUOI_PS1_CO_BOM = ".ps1"
