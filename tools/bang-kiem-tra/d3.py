# -*- coding: utf-8 -*-
S07 = """
Trình tạo kịch bản|Mở trình tạo 6 bước + nhảy bước|Deployment OS > Kịch bản > Tạo kịch bản mới; bấm ô số bất kỳ|Thanh 1-6; nhảy thẳng tới bước, dữ liệu bước đang mở được giữ|Máy có >=1 bộ Windows|C|TH
Trình tạo kịch bản|Chọn OS (bước 1) + chọn driver gọn|Chọn bộ Windows; xem danh sách gói driver|Mỗi gói một dòng, 10 gói/trang, có ô tìm, tiêu đề "Đã chọn n / tổng"|Có OS + driver|C|TH
Trình tạo kịch bản|Tên máy cố định|Bước 2: Tên cố định KETOAN-01|Máy cài xong tên đúng; chặn tên sai (quá 15 ký tự, dấu, toàn số, bắt đầu/kết thúc bằng -)|Máy khách|C|TT
Trình tạo kịch bản|Tên máy: tiền tố + serial|Cài 2 máy 1 kịch bản|Tên dạng PC-<serial BIOS>, tiền tố <=8 ký tự, dài quá 15 thì giữ đuôi serial; không có serial dùng 6 số cuối MAC|2 máy/VM|C|TT
Trình tạo kịch bản|Tên máy: đối chiếu CSV|Tải CSV mẫu, điền serial,tên; cài máy trong/ngoài danh sách|Máy trong danh sách nhận đúng tên; ngoài danh sách nhận PC+serial; CSV có tên sai/trùng bị từ chối, báo rõ dòng nào sai|VM|C|TT
Trình tạo kịch bản|Tên máy: ngẫu nhiên|Cài nhiều máy|Tên PC-K7Q2M9X không trùng máy đang cài|VM|T|TT
Trình tạo kịch bản|Tên máy: hỏi lúc cài|Cài, WinPE hiện cửa sổ lệnh|Gõ sai thì báo lỗi hỏi lại; gõ đúng + Enter mới cài|VM|C|TH
Trình tạo kịch bản|Thông tin OS|Múi giờ, ngôn ngữ, bàn phím, key Windows, mật khẩu Administrator|Áp đúng; mật khẩu Administrator chỉ bắt buộc khi kịch bản chưa đặt; ô tích giữ tự đăng nhập mãi mãi (kiosk) hoạt động|VM|C|TH
Trình tạo kịch bản|Chọn ổ cài theo đặc điểm|Bước 3: Ổ đang chứa Windows / theo dung lượng / theo tên-model / nhỏ nhất / lớn nhất / theo số ổ|Chọn đúng ổ; USB không bao giờ bị chọn; không đúng 1 ổ khớp thì dừng + báo lý do, KHÔNG xoá gì|VM 2 ổ + USB|C|TH
Trình tạo kịch bản|Chia ổ tự động|Ổ C hết ổ hoặc N GB (>=40 GB), tạo ổ dữ liệu phần còn lại, nhãn từng ổ|Chia đúng, GPT cho UEFI và MBR cho BIOS tự chọn|VM BIOS và UEFI|C|TH
Trình tạo kịch bản|Chia ổ bằng tay + 5 mẫu Windows|Chọn mẫu, thêm/bớt phân vùng|Điền mẫu, chia đúng; ký tự ổ do Windows đặt|VM|T|TH
Trình tạo kịch bản|Dùng ổ N từ kết quả dò|Có kết quả Dò ổ đĩa|Bước 3 hiện kết quả dò kèm nút Dùng ổ N điền sẵn|Đã dò ổ|T|TH
Trình tạo kịch bản|Phần mềm (bước 4)|Tích phần mềm, ứng dụng nhiều file (Office), font|Tất cả cài khi đăng nhập lần đầu; font cài cho mọi tài khoản|VM|C|TH
Trình tạo kịch bản|Tuỳ chọn hệ thống/giao diện (bước 5)|Bật Remote Desktop, cho ping, không ngủ, tắt Fast Startup, .NET 3.5; hiện đuôi tệp, giao diện tối, Num Lock, tắt quảng cáo, taskbar căn trái|Áp cho cả máy/mọi tài khoản (cả tài khoản tạo sau)|VM|C|TH
Trình tạo kịch bản|Gỡ ứng dụng kèm sẵn + lệnh thêm|Tích gỡ ứng dụng rác, thêm lệnh|Gỡ đúng (Store, Máy tính, Paint... luôn giữ); lệnh thêm chạy sau cài|VM|T|TH
Trình tạo kịch bản|Gia nhập domain|Điền domain, OU, tài khoản join (không kèm domain), mật khẩu; cài|Máy tự vào domain; báo cáo mục Gia nhập domain Đạt; DNS qua DHCP có sẵn; tên máy không trùng; gõ CONGTY\\svc-join hay svc-join@congty.local tự cắt|AD DC + VM|C|TH
Trình tạo kịch bản|Cài lại máy trùng tên (Access is denied)|Cài lại cùng tên trong AD|Quyền Join a computer to the domain là đủ; lỗi thì Windows vẫn cài xong ở WORKGROUP và báo cáo hiện Lỗi|AD DC|T|TH
Trình tạo kịch bản|Windows 11 máy không đủ chuẩn|Cài trên VM không TPM / BIOS Legacy|Cài được (bung ảnh trực tiếp); tích "Cho phép nâng cấp Windows 11 trên máy không đủ chuẩn" thì chạy được bộ cài nâng cấp|VM không TPM|C|TH
Trình tạo kịch bản|Tổng kết và lưu (bước 6)|Thiếu thông tin rồi Lưu|Khung đỏ "Chưa lưu được" kèm link sửa ở bước...; đủ thì Lưu; kịch bản tự hiện trên menu PXE|-|C|TH
Trình tạo kịch bản|Sửa / nhân bản / xoá kịch bản|Dùng các nút ở danh sách|Hoạt động đúng; xoá ghi vào Nhật ký Thao tác|-|C|TH
Trình tạo kịch bản|Danh sách dài chia trang 25 mục|Tạo >25 mục|Chia trang đúng ở trình duyệt|-|L|TH
"""

S08 = """
Hệ điều hành|Thêm bộ Windows từ ISO|Tài nguyên > Hệ điều hành > Thêm, đặt tên, tải ISO|Có thanh tiến độ tách; tự tách boot.wim + install.wim; kiểm tra rồi mới xoá ISO; trống >=2 lần dung lượng ISO|ISO Windows|C|TH
Hệ điều hành|Thêm trực tiếp boot.wim + install.wim|Tải hai file|Dùng được|File wim|T|TH
Hệ điều hành|Tải file lớn (>2 GB)|Tải ISO 5 GB|Không lỗi 500/502, có thanh tiến độ (%, MB, tốc độ, thời gian còn lại), chặn khi thiếu chỗ|ISO lớn|C|TH
Phần mềm / Script|Tải phần mềm .exe/.msi + tham số cài im lặng|Tài nguyên > Phần mềm, tải, điền /S, /qn /norestart|Lưu; có gợi ý tham số theo loại bộ cài; phần mềm từ kho có sẵn tham số|exe/msi|C|TH
Phần mềm / Script|Ứng dụng nhiều file|Tải thư mục hoặc .zip (Office) + dòng lệnh cài|Giải nén vào Ứng dụng (nhiều file); cài đúng khi đăng nhập lần đầu|zip|C|TH
Phần mềm / Script|Font chữ: bộ font + tải nhiều file|Tạo bộ font, tải .ttf/.otf/.ttc/.otc/.zip/cả thư mục|Nhận đúng; file hỏng hoặc .woff bị từ chối kèm lý do; chọn ở bước 4 kịch bản|Font|T|TH
Phần mềm / Script|Script .ps1/.cmd/.bat|Tải script|Lưu được, dùng trong kịch bản|-|T|TH
Driver|Gói driver phổ biến tự tải khi có Internet|Mở Tài nguyên > Driver|15 gói NIC/ổ đĩa tự tải (~6 MB, Microsoft Update Catalog, ký Microsoft, kiểm toàn vẹn); 3 gói VirtIO có sẵn trong ISO; nút Tải tất cả gói chưa có|Internet|C|TH
Driver|Đánh dấu nạp vào ảnh boot|Xem trạng thái gói|Gói card mạng/ổ đĩa ghi "Đã có - nạp vào ảnh boot"|-|C|TH
Driver|Gói driver theo dòng máy|Thêm gói "Dell Latitude 5420", Quản lý file tải .cab/.exe SoftPaq/.zip/.7z, ghi "Dùng cho dòng máy"|Giải nén + đếm .inf; máy cài qua PXE đọc hãng/model BIOS và tự nạp gói khớp; Lịch sử ghi gói đã nạp; gợi ý dòng máy từ Lịch sử|Máy Dell/HP/Lenovo hoặc VM giả|C|TH
Driver|Bộ cài .exe không giải nén được|Tải gói SCCM Lenovo|Có hướng dẫn giải nén bằng Windows rồi nén zip tải lên|-|L|TH
Driver|Intel RST/VMD, Realtek, VMware|Cài trên máy bật VMD / VM VMware|Thấy ổ cứng/mạng|Máy thật/VMware|T|TH
WinPE|Thêm WinPE (.wim hoặc .iso) vào menu PXE|Tài nguyên > WinPE, tải, chọn, Đưa vào menu PXE|File .iso tự tách .wim; từ chối file không phải ảnh boot; "Bỏ khỏi menu" không xoá file|WinPE Strelec/Hiren/ADK|C|TH
WinPE|WinPE rút gọn kiểu WDS (không bootmgr/BCD)|Thêm WinPE chỉ có phần thân|Tự lấy bootmgr ký Microsoft từ bộ Windows có sẵn hoặc từ kho trung tâm|WinPE|T|TH
WinPE|Anhdv Boot (công cụ ngoài .wim)|Tải nguyên .iso|Tự lấy WinPE 64-bit, giữ thư mục Apps, WinPE nạp công cụ qua mạng (Pi xử lý ~3 phút), máy khách >=3 GB RAM; bỏ khỏi menu rồi thêm lại không mất công cụ|Anhdv ISO|T|TH
WinPE|Boot WinPE nguyên bản|Menu PXE > 2. Boot WinPE|Boot đúng WinPE, không chèn gì|VM|C|TH
Kho trung tâm|Tự kết nối khi có Internet|Mở Deployment OS > Kho trung tâm|Tự kết nối, hiện danh sách; chưa có mạng thì tự thử lại; thông tin phần cứng gửi kèm đã mã hoá|Internet + kho|C|TH
Kho trung tâm|Kết nối bằng mã 6 ký tự|Quản trị kho tạo mã, nhập địa chỉ + mã|Kết nối được; mã dùng 1 lần trong 15 phút|Kho|T|TH
Kho trung tâm|Lọc loại + tìm không dấu|Lọc Tất cả/Phần mềm/Ứng dụng nhiều file/Script/Hệ điều hành/WinPE/Font chữ|Lọc đúng|Kho|C|TH
Kho trung tâm|Tải về: tiến độ, tự tải tiếp, SHA-256|Bấm Tải về, cắt mạng giữa chừng|Thanh tiến độ + tốc độ + thời gian còn lại; mất mạng tự tải tiếp; xong kiểm SHA-256 (file hỏng bị xoá); dòng hiện "Đã có"|Kho|C|TH
Kho trung tâm|Tải ứng dụng nhiều file (Office 2019)|Bấm Tải về|Tự giải nén vào Ứng dụng nhiều file + điền sẵn lệnh cài; thiếu chỗ báo ngay|Kho 1,8 GB|T|TH
Kho trung tâm|Tải hệ điều hành|Bấm Tải về|Tự tách boot.wim + install.wim, hiện để chọn khi tạo kịch bản|Kho|C|TH
Kho trung tâm|Tải WinPE tự vào menu PXE|Tải WinPE; ô Tên trong menu PXE|Tự vào menu PXE mục 2|Kho|T|TH
Kho trung tâm|Font chữ (50 họ tiếng Việt)|Lọc Font chữ, Tải về|Tạo bộ font cùng tên, giải nén .ttf; tải lại ghi đè không tạo bản trùng|Kho|T|TH
Kho trung tâm|Ngắt kết nối từng máy|Quản trị kho ngắt|Máy bị ngắt khỏi kho|Kho|L|CH
"""

S09 = """
Bật/Tắt PXE|Chế độ 1: Boot OS trực tiếp|Cắm thẳng dây Console System -> máy cần cài, Bật PXE|Tự đặt IP + cấp DHCP; máy khách boot mạng ra menu|Máy cài + dây thẳng|C|TH
Bật/Tắt PXE|Chế độ 2: Qua mạng không có DHCP|Switch riêng, Bật PXE|Cấp DHCP cho mọi máy trên switch|Switch riêng|C|TH
Bật/Tắt PXE|Chế độ 3: Qua mạng có sẵn DHCP (proxyDHCP)|Mạng công ty có router, Bật PXE|Chỉ proxyDHCP (không cấp IP); máy khách ra menu; không tranh DHCP thật|Mạng có DHCP|C|TH
Bật/Tắt PXE|Cảnh báo không cấp DHCP lên mạng người khác|Đọc khung cảnh báo|Có cảnh báo rõ ở 2 chế độ đầu|-|C|TH
Bật/Tắt PXE|Đổi chế độ = Tắt rồi Bật lại|Tắt PXE, Bật chế độ khác|Hoạt động đúng; thông báo flash hiện sau redirect|-|T|TH
Bật/Tắt PXE|Chọn cổng mạng khi có >=2 NIC|Máy 2 cổng dây: khung Cổng mạng dùng cho PXE|Chọn đúng cổng; Tự chọn dùng cổng đang có tín hiệu; muốn đổi khi đang bật phải Tắt PXE trước; địa chỉ lấy đúng cổng của kiểu boot|Máy 2 NIC|C|TH
Bật/Tắt PXE|Khung xanh trạng thái|Sau khi bật|Cho biết PXE đang bật, chế độ nào, menu có bao nhiêu kịch bản|-|T|TH
Menu tại máy khách|Menu 6 mục|Boot mạng (F12)|1 Install Windows >, 2 Boot WinPE >, 3 Do o dia, 4 May moi bao Secure Boot Violation [tat], Khoi dong o cung (mặc định sau 30 giây), Khoi dong lai may|VM|C|TH
Menu tại máy khách|Không bao giờ tự cài lại máy|Không bấm gì|Sau thời gian chờ tự vào ổ cứng|VM|C|TH
Menu tại máy khách|Kịch bản tự hiện trên menu|Lưu kịch bản mới khi PXE bật|Hiện trong 1. Install Windows|VM|C|TH
Menu tại máy khách|Mục WinPE/Dò ổ mờ khi chưa có tài nguyên|Chưa có WinPE hoặc OS|Mục 2/3 hiện mờ|VM|T|TH
Kiểu máy|BIOS / Legacy|Boot mạng VM BIOS|Menu iPXE ra, cài MBR; không dừng "Booting from SAN device 0x80"|VM BIOS|C|TH
Kiểu máy|UEFI|Boot mạng VM UEFI|Menu ra, cài GPT|VM UEFI|C|TH
Kiểu máy|UEFI bật Secure Boot|Boot mạng VM Secure Boot|Qua được bằng bộ nạp ký Microsoft (cả 2011 và 2023), không cần tắt Secure Boot|VM Secure Boot|C|TH
Kiểu máy|Máy chỉ tin chứng chỉ 2023|Chọn mục 4 (đổi [DANG-BAT]) rồi cài|Dùng trình khởi động 2023 trong bộ cài Windows 11 24H2+; máy cũ phải để mục 4 tắt|Máy mới/VM|T|TH
Kiểu máy|Máy Secured-core|Boot trên máy tắt 3rd-party UEFI CA|Có hướng dẫn bật Allow Microsoft 3rd Party UEFI CA hoặc tạm tắt Secure Boot|Máy Secured-core|L|CH
Máy ảo|VMware E1000E/VMXNET3 + LSI SAS/NVMe/PVSCSI|Tạo VM theo khuyến nghị|Cài được; E1000/LSI Parallel không có driver (đã ghi chú)|VMware|C|TH
Máy ảo|KVM/Proxmox virtio|Cài VM virtio|Dùng được sau khi có gói driver VirtIO|KVM|C|TH
Máy ảo|Hyper-V Gen 2|Cài VM Gen 2|Cài được|Hyper-V|T|CH
Bảo mật PXE|File kịch bản chỉ phát cho mạng nội bộ|Yêu cầu từ Internet khi PXE bật|Từ chối|-|C|TH
Secure Boot|Chọn kịch bản không lộ mật khẩu ra ngoài|Kiểm file unattend/kịch bản từ ngoài|Không tải được từ ngoài|-|C|TH
"""

S10 = """
Dò ổ đĩa|Boot mục 3 Do o dia|Menu PXE > 3|WinPE hiện gọn ổ + phân vùng trong 1 màn hình, gửi kết quả về Console System, bấm phím để tắt máy; CHỈ ĐỌC, không xoá/sửa gì|VM nhiều ổ|C|TH
Dò ổ đĩa|Xem kết quả Ổ đĩa đã dò|Kịch bản > Ổ đĩa đã dò|Hãng/model, UEFI/BIOS, MAC, IP, từng ổ (số, model, NVMe/SATA/USB, dung lượng, GPT/MBR, phân vùng); giữ 100 lần dò gần nhất|-|C|TH
Dò ổ đĩa|Cảnh báo|Dò máy RST/VMD, nhiều ổ, có USB, BitLocker|Hiện khung cảnh báo đúng loại và cách xử lý|Máy thật|C|TH
Dò ổ đĩa|Dò gửi được báo cáo (thư mục nobody)|Dò sau khi cập nhật|Báo cáo về được (đã sửa bao_dam_thu_muc)|VM|C|TH
Tiến trình|Trang Đang cài|Cài 2 máy cùng lúc|Mỗi máy 1 khung mặc định thu gọn; mở xem từng bước (xong, đang chạy, thời gian); khung đang mở giữ nguyên khi tự cập nhật|2 VM|C|TH
Tiến trình|Bước treo bị dừng|Làm 1 bước treo|Bước có giới hạn thời gian, bị dừng, máy đi tiếp|VM|T|TH
Tiến trình|Máy khách: bảng tiến trình cài phần mềm|Đăng nhập lần đầu|Cửa sổ "Đang cài đặt phần mềm cho máy này" (không có PowerShell/màn đen), tự đóng khi xong rồi hiện bảng tổng kết|VM|C|TH
Tiến trình|Báo cáo trên máy|Sau khi cài xong|C:\\ConsolePi có BAO-CAO-TONG-KET.txt, bao-cao-day-du.json, tien-trinh.log; trang báo "xong" chỉ sau khi báo cáo ghi ra ổ (tắt máy an toàn)|VM|C|TH
Tiến trình|Bộ cài không tự thoát|Cài phần mềm có bộ cài treo|Tự nhận ra, đi tiếp|VM|T|TH
Lịch sử|Biên bản máy đã cài|Tiến trình > Lịch sử|Hãng, model, dòng máy, serial, MAC, IP, UEFI/BIOS, kịch bản, OS, gói driver, kết quả (bung xong/lỗi bước nào), tên máy; ghi cả máy lỗi giữa chừng|Đã cài vài máy|C|TH
Lịch sử|Tìm, Xuất CSV, xoá chọn|Gõ MAC/serial/model/tên; Xuất CSV; tick xoá|Lọc đúng; CSV mở bằng Excel đủ tiếng Việt; xoá chọn đúng; tối đa 2000 máy|-|C|TH
Lịch sử|Trạng thái|Theo dõi 1 máy|Đang cài (WinPE) -> Đang cấu hình Windows -> Xong / Xong, có bước lỗi / Lỗi khi cài + tên bước|VM|C|TH
Kiểm tra sẵn sàng|Chạy kiểm tra (~5 giây)|Cài đặt > Kiểm tra sẵn sàng|Báo từng mục + cách sửa: dây/tốc độ, DHCP, DHCP/TFTP/Samba/web, menu, chỗ trống/nơi chứa bộ cài, đồng hồ (<5 phút cho domain), từng kịch bản (file thiếu/hỏng, driver xoá, domain không tra được DNS); đỏ = hỏng, vàng = nên sửa|Mạng thật|C|TH
Kiểm tra sẵn sàng|Tình huống lỗi|Cắm dây 100 Mbps / mạng không DHCP / Pi cấp IP trong khi mạng có DHCP / bộ cài trên thẻ SD|Báo đúng cảnh báo tương ứng|Mạng|T|TH
Bật máy từ xa (WoL)|Chọn máy từ Lịch sử / dán danh sách MAC|Cài đặt > Bật máy từ xa; dán từ Excel|Danh sách đúng (MAC + tên)|-|C|TH
Bật máy từ xa (WoL)|Bật các máy đã chọn / Bật tất cả|Máy tắt (WoL bật trong BIOS)|Gói đánh thức gửi 3 lần qua mọi card (UDP 9 và 7, broadcast mạng con, Ethernet 0x0842); máy bật lên|Máy thật bật WoL|C|TH
Bật máy từ xa (WoL)|Máy ở VLAN khác|Nhập broadcast 192.168.20.255|Gói gửi đúng nơi (router phải cho directed broadcast)|Mạng nhiều VLAN|L|CH
Bật máy từ xa (WoL)|Vào thẳng menu cài|Đặt PXE đầu thứ tự boot|Máy được đánh thức vào menu, hết giờ tự vào ổ cứng|Máy thật|T|TH
"""
