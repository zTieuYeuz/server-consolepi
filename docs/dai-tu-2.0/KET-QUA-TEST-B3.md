# Kết quả test bước 3 (29/10/2026, máy .30 + máy ảo Windows .29 + kho .34)

Ký hiệu: ĐẠT / LỖI→ĐÃ SỬA / CHƯA TEST (lý do).

## Vòng tự động
| Mã | Kết quả |
|---|---|
| T0.1 | ĐẠT sau khi sửa 1 lỗi ruff (F541 `uem_kichban.py`). 292 test đạt, độ phủ lõi 78% |
| T0.2 | ĐẠT (hợp đồng 403 route) |
| T0.3 | ĐẠT: `tools/quet-route.py` quét 160 trang GET trên .30 — 0 lỗi 5xx, 0 trang treo. POST từ LAN khi chưa đăng nhập: mọi route bị chặn, trừ `/api/tiendo/*` (mở đúng thiết kế khi PXE đang chạy — đã kiểm `dnsmasq-pxe` active) |
| T0.4 | ĐẠT (test XSS 40 trang) |
| T0.5 | ĐẠT kho 12 test |

## Thử thật
| Mã | Kết quả |
|---|---|
| 1.6 | ĐẠT: từ /console bấm menu → chỉ cột phải tải lại, giữ biến JS, bỏ thuộc tính tmux |
| 1.12 | ĐẠT (28/10) câu ngắn; đoạn hướng dẫn dài còn tiếng Việt |
| 4.7 | ĐẠT: một dòng "guacd đang kết nối được" |
| 4.8 | CHƯA TEST: cần anh nhập mật khẩu Windows (chỉ thử được tới bước NLA, sai mật khẩu báo rõ) |
| 5.3 | LỖI→ĐÃ SỬA (29/10): máy có agent báo "Chờ gán tài khoản" → giờ "Đang giám sát" / "Chưa cài agent" |
| 5.7 | ĐẠT CMD/PowerShell, cửa sổ lớn tab mới; CMD gõ tiếng Việt lỗi font (hạn chế đã biết) |
| 5.8 / 5.9 / 5.10 | ĐẠT (261 dịch vụ, 100 tiến trình, tải win.ini) |
| 5.11 | ĐẠT VNC qua agent (28/10) |
| 5.21 | ĐÃ SỬA (agent 2.3.6 bỏ tác vụ PowerShell phiên người dùng); CHƯA thấy tận mắt vì máy ảo không ai đăng nhập |
| 6.3 / 6.5 / 6.7 / 6.8 / 6.10 | ĐẠT (28–29/10: cài kho, máy tắt→chờ→bật tự cài, kịch bản 2 phần mềm, Run As có nhật ký 4624 type 4) |
| 6.9 | ĐẠT bằng test tự động (dừng/tiếp tục); chưa bấm tay trên máy thật |
| 8.4 | ĐẠT 18 loại tác vụ chạy 2 lần trên W (`tools/thu-tac-vu-profile.py`); tường lửa 4 loại (29/10). Chưa chạy thật: winget_go, msi_cai, msi_go |
| 9.1 | ĐẠT ping, DNS, TLS |
| 12.1 | ĐẠT tải lên / tải về / xóa |
| 13.2 | ĐẠT tải gói sao lưu cấu hình (352 mục, có DB + secrets); khôi phục sang máy mới: làm ở bước 7 |
| 13.3 | LỖI→ĐÃ SỬA: deploy/storage là liên kết ra ngoài → đã gom (14 GB, 0,6 giây) |
| 13.4 | ĐẠT |
| 13.8 | CHƯA TEST đầu-cuối kênh Ổn định: cần gói ký bằng khóa phát hành của anh |
| 3.x, 4.4, 9.3, 9.7, 9.8 | CHƯA TEST: cần phần cứng (thẻ WiFi, Bluetooth, cáp console, switch) — .30 không có |
