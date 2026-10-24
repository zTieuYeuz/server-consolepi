# -*- coding: utf-8 -*-
S16 = """
Duyệt toàn bộ trang|Mọi đường dẫn menu ở 4 tổ hợp|Mở từng mục menu ở Chế độ PC/cảm ứng x nền sáng/tối|Không 404/500, không lỗi JavaScript trong console, chữ đọc được, không vỡ bố cục|Trình duyệt + DevTools|C|TH
Duyệt toàn bộ trang|Các trang con (tab phụ) của Deployment OS|Mở từng tab chính + tab phụ|Tab sáng đúng mục, nội dung đúng; không rơi nhầm ngữ cảnh Triển khai phần mềm|Trình duyệt|C|TH
Duyệt toàn bộ trang|Ngữ cảnh Triển khai phần mềm vs Deployment OS|Vào Tài nguyên từ 2 menu|Cùng trang nhưng thanh tab/menu sáng đúng (Triển khai phần mềm ẩn Hệ điều hành/Driver/WinPE)|Trình duyệt|C|TH
Duyệt toàn bộ trang|Trang không tồn tại|Gõ địa chỉ sai|Trang 404 thân thiện (không 500), có nút Home|Trình duyệt|T|TH
Nhập liệu bất thường|IP/host sai định dạng|Nhập "abc", "999.1.1.1", rỗng, rất dài vào Kết nối nhanh, Phiên mới, Máy tính, Quét mạng, Ping, DNS|Báo lỗi rõ, không treo, không lỗi 500|-|C|TH
Nhập liệu bất thường|Ký tự Unicode/emoji/dấu cách trong tên|Đặt tên phiên, nhóm, kịch bản, tên cổng console, ghi chú máy, tên file tải lên|Lưu và hiển thị đúng; giới hạn độ dài được báo rõ|-|C|TT
Nhập liệu bất thường|Gửi form hai lần / bấm đúp|Bấm đúp nút Lưu, Chạy, Bật PXE, Tạo file|Không tạo trùng, không chạy hai lần|-|C|CH
Nhập liệu bất thường|Tải lại trang sau khi gửi form|F5 sau Lưu/Chạy|Không gửi lại thao tác (redirect), thông báo flash hiện một lần|-|T|TH
Nhập liệu bất thường|Nút Back/Forward của trình duyệt|Duyệt, bấm Back nhiều lần|Trang không hỏng, trạng thái đúng|-|T|CH
Nhập liệu bất thường|Hai tab cùng thao tác một dữ liệu|Sửa cùng kịch bản ở 2 tab|Lưu sau ghi đè trước, không hỏng dữ liệu|-|T|CH
Nhập liệu bất thường|Tên tệp tải lên có dấu cách, tiếng Việt, trùng tên|Tải file tên "Bộ cài (1).exe" hai lần|Lưu đúng hoặc đổi tên có kiểm soát, không ghi đè nhầm|-|C|CH
Nhập liệu bất thường|Tải lên bị ngắt giữa chừng|Ngắt mạng khi đang tải file lớn|File dở bị dọn (Dọn rác an toàn), không tính là file hợp lệ|-|C|TH
Phiên và đăng nhập|Hết phiên đăng nhập|Để phiên lâu rồi thao tác|Chuyển về đăng nhập, không mất dữ liệu đang nhập (nếu có)|-|T|CH
Phiên và đăng nhập|Đăng nhập trên nhiều thiết bị|Đăng nhập từ 2-3 máy|Hoạt động độc lập|-|T|CH
Phiên và đăng nhập|Tên máy .local (mDNS)|Truy cập http://tên-máy.local|Mở được trên máy hỗ trợ mDNS|Windows 10+/Mac|T|TH
Phiên và đăng nhập|Địa chỉ localhost/kiosk 8880|Mở 127.0.0.1:8880 trên máy|Không cần đăng nhập, chỉ trong máy|Máy|C|TH
Truy cập và khả dụng|Phím tắt, Tab, Enter trên mọi form|Dùng bàn phím|Duyệt/đánh dấu được; Ctrl+K, Esc hoạt động|-|T|CH
Truy cập và khả dụng|Vùng chạm đủ lớn (cảm ứng)|Chạm nút trên màn cảm ứng|Nút >= 44 px, không chạm nhầm|RasPad|T|TH
Truy cập và khả dụng|Trạng thái không chỉ dựa vào màu|Xem chip trạng thái|Luôn có chữ (Đang chạy/Tắt/Lỗi...)|-|T|TH
Truy cập và khả dụng|Độ tương phản chữ nền sáng/tối|Quan sát mọi trang|Chữ đọc rõ ở cả hai nền, không có chữ trắng trên nền trắng|-|C|TH
PXE nội bộ|Các dịch vụ PXE|Bật PXE rồi xem dịch vụ|dnsmasq (DHCP/TFTP/proxy), nginx, Samba chia sẻ cho WinPE chạy; tắt PXE thì tắt hết|Máy chủ|C|TH
PXE nội bộ|Cổng 67/69 đang bị chiếm|Bật PXE khi cổng bị chiếm|Báo lỗi rõ ràng, không treo, trả trạng thái cũ|-|C|TH
PXE nội bộ|Bật PXE khi không đủ file (BCD, boot.wim)|Bật PXE khi thiếu tài nguyên|Báo đúng điều kiện thiếu|-|C|TH
PXE nội bộ|Bật PXE rồi cập nhật phần mềm|Chạy cap-nhat-pi.sh khi PXE đang bật|PXE vẫn hoạt động sau cập nhật, máy khách vẫn ra menu và cài được|Pi|C|TH
PXE nội bộ|Samba của PXE|Máy WinPE truy cập chia sẻ|Truy cập được trong mạng cài đặt, chỉ lúc PXE bật|WinPE|C|TH
PXE nội bộ|Nhiều máy chọn kịch bản khác nhau|2 máy cùng boot, mỗi máy 1 kịch bản|Mỗi máy nhận đúng kịch bản và đúng tên|2 VM|C|TH
Windows cài xong|Tài khoản Administrator + tự đăng nhập|Cài xong bật lần 1 và lần 2|Lần 1 vào Administrator; nếu không tích "giữ tự động đăng nhập" thì từ lần 2 hỏi mật khẩu|VM|C|TH
Windows cài xong|Phần mềm đã cài đúng + không còn cửa sổ đen|Kiểm sau khi đăng nhập|Phần mềm có đủ, cửa sổ tiến trình tự đóng, bảng tổng kết hiện|VM|C|TH
Windows cài xong|Báo cáo sau cài: mục Gia nhập domain|Đọc BAO-CAO-TONG-KET.txt|Có mục Gia nhập domain Đạt/Lỗi, bước lỗi nêu tên|VM|C|TH
Windows cài xong|Font đã cài cho mọi tài khoản|Mở Word sau khi đăng nhập lại|Thấy đủ họ chữ đã chọn|VM|T|TH
Windows cài xong|Tuỳ chọn áp cho tài khoản tạo sau|Tạo user mới sau cài|User mới nhận đủ tuỳ chọn giao diện|VM|T|TH
Windows cài xong|Gói driver theo dòng máy được nạp|Cài máy có hãng/model khớp|Windows có driver trong gói; Lịch sử ghi tên gói|Máy giả lập SMBIOS|T|TH
Quản lý máy trạm - chi tiết|Phân trang 20 dòng/ô tìm tức thời|Danh sách có >20 mục|Phân trang đúng, ô tìm lọc ngay|Dữ liệu nhiều|T|TT
Quản lý máy trạm - chi tiết|Hiệu năng với nhiều máy|Thêm 100+ máy (dải IP)|Trang vẫn mở nhanh; báo cáo nền không làm nghẽn|100+ máy ảo/giả|C|CH
Quản lý máy trạm - chi tiết|Xuất CSV mở bằng Excel|Tải CSV phần mềm/báo cáo|Đủ tiếng Việt, đúng cột|Excel|C|TH
Quản lý máy trạm - chi tiết|Báo cáo khi máy tắt|Máy offline bấm Lấy thông tin|Báo không tới được, giữ báo cáo cũ|Máy tắt|C|TH
Quản lý máy trạm - chi tiết|Máy không có tài khoản và không có agent|Bấm Lấy thông tin|Bị bỏ qua có thông báo (cần gán tài khoản hoặc cài agent)|-|C|TT
Quản lý máy trạm - chi tiết|Chuyển giữa agent và WinRM|Máy có cả hai|Dùng agent nếu sống, nếu không dùng WinRM|Windows|C|TT
Quản lý máy trạm - chi tiết|Thẻ, địa điểm, thông tin thêm|Tạo, gán nhiều máy, xoá thẻ đang dùng|Dữ liệu nhất quán|-|T|TT
Quản lý máy trạm - chi tiết|Xoá máy khỏi danh sách|Xoá máy có agent|Máy bị xoá khỏi danh sách; agent bị từ chối ở nhịp sau|Windows|C|TH
Quản lý máy trạm - chi tiết|Trợ lý phiên người dùng|Máy in/màn hình riêng của người dùng|Xuất hiện trong tab Máy in/Màn hình (đánh dấu của người dùng)|Windows|T|TH
VNC chi tiết|Nhiều phiên VNC cùng lúc|Mở 2 phiên 2 máy|Độc lập, mỗi phiên PIN riêng, cầu WebSocket tách|2 Windows|T|TT
VNC chi tiết|Bàn phím và chuột noVNC|Gõ, di chuột, Ctrl+Alt+Del|Hoạt động|Windows|C|TH
VNC chi tiết|Khoá sau hết giờ xin phép|Không bấm gì ở hộp xin phép|Hết giờ coi là từ chối, không cho điều khiển|Windows|C|TH
VNC chi tiết|Cổng 5900 không mở ra ngoài|Quét cổng 5900 từ máy khác|Đóng (tunnel chỉ 127.0.0.1) hoặc chỉ cho IP Console System (trực tiếp)|Windows|C|TH
Agent chi tiết|Agent chạy nhiều PowerShell song song|Giao 5 lệnh cùng lúc|Tối đa 4 chạy song song, còn lại chờ|Windows|T|CH
Agent chi tiết|Lệnh chạy quá thời gian|Giao lệnh Start-Sleep dài hơn timeout|Bị dừng đúng timeout, báo lỗi|Windows|C|CH
Agent chi tiết|Output lớn|Lệnh in rất nhiều dòng|Trả về đủ/cắt có thông báo, không treo agent|Windows|T|CH
Agent chi tiết|Ngắt mạng giữa lúc chuyển file|Cắt mạng khi tải 1 GB|Báo lỗi, tạo lại được; file dở được dọn|Windows|C|CH
Agent chi tiết|Server khởi động lại|Restart console-pi-dashboard|Agent thấy 502, tự nối lại; việc đang chờ trong RAM mất, profile giữ|Windows|C|TH
Agent chi tiết|Đồng hồ máy lệch nhiều|Chỉnh giờ máy lệch >10 phút|TLS thất bại hoặc chẩn đoán cảnh báo lệch giờ|Windows|T|CH
Agent chi tiết|Máy đổi IP / đổi mạng|Chuyển mạng khi agent chạy|Agent nối lại; Địa chỉ nguồn cập nhật|Windows|C|CH
Agent chi tiết|Cài MSI đè / cài lại trên máy đã có agent|Cài lại MSI|Không tạo máy trùng; chứng chỉ mới thay chứng chỉ cũ|Windows|C|CH
Agent chi tiết|Cài script lên máy đã cài bằng MSI|Chạy script trên máy đã có MSI|Hoạt động hoặc báo rõ (chưa kiểm chứng)|Windows|T|CH
Agent chi tiết|Hai máy cùng tên + cùng IP NAT|Hai máy tên giống sau cùng NAT|Có thể bị gộp một bản ghi (giới hạn đã biết) - ghi lại hành vi|Windows|T|CH
Agent chi tiết|Server đổi cổng mTLS|Đổi cổng sau khi đã cài agent|Agent cũ không nối được cổng mới -> cần cài lại bằng file mới (có cảnh báo trước khi lưu)|Windows|C|TH
Agent chi tiết|Máy bị khoá bởi AppLocker/WDAC|Cài trên máy có chính sách|Bị chặn (cần ký số hoặc allowlist) - ghi nhận|Windows doanh nghiệp|C|CH
Agent chi tiết|Phiên bản .NET Framework|Thử trên máy chỉ có .NET 4.0|Biên dịch tại chỗ chạy được (C# 5)|Windows 10 cũ|T|CH
Agent chi tiết|MSI sửa chữa (repair) / nâng cấp|msiexec /f hoặc cài MSI mới đè|Giữ cấu hình, không mất chứng chỉ|Windows|T|CH
Profile chi tiết|Profile cập nhật khi Pi tắt|Sửa profile khi agent mất kết nối|Agent nhận bản mới khi nối lại|Windows|C|TH
Profile chi tiết|Nhiều profile cùng máy|Gán 2 profile|Cả hai áp dụng, thứ tự rõ ràng|Windows|T|CH
Profile chi tiết|Profile chu kỳ + Chạy ngay|Đặt chu kỳ, bấm Chạy ngay|Chạy đúng, kết quả (ack) gửi bù|Windows|C|TH
Triển khai chi tiết|Huỷ đợt giữa chừng|Bấm Dừng khi đang chạy|Dừng ở bước kế, ghi trạng thái|Windows|C|TH
Triển khai chi tiết|Token tải file hết hạn|Dùng link sau 2 giờ|Bị từ chối|Windows|C|TH
Triển khai chi tiết|Ghi nhận mật khẩu admin mã hoá|Đổi/xoá tài khoản quản trị|Máy dùng tài khoản đó bị báo thiếu tài khoản|-|C|TH
Dữ liệu và sao lưu|Lịch sử cài đặt tối đa 2000 máy|Tạo >2000 dòng|Giữ 2000 gần nhất|Dữ liệu giả|L|TD
Dữ liệu và sao lưu|Sao lưu có chứa dữ liệu agent/UEM?|Kiểm nội dung file sao lưu|Ghi nhận: sao lưu KHÔNG gồm PKI/mã ghi danh/file agent đã tạo (cần sao lưu riêng thư mục dữ liệu nếu chuyển server)|Pi|C|CH
Dữ liệu và sao lưu|Chuyển dữ liệu sang server mới|Chép thư mục dữ liệu /var/lib/console-pi|Giữ kịch bản, tài nguyên, Lịch sử; agent cũ chỉ nối lại nếu PKI cũng được chép|2 server|C|CH
Dữ liệu và sao lưu|Dọn rác an toàn không xoá dữ liệu|Dọn rồi kiểm kịch bản/OS/driver|Không mất gì ngoài gói đã tải, log cũ, file dở|-|C|TH
"""
