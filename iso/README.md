# Console System OS — bản cài Linux (file ISO)

Thư mục này chứa **toàn bộ** cấu hình để dựng lại file `.iso` cài Console
System lên laptop/máy bàn. Không có gì giấu ở nơi khác.

## Dựng lại ISO

Cần một máy **x86_64** chạy Debian 13 (không dựng được trên Raspberry Pi vì
Pi là ARM). Máy build dùng thật: 8 nhân / 12 GB RAM / 49 GB trống, mỗi lần
build mất khoảng **15 phút**.

```bash
sudo apt install live-build xorriso squashfs-tools debootstrap
mkdir -p /build/console-system && cd /build/console-system
# chép các file trong thư mục này vào đúng vị trí của live-build:
#   hooks/*                    -> config/hooks/live/
#   danh-sach-goi.txt          -> config/package-lists/console-pi.list.chroot
#   bootloader/isolinux.cfg    -> config/bootloaders/isolinux/
#   bootloader/menu.cfg        -> config/bootloaders/syslinux_common/
#   bootloader/live.cfg.in     -> config/bootloaders/syslinux_common/
#   includes/*                 -> config/includes.chroot/... (xem dưới)
#   mã nguồn src/              -> config/includes.chroot/opt/console-pi/
./dung-iso.sh
```

`dung-iso.sh` làm đúng thứ tự **clean → config → build**, và chỉ báo thành
công khi **có file ISO thật** — không tin mã thoát của `lb build` (nó nuốt
lỗi ở bước dọn dẹp cuối và vẫn trả về 0; đã mất công hai lần vì chuyện này).

## Kiểm thử tự động

```bash
./test-iso.sh /build/console-system-1.0.0-amd64.iso
```

Boot ISO trong QEMU có **chuyển tiếp cổng** (`18080→80`, `18022→22`) rồi gọi
thẳng vào dashboard đang chạy bên trong. Đây mới là bằng chứng thật: không
phải "có file ISO" hay "boot lên màn hình", mà là **dịch vụ bên trong thực
sự phục vụ được**.

## Vị trí các file includes

| File trong repo | Vị trí trong ISO |
|---|---|
| `includes/update-motd.d/10-console-system` | `/etc/update-motd.d/` |
| `includes/console-system-lan-dau` | `/usr/local/sbin/` |
| `includes/console-system-lan-dau.service` | `/etc/systemd/system/` |
| `includes/10-console-system.conf` | `/etc/ssh/sshd_config.d/` |

## Những quyết định quan trọng (và lý do thật)

- **Không có desktop.** Máy này là thiết bị mạng, mọi thao tác qua trình
  duyệt từ máy khác. Bỏ desktop giúp ISO còn ~1.1 GB và chạy được trên máy
  RAM thấp.
- **Bỏ firmware đồ hoạ (~224 MB)** — nvidia/amdgpu/i915 — vì không có
  desktop thì không dùng tới. **Giữ nguyên toàn bộ firmware mạng** (94 thư
  mục: Intel, Realtek, Atheros, Broadcom, MediaTek, card mạng máy chủ...) vì
  đó chính là thứ giúp chạy được trên mọi laptop.
- **Secure Boot bật** (`shim-signed` + `grub-efi-amd64-signed`): laptop hãng
  thường bật sẵn Secure Boot, thiếu thì máy từ chối boot USB mà nhiều máy
  doanh nghiệp lại khoá BIOS nên không tắt được.
- **Dịch vụ mạng nguy hiểm bị TẮT tường minh.** Debian tự bật dịch vụ khi
  cài gói — bản dựng đầu tiên boot lên là chạy luôn DHCP server, phát WiFi,
  TFTP và Samba. Cắm vào mạng công ty là thành DHCP lậu, sập mạng khách.
- **Bí mật sinh ở lần khởi động đầu của từng máy**, không nhúng trong ISO —
  vì ISO là file công khai ai cũng tải được.
- **Menu boot tự chạy sau 5 giây.** Mặc định của live-build là chờ bấm phím
  mãi mãi; máy không cắm màn hình sẽ đứng im vĩnh viễn.
