# Sửa theo test trên .30 (26/10/2026)

| Mục | Việc | Trạng thái |
|---|---|---|
| 1.1 | Phiên "Kết nối nhanh gần đây": thêm nút ✕ xóa | xong, test tự động |
| 1.2 | Gốc lỗi: `scripts/phien-mo.sh` (và vài script) mất quyền chạy trong bản phát hành -> ttyd không mở được phiên. Sửa: 755 trong git + unit gọi qua `/bin/bash` + test canh quyền | xong; cần cài bản mới lên .30 |
| 2.1 | Ping / Traceroute / Chạy cả 2: 3 nút riêng | xong |
| 2.2 | PCAP: thêm giải thích dùng khi nào (bắt trên cổng mạng đã chọn, không phải cổng serial) | xong |
| 2.3 | LLDP/CDP: ISO không bật CDP cho lldpd như Pi (`DAEMON_ARGS="-c"`); đã thêm vào hook ISO. Nguyên nhân còn lại là vật lý: .30 cắm sau switch không chuyển LLDP | xong phần mã |
| 2.4 | Hướng dẫn test Netmiko / 802.1X / IF-THEN | `HUONG-DAN-TEST-NETTOOLS.md` |
| 3.1 | "Tự động đăng nhập tài khoản Administrator" + cảnh báo + popup xác nhận | xong |
| 4.1 | Xóa dòng kết quả (từng máy / tất cả thành công / tất cả lỗi) trong bảng tiến độ triển khai | xong, test |
| 4.2 | WinRM có ổn không | xem báo cáo trả lời |
| 4.3 | Script `bat-winrm.ps1` (tải ở trang Triển khai phần mềm; bản sao trong kho `tools/windows/`) | xong, chưa chạy trên Windows thật |
| 5.1 | Xóa máy khỏi quản lý (máy có agent: ẩn, tự hiện lại khi agent báo nhịp) | xong, test |
| 5.2 | Tab Dòng lệnh (CMD/PowerShell) | xong, test với client giả; chưa thử Windows thật |
| 5.3 | Bỏ tab Triển khai trùng ở từng máy | xong |
| 5.4 | Tab Dịch vụ + Tiến trình (xem, chạy/dừng/khởi động lại, kiểu khởi động, kết thúc tiến trình) | xong, test client giả |
| 5.5 | Agent tự cập nhật: đã có sẵn (so sánh phiên bản mỗi nhịp, tự biên dịch bản mới). Thêm test ép tăng `VER_FILE` khi sửa mã C# | xong |
| 5.6 | Profile: giải thích + sắp xếp theo bước | xong |
| 5.7 | Lỗi hiển thị nút "Chọn nhóm máy" (dấu `"` trong thuộc tính HTML) | xong |
| 5.8 | RustDesk Server tích hợp + cài client qua agent / script | xong phần máy chủ (chạy thật hbbs trên máy build); client Windows chưa thử thật |
| 5.9 | Tab "Sửa lỗi in/chia sẻ" (kịch bản duyệt sẵn) | xong, test client giả; chưa thử Windows thật |

Chưa làm được: kiểm trực tiếp SSH tới 192.168.110.21 / 192.168.100.2 qua giao diện (chỉ xác nhận SSH tới .21 đăng nhập được từ máy build; 192.168.100.2 chưa thử).
