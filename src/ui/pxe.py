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
import re
import shutil
import subprocess
import threading

from . import deployos as _d

STATE_FLAG = "/run/console-pi-pxe.flag"
DNSMASQ_CONF = "/etc/dnsmasq-pxe.conf"
PI_IP = "192.168.98.1"
PI_CIDR = f"{PI_IP}/24"
# Tra eth0 ve cho NetworkManager: dung `nmcli device connect <cong>` thay
# vi goi ten ket noi co dinh "netplan-eth0" - ten do chi dung tren Pi nay,
# may khac dat ten khac han ("Wired connection 1", "ens192"...). Goi theo
# THIET BI thi may nao cung dung.
DON_VI_SYSTEMD = "dnsmasq-pxe"

# File boot BAN KY chinh thuc kem san trong ma nguon (src/pxe-boot/, xem
# README o do) - chep vao TFTP moi lan bat PXE. Truoc 1.5.0 nguoi dung phai tu
# tai len, va iPXE cua Debian KHONG ky -> may bat Secure Boot tu choi.
#   BIOS        -> undionly.kpxe
#   UEFI (+SB)  -> snponly-shim.efi (shim, Microsoft ky) -> tu tai tang 2
#                  = snponly ban KY, phat duoi CA 2 TEN vi shim xin ten nao
#                  tuy cach no biet ten cua chinh no (log TFTP that):
#                    - DHCP day du (lab): xin "ipxe.efi"
#                    - proxyDHCP (mang cong ty, 26/09/2026): xin "snponly.efi"
#                  Loi that: Pi con "snponly.efi" CU cua Debian (khong ky, tai
#                  len tu truoc) -> may bat Secure Boot bao "Security
#                  Violation". Nay ghi de bang ban ky moi lan bat PXE.
THU_MUC_FILE_KEM = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "pxe-boot")
FILE_BOOT_KEM = ("undionly.kpxe", "snponly-shim.efi", "ipxe.efi", "snponly.efi",
                 "wimboot")
FILE_EFI_DAU = "snponly-shim.efi"

TEN_BOOTMGR_BIOS = "bootmgr.exe"
TEN_BOOTMGR_UEFI = "wdsmgfw.efi"
TEN_BCD_BIOS = "bcd-bios"
TEN_BCD_UEFI = "bcd-uefi"


def cong():
    """
    Cong co day dung cho PXE. Truoc day viet cung "eth0".

    VI SAO PHAI HOI MOI LAN thay vi tinh mot lan luc nap module: cong co
    the doi GIUA CHUNG - cam them USB-LAN, hoac tren may ban thi ten cong
    la enp3s0/ens192 tuy may. Tinh san 1 lan roi giu mai se ket vao gia
    tri sai ngay khi nguoi dung doi cong trong Cai dat.

    Neu may khong co cong day nao, tra ve "eth0" lam nuoc cuoi de cac lenh
    ben duoi con bao loi ro rang ("khong tim thay thiet bi eth0") thay vi
    nhan chuoi rong roi sinh ra lenh `ip addr add ... dev ` kho hieu.
    """
    from . import phancung as _pc
    return _pc.cong_day() or "eth0"


def _sh(cmd, timeout=20):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, str(e)


def dang_bat():
    return os.path.exists(STATE_FLAG)


def kieu_dang_bat():
    """
    Kieu boot cua phien PXE DANG chay ("" neu dang tat). Doc tu STATE_FLAG -
    day la nguon su that duy nhat ve che do dang phuc vu, vi cau hinh
    dnsmasq va IP cua eth0 deu duoc dat theo no.
    """
    try:
        with open(STATE_FLAG) as f:
            return f.read().strip()
    except OSError:
        return ""


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


def _file_kem_du():
    return all(os.path.isfile(os.path.join(THU_MUC_FILE_KEM, f)) for f in FILE_BOOT_KEM)


def _chep_file_boot():
    """Chep bo file boot kem san vao TFTP (BOOT_DIR) neu thieu/khac."""
    import filecmp
    for f in FILE_BOOT_KEM:
        nguon, dich = os.path.join(THU_MUC_FILE_KEM, f), _duong(f)
        try:
            if not (os.path.isfile(dich) and filecmp.cmp(nguon, dich, shallow=False)):
                shutil.copyfile(nguon, dich + ".moi")
                os.chmod(dich + ".moi", 0o644)
                os.replace(dich + ".moi", dich)
        except OSError as e:
            return False, f"Không chép được file boot {f}: {e}"
    return True, ""


def trang_thai_chuan_bi():
    """
    Danh sach (dat, nhan, chi_tiet) - PHAN NOI TIEP kiem_tra_san_sang() cua
    deployos.py, kiem tra rieng cac dieu kien PXE THAT SU can de bat duoc.

    Tu 1.5.0: iPXE + wimboot kem san (ban ky), bootmgr + BCD do wimboot tu
    lay tu boot.wim -> khong con buoc tai len / trich / lay BCD tu ISO.
    """
    du = _file_kem_du()
    return [(du, "File boot iPXE + wimboot (bản ký chính thức, kèm sẵn)",
             "Đủ - chạy được máy BIOS, UEFI và UEFI bật Secure Boot" if du else
             f"THIẾU trong {THU_MUC_FILE_KEM} - cài lại/cập nhật Console System")]


def san_sang_bat():
    return all(dat for dat, _, _ in trang_thai_chuan_bi())


def mo_ta_ket_noi(kieu_boot):
    """
    Huong dan ket noi + canh bao rieng cho tung kieu boot - dung chung cho
    ca thong bao "Da bat PXE" (bat_pxe) lan trang "Bat/Tat PXE" cua
    ui/deployos.py.

    LOI THAT DA GAP (tu kiem tra lai, chua ai bao nhung sai that): thong
    bao cu chi noi "cam day thang... (hoac qua switch neu dung kieu 'mang
    co DHCP')" - GAN NHAM switch cho kieu proxyDHCP, trong khi kieu THAT
    su dung switch la "mang_khong_dhcp" (Pi tu lam DHCP DAY DU tren ca
    switch do). Kieu "mang_co_dhcp" (proxyDHCP) khong he cap IP nen di
    switch hay day thang deu duoc, khong lien quan gi den viec co switch
    hay khong.
    """
    if kieu_boot == "mang_khong_dhcp":
        return (
            "Cắm Pi và máy cần cài vào CHUNG 1 switch (mạng đó KHÔNG được "
            "có DHCP server nào khác). Pi sẽ tự cấp IP cho MỌI thiết bị "
            "hỏi DHCP trên switch đó, không riêng gì máy cần cài - nếu "
            "switch còn cắm thêm máy khác không liên quan, máy đó cũng sẽ "
            "nhận nhầm IP từ Pi. Chỉ dùng switch RIÊNG, tách biệt hẳn khỏi "
            "mạng thật của khách."
        )
    if kieu_boot == "mang_co_dhcp":
        return (
            "Cắm Pi vào mạng đã có sẵn DHCP (switch của khách). Pi CHỈ trả "
            "lời \"file boot ở đâu\" (proxyDHCP) - không tự cấp IP, không "
            "tranh giành gì với DHCP thật của khách."
        )
    return "Cắm dây mạng THẲNG từ Pi sang đúng máy cần cài - không qua switch nào cả."


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
        return _ipv4_of(cong()) or PI_IP
    return PI_IP


def _mang_that(iface=None):
    if iface is None:
        iface = cong()
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
    # TU 1.5.0 QUAY LAI wimboot - nhung KHONG sua boot.wim (nguyen nhan
    # 0xc000000f o tren) va KHONG trong cho Setup tu quet autounattend: chen
    # them winpeshl.ini goi setup.exe /unattend:<duong dan ro> (xem unattend:
    # FILE NHUNG QUA WIMBOOT). Ly do bo sanboot: anh GPT chi chay UEFI tat
    # Secure Boot. Kiem chung lab BIOS/UEFI/UEFI+SB - iso/test/wimboot-lab.sh.
    # CHI CON MENU (25/09/2026 - xem ui/pxemenu.py): may khach TU CHON kich
    # ban. Khong con duong
    # "1 anh chung" cua nut "Dung" lan duong wimboot tran (boot.wim khong
    # co autounattend - Setup hoi tay, khong dung kich ban nao).
    from . import pxemenu as _m
    return _m.sinh_script(goc)


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
        mang, prefix = _mang_that(cong())
        if not mang:
            return False, (f"Khong doc duoc dia chi IP that cua {cong()} - "
                           f"kiem tra da cam day mang va co IP chua.")
        dhcp_range = f"dhcp-range={mang},proxy"
        dong_gateway = ""     # proxyDHCP khong cap IP nen khong can khai bao gateway
        dong_pxe_service = (
            'pxe-service=tag:bios-that,x86PC,"Cai dat qua mang (Console Pi)",undionly.kpxe\n'
            f'pxe-service=tag:efi-that,x86-64_EFI,"Cai dat qua mang (Console Pi)",{FILE_EFI_DAU}'
        )
    else:
        dhcp_range = (f"dhcp-range={PI_IP.rsplit('.',1)[0]}.50,"
                     f"{PI_IP.rsplit('.',1)[0]}.99,255.255.255.0,12h")
        dong_gateway = f"dhcp-option=3,{PI_IP}"

    noi_dung = f"""# Console Pi - PXE cho tab Deployment OS. Sinh tu dong, dung sua tay -
# sinh lai moi lan bat qua ui/pxe.py (_ghi_dnsmasq_conf).
interface={cong()}
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
#
# LOI THAT (25/09/2026, anh Thoai che do "mang co DHCP" - proxyDHCP): iPXE
# bao "Nothing to boot" du Pi CO tra loi dung ten file. Bat goi tin trong
# phong thi nghiem (router DHCP + Pi proxy + may khach QEMU): iPXE hoi Pi
# qua cong 4011, Pi tra loi co ten file nhung next-server (siaddr) = 0.0.0.0
# -> iPXE LOAI goi (src/net/udp/dhcp.c, dhcp_has_pxeopts(): proxyDHCP chi
# hop le khi CO next-server VA ten file, hoac co menu PXE). Sua: ghi RO dia
# chi Pi o truong thu 3 cua dhcp-boot -> dnsmasq dien siaddr. Ghi cho ca 3
# dong (ca 3 che do) - che do cap IP day du thi vo hai, van dung dia chi Pi.
dhcp-boot=tag:bios-that,undionly.kpxe,,{dia_chi_pi}
dhcp-boot=tag:efi-that,{FILE_EFI_DAU},,{dia_chi_pi}
dhcp-boot=tag:ipxe,http://{dia_chi_pi}:80/deployos/pxeboot/menu.ipxe,,{dia_chi_pi}
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


def _bat_pxe_that(kieu_boot="truc_tiep"):
    """
    Bat PXE o che do mang kieu_boot: dua eth0 ve dung trang thai cua che do
    do, dung/dung lai anh dia cho MOI kich ban Windows (menu - xem
    ui/pxemenu.py), ghi menu.ipxe, khoi dong dnsmasq + Samba.

    Dang bat san dung che do nay -> chi dung lai anh con thieu/da sua va
    ghi lai menu (khong khoi dong lai dnsmasq). Khac che do -> tat roi bat
    lai theo thu tu bat buoc o duoi.
    """
    da_bat_san = dang_bat()
    kieu_dang_chay = kieu_dang_bat()
    if not da_bat_san and not san_sang_bat():
        return False, "Chưa đủ điều kiện (xem bảng 'Sẵn sàng PXE' bên trên)."

    # ---- 1. Dang chay DUNG kieu cua kich ban nay: chi can dung lai anh dia
    # (eth0 va dnsmasq da o dung trang thai cua kieu do roi, khong dung vao).
    if da_bat_san and kieu_dang_chay == kieu_boot:
        them = _dung_menu(kieu_boot)
        if not _ghi_menu_ipxe(kieu_boot):
            return False, "Không ghi được script iPXE."
        return True, "PXE vẫn đang bật đúng chế độ này, đã cập nhật menu." + them

    # ---- 2. Khac kieu (hoac dang tat): dua eth0 ve dung trang thai cua kieu
    # MOI TRUOC, roi moi lam nhung viec phu thuoc vao dia chi Pi.
    #
    # HAI LOI THAT DA GAP, ca hai deu tu cung mot goc "khong theo dung kich
    # ban da chon" (18/09/2026, phat hien tai cho khi anh Thoai chay that):
    #
    # (a) Doi kieu boot ma KHONG doi gi ca: ham nay truoc day chi hoi "PXE
    #     bat chua", bat roi la thoat som. Anh Thoai dang chay
    #     "mang_co_dhcp" (proxyDHCP dai 192.168.110.0 cua cong ty), rut day
    #     cam thang sang may can cai roi bam "Dung" kich ban
    #     "mang_khong_dhcp" -> anh dia dung LAI DUNG, nhung dnsmasq VAN cau
    #     hinh proxy tren dai cu va eth0 thi mat sach IP. Log dnsmasq:
    #         DHCP packet received on eth0 which has no address
    #         no address range available for DHCP request via eth0
    #     May can cai CO hoi, Pi CO nghe, nhung khong tra loi duoc cau nao
    #     -> treo vinh vien o "Start PXE over IPv4". Ham con bao "PXE van
    #     dang bat, khong can khoi dong lai" = nghe nhu moi thu on.
    #
    # (b) Nang hon va am hon, dung o CHIEU NGUOC LAI (anh Thoai chi ra
    #     truoc khi no kip xay ra that): anh dia TUNG duoc dung TRUOC khi
    #     doi che do mang. Dia chi Pi nhet vao anh dia lay tu eth0 NGAY LUC
    #     DO - tuc la dia chi cua che do CU. Doi tu "mang_khong_dhcp" sang
    #     "mang_co_dhcp" thi anh dia se mang dia chi tinh cu 192.168.98.1,
    #     sau do eth0 moi tra ve DHCP that (vd 192.168.110.14). dnsmasq thi
    #     dung dia chi moi, nhung WinPE boot len lai di tim kho trien khai
    #     o 192.168.98.1 -> "khong ket noi duoc kho trien khai", trong y
    #     het loi mang, rat kho lan ra.
    #
    # SUA (cho ca hai): thu tu BAT BUOC la doi che do mang -> co dia chi Pi
    # THAT cua che do moi -> moi dung anh dia va ghi cau hinh. Nho vay moi
    # thu (anh dia, menu.ipxe, dnsmasq) luon cung mot dia chi, va luon dung
    # kieu boot cua kich ban nguoi dung chon.
    doi_kieu = da_bat_san
    if doi_kieu:
        _tat_pxe_that()

    if kieu_boot != "mang_co_dhcp":
        # Che do tu cap IP: can chiem han eth0, giong het direct.py
        _sh(["nmcli", "device", "set", cong(), "managed", "no"])
        _sh(["ip", "addr", "flush", "dev", cong()])
        ok, out = _sh(["ip", "addr", "add", PI_CIDR, "dev", cong()])
        if not ok and "File exists" not in out:
            _sh(["nmcli", "device", "set", cong(), "managed", "yes"])
            return False, f"Không đặt được IP tĩnh cho {cong()}: {out[:150]}"
        _sh(["ip", "link", "set", cong(), "up"])
    elif not _mang_that(cong())[0]:
        # proxyDHCP bat buoc phai co IP THAT do mang khach cap. Kiem tra SAU
        # khi da tra eth0 ve cho NetworkManager (tat_pxe o tren), khong phai
        # truoc - neu kiem tra truoc, IP tinh con sot lai cua che do cu se
        # lam phep kiem tra nay do nham.
        return False, (f"Chưa đọc được địa chỉ IP thật của {cong()} - kiểm "
                       f"tra đã cắm dây mạng vào mạng có DHCP chưa.")

    # ---- 3. Gio eth0 da dung dia chi cua kieu MOI -> dung anh dia + ghi
    # cau hinh, tat ca deu dung chung dia chi nay.
    dia_chi_pi = _dia_chi_pi_that(kieu_boot)

    def _tra_lai_eth0():
        if kieu_boot != "mang_co_dhcp":
            _sh(["nmcli", "device", "set", cong(), "managed", "yes"])
            _sh(["nmcli", "device", "connect", cong()], timeout=30)

    them_menu = _dung_menu(kieu_boot)

    if not _ghi_menu_ipxe(kieu_boot):
        _tra_lai_eth0()
        return False, "Không ghi được script iPXE."

    ok, err = _ghi_dnsmasq_conf(kieu_boot)
    if not ok:
        _tra_lai_eth0()
        return False, f"Không ghi được cấu hình dnsmasq: {err}"

    ok, out = _sh(["systemctl", "restart", DON_VI_SYSTEMD])
    if not ok:
        if kieu_boot != "mang_co_dhcp":
            _sh(["nmcli", "device", "set", cong(), "managed", "yes"])
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
            _sh(["nmcli", "device", "set", cong(), "managed", "yes"])
        return False, ("Bật được PXE nhưng không bật được kho Samba "
                       f"(smbd): {out_smb[:200]}")

    open(STATE_FLAG, "w").write(kieu_boot)
    dau = ("Đã ĐỔI chế độ PXE sang kiểu mới (tắt kiểu cũ rồi bật lại)."
           if doi_kieu else "Đã bật PXE.")
    return True, (f"{dau} {mo_ta_ket_noi(kieu_boot)} Vào BIOS/UEFI máy "
                  "đó chọn boot qua mạng (Network Boot / PXE Boot)." + them_menu)


# ---- KHOA: moi luc chi 1 viec bat/tat PXE / dung anh dia.
#
# LOI THAT (Pi, 24/09/2026 - anh Thoai: "pxe cua console pi sao ko bat
# duoc"): bat menu PXE thi "Bat PXE" phai dung them 1 anh dia cho MOI kich
# ban Windows (~1-2 phut moi cai tren Pi) -> trang quay lau, bam them lan
# nua -> 2 lan bat CHAY CHONG nhau: lan sau thay o dia dang bi lan truoc
# chiem cho (file tam ~1 GB) nen bao "khong du cho" va BO kich ban do khoi
# menu, ca hai cung khoi dong lai dnsmasq va ghi de menu.ipxe cua nhau.
# Gio lan bam sau duoc bao ro "dang lam, cho" thay vi chay chong.
_KHOA = threading.RLock()
_DANG_LAM = ("Đang bật/cập nhật PXE từ lần bấm trước. Chờ vài giây rồi "
             "tải lại trang - KHÔNG cần bấm lại.")


def _file_sau_mount(diem_mount):
    """File anh dia dung sau 1 diem mount loop (/dev/loopNp1), khong co -> ""."""
    try:
        with open("/proc/mounts") as f:
            for dong in f:
                phan = dong.split()
                if len(phan) > 1 and phan[1] == diem_mount and phan[0].startswith("/dev/loop"):
                    # /dev/loop1p1 -> loop1 (KHONG split("p"): "loop" co chu p)
                    loop = re.match(r"/dev/(loop\d+)", phan[0]).group(1)
                    with open(f"/sys/block/{loop}/loop/backing_file") as g:
                        return g.read().strip()
    except OSError:
        pass
    return ""


def _don_rac_dung_anh():
    """
    Don do dang con sot lai tu lan dung anh truoc bi ngat giua chung (dung
    cho that: gpt-mnt-* con mount lam treo loop device, file tam 500 MB).
    CHI goi khi dang giu _KHOA - luc do chac chan khong co ai dang dung.
    """
    try:
        ten = os.listdir(_d.BOOT_DIR)
    except OSError:
        return
    for n in ten:
        p = os.path.join(_d.BOOT_DIR, n)
        if n.startswith("gpt-mnt-") and os.path.isdir(p):
            if os.path.ismount(p):
                # Anh dia dang bi ket mount nay co the CHUA ghi du -> xoa dau
                # van tay cua no de lan dung sau bat buoc dung lai, khong
                # "dung lai anh cu" (dau van tay van khop du file hong).
                anh = _file_sau_mount(p)
                if anh:
                    try:
                        os.remove(anh + ".json")
                    except OSError:
                        pass
                ok, _ = _sh(["umount", p], timeout=300)
                if not ok:
                    _sh(["umount", "-l", p], timeout=30)
            try:
                os.rmdir(p)
            except OSError:
                pass
        elif n.startswith("gpt-src-") and os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
        elif n.endswith(".dang-dung"):
            try:
                os.remove(p)
            except OSError:
                pass


def bat_pxe(kieu_boot="truc_tiep"):
    """Xem _bat_pxe_that. Co khoa: bam 2 lan khong chay chong."""
    if not _KHOA.acquire(blocking=False):
        return False, _DANG_LAM
    try:
        from . import phancung as _pc
        loi = _pc.loi_cong_da_chon_mat()
        if loi:
            return False, loi
        _don_rac_dung_anh()
        return _bat_pxe_that(kieu_boot)
    finally:
        _KHOA.release()


def tat_pxe():
    if not _KHOA.acquire(blocking=False):
        return False, _DANG_LAM
    try:
        return _tat_pxe_that()
    finally:
        _KHOA.release()


def cap_nhat_menu():
    """Xem _cap_nhat_menu_that. Dang ban thi bao, khong chay chong."""
    if not _KHOA.acquire(blocking=False):
        return (" Menu PXE CHƯA cập nhật: đang bận xử lý lần bấm khác - "
                "chờ vài giây rồi bấm \"Lưu cài đặt menu\" lại.")
    try:
        _don_rac_dung_anh()
        return _cap_nhat_menu_that()
    finally:
        _KHOA.release()


TAI_KHOAN_SAMBA = "consolepi-deploy"


def _bao_dam_tai_khoan_samba():
    """
    Dam bao tai khoan Samba cua kho trien khai TON TAI, BAT, va mat khau
    KHOP file khoa (deploy.cmd nhung mat khau tu file khoa nay) - chay moi
    lan bat PXE / cap nhat menu, truoc khi sinh file cho kich ban.

    LOI THAT (26/09/2026, may cai tu ISO 1.5.0): thiet lap lan dau cua ISO
    tao NHAM tai khoan "deploy" thay vi "consolepi-deploy" -> WinPE `net use`
    bao "System error 1312", khong lay duoc install.wim. Tu sua o day de ca
    may DA CAI tu ISO loi cung tu het sau khi cap nhat, khong phai cai lai.
    Tren Pi (install.sh da tao dung) thi chi dong bo lai - vo hai.
    """
    import secrets
    from .duongdan import FILE_KHOA_SAMBA
    try:
        with open(FILE_KHOA_SAMBA, encoding="utf-8") as f:
            mk = f.read().strip()
    except OSError:
        mk = ""
    if not mk:
        mk = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789")
                     for _ in range(24))
        try:
            os.makedirs(os.path.dirname(FILE_KHOA_SAMBA), exist_ok=True)
            fd = os.open(FILE_KHOA_SAMBA, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(mk)
        except OSError as e:
            return False, f"Không tạo được khoá Samba: {e}"
    ok, _ = _sh(["id", TAI_KHOAN_SAMBA])
    if not ok:
        ok, out = _sh(["useradd", "--system", "--no-create-home",
                       "--shell", "/usr/sbin/nologin", TAI_KHOAN_SAMBA])
        if not ok:
            return False, f"Không tạo được tài khoản {TAI_KHOAN_SAMBA}: {out[:150]}"
    try:
        r = subprocess.run(["smbpasswd", "-s", "-a", TAI_KHOAN_SAMBA],
                           input=f"{mk}\n{mk}\n", capture_output=True,
                           text=True, timeout=20)
        if r.returncode != 0:
            return False, f"Không đặt được mật khẩu Samba: {(r.stdout + r.stderr)[:150]}"
    except (OSError, subprocess.SubprocessError) as e:
        return False, f"Không chạy được smbpasswd: {e}"
    _sh(["smbpasswd", "-e", TAI_KHOAN_SAMBA])
    return True, ""


def _dung_menu(kieu_boot):
    """
    Ghi file nhung (wimboot) cho moi kich ban Windows (menu PXE) + chep file
    boot kem san vao TFTP. Tra ve doan chu noi them vao thong bao.
    """
    from . import pxemenu as _m
    ok, loi = _chep_file_boot()
    ok_smb, loi_smb = _bao_dam_tai_khoan_samba()
    kq = _m.chuan_bi_menu(_dia_chi_pi_that(kieu_boot), kieu_boot)
    if not ok_smb:
        kq.insert(0, loi_smb)
    if not ok:
        kq.insert(0, loi)
    so_muc = len(_m.muc_menu())
    return (f" Menu: {so_muc} kịch bản." + (" " + " ".join(kq) if kq else ""))


def _cap_nhat_menu_that():
    """
    Goi khi doi cai dat menu / luu-xoa kich ban (menu co TAT CA kich ban
    Windows) LUC PXE DANG BAT: dung anh con thieu va ghi lai menu.ipxe ngay, khong phai tat-bat
    lai PXE. PXE dang tat thi khong lam gi (lan bat sau se tu dung).
    """
    if not dang_bat():
        return ""
    kieu = kieu_dang_bat()
    them = _dung_menu(kieu)
    if not _ghi_menu_ipxe(kieu):
        return " KHÔNG ghi được menu.ipxe."
    return them


def _tat_pxe_that():
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
        _sh(["ip", "addr", "flush", "dev", cong()])
        _sh(["nmcli", "device", "set", cong(), "managed", "yes"])
        _sh(["nmcli", "device", "connect", cong()], timeout=30)
    try:
        os.remove(STATE_FLAG)
    except OSError:
        pass
    return True, f"Đã tắt PXE, trả {cong()} về bình thường."


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

    # Ten thu muc/file cua duong wimboot: chi ky tu an toan, khong ".." -
    # cung la ten do pxemenu.ten_thu_muc() sinh ra.
    _TEN_SACH = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9._-]{0,150}$")

    @app.route("/deployos/pxeboot/_pxe/<thu_muc>/<ten>")
    @app.route("/deployos/pxeboot/_pxe/<ten>", defaults={"thu_muc": ""})
    def deployos_pxeboot_nhung(thu_muc, ten):
        """File wimboot chen vao cho tung kich ban (+ drivers.wim dung chung)."""
        from . import pxemenu as _m
        if not dang_bat() or not _TEN_SACH.match(ten) or (
                thu_muc and not _TEN_SACH.match(thu_muc)):
            abort(404)
        goc = os.path.join(_d.BOOT_DIR, _m.THU_MUC_PXE, thu_muc)
        from . import unattend as _u
        if not thu_muc and ten == _u.TEN_NHUNG_DRIVER:
            ten = _u.TEN_WIM_DRIVER      # xem pxemenu: ten cuoi URL = ten file
        if not os.path.isfile(os.path.join(goc, ten)):
            abort(404)
        return send_from_directory(goc, ten)

    @app.route("/deployos/pxeboot/os/<os_id>/boot.wim")
    def deployos_pxeboot_bootwim(os_id):
        """boot.wim GOC cua tung he dieu hanh - wimboot nap, khong sua gi."""
        if not dang_bat() or not _TEN_SACH.match(os_id):
            abort(404)
        p = _d.duong_boot_wim(os_id)
        if not os.path.isfile(p):
            abort(404)
        return send_from_directory(os.path.dirname(p), os.path.basename(p))

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
        # Nut bat/tat PXE nay gio nam o tab "Cai dat" cua Deployment OS -
        # form o do gui kem truong an `ve` de quay lai DUNG trang vua bam,
        # khong nhay ve danh sach kich ban (mat ngu canh dang lam).
        ve = request.form.get("ve", "")
        if ve.startswith("/deployos/"):
            return redirect(ve)
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
        from . import pxemenu as _m
        ok, msg = _m.luu_cauhinh(request.form.get("kieu_boot", ""),
                                 request.form.get("cho_giay", "30"))
        if not ok:
            return _ve_lai(msg, False)
        ok, msg = bat_pxe(_m.doc_cauhinh()["kieu_boot"])
        return _ve_lai(msg, ok)

    @app.route("/deployos/pxe/tat", methods=["POST"])
    def deployos_pxe_tat():
        ok, msg = tat_pxe()
        return _ve_lai(msg, ok)

    # ---- Menu PXE (Buoc A - xem ui/pxemenu.py)
    @app.route("/deployos/menu-pxe/luu", methods=["POST"])
    def deployos_menu_pxe_luu():
        """Doi so giay cho luc PXE dang bat (doi che do mang: tat roi bat lai)."""
        from . import pxemenu as _m
        ok, msg = _m.luu_cauhinh(cho_giay=request.form.get("cho_giay", "30"))
        if ok:
            msg += cap_nhat_menu()
        return _ve_lai(msg, ok)

    return app
