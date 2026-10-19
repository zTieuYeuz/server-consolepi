# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console System - Trang "Nhat ky" (yeu cau: "phai co he thong log lai ghi
lai tat ca nhung loi, nhieu khi can check thi sao"; 27/09/2026: them tab Log
ghi lai TOAN BO nhat ky cua may, giu 7 ngay).

3 tab:
  1. Loi ung dung  : loi Python KHONG DUOC BAT trong dashboard (errlog.ghi_loi()).
  2. Canh bao dich vu: canh bao/loi journal cua tung dich vu chinh.
  3. Log           : TOAN BO nhat ky he thong (journal) + cac file log rieng
                     cua Console System, loc theo thoi gian / dich vu / muc do
                     / tu khoa, tai ve thanh file .txt.

Thoi gian giu: journald MaxRetentionSec=7day + logrotate "rotate 7" (xem
config/journald-console-pi.conf, config/logrotate-console-pi) - trang nay
chi DOC, khong xoa/sua gi, an toan de xem bat cu luc nao.

AN TOAN: moi tham so tu URL deu duoc so khop voi danh sach cho phep truoc
khi dua vao journalctl (chay bang danh sach doi so, khong qua shell); tu
khoa tim chi loc bang Python, khong bao gio thanh doi so dong lenh.

(c) 2026 zTieuYeuz - Console System
"""
import glob
import gzip
import os
import re
import subprocess
import time
from urllib.parse import urlencode

from flask import Response, request

from .layout import render_page, svg_icon
from .errlog import LOG_FILE, LOG_THAO_TAC, DICH_VU_CAN_THEO_DOI, doc_nhat_ky, doc_journal_dich_vu

# Khoang thoi gian: ma -> (nhan, doi so --since cua journalctl, so giay)
KHOANG = {
    "1h": ("1 giờ qua", "-1h", 3600),
    "6h": ("6 giờ qua", "-6h", 6 * 3600),
    "24h": ("24 giờ qua", "-24h", 86400),
    "7d": ("7 ngày", "-7d", 7 * 86400),
}
# Muc do: ma -> (nhan, doi so -p)
MUC = {
    "tat": ("Tất cả", None),
    "canh": ("Cảnh báo trở lên", "warning"),
    "loi": ("Chỉ lỗi", "err"),
}
SO_DONG_HIEN = 1500          # hien toi da tren trang (Pi yeu, trinh duyet cam ung)
FILE_LOG_MAU = "console-pi-*.log"


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _bo_dau(s):
    import unicodedata
    s = (s or "").replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


def _ds_file_log():
    """Cac file log rieng cua Console System (ten ngan, khong duong dan)."""
    from . import errlog
    return sorted(os.path.basename(p) for p in glob.glob(os.path.join(errlog.THU_MUC_LOG, FILE_LOG_MAU)))


def _dich_vu_co():
    """Dich vu Console System dang co tren may + vai dich vu he thong lien quan."""
    ds = list(DICH_VU_CAN_THEO_DOI)
    try:
        r = subprocess.run(["systemctl", "list-units", "console-pi*", "--all",
                            "--no-legend", "--plain"], capture_output=True, text=True, timeout=5)
        for dong in r.stdout.splitlines():
            ten = dong.split()[0] if dong.split() else ""
            if ten.endswith(".service"):
                ten = ten[:-8]
                if ten not in ds:
                    ds.append(ten)
    except Exception:
        pass
    for ten in ("hostapd", "dnsmasq", "NetworkManager", "ssh", "kernel"):
        if ten not in ds:
            ds.append(ten)
    return ds


def _tham_so():
    """Doc va KIEM tham so tu URL - chi nhan gia tri trong danh sach cho phep."""
    khoang = request.args.get("khoang", "24h")
    if khoang not in KHOANG:
        khoang = "24h"
    muc = request.args.get("muc", "tat")
    if muc not in MUC:
        muc = "tat"
    nguon = request.args.get("nguon", "he-thong")
    dv = request.args.get("dv", "")
    if nguon == "he-thong":
        if dv and dv not in _dich_vu_co():
            dv = ""
    elif nguon not in _ds_file_log():
        nguon, dv = "he-thong", ""
    tim = (request.args.get("tim", "") or "")[:80]
    return khoang, muc, nguon, dv, tim


def _lenh_journal(khoang, muc, dv, so_dong=None):
    lenh = ["journalctl", "--no-pager", "-o", "short-iso", "--since", KHOANG[khoang][1]]
    if MUC[muc][1]:
        lenh += ["-p", MUC[muc][1]]
    if dv == "kernel":
        lenh += ["-k"]
    elif dv:
        lenh += ["-u", dv]
    if so_dong:
        lenh += ["-n", str(so_dong)]
    return lenh


def _doc_file_log(ten, khoang):
    """Doc file log + cac ban da xoay vong (.1, .N.gz) con trong khoang thoi gian."""
    from . import errlog
    return errlog.doc_file_xoay_vong(os.path.join(errlog.THU_MUC_LOG, ten), KHOANG[khoang][2])


def _loc(dong, muc, tim, la_file):
    if la_file and muc != "tat":
        tu = ("error", "loi", "fail", "traceback", "exception") if muc == "loi" else \
             ("error", "loi", "fail", "traceback", "exception", "warn", "canh bao")
        co = _bo_loc(tu)
        dong = [d for d in dong if co(d)]
    if tim:
        co = _bo_loc((tim,))
        dong = [d for d in dong if co(d)]
    return dong


def _bo_loc(cac_tu):
    """
    Ham kiem tra "dong co chua 1 trong cac tu" - khong phan biet hoa thuong, GO KHONG DAU VAN TIM RA
    ("cai dat" khop "Cài đặt"). Duong nhanh (19/10/2026: tim 7 ngay tren Pi mat ~15 giay vi bo dau tung
    dong trong ~185 nghin dong): dong chi gom ky tu ASCII thi KHONG can bo dau, chi so chu thuong;
    chi dong co dau moi chuan hoa. Tu khoa chuan hoa MOT LAN o day, khong tinh lai moi dong.
    """
    ks = [_bo_dau(t) for t in cac_tu]

    def co(d):
        if d.isascii():
            th = d.lower()
            return any(k in th for k in ks)
        bd = _bo_dau(d)
        return any(k in bd for k in ks)
    return co


def _lay_log(khoang, muc, nguon, dv, tim, gioi_han):
    """-> (danh sach dong, loi hoac '')"""
    if nguon != "he-thong":
        return _loc(_doc_file_log(nguon, khoang), muc, tim, True)[-gioi_han:], ""
    try:
        # Co tu khoa: lay rong hon roi loc (journalctl --grep khong co tren moi ban)
        r = subprocess.run(_lenh_journal(khoang, muc, dv, None if tim else gioi_han),
                           capture_output=True, text=True, timeout=40, errors="replace")
    except subprocess.TimeoutExpired:
        return [], "Đọc nhật ký quá lâu - hãy chọn khoảng thời gian ngắn hơn hoặc 1 dịch vụ."
    except Exception as e:
        return [], f"Không đọc được nhật ký: {e}"
    dong = [d for d in r.stdout.splitlines() if not d.startswith("-- ")]
    return _loc(dong, muc, tim, False)[-gioi_han:], ""


def _khoi_log():
    khoang, muc, nguon, dv, tim = _tham_so()
    dong, loi = _lay_log(khoang, muc, nguon, dv, tim, SO_DONG_HIEN)

    def _chon(ten, ds, cur):
        return f'<select name="{ten}" onchange="this.form.submit()">' + "".join(
            f'<option value="{_esc(k)}"{" selected" if k == cur else ""}>{_esc(v)}</option>'
            for k, v in ds) + "</select>"

    ds_nguon = [("he-thong", "Nhật ký hệ thống (journal)")] + \
               [(f, f"File: {f}") for f in _ds_file_log()]
    ds_dv = [("", "Mọi dịch vụ")] + [(d, "Nhân Linux (kernel)" if d == "kernel" else d)
                                     for d in _dich_vu_co()]
    qs = _esc(urlencode({"khoang": khoang, "muc": muc, "nguon": nguon, "dv": dv, "tim": tim}))
    o_dv = ("" if nguon != "he-thong" else
            f'<label>Dịch vụ {_chon("dv", ds_dv, dv)}</label>')
    noi_dung = "\n".join(dong)
    thong_bao = (f'<div class="msg err">{_esc(loi)}</div>' if loi else
                 f'<div class="hint" style="margin:6px 0;">Đang hiện {len(dong)} dòng'
                 f'{" (mới nhất, tối đa " + str(SO_DONG_HIEN) + ")" if len(dong) >= SO_DONG_HIEN else ""}'
                 ' - dòng mới nhất ở dưới cùng. Muốn xem đủ thì bấm "Tải về".</div>')
    return f"""
    <form method="GET" action="/logs" class="card nk-loc">
      <input type="hidden" name="tab" value="log">
      <label>Nguồn {_chon("nguon", ds_nguon, nguon)}</label>
      {o_dv}
      <label>Thời gian {_chon("khoang", [(k, v[0]) for k, v in KHOANG.items()], khoang)}</label>
      <label>Mức độ {_chon("muc", [(k, v[0]) for k, v in MUC.items()], muc)}</label>
      <label class="nk-tim">Tìm <input type="text" name="tim" value="{_esc(tim)}"
             placeholder="gõ không dấu cũng được"></label>
      <button type="submit">{svg_icon("search")} Lọc</button>
      <a class="btn gray" href="/logs/tai?{qs}">{svg_icon("save")} Tải về (.txt)</a>
    </form>
    {thong_bao}
    <div class="card" style="padding:0;overflow:hidden;">
      <pre id="nk-log" style="margin:0;max-height:62vh;overflow:auto;padding:14px;font-size:12.5px;">{_esc(noi_dung) or '(không có dòng nào khớp bộ lọc)'}</pre>
    </div>
    <script>(function(){{var p=document.getElementById('nk-log');if(p)p.scrollTop=p.scrollHeight;}})();</script>
    """


CSS = """
.nk-tab{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px;}
.nk-loc{display:flex;flex-wrap:wrap;gap:10px 14px;align-items:flex-end;padding:12px 14px;}
.nk-loc label{display:flex;flex-direction:column;gap:4px;font-size:13px;color:var(--chu2,#9aa);}
.nk-loc select,.nk-loc input{min-width:150px;}
.nk-loc .nk-tim input{min-width:190px;}
"""


def register_logs(app):
    @app.after_request
    def _ghi_thao_tac(resp):
        from .errlog import ghi_thao_tac_tu_dong
        ghi_thao_tac_tu_dong(request, resp)
        return resp

    @app.route("/logs")
    def logs_page():
        tab = request.args.get("tab", "loi")
        if tab not in ("loi", "dichvu", "log", "thaotac"):
            tab = "loi"

        dv_chon = request.args.get("dv", DICH_VU_CAN_THEO_DOI[0])
        if dv_chon not in DICH_VU_CAN_THEO_DOI:
            dv_chon = DICH_VU_CAN_THEO_DOI[0]

        def _nut(ma, nhan, href):
            return f'<a class="btn {"blue" if tab == ma else "gray"}" href="{href}">{nhan}</a>'

        if tab == "loi":
            noi_dung = f"""
            <div class="msg info">Chỉ ghi lỗi THẬT SỰ của phần mềm (lỗi bất ngờ trong mã nguồn),
              không ghi các lỗi công cụ đã tự báo ngay trên màn hình (ví dụ "không kết nối được").
              Hiện lỗi của <b>7 ngày gần nhất</b> (kể cả các bản log đã xoay vòng), tự động dọn sau 7 ngày.</div>
            <div class="card" style="padding:0;overflow:hidden;">
              <pre style="margin:0;max-height:65vh;overflow:auto;padding:14px;">{_esc(doc_nhat_ky(300)) or '(chưa có lỗi nào được ghi lại - tốt!)'}</pre>
            </div>"""
        elif tab == "thaotac":
            noi_dung = f"""
            <div class="msg info">Dấu vết <b>ai làm gì</b>: đăng nhập thành công / thất bại, tắt hoặc khởi động lại máy,
              bật tắt PXE và các thao tác ghi dữ liệu (xoá kịch bản, xoá hệ điều hành...). Mỗi dòng gồm thời gian,
              <i>người dùng@địa chỉ máy</i> và thao tác. <b>Không bao giờ ghi mật khẩu.</b> Giữ 7 ngày.</div>
            <div class="card" style="padding:0;overflow:hidden;">
              <pre style="margin:0;max-height:65vh;overflow:auto;padding:14px;">{_esc(doc_nhat_ky(300, LOG_THAO_TAC)) or '(chưa có thao tác nào được ghi lại)'}</pre>
            </div>"""
        elif tab == "dichvu":
            # 1 nut cho moi dich vu, bam vao moi tai (khong tai het moi journal luc vao trang)
            nut_dv = "".join(
                f'<a class="btn {"blue" if d == dv_chon else "gray"} small" '
                f'href="/logs?tab=dichvu&dv={d}">{_esc(d)}</a>'
                for d in DICH_VU_CAN_THEO_DOI)
            noi_dung = f"""
            <div class="row" style="margin-bottom:10px;">{nut_dv}</div>
            <div class="card" style="padding:0;overflow:hidden;">
              <pre style="margin:0;max-height:60vh;overflow:auto;padding:14px;">{_esc(doc_journal_dich_vu(dv_chon, 60))}</pre>
            </div>"""
        else:
            noi_dung = _khoi_log()

        body = f"""
        <div class="nk-tab">
          {_nut("loi", "Lỗi ứng dụng", "/logs?tab=loi")}
          {_nut("dichvu", "Cảnh báo dịch vụ", f"/logs?tab=dichvu&dv={dv_chon}")}
          {_nut("thaotac", "Thao tác", "/logs?tab=thaotac")}
          {_nut("log", "Log toàn bộ", "/logs?tab=log")}
          <a class="btn gray" href="{_esc(request.full_path)}">{svg_icon("refresh")} Làm mới</a>
        </div>
        {noi_dung}
        """
        return render_page(body, active="/logs", title="Nhật ký",
                           subtitle="Toàn bộ nhật ký của máy trong 7 ngày gần nhất - không cần nhớ lệnh",
                           extra_css=CSS)

    @app.route("/logs/tai")
    def logs_tai():
        """Tai ve toan bo log theo bo loc (khong gioi han so dong hien)."""
        khoang, muc, nguon, dv, tim = _tham_so()
        dong, loi = _lay_log(khoang, muc, nguon, dv, tim, 10 ** 7)
        dau = (f"# Console System - nhat ky ({nguon}{' / ' + dv if dv else ''}, "
               f"{KHOANG[khoang][0]}, {MUC[muc][0]}{', tim: ' + tim if tim else ''})\n"
               f"# Xuat luc {time.strftime('%Y-%m-%d %H:%M:%S')} tren may {os.uname().nodename}\n")
        ten = f"nhat-ky-{time.strftime('%Y%m%d-%H%M')}.txt"
        return Response(dau + (loi + "\n" if loi else "") + "\n".join(dong) + "\n",
                        mimetype="text/plain; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{ten}"'})

    return app
