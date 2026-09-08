"""
Console Pi - Phat PXE that (giai doan ke tiep cua Deployment OS)

Tiep noi module ui/deployos.py: chinh la phan "cau hinh PXE cua dnsmasq" ma
kiem_tra_san_sang() trong deployos.py bao la "chua dung - GIAI DOAN KE
TIEP". File nay lam cho no thanh THAT.

CO CHE PXE (da kiem chung tung phan qua man dnsmasq + wimlib, khong doan):
  1. May can cai boot, gui broadcast DHCP.
  2. dnsmasq (file nay dieu khien) tra IP + noi lay bootloader qua TFTP:
     - May kien truc BIOS (client-arch=0)      -> undionly.kpxe
     - May kien truc UEFI x64 (client-arch=7/9)-> ipxe.efi
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
DON_VI_SYSTEMD = "console-pi-pxe"

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
        return False, "Chua co boot.wim - tai len o tab 2.1 File boot truoc."

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
            return False, f"Khong trich duoc {ten_luu}: {out[-200:]}"
        # wimlib giu nguyen ten goc (bootmgr.exe/wdsmgfw.efi) - da dung ten
        # do lam TEN_LUU nen khong can doi ten. Chi kiem tra co that khong.
        if not os.path.isfile(dich):
            return False, f"Trich xong nhung khong thay {ten_luu} tai {dich}."
        ket_qua.append(ten_luu)
    return True, f"Da trich {', '.join(ket_qua)} tu boot.wim."


def _co_bcd():
    return os.path.isfile(_duong(TEN_BCD_BIOS)) and os.path.isfile(_duong(TEN_BCD_UEFI))


def trang_thai_chuan_bi():
    """
    Danh sach (dat, nhan, chi_tiet) - PHAN NOI TIEP kiem_tra_san_sang() cua
    deployos.py, kiem tra rieng cac dieu kien PXE THAT SU can de bat duoc.
    """
    ra = []
    co_ipxe_tftp = os.path.isfile(_duong("undionly.kpxe")) and os.path.isfile(_duong("ipxe.efi"))
    ra.append((co_ipxe_tftp, "Bootloader iPXE (BIOS + UEFI)",
               "Da co ca undionly.kpxe va ipxe.efi" if co_ipxe_tftp else
               "Thieu - tai len o tab 2.1 File boot"))

    co_wimboot = os.path.isfile(_duong("wimboot"))
    ra.append((co_wimboot, "wimboot",
               "Da co" if co_wimboot else "Thieu - tai len o tab 2.1 File boot"))

    ra.append((_co_bootmgr_pxe(), "bootmgr.exe + wdsmgfw.efi (trich tu boot.wim)",
               "Da trich" if _co_bootmgr_pxe() else
               "Chua trich - bam nut 'Trich bootmgr tu boot.wim' ben duoi"))

    ra.append((_co_bcd(), "File BCD (tu ISO goc)",
               "Da co" if _co_bcd() else
               "CHUA CO - can lay tu goc ISO (thu muc boot/bcd va "
               "efi/microsoft/boot/bcd), khong nam san trong boot.wim. "
               "Tai lai ISO va bam nut lay BCD."))
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
    return f"""#!ipxe
kernel {goc}/wimboot
initrd {goc}/boot.wim    boot.wim
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

    if kieu_boot == "mang_co_dhcp":
        mang, prefix = _mang_that(IFACE)
        if not mang:
            return False, (f"Khong doc duoc dia chi IP that cua {IFACE} - "
                           f"kiem tra da cam day mang va co IP chua.")
        dhcp_range = f"dhcp-range={mang},proxy"
        dong_gateway = ""     # proxyDHCP khong cap IP nen khong can khai bao gateway
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
# tai lai chinh no). Dat SAU cac dong tag:bios/efi-x64 de dnsmasq uu tien
# dong nay khi ca 2 dieu kien deu dung (may da chay iPXE VA la UEFI/BIOS).
dhcp-userclass=set:ipxe,iPXE
dhcp-boot=tag:bios,undionly.kpxe
dhcp-boot=tag:efi-x64,ipxe.efi
dhcp-boot=tag:ipxe,http://{dia_chi_pi}:80/deployos/pxeboot/menu.ipxe

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


def bat_pxe(kieu_boot="truc_tiep"):
    if dang_bat():
        return True, "PXE dang bat san."
    if not san_sang_bat():
        return False, "Chua du dieu kien (xem bang 'San sang PXE' ben tren)."

    if kieu_boot == "mang_co_dhcp" and not _mang_that(IFACE)[0]:
        return False, (f"Chua doc duoc dia chi IP that cua {IFACE} - kiem "
                       f"tra da cam day mang vao mang co DHCP chua.")

    if not _ghi_menu_ipxe(kieu_boot):
        return False, "Khong ghi duoc script iPXE."

    ok, err = _ghi_dnsmasq_conf(kieu_boot)
    if not ok:
        return False, f"Khong ghi duoc cau hinh dnsmasq: {err}"

    if kieu_boot != "mang_co_dhcp":
        # Che do tu cap IP: can chiem han eth0, giong het direct.py
        _sh(["nmcli", "device", "set", IFACE, "managed", "no"])
        _sh(["ip", "addr", "flush", "dev", IFACE])
        ok, out = _sh(["ip", "addr", "add", PI_CIDR, "dev", IFACE])
        if not ok and "File exists" not in out:
            _sh(["nmcli", "device", "set", IFACE, "managed", "yes"])
            return False, f"Khong dat duoc IP tinh cho {IFACE}: {out[:150]}"
        _sh(["ip", "link", "set", IFACE, "up"])

    ok, out = _sh(["systemctl", "restart", DON_VI_SYSTEMD])
    if not ok:
        if kieu_boot != "mang_co_dhcp":
            _sh(["nmcli", "device", "set", IFACE, "managed", "yes"])
        return False, f"Khong bat duoc dich vu PXE: {out[:200]}"

    open(STATE_FLAG, "w").write(kieu_boot)
    return True, ("Da bat PXE. Cam day mang tu Pi sang may can cai (hoac qua "
                  "chung 1 switch neu dung kieu 'mang co DHCP'), vao BIOS/UEFI "
                  "may do chon boot qua mang (Network Boot / PXE Boot).")


def tat_pxe():
    if not dang_bat():
        return True, "PXE von da tat."
    _sh(["systemctl", "stop", DON_VI_SYSTEMD])
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
    return True, f"Da tat PXE, tra {IFACE} ve binh thuong."


# ==================================================================== web
def register_pxe(app):
    from flask import request, redirect, send_from_directory, abort
    from .layout import render_page
    from .home import _esc

    EXT_PHUC_VU = {".kpxe", ".efi", ".ipxe", ".wim", ".exe", "", }
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
        return send_from_directory(_d.BOOT_DIR, ten_sach)

    @app.route("/deployos/pxe/trich-bootmgr", methods=["POST"])
    def deployos_pxe_trich():
        ok, msg = trich_bootmgr_tu_winpe()
        return redirect("/deployos/boot")

    @app.route("/deployos/pxe/bat", methods=["POST"])
    def deployos_pxe_bat():
        kieu = request.form.get("kieu_boot", "truc_tiep")
        ok, msg = bat_pxe(kieu)
        return redirect("/deployos/boot")

    @app.route("/deployos/pxe/tat", methods=["POST"])
    def deployos_pxe_tat():
        ok, msg = tat_pxe()
        return redirect("/deployos/boot")

    return app
