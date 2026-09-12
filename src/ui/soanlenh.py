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
import json

from .commands import load_library


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# JS de rieng ngoai f-string vi co rat nhieu dau ngoac nhon - nhet vao
# f-string phai nhan doi het, rat de sai va kho doc.
SOAN_JS = """
<script>
(function () {
  "use strict";
  var form = document.getElementById("form_dan");
  if (!form) return;
  var o = document.getElementById("o_lenh");
  var chon = document.getElementById("chon_tap");
  var bao = document.getElementById("bao_dan");
  var KHOA_LUU = form.getAttribute("data-khoa-luu") || "consolepi-o-lenh";

  function noi(chuoi, loai) {
    bao.textContent = chuoi;
    bao.className = "msg " + (loai || "info");
    bao.style.display = chuoi ? "block" : "none";
  }

  // Giu lai noi dung dang soan khi tai lai trang. Chi luu tren may dang
  // dung, khong gui ve server.
  function luu() { try { localStorage.setItem(KHOA_LUU, o.value); } catch (e) {} }
  o.addEventListener("input", luu);
  if (!o.value) {
    try { var cu = localStorage.getItem(KHOA_LUU); if (cu) o.value = cu; } catch (e) {}
  } else { luu(); }

  document.getElementById("nut_chep").addEventListener("click", function () {
    var i = chon.value;
    if (i === "") { noi("Chọn 1 tập lệnh trong danh sách trước.", "warn"); return; }
    o.value = THU_VIEN[i].lenh;
    luu();
    noi("Da chep \\"" + THU_VIEN[i].ten + "\\" vao o. Sua lai IP/ten cho dung roi dan.", "info");
  });

  function copyCachCu() {
    // Trang chay HTTP thuong (vao bang IP trong LAN) thi navigator.clipboard
    // KHONG ton tai - trinh duyet chi cho dung Clipboard API o ngu canh bao
    // mat (HTTPS hoac localhost). execCommand cu van chay duoc tren HTTP.
    try {
      o.focus(); o.select();
      var ok = document.execCommand("copy");
      noi(ok ? "Đã copy nội dung ô lệnh."
             : "Trinh duyet khong cho copy tu dong - noi dung da duoc boi den, copy tay giup em.",
          ok ? "ok" : "warn");
    } catch (e) {
      noi("Trinh duyet khong cho copy tu dong - noi dung da duoc boi den, copy tay giup em.", "warn");
    }
  }

  document.getElementById("nut_copy").addEventListener("click", function () {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(o.value).then(
        function () { noi("Đã copy nội dung ô lệnh.", "ok"); },
        function () { copyCachCu(); });
    } else { copyCachCu(); }
  });

  document.getElementById("nut_dan_cb").addEventListener("click", function () {
    if (navigator.clipboard && navigator.clipboard.readText && window.isSecureContext) {
      navigator.clipboard.readText().then(function (t) {
        o.value = t; luu(); noi("Đã dán nội dung từ clipboard vào ô.", "ok");
      }, function () {
        noi("Trinh duyet chan doc clipboard. Cham vao o roi dan tay, hoac dung ban phim ao.", "warn");
      });
    } else {
      noi("Vao bang HTTP nen trinh duyet khong cho doc clipboard. Cham vao o roi dan tay, " +
          "hoac dung ban phim ao.", "warn");
    }
  });

  document.getElementById("nut_xoa").addEventListener("click", function () {
    o.value = ""; luu(); noi("Đã xóa ô lệnh.", "info");
  });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var nut = document.getElementById("nut_dan");
    var chuCu = nut.innerHTML;
    nut.disabled = true; nut.innerHTML = "Đang dán...";
    noi("Đang dán vào terminal, chờ thiết bị phản hồi...", "info");
    fetch(form.action, {
      method: "POST", body: new FormData(form),
      headers: { "X-Console-Pi": "fetch" }, cache: "no-store"
    })
      .then(function (r) {
        if (!r.ok) throw new Error("Server trả về HTTP " + r.status);
        return r.json();
      })
      .then(function (d) { noi(d.msg, d.ok ? "ok" : "err"); })
      .catch(function (err) { noi("Không liên lạc được với server: " + err.message, "err"); })
      .finally(function () { nut.disabled = false; nut.innerHTML = chuCu; });
  });
})();
</script>
"""


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
COPY_TERM_JS = """
<script>
(function () {
  "use strict";
  var bao = document.getElementById("bao_copyterm");
  if (!bao) return;

  function noi(chuoi, loai) {
    bao.textContent = chuoi;
    bao.className = "msg " + (loai || "info");
    bao.style.display = chuoi ? "block" : "none";
  }

  function layTerm() {
    var f = document.querySelector("iframe");
    if (!f) return null;
    try { return f.contentWindow && f.contentWindow.term ? f.contentWindow.term : null; }
    catch (e) { return null; }   // khac nguon goc (khong xay ra o day, nhung cu chac)
  }

  // Trang vao bang IP LAN chay HTTP thuong -> navigator.clipboard khong ton
  // tai (chi co o HTTPS/localhost). execCommand cu van chay tren HTTP.
  function chepCachCu(chu) {
    var o = document.createElement("textarea");
    o.value = chu;
    o.style.position = "fixed"; o.style.left = "-9999px";
    document.body.appendChild(o);
    o.focus(); o.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    document.body.removeChild(o);
    noi(ok ? "Da copy " + chu.length + " ky tu." :
        "Trinh duyet khong cho copy tu dong. Giu Shift roi boi den bang chuot va copy tay giup em.",
        ok ? "ok" : "warn");
  }

  function chep(chu) {
    if (!chu) return;
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(chu).then(
        function () { noi("Da copy " + chu.length + " ky tu.", "ok"); },
        function () { chepCachCu(chu); });
    } else { chepCachCu(chu); }
  }

  document.getElementById("nut_copy_chon").addEventListener("click", function () {
    var t = layTerm();
    if (!t) { noi("Khung terminal chua san sang - doi no hien chu roi bam lai.", "warn"); return; }
    var chu = t.getSelection();
    if (!chu) {
      noi("Chua boi den chu nao. GIU PHIM SHIFT trong luc keo chuot de boi den " +
          "(khong giu Shift thi tmux giu chuot de cuon man hinh), roi bam lai nut nay.", "warn");
      return;
    }
    chep(chu);
  });

  document.getElementById("nut_copy_all").addEventListener("click", function () {
    var t = layTerm();
    if (!t) { noi("Khung terminal chua san sang - doi no hien chu roi bam lai.", "warn"); return; }
    t.selectAll();
    var chu = t.getSelection();
    t.clearSelection();
    if (!chu) { noi("Khung terminal dang trong.", "warn"); return; }
    chep(chu);
  });
})();
</script>
"""


def khoi_copy_terminal():
    """
    Hang nut "copy chu tu terminal ra ngoai" - dat ngay duoi khung terminal.
    Trang nao dung phai co dung 1 the <iframe> cua terminal.
    """
    return f"""
    <div class="row" style="margin-bottom:10px;">
      <button type="button" class="gray" id="nut_copy_chon">📋 Copy vùng đã chọn</button>
      <button type="button" class="gray" id="nut_copy_all">📄 Copy ca man hinh</button>
    </div>
    <p style="color:#8b93a1;font-size:13px;margin:0 0 12px;">
      Bôi đen bằng chuột phải <strong>giu phim Shift</strong> (khong giu thi tmux
      giữ chuột để cuộn màn hình). Không có bàn phím thì dùng nút
      <strong>Copy ca man hinh</strong>.
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
          <option value="">-- Chon tap lenh tu Thu vien --</option>
          {lua_chon}
        </select>
        <button type="button" class="gray" id="nut_chep">📄 Chep vao o</button>
        <a class="btn gray" href="/commands">📚 Sua thu vien</a>
      </div>
      <textarea name="noi_dung" id="o_lenh" style="max-width:100%;min-height:110px;"
                placeholder="Go lenh o day, hoac chon tap lenh o tren roi sua lai IP/ten cong...">{_esc(prefill)}</textarea>
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
