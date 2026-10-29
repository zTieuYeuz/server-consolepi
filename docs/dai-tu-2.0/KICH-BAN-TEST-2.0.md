# Kịch bản test Console System 2.0 (bước 2 — 29/10/2026)

Dùng cho bước 3 (test lần 1), bước 5 (test lại sau tối ưu) và bước 7 (test trên Console mới cài từ ISO / ảnh Pi).
Mỗi lần chạy ghi kết quả vào `KET-QUA-TEST-<buoc>.md` cùng mã ca test (ĐẠT / LỖI / KHÔNG TEST ĐƯỢC + lý do).

## Môi trường
| Mã | Máy | Dùng cho |
|---|---|---|
| A | Console amd64 (.30; bước 7: máy ảo mới cài từ ISO) | toàn bộ giao diện web, PXE, WinRM, agent |
| P | Raspberry Pi (.14; bước 7: thẻ nhớ mới ghi từ ảnh Pi) | WiFi/AP, Bluetooth, màn hình cảm ứng, cáp console |
| W | Windows 11 thử (máy ảo ESXi "windows test" .29) | agent, WinRM, PXE cài Windows, RDP, VNC |
| K | Kho .34 (kho-console.home-server.id.vn) | Kho trung tâm, cập nhật, góp ý |
| D | Web docs (Cloudflare Pages) | tài liệu, trang tải về |

Cách test: **T** = tự động (pytest / script), **W** = thao tác thật trên giao diện web (trình duyệt), **H** = cần phần cứng thật (cáp console, thẻ WiFi, Bluetooth, màn hình cảm ứng). Ca H không có phần cứng → ghi KHÔNG TEST ĐƯỢC, không ghi ĐẠT.

## 0. Vòng tự động (chạy đầu tiên mỗi lần)
| Mã | Nội dung | Cách | Mong đợi |
|---|---|---|---|
| T0.1 | `tools/ci.sh`: ruff, import-linter, cú pháp Python 3.11, bandit, pytest, độ phủ lõi | T | CI XANH |
| T0.2 | Hợp đồng route (403 route) / trang / hành vi không đổi ngoài chỗ cố ý | T | khớp |
| T0.3 | **Quét từng route trên máy thật**: mọi trang GET (đã đăng nhập) trả 200/302 hợp lệ, không 500; mọi POST không token bị chặn khi chưa đăng nhập từ mạng | T+W | không route nào 500; route công khai đúng danh sách |
| T0.4 | Không trang nào in `<script>` từ dữ liệu người dùng (XSS) | T | đạt |
| T0.5 | Kho: `pytest tests` | T | đạt |
| T0.6 | Docs: `python3 build.py` dựng được site, không link hỏng | T | đạt |

## 1. Đăng nhập, khung trang, giao diện
| Mã | Chức năng | Bước | Mong đợi |
|---|---|---|---|
| 1.1 | Đăng nhập đúng (PAM) | /login với tài khoản Linux | vào Tổng quan, nhật ký ghi "Đăng nhập thành công" |
| 1.2 | Đăng nhập sai | sai mật khẩu | báo lỗi, không lộ mật khẩu trong nhật ký |
| 1.3 | Đăng xuất | /logout | về /login, phiên hết hiệu lực |
| 1.4 | Truy cập từ mạng chưa đăng nhập | mở trang bất kỳ | chuyển /login (trừ danh sách công khai) |
| 1.5 | Màn hình tại chỗ (kiosk, cổng 8880) | mở không đăng nhập | vào được; /cap-nhat vẫn yêu cầu đăng nhập quản trị |
| 1.6 | Menu trái tải riêng cột phải | bấm 10 mục menu liên tiếp, kể cả từ Console/SSH | cột trái giữ nguyên, nút Quay lại đúng, không lỗi JS |
| 1.7 | Tìm chức năng (Ctrl+K) | gõ "winrm", "pxe" | ra đúng mục, bấm mở đúng trang |
| 1.8 | Giao diện sáng/tối | đổi chủ đề | áp dụng mọi trang |
| 1.9 | Chế độ cảm ứng / PC | /giaodien | đổi bố cục, quay về trang cũ |
| 1.10 | Bàn phím ảo | trang Console/SSH ở chế độ cảm ứng | hiện, gõ được vào phiên |
| 1.11 | Popup xác nhận giữa màn hình | mọi nút Xóa/Dừng | popup giữa màn hình, không dùng confirm() gốc |
| 1.12 | Tiếng Anh | Cài đặt → Language → English | menu, nút, nhãn tiếng Anh; về tiếng Việt được |
| 1.13 | Chip trạng thái LAN/WiFi trên thanh trên | quan sát | đúng IP / trạng thái |
| 1.14 | Thương hiệu, logo, favicon | xem trang đăng nhập + khung | hiện đúng |

## 2. Tổng quan (/)
| 2.1 | Thẻ tổng quan | mở / | CPU, RAM, ổ, nhiệt độ, mạng hiện số thật |
| 2.2 | /api/status, /api/suckhoe | gọi API | JSON hợp lệ |
| 2.3 | Lối tắt chức năng | bấm từng thẻ | mở đúng trang |

## 3. Kết nối vào Console
| 3.1 | WiFi: quét, kết nối, lưu, xóa, ngắt, thêm tay | P: thao tác thật | kết nối được, lưu sau khởi động lại (file trong /var/lib/console-system/secrets/he-thong/wifi) — H |
| 3.2 | WiFi: phát AP ConsolePi, giải phóng AP, ép AP | P | điện thoại thấy & vào được — H |
| 3.3 | WiFi: đổi MAC (bật/tắt) | P | MAC đổi đúng — H |
| 3.4 | Bluetooth: quét, ghép, kết nối, gỡ, ghép lại, reset; mạng qua Bluetooth (PAN) | P | — H |
| 3.5 | Truy cập qua Internet: lưu token Cloudflare, bật/tắt tunnel, xóa token | A/P | token lưu trong secrets/cloudflared-token; tunnel chạy; xóa thì tắt |
| 3.6 | Tailscale: cài, authkey, bật/tắt, quên | A | trạng thái đúng; authkey trong secrets/ |

## 4. Thiết bị mạng
| 4.1 | Phiên kết nối: tạo phiên SSH/Telnet/Serial nhanh, lưu, nhóm (tạo/đổi tên/xóa), xóa phiên | W | danh sách đúng, mở terminal |
| 4.2 | Phiên: đổi baud, dán chữ, gửi mật khẩu, xem log, ngắt | W/H | đúng |
| 4.3 | Thư viện lệnh trong phiên | W | chèn lệnh |
| 4.4 | Console Serial: liệt kê cổng, mở /console/<dev> | H | thấy dấu nhắc thiết bị |
| 4.5 | SSH: kết nối máy có SSH (vd .30 → .34), dán | W | phiên chạy |
| 4.6 | Terminal cục bộ, dán | W | chạy lệnh |
| 4.7 | Remote Desktop: trạng thái guacd (một dòng), cài/bật guacd | W | "guacd đang kết nối được" |
| 4.8 | Remote Desktop: kết nối RDP máy W bằng tài khoản thật (anh nhập) | W | thấy màn hình, chuột/phím, Ctrl+Alt+Del, toàn màn hình, ngắt |
| 4.9 | Remote Desktop: sai mật khẩu / máy tắt | W | báo lỗi rõ ràng |

## 5. Quản lý máy trạm (UEM)
| 5.1 | Tổng quan máy trạm: các thẻ số, bấm thẻ lọc | W | số khớp danh sách |
| 5.2 | Máy tính: lọc tên/IP/nhóm/HĐH/hãng/thẻ/địa điểm/trạng thái | W | đúng |
| 5.3 | Trạng thái máy: Đang giám sát / Không kết nối / Chưa cài agent / Chưa có báo cáo / Quá hạn / Vô hiệu | W | máy có agent không bao giờ "Chờ gán tài khoản" |
| 5.4 | Thao tác hàng loạt (3 cột): lấy thông tin, nhóm (thêm/gỡ/tạo), thẻ, địa điểm, bật/tắt giám sát, xóa | W | mỗi việc đúng, xóa có popup |
| 5.5 | Trang máy — nhóm tab: Tổng quan, Phần cứng, HĐH & phần mềm, Điều khiển từ xa, Chia sẻ & sửa lỗi, Quản lý | W | mọi tab mở được, có dữ liệu thật của W |
| 5.6 | Ghi chú, Thông tin thêm (metadata), Quản lý (tên, IP, MAC, thẻ, địa điểm, giám sát) | W | lưu được |
| 5.7 | Dòng lệnh: CMD, PowerShell (tiếng Việt), lịch sử ↑↓, Đóng, Xóa màn hình, **Mở cửa sổ lớn** (tab mới, ?mo=cmd) | W | chạy đúng; rời trang tiến trình trên máy tắt |
| 5.8 | Dịch vụ: liệt kê, lọc, chạy/dừng/khởi động lại, đổi kiểu khởi động | W | đúng trên W |
| 5.9 | Tiến trình: liệt kê, kết thúc | W | đúng |
| 5.10 | Duyệt file: liệt kê, tải về, tải lên, tạo thư mục, xóa | W | đúng |
| 5.11 | Điều khiển từ xa: VNC (cài TightVNC, mở, kết thúc, gỡ), tải file RDP, RustDesk của máy | W | xem được màn hình W |
| 5.12 | Nguồn: khởi động lại / tắt / ngủ đông / hủy lệnh; bật bằng Wake-on-LAN | W | đúng (WoL: H nếu VM không hỗ trợ) |
| 5.13 | Chia sẻ & sửa lỗi: các mục sửa lỗi in/chia sẻ, máy in (xóa) | W | chạy được, báo kết quả |
| 5.14 | Báo cáo ngay (Lấy thông tin) | W | cập nhật giờ báo cáo |
| 5.15 | Phần mềm đã cài (toàn bộ / chi tiết theo phần mềm / CSV) | W | đúng |
| 5.16 | Bảo mật, Cập nhật Windows | W | dữ liệu thật |
| 5.17 | Báo cáo + 7 file CSV | W | tải được, mở Excel đúng UTF-8 |
| 5.18 | Quản trị: thẻ, metadata, địa điểm, cài đặt (tần suất), nhật ký, máy giám sát | W | thêm/sửa/xóa được |
| 5.19 | Agent: tạo gói MSI (có/không passkey), lưu passkey triển khai, đưa vào kho phần mềm (tự điền tham số), tải, xóa, TLS, cài đặt agent | W | MSI cài được trên W |
| 5.20 | Agent: cài qua WinRM, gỡ, đổi chứng chỉ, mã ghi danh | W | đúng |
| 5.21 | Agent tự cập nhật khi đổi phiên bản; **không bật cửa sổ CMD/PowerShell** khi người dùng đăng nhập Windows | W | tray chạy, không cửa sổ |
| 5.22 | Agent: biểu tượng khay (xem log, đồng bộ, chẩn đoán) | W | đúng |

## 6. Cài phần mềm qua Agent
| 6.1 | Cài bằng WinGet: tìm, chọn máy/group, cài/nâng cấp/gỡ, nâng cấp tất cả, nhập mã gói | W | đúng trên W |
| 6.2 | Cập nhật danh mục WinGet | W | số gói tăng |
| 6.3 | Cài từ kho phần mềm (file .exe/.msi) | W | cài xong, mã thoát 0 |
| 6.4 | Chính sách: thử lại N lần, chờ tối đa N ngày, Wake-on-LAN | W | lưu vào đợt |
| 6.5 | **Máy tắt**: đợt → "Chờ máy bật"; khởi động lại Console vẫn còn; bật máy tự cài | W | Hoàn tất |
| 6.6 | Trạng thái triển khai: đếm theo trạng thái, chi tiết, Hủy máy đang chờ, Chạy lại máy lỗi | W | đúng |
| 6.7 | Kịch bản: tạo (phần mềm, máy/group, SYSTEM, chạy ngay), Lưu và chạy, tiến độ từng bước | W | xong |
| 6.8 | Kịch bản: máy tắt → chờ → bật → tự cài | W | xong |
| 6.9 | Kịch bản: Dừng giữa chừng, Tiếp tục (không cài lại bước đã xong), Chạy lại từ đầu, Xóa | W | đúng |
| 6.10 | Kịch bản: cài bằng tài khoản (Run As) | W | nhật ký Security W: logon type 4 đúng user; tác vụ tạm + file mật khẩu đã xóa |
| 6.11 | Kịch bản: hẹn giờ riêng (hằng ngày/tuần/tháng/năm/một lần), lịch dùng chung | W | chờ tới giờ; chạy đúng giờ |
| 6.12 | Lịch sử triển khai | W | ghi kết quả cuối |

## 7. Hỗ trợ từ xa (RustDesk) + VNC
| 7.1 | 5 tab bước: máy chủ, Internet/NAT, file MSI, triển khai, bảng hỗ trợ, cài đặt, lịch sử | W | đúng |
| 7.2 | Cài máy chủ hbbs/hbbr, kiểm tra, khóa | A | dịch vụ chạy |
| 7.3 | Tải MSI RustDesk (đã điền máy chủ), cài client lên W, gán ID, mật khẩu, kết nối trên trình duyệt | W | xem được W |
| 7.4 | ID đã đăng ký nhưng chưa cài agent: hiện hostname/user/OS/online, xóa ID | W | đúng |
| 7.5 | Ghi hình phiên, xóa ghi hình, lịch sử | W | đúng |
| 7.6 | VNC trang riêng: tải TightVNC 32/64, chạy, trạng thái | W | đúng |
| 7.7 | doi-may-chu.ps1, cho-phep-trinh-duyet.reg | W | tải được, nội dung đúng máy chủ |

## 8. Cấu hình (Profiles)
| 8.1 | Tạo, đổi tên, mô tả, bật/tắt (nút đầu trang), áp dụng ngay, xóa | W | đúng |
| 8.2 | Phạm vi: tất cả / nhóm / thẻ | W | số máy đúng |
| 8.3 | Thẻ loại tác vụ + 8 mẫu điền sẵn form | W | form điền đúng |
| 8.4 | Mỗi loại tác vụ chạy thật trên W, chạy 2 lần (lần 2 "đã đúng sẵn"): WinGet cài/gỡ; Registry 6 loại; Người dùng tạo/xóa; Nhóm 4 loại; MSI cài/gỡ; PowerShell một lần/mỗi chu kỳ; **Tường lửa 4 loại; Dịch vụ** | W | đúng, idempotent |
| 8.5 | Sắp thứ tự ↑↓, tắt tác vụ, sửa, xóa, "lỗi thì chạy tiếp" | W | đúng |
| 8.6 | Agent tự áp dụng khi mất kết nối Console (tác vụ tự trị) | W | đúng |
| 8.7 | Tab Kết quả từng máy, Vấn đề | W | đúng |

## 9. Công cụ mạng (/nettools — 15 công cụ)
| 9.1 | Ping, DNS check, TLS check, MTU, DHCP test | A | kết quả thật |
| 9.2 | ARP scan, L2 scan, topology (bản đồ mạng), LLDP | A | thấy thiết bị LAN |
| 9.3 | 802.1X (dot1x) | H | — |
| 9.4 | Bắt gói (pcap): start/stop/tải/chuyển đổi | A | file .pcap mở được |
| 9.5 | TFTP: bật/tắt/tải/xóa | A | đúng |
| 9.6 | If-then rules: thêm/xóa/đánh giá/xuất/nhập (mã hóa) | A | đúng |
| 9.7 | Netmiko: form, test kết nối (chỉ đọc), xem trước, chạy | H (cần switch) | — |
| 9.8 | Sao lưu cấu hình qua cáp console: chụp, tải, xóa | H | — |

## 10. Cài Windows qua mạng (Deploy OS)
| 10.1 | Wizard bắt đầu (từng bước) | W | đúng |
| 10.2 | Hệ điều hành: tạo, tải ISO/WIM/SxS, tách, xóa, tiến độ tách | A | đúng |
| 10.3 | Driver: tạo gói, tải file, model, gói phổ biến, nạp cho boot, xóa | A | đúng |
| 10.4 | Font: tạo bộ, tải, xóa | A | đúng |
| 10.5 | Ứng dụng nhiều file: tạo, tải, lệnh cài, xóa mục | A | đúng |
| 10.6 | Kịch bản Windows: tạo/sửa/xóa, mẫu CSV, đặt tên máy 5 cách | W | đúng |
| 10.7 | PXE: bật/tắt, cổng, trích bootmgr, menu PXE, WinPE riêng | A | máy W boot mạng (F12) thấy menu |
| 10.8 | **Cài Windows thật trên W qua PXE** kịch bản LaptopHome đủ 21 bước, kèm agent | W | xong, agent nối |
| 10.9 | Tiến trình cài (từng máy, xóa dòng), lịch sử + CSV, ổ đĩa (xóa) | W | đúng |
| 10.10 | Hạ tầng (kiểm infrastructure), Wake-on-LAN (thêm/gửi/xóa), tham số | A | đúng |
| 10.11 | Kho trung tâm (trong deploy): ghép, tải 1/nhiều, tiến độ, hủy, xóa cấu hình | A+K | tải về đúng SHA-256 |

## 11. Cài phần mềm qua LAN (WinRM)
| 11.1 | Máy: thêm tay, sửa, xóa, kiểm tra, quét mạng + thêm, kiểm kê + CSV | W | đúng |
| 11.2 | Nhóm máy, tài khoản quản trị (thêm/thử/xóa), bật WinRM (script, chỉ cho Console) | W | đúng |
| 11.3 | Kịch bản: các bước (phần mềm, ứng dụng, script, WinGet, RustDesk, nguồn, bảo mật, kiểm kê, nhóm tài nguyên), "chỉ cài một lần" | W | đúng |
| 11.4 | Lịch (5 kiểu), Chạy/Dừng, tiến độ (xóa dòng), chạy nhanh | W | đúng |
| 11.5 | Không thấy kịch bản / lịch riêng của Agent ở trang LAN | W | đúng |

## 12. Kho lưu trữ
| 12.1 | Kho file: tải lên, tải về, xóa | A | đúng |
| 12.2 | Tài nguyên máy (8 tab): phần mềm (tham số), script, file, nhóm tài nguyên... | A | đúng |
| 12.3 | Kho trung tâm: ghép token, duyệt, tải | A+K | đúng |
| 12.4 | Thư viện lệnh: thêm/sửa/xóa/gửi | A | đúng |

## 13. Hệ thống
| 13.1 | Cài đặt: xoay màn hình, kiosk bật/tắt, tạo lại mật khẩu terminal, dọn rác, ngôn ngữ | A/P | đúng |
| 13.2 | **Sao lưu** cấu hình / toàn bộ: tải về; **khôi phục** sang máy mới → mọi dữ liệu trở lại (máy, kịch bản, agent nối lại, WiFi, token) | A | đúng |
| 13.3 | Tất cả dữ liệu nằm trong /var/lib/console-system (không liên kết ra ngoài trừ liên kết ngược) | A | `find` không thấy dữ liệu người dùng ngoài thư mục |
| 13.4 | Nhật ký: xem, tải | A | đúng |
| 13.5 | Nguồn: khởi động lại / tắt Console | A | đúng |
| 13.6 | Góp ý: gửi kèm ảnh tới kho | A+K | kho nhận |
| 13.7 | Giải trí, Tài liệu (/docs) | A | mở được |
| 13.8 | **Cập nhật**: chỉ quản trị thấy chuông/tab; điều khoản; kiểm tra ngay; nâng cấp (mật khẩu, gõ CAP NHAT, sao lưu, tải gói, kiểm chữ ký, kiểm từng file, khởi động lại dịch vụ, nhắc khởi động lại máy); hạ cấp; hủy | A+K | bản 2.0.x → 2.0.x+1 qua **kênh Ổn định trên tên miền Cloudflare** |
| 13.9 | Cập nhật: gói sửa đổi / sai chữ ký / nhảy cấp / PXE đang chạy / không phải quản trị / mất điện giữa chừng | T+A | bị chặn hoặc tự hoàn tác |
| 13.10 | Chống chỉnh sửa (sửa 1 file → chặn cập nhật, báo kho); khóa / mở khóa máy bằng lệnh ký | T+A | đúng |

## 14. Kho (.34) và Web docs
| 14.1 | Kho: đăng nhập, MFA, khóa sau nhiều lần sai, chuyển hướng `ve=` chỉ nội bộ | K | đúng |
| 14.2 | Kho: thêm/tải mục, font, bộ khởi động, tham số, góp ý, cập nhật (danh mục/gói/khóa gói/báo cáo), máy nghi ngờ, lệnh khóa | K | đúng |
| 14.3 | Kho: sao lưu tự động 05:00 kéo về build-os (gồm capnhat/) | K | có bản mới |
| 14.4 | Docs: mọi trang mở được, mục 2.0 đầy đủ, trang tải về đúng bản + SHA-256 | D | đúng |

## 15. Cài đặt mới (bước 7)
| 15.1 | ISO amd64: cài trên máy ảo UEFI (và BIOS), lần đầu khởi động, thiết lập lần đầu, bảng kiểm 62 mục | A | đạt |
| 15.2 | Ảnh Pi: ghi thẻ, boot Pi thật, thiết lập lần đầu, AP, màn hình cảm ứng | P | đạt |
| 15.3 | Máy mới tự đăng ký kho, thấy bản cập nhật kênh Ổn định | A+K | đạt |
| 15.4 | Chạy lại toàn bộ mục 1–14 trên máy mới | | |
