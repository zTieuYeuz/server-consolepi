# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi - Cac khoi dung chung quanh khung terminal (Terminal / SSH /
Console serial).

  1. khoi_soan_lenh()    - o soan tap lenh: chon tap lenh tu Thu vien -> sua
                           lai cho dung -> Copy / Dan tu clipboard / Dan
                           thang vao khung terminal.
  2. khoi_copy_terminal() - copy chu TU trong khung terminal RA ngoai.

De o 1 cho de sua 1 lan la moi tab cung duoc, khong bi lech nhau theo thoi
gian.

Cac nut deu gui bang fetch (khong tai lai trang) vi 2 ly do THAT:
  - Tai lai trang se nap lai khung terminal ben tren -> mat cai dang nhin
  - ttyd co dang ky canh bao truoc khi roi trang, nen moi lan bam nut la
    trinh duyet hoi "Leave site?" - rat vuong khi dang lam viec
"""
from consolesystem.core import taisan as _taisan
import sys as _sys
_sys.modules["ui.soanlenh"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import json

from ui.commands import load_library
from consolesystem.core.esc import esc as _esc




# JS de rieng ngoai f-string vi co rat nhieu dau ngoac nhon - nhet vao
# f-string phai nhan doi het, rat de sai va kho doc.
SOAN_JS = _taisan.doc("features/terminal/soanlenh.SOAN_JS.html")


# ---------------------------------------------------------------------------
# Copy chu TU trong khung terminal RA ngoai
#
# LOI THAT DA TIM RA (nguoi dung bao "muon copy 1 dong lenh tu terminal ra ma
# khong lam duoc, anh dung chuot"), da kiem chung bang thuc nghiem chu khong
# doan - dung CDP mo phong keo chuot that tren chinh khung terminal dang chay:
#     keo chuot BINH THUONG  -> term.getSelection() tra ve rong
#     keo chuot GIU PHIM SHIFT -> tra ve dung doan chu da boi den
#
# Nguyen nhan: cac phien terminal deu chay trong tmux voi `mouse on` (bat co
# chu dich tu truoc de banh xe chuot cuon dung lich su man hinh thay vi bi
# dich thanh phim Mui ten - xem scripts/term-launch.sh). Khi tmux bat che do
# chuot, no bao terminal "gui moi su kien chuot cho ung dung" - xterm.js
# nhuong quyen xu ly chuot cho tmux nen khong con tu boi den chu nua. Giu
# Shift la duong "vuot rao" tieu chuan cua xterm.js (giong gnome-terminal,
# iTerm2, Windows Terminal) de ep no tu boi den lai.
#
# KHONG tat `mouse on` cua tmux de "sua" viec nay: lam vay se lam sai lai loi
# banh xe chuot da sua truoc do. Thay vao do: (1) ghi ro huong dan giu Shift
# ngay tren giao dien, (2) them nut Copy doc thang selection cua xterm.js qua
# API `term.getSelection()` (ttyd co gan doi tuong Terminal vao window.term
# cua khung iframe - da kiem chung that), (3) them nut copy CA MAN HINH bang
# `term.selectAll()` cho truong hop can lay ca doan ket qua lenh dai.
COPY_TERM_JS = _taisan.doc("features/terminal/soanlenh.COPY_TERM_JS.html")


def khoi_copy_terminal():
    """
    Hang nut "copy chu tu terminal ra ngoai" - dat ngay duoi khung terminal.
    Trang nao dung phai co dung 1 the <iframe> cua terminal.
    """
    return f"""
    <div class="row" style="margin-bottom:10px;">
      <button type="button" class="gray" id="nut_copy_chon">📋 Copy vùng đã chọn</button>
      <button type="button" class="gray" id="nut_copy_all">📄 Copy cả màn hình</button>
    </div>
    <p style="color:#8b93a1;font-size:13px;margin:0 0 12px;">
      Bôi đen bằng chuột phải <strong>giữ phím Shift</strong> (không giữ thì tmux
      giữ chuột để cuộn màn hình). Không có bàn phím thì dùng nút
      <strong>Copy cả màn hình</strong>.
    </p>
    <div id="bao_copyterm" class="msg" style="display:none;"></div>
    {COPY_TERM_JS}"""


def khoi_soan_lenh(url_dan, khoa_luu, prefill=""):
    """
    Tra ve HTML cua o soan tap lenh.

    url_dan  : duong dan POST de dan vao terminal (moi tab 1 duong rieng)
    khoa_luu : khoa luu noi dung dang soan tren may nguoi dung (moi tab
               1 khoa rieng - dang soan o tab SSH khong de len tab Terminal)
    """
    lib = load_library()
    lua_chon = "".join(
        f'<option value="{i}">{_esc(it.get("name"))}</option>' for i, it in enumerate(lib)
    )
    # Nhung du lieu NGUOI DUNG TU NHAP vao the <script> - phai chan duong
    # thoat ra chay ma doc hai:
    #   ensure_ascii=True   -> ky tu ngoai ASCII thanh \\uXXXX, khong the lam
    #                          vo cu phap JS (ke ca U+2028/U+2029)
    #   doi < > & -> \\u00xx -> sau khi doi thi khong con dau "<" tho nao
    #                          trong the script. Chi thay "</" bang "<\\/" la
    #                          CHUA DU: mot tap lenh chua "<script>" van lot,
    #                          ma theo chuan HTML gap "<script" ben trong the
    #                          script se day bo phan tich sang trang thai dac
    #                          biet, khien </script> ke tiep khong dong the.
    du_lieu = (json.dumps(
        [{"ten": it.get("name", ""), "lenh": it.get("commands", "")} for it in lib],
        ensure_ascii=True,
    ).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))

    return f"""
    <form method="POST" action="{url_dan}" id="form_dan" data-khoa-luu="{_esc(khoa_luu)}">
      <div class="row" style="margin-bottom:8px;">
        <select id="chon_tap" style="max-width:300px;">
          <option value="">-- Chọn tập lệnh từ Thư viện --</option>
          {lua_chon}
        </select>
        <button type="button" class="gray" id="nut_chep">📄 Chep vao o</button>
        <a class="btn gray" href="/commands">📚 Sua thu vien</a>
      </div>
      <textarea name="noi_dung" id="o_lenh" style="max-width:100%;min-height:110px;"
                placeholder="Gõ lệnh ở đây, hoặc chọn tập lệnh ở trên rồi sửa lại IP/tên cổng...">{_esc(prefill)}</textarea>
      <div class="row" style="margin-top:10px;">
        <button type="submit" class="blue" id="nut_dan">⌨️ Dan vao terminal</button>
        <button type="button" class="gray" id="nut_copy">📋 Copy</button>
        <button type="button" class="gray" id="nut_dan_cb">📥 Dan tu clipboard</button>
        <button type="button" class="gray" id="nut_xoa">🧹 Xoa o</button>
      </div>
      <div id="bao_dan" class="msg" style="display:none;"></div>
      <p style="color:#8b93a1;font-size:13px;margin:9px 0 0;">
        Nút Dán tự chọn đúng cách: đang ở <strong>shell cua Pi</strong> thì dán cả khối và
        <strong>không dòng nào chạy</strong>; dang <strong>SSH/console vào thiết bị</strong> thi
        gửi từng dòng, chờ thiết bị in xong mới gửi tiếp (khỏi rơi mất chữ), dòng CUỐI để anh
        tu bam Enter.
      </p>
    </form>
    <script>var THU_VIEN = {du_lieu};</script>
    {SOAN_JS}"""
