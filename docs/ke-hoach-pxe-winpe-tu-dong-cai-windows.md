# Kế hoạch: PXE Boot + WinPE + Tự động cài Windows (kiểu MDT) trên Console Pi

> Bản phác thảo ban đầu đã được anh Thoại đồng ý triển khai. Mục "Tiến độ
> thật" bên dưới ghi lại chính xác đã làm tới đâu, kiểm chứng được gì, và
> đang thiếu gì - cập nhật theo từng phiên làm việc thật, không phải kế
> hoạch tĩnh nữa.

## Tiến độ thật (cập nhật 2026-09-08)

**Đã xong và kiểm chứng thật trên máy:**
- Cài `wimtools` (wimlib 1.14.4) - **đính chính so với bản phác thảo ban
  đầu**: KHÔNG cần máy Windows + Windows ADK để xử lý file `.wim`/`.esd`
  như dự đoán ban đầu. wimlib trên Linux đọc/tách/trích xuất được trực
  tiếp, đã kiểm chứng thật (xem `wiminfo`, `wimlib-imagex export`,
  `wimlib-imagex extract` chạy thành công trên chính Pi).
- Tách `install.wim` (Windows 10 Pro, do anh Thoại chọn) từ `install.esd`
  gộp 7 phiên bản trong ISO - dùng `wimlib-imagex export ... 6
  --compress=LZX`.
- Tải `iPXE` (gói apt `ipxe` có sẵn trong kho Debian, không cần internet
  ngoài) - lấy `undionly.kpxe` (máy BIOS) và `ipxe.efi`/`snponly.efi`
  (máy UEFI).
- Tải `wimboot` (dự án chính thức của cùng tác giả iPXE, tải qua GitHub
  API `ipxe/wimboot` - bản x86_64 cho máy đích, không phải bản ARM64 của
  Pi).
- **Phát hiện quan trọng**: `\Windows\Boot\PXE\bootmgr.exe` (máy BIOS) và
  `\Windows\Boot\PXE\wdsmgfw.efi` (máy UEFI) - bộ bootmgr CHUYÊN DỤNG cho
  boot-qua-mạng - nằm SẴN bên trong `boot.wim`, không cần lấy từ ISO. Đã
  viết `ui/pxe.py: trich_bootmgr_tu_winpe()` dùng `wimlib-imagex extract`
  để lấy trực tiếp, kiểm chứng thật (file trích ra đúng, đọc được).
- Dựng `ui/pxe.py`: cấu hình `dnsmasq` cho cả 3 kiểu boot (trực tiếp/mạng
  không DHCP dùng DHCP đầy đủ; mạng có DHCP dùng proxyDHCP), nhận diện
  kiến trúc máy (RFC 4578 option 93) để phát đúng bootloader BIOS/UEFI,
  chặn vòng lặp vô tận qua `dhcp-userclass=set:ipxe,iPXE`, sinh script
  `menu.ipxe` chỉ định `wimboot` nạp `boot.wim`+`BCD`+`bootmgr.exe`. Đã
  kiểm chứng cú pháp cả 3 cấu hình bằng `dnsmasq --test` (hợp lệ).
- Đường phục vụ file cho máy đích qua HTTP mà KHÔNG cần đăng nhập
  (`/deployos/pxeboot/<file>`) - chỉ mở khi PXE đang thật sự BẬT, chỉ phục
  vụ đúng thư mục lưu trữ, đã kiểm thử chặn vượt thư mục/đuôi file lạ.
- Thẻ "Sẵn sàng PXE" + nút Bật/Tắt thật trong bước 7 của trình tự - đọc
  đúng trạng thái thật, không giả vờ.
- Bộ kiểm thử riêng cho `pxe.py`: 14 phép thử, đạt hết.

**Lỗi thật đã gặp trong quá trình làm (ghi lại để không lặp lại):**
- Đã LỠ XOÁ file ISO gốc trước khi kịp lấy file `BCD` (2 file nhỏ ở
  `boot/bcd` và `efi/microsoft/boot/bcd`) - phải nhờ anh Thoại tải lại ISO
  một lần nữa. Bài học: khi xử lý ISO nguồn, phải liệt kê ĐẦY ĐỦ mọi thứ
  cần trích trước khi xoá bản gốc, không xoá theo từng đợt.
- Ban đầu đặt điều kiện hiện nút "Bật PXE" phụ thuộc vào việc file
  `/etc/dnsmasq-pxe.conf` đã tồn tại sẵn - nhưng file đó chỉ được tạo ra
  KHI bấm chính nút đó, tạo vòng luẩn quẩn (nút cần thiết bị chính điều
  kiện của nó khoá). Đã sửa: bỏ hẳn kiểm tra tĩnh đó, thay bằng
  `pxe.trang_thai_chuan_bi()` là nguồn sự thật duy nhất.

**Cập nhật 2026-09-08 (lần 2) - đã lấy đủ file BCD:**
- Anh Thoại tải lại ISO, lần này đã lấy đủ `boot/bcd` (BIOS) và
  `efi/microsoft/boot/bcd` (UEFI) TRƯỚC khi xoá ISO - rút kinh nghiệm từ
  lần trước.
- **Bảng "Sẵn sàng PXE" giờ đủ 4/4 điều kiện (`san_sang_bat() == True`
  - kiểm chứng thật)**. Nút "Bật PXE ngay" đã hiện đúng qua HTTP thật ở
  bước 7, kèm cảnh báo cắt DHCP trên eth0.
- **CHƯA tự bấm "Bật PXE"**: việc này cắt DHCP trên chính cổng eth0 của
  Pi - cổng đang được dùng làm đường kết nối cho chính phiên làm việc này
  (192.168.110.14). Bấm nhầm sẽ tự ngắt kết nối giữa chừng. Đây là bước
  anh Thoại cần tự làm cùng lúc cắm 1 máy PC thật vào Pi để thử.

**Chưa kiểm chứng được (cần phần cứng thật, không giả lập được trên Pi):**
- Toàn bộ chuỗi boot thật từ 1 máy PC/laptop thật qua PXE tới màn hình cài
  đặt Windows - CHƯA có máy thật nào để thử. Mọi thứ ở trên mới kiểm chứng
  được ở mức "đúng cơ chế, đúng cú pháp, đúng file" chứ chưa "đã tận mắt
  thấy 1 máy boot thành công". Bước tiếp theo bắt buộc là anh Thoại thử
  trên 1 máy thật (khuyến nghị máy test, không phải máy khách) sau khi có
  đủ file BCD.

## 1. Bối cảnh và mục tiêu

Anh Thoại là kỹ thuật viên mạng đi hiện trường sửa switch/router. Nhu cầu
mới: khi gặp 1 máy PC hỏng (Windows lỗi, cần cài lại), muốn cắm dây mạng
vào Console Pi rồi **boot thẳng vào WinPE qua mạng**, tự động cài lại
Windows + phần mềm cần thiết mà không cần mang theo USB cài đặt riêng hay
gõ tay từng bước.

Mô hình tham khảo: MDT (Microsoft Deployment Toolkit) của Microsoft - vốn
chạy trên Windows Server, dùng WDS (Windows Deployment Services) làm PXE
server. **MDT bản thân không cài lên Linux/Pi được** - nhưng cơ chế bên
dưới nó dùng (PXE boot -> WinPE -> script tự động chia ổ, áp ảnh, cài
driver, cài phần mềm) hoàn toàn dựng lại được bằng công cụ Linux có sẵn.
Đây chính là hướng đi của kế hoạch này.

## 2. Luồng hoạt động tổng quan

```
[PC hong] --day LAN--> [Console Pi]
   |
   | 1. PC bat, chon boot qua mang (PXE) trong BIOS/UEFI
   | 2. PC gui broadcast DHCP xin dia chi + noi lay file boot
   v
[dnsmasq tren Pi] --tra ve IP (hoac chi tra "boot file o dau" neu dung
                    proxyDHCP song song DHCP cong ty)--> [PC]
   |
   | 3. PC tai file bootloader nho (iPXE) qua TFTP
   v
[iPXE chay tren PC] --tai wimboot/boot.wim qua HTTP (nhanh, on dinh
                       hon TFTP rat nhieu voi file lon)--> [nginx tren Pi]
   |
   | 4. WinPE khoi dong, tu chay 1 script (khong can nguoi bam gi)
   v
[Script trong WinPE]:
   - Chia o dia (diskpart)
   - Ap anh Windows tu file .wim/.esd (dism /apply-image)
   - Ghi bootloader (bcdboot)
   - Copy unattend.xml vao dung cho
   - Khoi dong lai -> Windows Setup tu chay tiep (khong hoi gi nho
     unattend.xml): dat ten may, mang, tai khoan...
   |
   v
[FirstLogonCommands trong unattend.xml] --tu dong chay--> Script cai
   phan mem (uu tien winget neu co internet, roi lai file MSI/EXE luu
   san tren Pi neu khong co internet)
```

## 3. Các thành phần cần có trên Pi

| Thành phần | Vai trò | Đã có sẵn trong Console Pi? |
|---|---|---|
| `dnsmasq` | DHCP/proxyDHCP + TFTP (giai đoạn 1: phát iPXE) | Có (dùng cho TFTP server + AP hiện tại) - cần thêm cấu hình PXE riêng |
| `nginx` | Phục vụ `boot.wim`/ảnh Windows qua HTTP (nhanh hơn TFTP nhiều với file lớn) | Có sẵn, chỉ thêm 1 `location` mới |
| iPXE (`undionly.kpxe` / `ipxe.efi`) | Bootloader trung gian: TFTP tải file này trước (nhỏ), rồi nó tự chuyển sang tải qua HTTP | Cần tải về, không có sẵn trên Pi (không phải gói apt, tải file build sẵn từ ipxe.org) |
| Chỗ chứa ảnh Windows (`install.wim`) + WinPE (`boot.wim`) | Ảnh cài đặt + môi trường cài đặt | Cần **ổ USB rời** gắn thêm - SD card của Pi không đủ chỗ (1 bộ ISO Windows + tùy biến WinPE dễ chiếm 5-10GB) |
| Samba (`smbd`) | Windows Setup/WinPE cần 1 share mạng kiểu `\\pi\deploy` để truy cập file trong lúc cài | Chưa có - cần cài mới (gói `samba`) |
| `unattend.xml` | File trả lời tự động cho Windows Setup (ổ đĩa, tên máy, tài khoản, chạy lệnh sau cài) | Tự soạn riêng theo từng phiên bản Windows |
| Script cài phần mềm | Chạy sau khi Windows cài xong, tự cài Chrome/... | Tự viết (PowerShell hoặc batch) |

## 4. Hai kịch bản đấu nối mạng

### Kịch bản A - Cắm thẳng Pi <-> PC hỏng (khuyến nghị mặc định)

- Pi chạy DHCP đầy đủ (giống `dnsmasq-direct` hiện có khi cắm LAN thẳng),
  không đụng chạm gì mạng công ty khách.
- Đơn giản, an toàn nhất, không lo đụng độ DHCP.
- Nhược điểm: PC đang cài không ra internet được (trừ khi Pi làm NAT chia
  mạng qua WiFi - có thể làm thêm nếu cần `winget` lúc cài phần mềm).

### Kịch bản B - Pi và PC cùng cắm qua switch chung (có DHCP công ty)

- Pi phải chạy **proxyDHCP** (`dhcp-range=<mang>,proxy` trong dnsmasq) -
  chỉ trả lời câu hỏi "file boot ở đâu", KHÔNG cấp phát IP (để DHCP server
  thật của công ty lo việc đó, tránh đụng độ 2 DHCP cùng cấp IP).
- PC có thể ra internet bình thường qua router công ty -> `winget` dùng
  được ngay.
- Phức tạp hơn: phải kiểm tra kỹ mạng khách có cho phép broadcast DHCP
  option 60/66/67 đi qua không (một số switch/router lọc các gói PXE).

**Khuyến nghị**: làm kịch bản A trước (chắc ăn, không phụ thuộc mạng
khách), kịch bản B để sau nếu thấy cần.

## 5. Tự động cài phần mềm sau khi cài Windows xong

Theo đúng thống nhất với anh Thoại - **kết hợp cả 2 cách, chọn theo tình
huống**:

1. `unattend.xml` (đoạn `FirstLogonCommands`) chạy 1 script điều phối
   (PowerShell) ngay lần đăng nhập đầu tiên.
2. Script kiểm tra có internet không (`Test-Connection`/ping 1.1.1.1):
   - **Có internet** -> dùng `winget install <ten-app> --silent
     --accept-package-agreements` cho từng phần mềm trong danh sách (luôn
     lấy bản mới nhất, không cần tự host file).
   - **Không internet** -> lấy file cài đặt (MSI/EXE) từ share Samba của
     Pi (`\\<ip-pi>\deploy\apps\`), chạy silent install tương ứng
     (`msiexec /i ... /quiet /norestart` hoặc `... /S`/`/verysilent` tuỳ
     hãng - mỗi phần mềm có cờ silent khác nhau, cần tra và ghi chú rõ
     trong danh sách).
3. Danh sách phần mềm cấu hình dễ sửa (vd 1 file JSON/YAML đơn giản), để
   anh Thoại tự thêm/bớt phần mềm mà không cần sửa script.

## 6. Việc cần làm nếu quyết định triển khai (các giai đoạn)

Làm từng giai đoạn, test xong mới sang giai đoạn kế - đúng cách làm mọi
tính năng khác của Console Pi:

1. **Giai đoạn 1 - Hạ tầng PXE cơ bản**: cấu hình dnsmasq proxyDHCP/DHCP +
   TFTP cho iPXE, tải sẵn iPXE build, xác nhận 1 máy ảo/PC thật boot được
   tới màn hình iPXE (chưa cần WinPE, chỉ cần thấy iPXE chạy là qua được
   phần khó nhất của PXE).
2. **Giai đoạn 2 - Boot được vào WinPE**: dựng ảnh WinPE (cần Windows ADK
   để tạo `boot.wim` tuỳ biến - **phải làm trên 1 máy Windows riêng**, Pi
   không tự tạo được ảnh này, chỉ lưu trữ và phục vụ nó), cấu hình iPXE
   chainload đúng file, xác nhận vào được màn hình dấu nhắc lệnh WinPE qua
   mạng.
3. **Giai đoạn 3 - Tự động chia ổ + áp ảnh Windows**: soạn script WinPE tự
   chạy (`diskpart`, `dism /apply-image`, `bcdboot`), test trên 1 máy thật
   không tiếc dữ liệu (máy test, KHÔNG test trên máy khách thật).
4. **Giai đoạn 4 - `unattend.xml`**: soạn file trả lời tự động, test toàn
   bộ chuỗi từ PXE tới lúc vào được màn hình Desktop mà không cần bấm gì.
5. **Giai đoạn 5 - Tự động cài phần mềm**: script điều phối winget/offline
   theo mục 5, test với vài phần mềm mẫu (Chrome, ...).
6. **Giai đoạn 6 - Tài liệu hoá + gắn vào giao diện Console Pi**: thêm 1
   trang trong dashboard hiện có để bật/tắt dịch vụ PXE, xem trạng thái,
   quản lý danh sách phần mềm - theo đúng khuôn mẫu các module khác trong
   `nettools`/`ui`.

## 7. Rủi ro và giới hạn cần anh Thoại biết trước

- **Bản quyền Windows**: `unattend.xml` cần product key hoặc máy phải kích
  hoạt bằng cách khác (KMS/số hoá quyền - digital license theo phần
  cứng). Cần anh Thoại xác nhận cách anh đang có license Windows hợp lệ
  cho các máy sửa, vì đây là quyết định của anh chứ Console Pi không tự ý
  chọn giúp.
- **Driver theo từng dòng máy**: nếu anh sửa nhiều loại máy khác nhau
  (khác hãng, khác đời), MDT có tính năng "chọn driver theo model" khá
  hay - tự làm lại phần này tốn công nhất, có thể để đơn giản hoá bằng
  cách chỉ hỗ trợ vài dòng máy anh hay gặp nhất trước.
- **Tạo ảnh WinPE cần máy Windows riêng có cài ADK** - Pi/Linux không tự
  làm được bước này, chỉ lưu trữ và phục vụ ảnh đã tạo sẵn.
- **PXE chỉ hoạt động qua dây LAN**, không qua WiFi (giới hạn của chuẩn
  PXE, không phải giới hạn của Pi).
- **Rủi ro xoá nhầm dữ liệu**: script `diskpart`/`dism` là thao tác GHI
  ĐÈ Ổ ĐĨA - phải có bước xác nhận rõ ràng (hoặc chọn đúng ổ theo kích cỡ/
  serial) trước khi chạy, tránh xoá nhầm ổ đang có dữ liệu quan trọng nếu
  máy có nhiều hơn 1 ổ cứng.

## 8. Câu hỏi cần anh Thoại quyết định trước khi bắt đầu code

1. Ưu tiên kịch bản mạng nào trước - A (cắm thẳng) hay B (qua switch
   công ty)?
2. Nguồn Windows ISO/license dùng cho việc này là gì (Windows 10/11,
   phiên bản Pro/Home, key theo dạng nào)?
3. Anh có sẵn 1 máy Windows để tạo ảnh WinPE tuỳ biến (cần cài Windows
   ADK) không, hay cần em hướng dẫn dựng tạm?
4. Danh sách phần mềm cần tự động cài là gì (ngoài Chrome) - để lên danh
   sách mẫu ban đầu?
5. Có ổ USB rời nào định gắn thêm vào Pi để chứa ảnh Windows không, dung
   lượng khoảng bao nhiêu?
