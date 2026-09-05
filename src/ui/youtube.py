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

------------------------------------------------------------------------
LOI THAT DA GAP VA DA KIEM CHUNG (khong doan): sau khi bam "Mo YouTube",
o TIM KIEM/BINH LUAN/CHAT tren chinh trang youtube.com khong hien ban phim
ao - vi vkeyboard.js chi chay tren trang CUA CHINH Console Pi, khong the
gan vao mot website khac (youtube.com) duoc.

Da thu tim cach de he thong hien ban phim ao tren MOI ung dung (khong rieng
gi trang cua minh), giong dien thoai that:
  1. Cai thu wvkbd va squeekboard (2 ban phim ao Wayland pho bien nhat cho
     man hinh nhung/kiosk) va chay thang tren phien Wayland dang song cua
     kiosk de xem thuc te co hien duoc khong.
  2. Ca hai deu bao loi NGAY LAP TUC: "layer shell not available" / "No
     layer shell global available" - roi thoat, khong hien gi ca.
  3. Nguyen nhan: bo dieu phoi man hinh (compositor) dang dung cho kiosk
     la `cage` (xem scripts/kiosk-start.sh) - day la loai kiosk toi gian,
     CHI chay dung 1 ung dung toan man hinh va KHONG cai dat giao thuc
     "wlr-layer-shell" ma moi ban phim ao Wayland tieu chuan can de tu ve
     minh len TREN ung dung dang chay. Da xac nhan bang lenh
     `strings $(which cage) | grep layer_shell` - khong co dong nao ca.
  4. Da go 2 goi thu nghiem tren ngay sau khi kiem tra xong (khong dung
     duoc thi khong de lai chiem dung luong vo ich).

=> Ket luan trung thuc: VOI compositor `cage` hien tai, KHONG co ban phim
   ao he thong nao chay duoc chung voi kiosk. Day la gioi han that cua
   kien truc dang dung, khong phai loi code cua tab YouTube. Doi sang mot
   compositor khac co ho tro layer-shell (vi du labwc, sway) co the giai
   quyet duoc VE MAT KY THUAT, nhung do la mot thay doi lon anh huong toi
   toan bo co che khoa kiosk (cage co chu dich CHI cho chay 1 ung dung,
   labwc/sway la trinh quan ly cua so day du hon, be mat rui ro lon hon) -
   KHONG tu y doi khi chua duoc anh Thoai dong y ro rang.

Giai phap thuc te da lam trong luc cho:
  - Them o "Tim va mo ket qua" NGAY TREN TRANG NAY: go tu khoa bang ban
    phim ao CUA CHINH CONSOLE PI (da biet chay tot), bam Tim la mo thang
    trang ket qua that cua YouTube da dien san tu khoa - khong can go gi
    them tren trang YouTube cho truong hop TIM KIEM.
  - Rieng viec go BINH LUAN/CHAT/dang nhap tai khoan tren chinh trang
    YouTube thi hien tai BAT BUOC phai dung ban phim that: cam USB hoac
    ghep noi Bluetooth (tab Bluetooth cua Console Pi da ho tro san thiet
    bi HID nhu ban phim/chuot).
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
            Roi khoi dashboard, mo thang trang YouTube that - xem danh sach
            de xuat, dang nhap tai khoan... nhu tren dien thoai.</p>
          <a class="btn" href="https://www.youtube.com" style="font-size:16px;">
            🌐 Mo trang chu YouTube</a>

          <p style="color:#8b93a1;font-size:13px;margin:16px 0 9px;">
            Muon tim theo tu khoa truoc? Go o day (ban phim ao cua Console Pi
            van hien binh thuong vi day la o nhap cua chinh trang nay) roi
            bam Tim - se mo thang trang ket qua that, khong can go lai:</p>
          <form method="GET" action="https://www.youtube.com/results">
            <input type="text" name="search_query" placeholder="Tim tren YouTube..." required>
            <div class="row" style="margin-top:11px;">
              <button type="submit" style="font-size:16px;">🔎 Tim va mo</button>
            </div>
          </form>

          <div class="msg warn" style="margin-top:16px;">
            <strong>Cach quay lai dashboard:</strong> vuot ngon tay tu SAT MEP
            TRAI man hinh sang phai (giong vuot lui tren dien thoai). Man
            hinh nay khong co nut Back hay thanh dia chi nen phai dung cu chi
            nay - khong co cach nao khac de quay ve.
          </div>
          <div class="msg info" style="margin-top:10px;">
            <strong>Luu y quan trong:</strong> mot khi da o trong trang
            YouTube that, o binh luan/chat/dang nhap tai khoan cua chinh
            YouTube se <strong>khong hien ban phim ao</strong> - da kiem tra
            va xac nhan man hinh cam ung nay khong ho tro ban phim ao chay
            chung voi nhieu ung dung (chi tiet ky thuat: xem <a href="/docs#youtube">
            Tai lieu</a>). Muon go duoc o do thi can cam ban phim that (USB
            hoac Bluetooth, xem tab <a href="/bluetooth">Bluetooth</a>).
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
