# Khoá trang kho bằng Cloudflare Access (vẫn cho Console System cập nhật)

> Tài liệu nội bộ, chỉ dành cho chủ kho. Không đưa lên trang docs công khai.
> Console System - (c) 2026 zTieuYeuz.

## Mục tiêu

- **Con người** (trình duyệt) vào trang kho: phải qua cổng đăng nhập của Cloudflare, và chỉ email của anh mới vào được. Người lạ không thấy được cả trang đăng nhập của kho.
- **Console System** (máy) vẫn lấy dữ liệu và gửi góp ý được như cũ.

Mọi thứ máy gọi lên kho đều nằm dưới đường dẫn **`/api/`**: ghép nối, danh sách, tải file, tham số, góp ý. Vì vậy chỉ cần tách riêng đường `/api/*` ra, cho máy đi qua.

Kho có sẵn một lớp bảo vệ riêng cho `/api/*`:
- ghép nối bằng mã 6 ký tự, sống 15 phút, dùng 1 lần, sai 10 lần thì khoá 10 phút;
- mỗi máy có token riêng, và anh ngắt được ở trang kho;
- góp ý cần khoá riêng và bị giới hạn 20 lần mỗi giờ.

---

## Cách A — khuyên dùng: Bypass cho `/api/*`

Không có bí mật nào phải nhúng vào máy hay ISO. Mọi máy đã bán vẫn chạy tiếp mà không cần build lại.

### Bước 1. Bật đăng nhập bằng mã gửi qua email
1. Vào **dash.cloudflare.com**, chọn **Zero Trust** ở menu trái.
2. Vào **Settings → Authentication**, mục **Login methods**.
3. Kiểm tra đã có **One-time PIN**. Chưa có thì bấm **Add new → One-time PIN → Save**.

### Bước 2. Tạo ứng dụng cho MÁY (đường `/api/*`), làm trước
1. Vào **Access → Applications → Add an application → Self-hosted**.
2. **Application name**: `Kho - API cho Console System`.
3. **Session Duration**: để mặc định.
4. **Application domain**:
   - Subdomain: `kho-console`
   - Domain: `home-server.id.vn`
   - **Path: `api/*`**
5. Bấm **Next** tới phần **Policies → Add a policy**:
   - Policy name: `May Console System`
   - **Action: Bypass**
   - Include: **Everyone**
6. Bấm **Next** rồi **Add application**.

### Bước 3. Tạo ứng dụng cho CON NGƯỜI (cả trang)
1. Vào **Add an application → Self-hosted** lần nữa.
2. **Application name**: `Kho - Quan tri`.
3. **Session Duration**: `24 hours`.
4. **Application domain**: Subdomain `kho-console`, Domain `home-server.id.vn`, **Path để trống**.
5. Policy:
   - Policy name: `Chi chu kho`
   - **Action: Allow**
   - Include: **Emails**, điền email của anh (có thể thêm email dự phòng).
6. Bấm **Add application**.

Cloudflare luôn ưu tiên đường dẫn **cụ thể hơn**. Vì thế `/api/*` theo ứng dụng ở Bước 2 (Bypass), còn mọi trang khác theo Bước 3 (chỉ email của anh).

### Bước 4. Kiểm tra
1. Mở trình duyệt ẩn danh, vào trang kho. Phải thấy trang **Cloudflare Access** hỏi email.
2. Nhập email của anh, lấy mã trong hộp thư và nhập vào. Lúc này mới thấy trang đăng nhập của kho; đăng nhập như cũ.
3. Trên Console System, vào **Deployment OS → Tài nguyên → Tham số cài đặt → 🔄 Cập nhật từ kho**. Phải báo "Đã cập nhật từ kho (… dòng trên kho)".
4. Trên Console System, vào **Deployment OS → Kho trung tâm**. Danh sách phần mềm phải hiện bình thường.
5. Nếu bước 3 hoặc 4 báo lỗi: kiểm tra lại Path ở Bước 2 phải đúng `api/*` (không có dấu `/` ở đầu).

Chụp màn hình từng bước gửi em, em kiểm tra giúp.

---

## Cách B — chặt hơn: Service Token cho `/api/*`

Mỗi request của máy phải kèm một cặp mã (Client ID + Secret). Ai không có cặp mã thì bị Cloudflare chặn ngay từ ngoài, không chạm tới được kho.

**Lưu ý trước khi làm:**
- Cặp mã sẽ nằm trong ISO. Người quyết tâm mổ ISO vẫn lấy được, nhưng vẫn phải qua lớp mã ghép nối và token của kho.
- **Máy đã cài từ ISO cũ (chưa có cặp mã) sẽ mất kết nối kho** ngay khi chuyển sang cách này. Chỉ chuyển khi mọi máy đang dùng đã có cặp mã.
- Service Token có hạn dùng (mặc định 1 năm). Hết hạn phải tạo mới và build lại.

### Các bước
1. Vào **Zero Trust → Access → Service auth → Service Tokens → Create Service Token**. Đặt tên `console-system`, chọn thời hạn.
2. Sao chép **Client ID** và **Client Secret**. Secret chỉ hiện một lần.
3. **Anh tự đặt** cặp mã lên máy. Đừng gửi qua chat:
   - Máy build (để mọi ISO sau có sẵn): SSH vào máy build, tạo file `/root/.config/zt/cf-access.json`, quyền 600:
     ```json
     {"client_id": "xxxx.access", "client_secret": "yyyy"}
     ```
   - Console Pi đang dùng: tạo file `/var/lib/console-pi/cf-access.json` với cùng nội dung, quyền 600.
4. Sửa ứng dụng ở Bước 2 của Cách A: đổi policy từ **Bypass** sang **Service Auth**, Include **Service Token = console-system**.
5. Kiểm tra lại như Bước 4 ở trên, rồi báo em build lại ISO.

---

## Nếu có sự cố

- Console System báo "Không mở được … / HTTP 403": Access đang chặn `/api/*`. Tạm đổi policy ở Bước 2 về **Bypass** là máy chạy lại ngay.
- Anh bị khoá ngoài (mất email): vào dash.cloudflare.com bằng tài khoản Cloudflare, xoá hoặc tắt ứng dụng `Kho - Quan tri`.
- Không cần sửa gì trên máy kho. Kho vẫn giữ lớp đăng nhập riêng (tên + mật khẩu, khoá sau 5 lần sai), nên thành **2 lớp**.
