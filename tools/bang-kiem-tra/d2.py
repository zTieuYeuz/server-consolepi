# -*- coding: utf-8 -*-
S05 = """
Phiên kết nối - bố cục|Danh sách bên trái|Mở Quản lý và kết nối thiết bị > Phiên kết nối|Có: Cổng console tự nhận, Terminal máy này, thiết bị đã lưu theo nhóm; có ô tìm|Máy chạy|C|TT
Phiên kết nối - bố cục|Nhiều tab cùng lúc|Mở 3 phiên|Chuyển qua lại giữa các tab; nội dung mỗi tab giữ nguyên|Trình duyệt|C|TH
Phiên kết nối - bố cục|Tải lại trang / đóng trình duyệt không mất phiên|Mở phiên, chạy lệnh dài, tải lại trang|Mở lại thấy đúng màn hình cũ, lệnh vẫn chạy (tmux)|Trình duyệt|C|TH
Phiên kết nối - bố cục|Bấm × trên tab tắt hẳn phiên|Bấm × rồi mở lại|Phiên cũ bị tắt, mở lại là phiên mới|Trình duyệt|C|TH
Phiên kết nối - bố cục|Hai màn hình xem một phiên|Mở cùng phiên trên RasPad và laptop|Hai nơi thấy cùng nội dung, khung theo màn hình vừa gõ, không vỡ/lặp chữ|2 thiết bị|T|TH
Phiên kết nối - kết nối nhanh|ssh user@IP / chỉ IP / :cổng|Gõ vào ô Kết nối nhanh|Mở SSH đúng host, user, cổng (mặc định 22)|Thiết bị SSH|C|TH
Phiên kết nối - kết nối nhanh|telnet IP|Gõ telnet 10.0.0.1|Mở Telnet (thoát Ctrl+])|Thiết bị Telnet|C|TH
Phiên kết nối - kết nối nhanh|ttyUSB0|Gõ ttyUSB0|Mở cổng console tương ứng|Cáp console|C|TH
Phiên kết nối - kết nối nhanh|Chống chèn lệnh|Nhập host/user có ký tự lạ như dấu chấm phẩy, dấu gạch đứng, $( )|Không chạy lệnh chèn (tham số cố định, không qua shell)|-|C|TH
Phiên kết nối - lưu thiết bị|+ Phiên mới: SSH / Telnet / Serial|Điền tên, nhóm, IP/cổng/user (hoặc cổng console + baud), Lưu & kết nối|Lưu vào danh sách; Serial chọn cổng + baud (9600)|Thiết bị|C|TH
Phiên kết nối - lưu thiết bị|Lưu mật khẩu (tuỳ chọn) + Gõ mật khẩu|Tích Lưu mật khẩu, kết nối, bấm Gõ mật khẩu|Máy tự gõ đúng lúc thiết bị hỏi; mật khẩu không hiện trên màn hình, không có trong lịch sử lệnh, không gửi ngược ra trình duyệt|Thiết bị|C|TH
Phiên kết nối - lưu thiết bị|Xoá mật khẩu đã lưu|Sửa phiên > tích Xoá mật khẩu đã lưu|Mật khẩu bị xoá|-|T|TH
Phiên kết nối - lưu thiết bị|Sửa/xoá thiết bị (✎)|Rê chuột lên dòng, bấm ✎|Sửa/xoá được|-|T|TH
Phiên kết nối - nhóm|Tạo nhóm, chọn nhóm khi lưu phiên|Tạo nhóm trước rồi + Phiên mới|Ô Nhóm là danh sách thả xuống; chọn "+ Tạo nhóm mới..." tạo ngay tại chỗ|-|C|TT
Phiên kết nối - nhóm|Nhóm trống vẫn hiện|Tạo nhóm chưa có phiên|Hiện "Chưa có phiên"|-|T|TT
Phiên kết nối - nhóm|Đổi tên / xoá nhóm|Đổi tên rồi xoá|Đổi tên cập nhật mọi phiên trong nhóm; xoá nhóm không xoá phiên (về mục Đã lưu); tên <=40 ký tự, không trùng (không phân biệt hoa thường), không trùng tên nhóm hệ thống|-|T|TT
Phiên kết nối - thanh công cụ|Thư viện lệnh trong phiên|Bấm Thư viện lệnh: tìm, lọc thẻ, chọn lệnh, sửa ô {{...}}, Gửi vào phiên|Ngăn trượt bên phải; chỗ chưa điền thì hỏi lại trước gửi; kết quả đã gửi/lỗi hiện dưới nút; Quản lý mở trang Thư viện lệnh|Thiết bị|C|TT
Phiên kết nối - thanh công cụ|Gửi từng dòng an toàn|Gửi tập lệnh nhiều dòng vào switch|Gửi từng dòng, chờ dấu nhắc, tự Space khi --More--, dòng cuối KHÔNG tự Enter; không rơi ký tự (show inventory không thành how inventory)|Switch Cisco|C|TH
Phiên kết nối - thanh công cụ|Terminal máy này: dán không chạy|Gửi tập lệnh vào terminal máy|Dán cả khối nhưng không tự chạy|-|T|TH
Phiên kết nối - thanh công cụ|Tô màu|Bật Tô màu, xem kết quả lệnh|Lỗi đỏ, cảnh báo vàng, tốt xanh lá, IP lam nhạt, MAC tím, cổng xanh dương, giờ xám; chỉ tô chữ mặc định; nhớ lựa chọn; không làm trễ phím|Thiết bị|T|TT
Phiên kết nối - thanh công cụ|Lưu log|Bấm Lưu log|Tải .txt gồm cả phần đã cuộn qua|-|C|TH
Phiên kết nối - thanh công cụ|Toàn màn hình / Ngắt phiên|Bấm lần lượt|Phóng to; ngắt như bấm ×|-|T|TH
Phiên kết nối - thanh công cụ|Chép/dán|Bôi đen (tự chép), chuột phải > Paste, Ctrl+V / Ctrl+Shift+V|Vệt bôi giữ sau nhả chuột, tự chép clipboard, chuột phải chỉ hiện 1 menu, không hiện công cụ cái kéo của Edge|Edge/Chrome|C|TT
Phiên kết nối - thanh công cụ|Cuộn lịch sử bằng chuột|Cuộn bánh xe|Cuộn lại màn hình; bấm phím về dòng lệnh|-|T|TH
Phiên kết nối - thanh công cụ|Mất kết nối giữa chừng|Khởi động lại thiết bị đang SSH|Tab báo "Phiên đã kết thúc - Enter = kết nối lại"; Enter vào lại, q đóng|SSH|C|TH
Phiên kết nối - thanh công cụ|SSH thiết bị đời cũ|SSH vào switch chỉ hỗ trợ SHA-1|Kết nối được (bật lại thuật toán cũ cho chiều đi ra); không báo no matching key exchange|Switch cũ|T|TH
Phiên kết nối - thanh công cụ|Telnet tích hợp|Telnet vào switch/router|Dùng được, thoát Ctrl+]|Thiết bị|T|TH
Console (RS232)|Tự nhận cáp USB-serial|Cắm cáp FTDI/Prolific/CH340|Hiện ttyUSB0/1... và tên chip; rút là mất|Cáp|C|TH
Console (RS232)|Tự nhận cáp Cisco USB console|Cắm cáp Cisco micro-USB|Hiện ttyACM0/1...|Cáp Cisco|C|TH
Console (RS232)|Tự dò baud / đổi baud|Mở cổng, đổi tốc độ|Mặc định 9600; đổi baud thì phiên tự mở lại với tốc độ mới|Thiết bị|C|TH
Console (RS232)|Đặt tên gợi nhớ cho cổng|Đặt tên "Core switch tầng 3"|Tên hiện ở Console, Tổng quan, Phiên kết nối; cáp chưa đặt tên có nhắc ở Tổng quan|Cáp|T|TH
Console (RS232)|Phiên console không mất khi đóng trình duyệt|Đóng trình duyệt, mở lại|Vẫn đúng chỗ cũ|Cáp|C|TH
Console (RS232)|Hai nơi mở cùng một cổng|Mở cùng cổng trên 2 trình duyệt|Thấy cùng một màn hình, không tranh ký tự|Cáp|T|TH
Console (RS232)|Cắm thêm cáp không phải khởi động lại|Cắm cáp thứ 2 khi đang chạy|Tự nhận|2 cáp|T|TH
Console (RS232)|Sao lưu qua cáp console|(Xem Network Tools > Sao lưu qua cáp console)|-|Cáp|T|TH
Cắm thẳng thiết bị|Bật chế độ cắm thẳng|Cắm dây thẳng sang cổng quản lý iLO/iDRAC, bấm Bật chế độ cắm thẳng|Máy lấy 192.168.99.1, cấp DHCP 192.168.99.50-99; cảnh báo đổi IP cổng LAN|Máy chủ có iLO/iDRAC/IPMI|C|TH
Cắm thẳng thiết bị|Quét thiết bị + Mở|Đợi 15-30 giây, bấm Quét thiết bị, bấm Mở|Thấy thiết bị, nhận hãng từ MAC (HPE iLO, Dell iDRAC, Supermicro IPMI, Lenovo IMM, Cisco, VMware); Mở vào web quản lý|Thiết bị BMC|C|TH
Cắm thẳng thiết bị|Quét rộng / nhập dải IP|Thiết bị đặt IP tĩnh khác dải|Thấy bằng quét ARP lớp 2 hoặc nhập dải|Thiết bị IP tĩnh|T|TH
Cắm thẳng thiết bị|Tắt chế độ|Bấm Tắt chế độ|Trả cổng về bình thường|-|C|TH
Cắm thẳng thiết bị|Cổng không còn tồn tại|Chọn cổng đã rút|Máy từ chối bật (không chạy âm thầm trên cổng khác)|-|L|TH
Thư viện lệnh (Kho lưu trữ)|Danh sách + tìm + thẻ|Mở Thư viện lệnh, gõ tìm, bấm thẻ|Lọc đúng; có sẵn mẫu Cisco|-|C|TT
Thư viện lệnh (Kho lưu trữ)|Thêm/sửa/xoá tập lệnh|Tạo tập lệnh có {{cổng}} {{vlan}}|Lưu được, tìm thấy|-|C|TT
Thư viện lệnh (Kho lưu trữ)|Gửi vào Terminal|Bấm Gửi vào Terminal|Dán vào terminal máy, không tự chạy|-|T|TH
Thư viện lệnh (Kho lưu trữ)|Dùng trong Phiên kết nối|Bấm nút trên tập lệnh|Mở phiên với lệnh chọn sẵn|Thiết bị|T|TH
"""

S06 = """
Kiểm tra cổng mạng|Kiểm tra toàn diện một nút|Cắm vào ổ mạng/cổng switch, Network Tools > Kiểm tra cổng mạng, chọn eth0, bấm Kiểm tra toàn diện|20-60 giây ra: tốc độ/duplex, lỗi CRC, PoE (nếu có mạch đo), DHCP (OFFER, IP, gateway, DNS), Internet (ping + web), băng thông (Cloudflare, tải 25 MB); xong trả cổng như cũ|Dây mạng + DHCP|C|TH
Kiểm tra cổng mạng|Half Duplex cảnh báo|Cổng switch ép half duplex|Hiện cảnh báo lệch duplex|Switch|T|TH
Kiểm tra cổng mạng|So năng lực hai bên|Cổng ép 100M trong khi hai bên hỗ trợ Gigabit|Cảnh báo ai đang ép tốc độ thấp|Switch|T|TH
Kiểm tra cổng mạng|DHCP gửi lại 3 lần|Mạng làm rớt gói DHCP đầu|Tự gửi lại tới 3 lần (RFC 2131)|Mạng|T|TH
Kiểm tra cổng mạng|Option 121|Mạng chỉ gửi gateway bằng Option 121|Đọc được gateway, không báo nhầm thiếu gateway|Mạng công ty|T|TH
Kiểm tra cổng mạng|Không có DHCP|Cổng không có DHCP/sai VLAN|Báo không có OFFER kèm gợi ý|Cổng khoá|T|TH
Kiểm tra cổng mạng|Không đụng IP quản lý|Chạy khi đang truy cập qua mạng khác|IP quản lý nguyên vẹn|-|C|TH
Kiểm tra cổng mạng|Nhật ký riêng|Xem console-pi-dhcptest.log|Có ghi lại|-|L|TH
ARP Scan|Quét subnet|Network Tools > ARP Scan|Liệt kê thiết bị online, IP, MAC, hãng|Mạng|C|TH
Ping / Traceroute|Ping và traceroute|Nhập 8.8.8.8, tên miền|Kết quả/độ trễ; ping liên tục có đồ thị|Internet|C|TH
PCAP Capture|Bắt gói|Chọn cổng, bắt, lưu ra USB, mở bằng tshark/Wireshark|Có file pcap hợp lệ|Mạng + USB|T|TH
LLDP/CDP Discovery|Biết cắm vào switch nào|Đợi 30-60 giây, Quét lại|Tên switch, cổng, VLAN, PoE, năng lực, hệ điều hành; có Địa chỉ quản lý thì nút Mở web vào được|Switch bật LLDP/CDP|C|TH
STP/LACP/VLAN Scan|Bắt BPDU/LACP/802.1Q|Chạy trên dây đang cắm|Hiện STP, LACP, VLAN nếu có|Switch|T|TH
MTU Discovery|Đo MTU|Nhập 8.8.8.8|Con số MTU thật (PPPoE ~1492, VPN ~1400-1436); dùng MTU router trả về nếu có|Internet|T|TH
Kiểm tra DNS|So nhiều DNS|Nhập google.com|So DNS đang dùng với Google, Cloudflare, Quad9; khác hẳn thì cảnh báo (CDN khác nhau là bình thường)|Internet|T|TH
Kiểm tra chứng chỉ TLS|Xem chứng chỉ|Nhập google.com:443 và thiết bị iLO/switch|Banner xanh hợp lệ CHỈ khi hệ thống xác thực thật; tự ký/hết hạn/sai tên đều ghi rõ lý do|Internet/thiết bị|T|TH
Sơ đồ mạng 1 đoạn|Vẽ sơ đồ|Chọn cổng, Vẽ sơ đồ|Máy -> switch -> các host, mỗi hàng <=7, kèm bảng IP/MAC/hãng; không có switch thì ghi rõ (không vẽ bừa)|Mạng|T|TH
Máy chủ TFTP|Bật TFTP và tải file|Bật, switch copy running-config tftp://IP/backup.cfg; tải file về; copy dòng lệnh|Mặc định TẮT; chỉ nghe cổng dây LAN; nhận ghi file; tải được từ giao diện|Switch Cisco|C|TH
Máy chủ TFTP|Nạp firmware|copy tftp://IP/firmware.bin flash:|Switch tải được file|Switch|T|TH
Sao lưu qua cáp console|Lấy cấu hình qua console|Chọn cổng console, chạy sao lưu|Có file cấu hình khi thiết bị mất IP quản lý|Cáp console|C|TH
Netmiko Config|SSH đẩy cấu hình có xem trước|Nhập thiết bị + lệnh, xem trước rồi chạy|Xem trước đúng, chạy đúng, báo kết quả|Switch SSH|T|TH
802.1X Testing|Thử EAP với RADIUS|Nhập RADIUS, tài khoản|Kết quả xác thực; không đụng eth0|RADIUS server|L|TH
IF/THEN Automation|Quy tắc tự động|Tạo rule "nếu thấy switch quen thì gợi ý cấu hình"|Rule lưu, kích hoạt đúng; giữ khi cập nhật|Switch|L|TH
Chung|Giao diện Network Tools mới|Mở trang chủ Network Tools|Kiểm tra cổng mạng nổi bật nhất, 2 nhóm chỉ-đọc/ghi, biểu tượng Phosphor, mở từng công cụ không lỗi|Trình duyệt|C|TT
Chung|Dịch vụ nguy hiểm không tự bật|Khởi động lại|TFTP/DHCP/PXE không tự bật; cảnh báo rõ khi bật|-|C|TH
"""
