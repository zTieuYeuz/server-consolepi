"""
Console Pi - Tab YouTube (giai tri luc ranh, theo yeu cau cua anh Thoai)

LICH SU (3 vong doi, moi vong deu dua tren that bai/phan hoi that su cua
vong truoc - khong doan):

  1. Ban dau: dan link roi nhung iframe (an toan nhung bat tien, "cam tablet
     ma phai dan link thi vo ly" - dung nhu vay).
  2. Doi sang dieu huong thang sang youtube.com + "vuot canh man hinh de
     lui" lam duong quay ve. THAT BAI THAT SU: bam vao 1 lien ket trong
     YouTube, bi dua sang mot website khac (datbike.vn) roi KET CUNG luon o
     do - vuot canh khong dua ve duoc, phai remote vao chay
     `systemctl restart console-pi-kiosk` moi cuu duoc man hinh. Nguyen
     nhan: co che vuot canh cua Chromium chu yeu lam cho touchpad/chuot tren
     Windows/macOS, tren man hinh cam ung Linux khong duoc trien khai day
     du/dang tin cay.
  3. Da rut lai ve dang nhung o vong 2, nhung anh Thoai phan hoi dung: dung
     tablet thi phai bam la vao thang duoc, khong the bat dan link.

=> GIAI PHAP CUOI CUNG (da kiem chung that bang script test rieng, dieu
   huong qua nhieu trang cuc bo khac nhau va xac nhan ket qua "FOUND" moi
   lan, khong doan): thay vi dua vao mot cu chi khong dang tin cay, mot
   tien trinh nen rieng (scripts/kiosk-helper.py) dieu khien Chromium tu
   ben ngoai qua giao thuc DevTools cua chinh no
   (--remote-debugging-port=9222 trong kiosk-start.sh, CHI nghe tren
   127.0.0.1 - da xac nhan bang `ss -tlnp` khong lo ra mang ngoai) de TIEM
   vao MOI trang duoc tai (bat ke la trang nao - YouTube, hay ngay ca
   datbike.vn neu lo bam trung lan nua):
     1. Mot nut "🏠 Console Pi" luon noi co dinh - bam vao la ve thang
        dashboard.
     2. Mot ban phim ao HTML/JS thuan (khong phai ban phim ao he thong) -
        xem muc rieng ben duoi.
   Xem chi tiet ky thuat day du trong scripts/kiosk-helper.py.

   Vi nut Ve Dashboard hoat dong o TAT CA moi trang (khong phu thuoc
   website nao), nut "🌐 Mo YouTube" dieu huong thang duoc dua tro lai an
   toan - lan nay duong quay ve khong con phu thuoc vao 1 cu chi rieng cua
   trang YouTube nua ma la mot co che chung, doc lap voi noi dung dang mo.

Ve ban phim ao tren YouTube that (da tung ket luan "khong lam duoc" - KET
LUAN DO CHUA DUNG, da sua):
  Ket luan truoc: vkeyboard.js (dashboard) chi chay duoc tren trang cua
  chinh no, va ban phim ao he thong (wvkbd/squeekboard) khong chay duoc vi
  compositor kiosk (`cage`) thieu giao thuc "layer-shell". CA HAI DIEU NAY
  DEU DUNG - nhung tu do ket luan "khong the co ban phim ao tren trang
  khac" la SAI. Mot khi da co CDP de tiem nut Ve Dashboard, CUNG dung
  duoc chinh co che do de tiem mot ban phim ao HTML/JS THUAN vao ben trong
  YouTube - khong can layer-shell hay quyen he thong nao ca, vi no chi la
  DOM/script binh thuong chay trong chinh trang do. Da kiem chung that
  (khong doan): tiem vao 1 trang test co input/textarea/contenteditable,
  go chu, xoa, bam Enter deu hoat dong dung, gia lap y het kieu du lieu
  cua o tim kiem/binh luan/chat that.

Gioi han that con lai (khong bia):
  - YouTube khong cho embed tim kiem/duyet day du trong iframe (da kiem tra
    `curl -I` - X-Frame-Options: SAMEORIGIN). Nut "Mo YouTube" giai quyet
    dung cho truong hop nay vi no KHONG dung iframe, dieu huong that.
  - Ban phim ao tiem qua CDP chi chac chan go duoc vao <input>/<textarea>/
    phan tu contenteditable tieu chuan (da kiem chung 3 loai nay). O nhap
    dac biet phuc tap hon (vd trinh soan thao rich-text nhieu lop long
    nhau) chua kiem chung tung truong hop - neu gap o nao khong go duoc,
    bao lai de kiem tra rieng.
"""
import re

from flask import request

from .layout import render_page

_ID_PATTERNS = [
    r"(?:v=|/embed/|/shorts/|youtu\.be/)([A-Za-z0-9_-]{11})",
]

# KHONG duoc them allow-top-navigation/allow-popups: phong thu 2 lop cho
# video/tim kiem nhung - du nut Home da xu ly duoc truong hop dieu huong
# that (nut "Mo YouTube"), van khong de video/quang cao BEN TRONG iframe tu
# y dieu huong ca trang dashboard di noi khac.
_IFRAME_SANDBOX = "allow-scripts allow-same-origin allow-presentation"


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
                      sandbox="{_IFRAME_SANDBOX}"
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
                      sandbox="{_IFRAME_SANDBOX}"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media;
                             gyroscope; picture-in-picture"
                      allowfullscreen
                      style="display:block;width:100%;aspect-ratio:16/9;border:0;"></iframe>
            </div>
            <p style="color:#8b93a1;font-size:13px;margin-top:9px;">
              Kieu tim kiem nay khong phai duong chinh thuc cua YouTube - neu
              khong ra ket qua, hay bam nut "Mo YouTube" o tren de tim that.</p>"""

        err_html = f'<div class="msg err">{_esc(err)}</div>' if err else ""

        body = f"""
        {err_html}
        <div class="card" style="border-left:4px solid #4CAF50;">
          <h3>🌐 Mo YouTube (duyet/tim kiem day du)</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 13px;">
            Bam la vao thang YouTube that - duyet, tim kiem, dang nhap tai
            khoan nhu tren dien thoai/tablet binh thuong.</p>
          <a class="btn" href="https://www.youtube.com" style="font-size:16px;">
            🌐 Mo YouTube</a>
          <div class="msg ok" style="margin-top:14px;">
            <strong>Luon co duong ve:</strong> se thay 1 nut nho
            <strong>"🏠 Console Pi"</strong> noi o goc tren ben trai man
            hinh, o BAT KY trang nao dang mo - bam vao do la ve thang
            dashboard nay ngay lap tuc, khong can vuot hay go gi ca.
          </div>
          <div class="msg ok" style="margin-top:10px;">
            <strong>Ban phim ao cung hien duoc luon</strong> khi cham vao o
            tim kiem/binh luan/chat cua chinh trang YouTube - se thay ban
            phim quen thuoc hien len duoi man hinh giong cac trang khac
            cua Console Pi. Chi tiet ky thuat: xem
            <a href="/docs#youtube">Tai lieu</a>.
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
