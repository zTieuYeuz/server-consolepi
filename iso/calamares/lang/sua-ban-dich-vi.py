#!/usr/bin/env python3
"""Sua ban dich tieng Viet cua Calamares 3.3.14 cho trinh cai Console System.

VI SAO CAN (22/09/2026, cai thu bang giao dien do hoa): ban dich goc
(lang/calamares_vi.ts cua Calamares) co loi hien ngay tren man hinh:
  - trang Nguoi dung: "Hay cho Vigo biet ten day du cua ban?" (chu "Vigo"
    la rac cua nguoi dich) va "Tu dang nhat" (sai chinh ta)
  - o "Yeu cau mat khau manh" duoc dich NGUOC nghia
  - "Package selection" dich thanh "Chon phan vung"
  - hop xac nhan truoc khi XOA DIA ("Continue with Installation?",
    "&Install Now", "Go &Back"), hop huy, tom tat phan vung, thong bao
    loi cai dat... con de nguyen tieng Anh (chua dich)
Khach hang nhin thay la mat tin tuong, nhat la o dung cho nguy hiem nhat
(xac nhan xoa dia).

Calamares doc /usr/share/calamares/lang/calamares_vi.qm TRUOC ban dich
nhung trong chuong trinh (xem tryLoad() trong Retranslator.cpp), nen chi
can dat file .qm da sua vao do.

Cach dung (tren may build, can goi qt6-l10n-tools):
    curl -fsSL -o /tmp/vi.ts \
      https://raw.githubusercontent.com/calamares/calamares/v3.3.14/lang/calamares_vi.ts
    python3 sua-ban-dich-vi.py /tmp/vi.ts /tmp/vi-sua.ts
    /usr/lib/qt6/bin/lrelease /tmp/vi-sua.ts -qm calamares_vi.qm
Doi phien ban Calamares thi phai lay lai .ts dung phien ban roi chay lai.
"""
import sys
import xml.etree.ElementTree as ET

# nguyen van (source) -> ban dich. Ap cho MOI context co cung nguyen van.
SUA = {
    # --- dich sai ---
    "What is your name?": "Họ và tên của bạn là gì?",
    "Log in automatically without asking for the password.":
        "Tự đăng nhập không cần mật khẩu.",
    "Your username is too long.": "Tên đăng nhập quá dài.",
    "'%1' is not allowed as username.": "Không được dùng '%1' làm tên đăng nhập.",
    "Package selection": "Chọn gói",
    "What is the name of this computer?": "Tên của máy tính này là gì?",
    "Your hostname is too short.": "Tên máy quá ngắn.",
    "Your hostname is too long.": "Tên máy quá dài.",
    "'%1' is not allowed as hostname.": "Không được dùng '%1' làm tên máy.",
    "No EFI system partition configured": "Chưa có phân vùng hệ thống EFI",
    "&Close": "Đón&g",
    # --- chua dich ---
    "%p%": "%p%",
    "Set Up": "Thiết lập",
    "Continue with Setup?": "Tiếp tục thiết lập?",
    "Continue with Installation?": "Tiếp tục cài đặt?",
    "&Set Up Now": "&Thiết lập ngay",
    "&Install Now": "&Cài đặt ngay",
    "Go &Back": "&Quay lại",
    "&Set Up": "&Thiết lập",
    "Cancel the setup process without changing the system.":
        "Huỷ thiết lập, không thay đổi gì trên máy.",
    "Cancel the installation process without changing the system.":
        "Huỷ cài đặt, không thay đổi gì trên máy.",
    "Cancel Setup?": "Huỷ thiết lập?",
    "Cancel Installation?": "Huỷ cài đặt?",
    "No swap": "Không dùng swap",
    "Reuse swap": "Dùng lại swap có sẵn",
    "Swap to file": "Swap bằng tệp",
    "Swap (no Hibernate)": "Phân vùng swap (không ngủ đông)",
    "Swap (with Hibernate)": "Phân vùng swap (có ngủ đông)",
    "Bootloader location:": "Nơi cài trình khởi động:",
    "The setup of %1 did not complete successfully.":
        "Thiết lập %1 chưa hoàn tất.",
    "The installation of %1 did not complete successfully.":
        "Cài đặt %1 chưa hoàn tất.",
    "The installation of %1 is complete.": "Đã cài xong %1.",
    "Keyboard model has been set to %1.": "Đã đặt kiểu bàn phím: %1.",
    "Keyboard layout has been set to %1/%2.": "Đã đặt bố cục bàn phím: %1/%2.",
    "Set timezone to %1.": "Đặt múi giờ: %1.",
    "Install option: <strong>%1</strong>": "Tuỳ chọn cài: <strong>%1</strong>",
    "None": "Không",
    "OK!": "OK!",
    "This computer does not satisfy the minimum requirements for setting up %1.<br/>Setup cannot continue.":
        "Máy tính này không đạt yêu cầu tối thiểu để thiết lập %1.<br/>Không thể tiếp tục.",
    "This computer does not satisfy the minimum requirements for installing %1.<br/>Installation cannot continue.":
        "Máy tính này không đạt yêu cầu tối thiểu để cài %1.<br/>Không thể tiếp tục cài đặt.",
    "Password must be a minimum of %1 characters.":
        "Mật khẩu phải có ít nhất %1 ký tự.",
    "&Change…": "&Đổi…",
    "Gathering system information…": "Đang thu thập thông tin máy…",
    "Install %1 <strong>alongside</strong> another operating system":
        "Cài %1 <strong>song song</strong> với hệ điều hành khác",
    "<strong>Erase</strong> disk and install %1":
        "<strong>Xoá</strong> đĩa và cài %1",
    "<strong>Replace</strong> a partition with %1":
        "<strong>Thay</strong> một phân vùng bằng %1",
    "<strong>Manual</strong> partitioning":
        "Phân vùng <strong>thủ công</strong>",
    "Install %1 <strong>alongside</strong> another operating system on disk <strong>%2</strong> (%3)":
        "Cài %1 <strong>song song</strong> với hệ điều hành khác trên đĩa <strong>%2</strong> (%3)",
    "<strong>Erase</strong> disk <strong>%2</strong> (%3) and install %1":
        "<strong>Xoá</strong> đĩa <strong>%2</strong> (%3) và cài %1",
    "<strong>Replace</strong> a partition on disk <strong>%2</strong> (%3) with %1":
        "<strong>Thay</strong> một phân vùng trên đĩa <strong>%2</strong> (%3) bằng %1",
    "<strong>Manual</strong> partitioning on disk <strong>%1</strong> (%2)":
        "Phân vùng <strong>thủ công</strong> trên đĩa <strong>%1</strong> (%2)",
    "Create a swap file.": "Tạo tệp swap.",
    "No partitions will be changed.": "Không phân vùng nào bị thay đổi.",
    "An EFI system partition is necessary to start %1.<br/><br/>To configure an EFI system partition, go back and select or create a suitable filesystem.":
        "Cần có phân vùng hệ thống EFI để khởi động %1.<br/><br/>Hãy quay lại, chọn hoặc tạo một phân vùng phù hợp.",
    "An EFI system partition is necessary to start %1.<br/><br/>The EFI system partition does not meet recommendations. It is recommended to go back and select or create a suitable filesystem.":
        "Cần có phân vùng hệ thống EFI để khởi động %1.<br/><br/>Phân vùng EFI hiện tại chưa đạt khuyến nghị. Nên quay lại, chọn hoặc tạo một phân vùng phù hợp.",
    "The filesystem must be mounted on <strong>%1</strong>.":
        "Phân vùng phải được gắn vào <strong>%1</strong>.",
    "The filesystem must have type FAT32.": "Phân vùng phải có định dạng FAT32.",
    "The filesystem must have flag <strong>%1</strong> set.":
        "Phân vùng phải bật cờ <strong>%1</strong>.",
    "The filesystem must be at least %1 MiB in size.":
        "Phân vùng phải lớn ít nhất %1 MiB.",
    "The minimum recommended size for the filesystem is %1 MiB.":
        "Kích thước khuyến nghị tối thiểu là %1 MiB.",
    "You can continue without setting up an EFI system partition but your system may fail to start.":
        "Bạn có thể tiếp tục mà không có phân vùng EFI, nhưng máy có thể không khởi động được.",
    "You can continue with this EFI system partition configuration but your system may fail to start.":
        "Bạn có thể tiếp tục với phân vùng EFI này, nhưng máy có thể không khởi động được.",
    "EFI system partition configured incorrectly": "Phân vùng EFI cấu hình sai",
    "EFI system partition recommendation": "Khuyến nghị về phân vùng EFI",
    "About %1 Setup": "Giới thiệu trình thiết lập %1",
    "About %1 Installer": "Giới thiệu trình cài đặt %1",
    "%1 Support": "Hỗ trợ %1",
    # --- trang Tong quan: mo ta tung thao tac se lam tren o dia. Day la
    # cho khach doc de biet o nao sap bi xoa - phai la tieng Viet ---
    "Creating new %1 partition table on %2…": "Tạo bảng phân vùng %1 mới trên %2…",
    "Creating new <strong>%1</strong> partition table on <strong>%2</strong> (%3)…":
        "Tạo bảng phân vùng <strong>%1</strong> mới trên <strong>%2</strong> (%3)…",
    "Create new %1MiB partition on %3 (%2) with entries %4":
        "Tạo phân vùng %1MiB mới trên %3 (%2) cho %4",
    "Create new %1MiB partition on %3 (%2)": "Tạo phân vùng %1MiB mới trên %3 (%2)",
    "Create new %2MiB partition on %4 (%3) with file system %1":
        "Tạo phân vùng %2MiB mới trên %4 (%3), định dạng %1",
    "Create new <strong>%1MiB</strong> partition on <strong>%3</strong> (%2) with entries <em>%4</em>":
        "Tạo phân vùng <strong>%1MiB</strong> mới trên <strong>%3</strong> (%2) cho <em>%4</em>",
    "Create new <strong>%1MiB</strong> partition on <strong>%3</strong> (%2)":
        "Tạo phân vùng <strong>%1MiB</strong> mới trên <strong>%3</strong> (%2)",
    "Create new <strong>%2MiB</strong> partition on <strong>%4</strong> (%3) with file system <strong>%1</strong>":
        "Tạo phân vùng <strong>%2MiB</strong> mới trên <strong>%4</strong> (%3), định dạng <strong>%1</strong>",
    "Creating new %1 partition on %2…": "Đang tạo phân vùng %1 mới trên %2…",
    "Set flags on partition %1": "Đặt cờ cho phân vùng %1",
    "Set flags on %1MiB %2 partition": "Đặt cờ cho phân vùng %2 %1MiB",
    "Set flags on new partition": "Đặt cờ cho phân vùng mới",
    "Set flags on partition <strong>%1</strong> to <strong>%2</strong>":
        "Đặt cờ <strong>%2</strong> cho phân vùng <strong>%1</strong>",
    "Set flags on %1MiB <strong>%2</strong> partition to <strong>%3</strong>":
        "Đặt cờ <strong>%3</strong> cho phân vùng <strong>%2</strong> %1MiB",
    "Set flags on new partition to <strong>%1</strong>":
        "Đặt cờ <strong>%1</strong> cho phân vùng mới",
    "Setting flags <strong>%2</strong> on partition <strong>%1</strong>…":
        "Đang đặt cờ <strong>%2</strong> cho phân vùng <strong>%1</strong>…",
    "Setting flags <strong>%3</strong> on %1MiB <strong>%2</strong> partition…":
        "Đang đặt cờ <strong>%3</strong> cho phân vùng <strong>%2</strong> %1MiB…",
    "Setting flags <strong>%1</strong> on new partition…":
        "Đang đặt cờ <strong>%1</strong> cho phân vùng mới…",
    "Install %1 on <strong>new</strong> %2 system partition":
        "Cài %1 lên phân vùng hệ thống %2 <strong>mới</strong>",
    "Install %1 on <strong>new</strong> %2 system partition with features <em>%3</em>":
        "Cài %1 lên phân vùng hệ thống %2 <strong>mới</strong>, tính năng <em>%3</em>",
    "Set up <strong>new</strong> %2 partition with mount point <strong>%1</strong>%3":
        "Tạo phân vùng %2 <strong>mới</strong> gắn vào <strong>%1</strong>%3",
    "Set up <strong>new</strong> %2 partition with mount point <strong>%1</strong> and features <em>%3</em>":
        "Tạo phân vùng %2 <strong>mới</strong> gắn vào <strong>%1</strong>, tính năng <em>%3</em>",
    "Install %2 on %3 system partition <strong>%1</strong>":
        "Cài %2 lên phân vùng hệ thống %3 <strong>%1</strong>",
    "Install %2 on %3 system partition <strong>%1</strong> with features <em>%4</em>":
        "Cài %2 lên phân vùng hệ thống %3 <strong>%1</strong>, tính năng <em>%4</em>",
    "Set up %3 partition <strong>%1</strong> with mount point <strong>%2</strong>%4…":
        "Dùng phân vùng %3 <strong>%1</strong>, gắn vào <strong>%2</strong>%4…",
    "Set up %3 partition <strong>%1</strong> with mount point <strong>%2</strong> and features <em>%4</em>":
        "Dùng phân vùng %3 <strong>%1</strong>, gắn vào <strong>%2</strong>, tính năng <em>%4</em>",
    "Install boot loader on <strong>%1</strong>…": "Cài trình khởi động lên <strong>%1</strong>…",
    "Setting up mount points…": "Đang gắn các phân vùng…",
    "Format partition %1 (file system: %2, size: %3 MiB) on %4":
        "Định dạng phân vùng %1 (%2, %3 MiB) trên %4",
    "Format <strong>%3MiB</strong> partition <strong>%1</strong> with file system <strong>%2</strong>":
        "Định dạng phân vùng <strong>%1</strong> <strong>%3MiB</strong> thành <strong>%2</strong>",
    "Formatting partition %1 with file system %2…": "Đang định dạng phân vùng %1 thành %2…",
    # --- cac buoc chay trong luc cai (dong trang thai duoi thanh tien do) ---
    "Clearing mounts for partitioning operations on %1…": "Đang tháo các phân vùng đang gắn trên %1…",
    "Clearing all temporary mounts…": "Đang tháo các điểm gắn tạm…",
    "Create user <strong>%1</strong>": "Tạo tài khoản <strong>%1</strong>",
    "Creating user %1…": "Đang tạo tài khoản %1…",
    "Setting file permissions…": "Đang đặt quyền tệp…",
    "Setting hostname %1…": "Đang đặt tên máy %1…",
    "Setting password for user %1…": "Đang đặt mật khẩu cho %1…",
    "Setting timezone to %1/%2…": "Đang đặt múi giờ %1/%2…",
    "Running shell processes…": "Đang chạy các bước thiết lập…",
    "Creating initramfs…": "Đang tạo initramfs…",
    "Running command %1 in target system…": "Đang chạy lệnh %1 trên hệ thống mới…",
    "Running command %1…": "Đang chạy lệnh %1…",
}

# Cau dai co the doi cho nhau: sua theo doan dau (chi nhung cau chac chan)
SUA_THEO_DAU = {
    # dich goc noi "chon muc nay thi DUOC dung mat khau yeu" - nguoc han
    "When this box is checked, password-strength checking is done":
        "Khi chọn mục này, mật khẩu sẽ được kiểm tra độ mạnh và bạn sẽ không thể dùng mật khẩu yếu.",
    # Trang Hoan thanh: ban goc viet thuong dau cau va moi "tiep tuc dung moi
    # truong USB" - trinh cai nay chay rieng, khong co moi truong nao de
    # dung tiep. Noi ro viec can lam: rut USB, khoi dong lai.
    "<h1>All done.</h1><br/>%1 has been installed on your computer.<br/>You may now restart":
        "<h1>Hoàn thành.</h1><br/>Đã cài xong %1.<br/>Hãy rút USB ra rồi khởi động lại máy để dùng hệ thống mới.",
    "<h1>Installation Failed</h1><br/>%1 has not been installed":
        "<h1>Cài đặt thất bại</h1><br/>Chưa cài được %1 lên máy.<br/>Thông báo lỗi: %2.",
}


def main(vao, ra):
    cay = ET.parse(vao)
    da_sua = set()
    for m in cay.getroot().iter("message"):
        src = m.find("source").text or ""
        moi = SUA.get(src)
        if moi is None:
            for dau, bd in SUA_THEO_DAU.items():
                if src.startswith(dau):
                    moi, src = bd, dau
                    break
        if moi is None:
            continue
        t = m.find("translation")
        if m.get("numerus") == "yes":
            continue  # chuoi so nhieu: khong dung o day
        t.text = moi
        t.attrib.pop("type", None)
        da_sua.add(src)
    thieu = (set(SUA) | set(SUA_THEO_DAU)) - da_sua
    if thieu:
        # nguyen van khong con trong .ts (doi phien ban Calamares?) - bao ra
        # de nguoi dung biet, khong am tham bo qua
        print("KHONG tim thay trong .ts:", *sorted(thieu), sep="\n  ", file=sys.stderr)
        sys.exit(1)
    cay.write(ra, encoding="utf-8", xml_declaration=True)
    print(f"da sua {len(da_sua)} chuoi -> {ra}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
