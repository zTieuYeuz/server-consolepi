# Kết quả test bước 5 — sau tối ưu (29/10/2026, .30 bản 2.0.0-4 + W .29)
| Mã | Kết quả |
|---|---|
| T0.1 | ĐẠT: CI XANH (ruff, import-linter, Python 3.11, bandit mức cao 0, 292 pytest, độ phủ lõi 78%); kho 13 test đạt |
| T0.2 | ĐẠT: trang sinh ra giống hệt từng byte sau khi tách uem_trang_b |
| T0.3 | ĐẠT: 160 trang GET, 0 lỗi |
| 5.8 / 5.9 / 5.10 / 9.1 / 12.1 / 13.2 / 13.4 | ĐẠT (`tools/thu-chuc-nang.py`) |
| 6.3 | ĐẠT: đợt cài từ kho → Hoàn tất mã 0 |
| 6.7 | ĐẠT: kịch bản Agent Lưu và chạy → xong mã 0; Xóa được |
| 8.4 | ĐẠT: 18 loại tác vụ chạy 2 lần, lần 2 "đã đúng sẵn" |
| Mượt | 22 trang chính < 0,07 giây |
Các ca CHƯA TEST giữ nguyên như bước 3 (cần mật khẩu Windows, khóa ký, phần cứng WiFi/Bluetooth/cáp console).
