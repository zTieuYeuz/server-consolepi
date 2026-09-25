# File boot PXE kèm sẵn

Đây là bản phát hành chính thức, không sửa gì. Khi bật PXE, `ui/pxe.py` chép các file này vào thư mục TFTP.

| File | Nguồn | Dùng cho |
|---|---|---|
| `undionly.kpxe` | iPXE v2.0.0 `ipxeboot.tar.gz` → `x86_64/undionly.kpxe` | Máy BIOS/Legacy |
| `snponly-shim.efi` | iPXE v2.0.0 → `x86_64-sb/shimx64.efi` (shim, Microsoft UEFI CA 2011 ký) | Máy UEFI, có hoặc không Secure Boot |
| `ipxe.efi` | iPXE v2.0.0 → `x86_64-sb/snponly.efi` (iPXE Secure Boot CA ký) | shim tự tải file tên `ipxe.efi` qua TFTP |
| `wimboot` | wimboot v2.9.0 release (Microsoft UEFI CA 2011 ký) | Nạp boot.wim của Windows |

Về tên file `ipxe.efi`: shim tải tầng 2 theo tên mặc định là `ipxe.efi`. Điều này đã kiểm chứng qua log TFTP trong lab. Nên file này thực chất là bản `snponly.efi` đã ký, chỉ đổi tên. Lý do dùng snponly: NIC ảo VMware làm `ipxe.efi` đầy đủ bị crash.

Nguồn:
- https://github.com/ipxe/ipxe/releases/tag/v2.0.0
- https://github.com/ipxe/wimboot/releases/tag/v2.9.0

Giấy phép: iPXE và wimboot dùng GPLv2 / UBDL; mã nguồn có tại các link trên. shim dùng giấy phép BSD.

Kiểm tra toàn vẹn: `sha256sum -c SHA256SUMS`. Chữ ký đã kiểm bằng `sbverify --list`.
