"""
Console Pi - Tab SSH

Chi con 1 che do duy nhat: SSH TUONG TAC bang terminal that (ttyd + tmux),
go duoc moi thu nhu PuTTY. Kem ngay duoi khung terminal 1 O SOAN TAP LENH:
chon tap lenh co san tu Thu vien -> sua lai IP/ten cho dung -> Copy hoac dan
thang vao terminal.

DA BO "chay hang loat" (Netmiko) o tab nay theo yeu cau: no trung vai tro voi
cong cu "Netmiko Config" ben Network Tools, va trong thuc te lam viec thi
duong nao cung phai nhin man hinh thiet bi that de biet lenh an vao chua.

TU DIEN MAT KHAU - vi sao KHONG dung sshpass:
  - sshpass -p '<mk>' dat mat khau THANG TREN DONG LENH: ai chay `ps` cung
    doc duoc, va no con nam lai trong lich su cuon cua terminal.
  - Cach dung o day: go lenh ssh vao terminal, roi DOI cho toi khi dong cuoi
    cua man hinh dung la dau nhac mat khau, moi go mat khau vao. Dau nhac
    mat khau khong hien lai ky tu nen mat khau khong bao gio hien tren man
    hinh, khong vao `ps`, khong vao lich su lenh. Da kiem chung that bang
    tmux capture-pane truoc khi viet ham nay.
  - Neu qua 12 giay khong thay dau nhac (thiet bi cham, dung khoa, khong ket
    noi duoc...) thi BAO THAT la khong thay, khong im lang coi nhu xong.
"""
import json
import re
import subprocess
import time

from flask import request

from .layout import render_page
from .commands import load_library, dan_tung_dong_vao_tmux
from .terminal import SSH_SESSION, tmux_session_exists, service_active

# Dau nhac mat khau cua ssh ("...'s password:", "Enter passphrase for key ...:")
_DAU_NHAC_MK = re.compile(r"(?:password|passphrase).*:\s*$", re.I)


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _chup_man_hinh(session):
    """Doc noi dung dang hien tren man hinh cua phien tmux."""
    try:
        r = subprocess.run(["tmux", "capture-pane", "-p", "-t", session],
                           capture_output=True, text=True, timeout=5)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


def _dong_cuoi(text):
    dong = [l.rstrip() for l in (text or "").splitlines() if l.strip()]
    return dong[-1] if dong else ""


def _la_dau_nhac_mat_khau(dong):
    return bool(dong) and bool(_DAU_NHAC_MK.search(dong))


def _cho_dau_nhac_mat_khau(session, truoc, giay_toi_da=12):
    """
    Doi cho toi khi man hinh terminal hien dau nhac mat khau.

    Bat buoc man hinh phai KHAC luc truoc khi go lenh: neu khong so sanh, mot
    dau nhac mat khau con sot lai cua phien cu se bi cham nham la dau nhac
    cua phien vua mo, va mat khau se bi go nham cho.
    """
    het_han = time.time() + giay_toi_da
    while time.time() < het_han:
        time.sleep(0.3)
        hien = _chup_man_hinh(session)
        if hien and hien != truoc and _la_dau_nhac_mat_khau(_dong_cuoi(hien)):
            return True
    return False


def start_ssh_in_tmux(host, user, port=22, password=""):
    """Chay lenh ssh trong phien tmux; tu dien mat khau neu duoc nhap san."""
    host = (host or "").strip()
    user = (user or "").strip()
    if not host or not user:
        return False, "Thieu dia chi hoac tai khoan."

    # Loc dau vao: host/user duoc ghep thanh 1 DONG LENH chay trong shell cua
    # terminal, khong loc thi mot gia tri kieu "1.1.1.1; rm -rf /" se chay
    # that su tren Pi.
    if not re.fullmatch(r"[A-Za-z0-9._:\-]{1,255}", host):
        return False, "Dia chi khong hop le (chi cho chu, so va cac dau . - _ :)."
    if not re.fullmatch(r"[A-Za-z0-9._\-\\]{1,64}", user):
        return False, "Tai khoan khong hop le (chi cho chu, so va cac dau . - _ \\)."
    try:
        cong = int(port or 22)
    except (TypeError, ValueError):
        return False, "Cong khong hop le."
    if not 1 <= cong <= 65535:
        return False, "Cong phai trong khoang 1-65535."

    if not tmux_session_exists(SSH_SESSION):
        return False, ("Chua co phien terminal SSH. Mo khung terminal ben duoi "
                       "de tao phien truoc roi bam lai.")

    truoc = _chup_man_hinh(SSH_SESSION)
    # Terminal dang dung o 1 dau nhac mat khau cu: go lenh vao day thi ca dong
    # lenh se bi hieu la mat khau. Dung lai va noi ro, thay vi lam roi them.
    if _la_dau_nhac_mat_khau(_dong_cuoi(truoc)):
        return False, ("Khung terminal dang dung o dau nhac mat khau cua lan truoc. "
                       "Vao khung terminal xu ly xong (nhap mat khau hoac bam Ctrl+C) "
                       "roi bam Ket noi lai.")

    cmd = f"ssh -o StrictHostKeyChecking=accept-new -p {cong} {user}@{host}"
    try:
        subprocess.run(["tmux", "send-keys", "-t", SSH_SESSION, cmd, "Enter"],
                       capture_output=True, timeout=5)
    except Exception as e:
        return False, f"Loi: {e}"

    if not password:
        return True, (f"Da gui lenh ket noi toi {host}. "
                      f"Nhap mat khau trong khung terminal ben duoi.")

    if not _cho_dau_nhac_mat_khau(SSH_SESSION, truoc, 12):
        return True, (f"Da gui lenh ket noi toi {host} nhung sau 12 giay khong thay dau "
                      f"nhac mat khau - co the thiet bi phan hoi cham, dang dung khoa (key), "
                      f"hoac khong ket noi duoc. Xem khung terminal ben duoi, nhap tay neu can.")

    try:
        # -l = gui NGUYEN VAN. Thieu -l thi tmux dich cac chuoi trung ten phim
        # (vi du mat khau chua "Enter", "Space") thanh phim bam thay vi ky tu.
        subprocess.run(["tmux", "send-keys", "-l", "-t", SSH_SESSION, password],
                       capture_output=True, timeout=5)
        subprocess.run(["tmux", "send-keys", "-t", SSH_SESSION, "Enter"],
                       capture_output=True, timeout=5)
    except Exception as e:
        return False, f"Loi khi gui mat khau: {e}"

    return True, (f"Da ket noi toi {host} va tu dien mat khau. "
                  f"Xem ket qua trong khung terminal ben duoi.")


# ---------------------------------------------------------------------------
# JS cua trang. De rieng ngoai f-string vi co rat nhieu dau ngoac nhon, nhet
# vao f-string phai nhan doi het - rat de sai va kho doc.
# ---------------------------------------------------------------------------
SSH_JS = """
<script>
(function () {
  "use strict";
  var o = document.getElementById("o_lenh");
  if (!o) return;
  var chon = document.getElementById("chon_tap");
  var bao = document.getElementById("bao_js");
  var baoServer = document.getElementById("bao_server");
  var KHOA_LUU = "consolepi-ssh-o-lenh";

  function noi(chuoi, xau) {
    bao.textContent = chuoi;
    bao.style.color = xau ? "#ffd166" : "#8b93a1";
  }

  // ---------------------------------------------------------------------
  // Gui form bang fetch, KHONG tai lai trang.
  //
  // Truoc day 2 nut nay la form POST binh thuong nen moi lan bam la trang
  // tai lai -> trinh duyet hoi "Leave site?" (do ttyd trong khung terminal
  // co dang ky canh bao truoc khi roi trang de khoi mat phien), va khung
  // terminal cung bi nap lai tu dau. Gui bang fetch thi terminal giu nguyen,
  // khong con hop thoai nao.
  // ---------------------------------------------------------------------
  function hienServer(chuoi, ok) {
    baoServer.textContent = chuoi;
    baoServer.className = "msg " + (ok ? "ok" : "err");
    baoServer.style.display = chuoi ? "block" : "none";
  }

  function guiForm(form, nut, chuNut) {
    var chuCu = nut.innerHTML;
    nut.disabled = true;
    nut.innerHTML = chuNut;
    hienServer("", true);
    fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: { "X-Console-Pi": "fetch" },
      cache: "no-store"
    })
      .then(function (r) {
        if (!r.ok) throw new Error("Server tra ve HTTP " + r.status);
        return r.json();
      })
      .then(function (d) { hienServer(d.msg, d.ok); })
      .catch(function (e) { hienServer("Khong lien lac duoc voi server: " + e.message, false); })
      .finally(function () { nut.disabled = false; nut.innerHTML = chuCu; });
  }

  var formKetNoi = document.getElementById("form_ket_noi");
  formKetNoi.addEventListener("submit", function (e) {
    e.preventDefault();
    guiForm(formKetNoi, document.getElementById("nut_ket_noi"), "Dang ket noi...");
    // Xoa mat khau khoi man hinh ngay sau khi gui di
    formKetNoi.querySelector("[name=password]").value = "";
  });

  var formDan = document.getElementById("form_dan");
  formDan.addEventListener("submit", function (e) {
    e.preventDefault();
    guiForm(formDan, document.getElementById("nut_dan"), "Dang dan...");
  });

  // Giu lai noi dung dang soan khi tai lai trang / bam Ket noi. Chi luu tren
  // may dang dung, khong gui ve server.
  function luu() { try { localStorage.setItem(KHOA_LUU, o.value); } catch (e) {} }
  o.addEventListener("input", luu);
  if (!o.value) {
    try {
      var cu = localStorage.getItem(KHOA_LUU);
      if (cu) o.value = cu;
    } catch (e) {}
  } else {
    luu();
  }

  document.getElementById("nut_chep").addEventListener("click", function () {
    var i = chon.value;
    if (i === "") { noi("Chon 1 tap lenh trong danh sach truoc.", true); return; }
    o.value = THU_VIEN[i].lenh;
    luu();
    noi("Da chep \\"" + THU_VIEN[i].ten + "\\" vao o. Sua lai IP/ten cho dung roi dan.");
  });

  function copyCachCu() {
    // Trang chay HTTP thuong (vao bang IP trong LAN) thi navigator.clipboard
    // KHONG ton tai - trinh duyet chi cho dung Clipboard API o ngu canh bao
    // mat (HTTPS hoac localhost). execCommand cu van chay duoc tren HTTP.
    try {
      o.focus(); o.select();
      var ok = document.execCommand("copy");
      noi(ok ? "Da copy noi dung o lenh." :
               "Trinh duyet khong cho copy tu dong - noi dung da duoc boi den, copy tay giup em.", !ok);
    } catch (e) {
      noi("Trinh duyet khong cho copy tu dong - noi dung da duoc boi den, copy tay giup em.", true);
    }
  }

  document.getElementById("nut_copy").addEventListener("click", function () {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(o.value).then(
        function () { noi("Da copy noi dung o lenh."); },
        function () { copyCachCu(); }
      );
    } else {
      copyCachCu();
    }
  });

  document.getElementById("nut_dan_cb").addEventListener("click", function () {
    if (navigator.clipboard && navigator.clipboard.readText && window.isSecureContext) {
      navigator.clipboard.readText().then(function (t) {
        o.value = t; luu(); noi("Da dan noi dung tu clipboard vao o.");
      }, function () {
        noi("Trinh duyet chan doc clipboard. Cham vao o roi dan tay, hoac dung ban phim ao.", true);
      });
    } else {
      noi("Vao bang HTTP nen trinh duyet khong cho doc clipboard. Cham vao o roi dan tay, " +
          "hoac dung ban phim ao.", true);
    }
  });

  document.getElementById("nut_xoa").addEventListener("click", function () {
    o.value = ""; luu(); noi("Da xoa o lenh.");
  });
})();
</script>
"""


def _render(msg="", ok=True, prefill=""):
    lib = load_library()
    term_running = service_active("console-pi-term-ssh.service")

    lib_options = "".join(
        f'<option value="{i}">{_esc(it.get("name"))}</option>' for i, it in enumerate(lib)
    )
    # Nhung du lieu do NGUOI DUNG TU NHAP vao trong the <script> - phai chan
    # duong thoat ra ngoai chay ma doc hai:
    #   - ensure_ascii=True: moi ky tu ngoai ASCII thanh \\uXXXX, khong bao gio
    #     lam vo cu phap JS (ke ca U+2028/U+2029 von lam vo chuoi JS).
    #   - Doi < > & thanh \\u003c \\u003e \\u0026: trong JSON, 3 ky tu nay chi
    #     xuat hien BEN TRONG chuoi nen doi la an toan, va sau khi doi thi
    #     trang khong con ky tu "<" tho nao trong the <script>.
    #     DA THU THAT: chi thay "</" bang "<\\/" la CHUA DU - mot tap lenh chua
    #     "<script>" van lot vao nguyen ven, ma theo chuan HTML, gap "<script"
    #     ben trong the script se day bo phan tich sang trang thai dac biet
    #     (script data double escaped) khien the </script> ke tiep KHONG con
    #     dong the nua -> vo trang / mo duong chen ma.
    lib_json = (json.dumps(
        [{"ten": it.get("name", ""), "lenh": it.get("commands", "")} for it in lib],
        ensure_ascii=True,
    ).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))

    msg_html = f'<div class="msg {"ok" if ok else "err"}">{_esc(msg)}</div>' if msg else ""
    term_status = ("" if term_running else
                   '<div class="msg err">Dich vu terminal SSH chua chay: '
                   '<code>sudo systemctl start console-pi-term-ssh</code></div>')

    # Bo trong: chi 1 hang nhap gon, khong tieu de/doan giai thich dai - de
    # danh cang nhieu chieu cao cang tot cho khung terminal.
    body = f"""
    {msg_html}
    {term_status}
    <div id="bao_server" class="msg ok" style="display:none;"></div>

    <form method="POST" action="/ssh/connect" id="form_ket_noi" class="row"
          style="align-items:flex-end;margin-bottom:10px;">
      <div><label style="margin-top:0;">Dia chi</label>
        <input type="text" name="host" placeholder="192.168.1.1" style="max-width:180px;" required></div>
      <div><label style="margin-top:0;">Tai khoan</label>
        <input type="text" name="user" placeholder="admin" style="max-width:140px;" required></div>
      <div><label style="margin-top:0;">Mat khau</label>
        <input type="password" name="password" autocomplete="new-password"
               placeholder="de trong = tu nhap" style="max-width:175px;"></div>
      <div><label style="margin-top:0;">Cong</label>
        <input type="number" name="port" value="22" style="max-width:85px;"></div>
      <div><button type="submit" id="nut_ket_noi">🔑 Ket noi</button></div>
    </form>

    <div class="card" style="padding:0;overflow:hidden;margin-bottom:12px;">
      <iframe src="/term-ssh/" title="SSH terminal"
              style="width:100%;height:calc(100vh - 330px);min-height:360px;border:0;display:block;background:#000;"></iframe>
    </div>

    <form method="POST" action="/ssh/paste" id="form_dan">
      <div class="row" style="margin-bottom:8px;">
        <select id="chon_tap" style="max-width:300px;">
          <option value="">-- Chon tap lenh tu Thu vien --</option>
          {lib_options}
        </select>
        <button type="button" class="gray" id="nut_chep">📄 Chep vao o</button>
      </div>
      <textarea name="noi_dung" id="o_lenh" style="max-width:100%;min-height:110px;"
                placeholder="Go lenh o day, hoac chon tap lenh o tren roi sua lai IP/ten cong...">{_esc(prefill)}</textarea>
      <div class="row" style="margin-top:10px;">
        <button type="submit" class="blue" id="nut_dan">⌨️ Dan vao terminal</button>
        <button type="button" class="gray" id="nut_copy">📋 Copy</button>
        <button type="button" class="gray" id="nut_dan_cb">📥 Dan tu clipboard</button>
        <button type="button" class="gray" id="nut_xoa">🧹 Xoa o</button>
      </div>
      <p id="bao_js" style="color:#8b93a1;font-size:13px;margin:9px 0 0;min-height:18px;">Dan =
      gui tung dong mot (thiet bi khong roi mat chu); dong CUOI chua bam Enter de anh doc lai.</p>
    </form>

    <script>var THU_VIEN = {lib_json};</script>
    {SSH_JS}"""

    html = render_page(body, active="/ssh", title="SSH", subtitle="")
    return html.replace("<body>", f'<body data-tmux-session="{SSH_SESSION}">', 1)


def register_ssh(app):
    @app.route("/ssh")
    def ssh_page():
        lib_idx = request.args.get("lib")
        prefill = ""
        if (lib_idx or "").isdigit():
            lib = load_library()
            i = int(lib_idx)
            if 0 <= i < len(lib):
                prefill = lib[i].get("commands", "")
        return _render(prefill=prefill)

    def _tra_ve(ok, msg, prefill=""):
        """
        Goi tu fetch (JS) thi tra JSON de trang KHONG phai tai lai - vua muot
        hon, vua khong lam khung terminal nap lai tu dau, vua khong dinh hop
        thoai "Leave site?" cua ttyd. Goi kieu form thuong (JS loi/bi tat) thi
        van dung nhu cu - khong bao gio mat duong lui.
        """
        if request.headers.get("X-Console-Pi") == "fetch":
            from flask import jsonify
            return jsonify({"ok": ok, "msg": msg})
        return _render(msg=msg, ok=ok, prefill=prefill)

    @app.route("/ssh/connect", methods=["POST"])
    def ssh_connect():
        f = request.form
        ok, msg = start_ssh_in_tmux(f.get("host", "").strip(),
                                    f.get("user", "").strip(),
                                    f.get("port", 22) or 22,
                                    f.get("password", ""))
        # Khong bao gio tra mat khau nguoc lai trang.
        return _tra_ve(ok, msg)

    @app.route("/ssh/paste", methods=["POST"])
    def ssh_paste():
        noi_dung = request.form.get("noi_dung", "")
        if not noi_dung.strip():
            return _tra_ve(False, "O lenh dang trong - chua co gi de dan.", noi_dung)
        # Gui TUNG DONG co giai lao: thiet bi mang khong roi mat ky tu dau
        # dong (xem giai thich trong dan_tung_dong_vao_tmux).
        ok, msg = dan_tung_dong_vao_tmux(SSH_SESSION, noi_dung)
        return _tra_ve(ok, msg, noi_dung)

    return app
