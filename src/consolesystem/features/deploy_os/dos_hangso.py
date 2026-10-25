# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Deploy OS - hang so dung chung: duoi file cho phep, danh sach OS, mui gio, ngon ngu, ban phim, ten cac buoc wizard.

(B4: tach nguyen van tu deployos.py; ten ham/hang giu nguyen, nguon van re-export.)"""
import os
from ui.duongdan import DEPLOY_DIR, BOOT_DIR, APPS_DIR, SCRIPTS_DIR, KICHBAN_DIR, OS_DIR, DRIVERS_DIR, UNGDUNG_DIR, FONTS_DIR, EXT_SCRIPT  # noqa: F401  (B3: khai bao o core/duongdan.py)



def _unattend():
    """Nap ui.unattend khi can (tranh vong import)."""
    from ui import unattend
    return unattend

APPS_META = os.path.join(APPS_DIR, "_thongtin.json")

# Con lai duoi muc nay thi khong cho tai them (giong ui/storage.py)
MIN_FREE_GB = 3

EXT_BOOT = {".iso", ".wim", ".esd", ".img", ".vhd", ".vhdx", ".efi", ".kpxe", ".ipxe"}

# Tab "WinPE" (truoc la "File boot", 03/10/2026): chi nhan va hien file WinPE
EXT_WINPE = {".wim", ".iso"}

EXT_APP = {".msi", ".exe"}

# ---------------------------------------------------------------- lua chon
KIEU_BOOT = [
    ("truc_tiep", "Boot OS trực tiếp với máy cần cài",
     "Cắm dây mạng THẲNG từ Pi sang máy cần cài. Pi tự cấp IP và chỉ đường "
     "boot. Không đụng chạm gì tới mạng của khách - chắc ăn nhất."),
    ("mang_khong_dhcp", "Boot OS qua mạng không có DHCP",
     "Pi và máy cần cài cùng cắm vào 1 switch, nhưng mạng đó KHÔNG có "
     "DHCP server nào. Pi đóng luôn vai trò cấp IP và chỉ đường boot."),
    ("mang_co_dhcp", "Boot OS qua mạng có sẵn DHCP",
     "Mạng đã có DHCP sẵn (router công ty). Pi chỉ chạy proxyDHCP - CHỈ "
     "trả lời 'file boot ở đâu', KHÔNG cấp IP, tránh đụng độ 2 DHCP."),
]

DANH_SACH_OS = [
    ("windows", "Windows", [("10", "Windows 10"), ("11", "Windows 11")]),
    ("linux", "Linux", [("ubuntu", "Ubuntu"), ("debian", "Debian")]),
]

MUI_GIO = [
    "Asia/Ho_Chi_Minh", "Asia/Bangkok", "Asia/Singapore", "Asia/Tokyo",
    "Asia/Seoul", "Asia/Shanghai", "UTC",
]

# Ngon ngu hien thi cua Windows (ma BCP-47 that su Windows dung cho
# <UILanguage>/<SystemLocale>).
#
# LUU Y QUAN TRONG (de tranh hieu nham): doi muc nay chi doi duoc neu
# BAN WINDOWS DANG CAI CO SAN goi ngon ngu do. Anh Windows tai ve
# thuong chi co 1 ngon ngu; chon tieng Viet tren 1 anh chi co en-US thi
# Windows se im lang quay ve en-US chu khong bao loi. Muon that su doi
# ngon ngu phai dung anh da tich hop goi ngon ngu do.
NGON_NGU = [
    ("en-US", "English (United States)"),
    ("vi-VN", "Tiếng Việt"),
    ("ja-JP", "日本語 (Nhật)"),
    ("ko-KR", "한국어 (Hàn)"),
    ("zh-CN", "中文 (Trung giản thể)"),
    ("fr-FR", "Français"),
    ("de-DE", "Deutsch"),
]

# Kieu ban phim (<InputLocale>). Khac han ngon ngu hien thi: day la cach
# cac phim tren ban phim duoc hieu, KHONG phu thuoc vao goi ngon ngu co
# trong anh hay khong, nen doi muc nay luon co tac dung.
#
# Tieng Viet KHONG co kieu ban phim rieng tren Windows - nguoi Viet go
# bang Unikey/EVKey tren ban phim US, nen mac dinh dung US la dung.
BAN_PHIM = [
    ("0409:00000409", "US - Mỹ (dùng cho tiếng Việt, Unikey/EVKey)"),
    ("0809:00000809", "United Kingdom - Anh"),
    ("040c:0000040c", "French - Pháp (AZERTY)"),
    ("0407:00000407", "German - Đức (QWERTZ)"),
    ("0411:00000411", "Japanese - Nhật"),
    ("0412:00000412", "Korean - Hàn"),
    ("0804:00000804", "Chinese Simplified - Trung"),
]

# Cac buoc cua trinh tu tu chon (dung chung cho ca 2 che do: chay ngay va
# luu thanh kich ban - chi khac o buoc cuoi)
#
# Buoc 1 "Kieu boot" DA BO (25/09/2026): che do mang gio chon 1 lan khi bat
# PXE (menu, may khach tu chon kich ban) - khong con thuoc tung kich ban.
# Giu nguyen SO buoc noi bo (2..7) de khong dung toi code tung buoc; chi
# danh so HIEN THI lai tu 1 (xem so_hien_thi).
TEN_BUOC = [
    (2, "Chọn OS"),
    (3, "Thông tin OS"),
    (4, "Phân chia ổ đĩa"),
    (5, "Phần mềm"),
    (6, "Chỉnh sửa cài đặt"),
    (7, "Tổng kết"),
]

# ------------------------------- ung dung THU MUC (mo hinh MDT: "Application
# with source files") - KHAC voi "Phan mem" o tren (1 file .msi/.exe suy tham
# so theo duoi): 1 ung dung o day la CA 1 THU MUC (bao nhieu file/thu muc con
# cung duoc) + 1 DONG LENH CAI TU DO nguoi dung tu go, dung y het cach
# Deployment Workbench cua MDT lam ("Source Files" + "Command line" + MDT tu
# cd vao dung thu muc do roi chay lenh). Sinh ra de dap ung cac bo cai nhieu
# file (vd Office 365 qua Office Deployment Tool: thu muc Office\ + setup.exe
# + configuration.xml) ma kieu "1 file" o tren khong the mo ta duoc.
EXT_UNGDUNG_ZIP = {".zip"}
