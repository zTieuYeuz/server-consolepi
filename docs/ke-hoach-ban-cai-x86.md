# Kế hoạch: đóng Console Pi thành bản cài Linux chạy trên laptop/máy bàn

> Trạng thái: **bản kế hoạch, chưa bắt đầu code**. Viết đêm 19/09/2026 theo
> yêu cầu của anh Thoại (mục 7): *"build nguyên hệ thống này thành 1 file os
> linux để anh em system tải về rồi boot vào usb rồi cài lên laptop hay máy
> bàn đều chạy được"*.

---

## 1. Mục tiêu

Một file `.iso` tải về, ghi ra USB, boot lên là:

1. **Dùng thử được ngay** (chế độ Live, không cài gì) — cắm cáp console vào
   switch là làm việc được luôn.
2. **Cài lên ổ cứng được** nếu muốn dùng lâu dài, có trình cài đặt đồ họa.
3. Sau khi cài xong, mở trình duyệt vào là thấy đúng dashboard Console Pi
   như đang chạy trên Pi hiện nay.

Đối tượng: anh em system/network — không phải dân Linux chuyên sâu. Nên
trình cài đặt phải bấm là xong, không hỏi những câu khó.

---

## 2. Thực trạng đã đo được trên máy (không phải ước lượng)

| Hạng mục | Số liệu thật |
|---|---|
| Chỗ viết cứng tên cổng `eth0` | **103 chỗ / 19 file** |
| Chỗ viết cứng tên cổng `wlan0` | **80 chỗ / 15 file** |
| Lệnh chỉ có trên Pi (`vcgencmd` đo nhiệt) | 9 chỗ |
| Phụ thuộc `/boot/config.txt` (xoay màn hình) | 1 chỗ |
| Máy Pi hiện tại | Debian 13 (trixie), `aarch64` |
| Máy chủ .34 (dự kiến làm máy build) | Debian 12, **x86_64**, 1 vCPU, 2GB RAM, 22GB trống |

**Kết luận quan trọng:** phần khó KHÔNG phải khâu đóng gói ISO (việc đó có
công cụ chuẩn, đi theo đường mòn). Phần khó là **183 chỗ giả định phần cứng
Raspberry Pi**. Nếu bê nguyên code sang máy x86, dashboard vẫn lên nhưng:

- Tab WiFi/AP, Cắm thẳng thiết bị, PXE/Deployment OS **đều hỏng** — vì trên
  máy bàn cổng mạng tên là `enp3s0`, `wlp2s0`… chứ không phải `eth0`/`wlan0`.
- Ô nhiệt độ CPU trống (không có `vcgencmd`).
- Chức năng xoay màn hình vô nghĩa (không có `/boot/config.txt`).

---

## 3. Những khó khăn thật, nói trước để không vỡ mộng giữa chừng

### 3.1 Tên cổng mạng — việc lớn nhất
Linux hiện đại đặt tên cổng theo vị trí phần cứng (`enp3s0`, `wlx00c0ca…`),
mỗi máy một khác. Không thể đoán. Cách xử lý: thêm một lớp *phát hiện cổng*
duy nhất — tự tìm cổng có dây đang cắm, cổng WiFi đầu tiên — và cho phép
người dùng chọn lại trong Cài đặt. Mọi nơi khác gọi qua lớp đó.

### 3.2 WiFi phát sóng (AP) không phải card nào cũng làm được
Pi có chip Broadcom hỗ trợ AP sẵn. Rất nhiều card Intel trên laptop
**không** phát AP ổn định, hoặc không hỗ trợ. Không thể hứa chắc chạy trên
mọi máy. Cách xử lý trung thực: khi cài xong, tự kiểm tra bằng
`iw list | grep -A10 "Supported interface modes"` và **nói rõ** card này có
phát AP được hay không, thay vì để người dùng bấm rồi thất bại khó hiểu.

### 3.3 Máy build yếu
Máy .34 chỉ 1 vCPU / 2GB RAM. Build một ISO Debian live mất khoảng
**40–90 phút mỗi lần**. Chấp nhận được (không build thường xuyên), nhưng
đừng kỳ vọng sửa–build–thử trong vài phút.

### 3.4 Không build ISO x86 trên con Pi được
Pi là `aarch64`. Phải build trên máy x86_64 → dùng máy .34. Đây cũng là lý
do nên tách việc build ra khỏi con Pi hoàn toàn.

### 3.5 Bluetooth PAN, màn hình cảm ứng, nút nguồn
Là tính năng gắn với phần cứng RasPad. Trên máy bàn nên **ẩn đi** thay vì
hiện ra rồi báo lỗi.

---

## 4. Kiến trúc đề xuất

```
Debian 13 (trixie) x86_64
        │
        ├── live-build  ──> console-pi-x.y.z-amd64.iso
        │                    ├── Chế độ Live (chạy thẳng từ USB)
        │                    └── Calamares (trình cài đặt đồ họa)
        │
        └── gói .deb "console-pi-toolkit"  <── chính repo này
                 └── cài vào /opt/console-pi + systemd + nginx
```

**Vì sao chọn `live-build` + `Calamares`:**
- `live-build` là công cụ chính thức của Debian, tạo được ISO vừa Live vừa
  cài được; tài liệu đầy đủ, không phải tự chế.
- `Calamares` là trình cài đặt đồ họa nhiều bản Linux dùng (bấm Next là
  xong), hợp với đối tượng anh em system hơn là màn hình text của
  debian-installer.
- Giữ nền Debian giống hệt Pi hiện tại (Raspberry Pi OS cũng là Debian) →
  **dùng lại được gần như nguyên vẹn** `install.sh`, cấu hình nginx, các
  file systemd. Đây là lý do quan trọng nhất: không phải viết lại từ đầu.

**Vì sao đóng thành gói `.deb`** thay vì chép thư mục: cài/gỡ/nâng cấp bằng
`apt`, khai báo được phụ thuộc, và bản ISO chỉ việc "cài gói này" — một
đường duy nhất cho cả Pi lẫn x86.

---

## 5. Các giai đoạn

### Giai đoạn 0 — Làm code hết phụ thuộc phần cứng Pi *(việc nặng nhất)*
Làm ngay được trên Pi hiện tại, **không cần chờ gì cả**, và làm xong thì
chính con Pi cũng chạy tốt hơn.

1. Thêm `ui/phancung.py`: phát hiện cổng có dây / cổng WiFi, đọc nhiệt độ
   CPU (thử `vcgencmd`, không có thì đọc `/sys/class/thermal`), nhận biết
   đang chạy trên Pi hay máy thường.
2. Thay dần 183 chỗ viết cứng → gọi qua lớp trên. **Làm từng file, test
   từng file**, không sửa hàng loạt một lượt.
3. Cho phép chọn cổng thủ công trong Cài đặt (lưu vào file cấu hình).
4. Ẩn các tab phần cứng RasPad khi không phải Pi.

*Ước lượng: đây là 60–70% tổng công sức của cả mục 7.*

### Giai đoạn 1 — Đóng gói `.deb` + dựng máy build
- Viết `debian/` rules đóng repo này thành `console-pi-toolkit_*.deb`.
- Cài `live-build` trên máy .34, build thử một ISO Debian trắng cho chạy
  được đã (chưa có gì của mình) — để biết đường đi trước.

### Giai đoạn 2 — ISO Live chạy được
- Nhét gói `.deb` vào ISO, bật sẵn dịch vụ, tự mở trình duyệt vào dashboard.
- Tự tạo mật khẩu quản trị **ngẫu nhiên cho từng máy** ngay lần chạy đầu và
  hiện lên màn hình (tuyệt đối không nhúng mật khẩu cố định vào ISO — đây là
  ISO công khai ai cũng tải được).
- Thử boot thật bằng USB trên một máy thật.

### Giai đoạn 3 — Cài lên ổ cứng
- Thêm Calamares, chỉnh bộ câu hỏi cho ngắn gọn.
- Chạy phần thiết lập lần đầu sau khi cài (giống `install.sh` hiện nay).

### Giai đoạn 4 — Tương thích phần cứng
- Kiểm tra card WiFi có phát AP được không, báo rõ ràng.
- Thử trên vài máy khác nhau: laptop Intel, máy bàn, máy ảo.

### Giai đoạn 5 — Phát hành
- Tự động build khi tạo tag Git, đưa ISO lên GitHub Releases kèm SHA256.
- Viết hướng dẫn: ghi USB bằng Rufus/balenaEtcher, boot thế nào.

---

## 6. Những điều cần anh chốt trước khi bắt tay

1. **Có nên làm Giai đoạn 0 trước và làm dần không?** Em đề xuất: có. Nó
   khiến con Pi hiện tại tốt lên ngay (chọn được cổng mạng thay vì ép
   `eth0`), và là phần bắt buộc dù có làm ISO hay không.
2. **Máy build**: dùng luôn máy .34 hay dựng máy ảo riêng mạnh hơn? Máy .34
   dùng được nhưng mỗi lần build khá lâu.
3. **Bản ISO có kèm tính năng Deployment OS (PXE) không?** Nếu có, ISO sẽ
   nặng thêm và cần cân nhắc: một máy lạ cắm vào mạng công ty rồi bật DHCP
   là chuyện nghiêm trọng. Em đề xuất có, nhưng **mặc định tắt** và cảnh báo
   rõ như hiện nay.
4. **Tên bản phát hành** để đặt cho đúng (vd `Console Pi OS` hay tên khác).

---

## 7. Rủi ro lớn nhất

| Rủi ro | Cách giảm |
|---|---|
| Sửa 183 chỗ làm hỏng tính năng đang chạy tốt trên Pi | Làm từng file, test từng file trên chính con Pi thật trước khi qua file kế |
| Card WiFi không phát AP được → mất một mảng tính năng | Kiểm tra và báo thật ngay khi cài, không hứa suông |
| ISO công khai mà nhúng mật khẩu/khoá cố định | Mọi bí mật đều sinh ngẫu nhiên ở lần chạy đầu — đúng nguyên tắc đã áp dụng cho khoá Samba và tài khoản kho |
| Làm giữa chừng rồi bỏ, kẹt ở trạng thái dở dang | Mỗi giai đoạn đều tự đứng được: Giai đoạn 0 xong là Pi đã tốt hơn, dù không làm tiếp |
