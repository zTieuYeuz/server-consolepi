"""
Console Pi - THEO DOI TIEN TRINH cai dat tren may dich (thoi gian thuc).

VAN DE THAT PHAI GIAI QUYET: sau khi Windows boot xong, cac phan mem duoc
cai lan luot bang FirstLogonCommands. Nguoi dung dung nhin man hinh may do
KHONG the biet:
  - dang cai toi cai nao trong so 10 cai,
  - cai nao xong, cai nao that bai,
  - hay no dang TREO (da xay ra that voi Office 365: dung im 45 phut ma
    man hinh khong khac gi luc dang chay binh thuong).

Nay may dich BAO NGUOC ve Pi sau moi buoc. Trang /deployos/tiendo hien
bang tich xanh theo thoi gian thuc, nhin la biet ngay dang o dau.

LUU GI: chi giu trong BO NHO + 1 file JSON nho. Day la du lieu tam cua
mot lan cai, khong phai du lieu quy - mat cung khong sao, nhung ghi ra
file de dashboard khoi dong lai giua chung van khong mat bang dang xem.
"""

import json
import os
import threading
import time

from .duongdan import THU_MUC_DU_LIEU

FILE_LUU = os.path.join(THU_MUC_DU_LIEU, "tien-trinh.json")

# So may giu lai trong lich su. Console Pi la thiet bi cam tay dung cho
# tung may mot, khong phai he thong quan ly hang tram may - giu 20 lan cai
# gan nhat la du de doi chieu "hom qua cai may kia co bi loi nay khong".
SO_MAY_GIU = 20

_khoa = threading.Lock()
_du_lieu = {}      # {ten_may: {"cap_nhat": ts, "buoc": [ {...}, ... ]}}
_da_nap = False

TRANG_THAI = {
    "cho": ("Chờ", "#8b93a1"),
    "dang": ("Đang chạy", "#f59e0b"),
    "xong": ("Xong", "#4CAF50"),
    "loi": ("Lỗi", "#ff6b6b"),
    "qua_gio": ("Quá giờ", "#ff6b6b"),
}


def _nap():
    global _du_lieu, _da_nap
    if _da_nap:
        return
    try:
        with open(FILE_LUU, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict):
            _du_lieu = d
    except (OSError, ValueError):
        _du_lieu = {}
    _da_nap = True


def _ghi():
    """Ghi ra file. Loi thi BO QUA - day chi la ban sao du phong, khong
    duoc phep lam hong luong bao tien trinh dang chay."""
    try:
        os.makedirs(THU_MUC_DU_LIEU, exist_ok=True)
        tam = FILE_LUU + ".tmp"
        with open(tam, "w", encoding="utf-8") as f:
            json.dump(_du_lieu, f, ensure_ascii=False)
        os.replace(tam, FILE_LUU)
    except OSError:
        pass


def _don_bot():
    """Giu lai SO_MAY_GIU may moi nhat."""
    if len(_du_lieu) <= SO_MAY_GIU:
        return
    theo_thoi_gian = sorted(_du_lieu.items(),
                            key=lambda kv: kv[1].get("cap_nhat", 0),
                            reverse=True)
    for ten, _v in theo_thoi_gian[SO_MAY_GIU:]:
        _du_lieu.pop(ten, None)


def bat_dau(ten_may, ten_kichban, cac_buoc):
    """
    May dich bao "toi bat dau cai", kem DANH SACH BUOC se chay.

    Biet truoc ca danh sach nen giao dien hien duoc "3/10" ngay tu dau,
    thay vi cac buoc lan luot hien ra khong biet con bao nhieu nua.
    """
    with _khoa:
        _nap()
        _du_lieu[ten_may] = {
            "kichban": ten_kichban,
            "bat_dau": time.time(),
            "cap_nhat": time.time(),
            "buoc": [{"ten": t, "trang_thai": "cho", "giay": 0, "ghi_chu": ""}
                     for t in cac_buoc],
        }
        _don_bot()
        _ghi()
    return True


def cap_nhat(ten_may, chi_so, trang_thai, giay=0, ghi_chu=""):
    """Cap nhat 1 buoc. Tao ban ghi tam neu chua co bat_dau (phong truong
    hop dashboard vua khoi dong lai giua chung lan cai)."""
    with _khoa:
        _nap()
        m = _du_lieu.get(ten_may)
        if not m:
            m = {"kichban": "?", "bat_dau": time.time(), "buoc": []}
            _du_lieu[ten_may] = m
        while len(m["buoc"]) <= chi_so:
            m["buoc"].append({"ten": f"Bước {len(m['buoc']) + 1}",
                              "trang_thai": "cho", "giay": 0, "ghi_chu": ""})
        b = m["buoc"][chi_so]
        if trang_thai in TRANG_THAI:
            b["trang_thai"] = trang_thai
        if giay:
            b["giay"] = giay
        if ghi_chu:
            b["ghi_chu"] = ghi_chu[:200]
        m["cap_nhat"] = time.time()
        _ghi()
    return True


def ket_thuc(ten_may):
    with _khoa:
        _nap()
        if ten_may in _du_lieu:
            _du_lieu[ten_may]["xong_luc"] = time.time()
            _du_lieu[ten_may]["cap_nhat"] = time.time()
            _ghi()
    return True


def danh_sach():
    """Tat ca may, may cap nhat gan nhat len dau."""
    with _khoa:
        _nap()
        ra = []
        for ten, m in _du_lieu.items():
            buoc = m.get("buoc", [])
            ra.append({
                "ten_may": ten,
                "kichban": m.get("kichban", "?"),
                "bat_dau": m.get("bat_dau", 0),
                "cap_nhat": m.get("cap_nhat", 0),
                "xong_luc": m.get("xong_luc"),
                "buoc": buoc,
                "so_xong": sum(1 for b in buoc if b["trang_thai"] == "xong"),
                "so_loi": sum(1 for b in buoc
                              if b["trang_thai"] in ("loi", "qua_gio")),
                "tong": len(buoc),
            })
        ra.sort(key=lambda x: x["cap_nhat"], reverse=True)
        return ra


def xoa(ten_may):
    with _khoa:
        _nap()
        co = _du_lieu.pop(ten_may, None) is not None
        if co:
            _ghi()
        return co


# ============================================================ giao dien + API
def _thoi_gian(ts):
    return time.strftime("%H:%M:%S", time.localtime(ts)) if ts else "?"


def register_tiendo(app):
    from flask import jsonify, request, redirect
    from .layout import render_page
    import html as _h

    def _esc(s):
        return _h.escape(str(s or ""))

    # ---------------------------------------------------------------- API
    # May dich (Windows) POST vao day. KHONG can dang nhap - luc do may do
    # vua cai xong, chua co phien dang nhap nao voi dashboard, va no chi
    # GHI du lieu tien trinh (khong doc duoc gi cua Pi). Xem them danh sach
    # duong mo trong ui/auth.py.
    @app.route("/api/tiendo/batdau", methods=["POST"])
    def api_tiendo_batdau():
        g = request.get_json(silent=True) or {}
        may = str(g.get("may") or "?")[:64]
        bat_dau(may, str(g.get("kichban") or "?")[:120],
                [str(t)[:120] for t in (g.get("buoc") or [])][:60])
        return jsonify({"ok": True})

    @app.route("/api/tiendo/buoc", methods=["POST"])
    def api_tiendo_buoc():
        g = request.get_json(silent=True) or {}
        try:
            chi_so = int(g.get("chi_so", 0))
        except (TypeError, ValueError):
            chi_so = 0
        cap_nhat(str(g.get("may") or "?")[:64], max(0, min(chi_so, 59)),
                 str(g.get("trang_thai") or ""), int(g.get("giay") or 0),
                 str(g.get("ghi_chu") or ""))
        return jsonify({"ok": True})

    @app.route("/api/tiendo/ketthuc", methods=["POST"])
    def api_tiendo_ketthuc():
        g = request.get_json(silent=True) or {}
        ket_thuc(str(g.get("may") or "?")[:64])
        return jsonify({"ok": True})

    @app.route("/api/tiendo/data")
    def api_tiendo_data():
        """Cho trang tu lam moi - tra ve bang da render san."""
        return jsonify({"html": _bang_tat_ca(_esc)})

    # -------------------------------------------------------------- trang
    def _bang_tat_ca(esc):
        ds = danh_sach()
        if not ds:
            return ('<div class="msg warn">Chưa có máy nào báo về. Bảng này tự '
                    'hiện ngay khi máy vừa cài xong Windows và bắt đầu cài phần '
                    'mềm &mdash; không cần làm gì thêm.</div>')
        ra = ""
        for m in ds:
            xong = m["xong_luc"]
            if xong:
                nhan = ('<span style="color:#4CAF50;">đã xong</span>'
                        if not m["so_loi"] else
                        f'<span style="color:#ff6b6b;">xong, {m["so_loi"]} lỗi</span>')
            else:
                nhan = '<span style="color:#f59e0b;">đang chạy...</span>'

            pct = round(m["so_xong"] * 100 / m["tong"]) if m["tong"] else 0
            hang = ""
            for i, b in enumerate(m["buoc"], 1):
                ten_tt, mau = TRANG_THAI.get(b["trang_thai"], ("?", "#8b93a1"))
                if b["trang_thai"] == "xong":
                    bieu = '<span style="color:#4CAF50;font-size:17px;">&#10004;</span>'
                elif b["trang_thai"] == "dang":
                    bieu = '<span style="color:#f59e0b;font-size:17px;">&#9679;</span>'
                elif b["trang_thai"] in ("loi", "qua_gio"):
                    bieu = '<span style="color:#ff6b6b;font-size:17px;">&#10008;</span>'
                else:
                    bieu = '<span style="color:#6b7280;font-size:17px;">&#9675;</span>'
                gio = f'{b["giay"]}s' if b["giay"] else ""
                ghi = (f'<br><small style="color:#ff6b6b;">{esc(b["ghi_chu"])}</small>'
                       if b["ghi_chu"] else "")
                hang += (f'<tr><td style="width:34px;">{bieu}</td>'
                         f'<td>{i}. {esc(b["ten"])}{ghi}</td>'
                         f'<td style="width:90px;color:{mau};">{ten_tt}</td>'
                         f'<td style="width:70px;color:#8b93a1;">{gio}</td></tr>')

            ra += f"""
            <div class="card">
              <h3 style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
                <span>{esc(m["ten_may"])}</span>
                <small style="color:#8b93a1;font-weight:400;font-size:13px;">
                  {esc(m["kichban"])}</small>
                <span style="margin-left:auto;font-size:13.5px;font-weight:400;">
                  {m["so_xong"]}/{m["tong"]} &mdash; {nhan}</span>
              </h3>
              <div style="background:#2c3036;border-radius:5px;height:9px;
                          overflow:hidden;margin-bottom:12px;">
                <div style="width:{pct}%;height:100%;background:#4CAF50;"></div>
              </div>
              <table>{hang}</table>
              <p style="color:#8b93a1;font-size:12.5px;margin:10px 0 0;">
                Bắt đầu {_thoi_gian(m["bat_dau"])} &middot;
                cập nhật {_thoi_gian(m["cap_nhat"])}</p>
              <form method="POST" action="/deployos/tiendo/xoa" style="margin-top:8px;"
                    onsubmit="return confirm('Xoá bản ghi của máy này?');">
                <input type="hidden" name="may" value="{esc(m["ten_may"])}">
                <button type="submit" class="gray small">Xoá bản ghi</button>
              </form>
            </div>"""
        return ra

    @app.route("/deployos/tiendo")
    def deployos_tiendo():
        body = f"""
        <p style="color:#8b93a1;font-size:13.5px;margin:0 0 14px;">
          Máy đang cài tự báo về đây sau mỗi bước. Bảng tự cập nhật, không
          cần bấm làm mới.</p>
        <div id="bang-tiendo">{_bang_tat_ca(_esc)}</div>
        <script>
        (function() {{
          var o = document.getElementById('bang-tiendo');
          function lamMoi() {{
            fetch('/api/tiendo/data', {{cache: 'no-store'}})
              .then(function(r) {{ return r.json(); }})
              .then(function(d) {{ if (d && d.html) o.innerHTML = d.html; }})
              .catch(function() {{}});
          }}
          setInterval(lamMoi, 3000);
          document.addEventListener('visibilitychange', function() {{
            if (!document.hidden) lamMoi();
          }});
        }})();
        </script>"""
        return render_page(body, active="/deployos/tiendo",
                           title="Tiến trình cài đặt",
                           subtitle="Theo dõi máy đang cài theo thời gian thực")

    @app.route("/deployos/tiendo/xoa", methods=["POST"])
    def deployos_tiendo_xoa():
        xoa(request.form.get("may", ""))
        return redirect("/deployos/tiendo")
