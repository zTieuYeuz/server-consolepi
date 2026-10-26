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
| 5.8 | RustDesk Server tích hợp + cài client kèm máy chủ ID / chuyển tiếp (agent, Triển khai phần mềm, script) | xong, thử thật trên .30 + .33 (agent và WinRM) |
| 5.9 | Tab "Sửa lỗi in/chia sẻ" (kịch bản duyệt sẵn) | xong, test client giả; chưa thử Windows thật |

Chưa làm được: kiểm trực tiếp SSH tới 192.168.110.21 / 192.168.100.2 qua giao diện (chỉ xác nhận SSH tới .21 đăng nhập được từ máy build; 192.168.100.2 chưa thử).

## RustDesk làm lại (26/10 tối, theo yêu cầu anh)
- Bỏ hướng web: gõ chữ qua web client không ổn. Đã gỡ khỏi mã: thẻ rustdesk-api, chế độ WebSocket, hướng dẫn Cloudflare. RustDesk Server bản miễn phí chỉ nhận máy đăng ký ID qua UDP 21116, Cloudflare Tunnel không chuyển UDP.
- Cấu hình chỉ còn **Máy chủ ID** và **Máy chủ chuyển tiếp** (để trống = trùng máy chủ ID; cả hai để trống = IP LAN). Cổng cần mở ra Internet: TCP 21115, 21116, 21117 và UDP 21116. Máy trong LAN cũng dùng địa chỉ công khai nên router cần NAT loopback.
- Cài client luôn kèm máy chủ ID / chuyển tiếp / key / mật khẩu chung, dùng chung `cai_va_ghi()`: nút Cài ở trang RustDesk (agent), bước **RustDesk** trong Triển khai phần mềm (WinRM, kể cả Chạy nhanh), bộ cài `rustdesk*.exe/.msi` trong Tài nguyên (kiểm SHA-256 chính file đó). Danh mục WinGet không có gói RustDesk.
- Cài client ghi cả cấu hình dịch vụ lẫn cấu hình riêng từng người dùng (C:\Users\*\AppData\Roaming\RustDesk). Bước "chỉ cài một lần" tính theo địa chỉ máy chủ: đổi máy chủ thì lần chạy sau cài lại.
- Bộ cài chạy qua WMI `Win32_Process.Create` để tách khỏi phiên WinRM (WinRM đóng phiên giết tiến trình con, làm máy mất dịch vụ RustDesk khi cài đè); chờ dịch vụ mới chạy rồi mới cấu hình.
- Thử thật trên .33: gỡ RustDesk → cài bằng agent (1 phút 23 giây) → `RustDesk2.toml` dịch vụ đúng máy chủ/key, nhật ký RustDesk `start udp: 192.168.110.30:21116` + độ trễ. Cài qua kịch bản WinRM 2 lần (lần đầu máy thiếu dịch vụ, lần sau cài đè): xong, dịch vụ chạy, đăng ký lại. Cài lại bằng agent sau khi cố ý đổi cấu hình người dùng sang `dummy.invalid`: file được sửa về .30.
- Chưa thử: địa chỉ công khai thật (chờ anh mở cổng và đưa tên miền/IP), máy ở ngoài Internet, NAT loopback của router.
