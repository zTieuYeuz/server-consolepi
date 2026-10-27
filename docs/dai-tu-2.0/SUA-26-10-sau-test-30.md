# Sửa theo test trên .30 (26/10/2026)

| Mục | Việc | Trạng thái |
|---|---|---|
| 1.1 | Phiên "Kết nối nhanh gần đây": thêm nút ✕ xóa | xong, test tự động |
| 1.2 | Gốc lỗi: `scripts/phien-mo.sh` (và vài script) mất quyền chạy trong bản phát hành -> ttyd không mở được phiên. Sửa: 755 trong git + unit gọi qua `/bin/bash` + test canh quyền | xong; cần cài bản mới lên .30 |
| 2.1 | Ping / Traceroute / Chạy cả 2: 3 nút riêng | xong |
| 2.2 | PCAP: thêm giải thích dùng khi nào (bắt trên cổng mạng đã chọn, không phải cổng serial) | xong |
| 2.3 | LLDP/CDP: ISO không bật CDP cho lldpd như Pi (`DAEMON_ARGS="-c"`); đã thêm vào hook ISO. Nguyên nhân còn lại là vật lý: .30 cắm sau switch không chuyển LLDP | xong phần mã |
| 2.4 | Hướng dẫn test Netmiko / 802.1X / IF-THEN | `HUONG-DAN-TEST-NETTOOLS.md` |
| 3.1 | "Tự động đăng nhập tài khoản Administrator" + cảnh báo + popup xác nhận | xong |
| 4.1 | Xóa dòng kết quả (từng máy / tất cả thành công / tất cả lỗi) trong bảng tiến độ triển khai | xong, test |
| 4.2 | WinRM có ổn không | xem báo cáo trả lời |
| 4.3 | Script `bat-winrm.ps1` (tải ở trang Triển khai phần mềm; bản sao trong kho `tools/windows/`) | xong, chưa chạy trên Windows thật |
| 5.1 | Xóa máy khỏi quản lý (máy có agent: ẩn, tự hiện lại khi agent báo nhịp) | xong, test |
| 5.2 | Tab Dòng lệnh (CMD/PowerShell) | xong, test với client giả; chưa thử Windows thật |
| 5.3 | Bỏ tab Triển khai trùng ở từng máy | xong |
| 5.4 | Tab Dịch vụ + Tiến trình (xem, chạy/dừng/khởi động lại, kiểu khởi động, kết thúc tiến trình) | xong, test client giả |
| 5.5 | Agent tự cập nhật: đã có sẵn (so sánh phiên bản mỗi nhịp, tự biên dịch bản mới). Thêm test ép tăng `VER_FILE` khi sửa mã C# | xong |
| 5.6 | Profile: giải thích + sắp xếp theo bước | xong |
| 5.7 | Lỗi hiển thị nút "Chọn nhóm máy" (dấu `"` trong thuộc tính HTML) | xong |
| 5.8 | RustDesk Server tích hợp + cài client kèm máy chủ ID / chuyển tiếp (agent, Triển khai phần mềm, script) | xong, thử thật trên .30 + .33 (agent và WinRM) |
| 5.9 | Tab "Sửa lỗi in/chia sẻ" (kịch bản duyệt sẵn) | xong, test client giả; chưa thử Windows thật |

Chưa làm được: kiểm trực tiếp SSH tới 192.168.110.21 / 192.168.100.2 qua giao diện (chỉ xác nhận SSH tới .21 đăng nhập được từ máy build; 192.168.100.2 chưa thử).

## RustDesk làm lại (26/10 tối, theo yêu cầu anh)
- Bỏ hướng web: gõ chữ qua web client không ổn. Đã gỡ khỏi mã: thẻ rustdesk-api, chế độ WebSocket, hướng dẫn Cloudflare. RustDesk Server bản miễn phí chỉ nhận máy đăng ký ID qua UDP 21116, Cloudflare Tunnel không chuyển UDP.
- Cấu hình chỉ còn **Máy chủ ID** và **Máy chủ chuyển tiếp** (để trống = trùng máy chủ ID; cả hai để trống = IP LAN). Cổng cần mở ra Internet: TCP 21115, 21116, 21117 và UDP 21116. Máy trong LAN cũng dùng địa chỉ công khai nên router cần NAT loopback.
- Cài client luôn kèm máy chủ ID / chuyển tiếp / key / mật khẩu chung, dùng chung `cai_va_ghi()`: nút Cài ở trang RustDesk (agent), bước **RustDesk** trong Triển khai phần mềm (WinRM, kể cả Chạy nhanh), bộ cài `rustdesk*.exe/.msi` trong Tài nguyên (kiểm SHA-256 chính file đó). Danh mục WinGet không có gói RustDesk.
- Cài client ghi cả cấu hình dịch vụ lẫn cấu hình riêng từng người dùng (C:\Users\*\AppData\Roaming\RustDesk). Bước "chỉ cài một lần" tính theo địa chỉ máy chủ: đổi máy chủ thì lần chạy sau cài lại.
- Bộ cài chạy qua WMI `Win32_Process.Create` để tách khỏi phiên WinRM (WinRM đóng phiên giết tiến trình con, làm máy mất dịch vụ RustDesk khi cài đè); chờ dịch vụ mới chạy rồi mới cấu hình.
- Thử thật trên .33: gỡ RustDesk → cài bằng agent (1 phút 23 giây) → `RustDesk2.toml` dịch vụ đúng máy chủ/key, nhật ký RustDesk `start udp: 192.168.110.30:21116` + độ trễ. Cài qua kịch bản WinRM 2 lần (lần đầu máy thiếu dịch vụ, lần sau cài đè): xong, dịch vụ chạy, đăng ký lại. Cài lại bằng agent sau khi cố ý đổi cấu hình người dùng sang `dummy.invalid`: file được sửa về .30.
- Chưa thử: địa chỉ công khai thật (chờ anh mở cổng và đưa tên miền/IP), máy ở ngoài Internet, NAT loopback của router.

## RustDesk theo luồng người dùng (26/10 khuya)
Luồng: cài ISO → trang RustDesk bước 1 cài máy chủ → bước 2 nhập tên miền/IP công cộng, cổng NGOÀI của máy chủ ID (P) và chuyển tiếp (R), mật khẩu chung → bảng hướng dẫn NAT tự tính: P-1/TCP → 21115, P/TCP+UDP → 21116, R/TCP → 21117 (3 cổng, 4 dòng NAT) → bước 3 file cài `Cai-RustDesk-ConsoleSystem` (.bat bấm đúp / .ps1) điền sẵn tất cả, tự lưu và tự cập nhật trong kho Triển khai phần mềm (Tài nguyên, Script) → bước 4 deploy (Script từ kho, bước RustDesk, nút agent, hoặc gửi .bat) → bước 5 tab Hỗ trợ từ xa của máy.
- Chạy file từ kho bằng Triển khai phần mềm: ID tự ghi vào Console (tab Hỗ trợ từ xa dùng được ngay).
- Thử thật: tạm chuyển cổng trên .30 (nft) 1221/1222/1300 → 21115/21116/21117, cấu hình cổng ngoài 1222/1300, chạy file từ kho qua WinRM trên .33: ID ghi lại, cấu hình dịch vụ + người dùng là `:1222` / `:1300`, nhật ký RustDesk `nat response from :1222` và `:1221`, `start udp :1222`. Đã trả về cấu hình LAN và gỡ chuyển cổng.
- Chạy file .bat thật trên .33: lần đầu lỗi (script ghi ra không BOM, PowerShell 5.1 đọc sai tiếng Việt) → đã sửa, chạy lại cài xong và in ID.
- Chưa thử: cổng chuyển tiếp khi kết nối thật phải đi relay, tên miền thật ngoài Internet, NAT loopback.


## RustDesk: một file MSI (26/10, 23:30)
- Bước 2 còn 2 ô (tên miền hoặc IP WAN, mật khẩu); máy chủ chuyển tiếp riêng ở mục Nâng cao. Anh chọn NAT thẳng từ IP WAN (`itserver.asuscomm.com` → 118.68.146.97, không CGNAT).
- Bỏ .bat/.ps1, thay bằng `Cai-RustDesk-ConsoleSystem.msi` (wixl): chứa sẵn bộ cài RustDesk 1.5.0 chính thức (SHA-256 ghim, tải 1 lần về thư mục dữ liệu) + script điền máy chủ ID / chuyển tiếp / key / mật khẩu chung, chạy bằng custom action deferred SYSTEM (loại 3122), nhật ký `C:\Windows\Temp\cs-rustdesk-cai.log`. MSI tự tạo lại vào kho Phần mềm khi đổi cấu hình; cài qua bước Phần mềm của Triển khai phần mềm thì ID tự ghi vào Console.
- Thử thật .33: gỡ RustDesk → kịch bản WinRM bước Phần mềm cài MSI: mã thoát 0, ID 163846525 ghi lại, dịch vụ chạy, cấu hình `itserver.asuscomm.com`, đăng ký UDP 21116 qua router. Chưa thử: bấm đúp MSI có UAC trên máy người dùng, máy ngoài Internet thật.

## RustDesk bước 5 - bảng điều khiển (27/10)
- Bảng máy: tên, IP, online/offline (agent), ID, mật khẩu, nút **Kết nối**, **Kiểm tra máy** (đọc bản RustDesk, dịch vụ, máy chủ ID/chuyển tiếp đang trỏ, chế độ duyệt, ID); ô tìm kiếm; danh sách ID đã đăng ký nhưng chưa gắn máy kèm nút Gắn.
- Hỏi phép trước khi kết nối (như VNC): hộp Có/Không trên máy qua agent, 40 giây; từ chối/hết giờ thì Console không trả về liên kết kết nối. Đây là lớp hỏi của Console, người biết mật khẩu vẫn tự vào được bằng RustDesk.
- Tùy chọn "Bắt buộc duyệt ngay trong RustDesk": đặt `approve-mode = click` (đưa vào MSI, script cấu hình và bước Áp dụng); khi bật, mọi kết nối phải được người ngồi máy bấm Chấp nhận. Đã thử thật: giá trị được ghi đúng vào cấu hình dịch vụ + người dùng trên .33. Chưa thử: kết nối thật để thấy hộp Chấp nhận, hộp hỏi phép trên màn hình thật (cần người ngồi máy).

## RustDesk tab 6 Cài đặt + tab 7 Lịch sử + ghi hình (27/10)
- Console nghe cổng **21114** (API server mặc định của client RustDesk = máy chủ ID, cổng ID - 2). Client tự gửi: nhịp `/api/heartbeat` kèm mã các kết nối đang mở (3 giây/lần khi có kết nối), kiểm toán `/api/audit/conn` (new + IP, xác thực + ID/tên máy kết nối tới + loại, close). Trả lời nhịp `{"disconnect":[mã]}` thì client ngắt ngay kết nối đó (đọc mã nguồn RustDesk 1.5.0: `hbbs_http/sync.rs`, `server/connection.rs`). Router cần thêm NAT TCP 21114 (bảng ở bước 2 đã thêm dòng).
- Chế độ (tab 6, áp cho mọi kết nối): **Thông báo** = khi có kết nối đã xác thực, màn hình máy hiện thông báo (WTSSendMessage qua agent, không chờ) ghi tên người dùng Console nếu bấm từ Console, không thì tên máy kết nối tới. **Xin phép** = nút Kết nối hiện hộp Có/Không giữa màn hình (agent, 300 giây) ghi tên người dùng Console; đồng ý thì 5 phút được bắt đầu kết nối, phiên đó mở thêm kết nối (truyền file) vẫn được; mọi kết nối khác bị ngắt qua nhịp (kể cả lúc đang nhập mật khẩu).
- Bỏ: tùy chọn approve-mode click và hộp hỏi 40 giây ở bước 5 (thay bằng tab 6). Dịch vụ `console-system-rustdesk-api` cũ trên .30 đã dừng + tắt (chiếm cổng 21114), dữ liệu còn nguyên.
- Lịch sử (tab 7): `data/rustdesk/lich-su.jsonl`, dọn bản ghi quá 90 ngày mỗi ngày; ghép thành phiên: bắt đầu, máy, người kết nối, IP, loại, thời lượng, kết quả, bản ghi hình.
- Ghi hình: `allow-auto-record-incoming = 'Y'` (MSI, script cấu hình, Áp dụng); dịch vụ RustDesk ghi vào `C:\ProgramData\RustDesk\recording` (đọc từ mã nguồn `video_save_directory(root)`). Vòng nền 2 phút lấy file đã xong (không ghi thêm 90 giây) qua agent về `data/rustdesk/ghi-hinh/<máy>/`, kiểm kích thước rồi xóa trên máy; chỉ hỏi máy vừa có kết nối, 30 phút quét hết 1 lần; vượt giới hạn GB thì xóa bản cũ nhất; ổ còn dưới 2 GB thì tạm dừng.
- Thử thật: RustDesk 1.5.0 trên .33 gửi nhịp về .30 (tạm đặt `api-server = http://192.168.110.30:21114` trên .33 vì router chưa NAT 21114); thông báo WTSSendMessage hiện được trên .33 (TB_OK). Chưa thử được: kết nối RustDesk thật (ngắt khi chưa xin phép, lịch sử phiên thật, file ghi hình thật) vì không có máy kỹ thuật chạy RustDesk để em tự kết nối.
