/*
 * Console Pi - Tu dong lam moi trang thai
 *
 * Chay tren MOI thiet bi (khac vkeyboard.js chi chay tren man hinh Pi).
 *
 * Nguyen tac: khong duoc lam gian doan viec dang lam.
 *   - Thanh trang thai cap nhat bang AJAX, khong tai lai trang
 *   - Chi trang Tong quan moi tai lai ca trang (de cap nhat cong console
 *     va tinh trang dich vu)
 *   - BO QUA hoan toan neu dang go chu, dang mo terminal, hoac ban phim
 *     ao dang bat - tai lai luc do se mat du lieu dang nhap do
 */
(function () {
  "use strict";

  var PERIOD = 30000;   // 30 giay

  function busy() {
    var el = document.activeElement;
    if (el && /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName)) return true;
    if (document.body.hasAttribute("data-tmux-session")) return true;
    if (document.querySelector("#cpvk.on")) return true;
    return false;
  }

  function refreshChips() {
    fetch("/api/status", { cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d || !d.chips) return;
        d.chips.forEach(function (c, i) {
          var el = document.querySelector('.chip[data-chip="' + i + '"]');
          if (!el) return;
          el.className = "chip " + (c.up ? "up" : "down");
          el.setAttribute("data-chip", i);
          var v = el.querySelector(".v"), x = el.querySelector(".x");
          if (v && v.textContent !== c.val) v.textContent = c.val;
          if (x && x.textContent !== c.extra) x.textContent = c.extra;
        });
      })
      .catch(function () {});
  }

  setInterval(function () {
    if (busy()) return;
    refreshChips();
    if (location.pathname === "/") location.reload();
  }, PERIOD);
})();

/*
 * ---------------------------------------------------------------------------
 * Hieu ung cho khi bam nut cham
 *
 * Cac thao tac quet mang (WiFi, Bluetooth, L2, ghep cap, chay lenh SSH) mat
 * vai giay den vai chuc giay. Neu khong bao gi, nguoi dung tuong may treo va
 * bam lai nhieu lan - vua kho chiu vua co the chay trung.
 *
 * Cach dung: them data-busy="Dang quet..." vao nut. Khi bam, nut doi chu,
 * hien vong xoay, va tu khoa lai.
 * ---------------------------------------------------------------------------
 */
(function () {
  "use strict";

  var css = document.createElement("style");
  css.textContent =
    '@keyframes cpspin{to{transform:rotate(360deg)}}' +
    '.cp-spin{display:inline-block;width:13px;height:13px;margin-right:7px;' +
    'border:2px solid rgba(255,255,255,.35);border-top-color:#fff;border-radius:50%;' +
    'animation:cpspin .7s linear infinite;vertical-align:-2px;}' +
    'button[disabled]{opacity:.75;cursor:progress;}' +
    '.cp-bar{position:fixed;top:0;left:0;height:3px;width:0;background:#4CAF50;' +
    'z-index:2147483600;transition:width .35s ease;box-shadow:0 0 8px #4CAF50;}';
  document.head.appendChild(css);

  // Vach tien do mong tren cung - bao cho biet trang dang xu ly
  var bar = document.createElement("div");
  bar.className = "cp-bar";
  document.body.appendChild(bar);

  function startBar() {
    bar.style.width = "0";
    setTimeout(function () { bar.style.width = "70%"; }, 30);
  }

  document.addEventListener("submit", function (e) {
    var form = e.target;
    if (!form || form.tagName !== "FORM") return;

    var btn = form.querySelector('button[type=submit], button:not([type])');
    if (!btn || btn.disabled) return;

    // Cho trinh duyet gui form xong roi moi khoa nut, neu khoa ngay thi
    // gia tri cua chinh nut do khong duoc gui kem
    setTimeout(function () {
      var label = btn.getAttribute("data-busy") || "Dang xu ly...";
      btn.dataset.cpOld = btn.innerHTML;
      btn.innerHTML = '<span class="cp-spin"></span>' + label;
      btn.disabled = true;
      startBar();
    }, 0);
  });

  // Bam link cung hien vach tien do (cac trang quet co the cham)
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href]");
    if (!a) return;
    var href = a.getAttribute("href") || "";
    if (href.startsWith("#") || href.startsWith("javascript:")) return;
    if (a.target === "_blank") return;
    startBar();
  });

  window.addEventListener("pageshow", function () {
    // Quay lai bang nut Back: mo khoa nut da bi khoa truoc do
    bar.style.width = "0";
    var btns = document.querySelectorAll("button[disabled]");
    for (var i = 0; i < btns.length; i++) {
      if (btns[i].dataset.cpOld) {
        btns[i].innerHTML = btns[i].dataset.cpOld;
        btns[i].disabled = false;
      }
    }
  });
})();
