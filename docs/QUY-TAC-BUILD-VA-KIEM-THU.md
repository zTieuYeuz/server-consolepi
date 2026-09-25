# Quy tắc build và kiểm thử — Console Pi / Console System

> **Bắt buộc áp dụng cho MỌI thay đổi**, từ nay cho đến khi anh Thoại yêu cầu
> cập nhật. Tổng hợp từ các yêu cầu của anh Thoại và từ **lỗi thật đã gặp**
> (ghi rõ ở từng mục). Chỉ sửa file này khi anh Thoại bảo.
>
> Phiên bản quy tắc: **2** — 25/09/2026 (thêm quy tắc 16: làm trên Console Pi trước).

---

## 1. Tư duy gốc: đây là sản phẩm đem bán

Mọi quyết định đều trả lời câu hỏi: *"Người mua trả tiền cho cái này có hài
lòng không?"*. Sản phẩm phải:

- **Ổn định**: không lỗi, không treo, không màn hình đen, không dịch vụ chết.
- **Tiện lợi**: cài xong là dùng được ngay (kiosk tự hiện, dashboard tự chạy),
  ít bước bấm nhất có thể (vd. bỏ nút thừa như "Dùng" khi menu PXE đã đủ).
- **Dễ dùng**: chữ tiếng Việt rõ ràng, thông báo nói **nguyên nhân + cách
  sửa**, không bao giờ im lặng khi thất bại.
- **An toàn**: cắm vào mạng khách không bao giờ làm sập mạng khách.
- **Chạy trên nhiều loại máy của nhiều hãng**: PC, laptop, mini PC, máy cũ,
  máy chỉ có card đồ hoạ tích hợp (iGPU), máy ảo (VMware, VirtualBox,
  Hyper-V, Proxmox), máy BIOS lẫn UEFI, có/không Secure Boot.

Kiểm thử **kỹ từng chút một**, như chính mình là người mua khó tính nhất.

---

## 2. Quy tắc bất biến (không bao giờ vi phạm)

| # | Quy tắc | Lý do |
|---|---|---|
| 1 | **Không phá logic.** Sửa giao diện thì phải kiểm lại hành vi phía sau, không chỉ nhìn cho đẹp. | Yêu cầu của anh Thoại. |
| 2 | **Test xong từng phần mới sang phần tiếp theo.** Không gộp nhiều thay đổi chưa kiểm rồi mới test một lần. | Để biết chính xác cái gì làm hỏng cái gì. |
| 3 | **Sửa chỗ này không được làm hỏng chỗ kia.** Có nhiều chế độ/biến thể thì test **tất cả** (vd. PXE: cả 3 chế độ mạng × BIOS/UEFI). | Anh Thoại: "test cả 3 kiểu, đừng sửa cái này thì cái kia lại lỗi". |
| 4 | **Trang nào cũng có nút Home**, kể cả trang mở từ trang khác. | Yêu cầu của anh Thoại. |
| 5 | **Bộ cài phát hành KHÔNG BAO GIỜ điền sẵn ổ đĩa / chia ổ** (preseed hay Calamares). Chỉ máy ảo test mới được tự động chia ổ, và tham số đó nằm ở dòng lệnh máy ảo, không nằm trong ISO. | Chọn nhầm ổ = mất dữ liệu khách. |
| 6 | **ISO chỉ nằm trên máy build**, không đẩy lên GitHub. GitHub chỉ chứa mã nguồn. | Yêu cầu của anh Thoại. |
| 7 | **Dịch vụ mạng không xác thực (DHCP, TFTP, Samba, phát WiFi, PXE) không bao giờ tự bật khi khởi động.** Chỉ bật khi người dùng bấm, có cảnh báo rõ. | ISO bản đầu boot lên là phát DHCP → sập mạng khách. |
| 8 | **Bí mật sinh ở lần khởi động đầu của từng máy**, không nhúng trong ISO. | ISO là file công khai. |
| 9 | **Không bịa dữ liệu** khi phần cứng không hỗ trợ — ghi rõ "không hỗ trợ / không phát hiện". | Nguyên tắc xuyên suốt dự án. |
| 10 | **Trạng thái mạng tạm thời luôn được dọn** (khối `finally`, trả eth0 về NetworkManager khi lỗi). | Tránh Pi mất mạng sau một lần thử hỏng. |
| 11 | **Ưu tiên không thêm gói hệ thống mới** nếu khả năng đã có sẵn. Thêm gói thì thêm vào **cả** `iso/danh-sach-goi.txt`, `iso/i386/danh-sach-goi.txt` và `install.sh` của Pi. | ISO từng thiếu `parted` → Deployment OS trên x86 chưa bao giờ dựng được ảnh. |
| 12 | **Không đụng tới Pi đang chạy thật (192.168.110.14) khi test.** Test bằng dữ liệu tạm (`CONSOLE_PI_DATA=$(mktemp -d)`) và **lệnh hệ thống giả** (thay `_sh`), không bật PXE/DHCP ra mạng công ty. | Pi là máy production của anh Thoại. |
| 13 | **Đăng nhập máy khác chỉ bằng khoá SSH**, không dùng mật khẩu anh gửi trong chat; nhắc anh đổi mật khẩu đã lộ. | An toàn. |
| 14 | **Luôn trả lời anh Thoại bằng tiếng Việt.** | Yêu cầu của anh Thoại. |
| 15 | **Không nói "xong" khi chưa kiểm chứng.** Cái gì chưa test được thì nói rõ là chưa test và vì sao. | Báo cáo trung thực. |
| 16 | **Mọi chức năng MỚI phải làm trên Console Pi TRƯỚC**: code trong repo → cập nhật lên Pi (`cap-nhat-pi.sh`) → anh Thoại dùng thử trên Pi đạt → **sau đó** mới đưa vào ISO (x86) và build. Không phát triển tính năng mới thẳng trên ISO/máy ảo. | Yêu cầu của anh Thoại (25/09/2026). Pi là sản phẩm gốc; ISO là bản chuyển sang x86 của chính code đó. |

---

## 3. Hạ tầng

| Thành phần | Địa chỉ | Ghi chú |
|---|---|---|
| Console Pi thật (production) | 192.168.110.14 (`Server-console`) | Code chạy ở `/opt/console-pi`, dữ liệu `/var/lib/console-pi`. Không phá. |
| Máy build | 192.168.110.37 (`build-os`, Debian 13, SSH alias `build-consolepi`) | Dựng lại 25/09/2026 sau khi máy cũ .19 bị xoá. |
| Mã nguồn | `/home/administrator/consolepi-toolkit` trên Pi → GitHub `zTieuYeuz/server-consolepi` (nhánh `main`) | **Nguồn duy nhất.** Mọi thứ trên máy build sinh ra từ đây. |
| Cây build 64-bit | `/build/console-system` | Debian 13 trixie, Secure Boot, Calamares |
| Cây build 32-bit | `/build/console-system-i386` | Debian 12 bookworm (Debian 13 đã bỏ 32-bit) |

**Bài học mất máy build (25/09/2026):** cây build cũ được dựng tay qua hàng
trăm lệnh `scp`, mất máy là mất hết. Từ nay:

- **Không bao giờ sửa tay trong `/build/...` mà không sửa trong repo.**
- Cây build luôn dựng lại được bằng `iso/dung-cay-build.sh`.
- Script test nằm trong `iso/test/`, không nằm rải rác trên máy build.

---

## 4. Cách build

### 4.1. Chuẩn bị máy build mới (chỉ làm 1 lần)
```bash
# Debian 13 x86_64, ≥ 6 nhân, ≥ 8 GB RAM, ≥ 50 GB trống
apt-get install -y live-build xorriso squashfs-tools debootstrap curl ca-certificates \
  rsync git sudo qemu-system-x86 qemu-utils ovmf socat sshpass dnsmasq wimtools 7zip \
  genisoimage parted dosfstools mtools python3-pil python3-flask ipxe-qemu tcpdump
systemctl disable --now dnsmasq     # BAT BUOC: khong de may build phat DHCP ra mang cong ty
```

### 4.2. Đưa mã nguồn lên và dựng cây build
```bash
# tren Pi
rsync -a --delete --exclude=__pycache__ ~/consolepi-toolkit/ build-consolepi:/root/consolepi-toolkit/
# tren may build
bash /root/consolepi-toolkit/iso/dung-cay-build.sh          # ca 2 cay (hoac: amd64 | i386)
```

### 4.3. Build ISO
```bash
systemd-run --unit=b-all --collect -p RuntimeMaxSec=7200 \
  sh -c "/build/console-system/dung-iso.sh; /build/console-system-i386/dung-iso.sh"
journalctl -u b-all | grep -E "XONG|THAT BAI|E:"
```
- 64-bit ≈ 15 phút, ~1440 MB. 32-bit ≈ 15 phút, ~1040 MB. Kích thước lệch
  nhiều so với con số này = có gì đó sai (thiếu gói / thừa gói).
- **Luôn chạy bằng `systemd-run` + `RuntimeMaxSec`**, không chạy trần qua SSH.
  *Lỗi thật:* một lần build 32-bit treo 3 tiếng ở `apt-get update` vì mạng.

### 4.4. Những cái bẫy đã gặp (đọc trước khi sửa build)

| Bẫy | Cách tránh |
|---|---|
| `lb clean` xoá dấu mốc → `lb build` báo "success" nhưng **không có ISO** | Luôn chạy `dung-iso.sh` (clean → config → build) và **chỉ tin file ISO thật**, không tin mã thoát. |
| Dấu `%` trong danh sách gói → printf nuốt **mọi dòng sau** → ISO thiếu gói mà vẫn "thành công" | `dung-iso.sh` và `dung-cay-build.sh` chặn sớm. Không viết `%`, viết chữ "phần trăm". |
| Đặt `/etc/os-release` trong includes.chroot → bị `base-files` ghi đè | Đổi thương hiệu **trong hook**, lấy từ `/usr/lib/os-release`, giữ `VERSION_CODENAME` và `ID=debian`. |
| Dùng cả `includes.chroot` và `includes.chroot_after_packages` | live-build từ chối. Chỉ dùng `includes.chroot` + hook. |
| Bộ cài hỏi firmware Realtek trên mini PC thật | `dung-iso.sh` nhúng `rtl_nic` vào initrd bộ cài (64-bit: `usr/lib/firmware`, 32-bit: `lib/firmware`). |
| GRUB chưa ký → máy bật Secure Boot không boot | Hook xoá `00recommends` để bộ cài kéo `grub-efi-amd64-signed`; Calamares tự cài `shim-signed`. |
| Theme đồ hoạ GRUB che kín menu | **Không** chép `splash.svg` vào `grub-pc/`. |
| Tải gói lỗi giữa chừng ("Couldn't download packages") | Kiểm tra gói có trên mirror không; có thì chỉ là mạng chập chờn → build lại. |
| `pkill -f <mẫu>` giết luôn phiên SSH đang chạy lệnh | Dùng file PID hoặc `ps -eo pid,comm`, không `pkill -f`. |
| Vòng chờ `pgrep -f` tự khớp chính nó → chờ mãi | Dùng `systemctl is-active <unit>` hoặc `grep "[x]yz"`. |
| `systemd-run` báo "Running as unit" nhưng tiến trình chết ngay | Luôn kiểm `systemctl is-active` + journal sau vài giây. |

---

## 5. Quy trình 7 bước (bắt buộc cho mọi thay đổi ảnh hưởng ISO)

0. **Chức năng mới: làm trên Console Pi trước** (quy tắc 16) — test tầng 1–2,
   cập nhật lên Pi, anh Thoại dùng thử đạt trên Pi rồi mới vào bước 1.
   (Riêng lỗi chỉ có ở bản x86 — kiosk trên PC, bộ cài, Secure Boot... — thì
   sửa và test thẳng trên ISO, nhưng code dùng chung vẫn phải chạy đúng trên Pi.)
1. **Build** ISO gọn, nhẹ, tối ưu — chạy mượt trên máy nhỏ, cũ, laptop.
2. **Cài thử thật** rồi **đánh giá như hàng sắp bán**: đủ chuẩn để bán chưa?
3. Chưa đạt → quay lại bước 1, sửa, lặp bước 2 đến khi đạt.
4. Đạt rồi → **dùng thử MỌI chức năng**, đặt tiêu chuẩn phát hành khắt khe
   nhất, cái gì chưa đạt thì sửa.
5. Có lỗi → **sửa trong mã nguồn (repo)**, quay lại bước 1.
6. Đạt → đẩy **mã nguồn** lên GitHub (ISO ở lại máy build), gửi anh Thoại
   **đường dẫn ISO + SHA256** để anh test lần cuối.
7. Cập nhật tài liệu: `src/ui/docs.py`, `iso/README.md`, `CHANGELOG.md`, `VERSION`.

Thay đổi chỉ ảnh hưởng Pi (không đụng ISO) vẫn làm bước 4–7, cộng thêm mục 7
(cập nhật Pi) bên dưới.

---

## 6. Các tầng kiểm thử (làm theo thứ tự, tầng dưới đạt mới lên tầng trên)

### Tầng 1 — Tĩnh (mỗi lần sửa)
- `bash -n` / `sh -n` cho script, `python3 -c "import ast; ast.parse(...)"` cho Python.
- Script systemd: kiểm lỗi escape (`$$`, `\.`).

### Tầng 2 — Logic trên Pi, **không đụng hệ thống thật**
- Chạy Flask test client với `CONSOLE_PI_DATA=$(mktemp -d)`; thay hàm chạy
  lệnh hệ thống (`_sh`) bằng hàm giả **ghi lại lệnh** để kiểm lệnh nào sẽ chạy.
- Đăng nhập bằng header `X-ConsolePi-Local: 1` (giống kiosk cổng 8880).
- Kiểm **cả đường thành công lẫn đường lỗi** (thiếu dữ liệu, bấm 2 lần, hết chỗ đĩa...).
- Khi sửa route/trang: dò **mọi link** trên trang (≥ 47 trang hiện có) phải 200/302.

### Tầng 3 — Ruột ISO (sau mỗi lần build)
- `unsquashfs -l` kiểm các file quan trọng có mặt (code mới, ttyd, parted,
  wimlib, 7z, cage, chromium, calamares, policy Chromium...).
- Kiểm file **không được có** (`00-toc-do-build`, `00recommends`).
- Kho gói trên USB có `shim-signed`, `grub-efi-amd64-signed`, `firmware-realtek`.
- initrd bộ cài có `preseed.cfg`, `console-system-nguon-apt.sh`, `rtl_nic/`.

### Tầng 4 — Cài thật trên máy ảo
- `iso/test/cai-uefi.sh` (UEFI, ISO cắm như USB) → phải thấy
  "Finishing the installation".
- `iso/test/boot-uefi.sh` → SSH qua cổng 18022 → chạy
  `iso/test/kiem-tra-may-da-cai.sh` → **0 LỖI**. Bộ này kiểm: tên hệ thống,
  không dịch vụ lỗi, bí mật riêng từng máy, nguồn apt, dịch vụ chính chạy,
  **không tự phát DHCP/WiFi/TFTP/Samba**, kiosk hiện dashboard, đủ công cụ
  Deployment OS, mọi trang web mở được, có nút Home, không Traceback.
- Chụp màn hình qua QEMU monitor (`screendump`) và **nhìn tận mắt**.
- Bản 32-bit: tối thiểu kiểm ruột ISO + boot live.

### Tầng 5 — Chức năng chuyên sâu (khi thay đổi chạm tới)
- **Kiosk**: GPU (Intel/AMD, cả iGPU) và CPU (máy ảo, card máy chủ); tắt
  kiosk phải về dòng lệnh; xoay màn hình (restart) không mất kiosk.
- **PXE**: `iso/test/pxe-lab.sh` — phòng thí nghiệm tách biệt (network
  namespace) với cấu hình **do chính code sinh ra** (`sinh-cau-hinh.py`):
  **3 chế độ mạng × BIOS/UEFI**, mỗi lần phải: hiện menu → vào
  "Install Windows" → chọn kịch bản thứ 2 → tải đúng ảnh `_menu-B.img`.
  Chế độ "có DHCP" phải có router DHCP giả chạy song song (tái hiện mạng công ty).
- **Deployment OS**: dựng ảnh thật từ `boot.wim` Windows thật, mở ảnh ra kiểm
  đúng tên máy/tài khoản của kịch bản.

### Tầng 6 — Máy thật (anh Thoại)
- Anh test trên máy thật (mini PC Dell, VMware...). Em chuẩn bị đường dẫn
  ISO + SHA256 và **hướng dẫn từng bước**, nói rõ phần nào em chưa test được.

---

## 7. Cập nhật con Console Pi đang chạy

- Không có sudo không mật khẩu → em chuẩn bị, **anh chạy**:
  ```bash
  sudo bash ~/cap-nhat-pi.sh
  ```
  (bản trong repo: `tools/cap-nhat-pi.sh`). Script tự **sao lưu**, chép code,
  **kiểm cú pháp trước khi khởi động lại** (lỗi thì tự trả bản cũ), rồi in
  kết quả các trang.
- Sau khi anh chạy: em so từng file giữa repo và `/opt/console-pi`, kiểm
  dịch vụ, dò mọi link, xem journal không có Traceback.
- Luôn đưa lệnh quay lại bản cũ.

---

## 8. Phát hành và báo cáo

- **Phiên bản**: `VERSION` theo x.y.z — sửa lỗi tăng z, thêm tính năng tăng y.
- **CHANGELOG.md**: mỗi bản ghi *vì sao* (lỗi thật / yêu cầu của anh), *sửa
  gì*, và mục **"Kiểm chứng:"** liệt kê đúng những gì đã test (và chưa test).
- **Commit** rõ ràng, có dòng Co-Authored-By; push lên `main` khi đạt.
- Đồng bộ mã nguồn sang máy build (qua `rsync` + `dung-cay-build.sh`) để
  ISO lần sau có luôn.
- **Báo cáo anh Thoại**: tiếng Việt, ngắn, có bảng kết quả; nói rõ lỗi đã
  tìm ra, nguyên nhân thật, đã sửa gì, test gì, **chưa test gì**, anh cần làm gì.
- Chờ lâu (build, cài thử): báo tiến độ, không im lặng.

---

## 9. Cập nhật bộ quy tắc

Lịch sử:
- v1 (25/09/2026): bản đầu.
- v2 (25/09/2026): quy tắc 16 + bước 0 — chức năng mới làm trên Console Pi trước.


Chỉ cập nhật khi anh Thoại yêu cầu. Khi cập nhật: tăng số phiên bản quy tắc
ở đầu file, ghi ngày và thay đổi.
