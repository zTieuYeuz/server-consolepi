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

### Console
Truy cập cổng RS232 qua web (ttyd + microcom trong tmux). Tự nhận cổng khi cắm
cáp USB-serial, đặt tên gợi nhớ cho từng cổng.

### Chẩn đoán mạng (9 công cụ)
ARP Scan · Ping/Traceroute · PCAP Capture · LLDP/CDP Discovery ·
DHCP Testing · STP/LACP/VLAN Detection · Netmiko (SSH cấu hình switch) ·
802.1X Testing · IF/THEN Automation

### Terminal & Tự động hoá
- **Terminal local** — dòng lệnh trên Pi, phiên tmux không mất khi đóng trình duyệt
- **SSH** — vừa terminal tương tác, vừa chạy hàng loạt có xem trước
- **Thư viện lệnh** — lưu/sửa/xoá tập lệnh, sẵn 5 tập lệnh Cisco. Dán được
  thẳng vào terminal (không tự chạy — bạn xem lại rồi mới bấm Enter)

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
install.sh              Cài đặt một lệnh (idempotent)
uninstall.sh            Gỡ cài đặt
src/app.py              Lắp ráp app Flask
src/ui/                 Giao diện + đăng nhập
    layout.py           Khung chung: thanh trái + thanh trạng thái mạng
    auth.py             Đăng nhập qua PAM
    home.py             Trang Tổng quan
    network.py          WiFi / AP / Bluetooth
    terminal.py         Terminal local + API gửi phím vào tmux
    ssh.py              SSH tương tác + chạy hàng loạt
    commands.py         Thư viện lệnh
    settings.py         Xoay màn hình, thông tin hệ thống
    docs.py             Tài liệu tra cứu ngoại tuyến
src/nettools/           9 công cụ chẩn đoán mạng
src/scripts/            Script hệ thống
config/                 Cấu hình nginx
systemd/                Định nghĩa dịch vụ
```

---

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
