# File boot PXE kèm sẵn

Đây là bản phát hành chính thức, không sửa gì. Khi bật PXE, `ui/pxe.py` chép các file này vào thư mục TFTP.

| File | Nguồn | Dùng cho |
|---|---|---|
| `undionly.kpxe` | iPXE v2.0.0 `ipxeboot.tar.gz` → `x86_64/undionly.kpxe` | Máy BIOS/Legacy |
| `snponly-shim.efi` | ipxe/shim `ipxe-16.1` → `ipxe-shimx64.efi` (ký **cả** Microsoft UEFI CA 2011 **và** Microsoft UEFI CA 2023) | Máy UEFI, có hoặc không Secure Boot |
| `ipxe.efi`, `snponly.efi` | iPXE v2.0.0 → `x86_64-sb/snponly.efi` (iPXE Secure Boot CA ký), 2 bản giống hệt | shim tải tầng 2 qua TFTP |
| `wimboot` | wimboot v2.9.0 release (ký cả Microsoft UEFI CA 2011 và 2023) | Nạp boot.wim của Windows |

Về 2 tên file: shim xin tầng 2 bằng tên nào còn tuỳ trường hợp. Log TFTP thật cho thấy: khi Pi cấp IP (DHCP đầy đủ) nó xin `ipxe.efi`, còn khi dùng proxyDHCP trên mạng công ty nó xin `snponly.efi`. Vì vậy phát cùng một bản `snponly` đã ký dưới cả hai tên. Lý do dùng snponly: NIC ảo VMware làm `ipxe.efi` đầy đủ bị crash.

## Chứng chỉ Secure Boot 2011 hết hạn (từ 1.8.7)

Chứng chỉ Microsoft UEFI CA 2011 hết hạn 6/2026. Máy đời mới có thể chỉ tin chứng chỉ 2023.
Shim trong bản iPXE v2.0.0 chỉ ký 2011 nên bị chặn ngay ("Access Denied"). Từ 1.8.7 Console System
dùng shim `ipxe-16.1` ký kép, kèm wimboot 2.9.0 (cũng ký kép): máy cũ và máy mới đều qua được.

Bước cuối là bootmgr của Windows (nằm trong boot.wim, ký "Windows Production PCA 2011"). Máy chỉ tin
2023 sẽ báo "Security Policy Violation" ở đây. Bộ cài Windows 11 từ 24H2 có sẵn bản bootmgr ký
"Windows UEFI CA 2023" (`\Windows\Boot\EFI_EX\bootmgfw_EX.efi`). Console System tự trích bản này
(`ui/pxemenu.py: _trich_bootmgr_ex`) và chỉ dùng khi bật mục **"4. May moi..."** trong menu PXE, vì
máy cũ chưa cập nhật chứng chỉ 2023 lại chặn bản này.

Kiểm chứng (lab QEMU/OVMF, `iso/test/wimboot-lab.sh` với `VARS=` là firmware chỉ có chứng chỉ 2023):

| Firmware | Shim | bootmgr | Kết quả |
|---|---|---|---|
| chỉ 2011 | cũ (2011) | thường | ĐẠT |
| chỉ 2023 | cũ (2011) | thường | firmware chặn shim (Access Denied) |
| chỉ 2011 | mới (ký kép) | thường | ĐẠT |
| chỉ 2023 | mới (ký kép) | thường (Win10) | qua shim, iPXE, wimboot; chặn bootmgr 2011 |
| chỉ 2023 | mới (ký kép) | **EX** (Win11 26H2) | ĐẠT - vào WinPE, Secure Boot bật, nối được share |
| chỉ 2011 | mới (ký kép) | EX (Win11 26H2) | firmware chặn bootmgr 2023 (vì vậy mặc định TẮT) |
| chỉ 2011 | mới (ký kép) | thường (Win11 26H2) | ĐẠT |

Nguồn:
- https://github.com/ipxe/ipxe/releases/tag/v2.0.0
- https://github.com/ipxe/wimboot/releases/tag/v2.9.0
- https://github.com/ipxe/shim/releases/tag/ipxe-16.1

Giấy phép: iPXE và wimboot dùng GPLv2 / UBDL; mã nguồn có tại các link trên. shim dùng giấy phép BSD.

Kiểm tra toàn vẹn: `sha256sum -c SHA256SUMS`. Chữ ký đã kiểm bằng `sbverify --list`.
