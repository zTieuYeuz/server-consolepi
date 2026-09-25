# Script test (chỉ dùng trên máy build, máy ảo bỏ đi)

Không có file nào ở đây nằm trong ISO phát hành. Mật khẩu trong các script, như `Test12345` hay `Test@1234`, chỉ thuộc máy ảo test.

| Script | Việc |
|---|---|
| `cai-uefi.sh [iso] [thu_muc] [dung_luong]` | Cài ISO tự động lên ổ ảo (UEFI, ISO cắm như USB) |
| `boot-uefi.sh` | Boot ổ vừa cài (SSH 18022, web 18080) |
| `kiem-tra-may-da-cai.sh` | Chạy bên trong máy đã cài: bảng kiểm "hàng đem bán" |
| `wimboot-lab.sh <bios\|uefi\|sb> <dir>` | Lab netns: iPXE ký + wimboot + boot.wim thật vào WinPE, `net use` Samba, đọc PEFirmwareType / SecureBoot. Có `DISK=` để gắn ổ Windows (thử menu "Khởi động ổ cứng") |
| `pxe-lab.sh` + `sinh-cau-hinh.py` | Lab netns kiểm dnsmasq + menu do chính code sinh ra, 3 chế độ mạng |
| `pi-that.sh <bios\|uefi\|sb> start\|odia\|key\|chup\|stop` | Máy ảo ra **LAN thật** qua macvtap, boot từ **Console Pi thật** (chế độ "Mạng có sẵn DHCP") và cài Windows trọn vẹn |
| `may-chu-iso.sh` | Lab đầy đủ: **máy cài từ ISO** làm máy chủ (2 card mạng), mạng `brlab` riêng, router giả cho chế độ có DHCP, máy khách BIOS/UEFI/Secure Boot. Lệnh `cap-nhat` đẩy code mới nhất trong repo vào máy chủ, không phải build lại ISO |
| `chay-khach.sh <fw> <n>` | Bật máy khách, chờ tải menu, chọn "Install Windows" rồi kịch bản thứ n+1, chụp màn hình mỗi phút |
| `tao-kich-ban.py` | Chạy trên máy chủ: tạo bộ kịch bản test **qua chính trình tạo trên web**: T1 cơ bản, T2 đầy đủ (6 phân vùng, Administrator, phần mềm, script, tuỳ chọn, gỡ app), T3 Win11 |
| `tep-kich-ban/` | Script test (.ps1/.cmd) tải lên kho, chạy trên máy Windows sẽ ghi file dấu vết vào `C:\ConsolePi` |

Kiểm kết quả cài: tắt máy khách rồi `qemu-nbd -r -c /dev/nbd1 disk.qcow2` và `mount -t ntfs-3g -o ro /dev/nbd1pN`. Sau đó đọc các file trong `C:\ConsolePi`: `BAO-CAO-TONG-KET.txt`, `tien-trinh.log` và các file dấu vết.
