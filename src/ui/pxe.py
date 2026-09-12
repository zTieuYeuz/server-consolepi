"""
Console Pi - Phat PXE that (giai doan ke tiep cua Deployment OS)

Tiep noi module ui/deployos.py: chinh la phan "cau hinh PXE cua dnsmasq" ma
kiem_tra_san_sang() trong deployos.py bao la "chua dung - GIAI DOAN KE
TIEP". File nay lam cho no thanh THAT.

CO CHE PXE (da kiem chung tung phan qua man dnsmasq + wimlib, khong doan):
  1. May can cai boot, gui broadcast DHCP.
  2. dnsmasq (file nay dieu khien) tra IP + noi lay bootloader qua TFTP:
     - May kien truc BIOS (client-arch=0)      -> undionly.kpxe
     - May kien truc UEFI x64 (client-arch=7/9)-> snponly.efi

     LOI THAT DA GAP (kiem chung that tren 1 may ao VMware that, khong
     doan): ban dau dung `ipxe.efi` (ban co san driver mang rieng cua
     iPXE) - TAI DUOC qua TFTP binh thuong nhung CHAY THI CRASH ngay lap
     tuc, khien firmware lien tuc quay lai xin boot lai tu dau (vong lap
     vo han, giong het trieu chung "boot no chay xoay vong hoai"). Doi
     sang `snponly.efi` (ban CHI dung driver mang co san cua UEFI qua
     Simple Network Protocol, khong tu mang driver rieng) thi chay duoc
     ngay - day la van de tuong thich pho bien giua iPXE va NIC ao cua
     VMware, snponly.efi la giai phap chinh thuc cua du an iPXE cho dung
     truong hop nay.
  3. Bootloader do (iPXE) tu no LAI gui 1 lan DHCP nua de tu nhan dang la
     "iPXE" (qua DHCP option 77 - "user class"). dnsmasq nhan ra qua
     dhcp-userclass, lan nay tra ve dia chi 1 SCRIPT iPXE qua HTTP thay vi
     lai bootloader cu - neu khong lam buoc nay se bi VONG LAP VO TAN (iPXE
     tu tai lai chinh no mai mai).
  4. Script iPXE (menu.ipxe, sinh dong o duoi) chi dinh `wimboot` lam
     "kernel", nap `boot.wim` + `bootmgr.exe`/`wdsmgfw.efi` + `BCD` lam
     "initrd" - day la cach chinh thuc du an wimboot (cung tac gia iPXE)
     huong dan de boot WinPE tu file .wim qua mang, khong dung co che PXE/
     WDS truyen thong (khong can BCD kieu WDS phuc tap).

QUAN TRONG - BCD CHUA CO: file `BCD` (lay tu goc ISO Windows, thu muc
`boot/bcd` cho BIOS va `efi/microsoft/boot/bcd` cho UEFI) la 2 file NHO
(vai chuc KB) nhung KHONG nam san trong boot.wim - phai lay tu chinh ISO
goc. Da lo mat ban dau (xoa ISO truoc khi kip lay) - anh Thoai se tai lai
ISO 1 lan nua, luc do them buoc lay 2 file nay truoc khi xoa. Khi chua co
BCD, muc "San sang PXE" van bao ro con thieu, KHONG gia vo da xong.

AN TOAN:
  - Bat tinh nang nay CAT DHCP tren eth0 - neu dang truy cap dashboard QUA
    chinh cong eth0 do se mat ket noi (giong het canh bao cua direct.py).
  - Duong tai file boot qua HTTP (/deployos/pxeboot/<ten>) KHONG can dang
    nhap - bat buoc, vi may dang boot chua co gi de dang nhap ca. Nhung
    CHI mo khi PXE dang BAT (kiem tra qua dang_bat()), va CHI phuc vu dung
    file nam trong BOOT_DIR voi duoi da duyet - khong khac gi ve mat rui ro
    so voi TFTP/AP dnsmasq da co san trong du an (mac dinh tat, chi bat khi
    nguoi dung chu dong yeu cau).
"""
import os
import subprocess

from . import deployos as _d

STATE_FLAG = "/run/console-pi-pxe.flag"
DNSMASQ_CONF = "/etc/dnsmasq-pxe.conf"
IFACE = "eth0"
PI_IP = "192.168.98.1"
PI_CIDR = f"{PI_IP}/24"
NM_CONN = "netplan-eth0"
DON_VI_SYSTEMD = "dnsmasq-pxe"

TEN_BOOTMGR_BIOS = "bootmgr.exe"
TEN_BOOTMGR_UEFI = "wdsmgfw.efi"
TEN_BCD_BIOS = "bcd-bios"
TEN_BCD_UEFI = "bcd-uefi"


def _sh(cmd, timeout=20):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, str(e)


def dang_bat():
    return os.path.exists(STATE_FLAG)


def _duong(ten):
    return os.path.join(_d.BOOT_DIR, ten)


def _co_bootmgr_pxe():
    """
    bootmgr.exe/wdsmgfw.efi lay tu BEN TRONG boot.wim (\\Windows\\Boot\\PXE\\)
    - da kiem chung that qua `wimlib-imagex dir`. Trich ra 1 lan, luu rieng
    de khong phai giai nen lai boot.wim moi lan bat PXE.
    """
    return os.path.isfile(_duong(TEN_BOOTMGR_BIOS)) and os.path.isfile(_duong(TEN_BOOTMGR_UEFI))


def trich_bootmgr_tu_winpe():
    """
    Trich bootmgr.exe (BIOS) va wdsmgfw.efi (UEFI) tu ben trong boot.wim ra
    thanh file rieng trong BOOT_DIR. Goi 1 lan sau khi boot.wim duoc tai
    len - khong can dung ISO nua cho buoc nay (da kiem chung: wimlib doc
    duoc thang tu image so 1 cua boot.wim, khong can giai nen toan bo).
    """
    boot_wim = _duong("boot.wim")
    if not os.path.isfile(boot_wim):
        return False, "Chưa có boot.wim - tải lên ở tab Tài nguyên > Hệ điều hành trước."

    ket_qua = []
    for duong_wim, ten_luu in (
        (r"\Windows\Boot\PXE\bootmgr.exe", TEN_BOOTMGR_BIOS),
        (r"\Windows\Boot\PXE\wdsmgfw.efi", TEN_BOOTMGR_UEFI),
    ):
        dich = _duong(ten_luu)
        ok, out = _sh(["wimlib-imagex", "extract", boot_wim, "1",
                       duong_wim, "--dest-dir=" + os.path.dirname(dich)],
                      timeout=60)
        if not ok:
            return False, f"Không trích được {ten_luu}: {out[-200:]}"
        # wimlib giu nguyen ten goc (bootmgr.exe/wdsmgfw.efi) - da dung ten
        # do lam TEN_LUU nen khong can doi ten. Chi kiem tra co that khong.
        if not os.path.isfile(dich):
            return False, f"Trích xong nhưng không thấy {ten_luu} tại {dich}."
        ket_qua.append(ten_luu)
    return True, f"Đã trích {', '.join(ket_qua)} từ boot.wim."


def _co_bcd():
    return os.path.isfile(_duong(TEN_BCD_BIOS)) and os.path.isfile(_duong(TEN_BCD_UEFI))


def trang_thai_chuan_bi():
    """
    Danh sach (dat, nhan, chi_tiet) - PHAN NOI TIEP kiem_tra_san_sang() cua
    deployos.py, kiem tra rieng cac dieu kien PXE THAT SU can de bat duoc.
    """
    ra = []
    co_ipxe_tftp = os.path.isfile(_duong("undionly.kpxe")) and os.path.isfile(_duong("snponly.efi"))
    ra.append((co_ipxe_tftp, "Bootloader iPXE (BIOS + UEFI)",
               "Đã có cả undionly.kpxe và snponly.efi" if co_ipxe_tftp else
               "Thiếu - tải lên ở tab Tài nguyên > File boot (cần cả "
               "undionly.kpxe và snponly.efi - snponly.efi tương thích tốt "
               "hơn với máy ảo/một số card mạng UEFI, đã kiểm chứng thật)"))

    co_wimboot = os.path.isfile(_duong("wimboot"))
    ra.append((co_wimboot, "wimboot",
               "Đã có" if co_wimboot else "Thiếu - tải lên ở tab Tài nguyên > File boot"))

    ra.append((_co_bootmgr_pxe(), "bootmgr.exe + wdsmgfw.efi (trích từ boot.wim)",
               "Đã trích" if _co_bootmgr_pxe() else
               "Chưa trích - bấm nút 'Trích bootmgr từ boot.wim' bên dưới"))

    ra.append((_co_bcd(), "File BCD (từ ISO gốc)",
               "Đã có" if _co_bcd() else
               "CHƯA CÓ - cần lấy từ gốc ISO (thư mục boot/bcd và "
               "efi/microsoft/boot/bcd), không nằm sẵn trong boot.wim. "
               "Tải lại ISO và bấm nút lấy BCD."))
    return ra


def san_sang_bat():
    return all(dat for dat, _, _ in trang_thai_chuan_bi())


def _dia_chi_pi_that(kieu_boot):
    """
    Dia chi IP THAT cua Pi tren eth0 ma may dang boot se dung de goi TFTP/
    HTTP ve - KHONG duoc dung PI_IP (192.168.98.1) mot cach mu quang.

    LOI THAT DA GAP (anh Thoai dinh test kieu "mang co DHCP" thi bat ra):
    PI_IP la dia chi TINH Pi TU DAT cho chinh no, chi dung khi Pi lam DHCP
    day du (kieu truc_tiep/mang_khong_dhcp). O kieu "mang co DHCP"
    (proxyDHCP), Pi KHONG tu dat IP - no giu nguyen IP THAT do DHCP cua
    mang khach cap (vd 192.168.110.14). Neu van nhung PI_IP vao day, may
    dang boot se duoc chi toi mot dia chi khong ai lang nghe ca - hong tu
    dau, khong lien quan gi den PXE.
    """
    if kieu_boot == "mang_co_dhcp":
        from .layout import _ipv4_of
        return _ipv4_of(IFACE) or PI_IP
    return PI_IP


def _mang_that(iface=IFACE):
    """(dia_chi_mang, do_dai_prefix) THAT cua interface - dung cho proxyDHCP
    can biet dung dai mang cua DHCP server that, khong doan."""
    import ipaddress
    ok, out = _sh(["ip", "-o", "-4", "addr", "show", iface])
    if ok:
        for tu in out.split():
            if "/" in tu and tu[0].isdigit():
                try:
                    m = ipaddress.ip_interface(tu).network
                    return str(m.network_address), m.prefixlen
                except ValueError:
                    continue
    return None, None


def _sinh_menu_ipxe(kieu_boot="truc_tiep"):
    """
    Script iPXE that su duoc iPXE tai qua HTTP o buoc 3 (xem docstring dau
    file). Duong dan tro ve http://<dia_chi_pi_that>/deployos/pxeboot/<file>
    - CONG 80 (qua nginx, khong phai 8880 loopback) vi may dang boot la may
    KHAC tren mang, khong phai chinh Pi. Dia chi Pi phai la dia chi THAT
    (xem _dia_chi_pi_that) - khong duoc gia dinh la PI_IP cho moi kieu boot.
    """
    goc = f"http://{_dia_chi_pi_that(kieu_boot)}/deployos/pxeboot"

    # LOI THAT DA GAP (anh Thoai kiem chung that qua nhieu vong boot may
    # ao that, ca bang wimlib LAN bang DISM chinh chu Microsoft): moi
    # cach nhung autounattend.xml vao BEN TRONG boot.wim (wimlib update,
    # mount FUSE+commit, DISM mount+commit qua console that) DEU lam
    # boot.wim MAT KHA NANG BOOT qua wimboot ("Windows Boot Manager
    # 0xc000000f") - du dung tool nao, du DISM bao "completed
    # successfully". boot.wim GOC (khong qua sua gi) luon boot binh
    # thuong - da doi chieu truc tiep nhieu lan. Nap autounattend.xml
    # nhu 1 file/dia mem RIENG qua initrd phu cua wimboot cung KHONG
    # duoc Setup nhan dien - vi tai lieu chinh thuc cua wimboot
    # (ipxe.org/appnote/wimboot_architecture) xac nhan no chi phoi cac
    # file phu ra 1 he thong file ao RIENG cho GIAI DOAN bootmgr.exe
    # (truoc khi vao he dieu hanh), khong phai o dia X: that ma
    # WinPE/Setup chay - Setup khong bao gio thay duoc file o do.
    #
    # SUA DUNG (lan 1): bo wimboot hoan toan cho Windows, dung `sanboot`
    # cua iPXE - trinh dien CA MOT anh ISO nhu 1 o dia quang that su cho
    # firmware, dung y het co che boot tu USB/DVD that (khop voi cach
    # anh Thoai da tung lam thanh cong: "them file autounattend.xml vao
    # file ISO la chay luon"). Windows Setup luc nay THAT SU quet duoc
    # goc cua o dia rieng (khong phai X:) va tu ap dung autounattend.xml.
    #
    # LOI THAT DA GAP VOI ISO (da kiem chung, tra cuu duoc tai ipxe.org):
    # sanboot mot ISO qua HTTP o che do UEFI tra ve loi iPXE
    # (0x7f22208e roi 0x7f222091 sau khi sua 1 loi khac). Day la 1 LOI
    # THAT DA BIET cua chinh iPXE (xem mailing list ipxe-devel, thang
    # 12/2016, "Bug in UEFI Sanboot with iso9660"): code `efi_block.c`
    # cua iPXE tu nhan dien chu ky ISO9660 tren dia va ap dat sai
    # `blksize_shift`, doc sai du lieu FAT nam trong ISO - xay ra voi
    # BAT KY dia nao vua co ISO9660 vua co cau truc UEFI phuc tap. Fix
    # that su can sua ma nguon C cua iPXE (ngoai pham vi hop ly).
    #
    # SUA DUNG (lan 2, dang dung): bo ISO9660 hoan toan, dung anh dia
    # GPT + 1 phan vung FAT32 (kieu USB cai Windows that) - KHONG co chu
    # ky ISO9660 nao nen khong bao gio cham vao doan code loi do. Dung
    # 100% bang cong cu Linux (wimlib-imagex split de chia install.wim
    # vuot 4GB thanh install.swm/install2.swm, parted+mkfs.vfat de dung
    # GPT+FAT32, cac file boot van trich thang tu boot.wim) - xem
    # ui/unattend.py: dung_dia_gpt_tu_dong().
    from . import unattend as _u
    if _u.co_san_dia_gpt_tu_dong():
        return f"""#!ipxe
sanboot --no-describe {goc}/{_u.TEN_DIA_GPT_TU_DONG}
"""

    return f"""#!ipxe
kernel {goc}/wimboot
initrd {goc}/boot.wim            boot.wim
initrd {goc}/{TEN_BCD_BIOS}      BCD
initrd {goc}/{TEN_BOOTMGR_BIOS}  bootmgr.exe
boot
"""


def _ghi_menu_ipxe(kieu_boot="truc_tiep"):
    try:
        with open(_duong("menu.ipxe"), "w") as f:
            f.write(_sinh_menu_ipxe(kieu_boot))
        return True
    except OSError:
        return False


def _ghi_dnsmasq_conf(kieu_boot):
    """
    kieu_boot:
      truc_tiep / mang_khong_dhcp -> Pi lam DHCP DAY DU tren eth0 (giong het
        che do "Cam thang thiet bi" cua direct.py, chi khac dai IP de khong
        dung do neu ca 2 tinh nang deu duoc bat nham cung luc).
      mang_co_dhcp -> Pi CHI cham (proxyDHCP): khong cap IP, chi tra loi
        "file boot o dau" - de DHCP that cua mang khach lo phan cap IP.
        QUAN TRONG (loi that da gap, da sua): dai mang proxy PHAI la dai
        mang THAT cua eth0 luc do (vd 192.168.110.0/24, do DHCP cua mang
        khach cap), KHONG duoc dung PI_IP gia dinh - proxyDHCP se khong
        khop dung mang neu dai sai, hong tu dau khong lien quan gi PXE.
    """
    dia_chi_pi = _dia_chi_pi_that(kieu_boot)

    # LOI THAT DA GAP (kiem chung bang tcpdump that trong luc anh Thoai
    # dang cho): o che do proxyDHCP, dnsmasq KHONG dung dhcp-boot de quyet
    # dinh file boot - theo dung man dnsmasq: "--dhcp-range=...,proxy...
    # dnsmasq don gian cung cap thong tin trong --pxe-prompt va
    # --pxe-service de cho phep netboot" (dhcp-boot van khai bao duoc
    # nhung KHONG co tac dung trong che do proxy). Da bat qua that: dnsmasq
    # nhan dung goi tin DHCPDISCOVER cua may (thay trong log "vendor
    # class: PXEClient..."), NHUNG khong bao gio gui goi tra loi nao ca
    # (xac nhan bang tcpdump tren eth0 - khong co goi nao nguon tu Pi).
    # Them pxe-service (co tag rieng cho BIOS/UEFI) moi la cach dung cho
    # proxyDHCP theo tai lieu chinh thuc.
    dong_pxe_service = ""
    if kieu_boot == "mang_co_dhcp":
        mang, prefix = _mang_that(IFACE)
        if not mang:
            return False, (f"Khong doc duoc dia chi IP that cua {IFACE} - "
                           f"kiem tra da cam day mang va co IP chua.")
        dhcp_range = f"dhcp-range={mang},proxy"
        dong_gateway = ""     # proxyDHCP khong cap IP nen khong can khai bao gateway
        dong_pxe_service = (
            'pxe-service=tag:bios-that,x86PC,"Cai dat qua mang (Console Pi)",undionly.kpxe\n'
            'pxe-service=tag:efi-that,x86-64_EFI,"Cai dat qua mang (Console Pi)",snponly.efi'
        )
    else:
        dhcp_range = (f"dhcp-range={PI_IP.rsplit('.',1)[0]}.50,"
                     f"{PI_IP.rsplit('.',1)[0]}.99,255.255.255.0,12h")
        dong_gateway = f"dhcp-option=3,{PI_IP}"

    noi_dung = f"""# Console Pi - PXE cho tab Deployment OS. Sinh tu dong, dung sua tay -
# sinh lai moi lan bat qua ui/pxe.py (_ghi_dnsmasq_conf).
interface={IFACE}
bind-interfaces
except-interface=lo
{dhcp_range}
{dong_gateway}
port=0

# --- Nhan dang kien truc may (RFC 4578) de tra dung bootloader ---
dhcp-match=set:bios,option:client-arch,0
dhcp-match=set:efi-x64,option:client-arch,7
dhcp-match=set:efi-x64,option:client-arch,9

# May dang chay iPXE roi (tu nhan dang qua user-class "iPXE") thi chuyen
# sang script iPXE qua HTTP - KHONG lam vay se vong lap vo tan (iPXE tu
# tai lai chinh no).
#
# LOI THAT DA GAP (kiem chung bang tcpdump + --log-debug that, khong doan):
# mot goi DHCPDISCOVER cua may co the mang CA HAI tag "bios"/"efi-x64" LAN
# "ipxe" cung luc (may da chay iPXE VA la kien truc UEFI/BIOS). Da thu ca
# 2 thu tu khai bao dhcp-boot (ipxe truoc, ipxe sau) - KHONG anh huong gi,
# dnsmasq luon uu tien tag "efi-x64"/"bios" bat ke thu tu file, khien iPXE
# TU TAI LAI CHINH NO mai mai (vong lap vo han - dung trieu chung "chay
# xoay vong hoai" anh Thoai gap). Sua dung: dung `tag-if` de tao tag MOI
# (vd "efi-that") CHI bat khi la UEFI VA CHUA chay iPXE - tach biet han 2
# truong hop thay vi de chung de tag cung khop 1 request.
dhcp-userclass=set:ipxe,iPXE
tag-if=set:bios-that,tag:bios,tag:!ipxe
tag-if=set:efi-that,tag:efi-x64,tag:!ipxe
dhcp-boot=tag:bios-that,undionly.kpxe
dhcp-boot=tag:efi-that,snponly.efi
dhcp-boot=tag:ipxe,http://{dia_chi_pi}:80/deployos/pxeboot/menu.ipxe
{dong_pxe_service}
enable-tftp
tftp-root={_d.BOOT_DIR}
log-dhcp
"""
    try:
        with open(DNSMASQ_CONF, "w") as f:
            f.write(noi_dung)
        return True, ""
    except OSError as e:
        return False, str(e)


def _don_phien_smb_cu(dia_chi_may):
    r"""
    Ngat cac phien SMB CU con ket lai tren Pi cua dung may sap boot.

    LOI THAT DA GAP - day la nguyen nhan GOC cua chuyen "luc duoc luc
    khong" khi cai Windows (tim ra bang tcpdump tren chinh Pi, khong doan):

        192.168.110.33.49668 > 192.168.110.14.445: Flags [S]        <- SYN
        192.168.110.14.445 > 192.168.110.33.49668: Flags [.], ack 1 <- ACK tran

    May cai gui SYN de mo ket noi SMB, nhung Pi tra ve ACK TRAN thay vi
    SYN-ACK, nen bat tay TCP KHONG BAO GIO xong -> Windows bao "System
    error 53 - The network path was not found". Kiem chung tiep bang
    `ss -tan`:

        ESTAB  192.168.110.14:445  192.168.110.33:49668

    Tuc la Pi VAN dang giu ket noi cu tu lan boot TRUOC o trang thai
    ESTABLISHED: may kia bi reset/khoi dong lai giua chung nen khong he
    gui FIN/RST, Pi khong biet no da chet. Lan boot sau, WinPE lai cap
    DUNG cung so cong nguon (49668 - WinPE luon cap cong tu cung mot
    cho) va DHCP lai cap dung cung IP -> trung y het 4-tuple cu -> nhan
    Linux coi SYN moi la goi lac cua ket noi dang co va tra "challenge
    ACK" (RFC 5961) thay vi SYN-ACK.

    Vi vay lan cai DAU tien sau khi Pi khoi dong thi chay ngon, cac lan
    RESET may de cai lai thi hong - dung nhu hien tuong anh Thoai gap.
    (Go tay bang Shift+F10 lai duoc, vi luc do Windows cap cong nguon
    khac.)

    Cach don: `smbcontrol smbd kill-client-ip <ip>` - chi ngat dung may
    do, khong dung toi client nao khac dang dung Samba.
    """
    if not dia_chi_may:
        return
    _sh(["smbcontrol", "smbd", "kill-client-ip", dia_chi_may], timeout=10)


def bat_pxe(kieu_boot="truc_tiep", cauhinh=None):
    """
    cauhinh: dict trang thai wizard (ten_may, username, password, o_dia...)
    - neu co va la Windows, TU DONG dung lai anh dia GPT+FAT32 (boot.wim +
    script trien khai + unattend rieng cho os_id/kich ban NAY - xem
    ui/unattend.py: dung_dia_gpt_tu_dong()) truoc khi bat, de may can cai
    tu chay het khong can go tay gi ca.

    LOI THAT DA GAP (anh Thoai bao "lam sao biet chac no dung kich ban anh
    muon"): ham nay TUNG (a) goi chuan_bi_autounattend() - ham CU da bi
    thay the tu lau (dia mem ao, khong con dung nua) thay vi
    dung_dia_gpt_tu_dong() la ham THAT SU dang duoc PXE su dung (xem
    _sinh_menu_ipxe: sanboot thang vao file dung_dia_gpt_tu_dong() tao
    ra); va (b) neu PXE DA dang bat san thi return SOM ngay dau ham,
    KHONG BAO GIO dung lai anh dia - nghia la bam "Dung" 1 kich ban khac
    trong khi PXE dang chay se KHONG co tac dung gi, may can cai van boot
    vao anh dia CU. Sua lai: LUON dung lai anh dia truoc (khop dung
    os_id/kich ban dang chon), roi moi kiem tra da bat san hay chua de
    quyet dinh co can khoi dong lai dich vu dnsmasq hay khong (khong can
    khoi dong lai neu da bat san - file anh dia se duoc doc lai tu dau
    o lan sanboot TIEP THEO).
    """
    da_bat_san = dang_bat()
    if not da_bat_san and not san_sang_bat():
        return False, "Chưa đủ điều kiện (xem bảng 'Sẵn sàng PXE' bên trên)."

    if kieu_boot == "mang_co_dhcp" and not _mang_that(IFACE)[0]:
        return False, (f"Chưa đọc được địa chỉ IP thật của {IFACE} - kiểm "
                       f"tra đã cắm dây mạng vào mạng có DHCP chưa.")

    da_dung_anh_dia = False
    if cauhinh and cauhinh.get("os_ho") == "windows":
        from . import unattend as _u
        ok, msg = _u.dung_dia_gpt_tu_dong(cauhinh, _dia_chi_pi_that(kieu_boot))
        if not ok:
            return False, f"Không dựng được ảnh đĩa cài đặt: {msg}"
        da_dung_anh_dia = True

    if da_bat_san:
        if da_dung_anh_dia:
            return True, ("Đã cập nhật ảnh đĩa cài đặt theo kịch bản đang "
                           "chọn. PXE vẫn đang bật, không cần khởi động lại.")
        return True, "PXE đang bật sẵn."

    if not _ghi_menu_ipxe(kieu_boot):
        return False, "Không ghi được script iPXE."

    ok, err = _ghi_dnsmasq_conf(kieu_boot)
    if not ok:
        return False, f"Không ghi được cấu hình dnsmasq: {err}"

    if kieu_boot != "mang_co_dhcp":
        # Che do tu cap IP: can chiem han eth0, giong het direct.py
        _sh(["nmcli", "device", "set", IFACE, "managed", "no"])
        _sh(["ip", "addr", "flush", "dev", IFACE])
        ok, out = _sh(["ip", "addr", "add", PI_CIDR, "dev", IFACE])
        if not ok and "File exists" not in out:
            _sh(["nmcli", "device", "set", IFACE, "managed", "yes"])
            return False, f"Không đặt được IP tĩnh cho {IFACE}: {out[:150]}"
        _sh(["ip", "link", "set", IFACE, "up"])

    ok, out = _sh(["systemctl", "restart", DON_VI_SYSTEMD])
    if not ok:
        if kieu_boot != "mang_co_dhcp":
            _sh(["nmcli", "device", "set", IFACE, "managed", "yes"])
        return False, f"Không bật được dịch vụ PXE: {out[:200]}"

    # BAT LUON SAMBA - khong the thieu.
    #
    # LOI THAT DA GAP (11/09/2026): sau khi khoi dong lai Pi, bam "Dung"
    # thi dnsmasq-pxe len binh thuong nen may VAN PXE boot duoc, nhung
    # smbd thi khong (`smbd.service; disabled` - khong tu chay luc boot,
    # va truoc day no chi chay vi da duoc bat bang tay tu truoc do).
    # Ket qua: WinPE boot len roi dung o buoc [2/6] "khong ket noi duoc
    # kho trien khai" - trong giong het loi mang, rat kho doan ra.
    # PXE ma khong co kho Samba thi vo nghia, nen hai thu nay PHAI len
    # cung nhau. Dung `start` (khong phai `restart`) de khong ngat cac
    # may dang chep file do neu PXE duoc bat lai giua chung.
    ok_smb, out_smb = _sh(["systemctl", "start", "smbd"])
    if not ok_smb:
        _sh(["systemctl", "stop", DON_VI_SYSTEMD])
        if kieu_boot != "mang_co_dhcp":
            _sh(["nmcli", "device", "set", IFACE, "managed", "yes"])
        return False, ("Bật được PXE nhưng không bật được kho Samba "
                       f"(smbd): {out_smb[:200]}")

    open(STATE_FLAG, "w").write(kieu_boot)
    return True, ("Đã bật PXE. Cắm dây mạng từ Pi sang máy cần cài (hoặc qua "
                  "chung 1 switch nếu dùng kiểu 'mạng có DHCP'), vào BIOS/UEFI "
                  "máy đó chọn boot qua mạng (Network Boot / PXE Boot).")


def tat_pxe():
    if not dang_bat():
        return True, "PXE vốn đã tắt."
    _sh(["systemctl", "stop", DON_VI_SYSTEMD])
    # Tat luon Samba (xem ghi chu o bat_pxe): smb.conf chi co DUY NHAT
    # share [deploy] phuc vu PXE, khong con viec gi khac dung toi, nen tat
    # di de khong phoi SMB ra mang khi khong trien khai.
    _sh(["systemctl", "stop", "smbd"])
    try:
        kieu = open(STATE_FLAG).read().strip()
    except OSError:
        kieu = "truc_tiep"
    if kieu != "mang_co_dhcp":
        _sh(["ip", "addr", "flush", "dev", IFACE])
        _sh(["nmcli", "device", "set", IFACE, "managed", "yes"])
        _sh(["nmcli", "connection", "up", NM_CONN], timeout=30)
    try:
        os.remove(STATE_FLAG)
    except OSError:
        pass
    return True, f"Đã tắt PXE, trả {IFACE} về bình thường."


# ==================================================================== web
def register_pxe(app):
    from flask import request, redirect, send_from_directory, abort, flash
    from .layout import render_page
    from .home import _esc

    EXT_PHUC_VU = {".kpxe", ".efi", ".ipxe", ".wim", ".exe", ".img", ".xml",
                   ".iso", "", }
    TEN_PHUC_VU_RIENG = {"wimboot", TEN_BCD_BIOS, TEN_BCD_UEFI}

    @app.route("/deployos/pxeboot/<ten>")
    def deployos_pxeboot_file(ten):
        """
        Duong PHUC VU KHONG DANG NHAP cho may dang boot qua mang - xem canh
        bao an toan trong docstring dau file. CHI hoat dong khi PXE dang
        that su duoc bat (dang_bat()), tranh mo cua nay khi khong dung den.
        """
        if not dang_bat():
            abort(404)
        ten_sach = _d.ten_an_toan(ten)
        if not ten_sach:
            abort(404)
        duoi = os.path.splitext(ten_sach)[1].lower()
        if ten_sach not in TEN_PHUC_VU_RIENG and duoi not in EXT_PHUC_VU:
            abort(404)
        p = _d._duong_dan_trong(_d.BOOT_DIR, ten_sach)
        if not p or not os.path.isfile(p):
            abort(404)

        # Don phien SMB cu cua may sap boot - xem _don_phien_smb_cu().
        #
        # PHAI gan vao "menu.ipxe" chu KHONG duoc gan vao file anh dia.
        # LOI THAT DA GAP (anh Thoai: boot toi "Booting from SAN device
        # 0x80" roi man hinh den thui): `sanboot` KHONG tai anh dia ve mot
        # lan - no phuc vu anh dia nhu 1 O DIA QUA MANG, doc tung khoi
        # theo yeu cau SUOT qua trinh boot, tuc la route nay bi goi RAT
        # NHIEU lan. Gan lenh don (mot tien trinh smbcontrol rieng, cho
        # toi 10 giay) vao do = moi lan doc 1 khoi lai de ra 1 tien trinh
        # -> boot dung hinh. menu.ipxe thi chi duoc tai DUNG 1 LAN o dau
        # moi lan boot, va tai TRUOC khi sanboot chay - dung cho can.
        if ten_sach == "menu.ipxe":
            _don_phien_smb_cu(request.remote_addr)

        return send_from_directory(_d.BOOT_DIR, ten_sach)

    def _ve_lai(msg, ok):
        """
        LOI THAT DA GAP (anh Thoai bam "Bat PXE" xong khong thay gi ca -
        khong biet thanh cong hay that bai): 3 route duoi day TRUOC KIA vut
        bo het ket qua (ok, msg) roi redirect thang ve "/deployos/kichban" -
        mat luon ca trinh tu dang lam (quay ve man hinh chon tu dau) LAN
        khong hien 1 chu nao cho biet vua xay ra chuyen gi. Dung nhat khi
        that bai that su (vd chua cam day mang) - nguoi dung khong co cach
        nao biet ly do.

        Sua: dung flash() (session) mang thong diep qua redirect, VA quay
        ve DUNG buoc 7 cua chinh trinh tu dang lam (giu "ma" qua truong an
        trong form) thay vi ve trang dau - khong mat lua chon da chon.
        """
        flash(msg, "ok" if ok else "err")
        ma = request.form.get("ma", "")
        if ma:
            return redirect(f"/deployos/wizard/{ma}/7")
        return redirect("/deployos/kichban")

    @app.route("/deployos/pxe/trich-bootmgr", methods=["POST"])
    def deployos_pxe_trich():
        ok, msg = trich_bootmgr_tu_winpe()
        return _ve_lai(msg, ok)

    @app.route("/deployos/pxe/bat", methods=["POST"])
    def deployos_pxe_bat():
        kieu = request.form.get("kieu_boot", "truc_tiep")
        # Doc lai toan bo cau hinh cua trinh tu (khong chi kieu_boot) de
        # sinh dung autounattend.xml khop voi ten may/tai khoan/o dia anh
        # Thoai da chon - xem bat_pxe() va ui/unattend.py.
        ma = request.form.get("ma", "")
        cauhinh = _d._wizard_lay(ma) if ma else None
        # LOI THAT DA GAP (anh Thoai: cai xong nhung "mat khau khong dung,
        # no chay kich ban nao ay"): trang thai trinh tu nam trong BO NHO
        # (_WIZARD) nen se MAT khi dashboard khoi dong lai hoac qua han.
        # Luc do cauhinh = None, bat_pxe() se BO QUA hoan toan buoc dung
        # lai anh dia va bat PXE voi anh dia CU (cua lan chay truoc do,
        # co the cua kich ban khac hoan toan) MA KHONG BAO GI CA. Phai
        # bao loi ro rang thay vi im lang chay sai kich ban.
        if ma and cauhinh is None:
            return _ve_lai(
                "Trình tự đã hết hạn (hoặc dashboard vừa khởi động lại) nên "
                "không còn giữ được lựa chọn của anh. CHƯA bật PXE - vào lại "
                "danh sách kịch bản và bấm \"Dùng\" lần nữa để chắc chắn máy "
                "cài đúng kịch bản anh muốn.", False)
        ok, msg = bat_pxe(kieu, cauhinh)
        return _ve_lai(msg, ok)

    @app.route("/deployos/pxe/tat", methods=["POST"])
    def deployos_pxe_tat():
        ok, msg = tat_pxe()
        return _ve_lai(msg, ok)

    return app
