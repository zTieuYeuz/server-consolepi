# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi - NOI DUY NHAT khai bao duong dan.

VI SAO CO FILE NAY (van de that, khong phai don dep cho vui):

Truoc day MOI du lieu cua nguoi dung (phan mem tai len, anh Windows vai
GB, kich ban, thu vien lenh, kho file) deu nam TRON trong /opt/console-pi
- tuc la nam CHUNG voi ma nguon. Hai hau qua that:

  1. uninstall.sh co dong `rm -rf /opt/console-pi` - go cai dat 1 lan la
     mat sach bo cai Office 3.6GB, anh Windows, toan bo kich ban da dung
     cong suc tao ra. Khong co canh bao nao.
  2. Moi lan cai lai/nang cap tu GitHub deu phai nho "giu lai file nao,
     xoa file nao" bang 1 danh sach PRESERVE viet tay trong install.sh -
     quen 1 dong la mat du lieu.

CACH SUA: tach hai loai ra hai cho RIENG BIET, theo dung quy uoc Linux:

  /opt/console-pi/     = MA NGUON. Ghi de thoai mai, xoa cung duoc.
  /var/lib/console-pi/ = DU LIEU. Khong bao gio bi ban cai dat dung toi.

Nho vay "cai lai code" va "xoa du lieu" tro thanh hai viec KHAC NHAU,
khong con the lo tay lam nham.

Moi module deu import duong dan tu day, KHONG tu viet chuoi duong dan
rieng - de sau nay doi cho chi phai sua dung 1 file.
"""

import sys as _sys
_sys.modules["ui.duongdan"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import os

# ---------------------------------------------------------------- ma nguon
THU_MUC_MA_NGUON = "/opt/console-pi"
# Goc cua cay ma THAT dang chay (dev: src/ ; ban phat hanh: releases/<ban>/). Tai nguyen di kem ma (branding, pxe-boot, agent_bin...) tim theo day,
# KHONG theo vi tri file module (B2: module da chuyen vao consolesystem/... nen dem dirname tu __file__ o noi khac se sai).
GOC_MA = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR_UI = os.path.join(GOC_MA, "ui")                    # chua tai nguyen cu: agent_bin/, goi-driver.json
DIR_BRANDING = os.path.join(GOC_MA, "branding")
DIR_PXE_BOOT = os.path.join(GOC_MA, "pxe-boot")
DIR_NOVNC = os.path.join(GOC_MA, "nettools", "static", "novnc")
FILE_VERSION_DEV = os.path.join(GOC_MA, "..", "VERSION")     # cay phat trien: VERSION nam o goc repo, ngoai src/

# 2.0 (A3): co HAI bo cuc. Cu: du lieu o /var/lib/console-pi (lan secrets, pki) + vai file canh ma o /opt/console-pi.
# Moi: /var/lib/console-system/{config,secrets,pki,data,deploy,storage,...}. Dau ".bo-cuc-moi" trong thu muc goc = da chuyen
# (ghi CUOI CUNG boi ui/dichuyen.dua_ve_bo_cuc_moi). Chua co dau thi chay y nhu 1.9.5.
GOC_BO_CUC_CU = "/var/lib/console-pi"
GOC_BO_CUC_MOI = "/var/lib/console-system"


def _la_moi(goc):
    return os.path.exists(os.path.join(goc, ".bo-cuc-moi"))


_GOC_ENV = os.environ.get("CONSOLE_PI_DATA")
GOC = _GOC_ENV or (GOC_BO_CUC_MOI if _la_moi(GOC_BO_CUC_MOI) else GOC_BO_CUC_CU)
BO_CUC_MOI = _la_moi(GOC)
THU_MUC_DU_LIEU = os.path.join(GOC, "data") if BO_CUC_MOI else GOC


def _duong(*phan):
    return os.path.join(THU_MUC_DU_LIEU, *phan)


def _vt(cu, moi):
    """Vi tri theo bo cuc dang dung: cu = duong tuyet doi o bo cuc cu, moi = duong tuong doi trong thu muc goc moi."""
    return os.path.join(GOC, moi) if BO_CUC_MOI else cu




def _ma(*phan):
    return os.path.join(THU_MUC_MA_NGUON, *phan)


# A1 (2.0): moi duong dan CUNG truoc day rai trong ma deu khai bao o day. GIA TRI GIU NGUYEN (chua doi vi tri that).
# --- file/thu muc canh ma nguon (se chuyen sang bo cuc moi o buoc A3)
FILE_CONFIG = _vt(_ma("config.json"), "config/config.json")
FILE_FLASK_SECRET = _vt(_ma("flask-secret.key"), "secrets/flask-secret.key")
FILE_VERSION = _ma("VERSION")
FILE_VERSION_TXT = _ma("version.txt")
FILE_XOAY_MAN_HINH = _vt(_ma("screen-rotation"), "config/screen-rotation")
FILE_TEN_CONG = _vt(_ma("port-names.json"), "config/port-names.json")
FILE_FORCE_AP = _vt(_ma("force-ap.flag"), "config/force-ap.flag")
FILE_MAC_SPOOF = _vt(_ma("wifi-mac-spoof.flag"), "config/wifi-mac-spoof.flag")
SCRIPT_WIFI_FALLBACK = _ma("scripts", "wifi-fallback.sh")
DIR_DRIVER_SAN = _ma("driver-san")
DIR_CAPTURES = _vt(_ma("captures"), "data/captures")
DIR_BACKUPS = _vt(_ma("backups"), "data/thiet-bi-backups")      # sao luu cau hinh THIET BI MANG (khac backups/ cua he thong)
DIR_TFTP = _vt(_ma("tftp"), "data/tftp")
FILE_IFTHEN = _vt(_ma("nettools", "ifthen-rules.json"), "config/ifthen-rules.json")
# --- trang thai tam (chi ton tai luc may chay)
FLAG_DIRECT = "/run/console-pi-direct.flag"
FLAG_PXE = "/run/console-pi-pxe.flag"
FLAG_TFTP = "/run/console-system-tftp.flag"
FILE_BT_STATE = "/run/console-pi-bt.json"
FILE_BOOT_STATUS = "/run/console-pi-boot-status.json"
# --- nhat ky kiem toan
LOG_DHCPTEST = "/var/log/console-pi-dhcptest.log"
LOG_NETMIKO = "/var/log/console-pi-netmiko.log"

# ----------------------------------------------------------------- du lieu
# Cho phep doi bang bien moi truong (tien khi chay thu tren may khac, hoac
# khi muon de du lieu tren o USB gan ngoai).


# Du lieu Deployment OS: anh Windows/Linux, phan mem, ung dung nhieu file,
# driver, script, kich ban, file boot. Day la thu muc NANG NHAT (nhieu GB).
DEPLOY_DIR = os.path.join(GOC, "deploy")

# Thu muc con cua DEPLOY (B3: gom o day de moi tinh nang dung chung, khong phai import deployos chi de lay duong dan)
BOOT_DIR = os.path.join(DEPLOY_DIR, "boot")
APPS_DIR = os.path.join(DEPLOY_DIR, "apps")
SCRIPTS_DIR = os.path.join(DEPLOY_DIR, "scripts")
KICHBAN_DIR = os.path.join(DEPLOY_DIR, "kichban")
OS_DIR = os.path.join(DEPLOY_DIR, "os")
DRIVERS_DIR = os.path.join(DEPLOY_DIR, "drivers")
UNGDUNG_DIR = os.path.join(DEPLOY_DIR, "ungdung")
FONTS_DIR = os.path.join(DEPLOY_DIR, "fonts")      # moi "bo font" = 1 thu muc
EXT_SCRIPT = {".bat", ".ps1", ".cmd"}                # duoi file script cai dat duoc phep

# Kho file dung chung (tab "Kho file")
STORAGE_DIR = os.path.join(GOC, "storage")

# Bang tra tham so cai dat im lang (tab "Tham so cai dat")

# Danh dau cac goi driver nhung SAN trong ISO da nap roi (xem goidriver.nap_san) -
# nguoi dung xoa goi thi KHONG tu nap lai
FILE_DRIVER_SAN = _duong("driver-san.da-nap.json")

# Thu vien lenh thiet bi mang cua nguoi dung (tab "Thu vien lenh")
FILE_THU_VIEN_LENH = _vt(_duong("command-library.json"), "config/command-library.json")

# Mat khau tai khoan Samba dung cho PXE deploy - install.sh tu sinh ngau
# nhien, quyen 600. De ben DU LIEU chu khong phai ben ma nguon vi no phai
# song sot qua cac lan cai lai code (neu mat, CSDL Samba va file khoa lech
# nhau -> WinPE khong ket noi duoc kho nua).
FILE_KHOA_SAMBA = _vt(_duong("samba-deploy.key"), "secrets/samba-deploy.key")

# Cau hinh ket noi Kho luu tru trung tam (URL + token rieng cua Pi nay) -
# xem ui/khotrungtam.py. Token la bi mat, de ben DU LIEU (khong phai ma
# nguon) vi cung ly do voi FILE_KHOA_SAMBA o tren.
FILE_KHO_TRUNGTAM = _vt(_duong("kho-trungtam.json"), "secrets/kho-trungtam.json")

# Thong tin dang nhap Cloudflare Access cho Kho trung tam (bi mat)
FILE_CF_ACCESS = _vt(_duong("cf-access.json"), "secrets/cf-access.json")

# Khoa RIENG CUA MAY de boc khoa giai ma goi cap nhat (kho cap luc dang ky, qua kenh ma hoa X25519) - xem capnhat/may.py
FILE_KHOA_MAY = _vt(_duong("khoa-may.key"), "secrets/khoa-may.key")
# Thu muc cap nhat: trang thai kiem tra, cong viec nang cap, goi da tai, ban sao luu truoc khi nang cap (bo cuc moi: <goc>/updates)
DIR_CAP_NHAT = os.path.join(GOC, "updates")

# Chia khoa ma hoa tai khoan Trien khai + thu muc PKI (chung chi/khoa CA)
FILE_TK_KHOA = _vt(_duong("trienkhai", ".khoa"), "secrets/trienkhai.khoa")
DIR_PKI = _vt(_duong("trienkhai", "pki"), "pki")


def bao_dam_thu_muc_du_lieu():
    """
    Tao san thu muc du lieu neu chua co. Goi truoc khi ghi file dau tien.

    Quyen 755: dich vu web chay quyen root nen doc/ghi duoc, con tien trinh
    Samba (chay quyen "nobody") chi can DOC de phuc vu WinPE lay file.
    """
    try:
        os.makedirs(THU_MUC_DU_LIEU, mode=0o755, exist_ok=True)
        return True
    except OSError:
        return False


def pxe_dang_bat():
    """PXE dang chay? (co file co /run/console-pi-pxe.flag) - nguon su that duy nhat, tinh nang nao cung hoi duoc ma khong import pxe."""
    return os.path.exists(FLAG_PXE)
