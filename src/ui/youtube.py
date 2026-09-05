"""
Console Pi - Tab YouTube (giai tri luc ranh, theo yeu cau cua anh Thoai)

Ban dau lam dang "dan link roi nhung iframe" - anh phan hoi la khong muon
dan link, muon duoc mo thang YouTube that (duyet/tim kiem binh thuong nhu
tren dien thoai). Da doi lai theo huong nay, kem 1 thay doi bat buoc o
kiosk-start.sh de co duong quay ve:

Vi sao KHONG nhung duoc ca trang youtube.com vao iframe de vua duyet vua
giu thanh dieu huong: da kiem tra that bang `curl -I` (khong doan) -
www.youtube.com, m.youtube.com, va trang ket qua tim kiem deu tra ve header
`X-Frame-Options: SAMEORIGIN`, trinh duyet se TU CHOI hien no trong iframe
cua trang khac. Day la gioi han tu phia Google, khong co cach nao vuot qua
tu phia Console Pi (dung nginx lam proxy roi go bo header nay ve mat ky
thuat co the lam duoc, nhung YouTube tai rat nhieu tai nguyen tu cac ten
mien khac (googlevideo.com, ytimg.com, accounts.google.com...) khong di qua
proxy - se vo video/tim kiem that thuong xuyen, khong dang tin cay de dung).

Vi vay nut "Mo YouTube" o duoi DIEU HUONG THANG (khong phai iframe) sang
https://www.youtube.com - day la mo YouTube that, day du, duyet/tim kiem
binh thuong. Cai gia phai tra: roi khoi dashboard, mat thanh dieu huong.

Duong quay ve: man hinh cam ung chay Chromium kiosk toan man hinh (xem
scripts/kiosk-start.sh) - KHONG CO thanh dia chi, KHONG CO nut Back. Da BAT
lai co che "vuot canh man hinh de lui/tien" cua Chromium
(--overscroll-history-navigation=1, truoc day dang tat) danh rieng cho tinh
huong nay - day la duong DUY NHAT de thoat khoi youtube.com quay lai
dashboard ma khong can khoi dong lai kiosk. Da ghi huong dan ngay tren giao
dien vi day khong phai thao tac hien nhien (khong co nut nao hien thi ca).

Van giu them cach "dan link roi phat trong khung" (embed qua /embed/<id>,
KHONG bi chan iframe) - hop khi chi muon nghe 1 bai nhac nen ma khong can
roi dashboard (vi du dang xem Nettools, khong muon mat cho).
"""
import re

from flask import request

from .layout import render_page

_ID_PATTERNS = [
    r"(?:v=|/embed/|/shorts/|youtu\.be/)([A-Za-z0-9_-]{11})",
]


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def extract_video_id(text):
    """Nhan dang ID video (11 ky tu) tu nhieu dang duong dan YouTube hay ID tho."""
    text = (text or "").strip()
    if not text:
        return ""
    for pat in _ID_PATTERNS:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", text):
        return text
    return ""


def register_youtube(app):
    @app.route("/youtube", methods=["GET", "POST"])
    def youtube_page():
        video_id, query, err = "", "", ""

        if request.method == "POST":
            link = request.form.get("link", "")
            query = request.form.get("query", "")
            if link:
                video_id = extract_video_id(link)
                if not video_id:
                    err = ("Khong nhan dang duoc video tu duong dan nay. "
                           "Kiem tra lai da dan dung duong link YouTube chua.")

        player_html = ""
        if video_id:
            player_html = f"""
            <h2>Dang phat</h2>
            <div class="card" style="padding:0;overflow:hidden;">
              <iframe src="https://www.youtube.com/embed/{video_id}"
                      title="YouTube video" frameborder="0"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media;
                             gyroscope; picture-in-picture"
                      allowfullscreen
                      style="display:block;width:100%;aspect-ratio:16/9;border:0;"></iframe>
            </div>"""
        elif query:
            q = query.strip().replace(" ", "+")
            player_html = f"""
            <h2>Ket qua tim kiem</h2>
            <div class="card" style="padding:0;overflow:hidden;">
              <iframe src="https://www.youtube.com/embed?listType=search&list={q}"
                      title="Ket qua tim kiem YouTube" frameborder="0"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media;
                             gyroscope; picture-in-picture"
                      allowfullscreen
                      style="display:block;width:100%;aspect-ratio:16/9;border:0;"></iframe>
            </div>
            <p style="color:#8b93a1;font-size:13px;margin-top:9px;">
              Kieu tim kiem nay khong phai duong chinh thuc cua YouTube - neu
              khong ra ket qua, bam nut "Mo YouTube" o tren de tim kiem that.</p>"""

        err_html = f'<div class="msg err">{_esc(err)}</div>' if err else ""

        body = f"""
        {err_html}
        <div class="card" style="border-left:4px solid #4CAF50;">
          <h3>🌐 Mo YouTube (duyet/tim kiem day du)</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 13px;">
            Roi khoi dashboard, mo thang trang YouTube that - go tim, xem
            danh sach de xuat, dang nhap tai khoan... nhu tren dien thoai.</p>
          <a class="btn" href="https://www.youtube.com" style="font-size:16px;">
            🌐 Mo YouTube</a>
          <div class="msg warn" style="margin-top:14px;">
            <strong>Cach quay lai dashboard:</strong> vuot ngon tay tu SAT MEP
            TRAI man hinh sang phai (giong vuot lui tren dien thoai). Man
            hinh nay khong co nut Back hay thanh dia chi nen phai dung cu chi
            nay - khong co cach nao khac de quay ve.
          </div>
        </div>

        <div class="card">
          <h3>Hoac phat 1 video ngay trong dashboard (khong roi trang)</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
            Hop khi chi muon nghe nhac nen ma van giu nguyen tab dang lam -
            mo YouTube tren dien thoai, bam <strong>Chia se → Sao chep duong
            dan</strong>, roi dan vao day.</p>
          <form method="POST">
            <label>Duong dan hoac ID video</label>
            <input type="text" name="link" placeholder="https://youtu.be/..." required>
            <div class="row" style="margin-top:13px;">
              <button type="submit" class="gray" data-busy="Dang tai...">▶ Phat</button>
            </div>
          </form>
        </div>

        <div class="card">
          <h3>Tim kiem nhanh, xem ngay trong trang (co the khong on dinh)</h3>
          <form method="POST">
            <label>Tu khoa</label>
            <input type="text" name="query" placeholder="vi du: lofi hip hop radio" required>
            <div class="row" style="margin-top:13px;">
              <button type="submit" class="gray" data-busy="Dang tim...">🔍 Tim</button>
            </div>
          </form>
        </div>
        {player_html}"""

        return render_page(
            body, active="/youtube", title="YouTube",
            subtitle="Giai tri luc ranh")

    return app
