"""
Console Pi - Tab YouTube (giai tri luc ranh, theo yeu cau cua anh Thoai)

Vi sao KHONG nhung thang ca trang youtube.com day du:
Da kiem tra that bang `curl -I https://www.youtube.com` (khong doan) - trang
chinh tra ve header `X-Frame-Options: SAMEORIGIN`, nen trinh duyet se TU CHOI
hien no trong iframe cua trang khac. Rieng duong dan `/embed/<video_id>`
(YouTube lam rieng de nhung vao website khac) KHONG co header nay, nen dung
duoc cai nay.

Vi sao KHONG dung <a href> dieu huong thang sang youtube.com:
Man hinh cam ung gan tren Pi chay Chromium o che do `--kiosk` (xem
scripts/kiosk-start.sh) - KHONG CO thanh dia chi, KHONG CO nut Back, va con
tat luon cu chi vuot lui (`--overscroll-history-navigation=0`). Neu dieu
huong thang sang youtube.com, nguoi dung se bi KET CUNG tren do, khong co
duong nao quay lai dashboard ma phai khoi dong lai kiosk. Vi vay video BAT
BUOC phai o dang iframe NGAY TRONG khung giao dien chung (co san thanh dieu
huong ben trai) - luc nao cung bam sang tab khac duoc.

Gioi han that (khong bia): YouTube khong cho embed tim kiem/duyet day du.
Cach chac chan luon dung la dan thang duong link video (chia se tu dien
thoai). O tim kiem nhanh dung mot kieu embed khong chinh thuc
(`listType=search`) - co the ngung hoat dong bat cu luc nao neu YouTube doi,
da ghi ro tren giao dien de khong ai tuong day la loi cua Console Pi.
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
              khong ra ket qua, hay mo YouTube tren dien thoai, bam
              <strong>Chia se → Sao chep duong dan</strong> roi dan vao o ben tren.</p>"""

        err_html = f'<div class="msg err">{_esc(err)}</div>' if err else ""

        body = f"""
        {err_html}
        <div class="card">
          <h3>Phat video theo duong dan (luon dung)</h3>
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
            subtitle="Giai tri luc ranh - video luon nam trong khung dashboard "
                     "de luc nao cung bam sang tab khac duoc")

    return app
