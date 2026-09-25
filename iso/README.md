# Console System OS — bản cài Linux (file ISO)

Thư mục này chứa **toàn bộ** cấu hình để dựng lại file `.iso` cài Console
System lên laptop/máy bàn. Không có gì giấu ở nơi khác.

## Dựng lại ISO

Cần một máy **x86_64** chạy Debian 13 (không dựng được trên Raspberry Pi vì
Pi là ARM). Máy build dùng thật: 8 nhân / 12 GB RAM / 49 GB trống, mỗi lần
build mất khoảng **15 phút**.

```bash
# may build Debian 13: xem goi can cai trong docs/QUY-TAC-BUILD-VA-KIEM-THU.md muc 4.1
rsync -a --delete --exclude=__pycache__ ~/consolepi-toolkit/ build-consolepi:/root/consolepi-toolkit/
bash /root/consolepi-toolkit/iso/dung-cay-build.sh      # dung ca 2 cay build tu repo
/build/console-system/dung-iso.sh                        # ISO 64-bit
/build/console-system-i386/dung-iso.sh                   # ISO 32-bit
```

`dung-cay-build.sh` chép **mọi thứ** từ repo vào đúng vị trí của live-build
(bảng bên dưới) — cây build không còn được sửa tay (bài học mất máy build cũ
25/09/2026). Quy tắc build và kiểm thử đầy đủ: `docs/QUY-TAC-BUILD-VA-KIEM-THU.md`.
Script test (chỉ dùng cho máy ảo): `iso/test/`.

`dung-iso.sh` làm đúng thứ tự **clean → config → build**, và chỉ báo thành
công khi **có file ISO thật** — không tin mã thoát của `lb build` (nó nuốt
lỗi ở bước dọn dẹp cuối và vẫn trả về 0; đã mất công hai lần vì chuyện này).

## Kiểm thử tự động

```bash
./test-iso.sh /build/console-system/live-image-amd64.hybrid.iso
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
| `includes-installer/console-system-nguon-apt.sh` | goc initrd cua trinh cai chu (`config/includes.installer/`), goi tu `preseed/late_command` |
| `includes/console-system-kiosk-ve` | `/usr/local/sbin/` (chon ve kiosk bang GPU hay CPU theo driver card do hoa + canh gac 90s tu doi sang CPU) |
| `includes/chromium-policies/console-system.json` | `/etc/chromium/policies/managed/` (tat hop thoai "Dich trang" cua Chromium tren kiosk - co `--disable-features=Translate` khong con tac dung o Chromium 153) |
| `includes/apt.conf.d/00-toc-do-build` | `/etc/apt/apt.conf.d/` (bi hook xoa khoi may da cai) |
| `calamares/settings.conf`, `calamares/modules/`, `calamares/branding/` | `/etc/calamares/` |
| `calamares/lang/calamares_vi.qm` (sinh bang `calamares/lang/sua-ban-dich-vi.py`) | `/usr/share/calamares/lang/` |
| `calamares/he-thong/console-system-grub-install` | `/usr/local/sbin/` |
| `calamares/he-thong/console-system-cai.service` | `/etc/systemd/system/` |
| `calamares/he-thong/05-khi-cai-dat.conf` | `/etc/systemd/system/console-pi-kiosk.service.d/` va `console-pi-kiosk-helper.service.d/` |

## Trình cài đồ hoạ (Calamares)

Mục boot *"CAI Console System - giao dien do hoa"* khởi động hệ thống chạy thử
với tham số `console-system.cai=giaodien`; dịch vụ `console-system-cai.service`
thấy tham số đó thì mở Calamares toàn màn hình trong `cage`, vẽ bằng CPU
(`WLR_RENDERER=pixman`) nên chạy được cả trên máy ảo không có 3D. Trình cài chữ
(d-i) vẫn giữ làm mục dự phòng.

Những chỗ đã phải xử lý riêng (đều kiểm chứng bằng cài thật trong QEMU):
- **GRUB có ký cho Secure Boot**: tự cài `grub-efi-amd64-signed` + `shim-signed`
  từ kho gói trên chính USB (`shellprocess@caigrub`), không cần Internet.
- **Đường dự phòng `/EFI/BOOT/BOOTX64.EFI`**: tắt bước dự phòng của Calamares
  (nó chép grub không có shim, máy bật Secure Boot sẽ từ chối) và để
  `grub-install --force-extra-removable` của Debian lo.
- **Khoá SSH riêng cho từng máy**: live-build xoá khoá khỏi ISO, Calamares
  không tạo lại nên `ssh.service` chết. `ssh-keygen -A` ở bước dọn dẹp.
- **Tiếng Việt mặc định**: đặt `LANG` qua `env` ngay trong `ExecStart`, vì
  `Environment=` bị PAM ghi đè.

## Những quyết định quan trọng (và lý do thật)

- **Không có desktop, chỉ có kiosk.** Cài xong tự hiện dashboard toàn màn
  hình (cage + Chromium, như RasPad) trên mọi loại máy, kể cả máy ảo. Card
  Intel/AMD (cả iGPU trong CPU) vẽ bằng GPU; còn lại (máy ảo, card máy chủ,
  nouveau, simpledrm) vẽ bằng CPU — vì cage 0.2.0 gặp card không 3D thì
  **treo luôn** chứ không thoát (đã thấy thật trên VMware), màn hình đen
  vĩnh viễn. Có canh gác: GPU mà 90 giây chưa có trình duyệt thì tự đổi CPU.
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

## Hai bản — 64-bit và 32-bit

| | 64-bit (amd64) | 32-bit (i386) |
|---|---|---|
| File (trên máy build) | `/build/console-system/live-image-amd64.hybrid.iso` | `/build/console-system-i386/live-image-i386.hybrid.iso` |
| Kích thước | ~1440 MB | ~1040 MB |
| Nền | Debian 13 (trixie) | Debian 12 (bookworm) |
| Python | 3.13 | 3.11 |
| Secure Boot | Có (`shim-signed`) | Không (máy đời đó không có UEFI) |
| Thư mục build | `iso/` | `iso/i386/` |

**Vì sao bản 32-bit phải dùng Debian 12:** Debian **đã bỏ hẳn** kernel và
trình cài đặt 32-bit từ bản 13. Đã tra kho để chắc chắn, không đoán:

```
Debian 13 (trixie)   -> 0 gói linux-image-686
Debian 12 (bookworm) -> 4 gói linux-image-686
```

**Lưu ý về tuổi thọ:** Debian 12 sắp hết hạn hỗ trợ, nghĩa là bản 32-bit sẽ
không còn nhận cập nhật bảo mật trong khi bản 64-bit còn dài. Máy **chỉ**
chạy được 32-bit là loại trước ~2006 — máy từ 2007 trở đi đều có CPU 64-bit
kể cả khi đang chạy Windows 32-bit, nên dùng bản 64-bit được.

## Đặt thương hiệu — phải viết trong hook, không đặt file

Phần đổi tên hệ thống (`/etc/os-release`) đã qua **bốn lần thử** mới đúng:

1. Đặt file trong `config/includes.chroot/etc/os-release` → bị gói
   `base-files` **ghi đè âm thầm**, ISO vẫn tự khai là Debian
2. Chuyển sang `config/includes.chroot_after_packages/` → live-build **từ
   chối build**: *"You have files in includes.chroot and
   includes.chroot_after_packages. Only one directory is allowed."*
3. **Viết trong hook** (`hooks/0100-console-system.hook.chroot`) → đúng chỗ,
   vì hook chạy sau khi cài gói xong và không xung đột thư mục
4. Nhưng lần 3 **viết lại cả file bằng tay** nên mất dòng `VERSION_CODENAME`
   → script cài Tailscale (và Docker, Grafana...) báo *"VERSION_CODENAME:
   parameter not set"*. Nay hook **lấy nguyên file gốc** `/usr/lib/os-release`
   của Debian và chỉ đổi `NAME`/`PRETTY_NAME`/`VERSION`/`HOME_URL`; thiếu
   `VERSION_CODENAME` thì bản build tự dừng.

Giữ nguyên `ID=debian` trong `os-release`: rất nhiều công cụ đọc trường này
để biết đang chạy trên họ Debian nào. Chỉ đổi `NAME`/`PRETTY_NAME` là thứ
người dùng nhìn thấy.
