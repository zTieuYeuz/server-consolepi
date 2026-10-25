# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Unattend - ISO tu dong / dia mem ao chua autounattend.

(B4: tach nguyen van tu unattend.py; ten ham/hang giu nguyen, nguon van re-export.)"""
import os
from consolesystem.core import duongdan as _DD
from consolesystem.features.deploy_os.un_hangso import (_sh)  # noqa: F401
from consolesystem.features.deploy_os.un_xml import (sinh_autounattend_xml)  # noqa: F401


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
    duong_xml = os.path.join(_DD.BOOT_DIR, TEN_AUTOUNATTEND)
    try:
        with open(duong_xml, "w", encoding="utf-8") as f:
            f.write(xml_noi_dung)
    except OSError as e:
        return False, f"Khong ghi duoc {TEN_AUTOUNATTEND}: {e}"

    duong_floppy = os.path.join(_DD.BOOT_DIR, TEN_FLOPPY)
    ok, msg = tao_dia_mem_ao(xml_noi_dung, duong_floppy)
    if not ok:
        return False, msg
    return True, f"Da ghi {TEN_AUTOUNATTEND} va {TEN_FLOPPY}."

def co_san_autounattend():
    return os.path.isfile(os.path.join(_DD.BOOT_DIR, TEN_AUTOUNATTEND))

def co_san_dia_mem_autounattend():
    return os.path.isfile(os.path.join(_DD.BOOT_DIR, TEN_FLOPPY))

TEN_ISO_TU_DONG = "windows-autounattend.iso"

def co_san_iso_tu_dong():
    """True neu da dung xong ISO tu dong (xem dung_iso_tu_dong)."""
    return os.path.isfile(os.path.join(_DD.BOOT_DIR, TEN_ISO_TU_DONG))

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

    goc_wim = os.path.join(_DD.BOOT_DIR, "boot.wim")
    duong_install = os.path.join(_DD.BOOT_DIR, "install.wim")
    if not os.path.isfile(goc_wim):
        return False, "Chua co boot.wim."
    if not os.path.isfile(duong_install):
        return False, "Chua co install.wim."

    import shutil
    import tempfile
    tam = tempfile.mkdtemp(prefix="iso-src-", dir=_DD.BOOT_DIR)
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

        duong_iso = os.path.join(_DD.BOOT_DIR, TEN_ISO_TU_DONG)
        duong_iso_tam = duong_iso + ".dang-dung"
        iso.write(duong_iso_tam)
        iso.close()
        os.replace(duong_iso_tam, duong_iso)
        return True, f"Da dung {TEN_ISO_TU_DONG} ({os.path.getsize(duong_iso):,} bytes)."
    except Exception as e:
        return False, f"Loi khi dung ISO: {e}"
    finally:
        shutil.rmtree(tam, ignore_errors=True)
