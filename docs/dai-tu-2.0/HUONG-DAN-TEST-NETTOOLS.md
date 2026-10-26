# Hướng dẫn test Netmiko, 802.1X, IF/THEN (Network Tools)

Cả 3 công cụ đều cần **một thiết bị/máy đóng vai bị-test**. Console System chỉ là bên đi test.

## 1. Netmiko (đẩy cấu hình qua SSH)
Trang đi theo 4 bước an toàn: Test kết nối (chỉ chạy 1 lệnh đọc) -> Preview (chưa kết nối) -> Run (ghi thật). Ô "lưu vĩnh viễn" mặc định tắt.
- **Thiết bị thử không rủi ro:** một máy Linux có SSH (ví dụ 192.168.110.21). Chọn device type `linux`, nhập user/mật khẩu, lệnh test `hostname`. Rồi Preview và Run với lệnh vô hại như `echo ok > /tmp/netmiko-test`.
- **Switch/router thật:** chọn đúng loại (`cisco_ios`, `hp_procurve`, `mikrotik_routeros`...). Bước Test với `show version`. Chỉ khi OK mới Run lệnh cấu hình, và **không** tick lưu vĩnh viễn ở lần thử đầu.
- Mọi lần chạy ghi nhật ký (không có mật khẩu) trong trang Nhật ký.

## 2. 802.1X (thử RADIUS bằng eapol_test)
Công cụ nói chuyện UDP thẳng tới RADIUS server, **không** đụng cổng mạng của máy nên không làm rớt kết nối.
- Cần một **RADIUS server** (thiếu hiện tại). Cách dễ nhất: trên một máy Linux khác cài `sudo apt install freeradius`, thêm user thử trong `/etc/freeradius/3.0/users` (ví dụ `thu Cleartext-Password := "mk123"`), thêm client là IP máy Console System trong `clients.conf` (secret `testing123`), rồi `sudo systemctl restart freeradius`.
- Trên trang 802.1X nhập: IP RADIUS, port 1812, secret `testing123`, EAP `PEAP`, phase2 `MSCHAPV2`, user `thu`, mật khẩu `mk123`. Kết quả mong đợi: `SUCCESS`. Sai mật khẩu phải ra `FAILURE`.

## 3. IF/THEN (gợi ý lệnh theo thiết bị phát hiện bằng LLDP)
Quy tắc dạng "nếu tên/IP thiết bị lân cận khớp mẫu thì gợi ý bộ lệnh Netmiko". Nó **không** tự chạy, bạn phải bấm xác nhận qua Preview/Run.
1. Vào trang LLDP/CDP, xem tên thiết bị lân cận đang thấy (ví dụ `SW-TANG1`).
2. Vào IF/THEN, thêm quy tắc: mẫu `SW-*`, bộ lệnh `show vlan brief`, loại thiết bị.
3. Quay lại LLDP khi có thiết bị khớp, trang sẽ gợi ý bộ lệnh. Bấm sang Netmiko để Preview rồi Run.
4. Dùng Xuất/Nhập (mã hóa bằng mật khẩu bạn đặt) để sao lưu quy tắc.
Muốn thử khi chưa có switch: đặt mẫu khớp tên Pi/ASUS mà LLDP đang thấy, và dùng lệnh vô hại.
