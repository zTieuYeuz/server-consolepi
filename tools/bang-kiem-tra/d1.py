# -*- coding: utf-8 -*-
# Định dạng mỗi dòng: nhóm | chức năng | cách kiểm tra | kết quả mong đợi | điều kiện / thiết bị | ưu tiên (C/T/L) | em đã kiểm (TH/TD/TT/CH)
S01 = """
Ảnh Raspberry Pi|Ghi ảnh .img.xz bằng Raspberry Pi Imager|Chọn "Use custom", file ConsoleSystem-...-raspberrypi.img.xz, điền tài khoản + SSH (+WiFi), ghi thẻ, cắm Pi, cấp nguồn|Pi tự mở rộng thẻ và tự thiết lập trong 3-5 phút (không cần Internet), có thể tự khởi động lại 1 lần; vào http://IP-Pi đăng nhập được bằng tài khoản vừa tạo|Pi 3/4/5, thẻ >=16 GB, nguồn đủ công suất|C|TH
Ảnh Raspberry Pi|Quên tạo tài khoản trong Imager|Ghi ảnh KHÔNG điền tài khoản, gắn màn hình + bàn phím, bật Pi|Pi hỏi tạo tài khoản ngay trên màn hình; tạo xong Console System tự thiết lập tiếp|Pi + màn hình + bàn phím|T|CH
Ảnh Raspberry Pi|Cài lên Raspberry Pi OS Lite 64-bit có sẵn|Chép thư mục mã nguồn vào Pi, chạy sudo bash install.sh --local <thư mục>|Cài 5-15 phút, xong khởi động lại thì dashboard chạy; không báo lỗi thiếu gói|Pi OS Lite 64-bit (Debian 12/13), có mạng|C|TH
Ảnh Raspberry Pi|Cài không màn hình (--no-screen)|Chạy install.sh --local <thư mục> --no-screen|Bỏ phần giao diện cảm ứng/kiosk, tiết kiệm ~500 MB, dashboard vẫn dùng được qua mạng|Pi không màn hình|T|CH
Ảnh Raspberry Pi|Cài đè bản mới giữ cấu hình|Cấu hình sẵn: WiFi lưu, tên cổng console, thư viện lệnh, kịch bản, AP, hướng màn hình rồi chạy lại install.sh|Tất cả cấu hình trên còn nguyên sau khi cài đè|Pi đã có dữ liệu|C|TH
Ảnh Raspberry Pi|Gỡ cài đặt|sudo bash uninstall.sh rồi sudo bash uninstall.sh --purge|Lần 1 gỡ phần mềm giữ cấu hình; --purge xoá sạch cả cấu hình|Pi|T|CH
Ảnh Raspberry Pi|Cập nhật bằng cap-nhat-pi.sh|rsync mã nguồn sang Pi, chạy trên Pi: sudo bash ~/consolepi-toolkit/tools/cap-nhat-pi.sh|In kết quả kiểm trang (/ -> 200, /deployos -> 302...), tạo file sao lưu .tgz kèm lệnh trả lại bản cũ, dịch vụ console-pi-dashboard active, dữ liệu giữ nguyên|Pi, SSH|C|TH
Ảnh Raspberry Pi|Cập nhật tự cài nginx location VNC + cổng mTLS agent|Chạy cap-nhat-pi.sh trên Pi chưa có|Có location /uem-vnc-ws/ trong nginx, cổng mTLS agent mở, lỗi thì tự trả cấu hình cũ|Pi|C|TT
Bản cài laptop / máy bàn (ISO)|Ghi USB bằng Rufus chế độ DD Image|Rufus: chọn ISO, START, chọn "Write in DD Image mode"|USB boot được, hiện menu Console System|USB >=4 GB, Windows|C|TH
Bản cài laptop / máy bàn (ISO)|Menu khởi động 4 mục + tự vào Chạy thử sau 5 giây|Boot USB, không bấm gì|Sau 5 giây vào "Chạy thử" (không cài gì, không đụng ổ cứng); menu không bao giờ tự vào trình cài; dòng đầu ghi tác giả zTieuYeuz|Máy x86|C|TH
Bản cài laptop / máy bàn (ISO)|Chạy thử chế độ an toàn|Chọn "Chạy thử - chế độ an toàn" trên máy bị đen màn hình|Boot được, dashboard mở được|Máy lạ/GPU khó|T|CH
Bản cài laptop / máy bàn (ISO)|Cài bằng giao diện đồ hoạ (8 bước)|Chọn CÀI - giao diện đồ hoạ: Chào mừng, Vị trí, Phân vùng, Người dùng, Tổng quan, Cài đặt, Hoàn thành|Múi giờ HCM điền sẵn; Tiếp theo mờ tới khi chọn ổ; hình Hiện tại/Sau; hộp xác nhận lần cuối; cài 5-15 phút; có màn hình giới thiệu tính năng|Máy x86 UEFI hoặc BIOS|C|TH
Bản cài laptop / máy bàn (ISO)|Trình cài không tự chọn ổ|Vào bước Phân vùng chưa chọn gì|Nút Tiếp theo mờ; phải tự chọn thiết bị + Xoá đĩa; USB cài không có trong danh sách|2 ổ + USB|C|TH
Bản cài laptop / máy bàn (ISO)|Cài chế độ chữ (dự phòng)|Chọn CÀI - chế độ chữ|Cài được trên máy lỗi đồ hoạ|Máy lỗi GPU|T|CH
Bản cài laptop / máy bàn (ISO)|Boot sau cài|Rút USB, khởi động lại|Vào thẳng giao diện Console System trên màn hình (kiosk); bảng Chi tiết mạng hiện IP; không có desktop|Máy x86|C|TH
Bản cài laptop / máy bàn (ISO)|UEFI + Secure Boot|Cài và boot trên máy bật Secure Boot|Cả USB lẫn máy đã cài boot được (shim ký Microsoft), không phải tắt Secure Boot|Máy UEFI Secure Boot|C|TH
Bản cài laptop / máy bàn (ISO)|Mini PC bỏ qua mục boot đã lưu|Cài rồi rút USB trên mini PC|Vẫn boot được nhờ trình khởi động ở đường dự phòng EFI|Mini PC|T|TH
Bản cài laptop / máy bàn (ISO)|Bản i386 (32-bit)|Cài ISO i386 trên máy 32-bit hoặc VM i386|Cài bằng trình cài chữ, dashboard chạy Python 3.11, đủ chức năng chính|Máy/VM 32-bit|T|TT
Bản cài laptop / máy bàn (ISO)|Card mạng firmware có sẵn|Cài trên máy có card Intel/Realtek/Atheros/Broadcom/MediaTek/Qualcomm|Có mạng ngay sau cài; firmware Realtek nhúng sẵn cả trong trình cài|Máy thật nhiều loại NIC|T|TH
Bản cài laptop / máy bàn (ISO)|Cài trên VMware không đổi card|Tạo VM VMware mặc định, cài ISO|Cài và dùng được, có mạng|VMware|C|TH
Bản cài laptop / máy bàn (ISO)|Kiosk fallback|Làm trình duyệt kiosk lỗi 5 lần liên tiếp|Máy tự về màn hình dòng lệnh có logo và địa chỉ IP, không đen màn hình vĩnh viễn|Máy x86|T|CH
Bản cài laptop / máy bàn (ISO)|Vẽ bằng GPU / CPU|Chạy trên Intel/AMD, VM, card iDRAC/iLO, NVIDIA|Intel/AMD vẽ bằng GPU; VM/iDRAC/NVIDIA vẽ bằng CPU; GPU lỗi tự đổi sang CPU và nhớ|Nhiều loại máy|T|TH
Bản cài laptop / máy bàn (ISO)|Bật/tắt giao diện trên màn hình máy này|Cài đặt > Giao diện trên màn hình máy này|Bật/tắt được kiosk, không cần cài lại|Máy x86|T|TH
Khởi động và tự kiểm tra|Tự kiểm tra sau mỗi lần boot|Khởi động lại, mở Nhật ký > Log toàn bộ > nguồn console-pi-selftest.log|Có kết quả Đạt/Lỗi cho mọi dịch vụ, từng trang web, từng cổng console, kịch bản LAN thẳng/AP/Bluetooth tự nối lại|Pi hoặc x86|C|TH
Khởi động và tự kiểm tra|Bốn đường vào giao diện|Thử: http://IP hoặc tên.local; WiFi ConsolePi -> 192.168.50.1; LAN thẳng laptop->máy; Bluetooth PAN -> 192.168.60.1|Luôn còn ít nhất một đường vào được|Pi (Bluetooth PAN chỉ Pi)|C|TH
Khởi động và tự kiểm tra|Dịch vụ nguy hiểm không tự bật|Khởi động lại máy rồi xem trạng thái PXE/DHCP/TFTP/Samba/AP|Tất cả đều TẮT sau boot, chỉ bật khi bấm|Mạng thật|C|TH
Khởi động và tự kiểm tra|Màn hình chờ kiosk có thanh tiến trình|Khởi động máy có màn hình|Màn hình chờ có thanh tiến trình bám sát việc khởi động thật, rồi vào giao diện|Máy có màn hình|T|TH
Khởi động và tự kiểm tra|DNS dự phòng khi rút dây|Rút dây LAN chỉ còn WiFi/hotspot rồi ping tên miền|Phân giải được nhờ DNS dự phòng 1.1.1.1 và 8.8.8.8|Pi/x86 + WiFi|T|TH
Khởi động và tự kiểm tra|Nhật ký tự xoay vòng 7 ngày|Kiểm logrotate và journald sau vài ngày|Log chỉ giữ 7 ngày, không đầy thẻ nhớ|Chạy lâu|T|TH
Khởi động và tự kiểm tra|Python 3.11 tương thích|Chạy bash iso/test/kiem-python311.sh trên máy build|Kết quả "loi 3.11: 0" (bản i386 dùng Python 3.11, cú pháp 3.12+ làm chết dashboard)|Máy build|C|TD
Khởi động và tự kiểm tra|Chạy nhiều lần không hỏng|Reboot Pi 5 lần liên tiếp|Dashboard luôn lên, không treo, selftest đạt|Pi|T|CH
"""

S02 = """
Đăng nhập và truy cập|Đăng nhập bằng tài khoản Linux của máy|Mở trang từ máy khác, nhập đúng tài khoản/mật khẩu|Vào được giao diện; sai mật khẩu bị từ chối|Máy khác trong mạng|C|TH
Đăng nhập và truy cập|Màn hình gắn trực tiếp không hỏi đăng nhập|Mở giao diện trên màn hình của chính máy (kiosk/localhost:8880)|Vào thẳng, không hỏi đăng nhập; truy cập qua mạng luôn phải đăng nhập|Máy có màn hình|C|TH
Đăng nhập và truy cập|Đăng xuất|Bấm đăng xuất|Về trang đăng nhập; phiên cũ không dùng lại được|Trình duyệt|T|CH
Đăng nhập và truy cập|Ghi nhật ký Thao tác|Đăng nhập sai, đăng nhập đúng, xoá kịch bản...|Nhật ký > Thao tác ghi người dùng@địa chỉ, giờ, thao tác; KHÔNG ghi mật khẩu|Trình duyệt|C|TT
Đăng nhập và truy cập|File cài PXE chỉ phát cho mạng nội bộ|Khi PXE bật, thử tải file kịch bản từ Internet/qua Cloudflare|Bị từ chối; chỉ máy cùng mạng nội bộ tải được; tắt PXE thì đóng hẳn|PXE + truy cập ngoài|C|TH
Đăng nhập và truy cập|Đường agent công khai chỉ từ mạng nội bộ|Gọi /uem/agent/* từ IP ngoài mạng nội bộ không qua cổng mTLS|Bị chuyển về đăng nhập hoặc từ chối; chỉ cổng mTLS có chứng chỉ máy mới được|Curl từ ngoài|C|TT
Chế độ giao diện|Chế độ PC|Mở bằng laptop|Menu trái hiện đủ nhóm, nút » thu gọn thành dải biểu tượng, nền mặc định tối, ô tìm Ctrl+K|Laptop|C|TT
Chế độ giao diện|Chế độ cảm ứng|Bấm nút "Chế độ cảm ứng" góc phải trên|Thanh dưới cố định: Trang chủ, Quay lại, Tìm, Menu, Nguồn; nút Menu mở ô to đủ mọi mục; nền sáng mặc định; vẫn ở nguyên trang đang xem|Màn hình cảm ứng/tablet|C|TT
Chế độ giao diện|Nhớ lựa chọn riêng từng máy/trình duyệt|Đổi chế độ + nền trên laptop, mở trên RasPad|Mỗi nơi giữ lựa chọn riêng|2 thiết bị|T|TT
Chế độ giao diện|Mặc định lần đầu|Mở lần đầu trên màn hình gắn máy và trên laptop|Màn gắn máy mở Chế độ cảm ứng; laptop mở Chế độ PC|2 thiết bị|T|TH
Chế độ giao diện|Điện thoại (màn hẹp)|Mở trên điện thoại|Cả hai chế độ dùng thanh dưới, không bể bố cục|Điện thoại|T|TT
Chế độ giao diện|Nền sáng / tối|Bấm nút Sáng/Tối mọi trang|Đổi nền toàn bộ, không trang nào còn màu cứng sai (chữ đọc được)|Trình duyệt|C|TT
Chế độ giao diện|Giảm chuyển động|Bật "giảm chuyển động" của hệ điều hành rồi mở trang|Mọi hiệu ứng tắt, trang vẫn đủ nội dung|Windows/Android|L|CH
Điều hướng|Menu nhóm dropdown, chữ nhóm lớn, mục con thụt vào|Xem menu trái|6 nhóm: Kết nối Console System, Quản lý và kết nối thiết bị, Quản lý máy trạm, System Utilities, Kho lưu trữ, Cài đặt; bấm nhóm mở/đóng; mục đang mở tô xanh|Chế độ PC|C|TT
Điều hướng|Đủ mọi mục menu|Bấm lần lượt từng mục|Wifi/AP, Bluetooth, Truy cập từ xa, Phiên kết nối, Console, Cắm thẳng, 9 mục Quản lý máy trạm, Network Tools, Deployment OS, Triển khai phần mềm, Kho file, Thư viện lệnh, Cài đặt chung, Nhật ký, Nguồn điện, Góp ý, Giải trí, Tài liệu đều mở được (không 404/500)|Trình duyệt|C|TT
Điều hướng|Tìm nhanh Ctrl+K / nút Tìm|Gõ "wol", "bat may tu xa", "dhcp", "pxe" không dấu|Ra đúng: Bật máy từ xa, Kiểm tra cổng mạng, Bật/Tắt PXE; mũi tên chọn, Enter mở, Esc đóng|Trình duyệt|C|TT
Điều hướng|Nút Home mọi trang|Mở từng trang|Mọi trang đều có đường về Trang chủ: nút tròn nhà góc phải dưới (PC) hoặc nút Trang chủ (cảm ứng)|Trình duyệt|C|TT
Điều hướng|Nút Quay lại chế độ cảm ứng|Trên màn cảm ứng bấm Quay lại|Về trang trước|Cảm ứng|T|TH
Thanh đầu trang|Chip mạng LAN/WiFi/Bluetooth/Cloudflare kèm IP|Xem thanh đầu trang ở nhiều độ rộng cửa sổ|Hiện đủ các chip có nhãn loại + IP (không bị cắt/chồng chéo), co giãn theo màn hình, chip không bao giờ bị ẩn|Máy nhiều card mạng|C|TH
Thanh đầu trang|Responsive header|Thu nhỏ cửa sổ dần|Chip chuyển cỡ f1/f2/f3 vừa khít, không vỡ|Trình duyệt|T|TH
Bàn phím ảo|Hiện khi chạm ô nhập trên màn hình máy|Chạm ô nhập ở mọi trang|Bàn phím ảo hiện và nằm trên thanh dưới; chỉ hiện trên màn gắn máy (không hiện khi vào từ laptop)|RasPad/màn cảm ứng|C|TT
Bàn phím ảo|Nút tròn bật/tắt bàn phím|Bấm nút tròn góc phải dưới|Bật/tắt bàn phím|Cảm ứng|T|TH
Bàn phím ảo|Trong Console/SSH/terminal|Mở phiên Console/SSH trên màn cảm ứng, chạm|Bàn phím ảo hiện và gõ vào đúng phiên tmux; ở chế độ cảm ứng thanh dưới chừa chỗ không đè nút|Cảm ứng|C|TT
Bàn phím ảo|Trong trang Giải trí (YouTube/TikTok)|Chạm ô tìm kiếm trên youtube.com|Bàn phím ảo hiện và gõ đúng|Cảm ứng + Internet|T|TH
Xoay màn hình|Xoay hình + toạ độ cảm ứng|Cài đặt > Xoay màn hình|Hình và chạm cùng xoay (không lệch); hướng nhớ cho lần boot sau|RasPad|T|TH
"""

S03 = """
Tổng quan|Trang Tổng quan: dòng trạng thái|Mở /|Dòng lớn "Mọi thứ đang ổn." hoặc "Có N việc cần chú ý.", phiên bản, thời gian chạy, 2 nút Cài Windows qua mạng + Mở Console, địa chỉ mạng LAN/WiFi|Máy chạy|C|TT
Tổng quan|Cần chú ý|Gây tình huống: nguồn yếu, CPU nóng >=70 °C, dịch vụ lỗi, ổ >=80%, cáp console chưa đặt tên, PXE bật|Mỗi tình huống hiện 1 mục cần chú ý đúng nội dung; mục ổ đầy dẫn đến trang chọn xoá; hệ thống KHÔNG tự xoá dữ liệu|Pi/x86|C|TH
Tổng quan|Đang diễn ra|Cho máy đang cài Windows qua mạng|Hiện khối Đang diễn ra với máy đang cài|PXE + máy khách|T|TH
Tổng quan|Ô việc hay làm|Xem 5 ô PC / 8 ô cảm ứng|Nhãn là số thật (vd 2 cổng console, PXE đang bật, 3 máy đã lưu để bật từ xa); ô Cài Windows qua mạng to nhất|Có dữ liệu|T|TH
Tổng quan|Sức khỏe thiết bị|Xem CPU, RAM, đĩa, nhiệt độ, tải, nguồn điện|Số thật, thanh đổi màu khi gần đầy, tự cập nhật 10 giây, chỗ không đo được ghi "không áp dụng" (không bịa số, không hiện pin nếu không đọc được)|Pi/x86|C|TH
Tổng quan|Cổng console đang cắm + đặt tên|Cắm cáp, xem khối cổng console|Hiện từng cổng, đặt tên gợi nhớ|Cáp USB-serial|T|TH
Tổng quan|Cài đặt gần đây|Sau khi cài vài máy qua PXE|Hiện 5 máy gần nhất lấy từ Lịch sử|PXE|T|TH
Tổng quan|Dịch vụ hệ thống|Xem danh sách dịch vụ|Trạng thái ghi bằng chữ Đang chạy/Tắt/Lỗi (không chỉ màu), chấm nhấp nháy chậm khi đang chạy|Máy chạy|T|TT
Tổng quan|API sức khỏe|Gọi /api/suckhoe|Trả JSON số liệu, không ghi vào nhật ký truy cập (đã lọc)|curl|L|TH
Cài đặt chung|Giới thiệu|Cài đặt > Cài đặt chung, khung đầu tiên|Hiện phiên bản, tác giả zTieuYeuz, bản quyền, nút mở trang hướng dẫn|Trình duyệt|T|TT
Cài đặt chung|Thông tin hệ thống|Xem khung Thông tin hệ thống|Hiển thị đúng model/OS/IP/uptime|Máy chạy|L|CH
Cài đặt chung|Mật khẩu terminal|Xem và đổi mật khẩu terminal (ttyd)|Hiện/ẩn được, đổi xong terminal dùng mật khẩu mới|Máy chạy|T|CH
Cài đặt chung|Dung lượng|Xem khung Dung lượng thẻ nhớ|Từng mục chiếm bao nhiêu, vàng >=80%, đỏ >=90%, bấm vào tới trang để xoá bớt|Máy có dữ liệu|C|TH
Cài đặt chung|Dọn rác an toàn|Bấm dọn rác|Chỉ xoá gói cài đã tải, nhật ký cũ, file tải dở; KHÔNG đụng dữ liệu người dùng|Máy có rác|C|TH
Cài đặt chung|Sao lưu cấu hình|Bấm tải file sao lưu|Tải file nhỏ (vài KB): kịch bản, bảng tham số, thư viện lệnh, kết nối kho, tham số cài im lặng; KHÔNG có Windows/bộ cài|Máy có cấu hình|C|TH
Cài đặt chung|Khôi phục cấu hình|Nạp lại file sao lưu trên máy sạch|Cấu hình trở lại đủ; gói độc hại có đường dẫn ../ (zip slip) bị chặn sạch|2 máy|C|TH
Cài đặt chung|Giao diện trên màn hình máy này|Bật/tắt trong Cài đặt|Kiosk bật/tắt đúng|Máy x86|T|TH
Cài đặt chung|Xoay màn hình|(xem mục Giao diện)|-|RasPad|T|TH
"""

S04 = """
WiFi / AP|Quét và nối WiFi|Kết nối server > WiFi/AP > Quét lại > chọn mạng > nhập mật khẩu > Kết nối|20-30 giây sau khung Trạng thái hiện tên mạng + IP; tích "Lưu để lần sau tự kết nối" thì lần sau tự nối|Card WiFi + router|C|TH
WiFi / AP|Nút Kết nối trên bảng WiFi đã lưu|Bấm Kết nối ở mạng đã lưu|Nối lại được không cần nhập mật khẩu|WiFi đã lưu|T|TH
WiFi / AP|Tự phát WiFi ConsolePi khi không có WiFi quen|Tắt WiFi quen, đợi tối đa ~2 phút|Máy tự phát WiFi "ConsolePi"; nối vào, mở http://192.168.50.1 thấy giao diện|Card WiFi hỗ trợ AP|C|TH
WiFi / AP|Mật khẩu AP riêng từng máy|Xem Chế độ phát sóng > Hiện|Mật khẩu ngẫu nhiên riêng từng máy, che mặc định, bấm Hiện mới thấy|Pi|C|TH
WiFi / AP|Khoá AP / Gỡ khoá AP|Bấm Phát AP ConsolePi (khoá) rồi Gỡ khoá|Khoá thì không tự chuyển sang WiFi quen; gỡ khoá trả về chế độ tự động|Pi|T|TH
WiFi / AP|Quét rỗng không làm hỏng AP|Giả quét WiFi trả rỗng|Máy quét tối đa 3 lần, nếu vẫn không thấy mạng nào thì giữ nguyên hiện trạng (không coi là không có mạng quen)|Pi|T|TH
WiFi / AP|Người lạ bám AP không ghim mãi|Cho 1 điện thoại nối AP|Chỉ giữ tối đa 10 phút rồi đánh giá lại|Pi|T|TH
WiFi / AP|Chuyển AP về WiFi|Cho WiFi quen xuất hiện lại|Chờ liên kết xong mới xin IP, cả vòng ~17 giây|Pi|T|TH
WiFi / AP|Giả MAC WiFi|Bật giả MAC rồi nối WiFi công ty chặn Pi; tắt trả MAC thật|MAC giả cố định (không đổi mỗi lần); tắt thì trả đúng MAC thật|Mạng chặn Pi|T|TH
WiFi / AP|Hotspot điện thoại|Rút dây LAN, nối hotspot 4G|Dùng được; Cloudflare Tunnel vẫn chạy qua HTTP/2 TCP 443|Điện thoại 4G/5G|T|TH
WiFi / AP|Trên x86 không hỗ trợ AP|Dùng card WiFi không có chế độ AP|Giao diện báo rõ/không treo|Laptop card Intel|L|CH
Bluetooth|Ghép bàn phím|Giữ nút Connect tới khi đèn nháy nhanh, bấm Ghép cặp (đếm ngược 150 s)|Ghép được; bàn phím tự ngắt sau vài giây rảnh (không phải lỗi), bấm nhanh phím để nối lại|Pi + bàn phím BT|T|TH
Bluetooth|Ghép bàn phím có hỏi mã|Dùng bàn phím yêu cầu mã|Màn hình hiện dãy số, gõ trên bàn phím + Enter|Pi|L|TH
Bluetooth|Tai nghe/loa|Ghép thiết bị không gõ được|Dùng mã mặc định nhà sản xuất (0000, 1234...) và ghi rõ|Pi|L|TH
Bluetooth|Mạng dự phòng PAN từ Windows|Ghép từ phía Windows, Connect using > Access point|Windows nhận IP, vào http://192.168.60.1 (hoặc IP hiện trên trang); trang phân biệt "có Bluetooth, chưa vào mạng" (vàng) và "đã vào mạng kèm IP" (xanh)|Pi + Windows 11|T|TH
Bluetooth|Ghép nhiều thiết bị cùng lúc|Ghép bàn phím và máy tính PAN song song|Chạy song song không xung đột|Pi|L|TH
Bluetooth|Trust để tự nối lại|Bấm Trust rồi khởi động lại|Tự nối lại|Pi|T|TH
Bluetooth|Không bấm Ghép cặp lại khi chỉ mất kết nối|Đọc cảnh báo trên trang|Nút Ghép cặp lại xoá liên kết cũ - có cảnh báo|Pi|L|TH
Truy cập từ xa|Cloudflare Tunnel: cài cloudflared|Truy cập từ xa > Cài cloudflared (có Internet)|Cài xong, hiện nơi dán token|Internet|C|TH
Truy cập từ xa|Cloudflare Tunnel: dán token, Bật đường hầm|Tạo tunnel trong Zero Trust (arm64/amd64), trỏ http://127.0.0.1:80, dán token, Lưu, Bật|Link HTTPS truy cập được từ Internet vào đúng giao diện (qua đăng nhập của máy); token chỉ quản trị viên đọc được|Tài khoản Cloudflare|C|TH
Truy cập từ xa|Tắt đường hầm|Bấm Tắt|Link không còn truy cập được (Cloudflare 502/523)|Cloudflare|T|TH
Truy cập từ xa|Chip Cloudflare trên thanh đầu|Bật tunnel|Chip Cloudflare hiện trạng thái đúng|Cloudflare|T|TH
Truy cập từ xa|Tailscale: cài, dán Auth key, Lưu và kết nối|Cài Tailscale, tạo Auth key trong Settings > Keys, dán|Hiện domain thật; máy khác cùng tài khoản vào được cả SSH và web|Tài khoản Tailscale|T|TH
Truy cập từ xa|Tailscale: đổi Auth key / Quên thiết bị / Tắt|Bấm lần lượt|Quên = đăng xuất hẳn + xoá khoá; Tắt = ngắt tạm|Tailscale|L|TH
Truy cập từ xa|Chạy sau 4G / nhiều lớp NAT|Máy dùng hotspot, truy cập từ xa|Vào được không cần mở cổng router, không cần IP tĩnh|4G|T|TH
"""
