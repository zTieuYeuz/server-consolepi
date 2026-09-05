/*
 * Console Pi - Ban phim ao + tro giup che do kiosk
 *
 * Chay o CA HAI noi, nhung mac dinh khac nhau:
 *   - Man hinh gan tai cho (localhost) : mac dinh BAT san - man hinh cam
 *     ung khong co ban phim that.
 *   - Truy cap tu xa (laptop/dien thoai qua mang, hoac qua Cloudflare
 *     Tunnel): mac dinh TAT - may do thuong da co ban phim that/ban phim
 *     ao rieng cua he dieu hanh. NHUNG van hien nut bat/tat o goc man hinh,
 *     de ai dang dieu khien tu xa bang dien thoai/may tinh bang KHONG CO
 *     ban phim that van tu bat len duoc khi can - dac biet huu ich khi go
 *     lenh vao Console/Terminal va can cac phim dac biet (Ctrl+C, Tab,
 *     Esc, mui ten) ma ban phim ao mac dinh cua trinh duyet khong co.
 *   Lua chon bat/tat duoc nho rieng theo tung dia chi truy cap (localStorage
 *   theo origin), nen bat len khi dung tu xa khong anh huong toi man hinh
 *   tai cho va nguoc lai.
 *
 * Go duoc vao 2 loai dich:
 *   1. O nhap lieu thong thuong (input/textarea) - go truc tiep
 *   2. Khung Console/Terminal - gui phim qua tmux (vi xterm.js khong phai
 *      o nhap lieu, khong go thang vao duoc). Trang nao co the nhan phim
 *      kieu nay se khai bao <body data-tmux-session="...">
 *
 * Khong dung thu vien ngoai - Pi mang di hien truong co the khong co mang.
 */
(function () {
  "use strict";

  var h = location.hostname;
  var IS_LOCAL = (h === "127.0.0.1" || h === "localhost" || h === "::1");
  if (window.__consolePiVK) return;
  window.__consolePiVK = true;

  // --- Che do kiosk: bo target="_blank" de khong bi ket cua so moi --------
  // CHI ap dung cho man hinh tai cho: trinh duyet that (truy cap tu xa) can
  // giu tab moi binh thuong, khong duoc can thiep.
  function killBlank(root) {
    if (!IS_LOCAL) return;
    var a = (root && root.querySelectorAll ? root : document)
              .querySelectorAll('a[target="_blank"]');
    for (var i = 0; i < a.length; i++) a[i].removeAttribute("target");
  }

  // ------------------------------------------------------------------------
  var target = null;        // o nhap lieu dang go
  var shift = false, symbols = false;
  var visible = false;
  var tmuxSession = null;   // neu trang la console/terminal

  var ROWS_LETTERS = [
    ["1","2","3","4","5","6","7","8","9","0"],
    ["q","w","e","r","t","y","u","i","o","p"],
    ["a","s","d","f","g","h","j","k","l"],
    ["z","x","c","v","b","n","m"]
  ];
  var ROWS_SYMBOLS = [
    ["!","@","#","$","%","^","&","*","(",")"],
    ["-","_","=","+","[","]","{","}","\\","|"],
    [";",":","'","\"",",",".","<",">"],
    ["/","?","~","`"]
  ];

  /* CSS dung !important cho cac thuoc tinh bo cuc.
     Ly do: mot so trang co san rule kieu `button { width:100% }` (vd trang
     dang nhap) se de len phim, lam ban phim bi keo gian het chieu ngang. */
  /* Kich thuoc phim tinh theo % chieu cao man hinh (vh) thay vi so px co
     dinh: truoc day 58px/21px co dinh lam ban phim CHIEM QUA NUA man hinh
     nho cua RasPad (man 7"/10" cao that su chi ~480-600px), che mat gan
     het noi dung phia tren. Dung clamp(min, ti-le-vh, max) de:
       - man cao (>=800px, RasPad 10.1"): giu nguyen 58px/21px nhu truoc
       - man thap (480-600px): tu thu nho xuong, nhung khong bao gio duoi
         40px chieu cao / 16px chu - duoi muc do la ngon tay bam de trung
         phim ben canh, "toi uu" thanh "khong go duoc" thi phan tac dung. */
  var css = [
    '#cpvk{position:fixed!important;left:0!important;right:0!important;bottom:0!important;',
    'z-index:2147483000!important;background:#1c1f23!important;border-top:2px solid #4CAF50!important;',
    'padding:clamp(4px,1vh,9px) 8px clamp(6px,1.3vh,9px)!important;display:none;',
    'box-shadow:0 -6px 22px rgba(0,0,0,.7)!important;',
    'font-family:system-ui,Arial,sans-serif!important;}',
    '#cpvk.on{display:block!important;}',
    '#cpvk *{box-sizing:border-box!important;}',
    '#cpvk .cprow{display:flex!important;justify-content:center!important;gap:6px!important;',
    'margin:clamp(3px,0.9vh,7px) 0!important;width:100%!important;}',
    /* Phim chuan rong bang 1/10 man hinh -> hang 10 phim trai kin chieu ngang.
       Hang it phim hon (9, 7) van dung kich thuoc do va tu can giua, giong
       ban phim that. Truoc day dung min-width co dinh nen bi don cum o giua,
       hai ben trong tron. */
    '#cpvk .cprow button{flex:0 0 calc((100% - 54px) / 10)!important;',
    'width:auto!important;min-width:0!important;',
    'max-width:none!important;height:clamp(40px,7.5vh,58px)!important;',
    'min-height:40px!important;margin:0!important;',
    'padding:0 4px!important;font-size:clamp(16px,3vh,21px)!important;line-height:1!important;',
    'background:#33383e!important;color:#e9edf2!important;border:1px solid #454b52!important;',
    'border-radius:7px!important;cursor:pointer!important;touch-action:manipulation!important;',
    '-webkit-user-select:none!important;user-select:none!important;font-family:inherit!important;',
    'text-transform:none!important;letter-spacing:normal!important;}',
    '#cpvk button:active{background:#4CAF50!important;color:#fff!important;}',
    /* Hang cuoi co gian day chieu ngang, Space rong nhat */
    '#cpvk .cprow.last button{flex:1 1 0!important;}',
    '#cpvk .cprow.last button.w{flex:1.4 1 0!important;font-size:clamp(13px,2.2vh,15px)!important;}',
    '#cpvk .cprow.last button.sp{flex:4 1 0!important;font-size:clamp(14px,2.4vh,16px)!important;}',
    '#cpvk button.act{background:#454b52!important;font-size:clamp(12px,2vh,14px)!important;}',
    '#cpvk button.on{background:#4CAF50!important;color:#fff!important;}',
    '#cpvk .cpbar{display:flex!important;justify-content:space-between!important;',
    'align-items:center!important;gap:10px!important;padding:1px 4px 4px!important;',
    'color:#93a0b0!important;font-size:12px!important;}',
    '#cpvk .cpbar b{color:#4CAF50!important;}',
    '#cpvk button.cpclose{background:#d64545!important;color:#fff!important;',
    'min-width:70px!important;height:clamp(30px,4.5vh,34px)!important;',
    'min-height:30px!important;font-size:13px!important;}',
    /* Nut bat/tat noi - luon o goc phai duoi */
    '#cpvktoggle{position:fixed!important;right:14px!important;bottom:14px!important;',
    'z-index:2147482999!important;width:clamp(46px,7vh,58px)!important;',
    'height:clamp(46px,7vh,58px)!important;min-width:46px!important;',
    'min-height:46px!important;padding:0!important;border-radius:50%!important;',
    'background:#4CAF50!important;color:#fff!important;border:none!important;',
    'font-size:24px!important;cursor:pointer!important;box-shadow:0 3px 12px rgba(0,0,0,.55)!important;',
    'display:flex!important;align-items:center!important;justify-content:center!important;',
    'touch-action:manipulation!important;-webkit-user-select:none!important;user-select:none!important;}',
    '#cpvktoggle.off{background:#5a6672!important;}'
  ].join("");

  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  var kb = document.createElement("div");
  kb.id = "cpvk";
  document.body.appendChild(kb);

  var toggle = document.createElement("button");
  toggle.id = "cpvktoggle";
  toggle.type = "button";
  toggle.textContent = "⌨";
  toggle.title = "Bat/tat ban phim ao";
  document.body.appendChild(toggle);

  // Nho lua chon bat/tat rieng theo tung dia chi truy cap (localStorage la
  // theo origin nen localhost va ten mien Cloudflare tu nhien co gia tri
  // rieng, khong dung chung).
  //
  // Mac dinh: BAT o man hinh tai cho (khong co ban phim that), TAT khi truy
  // cap tu xa (may do thuong da co ban phim rieng). Nguoi dung co the tu doi
  // bang nut bat/tat - luc do gia tri da luu se ghi de len mac dinh nay.
  var luu = localStorage.getItem("cpvk_enabled");
  var enabled = luu !== null ? (luu !== "0") : IS_LOCAL;
  function paintToggle() {
    toggle.className = enabled ? "" : "off";
    toggle.title = enabled ? "Ban phim ao: DANG BAT" : "Ban phim ao: DANG TAT";
  }
  paintToggle();

  toggle.addEventListener("pointerdown", function (e) {
    e.preventDefault();
    enabled = !enabled;
    localStorage.setItem("cpvk_enabled", enabled ? "1" : "0");
    paintToggle();
    if (!enabled) hide();
    else if (tmuxSession) show(null);          // trang terminal: mo ngay
    else if (isTypable(document.activeElement)) show(document.activeElement);
  });

  /* Giu focus o o nhap lieu khi cham vao ban phim.
     KHONG duoc preventDefault tren touchstart: lam vay se chan luon su kien
     click ma trinh duyet sinh ra sau do -> cham vao phim khong an gi.
     Chi can chan mousedown/pointerdown la du giu focus. */
  kb.addEventListener("mousedown", function (e) { e.preventDefault(); });

  // --- Gui phim ----------------------------------------------------------
  function sendToTmux(keys) {
    fetch("/api/send-keys", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session: tmuxSession, keys: keys })
    }).catch(function () {});
  }

  function insert(text) {
    if (tmuxSession && !target) { sendToTmux(text); return; }
    if (!target) return;
    var s = target.selectionStart, e = target.selectionEnd;
    if (typeof s === "number" && typeof e === "number") {
      target.value = target.value.slice(0, s) + text + target.value.slice(e);
      target.selectionStart = target.selectionEnd = s + text.length;
    } else {
      target.value += text;
    }
    target.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function backspace() {
    if (tmuxSession && !target) { sendToTmux("BSpace"); return; }
    if (!target) return;
    var s = target.selectionStart, e = target.selectionEnd;
    if (typeof s === "number" && s !== e) {
      target.value = target.value.slice(0, s) + target.value.slice(e);
      target.selectionStart = target.selectionEnd = s;
    } else if (typeof s === "number" && s > 0) {
      target.value = target.value.slice(0, s - 1) + target.value.slice(s);
      target.selectionStart = target.selectionEnd = s - 1;
    } else {
      target.value = target.value.slice(0, -1);
    }
    target.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function enter() {
    if (tmuxSession && !target) { sendToTmux("Enter"); return; }
    if (!target) return;
    if (target.tagName === "TEXTAREA") { insert("\n"); return; }
    var form = target.form;
    hide();
    if (form) { form.requestSubmit ? form.requestSubmit() : form.submit(); }
  }

  function btn(label, cls, fn) {
    var b = document.createElement("button");
    b.type = "button";
    b.textContent = label;
    if (cls) b.className = cls;

    /* Dung pointerdown thay vi click: chay cho ca chuot lan cam ung, va
       phan hoi ngay khi cham (khong phai cho nha tay). preventDefault o day
       giu focus o o nhap lieu ma KHONG chan su kien nao khac.

       LOI THAT DA TIM RA (nguoi dung bao phim "?123" va "⇧" phai BAM GIU
       moi an, bam nhanh binh thuong thi khong): hai phim nay goi render(),
       ham nay xoa het roi ve lai TOAN BO ban phim (kb.innerHTML = "") ngay
       trong luc ngon tay con dang cham xuong man hinh. Tuc la chinh cai nut
       dang duoc cham lai bi XOA KHOI TRANG giua chung cu chi cham - man hinh
       cam ung/trinh duyet hieu nham thanh cu chi bi huy (giong nhu vuot/keo)
       va khong tinh la mot cai cham hop le, phai giu du lau moi "an" duoc.
       Cac phim khac (go chu, xoa, enter) khong tu ve lai chinh no nen khong
       bi loi nay.
       Cach sua: doi viec goi fn() (co the ve lai DOM) sang CHAY SAU, bang
       setTimeout 0 - de trinh duyet xu ly xong tron ven cu chi cham hien tai
       (pointerdown/click) tren nut con nguyen trong trang, roi moi doi DOM. */
    var fired = false;
    b.addEventListener("pointerdown", function (ev) {
      ev.preventDefault();
      fired = true;
      setTimeout(fn, 0);
    });
    // Du phong cho trinh duyet cu khong ho tro Pointer Events
    b.addEventListener("click", function (ev) {
      ev.preventDefault();
      if (!fired) setTimeout(fn, 0);
      fired = false;
    });
    return b;
  }

  function render() {
    kb.innerHTML = "";

    var bar = document.createElement("div");
    bar.className = "cpbar";
    var lbl = document.createElement("span");
    if (tmuxSession && !target) {
      lbl.innerHTML = "⌨ Go thang vao <b>terminal</b>";
    } else {
      lbl.innerHTML = "⌨ Dang go vao: <b>" +
        (target ? (target.getAttribute("name") || target.type || "o nhap lieu") : "-") + "</b>";
    }
    bar.appendChild(lbl);
    bar.appendChild(btn("✕ Dong", "cpclose", hide));
    kb.appendChild(bar);

    (symbols ? ROWS_SYMBOLS : ROWS_LETTERS).forEach(function (keys) {
      var r = document.createElement("div");
      r.className = "cprow";
      keys.forEach(function (k) {
        var lb = (!symbols && shift) ? k.toUpperCase() : k;
        r.appendChild(btn(lb, "", function () {
          insert(lb);
          if (shift && !symbols) { shift = false; render(); }
        }));
      });
      kb.appendChild(r);
    });

    var last = document.createElement("div");
    last.className = "cprow last";
    last.appendChild(btn(symbols ? "ABC" : "?123", "w act" + (symbols ? " on" : ""),
                         function () { symbols = !symbols; render(); }));
    if (!symbols) {
      last.appendChild(btn("⇧", "w act" + (shift ? " on" : ""),
                           function () { shift = !shift; render(); }));
    }
    last.appendChild(btn(".", "", function () { insert("."); }));
    last.appendChild(btn("Space", "sp", function () {
      if (tmuxSession && !target) sendToTmux("Space"); else insert(" ");
    }));
    last.appendChild(btn("⌫", "w act", backspace));
    last.appendChild(btn("↵", "w act", enter));
    kb.appendChild(last);

    // Phim rieng cho terminal
    if (tmuxSession && !target) {
      var ctl = document.createElement("div");
      ctl.className = "cprow last";
      ctl.appendChild(btn("Tab", "w act", function () { sendToTmux("Tab"); }));
      ctl.appendChild(btn("Esc", "w act", function () { sendToTmux("Escape"); }));
      ctl.appendChild(btn("Ctrl+C", "w act", function () { sendToTmux("C-c"); }));
      ctl.appendChild(btn("↑", "act", function () { sendToTmux("Up"); }));
      ctl.appendChild(btn("↓", "act", function () { sendToTmux("Down"); }));
      ctl.appendChild(btn("←", "act", function () { sendToTmux("Left"); }));
      ctl.appendChild(btn("→", "act", function () { sendToTmux("Right"); }));
      kb.appendChild(ctl);
    }
  }

  function show(el) {
    if (!enabled) return;
    target = el;
    shift = false; symbols = false;
    render();
    kb.classList.add("on");
    visible = true;
    if (el) {
      setTimeout(function () {
        var r = el.getBoundingClientRect();
        if (r.bottom > window.innerHeight - kb.offsetHeight) {
          el.scrollIntoView({ block: "center", behavior: "smooth" });
        }
      }, 60);
    }
  }

  function hide() {
    kb.classList.remove("on");
    visible = false;
    target = null;
  }

  function isTypable(el) {
    if (!el || !el.tagName) return false;
    if (el.tagName === "TEXTAREA") return true;
    if (el.tagName !== "INPUT") return false;
    return ["text","password","number","search","email","url","tel"]
             .indexOf((el.type || "text").toLowerCase()) !== -1;
  }

  document.addEventListener("focusin", function (e) {
    if (isTypable(e.target)) show(e.target);
  });
  document.addEventListener("focusout", function () {
    setTimeout(function () {
      if (isTypable(document.activeElement)) return;
      if (tmuxSession) { target = null; if (visible) render(); return; }
      hide();
    }, 150);
  });

  function init() {
    killBlank(document);
    tmuxSession = document.body.getAttribute("data-tmux-session") || null;
    if (tmuxSession && enabled) show(null);   // trang terminal: hien san
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  if (window.MutationObserver) {
    new MutationObserver(function (m) {
      for (var i = 0; i < m.length; i++)
        for (var j = 0; j < m[i].addedNodes.length; j++)
          if (m[i].addedNodes[j].nodeType === 1) killBlank(m[i].addedNodes[j]);
    }).observe(document.documentElement, { childList: true, subtree: true });
  }
})();
