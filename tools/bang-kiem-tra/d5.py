# -*- coding: utf-8 -*-
S14 = """
Kho file|Nơi lưu: USB ưu tiên|Cắm USB rồi tải file lên Kho lưu trữ > Kho file|Dòng "Nơi đang lưu" ghi USB; không có USB thì ghi vào thẻ/ổ máy|USB|C|TH
Kho file|Tải lên file lớn|Tải ISO 5 GB|Ghi thẳng ra đĩa không làm đầy RAM; thanh tiến độ|ISO|C|TH
Kho file|Chặn khi dưới 3 GB trống|Làm đầy đĩa|Chặn tải lên, thông báo rõ|-|C|TH
Kho file|SHA-256 + tải về|Xem danh sách File đang có|Mỗi file kèm SHA-256, nút tải về đúng|-|C|TH
Kho file|Chỉ nhận file dữ liệu|Thử tải .sh/.exe/.py|Bị từ chối (chỉ iso, img, bin, tar, gz, xz, zip, conf, cfg...)|-|C|TH
Nhật ký|Lỗi ứng dụng|Nhật ký > Lỗi ứng dụng|Lỗi 7 ngày kể cả sau logrotate (đọc cả file xoay vòng .1/.gz); lỗi 404 bình thường không bị tính thành 500|-|C|TH
Nhật ký|Cảnh báo dịch vụ|Nhật ký > Cảnh báo dịch vụ|Chỉ cảnh báo/lỗi của dịch vụ chính|-|T|TH
Nhật ký|Thao tác (ai làm gì)|Nhật ký > Thao tác|Đăng nhập thành công/thất bại, đăng xuất, tắt máy/khởi động lại, bật/tắt PXE, xoá kịch bản/OS...; có thời gian, user@địa chỉ; không ghi mật khẩu|-|C|TT
Nhật ký|Log toàn bộ + bộ lọc|Lọc theo nguồn, dịch vụ, thời gian, mức độ, từ khoá (không dấu)|Lọc đúng; dòng "trang tự hỏi số liệu" lặp đã lược bỏ; tìm 7 ngày ~7 giây|-|C|TH
Nhật ký|Tải về .txt|Bấm Tải về|Xuất đúng phần đang lọc|-|C|TH
Nhật ký|Giữ 7 ngày rồi tự dọn|Kiểm sau 7 ngày|Không đầy thẻ nhớ (logrotate maxage 7)|-|T|TH
Nhật ký|Nhật ký tự kiểm tra|Chọn nguồn console-pi-selftest.log|Có kết quả boot gần nhất|-|C|TH
Nguồn điện|Tắt máy / Khởi động lại có xác nhận|Nguồn điện > Tắt máy|Có hộp xác nhận, tắt an toàn (đợi đèn Pi ngừng nháy); ghi Nhật ký Thao tác|Pi/x86|C|TH
Nguồn điện|Cảnh báo sụt áp|Dùng nguồn yếu|Tổng quan báo sụt áp "đang xảy ra" trước khi hỏng|Pi|C|TH
Nguồn điện|Vỏ RasPad|Bấm Tắt máy|Chỉ tắt Pi, không tắt màn hình/mạch nguồn vỏ; có hướng dẫn gạt công tắc sau khi đèn ngừng nháy|RasPad|L|TH
Góp ý|Gửi góp ý có file đính kèm|Điền loại, nội dung, đính kèm ảnh/tài liệu (<=10 tệp, mỗi tệp <=20 MB), Gửi|Gửi tới tác giả; hiện trong "Góp ý đã gửi từ máy này"|Internet|C|TH
Góp ý|Không có mạng vẫn gửi được|Tắt mạng, gửi, bật mạng|Lưu trên máy và tự gửi khi có mạng; trạng thái cập nhật|-|C|TH
Góp ý|Gửi kèm thông tin máy|Tích/bỏ tích|Chỉ gửi tên máy, phiên bản, loại thiết bị; KHÔNG gửi địa chỉ mạng, mật khẩu, cấu hình|-|C|TH
Giải trí|Mở YouTube/TikTok|Giải trí > chọn|Mở trang thật, có âm thanh|Màn cảm ứng + Internet|T|TH
Giải trí|Nút nổi 🏠 Console Pi|Bấm liên kết sang website khác|Nút nổi (góc dưới trái) luôn quay về giao diện, mọi trang được tải|-|T|TH
Tài liệu|Mở Tài liệu|Cài đặt > Tài liệu|Mở được; khung Giới thiệu có nút mở trang hướng dẫn (cần Internet; không mạng thì mở trên điện thoại)|-|T|TH
Tài liệu|Tài liệu theo tab, dễ tra|Mở /docs|Tab Cài đặt, Bắt đầu, Tính năng, Kỹ thuật... hiển thị đúng|-|L|TH
Trang web đi kèm|Trang tải về / hướng dẫn console-docs|Mở https://console-docs.home-server.id.vn|Hiển thị đúng phiên bản + link tải + SHA-256|Internet|T|TH
"""

S15 = """
Nền tảng|Raspberry Pi 3, 4, 5|Cài và chạy bộ kiểm tra chính trên từng đời|Chạy ổn định, đủ chức năng (Bluetooth PAN, màn hình RasPad chỉ có trên Pi)|Pi 3/4/5|C|TH
Nền tảng|x86 amd64 (Debian 13)|Cài ISO, chạy bộ kiểm tra|Đủ chức năng trừ Bluetooth PAN/RasPad|Máy x86|C|TH
Nền tảng|x86 i386 (Debian 12, Python 3.11)|Cài ISO i386|Dashboard chạy; kiem-python311.sh = 0 lỗi|Máy/VM 32-bit|C|TT
Nền tảng|VMware / KVM / Hyper-V|Cài Console System làm máy ảo|Chạy; máy khách PXE cùng mạng ảo (NAT/bridge) boot được|Hypervisor|C|TH
Nền tảng|Trình duyệt Edge / Chrome / Firefox / Safari (iPad, iPhone)|Mở các trang chính|Hiển thị đúng; terminal chép/dán đúng; trên iPad không hiện bàn phím ảo|Nhiều trình duyệt|C|TH
Nền tảng|Không có Internet|Rút Internet, dùng Console, Network Tools, PXE|Vẫn chạy (Internet chỉ cần cho kho, driver tải, truy cập từ xa, góp ý)|Mạng cô lập|C|TH
Nền tảng|Mạng công ty có router/DHCP|Cắm vào mạng công ty|Không làm loạn mạng (dịch vụ ảnh hưởng mạng tắt sẵn)|Mạng công ty|C|TH
Nền tảng|Đồng hồ hệ thống|Kiểm giờ Pi sau boot không có Internet|Cảnh báo ở Kiểm tra sẵn sàng; domain cần lệch <5 phút|Pi|T|TH
Hiệu năng / chịu tải|Nhiều máy cài PXE cùng lúc|Cài 5-10 máy 1 lúc|Tiến trình từng máy đúng; bộ cài trên thẻ SD chậm (khuyên SSD USB 3)|Nhiều VM/máy|C|CH
Hiệu năng / chịu tải|Tải file lớn nhiều lần|Tải 2 file 5 GB|Không 502/500; thư mục tạm /var/tmp; dọn rác an toàn|-|C|TH
Hiệu năng / chịu tải|Đĩa gần đầy|Đổ đầy đĩa|Cảnh báo, chặn tải lên, không hỏng dịch vụ|-|C|TH
Hiệu năng / chịu tải|Mất điện đột ngột|Rút nguồn Pi khi đang chạy|Khởi động lại bình thường (khuyến cáo tắt đúng cách vẫn nên nhắc)|Pi|T|CH
Hiệu năng / chịu tải|Dashboard chạy lâu ngày|Để chạy 7 ngày|Không rò rỉ bộ nhớ, log xoay vòng, selftest sạch|Pi/x86|C|CH
Hiệu năng / chịu tải|Pi khởi động lại giữa chừng việc|Khởi động lại Pi khi đang triển khai/agent chạy|Việc đang chờ trong RAM bị mất (đã biết); profile agent đã lưu về máy thì không mất|Pi + agent|C|TH
Bảo mật|XSS trên mọi trang|Dữ liệu độc hại ở tên máy, thẻ, ghi chú, tên file|Mọi chỗ đều thoát ký tự, không chạy script|-|C|TT
Bảo mật|Path traversal|Tải/xoá file với ../ trong tên|Bị chặn|-|C|TH
Bảo mật|Chèn lệnh|Host/user SSH, tên file, tham số có ký tự đặc biệt|Không chạy lệnh chèn (đã vá 0.4.16/0.4.17)|-|C|TH
Bảo mật|Gói sao lưu độc hại (zip slip)|Nạp file sao lưu có ../|Bị chặn sạch|-|C|TH
Bảo mật|Mật khẩu/khoá không lộ ra log hay trình duyệt|Xem Nhật ký, nhật ký tác vụ, giao diện, file dữ liệu|Không có mật khẩu rõ (kể cả mật khẩu admin Windows, mật khẩu SSH, passkey, token Cloudflare)|-|C|TT
Bảo mật|Quyền file khoá/token|ls -l các file khoá, token, PKI|Chỉ root (0600/0700)|Pi|C|TT
Bảo mật|Token tải file 2 giờ chỉ IP nội bộ|Dùng link token từ IP ngoài / sau 2 giờ|Bị từ chối|-|C|TH
Bảo mật|Đăng nhập sai nhiều lần|Thử sai 10 lần|Ghi vào Nhật ký Thao tác; cơ chế chống dò mật khẩu chưa được ghi nhận - ghi lại kết quả quan sát|-|T|CH
Bảo mật|Cổng 8443 chỉ nhận mTLS|Quét cổng 8443 từ ngoài|Chỉ endpoint cài đặt (mã ghi danh) và agent có chứng chỉ trả lời; còn lại 403/404|Mạng ngoài|C|TT
Bảo mật|Header X-CS-* giả mạo|Gọi cổng 80 với header giả|Không tin (cần bí mật nginx)|-|C|TT
Bảo mật|Cloudflare Access|Bật Access trước tunnel|Người lạ bị chặn ngay từ biên|Cloudflare|T|CH
Cập nhật / phục hồi|Cập nhật giữ dữ liệu|Cập nhật qua cap-nhat-pi.sh|Cấu hình, kịch bản, OS, driver, PKI, mã ghi danh, file agent đã tạo còn nguyên|Pi|C|TH
Cập nhật / phục hồi|Trả lại bản cũ|Chạy lệnh tar trả lại in sau cập nhật|Về đúng bản cũ, dịch vụ chạy|Pi|T|CH
Cập nhật / phục hồi|Sao lưu rồi khôi phục sang máy mới|Dựng server mới, nạp sao lưu|Kịch bản, tham số, thư viện lệnh, kết nối kho trở lại (không có bộ Windows/phần mềm)|2 máy|C|TH
Cập nhật / phục hồi|PKI/agent sau khi chuyển server|Chuyển sang server mới|Agent cũ KHÔNG nối vào server mới (CA khác) -> phải cài lại bằng file mới (lưu ý khi mô phỏng)|2 server|C|CH
Ngôn ngữ|Tiếng Việt đủ dấu|Duyệt mọi trang|Không lỗi mã hoá, CSV mở bằng Excel đủ dấu|-|C|TT
Ngôn ngữ|Tìm không dấu|Tìm chức năng, tìm kho, tìm phần mềm|Ra đúng kết quả|-|T|TT
"""
