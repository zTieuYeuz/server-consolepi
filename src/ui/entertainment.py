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
            Bam la vao thang YouTube that - duyet, tim kiem, dang nhap tai
            khoan nhu tren dien thoai/tablet binh thuong.</p>
          <a class="btn" href="https://www.youtube.com" style="font-size:16px;">
            🌐 Mo YouTube</a>
        </div>

        <div class="card" style="border-left:4px solid #4CAF50;">
          <h3>🎵 Mo TikTok</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 13px;">
            Bam la vao thang TikTok that - luot video, tim kiem, dang nhap
            tai khoan nhu tren dien thoai/tablet binh thuong.</p>
          <a class="btn" href="https://www.tiktok.com" style="font-size:16px;">
            🎵 Mo TikTok</a>
        </div>

        <div class="msg ok">
          <strong>Luon co duong ve:</strong> se thay 1 nut nho
          <strong>"🏠 Console Pi"</strong> noi o goc duoi ben trai man hinh,
          o BAT KY trang nao dang mo - bam vao do la ve thang dashboard nay
          ngay lap tuc, khong can vuot hay go gi ca.
        </div>
        <div class="msg ok">
          <strong>Ban phim ao cung hien duoc</strong> khi cham vao o tim
          kiem/binh luan/chat cua chinh trang dang mo - se thay ban phim
          quen thuoc hien len duoi man hinh giong cac trang khac cua
          Console Pi. Chi tiet ky thuat: xem <a href="/docs#giaitri">Tai lieu</a>.
        </div>"""

        return render_page(
            body, active="/giaitri", title="Giai tri",
            subtitle="Giai lao luc ranh - luon co duong quay ve dashboard")

    return app
