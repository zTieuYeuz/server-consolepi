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
from consolesystem.core import taisan as _taisan
from consolesystem.core.nhatky import bo_qua as _bo_qua
import sys as _sys
_sys.modules["ui.logs"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import glob
import gzip
import os
import re
import subprocess
import time
from urllib.parse import urlencode

from flask import Response, request

from ui.layout import render_page, svg_icon
from ui.errlog import LOG_FILE, LOG_THAO_TAC, DICH_VU_CAN_THEO_DOI, doc_nhat_ky, doc_journal_dich_vu
from consolesystem.core.esc import esc as _esc

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




def _bo_dau(s):
    import unicodedata
    s = (s or "").replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


def _ds_file_log():
    """Cac file log rieng cua Console System (ten ngan, khong duong dan)."""
    from ui import errlog
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
    except Exception as _loi:
        _bo_qua(_loi)
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
    from ui import errlog
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


def _dong_loi_hoac_thao_tac(duong):
    """Doc file log + cac ban xoay vong 7 ngay -> list dong (toi da 6000 dong cuoi)."""
    from ui import errlog
    try:
        return errlog.doc_file_xoay_vong(duong, 7 * 86400)[-6000:]
    except Exception:
        return []


def _dong_canh_bao_dich_vu(dv, so_dong=400):
    try:
        r = subprocess.run(["journalctl", "-u", dv, "-p", "warning", "-n", str(so_dong),
                            "--no-pager", "-o", "short-iso"],
                           capture_output=True, text=True, timeout=15, errors="replace")
        return [d for d in r.stdout.splitlines() if d.strip() and not d.startswith("-- ")]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# GIAO DIEN NHAT KY (lam lai 22/10/2026, anh Thoai: "de nhin, de tim kiem").
# Truoc day: 4 khoi chu tho (<pre>) dai hang nghin dong, khong phan biet loi / canh bao / binh thuong, tim phai
# bam Loc va tai lai trang. Nay MOT bo xem chung cho ca 4 tab:
#   - moi su kien mot hang: gio | muc (cham mau) | nguon (the nho) | noi dung; traceback gap lai thanh "Chi tiet";
#   - dong lap lien tiep gop thanh "x N"; ngay moi co dong ngan cach (Hom nay / Hom qua / ngay);
#   - o tim loc TUC THI khi go (khong dau van khop) va to sang tu khoa; Enter o tab Log toan bo moi tim tren
#     CA 7 NGAY o may chu (trang chi nap 1500 dong moi nhat);
#   - chip Tat ca / Canh bao / Loi, chip thoi gian, moi nhat o tren (dao duoc), xuong dong, tai ve, lam moi.
# Du lieu day xuong bang mot khoi JSON, JS ve bang createElement/textContent (khong chen duoc ma).
# ---------------------------------------------------------------------------
CSS = _taisan.doc("features/logs/logs.CSS.css")

JS = _taisan.doc("features/logs/logs.JS.html")

_MO_TA = {
    "loi": "Chỉ ghi lỗi <b>thật sự</b> của phần mềm (lỗi bất ngờ trong mã nguồn), không ghi các lỗi công cụ đã tự báo ngay trên màn hình. "
           "Hiện lỗi của <b>7 ngày gần nhất</b>, tự dọn sau 7 ngày. Bấm vào một dòng có mũi tên để xem chi tiết.",
    "dichvu": "Cảnh báo và lỗi của từng dịch vụ chính. Chọn dịch vụ ở dưới; chỉ hiện từ mức cảnh báo trở lên để khỏi lẫn các dòng bình thường.",
    "thaotac": "Dấu vết <b>ai làm gì</b>: đăng nhập thành công hoặc thất bại, tắt hay khởi động lại máy, bật tắt PXE, xóa kịch bản, xóa hệ điều hành. "
               "Mỗi dòng có giờ, <i>người dùng@địa chỉ máy</i> và thao tác. <b>Không bao giờ ghi mật khẩu.</b> Giữ 7 ngày.",
    "log": "Toàn bộ nhật ký của máy trong 7 ngày. Gõ vào ô tìm để lọc ngay; nhấn <b>Enter</b> để tìm trong cả khoảng thời gian đã chọn "
           "(trang chỉ nạp 1500 dòng mới nhất).",
}
_RONG = {"loi": "Chưa có lỗi nào được ghi lại. Tốt!", "dichvu": "Dịch vụ này không có cảnh báo hay lỗi nào gần đây.",
         "thaotac": "Chưa có thao tác nào được ghi lại.", "log": "Không có dòng nào khớp bộ lọc."}


def _trang_xem(tab, kind, dong, tim="", tim_may_chu=False, gioi_han=0, khu_chon="", tai_href="", an_form=""):
    import json as _json
    du_lieu = {"kind": kind, "lines": dong, "tim": tim, "tim_may_chu": tim_may_chu, "gioi_han": gioi_han,
               "bay_gio": time.strftime("%Y-%m-%d %H:%M:%S"), "rong": _RONG[tab]}
    nhung = _json.dumps(du_lieu, ensure_ascii=False).replace("</", "<\\/")
    tim_icon = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M11 4a7 7 0 100 14 7 7 0 000-14zM20 20l-4-4"/></svg>'
    chip_khoang = ("" if tab == "log" else
                   '<span class="nk-nhan">Thời gian</span><span class="nk-chip" id="nk-kh">'
                   '<button type="button" class="on" data-v="0">Tất cả</button><button type="button" data-v="3600">1 giờ</button>'
                   '<button type="button" data-v="86400">24 giờ</button></span>')
    form_dau = '<form method="GET" action="/logs" class="nk-o">' if tab == "log" else '<div class="nk-o">'
    form_cuoi = "</form>" if tab == "log" else "</div>"
    an = an_form
    return f"""
    <div class="nk-bar"><div class="nk-bar-in">
      {khu_chon}
      <div class="nk-h">
        {form_dau}{an}{tim_icon}
          <input type="text" id="nk-tim" name="tim" placeholder="Tìm trong nhật ký, gõ không dấu cũng được" autocomplete="off">
          <button type="button" id="nk-xoa" aria-label="Xóa ô tìm">&#10005;</button>
        {form_cuoi}
        <span class="nk-nhan">Mức</span>
        <span class="nk-chip" id="nk-muc"><button type="button" class="on" data-v="">Tất cả</button>
          <button type="button" class="m-canh" data-v="canh">Cảnh báo</button><button type="button" class="m-loi" data-v="loi">Lỗi</button></span>
        {chip_khoang}
      </div>
      <div class="nk-h">
        <button type="button" class="nk-btn on" id="nk-moi">Mới nhất ở trên</button>
        <button type="button" class="nk-btn on" id="nk-dong">Xuống dòng</button>
        <a class="nk-btn" href="{_esc(request.full_path)}">{svg_icon("refresh")} Làm mới</a>
        <a class="nk-btn" href="{_esc(tai_href)}">{svg_icon("save")} Tải về (.txt)</a>
      </div>
      <div class="nk-tt" id="nk-tt"></div>
    </div></div>
    <div class="nk-kv"><div class="nk-ds" id="nk-ds"></div></div>
    <script id="nk-data" type="application/json">{nhung}</script>
    {JS}"""


def _khoi_log():
    khoang, muc, nguon, dv, tim = _tham_so()
    dong, loi = _lay_log(khoang, muc, nguon, dv, tim, SO_DONG_HIEN)

    def _chon(ten, ds, cur, nhan):
        return (f'<label>{nhan}<select name="{ten}" onchange="document.getElementById(\'nk-form-nguon\').submit()">' + "".join(
            f'<option value="{_esc(k)}"{" selected" if k == cur else ""}>{_esc(v)}</option>' for k, v in ds) + "</select></label>")

    ds_nguon = [("he-thong", "Nhật ký hệ thống (journal)")] + [(f, f"File: {f}") for f in _ds_file_log()]
    ds_dv = [("", "Mọi dịch vụ")] + [(d, "Nhân Linux (kernel)" if d == "kernel" else d) for d in _dich_vu_co()]
    qs = urlencode({"tab": "log", "khoang": khoang, "muc": muc, "nguon": nguon, "dv": dv, "tim": tim})
    o_dv = "" if nguon != "he-thong" else _chon("dv", ds_dv, dv, "Dịch vụ")
    khu = (f'<form method="GET" action="/logs" id="nk-form-nguon" class="nk-sel"><input type="hidden" name="tab" value="log">'
           f'<input type="hidden" name="tim" value="{_esc(tim)}">'
           f'{_chon("nguon", ds_nguon, nguon, "Nguồn")}{o_dv}'
           f'{_chon("khoang", [(k, v[0]) for k, v in KHOANG.items()], khoang, "Khoảng thời gian")}'
           f'{_chon("muc", [(k, v[0]) for k, v in MUC.items()], muc, "Mức độ (máy chủ lọc)")}</form>')
    thong_bao = f'<div class="msg err">{_esc(loi)}</div>' if loi else ""
    kind = "journal" if nguon == "he-thong" else "file"
    an = "".join(f'<input type="hidden" name="{k}" value="{_esc(v)}">'
                 for k, v in (("tab", "log"), ("nguon", nguon), ("khoang", khoang), ("muc", muc), ("dv", dv)))
    return thong_bao + _trang_xem("log", kind, dong, tim=tim, tim_may_chu=True, gioi_han=SO_DONG_HIEN,
                                  khu_chon=khu, tai_href="/logs/tai?" + qs, an_form=an)


def register_logs(app):
    @app.after_request
    def _ghi_thao_tac(resp):
        from ui.errlog import ghi_thao_tac_tu_dong
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

        if tab == "loi":
            noi_dung = _trang_xem("loi", "loi", _dong_loi_hoac_thao_tac(LOG_FILE), tai_href="/logs/tai?tab=loi")
        elif tab == "thaotac":
            noi_dung = _trang_xem("thaotac", "thaotac", _dong_loi_hoac_thao_tac(LOG_THAO_TAC), tai_href="/logs/tai?tab=thaotac")
        elif tab == "dichvu":
            nut_dv = "".join(
                f'<a class="nk-btn{" on" if d == dv_chon else ""}" href="/logs?tab=dichvu&dv={d}">{_esc(d)}</a>'
                for d in DICH_VU_CAN_THEO_DOI)
            khu = f'<div class="nk-h"><span class="nk-nhan">Dịch vụ</span>{nut_dv}</div>'
            noi_dung = _trang_xem("dichvu", "journal", _dong_canh_bao_dich_vu(dv_chon), khu_chon=khu,
                                  tai_href=f"/logs/tai?tab=dichvu&dv={dv_chon}")
        else:
            noi_dung = _khoi_log()

        def _tab(ma, nhan, href):
            return f'<a href="{href}"{" class=on" if tab == ma else ""}>{nhan}</a>'

        body = f"""
        <div class="nk">
          <nav class="nk-tab">
            {_tab("loi", "Lỗi ứng dụng", "/logs?tab=loi")}
            {_tab("dichvu", "Cảnh báo dịch vụ", f"/logs?tab=dichvu&dv={dv_chon}")}
            {_tab("thaotac", "Thao tác", "/logs?tab=thaotac")}
            {_tab("log", "Log toàn bộ", "/logs?tab=log")}
          </nav>
          <p class="nk-mota">{_MO_TA[tab]}</p>
          {noi_dung}
        </div>"""
        return render_page(body, active="/logs", title="Nhật ký",
                           subtitle="Toàn bộ nhật ký của máy trong 7 ngày gần nhất, không cần nhớ lệnh",
                           extra_css=CSS)

    @app.route("/logs/tai")
    def logs_tai():
        """Tai ve toan bo log theo bo loc (khong gioi han so dong hien)."""
        tab = request.args.get("tab", "log")
        if tab == "loi":
            dong, tieu = _dong_loi_hoac_thao_tac(LOG_FILE), "loi ung dung"
        elif tab == "thaotac":
            dong, tieu = _dong_loi_hoac_thao_tac(LOG_THAO_TAC), "thao tac"
        elif tab == "dichvu":
            dv = request.args.get("dv", "")
            dv = dv if dv in DICH_VU_CAN_THEO_DOI else DICH_VU_CAN_THEO_DOI[0]
            dong, tieu = _dong_canh_bao_dich_vu(dv, 5000), f"canh bao dich vu {dv}"
        else:
            khoang, muc, nguon, dv, tim = _tham_so()
            dong, loi = _lay_log(khoang, muc, nguon, dv, tim, 10 ** 7)
            tieu = (f"{nguon}{' / ' + dv if dv else ''}, {KHOANG[khoang][0]}, {MUC[muc][0]}"
                    f"{', tim: ' + tim if tim else ''}")
            if loi:
                dong = [loi] + dong
        dau = (f"# Console System - nhat ky ({tieu})\n"
               f"# Xuat luc {time.strftime('%Y-%m-%d %H:%M:%S')} tren may {os.uname().nodename}\n")
        ten = f"nhat-ky-{time.strftime('%Y%m%d-%H%M')}.txt"
        return Response(dau + "\n".join(dong) + "\n", mimetype="text/plain; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{ten}"'})

    return app
