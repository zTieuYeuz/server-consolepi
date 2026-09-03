# Console Pi Toolkit

Biến Raspberry Pi thành **console server + bộ công cụ chẩn đoán mạng** di động.
Cắm cáp console vào switch/router, truy cập qua web để điều khiển từ xa —
không cần laptop, không cần PuTTY.

Lấy cảm hứng từ netool.io Pro2 ($299), làm lại bằng phần cứng sẵn có.

---

## Cài đặt — một lệnh

```bash
curl -fsSL https://raw.githubusercontent.com/USER/consolepi-toolkit/main/install.sh | sudo bash
```

Thiết bị **không gắn màn hình** (bỏ qua giao diện kiosk, tiết kiệm ~500MB):

```bash
curl -fsSL https://raw.githubusercontent.com/USER/consolepi-toolkit/main/install.sh | sudo bash -s -- --no-screen
```

Cài từ thư mục có sẵn (không cần mạng):

```bash
git clone https://github.com/USER/consolepi-toolkit.git
sudo bash consolepi-toolkit/install.sh --local consolepi-toolkit
```

> **Chạy lại được nhiều lần.** Cài đè bản mới không làm mất: WiFi đã lưu,
> thư viện lệnh, tên cổng console, rule IF/THEN, cấu hình AP, hướng màn hình.

---

## Tính năng

### Kết nối — 4 đường vào, luôn có ít nhất một đường
| Cách | Địa chỉ | Dùng khi |
|---|---|---|
| WiFi client | `http://<hostname>.local` | Có WiFi quen thuộc |
| Tự phát AP `ConsolePi` | `http://192.168.50.1` | Tới nơi lạ, không có WiFi |
| Cáp LAN thẳng vào laptop | `http://<hostname>.local` | Không có WiFi lẫn switch |
| Bluetooth PAN | `http://192.168.60.1` | Phương án cuối |

Pi tự chuyển giữa WiFi client và AP mỗi 2 phút, có nút khoá AP khi cần giữ nguyên.

### Console — nhận mọi loại cáp
Truy cập cổng RS232 qua web (ttyd + microcom trong tmux). Nhận **cả hai họ thiết bị**:

| Loại cáp | Thiết bị | Cổng |
|---|---|---|
| USB-serial thường (FTDI, Prolific, CH340) | `/dev/ttyUSB0-3` | 8001-8004 |
| Cáp Cisco USB Console (micro-USB), thiết bị CDC-ACM | `/dev/ttyACM0-3` | 8005-8008 |

Udev rule tự khởi động dịch vụ cho **bất kỳ** cổng serial USB mới cắm — cáp lạ
chưa từng thấy vẫn tự nhận. Dashboard hiện tên chip để biết đang cắm cáp gì.
Đặt được tên gợi nhớ cho từng cổng.

### Bluetooth — phân biệt đúng loại thiết bị
Giải mã **Class of Device** theo chuẩn Bluetooth (không chỉ dựa vào `Icon`), kết
hợp với UUID dịch vụ mà thiết bị quảng cáo. Nút kết nối khớp đúng hồ sơ:
máy tính/điện thoại → **PAN** (mạng), bàn phím/chuột → **HID**. Thiết bị đã ghép
cặp tự nối lại khi bật lên (`ReconnectUUIDs`).

### Chẩn đoán mạng (15 công cụ)
ARP Scan · Ping/Traceroute · PCAP Capture · LLDP/CDP Discovery ·
**Kiểm tra toàn diện cổng mạng** (tốc độ/duplex, lỗi đường truyền, PoE, DHCP,
Internet, băng thông qua Cloudflare — một nút bấm) · STP/LACP/VLAN Detection ·
**MTU Discovery** (phát hiện PPPoE/VPN làm giảm MTU) ·
**Kiểm tra DNS** (đối chiếu nhiều DNS server, phát hiện hijack) ·
**Kiểm tra chứng chỉ TLS** (subject/issuer/hạn dùng, không bao giờ giả vờ tin cậy) ·
**Ping liên tục kèm đồ thị sống** (theo dõi rớt gói khi rung dây) ·
**Sơ đồ mạng 1 đoạn** (Pi → switch → host, ghép ARP + LLDP) ·
**Máy chủ TFTP** (sao lưu/nạp cấu hình, firmware switch) ·
Netmiko (SSH cấu hình switch) · 802.1X Testing · IF/THEN Automation

### Terminal & Tự động hoá
- **Terminal local** — dòng lệnh trên Pi, phiên tmux không mất khi đóng trình duyệt
- **SSH** — vừa terminal tương tác, vừa chạy hàng loạt có xem trước
- **Thư viện lệnh** — lưu/sửa/xoá tập lệnh, sẵn 5 tập lệnh Cisco. Dán được
  thẳng vào terminal (không tự chạy — bạn xem lại rồi mới bấm Enter)

### Sức khoẻ thiết bị & nguồn
Cảnh báo **sụt áp** (`vcgencmd get_throttled`) — nguyên nhân phổ biến nhất làm Pi
treo hoặc hỏng thẻ nhớ, và nó báo *trước* khi hỏng. Kèm nhiệt độ CPU, tải, RAM,
đĩa, thời gian chạy. Nút **Tắt máy / Khởi động lại** có hộp xác nhận.

### Kho file (ISO, firmware)
Mang theo bộ cài OS, firmware switch, file cấu hình để dùng khi không có internet.
Ghi theo luồng ra đĩa (không nạp vào RAM), ưu tiên USB nếu có cắm, chặn khi sắp
đầy, kèm SHA256 để đối chiếu. nginx đã nâng giới hạn lên 8GB.

### Cắm thẳng thiết bị (iLO / iDRAC / IPMI)
Khi máy chủ tắt lịm và chỉ còn cổng quản lý: Pi thành mạng mini `192.168.99.1`,
cấp DHCP, quét ARP tìm thiết bị, nhận diện hãng qua OUI (HPE, Dell, Supermicro,
Lenovo, Cisco), mở thẳng giao diện web của thiết bị. Quét được cả dải IP tĩnh.

### Truy cập từ xa (Cloudflare Tunnel)
Đưa Pi tới điểm xa, người ở đó chỉ cắm console và cắm mạng — bạn ngồi nhà vẫn vào
cấu hình được. Không cần mở port, không cần IP tĩnh, chạy được cả sau 4G.

### Tự kiểm tra
```bash
sudo /opt/console-pi/scripts/selftest.sh
```
Kiểm tra toàn bộ dịch vụ, mọi trang web, từng cổng console, và ba kịch bản:
cáp LAN thẳng, tự phát AP khi không có WiFi, thiết bị Bluetooth đã ghép tự nối lại.

### Màn hình cảm ứng (tuỳ chọn)
Chế độ kiosk toàn màn hình, bàn phím ảo, nút xoay màn hình. Tự động bỏ qua
nếu thiết bị không gắn màn hình.

---

## Kiến trúc

```
Trình duyệt ──> nginx :80 ──┬──> Flask 127.0.0.1:5000    (giao diện)
                            ├──> ttyd 127.0.0.1:8010     (Terminal local)
                            ├──> ttyd 127.0.0.1:8011     (Terminal SSH)
                            └──> ttyd 127.0.0.1:800x     (Console serial)
```

Các `ttyd` chỉ lắng nghe `127.0.0.1` — không vào thẳng được từ mạng. Mọi
đường vào đều qua nginx và bị kiểm tra đăng nhập trước (`auth_request`).

**Đăng nhập** bằng tài khoản Linux của chính Pi (qua PAM). Không có tài khoản
riêng, không lưu mật khẩu trên dashboard.

**Ngoại lệ có ý:** truy cập từ chính màn hình gắn trên Pi (`127.0.0.1`) không
hỏi đăng nhập — để bật máy lên là dùng được ngay. Truy cập từ mạng vẫn phải
đăng nhập. Tắt ngoại lệ này bằng `"local_screen_no_login": false` trong
`/opt/console-pi/config.json`.

---

## Cấu trúc mã nguồn

```
install.sh              Cài đặt một lệnh (chạy lại được nhiều lần)
uninstall.sh            Gỡ cài đặt
src/app.py              Lắp ráp Flask
src/ui/                 layout · auth · home · health · network · terminal
                        ssh · commands · storage · direct · remote · docs · settings
src/nettools/           15 công cụ chẩn đoán mạng + static/
src/scripts/            wifi-fallback · ttyd-one · term-launch · kiosk-start
                        selftest · bt-auto-agent · bt-nap-daemon · bt-pan0-setup
                        console-bashrc · grc-cisco.conf
config/                 nginx · udev (serial, wifi, cảm ứng)
systemd/                13 unit
```

## Yêu cầu

- Raspberry Pi 3 / 4 / 5 (đã kiểm chứng trên Pi 4)
- Raspberry Pi OS Lite (Debian 12/13) 64-bit
- Cáp USB-serial (FTDI/Prolific) cho chức năng console
- Màn hình HDMI + cảm ứng USB (tuỳ chọn)

---

## Gỡ cài đặt

```bash
sudo /opt/console-pi/uninstall.sh            # giữ lại cấu hình
sudo /opt/console-pi/uninstall.sh --purge    # xoá sạch
```

---

## Lưu ý bảo mật

Dashboard chạy **HTTP không mã hoá**. Trong mạng nội bộ hoặc qua AP `ConsolePi`
thì chấp nhận được. Nếu mở ra internet, mật khẩu Linux sẽ truyền dạng rõ —
lúc đó cần thêm HTTPS hoặc chỉ truy cập qua VPN.

Tab Terminal và SSH cho **quyền root đầy đủ**. Đó là lý do có lớp đăng nhập.
