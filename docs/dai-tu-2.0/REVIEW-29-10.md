# Bước 1 — Review toàn bộ hệ thống (29/10/2026)

Phạm vi: `consolepi-toolkit` (nhánh v2, ~48.700 dòng Python), `kho-console-pi` (~3.700 dòng, đang chạy trên .34), `consolepi-docs` (37 trang).

## Kết quả công cụ tự động (toolkit, `tools/ci.sh`)
| Bước | Kết quả |
|---|---|
| ruff | 1 lỗi: `uem_kichban.py:128` f-string không có biến (F541) |
| import-linter (luật kiến trúc) | đạt |
| Cú pháp Python 3.11 (Debian 12) | đạt |
| pytest | 292 đạt, 61 bỏ qua (cần phần cứng/WinRM thật), 1 xfail |
| Độ phủ lõi `core/` | 78% (ngưỡng 70%) |
| bandit | 41 cảnh báo; mức cao: B202 tarfile (`core/dichuyen.py:138` — Python < 3.11.4 không có `filter`), B103 chmod 0777 TFTP_ROOT, B324 SHA1 dùng làm khóa nhận diện (không phải bảo mật) |

Kho: 12 test đạt. Mã kho trên .34 khớp từng file với repo (chỉ thiếu thư mục tests, đúng thiết kế). Có `tools/windows/bat-winrm.ps1` chưa commit.

## Phát hiện cần sửa (đưa vào bước 3/4)
### Bảo mật
1. **Kho — chuyển hướng mở sau đăng nhập**: `auth._vao_duoc` chặn `//evil` nhưng không chặn `/\evil.com` (trình duyệt hiểu như `//`). Sửa: chỉ nhận đường bắt đầu bằng `/` theo sau là ký tự khác `/` và `\`.
2. **Toolkit — giải nén tar không lọc** khi Python thiếu `tarfile.data_filter` (Debian 12 gốc là 3.11.2): `core/dichuyen.py`. Sửa: tự kiểm từng mục (tên an toàn, không link, không thiết bị) như `saoluu.py` đã làm.
3. **TFTP_ROOT chmod 0777**: thu hẹp quyền (0755, chủ sở hữu dnsmasq/tftp đọc được).
4. **Tailscale cài bằng `curl … | sh`** (`remote.py`): chấp nhận được (nguồn chính thức, HTTPS) nhưng nên ghi rõ trong tài liệu; cân nhắc gói apt có ký.
5. Cảnh báo bandit mức trung/thấp còn lại: đọc lại từng cái ở bước 4.

### Ổn định / đúng chức năng (đã biết từ các phiên trước, cần kiểm lại ở bước 3)
6. CMD gõ tiếng Việt bị lỗi font (PowerShell đúng).
7. Remote Desktop: chưa thử đăng nhập thật vào màn hình Windows.
8. Đợt cài và kịch bản Agent cùng cài lên một máy có thể đụng nhau (msiexec 1618) — có thử lại, nhưng nên xếp hàng theo máy.
9. Dừng kịch bản chỉ có hiệu lực sau bước đang chạy (bộ cài không ngắt được) — ghi rõ trên giao diện (đã ghi).
10. Bản tiếng Anh: mới dịch câu ngắn; đoạn hướng dẫn dài còn tiếng Việt.

### Bảo trì / sắp xếp
11. File quá lớn, khó sửa: `network.py` 1.743 dòng, `dosui_kichban.py` 1.513, `uem_trang_b.py` 1.448, `layout.py` 1.157, `tk_trang.py` 1.115, `pxe.py` 1.085, `tk_dongco.py` 1.003. Tách theo chức năng ở bước 4.
12. HTML lẫn trong chuỗi Python ở nhiều trang (đã tách 37 chuỗi lớn ra `assets/`; còn nhiều trang mới viết thêm: kịch bản Agent, Profile, Remote Desktop).
13. Thư mục cũ `/var/lib/console-pi` trên máy chuyển từ 1.9 còn bản sao cấu hình cũ (đã có bản thật trong `/var/lib/console-system`).

### Tài liệu (web docs)
14. Docs dừng ở **1.9.4**: thiếu toàn bộ phần 2.0 — Quản lý máy trạm (agent, Profile, Tường lửa, Dịch vụ), Cài phần mềm qua Agent (đợt cài, kịch bản, Run As), Cài phần mềm qua LAN, Tài nguyên máy, Remote Desktop, Hỗ trợ từ xa, Cập nhật (chuông, nâng/hạ cấp, khóa máy), Sao lưu một thư mục, tiếng Anh. `tai-ve.json` còn 1.9.4.

### Phát hành
15. Tài liệu tin cậy hết hạn **23/04/2027** — phải ký lại bằng khóa gốc trước ngày đó.
16. Kênh Ổn định qua tên miền Cloudflare chưa thử đầu-cuối (25/10 mới thử kênh Thử nghiệm qua LAN).
17. Pi .14 đang 2.0.0 (25/10), chưa có các thay đổi từ 26/10.
