# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Unattend - danh sach TUY CHON Windows (registry/lenh) va domain.

(B4: tach nguyen van tu unattend.py; ten ham/hang giu nguyen, nguon van re-export.)"""
from consolesystem.core.esc import esc_xml as _esc



# =====================================================================
# TUY CHON WINDOWS SAU KHI CAI (mo hinh MDT: "Task Sequence" co san cac
# buoc thiet lap thay vi bat nguoi dung tu viet script)
#
# MOT NGUON SU THAT DUY NHAT: giao dien (ui/deployos.py buoc 6) doc
# chinh bang nay de ve o tich, va sinh_unattend_offline_xml() cung doc
# chinh bang nay de sinh lenh - khong the lech nhau.
#
# Moi muc: (ma, nhan hien thi, mo ta, pha, [cac lenh])
#   pha = "may"       -> chay o pass specialize, quyen SYSTEM, TRUOC khi
#                        co nguoi dang nhap (thiet lap cap may)
#   pha = "ho_so"     -> thiet lap giao dien (HKCU) cho MOI tai khoan: ghi vao
#                        ho so mac dinh (C:\Users\Default) o pass specialize,
#                        TRUOC khi tao tai khoan nao -> tai khoan dau tien va
#                        moi tai khoan tao sau deu nhan (xem _lenh_ho_so_mac_dinh).
#                        Anh Thoai 03/10/2026: "ap dung cho nguoi dung dang
#                        nhap dau tien" phai ap dung duoc cho ca may.
#   pha = "nguoi_dung"-> chay o lan dang nhap dau (can mang / can phien
#                        Windows) nhung tac dung CAP MAY (.NET 3.5, loi tat
#                        Edge chung).
# =====================================================================
TUY_CHON_WINDOWS = [
    ("rdp", "Bật Remote Desktop",
     "Cho phép nối từ xa qua RDP và mở sẵn cổng trên tường lửa", "may", [
         r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server"'
         r' /v fDenyTSConnections /t REG_DWORD /d 0 /f',
         'netsh advfirewall firewall set rule group="remote desktop"'
         ' new enable=Yes',
     ]),
    ("ping", "Cho phép ping tới máy này",
     "Mở ICMP vào - rất cần khi đi kiểm tra mạng", "may", [
         'netsh advfirewall firewall add rule name="ICMPv4 vao"'
         ' protocol=icmpv4:8,any dir=in action=allow',
     ]),
    ("khong_ngu", "Không tự động ngủ / tắt màn hình",
     "Đặt thời gian chờ về 0 khi cắm điện - hợp cho máy để bàn làm việc lâu", "may", [
         "powercfg /change standby-timeout-ac 0",
         "powercfg /change monitor-timeout-ac 0",
         "powercfg /change hibernate-timeout-ac 0",
     ]),
    ("tat_fast_startup", "Tắt Fast Startup",
     "Để lệnh Shut down tắt máy THẬT SỰ - tránh lỗi thiết bị cắm ngoài",
     "may", [
         r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Power"'
         r' /v HiberbootEnabled /t REG_DWORD /d 0 /f',
     ]),
    ("tat_uac", "Tắt UAC (hộp hỏi quyền)",
     "GIẢM AN TOÀN - chỉ dùng cho máy thử nghiệm / phòng lab", "may", [
         r'reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"'
         r' /v EnableLUA /t REG_DWORD /d 0 /f',
     ]),
    ("tat_telemetry", "Giảm thu thập dữ liệu (telemetry)",
     "Đặt mức thấp nhất mà bản Windows đó cho phép", "may", [
         r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection"'
         r' /v AllowTelemetry /t REG_DWORD /d 0 /f',
     ]),
    ("hien_duoi_file", "Hiện phần mở rộng tập tin",
     "Thấy .exe .bat .pdf... thay vì giấu đi", "ho_so", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"'
         r' /v HideFileExt /t REG_DWORD /d 0 /f',
     ]),
    ("hien_file_an", "Hiện tập tin ẩn",
     "Hiện cả file/thư mục bị đánh dấu ẩn", "ho_so", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"'
         r' /v Hidden /t REG_DWORD /d 1 /f',
     ]),

    # ---- Bo sung dot 2 (tham khao schneegans.de/windows/unattend-generator)
    # Chi lay nhung muc THUC SU huu ich cho may cai tai hien truong, bo qua
    # cac muc trang tri (mau sac, hinh nen, hieu ung) va cac muc nguy hiem
    # (tat hoan toan Defender, tat SmartScreen o muc he thong).

    ("tat_bitlocker", "Không tự mã hoá ổ đĩa (BitLocker)",
     "RẤT NÊN BẬT khi cài máy cho người khác: Windows 11 tự bật mã hoá ổ và "
     "gắn khoá vào tài khoản Microsoft - máy hỏng mà không có khoá là mất "
     "sạch dữ liệu, cứu cũng không được", "may", [
         r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\BitLocker"'
         r' /v PreventDeviceEncryption /t REG_DWORD /d 1 /f',
     ]),
    ("tat_windows_update", "Tắt Windows Update tự động",
     "Máy không tự tải bản cập nhật và tự khởi động lại giữa giờ làm. "
     "Đổi lại phải tự cập nhật định kỳ, nếu không sẽ thiếu vá lỗi bảo mật",
     "may", [
         r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"'
         r' /v NoAutoUpdate /t REG_DWORD /d 1 /f',
     ]),
    ("bat_duong_dan_dai", "Cho phép đường dẫn dài hơn 260 ký tự",
     "Hết lỗi copy báo \"tên file quá dài\" khi thư mục lồng nhau nhiều tầng",
     "may", [
         r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem"'
         r' /v LongPathsEnabled /t REG_DWORD /d 1 /f',
     ]),
    ("tat_system_restore", "Tắt System Restore",
     "Không giữ điểm khôi phục - tiết kiệm vài GB ổ đĩa. Chỉ nên dùng cho "
     "máy đã có cách sao lưu khác", "may", [
         'powershell -NoProfile -ExecutionPolicy Bypass -Command '
         '"Disable-ComputerRestore -Drive C:\\"',
     ]),
    ("hieu_suat_cao", "Đặt nguồn điện ở mức Hiệu suất cao",
     "CPU không hạ xung để tiết kiệm điện - máy phản hồi nhanh hơn, tốn "
     "điện hơn. Hợp cho máy bàn cắm điện liên tục", "may", [
         "powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
     ]),
    ("tat_bing_start", "Tắt tìm kiếm Bing trong menu Start",
     "Gõ tìm chương trình thì chỉ tìm trong máy, không lẫn kết quả web",
     "ho_so", [
         r'reg add "HKCU\Software\Policies\Microsoft\Windows\Explorer"'
         r' /v DisableSearchBoxSuggestions /t REG_DWORD /d 1 /f',
     ]),
    ("mo_this_pc", "Mở Explorer vào This PC thay vì Quick Access",
     "Bấm vào Explorer là thấy ngay danh sách ổ đĩa", "ho_so", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"'
         r' /v LaunchTo /t REG_DWORD /d 1 /f',
     ]),
    ("menu_chuot_cu", "Menu chuột phải kiểu cũ (Windows 11)",
     "Bỏ menu rút gọn của Windows 11, hiện thẳng menu đầy đủ như Windows 10 - "
     "không phải bấm thêm \"Show more options\". Không ảnh hưởng Windows 10",
     "ho_so", [
         r'reg add "HKCU\Software\Classes\CLSID'
         r'\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}'
         r'\InprocServer32" /f /ve',
     ]),
    ("taskbar_trai", "Thanh tác vụ căn trái (Windows 11)",
     "Nút Start về góc trái như Windows 10. Không ảnh hưởng Windows 10",
     "ho_so", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"'
         r' /v TaskbarAl /t REG_DWORD /d 0 /f',
     ]),
    # LOI THAT (lab Win11 24H2, 26/09/2026): ghi HKCU ...\TaskbarDa bi Windows
    # 11 moi CHAN (driver UCPD bao ve khoa nay) -> "Ma loi: 1". Dung CHINH
    # SACH may (pha "may", quyen quan tri): Dsh\AllowNewsAndInterests cho
    # Windows 11, "Windows Feeds"\EnableFeeds cho tin tuc/thoi tiet Windows 10.
    ("tat_widgets", "Tắt Widgets / bảng tin thời tiết",
     "Bỏ ô thời tiết - tin tức trên thanh tác vụ", "may", [
         r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Dsh"'
         r' /v AllowNewsAndInterests /t REG_DWORD /d 0 /f',
         r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Feeds"'
         r' /v EnableFeeds /t REG_DWORD /d 0 /f',
     ]),
    ("tat_goi_y_app", "Tắt gợi ý ứng dụng và quảng cáo",
     "Windows không tự cài app gợi ý, không hiện quảng cáo trong Start và "
     "màn hình khoá", "ho_so", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion'
         r'\ContentDeliveryManager" /v SilentInstalledAppsEnabled'
         r' /t REG_DWORD /d 0 /f',
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion'
         r'\ContentDeliveryManager" /v SubscribedContent-338388Enabled'
         r' /t REG_DWORD /d 0 /f',
     ]),

    # ---- Bo sung dot 3
    ("hien_icon_desktop", "Hiện This PC và Network ngoài desktop",
     "Bỏ desktop trống trơn - có sẵn biểu tượng máy tính và mạng để bấm vào",
     "ho_so", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer'
         r'\HideDesktopIcons\NewStartPanel"'
         r' /v {20D04FE0-3AEA-1069-A2D8-08002B30309D} /t REG_DWORD /d 0 /f',
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer'
         r'\HideDesktopIcons\NewStartPanel"'
         r' /v {F02C1A0D-BE21-4350-88B0-7367FC96EF3C} /t REG_DWORD /d 0 /f',
     ]),
    ("uu_tien_hieu_nang", "Ưu tiên hiệu năng thay vì giao diện đẹp",
     "Tắt hiệu ứng mờ, đổ bóng, cửa sổ bay - máy cũ / máy yếu chạy mượt hơn "
     "rõ rệt", "ho_so", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer'
         r'\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 2 /f',
     ]),
    ("tat_tu_khoi_dong_lai", "Không tự khởi động lại khi có người đang dùng",
     "Windows Update không được tự khởi động lại máy khi còn người đăng "
     "nhập - tránh mất việc đang làm dở", "may", [
         r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"'
         r' /v NoAutoRebootWithLoggedOnUsers /t REG_DWORD /d 1 /f',
     ]),
    ("bat_net_framework35", "Bật .NET Framework 3.5 (tải qua mạng)",
     "Nhiều phần mềm kế toán, phần mềm quản lý cũ bắt buộc phải có. "
     "Máy TỰ TẢI gói này từ Windows Update nên cần Internet — chỉ chạy "
     "sau khi đã vào Windows, không làm chậm lúc cài. Không có mạng thì "
     "bước này báo lỗi rồi đi tiếp, không làm hỏng các bước sau",
     "nguoi_dung", [
         # CHAY O PHA NGUOI DUNG, KHONG PHAI PHA MAY - day la diem mau chot.
         #
         # LOI THAT DA GAP (12/09/2026, anh Thoai chup man hinh): lenh nay
         # truoc day chay o pha `specialize`. DISM di hoi Windows Update de
         # tai goi ve, mang cham -> dung im o "Enabling feature(s) 5.9%"
         # HANG GIO (CPU 2%, dia 0%, mang 0 Kbps). Vi specialize chay DONG
         # BO nen ca qua trinh cai Windows treo cung o man "Getting ready",
         # khong co cach nao biet chuyen gi dang xay ra.
         #
         # Hai thu da doi han tinh chat cua no:
         #   1. Chuyen sang pha nguoi_dung: luc do Windows da vao desktop,
         #      mang that su hoat dong (day chinh la ly do anh Thoai muon
         #      doi sang ban "online"), va treo cung khong chan viec boot.
         #   2. Chay trong tien-trinh.ps1 nen co GIOI HAN THOI GIAN va
         #      hien ro tren cua so tien trinh - qua gio thi bi dung va
         #      di tiep, khong con treo vo han duoc nua.
         # Vi vay KHONG con /limitaccess: gio cho phep no tai that.
         "dism /online /enable-feature /featurename:NetFx3 /all /norestart",
     ]),
    ("tat_ipv6", "Tắt IPv6 trên mọi card mạng",
     "CHỈ dùng khi hệ thống mạng của anh chưa chạy IPv6 và IPv6 gây chậm "
     "phân giải tên. Mạng có IPv6 thật thì đừng bật mục này", "may", [
         r'reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters"'
         r' /v DisabledComponents /t REG_DWORD /d 255 /f',
     ]),
    ("bat_admin_shares", "Mở chia sẻ quản trị qua mạng (C$, ADMIN$)",
     "Cho phép vào ổ đĩa máy này từ xa bằng \\\\tên-máy\\c$ - tiện khi đi "
     "hỗ trợ từ xa. GIẢM AN TOÀN nếu máy nằm ở mạng không tin cậy", "may", [
         r'reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies'
         r'\System" /v LocalAccountTokenFilterPolicy /t REG_DWORD /d 1 /f',
     ]),
    ("tat_man_hinh_khoa", "Bỏ màn hình khoá, vào thẳng ô đăng nhập",
     "Không phải bấm/vuốt một lần thừa trước khi nhập mật khẩu", "may", [
         r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Personalization"'
         r' /v NoLockScreen /t REG_DWORD /d 1 /f',
     ]),
    ("tat_cortana", "Tắt Cortana",
     "Tắt trợ lý ảo - đỡ tốn tài nguyên và không gửi nội dung tìm kiếm ra "
     "ngoài", "may", [
         r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search"'
         r' /v AllowCortana /t REG_DWORD /d 0 /f',
     ]),
    ("ps_chay_script", "Cho phép chạy script PowerShell",
     "Đặt ExecutionPolicy về RemoteSigned - chạy được script .ps1 tự viết "
     "mà không phải gõ lệnh mở khoá mỗi lần", "may", [
         "powershell -NoProfile -Command "
         "\"Set-ExecutionPolicy RemoteSigned -Scope LocalMachine -Force\"",
     ]),

    # ---- Bo sung dot 4: doi chieu voi schneegans.de/windows/unattend-
    # generator, lay nhung muc CON THIEU ma thuc su co ich khi cai may tai
    # hien truong. Van bo qua cac muc trang tri (mau nhan, hinh nen, 15
    # hieu ung dong rieng le) va cac muc pha an toan (tat han Defender,
    # siet ACL o dia C:).

    ("bat_numlock", "Bật sẵn Num Lock khi khởi động",
     "Khỏi phải bấm Num Lock mỗi lần bật máy mới gõ được số ở bàn phím "
     "phải. Thứ nhỏ nhưng ngày nào cũng gặp", "ho_so", [
         # 2 = Num Lock bat. Dat o .DEFAULT nen ap dung ca man hinh dang
         # nhap, khong chi sau khi vao desktop.
         r'reg add "HKU\.DEFAULT\Control Panel\Keyboard"'
         r' /v InitialKeyboardIndicators /t REG_SZ /d 2 /f',
         r'reg add "HKCU\Control Panel\Keyboard"'
         r' /v InitialKeyboardIndicators /t REG_SZ /d 2 /f',
     ]),
    ("tat_edge_lan_dau", "Bỏ màn hình chào của Edge lần đầu mở",
     "Mở Edge là vào thẳng, không phải bấm qua 4-5 trang giới thiệu và "
     "hỏi đồng bộ. Rất được việc khi giao máy cho người dùng", "may", [
         r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Edge"'
         r' /v HideFirstRunExperience /t REG_DWORD /d 1 /f',
     ]),
    ("tat_edge_chay_ngam", "Không cho Edge chạy ngầm khi đã đóng",
     "Tắt Startup Boost và chạy nền - Edge không còn ngốn RAM khi anh "
     "không dùng tới. Hợp với máy cấu hình thấp", "may", [
         r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Edge"'
         r' /v StartupBoostEnabled /t REG_DWORD /d 0 /f',
         r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Edge"'
         r' /v BackgroundModeEnabled /t REG_DWORD /d 0 /f',
     ]),
    ("xoa_loi_tat_edge", "Xoá lối tắt Edge trên desktop",
     "Windows tự tạo lối tắt Edge ngoài desktop dù người dùng không xin. "
     "Xoá đi cho desktop sạch", "nguoi_dung", [
         r'cmd /c del /q "%PUBLIC%\Desktop\Microsoft Edge.lnk"'
         r' "%USERPROFILE%\Desktop\Microsoft Edge.lnk" 2>nul',
     ]),
    ("tat_smartscreen", "Tắt SmartScreen",
     "Bỏ hộp thoại chặn \"Windows protected your PC\" khi chạy phần mềm "
     "tải về. GIẢM AN TOÀN - chỉ nên bật cho máy thử nghiệm hoặc máy chỉ "
     "chạy phần mềm nội bộ đã tin cậy", "may", [
         r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\System"'
         r' /v EnableSmartScreen /t REG_DWORD /d 0 /f',
         r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Edge"'
         r' /v SmartScreenEnabled /t REG_DWORD /d 0 /f',
     ]),
    ("tat_am_thanh", "Tắt âm thanh hệ thống",
     "Máy không kêu \"beng\" mỗi lần có thông báo hay cắm/rút USB. Hợp "
     "cho máy đặt ở quầy, phòng họp, phòng máy", "ho_so", [
         r'reg add "HKCU\AppEvents\Schemes" /ve /t REG_SZ /d ".None" /f',
     ]),
    ("hien_het_khay", "Luôn hiện mọi biểu tượng khay hệ thống",
     "Không giấu biểu tượng vào mũi tên nữa - thấy ngay phần mềm nào "
     "đang chạy. Rất cần khi đi kiểm tra máy cho người khác",
     "ho_so", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer"'
         r' /v EnableAutoTray /t REG_DWORD /d 0 /f',
     ]),
    ("an_nut_taskview", "Ẩn nút Task View trên thanh tác vụ",
     "Bớt một nút ít dùng, thanh tác vụ gọn hơn", "ho_so", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"'
         r' /v ShowTaskViewButton /t REG_DWORD /d 0 /f',
     ]),
    ("thu_o_tim_kiem", "Thu nhỏ ô tìm kiếm thành biểu tượng",
     "Ô tìm kiếm dài chiếm gần nửa thanh tác vụ - thu lại thành một biểu "
     "tượng nhỏ, còn chỗ cho cửa sổ đang mở", "ho_so", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Search"'
         r' /v SearchboxTaskbarMode /t REG_DWORD /d 1 /f',
     ]),
    ("tat_mo_ta_thu_muc", "Tắt bảng chú thích khi rê chuột vào thư mục",
     "Bỏ ô vàng hiện ra che mất tên file khi rê chuột", "ho_so", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"'
         r' /v ShowInfoTip /t REG_DWORD /d 0 /f',
     ]),
    ("tat_last_access", "Không ghi thời điểm mở file lần cuối",
     "Mỗi lần MỞ file Windows đều ghi lại một dấu thời gian xuống ổ - tắt "
     "đi thì ổ đỡ phải ghi, máy nhanh hơn, ổ SSD/thẻ nhớ bền hơn", "may", [
         "fsutil behavior set disableLastAccess 1",
     ]),
    ("chan_app_theo_thiet_bi", "Không tự cài app kèm theo thiết bị",
     "Cắm chuột/máy in vào là Windows tự tải app của hãng về cài - tắt đi "
     "để máy giao cho người dùng giữ nguyên như lúc bàn giao", "may", [
         r'reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Device Metadata"'
         r' /v PreventDeviceMetadataFromNetwork /t REG_DWORD /d 1 /f',
     ]),
    ("tat_wpbt", "Chặn hãng máy tự nhét phần mềm qua BIOS (WPBT)",
     "Một số hãng nhét sẵn file chạy trong BIOS, Windows tự lấy ra chạy "
     "mỗi lần cài lại - kể cả khi vừa format sạch. Tắt để máy cài lại là "
     "thật sự sạch", "may", [
         r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager"'
         r' /v DisableWpbtExecution /t REG_DWORD /d 1 /f',
     ]),
    ("tat_tang_toc_chuot", "Tắt tăng tốc con trỏ chuột",
     "Chuột đi đúng quãng tay di, không bị nhanh chậm theo tốc độ vẩy. "
     "Người quen dùng chuột chính xác sẽ thấy dễ chịu hơn", "ho_so", [
         r'reg add "HKCU\Control Panel\Mouse" /v MouseSpeed /t REG_SZ /d 0 /f',
         r'reg add "HKCU\Control Panel\Mouse" /v MouseThreshold1 /t REG_SZ /d 0 /f',
         r'reg add "HKCU\Control Panel\Mouse" /v MouseThreshold2 /t REG_SZ /d 0 /f',
     ]),
    ("giao_dien_toi", "Dùng giao diện Tối (Dark mode)",
     "Nền tối cho cả Windows và ứng dụng - đỡ chói khi làm việc trong "
     "phòng thiếu sáng hoặc ban đêm", "ho_so", [
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes'
         r'\Personalize" /v AppsUseLightTheme /t REG_DWORD /d 0 /f',
         r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes'
         r'\Personalize" /v SystemUsesLightTheme /t REG_DWORD /d 0 /f',
     ]),
    # Muc 1 (14/10/2026): Windows 11 tren may khong du chuan. Cai qua Console System thi
    # khong bi chan (DISM bung anh, khong qua setup.exe). Nhung SAU NAY chay bo cai nang
    # cap tai cho (setup.exe tu ISO ban moi) thi Setup se chan "This PC doesn't meet...".
    # Khoa MoSetup la cach Microsoft cong bo cho nang cap tai cho; LabConfig KHONG co tac
    # dung o day (chi cho cai moi tu WinPE) nen khong ghi.
    ("win11_khong_chuan", "Cho phép nâng cấp Windows 11 trên máy không đủ chuẩn",
     "Máy không có TPM 2.0 / CPU không nằm trong danh sách: cài qua Console System vẫn "
     "được, nhưng sau này chạy bộ cài để nâng cấp lên bản Windows 11 mới hơn sẽ bị chặn. "
     "Tick để mở khoá việc nâng cấp đó. Microsoft không cam kết hỗ trợ máy không đủ chuẩn",
     "may", [
         r'reg add "HKLM\SYSTEM\Setup\MoSetup" /v AllowUpgradesWithUnsupportedTPMOrCPU'
         r' /t REG_DWORD /d 1 /f',
     ]),
    ("xoa_windows_old", "Xoá thư mục Windows.old nếu còn sót",
     "Bản Windows cũ để lại có thể chiếm hàng chục GB. Chỉ xoá nếu có, "
     "không có thì bỏ qua", "may", [
         r'cmd /c if exist C:\Windows.old rd /s /q C:\Windows.old',
     ]),
]

def _khoi_gia_nhap_domain(d):
    """
    Component Microsoft-Windows-UnattendedJoin (pass specialize) - TINH
    NANG CHINH THUC cua Windows de tu gia nhap domain, dung dung co che
    MDT dung. Rong neu khong khai bao domain.

    Tai khoan dung de gia nhap PHAI co quyen them may vao domain (thuong
    la 1 tai khoan rieng cho viec nay, khong nhat thiet la Domain Admin).
    """
    domain = (d.get("domain") or "").strip()
    if not domain:
        return ""
    ou = (d.get("domain_ou") or "").strip()
    khoi_ou = f"\n        <MachineObjectOU>{_esc(ou)}</MachineObjectOU>" if ou else ""
    return f"""
    <component name="Microsoft-Windows-UnattendedJoin" processorArchitecture="amd64"
        publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS"
        xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <Identification>
        <Credentials>
          <Domain>{_esc(domain)}</Domain>
          <Username>{_esc(d.get('domain_user') or '')}</Username>
          <Password>{_esc(d.get('domain_pass') or '')}</Password>
        </Credentials>
        <JoinDomain>{_esc(domain)}</JoinDomain>{khoi_ou}
      </Identification>
    </component>"""
