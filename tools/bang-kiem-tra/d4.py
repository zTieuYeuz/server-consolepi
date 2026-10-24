# -*- coding: utf-8 -*-
S11 = """
Tài nguyên (dùng chung trang Deployment OS)|Phần mềm / Ứng dụng nhiều file / Font / Script|Triển khai phần mềm > Tài nguyên: tải từng loại|Tải được; thanh tab chỉ có Phần mềm, Ứng dụng, Font, Script, Nhóm tài nguyên (ẩn Hệ điều hành/Driver/WinPE); tab sáng đúng mục|Có file|C|TT
Tài nguyên (dùng chung trang Deployment OS)|Nhóm tài nguyên|Tạo nhóm gồm nhiều phần mềm/script|Dùng được như 1 bước (loại "Nhóm tài nguyên")|-|T|TT
Kho trung tâm trong ngữ cảnh Triển khai|Tải script/font từ kho|Triển khai phần mềm > Kho trung tâm|Tải được trong ngữ cảnh Triển khai, thanh tab đúng|Kho|T|TT
Máy - Danh sách|Thêm máy theo IP|Máy - nhóm máy > Danh sách > thêm (IP, tên, tài khoản)|Thêm được; trùng IP bỏ qua|Máy Windows|C|TT
Máy - Danh sách|Sửa / xoá / bật-tắt|Dùng các nút|Đúng|-|C|TT
Máy - Danh sách|Kiểm tra kết nối (WinRM)|Bấm kiểm tra|Báo thành công/sai tài khoản/không tới được bằng thông báo dễ hiểu|Windows bật WinRM|C|TH
Máy - Danh sách|Hướng dẫn bật WinRM|Đọc hướng dẫn trên trang|Có LocalAccountTokenFilterPolicy=1 cho tài khoản cục bộ; Console System không tự bật hộ|-|T|TH
Máy - Nhóm máy|Tạo/sửa/xoá nhóm máy|Tab Nhóm máy|Gán máy vào nhóm; dùng nhóm làm đích kịch bản|-|C|TT
Máy - Quét mạng|Quét LAN + dải thêm|Nhập CIDR (vd 192.168.2.0/24), Quét mạng LAN|Tiến độ n/m; liệt kê IP, tên, MAC, cổng mở; tick Thêm các máy đã chọn; tạo luôn nhóm|Mạng nhiều máy|C|TH
Máy - Tài khoản quản trị|Thêm / thử đăng nhập / xoá tài khoản|Tab Tài khoản quản trị|Mật khẩu lưu mã hoá (Fernet, khoá .khoa 0600), không hiện lại; Thử đăng nhập báo đúng/sai; tránh thử sai nhiều lần làm khoá tài khoản|Máy Windows|C|TH
Kịch bản|Tạo kịch bản nhiều bước|Kịch bản > thêm bước: Phần mềm, Ứng dụng, Script, WinGet, Nguồn điện (bật/tắt/khởi động lại), Kiểm tra bảo mật, Kiểm kê|Lưu được, sửa được|-|C|TT
Kịch bản|Bước Phần mềm (exe/msi)|Chạy trên máy đích|Máy đích tự tải qua /tk/tai/<token>/<tên> (token 2 giờ, chỉ IP nội bộ), cài im lặng đúng|Windows|C|TH
Kịch bản|Bước Script (.ps1/.bat)|Chạy|Kết quả đúng; .bat tải qua token|Windows|C|TH
Kịch bản|Bước Ứng dụng nhiều file|Chạy|Giải nén + chạy lệnh cài|Windows|T|TH
Kịch bản|Bước WinGet|Chạy cài một gói|Cài với --scope machine; lỗi báo rõ|Windows 10/11 có winget|C|TH
Kịch bản|Bước Nguồn điện: Bật (WoL)|Máy đang bật / đang tắt|Máy đang bật thì bỏ qua; MAC phải hợp lệ|WoL|T|TH
Kịch bản|Bước Nguồn điện: Tắt / Khởi động lại|Chạy (tắt thử rồi huỷ bằng shutdown /a)|Thực hiện đúng; khởi động lại thật máy lên lại|Windows|C|TH
Kịch bản|Bước Kiểm kê + Bảo mật|Chạy|Có kiểm kê (tên máy, hãng, model, serial, OS, CPU, RAM, IP, ổ, phần mềm, CSV) và trạng thái bảo mật|Windows|C|TH
Kịch bản|Chỉ cài một lần|Bật tuỳ chọn, chạy 2 lần|Lần 2 bỏ qua nếu đã thành công|-|C|TH
Kịch bản|Thử lại|Máy tắt, bước lỗi|Máy tắt thử lại sau 5 phút; bước lỗi thử lại sau 15 phút, tối đa 3 lần|-|T|TH
Lập lịch|Hẹn giờ hằng ngày|Tạo lịch hằng ngày|Chạy đúng giờ, không lặp; chỉ tính các lần hẹn SAU lúc bấm Chạy|Windows|C|TH
Lập lịch|Hằng tuần / tháng / năm|Tạo các lịch|Tính ngày đúng (đã kiểm bằng unit test, chưa chờ đúng ngày thật)|-|T|TD
Triển khai|Chạy / Dừng + popup tiến độ|Bấm Chạy kịch bản trên nhiều máy|Popup tiến độ từng máy (Đang chạy/xong/lỗi); song song tối đa 10; nút Dừng; chạy lại khi kịch bản không lịch đã xong|2+ máy|C|TH
Triển khai|Chạy nhanh|Chạy nhanh một bước|Tự tắt sau khi xong|Windows|T|TH
Triển khai|Máy không tồn tại / tắt|Có máy offline trong đợt|Báo "chờ máy lên", KHÔNG làm hỏng máy khác|Máy offline|C|TH
Triển khai|Khởi động lại dịch vụ giữa lượt chạy|Restart console-pi-dashboard khi đang chạy|Vẫn chạy tiếp (bước dài đang chạy sẽ chạy lại từ đầu)|-|T|TH
Chức năng khác|Kiểm kê một máy + CSV|Chức năng khác / Máy > Kiểm kê|Bảng thông tin + danh sách phần mềm có ô tìm + Tải CSV|Windows|C|TH
Chức năng khác|Bảo mật / Nguồn điện nhanh|Dùng các nút|Hoạt động|Windows|T|TH
Thông tin chung|Mật khẩu admin lưu mã hoá|Xem file dữ liệu|Không có mật khẩu rõ trong dữ liệu/nhật ký|-|C|TT
Thông tin chung|Bộ lập lịch không đăng nhập thử bằng mật khẩu giả|Dữ liệu mẫu bật=True khi dịch vụ chạy|KHÔNG dựng dữ liệu mẫu bật khi dịch vụ chạy (đã bị khoá tài khoản thử)|-|C|TH
Thông tin chung|Nhiều máy thật song song|Chạy 10+ máy thật|Chạy song song đúng (mới thử 1 máy thật)|10+ máy|C|CH
Thông tin chung|Máy domain / GPO|Máy trong domain có GPO chặn|Hoạt động hoặc báo rõ (chưa kiểm chứng)|AD|T|CH
"""

S12 = """
Tổng quan máy trạm|Dashboard|Quản lý máy trạm > Tổng quan máy trạm|Các số liệu: số máy, online/offline, hệ điều hành, phần mềm, bảo mật... đúng dữ liệu|Có máy|C|TT
Máy tính|Danh sách + lọc + tìm|Máy tính|Bảng có ô tìm, lọc, đánh dấu trạng thái (online, offline, chưa có báo cáo)|Có máy|C|TT
Máy tính|Thêm máy: IP / dải 192.168.1.10-30 / nhiều IP|Điền ô Thêm máy mới|Thêm đúng, bỏ qua IP đã có; có thể gán tài khoản; lấy MAC từ ARP; tự lấy báo cáo|-|C|TT
Máy tính|Quét mạng thêm máy|Bấm Quét mạng|Chuyển sang trang quét mạng của Triển khai|Mạng|T|TT
Máy tính|Thao tác hàng loạt|Chọn nhiều máy: Lấy thông tin / Gán tài khoản / Thêm-gỡ thẻ / Đặt địa điểm / Bật-Vô hiệu giám sát / Xoá|Làm đúng cho tất cả máy chọn; máy chưa gán tài khoản bị bỏ qua khi báo cáo|Nhiều máy|C|TT
Máy tính|Tự điền MAC và tên máy từ báo cáo|Máy mới (chưa có MAC/tên) bấm Lấy thông tin|Ô MAC và tên máy được điền từ card mạng/hostname; ô đã có (anh sửa tay) KHÔNG bị ghi đè|Máy có agent hoặc tài khoản|C|TT
Máy tính|Nhóm máy: tạo, thêm, gỡ|Chọn nhiều máy > Tạo nhóm mới / Thêm vào nhóm / Gỡ khỏi nhóm|Nhóm hiện ở chip từng máy và bộ lọc Mọi nhóm máy; trùng tên bị từ chối; xoá máy thì tự rời nhóm|Nhiều máy|C|TT
Máy tính|Policy (profile) áp cho nhóm máy|Profiles > chọn Nhóm máy áp dụng > Áp dụng ngay|Chỉ máy trong nhóm (hoặc có thẻ) nhận profile; danh sách profile ghi phạm vi theo nhóm|Máy có agent|C|TH
Máy tính|Triển khai WinGet chọn theo nhóm|Trang Triển khai: bấm Chọn nhóm ...|Tick đúng các máy của nhóm|Nhiều máy|T|TT
Máy tính|Báo cáo tự động mỗi 60 phút|Đợi hoặc bấm Lấy thông tin|Cập nhật phần cứng/OS/phần mềm/bảo mật|Máy có tài khoản hoặc agent|C|TH
Chi tiết máy - tab|Tổng quan, Phần cứng, Hệ điều hành, Ổ đĩa, Màn hình, Card mạng, Máy in, Chia sẻ|Mở từng tab|Hiển thị đúng; Máy in/Màn hình có thêm dữ liệu từ trợ lý phiên (nếu có agent)|Windows|C|TH
Chi tiết máy - tab|Phần mềm + CSV|Tab Phần mềm, Tải CSV|Danh sách đúng + CSV|Windows|C|TH
Chi tiết máy - tab|Cập nhật (Windows Update)|Tab Cập nhật|Trạng thái tự động cập nhật, lần tìm/cài cuối, bản chờ cài (có dự phòng đọc từ registry)|Windows|C|TH
Chi tiết máy - tab|Duyệt file: xem, tải xuống, tải lên, tạo thư mục, xoá|Tab Duyệt file|Thao tác đúng; qua agent không còn giới hạn 25 MB (luồng, 2 GB)|Windows|C|TH
Chi tiết máy - tab|Hỗ trợ từ xa: chạy lệnh PowerShell|Gõ lệnh có tiếng Việt|Kết quả hiện đúng, mật khẩu bị che (***)|Windows|C|TH
Chi tiết máy - tab|Hỗ trợ từ xa: tải file .rdp|Bấm RDP|Tải file .rdp đúng IP|Windows|T|TH
Chi tiết máy - tab|Nguồn điện: tắt / khởi động lại / huỷ|Thử từng nút (huỷ shutdown bằng shutdown /a)|Thực hiện đúng|Windows|C|TH
Chi tiết máy - tab|Xoá máy in|Xoá 1 máy in|Xoá thật trên máy + báo cáo lại|Windows|T|TH
Chi tiết máy - tab|Triển khai / Tác vụ / Nguồn|Mở các tab|Danh sách triển khai theo máy, lịch sử tác vụ (có XSS-safe)|-|C|TT
Chi tiết máy - tab|Ghi chú, Thông tin thêm (metadata), Quản lý|Lưu|Lưu được; gán tài khoản, bật/tắt giám sát, thẻ, địa điểm, xoá máy|-|C|TT
Chi tiết máy - tab|Agent|Mở tab Agent|Trạng thái, phiên bản, báo nhịp, chứng chỉ, nút Cài/Cấp lại chứng chỉ/Gỡ agent, lệnh cài một dòng|Windows|C|TH
Phần mềm (toàn hệ thống)|Danh sách gộp theo phần mềm|Quản lý máy trạm > Phần mềm|Gom theo tên + nhà sản xuất, số phiên bản, số máy; ô tìm; Tải CSV; bấm phần mềm xem máy nào cài|Có báo cáo|C|TT
Bảo mật|Tổng hợp|Bảo mật > Tổng hợp|Diệt virus (tên, CSDL mới/cũ), tường lửa đang bật, BitLocker ổ C, SMB1|Windows|C|TT
Bảo mật|Cập nhật Windows|Bảo mật > Cập nhật Windows|Tự động cập nhật, lần tìm/cài cuối, số bản chờ|Windows|C|TT
Triển khai WinGet|Tìm gói trong danh mục|Gõ tên gói|Tìm theo tên (chưa tìm kiếm không dấu); danh mục tải/cập nhật được|Internet|C|TH
Triển khai WinGet|Cài / Gỡ / Nâng cấp / Nâng cấp tất cả|Chọn gói + nhiều máy, Chạy|Mỗi máy song song <=4; idempotent; lịch sử đợt; tự lấy lại báo cáo sau khi xong|Windows có winget|C|TH
Triển khai WinGet|Tiến độ đợt|Mở trang tiến độ|Từng máy Đang chạy/Đạt/Đã đạt/Lỗi|-|C|TH
Profiles|Tạo/xoá/áp dụng profile|Profiles > Tạo|Gán cho máy/thẻ; áp dụng; "Chạy ngay"|-|C|TT
Profiles|Tác vụ WinGet cài / gỡ|Thêm tác vụ|Chạy đúng, luôn giữ bản mới nhất nếu bật|Windows|C|TH
Profiles|Tác vụ Registry (tạo/xoá khoá, giá trị mặc định, đặt/xoá giá trị, các kiểu dữ liệu)|Thêm từng loại|Áp dụng đúng, idempotent (đặt lại giá trị không báo đổi)|Windows|C|TH
Profiles|Tác vụ Người dùng cục bộ (tạo/cập nhật/xoá) và Nhóm cục bộ (tạo, xoá, thêm/gỡ người dùng)|Thêm từng loại|Đúng; mật khẩu chỉ đi bằng WinRM, không vào bundle agent|Windows|C|TH
Profiles|Tác vụ MSI cài/gỡ + PowerShell|Thêm|Chạy đúng; kiểm toàn vẹn băm; MSI trong kho chạy qua WinRM|Windows|C|TH
Profiles|Đánh dấu "Agent tự áp dụng" / "Cần Console System"|Xem trang profile|Hiển thị đúng loại tác vụ tự trị|-|T|TT
Profiles|Hành động tác vụ (sửa, xoá, lên/xuống...)|Dùng nút|Hoạt động|-|T|TT
Báo cáo|Báo cáo CSV|Quản lý máy trạm > Báo cáo|Tải các CSV (máy, phần mềm...) đủ tiếng Việt|-|C|TT
Quản trị|Máy được giám sát|Quản trị > Máy được giám sát|Bảng máy, trạng thái, tài khoản, báo cáo cuối; Lấy thông tin, Vô hiệu/Bật lại|-|C|TT
Quản trị|Thẻ / Địa điểm / Thông tin thêm|Tạo, sửa, xoá|Dùng được để gán máy|-|C|TT
Quản trị|Cài đặt chung|Đổi cài đặt (chu kỳ báo cáo...)|Lưu và áp dụng|-|T|TT
Quản trị|Nhật ký tác vụ|Xem|Ghi lại tác vụ từng máy (kể cả lệnh PowerShell, thành công/lỗi)|-|C|TT
Quản trị|Trang Agent (xem sheet 13)|-|-|-|C|TT
Chưa hỗ trợ|Danh sách tính năng OpenUEM chưa có|Mở trang|Nêu thật: RustDesk/NetBird, OIDC/2FA, SMTP, đa tổ chức, Linux/macOS|-|T|TT
Điều khiển từ xa VNC|Cài TightVNC|Máy > Hỗ trợ từ xa > Cài|TightVNC 2.8.85 (SHA-256 ghim), dịch vụ thủ công, PIN ngẫu nhiên mã hoá DES mỗi phiên|Windows|C|TH
Điều khiển từ xa VNC|Chế độ trực tiếp (WinRM)|Mở phiên trong trình duyệt (noVNC)|Thấy màn hình; IpAccessControl chỉ IP Console System; Pi khác bị từ chối|Windows WinRM|C|TH
Điều khiển từ xa VNC|Chế độ tunnel qua agent|Máy chỉ có agent, mở phiên|TightVNC chỉ nghe 127.0.0.1, đi ngược qua mTLS, KHÔNG mở cổng 5900|Windows + agent|C|TH
Điều khiển từ xa VNC|Hộp xin phép người đang dùng|Bật "báo người dùng"/"xin phép"|Hiện hộp Có/Không (WTSSendMessage); không có người đăng nhập thì coi là từ chối; hết giờ = từ chối|Windows có người dùng|C|TH
Điều khiển từ xa VNC|Kết thúc phiên|Đóng tab / bấm Kết thúc|Cổng đóng, dịch vụ VNC dừng|Windows|C|TH
Điều khiển từ xa VNC|Gỡ VNC|Bấm Gỡ|Gỡ sạch|Windows|T|TH
An toàn|Quét XSS 40 trang|Đặt tên máy/thẻ/ghi chú chứa <script>, "><img onerror>|Không chạy script ở bất kỳ trang nào; tiêu đề trang cũng thoát ký tự|-|C|TT
"""

S13 = """
Cài đặt agent|Một dòng PowerShell (máy mới chưa có trong danh sách)|Trang Agent > nhập IP/Tạo file cài hoặc tab Agent của máy > Tạo lệnh cài, dán vào PowerShell Administrator|Cài thành dịch vụ ConsoleSystemAgent (LocalSystem), ghim CA, máy hiện trong danh sách|Windows 10/11|C|TH
Cài đặt agent|Cài qua WinRM|Tab Agent của máy > Cài agent qua WinRM|Cài trong ~1 phút, trạng thái đang chạy|WinRM + tài khoản|C|TH
Cài đặt agent|File MSI (tạo trên trang Agent)|Quản lý máy trạm > Quản trị > Agent > Tạo file MSI|Có timeline 6 bước; file lưu để tải; cài msiexec /i ... /qn được; dịch vụ chạy; máy tự ghi danh|Pi có wixl|C|TH
Cài đặt agent|Script .ps1 (tạo trên trang Agent)|Bấm Tạo script, chạy trên máy (tự xin Administrator)|Cài được; compile tại máy; báo ST=DA_LAM|Windows|C|TH
Cài đặt agent|Địa chỉ dự phòng|Tick nhiều địa chỉ (domain + IP LAN) khi tạo file|Cài thử lần lượt; agent tự chuyển địa chỉ khi địa chỉ đầu chết, 10 phút thử quay lại địa chỉ chính|Windows|C|TH
Cài đặt agent|Không hết hạn, không giới hạn máy|Tạo 1 file, ghi danh 10+ máy|Mã không hết hạn, không giới hạn số máy; máy cùng tên+IP không tạo bản ghi thừa|Nhiều máy|C|TT
Cài đặt agent|Xoá file thu hồi mã|Xoá file trong danh sách|Mã ghi danh bị thu hồi (máy chưa cài không dùng được), máy đã cài vẫn chạy|-|C|TT
Cài đặt agent|Đưa MSI vào kho phần mềm|Bấm Đưa vào kho phần mềm|MSI vào Tài nguyên > Phần mềm; dùng tác vụ MSI cài đặt với ProductCode hiển thị|-|T|TT
Cài đặt agent|Máy bật Smart App Control|Cài trên Win11 SAC bật|Bị chặn (CodeIntegrity 3077) - cần ký số hoặc tắt SAC (giới hạn đã biết)|Win11 SAC|C|TH
Kết nối|Domain + cổng mTLS đổi được|Trang Agent > Domain và cổng > Lưu (đổi cổng 8443 sang cổng khác)|nginx ghi lại + kiểm tra + nạp; lỗi tự trả cấu hình cũ; cổng bị chiếm/trùng cổng nội bộ bị từ chối; cảnh báo agent cũ cần cài lại|Pi|C|TH
Kết nối|IP LAN server tự cập nhật|Đổi IP server|Dòng IP LAN tự đổi (5 giây), báo "IP vừa thay đổi"; file cài ghim theo CA nên không hỏng|Pi|T|TH
Kết nối|mTLS hai chiều|Gọi cổng 8443 không có chứng chỉ khách|Agent chỉ tin CA ghim; server chỉ nhận agent có chứng chỉ đã cấp (CN=cs-agent-<id>); chứng chỉ khác bị 403|Pi|C|TT
Kết nối|Qua Internet bằng domain + chuyển cổng|Chuyển TCP 8443 router về server, domain trỏ IP công cộng|Agent ngoài Internet kết nối và nhận việc (chưa kiểm chứng thật)|Router + domain|C|CH
Kết nối|Qua VPN (Tailscale/WireGuard)|Dùng IP trong VPN|Hoạt động không mở cổng|VPN|T|CH
Kết nối|Cloudflare Tunnel không dùng được|Thử qua tunnel|Không hoạt động (proxy cắt TLS) - đã nêu trên giao diện|Cloudflare|L|TH
Kết nối|Server đổi IP / mất chứng chỉ máy chủ|Đổi IP server|Chứng chỉ máy chủ cấp lại; agent vẫn tin vì ghim CA|Pi|T|TH
Passkey|Đặt passkey khi tạo file|Điền passkey 4-64 ký tự|File chỉ chứa dấu băm PBKDF2; không lưu passkey gốc|-|C|TT
Passkey|Cài MSI im lặng thiếu/sai passkey|msiexec /i ... /qn (không PASSKEY / sai)|Thất bại 1603, rollback sạch, log ghi lý do|Windows|C|TH
Passkey|Cài MSI đúng passkey|msiexec /i ... /qn PASSKEY=...|Cài được|Windows|C|TH
Passkey|Cài MSI bấm đúp (có UI)|Bấm đúp file MSI|Hiện hộp thoại nhập passkey (chưa thử)|Windows|C|CH
Passkey|Script có passkey|Chạy .ps1|Hỏi passkey (che), sai thì báo, đúng thì cài|Windows|C|TH
Passkey|Cài lại đè khi máy đã có passkey|Cài file khác passkey|Phải nhập passkey đang dùng của máy|Windows|T|CH
Gỡ cài đặt|uninstall.bat cần Administrator|Chạy uninstall.bat không quyền admin|Báo cần chạy bằng Administrator|Windows|C|TH
Gỡ cài đặt|uninstall.bat + passkey|Chạy bằng admin, nhập sai rồi đúng|Sai báo còn 2 lần; đúng thì gỡ sạch dịch vụ, thư mục, dữ liệu, tác vụ khay, khoá riêng; hộp thoại "Đã gỡ"|Windows|C|TH
Gỡ cài đặt|msiexec /x cần passkey|msiexec /x ... /qn (thiếu/sai/đúng PASSKEY)|Thiếu/sai bị chặn, agent còn nguyên; đúng thì gỡ sạch|Windows|C|TH
Gỡ cài đặt|Gỡ từ xa trên giao diện|Tab Agent > Gỡ agent|Gỡ không cần passkey, sạch (xoá cả khoá riêng trong MachineKeys)|Windows|C|TH
Gỡ cài đặt|Ẩn khỏi Control Panel / Settings|Mở Programs and Features|Không thấy Console System Agent (ARPSYSTEMCOMPONENT=1); vẫn thấy trong Services/Task Manager|Windows|C|TH
Biểu tượng khay|Icon xuất hiện sau đăng nhập|Đăng nhập Windows|Chữ C xanh (nối được) / cam (mất kết nối) hiện thẳng trên taskbar (IsPromoted)|Windows 11|C|TH
Biểu tượng khay|Menu chuột phải|Chuột phải icon|Phiên bản, trạng thái + giờ nhịp, Xem log, Chẩn đoán kết nối..., Đồng bộ ngay|Windows|C|TH
Biểu tượng khay|Xem log|Bấm Xem log|Cửa sổ nhật ký tự làm mới|Windows|C|TH
Biểu tượng khay|Đồng bộ ngay|Bấm Đồng bộ ngay|Huỷ long-poll, nhịp ngay (log "dong bo ngay theo yeu cau nguoi dung"), có thông báo; lấy policy/phần mềm mới|Windows|C|TH
Biểu tượng khay|Chẩn đoán kết nối|Bấm Chẩn đoán kết nối|Bảng Đạt/Cảnh báo/Lỗi: dịch vụ, chứng chỉ máy (hạn), CA, từng server (DNS, TCP, mTLS), đồng hồ lệch, nhịp, profile, đĩa, passkey; nút Quét lại, Chép kết quả|Windows|C|TH
Biểu tượng khay|Chẩn đoán khi bị thu hồi chứng chỉ|Thu hồi chứng chỉ trên Pi|Báo "Server từ chối chứng chỉ của máy" + cách xử lý; khôi phục thì tự nối lại sau ~1 phút|Windows + Pi|T|TH
Biểu tượng khay|Chạy lại sau cập nhật agent|Cập nhật phiên bản agent|Khay tự chạy lại|Windows|T|TH
Việc agent|Chạy PowerShell, tiếng Việt|Chạy lệnh có dấu|Kết quả đúng|Windows|C|TH
Việc agent|Chuyển file dạng luồng 2 GB|Tải 110 MB lên và xuống|SHA khớp cả hai chiều; không còn giới hạn 25 MB|Windows|C|TH
Việc agent|Giao việc|Giao lệnh khi máy online|Tới và chạy trong ~0,3 giây ở LAN|Windows|C|TH
Việc agent|Máy offline|Giao triển khai khi máy tắt|Triển khai tức thời thất bại (hàng đợi lưu trong RAM, mất khi Pi khởi động lại); dùng Profile cho việc cần chờ|Windows|C|TH
Profile tự trị|Agent lưu profile và tự áp dụng|Tắt dịch vụ Console System ~5 phút|Agent vẫn áp dụng lại giá trị registry theo chu kỳ; kết quả gửi bù sau|Windows|C|TH
Profile tự trị|Tác vụ cần mật khẩu|Thêm user có mật khẩu|Chỉ chạy qua WinRM, không vào bundle|Windows|C|TT
Vòng đời|Tự cập nhật|Nâng phiên bản agent trên server|Agent báo phiên bản cũ -> nhận mã nguồn -> tự biên dịch -> thay file -> khởi động lại dịch vụ + khay (đã thử 2.0.0 -> 2.3.2)|Windows|C|TH
Vòng đời|Tự chạy lại khi bị giết|Kill cs-agent|Dịch vụ tự chạy lại sau ~5 giây|Windows|C|TH
Vòng đời|Khởi động cùng Windows (delayed-auto)|Reboot máy|Agent tự chạy|Windows|C|TH
Vòng đời|Gia hạn chứng chỉ|Chứng chỉ còn <60 ngày|Server tự cấp, agent đổi (chấp nhận cả cũ lẫn mới tới khi dùng mới); nút Cấp lại chứng chỉ|Windows|C|TT
Vòng đời|Thu hồi bằng xoá serial|Xoá serial trên server|Agent bị từ chối ngay (403)|Windows|C|TH
Vòng đời|Trợ lý phiên người dùng|Đăng nhập RDP thật|Gửi máy in riêng, màn hình, tên người đăng nhập vào nhịp|Windows có người dùng|T|TH
Vòng đời|Windows 10 / Server 2016+ / domain|Cài trên các hệ điều hành này|Hoạt động (chưa thử, cần .NET Framework 4 để biên dịch tại chỗ)|Win10, Server|C|CH
Vòng đời|Windows 32-bit|Cài MSI trên Windows 32-bit|Chưa hỗ trợ MSI (chỉ x64)|Win 32-bit|L|CH
"""
