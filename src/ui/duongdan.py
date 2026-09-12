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

import os

# ---------------------------------------------------------------- ma nguon
THU_MUC_MA_NGUON = "/opt/console-pi"

# ----------------------------------------------------------------- du lieu
# Cho phep doi bang bien moi truong (tien khi chay thu tren may khac, hoac
# khi muon de du lieu tren o USB gan ngoai).
THU_MUC_DU_LIEU = os.environ.get("CONSOLE_PI_DATA", "/var/lib/console-pi")


def _duong(*phan):
    return os.path.join(THU_MUC_DU_LIEU, *phan)


# Du lieu Deployment OS: anh Windows/Linux, phan mem, ung dung nhieu file,
# driver, script, kich ban, file boot. Day la thu muc NANG NHAT (nhieu GB).
DEPLOY_DIR = _duong("deploy")

# Kho file dung chung (tab "Kho file")
STORAGE_DIR = _duong("storage")

# Bang tra tham so cai dat im lang (tab "Tham so cai dat")
FILE_THAM_SO = _duong("tham-so-cai-dat.json")

# Thu vien lenh thiet bi mang cua nguoi dung (tab "Thu vien lenh")
FILE_THU_VIEN_LENH = _duong("command-library.json")

# Mat khau tai khoan Samba dung cho PXE deploy - install.sh tu sinh ngau
# nhien, quyen 600. De ben DU LIEU chu khong phai ben ma nguon vi no phai
# song sot qua cac lan cai lai code (neu mat, CSDL Samba va file khoa lech
# nhau -> WinPE khong ket noi duoc kho nua).
FILE_KHOA_SAMBA = _duong("samba-deploy.key")


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
