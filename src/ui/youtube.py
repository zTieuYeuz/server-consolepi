"""
Console Pi - Tab YouTube (giai tri luc ranh, theo yeu cau cua anh Thoai)

LICH SU (de hieu vi sao trang nay CHI nhung video, khong dieu huong thang
sang youtube.com nua - da thu va that bai that su, khong phai doan):

  1. Ban dau lam dang "dan link roi nhung iframe" (an toan, khong roi trang).
  2. Anh Thoai phan hoi muon duoc "mo YouTube luon" - da doi sang dieu huong
     thang (<a href="https://www.youtube.com">) + bat co che vuot canh man
     hinh de lui (Chromium --overscroll-history-navigation) lam duong quay
     ve, vi kiosk khong co thanh dia chi/nut Back.
  3. THAT BAI THAT SU: anh Thoai bam vao 1 lien ket ben trong YouTube, bi
     dua sang mot trang web khac (datbike.vn) roi KET CUNG luon o do - vuot
     canh man hinh khong dua duoc ve dashboard hay YouTube. Phai remote vao
     chay `systemctl restart console-pi-kiosk` de cuu man hinh.
  4. Nguyen nhan that: co che "vuot canh de lui" cua Chromium duoc thiet ke
     chinh cho touchpad/chuot tren Windows/macOS - tren Linux voi man hinh
     cam ung thuan (khong co touchpad), no khong duoc trien khai day du/dang
     tin cay. Tuc la NGAY CA KHI da bat flag, cu chi vuot khong chac chan
     hoat dong - lam nguoi dung bi ket cung That su tren mot website bat ky
     ma khong co duong nao quay lai, phai remote vao sua tu xa.

=> KET LUAN: dieu huong thang ra ngoai youtube.com (hay bat ky trang nao
   khac) tren man hinh kiosk nay la KHONG AN TOAN - da chuyen ve han dang
   NHUNG (embed) trong iframe, KHONG con nut "Mo YouTube" dieu huong that
   nua. Da tat lai co che vuot canh (--overscroll-history-navigation=0
   trong scripts/kiosk-start.sh) vi no khong dang tin cay va tu no cung la
   1 duong roi dashboard ngoai y muon o BAT KY trang nao khac (khong rieng
   YouTube) neu vo tinh vuot trung.

Muon that su "mo YouTube tu do duyet" ma van co duong ve chac chan, cach
duy nhat dang tin cay la lam mot nut "Ve Dashboard" luon noi tren MOI trang
web (bat ke dang o dau) bang cach dieu khien Chromium tu ben ngoai qua
giao thuc DevTools (remote debugging), khong phu thuoc vao chinh trang web
dang mo. Day la mot cong viec rieng, chua lam (can may dai voi anh Thoai
truoc khi lam vi no mo them 1 cong debug tren May, du chi nghe tren
localhost) - hien tai CHUA co, nen KHONG dua vao dieu huong that.

Gioi han that con lai (khong bia): YouTube khong cho embed tim kiem/duyet
day du (da kiem tra `curl -I` - www.youtube.com/m.youtube.com/trang ket
qua deu tra X-Frame-Options: SAMEORIGIN, chan iframe). Cach chac chan luon
dung la dan thang duong link video (chia se tu dien thoai). O tim kiem
nhanh dung mot kieu embed khong chinh thuc (`listType=search`) - co the
ngung hoat dong bat cu luc nao neu YouTube doi, da ghi ro tren giao dien.

Ban phim ao CUA CONSOLE PI chay binh thuong tren cac o nhap CUA CHINH
TRANG NAY (dan link, go tu khoa) - no chi khong the gan vao BEN TRONG
video dang nhung (video load tu youtube.com, mot trang khac).
"""
import re

from flask import request

from .layout import render_page

_ID_PATTERNS = [
    r"(?:v=|/embed/|/shorts/|youtu\.be/)([A-Za-z0-9_-]{11})",
]

# KHONG duoc them allow-top-navigation/allow-popups: day la phong thu 2 lop
# sau bai hoc dieu huong that bai o tren - du chi con dan video/tim kiem
# vao iframe, van chan tuyet doi kha nang mot video/quang cao BEN TRONG
# iframe dieu huong ca trang dashboard di noi khac.
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
              khong ra ket qua, hay dan thang duong link video vao o ben tren.</p>"""

        err_html = f'<div class="msg err">{_esc(err)}</div>' if err else ""

        body = f"""
        {err_html}
        <div class="msg warn">
          <strong>Da bo nut "Mo YouTube" dieu huong thang.</strong> Da thu va
          that bai that su: vuot canh man hinh de quay ve khong dang tin cay
          tren man hinh cam ung nay, co lan bi ket cung tren mot trang web
          khac va phai remote vao sua. Video gio CHI phat trong khung ben
          duoi - khong bao gio roi khoi dashboard, luon an toan.
        </div>

        <div class="card">
          <h3>Phat video theo duong dan</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
            Mo YouTube tren dien thoai, bam <strong>Chia se → Sao chep duong
            dan</strong>, roi dan vao day.</p>
          <form method="POST">
            <label>Duong dan hoac ID video</label>
            <input type="text" name="link" placeholder="https://youtu.be/..." required>
            <div class="row" style="margin-top:13px;">
              <button type="submit" data-busy="Dang tai...">▶ Phat</button>
            </div>
          </form>
        </div>

        <div class="card">
          <h3>Hoac tim kiem nhanh (co the khong on dinh)</h3>
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
            subtitle="Giai tri luc ranh - video luon nam trong khung dashboard, khong bao gio roi trang")

    return app
