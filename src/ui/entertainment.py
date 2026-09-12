"""
Console Pi - Tab Giai tri (YouTube, TikTok...) luc ranh giua gio lam viec

LICH SU (nhieu vong doi, moi vong dua tren phan hoi/that bai that su cua
vong truoc - khong doan):

  1. Ban dau: dan link roi nhung iframe (an toan nhung bat tien, "cam
     tablet ma phai dan link thi vo ly" - dung nhu vay).
  2. Doi sang dieu huong thang sang youtube.com + "vuot canh man hinh de
     lui" lam duong quay ve. THAT BAI THAT SU: bam vao 1 lien ket trong
     YouTube, bi dua sang mot website khac (datbike.vn) roi KET CUNG luon o
     do - vuot canh khong dua ve duoc, phai remote vao chay
     `systemctl restart console-pi-kiosk` moi cuu duoc man hinh.
  3. Giai phap that su dung tin cay duoc: mot tien trinh nen rieng
     (scripts/kiosk-helper.py) dieu khien Chromium tu ben ngoai qua giao
     thuc DevTools cua chinh no de TIEM vao MOI trang duoc tai (bat ke la
     trang nao): (a) mot nut noi "🏠 Console Pi" o goc duoi ben trai - bam
     la ve thang dashboard, va (b) mot ban phim ao HTML/JS thuan - go duoc
     vao chinh o tim kiem/binh luan/chat cua trang that (xem chi tiet ky
     thuat trong scripts/kiosk-helper.py, ke ca loi Trusted Types cua
     YouTube da gap va sua).
  4. Voi luoi an toan nay (nut Home + ban phim ao dung o moi trang), bo
     han cach "dan link/nhung iframe" - khong con can nua vi da dieu huong
     that duoc an toan. Trang nay gio chi con 2 nut: mo thang YouTube va
     TikTok that, khong con lua chon nhung video/tim kiem rieng.

Gioi han that con lai (khong bia):
  - Ban phim ao tiem qua CDP chi chac chan go duoc vao <input>/<textarea>/
    phan tu contenteditable tieu chuan (da kiem chung 3 loai nay tren
    chinh youtube.com that). O nhap dac biet phuc tap hon chua kiem chung
    tung truong hop - neu gap o nao khong go duoc, bao lai de kiem tra.
  - Am thanh phu thuoc cau hinh PipeWire/ngo ra am thanh cua may (xem
    /docs#giaitri) - khong lien quan gi den 2 nut o trang nay.
"""
from .layout import render_page


def register_entertainment(app):
    @app.route("/giaitri")
    def entertainment_page():
        body = """
        <div class="card" style="border-left:4px solid #4CAF50;">
          <h3>🌐 Mo YouTube</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 13px;">
            Bấm là vào thẳng YouTube thật - duyệt, tìm kiếm, đăng nhập tài
            khoản như trên điện thoại/tablet bình thường.</p>
          <a class="btn" href="https://www.youtube.com" style="font-size:16px;">
            🌐 Mo YouTube</a>
        </div>

        <div class="card" style="border-left:4px solid #4CAF50;">
          <h3>🎵 Mo TikTok</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 13px;">
            Bấm là vào thẳng TikTok thật - lướt video, tìm kiếm, đăng nhập
            tai khoản như trên điện thoại/tablet bình thường.</p>
          <a class="btn" href="https://www.tiktok.com" style="font-size:16px;">
            🎵 Mo TikTok</a>
        </div>

        <div class="msg ok">
          <strong>Luôn có đường về:</strong> sẽ thấy 1 nút nhỏ
          <strong>"🏠 Console Pi"</strong> nổi ở góc dưới bên trái màn hình,
          ở BẤT KỲ trang nào đang mở - bấm vào đó là về thẳng dashboard này
          ngay lập tức, không cần vuốt hay gõ gì cả.
        </div>
        <div class="msg ok">
          <strong>Bàn phím ảo cũng hiện được</strong> khi chạm vào ô tìm
          kiếm/bình luận/chat của chính trang đang mở - sẽ thấy bàn phím
          quen thuộc hiện lên dưới màn hình giống các trang khác của
          Console Pi. Chi tiet ky thuat: xem <a href="/docs#giaitri">Tài liệu</a>.
        </div>"""

        return render_page(
            body, active="/giaitri", title="Giải trí",
            subtitle="Giải lao lúc rảnh - luôn có đường quay về dashboard")

    return app
