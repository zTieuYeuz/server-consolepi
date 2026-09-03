"""
Console Pi - Thu vien lenh (yeu cau so 6)

Luu cac tap lenh hay dung, them/sua/xoa duoc qua web. Tu day co the:
  - Gui thang vao Terminal dang mo (qua tmux send-keys)
  - Copy sang tab SSH de sua (doi IP/ten) roi chay hang loat

File luu: /opt/console-pi/command-library.json  (giu nguyen khi cai dat lai)
"""
import json
import os
import subprocess
import time

from flask import request

from .layout import render_page

LIB_FILE = "/opt/console-pi/command-library.json"

# 5 tap lenh co ban hay dung nhat khi lam viec voi switch Cisco
DEFAULT_LIBRARY = [
    {
        "name": "Xem thong tin co ban switch",
        "desc": "Kiem tra model, IOS version, uptime, so serial",
        "tags": "cisco, xem",
        "commands": "show version\nshow inventory\nshow env all",
    },
    {
        "name": "Xem trang thai tat ca cong",
        "desc": "Cong nao up/down, toc do, duplex, VLAN dang gan",
        "tags": "cisco, xem, port",
        "commands": "show ip interface brief\nshow interfaces status\nshow interfaces description",
    },
    {
        "name": "Xem VLAN va bang MAC",
        "desc": "Danh sach VLAN, cong nao thuoc VLAN nao, MAC dang hoc duoc",
        "tags": "cisco, xem, vlan",
        "commands": "show vlan brief\nshow mac address-table\nshow interfaces trunk",
    },
    {
        "name": "Gan VLAN cho 1 cong (access)",
        "desc": "SUA lai ten cong va so VLAN truoc khi chay",
        "tags": "cisco, cau hinh, vlan",
        "commands": ("interface GigabitEthernet0/1\n"
                     " description Cau hinh boi Console Pi\n"
                     " switchport mode access\n"
                     " switchport access vlan 10\n"
                     " no shutdown"),
    },
    {
        "name": "Cau hinh IP quan ly + SSH",
        "desc": "SUA lai IP/subnet/gateway/domain truoc khi chay",
        "tags": "cisco, cau hinh, quan ly",
        "commands": ("interface Vlan1\n"
                     " ip address 192.168.1.10 255.255.255.0\n"
                     " no shutdown\n"
                     "exit\n"
                     "ip default-gateway 192.168.1.1\n"
                     "ip domain-name local.lan\n"
                     "crypto key generate rsa modulus 2048\n"
                     "ip ssh version 2\n"
                     "line vty 0 4\n"
                     " transport input ssh\n"
                     " login local"),
    },
]


def load_library():
    """Doc thu vien. Lan dau chua co file thi tao san 5 tap lenh mau."""
    try:
        with open(LIB_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except FileNotFoundError:
        save_library(DEFAULT_LIBRARY)
        return list(DEFAULT_LIBRARY)
    except Exception:
        pass
    return []


def save_library(items):
    try:
        with open(LIB_FILE, "w") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def add_item(name, desc, tags, commands):
    items = load_library()
    items.append({"name": name, "desc": desc, "tags": tags, "commands": commands})
    return save_library(items)


def update_item(index, name, desc, tags, commands):
    items = load_library()
    if 0 <= index < len(items):
        items[index] = {"name": name, "desc": desc, "tags": tags, "commands": commands}
        return save_library(items)
    return False


def delete_item(index):
    items = load_library()
    if 0 <= index < len(items):
        items.pop(index)
        return save_library(items)
    return False


def send_to_tmux(session_name, text, press_enter=False):
    """
    Dan tap lenh vao phien tmux dang chay (terminal tren web).

    Dung "bracketed paste" cua tmux (paste-buffer -p) thay vi send-keys:
      - send-keys se lam cac dong DINH LIEN nhau thanh 1 dong vo nghia
      - bracketed paste giu nguyen xuong dong, va shell (bash >= 4.4) hieu
        day la van ban dan vao nen KHONG tu chay - nguoi dung xem lai roi
        moi tu bam Enter. Dung y do "sua xong xac nhan moi chay".
    """
    import tempfile

    try:
        has = subprocess.run(["tmux", "has-session", "-t", session_name],
                             capture_output=True, timeout=5)
        if has.returncode != 0:
            return False, (f"Chua co phien terminal '{session_name}'. "
                           f"Mo tab Terminal truoc roi bam lai.")

        buf_name = "consolepi-lib"
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write(text.rstrip("\n"))
            tmp = f.name
        try:
            subprocess.run(["tmux", "load-buffer", "-b", buf_name, tmp],
                           capture_output=True, timeout=5)
            subprocess.run(["tmux", "paste-buffer", "-p", "-b", buf_name,
                            "-t", session_name],
                           capture_output=True, timeout=5)
            if press_enter:
                subprocess.run(["tmux", "send-keys", "-t", session_name, "Enter"],
                               capture_output=True, timeout=5)
        finally:
            os.unlink(tmp)

        n = len([l for l in text.splitlines() if l.strip()])
        if press_enter:
            return True, f"Da dan va chay {n} lenh trong terminal."
        # Loi nhan trung tinh: ham nay duoc goi ca tu trang Thu vien lenh lan
        # tu trang SSH (khung terminal nam ngay tren cung trang), nen khong
        # noi cung "mo tab Terminal" nua.
        return True, (f"Da dan {n} lenh vao khung terminal (CHUA chay). "
                      f"Doc lai lan cuoi roi bam Enter trong khung terminal de chay.")
    except FileNotFoundError:
        return False, "Chua cai tmux tren may."
    except Exception as e:
        return False, f"Loi: {e}"


def _chup_man_hinh_tmux(session_name):
    try:
        r = subprocess.run(["tmux", "capture-pane", "-p", "-t", session_name],
                           capture_output=True, text=True, timeout=5)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


def _dong_cuoi_man_hinh(text):
    dong = [l.rstrip() for l in (text or "").splitlines() if l.strip()]
    return dong[-1] if dong else ""


def _giong_dau_nhac(dong):
    """
    Dong nay co giong dau nhac dang cho go lenh khong?

    Switch/router: "Switch#", "Switch>", "Switch(config-if)#".
    May Linux:     "... $" hoac "... #".
    KHONG tinh dau ":" la dau nhac - do thuong la dau nhac MAT KHAU, gui lenh
    vao do la sai cho.
    """
    d = (dong or "").rstrip()
    return d.endswith("#") or d.endswith(">") or d.endswith("$")


def _cho_thiet_bi_in_xong(session_name, im_lang_giay=0.5,
                          im_lang_khong_dau_nhac=2.5, cho_toi_da=25.0):
    """
    Doi cho toi khi thiet bi IN XONG va THUC SU san sang nhan lenh tiep theo.

    VI SAO KHONG cho mot khoang co dinh: lenh "show version" tren switch that
    in ra hang tram dong, mat vai giay. Cho co dinh 0.18s roi ban dong ke
    tiep thi thiet bi VAN DANG IN, chua doc kip dau vao -> mat ky tu dau dong
    (loi that: "show inventory" thanh "how inventory").

    Dieu kien coi la san sang - phai du CA HAI:
      1. Man hinh khong doi trong `im_lang_giay`
      2. Dong cuoi GIONG DAU NHAC (ket thuc bang # > $)
    Chi "im lang" thoi la CHUA DU: thiet bi cham co the ngung giua chung 1
    nhip roi in tiep, hoac dang dung o "--More--" cho bam phim - ca hai deu
    khong phai la da xong. Neu im lang lau (`im_lang_khong_dau_nhac`) ma van
    khong thay dau nhac thi cung tra ve, de khong ket lai voi nhung thiet bi
    co dau nhac la.

    LOI THAT DA GAP NGAY TRONG HAM NAY: ban dau chi kiem tra "--More--" khi
    man hinh CO THAY DOI. Nhung thiet bi dung o "--More--" thi man hinh dung
    im -> bi cham nham la "da in xong" -> gui dong ke tiep, va ky tu dau tien
    cua dong do bi thiet bi an luon lam PHIM BAM de sang trang. Ket qua dung
    y het loi cu: mat 1 ky tu dau dong. Nay kiem tra "--More--" o MOI vong.
    """
    het_han = time.time() + cho_toi_da
    truoc = _chup_man_hinh_tmux(session_name)
    lan_doi_cuoi = time.time()

    while time.time() < het_han:
        time.sleep(0.15)
        hien = _chup_man_hinh_tmux(session_name)
        cuoi = _dong_cuoi_man_hinh(hien)

        # Kiem tra o MOI vong, khong phu thuoc man hinh co doi hay khong
        if "--more--" in cuoi.lower():
            subprocess.run(["tmux", "send-keys", "-t", session_name, "Space"],
                           capture_output=True, timeout=5)
            truoc = hien
            lan_doi_cuoi = time.time()
            continue

        if hien != truoc:
            truoc = hien
            lan_doi_cuoi = time.time()
            continue

        im_lang = time.time() - lan_doi_cuoi
        if im_lang >= im_lang_giay and _giong_dau_nhac(cuoi):
            return True
        if im_lang >= im_lang_khong_dau_nhac:
            return True

    return False


def dan_tung_dong_vao_tmux(session_name, text, tre_giay=0.25, toi_da_dong=120):
    """
    Dan tap lenh vao phien tmux nhung GUI TUNG DONG, co giai lao giua cac dong.

    VI SAO KHONG dung send_to_tmux() o day: ham do bắn ca khoi van ban ra 1
    luot. Voi bash thi khong sao, nhung voi THIET BI MANG THAT (switch/router
    qua SSH hoac cong console) thi CLI khong co dieu khien luong - trong luc
    thiet bi con dang xu ly + echo lai dong truoc, cac ky tu dau cua dong ke
    tiep bi ROI MAT.

    LOI THAT DA GAP (2 vong):
      1. Ban ca khoi ra 1 luot -> "show interfaces trunk" thanh "how
         interfaces trunk".
      2. Sua thanh cho CO DINH 0.18s giua cac dong -> VAN MAT CHU, vi
         "show version" tren switch that in ra hang tram dong mat vai giay,
         0.18s la qua ngan, thiet bi con dang in thi dong sau da toi.
    Nen bay gio KHONG cho theo thoi gian co dinh nua ma CHO DEN KHI THIET BI
    IN XONG (man hinh im lang) roi moi gui dong tiep - dung nhip cua tung
    thiet bi, thiet bi cham cach may cung khong mat chu.

    KHONG bam Enter o DONG CUOI: cac dong truoc no thi thiet bi mang coi
    xuong dong = Enter nen se chay, rieng dong cuoi de nguyen cho nguoi dung
    doc lai lan cuoi roi tu bam - giu dung nguyen tac "xem roi moi chay".
    """
    dong = [d for d in text.rstrip("\n").split("\n")]
    if not dong or not any(d.strip() for d in dong):
        return False, "Khong co noi dung de dan."
    if len(dong) > toi_da_dong:
        return False, (f"Tap lenh co {len(dong)} dong, vuot qua {toi_da_dong} dong cho 1 lan dan. "
                       f"Chia nho ra dan lam nhieu lan cho an toan.")

    try:
        has = subprocess.run(["tmux", "has-session", "-t", session_name],
                             capture_output=True, timeout=5)
        if has.returncode != 0:
            return False, (f"Chua co phien terminal '{session_name}'. "
                           f"Mo khung terminal truoc roi bam lai.")

        han_chot = time.time() + 180          # tran tong: khong treo mai mai
        da_gui = 0
        cham_gio = False

        for i, d in enumerate(dong):
            if time.time() > han_chot:
                cham_gio = True
                break

            # -l = gui NGUYEN VAN, khong dich cac chuoi trung ten phim
            # (vi du dong lenh co chu "Space" hay "Enter") thanh phim bam.
            subprocess.run(["tmux", "send-keys", "-l", "-t", session_name, d],
                           capture_output=True, timeout=5)
            da_gui += 1

            if i < len(dong) - 1:
                subprocess.run(["tmux", "send-keys", "-t", session_name, "Enter"],
                               capture_output=True, timeout=5)
                # Cho THIET BI in xong roi moi gui dong ke tiep (khong phai
                # cho mot khoang co dinh - xem giai thich o tren).
                _cho_thiet_bi_in_xong(session_name)
                # Nghi them 1 nhip ngan: vai thiet bi in xong dau nhac roi
                # van con ban vai chuc ms truoc khi doc duoc dau vao.
                time.sleep(tre_giay)
    except FileNotFoundError:
        return False, "Chua cai tmux tren may."
    except Exception as e:
        return False, f"Loi: {e}"

    if cham_gio:
        return False, (f"Da gui {da_gui}/{len(dong)} dong roi phai dung vi qua 3 phut - "
                       f"thiet bi phan hoi qua cham hoac dang ket. Kiem tra khung terminal, "
                       f"dan phan con lai sau.")

    n = len([d for d in dong if d.strip()])
    if len(dong) == 1:
        return True, "Da dan vao khung terminal (CHUA chay) - bam Enter trong terminal de chay."
    return True, (f"Da dan {n} lenh: gui tung dong, moi dong deu CHO THIET BI IN XONG moi "
                  f"gui dong tiep nen khong bi roi mat chu. Dong CUOI chua bam Enter - "
                  f"doc lai roi tu bam de chay.")


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# CSS + JS cho o tim kiem. De rieng ngoai f-string vi trong JS co rat nhieu
# dau ngoac nhon - nhet vao f-string phai nhan doi het, rat de sai va kho doc.
LIB_CSS = """
<style>
.tim-hop { display:flex; gap:9px; align-items:center; flex-wrap:wrap; margin-bottom:12px; }
.tim-hop input { max-width:420px; }
.the-loc { display:flex; gap:7px; flex-wrap:wrap; margin-bottom:14px; }
.the-loc .the { background:#22262b; border:1px solid #363b42; color:#a8b0bd;
                border-radius:99px; padding:6px 13px; font-size:13px; cursor:pointer;
                min-height:34px; }
.the-loc .the:hover { background:#2c3036; color:#fff; }
.lenh-luoi { display:grid; grid-template-columns:repeat(auto-fill,minmax(345px,1fr)); gap:13px; }
.lenh-luoi .card { margin-bottom:0; display:flex; flex-direction:column; }
.lenh-luoi pre { max-height:132px; overflow:auto; margin:9px 0 0; flex:1; }
.tap-ten { margin:0 0 3px; font-size:15px; color:#4CAF50; }
.tap-mo-ta { color:#8b93a1; font-size:13px; }
.tap-meta { color:#6b7280; font-size:12px; margin-top:4px; }
</style>
"""

LIB_JS = """
<script>
(function () {
  "use strict";
  var o = document.getElementById("tim_lenh");
  if (!o) return;
  var nutXoa = document.getElementById("xoa_tim");
  var dem = document.getElementById("dem_kq");
  var trong = document.getElementById("khong_thay");
  var the = Array.prototype.slice.call(document.querySelectorAll("[data-tim]"));

  function loc() {
    var q = (o.value || "").trim().toLowerCase();
    var hien = 0;
    the.forEach(function (el) {
      var khop = !q || (el.getAttribute("data-tim") || "").indexOf(q) >= 0;
      el.style.display = khop ? "" : "none";
      if (khop) hien++;
    });
    dem.textContent = hien + "/" + the.length;
    trong.style.display = hien ? "none" : "block";
    nutXoa.style.display = q ? "inline-block" : "none";
  }

  o.addEventListener("input", loc);
  nutXoa.addEventListener("click", function () { o.value = ""; loc(); o.focus(); });

  // Bam vao the (tag) = loc theo the do. Tien khi dung man hinh cam ung
  // khong co ban phim: khong can go chu nao van loc duoc.
  document.querySelectorAll("[data-the]").forEach(function (c) {
    c.addEventListener("click", function () {
      var t = c.getAttribute("data-the");
      o.value = (o.value.trim().toLowerCase() === t) ? "" : t;   // bam lai = bo loc
      loc();
    });
  });

  loc();
})();
</script>
"""


def render_library_page(msg="", ok=True, edit_index=None):
    items = load_library()

    # Gom the (tag) duy nhat de lam nut loc nhanh
    tat_ca_the = []
    for it in items:
        for t in (it.get("tags") or "").split(","):
            t = t.strip().lower()
            if t and t not in tat_ca_the:
                tat_ca_the.append(t)
    the_html = "".join(
        f'<button type="button" class="the" data-the="{_esc(t)}">{_esc(t)}</button>'
        for t in sorted(tat_ca_the)
    )
    the_khoi = f'<div class="the-loc">{the_html}</div>' if the_html else ""

    rows = ""
    for i, it in enumerate(items):
        cmds = _esc(it.get("commands", ""))
        n_lines = len([l for l in it.get("commands", "").splitlines() if l.strip()])
        # Chuoi de tim kiem: gom ten + mo ta + the + noi dung lenh, viet
        # thuong san de JS chi viec so sanh, khong phai xu ly gi them.
        kho_tim = _esc(" ".join([
            it.get("name", ""), it.get("desc", ""),
            it.get("tags", ""), it.get("commands", ""),
        ]).lower())
        rows += f"""
        <div class="card" data-tim="{kho_tim}">
          <h3 class="tap-ten">{_esc(it.get('name'))}</h3>
          <div class="tap-mo-ta">{_esc(it.get('desc'))}</div>
          <div class="tap-meta">{n_lines} lenh &middot; {_esc(it.get('tags'))}</div>
          <pre>{cmds}</pre>
          <div class="row" style="margin-top:10px;">
            <form method="POST" action="/commands/send" style="display:inline;">
              <input type="hidden" name="index" value="{i}">
              <button type="submit" class="blue small">⌨️ Gui vao Terminal</button>
            </form>
            <a class="btn small" href="/ssh?lib={i}">🔑 Dung o tab SSH</a>
            <a class="btn gray small" href="/commands?edit={i}">✏️ Sua</a>
            <form method="POST" action="/commands/delete" style="display:inline;"
                  onsubmit="return confirm('Xoa tap lenh &quot;{_esc(it.get('name'))}&quot;?');">
              <input type="hidden" name="index" value="{i}">
              <button type="submit" class="red small">🗑 Xoa</button>
            </form>
          </div>
        </div>"""

    if not items:
        rows = '<div class="msg info">Thu vien dang trong. Them tap lenh dau tien ben duoi.</div>'

    # Form them moi hoac sua
    editing = edit_index is not None and 0 <= edit_index < len(items)
    cur = items[edit_index] if editing else {"name": "", "desc": "", "tags": "", "commands": ""}
    action = "/commands/update" if editing else "/commands/add"

    form_ruot = f"""
      <form method="POST" action="{action}">
        {f'<input type="hidden" name="index" value="{edit_index}">' if editing else ''}
        <label>Ten tap lenh</label>
        <input type="text" name="name" required value="{_esc(cur.get('name'))}"
               placeholder="Vi du: Gan VLAN cho 1 cong">
        <label>Mo ta ngan</label>
        <input type="text" name="desc" value="{_esc(cur.get('desc'))}"
               placeholder="Nho ghi ro cho nao can sua truoc khi chay">
        <label>The (phan cach bang dau phay) - dung de loc nhanh o tren</label>
        <input type="text" name="tags" value="{_esc(cur.get('tags'))}"
               placeholder="cisco, vlan, cau hinh">
        <label>Cac lenh (moi dong 1 lenh)</label>
        <textarea name="commands" required style="max-width:100%;">{_esc(cur.get('commands'))}</textarea>
        <div class="row" style="margin-top:12px;">
          <button type="submit">{'Luu thay doi' if editing else 'Them vao thu vien'}</button>
          {'<a class="btn gray" href="/commands">Huy</a>' if editing else ''}
        </div>
      </form>"""

    if editing:
        # Dang sua thi mo san va dua len TREN CUNG - do la viec anh dang lam.
        form_html = f"""
        <h2>✏️ Sua: {_esc(cur.get('name'))}</h2>
        <div class="card">{form_ruot}</div>"""
    else:
        # Khong sua thi thu gon xuong DUOI danh sach: vao trang la thay ngay
        # thu vien de tim, khong bi form them moi choan het phan tren.
        form_html = f"""
        <details style="margin-top:18px;">
          <summary style="cursor:pointer;color:#4CAF50;font-size:16px;font-weight:600;
                          padding:10px 0;">➕ Them tap lenh moi</summary>
          <div class="card" style="margin-top:10px;">{form_ruot}</div>
        </details>"""

    msg_html = f'<div class="msg {"ok" if ok else "err"}">{_esc(msg)}</div>' if msg else ""

    body = f"""
    {LIB_CSS}
    {msg_html}
    <div class="tim-hop">
      <input type="text" id="tim_lenh" placeholder="🔎 Go de tim: ten, mo ta, the, hoac noi dung lenh...">
      <button type="button" class="gray small" id="xoa_tim" style="display:none;">✕ Xoa tim</button>
      <span style="color:#8b93a1;font-size:13px;">Hien <strong id="dem_kq">0/0</strong> tap lenh</span>
    </div>
    {the_khoi}
    <div id="khong_thay" class="msg info" style="display:none;">
      Khong co tap lenh nao khop. Thu tu khoa ngan hon, hoac bam ✕ Xoa tim.
    </div>
    <div class="lenh-luoi">{rows}</div>
    {form_html}
    <div class="msg info" style="margin-top:18px;">
      <strong>Cach dung:</strong> <em>Gui vao Terminal</em> dan lenh vao terminal dang mo nhung
      <strong>khong tu bam Enter</strong> - anh xem lai roi tu chay.
      <em>Dung o tab SSH</em> chep tap lenh sang o soan o tab SSH de sua IP/ten truoc khi dan.
    </div>
    {LIB_JS}"""

    return render_page(body, active="/commands", title="Thu vien lenh",
                       subtitle="Luu san cac tap lenh hay dung, sua duoc truoc khi chay")


def register_commands(app, tmux_session="consolepi-local"):
    @app.route("/commands")
    def commands_page():
        edit = request.args.get("edit")
        edit_index = int(edit) if (edit or "").isdigit() else None
        return render_library_page(edit_index=edit_index)

    @app.route("/commands/add", methods=["POST"])
    def commands_add():
        f = request.form
        if not (f.get("name") or "").strip() or not (f.get("commands") or "").strip():
            return render_library_page(msg="Thieu ten hoac noi dung lenh.", ok=False)
        add_item(f.get("name").strip(), f.get("desc", "").strip(),
                 f.get("tags", "").strip(), f.get("commands"))
        return render_library_page(msg=f"Da them '{f.get('name')}'.", ok=True)

    @app.route("/commands/update", methods=["POST"])
    def commands_update():
        f = request.form
        idx = int(f.get("index", -1) or -1)
        if update_item(idx, f.get("name", "").strip(), f.get("desc", "").strip(),
                       f.get("tags", "").strip(), f.get("commands", "")):
            return render_library_page(msg="Da luu thay doi.", ok=True)
        return render_library_page(msg="Khong tim thay tap lenh de sua.", ok=False)

    @app.route("/commands/delete", methods=["POST"])
    def commands_delete():
        idx = int(request.form.get("index", -1) or -1)
        if delete_item(idx):
            return render_library_page(msg="Da xoa tap lenh.", ok=True)
        return render_library_page(msg="Khong tim thay tap lenh.", ok=False)

    @app.route("/commands/send", methods=["POST"])
    def commands_send():
        idx = int(request.form.get("index", -1) or -1)
        items = load_library()
        if not (0 <= idx < len(items)):
            return render_library_page(msg="Khong tim thay tap lenh.", ok=False)
        ok, msg = send_to_tmux(tmux_session, items[idx].get("commands", ""))
        return render_library_page(msg=msg, ok=ok)

    return app
