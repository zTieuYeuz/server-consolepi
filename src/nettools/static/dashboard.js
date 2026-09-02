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
