"""
Console Pi - Khoi "o soan tap lenh" dung chung cho tab Terminal va tab SSH.

Ca 2 tab deu can y het nhau: chon tap lenh tu Thu vien -> sua lai cho dung ->
Copy / Dan tu clipboard / Dan thang vao khung terminal. De o 1 cho de sua 1 lan
la ca 2 tab cung duoc, khong bi lech nhau theo thoi gian.

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
    if (i === "") { noi("Chon 1 tap lenh trong danh sach truoc.", "warn"); return; }
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
      noi(ok ? "Da copy noi dung o lenh."
             : "Trinh duyet khong cho copy tu dong - noi dung da duoc boi den, copy tay giup em.",
          ok ? "ok" : "warn");
    } catch (e) {
      noi("Trinh duyet khong cho copy tu dong - noi dung da duoc boi den, copy tay giup em.", "warn");
    }
  }

  document.getElementById("nut_copy").addEventListener("click", function () {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(o.value).then(
        function () { noi("Da copy noi dung o lenh.", "ok"); },
        function () { copyCachCu(); });
    } else { copyCachCu(); }
  });

  document.getElementById("nut_dan_cb").addEventListener("click", function () {
    if (navigator.clipboard && navigator.clipboard.readText && window.isSecureContext) {
      navigator.clipboard.readText().then(function (t) {
        o.value = t; luu(); noi("Da dan noi dung tu clipboard vao o.", "ok");
      }, function () {
        noi("Trinh duyet chan doc clipboard. Cham vao o roi dan tay, hoac dung ban phim ao.", "warn");
      });
    } else {
      noi("Vao bang HTTP nen trinh duyet khong cho doc clipboard. Cham vao o roi dan tay, " +
          "hoac dung ban phim ao.", "warn");
    }
  });

  document.getElementById("nut_xoa").addEventListener("click", function () {
    o.value = ""; luu(); noi("Da xoa o lenh.", "info");
  });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var nut = document.getElementById("nut_dan");
    var chuCu = nut.innerHTML;
    nut.disabled = true; nut.innerHTML = "Dang dan...";
    noi("Dang dan vao terminal, cho thiet bi phan hoi...", "info");
    fetch(form.action, {
      method: "POST", body: new FormData(form),
      headers: { "X-Console-Pi": "fetch" }, cache: "no-store"
    })
      .then(function (r) {
        if (!r.ok) throw new Error("Server tra ve HTTP " + r.status);
        return r.json();
      })
      .then(function (d) { noi(d.msg, d.ok ? "ok" : "err"); })
      .catch(function (err) { noi("Khong lien lac duoc voi server: " + err.message, "err"); })
      .finally(function () { nut.disabled = false; nut.innerHTML = chuCu; });
  });
})();
</script>
"""


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
        Nut Dan tu chon dung cach: dang o <strong>shell cua Pi</strong> thi dan ca khoi va
        <strong>khong dong nao chay</strong>; dang <strong>SSH/console vao thiet bi</strong> thi
        gui tung dong, cho thiet bi in xong moi gui tiep (khoi roi mat chu), dong CUOI de anh
        tu bam Enter.
      </p>
    </form>
    <script>var THU_VIEN = {du_lieu};</script>
    {SOAN_JS}"""
