# Console System (Console Pi)

**Console server kiêm trạm cài Windows hàng loạt qua mạng (PXE)** — chạy trên
Raspberry Pi hoặc trên laptop / máy bàn.

- **Console server:** cắm cáp console vào switch/router, điều khiển từ trình duyệt,
  không cần laptop, không cần PuTTY. Kèm bộ công cụ chẩn đoán mạng.
- **Deployment OS:** tạo kịch bản một lần, máy khách boot qua mạng (PXE) rồi tự chia ổ,
  cài Windows, phần mềm, font, và báo tiến trình + kết quả về web.

📖 **Tài liệu hướng dẫn đầy đủ (tiếng Việt):** https://console-docs.home-server.id.vn
· ⬇️ **Tải bản cài:** https://console-docs.home-server.id.vn/tai-ve

Lấy cảm hứng từ netool.io Pro2 ($299), làm lại bằng phần cứng sẵn có.

---

## Cài đặt

Có 3 cách, chọn theo thiết bị của bạn. File cài (ISO, ảnh thẻ nhớ) **không nằm trong
repo này** — tải ở trang [Tải về](https://console-docs.home-server.id.vn/tai-ve),
có SHA-256 để đối chiếu.

| Thiết bị | Cách cài | Hướng dẫn chi tiết |
|---|---|---|
| **Laptop / máy bàn** (Intel/AMD, 64-bit hoặc 32-bit) | Tải file `.iso`, ghi ra USB bằng Rufus (chế độ **DD Image**), boot từ USB, chạy thử hoặc cài lên ổ cứng bằng trình cài đồ hoạ | [Cài trên máy tính](https://console-docs.home-server.id.vn/cai-dat-may-tinh) |
| **Raspberry Pi 3 / 4 / 5** | Tải file `…-raspberrypi.img.xz`, ghi ra thẻ nhớ bằng Raspberry Pi Imager (**Use custom**), cắm vào Pi, cấp nguồn | [Cài trên Raspberry Pi](https://console-docs.home-server.id.vn/cai-dat-pi) |
| **Raspberry Pi OS / Debian có sẵn** | Cài từ mã nguồn bằng `install.sh` (bên dưới) | [Cài trên Raspberry Pi](https://console-docs.home-server.id.vn/cai-dat-pi) |

> File `.iso` chỉ dành cho chip Intel/AMD. Raspberry Pi dùng chip ARM nên cần file ảnh thẻ nhớ riêng.

### Cài từ mã nguồn (Raspberry Pi OS Lite 64-bit hoặc Debian 12/13)

```bash
git clone https://github.com/zTieuYeuz/server-consolepi.git consolepi-toolkit
sudo bash consolepi-toolkit/install.sh --local consolepi-toolkit
```

Thiết bị **không gắn màn hình** (bỏ giao diện kiosk, tiết kiệm ~500MB): thêm `--no-screen`.
Quá trình cài mất 5–15 phút tuỳ tốc độ mạng và thẻ nhớ; cài xong nên khởi động lại.

Sau khi cài, mở trình duyệt vào địa chỉ của máy (xem bảng *Kết nối* bên dưới) và
đăng nhập bằng tài khoản Linux của máy đó.

Dựng lại máy hỏng (kèm dữ liệu + bí mật từ bản sao lưu): xem `docs/KHOI-PHUC-TU-DAU.md`.
Tự dựng file ISO / ảnh Pi từ mã nguồn: xem `iso/README.md`.

> **Chạy lại được nhiều lần.** Cài đè bản mới không làm mất: WiFi đã lưu,
> thư viện lệnh, tên cổng console, rule IF/THEN, cấu hình AP, kịch bản cài Windows,
> hướng màn hình.

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

### Chẩn đoán mạng (14 công cụ)
ARP Scan · Ping/Traceroute · PCAP Capture · LLDP/CDP Discovery ·
**Kiểm tra toàn diện cổng mạng** (tốc độ/duplex, lỗi đường truyền, PoE, DHCP,
Internet, băng thông qua Cloudflare — một nút bấm) · STP/LACP/VLAN Detection ·
**MTU Discovery** (phát hiện PPPoE/VPN làm giảm MTU) ·
**Kiểm tra DNS** (đối chiếu nhiều DNS server, phát hiện hijack) ·
**Kiểm tra chứng chỉ TLS** (subject/issuer/hạn dùng, không bao giờ giả vờ tin cậy) ·
**Sơ đồ mạng 1 đoạn** (Pi → switch → host, ghép ARP + LLDP) ·
**Máy chủ TFTP** (sao lưu/nạp cấu hình, firmware switch) ·
Netmiko (SSH cấu hình switch) · 802.1X Testing · IF/THEN Automation

### Terminal & Tự động hoá
- **Terminal local** — dòng lệnh trên Pi, phiên tmux không mất khi đóng trình duyệt
- **SSH** — terminal tương tác (như PuTTY), điền sẵn được mật khẩu, kèm ô soạn
  tập lệnh ngay dưới khung terminal: chọn từ thư viện → sửa → Copy hoặc dán thẳng
  vào terminal
- **Thư viện lệnh** — lưu/sửa/xoá tập lệnh, sẵn 5 tập lệnh Cisco, có ô tìm kiếm
  và lọc theo thẻ. Dán được thẳng vào terminal (không tự chạy — bạn xem lại rồi
  mới bấm Enter)

### Sức khoẻ thiết bị & nguồn
Cảnh báo **sụt áp** (`vcgencmd get_throttled`) — nguyên nhân phổ biến nhất làm Pi
treo hoặc hỏng thẻ nhớ, và nó báo *trước* khi hỏng. Kèm nhiệt độ CPU, tải, RAM,
đĩa, thời gian chạy. Nút **Tắt máy / Khởi động lại** có hộp xác nhận.

### Deployment OS — cài Windows hàng loạt qua mạng (PXE)
Tạo **kịch bản cài máy** 6 bước (hệ điều hành, thông tin máy, chia ổ, phần mềm, tuỳ chọn
Windows, tổng kết). Máy khách boot qua mạng (iPXE + WinPE) — BIOS, UEFI và UEFI Secure
Boot — tự chia ổ, bung ảnh Windows, cài phần mềm, font, ứng dụng nhiều file (ví dụ Office),
gia nhập domain. Theo dõi tiến trình từng máy theo thời gian thực và nhận báo cáo tổng kết.
Có mục **dò ổ đĩa chỉ đọc** để chọn đúng ổ trước khi viết kịch bản, và chế độ boot WinPE
riêng (Hiren's, Strelec…). DHCP/TFTP/Samba **không tự chạy** — chỉ bật khi bạn bật PXE.
Xem [hướng dẫn](https://console-docs.home-server.id.vn/deployment-os).

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

### Tài liệu tra cứu ngay trên máy
Trang **Tài liệu** gom 20 mục (kiến trúc, vị trí file, lệnh bảo trì, sự cố đã gặp),
chia theo tab kèm ô tìm kiếm toàn văn — gõ từ khoá là hiện số kết quả trong từng mục.
Có nút *Xem tất cả* để dùng Ctrl+F hoặc in ra giấy. **Chạy hoàn toàn ngoại tuyến**,
tra được cả khi thiết bị không có internet.

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
                        deployos · pxe · tiendo · doodia · fontinfo · khotrungtam
src/nettools/           14 công cụ chẩn đoán mạng + static/
src/scripts/            wifi-fallback · ttyd-one · term-launch · kiosk-start
                        selftest · bt-auto-agent · bt-nap-daemon · bt-pan0-setup
                        console-bashrc · grc-cisco.conf
config/                 nginx · udev (serial, wifi, cảm ứng)
systemd/                19 unit
iso/                    Dựng ISO 64/32-bit và ảnh Raspberry Pi (xem iso/README.md)
docs/                   Quy tắc build + kiểm thử, khôi phục từ đầu
tools/                  Sao lưu, đồng bộ kho
```

## Yêu cầu

- Raspberry Pi 3 / 4 / 5 (đã kiểm chứng trên Pi 4), hoặc laptop/máy bàn Intel/AMD (ISO 64-bit; ISO 32-bit chạy được trên máy 1 GB RAM)
- Raspberry Pi OS Lite (Debian 12/13) 64-bit nếu cài từ mã nguồn
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

---

© 2026 zTieuYeuz. All rights reserved. Mã nguồn công khai để tham khảo; muốn dùng lại hoặc phân phối, vui lòng liên hệ tác giả.
