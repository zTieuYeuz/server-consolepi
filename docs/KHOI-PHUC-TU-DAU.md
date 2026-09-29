# Khôi phục Console Pi (và kho) từ đầu

> Tài liệu nội bộ, không đưa lên trang docs công khai.
> Console System - (c) 2026 zTieuYeuz.

Dùng khi thẻ nhớ/ổ cứng Console Pi hỏng, hoặc máy kho hỏng. Mọi thứ cần để dựng
lại nằm ở **3 nơi**:

| Thứ gì | Nằm ở đâu |
|---|---|
| Mã nguồn Console System (Pi + ISO) | GitHub `zTieuYeuz/server-consolepi` (private) |
| Mã nguồn trang docs | GitHub `zTieuYeuz/consolepi-docs` (private) |
| Mã nguồn kho | GitHub `zTieuYeuz/kho-console-pi` (private) |
| Dữ liệu + bí mật của Pi (mật khẩu, token tunnel, WiFi, kịch bản, tham số, thư viện lệnh, khoá ký ISO, SSH key) | Máy build: `/root/sao-luu/pi-*.tar.gz` |
| Dữ liệu kho (CSDL, file đã tải lên, tài khoản admin, khoá góp ý) | Máy build: `/root/sao-luu/kho-*.tar.gz` |

Bản sao lưu tạo bằng `tools/sao-luu-sang-may-build.sh` (chạy trên Pi), giữ 10
bản mới nhất. **Nên chép thêm bản mới nhất ra Google Drive/USB** — máy build
cũng có thể hỏng.

**Không có trong sao lưu (dữ liệu nặng, ~15 GB):** ảnh Windows trong
`deploy/os`, `deploy/ungdung`, file `.exe/.msi` trong `deploy/apps`. Đây là
file tải lại được (ISO Windows từ Microsoft, phần mềm từ kho hoặc trang hãng);
bảng tham số cài im lặng và kịch bản thì CÓ trong sao lưu.

---

## A. Dựng lại Console Pi

1. Ghi **Raspberry Pi OS (64-bit, Bookworm trở lên)** vào thẻ nhớ mới bằng
   Raspberry Pi Imager. Đặt user `administrator`, bật SSH, hostname
   `Server-console`.
2. Cắm mạng, SSH vào Pi.
3. Lấy lại SSH key từ bản sao lưu (để kéo được repo private). Từ một máy có
   quyền vào máy build:
   ```bash
   scp root@<ip-may-build>:/root/sao-luu/pi-<ngay>.tar.gz administrator@<ip-pi>:~
   ```
   Trên Pi:
   ```bash
   mkdir -p ~/khoi-phuc && tar -xzf ~/pi-*.tar.gz -C ~/khoi-phuc
   cp -a ~/khoi-phuc/home/administrator/.ssh ~/ && chmod 700 ~/.ssh && chmod 600 ~/.ssh/id_*
   ```
4. Kéo mã nguồn và cài:
   ```bash
   git clone git@github.com:zTieuYeuz/server-consolepi.git ~/consolepi-toolkit
   sudo bash ~/consolepi-toolkit/install.sh --local ~/consolepi-toolkit
   ```
   (Thêm `--no-screen` nếu không gắn màn hình cảm ứng.)
5. Trả dữ liệu + bí mật về chỗ cũ:
   ```bash
   sudo systemctl stop console-pi-dashboard console-pi-tunnel
   sudo tar -xzf ~/pi-*.tar.gz -C / --exclude='home/*'
   cp -a ~/khoi-phuc/home/administrator/.config ~/
   sudo systemctl daemon-reload
   sudo systemctl restart NetworkManager console-pi-dashboard console-pi-tunnel
   ```
6. Chép lại dữ liệu nặng (ảnh Windows, phần mềm) vào Deployment OS qua giao
   diện, hoặc bấm **Cập nhật từ kho** / tải từ kho.
7. Kiểm tra:
   ```bash
   sudo /opt/console-pi/scripts/selftest.sh
   ```
   Truy cập từ xa qua tunnel, đăng nhập bằng mật khẩu cũ, Kho trung tâm hiện
   danh sách, Tham số cài đặt còn đủ dòng.
8. Xoá file tạm: `rm -rf ~/khoi-phuc ~/pi-*.tar.gz`.

## B. Dựng lại máy kho

1. Cài Debian/Ubuntu mới, cài `python3-venv caddy`.
2. Kéo mã: `git clone git@github.com:zTieuYeuz/kho-console-pi.git /root/kho-console-pi`
3. Cài:
   ```bash
   mkdir -p /opt/kho-console-pi && cp -a /root/kho-console-pi/src /opt/kho-console-pi/
   python3 -m venv /opt/kho-console-pi/venv
   /opt/kho-console-pi/venv/bin/pip install -r /root/kho-console-pi/requirements.txt
   cp /root/kho-console-pi/systemd/kho-console-pi.service /etc/systemd/system/
   cp /root/kho-console-pi/config/Caddyfile /etc/caddy/Caddyfile
   ```
4. Trả dữ liệu: `tar -xzf kho-<ngay>.tar.gz -C /` (bung ra
   `/var/lib/kho-console-pi`), rồi `chown -R www-data:www-data /var/lib/kho-console-pi`.
5. `systemctl daemon-reload && systemctl enable --now kho-console-pi && systemctl reload caddy`
6. Tunnel Cloudflare của kho: trỏ lại hostname `kho-console` về máy mới trong
   Cloudflare Zero Trust → Networks → Tunnels. Cloudflare Access (khoá trang)
   nằm trên Cloudflare, không mất.
7. Kiểm tra: trên Console Pi bấm **Cập nhật từ kho** phải chạy.

## C. Máy build hỏng

Máy build dựng lại được hoàn toàn từ repo (`iso/dung-cay-build.sh`). Có 2 thứ
riêng cần giữ ở `/root/.config/zt/` trên máy build:

| File | Dùng để làm gì | Có bản dự phòng ở đâu |
|---|---|---|
| `dau-an.key` | Ký ISO (chứng minh bản build của mình) | Pi: `~/.config/zt/`, nằm trong sao lưu Pi |
| `cf-access.json` | Service Token Cloudflare (nếu dùng Cách B) | Không bắt buộc, anh tự đặt |

Và thư mục `/root/sao-luu` (nên có bản trên Drive).

## D. Khoá mã hoá của kho (tự đăng ký máy)

Từ 29/09/2026 mỗi Console System tự gửi thông tin máy lên kho, mã hoá đầu-cuối
bằng khoá công khai của kho **ghim cứng trong mã nguồn**
(`KHOA_CONG_KHAI_KHO` trong `src/ui/khotrungtam.py`). Khoá riêng tương ứng nằm
ở máy kho: `/var/lib/kho-console-pi/dang-ky-x25519.key` — có trong bản sao lưu
`kho-*.tar.gz`.

- Dựng lại kho **phải trả lại đúng file này** (bước B.4 đã bung nó ra). Nếu mất
  file: kho tự sinh khoá mới, khi đó mọi máy đã bán sẽ **không gửi được thông
  tin** (vẫn tải phần mềm bình thường bằng token cũ) cho tới khi cập nhật
  `KHOA_CONG_KHAI_KHO` trong mã nguồn và phát hành bản mới.
- Tuyệt đối không đưa file khoá riêng lên GitHub.

