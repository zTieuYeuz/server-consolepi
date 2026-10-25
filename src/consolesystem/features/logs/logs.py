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
CSS = """
.nk { display:flex; flex-direction:column; gap:14px; }
.nk-tab { display:inline-flex; gap:4px; padding:4px; border:1px solid var(--vien); background:var(--the); border-radius:12px;
          flex-wrap:wrap; align-self:flex-start; }
.nk-tab a { padding:0 16px; height:40px; line-height:40px; border-radius:9px; color:var(--chu-mo); font-weight:550; font-size:14.5px;
            white-space:nowrap; transition:background .35s var(--muot), color .35s var(--muot); }
.nk-tab a:hover { color:var(--chu); background:var(--hang-nen); }
.nk-tab a.on { background:var(--nhan-mo); color:var(--nhan); }
.nk-mota { color:var(--chu-mo); font-size:14px; line-height:1.55; margin:0; max-width:900px; }
.nk-mota b { color:var(--chu); font-weight:600; }
.nk-bar { background:var(--the-noi); border:1px solid var(--vien); border-radius:var(--bo); padding:6px; }
.nk-bar-in { background:var(--the); border-radius:calc(var(--bo) - 6px); padding:14px; display:flex; flex-direction:column; gap:12px; }
.nk-h { display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
.nk-o { position:relative; flex:1 1 280px; min-width:200px; }
.nk-o svg { position:absolute; left:12px; top:50%; width:18px; height:18px; transform:translateY(-50%); stroke:var(--chu-mo2); fill:none;
            stroke-width:1.7; stroke-linecap:round; stroke-linejoin:round; pointer-events:none; }
.nk-o input { width:100%; max-width:none; margin:0; height:44px; padding-left:38px; padding-right:40px; }
.nk-o button { position:absolute; right:6px; top:50%; transform:translateY(-50%); width:32px; height:32px; min-height:32px; padding:0; border:0;
               background:transparent; color:var(--chu-mo); border-radius:8px; cursor:pointer; display:none; }
.nk-o button:hover { background:var(--hang-nen); color:var(--chu); }
.nk-chip { display:inline-flex; gap:4px; }
.nk-chip button, .nk-btn { height:36px; min-height:36px; padding:0 13px; border-radius:99px; border:1px solid var(--vien-ro); background:transparent;
                           color:var(--chu-mo); font:550 13.5px var(--chu-font); cursor:pointer; display:inline-flex; align-items:center; gap:6px;
                           text-decoration:none; transition:background .3s var(--muot), color .3s var(--muot), border-color .3s var(--muot); }
.nk-chip button:hover, .nk-btn:hover { color:var(--chu); border-color:var(--chu-mo2); }
.nk-chip button.on, .nk-btn.on { background:var(--nhan-mo); color:var(--nhan); border-color:var(--nhan); }
.nk-chip button.m-loi.on { background:var(--do-mo); color:var(--do); border-color:var(--do); }
.nk-chip button.m-canh.on { background:var(--vang-mo); color:var(--vang); border-color:var(--vang); }
.nk-btn svg { width:16px; height:16px; stroke:currentColor; fill:none; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }
.nk-nhan { color:var(--chu-mo2); font-size:12.5px; font-weight:600; letter-spacing:.04em; text-transform:uppercase; margin-right:2px; }
.nk-sel { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
.nk-sel label { display:flex; flex-direction:column; gap:3px; font-size:12px; color:var(--chu-mo2); font-weight:600; }
.nk-sel select { min-width:150px; height:40px; margin:0; }
.nk-tt { display:flex; gap:14px; flex-wrap:wrap; align-items:center; color:var(--chu-mo); font-size:13px; }
.nk-tt b { color:var(--chu); font-weight:600; }
.nk-tt .l { color:var(--do); } .nk-tt .c { color:var(--vang); }
.nk-kv { background:var(--the-noi); border:1px solid var(--vien); border-radius:var(--bo); padding:6px; }
.nk-ds { background:var(--the); border-radius:calc(var(--bo) - 6px); overflow:auto; max-height:68vh; scrollbar-width:thin; }
.nk-ngay { position:sticky; top:0; z-index:2; padding:8px 16px; background:var(--the-noi); color:var(--chu-mo); font-size:12.5px; font-weight:600;
           letter-spacing:.03em; border-bottom:1px solid var(--vien); }
.nk-h2 { display:grid; grid-template-columns:78px 8px minmax(0,auto) minmax(0,1fr); gap:0 12px; align-items:baseline; padding:9px 16px;
         border-bottom:1px solid var(--vien); font-size:13.5px; line-height:1.55; }
.nk-h2:hover { background:var(--hang-hover); }
.nk-h2.co-ct { cursor:pointer; }
.nk-h2.loi { background:var(--do-mo); } .nk-h2.canh { background:var(--vang-mo); }
.nk-gio { font:12.5px var(--mono); color:var(--chu-mo2); white-space:nowrap; }
.nk-cham { width:8px; height:8px; border-radius:50%; background:var(--vien-ro); align-self:center; }
.nk-h2.loi .nk-cham { background:var(--do); } .nk-h2.canh .nk-cham { background:var(--vang); }
.nk-ng { background:var(--hang-nen); border:1px solid var(--vien); color:var(--chu-mo); border-radius:6px; padding:0 8px; font:500 12px var(--mono);
         max-width:220px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; justify-self:start; }
.nk-nd { min-width:0; overflow-wrap:anywhere; white-space:pre-wrap; font-family:var(--mono); font-size:13px; color:var(--chu); }
.nk-wrap-off .nk-nd { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.nk-nd mark { background:var(--vang-mo); color:var(--vang); border-radius:3px; padding:0 1px; outline:1px solid var(--vang); }
.nk-x { margin-left:8px; background:var(--nhan-mo); color:var(--nhan); border-radius:99px; padding:0 8px; font:600 11.5px var(--chu-font); }
.nk-ct { grid-column:1 / -1; margin:8px 0 2px 98px; padding:12px 14px; background:var(--pre-nen); color:var(--pre-chu); border:1px solid var(--vien);
         border-radius:10px; font:12.5px/1.6 var(--mono); white-space:pre; overflow:auto; max-height:320px; }
.nk-mui { color:var(--chu-mo2); font-size:12px; margin-left:8px; }
.nk-rong { padding:48px 20px; text-align:center; color:var(--chu-mo); font-size:14.5px; }
.nk-them { display:block; width:100%; height:48px; border:0; border-top:1px solid var(--vien); background:transparent; color:var(--nhan); font:600 14px var(--chu-font); cursor:pointer; }
.nk-them:hover { background:var(--nhan-mo); }
@media (max-width:760px) {
  .nk-h2 { grid-template-columns:62px 8px minmax(0,1fr); }
  .nk-h2 .nk-ng { grid-column:3; margin-bottom:2px; }
  .nk-h2 .nk-nd { grid-column:1 / -1; }
  .nk-ct { margin-left:0; }
}
"""

JS = """
<script>
(function () {
  "use strict";
  var D = JSON.parse(document.getElementById("nk-data").textContent);
  var NS = "http://www.w3.org/2000/svg";
  var q = "", muc = "", khoang = "", moiTruoc = true, xuongDong = true, hienToiDa = 300;
  var $ = function (id) { return document.getElementById(id); };
  function el(t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; }
  function bo(s) { return (s || "").toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").replace(/đ/g, "d"); }
  var RE_LOI = /(\\berror\\b|\\bcritical\\b|\\bfatal\\b|traceback|exception|\\bfailed\\b|failure|lỗi|\\bloi\\b|denied|refused|segfault|panic|không thể|khong the)/i;
  var RE_CANH = /(\\bwarn(ing)?\\b|cảnh báo|canh bao|timeout|timed out|deprecated|\\bretry\\b|thất bại|that bai|unreachable)/i;

  // ---- phan tich dong log thanh su kien ------------------------------------------------
  var R_LOI = /^(\\d{4}-\\d\\d-\\d\\d) (\\d\\d:\\d\\d:\\d\\d) \\| (?:\\[([^\\]]*)\\] )?(.*)$/;
  var R_TT = /^(\\d{4}-\\d\\d-\\d\\d) (\\d\\d:\\d\\d:\\d\\d) \\| ([^|]*?) \\| (.*)$/;
  var R_JR = /^(\\d{4}-\\d\\d-\\d\\d)T(\\d\\d:\\d\\d:\\d\\d)\\S*\\s+(\\S+)\\s+([^\\s:\\[]+)(?:\\[\\d+\\])?:\\s?(.*)$/;
  function phanTich() {
    var ds = [], cur = null;
    D.lines.forEach(function (ln) {
      if (!ln.trim() && !cur) return;
      var m = null, e = null;
      if (D.kind === "thaotac" && (m = R_TT.exec(ln))) e = { ngay: m[1], gio: m[2], ng: m[3].trim(), msg: m[4] };
      else if (D.kind === "loi" && (m = R_LOI.exec(ln))) e = { ngay: m[1], gio: m[2], ng: m[3] || "", msg: m[4] };
      else if ((D.kind === "journal" || D.kind === "file") && (m = R_JR.exec(ln))) e = { ngay: m[1], gio: m[2], ng: m[4], msg: m[5] };
      else if (D.kind === "file" && (m = R_LOI.exec(ln))) e = { ngay: m[1], gio: m[2], ng: m[3] || "", msg: m[4] };
      if (e) { e.ct = []; e.lap = 1; ds.push(e); cur = e; }
      else if (cur) cur.ct.push(ln);
      else { cur = { ngay: "", gio: "", ng: "", msg: ln, ct: [], lap: 1 }; ds.push(cur); }
    });
    ds.forEach(function (e) {
      var tc = e.msg + " " + (e.ct[0] || "");
      e.muc = D.kind === "loi" ? "loi" : RE_LOI.test(tc) ? "loi" : RE_CANH.test(tc) ? "canh" : "";
      if (D.kind === "thaotac" && /thất bại|that bai|failed/i.test(e.msg)) e.muc = "canh";
      if (D.kind === "thaotac") {            // tên thao tác dễ đọc; giữ nguyên bản gốc để tìm và để rê chuột xem
        var mm = /^POST (\\S+)/.exec(e.msg), vn = null;
        if (mm) NHAN_TT.forEach(function (x) { if (!vn && mm[1].indexOf(x[0]) === 0) vn = x[1]; });
        if (vn) { e.goc = e.msg; e.msg = vn + e.msg.slice(mm[0].length); }
      }
      e.tim = bo([e.ng, e.msg, e.goc || "", e.ct.join(" ")].join(" "));
      e.ts = e.ngay ? new Date(e.ngay + "T" + e.gio).getTime() : 0;
    });
    // gop cac su kien giong het nhau ngay sau nhau (khong co chi tiet)
    var gop = [];
    ds.forEach(function (e) {
      var l = gop[gop.length - 1];
      if (l && !e.ct.length && !l.ct.length && l.ng === e.ng && l.msg === e.msg && l.ngay === e.ngay) { l.lap++; l.gio2 = e.gio; }
      else gop.push(e);
    });
    return gop;
  }
  var NHAN_TT = [["/commands/add", "Thêm tập lệnh"], ["/commands/update", "Sửa tập lệnh"], ["/commands/delete", "Xóa tập lệnh"],
    ["/commands/send", "Gửi tập lệnh vào terminal"], ["/deployos/kichban/xoa", "Xóa kịch bản"], ["/deployos/kichban/luu", "Lưu kịch bản"],
    ["/deployos/os/xoa", "Xóa hệ điều hành"], ["/deployos/tiendo/xoa", "Xóa dòng tiến trình"], ["/deployos/lichsu/xoa", "Xóa dòng lịch sử"],
    ["/deployos/pxe", "Bật/tắt PXE"], ["/ssh/paste", "Dán lệnh vào SSH"], ["/terminal/paste", "Dán lệnh vào terminal"]];
  var DS = phanTich();
  var BAY_GIO = D.bay_gio ? new Date(D.bay_gio.replace(" ", "T")).getTime() : Date.now();

  function nhanNgay(n) {
    if (!n) return "Không rõ ngày";
    var h = new Date(BAY_GIO), a = new Date(n + "T00:00:00");
    var hh = new Date(h.getFullYear(), h.getMonth(), h.getDate()).getTime(), d = Math.round((hh - a.getTime()) / 86400000);
    var p = n.split("-"), s = p[2] + "/" + p[1] + "/" + p[0];
    return d === 0 ? "Hôm nay · " + s : d === 1 ? "Hôm qua · " + s : s;
  }
  function khop(e) {
    if (muc === "loi" && e.muc !== "loi") return false;
    if (muc === "canh" && !e.muc) return false;
    if (khoang && e.ts && BAY_GIO - e.ts > khoang * 1000) return false;
    return !q || e.tim.indexOf(q) >= 0;
  }
  function toSang(node, text) {
    var k = q ? bo(text).indexOf(q) : -1;
    if (k < 0 || bo(text).length !== text.length) { node.textContent = text; return; }   // chi to khi do dai khong doi sau khi bo dau
    node.appendChild(document.createTextNode(text.slice(0, k)));
    node.appendChild(el("mark", null, text.slice(k, k + q.length)));
    node.appendChild(document.createTextNode(text.slice(k + q.length)));
  }

  function ve() {
    var hien = DS.filter(khop); if (moiTruoc) hien = hien.slice().reverse();
    var nl = 0, nc = 0; hien.forEach(function (e) { if (e.muc === "loi") nl += e.lap; else if (e.muc === "canh") nc += e.lap; });
    var tt = $("nk-tt"); tt.textContent = "";
    var b = el("span"); b.appendChild(el("b", null, String(hien.length))); b.appendChild(document.createTextNode(" / " + DS.length + " sự kiện")); tt.appendChild(b);
    if (nl) tt.appendChild(el("span", "l", nl + " lỗi"));
    if (nc) tt.appendChild(el("span", "c", nc + " cảnh báo"));
    if (D.gioi_han && D.lines.length >= D.gioi_han) tt.appendChild(el("span", null, "Trang chỉ nạp " + D.gioi_han + " dòng mới nhất. Nhấn Enter ở ô tìm để tìm trong cả khoảng thời gian."));
    $("nk-xoa").style.display = q ? "block" : "none";
    var ds = $("nk-ds"); ds.textContent = ""; ds.className = "nk-ds" + (xuongDong ? "" : " nk-wrap-off");
    if (!hien.length) { ds.appendChild(el("div", "nk-rong", DS.length ? "Không có sự kiện nào khớp bộ lọc." : D.rong)); return; }
    var ngayCuoi = null;
    hien.slice(0, hienToiDa).forEach(function (e) {
      if (e.ngay !== ngayCuoi) { ngayCuoi = e.ngay; ds.appendChild(el("div", "nk-ngay", nhanNgay(e.ngay))); }
      var h = el("div", "nk-h2 " + e.muc + (e.ct.length ? " co-ct" : ""));
      var g = el("span", "nk-gio", e.gio || ""); if (e.lap > 1 && e.gio2) g.title = e.gio + " - " + e.gio2;
      h.appendChild(g); h.appendChild(el("span", "nk-cham"));
      h.appendChild(e.ng ? el("span", "nk-ng", e.ng) : el("span"));
      var nd = el("span", "nk-nd"); toSang(nd, e.msg); if (e.goc) nd.title = e.goc;
      if (e.lap > 1) nd.appendChild(el("span", "nk-x", "× " + e.lap));
      if (e.ct.length) nd.appendChild(el("span", "nk-mui", "▸ " + e.ct.length + " dòng chi tiết"));
      h.appendChild(nd);
      if (e.ct.length) h.onclick = function () {
        var c = h.querySelector(".nk-ct");
        if (c) { c.remove(); nd.lastChild.textContent = "▸ " + e.ct.length + " dòng chi tiết"; return; }
        var p = el("div", "nk-ct", e.ct.join("\\n")); p.onclick = function (ev) { ev.stopPropagation(); }; h.appendChild(p);
        nd.lastChild.textContent = "▾ ẩn chi tiết";
      };
      ds.appendChild(h);
    });
    if (hien.length > hienToiDa) {
      var n = el("button", "nk-them", "Hiện thêm " + Math.min(300, hien.length - hienToiDa) + " sự kiện (còn " + (hien.length - hienToiDa) + ")"); n.type = "button";
      n.onclick = function () { hienToiDa += 300; ve(); }; ds.appendChild(n);
    }
  }
  function chip(id, gt) {
    var bs = document.querySelectorAll("#" + id + " button");
    Array.prototype.forEach.call(bs, function (b) { b.classList.toggle("on", b.getAttribute("data-v") === gt); });
  }
  function bam(id, fn) {
    var bs = document.querySelectorAll("#" + id + " button");
    Array.prototype.forEach.call(bs, function (b) { b.onclick = function () { fn(b.getAttribute("data-v")); chip(id, b.getAttribute("data-v")); hienToiDa = 300; ve(); }; });
  }
  if ($("nk-muc")) bam("nk-muc", function (v) { muc = v; });
  if ($("nk-kh")) bam("nk-kh", function (v) { khoang = +v || 0; });
  $("nk-tim").addEventListener("input", function (e) { q = bo(e.target.value.trim()); hienToiDa = 300; ve(); });
  $("nk-xoa").addEventListener("click", function () { $("nk-tim").value = ""; q = ""; ve(); $("nk-tim").focus(); });
  if (!D.tim_may_chu) $("nk-tim").form && $("nk-tim").form.addEventListener("submit", function (e) { e.preventDefault(); });
  $("nk-moi").onclick = function () { moiTruoc = !moiTruoc; this.classList.toggle("on", moiTruoc); ve(); };
  $("nk-dong").onclick = function () { xuongDong = !xuongDong; this.classList.toggle("on", xuongDong); ve(); };
  if (D.tim) { $("nk-tim").value = D.tim; q = bo(D.tim); }
  ve();
})();
</script>
"""

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
    form_dau = f'<form method="GET" action="/logs" class="nk-o">' if tab == "log" else '<div class="nk-o">'
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
