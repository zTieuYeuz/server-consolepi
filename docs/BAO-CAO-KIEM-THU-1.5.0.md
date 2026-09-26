# Báo cáo kiểm thử — Console System 1.5.0

Kiểm thử ngày 25–26/09/2026. Người thực hiện: Claude, theo `docs/QUY-TAC-BUILD-VA-KIEM-THU.md`.

Mục tiêu của bản này: **cài Windows qua mạng (PXE) chạy được trên mọi kiểu máy** — BIOS/Legacy, UEFI, UEFI bật Secure Boot — mà không phải vào BIOS chỉnh gì. Kèm theo đó là một loạt lỗi thật đã phát hiện và sửa trong lúc test.

## 1. Môi trường test

| Hạng mục | Chi tiết |
|---|---|
| Console Pi thật | 192.168.110.14, chế độ "Mạng có sẵn DHCP" trên mạng công ty |
| Máy chủ cài từ ISO | Máy ảo cài ISO 1.5.0 amd64 tự động, 2 card mạng, mạng lab riêng `brlab` (không đụng LAN thật) |
| Máy khách | QEMU/KVM trên máy build: BIOS (SeaBIOS), UEFI (OVMF), UEFI + Secure Boot (OVMF nạp khoá Microsoft; WinPE đọc được `UEFISecureBootEnabled=1`) |
| Hệ điều hành | Windows 10 Pro 22H2 (build 19045), Windows 11 Pro 24H2 (build 26100) — boot.wim/install.wim thật của anh Thoại |
| Kịch bản | Tạo **qua chính trình tạo trên web** (`iso/test/tao-kich-ban.py`). T1 Cơ bản. T2 Đầy đủ: 6 phân vùng, Administrator, tự đăng nhập, tiếng Việt, 2 phần mềm (cho máy / cho người dùng), ứng dụng thư mục, script .ps1 + .cmd, lệnh thêm, 7 tuỳ chọn, gỡ 2 app. T3 Win11: tuỳ chọn Win11, WinRAR, script, lệnh thêm |
| Kiểm kết quả | Tắt máy đúng cách → mở ổ Windows → đọc `C:\ConsolePi\BAO-CAO-TONG-KET.txt`, `bao-cao-day-du.json` (cả mục chưa đạt), `tien-trinh.log` và các file dấu vết do script tạo |

## 2. Ma trận kết quả (cài trọn vẹn tới desktop + báo cáo)

| # | Máy chủ | Kiểu máy | Chế độ mạng | Kịch bản | Kết quả |
|---|---|---|---|---|---|
| 1 | Pi thật | BIOS | Mạng có sẵn DHCP | Install windows 10 - DHCP | ✅ Vào desktop, cài phần mềm |
| 2 | Pi thật | UEFI | Mạng có sẵn DHCP | Install windows 10 - DHCP | ✅ **20/20 việc**, gồm Office |
| 3 | Pi thật | UEFI + Secure Boot | Mạng có sẵn DHCP | — | ❌ → tìm ra lỗi A (đã sửa, xác nhận lại ở #8, #9) |
| 4 | ISO | BIOS | Boot trực tiếp | T2 | ❌ → lỗi B (Samba). Sau khi sửa: MBR 6 phân vùng + phần mềm OK, lộ lỗi C (.ps1) |
| 5 | ISO | UEFI | Mạng không DHCP | T2 | ✅ 16 việc (bản trước khi sửa báo cáo) |
| 6 | ISO | UEFI + SB | Mạng có sẵn DHCP | T3 Win11 | ✅ Win11 vào desktop khi SB đang bật; lộ lỗi D, E |
| 7 | ISO | BIOS | Mạng có sẵn DHCP | T2 | ✅ 21 việc; `bao-cao-day-du.json` lộ lỗi F, G |
| 8 | ISO | UEFI | Boot trực tiếp | T2 | ✅ 22 việc; lỗi F vẫn còn → đổi cách sửa |
| 9 | ISO | **UEFI + SB** | Mạng không DHCP | **T2** | ✅ **24/24 việc, 0 mục chưa đạt** |
| 10 | ISO | BIOS | Mạng không DHCP | T1 | ✅ **5/5, 0 mục chưa đạt** |
| 11 | ISO | UEFI | Mạng có sẵn DHCP | T3 Win11 (sau khi sửa D, E) | ✅ **11/11, 0 mục chưa đạt** (Widgets đạt, báo cáo có mục "Sau đăng nhập") |

| 12 | **ISO cuối, cài sạch** | **UEFI + SB** | Boot trực tiếp | T2 | ✅ **24/24, 0 mục chưa đạt** |
| 13 | Pi thật | UEFI | Mạng có sẵn DHCP | TEST TOAN BO (15 bước, Office, .NET 3.5, gỡ 22 app) | ✅ **65/65 mục, 0 chưa đạt** |
| 14 | Pi thật | BIOS, **VMXNET3 + PVSCSI** (phần cứng WinPE không có driver) | Mạng có sẵn DHCP | Install windows 10 - DHCP | ❌ lộ lỗi H, I → sau khi sửa: ✅ **11/11**, Windows khởi động từ ổ PVSCSI, có mạng qua VMXNET3 |
| 15 | Pi thật | **UEFI + Secure Boot**, ổ **VirtIO** | Mạng có sẵn DHCP | TEST TOAN BO | ❌ lộ lỗi J → sau khi sửa: WinPE thấy ổ VirtIO, Windows khởi động từ ổ VirtIO |

Phủ đủ **3 kiểu máy × 3 chế độ mạng**. Máy cài sạch từ ISO cuối đạt **34/34** trên bảng kiểm "hàng đem bán": mạng 2 card, tài khoản Samba đúng, không tự phát DHCP, 44 trang không trang nào hỏng. Ngoài ra đã kiểm trong lab netns (wimboot-lab): BIOS, UEFI và UEFI+SB đều vào WinPE, `net use` Samba được.

## 3. Lỗi tìm ra và đã sửa

| | Lỗi | Nguyên nhân thật | Sửa |
|---|---|---|---|
| — | Máy BIOS đứng im ở "Booting from SAN device 0x80" (anh Thoại gặp) | Ảnh đĩa GPT+FAT32 cũ không có mã boot BIOS | **Viết lại PXE:** iPXE + shim + wimboot **bản ký chính thức** kèm sẵn; bỏ ảnh 500 MB. Bật PXE mất 0,7 giây thay vì 3 phút |
| — | UEFI: menu "Khởi động ổ cứng" rơi vào màn hình Setup của firmware | iPXE `exit` báo "thành công" nên firmware dừng lại | `exit 1` trên UEFI → firmware tự sang ổ cứng (đã xác nhận) |
| A | Secure Boot: "Security Violation" | shim xin `snponly.efi` ở chế độ proxyDHCP; trên Pi file đó là bản Debian cũ không ký | Phát bản ký dưới cả 2 tên `snponly.efi` và `ipxe.efi` |
| B | Máy cài từ ISO: WinPE `net use` báo **System error 1312** | ISO tạo nhầm tài khoản Samba `deploy` thay vì `consolepi-deploy` | Sửa ISO. Mỗi lần bật PXE tự đảm bảo tài khoản đúng, nên máy đã cài cũng tự khỏi |
| — | Máy cài từ ISO có 2 card LAN: **mất mạng** | Trình cài để lại hồ sơ NetworkManager không gắn card | Thiết lập lần đầu xoá hồ sơ đó; NetworkManager tự tạo hồ sơ cho từng card |
| C | Script **.ps1 không chạy**, mở ra Notepad rồi treo tới khi quá giờ | Gọi thẳng đường dẫn file | Chạy qua `powershell -ExecutionPolicy Bypass -File` |
| D | "Tắt Widgets" lỗi mã 1 trên Win11 | Win11 mới chặn ghi `TaskbarDa` | Dùng chính sách máy (`Dsh\AllowNewsAndInterests`, `Windows Feeds\EnableFeeds`) |
| E | Báo cáo không ghi được việc chạy sau đăng nhập | Bẫy của PowerShell 5.1 `ConvertFrom-Json` | Sửa. Báo cáo nay có mục "Sau đăng nhập" (script, lệnh thêm, cài/gỡ) |
| F | **Gỡ app kèm sẵn không ăn** (Weather/Solitaire vẫn còn) nhưng vẫn báo "xong" | Thiếu quyền, lỗi bị nuốt; gỡ offline bằng dism trong WinPE cũng không ăn | `go-app.ps1` chạy ở pha specialize (SYSTEM, trước khi có tài khoản), giống trình tạo schneegans.de → **đã xác nhận "đã gỡ"** |
| G | Báo cáo luôn ghi Num Lock "không tìm thấy" | PowerShell không có ổ `HKU:` | Dùng `Registry::HKEY_USERS\...` |
| — | Trang Tiến trình: bản ghi "?" 0/0, tên bước chỉ là "Bước 1, 2…"; 2 máy cùng tên bị gộp | PowerShell 5.1 gửi JSON bằng mã ISO-8859-1 | Gửi byte UTF-8, máy chủ đọc lại gói hỏng; bản ghi theo "tên máy · IP" |
| — | Trang Cài đặt PXE lỗi 500 khi có kịch bản | Đọc danh sách menu theo kiểu cũ | Sửa |
| — | Ô chọn GPT/MBR trong trình tạo không có tác dụng (luôn chia GPT) | Code bỏ qua lựa chọn | Tự động theo máy: UEFI → GPT, BIOS → MBR (có extended/logical khi > 3 phân vùng) |
| H | Driver "nạp vào ảnh boot" **chưa bao giờ tới WinPE** qua PXE (máy VMXNET3 vẫn "thiếu driver") | wimboot bỏ qua mọi file đuôi `.wim` khi chèn vào System32 | Chèn dưới tên `cpi-drivers.bin`, deploy.cmd chép lại rồi `dism` |
| I | Driver chỉ nạp trong WinPE, **không theo sang Windows**: ổ PVSCSI/VMD/virtio sẽ màn hình xanh INACCESSIBLE_BOOT_DEVICE, card VMXNET3 mất mạng sau cài | deploy.cmd bung ảnh bằng dism nên `DriverPaths` của unattend không có tác dụng | `dism /image:W:\ /add-driver` driver ảnh boot + driver của kịch bản. Đã thấy pvscsi.sys, vmxnet3.sys trong Windows cài xong |
| J | UEFI / Secure Boot vẫn không nhận driver sau khi sửa H | iPXE UEFI đưa file cho wimboot theo **tên cuối URL** (đối số thứ 2 của `initrd` chỉ là cmdline) → URL `.../drivers.wim` | URL đổi thành `.../cpi-drivers.bin` |
| K | Tắt máy ngay khi trang Tiến trình báo "đã xong" → không có báo cáo trên máy | Báo cáo được tạo SAU khi báo Pi | Chỉ báo "đã xong" khi báo cáo đã ghi ra đĩa |
| — | Báo cáo "Thiết bị thiếu driver: 1" với dòng tên trống | Thiết bị chưa có driver không có tên | Ghi thêm mã phần cứng (PCI\VEN_...) |
| — | Bản x86: "? °C", chữ không dấu, "vào Pi" | — | Đọc nhiệt độ qua hwmon, ghi rõ "không có cảm biến", sửa chữ |

## 4. Gói driver phổ biến (mới)

WinPE của Windows 10/11 không có driver cho: VMware VMXNET3, PVSCSI; Intel I225/I226, I219 đời 2020+; Intel RST VMD; virtio. Trang **Tài nguyên → Drivers → Gói driver phổ biến**: bấm "Tải tất cả" → Console Pi tự tải 10 gói **chính thức, Microsoft ký** từ Microsoft Update Catalog (tổng ~3,5 MB), kiểm sha256, giải nén, đánh dấu nạp vào ảnh boot. Không đóng gói sẵn driver của hãng trong sản phẩm (giấy phép) — máy người dùng tự tải như Windows Update.

Đã kiểm trên Pi thật: tải đủ 10/10 gói, sha256 khớp; drivers.wim 4,4 MB tự dựng lại; máy VMXNET3 + PVSCSI, VirtIO net + VirtIO block đều cài được.

**VMware "LSI Logic Parallel"**: Microsoft không có driver cho Windows 10/11 (đã bỏ từ Windows 8) → đổi sang LSI Logic SAS, NVMe hoặc VMware Paravirtual. Trang Drivers và Tài liệu đã ghi rõ.

## 5. ISO phát hành (build lại 26/09/2026, sau mọi bản sửa)

| Bản | File trên máy build | SHA256 |
|---|---|---|
| 64-bit | `/build/console-system/live-image-amd64.hybrid.iso` (1,51 GB) | `32189452be9b5a04d38604155e76c06811d37fb76b3abafa0d86001e0a95ceee` |
| 32-bit | `/build/console-system-i386/live-image-i386.hybrid.iso` (1042 MB) | `9cff5cd240e6cc11796a3a84a4661e5909896a9fb4e4134588a2eeb8344b1cec` |

Cài sạch ISO 64-bit cuối: bảng kiểm **34/34**. Tải gói driver phổ biến trên máy cài từ ISO: 10/10. PXE từ máy cài ISO → máy khách UEFI + VMXNET3 + PVSCSI, kịch bản T1: **5/5** (firmware OVMF của lab không boot được ổ PVSCSI nên phần sau cài chạy qua AHCI; VMware thật boot được PVSCSI, và bài test BIOS trên Pi thật đã boot Windows từ PVSCSI). Cổng mạng đã chọn không còn → PXE từ chối bật (đã thử).

## 6. Kiểm tra khác

- **Kho trung tâm** (kho-console.home-server.id.vn): trên Pi kết nối được, đọc 2 mục. Trên máy cài từ ISO: kết nối tới kho OK, token sai thì báo "Token không hợp lệ", xoá kết nối được. Muốn tải thật thì anh tạo token cho máy đó trong trang quản trị kho.
- **Bảng kiểm "hàng đem bán"** trên máy cài từ ISO: đạt toàn bộ; 3 mục dịch vụ PXE được bỏ qua đúng vì lúc đó đang bật PXE. Quét được 47 trang, không trang nào hỏng.
- **Tải script lên qua web**: OK.
- Toàn bộ code biên dịch được trên Python 3.11 (ISO i386, Debian 12) và 3.13.
- Chữ ký file boot kiểm bằng `sbverify`: shim và wimboot do Microsoft UEFI CA 2011 ký; iPXE do iPXE Secure Boot CA ký.

## 7. Việc anh cần làm

1. **Cập nhật Console Pi** (em không có quyền sudo trên Pi), rồi vào Deployment OS → Cài đặt → **Tắt PXE → Bật PXE**:
   ```bash
   sudo bash ~/cap-nhat-pi.sh
   ```
2. Thử trên VMware ở cả 3 kiểu Firmware: BIOS, EFI, EFI + Secure Boot.
3. Giới hạn cần biết: máy chuẩn "Secured-core" tắt sẵn "Microsoft 3rd-party UEFI CA" thì phải bật lại mục đó trong BIOS (mọi công cụ PXE không phải của Microsoft đều vậy).
4. Nhắc lại: đổi mật khẩu `Itadmin@2023`, vì mật khẩu này đã gửi trong chat (máy build, máy ảo VMware, trang kho).
